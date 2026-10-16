# author: dracaryS
# v3.2 Update Multifunctional Wiki

# static imports
import ui, localeInfo, osfInfo, _weakref, playersettingmodule, uiScriptLocale
from operator import truediv
import math
# dynamic imports
import app, grp, chat, chr, item, nonplayer, player, app, WikiRenderTarget, wiki, chrmgr
import servergamedata

if app.ENABLE_ITEMSHOP:
	import uiItemShop

IMG_DIR = "d:/ymir work/ui/game/wiki/"
IMG_DIR_CATEGORY = "d:/ymir work/ui/game/wiki/category/"

def GetArticleFileName(index):
	file_dict= {
		0 : "wiki/landingpage.txt",
		1 : "wiki/server/rules.txt",
		2 : "wiki/server/faq.txt",
		3 : "wiki/events/event.txt",
		4 : "wiki/events/wheel_of_fortune.txt",
		5 : "wiki/systems/aggression.txt",
		6 : "wiki/systems/buffi.txt",
		7 : "wiki/systems/energy_crystal.txt",
		9 : "wiki/systems/multi_farm.txt",
		10 : "wiki/systems/pendants.txt",
		11 : "wiki/systems/pet.txt",
		12 : "wiki/systems/pickup.txt",
		13 : "wiki/systems/premium_feature.txt",
		14 : "wiki/systems/reinforcements.txt",
		15 : "wiki/systems/sash_skin.txt",
		16 : "wiki/systems/67.txt",
		17 : "wiki/dungeons/ork.txt",
		18 : "wiki/dungeons/dt.txt",
		19 : "wiki/dungeons/dc.txt",
		20 : "wiki/dungeons/sd.txt",
		21 : "wiki/dungeons/beran.txt",
		22 : "wiki/dungeons/razador.txt",
		23 : "wiki/dungeons/nemere.txt",
		24 : "wiki/dungeons/dawn.txt",
		25 : "wiki/dungeons/hydra.txt",
		26 : "wiki/dungeons/meley.txt",
		27 : "wiki/dungeons/akzadur.txt",
		28 : "wiki/dungeons/nafaroth.txt",
		29 : "wiki/dungeons/zodiac.txt",
		30 : "wiki/systems/dss.txt",
		31 : "wiki/systems/mission_book.txt",
		32 : "wiki/systems/queue.txt",
	}
	return app.GetLocalePath()+"/"+file_dict[index] if index in file_dict else ""

def IsGameMaster():
	return True if player.GetName().find("[") != -1 or player.GetName().find("Hex") != -1 or player.GetName().find("Paradox") != -1 else False

def IsCategory(argument, searchingArgument):
	argument = argument.lower() if not localeInfo.IsARABIC() else argument
	searchingArgument = searchingArgument.lower() if not localeInfo.IsARABIC() else searchingArgument
	_dict = {
		"equipment" : ["equipment"],
		"article" : ["article",],
		"chests" : ["chests"],
		"monster" : ["monster"],
		"bosses" : ["bosses"],
		"metinstone" : ["metinstone"],
		"costume" : ["costume"],
		"cube" : ["cube"],
	}
	if searchingArgument in _dict:
		return True if argument in _dict[searchingArgument] else False
	return False

def GetCategoryDict():
	return {
		0 : {
			"name" : localeInfo.WIKI_EQUIPMENT,
			"type" : "equipment",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_EQUIPMENT_WEAPONS,
				1 : localeInfo.WIKI_EQUIPMENT_ARMOR,
				2 : localeInfo.WIKI_EQUIPMENT_HELMET,
				3 : localeInfo.WIKI_EQUIPMENT_SHIELD,
				4 : localeInfo.WIKI_EQUIPMENT_EARRING,
				5 : localeInfo.WIKI_EQUIPMENT_BRACELET,
				6 : localeInfo.WIKI_EQUIPMENT_NECKLACE,
				7 : localeInfo.WIKI_EQUIPMENT_SHOES,
				8 : localeInfo.WIKI_EQUIPMENT_BELT,
				9 : localeInfo.WIKI_EQUIPMENT_TALISMAN,
				10 : localeInfo.WIKI_CRYSTAL,
			},
		},
		1 : {
			"name" : localeInfo.WIKI_COSTUME,
			"type" : "costume",
			"items": {
				# Key : name
				0 : localeInfo.CATEGORY_COSTUMES_COSTUME_WEAPON,
				1 : localeInfo.CATEGORY_COSTUMES_COSTUME_BODY,
				2 : localeInfo.CATEGORY_COSTUMES_COSTUME_HAIR,
				3 : localeInfo.CATEGORY_COSTUMES_SASH,
				4 : localeInfo.WIKI_CATEGORY_COSTUMES_SASH_SKIN,
				5 : localeInfo.WIKI_PET,
				6 : localeInfo.WIKI_PET_SKIN,
				7 : localeInfo.WIKI_MOUNT,
				8 : localeInfo.WIKI_MOUNT_SKIN,
				9 : localeInfo.WIKI_PET_LEVEL,
			},
		},
		2 : {
			"name" : localeInfo.WIKI_CHESTS,
			"type" : "chests",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_CHESTS_BOSS,
				1 : localeInfo.WIKI_CHESTS_EVENT,
				2 : localeInfo.WIKI_CHESTS_ALTERNATIVE,
				3 : localeInfo.WIKI_ITEM_SHOP,
			},
		},
		3 : {
			"name" : localeInfo.WIKI_BOSSES,
			"type" : "bosses",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_LOW,
				1 : localeInfo.WIKI_HIGH,
				2 : localeInfo.WIKI_PRE_D,
				3 : localeInfo.WIKI_D,
				4 : localeInfo.WIKI_WORLD,
			},
		},
		4 : {
			"name" : localeInfo.WIKI_METINSTONE,
			"type" : "metinstone",
			"items": {
				# Key : name
				0 : localeInfo.WIKI_1_75,
				1 : localeInfo.WIKI_76_100,
				2 : localeInfo.WIKI_100,
				3 : localeInfo.WIKI_STONE_D,
			},
		},
		5 : {
			"name" : localeInfo.WIKI_BASIC_GUIDES,
			"type" : "guide",
			"items": {
				# Key : name
				2 : localeInfo.WIKI_FAQ,
				1 : localeInfo.WIKI_RULES,
			},
		},
		6 : {
			"name" : localeInfo.WIKI_SYSTEMS,
			"type" : "system",
			"items": {
				# Key : name
				9 : localeInfo.MULTI_FARM_BLOCK,
				12 : localeInfo.AUTO_PICKUP,
				13 : localeInfo.PREMIUM_SHOP,
				5 : localeInfo.BRAVERY_CAPE,
				6 : localeInfo.BUFFI_PARTNER,
				7 : localeInfo.WIKI_CRYSTAL,
				10 : localeInfo.WIKI_TALISMAN_GUIDE,
				11 : localeInfo.PET_SYSTEM,
				14 : localeInfo.WIKI_REINFORCEMENT,
				15 : localeInfo.WIKI_CATEGORY_COSTUMES_SASH_SKIN,
				16 : localeInfo.RARE_SYSTEM,
				30 : localeInfo.CATEGORY_DRAGON_STONE,
				31 : localeInfo.MISSION_BOOKS,
				32 : localeInfo.WIKI_QUEUE_GUIDE,
			},
		},
		7 : {
			"name" : localeInfo.WIKI_CRAFT,
			"type" : "cube",
			"items": {
				# Key : name
				0 : localeInfo.CATEGORY_EQUIPMENT_WEAPON,
				1 : localeInfo.CUBE_CATEGORY_ARMOR,
				2 : localeInfo.PRIVATESHOPSEARCH_HEAD,
				3 : localeInfo.PRIVATESHOPSEARCH_SHIELD,
				4 : localeInfo.PRIVATESHOPSEARCH_EQUIPMENT_EARRINGS,
				5 : localeInfo.CATEGORY_JEWELRY_ARMOR_WRIST,
				6 : localeInfo.PRIVATESHOPSEARCH_NECK,
				7 : localeInfo.CATEGORY_JEWELRY_ARMOR_FOOTS,
				8 : localeInfo.CATEGORY_JEWELRY_ITEM_BELT,
				# 9 : localeInfo.WIKI_DREAM_SOULS,
			},
		},
		8 : {
			"name" : localeInfo.WIKI_DUNGEONS,
			"type" : "dungeon",
			"items": {
				# Key : name
				17 : nonplayer.GetMonsterName(693),
				18 : localeInfo.MAP_DEVILTOWER1,
				19 : localeInfo.MAP_DEVILCATACOMB,
				20 : nonplayer.GetMonsterName(2092),
				21 : nonplayer.GetMonsterName(2493),
				22 : localeInfo.MAP_N_FLAME_DUNGEON_01,
				23 : localeInfo.MAP_N_SNOW_DUNGEON_01,
				24 : localeInfo.MAP_DAWNMIST_DUNGEON_01,
				25 : localeInfo.MAP_DEFENSE_WAVE,
				26 : localeInfo.MAP_N_FLAME_DRAGON,
				27 : nonplayer.GetMonsterName(6500),
				28 : nonplayer.GetMonsterName(6501),
				29 : localeInfo.MAP_CZ_DUNGEON,
			},
		},
		9 : {
			"name" : localeInfo.WIKI_EVENTS,
			"type" : "events",
			"items": {
				# Key : name
				3 : localeInfo.WIKI_EVENTS,
				4 : localeInfo.WHEEL_GAME_TITLE,
			},
		},
	}

