# -*- coding: utf-8 -*-
import app
import constInfo
import background

if app.ENABLE_GENDER_ALIGNMENT:
	import chr, net
	GENDER_FEMALE = 0
	GENDER_MALE = 1

MAP_TRENT02 = "MAP_TRENT02" # 임시
MAP_WL = "MAP_WL" # 임시
MAP_NUSLUCK = "MAP_NUSLUCK" # 임시 
MAP_TREE2 = "MAP_TREE2"

BLEND_POTION_NO_TIME = "BLEND_POTION_NO_TIME"
BLEND_POTION_NO_INFO = "BLEND_POTION_NO_INFO"

APP_TITLE = "Althea 2026 - DEV"

# Pet window fallbacks. Locale packs may override these symbols at load time.
PET_REVIVE_NEEDS_PROTEIN_BAR = u"K oživení potřebuješ Proteinovou tyčinku."
PET_ALBUM_HUMANS = u"Silný proti pololidem"
PET_ALBUM_MONSTERS = u"Silný proti příšerám"
PET_ALBUM_STAT_VALUE = u"+%s %% (%s %%)"

GUILD_HEADQUARTER = "Main Building"
GUILD_FACILITY = "Facility"
GUILD_OBJECT = "Object"
GUILD_MEMBER_COUNT_INFINITY = "INFINITY"

LOGIN_CONNECTION_CLOSED = "The connection to the server was interrupted. To reconnect, press Play in the launcher."

LOGIN_LAUNCHER_REQUIRED = "Start the game using Play in the launcher."

LOGIN_FAILURE_WEB_BLOCK = "BLOCK_LOGIN(WEB)"
LOGIN_FAILURE_BLOCK_LOGIN = "BLOCK_LOGIN"
LOGIN_FAILURE_DEVICE_LIMIT = "At most two accounts may be logged in on this device at the same time."
LOGIN_FAILURE_DEVICE_ID = "Device identification failed. Restart the client or contact support."
LOGIN_FAILURE_DEVICE_APPROVAL = "Approve this device in account management before logging in."
LOGIN_FAILURE_DEVICE_COOLDOWN = "A registered device was changed recently. Try again after the 12-hour protection period."
LOGIN_FAILURE_DEVICE_UNAVAILABLE = "Device verification is temporarily unavailable. Please try again later."
CHANNEL_NOTIFY_FULL = "CHANNEL_NOTIFY_FULL"

GUILD_BUILDING_LIST_TXT = app.GetLocalePath() + "/GuildBuildingList.txt"

GUILD_MARK_MIN_LEVEL = "1"
GUILD_MARK_NOT_ENOUGH_LEVEL = "길드레벨 1이상 부터 가능합니다."

ERROR_MARK_UPLOAD_NEED_RECONNECT = "UploadMark: Reconnect to game"
ERROR_MARK_CHECK_NEED_RECONNECT = "CheckMark: Reconnect to game"

VIRTUAL_KEY_ALPHABET_LOWERS = r"[1234567890]/qwertyuiop\=asdfghjkl;`'zxcvbnm.,"
VIRTUAL_KEY_ALPHABET_UPPERS = r'{1234567890}?QWERTYUIOP|+ASDFGHJKL:~"ZXCVBNM<>'
VIRTUAL_KEY_SYMBOLS = '!@#$%^&*()_+|{}:"<>?~'
VIRTUAL_KEY_NUMBERS = "1234567890-=\\[];',./`"
VIRTUAL_KEY_SYMBOLS_BR = '!@#$%^&*()_+|{}:"<>?~蓀呻郵悠壬蛭衝銜'

__IS_ENGLISH = "ENGLISH" == app.GetLocaleServiceName()
__IS_HONGKONG = "HONGKONG" == app.GetLocaleServiceName()
__IS_NEWCIBN = "locale/newcibn" == app.GetLocalePath()
__IS_EUROPE = "EUROPE" == app.GetLocaleServiceName()
__IS_CANADA = "locale/ca" == app.GetLocalePath()
__IS_BRAZIL = "locale/br" == app.GetLocalePath()
__IS_SINGAPORE = "locale/sg" == app.GetLocalePath()
__IS_VIETNAM = "locale/vn" == app.GetLocalePath()
__IS_ARABIC = "locale/ae" == app.GetLocalePath()
__IS_CIBN10 = "locale/cibn10" == app.GetLocalePath()
__IS_WE_KOREA = "locale/we_korea" == app.GetLocalePath()
__IS_TAIWAN = "locale/taiwan" == app.GetLocalePath()
__IS_JAPAN = "locale/japan" == app.GetLocalePath()
LOGIN_FAILURE_WRONG_SOCIALID = "ASDF"
LOGIN_FAILURE_SHUTDOWN_TIME = "ASDF"

if __IS_CANADA:
	__IS_EUROPE = True

def IsYMIR():
	return "locale/ymir" == app.GetLocalePath()

def IsJAPAN():
	return "locale/japan" == app.GetLocalePath()

def IsENGLISH():
	global __IS_ENGLISH
	return __IS_ENGLISH

def IsHONGKONG():
	global __IS_HONGKONG
	return __IS_HONGKONG

def IsTAIWAN():
	return "locale/taiwan" == app.GetLocalePath()

def IsNEWCIBN():
	return "locale/newcibn" == app.GetLocalePath()

def IsCIBN10():
	global __IS_CIBN10
	return __IS_CIBN10

def IsEUROPE():
	global __IS_EUROPE
	return __IS_EUROPE

def IsCANADA():
	global __IS_CANADA
	return __IS_CANADA

def IsBRAZIL():
	global __IS_BRAZIL
	return __IS_BRAZIL

def IsVIETNAM():
	global __IS_VIETNAM
	return __IS_VIETNAM

def IsSINGAPORE():
	global __IS_SINGAPORE
	return __IS_SINGAPORE

def IsARABIC():
	global __IS_ARABIC
	return __IS_ARABIC

def IsWE_KOREA():
	return "locale/we_korea" == app.GetLocalePath()

# SUPPORT_NEW_KOREA_SERVER
def LoadLocaleData():
	if IsYMIR():
		import net
		SERVER = "쾌도 서버"
		if SERVER == net.GetServerInfo()[:len(SERVER)]:
			app.SetCHEONMA(0)
			app.LoadLocaleData("locale/we_korea")
			constInfo.ADD_DEF_BONUS_ENABLE = 0
		else:
			app.SetCHEONMA(1)
			app.LoadLocaleData("locale/ymir")
			constInfo.ADD_DEF_BONUS_ENABLE = 1
	else:
		app.LoadLocaleData(app.GetLocalePath())

def IsCHEONMA():
	return IsYMIR() # 이제 YMIR 로케일은 무조건 천마서버임. 천마서버가 문을 닫기 전까지 변할 일 없음.

# END_OF_SUPPORT_NEW_KOREA_SERVER

def mapping(**kwargs): return kwargs

def SNA(text):
	def f(x):
		return text
	return f

def SA(text):
	def f(x):
		return text % x
	return f

def SAA(text):
	def f(x1, x2):
		return text % (x1, x2)
	return f

def SAAAA(text):
	def f(x1, x2, x3, x4):
		return text % (x1, x2, x3, x4)
	return f

def SAN(text):
	def f(x1, x2):
		return text % x1
	return f

def LoadLocaleFile(srcFileName, localeDict):
	funcDict = {"SA":SA, "SNA":SNA, "SAA":SAA, "SAN":SAN, "SAAAA":SAAAA,}

	try:
		lines = open(srcFileName, "r").readlines()
	except IOError:
		import dbg
		dbg.LogBox("LoadLocaleError(%(srcFileName)s)" % locals())
		app.Abort()

	for lineIndex, line in enumerate(lines, 1):
		try:
			localeLine = line.rstrip("\r\n")
			if not localeLine:
				continue

			tokens = localeLine.split("\t")
			if len(tokens) == 2:
				localeDict[tokens[0]] = tokens[1]
			elif len(tokens) >= 3:
				type = tokens[2].strip()
				if type:
					localeDict[tokens[0]] = funcDict[type](tokens[1])
				else:
					localeDict[tokens[0]] = tokens[1]
			else:
				raise RuntimeError("Unknown TokenSize")

		except:
			import dbg
			dbg.LogBox("%s: line(%d): %s" % (srcFileName, lineIndex, line), "Error")
			raise

all = ["locale", "error"]

if IsEUROPE() and IsBRAZIL():
	FN_GM_MARK = "locale/common/effect/gm.mse"
	LOCALE_FILE_NAME = "%s/locale_game.txt" % app.GetLocalePath()
	NEW_LOCALE_FILE_NAME = "%s/new_locale_game.txt" % app.GetLocalePath()

	constInfo.IN_GAME_SHOP_ENABLE = 0
elif IsSINGAPORE():
	FN_GM_MARK = "locale/common/effect/gm.mse"
	LOCALE_FILE_NAME = "%s/locale_game.txt" % app.GetLocalePath()
	NEW_LOCALE_FILE_NAME = "%s/new_locale_game.txt" % app.GetLocalePath()

	constInfo.IN_GAME_SHOP_ENABLE = 0
elif IsNEWCIBN():
	##게임명이깨진다.
	APP_TITLE = "劤祿莖2"
	FN_GM_MARK = "locale/common/effect/gm.mse"
	LOCALE_FILE_NAME = "%s/locale_game.txt" % app.GetLocalePath()
	NEW_LOCALE_FILE_NAME = "%s/new_locale_game.txt" % app.GetLocalePath()

	constInfo.IN_GAME_SHOP_ENABLE = 1
