#
# OSF Info
# Child of constInfo.py
#
# General Options
#

import app
import os
import player
import item
import chr
import localeInfo
import uiScriptLocale

NEW_LOGIN_WINDOW = True
ENABLE_PICK_MONEY_DIALOG = False # Disable/Enable pick money dialog from inventory
DEBUG_MODE = False # Debug mode (debug info and console)
USE_NEW_WHISPER_LETTER_CATEGORY = True # Use the new letter category for normal and gm players
WHISPER_ON_CHAT_LINE = True # Show whisper in chat line
PAST_HEALTH_ON_TARGET = True # Show past health on target (yellow gauge)
SHOW_LOADING_PROGRESS = False # Show loading progress
EXTENDED_LOADING_GUAGE = True # Loading guage extended with description
AFFECT_DISPLAY_IN_THINBOARD = True # Show align affect's using a ThinBoard
ALIGN_AFFECT_IMG_LIST = True # Align affect image list
FILTER_EMOJI_NOTICE = True # Filter emojis on tip notice or big notice to chat line
if app.ENABLE_KINGDOMS_WAR:
	KINGDOMS_TP = 0 # Kingdoms war teleport from event calendar
SHOW_EMOJI_IN_CHAT_LINE = True # Show emoji in chat line
SHOW_EMOJI_IN_WHISPER_LINE = False # Show emoji in whisper line
SHOW_USE_IMAGE_TEXT_LINE = True # Show use item image text line in tooltip
SHOW_SELL_IMAGE_TEXT_LINE = False # Show sell item image text line in tooltip
ENABLE_ITEM_HIGHLIGHT_RENEWAL = True # Highlight renewal for unusable item
SHOW_REFINE_ITEM_DESC = True # Show refine item description
ENABLE_OLD_QUEST_LETTER_LIST = True # Enable the old quest letter list
EXPANDED_TASKBAR_VISIBLE = True
EVENT_BANNER = True # Show event banner instead of mini-game rumi button

SHOW_REFINE_PERCENTAGE = True # Show refine success percentage
MONEY_K_FORMAT = True # Use money K format
MOUNT_ITEM_ATTR_TOOLTIP = True # Show quest item attributes on tooltip
PET_ITEM_ATTR_TOOLTIP = True # Show quest item attributes on tooltip
SHOW_ITEM_VNUM_TOOTIP = True # Show the item vnum
MARK_IMG_32x32 = True
LOGIN_UI_MODIFY = False # Login countdown
NEW_SELECT_UI = True # New select character interface
NEW_CREATE_UI = True # New create character interface
SELECT_CHARACTER_ROTATION = False # Enables character rotation in select phase.
INCREASE_POINTS_CTRL = 10
TOOLTIP_KEYS_COLOR_HEX = 0xffffcc99
if app.ENABLE_SKILL_COLOR_SYSTEM:
	SKILL_COLOR_BUFF_ONLY = False # Enable skill color button on buffs only

if app.ENABLE_DISCORD_STUFF:
	msgname = ""

if app.ENABLE_SHOW_CHEST_DROP:
	CHEST_DROP_INFO_DATA = {}

if app.ENABLE_HIDE_AFFECT_ICONS:
	AffectIconState = False

if app.ENABLE_AURA_SYSTEM:
	AURA_ATTACHED_LIST_SLOT = {}

if app.ENABLE_DUNGEON_INFO:
	dungeonInfoCMD = ""
	dungeonInfoQuestIdx = -1
	dungeonRejoinCMD = ""
	dungeonRejoinOffer = None

if app.ENABLE_SPECIAL_INVENTORY_SYSTEM: # Enable/disable the safebox and mall in special inventory
	OPEN_SAFEBOX_MALL_IN_SPECIAL_INV = True
else:
	OPEN_SAFEBOX_MALL_IN_SPECIAL_INV = False

AUTOPICKUP_ENABLED = False
PICKUP_MODE = 1