def GetResultPageImage(argument):
	imgDict = {
		"equipment":
		{
			0 : IMG_DIR_CATEGORY+"equipment_0.png",
			1 : IMG_DIR_CATEGORY+"equipment_1.png",
			2 : IMG_DIR_CATEGORY+"equipment_2.png",
			3 : IMG_DIR_CATEGORY+"equipment_3.png",
			4 : IMG_DIR_CATEGORY+"equipment_4.png",
			5 : IMG_DIR_CATEGORY+"equipment_5.png",
			6 : IMG_DIR_CATEGORY+"equipment_6.png",
			7 : IMG_DIR_CATEGORY+"equipment_7.png",
			8 : IMG_DIR_CATEGORY+"equipment_8.png",
			9 : IMG_DIR_CATEGORY+"equipment_9.png",
			10 : IMG_DIR_CATEGORY+"equipment_10.png",
		},
		"costume":
		{
			0 : IMG_DIR_CATEGORY+"costume_weapons.png",
			1 : IMG_DIR_CATEGORY+"costume_armor.png",
			2 : IMG_DIR_CATEGORY+"costume_hair.png",
			3 : IMG_DIR_CATEGORY+"costume_sash.png",
			4 : IMG_DIR_CATEGORY+"costume_sashcostumes.png",
			5 : IMG_DIR_CATEGORY+"pets.png",
			6 : IMG_DIR_CATEGORY+"costume_pet.png",
			7 : IMG_DIR_CATEGORY+"costume_mount.png",
			8 : IMG_DIR_CATEGORY+"mount_skins.png",
			9 : IMG_DIR_CATEGORY+"pet_system.png",
		},
		"chests":
		{
			0 : IMG_DIR_CATEGORY+"chests.png",
			1 : IMG_DIR_CATEGORY+"chests.png",
			2 : IMG_DIR_CATEGORY+"chests.png",
			3 : IMG_DIR_CATEGORY+"chests.png",
		},
		"bosses":
		{
			0 : IMG_DIR_CATEGORY+"bosses_wall.png",
			1 : IMG_DIR_CATEGORY+"bosses_wall.png",
			2 : IMG_DIR_CATEGORY+"bosses_wall.png",
			3 : IMG_DIR_CATEGORY+"bosses_wall.png",
			4 : IMG_DIR_CATEGORY+"bosses_wall.png",
		},
		"monster":
		{
			0 : IMG_DIR_CATEGORY+"monster_wall.png",
			1 : IMG_DIR_CATEGORY+"monster_wall.png",
			2 : IMG_DIR_CATEGORY+"monster_wall.png",
		},
		"metinstone":
		{
			0 : IMG_DIR_CATEGORY+"metinstone_wall.png",
			1 : IMG_DIR_CATEGORY+"metinstone_wall.png",
			2 : IMG_DIR_CATEGORY+"metinstone_wall.png",
			3 : IMG_DIR_CATEGORY+"metinstone_wall.png",
		},
		"cube":
		{
			0 : IMG_DIR_CATEGORY+"crafting.png",
			1 : IMG_DIR_CATEGORY+"crafting.png",
			2 : IMG_DIR_CATEGORY+"crafting.png",
			3 : IMG_DIR_CATEGORY+"crafting.png",
			4 : IMG_DIR_CATEGORY+"crafting.png",
			5 : IMG_DIR_CATEGORY+"crafting.png",
			6 : IMG_DIR_CATEGORY+"crafting.png",
			7 : IMG_DIR_CATEGORY+"crafting.png",
			8 : IMG_DIR_CATEGORY+"crafting.png",
			9 : IMG_DIR_CATEGORY+"crafting.png",
			# 10 : IMG_DIR_CATEGORY+"crafting.png",
		},
	}
	categoryName = argument[0].lower() if not localeInfo.IsARABIC() else argument[0]
	if categoryName in imgDict:
		if int(argument[1]) in imgDict[categoryName]:
			return imgDict[categoryName][int(argument[1])]
	return ""

def price_to_k(price):
	return str(price)[::-1].replace("000", "k")[::-1]
def format_number(num):
	suffixes = {3 : 'K', 6: 'M', 9: 'B', 12: 'T', 15: 'Q'}
	num = float(num)
	sign = ''
	if num < 0:
		sign = '-'
		num = abs(num)
	if num == 0:
		return '0'
	digits = int(math.log10(num))
	if digits < 3:
		return sign + str(int(num))
	else:
		suffix = suffixes.get(digits, '')
		formatted_num = str(round(num / 10**(digits - 3), 1))
		return sign + formatted_num + suffix

def IsArticleCategory(argument):
	categoryName = argument[0].lower() if not localeInfo.IsARABIC() else argument[0]
	if categoryName == "system" or categoryName == "dungeon" or categoryName == "guide" or categoryName == "events":
		return True
	return False

def GetMapNameWithIndex(mapIndex):
	_dict = {
		41 : localeInfo.MAP_C1,
		1 : localeInfo.MAP_A1,
		21 : localeInfo.MAP_B1,
		3 : localeInfo.MAP_A3,
		23 : localeInfo.MAP_B3,
		43 : localeInfo.MAP_C3,
		64 : localeInfo.MAP_N_THREEWAY,
		63 : localeInfo.MAP_DESERT,
		65 : localeInfo.MAP_TEMPLE,
		61 : localeInfo.MOUNT_SOHAN_MAP_NAME,
		62 : localeInfo.MOUNT_DOYUMHWAN_MAP_NAME,
		67 : localeInfo.MAP_TRENT,
		68 : localeInfo.MAP_TRENT02,
		302 : localeInfo.MAP_DAWNMISTWOOD,
		304 : localeInfo.MAP_MT_THUNDER,
		303 : localeInfo.MAP_BAYBLACKSAND,
		301 : localeInfo.MAP_CAPEDRAGONHEAD,
		356 : localeInfo.MAP_DAWNMIST_DUNGEON_01,
		357 : "Pul-ui Hwangyeong",
		71 : localeInfo.MAP_SKIPIA_DUNGEON_BOSS_1,
		73 : localeInfo.MAP_SKIPIA_DUNGEON_01,
		365 : nonplayer.GetMonsterName(2092),
		354 : nonplayer.GetMonsterName(693),
		66 : localeInfo.MAP_DEVILTOWER1,
		216 : localeInfo.MAP_DEVILCATACOMB,
		208 : nonplayer.GetMonsterName(2493),
		352 : localeInfo.MAP_N_SNOW_DUNGEON_01,
		351 : localeInfo.MAP_N_FLAME_DUNGEON_01,
		364 : localeInfo.MAP_DAWNMIST_DUNGEON_01,
		358 : localeInfo.MAP_DEFENSE_WAVE,
		361 : localeInfo.MAP_N_FLAME_DRAGON,
		363 : nonplayer.GetMonsterName(6500),
		362 : nonplayer.GetMonsterName(6501),
		366 : localeInfo.MAP_CZ_DUNGEON,
	}
	return _dict[mapIndex] if mapIndex in _dict else ""
def GetOriginMapName(mobIndex):
	# Spawn maps come from the server regen files (servergamedata.MOB_MAPS,
	# generated by tools/build_server_game_data.py); dungeon instances are omitted.
	_ListofMaps = []
	for mapIndex in servergamedata.MOB_MAPS.get(mobIndex, ()):
		mapName = GetMapNameWithIndex(mapIndex)
		if mapName and mapName not in _ListofMaps:
			_ListofMaps.append(mapName)
	return _ListofMaps if len(_ListofMaps) > 1 else (_ListofMaps[0] if len(_ListofMaps) > 0 else "")