elif IsTAIWAN():
	APP_TITLE = "갓III곌"
	FN_GM_MARK = "locale/common/effect/gm.mse"
	LOCALE_FILE_NAME = "%s/locale_game.txt" % app.GetLocalePath()
	NEW_LOCALE_FILE_NAME = "%s/new_locale_game.txt" % app.GetLocalePath()

	constInfo.IN_GAME_SHOP_ENABLE = 1
else:
	FN_GM_MARK = "locale/common/effect/gm.mse"
	LOCALE_FILE_NAME = "%s/locale_game.txt" % app.GetLocalePath()
	NEW_LOCALE_FILE_NAME = "%s/new_locale_game.txt" % app.GetLocalePath()

	constInfo.IN_GAME_SHOP_ENABLE = 1

LoadLocaleFile(LOCALE_FILE_NAME, locals())
LoadLocaleFile(NEW_LOCALE_FILE_NAME, locals())

# The legacy locale tables use different code pages. Keep UTF-8-safe
# fallbacks here until every language owns GLOBAL_HUB_* rows; individual table
# values still override these defaults when present.
_GLOBAL_HUB_CZECH = (
	app.GetLocalePath().replace("\\", "/").lower().endswith("/cz")
)
if "GLOBAL_HUB_NAME" not in locals():
	GLOBAL_HUB_NAME = (
		u"Společné město" if _GLOBAL_HUB_CZECH else u"Shared City"
	)
if "GLOBAL_HUB_ENTER_NOTICE" not in locals():
	GLOBAL_HUB_ENTER_NOTICE = (
		u"Připojeno: Společné město."
		if _GLOBAL_HUB_CZECH
		else u"Connected: Shared City."
	)
if "GLOBAL_HUB_CHANNEL_SWITCH_BLOCKED" not in locals():
	GLOBAL_HUB_CHANNEL_SWITCH_BLOCKED = (
		u"Ve Společném městě nelze měnit kanál."
		if _GLOBAL_HUB_CZECH
		else u"Channel switching is unavailable in the Shared City."
	)
if "GLOBAL_HUB_ESC_CHANNEL_STATUS" not in locals():
	GLOBAL_HUB_ESC_CHANNEL_STATUS = (
		u"Společné město - změna CH nedostupná"
		if _GLOBAL_HUB_CZECH
		else u"Shared City - CH switching unavailable"
	)

# Map index 1 keeps its legacy runtime identity, but every player-facing map
# label must describe the unified hub rather than the retired Yongan district.
MAP_A1 = GLOBAL_HUB_NAME
del _GLOBAL_HUB_CZECH

DUNGEON_DISPLAY_NAMES = {
	5695: "Orc Sanctuary",
	5672: "Ancient Minotaur Dungeon",
	5710: "Mystical Bamboo Dungeon",
	5731: "Temple of the Drowned God",
	2092: "King Spider",
	4944: "Ghost Pirate Cave",
	4815: "Frostbane Fortress",
	4685: "Demon Dungeon",
	4701: "Jiangshi Temple",
	4760: "Mazarif Ruins",
	4856: "Duratus Dungeon",
	4549: "Andun Temple",
}

_DUNGEON_DISPLAY_NAMES_CZECH = (
	app.GetLocalePath().replace("\\", "/").lower().endswith("/cz")
)
if _DUNGEON_DISPLAY_NAMES_CZECH:
	DUNGEON_DISPLAY_NAMES.update({
		5695: u"Svatyn\u011b Ork\u016f",
		5672: u"Doup\u011b Prastar\u00e9ho Minotaura",
		5710: u"Mystick\u00fd Bambusov\u00fd chr\u00e1m",
		5731: u"Chr\u00e1m Utopen\u00e9ho Boha",
		2092: u"Pavou\u010d\u00ed Kr\u00e1lovstv\u00ed",
		4944: u"Jeskyn\u011b P\u0159\u00edzra\u010dn\u00fdch Pir\u00e1t\u016f",
		4815: u"Ledov\u00e1 Citadela",
		4685: u"Br\u00e1na Zatracen\u00ed",
		4701: u"Chr\u00e1m Jiangshi",
		4760: u"Ruiny Mazarifa",
		4856: u"Duratův dungeon",
		4549: u"Andunův chrám",
	})

########################################################################################################
## NOTE : 아이템을 버릴때 "무엇을/를 버리시겠습니까?" 문자열의 조사 선택을 위한 코드
dictSingleWord = {
	"m":1, "n":1, "r":1, "M":1, "N":1, "R":1, "l":1, "L":1, "1":1, "3":1, "6":1, "7":1, "8":1, "0":1,
}

dictDoubleWord = {
	"가":1, "갸":1, "거":1, "겨":1, "고":1, "교":1, "구":1, "규":1, "그":1, "기":1, "개":1, "걔":1, "게":1, "계":1, "과":1, "괘":1, "궈":1, "궤":1, "괴":1, "귀":1, "긔":1,
	"까":1, "꺄":1, "꺼":1, "껴":1, "꼬":1, "꾜":1, "꾸":1, "뀨":1, "끄":1, "끼":1, "깨":1, "꺠":1, "께":1, "꼐":1, "꽈":1, "꽤":1, "꿔":1, "꿰":1, "꾀":1, "뀌":1, "끠":1,
	"나":1, "냐":1, "너":1, "녀":1, "노":1, "뇨":1, "누":1, "뉴":1, "느":1, "니":1, "내":1, "냬":1, "네":1, "녜":1, "놔":1, "놰":1, "눠":1, "눼":1, "뇌":1, "뉘":1, "늬":1,
	"다":1, "댜":1, "더":1, "뎌":1, "도":1, "됴":1, "두":1, "듀":1, "드":1, "디":1, "대":1, "댸":1, "데":1, "뎨":1, "돠":1, "돼":1, "둬":1, "뒈":1, "되":1, "뒤":1, "듸":1,
	"따":1, "땨":1, "떠":1, "뗘":1, "또":1, "뚀":1, "뚜":1, "뜌":1, "뜨":1, "띠":1, "때":1, "떄":1, "떼":1, "뗴":1, "똬":1, "뙈":1, "뚸":1, "뛔":1, "뙤":1, "뛰":1, "띄":1,
	"라":1, "랴":1, "러":1, "려":1, "로":1, "료":1, "루":1, "류":1, "르":1, "리":1, "래":1, "럐":1, "레":1, "례":1, "롸":1, "뢔":1, "뤄":1, "뤠":1, "뢰":1, "뤼":1, "릐":1,
	"마":1, "먀":1, "머":1, "며":1, "모":1, "묘":1, "무":1, "뮤":1, "므":1, "미":1, "매":1, "먜":1, "메":1, "몌":1, "뫄":1, "뫠":1, "뭐":1, "뭬":1, "뫼":1, "뮈":1, "믜":1,
	"바":1, "뱌":1, "버":1, "벼":1, "보":1, "뵤":1, "부":1, "뷰":1, "브":1, "비":1, "배":1, "뱨":1, "베":1, "볘":1, "봐":1, "봬":1, "붜":1, "붸":1, "뵈":1, "뷔":1, "븨":1,
	"빠":1, "뺘":1, "뻐":1, "뼈":1, "뽀":1, "뾰":1, "뿌":1, "쀼":1, "쁘":1, "삐":1, "빼":1, "뺴":1, "뻬":1, "뼤":1, "뽜":1, "뽸":1, "뿨":1, "쀄":1, "뾔":1, "쀠":1, "쁴":1,
	"사":1, "샤":1, "서":1, "셔":1, "소":1, "쇼":1, "수":1, "슈":1, "스":1, "시":1, "새":1, "섀":1, "세":1, "셰":1, "솨":1, "쇄":1, "숴":1, "쉐":1, "쇠":1, "쉬":1, "싀":1,
	"싸":1, "쌰":1, "써":1, "쎠":1, "쏘":1, "쑈":1, "쑤":1, "쓔":1, "쓰":1, "씨":1, "쌔":1, "썌":1, "쎄":1, "쎼":1, "쏴":1, "쐐":1, "쒀":1, "쒜":1, "쐬":1, "쒸":1, "씌":1,
	"아":1, "야":1, "어":1, "여":1, "오":1, "요":1, "우":1, "유":1, "으":1, "이":1, "애":1, "얘":1, "에":1, "예":1, "와":1, "왜":1, "워":1, "웨":1, "외":1, "위":1, "의":1,
	"자":1, "쟈":1, "저":1, "져":1, "조":1, "죠":1, "주":1, "쥬":1, "즈":1, "지":1, "재":1, "쟤":1, "제":1, "졔":1, "좌":1, "좨":1, "줘":1, "줴":1, "죄":1, "쥐":1, "즤":1,
	"짜":1, "쨔":1, "쩌":1, "쪄":1, "쪼":1, "쬬":1, "쭈":1, "쮸":1, "쯔":1, "찌":1, "째":1, "쨰":1, "쩨":1, "쪠":1, "쫘":1, "쫴":1, "쭤":1, "쮀":1, "쬐":1, "쮜":1, "쯰":1,
	"차":1, "챠":1, "처":1, "쳐":1, "초":1, "쵸":1, "추":1, "츄":1, "츠":1, "치":1, "채":1, "챼":1, "체":1, "쳬":1, "촤":1, "쵀":1, "춰":1, "췌":1, "최":1, "취":1, "츼":1,
	"카":1, "캬":1, "커":1, "켜":1, "코":1, "쿄":1, "쿠":1, "큐":1, "크":1, "키":1, "캐":1, "컈":1, "케":1, "켸":1, "콰":1, "쾌":1, "쿼":1, "퀘":1, "쾨":1, "퀴":1, "킈":1,
	"타":1, "탸":1, "터":1, "텨":1, "토":1, "툐":1, "투":1, "튜":1, "트":1, "티":1, "태":1, "턔":1, "테":1, "톄":1, "톼":1, "퇘":1, "퉈":1, "퉤":1, "퇴":1, "튀":1, "틔":1,
	"파":1, "퍄":1, "퍼":1, "펴":1, "포":1, "표":1, "푸":1, "퓨":1, "프":1, "피":1, "패":1, "퍠":1, "페":1, "폐":1, "퐈":1, "퐤":1, "풔":1, "풰":1, "푀":1, "퓌":1, "픠":1,
	"하":1, "햐":1, "허":1, "혀":1, "호":1, "효":1, "후":1, "휴":1, "흐":1, "히":1, "해":1, "햬":1, "헤":1, "혜":1, "화":1, "홰":1, "훠":1, "훼":1, "회":1, "휘":1, "희":1,
}

