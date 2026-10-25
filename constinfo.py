import app

# option
IN_GAME_SHOP_ENABLE = 1
CONSOLE_ENABLE = 0

PVPMODE_ENABLE = 1
#PVPMODE_TEST_ENABLE = 0
PVPMODE_ACCELKEY_ENABLE = 1
PVPMODE_ACCELKEY_DELAY = 0.5
PVPMODE_PROTECTED_LEVEL = 30

FOG_LEVEL0 = 4800.0
FOG_LEVEL1 = 9600.0
FOG_LEVEL2 = 12800.0
FOG_LEVEL = FOG_LEVEL0
FOG_LEVEL_LIST=[FOG_LEVEL0, FOG_LEVEL1, FOG_LEVEL2]

CAMERA_MAX_DISTANCE_SHORT = 2500.0
CAMERA_MAX_DISTANCE_LONG = 3500.0 * 2
CAMERA_MAX_DISTANCE_LIST=[CAMERA_MAX_DISTANCE_SHORT, CAMERA_MAX_DISTANCE_LONG]
CAMERA_MAX_DISTANCE = CAMERA_MAX_DISTANCE_SHORT

CHRNAME_COLOR_INDEX = 0

ENVIRONMENT_NIGHT="d:/ymir work/environment/lightblue_sky/skybox_reco_lightblue.msenv"

# constant
HIGH_PRICE = 500000
MIDDLE_PRICE = 50000
ERROR_METIN_STONE = 28960
SUB2_LOADING_ENABLE = 1
EXPANDED_COMBO_ENABLE = 1
CONVERT_EMPIRE_LANGUAGE_ENABLE = 1
USE_ITEM_WEAPON_TABLE_ATTACK_BONUS = 0
ADD_DEF_BONUS_ENABLE = 1
LOGIN_COUNT_LIMIT_ENABLE = 0

USE_SKILL_EFFECT_UPGRADE_ENABLE = 1

VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD = 1
GUILD_MONEY_PER_GSP = 100
GUILD_WAR_TYPE_SELECT_ENABLE = 1
TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE = 0

HAIR_COLOR_ENABLE = 1
ARMOR_SPECULAR_ENABLE = 1
WEAPON_SPECULAR_ENABLE = 1
SEQUENCE_PACKET_ENABLE = 1
KEEP_ACCOUNT_CONNETION_ENABLE = 1
MINIMAP_POSITIONINFO_ENABLE = 0
CONVERT_EMPIRE_LANGUAGE_ENABLE = 0
USE_ITEM_WEAPON_TABLE_ATTACK_BONUS = 0
ADD_DEF_BONUS_ENABLE = 0
LOGIN_COUNT_LIMIT_ENABLE = 0
PVPMODE_PROTECTED_LEVEL = 15

isItemQuestionDialog = 0

def GET_ITEM_QUESTION_DIALOG_STATUS():
	global isItemQuestionDialog
	return isItemQuestionDialog

def SET_ITEM_QUESTION_DIALOG_STATUS(flag):
	global isItemQuestionDialog
	isItemQuestionDialog = flag

import app
import net

########################

def SET_DEFAULT_FOG_LEVEL():
	global FOG_LEVEL
	app.SetMinFog(FOG_LEVEL)

def SET_FOG_LEVEL_INDEX(index):
	global FOG_LEVEL
	global FOG_LEVEL_LIST
	try:
		FOG_LEVEL=FOG_LEVEL_LIST[index]
	except IndexError:
		FOG_LEVEL=FOG_LEVEL_LIST[0]
	app.SetMinFog(FOG_LEVEL)

def GET_FOG_LEVEL_INDEX():
	global FOG_LEVEL
	global FOG_LEVEL_LIST
	return FOG_LEVEL_LIST.index(FOG_LEVEL)

########################

def SET_DEFAULT_CAMERA_MAX_DISTANCE():
	global CAMERA_MAX_DISTANCE
	app.SetCameraMaxDistance(CAMERA_MAX_DISTANCE)