def _ServerDropWays():
	# Every entry below is generated from the server authorities: the C++
	# ordinary-monster loot table, mission books by map, NPC shops (ShopEx and
	# SQL) and cube recipes. Stone and boss drops come from mob_drop_item.txt.
	monster = getattr(localeInfo, "WIKI_MONSTER", "Monsters")
	shop = uiScriptLocale.SHOP_TITLE
	craft = getattr(localeInfo, "WIKI_CRAFT", "Craftings")
	ways = [(monster + " (Lv. -%d)" % servergamedata.ORDINARY_MONSTER_LEVEL_GAP, servergamedata.ORDINARY_MONSTER_LOOT)]
	for bookVnum, mapIndexes in servergamedata.ORDINARY_MONSTER_BOOKS.items():
		mapNames = [name for name in [GetMapNameWithIndex(index) for index in mapIndexes] if name]
		ways.append((monster + (" - " + ", ".join(mapNames) if mapNames else ""), (bookVnum,)))
	for npcVnum, itemVnums in servergamedata.SHOP_ITEMS.items():
		ways.append((shop + " " + nonplayer.GetMonsterName(npcVnum), itemVnums))
	for npcVnum, itemVnums in servergamedata.CRAFT_RESULTS.items():
		ways.append((craft + " " + nonplayer.GetMonsterName(npcVnum), itemVnums))
	return ways

def GetSpecialDropWays(itemVnum, refineVnum):
	# Sources that are not server data files stay listed by hand.
	_dict = {
			uiScriptLocale.ITEM_MALL : [503001, 503002, 503003, 503004, 503005, 503006, 503007, 503008, 503009, 503010, 503011, 503012, 502001, 502002, 502003, 502004, 502005, 502006, 502007, 502008, 502009, 502010, 502011, 502012],
			localeInfo.MISSION_BOOKS : [951070, 951071, 951072, 951078],
			localeInfo.CZ_REWARD_TOOLTIP_10GAN : [33028],
			localeInfo.WHEEL_GAME_TITLE : [401012, 402020, 402021, 402019, 403017, 403018, 403019],
			localeInfo.GUILD_DRAGONLAIR_PARTY_TOOLTIP_TITLE : [504004, 504003, 504010, 504009, 504006, 504005, 504002, 504001, 504008, 504007],
			localeInfo.BATTLE_PASS : [505001, 505002, 505003, 505004, 505005, 505006, 505007, 505008, 505009, 505010, 505011, 505012, 505013, 505014, 503001, 503002, 503003, 503004, 503005, 503006, 503007, 503008, 503009, 503010, 503011, 503012],
		}
	_returnList=[]
	for key, data in list(_dict.items()) + _ServerDropWays():
		for itemIndex in data:
			if (itemIndex == itemVnum or (refineVnum and itemIndex >= itemVnum and itemIndex <= itemVnum+refineVnum)):
				if key not in _returnList:
					_returnList.append(key)
				break
	return _returnList

if app.ENABLE_ITEMSHOP:
	def GetItemShopData(itemVnum, refineVnum):
		itemshopDict = uiItemShop.itemshopData
		LIST_ITEM_VNUM = uiItemShop.LIST_ITEM_VNUM
		_ListOfItemShops = []
		for categoryIndex, categoryData in itemshopDict.items():
			for subCategory in categoryData:
				for itemData in subCategory:
					shopItemIndex = itemData[LIST_ITEM_VNUM]
					(shopItemIndexRefine, isRefineShopItem) = getRealVnum(shopItemIndex)
					if (itemVnum == shopItemIndex or (refineVnum and isRefineShopItem and itemVnum == shopItemIndexRefine)):
						itemShopCategoryData = uiItemShop.itemShopCategoryData[categoryIndex]
						categoryName = itemShopCategoryData["name"] if len(itemShopCategoryData["subCategory"]) == 0 else (localeInfo.WIKI_ITEMSHOP_DROP % (itemShopCategoryData["name"], itemShopCategoryData["subCategory"][categoryData.index(subCategory)]))
						_ListOfItemShops.append(categoryName)
		return _ListOfItemShops

# WikiRenderTarget Method:

def CanEquipItem(raceIndex):
	ANTI_FLAG_DICT = {
		0 : item.ITEM_ANTIFLAG_WARRIOR,
		1 : item.ITEM_ANTIFLAG_ASSASSIN,
		2 : item.ITEM_ANTIFLAG_SURA,
		3 : item.ITEM_ANTIFLAG_SHAMAN,
	}
	job = chr.RaceToJob(raceIndex)
	sex = chr.RaceToSex(raceIndex)
	MALE = 1
	FEMALE = 0
	if item.IsAntiFlag(ANTI_FLAG_DICT[job]):
		return 1
	elif item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE) and sex == MALE:
		return 2
	elif item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE) and sex == FEMALE:
		return 2
	return 0
def GetOtherSexRace(race):
	otherSexMapping = {
		playersettingmodule.RACE_WARRIOR_W : playersettingmodule.RACE_WARRIOR_M,
		playersettingmodule.RACE_ASSASSIN_W : playersettingmodule.RACE_ASSASSIN_M,
		playersettingmodule.RACE_SHAMAN_W :	playersettingmodule.RACE_SHAMAN_M,
		playersettingmodule.RACE_SURA_W :	playersettingmodule.RACE_SURA_M,
		playersettingmodule.RACE_WARRIOR_M :	playersettingmodule.RACE_WARRIOR_W,
		playersettingmodule.RACE_ASSASSIN_M :	playersettingmodule.RACE_ASSASSIN_W,
		playersettingmodule.RACE_SHAMAN_M :	playersettingmodule.RACE_SHAMAN_W,
		playersettingmodule.RACE_SURA_M : playersettingmodule.RACE_SURA_W,
	}
	return otherSexMapping[race]
def GetValidRace(raceIndex = 0):
	can_equip = CanEquipItem(raceIndex)
	race = raceIndex
	sex = chr.RaceToSex(race)
	MALE = 1
	FEMALE = 0
	if can_equip == 0:
		return race
	elif can_equip == 1:
		if item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_WEAPON:
			raceDict = {
				0 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M, ],
				1 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				2 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				3 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M, ],
				4 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
				5 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
			}
			item_type = item.GetValue(3)
			return raceDict[item_type][sex]
		else:
			raceDict = {
				0 :	[ playersettingmodule.RACE_WARRIOR_W, playersettingmodule.RACE_WARRIOR_M ],
				1 :	[ playersettingmodule.RACE_ASSASSIN_W, playersettingmodule.RACE_ASSASSIN_M ],
				2 :	[ playersettingmodule.RACE_SURA_W, playersettingmodule.RACE_SURA_M ],
				3 :	[ playersettingmodule.RACE_SHAMAN_W, playersettingmodule.RACE_SHAMAN_M ],
			}
			flags = []
			ANTI_FLAG_DICT = {
				0 : item.ITEM_ANTIFLAG_WARRIOR,
				1 : item.ITEM_ANTIFLAG_ASSASSIN,
				2 : item.ITEM_ANTIFLAG_SURA,
				3 : item.ITEM_ANTIFLAG_SHAMAN,
			}
			for i in range(len(ANTI_FLAG_DICT)):
				if not item.IsAntiFlag(ANTI_FLAG_DICT[i]):
					flags.append(i)
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
				sex = FEMALE
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
				sex = MALE
			return raceDict[flags[0]][sex] if len(flags) == 1 else 0
	elif can_equip == 2:
		return GetOtherSexRace(race)

def IsCanModelPreview(itemVnum):
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	itemSubType = item.GetItemSubType()
	if itemType == item.ITEM_TYPE_WEAPON and itemSubType != item.WEAPON_ARROW:
		return True
	elif itemType == item.ITEM_TYPE_ARMOR and itemSubType == item.ARMOR_BODY:
		return True
	elif itemType == item.ITEM_TYPE_COSTUME and (itemSubType == item.COSTUME_TYPE_WEAPON or itemSubType == item.COSTUME_TYPE_BODY or itemSubType == item.COSTUME_TYPE_HAIR or itemSubType == item.COSTUME_TYPE_MOUNT or itemSubType == item.COSTUME_TYPE_PET or itemSubType == item.COSTUME_TYPE_ACCE or itemSubType == item.COSTUME_TYPE_ACCE_SKIN):
		return True
	return False

HAIRSTYLE_CAMERA_CFG = {
	playersettingmodule.RACE_WARRIOR_M : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 152.3934]),
	playersettingmodule.RACE_ASSASSIN_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_SURA_M : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 172.1804]),
	playersettingmodule.RACE_SHAMAN_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_WARRIOR_W : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 147.3934]),
	playersettingmodule.RACE_ASSASSIN_M : ([344.2622, -16.3934, 150.0000], [0.0000, 0.0000, 156.7869]),
	playersettingmodule.RACE_SURA_W : ([311.4753, -16.3934, 150.0000], [0.0000, 0.0000, 156.7869]),
	playersettingmodule.RACE_SHAMAN_M : ([377.0492, -16.3934, 150.0000], [0.0000, 0.0000, 163.7869])
}
def GetCharTypeHairCamera(char_type):
	if not char_type in HAIRSTYLE_CAMERA_CFG:
		return tuple([], [])
	return HAIRSTYLE_CAMERA_CFG[char_type]