locale = mapping(
)

def GetAuxiliaryWordType(text):
	textLength = len(text)

	if textLength > 1:
		singleWord = text[-1]

		if (singleWord >= '0' and singleWord <= '9') or\
			(singleWord >= 'a' and singleWord <= 'z') or\
			(singleWord >= 'A' and singleWord <= 'Z'):
			if singleWord not in dictSingleWord:
				return 1

		elif text[-1:] in dictDoubleWord: # py2 CP949: last syllable was text[-2:] (2 bytes); py3 str: 1 char
			return 1

	return 0

def CutMoneyString(sourceText, startIndex, endIndex, insertingText, backText):
	sourceLength = len(sourceText)

	if sourceLength < startIndex:
		return backText

	text = sourceText[max(0, sourceLength-endIndex):sourceLength-startIndex]

	if not text:
		return backText

	if int(text) <= 0:
		return backText

	text = str(int(text))

	if backText:
		backText = " " + backText

	return text + insertingText + backText

if app.ENABLE_GEM_SYSTEM:
	def SecondToHMGolbal(time):
		if time < 60:
			return "00:01"

		minute = int((time / 60) % 60)
		hour = int((time / 60) / 60)

		text = ""

		if hour > 0:
			if hour >= 10:
				text += str(hour) + ":"
			else:
				text += "0" + str(hour) + ":"
		else:
			text += "00:"

		if minute > 0:
			if minute >= 10:
				text += str(minute)
			else:
				text += "0" + str(minute)

		return text

def SecondToDHMS(time):
	if time < 60:
		if IsARABIC():
			return "%.2f %s" % (time, SECOND)
		else:
			return "%.2f %s" % (time, SECOND)

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60) % 24
	day = int(int((time / 60) / 60) / 24)

	text = ""

	if day > 0:
		text += str(day) + DAY
		text += " "

	if hour > 0:
		text += str(hour) + HOUR
		text += " "

	if minute > 0:
		text += str(minute) + MINUTE

	if second > 0:
		text += str(second) + SECOND

	return text

def SecondToDHM(time):
	if time < 60:
		if IsARABIC():
			return "%.2f %s" % (time, SECOND)
		else:
			return "0" + MINUTE

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60) % 24
	day = int(int((time / 60) / 60) / 24)

	text = ""

	if day > 0:
		text += str(day) + DAY
		text += " "

	if hour > 0:
		text += str(hour) + HOUR
		text += " "

	if minute > 0:
		text += str(minute) + MINUTE

	return text

def SecondToHM(time):
	if time < 60:
		if IsARABIC():
			return "%.2f %s" % (time, SECOND)
		else:
			return "0" + MINUTE

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60)

	text = ""

	if hour > 0:
		text += str(hour) + HOUR
		if hour > 0:
			text += " "

	if minute > 0:
		text += str(minute) + MINUTE

	return text

def SecondToDay(time):
	if time < 60:
		return "1" + DAY

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60) % 24
	day = int(int((time / 60) / 60) / 24)

	if day < 1:
		day = 1

	if day > 9999:
		day = 9999

	text = str(day) + DAY
	return text

def SecondToDayNumber(time):
	if time < 60:
		return 1

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60) % 24
	day = int(int((time / 60) / 60) / 24)

	if day < 1:
		day = 1

	if day > 9999:
		day = 9999

	return day

def SecondToH(time):
	hour = int((time / 60) / 60)

	text = ""
	hour = max(0, hour)
	text += str(hour)

	return text

#if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM or app.ENABLE_12ZI:
def SecondToColonTypeHMS(time):
	if time < 60:
		return "00:00:%02d" % (time)

	second = int(time % 60)
	minute = int((time / 60) % 60)
	hour = int((time / 60) / 60)

	return "%02d:%02d:%02d" % (hour, minute, second)

def SecondToColonTypeMS(time):
	second = int(time % 60)
	minute = int((time / 60) % 60)

	return "%02d:%02d" % (minute, second)

if app.ENABLE_GENDER_ALIGNMENT:
	def GetAlignmentTitleName(currentAlignment):
		titleNameTuple = TITLE_NAME_DICT.get(chr.RaceToSex(net.GetMainActorRace()), ('UNKNOWN_GENDER',))

		for alignmentIndex, alignmentValue in enumerate((12000, 8000, 4000, 1000, 0, -4000, -8000, -12000)):
			if currentAlignment >= alignmentValue:
				return titleNameTuple[alignmentIndex]

		return titleNameTuple[-1]
else:
	def GetAlignmentTitleName(alignment):
		if alignment >= 12000:
			return TITLE_NAME_LIST[0]
		elif alignment >= 8000:
			return TITLE_NAME_LIST[1]
		elif alignment >= 4000:
			return TITLE_NAME_LIST[2]
		elif alignment >= 1000:
			return TITLE_NAME_LIST[3]
		elif alignment >= 0:
			return TITLE_NAME_LIST[4]
		elif alignment > -4000:
			return TITLE_NAME_LIST[5]
		elif alignment > -8000:
			return TITLE_NAME_LIST[6]
		elif alignment > -12000:
			return TITLE_NAME_LIST[7]

		return TITLE_NAME_LIST[8]

OPTION_PVPMODE_MESSAGE_DICT = {
	0 : PVP_MODE_NORMAL,
	1 : PVP_MODE_REVENGE,
	2 : PVP_MODE_KILL,
	3 : PVP_MODE_PROTECT,
	4 : PVP_MODE_GUILD,
}

error = mapping(
	CREATE_WINDOW = GAME_INIT_ERROR_MAIN_WINDOW,
	CREATE_CURSOR = GAME_INIT_ERROR_CURSOR,
	CREATE_NETWORK = GAME_INIT_ERROR_NETWORK,
	CREATE_ITEM_PROTO = GAME_INIT_ERROR_ITEM_PROTO,
	CREATE_MOB_PROTO = GAME_INIT_ERROR_MOB_PROTO,
	CREATE_NO_DIRECTX = GAME_INIT_ERROR_DIRECTX,
	CREATE_DEVICE = GAME_INIT_ERROR_GRAPHICS_NOT_EXIST,
	CREATE_NO_APPROPRIATE_DEVICE = GAME_INIT_ERROR_GRAPHICS_BAD_PERFORMANCE,
	CREATE_FORMAT = GAME_INIT_ERROR_GRAPHICS_NOT_SUPPORT_32BIT,
	NO_ERROR = ""
)

GUILDWAR_NORMAL_DESCLIST = [GUILD_WAR_USE_NORMAL_MAP, GUILD_WAR_LIMIT_30MIN, GUILD_WAR_WIN_CHECK_SCORE]
GUILDWAR_WARP_DESCLIST = [GUILD_WAR_USE_BATTLE_MAP, GUILD_WAR_WIN_WIPE_OUT_GUILD, GUILD_WAR_REWARD_POTION]
GUILDWAR_CTF_DESCLIST = [GUILD_WAR_USE_BATTLE_MAP, GUILD_WAR_WIN_TAKE_AWAY_FLAG1, GUILD_WAR_WIN_TAKE_AWAY_FLAG2, GUILD_WAR_REWARD_POTION]