def LoadPickupConfig():
	PICKUP_FOLDER = "UserData/pickup"
	CheckDirectory(PICKUP_FOLDER)
	PICKUP_CFG_FILE = PICKUP_FOLDER + "/" + player.GetName() + ".cfg"
	if CheckFile(PICKUP_CFG_FILE):	

		for xx in range(4):
			player.PickupBlockClassType(False, xx)
			
		for xx in range(6):
			player.PickupBlockWeaponType(False, xx)
			
		for xx in range(6):
			player.PickupBlockArmorType(False, xx)
	
		lines = open(PICKUP_CFG_FILE, "r").readlines()
		if len(lines) > 0:
			for line in lines:
				if len(line) <= 2:
					continue
					
				line = line.replace("\n", "")
				lineSplit = line.split(":")
				
				if lineSplit[0] == "pick_mode":
					PICKUP_MODE = int(lineSplit[1])
					
				elif lineSplit[0] == "block_class":
					if len(lineSplit[1]) >= 1:
						splitClass = lineSplit[1].split(",")
						for blockClass in splitClass:
							player.PickupBlockClassType(True, int(blockClass))
							
				elif lineSplit[0] == "min_lvl":
					player.PickupBlockMinLvl(int(lineSplit[1]))
					
				elif lineSplit[0] == "max_lvl":
					player.PickupBlockMaxLvl(int(lineSplit[1]))
					
				elif lineSplit[0] == "block_weapon":
					if len(lineSplit[1]) >= 1:
						splitClass = lineSplit[1].split(",")
						for blockClass in splitClass:
							player.PickupBlockWeaponType(True, int(blockClass))
							
				elif lineSplit[0] == "block_armor":
					if len(lineSplit[1]) >= 1:
						splitClass = lineSplit[1].split(",")
						for blockClass in splitClass:
							player.PickupBlockArmorType(True, int(blockClass))
##################################################################################

SUPPORT_SKILL_VNUMS = (196, 194, 195, 197, 198)

if app.ENABLE_BUFF_SYSTEM:
	SUPPORT_ITEM_VNUM = 61020
	# Server-side persistent activation marker for the inventory-held seal.
	# Hair is stored in the item's transmutation VNUM, so socket 2 is free.
	SUPPORT_ACTIVE_SOCKET = 2
	SUPPORT_SLOT_ARMOR = 1
	SUPPORT_SLOT_HAIR = 2
	SUPPORT_SLOT_WEAPON = 3
	SUPPORT_SLOT_EFFECT_WEAPON = 4
	SUPPORT_SLOT_EFFECT_ARMOR = 5
	SUPPORT_SLOT_SASH = 6
	SUPPORT_SLOT_MAX = 7
	
	SUPPORT_EQUIPMENT = {}
	for eq in range(SUPPORT_SLOT_MAX):
		SUPPORT_EQUIPMENT[eq] = 0
		
	SUPPORT_SKILLS = {}
	for sk in range(6):
		SUPPORT_SKILLS[sk] = {
			"GRADE" : 0,
			"LVL" : 0,
			"REAL_LVL" : 0,
		}
		
	def SkillLevelToGrade(lvl):
		# 0-19 	= grade 0
		# 20-29 = grade 1 | M
		# 30-39 = grade 2 | G
		# 40-49 = grade 3 | P
		if lvl >= 40:
			return 3
		elif lvl >= 30:
			return 2
		elif lvl >= 20:
			return 1
		else:
			return 0
			
	def SkillLevelToLvl(lvl):
		grade = SkillLevelToGrade(lvl)
		if grade == 3:
			return lvl - 40 + 1
		if grade == 2:
			return lvl - 30 + 1
		if grade == 1:
			return lvl - 20 + 1
		else:
			return lvl

if app.ENABLE_EXPRESSING_EMOTION:
	import emotion
	EXPRESSING_EMOTIONS = {}