def SetItemToModelPreview(modelIndex, itemVnum):
	item.SelectItem(itemVnum)
	itemType = item.GetItemType()
	itemSubType = item.GetItemSubType()

	if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_MOUNT:
		WikiRenderTarget.SelectModel(modelIndex, item.GetValue(1))
		WikiRenderTarget.SetVisibility(modelIndex, True)
		WikiRenderTarget.SetArmor(modelIndex, 0)
	elif itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_PET:
		WikiRenderTarget.SelectModel(modelIndex, item.GetValue(0))
		WikiRenderTarget.SetVisibility(modelIndex, True)
		WikiRenderTarget.SetArmor(modelIndex, 0)
	elif itemType == item.ITEM_TYPE_PET and itemSubType == item.PET_UPBRINGING:
		WikiRenderTarget.SelectModel(modelIndex, item.GetValue(0))
		WikiRenderTarget.SetVisibility(modelIndex, True)
		WikiRenderTarget.SetArmor(modelIndex, 0)
	else:
		raceIndex = GetValidRace(app.GetRandom(0,4))
		WikiRenderTarget.SelectModel(modelIndex, raceIndex)
		WikiRenderTarget.SetVisibility(modelIndex, True)
		if itemType == item.ITEM_TYPE_WEAPON:
			WikiRenderTarget.SetArmor(modelIndex, 11299)
			WikiRenderTarget.SetWeapon(modelIndex, itemVnum)
		elif itemType == item.ITEM_TYPE_ARMOR:
			WikiRenderTarget.SetArmor(modelIndex, itemVnum)
		elif itemType == item.ITEM_TYPE_COSTUME:
			if itemSubType == item.COSTUME_TYPE_WEAPON:
				WikiRenderTarget.SetArmor(modelIndex, 11299)
				WikiRenderTarget.SetWeapon(modelIndex,itemVnum)
			elif itemSubType == item.COSTUME_TYPE_BODY:
				WikiRenderTarget.SetArmor(modelIndex, itemVnum)
			elif itemSubType == item.COSTUME_TYPE_ACCE or itemSubType == item.COSTUME_TYPE_ACCE_SKIN:
				WikiRenderTarget.SetArmor(modelIndex, 11299)
				WikiRenderTarget.SetAcce(modelIndex, itemVnum - 85000)
			elif itemSubType == item.COSTUME_TYPE_HAIR:
				WikiRenderTarget.SetArmor(modelIndex, 11299)
				WikiRenderTarget.SetHair(modelIndex,itemVnum)
				(V3Eye, V3Target) = GetCharTypeHairCamera(raceIndex)
				if len(V3Eye) and len(V3Target):
					WikiRenderTarget.SetModelV3Eye(modelIndex, *V3Eye)
					WikiRenderTarget.SetModelV3Target(modelIndex, *V3Target)

# multi lang in scripts
def GetArgToString(buf):
	bufSplit = buf.split(" ")
	new_text=buf
	if len(bufSplit) >= 0:
		new_arg= ""
		for j in range(len(bufSplit)):
			new_arg+= "%s&"% str(bufSplit[j])
		try:
			text = MakeStringToList(new_arg[:len(new_arg)-1], new_text)
			new_text = text
		except:
			return new_text
	return new_text
def MakeStringToList(args, buf):
	new_buf = buf
	arg_list = args.split("&")
	for text in arg_list:
		if len(text) < 2:
			continue
		itemLink = text.find("I")
		if itemLink>=0:
			if text[itemLink+1].isdigit() == True:
				item.SelectItem(int(text[1:]))
				new_buf = new_buf.replace(text, item.GetItemName())
				continue
		mobLink = text.find("M")
		if mobLink>= 0:
			if text[mobLink+1].isdigit() == True:
				mobName = nonplayer.GetMonsterName(int(text[1:]))
				new_buf = new_buf.replace(text, "None" if not mobName or mobName == "" else mobName)
				continue
		skillLink = text.find("S")
		if skillLink >=0:
			if text[skillLink+1].isdigit() == True:
				skillName = skill.GetSkillName(int(text[1:]))
				new_buf = new_buf.replace(text, "None" if not skillName or skillName == "" else skillName)
				continue
		goldLink = text.find("Y")
		if goldLink >=0:
			if text[goldLink+1].isdigit() == True:
				new_buf = new_buf.replace(text, localeInfo.MoneyFormat(int(text[1:])))
				continue
	return new_buf

# constant function

class CategoryDefaultItem(ui.WikiWindow):
	def __del__(self):
		ui.WikiWindow.__del__(self)
	def Destroy(self):
		self.children={}
		self.offset = 0
		self.expanded = False
		self.event = None
		self.onCollapseEvent = None
		self.onExpandEvent = None
		self.parent = 0
		self.overLine = False
		self.itemList=[]
	def __init__(self):
		ui.WikiWindow.__init__(self)
		self.Destroy()
	def SetParent(self, parent):
		ui.WikiWindow.SetParent(self, parent)
		self.parent=_weakref.proxy(parent)
	def IsExpanded(self):
		return self.expanded
	def Expand(self):
		self.expanded = True
		if self.onExpandEvent:
			self.onExpandEvent()
	def Collapse(self):
		self.expanded = False
		if self.onCollapseEvent:
			self.onCollapseEvent()
	def SetOnExpandEvent(self, event):
		self.onExpandEvent = event
	def SetOnCollapseEvent(self, event):
		self.onCollapseEvent = event
	def SetEvent(self, event):
		self.event = event
	def SetOffset(self, offset):
		self.offset = offset
	def GetOffset(self):
		return self.offset
	def OnSelect(self):
		if self.event:
			self.event()
		self.parent.SelectItem(self)
	def OnMouseLeftButtonDown(self):
		self.OnSelect()