MINIMAP_ZONE_NAME_DICT = {
	# Runtime arena index 201 reuses a historical war-map index; name it explicitly.
	"metin2_map_pvp_arena": globals().get("PVP_MATCHMAKING_TITLE", "Hodnocená aréna"),
	"metin2_map_a1" :					MAP_A1,
	"map_a2" :							MAP_A2,
	"metin2_map_a3" :					MAP_A3,
	"map_b2" :							MAP_B2,
	"metin2_map_b3" :					MAP_B3,
	"map_c2" :							MAP_C2,
	"metin2_map_c3" :					MAP_C3,
	"map_n_snowm_01" :					MAP_SNOW,
	"metin2_map_n_flame_01" :			MAP_FLAME,
	"metin2_map_n_desert_01" :			MAP_DESERT,
	"metin2_map_milgyo" :				MAP_TEMPLE,
	"metin2_map_spiderdungeon" :		MAP_SPIDER,
	"metin2_map_spiderdungeon_03" :	(
		DUNGEON_DISPLAY_NAMES[2092]
		if _DUNGEON_DISPLAY_NAMES_CZECH
		else MAP_SPIDERDUNGEON_03
	),
	"metin2_map_deviltower1" :			MAP_SKELTOWER,
	"metin2_map_guild_01" :				MAP_AG,
	"metin2_map_guild_02" :				MAP_BG,
	"metin2_map_guild_03" :				MAP_CG,
	"metin2_map_trent" :				MAP_TREE,
	"metin2_map_trent02" :				MAP_TREE2,
	"metin2_map_WL_01" :		MAP_WL,
	"metin2_map_nusluck01" :	MAP_NUSLUCK,
	"Metin2_map_CapeDragonHead" :		MAP_CAPE,
	"metin2_map_Mt_Thunder" :			MAP_THUNDER,
	"metin2_map_dawnmist_dungeon_01" :	MAP_DAWNMIST_DUNGEON_01,
	"metin2_map_dawnmistwood" :			MAP_DAWN,
	"metin2_map_defensewave" :			MAP_DEFENSE_WAVE,
	"metin2_map_defensewave_port" :		MAP_DEFENSE_WAVE_PORT,
	"metin2_map_BayBlackSand" :			MAP_BAY,
	"metin2_map_n_flame_dragon" :		MAP_N_FLAME_DRAGON,
	"sung_mahi_desert" :				"Poušť Sung Mahi",
	"orktal" :							"Orktal",
	"plechito_ancient_jungle" :			"Ancient Jungle",
	"plechito_mirage_island" :			("Ztracený ostrov" if _DUNGEON_DISPLAY_NAMES_CZECH else "Mirage Island"),
	"plechito_desert_map_01" :			("Písky utrpení" if _DUNGEON_DISPLAY_NAMES_CZECH else "Sands of Suffering"),
	"horus_battleground" :				("Pomezí padlých" if _DUNGEON_DISPLAY_NAMES_CZECH else "Horus Battleground"),
	"realis_forsaken_crypt" :			"Forsaken Crypt",
	"realis_glacial_reach_d" :			"Glacial Reach",
	"realis_inferno_citadel" :			"Inferno Citadel",
	"realis_lotusshade_dungeon" :		"Lotusshade Dungeon",
	"realis_s_terrace" :				"Soulstone Terrace",
	"realis_shifting_sands" :			"Shifting Sands",
	"jotun_thrym" :					DUNGEON_DISPLAY_NAMES[5695],
	"plechito_pirate_cave_ghost" :		DUNGEON_DISPLAY_NAMES[4944],
	"plechito_minotaur_dungeon" :		DUNGEON_DISPLAY_NAMES[5672],
	"plechito_demon_dungeon23" :		DUNGEON_DISPLAY_NAMES[4685],
	"plechito_viking_dungeon" :		DUNGEON_DISPLAY_NAMES[4815],
	"plechito_jiangshi_temple" :		DUNGEON_DISPLAY_NAMES[4701],
	"plechito_ramadan2024_dungeon" :	DUNGEON_DISPLAY_NAMES[4760],
	"plechito_panda_dungeon" :		DUNGEON_DISPLAY_NAMES[5710],
	"plechito_summer2025_dungeon" :	DUNGEON_DISPLAY_NAMES[5731],
	"duratus_dungeon" :			DUNGEON_DISPLAY_NAMES[4856],
	"plechito_andun_temple" :		DUNGEON_DISPLAY_NAMES[4549],
	"plechito_egypt_crypt" :		(
		u"Hrobka tyranského faraona"
		if _DUNGEON_DISPLAY_NAMES_CZECH
		else "Crypt of the Tyrant Pharaoh"
	),
}

JOBINFO_TITLE = [
	[JOB_WARRIOR0, JOB_WARRIOR1, JOB_WARRIOR2,],
	[JOB_ASSASSIN0, JOB_ASSASSIN1, JOB_ASSASSIN2,],
	[JOB_SURA0, JOB_SURA1, JOB_SURA2,],
	[JOB_SHAMAN0, JOB_SHAMAN1, JOB_SHAMAN2,],
	[JOB_WOLFMAN0, JOB_WOLFMAN1, JOB_WOLFMAN1,],
]

if app.WJ_SHOW_PARTY_ON_MINIMAP:
	MINIMAP_ZONE_NAME_DICT_BY_IDX = {
		0 : "",
		1 : MAP_A1,
		3 : MAP_A3,
		4 : MAP_GUILD_01,
		5 : MAP_MONKEY_DUNGEON_11,
		6 : GUILD_VILLAGE_01,
		21 : MAP_B1,
		23 : MAP_B3,
		24 : MAP_GUILD_02,
		25 : MAP_MONKEY_DUNGEON_12,
		26 : GUILD_VILLAGE_02,
		41 : MAP_C1,
		43 : MAP_C3,
		44 : MAP_GUILD_03,
		45 : MAP_MONKEY_DUNGEON_13,
		46 : GUILD_VILLAGE_03,
		61 : MAP_N_SNOWM_01,
		62 : MAP_N_FLAME_01,
		63 : MAP_N_DESERT_01,
		64 : MAP_N_THREEWAY,
		65 : MAP_MILGYO,
		66 : MAP_DEVILTOWER1,
		67 : MAP_TRENT,
		68 : MAP_TRENT02,
		69 : MAP_WL_01,
		70 : MAP_NUSLUCK01,
		71 : MAP_SPIDERDUNGEON_02,
		72 : MAP_SKIPIA_DUNGEON_01,
		73 : MAP_SKIPIA_DUNGEON_02,
		74 : MAP_N_SNOWM_02,
		75 : MAP_N_FLAME_02,
		76 : MAP_N_DESERT_02,
		77 : MAP_A2_1,
		78 : MAP_MILGYO_A,
		79 : MAP_TRENT_A,
		80 : MAP_TRENT02_A,
		81 : MAP_WEDDING_01,
		91 : MAP_E,
		92 : MAP_E,
		93 : MAP_E,
		103 : MAP_T1,
		104 : MAP_SPIDERDUNGEON,
		105 : MAP_T2,
		107 : MAP_MONKEY_DUNGEON,
		108 : MAP_MONKEY_DUNGEON2,
		109 : MAP_MONKEY_DUNGEON3,
		110 : MAP_T3,
		111 : MAP_T4,
		112 : MAP_DUEL,
		113 : MAP_OXEVENT,
		114 : MAP_SUNGZI,
		118 : MAP_SUNGZI_FLAME_HILL_01,
		119 : MAP_SUNGZI_FLAME_HILL_02,
		120 : MAP_SUNGZI_FLAME_HILL_03,
		121 : MAP_SUNGZI_SNOW,
		122 : MAP_SUNGZI_SNOW_PASS01,
		123 : MAP_SUNGZI_SNOW_PASS02,
		124 : MAP_SUNGZI_SNOW_PASS03,
		125 : MAP_SUNGZI_DESERT_01,
		126 : MAP_SUNGZI_DESERT_HILL_01,
		127 : MAP_SUNGZI_DESERT_HILL_02,
		128 : MAP_SUNGZI_DESERT_HILL_03,
		130 : GUILD_WAR1,
		131 : GUILD_WAR2,
		132 : GUILD_WAR3,
		133 : GUILD_WAR4,
		180 : METIN_TEST,
		181 : MAP_EMPIREWAR01,
		182 : MAP_EMPIREWAR02,
		183 : MAP_EMPIREWAR03,
		184 : MAP_SKIPIA_DUNGEON_011,
		185 : MAP_SKIPIA_DUNGEON_021,
		186 : MAP_SKIPIA_DUNGEON_012,
		187 : MAP_SKIPIA_DUNGEON_022,
		188 : MAP_SKIPIA_DUNGEON_013,
		189 : MAP_SKIPIA_DUNGEON_023,
		193 : MAP_SPIDERDUNGEON_02_1,
		194 : MAP_HOLYPLACE_FLAME,
		195 : MAP_PATHWAY_FLAME_01,
		196 : MAP_PATHWAY_FLAME_02,
		197 : MAP_PATHWAY_FLAME_03,
		198 : MAP_HOLYPLACE_ICE,
		199 : MAP_PATHWAY_ICE_01,
		200 : MAP_PATHWAY_ICE_02,
		201 : MAP_PATHWAY_ICE_03,
		202 : MAP_HOLYPLACE_DESERT,
		203 : MAP_PATHWAY_DESERT_01,
		204 : MAP_PATHWAY_DESERT_02,
		205 : MAP_PATHWAY_DESERT_03,
		208 : MAP_SKIPIA_DUNGEON_BOSS,
		209 : MAP_SKIPIA_DUNGEON_BOSS_1,
		210 : MAP_SKIPIA_DUNGEON_BOSS_2,
		211 : MAP_SKIPIA_DUNGEON_BOSS_3,
		216 : MAP_DEVILCATACOMB,
		217 : (
			DUNGEON_DISPLAY_NAMES[2092]
			if _DUNGEON_DISPLAY_NAMES_CZECH
			else MAP_SPIDERDUNGEON_03
		),
		301 : MAP_CAPEDRAGONHEAD,
		302 : MAP_DAWNMISTWOOD,
		303 : MAP_BAYBLACKSAND,
		304 : MAP_MT_THUNDER,
		351 : MAP_N_FLAME_DUNGEON_01,
		352 : MAP_N_SNOW_DUNGEON_01,
		358 : MAP_DEFENSE_WAVE,
		359 : MAP_DEFENSE_WAVE_PORT,
		360 : MAP_MISTS_OF_ISLAND,
		361 : MAP_MINIBOSS_01,
		362 : MAP_MINIBOSS_02,
		363 : MAP_BOSS_LABYRINTH,
		364 : MAP_BOSS_CRACK_SKIPIA,
		365 : MAP_BOSS_CRACK_FLAME,
		366 : MAP_BOSS_CRACK_SNOW,
		367 : MAP_BOSS_CRACK_DAWNMIST,
		368 : MAP_BOSS_AWAKEN_SKIPIA,
		369 : MAP_BOSS_AWAKEN_FLAME,
		370 : MAP_BOSS_AWAKEN_SNOW,
		371 : MAP_BOSS_AWAKEN_DAWNMIST,
		372 : MAP_GUILD_PVE,
		373 : MAP_EASTPLAIN_01,
		374 : MAP_EMPIRECASTLE,
		375 : MAP_BATTLE_ROYALE,
		376 : MAP_EASTPLAIN_02,
		377 : MAP_EASTPLAIN_03,
		378 : MAP_ELEMENTAL_DUNGEON,
		379 : MAP_ELEMENTAL_DUNGEON,
		380 : MAP_ELEMENTAL_DUNGEON,
		381 : MAP_ELEMENTAL_DUNGEON,
		382 : MAP_MAZE_DUNGEON_01,
		383 : MAP_MAZE_DUNGEON_02,
		384 : MAP_MAZE_DUNGEON_03,
		385 : MAP_SNAKE_VALLEY,
		386 : MAP_SUNGMAHEE_TOWER_WAIT,
		387 : MAP_SUNGMAHEE_TOWER_DUNGEON,
		388 : MAP_ICE_CRYSTALS_CAVE,
		389 : MAP_WHITE_DRAGON_VALLEY,
		390 : MAP_SNAKE_TEMPLE_1,
		391 : MAP_SNAKE_TEMPLE_2,
		392 : MAP_PRIVATE_SHOP_MAP,
		393 : MAP_WHITE_DRAGON_CAVE_01,
		394 : MAP_WHITE_DRAGON_CAVE_02,
		395 : MAP_WHITE_DRAGON_CAVE_BOSS,
		396 : MAP_FARMING_DUNGEON,
		399 : MAP_SECRET_DUNGEON,
		400 : MAP_OTHER_WORLD_01,
		401 : MAP_OTHER_WORLD_02,
		402 : MAP_OTHER_WORLD_03,
		403 : MAP_OTHER_WORLD_04,
		405 : "Poušť Sung Mahi",
		406 : "Orktal",
		407 : "Ancient Jungle",
		408 : ("Ztracený ostrov" if _DUNGEON_DISPLAY_NAMES_CZECH else "Mirage Island"),
		409 : ("Písky utrpení" if _DUNGEON_DISPLAY_NAMES_CZECH else "Sands of Suffering"),
		410 : ("Pomezí padlých" if _DUNGEON_DISPLAY_NAMES_CZECH else "Horus Battleground"),
		411 : "Forsaken Crypt",
		412 : "Glacial Reach",
		413 : "Inferno Citadel",
		414 : "Lotusshade Dungeon",
		415 : "Soulstone Terrace",
		416 : "Shifting Sands",
		418 : DUNGEON_DISPLAY_NAMES[5695],
		419 : DUNGEON_DISPLAY_NAMES[4944],
		420 : DUNGEON_DISPLAY_NAMES[5672],
		421 : DUNGEON_DISPLAY_NAMES[4685],
		422 : DUNGEON_DISPLAY_NAMES[4815],
		423 : DUNGEON_DISPLAY_NAMES[4701],
		424 : DUNGEON_DISPLAY_NAMES[4760],
		425 : DUNGEON_DISPLAY_NAMES[5710],
		426 : DUNGEON_DISPLAY_NAMES[5731],
		34 : DUNGEON_DISPLAY_NAMES[4856],
		157 : DUNGEON_DISPLAY_NAMES[4549],
		178 : (
			u"Hrobka tyranského faraona"
			if _DUNGEON_DISPLAY_NAMES_CZECH
			else "Crypt of the Tyrant Pharaoh"
		),
	}
	#if background.IsMapInfoByMapName("metin2_map_dawnmist_dungeon_01"):
	MINIMAP_ZONE_NAME_DICT_BY_IDX[353] = MAP_DAWNMIST_DUNGEON_01
	#if background.IsMapInfoByMapName("metin2_map_Mt_Th_dungeon_01"):
	MINIMAP_ZONE_NAME_DICT_BY_IDX[354] = MAP_MT_TH_DUNGEON_01
	#if background.IsMapInfoByMapName("metin2_map_n_flame_dragon"):
	MINIMAP_ZONE_NAME_DICT_BY_IDX[356] = MAP_N_FLAME_DRAGON
	#if background.IsMapInfoByMapName("metin2_map_battlefied"):
	MINIMAP_ZONE_NAME_DICT_BY_IDX[357] = MAP_BATTLE_FIELD
	#if background.IsMapInfoByMapName("metin2_12zi_stage"):
	MINIMAP_ZONE_NAME_DICT_BY_IDX[355] = MAP_CZ_DUNGEON