if app.ENABLE_HIDE_COSTUME_SYSTEM:
	HIDDEN_BODY_COSTUME = 0
	HIDDEN_HAIR_COSTUME = 0
	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		HIDDEN_ACCE_COSTUME = 0
	if app.ENABLE_WEAPON_COSTUME_SYSTEM:
		HIDDEN_WEAPON_COSTUME = 0
	if app.ENABLE_ACCE_SKIN_SYSTEM:
		HIDDEN_ACCE_SKIN = 0
	if app.ENABLE_AURA_SYSTEM:
		HIDDEN_AURA_COSTUME = 0
	if app.ENABLE_SPECIAL_SHINING_SYSTEM:
		HIDDEN_SHINING_WEAPON = 0
		HIDDEN_SHINING_ARMOR = 0
	if app.ENABLE_MOUNT_COSTUME_SYSTEM:
		HIDDEN_MOUNT = 0

if app.ENABLE_SKILL_SELECT_GUI:
	ARE_ENABLED_6TH_SKILLS = 1

if app.ENABLE_OFFLINE_SHOP:
	SHOP_SKIN_VALUE = 0
	SHOP_BANNER_VALUE = 0
	SHOP_SKIN_UNLOCKED = {
		0 : False,
		1 : False,
		2 : False,
		3 : False,
		4 : False,
		5 : False,
		6 : False,
		7 : False,
	}
	SHOP_BANNER_UNLOCKED = {
		0 : False,
		1 : False,
		2 : False,
		3 : False,
		4 : False,
	}
	
	SHOP_SKIN_TIME = {
		0 : 0,
		1 : 0,
		2 : 0,
		3 : 0,
		4 : 0,
		5 : 0,
		6 : 0,
		7 : 0,
	}
	SHOP_BANNER_TIME = {
		0 : 0,
		1 : 0,
		2 : 0,
		3 : 0,
		4 : 0,
	}
	
	SHOP_VID = {}
	SHOPNAMES_RANGE = 4000
	IS_OFFLINE_SHOP_DECORATION = False
	OFFLINE_SHOP_DECORATION_UPDATE = False

if app.ENABLE_SHOP_SEARCH:
	SHOP_SEARCH_ITEM = -1
	SPECIAL_ITEMS = []
	COLORED_ITEMS = []

	def GetItemSpecialColor(itemVnum):
		for fromVnum, toVnum, title, color in SPECIAL_ITEMS:
			if itemVnum >= fromVnum and itemVnum <= toVnum:
				return (title, color)
	
		return (None, None)
	
	def GetItemTitleColor(itemVnum):
		for fromVnum, toVnum, color in COLORED_ITEMS:
			if itemVnum >= fromVnum and itemVnum <= toVnum:
				return color
	
		return None