class CategoryList(ui.WikiWindow):
	class CategoryItem(CategoryDefaultItem):
		def __del__(self):
			CategoryDefaultItem.__del__(self)
		def __init__(self, text):
			CategoryDefaultItem.__init__(self)
			directionIcon = ui.ExpandedImageBoxWiki()
			directionIcon.SetParent(self)
			directionIcon.AddFlag("not_pick")
			directionIcon.SetPosition(0,0)
			directionIcon.LoadImage(IMG_DIR +"buttons/btn_category_0.png")
			directionIcon.Show()
			self.children["directionIcon"] = directionIcon
			textLine=ui.TextLine()
			textLine.SetParent(directionIcon)
			textLine.AddFlag("not_pick")
			textLine.SetText(text)
			textLine.SetPosition(2, 1)
			textLine.Show()
			self.children["textLine"] = textLine
			self.SetOnExpandEvent(self.ExpandEvent)
			self.SetOnCollapseEvent(self.CollapseEvent)
			self.SetSize(115,20)
		def CollapseEvent(self):
			self.children["directionIcon"].LoadImage(IMG_DIR +"buttons/btn_category_0.png")
			self.children["directionIcon"].Show()
		def ExpandEvent(self):
			self.children["directionIcon"].LoadImage(IMG_DIR +"buttons/btn_category_active_2.png")
			self.children["directionIcon"].Show()

	class CategorySubItem(CategoryDefaultItem):
		def __del__(self):
			CategoryDefaultItem.__del__(self)
		def __init__(self, text):
			CategoryDefaultItem.__init__(self)
			textLine=ui.TextLine()
			textLine.SetParent(self)
			textLine.AddFlag("not_pick")
			textLine.SetFontName(localeInfo.UI_DEF_FONT)
			textLine.SetText(text)
			textLine.SetPosition(3, 0)
			textLine.Show()
			self.children["textLine"] = textLine
			self.SetSize(114,16)

		def OnMouseOverIn(self):
			self.overLine = True
		def OnMouseOverOut(self):
			self.overLine = False
		def OnRender(self):
			parent = self.parent
			if self.overLine and parent.GetSelectedItem() != self:
				grp.SetColor(grp.GenerateColor(0.188,0.369,0.333,0.6))
			elif parent.GetSelectedItem() == self:
				grp.SetColor(grp.GenerateColor(0.380,0.325,0.188, 0.6))
			else:
				grp.SetColor(grp.GenerateColor(0.086, 0.153 ,0.137 , 0.6))

			(_x, _y) = self.GetGlobalPosition()
			(_wx, _wy) = parent.GetGlobalPosition()
			if _y < _wy+5:
				grp.RenderBar(_x, _y+(_wy-_y), self.GetWidth(), self.GetHeight()-(_wy-_y))
			elif _y+self.GetHeight() > _wy+parent.GetHeight():
				grp.RenderBar(_x, _y, self.GetWidth(), self.GetHeight()-((_y+self.GetHeight())-abs(_wy+parent.GetHeight())))
			else:
				grp.RenderBar(_x, _y, self.GetWidth(), self.GetHeight())

		def OnMouseLeftButtonDown(self):
			if self.parent.GetSelectedItem() == self:
				return
			CategoryDefaultItem.OnMouseLeftButtonDown(self)

	def __del__(self):
		ui.WikiWindow.__del__(self)
	def Destroy(self):
		self.scrollBar=None
		self.selectedItem = None
		self.itemList = []
	def __init__(self):
		ui.WikiWindow.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.RefreshList))
		self.scrollBar=_weakref.proxy(scrollBar)

	def OnMouseWheel(self, length):
		return self.scrollBar.OnMouseWheel(length) if self.scrollBar else False

	def GetSelectedItem(self):
		return self.selectedItem
	def Reset(self):
		if self.selectedItem:
			self.selectedItem.Collapse()
			self.selectedItem=None

	def SelectItem(self, selectedItem):
		self.selectedItem = selectedItem
		if selectedItem != None:
			try:
				if selectedItem.IsExpanded():
					selectedItem.Collapse()
				else:
					selectedItem.Expand()
			except:
				return
		self.RefreshList()

	def SetBasePos(self, basePos):
		self.basePos=basePos
		self.RefreshList()

	def ClearItem(self):
		self.selectedItem=None
		for categoryData in self.itemList:
			categoryList = categoryData.itemList
			for category in categoryList:
				category.Hide()
				category.Destroy()
			categoryList = []
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
		self.SetBasePos(0)

	def AppendItemList(self, categoryData):
		self.ClearItem()
		for categoryList in categoryData:
			categoryBtn = None
			if "item" in categoryList:
				categoryBtn = categoryList["item"]
				categoryBtn.SetParent(self)
				if "children" in categoryList:
					for _x in categoryList["children"]:
						childItems = _x["item"]
						childItems.SetParent(self)
						categoryBtn.itemList.append(childItems)
						if "children" in _x:
							for _z in _x["children"]:
								childItemsLast = _z["item"]
								childItemsLast.SetParent(self)
								childItems.itemList.append(childItemsLast)
			if categoryBtn != None:
				self.itemList.append(categoryBtn)
		self.RefreshList()

	def RefreshDynamicPosition(self):
		y_pos = 0
		for categoryBtn in self.itemList:
			categoryBtn.SetPosition(categoryBtn.GetOffset(), y_pos, True)
			y_pos +=categoryBtn.GetHeight()+1
			if categoryBtn.IsExpanded():
				for childItem in categoryBtn.itemList:
					childItem.SetPosition(childItem.GetOffset(), y_pos, True)
					childItem.Show()
					y_pos +=childItem.GetHeight()+1
					if childItem.IsExpanded():
						for childItemLast in childItem.itemList:
							childItemLast.SetPosition(childItemLast.GetOffset(), y_pos, True)
							childItemLast.Show()
							y_pos +=childItemLast.GetHeight()+1
		return y_pos

	def RefreshList(self):
		(screenSize, windowHeight) = (self.RefreshDynamicPosition(), self.GetHeight())
		basePos = 0
		scrollBar = self.scrollBar
		if screenSize > windowHeight and scrollBar != None:
			basePos = int(scrollBar.GetPos()*(screenSize-windowHeight))
			scrollBar.SetScale(windowHeight, screenSize)
			scrollBar.Show()
			if scrollBar.middleBar.GetGlobalPosition()[1]+scrollBar.middleBar.GetHeight()-15 >= scrollBar.GetGlobalPosition()[1]+scrollBar.GetHeight():
				scrollBar.SetPos(0)
				self.SetBasePos(0)
				return
		else:
			self.scrollBar.Hide()
		y_pos = 0
		for categoryBtn in self.itemList:
			categoryBtn.SetPosition(categoryBtn.GetOffset(), categoryBtn.exPos[1]-basePos)
			categoryBtn.Show()
			if categoryBtn.IsExpanded():
				for childItem in categoryBtn.itemList:
					childItem.SetPosition(childItem.GetOffset(), childItem.exPos[1]-basePos)
					childItem.Show()
					if childItem.IsExpanded():
						for childItemLast in childItem.itemList:
							childItemLast.SetPosition(childItemLast.GetOffset(), childItemLast.exPos[1]-basePos)
							childItemLast.Show()
					else:
						for childItemLast in childItem.itemList:
							childItemLast.Hide()
			else:
				for childItem in categoryBtn.itemList:
					childItem.Hide()
					for childItemLast in childItem.itemList:
						childItemLast.Hide()

class DefaultWikiWindow(ui.WikiWindow):
	IsLoaded=False
	renderIndex=-1
	sortIndex=0
	isType=0
	_children={}
	def __init__(self):
		ui.WikiWindow.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)
	def Destroy(self):
		Listbox = self._children["Listbox"] if "Listbox" in self._children else None
		if Listbox:
			Listbox.RemoveAllItems()
			Listbox.Destroy()
			self._children["Listbox"] = None
		ListboxOrigin = self._children["ListboxOrigin"] if "ListboxOrigin" in self._children else None
		if ListboxOrigin:
			ListboxOrigin.RemoveAllItems()
			ListboxOrigin.Destroy()
			self._children["ListboxOrigin"] = None
		self._children={}
		self.isType = 0
		self.sortIndex=0
		self.renderIndex=-1
		self.IsLoaded = False
	def OnClickItem(self, arg, type, vnum):
		self.OverOutItem()

		parent = osfInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(vnum,type)

	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInItem(self, itemVnum, metinSlot=[], attrSlot=[]):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				if not len(metinSlot):
					metinSlot = [0 for j in range(player.METIN_SOCKET_MAX_NUM)]
				if not len(attrSlot):
					attrSlot = [(0,0) for j in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)