del _DUNGEON_DISPLAY_NAMES_CZECH

# 캐릭터창에서 캐릭터의 얼굴에 마우스 오버 했을 때 나오는 설명.
JOBINFO_DATA_LIST = [
	[
		["타고난 용맹과 굽히지 않는 무사의",
		"기개를 사람들은 일컬어 [용자]라고",
		"부른다. 어떠한 위기에서도 그들은 ",
		"뒤로 물러서지 않으며, 다치고 움직",
		"이기 힘든 동료를 위해 단신으로",
		"적들과 마주 싸우기도 한다. 이들은",
		"잘 단련된 근육과 힘, 강력한 공격력",
		"으로 전장 최선두에서 공격진으로",
		"활약한다.                      ",],
		["가장 일반적인 공격형 무사로, ",
		"적접전에 따른 직접 공격으로 전장",
		"에서 활약한다. 군직 특성상 근력을",
		"메인으로 스텟 포인트를 투자하되, ",
		"적접전에 따른 생명력 / 방어력",
		"확보를 위해 체력을 올린다. 또한",
		"공격의 정확성을 높이기 위해 민첩",
		"에도 포인트를 투자할 필요가 있다.",],
		["상당 수준의 정신력을 이용하는",
		"중/근거리 접전형 무사로, 각 기술",
		"하나하나의 높은 공격력으로 전장에서",
		"활약한다. 군직 특성상 근력을 메인",
		"으로 스탯 포인트를 투자하되, ",
		"중/근거리 공격의 정확성과 명중률을",
		"위해 민첩을 올린다. 또한 접전 시 ",
		"적 공격에 따른 생명력 / 방어력",
		"확보를 위해 체력에도 포인트를",
		"투자할 필요가 있다.        ",],
	],
	[
		["자객은 어떠한 상황에서도 자신의",
		"몸을 숨기고 은밀한 어둠의 임무를",
		"수행하면서 전장의 후위를 지원하는", 
		"자들이다. 이들은 아주 빠르고 신속",
		"하며, 비할 데 없이 과감하고 절제된",
		"행동으로 적의 급소에 치명타를 날리",
		"되, 전장에선 적진을 향해 무수한",
		"화살을 내뿜으며 자신의 용맹을",
		"선보인다.                   "],
		["두손 단검을 주무기로 다루며, 신속",
		"하게 치고 빠지는 자객 특유의 움직임",
		"으로 전장에서 활약한다. 군직 특성상",
		"민첩을 메인으로 스텟 포인트를 투자",
		"하되, 근력을 올려 공격력을 높인다.",
		"또한 근접전에 따른 생명력/방어력 ",
		"상승을 위해 체력에도 포인트를",
		"투자할 필요가 있다.          ",],
		["활을 주무기로 다루며, 긴 시야와",
		"사정거리에 따른 원거리 공격으로",
		"전장에서 활약한다. 군직 특성상",
		"공격 성공률의 증가를 위해 민첩을",
		"메인으로 올려야 하며, 원거리",
		"공격의 데미지 증가를 위해 근력을",
		"올릴 필요가 있다. 또한 적들에게",
		"포위되었을 시, 적 공격에 버티기",
		"위한 생명력/방어력 상승을 위해",
		"체력에도 포인트를 투자할 필요가",
		"있다.                        ", ],
	],
	[
		["수라는 [독은 독으로]의 속성으로",
		"창설된 특수 속성의 군직이다. ",
		"그들은 전장에서 적들의 사기를 저하",
		"시키고, 악마의 힘을 실은 마탄으로",
		"적의 영혼과 육신을 짓뭉갠다. 때로",
		"이들은 자신의 검과 갑옷에 어둠의",
		"힘을 실어, 전장에서 무사 못지 않은",
		"공격력을 발휘하기도 하는데, 적들을",
		"죽여대는그 모습이 워낙에 끔찍해",
		"사람들은 수라를 일컬어 [마신]이라",
		"부르기를 주저 앉는다."],
		["환무군의 수라는 악마의 씨에서",
		"얻어지는 마력을 무기나 방어구에",
		"실어 무사 못지 않은 전투력으로",
		"전장에서 활약한다. 군직 특성상",
		"지능이 높아질수록 착용 장비에", 
		"실리는 마력의 위력이 증대되므로,",
		"지능과 근력을 메인으로 스탯",
		"포인트를 투자하되, 접전에 따른",
		"생명력/방어력 확보를 위해 체력을",
		"올린다. 또한 공격의 정확성과",
		"회피를 위해서 민첩에도 포인트를",
		"투자할 필요가 있다.           ",],
		["흑마군의 수라들은 각종 어둠의",
		"주문과 악마의 마법으로 전장에서",
		"활약한다. 군직 특성상 마법 공격이",
		"주이므로 지능을 메인으로 스텟",
		"포인트를 투자하되, 원거리 마법",
		"공격의 정확성을 위해 민첩을 올린다.",
		"또한 포위 되었을시, 적 공격에 따른",
		"생명력 / 방어력 확보를 위해 체력에도",
		"포인트를 투자할 필요가 있다.    ",],
	],
	[
		["무당은 용신과 자연, 두 고대의",
		"힘을 다룰 수 있는 유일한 직종이다.",
		"그들은 후방에서 아군을 보조하고",
		"다친 동료의 부상을 회복 시키며",
		"떨어진 사기를 상승시킨다. 그들은",
		"아군의 수면과 휴식을 방해하는 자를 ",
		"절대 용서하지 않으며, 그런 자들",
		"에게는 한 점 주저 없이 주문을",
		"터트려 그 비겁함을 엄히 징계한다.",],
		["천룡군의 무당들은 각종 부적술과",
		"보조주문에 능하며, 적의 직 / 간접",
		"공격으로부터 아군을 지킨다. 군직",
		"특성상 마법 능력이 주이므로 지능을",
		"메인으로 스텟 포인트를 투자하되,",
		"포위되었을 시, 적 공격에 따른",
		"생명력 / 방어력 확보를 위해 체력을",
		"올린다. 또한 원거리 마법 공격의",
		"정확성을 위에 민첩에도 포인트를",
		"투자할 필요가 있다.           ",],
		["광뢰군의 무당들은 자연의 힘을",
		"빌려 아군을 회복하고, 뇌신의 ",
		"힘으로 밀집한 적들에게 큰 충격을",
		"입힐 수 있는 이들이다. 군직의",
		"특성상 마법 능력이 주이므로 지능을",
		"메인으로 스텟 포인트를 투자하되,",
		"포위되었을시, 적 공격에 따른",
		"생명력 / 방어력 확보를 위해 체력을",
		"올린다. 또한 원거리 마법 공격의",
		"정확성을 위에 민첩에도 포인트를",
		"투자할 필요가 있다.             "],
	],
	[
		["수인",],
		["수인은 [빙의와 쾌]의 속성으로",
		"창설이 된 특수 군직이다.",
		"그들은 전장에서 선봉에 서며, 마물들의",
		"사기를 저하시키고 육신을 찢어 발긴다.",
		"때로는 자신들의 몸에 늑대의 영혼을 이어",
		"받아, 전장에서 무사를 초월하는 순간적인",
		"공격력을 발취하기도 하는데, 적들은 그",
		"모습이 흡사 [대랑]을 닮아 [사신]이라",
		"부르기도 한다."],
		["해당없음"],
	],
]