def SET_CAMERA_MAX_DISTANCE_INDEX(index):
	global CAMERA_MAX_DISTANCE
	global CAMERA_MAX_DISTANCE_LIST
	try:
		CAMERA_MAX_DISTANCE=CAMERA_MAX_DISTANCE_LIST[index]
	except:
		CAMERA_MAX_DISTANCE=CAMERA_MAX_DISTANCE_LIST[0]

	app.SetCameraMaxDistance(CAMERA_MAX_DISTANCE)

def GET_CAMERA_MAX_DISTANCE_INDEX():
	global CAMERA_MAX_DISTANCE
	global CAMERA_MAX_DISTANCE_LIST
	return CAMERA_MAX_DISTANCE_LIST.index(CAMERA_MAX_DISTANCE)

########################

import chrmgr
import player
import app

def SET_DEFAULT_CHRNAME_COLOR():
	global CHRNAME_COLOR_INDEX
	chrmgr.SetEmpireNameMode(CHRNAME_COLOR_INDEX)

def SET_CHRNAME_COLOR_INDEX(index):
	global CHRNAME_COLOR_INDEX
	CHRNAME_COLOR_INDEX=index
	chrmgr.SetEmpireNameMode(index)

def GET_CHRNAME_COLOR_INDEX():
	global CHRNAME_COLOR_INDEX
	return CHRNAME_COLOR_INDEX

def SET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD(index):
	global VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD
	VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD = index

def GET_VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD():
	global VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD
	return VIEW_OTHER_EMPIRE_PLAYER_TARGET_BOARD

def SET_DEFAULT_CONVERT_EMPIRE_LANGUAGE_ENABLE():
	global CONVERT_EMPIRE_LANGUAGE_ENABLE
	net.SetEmpireLanguageMode(CONVERT_EMPIRE_LANGUAGE_ENABLE)

def SET_DEFAULT_USE_ITEM_WEAPON_TABLE_ATTACK_BONUS():
	global USE_ITEM_WEAPON_TABLE_ATTACK_BONUS
	player.SetWeaponAttackBonusFlag(USE_ITEM_WEAPON_TABLE_ATTACK_BONUS)

def SET_DEFAULT_USE_SKILL_EFFECT_ENABLE():
	global USE_SKILL_EFFECT_UPGRADE_ENABLE
	app.SetSkillEffectUpgradeEnable(USE_SKILL_EFFECT_UPGRADE_ENABLE)

def SET_TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE():
	global TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE
	app.SetTwoHandedWeaponAttSpeedDecreaseValue(TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE)

########################
import item

ACCESSORY_MATERIAL_LIST = [50623, 50624, 50625, 50626, 50627, 50628, 50629, 50630, 50631, 50632, 50633, 50634, 50635, 50636, 50637, 50638, 50639]
#ACCESSORY_MATERIAL_LIST = [50623, 50623, 50624, 50624, 50625, 50625, 50626, 50627, 50628, 50629, 50630, 50631, 50632, 50633, 
#				50623, 50623, 50624, 50624, ]
JewelAccessoryInfos = [
		# jewel		wrist	neck	ear
		[ 50634,	14420,	16220,	17220 ],
		[ 50635,	14500,	16500,	17500 ],
		[ 50636,	14520,	16520,	17520 ],
		[ 50637,	14540,	16540,	17540 ],
		[ 50638,	14560,	16560,	17560 ],
		[ 50639,	14570,	16570,	0 ],# 오광귀걸이는 없음(귀걸이는 수인관련)
	]

if app.ENABLE_PERMA_ACCESSORY:	
	PermanentJewelAccessoryInfos = [
			# jewel		wrist	neck	ear
			[ 55623,	14000,	16000,	17000 ],
			[ 55624,	14020,	16020,	17020 ],
			[ 55625,	14040,	16040,	17040 ],
			[ 55626,	14060,	16060,	17060 ],
			[ 55627,	14080,	16080,	17080 ],
			[ 55628,	14100,	16100,	17100 ],
			[ 55629,	14120,	16120,	17120 ],
			[ 55630,	14140,	16140,	17140 ],
			[ 55631,	14160,	16160,	17160 ],
			[ 55632,	14180,	16180,	17180 ],
			[ 55633,	14200,	16200,	17200 ],
			[ 55634,	14220,	16220,	17220 ],
			[ 55635,	14500,	16500,	17500 ],
			[ 55636,	14520,	16520,	17520 ],
			[ 55637,	14540,	16540,	17540 ],
			[ 55638,	14560,	16560,	17560 ],
			# Tourmaline: bracelet/necklace only; 17570 is Fog Jadite (server item.cpp).
			[ 55639,	14570,	16570,	0 ],
		]
		