class DefaultWikiImage(ui.ExpandedImageBoxWiki):
	isType=0
	sortIndex=0
	renderIndex=-1
	_children={}
	IsLoaded=False
	def __init__(self):
		ui.ExpandedImageBoxWiki.__init__(self)
		self.Destroy()
		self.SetInsideRender(True)

	def Destroy(self):
		Listbox = self._children["Listbox"] if "Listbox" in self._children else None
		if Listbox:
			Listbox.RemoveAllItems()
			Listbox.Destroy()
			self._children["Listbox"] = None
		ListboxOrigin = self._children["ListboxOrigin"] if "ListboxOrigin" in self._children else None
		if ListboxOrigin:
			ListboxOrigin.RemoveAllItems()
			ListboxOrigin.Destroy()
			self._children["ListboxOrigin"] = None
		self._children={}
		self.isType = 0
		self.sortIndex=0
		self.renderIndex=-1
		self.IsLoaded = False
	def OnClickItem(self, arg, type, vnum):
		self.OverOutItem()
		parent = osfInfo.GetWikiInterface()
		if parent != None:
			parent.ShowItemInfo(vnum,type)

	def OverOutItem(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.HideToolTip()
	def OverInItem(self, itemVnum, metinSlot=[],attrSlot=[]):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				if not len(metinSlot):
					metinSlot = [0 for j in range(player.METIN_SOCKET_MAX_NUM)]
				if not len(attrSlot):
					attrSlot = [(0, 0) for j in range(player.ATTRIBUTE_SLOT_MAX_NUM)]
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AddItemData(itemVnum, metinSlot, attrSlot)

class ListBoxEx(ui.WikiWindow):
	def __init__(self, isHorizontal=False):
		ui.WikiWindow.__init__(self)
		self.viewItemCount=10
		self.basePos=0
		self.itemHeight=16
		self.itemStep=20
		self.selItem=0
		self.itemList=[]
		self.onSelectItemEvent = lambda *arg: None
		self.itemWidth=100
		self.isHorizontal=isHorizontal
		self.scrollBar=None
		self.__UpdateSize()
	def __del__(self):
		ui.WikiWindow.__del__(self)
	def __UpdateSize(self):
		if self.isHorizontal:
			width = self.itemStep * self.__GetViewItemCount()
			self.SetSize(width, self.itemHeight)
		else:
			height = self.itemStep * self.__GetViewItemCount()
			self.SetSize(self.itemWidth, height)
	def IsEmpty(self):
		if len(self.itemList)==0:
			return 1
		return 0
	def SetItemStep(self, itemStep):
		self.itemStep=itemStep
		self.__UpdateSize()
	def SetItemSize(self, itemWidth, itemHeight):
		self.itemWidth=itemWidth
		self.itemHeight=itemHeight
		self.__UpdateSize()
	def SetViewItemCount(self, viewItemCount):
		self.viewItemCount=viewItemCount
	def SetSelectEvent(self, event):
		self.onSelectItemEvent = event
	def SAFE_SetSelectEvent(self, event):
		self.selectEvent=ui.__mem_func__(event)
	def SetBasePos(self, basePos):
		for oldItem in self.itemList[self.basePos:self.basePos+self.viewItemCount]:
			oldItem.Hide()
		self.basePos=basePos
		pos=basePos
		for newItem in self.itemList[self.basePos:self.basePos+self.viewItemCount]:
			(x, y)=self.GetItemViewCoord(pos, newItem.GetWidth())
			newItem.SetPosition(x, y)
			newItem.Show()
			pos+=1
	def GetItemIndex(self, argItem):
		return self.itemList.index(argItem)
	def GetSelectedItem(self):
		return self.selItem
	def SelectIndex(self, index):
		if index >= len(self.itemList) or index < 0:
			self.selItem = None
			return
		try:
			self.selItem=self.itemList[index]
		except:
			pass
	def SelectItem(self, selItem):
		self.selItem=selItem
		self.onSelectItemEvent(selItem)
	def RemoveAllItems(self):
		self.selItem=None
		for item in self.itemList:
			item.Hide()
			item.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
	def GetItems(self):
		return self.itemList
	def RemoveItem(self, delItem):
		if delItem==self.selItem:
			self.selItem=None
		self.itemList.remove(delItem)
	def AppendItem(self, newItem):
		newItem.SetParent(self)
		newItem.SetSize(self.itemWidth, self.itemHeight)
		self.itemList.append(newItem)
	def AppendItemWithIndex(self, index, newItem):
		newItem.SetParent(self)
		newItem.SetSize(self.itemWidth, self.itemHeight)
		self.itemList.insert(index,newItem)
		self.__OnScroll()
	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar=scrollBar

	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False

	def __OnScroll(self):
		self.SetBasePos(int(self.scrollBar.GetPos()*self.__GetScrollLen()))
	def __GetScrollLen(self):
		scrollLen=self.__GetItemCount()-self.__GetViewItemCount()
		if scrollLen<0:
			return 0
		return scrollLen
	def __GetViewItemCount(self):
		return self.viewItemCount
	def __GetItemCount(self):
		return len(self.itemList)
	def GetItemViewCoord(self, pos, itemWidth):
		if self.isHorizontal:
			return ((pos - self.basePos) * self.itemStep, 0)
		return (0, (pos - self.basePos) * self.itemStep)
	def __IsInViewRange(self, pos):
		if pos<self.basePos:
			return 0
		if pos>=self.basePos+self.viewItemCount:
			return 0
		return 1

class AutoLoad(object):
	def __init__(self):
		self.flagDict={}

	def __del__(self):
		self.flagDict={}

	def SetFlag(self, flag, value):
		self.flagDict[flag] = value

	def GetFlag(self, flag):
		return self.flagDict[flag] if flag in self.flagDict else 0

class ListBoxGrid(ui.WikiWindow):
	def __init__(self, isHorizontal= False):
		ui.WikiWindow.__init__(self)
		self.Destroy()
		self.isHorizontal=isHorizontal
		self.SetInsideRender(True)
		self.nameList = []
	def __del__(self):
		ui.WikiWindow.__del__(self)
	def Destroy(self):
		self.scrollLen=0
		self.basePos=0
		self.itemList=[]
		self.func=None
		self.scrollBar=None
		self.isHorizontal=False
	def RemoveAllItems(self):
		for items in self.itemList:
			items.Hide()
			items.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
	def GetItems(self):
		return self.itemList
	def RemoveItem(self, delItem):
		self.itemList.remove(delItem)
	def AppendItem(self, newItem):
		self.itemList.append(newItem)
		self.CalculateScroll()

	def SetNameList(self, name):
		self.nameList = name

	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar=scrollBar
		self.CalculateScroll()

	def OnScroll(self):
		if self.scrollBar:
			self.SetBasePos(int(self.scrollBar.GetPos()*self.__GetScrollLen()))
			if player.GetName().find("[") != -1 or player.GetName()=="Hex":
				chat.AppendChat(1, "article scroll pos: %.2f"%self.scrollBar.GetPos())

	def AddRenderEvent(self, func):
		self.func = ui.__mem_func__(func)

	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False

	def isNeedScrollBar(self):
		if self.scrollBar:
			return False
		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight()) > screenSize:
				screenSize = child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight())
		return screenSize > self.GetHeight()+10

	def CalculateScroll(self):
		scrollBar = self.scrollBar
		if len(self.itemList) == 0:
			if scrollBar:
				scrollBar.Hide()
			return
		if scrollBar == None:
			return
		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight()) > screenSize:
				screenSize = child.exPos[1]+(child.GetTextSize()[1] if isinstance(child, ui.TextLine) else child.GetHeight())
		windowHeight = self.GetHeight()
		scrollLen = 0
		if screenSize > windowHeight:
			scrollLen = screenSize-windowHeight
			scrollBar.SetScale(windowHeight, screenSize)
			scrollBar.Show()
			if scrollBar.middleBar.GetGlobalPosition()[1]+scrollBar.middleBar.GetHeight()-15 >= scrollBar.GetGlobalPosition()[1]+scrollBar.GetHeight():
				scrollBar.SetPos(0)
		else:
			scrollBar.Hide()
		self.scrollLen = scrollLen
	def __GetScrollLen(self):
		return self.scrollLen
	def SetBasePos(self, basePos, isAutomatic = True):
		if self.basePos == basePos and isAutomatic == True:
			return
		for items in self.itemList:
			(ex,ey) = items.exPos
			if self.isHorizontal:
				items.SetPosition(ex-(basePos),ey)
			else:
				items.SetPosition(ex,ey-(basePos))
		if self.func != None:
			self.func()
		self.basePos=basePos

	def OnMouseOverOut(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()

	def OnMouseOverIn(self):
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.ClearToolTip()
				if not self.nameList:
					return

				if isinstance(self.nameList, list):
					for originName in self.nameList:
						interface.tooltipItem.AppendTextLine(originName)
				else:
					interface.tooltipItem.AppendTextLine(self.nameList)
				interface.tooltipItem.ShowToolTip()

class TextlineLink(ui.WikiWindow):
	def Destroy(self):
		self.TextLine=None
		self.linkIcon=None
	def __init__(self):
		ui.WikiWindow.__init__(self)
		self.TextLine = CreateWindow(ui.TextLine(), self, (0, 0))
		self.linkIcon = CreateWindow(ui.ExpandedImageBoxWiki(), self, (0, 2), "d:/ymir work/ui/link_icon.tga")
	def SetText(self, text, scale):
		self.TextLine.SetText(text)
		(width, height) = self.TextLine.GetTextSize()
		newScale = float(height)/14.0
		self.linkIcon.SetScale(newScale, newScale)
		self.TextLine.SetPosition(self.linkIcon.GetWidth() + 3, 0)
		self.SetSize(self.linkIcon.GetWidth() + 3 + self.TextLine.GetTextSize()[0], height)
	def GetText(self):
		return self.TextLine.GetText()
	def GetTextSize(self):
		return self.TextLine.GetTextSize()
	def SetPackedFontColor(self, hex):
		self.TextLine.SetPackedFontColor(hex)
	def SetColor(self, hex, r, g, b):
		self.linkIcon.SetDiffuseColor(r, g, b, 1.0)
		self.TextLine.SetPackedFontColor(hex)
	def SetFontName(self, fontname):
		self.TextLine.SetFontName(fontname)

def getRealVnum(vnum):
	isRefineItem = False
	item.SelectItem(vnum)
	if item.ITEM_TYPE_METIN == item.GetItemType():
		return (vnum, False)

	isRefineItem = False

	level = "0"
	itemname = item.GetItemName()
	pos = itemname.find("+")
	#if pos != -1 and item.ITEM_TYPE_METIN != item.GetItemType():
	if pos != -1 and pos+1 < len(itemname):
		level = itemname[pos+1:]
		if level.isdigit():
			isRefineItem = True
			vnum -= int(level) if item.ITEM_TYPE_METIN != item.GetItemType() else int(level) * 100
	return (vnum, isRefineItem)

def ClickRadioButton(buttonList, buttonIndex):
	try:
		btn=buttonList[buttonIndex]
	except IndexError:
		return
	for eachButton in buttonList:
		eachButton.SetUp()
	btn.Down()

def CreateWindow(window, parent, windowPos, windowArgument = "", windowPositionRule = "", windowSize = (-1, -1), windowFontName = -1):
	window.SetParent(parent)
	window.SetPosition(*windowPos)
	if windowSize != (-1, -1):
		window.SetSize(*windowSize)
	if windowPositionRule:
		splitList = windowPositionRule.split(":")
		if len(splitList) == 2:
			(type, mode) = (splitList[0], splitList[1])
			if type == "all":
				window.SetHorizontalAlignCenter()
				window.SetVerticalAlignCenter()
				window.SetWindowHorizontalAlignCenter()
				window.SetWindowVerticalAlignCenter()
			elif type == "horizontal":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetHorizontalAlignCenter()
					elif mode == "right":
						window.SetHorizontalAlignRight()
					elif mode == "left":
						window.SetHorizontalAlignLeft()
				else:
					if mode == "center":
						window.SetWindowHorizontalAlignCenter()
					elif mode == "right":
						window.SetWindowHorizontalAlignRight()
					elif mode == "left":
						window.SetWindowHorizontalAlignLeft()
			elif type == "vertical":
				if isinstance(window, ui.TextLine):
					if mode == "center":
						window.SetVerticalAlignCenter()
					elif mode == "top":
						window.SetVerticalAlignTop()
					elif mode == "bottom":
						window.SetVerticalAlignBottom()
				else:
					if mode == "top":
						window.SetWindowVerticalAlignTop()
					elif mode == "center":
						window.SetWindowVerticalAlignCenter()
					elif mode == "bottom":
						window.SetWindowVerticalAlignBottom()
	if windowArgument:
		if isinstance(window, ui.TextLine):
			if windowFontName != -1:
				window.SetFontName(windowFontName)
			window.SetText(windowArgument)
			window.SetOutline(True)
		elif isinstance(window, ui.NumberLine):
			window.SetNumber(windowArgument)
		elif isinstance(window, ui.ExpandedImageBoxWiki) or isinstance(window, ui.ImageBoxWiki):
			window.LoadImage(windowArgument if windowArgument.find("gr2") == -1 else "icon/item/27995.tga")
	window.Show()
	return window

def calculatePos(pos, maxWidth):
	(x , y) = (0, 0)
	while True:
		if pos <= maxWidth:
			if pos < 0:
				pos = 0
			x = 32*pos
			break
		else:
			pos -= maxWidth+1
			y+=32
	return (x, y)

def IS_SET(value, flag):
	return (value & flag) == flag
def SET_BIT(value, bit):
	return value | (bit)
def REMOVE_BIT(value, bit):
	return value & ~(bit)
def getFlagValue(value):
	return 1 << value

def FindItemLevelRange(itemVnum, maxRefine):
	(firstLevel, secondLevel) = (0, 0)
	item.SelectItem(itemVnum-maxRefine)
	for i in range(item.LIMIT_MAX_NUM):
		(limitType, limitValue) = item.GetLimit(i)
		if item.LIMIT_LEVEL == limitType:
			if limitValue != 0:
				firstLevel=limitValue
			break

	item.SelectItem(itemVnum)
	for i in range(item.LIMIT_MAX_NUM):
		(limitType, limitValue) = item.GetLimit(i)
		if item.LIMIT_LEVEL == limitType:
			if limitValue != 0:
				secondLevel=limitValue
			break
	return (firstLevel, secondLevel)


def PrintDrop(selectedVnum, self, Listbox):
	item.SelectItem(60001)
	(itemVnum, isRefineItem) = getRealVnum(selectedVnum)
	(x, y, isHave, unknownItem) = (5, 5, False, item.GetItemName())

	chestList = wiki.GetItemDropFromChest(itemVnum, isRefineItem)
	if len(chestList)>0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_CHESTS+":"))
		y += 14

	for chestVnum in chestList:
		item.SelectItem(chestVnum)
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Ikey/plus|i "+item.GetItemName() if unknownItem != item.GetItemName() else "|Ikey/plus|i "+localeInfo.WIKI_UNKOWN_ITEM%chestVnum))
		y+=14

	if len(chestList)>0:
		y+=28

	if itemVnum < 51010 or itemVnum > 51030:
		mobList = wiki.GetItemDropFromMonster(itemVnum, isRefineItem)
	else:
		mobList = []

	if len(mobList) > 0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_MONSTER+":"))
		y += 14

	for mobVnum in mobList:
		mobLevel = nonplayer.GetMonsterLevel(mobVnum)
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Ikey/plus|i "+localeInfo.WIKI_UNKOWN_MOB%mobVnum if mobLevel <= 0 else "|Ikey/plus|i "+nonplayer.GetMonsterName(mobVnum)+ " - Lv."+str(mobLevel)))
		y+=14

	if len(mobList)>0:
		y+=28

	specialData = GetSpecialDropWays(itemVnum, isRefineItem)
	if len(specialData) > 0:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.CATEGORY_COSTUMES_ETC+":"))
		y += 14

	for dropWay in specialData:
		Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Ikey/plus|i "+dropWay))
		y+=14

	if app.ENABLE_ITEMSHOP:
		if len(specialData)>0:
			y+=28
		shopData = GetItemShopData(itemVnum, isRefineItem)
		if len(shopData) > 0:
			Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|cFF0080FF"+localeInfo.WIKI_ITEMSHOP+":"))
			y += 14
		for categoryName in shopData:
			Listbox.AppendItem(CreateWindow(ui.TextLine(), Listbox, (x, y, True), "|Ikey/plus|i "+categoryName))
			y += 14