WHISPER_ERROR = {
	1 : CANNOT_WHISPER_NOT_LOGON,
	2 : CANNOT_WHISPER_DEST_REFUSE,
	3 : CANNOT_WHISPER_SELF_REFUSE,
}

NOTIFY_MESSAGE = {
	"CANNOT_EQUIP_SHOP" : CANNOT_EQUIP_IN_SHOP,
	"CANNOT_EQUIP_EXCHANGE" : CANNOT_EQUIP_IN_EXCHANGE,
}

ATTACK_ERROR_TAIL_DICT = {
	"IN_SAFE" : CANNOT_ATTACK_SELF_IN_SAFE,
	"DEST_IN_SAFE" : CANNOT_ATTACK_DEST_IN_SAFE,
}

SHOT_ERROR_TAIL_DICT = {
	"EMPTY_ARROW" : CANNOT_SHOOT_EMPTY_ARROW,
	"IN_SAFE" : CANNOT_SHOOT_SELF_IN_SAFE,
	"DEST_IN_SAFE" : CANNOT_SHOOT_DEST_IN_SAFE,
}

USE_SKILL_ERROR_TAIL_DICT = {
	"IN_SAFE" : CANNOT_SKILL_SELF_IN_SAFE,
	"NEED_TARGET" : CANNOT_SKILL_NEED_TARGET,
	"NEED_EMPTY_BOTTLE" : CANNOT_SKILL_NEED_EMPTY_BOTTLE,
	"NEED_POISON_BOTTLE" : CANNOT_SKILL_NEED_POISON_BOTTLE,
	"REMOVE_FISHING_ROD" : CANNOT_SKILL_REMOVE_FISHING_ROD,
	"NOT_YET_LEARN" : CANNOT_SKILL_NOT_YET_LEARN,
	"NOT_MATCHABLE_WEAPON" : CANNOT_SKILL_NOT_MATCHABLE_WEAPON,
	"WAIT_COOLTIME" : CANNOT_SKILL_WAIT_COOLTIME,
	"NOT_ENOUGH_HP" : CANNOT_SKILL_NOT_ENOUGH_HP,
	"NOT_ENOUGH_SP" : CANNOT_SKILL_NOT_ENOUGH_SP,
	"CANNOT_USE_SELF" : CANNOT_SKILL_USE_SELF,
	"ONLY_FOR_ALLIANCE" : CANNOT_SKILL_ONLY_FOR_ALLIANCE,
	"CANNOT_ATTACK_ENEMY_IN_SAFE_AREA" : CANNOT_SKILL_DEST_IN_SAFE,
	"CANNOT_APPROACH" : CANNOT_SKILL_APPROACH,
	"CANNOT_ATTACK" : CANNOT_SKILL_ATTACK,
	"ONLY_FOR_CORPSE" : CANNOT_SKILL_ONLY_FOR_CORPSE,
	"EQUIP_FISHING_ROD" : CANNOT_SKILL_EQUIP_FISHING_ROD, 
	"NOT_HORSE_SKILL" : CANNOT_SKILL_NOT_HORSE_SKILL,
	"HAVE_TO_RIDE" : CANNOT_SKILL_HAVE_TO_RIDE,
}

if app.ENABLE_STANDING_MOUNT:
	USE_SKILL_ERROR_TAIL_DICT.update({
		"NOT_HORSE_STANDING_SKILL" : CANNOT_SKILL_NOT_STANDING_HORSE_SKILL,
	})

LEVEL_LIST = ["", HORSE_LEVEL1, HORSE_LEVEL2, HORSE_LEVEL3]

HEALTH_LIST = [
	HORSE_HEALTH0,
	HORSE_HEALTH1,
	HORSE_HEALTH2,
	HORSE_HEALTH3,
]

USE_SKILL_ERROR_CHAT_DICT = {
	"NEED_EMPTY_BOTTLE" : SKILL_NEED_EMPTY_BOTTLE,
	"NEED_POISON_BOTTLE" : SKILL_NEED_POISON_BOTTLE,
	"ONLY_FOR_GUILD_WAR" : SKILL_ONLY_FOR_GUILD_WAR,
}

SHOP_ERROR_DICT = {
	"NOT_ENOUGH_MONEY" : SHOP_NOT_ENOUGH_MONEY,
	"SOLDOUT" : SHOP_SOLDOUT,
	"INVENTORY_FULL" : SHOP_INVENTORY_FULL,
	"INVALID_POS" : SHOP_INVALID_POS,
	"NOT_ENOUGH_MONEY_EX" : SHOP_NOT_ENOUGH_MONEY_EX,
}
if app.ENABLE_SHOPEX_RENEWAL:
	SHOP_ERROR_DICT.update({
		"NOT_ENOUGH_ITEM": SHOP_NOT_ENOUGH_ITEM,
		"NOT_ENOUGH_EXP": SHOP_NOT_ENOUGH_EXP,
	})
if app.ENABLE_COMBAT_ZONE:
	SHOP_ERROR_DICT.update({
		"NOT_ENOUGH_POINTS" : COMBAT_ZONE_SHOP_NOT_ENOUGH_BATTLE_POINT,
		"MAX_LIMIT_POINTS" : COMBAT_ZONE_SHOP_EXCEED_LIMIT_TODAY,
		"OVERFLOW_LIMIT_POINTS" : COMBAT_ZONE_SHOP_OVERFLOW_LIMIT_TODAY,
	})

STAT_MINUS_DESCRIPTION = {
	"HTH-" : STAT_MINUS_CON,
	"INT-" : STAT_MINUS_INT,
	"STR-" : STAT_MINUS_STR,
	"DEX-" : STAT_MINUS_DEX,
}

MODE_NAME_LIST = (PVP_OPTION_NORMAL, PVP_OPTION_REVENGE, PVP_OPTION_KILL, PVP_OPTION_PROTECT,)
if app.ENABLE_GENDER_ALIGNMENT:
	TITLE_NAME_DICT = {
		GENDER_FEMALE : (PVP_LEVEL0_F, PVP_LEVEL1_F, PVP_LEVEL2_F, PVP_LEVEL3_F, PVP_LEVEL4_F, PVP_LEVEL5_F, PVP_LEVEL6_F, PVP_LEVEL7_F, PVP_LEVEL8_F,),
		GENDER_MALE : (PVP_LEVEL0_M, PVP_LEVEL1_M, PVP_LEVEL2_M, PVP_LEVEL3_M, PVP_LEVEL4_M, PVP_LEVEL5_M, PVP_LEVEL6_M, PVP_LEVEL7_M, PVP_LEVEL8_M,),
	}
else:
	TITLE_NAME_LIST = (PVP_LEVEL0, PVP_LEVEL1, PVP_LEVEL2, PVP_LEVEL3, PVP_LEVEL4, PVP_LEVEL5, PVP_LEVEL6, PVP_LEVEL7, PVP_LEVEL8,)

if app.ENABLE_GUILD_LEADER_GRADE_NAME:
	GUILD_LEADER_GRADE_NAME_LIST = (GUILD_LEADER_GRADE0, GUILD_LEADER_GRADE1)

QUEST_SCROLL_ROOT = "d:/ymir work/ui/game/crimson_ember/quest/scroll/"

def GetQuestScrollNormalImageName():
	return QUEST_SCROLL_ROOT + "quest_scroll_normal.png"
def GetQuestScrollHoverImageName():
	return QUEST_SCROLL_ROOT + "quest_scroll_hover.png"
def GetQuestScrollPressedImageName():
	return QUEST_SCROLL_ROOT + "quest_scroll_pressed.png"

def GetLetterImageName():
	return GetQuestScrollNormalImageName()
def GetLetterOpenImageName():
	return GetQuestScrollHoverImageName()
def GetLetterCloseImageName():
	return GetQuestScrollNormalImageName()

def GetBlueLetterImageName():
	return GetQuestScrollNormalImageName()
def GetBlueLetterOpenImageName():
	return GetQuestScrollHoverImageName()
def GetBlueLetterCloseImageName():
	return GetQuestScrollPressedImageName()