def minutetohour(time):
	return int((time // 60) // 60) % 24

def minutetominute(time):
	return int((time // 60) % 60)
	
def minutetosecond(time):
	return int(time % 60)	

if app.ENABLE_CAPTCHA_NEW:
	CAPTCHA_QUESTINDEX = 0

#########################################	
## USED FOR OFFLINE SHOP AND NORMAL SHOP
CACHED_ITEM_PRICES = {}
def ReadItemPrice(vnum,count):
	key = str(vnum) + "_" + str(count)
	# if key in CACHED_ITEM_PRICES:
		# return CACHED_ITEM_PRICES[key]
	
	saveDir = "UserData/shops"
	if not os.path.exists(saveDir):
		os.makedirs(saveDir)
		
	itemPrice=0
#	itemCheque=0
	saveFile = saveDir + "/" + key + ".txt"
	if os.path.exists(saveFile):
		fd = open(saveFile, 'r')
		readLine = fd.readlines()
		itemPrice = int(readLine[0])
#		itemCheque = int(readLine[1])
		
	CACHED_ITEM_PRICES[key] = itemPrice
#	return (itemPrice, itemCheque)
	return itemPrice
	
def SaveItemPrice(vnum, count, price):
	key = str(vnum) + "_" + str(count)
	# if key in CACHED_ITEM_PRICES:
		# if CACHED_ITEM_PRICES[key] == price:
			# return
		
	saveDir = "UserData/shops"
	
	if not os.path.exists(saveDir):
		os.makedirs(saveDir)
	
	CACHED_ITEM_PRICES[key] = price
	saveFile = saveDir + "/" + key + ".txt"
	f = open(saveFile, "w+")
#	f.write(str(price) + "\n" + str(cheque))
	f.write(str(price))
	f.close()

if app.ENABLE_MESSENGER_BLOCK:
	MESSENGER_KEY = 0

INPUT_IGNORE = 0

# MINI_GAME
if app.ENABLE_MINI_GAME_OKEY:
	RUMI_GAME_EVENT = False
if app.ENABLE_MINI_GAME_CATCH_KING:
	CATCH_KING_GAME_EVENT = False
# END_OF_MINI_GAME

if app.ENABLE_AUTO_REFINE:
	AUTO_REFINE = False
	IS_AUTO_REFINE = False
	AUTO_REFINE_TYPE = 0
	AUTO_REFINE_DATA = {
		"ITEM" : [-1, -1],
		"NPC" : [0, -1, -1, 0]
	}

_interface_instance = None
_game_instance = None
def GetInterfaceInstance():
	global _interface_instance
	return _interface_instance
	
def SetInterfaceInstance(instance):
	global _interface_instance
	if _interface_instance:
		del _interface_instance
	_interface_instance = instance
	
def GetGameInstance():
	global _game_instance
	return _game_instance

def SetGameInstance(instance):
	global _game_instance
	if _game_instance:
		del _game_instance
	_game_instance = instance	

def IsDebugMode():
	if DEBUG_MODE == True:
		return True

	return False

if app.ENABLE_CHATTING_WINDOW_RENEWAL:
	import os
	def CheckDirectory(directory):
		try:
			os.makedirs(directory)
		except:
			pass
			
	def CheckFile(directory):
		if os.path.exists(directory):
			return True
		return False
		
	def RemoveFile(directory):
		if os.path.exists(directory):
			os.remove(directory)

	import chat
	CHAT_LAST_SENTENCE_STACK = []
	OPTION_CHECKBOX_TALKING = 1
	OPTION_CHECKBOX_PARTY = 2
	OPTION_CHECKBOX_GUILD = 3
	OPTION_CHECKBOX_SHOUT = 4
	OPTION_CHECKBOX_INFO = 5
	OPTION_CHECKBOX_NOTICE = 6
	OPTION_CHECKBOX_DICE = 7
	OPTION_CHECKBOX_EXP_INFO = 8
	OPTION_CHECKBOX_ITEM_INFO = 9
	OPTION_CHECKBOX_MONEY_INFO = 10
	OPTION_CHECKBOX_FILTER = 11
	
	OPTION_CHECKBOX_FLAG_EN = 12
	OPTION_CHECKBOX_FLAG_PT = 13
	OPTION_CHECKBOX_FLAG_ES = 14
	OPTION_CHECKBOX_FLAG_FR = 15
	OPTION_CHECKBOX_FLAG_DE = 16
	OPTION_CHECKBOX_FLAG_RO = 17
	OPTION_CHECKBOX_FLAG_PL = 18
	OPTION_CHECKBOX_FLAG_IT = 19
	OPTION_CHECKBOX_FLAG_CZ = 20
	OPTION_CHECKBOX_FLAG_HU = 21
	OPTION_CHECKBOX_FLAG_TR = 22
	OPTION_MAX = 23

	OPTION_CHECKBOX_MODE = {
		OPTION_CHECKBOX_TALKING : [[chat.CHAT_TYPE_TALKING], uiScriptLocale.CHATTING_SETTING_TALKING],
		OPTION_CHECKBOX_INFO : [[chat.CHAT_TYPE_INFO], uiScriptLocale.CHATTING_SETTING_SYSTEM],
		OPTION_CHECKBOX_NOTICE : [[chat.CHAT_TYPE_NOTICE,chat.CHAT_TYPE_BIG_NOTICE], uiScriptLocale.CHATTING_SETTING_NOTICE],
		OPTION_CHECKBOX_PARTY : [[chat.CHAT_TYPE_PARTY], uiScriptLocale.CHATTING_SETTING_PARTY],
		OPTION_CHECKBOX_GUILD : [[chat.CHAT_TYPE_GUILD], uiScriptLocale.CHATTING_SETTING_GUILD],
		OPTION_CHECKBOX_SHOUT : [[chat.CHAT_TYPE_SHOUT], uiScriptLocale.CHATTING_SETTING_SHOUT],
		OPTION_CHECKBOX_DICE : [[chat.CHAT_TYPE_DICE_INFO], uiScriptLocale.CHATTING_SETTING_DICE],
		OPTION_CHECKBOX_ITEM_INFO : [[chat.CHAT_TYPE_ITEM_INFO], uiScriptLocale.CHATTING_SETTING_ITEM],
		OPTION_CHECKBOX_MONEY_INFO : [[chat.CHAT_TYPE_MONEY_INFO], uiScriptLocale.CHATTING_SETTING_GOLD],
	}

	cacheChat = {}
	def CreateEmptyList(index):
		list = [1] * OPTION_MAX
		list[0] = str(index)
		list[OPTION_CHECKBOX_EXP_INFO] = 0
		list[OPTION_CHECKBOX_FILTER] = 0
		for langIndex in range(OPTION_CHECKBOX_FLAG_EN, OPTION_MAX):
			list[langIndex] = 0
		return list
	
	def SaveChatData():
		global cacheChat
		if len(cacheChat) == 0:
			return
		MAIN_FILE = "UserData/chatting_config"
		PLAYER_FILE = MAIN_FILE+"/"+player.GetName()+".chat"

		try:
			file = open(PLAYER_FILE, "w+")
			for key, data in cacheChat.items():
				data = cacheChat[key]
				data[OPTION_CHECKBOX_EXP_INFO] = 0
				text = ""
				for x in range(OPTION_MAX):
					text+=str(data[x])+"#"
				file.write(text+"\n")
			file.close()
		except:
			pass

	def LoadChatNewEmpty(index):
		global cacheChat
		cacheChat[index] = CreateEmptyList(index)
		SaveChatData()

	def LoadChatEmpty():
		global cacheChat
		cacheChat = {}
		cacheChat[0] = CreateEmptyList(0)
		SaveChatData()

	def RemoveChat(index):
		global cacheChat
		if index in cacheChat:
			del cacheChat[index]
			SaveChatData()

	def LoadChatData():
		global cacheChat
		cacheChat = {}
		MAIN_FILE = "UserData/chatting_config"
		PLAYER_FILE = MAIN_FILE+"/"+player.GetName()+".chat"
		CheckDirectory(MAIN_FILE)
		if CheckFile(PLAYER_FILE):
			lines = open(PLAYER_FILE, "r").readlines()
			if len(lines) > 0:

				index = 0
				for line in lines:
					lineSplit = line.split("#")

					if len(lineSplit)==0 or OPTION_MAX != len(lineSplit)-1:
						LoadChatEmpty()
					else:
						list = [1] * OPTION_MAX
						for j in range(len(lineSplit)-1):
							if j == 0:
								list[j] = str(lineSplit[j])
							else:
								list[j] = int(lineSplit[j])
						list[OPTION_CHECKBOX_EXP_INFO] = 0
						cacheChat[index] = list
					index+=1
			else:
				LoadChatEmpty()
		else:
			LoadChatEmpty()

def IS_ANTI_EXP_RING(itemVnum):
	if itemVnum == 72501:
		return 1

	return 0

if app.ENABLE_EXTENDED_BLEND_AFFECT:
	def IS_DEW_POTION(itemVnum):
		return 79700 <= itemVnum <= 79729 or 50821 <= itemVnum <= 50826 or 950821 <= itemVnum <= 950826

	def IS_BLEND_POTION(itemVnum):
		if itemVnum >= 50821 and itemVnum <= 50826:
			return 1
		elif itemVnum == 51002:
			return 1

		return 0

	def IS_EXTENDED_BLEND_POTION(itemVnum):
		if itemVnum >= 950821 and itemVnum <= 950826: # Dews
			return 1
		elif itemVnum == 951002: # Cristal Energy
			return 1
		elif itemVnum >= 939017 and itemVnum <= 939020: # Dragon God Medals
			return 1
		elif itemVnum == 939024 or itemVnum == 939025: # Critical & Penetration
			return 1
		elif itemVnum == 927209 or itemVnum == 927212: # Attack Speed & Move Speed
			return 1

		return 0

if app.ENABLE_EXPRESSING_EMOTION:
	def GET_SPECIAL_EMOTION_NAME(idx):
		if idx >= app.SPECIAL_ACTION_START_INDEX and idx <= emotion.EMOTION_WHIRL:
			return emotion.SPECIAL_EMOTION_DICT[idx]["name"]

if app.ENABLE_MULTIPLE_SELECT:
	MULTIPLE_MODE_ADD = 1
	MULTIPLE_MODE_DELETE = 0

	MULTIPLE_LIST = []
	MULTIPLE_MODE = -1
	MULTIPLE_MODE_SPECIAL_INV = -1
	
	def CanSellItem(slotIndex):
		itemVnum = player.GetItemIndex(slotIndex)
		item.SelectItem(itemVnum)
		
		if item.IsAntiFlag(item.ANTIFLAG_SELL):
			return False
			
		return True
		
	def CanDestroyItem(slotIndex):
		#ALLOW DESTROY ALL ITEMS FOR GM:
		if chr.IsGameMaster(player.GetMainCharacterIndex()):
			return True
			
		itemVnum = player.GetItemIndex(slotIndex)
		item.SelectItem(itemVnum)
		
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_DESTROY):
			return False
			
		return True

def StripColor(text):
	import re

	regex = r'\|c([a-zA-Z0-9]){0,8}|'
	search = re.search(regex, text)
	if search:
		text = re.sub(regex, '', text)

	return text

def IsEmojiFilter(text):
	import re

	regex = r'\|I.*\|i'
	search = re.search(regex, text)
	if search:
		return True

	return False

def IsHyperLinkFilter(text):
	import re

	regex = r'\|H.*\|h'
	search = re.search(regex, text)
	if search:
		return True

	return False

def EmojiFilter(text):
	import re

	EMOJI_DIC = {
		':o' : 'emoji/amazed',
		':)' : 'emoji/happiness',
		':D' : 'emoji/happy',
		':\\' : 'emoji/indifferent',
		':p' : 'emoji/tongue',
		':P' : 'emoji/tongue',
		'xP' : 'emoji/dead',
		':X' : 'emoji/muted',
		':x' : 'emoji/muted',
		'>:D' : 'emoji/evil',
		':3' : 'emoji/in-love',
		'<3' : 'emoji/heart',
		':*' : 'emoji/kiss',
		':O' : 'emoji/surprised',
		'>:(' : 'emoji/angry',
		':||' : 'emoji/quiet',
	}

	for emoji_str, emoji_img in EMOJI_DIC.items():
		text = text.replace(emoji_str, "|I" + emoji_img + "|i")

	return text

if app.ENABLE_RENDER_TARGET_PREVIEW:
	RENDER_TARGET_ITEM_VNUM = 0
	RENDER_TARGET_ITEM_TYPE = 0
	RENDER_TARGET_OPEN = False

if app.ENABLE_KINGDOMS_WAR:
	def get_hour(leftTime):
		return ((leftTime // 60) // 60)

	def get_min(leftTime):
		return ((leftTime // 60) % 60)
		
	def get_sec(leftTime):
		return (leftTime % 60)
	
	def CalculateTime(time):
		hour = get_hour(time)
		minute = get_min(time)
		sec = get_sec(time)
		hour_text = "00"
		min_text = "00"
		sec_text = "00"
		if hour > 0:
			if hour > 0 and hour <= 9:
				hour_text = "0"+str(hour)
			else:
				hour_text=str(hour)
		if minute > 0:
			if minute > 0 and minute <= 9:
				min_text = "0"+str(minute)
			else:
				min_text=str(minute)
		if sec > 0:
			if sec > 0 and sec <= 9:
				sec_text = "0"+str(sec)
			else:
				sec_text=str(sec)
		return "%s:%s:%s"%(hour_text,min_text,sec_text)

if app.ENABLE_WIKI:
	def GetWikiInterface():
		interface = GetInterfaceInstance()
		return interface.wndWiki if interface != None else None