def CreateCategoryItem(text, event, offset = 0):
	listboxItem = CategoryList.CategoryItem(text)
	listboxItem.SetVisible(True)
	if event:
		listboxItem.SetEvent(event)
	if offset:
		listboxItem.SetOffset(offset)
	return listboxItem

def CreateCategorySubItem(text, event, offset = 0):
	listboxItem = CategoryList.CategorySubItem(text)
	listboxItem.SetVisible(True)
	if event:
		listboxItem.SetEvent(event)
	if offset:
		listboxItem.SetOffset(offset)
	return listboxItem

class RenderTargetNew(ui.WikiRenderTargetUi):
	def __init__(self):
		ui.WikiRenderTargetUi.__init__(self)
		self.children = {}
		self.children["totalPos"] = [0, 0]
		self.children["lastPos"] = [0, 0]
		self.children["isDrag"] = False
		self.SetMouseRightButtonDownEvent(ui.__mem_func__(self.RenderMouseRightDown))
		self.SetMouseRightButtonUpEvent(ui.__mem_func__(self.RenderMouseRightUp))

	def GetRenderIndex(self):
		return self.renderIndex

	def CanCheckMouse(self):
		if WikiRenderTarget.IsShow(self.GetRenderIndex()) != 1:
			return False
		if "isDrag" in self.children:
			return self.children["isDrag"]

	def OnUpdate(self):
		if self.CanCheckMouse():
			[currentMousePos, lastPos] = [app.GetCursorPosition(), self.children["lastPos"]]
			totalPos = self.children["totalPos"] if "totalPos" in self.children else [0, 0]
			_x = (currentMousePos[0] - lastPos[0]) + totalPos[0]
			_y = (currentMousePos[1] - lastPos[1]) + totalPos[1]
			fNewPitchVelocity = _y * 0.3
			fNewRotationVelocity = _x * 0.3
			WikiRenderTarget.RotateEyeAroundTarget(self.GetRenderIndex(), fNewPitchVelocity, fNewRotationVelocity)
			self.children["totalPos"] = [_x, _y]
			self.children["lastPos"] = currentMousePos

	def RenderMouseRightUp(self):
		app.SetCursor(app.NORMAL)
		self.children["isDrag"] = False
		return True

	def RenderMouseRightDown(self):
		app.SetCursor(app.CAMERA_ROTATE)
		self.children["isDrag"] = True
		self.children["lastPos"] = app.GetCursorPosition()
		return True

	def OnMouseWheel(self, nLen):
		renderIndex = self.GetRenderIndex()
		if WikiRenderTarget.IsShow(renderIndex) != 1:
			return False
		WikiRenderTarget.Zoom(renderIndex, app.CAMERA_TO_NEGATIVE if nLen > 0 else app.CAMERA_TO_POSITIVE)
		return True

class Grid: # from KeN
	def __init__(self, width, height):
		self.width = width
		self.height = height
		self.reset()
	def find_blank(self, width, height):
		if width > self.width or height > self.height:
			return -1

		for row in range(self.height):
			for col in range(self.width):
				index = row * self.width + col
				if self.is_empty(index, width, height):
					return index
		return -1
	def put(self, pos, width, height):
		if not self.is_empty(pos, width, height):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = True
				col += 1
		return True
	def clear(self, pos, width, height):
		if pos < 0 or pos >= (self.width * self.height):
			return
		for row in range(height):
			start = pos + (row * self.width)
			self.grid[start] = True
			col = 1
			while col < width:
				self.grid[start + col] = False
				col += 1
	def is_empty(self, pos, width, height):
		if pos < 0:
			return False
		row = pos // self.width
		if (row + height) > self.height:
			return False
		if (pos + width) > ((row * self.width) + self.width):
			return False
		for row in range(height):
			start = pos + (row * self.width)
			if self.grid[start]:
				return False
			col = 1
			while col < width:
				if self.grid[start + col]:
					return False
				col += 1
		return True
	def get_size(self):
		return self.width * self.height
	def reset(self):
		self.grid = [False] * (self.width * self.height)
		#self.put(self.width,1,1) # fix from dracaryS


