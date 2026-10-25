import fontconfig, ui, localeInfo
import pvmpersonal
import dewcatalog
import servergamedata
import pvmpersonaltext
import uieffecttooltipstyle
import uiaffecthover
import chr, app, skill, player, uiToolTip, chat, item, wndMgr
from uiToolTip import GET_AFFECT_STRING

AFFECT_GROUP_THRESHOLD = 1
# Biologist rewards: one permanent server affect per bonus point (AFFECT_COLLECT, game/src/biolog_research.cpp). The
# bar icon is built from these affects, so it survives a warp to another core, where the Biologist window sends no
# snapshot (TCK-0351: the bonus stayed, the icon vanished until "Odměna" was clicked in the window).
BIOLOG_AFFECT = 515

def SortAffectRowsByLength(rows, firstRowPinned=False):
	"""Sort non-empty rows by length, optionally keeping the first row on top."""
	indexedRows = [(index, row) for index, row in enumerate(rows) if row]
	indexedRows.sort(key=lambda data: (-len(data[1]), data[0]))
	if firstRowPinned and rows and rows[0]:
		indexedRows = [(0, rows[0])] + [data for data in indexedRows if data[0] != 0]
	return [row for unusedIndex, row in indexedRows]

def ShouldCollapseAffectGroup(memberCount, expanded, threshold=AFFECT_GROUP_THRESHOLD):
	return memberCount >= threshold and not expanded

def AppendAffectTitle(tooltip, title):
	font = tooltip.defFontName
	try:
		tooltip.SetDefaultFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
		return tooltip.AutoAppendNewTextLineResize(title, uieffecttooltipstyle.TITLE_COLOR)
	finally:
		tooltip.SetDefaultFontName(font)

# Skill affects show the tile the skill window shows for that skill now (owner 8. 10., tester "Špatné ikonky pro
# pasivky warriora": "prostě ta aktuální co máš v schopnosti"). The skill window draws skill.GetIconImageNew(skill,
# grade): CPythonSkill::__RegisterGradeIconImage loads d:/ymir work/ui/skill/<job>/<icon>_0<grade + 1>.sub with job
# and icon from <locale>/SkillDesc.txt, and the grade is clamped to 0 .. 3 (S keeps the P tile). GetIconImageNew
# hands out an image pointer, ImageBox.LoadImage needs the path, so the path is built from that same SkillDesc.txt
# (pack.Get) instead of a hand-written table (11. 10.: a table lookup gave Bojové zuření the poison and Aura meče
# the slow icon). A skill the player does not have (a party member's buff) shows the _03 tile; a skill SkillDesc
# has no graded tile for (Buffi's support skills 194 .. 198) keeps the path of the affect table.
SKILL_ICON_ROOT = "d:/ymir work/ui/skill/"
SKILL_ICON_GRADES = 4
SKILL_ICON_DEFAULT_GRADE = 2
# CPythonSkill::m_PathNameMap for the jobs whose skills have grade tiles.
SKILL_ICON_JOB_DIRS = {
	"WARRIOR": "warrior", "ASSASSIN": "assassin", "SURA": "sura", "SHAMAN": "shaman", "WOLFMAN": "wolfman",
	"PASSIVE": "passive", "78SKILL": "78skill",
}
SKILLDESC_JOB_COLUMN = 1
SKILLDESC_ICON_COLUMN = 12
_skillIconBases = None

def ParseSkillIconBases(raw):
	"""{skill vnum: d:/ymir work/ui/skill/<job>/<icon>} from the text of SkillDesc.txt."""
	if isinstance(raw, bytes):
		raw = raw.decode("latin-1")		# job and icon columns are ASCII, the names around them cp1250
	bases = {}
	for line in raw.splitlines():
		cells = line.split("\t")
		if len(cells) <= SKILLDESC_ICON_COLUMN:
			continue
		try:
			index = int(cells[0])
		except ValueError:
			continue
		job = SKILL_ICON_JOB_DIRS.get(cells[SKILLDESC_JOB_COLUMN].strip())
		icon = cells[SKILLDESC_ICON_COLUMN].strip()
		if job and icon:
			bases[index] = "%s%s/%s" % (SKILL_ICON_ROOT, job, icon)
	return bases

def SkillIconBases():
	global _skillIconBases
	if _skillIconBases is None:
		try:
			import pack
			bases = ParseSkillIconBases(pack.Get(app.GetLocalePath() + "/SkillDesc.txt"))
		except Exception:
			return {}
		_skillIconBases = bases
	return _skillIconBases

def SkillWindowIcon(skillIndex, grade):
	"""The tile the skill window draws for skillIndex at grade, "" when SkillDesc has no grade tiles for it."""
	base = SkillIconBases().get(skillIndex) if skillIndex else None
	if not base:
		return ""
	grade = min(max(int(grade), 0), SKILL_ICON_GRADES - 1)
	return "%s_%02d.sub" % (base, grade + 1)

def PlayerSkillGrade(skillIndex):
	"""The grade of one of the player's own skills (as the skill window shows it), None when the player has none."""
	if not skillIndex:
		return None
	try:
		slot = player.GetSkillSlotIndex(skillIndex)
		if player.GetSkillIndex(slot) != skillIndex:
			return None
		return int(player.GetSkillGrade(slot))
	except Exception:
		return None

def CurrentSkillIcon(path, skillIndex):
	"""The affect icon of a skill: the skill window's tile of the player's grade (_03 for a skill the player does not
	have), a lower grade when the art ends early (wolfman tiles end at _03), else path."""
	grade = PlayerSkillGrade(skillIndex)
	if grade is None:
		grade = SKILL_ICON_DEFAULT_GRADE
	grade = min(max(grade, 0), SKILL_ICON_GRADES - 1)
	for tier in range(grade, -1, -1):
		tile = SkillWindowIcon(skillIndex, tier)
		if not tile:
			break
		try:
			if not app.IsExistFile(tile):
				continue
		except Exception:
			pass
		return tile
	return path

if app.ENABLE_RENEWAL_AFFECT_SHOWER:
	import uiCommon, osfInfo, net
	from _weakref import proxy
	affectDict={}

	def UpsertAffectTooltipEntry(affectData, pointIdx, value, duration, now):
		"""Insert or refresh one point entry without duplicating an affect."""
		affectData = dict(affectData or {})
		entries = list(affectData.get("entries", []))

		if not entries:
			legacyEndTime = affectData.get("duration", 0)
			for legacyPointIdx, legacyValue in affectData.get("affect", []):
				entries.append([legacyPointIdx, legacyValue, legacyEndTime])

		endTime = now + duration if duration > 0 else 0
		replaced = False
		for index, entry in enumerate(entries):
			if entry[0] == pointIdx:
				entries[index] = [pointIdx, value, endTime]
				replaced = True
				break

		if not replaced:
			entries.append([pointIdx, value, endTime])

		affectData["entries"] = entries
		affectData["affect"] = [[entry[0], entry[1]] for entry in entries]
		affectData["duration"] = max([entry[2] for entry in entries] or [0])
		return affectData

	def RemoveAffectTooltipEntry(affectData, pointIdx):
		"""Remove one point entry and report whether a matching entry existed."""
		affectData = dict(affectData or {})
		entries = list(affectData.get("entries", []))

		if not entries:
			legacyEndTime = affectData.get("duration", 0)
			for legacyPointIdx, legacyValue in affectData.get("affect", []):
				entries.append([legacyPointIdx, legacyValue, legacyEndTime])

		remainingEntries = []
		removed = False
		for entry in entries:
			if not removed and entry[0] == pointIdx:
				removed = True
				continue
			remainingEntries.append(entry)

		affectData["entries"] = remainingEntries
		affectData["affect"] = [[entry[0], entry[1]] for entry in remainingEntries]
		affectData["duration"] = max([entry[2] for entry in remainingEntries] or [0])
		return affectData, removed

	def GetAffectGroupText(groupKey, textType="title"):
		isCzech = app.GetLocalePath().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz"
		if isCzech:
			texts = {
				"gods": ("Bohové", "Kliknutím rozbalit nebo sbalit"),
				"buffs": ("Buffy", "Kliknutím rozbalit nebo sbalit"),
				"skills": ("Schopnosti", "Kliknutím rozbalit nebo sbalit"),
				"dews": ("Rosy", "Kliknutím rozbalit nebo sbalit"),
				"potions": ("Lektvary", "Kliknutím rozbalit nebo sbalit"),
				"bonuses": ("Bonusy", "Kliknutím rozbalit nebo sbalit"),
				"systems": ("Systémové efekty", "Kliknutím rozbalit nebo sbalit"),
			}
		else:
			texts = {
				"gods": ("Dragon Gods", "Click to expand or collapse"),
				"buffs": ("Buffs", "Click to expand or collapse"),
				"skills": ("Skills", "Click to expand or collapse"),
				"dews": ("Dews", "Click to expand or collapse"),
				"potions": ("Potions", "Click to expand or collapse"),
				"bonuses": ("Bonuses", "Click to expand or collapse"),
				"systems": ("System effects", "Click to expand or collapse"),
			}
		title, hint = texts.get(groupKey, (groupKey, ""))
		return hint if textType == "hint" else title

	def TypeToAffect(affect):
		_dict = {
			chr.AFFECT_JEONGWI : 3,
			chr.AFFECT_GEOMGYEONG : 4,
			chr.AFFECT_CHEONGEUN : 19,
			chr.AFFECT_FALLEN_CHEONGEUN : 19,
			chr.AFFECT_GYEONGGONG : 49,
			chr.AFFECT_EUNHYEONG : 34,
			chr.AFFECT_GWIGEOM : 63,
			chr.AFFECT_GONGPO : 64,
			chr.AFFECT_JUMAGAP : 65,
			chr.AFFECT_HOSIN : 94,
			chr.AFFECT_BOHO : 95,
			chr.AFFECT_KWAESOK : 110,
			chr.AFFECT_HEUKSIN : 79,
			chr.AFFECT_MUYEONG : 78,
			chr.AFFECT_GICHEON : 96,
			chr.AFFECT_JEUNGRYEOK : 111,
			chr.AFFECT_PABEOP : 66,
		}
		return _dict[affect] if affect in _dict else affect

	def SkillToAffect(skillIndex, affects):
		"""The skill affect of a skill among affects, None when there is none. TypeToAffect returns an unmapped affect
		unchanged, so TypeToAffect(affect) == skill alone lets AFFECT_POISON (3) and AFFECT_SLOW (4) pass for the
		skills 3 (Bojové zuření) and 4 (Aura meče)."""
		for affect in affects:
			mapped = TypeToAffect(affect)
			if mapped != affect and mapped == skillIndex:
				return affect
		return None

	def SupportSkillTooltip(rawAffect):
		_supportPairs = (
			(chr.AFFECT_HOSIN, 194),
			(chr.AFFECT_BOHO, 195),
			(chr.AFFECT_KWAESOK, 197),
			(chr.AFFECT_GICHEON, 196),
			(chr.AFFECT_JEUNGRYEOK, 198),
		)
		for aff, supportVnum in _supportPairs:
			if rawAffect == aff and player.CheckAffect(supportVnum, 0):
				return supportVnum
		return TypeToAffect(rawAffect)

	def GetAffectTooltipData(rawAffect, isSkillAffect):
		affect = SupportSkillTooltip(rawAffect) if isSkillAffect else rawAffect
		if not isSkillAffect and rawAffect in (chr.AFFECT_POISON, chr.AFFECT_SLOW, chr.AFFECT_STUN):
			affect = ("actor", rawAffect)
		return affectDict.get(affect, {})

	def AffectToSkillIndex(rawAffect):
		_supportAffects = (
			chr.AFFECT_HOSIN,
			chr.AFFECT_BOHO,
			chr.AFFECT_KWAESOK,
			chr.AFFECT_GICHEON,
			chr.AFFECT_JEUNGRYEOK,
		)
		if rawAffect in _supportAffects:
			return SupportSkillTooltip(rawAffect)
		return player.AffectIndexToSkillIndex(rawAffect)