if 949 == app.GetDefaultCodePage():
	def EUL(name):
		if GetAuxiliaryWordType(name):
			return "를 "
		else:
			return "을 "

	def I(name):
		if GetAuxiliaryWordType(name):
			return "가 "
		else:
			return "이 "

	def DO_YOU_SELL_ITEM(sellItemName, sellItemCount, sellItemPrice):
		name = sellItemName
		if sellItemCount > 1:
			name += " "
			name += str(sellItemCount)
			name += "개"

		return name + EUL(name) + str(sellItemPrice) + "냥에 파시겠습니까?"

	def DO_YOU_BUY_ITEM(sellItemName, sellItemCount, sellItemPrice):
		name = sellItemName
		if sellItemCount > 1:
			name += " "
			name += str(sellItemCount)
			name += "개"

		return name + EUL(name) + str(sellItemPrice) + "에 사시겠습니까?"

	#def REFINE_FAILURE_CAN_NOT_ATTACH(attachedItemName):
	#	return attachedItemName+EUL(attachedItemName)+"부착할 수 없는 아이템입니다"

	def REFINE_FAILURE_NO_SOCKET(attachedItemName):
		return attachedItemName+EUL(attachedItemName)+"부착할 수 있는 소켓이 없습니다"

	def REFINE_FAILURE_NO_GOLD_SOCKET(attachedItemName):
		return attachedItemName+EUL(attachedItemName)+"부착할 수 있는 황금 소켓이 없습니다"

	def HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, dropItemCount):
		name = dropItemName
		if dropItemCount > 1:
			name += " "
			name += str(dropItemCount)
			name += "개"

		return name + EUL(name) + "버리시겠습니까?"

	def NumberToMoneyString(n):
		if n <= 0:
			return "0냥"

		n = str(n)
		result = CutMoneyString(n, 0, 4, "", "")
		result = CutMoneyString(n, 4, 8, "만", result)
		result = CutMoneyString(n, 8, 12, "억", result)
		result = result + "냥"

		return result

	def NumberToSecondaryCoinString(number):
		if number <= 0:
			return "0전"

		number = str(number)
		result = CutMoneyString(number, 0, 4, "", "")
		result = CutMoneyString(number, 4, 8, "만", result)
		result = CutMoneyString(number, 8, 12, "억", result)
		result = result + "전"

		return result

	def FISHING_NOTIFY(isFish, fishName):
		if isFish:
			return fishName + I(fishName) + "문 듯 합니다."
		else:
			return fishName + I(fishName) + "걸린듯 합니다."

	def FISHING_SUCCESS(isFish, fishName):
		if isFish:
			return fishName + EUL(fishName) + "잡았습니다!"
		else:
			return fishName + EUL(fishName) + "얻었습니다!"

elif 932 == app.GetDefaultCodePage():
	def DO_YOU_SELL_ITEM(sellItemName, sellItemCount, sellItemPrice):
		if sellItemCount > 1 :
			return "%s %s 뙿귩 %s궸봽귟귏궥궔갎" % (sellItemName, sellItemCount, NumberToMoneyString(sellItemPrice))
		else:
			return "%s 귩 %s궳봽귟귏궥궔갎" % (sellItemName, NumberToMoneyString(sellItemPrice))

	def DO_YOU_BUY_ITEM(buyItemName, buyItemCount, buyItemPrice):
		if buyItemCount > 1 :
			return "%s %s뙿귩 %s궳봼궋귏궥궔갎" % (buyItemName, buyItemCount, buyItemPrice)
		else:
			return "%s귩 %s궳봼궋귏궥궔갎" % (buyItemName, buyItemPrice)

	#def REFINE_FAILURE_CAN_NOT_ATTACH(attachedItemName):
	#	return "%s귩몧뭶궳궖궶궋귺귽긡?궳궥갃" % (attachedItemName)

	def REFINE_FAILURE_NO_SOCKET(attachedItemName):
		return "%s귩몧뭶궥귡?긑긞긣궕궇귟귏궧귪갃" % (attachedItemName)

	def REFINE_FAILURE_NO_GOLD_SOCKET(attachedItemName):
		return "%s귩몧뭶궳궖귡돥뗠?긑긞긣궕궇귟귏궧귪갃" % (attachedItemName)

	def HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, dropItemCount):
		if dropItemCount > 1 :
			return "%s %d 뙿귩롆궲귏궥궔갎" % (dropItemName, dropItemCount)
		else:
			return "%s귩롆궲귏궥궔갎" % (dropItemName)

	def FISHING_NOTIFY(isFish, fishName):
		if isFish:
			return "%s 궕륣궋궰궋궫귝궎궳궥" % (fishName)
		else:
			return "%s 궕궔궔궯궫귝궎궳궥" % (fishName)

	def FISHING_SUCCESS(isFish, fishName):
		if isFish:
			return "%s 귩뺕귏궑귏궢궫갏" % (fishName)
		else:
			return "%s 귩롨궸볺귢귏궢궫갏" % (fishName)

	def NumberToMoneyString(number):
		if number <= 0 :
			return "0뿼"

		number = str(number)
		result = CutMoneyString(number, 0, 4, "", "")
		result = CutMoneyString(number, 4, 8, "뼔", result)
		result = CutMoneyString(number, 8, 12, "돪", result)
		result = result + "뿼"

		return result

	def NumberToSecondaryCoinString(number):
		if number <= 0 :
			return "0jun"

		number = str(number)
		result = CutMoneyString(number, 0, 4, "", "")
		result = CutMoneyString(number, 4, 8, "뼔", result)
		result = CutMoneyString(number, 8, 12, "돪", result)
		result = result + "jun"

		return result

elif IsHONGKONG():
	def DO_YOU_SELL_ITEM(sellItemName, sellItemCount, sellItemPrice):
		if sellItemCount > 1 :
			return DO_YOU_SELL_ITEM2 % (sellItemName, sellItemCount, NumberToMoneyString(sellItemPrice))
		else:
			return DO_YOU_SELL_ITEM1 % (sellItemName, NumberToMoneyString(sellItemPrice))

	def DO_YOU_BUY_ITEM(buyItemName, buyItemCount, buyItemPrice):
		if buyItemCount > 1 :
			return DO_YOU_BUY_ITEM2 % (buyItemName, buyItemCount, buyItemPrice)
		else:
			return DO_YOU_BUY_ITEM1 % (buyItemName, buyItemPrice)

	#def REFINE_FAILURE_CAN_NOT_ATTACH(attachedItemName):
	#	return REFINE_FAILURE_CAN_NOT_ATTACH0 % (attachedItemName)

	def REFINE_FAILURE_NO_SOCKET(attachedItemName):
		return REFINE_FAILURE_NO_SOCKET0 % (attachedItemName)

	def REFINE_FAILURE_NO_GOLD_SOCKET(attachedItemName):
		return REFINE_FAILURE_NO_GOLD_SOCKET0 % (attachedItemName)

	def HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, dropItemCount):
		if dropItemCount > 1 :
			return HOW_MANY_ITEM_DO_YOU_DROP2 % (dropItemName, dropItemCount)
		else:
			return HOW_MANY_ITEM_DO_YOU_DROP1 % (dropItemName)

	def FISHING_NOTIFY(isFish, fishName):
		if isFish:
			return FISHING_NOTIFY1 % (fishName)
		else:
			return FISHING_NOTIFY2 % (fishName)

	def FISHING_SUCCESS(isFish, fishName):
		if isFish:
			return FISHING_SUCCESS1 % (fishName)
		else:
			return FISHING_SUCCESS2 % (fishName)

	def NumberToMoneyString(number):
		if number <= 0 :
			return "0 %s" % (MONETARY_UNIT0)

		number = str(number)
		result = CutMoneyString(number, 0, 4, 	"", "")
		result = CutMoneyString(number, 4, 8, 	MONETARY_UNIT1, result)
		result = CutMoneyString(number, 8, 12, 	MONETARY_UNIT2, result)
		result = result + MONETARY_UNIT0

		return result

	def NumberToSecondaryCoinString(number):
		if number <= 0 :
			return "0 %s" % (MONETARY_UNIT_JUN)

		number = str(number)
		result = CutMoneyString(number, 0, 4, 	"", "")
		result = CutMoneyString(number, 4, 8, 	MONETARY_UNIT1, result)
		result = CutMoneyString(number, 8, 12, 	MONETARY_UNIT2, result)
		result = result + MONETARY_UNIT_JUN

		return result

elif IsNEWCIBN() or IsCIBN10():
	def DO_YOU_SELL_ITEM(sellItemName, sellItemCount, sellItemPrice):
		if sellItemCount>1:
			return "횅땍狼겉%s몸%s鹿%s쏜귑찡딜찐？" % (str(sellItemCount), sellItemName, str(sellItemPrice))
		else:
			return "횅땍狼겉%s鹿%s쏜귑찡딜찐？" % (sellItemName, str(sellItemPrice))

	def DO_YOU_BUY_ITEM(sellItemName, sellItemCount, sellItemPrice):
		if sellItemCount>1:
			return "횅땍狼겉%s몸%s鹿%s쏜귑찜쏵찐？" % (str(sellItemCount), sellItemName, str(sellItemPrice))
		else:
			return "횅땍狼겉%s鹿%s쏜귑찜쏵찐？" % (sellItemName, str(sellItemPrice))

	#def REFINE_FAILURE_CAN_NOT_ATTACH(attachedItemName):
	#	return "轟랬穹퓌%s 돨陋구" % (attachedItemName)

	def REFINE_FAILURE_NO_SOCKET(attachedItemName):
		return "청唐옵鹿穹퓌%s 돨왝" % (attachedItemName)

	def REFINE_FAILURE_NO_GOLD_SOCKET(attachedItemName):
		return "청唐옵鹿穹퓌%s 돨뼝쏜왝" % (attachedItemName)

	def HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, dropItemCount):
		if dropItemCount>1:
			return "횅땍狼휀딜%d몸%s찐?" % (dropItemCount, dropItemName)
		else:
			return "횅땍狼휀딜%s찐?" % (dropItemName)

	def FISHING_NOTIFY(isFish, fishName):
		if isFish:
			return fishName # 본래 여기에 어떤 말이 붙어있는데, 인코딩이 깨져있어서 복원할 수가 없다 ㅠㅠ... cython에서 인코딩 에러 나서 지워버림...
		else:
			return "딥淪" + fishName + "죄。"

	def FISHING_SUCCESS(isFish, fishName):
		if isFish:
			return "딥淪" + fishName + "죄。"
		else:
			return "삿돤" + fishName + "죄。"

	def NumberToMoneyString(number):
		if number <= 0:
			return "0좃"

		number = str(number)
		result = CutMoneyString(number, 0, 4, "", "")
		result = CutMoneyString(number, 4, 8, "拱", result)
		result = CutMoneyString(number, 8, 12, "聾", result)
		result = result + "좃"

		return result

	def NumberToSecondaryCoinString(number):
		if number <= 0:
			return "0JUN"

		number = str(number)
		result = CutMoneyString(number, 0, 4, "", "")
		result = CutMoneyString(number, 4, 8, "拱", result)
		result = CutMoneyString(number, 8, 12, "聾", result)
		result = result + "JUN"

		return result