if app.ENABLE_PERMA_ACCESSORY:
	def GET_Permanent_ACCESSORY_MATERIAL_VNUM(vnum, subType):
		ret = vnum
		item_base = (vnum // 10) * 10
		for info in PermanentJewelAccessoryInfos:
			if item.ARMOR_WRIST == subType:
				if info[1] == item_base:
					return info[0]
			elif item.ARMOR_NECK == subType:
				if info[2] == item_base:
					return info[0]
			elif item.ARMOR_EAR == subType:
				if info[3] == item_base:
					return info[0]
					
		return False

def GET_ACCESSORY_MATERIAL_VNUM(vnum, subType):
	family = vnum // 100
	slot = (vnum % 100) // 10
	if 9200 <= family <= 9203 and ((slot == 2 and subType == item.ARMOR_WRIST) or (slot == 3 and subType == item.ARMOR_NECK) or (slot == 4 and subType == item.ARMOR_EAR)):
		return 50665 + family - 9200

	ret = vnum
	item_base = (vnum // 10) * 10
	for info in JewelAccessoryInfos:
		if item.ARMOR_WRIST == subType:
			if info[1] == item_base:
				return info[0]
		elif item.ARMOR_NECK == subType:
			if info[2] == item_base:
				return info[0]
		elif item.ARMOR_EAR == subType:
			if info[3] == item_base:
				return info[0]
 
	if vnum >= 16210 and vnum <= 16219:
		return 50625

	if item.ARMOR_WRIST == subType:
		WRIST_ITEM_VNUM_BASE = 14000
		ret -= WRIST_ITEM_VNUM_BASE
	elif item.ARMOR_NECK == subType:
		NECK_ITEM_VNUM_BASE = 16000
		ret -= NECK_ITEM_VNUM_BASE
	elif item.ARMOR_EAR == subType:
		EAR_ITEM_VNUM_BASE = 17000
		ret -= EAR_ITEM_VNUM_BASE

	type = ret // 20

	if type<0 or type>=len(ACCESSORY_MATERIAL_LIST):
		type = (ret-170) // 20
		if type<0 or type>=len(ACCESSORY_MATERIAL_LIST):
			return 0

	return ACCESSORY_MATERIAL_LIST[type]

##################################################################
## 새로 추가된 '벨트' 아이템 타입과, 벨트의 소켓에 꽂을 아이템 관련.. 
## 벨트의 소켓시스템은 악세서리와 동일하기 때문에, 위 악세서리 관련 하드코딩처럼 이런식으로 할 수밖에 없다..

def GET_BELT_MATERIAL_VNUM(vnum, subType = 0):
	# 현재는 모든 벨트에는 하나의 아이템(#18900)만 삽입 가능
	return 18900

##################################################################
## 자동물약 (legacy families remain recognized during the permanent migration)

AUTO_POTION_SUN_VNUM = 72726
AUTO_POTION_MOON_VNUM = 72730
AUTO_POTION_HP_VNUMS = (39037, 39038, 39039, 72723, 72724, 72725, 72726, 76021, 76022, 79012)
AUTO_POTION_SP_VNUMS = (39040, 39041, 39042, 72727, 72728, 72729, 72730, 76004, 76005, 79013)

# 해당 vnum이 자동물약인가?
def IS_AUTO_POTION(itemVnum):
	return IS_AUTO_POTION_HP(itemVnum) or IS_AUTO_POTION_SP(itemVnum)

# automatic Bravery Cape is an inventory toggle; the server sets
# metin socket 2 while it is active (sockets 0/1 hold the first-use expiry).
AUTO_BRAVE_CAPE_ACTIVE_SOCKET = 2

def IS_AUTO_BRAVE_CAPE(itemVnum):
	return 501001 <= itemVnum <= 501004

# 해당 vnum이 HP 자동물약인가?
def IS_AUTO_POTION_HP(itemVnum):
	if itemVnum in AUTO_POTION_HP_VNUMS:
		return 1

	return 0

# 해당 vnum이 SP 자동물약인가?
def IS_AUTO_POTION_SP(itemVnum):
	if itemVnum in AUTO_POTION_SP_VNUMS:
		return 1

	return 0

if app.ENABLE_GROWTH_PET_SYSTEM:
	def IS_PET_ITEM(itemVnum):
		if itemVnum == 0:
			return 0
			
		item.SelectItem(itemVnum)
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()
		
		if itemType == item.ITEM_TYPE_PET and itemSubType == item.PET_UPBRINGING:
			return 1
			
		return 0

if app.ENABLE_REFINE_ELEMENT_SYSTEM:
	import player
	import re

	def GetItemLinkRefineElementTokenStartIndex():
		idx = 3
		if app.ENABLE_ITEM_SOCKET5:
			idx += 5
		else:
			idx += 3
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			idx += 1
		if app.ENABLE_APPLY_RANDOM:
			idx += 8
		return idx

	def __IsRefineElementTokenBlock(refineTokens):
		if not refineTokens or len(refineTokens) < 8:
			return False

		if all(int(token, 16) == 0 for token in refineTokens):
			return True

		try:
			apply_type = int(refineTokens[0], 16)
			grade = int(refineTokens[1], 16)
		except ValueError:
			return False

		if grade <= 0 or grade > item.REFINE_ELEMENT_MAX:
			return False

		import uiRefine
		return apply_type in uiRefine.REFINE_ELEMENT_KIND_TUPLE

	def AppendRefineElementToItemLink(link, refine_element):
		if not link or refine_element is None:
			return link

		match = re.search(r'(\|H)([^|]+)(\|h)', link)
		if not match:
			return link

		hyperlink = match.group(2)
		tokens = hyperlink.split(':')
		if not tokens or tokens[0] != 'item':
			return link

		refineStart = GetItemLinkRefineElementTokenStartIndex()
		if len(tokens) >= refineStart + 8:
			if __IsRefineElementTokenBlock(tokens[refineStart:refineStart + 8]):
				return link

		try:
			apply_type = int(refine_element[0])
			grade = int(refine_element[1])
			values = refine_element[2]
			bonus = refine_element[3]
		except (TypeError, ValueError, IndexError):
			return link

		refineTokens = [
			'%x' % apply_type,
			'%x' % grade,
			'%x' % int(values[0]),
			'%x' % int(values[1]),
			'%x' % int(values[2]),
			'%x' % int(bonus[0]),
			'%x' % int(bonus[1]),
			'%x' % int(bonus[2]),
		]

		newHyperlink = ':'.join(tokens[:refineStart] + refineTokens + tokens[refineStart:])
		return link.replace(hyperlink, newHyperlink, 1)

	def GetItemLinkEx(slotIndex, window_type=player.INVENTORY):
		if window_type == player.INVENTORY:
			link = player.GetItemLink(slotIndex)
			refine_element = player.GetItemRefineElement(window_type, slotIndex)
		else:
			link = player.GetItemLink(window_type, slotIndex)
			refine_element = player.GetItemRefineElement(window_type, slotIndex)

		return AppendRefineElementToItemLink(link, refine_element)

# VIP elf outfits of the elf-form Buffi: the whole range the server accepts.
VIP_ELF_OUTFIT_FIRST = 49101
VIP_ELF_OUTFIT_LAST = 49109

def IS_VIP_ELF_OUTFIT(vnum):
	return VIP_ELF_OUTFIT_FIRST <= vnum <= VIP_ELF_OUTFIT_LAST

# Sigil I-V. The item table gives them no kind of their own (ITEM_MATERIAL like
# other materials) and the client receives no server list of shop price items,
# so the icon price row of the shop keeps this one range.
SIGIL_FIRST = 91200
SIGIL_LAST = 91204

def IS_SIGIL(vnum):
	return SIGIL_FIRST <= vnum <= SIGIL_LAST