class ScrollBarSpecial(ui.WikiWindow):
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
	CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)
	BAR_NUMB = 9 #This is static value! Please dont touch in him.
	SCROLL_WIDTH= 8
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
		ui.WikiWindow.__init__(self)
		self.horizontal_scroll = horizontal_scroll
		self.scrollEvent = None
		self.scrollSpeed = 50
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
	def OnScrollMove(self):
		if not self.scrollEvent:
			return
		arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else\
				float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
		self.scrollEvent(arg)
	def SetScrollEvent(self, func):
		self.scrollEvent = func

	def SetScrollSpeed(self, speed):
		self.scrollSpeed = speed

	def OnMouseWheel(self, length):
		if not self.IsShow():
			return False
		length = int((length * 0.01) * self.scrollSpeed)
		if not self.horizontal_scroll:
			val = min(max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetHeight() - self.middleBar.GetHeight() - 1)
			self.middleBar.SetPosition(1, val)
		else:
			val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
			self.middleBar.SetPosition(val, 1)
		self.OnScrollMove()
		return True

	def GetPos(self):
		if not self.horizontal_scroll:
			division = float(self.GetHeight() - 2 - self.middleBar.GetHeight())
			if division <= 0.0:
				return 0.0
			return float(self.middleBar.GetLocalPosition()[1] - 1) / division

		division = float(self.GetWidth() - 2 - self.middleBar.GetWidth())
		if division <= 0.0:
			return 0.0
		return float(self.middleBar.GetLocalPosition()[0] - 1) / division
	
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
		ui.WikiWindow.SetSize(self, width, height)
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
		self.sizeScale = float(selfSize)/float(fullSize)
		if self.sizeScale <= 0.0305:
			self.sizeScale = 0.05
		self.middleBar.SetSize(selfSize, fullSize)
	def SetStaticScale(self, r_size):
		self.middleBar.SetStaticScale(r_size)
	def SetPosScale(self, fScale):
		pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else (math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)
		self.SetPos(pos)
	def SetPos(self, pos):
		wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
		self.middleBar.SetPosition(*wPos)

class MultiTextLine(ui.WikiWindow):
	def Destroy(self):
		self.textRules = {}
	def __init__(self):
		ui.WikiWindow.__init__(self)
		self.Destroy()
		self.AddFlag("not_pick")
		self.textRules["textRange"] = 15
		self.textRules["text"] = ""
		self.textRules["textType"] = ""
		self.textRules["fontName"] = ""
		self.textRules["hexColor"] = 0
		self.textRules["fontColor"] = 0
		self.textRules["outline"] = 0
	def SetTextType(self, textType):
		self.textRules["textType"] = textType
		self.Refresh()
	def SetTextRange(self, textRange):
		self.textRules["textRange"] = textRange
		self.Refresh()
	def SetOutline(self, outline):
		self.textRules["outline"] = outline
		self.Refresh()
	def SetPackedFontColor(self, hexColor):
		self.textRules["hexColor"] = hexColor
		self.Refresh()
	def SetFontColor(self, r, g, b):
		self.textRules["fontColor"] =[r, g, b]
		self.Refresh()
	def SetFontName(self, fontName):
		self.textRules["fontName"] = fontName
		self.Refresh()
	def SetText(self, newText):
		self.textRules["text"] = newText
		self.Refresh()
	def Refresh(self):
		textRules = self.textRules
		if textRules["text"] == "":
			return
		self.children=[]
		outline = textRules["outline"]
		fontColor = textRules["fontColor"]
		hexColor = textRules["hexColor"]
		yRange = textRules["textRange"]
		fontName = textRules["fontName"]
		textType = textRules["textType"].split("#")
		totalTextList = textRules["text"].split("#")

		(xPosition, yPosition) = (0, 0)
		width = 0
		for text in totalTextList:
			childText = ui.TextLine()
			childText.SetParent(self)
			childText.AddFlag("not_pick")
			childText.SetPosition(xPosition, yPosition)
			if fontName != "":
				childText.SetFontName(fontName)
			if hexColor != 0:
				childText.SetPackedFontColor(hexColor)
			if fontColor != 0:
				childText.SetFontColor(*fontColor)
			if outline:
				childText.SetOutline()
			self.AddTextType(childText, textType)
			childText.SetText(str(text))
			if childText.GetTextSize()[0] > width:
				width = childText.GetTextSize()[0]
			childText.Show()
			self.children.append(childText)
			yPosition+=yRange

	def AddTextType(self, text, typeArg):
		if len(typeArg) != 2:
			return
		_typeDict = {
			"vertical": {
				"top":text.SetVerticalAlignTop,
				"bottom":text.SetVerticalAlignBottom,
				"center":text.SetVerticalAlignCenter,
			},
			"horizontal": {
				"left":text.SetHorizontalAlignLeft,
				"right":text.SetHorizontalAlignRight,
				"center":text.SetHorizontalAlignCenter,
			},
			"all_align": {
				"1" : [text.SetHorizontalAlignCenter,text.SetVerticalAlignCenter,text.SetWindowHorizontalAlignCenter,text.SetWindowVerticalAlignCenter],
			},
		}
		(firstToken, secondToken) = tuple(typeArg)
		if firstToken in _typeDict:
			textType = _typeDict[firstToken][secondToken] if secondToken in _typeDict[firstToken] else None
			if textType != None:
				if isinstance(textType, list):
					for rule in textType:
						rule()
				else:
					textType()

class ListBoxSpecial(ui.WikiWindow):
	def Destroy(self):
		self.basePos=0
		self.itemList=[]
		self.scrollBar=None
		self.scrollLen=0
		self.isHorizontal= False

	def __init__(self, isHorizontal = False):
		ui.WikiWindow.__init__(self)
		self.itemList=[]
		self.scrollBar=None
		self.Destroy()
		self.SetInsideRender(True)

	def RemoveAllItems(self):
		for item in self.itemList:
			item.Hide()
			item.Destroy()
		self.itemList=[]
		if self.scrollBar:
			self.scrollBar.SetPos(0)
		self.Render(0)

	def GetItems(self):
		return self.itemList

	def AppendItem(self, newItem, setPosition = True):
		newItem.SetParent(self)
		if setPosition:
			(_x,_y) = (0, 0)
			for child in self.itemList:
				if child.exPos[1]+child.GetHeight() > _y:
					_y = child.exPos[1]+child.GetHeight()
			newItem.SetPosition(_x, _y, True)
		self.itemList.append(newItem)
		self.CalculateScroll()

	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar=scrollBar

	def OnMouseWheel(self, length):
		if self.scrollBar:
			if self.scrollBar.IsShow():
				self.scrollBar.OnMouseWheel(length)
				return True
		return False

	def CalculateScroll(self):
		if len(self.itemList) == 0:
			return

		screenSize = 0
		for child in self.itemList:
			if child.exPos[1]+child.GetHeight() > screenSize:
				screenSize = child.exPos[1]+child.GetHeight()
		#if screenSize != 0:
		#	screenSize+=30
		windowHeight = self.GetHeight()
		(scrollBar,scrollLen) = (self.scrollBar, 0)
		if scrollBar:
			scrollBar.SetPos(0)
			if screenSize > windowHeight:
				scrollLen = screenSize-windowHeight
				scrollBar.SetScale(windowHeight, screenSize)
			else:
				scrollBar.SetScale(windowHeight, windowHeight)
			scrollBar.Show()
		self.scrollLen = scrollLen

	def __OnScroll(self):
		if self.scrollBar:
			self.SetBasePos(int(self.scrollBar.GetPos()*self.scrollLen))

	def Render(self, basePos):
		useWikiImprovements = getattr(app, "WIKI_IMPROVEMENTS", 1)
		windowHeight = self.GetHeight() if useWikiImprovements else 0
		for child in self.itemList:
			(ex,ey) = child.exPos
			if useWikiImprovements and hasattr(child, "renderLoaded") and windowHeight > ey - basePos:
				child.RenderLoad()
			if self.isHorizontal:
				child.SetPosition(ex-basePos,ey)
			else:
				child.SetPosition(ex,ey-basePos)
		self.basePos=basePos

	def SetBasePos(self, basePos):
		if self.basePos == basePos:
			return
		self.Render(basePos)