elif IsEUROPE() and not IsWE_KOREA() and not IsYMIR():
	def DO_YOU_SELL_ITEM(sellItemName, sellItemCount, sellItemPrice):
		if sellItemCount > 1:
			return DO_YOU_SELL_ITEM2 % (sellItemName, sellItemCount, NumberToMoneyString(sellItemPrice))
		else:
			return DO_YOU_SELL_ITEM1 % (sellItemName, NumberToMoneyString(sellItemPrice))

	def DO_YOU_BUY_ITEM(buyItemName, buyItemCount, buyItemPrice):
		if buyItemCount > 1:
			return DO_YOU_BUY_ITEM2 % (buyItemName, buyItemCount, buyItemPrice)
		else:
			return DO_YOU_BUY_ITEM1 % (buyItemName, buyItemPrice)

	#def REFINE_FAILURE_CAN_NOT_ATTACH(attachedItemName):
	#	return REFINE_FAILURE_CAN_NOT_ATTACH0 % (attachedItemName)

	def REFINE_FAILURE_NO_SOCKET(attachedItemName):
		return REFINE_FAILURE_NO_SOCKET0 % (attachedItemName)

	def REFINE_FAILURE_NO_GOLD_SOCKET(attachedItemName):
		return REFINE_FAILURE_NO_GOLD_SOCKET0 % (attachedItemName)

	def HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, dropItemCount):
		if dropItemCount > 1:
			return HOW_MANY_ITEM_DO_YOU_DROP2 % (dropItemName, dropItemCount)
		else:
			return HOW_MANY_ITEM_DO_YOU_DROP1 % (dropItemName)

	def FISHING_NOTIFY(isFish, fishName):
		if isFish:
			return FISHING_NOTIFY1 % (fishName)
		else:
			return FISHING_NOTIFY2 % (fishName)

	def FISHING_SUCCESS(isFish, fishName):
		if isFish:
			return FISHING_SUCCESS1 % (fishName)
		else:
			return FISHING_SUCCESS2 % (fishName)

	def NumberToMoneyString(n):
		if n <= 0:
			return "0"

		return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

	def NumberToSecondaryCoinString(n):
		if n <= 0:
			return "0 %s" % (MONETARY_UNIT_JUN)

		return "%s %s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]), MONETARY_UNIT_JUN)

	if app.ENABLE_COMBAT_ZONE:
		def NumberToCombatZoneCoinString(n):
			if n <= 0:
				return "0 %s" % (MONETARY_COMBAT_ZONE)
			return "%s %s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]), MONETARY_COMBAT_ZONE)

	def NumberToDisplayedCount(n):
		if n <= 0 :
			return "0 %s" % (MONETARY_UNIT0)

		return "%s %s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]), MONETARY_UNIT0)

	def NumberToDecimal(n):
		return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

	def AddPointToNumberString(n) :
		if n <= 0 :
			return "0"

		return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))		

	if app.ENABLE_SHOPEX_RENEWAL:
		def NumberToShopEXP(n):
			if n <= 0 :
				return "0 %s" % ("EXP")
			n = str(n)
			return "%s %s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]), "EXP")

	if app.ENABLE_OFFLINE_SHOP:
		def FormatDays(time):
			if time < 60:
				return "1" + DAYS
				
			second = int(time % 60)
			minute = int((time / 60) % 60)
			hour = int((time / 60) / 60) % 24
			day = int(int((time / 60) / 60) / 24)
			
			if day < 1:
				day = 1
				
			if day > 9999:
				day = 9999
				
			text = str(day) + DAYS
			return text

		def FormatSeconds(seconds):
			timeInfos = [
				["y", "y", 365 * 24 * 60 * 60],
				["d", "d", 24 * 60 * 60],
				["h", "h", 60 * 60],
				["m", "m", 60],
				["s", "s", 1],
			]
		
			timeStrings = []
			for timeInfo in timeInfos:
				fitCount = seconds // timeInfo[2]
		
				if fitCount >= 1:
					seconds = seconds - (timeInfo[2] * fitCount)
		
					if fitCount > 1:
						timeStrings.append(str(fitCount) + "" + timeInfo[1])
					else:
						timeStrings.append(str(fitCount) + "" + timeInfo[0])
		
			if len(timeStrings) == 0:
				return "-"
		
			return " ".join(timeStrings)
			
		def GetFormattedTimeString(time):
			minutes, seconds = divmod(time, 60)
			hours, minutes = divmod(minutes, 60)
			return "%dh %02dm" % (hours, minutes)
			
		def GetFormattedNumberString(num):
			num = str(num)
			
			parts = []
			while len(num) > 0:
				i = len(num) % 3
				if i == 0: i = 3
				parts.append(num[:i])
				
				num = num[i:]
			
			return '.'.join(parts)
		
		def FormatSeconds(seconds):
			timeInfos = [
				["y", "y", 365 * 24 * 60 * 60],
				["d", "d", 24 * 60 * 60],
				["h", "h", 60 * 60],
				["m", "m", 60],
				["s", "s", 1],
			]
		
			timeStrings = []
			for timeInfo in timeInfos:
				fitCount = seconds // timeInfo[2]
		
				if fitCount >= 1:
					seconds = seconds - (timeInfo[2] * fitCount)
		
					if fitCount > 1:
						timeStrings.append(str(fitCount) + "" + timeInfo[1])
					else:
						timeStrings.append(str(fitCount) + "" + timeInfo[0])
		
			if len(timeStrings) == 0:
				return "-"
		
			return " ".join(timeStrings)
		
		def FormatShortSeconds(seconds):
			timeInfos = [
				60 * 60,
				60,
				1
			]
		
			timeStrings = []
			for timeInfo in timeInfos:
				fitCount = seconds // timeInfo
				seconds = seconds - (timeInfo * fitCount)
				timeStrings.append("{:02d}".format(fitCount))
		
			return ":".join(timeStrings)
		
		def NumberToDecimalString(n):
			return str('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))
		
		def NumberToString(value):
			return "{:0,.0f}".format(value).replace(',', '.')
		
		def LongNumberToString(value):
			retVal = int(value)
			retVal = '{:,}'.format(retVal)
			retVal = retVal.replace(',', '.')
			return str(retVal)

if app.ENABLE_MAINTENANCE_SYSTEM:
	def MaintenanceSecondToDHMS(time, ignoreSecTime = -1, useShortName = TRUE):
		if time < 60:
			if IsARABIC():
				return "%.2f %s" % (time, SECOND)
			else:
				return "%.2f %s" % (time, SECOND)

		second = int(time % 60)
		minute = int((time / 60) % 60)
		hour = int((time / 60) / 60) % 24
		day = int(int((time / 60) / 60) / 24)

		text = ""

		if day > 0:
			text += str(day) + "d"
			text += " "

		if hour > 0:
			text += str(hour) + "h"
			text += " "

		if minute > 0:
			text += str(minute) + "m"
			text += " "

		if second > 0:
			text += str(second) + "s"

		return text

if app.ENABLE_GROWTH_PET_SYSTEM:
	def SecondToDay(time):
		if time < 60:
			return "1" + DAY
			
		second = int(time % 60)
		minute = int((time / 60) % 60)
		hour = int((time / 60) / 60) % 24
		day = int(int((time / 60) / 60) / 24)
		
		if day < 1:
			day = 1
			
		if day > 9999:
			day = 9999
			
		text = str(day) + DAY
		return text
		
	def SecondToDayNumber(time):
		if time < 60:
			return 1
			
		second = int(time % 60)
		minute = int((time / 60) % 60)
		hour = int((time / 60) / 60) % 24
		day = int(int((time / 60) / 60) / 24)
		
		if day < 1:
			day = 1
			
		if day > 9999:
			day = 9999
			
		return day

	def SecondToH(time):			
		hour = int((time / 60) / 60)

		text = ""
		hour = max( 0, hour )
		text += str(hour)

		return text

if app.ENABLE_DETAILS_UI:
	def DottedNumber(n) :
		return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ])) 

if app.ENABLE_EXCHANGE_LOG:
	def MoneyFormat(n):
		return "%s" % ('.'.join([ i-3<0 and str(n)[:i] or str(n)[i-3:i] for i in range(len(str(n))%3, len(str(n))+1, 3) if i ]))

if app.ENABLE_WIKI:
	def SecondToHMS(time):
		if time <= 0:
			return "0 " + SECOND
		second = int(time % 60)
		minute = int((time / 60) % 60)
		hour = int((time / 60) / 60) % 24
		text = ""
		if hour > 0:
			text += str(hour) + " " + HOUR
			text += " "
		if minute > 0:
			text += str(minute) + " " + MINUTE
			text += " "
		if second > 0:
			text += str(second) + " " + SECOND
		return text