if app.ENABLE_MULTI_FARM_BLOCK:
	import uiCommon
	import net
	class MultiFarmImage(ui.ExpandedImageBox):
		def __del__(self):
			ui.ExpandedImageBox.__del__(self)
		def Destroy(self):
			self.multiFarmStatus = 0
			self.players = []
		def __init__(self):
			ui.ExpandedImageBox.__init__(self)
			self.Destroy()
		def SetMultiFarmInfo(self, multiFarmStatus):
			self.multiFarmStatus = multiFarmStatus
			if multiFarmStatus:
				self.LoadImage("d:/ymir work/ui/game/farm/can_farm.tga")
			else:
				self.LoadImage("d:/ymir work/ui/game/farm/cant_farm.tga")
		def _BuildHover(self, tooltip):
			tooltip.AppendTextLine("|cffF1E6C0"+localeInfo.MULTI_FARM_TITLE)
			tooltip.AppendSpace(5)
			tooltip.AppendTextLine(localeInfo.MULTI_FARM_TEXT)
			tooltip.AppendSpace(5)
			for name in self.players:
				tooltip.AppendTextLine("|cffF1E6C0"+name)
		def ShowHover(self):
			interface = osfInfo.GetInterfaceInstance()
			tooltip = interface.tooltipItem if interface else None
			return uiaffecthover.ShowTooltip(tooltip, self, (self.multiFarmStatus, tuple(self.players)), self._BuildHover)
		def OnMouseOverIn(self):
			uiaffecthover.Over(self)
		def OnMouseOverOut(self):
			uiaffecthover.Out(self)

class LovePointImage(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.loverName = ""
		self.lovePoint = 0
	def SetLoverInfo(self, name, lovePoint):
		self.loverName = name
		self.lovePoint = lovePoint
		self.__Refresh()
	def OnUpdateLovePoint(self, lovePoint):
		self.lovePoint = lovePoint
		self.__Refresh()
	def __Refresh(self):
		self.lovePoint = max(0, self.lovePoint)
		self.lovePoint = min(100, self.lovePoint)
		loveGrade = 0 if 0 == self.lovePoint else self.lovePoint // 25 + 1
		FILE_PATH = "d:/ymir work/ui/pattern/LovePoint/"
		FILE_DICT = {
			0 : FILE_PATH + "01.dds",
			1 : FILE_PATH + "02.dds",
			2 : FILE_PATH + "02.dds",
			3 : FILE_PATH + "03.dds",
			4 : FILE_PATH + "04.dds",
			5 : FILE_PATH + "05.dds",
		}
		fileName = FILE_DICT.get(loveGrade, FILE_PATH+"00.dds")

		try:
			self.LoadImage(fileName)
			self.SetScale(0.7, 0.7)
		except:
			import dbg
			dbg.TraceError("LovePointImage.SetLoverInfo(lovePoint=%d) - LoadError %s" % (self.lovePoint, fileName))
	def _BuildHover(self, tooltip):
		tooltip.AutoAppendNewTextLineResize(self.loverName, 0xffE9E7D2)
		tooltip.AppendSpace(5)
		tooltip.AutoAppendNewTextLineResize(localeInfo.AFF_LOVE_POINT % self.lovePoint)
	def ShowHover(self):
		interface = osfInfo.GetInterfaceInstance()
		tooltip = interface.tooltipItem if interface else None
		return uiaffecthover.ShowTooltip(tooltip, self, (self.loverName, self.lovePoint), self._BuildHover)
	def OnMouseOverIn(self):
		uiaffecthover.Over(self)
	def OnMouseOverOut(self):
		uiaffecthover.Out(self)

if app.ENABLE_CONQUEROR_LEVEL:
	class SungMaAffectImage(ui.ExpandedImageBox):
		def __init__(self, str, hp, move, immune):
			ui.ExpandedImageBox.__init__(self)

			self.sungmaStr = str
			self.sungmaHp = hp
			self.sungmaMove = move
			self.sungmaImmune = immune

			self.toolTip = uiToolTip.ToolTip(100)
			self.toolTip.HideToolTip()

		def SetSungmaValue(self, str, hp, move, immune):
			self.sungmaStr = str
			self.sungmaHp = hp
			self.sungmaMove = move
			self.sungmaImmune = immune

			self.Refresh()

		def Refresh(self):
			fileName = "d:/ymir work/ui/skill/common/affect/sungma_buff.sub"
			try:
				self.LoadImage(fileName)
			except:
				import dbg
				dbg.TraceError("SungMaAffectImage.SetSungmaValue- LoadError %s" % (fileName))

			self.SetScale(0.7, 0.7)

			self.toolTip.ClearToolTip()

			self.toolTip.AppendSpace(5)
			self.toolTip.AutoAppendTextLine(localeInfo.TOOLTIP_AFFECT_SUNGMA_DESC, self.toolTip.TITLE_COLOR, False)
			self.toolTip.AutoAppendTextLine(localeInfo.TOOLTIP_AFFECT_SUNGMA_STR % (self.sungmaStr), self.toolTip.FONT_COLOR, False)
			self.toolTip.AutoAppendTextLine(localeInfo.TOOLTIP_AFFECT_SUNGMA_HP % (self.sungmaHp), self.toolTip.FONT_COLOR, False)
			self.toolTip.AutoAppendTextLine(localeInfo.TOOLTIP_AFFECT_SUNGMA_MOVE % (self.sungmaMove), self.toolTip.FONT_COLOR, False)
			self.toolTip.AutoAppendTextLine(localeInfo.TOOLTIP_AFFECT_SUNGMA_IMMUNE % (self.sungmaImmune), self.toolTip.FONT_COLOR, False)
			self.toolTip.ResizeToolTip()

		def ShowHover(self):
			self.toolTip.ShowToolTip()
			return self.toolTip.HideToolTip

		def OnMouseOverIn(self):
			uiaffecthover.Over(self)

		def OnMouseOverOut(self):
			uiaffecthover.Out(self)

class HorseImage(ui.ExpandedImageBox):
	def __del__(self):
		ui.ExpandedImageBox.__del__(self)
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)
		self.descriptions = []
	def __GetHorseGrade(self, level):
		return 0 if level == 0 else (level-1)//10 + 1
	def SetState(self, level, health, battery):
		self.descriptions = []
		if level>0:
			try:
				grade = self.__GetHorseGrade(level)
				self.__AppendText(localeInfo.LEVEL_LIST[grade])
			except IndexError:
				return
			try:
				healthName=localeInfo.HEALTH_LIST[health]
				if len(healthName)>0:
					self.__AppendText(healthName)
			except IndexError:
				return
			if health>0:
				if battery==0:
					self.__AppendText(localeInfo.NEEFD_REST)
			try:
				FILE_PATH = "d:/ymir work/ui/pattern/HorseState/"
				FILE_DICT = {
					0 : FILE_PATH+"00.dds",
					1 : FILE_PATH+"00.dds",
					2 : FILE_PATH+"00.dds",
					3 : FILE_PATH+"00.dds",
					10 : FILE_PATH+"10.dds",
					11 : FILE_PATH+"11.dds",
					12 : FILE_PATH+"12.dds",
					13 : FILE_PATH+"13.dds",
					20 : FILE_PATH+"20.dds",
					21 : FILE_PATH+"21.dds",
					22 : FILE_PATH+"22.dds",
					23 : FILE_PATH+"23.dds",
					30 : FILE_PATH+"30.dds",
					31 : FILE_PATH+"31.dds",
					32 : FILE_PATH+"32.dds",
					33 : FILE_PATH+"33.dds",
				}
				fileName=FILE_DICT[health*10+battery]
			except KeyError:
				return
			try:
				self.LoadImage(fileName)
				self.SetScale(0.7, 0.7)
			except:
				return
	def __AppendText(self, text):
		self.descriptions.append(text)
	def _BuildHover(self, tooltip):
		for text in self.descriptions:
			tooltip.AutoAppendNewTextLineResize(text)
	def ShowHover(self):
		if not self.descriptions:
			return None
		interface = osfInfo.GetInterfaceInstance()
		tooltip = interface.tooltipItem if interface else None
		return uiaffecthover.ShowTooltip(tooltip, self, tuple(self.descriptions), self._BuildHover)
	def OnMouseOverIn(self):
		uiaffecthover.Over(self)
	def OnMouseOverOut(self):
		uiaffecthover.Out(self)

if app.ENABLE_GROWTH_PET_SYSTEM:
	class GrowthPetImage(ui.ExpandedImageBox):

		def __init__(self):
			ui.ExpandedImageBox.__init__(self)

			self.toolTipText = None
			self.description = None

		def __del__(self):
			ui.ExpandedImageBox.__del__(self)

		def SetToolTipText(self, text, x = 0, y = -19):

			if not self.toolTipText:
				textLine = ui.TextLine()
				textLine.SetParent(self)
				textLine.SetSize(0, 0)
				textLine.SetOutline()
				textLine.Hide()
				self.toolTipText = textLine

			self.toolTipText.SetText(text)
			w, h = self.toolTipText.GetTextSize()
			if localeInfo.IsARABIC():
				self.toolTipText.SetPosition(w+20, y)
			else:
				self.toolTipText.SetPosition(max(0, x + self.GetWidth()//2 - w//2), y)

		def SetDescription(self, description):
			self.description = description

		def OnMouseOverIn(self):
			if self.toolTipText:
				self.toolTipText.Show()

		def OnMouseOverOut(self):
			if self.toolTipText:
				self.toolTipText.Hide()

BALANCED_RARITY_AFFECT = 814
SAGE_COMPLETION_AFFECT = 815

# Affect-bar label of a cooked-fish buff by its apply (English, Czech, suffix).
# Which fish, affect type and icon belong to an apply is server data
# (servergamedata.COOKED_FISH_BUFFS); ci/tests/test_fishing_client_data.py
# requires a label for every exported apply.
COOKED_FISH_LABELS = {
	'ATTBONUS_METIN': ('Meteors', 'Síla proti meteorům', '%'),
	'ATTBONUS_BOSS': ('Bosses', 'Síla proti bossům', '%'),
	'ATTBONUS_UNDEAD': ('Undead', 'Síla proti nemrtvým', '%'),
	'ATTBONUS_DEVIL': ('Devils', 'Síla proti ďáblům', '%'),
	'ATTBONUS_ORC': ('Orcs', 'Síla proti orkům', '%'),
	'ATTBONUS_HUMAN': ('Half humans', 'Síla proti pololidem', '%'),
	'ATT_GRADE_BONUS': ('Attack value', 'Hodnota útoku', ''),
	'MAGIC_ATT_GRADE': ('Magic attack value', 'Magická hodnota útoku', ''),
	'SKILL_DAMAGE_BONUS': ('Skill damage', 'Poškození schopností', '%'),
	'ENCHANT_FIRE': ('Fire power', 'Síla ohně', '%'),
	'ENCHANT_ICE': ('Ice power', 'Síla ledu', '%'),
	'ENCHANT_ELECT': ('Lightning power', 'Síla blesku', '%'),
	'ENCHANT_WIND': ('Wind power', 'Síla větru', '%'),
	'ENCHANT_EARTH': ('Earth power', 'Síla země', '%'),
	'ENCHANT_DARK': ('Dark power', 'Síla temnoty', '%'),
}


def SageCompletionTitle(value):
	return localeInfo.SAGE_COMPLETION_BONUS % (int(value), int(value))


def BalancedRarityTitle(percent):
	grade = max(0, min(6, int(percent) // 2))
	return localeInfo.RARITY_BALANCED_TITLE % (("", "I", "II", "III", "IV", "V", "VI")[grade], grade * 2)


class AffectImage(ui.ExpandedImageBox):
	def __init__(self):
		ui.ExpandedImageBox.__init__(self)

		self.toolTipText = None
		self.isSkillAffect = False
		self.pvmPersonalSkill = 0
		self.description = None
		self.endTime = 0
		self.affect = None
		self.isClocked = True
		self.hoverTimeLine = None
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			self.isCanRemove=False

	def LoadImage(self, filename):
		ui.ExpandedImageBox.LoadImage(self, filename)
		self.iconPath = filename

	def GetIconPath(self):
		return getattr(self, "iconPath", "")

	def SetAffect(self, affect):
		self.affect = affect
	def GetAffect(self):
		return self.affect
	def SetDescription(self, description):
		self.description = description
	def GetDescription(self):
		return self.description
	def SetDuration(self, duration):
		self.endTime = 0
		if duration > 0:
			self.endTime = app.GetGlobalTimeStamp() + duration
	def SetEndTime(self, endTime):
		self.endTime = max(0, endTime)
	def GetEndTime(self):
		return self.endTime

	if not app.ENABLE_RENEWAL_AFFECT_SHOWER:
		def SetToolTipText(self, text, x = 0, y = -19):
			if not self.toolTipText:
				textLine = ui.TextLine()
				textLine.SetParent(self)
				textLine.SetSize(0, 0)
				textLine.SetOutline()
				textLine.Hide()
				self.toolTipText = textLine
			self.toolTipText.SetText(text)
			w, h = self.toolTipText.GetTextSize()
			self.toolTipText.SetPosition(max(0, x + self.GetWidth()//2 - w//2), y)
		def UpdateAutoPotionDescription(self):
			self.SetToolTipText(self.description, 0, 40)
		def SetClock(self, isClocked):
			self.isClocked = isClocked
		def UpdateDescription(self):
			if not self.isClocked:
				self.__UpdateDescription2()
				return
			if not self.description:
				return
			toolTip = self.description
			if self.endTime > 0:
				leftTime = localeInfo.SecondToDHM(self.endTime - app.GetGlobalTimeStamp())
				toolTip += " (%s : %s)" % (localeInfo.LEFT_TIME, leftTime)
			self.SetToolTipText(toolTip, 0, 40)
		def __UpdateDescription2(self):
			if not self.description:
				return
			toolTip = self.description
			self.SetToolTipText(toolTip, 0, 40)

	def SetSkillAffectFlag(self, flag):
		self.isSkillAffect = flag

	def IsSkillAffect(self):
		return self.isSkillAffect

	if app.ENABLE_RENEWAL_AFFECT_SHOWER:
		def FormatTime(self, seconds):
			if seconds <= 0:
				return "0s"
			m, s = divmod(seconds, 60)
			h, m = divmod(m, 60)
			d, h = divmod(h, 24)
			timeText = ""
			if d > 0:
				timeText += "{}d".format(d)
				timeText += " "
			if h > 0:
				timeText += "{}h".format(h)
				timeText += " "
			if m > 0:
				timeText += "{}m".format(m)
				timeText += " "
			if s > 0:
				timeText += "{}s".format(s)
			return timeText

		def AddAffect(self, pointIdx, pointVal):
			if not [pointIdx, pointVal] in self.affectList:
				self.affectList.append([pointIdx, pointVal])
		def RemoveAffect(self, pointIdx, pointVal):
			if [pointIdx, pointVal] in self.affectList:
				del self.affectList[self.affectList.index([pointIdx, pointVal])]

	if app.ENABLE_RENEWAL_AFFECT_SHOWER:
		# The bar keeps one hover surface (root/uiaffecthover.py): the icon only says Over / Out, the controller shows
		# this icon's tooltip, hides the previous one and checks the mouse every frame. The content is built into the
		# shared tooltip once per data change; while shown, only the remaining time line is rewritten each second.
		def _HoverIsPersonal(self):
			return bool(self.pvmPersonalSkill and pvmpersonal.current())

		def _HoverTooltip(self):
			interface = osfInfo.GetInterfaceInstance()
			if not interface:
				return None
			if self._HoverIsPersonal() or self.IsSkillAffect():
				return interface.tooltipSkill
			return interface.tooltipItem

		def _HoverKey(self):
			if self._HoverIsPersonal():
				# Title, value and countdown come from the live personal model: each second is new content.
				return ("pvm", self.pvmPersonalSkill, self.description, int(app.GetTime()))
			rawAffect = self.GetAffect()
			data = GetAffectTooltipData(rawAffect, self.IsSkillAffect())
			return (rawAffect, self.description, self.IsSkillAffect(), self.isCanRemove, self.endTime,
				repr(sorted(data.items())) if data else "")

		def _HoverTimeText(self, endTime):
			return "%s: %s" % (localeInfo.LEFT_TIME, self.FormatTime(endTime - app.GetGlobalTimeStamp()))

		def _RefreshHoverTime(self):
			if self.hoverTimeLine:
				line, endTime = self.hoverTimeLine
				line.SetText(self._HoverTimeText(endTime))

		def _BuildHover(self, tooltip):
			self.hoverTimeLine = None
			if self._HoverIsPersonal():
				AppendAffectTitle(tooltip, pvmpersonaltext.title(self.pvmPersonalSkill, skill.GetSkillName(self.pvmPersonalSkill), app.GetTime()))
				row = pvmpersonal.current().rows.get(self.pvmPersonalSkill)
				role = {0: "combat", 1: "defense", 2: "defense"}.get(row.get("role"), "stat") if row else "stat"
				pvmpersonaltext.append_bonus(tooltip, self.pvmPersonalSkill, app.GetTime(),
					value_color=uieffecttooltipstyle.ColorForRole(role))
				return
			rawAffect = self.GetAffect()
			skillIndex = AffectToSkillIndex(rawAffect) if self.IsSkillAffect() else 0
			if rawAffect == chr.NEW_AFFECT_AUTO_HP_RECOVERY or rawAffect == chr.NEW_AFFECT_AUTO_SP_RECOVERY:
				tooltip.AutoAppendNewTextLineResize(self.description, 0xffC5C7C4)
				return
			affectData = GetAffectTooltipData(rawAffect, self.IsSkillAffect())
			affectList = affectData["affect"] if "affect" in affectData else []
			maxDuration = affectData["duration"] if "duration" in affectData else 0
			if self.description:
				AppendAffectTitle(tooltip, self.description)
				tooltip.AppendSpace(5)

			if rawAffect == BALANCED_RARITY_AFFECT:
				percent = int(affectList[0][1]) if affectList else 0
				grade = max(0, min(6, percent // 2))
				tooltip.AutoAppendNewTextLineResize(localeInfo.TOOLTIP_MELEE_MAGIC_ATTBONUS_PER(percent), 0xff95A693 - 0x100000000)
				import uiRarity
				tooltip.AutoAppendNewTextLineResize(localeInfo.RARITY_BALANCED_MINIMUM % uiRarity.GradeName(grade))
			if self.IsSkillAffect():
				try:
					role = uieffecttooltipstyle.RoleForPoint(affectList[0][0]) if affectList else "stat"
					tooltip.SetSkillEx(skillIndex, color=uieffecttooltipstyle.ColorForRole(role))
				except:
					for data in affectList:
						val = uiToolTip.ItemToolTip.POINT_DICT.get(data[0])
						text_line = None
						if callable(val):
							text_line = val(data[1])
						elif isinstance(val, str):
							try:
								text_line = val % data[1]
							except Exception:
								text_line = "{} {}".format(val, data[1])
						else:
							text_line = "{}: {}".format(data[0], data[1])
						if text_line:
							tooltip.AutoAppendNewTextLineResize(text_line, uieffecttooltipstyle.ColorForRole(uieffecttooltipstyle.RoleForPoint(data[0])))
			else:
				try:
					for data in affectList:
						if data[0] != 0 and data[0] in uiToolTip.ItemToolTip.POINT_DICT:
							tooltip.AutoAppendNewTextLineResize(uiToolTip.ItemToolTip.POINT_DICT[data[0]](data[1]), uieffecttooltipstyle.ColorForRole(uieffecttooltipstyle.RoleForPoint(data[0])))
				except:
					pass

			if rawAffect == chr.NEW_AFFECT_AUTO_METIN_FARM:
				tooltip.AppendSpace(5)
				tooltip.AutoAppendNewTextLineResize(localeInfo.AFFECT_METIN_QUEUE_INFO)

			elif rawAffect == chr.NEW_AFFECT_BRAVE_CAPE:
				tooltip.AppendSpace(5)
				tooltip.AutoAppendNewTextLineResize(localeInfo.BRAVERY_CAPE_TEXT)

			timeEnd = 0
			if self.endTime > 0 and (self.endTime-app.GetGlobalTimeStamp()) < (60*60*24*365):
				timeEnd = self.endTime
			elif maxDuration > 0 and (maxDuration-app.GetGlobalTimeStamp()) < (60*60*24*365):
				timeEnd = maxDuration
			if timeEnd:
				tooltip.AppendSpace(5)
				line = tooltip.AutoAppendNewTextLineResize(self._HoverTimeText(timeEnd), 0xffC5C7C4)
				if line is not None:
					self.hoverTimeLine = (line, timeEnd)
			if self.isCanRemove:
				tooltip.AppendSpace(7)
				tooltip.AutoAppendNewTextLineResize(localeInfo.AFFECTSHOWER_REMOVE_TEXT)

		def ShowHover(self):
			tooltip = self._HoverTooltip()
			if tooltip is None:
				return None
			if not uiaffecthover.Fill(tooltip, self, self._HoverKey(), self._BuildHover):
				self._RefreshHoverTime()
			tooltip.ShowToolTip()
			return uiaffecthover.Hider(tooltip, self)

		def TickHover(self):
			tooltip = self._HoverTooltip()
			if tooltip is None or not uiaffecthover.Owns(tooltip, uiaffecthover.Owner(self)):
				return None
			if uiaffecthover.Fill(tooltip, self, self._HoverKey(), self._BuildHover):
				tooltip.ShowToolTip()
			else:
				self._RefreshHoverTime()
			return uiaffecthover.Hider(tooltip, self)

	def OnMouseOverIn(self):
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			uiaffecthover.Over(self)
		elif self.toolTipText:
			self.toolTipText.Show()

	def OnMouseOverOut(self):
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			uiaffecthover.Out(self)
		elif self.toolTipText:
			self.toolTipText.Hide()

if app.ENABLE_RENEWAL_AFFECT_SHOWER:
	class AffectGroupImage(ui.ExpandedImageBox):
		def __init__(self, groupKey, iconPath, onSummaryOpen=None):
			ui.ExpandedImageBox.__init__(self)
			self.groupKey = groupKey
			self.summary = None
			self.members = []
			self.onSummaryOpen = onSummaryOpen
			self.portrait = None
			self.LoadImage(iconPath)
			self.SetScale(22.0 / max(1, self.GetWidth()), 22.0 / max(1, self.GetHeight()))
			self.SetSize(25, 26)
			if groupKey == "buffs":
				# The approved original 43px face inside the original 53px square.
				self.portrait = ui.ExpandedImageBox()
				self.portrait.SetParent(self)
				self.portrait.AddFlag("not_pick")
				self.portrait.LoadImage("icon/face/shaman_w.tga")
				self.portrait.SetScale(18.0 / max(1, self.portrait.GetWidth()), 18.0 / max(1, self.portrait.GetHeight()))
				self.portrait.SetSize(18, 18)
				self.portrait.SetPosition(2, 2)
				self.portrait.Show()

			self.countBadge = ui.NumberLine()
			self.countBadge.SetParent(self)
			self.countBadge.SetHorizontalAlignRight()
			self.countBadge.SetPosition(23, 15)
			self.countBadge.AddFlag("not_pick")
			self.countBadge.Show()

		def SetMembers(self, members):
			self.members = list(members)
			self.countBadge.SetNumber(str(len(self.members)))
			if self.summary and self.summary.IsShow():
				self.summary.Refresh()

		def GetSummaryRows(self):
			rows = []
			for member in self.members:
				if getattr(member, "pvmPersonalSkill", 0):
					model = pvmpersonal.current()
					row = model.rows.get(member.pvmPersonalSkill) if model else None
					if row:
						role = {0: "combat", 1: "defense", 2: "defense"}.get(row.get("role"), "stat")
						rows.append((member.GetIconPath(), member.GetDescription(),
							(pvmpersonaltext.value(row),), row["end"], (role,)))
						continue
				data = GetAffectTooltipData(member.GetAffect(), member.IsSkillAffect())
				bonuses = []
				roles = []
				for point, value in data.get("affect", []):
					formatter = uiToolTip.ItemToolTip.POINT_DICT.get(point)
					if point == AffectShower.MELEE_MAGIC_ATTACK_POINT:
						formatter = uiToolTip.ItemToolTip.AFFECT_DICT.get(item.APPLY_MELEE_MAGIC_ATTBONUS_PER)
					if formatter:
						text = formatter(value) if callable(formatter) else formatter
						if text and text not in bonuses:
							bonuses.append(text)
							roles.append(uieffecttooltipstyle.RoleForPoint(point))
				rows.append((member.GetIconPath(), member.GetDescription(), tuple(bonuses),
					data.get("duration", member.GetEndTime()), tuple(roles)))
			return rows

		def CreateSummary(self):
			from uiaffectsummary import AffectSummary
			return AffectSummary(self)

		def GetSummaryTitle(self):
			return GetAffectGroupText(self.groupKey)

		def ShowHover(self):
			if not self.members:
				return None
			if self.onSummaryOpen:
				self.onSummaryOpen(self.groupKey)
			if self.summary is None:
				self.summary = self.CreateSummary()
			self.summary.Open()
			return self.summary.Close

		def HoverHeld(self):
			# The summary is a panel the mouse may cross to; it closes itself after its own grace (uiaffectsummary).
			return bool(self.summary and self.summary.IsShow())

		def HoverGuard(self, other):
			# An icon of the row below lies on the way to the panel: it waits a moment before taking over. The window
			# height (25 x 26), not ImageBox.GetHeight = the texture (32 / 53 / 64 px).
			try:
				window = getattr(ui, "Window", None)
				height = window.GetHeight(self) if window else self.GetHeight()
				return other.GetGlobalPosition()[1] >= self.GetGlobalPosition()[1] + height - 1
			except Exception:
				return False

		def OnMouseOverIn(self):
			uiaffecthover.Over(self)

		def OnMouseOverOut(self):
			uiaffecthover.Out(self)

		def CloseSummary(self):
			if self.summary:
				self.summary.Close()

		def Destroy(self):
			self.CloseSummary()
			if self.summary:
				self.summary.Destroy()
			self.summary = None
			self.members = []
			self.onSummaryOpen = None
			if self.portrait:
				self.portrait.Hide()
			self.portrait = None
			self.Hide()

	class BiologPassiveImage(AffectGroupImage):
		def __init__(self):
			AffectGroupImage.__init__(self, "biolog",
				"d:/ymir work/ui/game/crimson_ember/biolog/research/chaegirab_header.png")

		def GetSummaryTitle(self):
			from settingslocale import Text
			return Text(u"Biologick\u00e9 bonusy", "Biologist bonuses")

		def CreateSummary(self):
			from uiaffectsummary import CompactAffectSummary
			return CompactAffectSummary(self)

		def SetPointMembers(self, members):
			# [(point, value)] of the server affect; SetMembers keeps [(apply, value)] of the Biologist window.
			self.byPoint = True
			self.SetMembers(members)

		def SetApplyMembers(self, members):
			self.byPoint = False
			self.SetMembers(members)

		def GetSummaryRows(self):
			if not getattr(self, "byPoint", False):
				return [(None, GET_AFFECT_STRING(kind, value), (), 0,
					uieffecttooltipstyle.RoleForPoint(item.GetApplyPoint(kind)))
					for kind, value in self.members]
			rows = []
			for point, value in self.members:
				formatter = uiToolTip.ItemToolTip.POINT_DICT.get(point)
				if point == AffectShower.MELEE_MAGIC_ATTACK_POINT:
					formatter = uiToolTip.ItemToolTip.AFFECT_DICT.get(item.APPLY_MELEE_MAGIC_ATTBONUS_PER)
				text = (formatter(value) if callable(formatter) else formatter) if formatter else None
				if text:
					rows.append((None, text, (), 0, uieffecttooltipstyle.RoleForPoint(point)))
			return rows

class PenetrationOverflowImage(AffectImage):
	# Existing server/client wire point, already stored by the native player.
	# Read the calculated bonus; its conversion rate remains server authority.
	POINT_RARITY_OVERFLOW_ATTACK = 170

	def __init__(self):
		AffectImage.__init__(self)
		self.attack = 0
		self.LoadImage("icon/affect/penetration_overflow.png")
		self.SetScale(0.7, 0.7)
		self.SetSize(22, 22)

	def SetAttack(self, attack):
		self.attack = attack
		self.SetDescription(localeInfo.PENETRATION_OVERFLOW_TITLE)
		if not app.ENABLE_RENEWAL_AFFECT_SHOWER:
			self.SetToolTipText("%s: %s / %s" % (self.description,
				localeInfo.TOOLTIP_ATT_GRADE(attack), localeInfo.TOOLTIP_MAGIC_ATT_GRADE(attack)), 0, 40)

	def _HoverKey(self):
		return ("penetration-overflow", self.description, self.attack)

	def _BuildHover(self, tooltip):
		AppendAffectTitle(tooltip, self.description)
		tooltip.AppendSpace(5)
		color = uieffecttooltipstyle.ColorForRole("combat")
		tooltip.AutoAppendNewTextLineResize(localeInfo.TOOLTIP_ATT_GRADE(self.attack), color)
		tooltip.AutoAppendNewTextLineResize(localeInfo.TOOLTIP_MAGIC_ATT_GRADE(self.attack), color)


class AffectShower(ui.Window):
	# Server affect types below AFFECT_MOV_SPEED (200) are skill identifiers.
	# Actor flags use a separate, overlapping namespace and own their icons.
	SKILL_AFFECT_TYPE_LIMIT = 200

	MALL_DESC_IDX_START = 1000
	CONSUMABLE_DESC_IDX_START = 2000
	MELEE_MAGIC_ATTACK_POINT = 132
	SUMMARY_ITEMS = {
		MALL_DESC_IDX_START + player.POINT_MAX_HP_PCT: 39017,
		MALL_DESC_IDX_START + MELEE_MAGIC_ATTACK_POINT: 39018,
		MALL_DESC_IDX_START + player.POINT_MALL_DEFBONUS: 39020,
		CONSUMABLE_DESC_IDX_START + player.POINT_CRITICAL_PCT: 39024,
		CONSUMABLE_DESC_IDX_START + player.POINT_PENETRATE_PCT: 39025,
	}
	AFK_AFFECT_KEY = 0x7FFFFF00
	IMAGE_STEP = 25
	AFFECT_MAX_NUM = 32
	INFINITE_AFFECT_DURATION = 0x1FFFFFFF
	END_STRING = "_03"
	GROUP_DATA = {
		"gods": (1, "icon/item/71030.tga"),
		"buffs": (1, "d:/ymir work/ui/public/crimson/windows/character/portrait_frame.tga"),
		"skills": (1, "d:/ymir work/ui/skill/warrior/geomgyeong_03.sub"),
		"dews": (1, "icon/affect/dews_group.tga"),
	}
	GROUP_ORDER = ("gods", "buffs", "skills", "dews")
	DEW_AFFECTS = tuple(dew["affect"] for dew in dewcatalog.DEWS) + tuple(
		getattr(chr, name) for name in (
			"AFFECT_BLEND_POTION_1", "AFFECT_BLEND_POTION_2", "AFFECT_BLEND_POTION_3",
			"AFFECT_BLEND_POTION_4", "AFFECT_BLEND_POTION_5", "AFFECT_BLEND_POTION_6",
		) if hasattr(chr, name))
	SHAMAN_BUFF_AFFECTS = (
		chr.AFFECT_HOSIN, chr.AFFECT_BOHO, chr.AFFECT_GICHEON,
		chr.AFFECT_KWAESOK, chr.AFFECT_JEUNGRYEOK,
	)
	DRAGON_GOD_AFFECTS = tuple(getattr(chr, name) for name in (
		"AFFECT_DRAGON_GOD_1", "AFFECT_DRAGON_GOD_2", "AFFECT_DRAGON_GOD_3",
		"AFFECT_DRAGON_GOD_4", "AFFECT_CRITICAL", "AFFECT_PENETRATE",
	) if hasattr(chr, name))
	CRITICAL_AFFECTS = (
		chr.AFFECT_POISON,
		chr.AFFECT_BLEEDING,
		chr.AFFECT_SLOW,
		chr.AFFECT_STUN,
		chr.AFFECT_PABEOP,
		28,  # Burning is harmful, even though its legacy icon uses skill artwork.
	)
	INDEPENDENT_AFFECTS = (
		BALANCED_RARITY_AFFECT,
		SAGE_COMPLETION_AFFECT,
		chr.AFFECT_ATT_SPEED_POTION,
		chr.NEW_AFFECT_AUTO_HP_RECOVERY,
		chr.NEW_AFFECT_AUTO_SP_RECOVERY,
	)
	if app.ENABLE_AUTO_PICKUP:
		INDEPENDENT_AFFECTS += (
			chr.AFFECT_AUTO_PICKUP_ENABLED,
			chr.AFFECT_AUTO_PICKUP_DISABLED,
		)
	POTION_AFFECTS = (
		chr.AFFECT_ATT_SPEED_POTION,
		chr.AFFECT_MOV_SPEED_POTION,
		chr.AFFECT_FISH_MIND,
	)
	if app.ENABLE_NEW_BLEND_AFFECT:
		POTION_AFFECTS += (
			chr.AFFECT_BLEND_POTION_1,
			chr.AFFECT_BLEND_POTION_2,
			chr.AFFECT_BLEND_POTION_3,
			chr.AFFECT_BLEND_POTION_4,
			chr.AFFECT_BLEND_POTION_5,
			chr.AFFECT_BLEND_POTION_6,
			chr.AFFECT_ENERGY,
			chr.AFFECT_DRAGON_GOD_1,
			chr.AFFECT_DRAGON_GOD_2,
			chr.AFFECT_DRAGON_GOD_3,
			chr.AFFECT_DRAGON_GOD_4,
			chr.AFFECT_CRITICAL,
			chr.AFFECT_PENETRATE,
			chr.AFFECT_ATTACK_SPEED,
			chr.AFFECT_MOVE_SPEED,
		)
	AFFECT_DATA_DICT =	{
		SAGE_COMPLETION_AFFECT: (SageCompletionTitle, "icon/item/50525.tga", 4, 0),
		BALANCED_RARITY_AFFECT: (BalancedRarityTitle, "d:/ymir work/ui/skill/common/affect/balanced_rarity.png", 4, 0),

			chr.AFFECT_POISON : (localeInfo.SKILL_TOXICDIE, "d:/ymir work/ui/skill/common/affect/poison.sub", 2, 0),
			chr.AFFECT_BLEEDING : (localeInfo.SKILL_BLEEDING, "d:/ymir work/ui/skill/common/affect/poison.sub", 2, 0),
			chr.AFFECT_SLOW : (localeInfo.SKILL_SLOW, "d:/ymir work/ui/skill/common/affect/slow.sub", 2, 0),
			chr.AFFECT_STUN : (localeInfo.SKILL_STUN, "d:/ymir work/ui/skill/common/affect/stun.sub", 2, 0),

			chr.AFFECT_ATT_SPEED_POTION : (localeInfo.SKILL_INC_ATKSPD, "d:/ymir work/ui/skill/common/affect/Increase_Attack_Speed.sub", 1, 2),
			chr.AFFECT_MOV_SPEED_POTION : (localeInfo.SKILL_INC_MOVSPD, "d:/ymir work/ui/skill/common/affect/Increase_Move_Speed.sub", 3, 0),
			chr.AFFECT_FISH_MIND : (localeInfo.SKILL_FISHMIND, "d:/ymir work/ui/skill/common/affect/fishmind.sub", 3, 0),

			chr.AFFECT_JEONGWI : (localeInfo.SKILL_JEONGWI, "d:/ymir work/ui/skill/warrior/jeongwi" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_GEOMGYEONG : (localeInfo.SKILL_GEOMGYEONG, "d:/ymir work/ui/skill/warrior/geomgyeong" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_CHEONGEUN : (localeInfo.SKILL_CHEONGEUN, "d:/ymir work/ui/skill/warrior/cheongeun" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_GYEONGGONG : (localeInfo.SKILL_GYEONGGONG, "d:/ymir work/ui/skill/assassin/gyeonggong" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_EUNHYEONG : (localeInfo.SKILL_EUNHYEONG, "d:/ymir work/ui/skill/assassin/eunhyeong" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_GWIGEOM : (localeInfo.SKILL_GWIGEOM, "d:/ymir work/ui/skill/sura/gwigeom" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_GONGPO : (localeInfo.SKILL_GONGPO, "d:/ymir work/ui/skill/sura/gongpo" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_JUMAGAP : (localeInfo.SKILL_JUMAGAP, "d:/ymir work/ui/skill/sura/jumagap" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_HOSIN : (localeInfo.SKILL_HOSIN, "d:/ymir work/ui/skill/shaman/hosin" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_BOHO : (localeInfo.SKILL_BOHO, "d:/ymir work/ui/skill/shaman/boho" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_KWAESOK : (localeInfo.SKILL_KWAESOK, "d:/ymir work/ui/skill/shaman/kwaesok" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_HEUKSIN : (localeInfo.SKILL_HEUKSIN, "d:/ymir work/ui/skill/sura/heuksin" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_MUYEONG : (localeInfo.SKILL_MUYEONG, "d:/ymir work/ui/skill/sura/muyeong" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_GICHEON : (localeInfo.SKILL_GICHEON, "d:/ymir work/ui/skill/shaman/gicheon" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_JEUNGRYEOK : (localeInfo.SKILL_JEUNGRYEOK, "d:/ymir work/ui/skill/shaman/jeungryeok" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_PABEOP : (localeInfo.SKILL_PABEOP, "d:/ymir work/ui/skill/sura/pabeop" + END_STRING + ".sub", 2, 0),
			chr.AFFECT_FALLEN_CHEONGEUN : (localeInfo.SKILL_CHEONGEUN, "d:/ymir work/ui/skill/warrior/cheongeun" + END_STRING + ".sub", 2, 0),
			28 : (localeInfo.SKILL_FIRE, "d:/ymir work/ui/skill/sura/hwayeom_03.sub",),
			chr.AFFECT_CHINA_FIREWORK : (localeInfo.SKILL_POWERFUL_STRIKE, "d:/ymir work/ui/skill/common/affect/powerfulstrike.sub", 2, 0),
			chr.AFFECT_RED_POSSESSION : (localeInfo.SKILL_GWIGEOM, "d:/ymir work/ui/skill/wolfman/red_possession_03.sub", 2, 0),
			chr.AFFECT_BLUE_POSSESSION : (localeInfo.SKILL_CHEONGEUN, "d:/ymir work/ui/skill/wolfman/blue_possession_03.sub", 2, 0),

			chr.NEW_AFFECT_EXP_BONUS : (localeInfo.TOOLTIP_MALL_EXPBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/exp_bonus.sub",1, 0),
			chr.NEW_AFFECT_ITEM_BONUS : (localeInfo.TOOLTIP_MALL_ITEMBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/item_bonus.sub",1, 0),
			chr.NEW_AFFECT_SAFEBOX : (localeInfo.TOOLTIP_MALL_SAFEBOX, "d:/ymir work/ui/skill/common/affect/safebox.sub",1, 0),
			chr.NEW_AFFECT_AUTOLOOT : (localeInfo.TOOLTIP_MALL_AUTOLOOT, "d:/ymir work/ui/skill/common/affect/autoloot.sub",1, 0),
			chr.NEW_AFFECT_FISH_MIND : (localeInfo.TOOLTIP_MALL_FISH_MIND, "d:/ymir work/ui/skill/common/affect/fishmind.sub",1, 0),
			chr.NEW_AFFECT_MARRIAGE_FAST : (localeInfo.TOOLTIP_MALL_MARRIAGE_FAST, "d:/ymir work/ui/skill/common/affect/marriage_fast.sub",1, 0),
			chr.NEW_AFFECT_GOLD_BONUS : (localeInfo.TOOLTIP_MALL_GOLDBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/gold_bonus.sub",1, 0),
			chr.NEW_AFFECT_NO_DEATH_PENALTY : (localeInfo.TOOLTIP_APPLY_NO_DEATH_PENALTY, "d:/ymir work/ui/skill/common/affect/gold_premium.sub",1, 0),

			chr.NEW_AFFECT_SKILL_BOOK_BONUS : (localeInfo.TOOLTIP_APPLY_SKILL_BOOK_BONUS, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 2),
			chr.NEW_AFFECT_SKILL_BOOK_NO_DELAY : (localeInfo.TOOLTIP_APPLY_SKILL_BOOK_NO_DELAY, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 2),

			chr.NEW_AFFECT_AUTO_HP_RECOVERY : (localeInfo.AUTO_RECOVERY_SUN_ACTIVE, "d:/ymir work/ui/pattern/auto_hpgauge/05.dds", 1, 1),
			chr.NEW_AFFECT_AUTO_SP_RECOVERY : (localeInfo.AUTO_RECOVERY_MOON_ACTIVE, "d:/ymir work/ui/pattern/auto_spgauge/05.dds", 1, 1),

			MALL_DESC_IDX_START+MELEE_MAGIC_ATTACK_POINT : (localeInfo.TOOLTIP_MALL_ATTBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/att_bonus.sub", 1, 0),
			CONSUMABLE_DESC_IDX_START+player.POINT_CRITICAL_PCT : (localeInfo.TOOLTIP_APPLY_CRITICAL_PCT, "d:/ymir work/ui/skill/common/affect/critical.sub", 1, 0),
			CONSUMABLE_DESC_IDX_START+player.POINT_PENETRATE_PCT : (localeInfo.TOOLTIP_APPLY_PENETRATE_PCT, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_ATT_BONUS : (localeInfo.TOOLTIP_MALL_ATTBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/att_bonus.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MALL_DEFBONUS : (localeInfo.TOOLTIP_MALL_DEFBONUS_STATIC, "d:/ymir work/ui/skill/common/affect/def_bonus.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MALL_EXPBONUS : (localeInfo.TOOLTIP_MALL_EXPBONUS, "d:/ymir work/ui/skill/common/affect/exp_bonus.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MALL_ITEMBONUS : (localeInfo.TOOLTIP_MALL_ITEMBONUS, "d:/ymir work/ui/skill/common/affect/item_bonus.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MALL_GOLDBONUS : (localeInfo.TOOLTIP_MALL_GOLDBONUS, "d:/ymir work/ui/skill/common/affect/gold_bonus.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_CRITICAL_PCT : (localeInfo.TOOLTIP_APPLY_CRITICAL_PCT,"d:/ymir work/ui/skill/common/affect/critical.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_PENETRATE_PCT : (localeInfo.TOOLTIP_APPLY_PENETRATE_PCT, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MAX_HP_PCT : (localeInfo.TOOLTIP_MAX_HP_PCT, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_MAX_SP_PCT : (localeInfo.TOOLTIP_MAX_SP_PCT, "d:/ymir work/ui/skill/common/affect/gold_premium.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_PC_BANG_EXP_BONUS : (localeInfo.TOOLTIP_MALL_EXPBONUS_P_STATIC, "d:/ymir work/ui/skill/common/affect/EXP_Bonus_p_on.sub", 1, 0),
			MALL_DESC_IDX_START+player.POINT_PC_BANG_DROP_BONUS: (localeInfo.TOOLTIP_MALL_ITEMBONUS_P_STATIC, "d:/ymir work/ui/skill/common/affect/Item_Bonus_p_on.sub", 1, 0),
	}

	POTION_AFFECTS += tuple(dew['affect'] for dew in dewcatalog.DEWS)
	for dew in dewcatalog.DEWS:
		AFFECT_DATA_DICT[dew['affect']] = (lambda value, d=dew: d['name_cz'] + ': ' + d['effect'] + ' +' + str(int(value)) + d['unit'],
			'icon/item/dews/' + dew['key'] + '_l.tga', 3, 0)

	AFFECT_DATA_DICT[chr.AFFECT_RESEARCHER_ELIXIR] = (localeInfo.TOOLTIP_AFFECT_RESEARCHER_ELIXIR, "d:/ymir work/ui/skill/common/affect/researcher_elixir.sub", 4, 0)
	AFFECT_DATA_DICT[chr.NEW_AFFECT_SAFE_BOX_BUFF] = (localeInfo.TOOLTIP_AFFECT_SAFEBOX_BUFF_01, "d:/ymir work/ui/skill/common/affect/safebox_buff.sub", 4, 0)

	if app.ENABLE_DRAGON_SOUL_SYSTEM:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_DRAGON_SOUL_DECK1] = (localeInfo.TOOLTIP_DRAGON_SOUL_DECK1, "d:/ymir work/ui/dragonsoul/buff_ds_sky1.tga", 4, 0)
		AFFECT_DATA_DICT[chr.NEW_AFFECT_DRAGON_SOUL_DECK2] = (localeInfo.TOOLTIP_DRAGON_SOUL_DECK2, "d:/ymir work/ui/dragonsoul/buff_ds_land1.tga", 4, 0)

	if app.ENABLE_COMBAT_ZONE:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_COMBAT_ZONE_POTION] = (localeInfo.COMBAT_ZONE_TOOLTIP_BATTLE_POTION, "icon/item/27125.tga", 4, 0)

	if app.ENABLE_RENEWAL_AFFECT_SHOWER:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_POLYMORPH] =  (localeInfo.POLYMORPH_AFFECT_TOOLTIP, "d:/ymir work/ui/game/poly/poly.png", 4, 0)

	if app.ENABLE_MULTI_FARM_BLOCK:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_MULTI_FARM] =  (localeInfo.MULTI_FARM_PREMIUM_EFFECT, "d:/ymir work/ui/game/farm/can_farm_premimum.tga", 4, 0)

	if app.ENABLE_AUTO_FARM_METIN:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_AUTO_METIN_FARM] =  (localeInfo.NEW_AFFECT_AUTO_METIN_FARM, "icon/item/61400.tga", 4, 0)

	if app.ENABLE_DS_SET:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_DS_SET] = (localeInfo.TOOLTIP_DS_SET, "d:/ymir work/ui/skill/common/affect/ds_set_bonus.sub", 4, 0)

	if app.ENABLE_BRAVE_CAPE_RENEWAL:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_BRAVE_CAPE] =  (localeInfo.NEW_AFFECT_BRAVE_CAPE, "d:/ymir work/ui/game/affect/aggro.png", 4, 0)

	if app.ENABLE_OFFLINE_SHOP:
		AFFECT_DATA_DICT[chr.AFFECT_OFFLINE_SHOP_DECORATION] = (localeInfo.OFFLINE_SHOP_DECORATION_AFFECT, "d:/ymir work/ui/skill/common/affect/ds_set_bonus.sub", 4, 0)

	if app.ENABLE_NEW_BLEND_AFFECT:
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_1] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_1, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_1) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_2] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_2, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_2) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_3] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_3, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_3) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_4] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_4, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_4) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_5] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_5, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_5) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_BLEND_POTION_6] = (localeInfo.TOOLTIP_AFFECT_BLEND_POTION_6, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_BLEND_POTION_6) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_ENERGY] = (localeInfo.TOOLTIP_AFFECT_ENERGY, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_ENERGY) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_DRAGON_GOD_1] = (localeInfo.TOOLTIP_AFFECT_DRAGON_GOD_1, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_DRAGON_GOD_1) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_DRAGON_GOD_2] = (localeInfo.TOOLTIP_AFFECT_DRAGON_GOD_2, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_DRAGON_GOD_2) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_DRAGON_GOD_3] = (localeInfo.TOOLTIP_AFFECT_DRAGON_GOD_3, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_DRAGON_GOD_3) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_DRAGON_GOD_4] = (localeInfo.TOOLTIP_AFFECT_DRAGON_GOD_4, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_DRAGON_GOD_4) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_CRITICAL] = (localeInfo.TOOLTIP_AFFECT_CRITICAL, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_CRITICAL) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_PENETRATE] = (localeInfo.TOOLTIP_AFFECT_PENETRATE, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_PENETRATE) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_ATTACK_SPEED] = (localeInfo.TOOLTIP_AFFECT_ATTACK_SPEED, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_ATTACK_SPEED) + ".dds")
		AFFECT_DATA_DICT[chr.AFFECT_MOVE_SPEED] = (localeInfo.TOOLTIP_AFFECT_MOVE_SPEED, "d:/ymir work/ui/game/blend_affect/" + str(chr.AFFECT_MOVE_SPEED) + ".dds")

	if app.ENABLE_FISHING_GAME:
		AFFECT_DATA_DICT[chr.AFFECT_FISHING_GOLD_TUNA] = (localeInfo.TOOLTIP_AFFECT_FISHING_GOLD_TUNA, "d:/ymir work/ui/skill/common/affect/fishing_gold_tuna_buff.sub")
		AFFECT_DATA_DICT[chr.AFFECT_FISHING_MOVE_SPEED_DOWN] = (localeInfo.TOOLTIP_AFFECT_FISHING_MOVE_SPEED_DOWN, "d:/ymir work/ui/skill/common/affect/fishing_move_speed_down.sub")

	# Cooked fish share one affect per bonus family; upgraded fish refresh it.
	# The families, affect types and icons come from the server fishing
	# catalog (servergamedata.COOKED_FISH_BUFFS); only the labels live here.
	fishIsCzech = getattr(app, "GetLocalePath", lambda: "locale/en")().replace("\\", "/").rsplit("/", 1)[-1].lower() == "cz"
	for fish_affect, fish_icon, fish_improved, fish_apply in servergamedata.COOKED_FISH_BUFFS:
		fish_english, fish_czech, fish_suffix = COOKED_FISH_LABELS[fish_apply]
		fish_label = fish_czech if fishIsCzech else fish_english
		AFFECT_DATA_DICT[fish_affect] = (
			lambda value, label=fish_label, suffix=fish_suffix: "%s +%d%s" % (label, int(value), suffix),
			"icon/item/%d.tga" % fish_icon, 4, 0)
	if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
		AFFECT_DATA_DICT[chr.NEW_AFFECT_RED_DRAGONLAIR_BUFF] = (localeInfo.TOOLTIP_AFFECT_RED_DRAGONLAIR_BUFF, "d:/ymir work/ui/skill/common/affect/def_grade_down.sub")

	if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
		AFFECT_DATA_DICT[chr.AFFECT_AUTO_USE] = (localeInfo.TOOLTIP_AUTO_SYSTEM_PRIMIUM, "d:/ymir work/ui/skill/common/affect/auto_premium.sub")


	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.ClearAllAffects()
		self.serverPlayTime=0
		self.clientPlayTime=0
		self.lastUpdateTime=0
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			self.removeAffectDialog = None
			global affectDict
			affectDict={}
		if getattr(self, "hover", None):
			uiaffecthover.Uninstall(self.hover)
		self.horseImage=None
		self.lovePointImage=None
		self.afkImage=None

		if app.ENABLE_MULTI_FARM_BLOCK:
			self.multiFarmBlockDialog=None
			self.farmStatusImage=None

		if app.ENABLE_CONQUEROR_LEVEL:
			self.sungmaImage = None

		if app.ENABLE_AUTO_PICKUP:
			self.autopickupQuestionDlg = None

		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.petSkillaffectImageDict = {}

	def __init__(self):
		ui.Window.__init__(self)
		self.affectImageDict={}
		self.affectGroupImageDict={}
		self.expandedAffectGroups=set()
		self.Destroy()
		# One tooltip / summary for the whole bar, driven by the icon under the mouse (root/uiaffecthover.py).
		# within: the bar window itself is under the mouse (a gap of an icon's cell) -> the frame check runs.
		self.hover = uiaffecthover.HoverController(app.GetTime, ui.__mem_func__(self.__HoverPointed),
			report=AffectShower.__HoverReport, within=ui.__mem_func__(self.IsIn))
		uiaffecthover.Install(self.hover)

		self.SetPosition(10, 10)
		self.Show()

	def __HoverCandidates(self):
		images = list(self.affectImageDict.values())
		images += list(getattr(self, "affectGroupImageDict", {}).values())
		images += list(getattr(self, "pvmPersonalImages", {}).values())
		for name in ("biologImage", "skillTreeImage", "horseImage", "lovePointImage", "afkImage", "farmStatusImage",
				"sungmaImage", "penetrationOverflowImage"):
			image = getattr(self, name, None)
			if image:
				images.append(image)
		return [image for image in images if image.IsShow()]

	@staticmethod
	def __HoverReport(text):
		import dbg
		dbg.TraceError(text)

	def __HoverPointed(self, hovered):
		"""The bar icon under the mouse, or None. The engine decides whether the mouse is on the bar at all (a window
		over the bar or the open summary panel takes it), the geometry decides which icon: an icon moved, hidden or
		replaced by a refresh under a still mouse gets no Over / Out from the engine.

		an icon owns its cell of the bar (IMAGE_STEP x the row step, or its window when larger), so the gap
		between two icons belongs to one of them and never blinks the tooltip; sizes are the window's
		(ui.Window.GetWidth), not ImageBox.GetWidth, which is the texture (32 px for a 22 px icon)."""
		images = self.__HoverCandidates()
		x, y = wndMgr.GetMousePosition()
		window = getattr(ui, "Window", None)
		step = getattr(self, "IMAGE_STEP", 25)
		rowStep = 26

		def size(image):
			if window:
				return window.GetWidth(image), window.GetHeight(image)
			return image.GetWidth(), image.GetHeight()

		def under(image, cell=True):
			left, top = image.GetGlobalPosition()
			width, height = size(image)
			if cell:
				width, height = max(width, step), max(height, rowStep)
			return left <= x < left + width and top <= y < top + height

		if hovered is not None and not any(image is hovered for image in images):
			# A button of the Pasivky row (uipvmpersonal) shares the surface: it stays while it is the pointed window.
			return hovered if hovered.IsShow() and hovered.IsIn() and under(hovered, False) else None
		if not (self.IsIn() or any(image.IsIn() for image in images)):
			return None
		if hovered is not None and any(image is hovered for image in images) and under(hovered):
			return hovered
		for image in sorted(images, key=lambda image: image.GetGlobalPosition()[::-1]):
			if under(image):
				return image
		return None

	def SetSkillTreeState(self, remaining, members):
		image = getattr(self, "skillTreeImage", None)
		wasVisible = bool(image and image.IsShow())
		if remaining > 0 and image is None:
			from uiskilltreeaffect import SkillTreeAffectImage
			image = SkillTreeAffectImage()
			image.SetParent(self)
			self.skillTreeImage = image
		if image:
			image.summaryAnchor = ui.__mem_func__(self.__SummaryAnchor)
			image.SetState(remaining, members)
			if wasVisible != bool(remaining > 0):
				self.__ArrangeImageList()

	def ClearAllAffects(self):
		if getattr(self, "penetrationOverflowImage", None):
			self.penetrationOverflowImage.Hide()
		self.penetrationOverflowImage = None
		for image in getattr(self, "affectImageDict", {}).values():
			image.Hide()
		if getattr(self, "biologImage", None):
			self.biologImage.Destroy()
		self.biologImage = None
		if getattr(self, "skillTreeImage", None):
			self.skillTreeImage.Destroy()
		self.skillTreeImage = None
		for image in getattr(self, "pvmPersonalImages", {}).values():
			image.Hide()
		self.pvmPersonalImages = {}
		if getattr(self, "hover", None):
			self.hover.Reset()
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			global affectDict
			affectDict = {}
		self.horseImage=None
		self.lovePointImage=None
		self.afkImage=None

		if app.ENABLE_MULTI_FARM_BLOCK:
			self.multiFarmBlockDialog=None
			self.farmStatusImage=None

		if app.ENABLE_CONQUEROR_LEVEL:
			self.sungmaImage = None

		self.affectImageDict={}
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			for groupImage in self.affectGroupImageDict.values():
				groupImage.Destroy()
			self.affectGroupImageDict={}
			self.expandedAffectGroups=set()
		self.__ArrangeImageList()

	def RefreshPenetrationOverflow(self):
		attack = max(0, int(player.GetStatus(PenetrationOverflowImage.POINT_RARITY_OVERFLOW_ATTACK)))
		image = getattr(self, "penetrationOverflowImage", None)
		if not attack:
			if image:
				image.Hide()
				self.penetrationOverflowImage = None
				self.__ArrangeImageList()
			return
		if image is None:
			image = PenetrationOverflowImage()
			image.SetParent(self)
			self.penetrationOverflowImage = image
			image.SetAttack(attack)
			image.Show()
			self.__ArrangeImageList()
		elif image.attack != attack:
			image.SetAttack(attack)

	def SetBiologBonuses(self, bonuses):
		# The Biologist window snapshot; only a fallback while no AFFECT_COLLECT arrived (the affect is the truth).
		if not app.ENABLE_RENEWAL_AFFECT_SHOWER:
			return
		if self.__BiologAffectMembers():
			self.RefreshBiologAffect()
			return
		self.__ShowBiologImage(sorted(bonuses.items()) if bonuses else [], False)

	def __BiologAffectMembers(self):
		data = affectDict.get(BIOLOG_AFFECT, {}) if app.ENABLE_RENEWAL_AFFECT_SHOWER else {}
		return sorted((entry[0], entry[1]) for entry in data.get("entries", []) if entry[0] and entry[1])

	def RefreshBiologAffect(self):
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			self.__ShowBiologImage(self.__BiologAffectMembers(), True)

	def __ShowBiologImage(self, members, byPoint):
		if not members:
			if self.biologImage:
				self.biologImage.Destroy()
				self.biologImage = None
			self.__ArrangeImageList()
			return
		if self.biologImage is None:
			self.biologImage = BiologPassiveImage()
			self.biologImage.SetParent(self)
			self.biologImage.summaryAnchor = ui.__mem_func__(self.__SummaryAnchor)
		if byPoint:
			self.biologImage.SetPointMembers(members)
		else:
			self.biologImage.SetApplyMembers(members)
		self.biologImage.Show()
		self.__ArrangeImageList()

	if app.ENABLE_AUTO_PICKUP:
		def OnAutopickupEnableQuestionDialog(self):
			import uiCommon
			self.autopickupQuestionDlg = uiCommon.QuestionDialog()
			self.autopickupQuestionDlg.SetText(localeInfo.QUESTION_ENABLE_AUTOPICKUP)
			self.autopickupQuestionDlg.SetWidth(350)
			self.autopickupQuestionDlg.SetAcceptEvent(lambda arg = True: self.OnAutopickupEnable(arg))
			self.autopickupQuestionDlg.SetCancelEvent(lambda arg = False: self.OnAutopickupEnable(arg))
			self.autopickupQuestionDlg.Open()

		def OnAutopickupEnable(self, answer):
			if not self.autopickupQuestionDlg:
				return

			self.autopickupQuestionDlg.Close()
			self.autopickupQuestionDlg = None

			if not answer:
				return

			net.SendChatPacket("/autopickup_set 1")
			return True

		def OnAutopickupDisableQuestionDialog(self):
			if player.IsVipActive():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.VIP_AUTOPICKUP_FORCED)
				return

			import uiCommon
			self.autopickupQuestionDlg = uiCommon.QuestionDialog()
			self.autopickupQuestionDlg.SetText(localeInfo.QUESTION_DISABLE_AUTOPICKUP)
			self.autopickupQuestionDlg.SetWidth(350)
			self.autopickupQuestionDlg.SetAcceptEvent(lambda arg = True: self.OnAutopickupDisable(arg))
			self.autopickupQuestionDlg.SetCancelEvent(lambda arg = False: self.OnAutopickupDisable(arg))
			self.autopickupQuestionDlg.Open()

		def OnAutopickupDisable(self, answer):
			if not self.autopickupQuestionDlg:
				return

			self.autopickupQuestionDlg.Close()
			self.autopickupQuestionDlg = None

			if not answer:
				return

			if player.IsVipActive():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.VIP_AUTOPICKUP_FORCED)
				return

			net.SendChatPacket("/autopickup_set 0")
			return True

	def ClearAffects(self):
		livingImages = {}
		for key, image in self.affectImageDict.items():
			if image.IsSkillAffect():
				image.Hide()
			else:
				livingImages[key] = image
		self.affectImageDict = livingImages
		self.__ArrangeImageList()

	def SetVipStatus(self, active, expires_at):
		if chr.AFFECT_PREMIUM in self.affectImageDict:
			del self.affectImageDict[chr.AFFECT_PREMIUM]

		self.__ArrangeImageList()

	def ResolveAffectKey(self, type, pointIdx):
		if type == chr.NEW_AFFECT_MALL:
			return self.MALL_DESC_IDX_START + pointIdx
		if type == chr.NEW_AFFECT_EXP_BONUS_EURO_FREE:
			return self.CONSUMABLE_DESC_IDX_START + pointIdx
		return type

	def DescribeAffect(self, affect, value):
		if affect in self.SUMMARY_ITEMS:
			item.SelectItem(self.SUMMARY_ITEMS[affect])
			return item.GetItemName()
		description = self.AFFECT_DATA_DICT[affect][0]
		return description(float(value)) if callable(description) else description

	def BINARY_NEW_AddAffect(self, type, pointIdx, value, duration):
		if type in (BALANCED_RARITY_AFFECT, SAGE_COMPLETION_AFFECT):
			duration = 0
		#print("BINARY_NEW_AddAffect", type, pointIdx, value, duration)

		affect = self.ResolveAffectKey(type, pointIdx)

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			global affectDict
			affectNew = self.AffectToRealIndex(affect)
			affectData = UpsertAffectTooltipEntry(
				affectDict.get(affectNew, {}),
				pointIdx,
				value,
				duration,
				app.GetGlobalTimeStamp()
			)
			affectDict[affectNew] = affectData
			maxDuration = affectData["duration"]
			if type == BIOLOG_AFFECT:
				self.RefreshBiologAffect()
				return

			if type < 304 and self.CheckRemoveAffect(type) == False and self.CheckBadAffect(type) == False:
				return
		else:
			if type < 304:
				return

		if type < self.SKILL_AFFECT_TYPE_LIMIT:
			return

		if affect in self.affectImageDict:
			dewIcon = dewcatalog.affect_icon(affect, value)
			if dewIcon:
				self.affectImageDict[affect].LoadImage(dewIcon)
				self.affectImageDict[affect].SetScale(0.7, 0.7)
			if affect == BALANCED_RARITY_AFFECT:
				self.affectImageDict[affect].SetDescription(BalancedRarityTitle(value))
			if app.ENABLE_RENEWAL_AFFECT_SHOWER:
				self.affectImageDict[affect].SetEndTime(maxDuration)
				self.affectImageDict[affect].SetDescription(self.DescribeAffect(affect, value))
				self.__ArrangeImageList()
			return

		if affect not in self.AFFECT_DATA_DICT:
			return

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			if type == chr.AFFECT_AUTO_USE:
				import chrmgr
				if not chrmgr.GetAutoOnOff():
					return

		if affect == chr.NEW_AFFECT_NO_DEATH_PENALTY or affect == chr.NEW_AFFECT_SKILL_BOOK_BONUS or affect == chr.NEW_AFFECT_AUTO_SP_RECOVERY or affect == chr.NEW_AFFECT_AUTO_HP_RECOVERY or affect == chr.NEW_AFFECT_SKILL_BOOK_NO_DELAY:
			duration = 0

		affectData = self.AFFECT_DATA_DICT[affect]
		description = affectData[0]
		filename = dewcatalog.affect_icon(affect, value) or affectData[1]

		if pointIdx == player.POINT_MALL_ITEMBONUS or\
			pointIdx == player.POINT_MALL_GOLDBONUS:
			value = float(value) * 100.0 / 100.0 # 1 + float(value) / 100.0

		description = self.DescribeAffect(affect, value)
		if affect in self.SUMMARY_ITEMS:
			item.SelectItem(self.SUMMARY_ITEMS[affect])
			filename = item.GetIconImageFileName()

		image = AffectImage()
		image.SetParent(self)
		image.LoadImage(filename)
		image.SetDescription(description)
		image.SetDuration(duration)
		image.SetAffect(affect)
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			image.SetEndTime(maxDuration)

		if app.ENABLE_AUTO_PICKUP:
			if affect == chr.AFFECT_AUTO_PICKUP_ENABLED:
				image.SetEvent(ui.__mem_func__(self.OnAutopickupDisableQuestionDialog),"mouse_click", affect)
			elif affect == chr.AFFECT_AUTO_PICKUP_DISABLED:
				image.SetEvent(ui.__mem_func__(self.OnAutopickupEnableQuestionDialog),"mouse_click", affect)

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			if self.CheckRemoveAffect(affect):
				image.isCanRemove=True
				image.SetEvent(ui.__mem_func__(self.__OnClickAffect),"mouse_click", affect, description)
		else:
			if affect == chr.NEW_AFFECT_EXP_BONUS_EURO_FREE or affect == chr.NEW_AFFECT_EXP_BONUS_EURO_FREE_UNDER_15 or self.INFINITE_AFFECT_DURATION < duration:
				image.SetClock(False)
				image.UpdateDescription()
			elif affect == chr.NEW_AFFECT_AUTO_SP_RECOVERY or affect == chr.NEW_AFFECT_AUTO_HP_RECOVERY:
				image.UpdateAutoPotionDescription()
			else:
				image.UpdateDescription()

		isDSAffect = (affect == chr.NEW_AFFECT_DRAGON_SOUL_DECK1 or affect == chr.NEW_AFFECT_DRAGON_SOUL_DECK2)
		image.SetScale(1.0 if isDSAffect else 0.7, 1.0 if isDSAffect else 0.7)
		image.Show()
		self.affectImageDict[affect] = image
		self.__ArrangeImageList()
		#except Exception as e:
		#	pass

	def BINARY_NEW_RemoveAffect(self, type, pointIdx):
		affect = self.ResolveAffectKey(type, pointIdx)

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			global affectDict
			affectNew = self.AffectToRealIndex(affect)
			affectData, removed = RemoveAffectTooltipEntry(affectDict.get(affectNew, {}), pointIdx)
			if affectData["entries"]:
				affectDict[affectNew] = affectData
				if type == BIOLOG_AFFECT:
					self.RefreshBiologAffect()
					return
				if type >= self.SKILL_AFFECT_TYPE_LIMIT and affect in self.affectImageDict:
					self.affectImageDict[affect].SetEndTime(affectData["duration"])
					self.__ArrangeImageList()
				return
			else:
				affectDict.pop(affectNew, None)
				if type == BIOLOG_AFFECT:
					self.RefreshBiologAffect()
					return

		if type < self.SKILL_AFFECT_TYPE_LIMIT:
			return

		self.__RemoveAffect(affect)
		self.__ArrangeImageList()

	if app.ENABLE_AUTO_PICKUP:
		def SelectAffect(self, affect):
			if affect == chr.AFFECT_AUTO_PICKUP_ENABLED:
				self.OnAutopickupDisableQuestionDialog()
			elif affect == chr.AFFECT_AUTO_PICKUP_DISABLED:
				self.OnAutopickupEnableQuestionDialog()

	def SetAffect(self, affect):
		self.__AppendAffect(affect)
		self.__ArrangeImageList()

	def ResetAffect(self, affect):
		self.__RemoveAffect(affect)
		self.__ArrangeImageList()

	def SetLoverInfo(self, name, lovePoint):
		image = LovePointImage()
		image.SetParent(self)
		image.SetLoverInfo(name, lovePoint)
		self.lovePointImage = image
		self.__ArrangeImageList()

	def ShowLoverState(self):
		if self.lovePointImage:
			self.lovePointImage.Show()
			self.__ArrangeImageList()

	def SetAfkIndicator(self, visible, description, clickEvent):
		if not visible:
			if self.afkImage:
				self.afkImage.Hide()
			self.afkImage = None
			self.__ArrangeImageList()
			return

		if not self.afkImage:
			image = AffectImage()
			image.SetParent(self)
			image.LoadImage("d:/ymir work/ui/game/affect/afk.png")
			image.SetAffect(self.AFK_AFFECT_KEY)
			image.SetEvent(clickEvent, "mouse_click")
			self.afkImage = image

		self.afkImage.SetDescription(description)
		self.afkImage.Show()
		self.__ArrangeImageList()

	def HideLoverState(self):
		if self.lovePointImage:
			self.lovePointImage.Hide()
			self.__ArrangeImageList()

	def ClearLoverState(self):
		self.lovePointImage = None
		self.__ArrangeImageList()

	def OnUpdateLovePoint(self, lovePoint):
		if self.lovePointImage:
			self.lovePointImage.OnUpdateLovePoint(lovePoint)

	def SetHorseState(self, level, health, battery):
		if level==0:
			self.horseImage=None
		else:
			image = HorseImage()
			image.SetParent(self)
			image.SetState(level, health, battery)
			image.Show()

			self.horseImage=image
		self.__ArrangeImageList()

	def SetPlayTime(self, playTime):
		self.serverPlayTime = playTime
		self.clientPlayTime = app.GetTime()

	if app.ENABLE_CONQUEROR_LEVEL:
		def SetSungMaAffectImage(self, str, hp, move, immune):
			image = SungMaAffectImage(str, hp, move, immune)
			image.SetParent(self)
			image.SetSungmaValue(str, hp, move, immune)
			image.Show()

			self.sungmaImage = image
			self.__ArrangeImageList()

	def __AppendAffect(self, affect):
		if affect in self.affectImageDict:
			return
		try:
			affectData = self.AFFECT_DATA_DICT[affect]
		except KeyError:
			return

		name = affectData[0]
		filename = affectData[1]

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			skillIndex = AffectToSkillIndex(affect)
		else:
			skillIndex = player.AffectIndexToSkillIndex(affect)
		if 0 != skillIndex:
			name = skill.GetSkillName(skillIndex)

		image = AffectImage()
		image.SetParent(self)

		__blockedAffects = [chr.AFFECT_POISON, chr.AFFECT_BLEEDING, chr.AFFECT_SLOW, chr.AFFECT_STUN]
		if not affect in __blockedAffects:
			image.SetSkillAffectFlag(True)
		if affect not in self.CRITICAL_AFFECTS:
			image.skillIconSource = (filename, self.__SkillIconIndex(affect, skillIndex))
			filename = CurrentSkillIcon(*image.skillIconSource)
		try:
			image.LoadImage(filename)
		except:
			pass

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			image.SetAffect(affect)
			image.SetDescription(name)
			if self.CheckRemoveAffect(affect):
				image.isCanRemove=True
				image.SetEvent(ui.__mem_func__(self.__OnClickAffect),"mouse_click", affect, name)

		image.SetScale(0.7, 0.7)
		image.Show()
		self.affectImageDict[affect] = image

	@staticmethod
	def __SkillIconIndex(affect, skillIndex):
		"""The skill behind a skill affect: the native mapping, else the table of the renewal shower."""
		if skillIndex:
			return skillIndex
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			mapped = TypeToAffect(affect)
			if mapped != affect:
				return mapped
		# The wolfman possessions have no native affect -> skill entry (SkillDesc 174 / 175).
		for name, index in (("AFFECT_RED_POSSESSION", 174), ("AFFECT_BLUE_POSSESSION", 175)):
			if affect == getattr(chr, name, None):
				return index
		return 0

	def RefreshSkillIcons(self):
		"""After a skill grade change (game.RefreshSkill): the skill affects follow the skill window's tile."""
		images = list(self.affectImageDict.values()) + list(getattr(self, "pvmPersonalImages", {}).values())
		for image in images:
			source = getattr(image, "skillIconSource", None)
			if not source:
				continue
			path = CurrentSkillIcon(*source)
			if path == image.GetIconPath():
				continue
			try:
				image.LoadImage(path)
			except Exception:
				continue
			image.SetScale(0.7, 0.7)
			if getattr(image, "pvmPersonalSkill", 0):
				image.SetSize(22, 22)
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			uiaffecthover.Invalidate()
			for groupImage in self.affectGroupImageDict.values():
				if groupImage.summary and groupImage.summary.IsShow():
					groupImage.summary.Refresh()

	def __RemoveAffect(self, affect):
		if affect not in self.affectImageDict:
			return
		image = self.affectImageDict.pop(affect)
		image.Hide()
		self.__ArrangeImageList()

	def get_idx(self, j):
		return j[0]

	def __GetAffectGroup(self, affect, affectImage):
		if not app.ENABLE_RENEWAL_AFFECT_SHOWER:
			return None
		if affect in self.CRITICAL_AFFECTS or affect in self.INDEPENDENT_AFFECTS:
			return None
		if getattr(affectImage, "pvmPersonalSkill", 0):
			return "skills"
		if affect in self.SUMMARY_ITEMS or affect in self.DRAGON_GOD_AFFECTS:
			return "gods"
		if affect in self.SHAMAN_BUFF_AFFECTS:
			return "buffs"
		if affect in self.DEW_AFFECTS:
			return "dews"
		if affectImage.IsSkillAffect():
			return "skills"
		return None

	def __GetOrCreateAffectGroupImage(self, groupKey):
		groupImage = self.affectGroupImageDict.get(groupKey)
		if groupImage:
			return groupImage

		unusedRowIndex, iconPath = self.GROUP_DATA[groupKey]
		groupImage = AffectGroupImage(groupKey, iconPath, ui.__mem_func__(self.__CloseAffectSummaries))
		groupImage.SetParent(self)
		groupImage.summaryAnchor = ui.__mem_func__(self.__SummaryAnchor)
		groupImage.SetEvent(
			ui.__mem_func__(self.__ToggleAffectGroup),
			"mouse_click",
			groupKey
		)
		self.affectGroupImageDict[groupKey] = groupImage
		return groupImage

	def __SummaryAnchor(self):
		"""Top and height of the whole bar: a group's summary panel opens under the bar."""
		return self.GetGlobalPosition()[1], self.GetHeight()

	def __CloseAffectSummaries(self, exceptGroup=None):
		for groupKey, image in self.affectGroupImageDict.items():
			if groupKey != exceptGroup:
				image.CloseSummary()

	def __ToggleAffectGroup(self, unusedArg, groupKey):
		self.__CloseAffectSummaries()
		if groupKey in self.expandedAffectGroups:
			self.expandedAffectGroups.remove(groupKey)
		else:
			self.expandedAffectGroups.add(groupKey)
		self.__ArrangeImageList()

	def SetPvmPersonalImages(self, images):
		for image in self.pvmPersonalImages.values():
			image.Hide()
		self.pvmPersonalImages = dict(images)
		self.__ArrangeImageList()

	def __ArrangeImageList(self):
		sortDict = [[] for i in range(10)]
		if getattr(self, "penetrationOverflowImage", None):
			sortDict[0].append([-125, self.penetrationOverflowImage])
		if getattr(self, "biologImage", None):
			sortDict[0].append([-200, self.biologImage])
		groupMembers = {}
		if getattr(self, "skillTreeImage", None) and self.skillTreeImage.IsShow():
			sortDict[0].append([-150, self.skillTreeImage])

		for affectImage in self.affectImageDict.values():
			affectImage.Hide()
		if self.afkImage:
			self.afkImage.Hide()
		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			for groupImage in self.affectGroupImageDict.values():
				groupImage.Hide()

		if app.ENABLE_MULTI_FARM_BLOCK:
			if self.farmStatusImage:
				sortDict[3].append([0,self.farmStatusImage])

		if self.lovePointImage:
			sortDict[0].append([100, self.lovePointImage])
		if self.horseImage:
			sortDict[0].append([1,self.horseImage])
		if self.afkImage:
			self.afkImage.Show()
			sortDict[3].append([-200, self.afkImage])

		for source, image in self.pvmPersonalImages.items():
			image.Hide()
			groupKey = "skills"
			groupMembers.setdefault(groupKey, []).append([source, -source, image])

		for affect, affectImage in self.affectImageDict.items():
			if (app.ENABLE_RENEWAL_AFFECT_SHOWER and self.pvmPersonalImages and affectImage.IsSkillAffect() and
					affect not in self.CRITICAL_AFFECTS and affect not in self.INDEPENDENT_AFFECTS and
					SupportSkillTooltip(affect) in self.pvmPersonalImages):
				continue
			affectData = self.AFFECT_DATA_DICT[affect]
			yIdx = affectData[2] if len(affectData) > 3 else 1
			xIdx = affectData[3] if len(affectData) > 3 else 0
			groupKey = self.__GetAffectGroup(affect, affectImage)
			if groupKey:
				groupMembers.setdefault(groupKey, []).append([xIdx, affect, affectImage])
				continue

			affectImage.Show()
			sortDict[yIdx-1].append([xIdx, affectImage])

		if app.ENABLE_RENEWAL_AFFECT_SHOWER:
			for groupKey, image in self.affectGroupImageDict.items():
				if groupKey not in groupMembers:
					image.SetMembers([])
					image.CloseSummary()
					self.expandedAffectGroups.discard(groupKey)
			for groupKey in self.GROUP_ORDER:
				members = groupMembers.get(groupKey, [])
				if not members:
					continue
				members.sort(key=lambda data: (data[0], data[1]))
				rowIndex, unusedIconPath = self.GROUP_DATA[groupKey]
				isExpanded = groupKey in self.expandedAffectGroups
				isCollapsed = ShouldCollapseAffectGroup(len(members), isExpanded)

				if len(members) >= AFFECT_GROUP_THRESHOLD:
					groupImage = self.__GetOrCreateAffectGroupImage(groupKey)
					groupImage.SetMembers([member[2] for member in members])
					groupImage.Show()
					sortDict[rowIndex - 1].append([-100 + self.GROUP_ORDER.index(groupKey), groupImage])

					if not isCollapsed:
						for xIdx, unusedAffect, affectImage in members:
							affectImage.Show()
							sortDict[rowIndex - 1].append([xIdx, affectImage])
				else:
					self.expandedAffectGroups.discard(groupKey)
					for xIdx, unusedAffect, affectImage in members:
						affectImage.Show()
						sortDict[rowIndex - 1].append([xIdx, affectImage])

		ySize, xSize, xSizeTotal = (0, 0, 0)
		for imageList in SortAffectRowsByLength(sortDict,
				chr.AFFECT_ATT_SPEED_POTION in self.affectImageDict):
			if len(imageList) > 1:
				imageList = sorted(imageList, key= self.get_idx, reverse=False)

			for image in imageList:
				if xSize and xSize + self.IMAGE_STEP > wndMgr.GetScreenWidth() - 20:
					xSizeTotal = max(xSizeTotal, xSize)
					xSize = 0
					ySize += 26
				image[1].SetPosition(xSize, ySize)
				xSize += self.IMAGE_STEP
			if xSize > xSizeTotal:
				xSizeTotal = xSize
			xSize = 0
			ySize += 26
		self.SetSize(xSizeTotal, ySize)

	if app.ENABLE_MULTI_FARM_BLOCK:
		def __OnClickMultiFarm(self, emptyArg):
			multiFarmBlockDialog = uiCommon.QuestionDialog()
			if self.farmStatusImage.multiFarmStatus:
				multiFarmBlockDialog.SetText(localeInfo.MULTI_FARM_DEACTIVE_TEXT)
			else:
				multiFarmBlockDialog.SetText(localeInfo.MULTI_FARM_ACTIVE_TEXT)
			multiFarmBlockDialog.SetAcceptEvent(lambda arg = True: self.OnCloseMultiFarm(arg))
			multiFarmBlockDialog.SetCancelEvent(lambda arg = False: self.OnCloseMultiFarm(arg))
			multiFarmBlockDialog.Open()
			self.multiFarmBlockDialog = multiFarmBlockDialog
		def OnCloseMultiFarm(self, answer):
			if not self.multiFarmBlockDialog:
				return
			if answer:
				net.SendChatPacket("/multi_farm")
			self.multiFarmBlockDialog.Close()
			self.multiFarmBlockDialog = None
		def SetMultiFarmPlayer(self, playerName):
			if self.farmStatusImage:
				self.farmStatusImage.players.append(playerName)
		def SetMultiFarmInfo(self, farmStatus):
			image = MultiFarmImage()
			image.SetParent(self)
			image.SetMultiFarmInfo(farmStatus)
			image.SetEvent(ui.__mem_func__(self.__OnClickMultiFarm),"mouse_click")
			image.Show()
			self.farmStatusImage = image
			self.__ArrangeImageList()

	def CheckBadAffect(self, type):
		if type == 209:
			return True
		if type == 210:
			return True
		if type == 211:
			return True
		return False

	def Hide(self):
		# The bar's OnUpdate stops with it: the controller lets the frame check close a surface (uiaffecthover.Out),
		# so a hidden bar (Ctrl+Q, cutscene) closes its tooltip itself.
		if getattr(self, "hover", None):
			self.hover.Reset()
		ui.Window.Hide(self)

	def OnUpdate(self):
		try:
			if app.ENABLE_RENEWAL_AFFECT_SHOWER:
				self.hover.Update()
			if app.GetGlobalTimeStamp() > self.lastUpdateTime:
				self.lastUpdateTime = app.GetGlobalTimeStamp()
				if app.ENABLE_RENEWAL_AFFECT_SHOWER:
					# Only the remaining time of the shown tooltip; the content is rebuilt when its data changed.
					self.hover.Tick()
				else:
					for image in self.affectImageDict.values():
						if image.GetAffect() == chr.NEW_AFFECT_AUTO_HP_RECOVERY or image.GetAffect() == chr.NEW_AFFECT_AUTO_SP_RECOVERY:
							image.UpdateAutoPotionDescription()
							continue
						if not image.IsSkillAffect():
							image.UpdateDescription()
		except Exception:
			# Once to syserr instead of silently every frame.
			if not getattr(self, "hoverUpdateFailed", False):
				self.hoverUpdateFailed = True
				import dbg, traceback
				dbg.TraceError("AffectShower.OnUpdate failed\n%s" % traceback.format_exc())
			return

	if app.ENABLE_RENEWAL_AFFECT_SHOWER:
		def AffectToRealIndex(self, affect):
			_dict = {
				209:("actor", chr.AFFECT_POISON),
				211:("actor", chr.AFFECT_SLOW),
				210:("actor", chr.AFFECT_STUN),
				201:chr.AFFECT_ATT_SPEED_POTION,
				200:chr.AFFECT_MOV_SPEED_POTION,
				208:chr.AFFECT_FISH_MIND,
			}
			return _dict[affect] if affect in _dict else affect
		def __OnClickAffect(self, arg, affect, name):
			self.removeAffectDialog = uiCommon.QuestionDialog()
			self.removeAffectDialog.SetText(localeInfo.AFFECT_REMOVE_QUESTION % name)
			self.removeAffectDialog.SetAcceptEvent(lambda arg = True: self.OnCloseRemoveAffect(arg))
			self.removeAffectDialog.SetCancelEvent(lambda arg = False: self.OnCloseRemoveAffect(arg))
			self.removeAffectDialog.affect = affect
			self.removeAffectDialog.Open()
		def OnCloseRemoveAffect(self, answer):
			if not self.removeAffectDialog:
				return
			if answer:
				net.SendChatPacket("/remove_affect %d"%SupportSkillTooltip(self.removeAffectDialog.affect))
			self.removeAffectDialog.Close()
			self.removeAffectDialog = None
		def CheckRemoveAffect(self, type):
			if type in (BALANCED_RARITY_AFFECT, SAGE_COMPLETION_AFFECT):
				return False
			if type == chr.AFFECT_PABEOP:
				return False
			if type == chr.NEW_AFFECT_POLYMORPH:
				return True
			elif type >= 400 and type <= 405:
				return True
			return True if TypeToAffect(type) != type else False

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def SetPetSkillAffect(self, index, affect):
			# Pet skills remain in the pet window, never in the top affect row.
			return

		def ClearPetSkillAffect(self):
			for index, image in self.petSkillaffectImageDict.values():
				image.Hide()
			self.petSkillaffectImageDict.clear()
			self.__ArrangeImageList()
