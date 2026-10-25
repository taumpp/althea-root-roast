import app
import ui
import grp
import player
import uiToolTip
import net
import localeInfo
import uiScriptLocale
import constInfo
import osfInfo
import mouseModule
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

if app.ENABLE_POISON_GAUGE_EFFECT:
	import chr
	import chrmgr

def _DressR1(function, window):
	# The R1 look of a party row / the party menu / the menu button (uipartyr1); None = the original look (also when it
	# cannot load).
	try:
		import uipartyr1
		return getattr(uipartyr1, function)(window)
	except:
		return None

class PartyMemberInfoBoard(ui.ScriptWindow):
	if localeInfo.IsJAPAN():
		BOARD_WIDTH = 130
	else:
		BOARD_WIDTH = 106
	BOARD_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.5)
	GAUGE_OUT_LINE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 0.3)

	LINK_COLOR = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
	UNLINK_COLOR = grp.GenerateColor(0.5, 0.5, 0.5, 1.0)
	#UNLINK_COLOR = grp.GenerateColor(0.9, 0.4745, 0.4627, 1.0)

	if app.WJ_SHOW_PARTY_ON_MINIMAP:
		class TextToolTip(ui.Window):
			def __init__(self):
				ui.Window.__init__(self, "TOP_MOST")

				textLine = ui.TextLine()
				textLine.SetParent(self)
				if localeInfo.IsARABIC():
					textLine.SetHorizontalAlignRight()
				else:
					textLine.SetHorizontalAlignLeft()
				textLine.SetOutline()
				textLine.Show()
				self.textLine = textLine

			def __del__(self):
				ui.Window.__del__(self)
				self.textLine = None

			def SetText(self, text, x, y):
				self.textLine.SetText(text)
				self.textLine.SetPosition(x, y)
				self.r1Rect = (x - 5, y, 1, 14)		# R1: the hint right of the member board, where the text began

			def Show(self):
				try:
					import uir1
					if uir1.TextTooltipShow(self, self.textLine.GetText(), getattr(self, "r1Rect", None), "right"):
						return
				except Exception:
					pass
				ui.Window.Show(self)

			def Hide(self):
				try:
					import uir1
					uir1.HideHint(self)
				except Exception:
					pass
				ui.Window.Hide(self)

	def __init__(self):
		self.PARTY_AFFECT_EXPERIENCE = 0
		self.PARTY_AFFECT_ATTACKER = 1
		self.PARTY_AFFECT_TANKER = 2
		self.PARTY_AFFECT_BUFFER = 3
		self.PARTY_AFFECT_SKILL_MASTER = 4
		self.PARTY_AFFECT_BERSERKER = 5
		self.PARTY_AFFECT_DEFENDER = 6
		#self.PARTY_AFFECT_TIME_BONUS = 5
		#self.PARTY_AFFECT_REGEN_BONUS = 6
		self.PARTY_AFFECT_INCREASE_AREA_150 = 7
		self.PARTY_AFFECT_INCREASE_AREA_200 = 8
		self.AFFECT_STRING_DICT = {
			self.PARTY_AFFECT_EXPERIENCE : localeInfo.PARTY_BONUS_EXP,
			self.PARTY_AFFECT_ATTACKER : localeInfo.PARTY_BONUS_ATTACKER,
			self.PARTY_AFFECT_TANKER : localeInfo.PARTY_BONUS_TANKER,
			self.PARTY_AFFECT_BUFFER : localeInfo.PARTY_BONUS_BUFFER,
			self.PARTY_AFFECT_SKILL_MASTER : localeInfo.PARTY_BONUS_SKILL_MASTER,
			self.PARTY_AFFECT_BERSERKER : localeInfo.PARTY_BONUS_BERSERKER,
			self.PARTY_AFFECT_DEFENDER : localeInfo.PARTY_BONUS_DEFENDER,
			self.PARTY_AFFECT_INCREASE_AREA_150 : localeInfo.PARTY_INCREASE_AREA_150,
			self.PARTY_AFFECT_INCREASE_AREA_200 : localeInfo.PARTY_INCREASE_AREA_200,
		}

		self.PARTY_SKILL_WARP = 2
		self.MEMBER_BUTTON_NORMAL = 10
		self.MEMBER_BUTTON_WARP = 11
		self.MEMBER_BUTTON_EXPEL = 12
		self.MEMBER_BUTTON_PATH = "d:/ymir work/ui/game/windows/"
		self.MEMBER_BUTTON_IMAGE_FILE_NAME_DICT = {
			player.PARTY_STATE_LEADER : "party_state_leader",
			player.PARTY_STATE_ATTACKER : "party_state_attacker",
			player.PARTY_STATE_BERSERKER : "party_state_berserker",
			player.PARTY_STATE_TANKER : "party_state_tanker",
			player.PARTY_STATE_DEFENDER : "party_state_defender",
			player.PARTY_STATE_BUFFER : "party_state_buffer",
			player.PARTY_STATE_SKILL_MASTER : "party_state_skill_master",
			self.MEMBER_BUTTON_NORMAL : "party_state_normal",
			self.MEMBER_BUTTON_WARP : "party_skill_warp",
			self.MEMBER_BUTTON_EXPEL : "party_expel",
		}

		ui.ScriptWindow.__init__(self)

		self.pid = None
		self.vid = None
		self.isOnline = None
		self.partyAffectImageList = []
		self.stateButtonDict = {}
		self.affectValueDict = {}
		self.state = -1
		self.isShowStateButton = False

		self.__LoadBoard()
		self.__CreateAffectToolTip()

		if app.WJ_SHOW_PARTY_ON_MINIMAP:
			self.tooltipMapName = self.TextToolTip()
			self.tooltipMapName.Hide()

		self.__CreateStateButton()
		self.Show()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

		print(" =============================== DESTROIED PartyMemberInfoBoard")

	def __LoadBoard(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			if localeInfo.IsJAPAN():
				pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "PartyMemberInfoBoard.py")
			else:
				pyScrLoader.LoadScriptFile(self, "UIScript/PartyMemberInfoBoard.py")
		except:
			import exception
			exception.Abort("PartyMemberInfoBoard.__LoadBoard.LoadScript")

		try:
			self.nameTextLine = self.GetChild("NamePrint")
			self.gauge = self.GetChild("Gauge")
			self.stateButton = self.GetChild("StateButton")
			self.partyAffectImageList.append(self.GetChild("ExperienceImage"))
			self.partyAffectImageList.append(self.GetChild("AttackerImage"))
			self.partyAffectImageList.append(self.GetChild("DefenderImage"))
			self.partyAffectImageList.append(self.GetChild("BufferImage"))
			self.partyAffectImageList.append(self.GetChild("SkillMasterImage"))
			self.partyAffectImageList.append(self.GetChild("TimeBonusImage"))
			self.partyAffectImageList.append(self.GetChild("RegenBonus"))
			self.partyAffectImageList.append(self.GetChild("IncreaseArea150"))
			self.partyAffectImageList.append(self.GetChild("IncreaseArea200"))
			self.stateButton.SetEvent(ui.__mem_func__(self.OnMouseLeftButtonDown))

			if app.WJ_SHOW_PARTY_ON_MINIMAP:
				self.gauge.GaugeImgBoxAddFlag("not_pick")

		except:
			import exception
			exception.Abort("PartyMemberInfoBoard.__LoadBoard.BindObject")

		self.__SetAffectsMouseEvent()
		self.__HideAllAffects()
		# R1 look (uipartyr1): the name plate and the R1 HP bar; None = the original look.
		self.r1 = _DressR1("DressMember", self)

	def Destroy(self):
		self.ClearDictionary()
		self.nameTextLine = None
		self.gauge = None
		self.stateButton = None
		self.partyAffectImageList = []
		self.stateButtonDict = {}

		self.affectValueDict = {}
		self.affectToolTip = None

		self.leaderButton = None
		self.attackerButton = None
		self.tankerButton = None

		if app.WJ_SHOW_PARTY_ON_MINIMAP:
			self.tooltipMapName = None

		self.Hide()

	def __SetAffectsMouseEvent(self):
		for i in range(len(self.partyAffectImageList)):
			self.partyAffectImageList[i].OnMouseOverIn = lambda selfArg = self, index = i : ui.__mem_func__(selfArg.OnAffectOverIn)(index)
		for i in range(len(self.partyAffectImageList)):
			self.partyAffectImageList[i].OnMouseOverOut = lambda selfArg = self, index = i : ui.__mem_func__(selfArg.OnAffectOverOut)(index)

	def __HideAllAffects(self):
		for img in self.partyAffectImageList:
			img.Hide()

	def __CreateAffectToolTip(self):
		affectToolTip = uiToolTip.ToolTip(220)
		affectToolTip.Hide()
		self.affectToolTip = affectToolTip

	def __CreateStateButton(self):
		name = self.MEMBER_BUTTON_IMAGE_FILE_NAME_DICT[self.MEMBER_BUTTON_EXPEL]
		button = ui.Button()
		button.SetUpVisual(self.MEMBER_BUTTON_PATH + name + "_01.sub")
		button.SetOverVisual(self.MEMBER_BUTTON_PATH + name + "_02.sub")
		button.SetDownVisual(self.MEMBER_BUTTON_PATH + name + "_03.sub")
		button.SetToolTipText(localeInfo.TARGET_BUTTON_EXCLUDE)
		button.SetEvent(ui.__mem_func__(self.OnExpel))
		button.Hide()
		self.stateButtonDict[self.MEMBER_BUTTON_EXPEL] = button

	def __ShowStateButton(self):
		self.isShowStateButton = True

		(x, y) = self.GetGlobalPosition()
		xPos = x + 110

		if self.MEMBER_BUTTON_EXPEL in self.stateButtonDict:
			button = self.stateButtonDict[self.MEMBER_BUTTON_EXPEL]
			button.SetPosition(xPos, y)
			button.Show()

	def __HideStateButton(self):
		self.isShowStateButton = False
		for button in self.stateButtonDict.values():
			button.Hide()

	def __GetAffectNumber(self, img):
		for i in range(self.partyAffectImageList):
			if img == self.partyAffectImageList[i]:
				return i

		return -1

	def SetCharacterName(self, name):
		self.nameTextLine.SetText(name)

	def GetCharacterName(self):
		return self.nameTextLine.GetText()

	def SetCharacterPID(self, pid):
		self.pid = pid

	def SetCharacterVID(self, vid):
		self.vid = vid

	def GetCharacterPID(self):
		return self.pid

	def GetCharacterVID(self):
		return self.vid

	def SetCharacterHP(self, hpPercentage):
		if app.ENABLE_POISON_GAUGE_EFFECT:
			vid = self.GetCharacterVID()
			if vid is not None and vid > 0 and chrmgr.HasAffectByVID(vid, chr.AFFECT_POISON):
				self.gauge.SetGaugeColor("lime")
			else:
				self.gauge.SetGaugeColor("red")
		try:
			hpPercentage = max(0, int(hpPercentage))
			self.gauge.SetPercentage(hpPercentage, 100)
		except TypeError:
			pass


	def SetCharacterState(self, state):
		if self.state == state:
			return

		self.state = state
		self.stateButton.Show()

		name = self.MEMBER_BUTTON_IMAGE_FILE_NAME_DICT[self.MEMBER_BUTTON_NORMAL]
		if state in self.MEMBER_BUTTON_IMAGE_FILE_NAME_DICT:
			name = self.MEMBER_BUTTON_IMAGE_FILE_NAME_DICT[state]

		self.stateButton.SetUpVisual(self.MEMBER_BUTTON_PATH + name + "_01.sub")
		self.stateButton.SetOverVisual(self.MEMBER_BUTTON_PATH + name + "_02.sub")
		self.stateButton.SetDownVisual(self.MEMBER_BUTTON_PATH + name + "_03.sub")

	def SetAffect(self, affectSlotIndex, affectValue):
		if affectSlotIndex >= len(self.partyAffectImageList):
			return

		if affectValue > 0:
			self.partyAffectImageList[affectSlotIndex].Show()
		else:
			self.partyAffectImageList[affectSlotIndex].Hide()

		self.affectValueDict[affectSlotIndex] = affectValue

	def SetOnline(self, online):
		# Roster presence survives losing the local actor during a map/core change.
		self.isOnline = bool(online)
		color = self.LINK_COLOR if self.isOnline else self.UNLINK_COLOR
		self.nameTextLine.SetPackedFontColor(color)

	def Link(self):
		self.nameTextLine.SetPackedFontColor(self.LINK_COLOR)
		self.gauge.Show()

	def Unlink(self):
		self.vid = None
		color = self.LINK_COLOR if self.isOnline else self.UNLINK_COLOR
		self.nameTextLine.SetPackedFontColor(color)
		self.gauge.Hide()
		self.__HideAllAffects()

	def OnWarp(self):
		self.__HideStateButton()

		if self.vid:
			net.SendPartyUseSkillPacket(self.PARTY_SKILL_WARP, self.vid)

	def OnExpel(self):
		self.__HideStateButton()

		if not self.pid:
			return

		net.SendPartyRemovePacket(self.pid)

	def OnMouseLeftButtonDown(self):
		if self.vid:
			player.SetTarget(self.vid)
			player.OpenCharacterMenu(self.vid)

			if mouseModule.mouseController.isAttached():
				attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
				net.SendExchangeStartPacket(self.vid)
				net.SendExchangeItemAddPacket(attachedSlotPos, 0)
				mouseModule.mouseController.DeattachObject()
				return

		if player.IsPartyLeader(player.GetMainCharacterIndex()):
			if player.PARTY_STATE_LEADER != self.state:
				if self.isShowStateButton:
					self.__HideStateButton()
				else:
					self.__ShowStateButton()

	def OnMouseLeftButtonUp(self):
		if self.vid:
			player.SetTarget(self.vid)
			player.OpenCharacterMenu(self.vid)

			if mouseModule.mouseController.isAttached():
				attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
				net.SendExchangeStartPacket(self.vid)
				net.SendExchangeItemAddPacket(attachedSlotPos, 0)
				mouseModule.mouseController.DeattachObject()

	def OnMouseRightButtonDown(self):
		self.OnMouseLeftButtonDown()

	def OnAffectOverIn(self, index):
		if index not in self.AFFECT_STRING_DICT:
			return

		if index not in self.affectValueDict:
			return

		text = self.AFFECT_STRING_DICT[index](self.affectValueDict[index])
		import uir1
		if uir1.UseR1():
			# R1 look: the one R1 hint above the party bonus icon, as every one-line hint.
			uir1.ShowHint(None, self.partyAffectImageList[index], text)
			return

		(x, y) = self.GetGlobalPosition()

		self.affectToolTip.ClearToolTip()
		self.affectToolTip.SetTitle(text)
		self.affectToolTip.SetToolTipPosition(x + index*12, y + 11)
		self.affectToolTip.ShowToolTip()

	def OnAffectOverOut(self, index):
		import uir1
		uir1.HideHint(self.partyAffectImageList[index])
		self.affectToolTip.HideToolTip()

	if app.WJ_SHOW_PARTY_ON_MINIMAP:
		def SetCurrentMapName(self, MapName):
			(x, y) = self.GetGlobalPosition()
			self.tooltipMapName.SetText(MapName, x + 110, y + 2)

		def OnMouseOverIn(self):
			self.tooltipMapName.Show()

		def OnMouseOverOut(self):
			self.tooltipMapName.Hide()

class PartyMenu(ui.ThinBoard):

	BUTTON_NAME = ( localeInfo.PARTY_BREAK_UP, localeInfo.PARTY_LEAVE )

	def __init__(self):
		ui.ThinBoard.__init__(self)
		self.buttonDict = {}
		self.distributionMode = 0
		self.isLeader = False
		self.showingButtonList = []
		self.modeButtonList = {}
		self.__CreateButtons()
		self.__CreateModeButtons()
		# R1 look (uipartyr1): the R1 frame and plates; None = the original look.
		self.r1 = _DressR1("DressMenu", self)

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def SetSize(self, width, height):
		ui.ThinBoard.SetSize(self, width, height)
		r1 = getattr(self, "r1", None)
		if r1:
			r1.Resize(width, height)

	def Destroy(self):
		self.buttonDict = {}
		self.showingButtonList = []
		self.modeButtonList = {}

	def __CreateModeButtons(self):
		self.modeTitle = ui.MakeTextLine(self)
		self.modeTitle.SetText(localeInfo.PARTY_EXP_DISTRIBUTION_MODE)

		self.modeButtonList = {}

		level = ui.RadioButton()
		level.SetParent(self)
		level.SetWindowHorizontalAlignCenter()
		level.SetEvent(ui.__mem_func__(self.OnClickEXPLevel))
		level.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		level.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		level.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		level.SetText(localeInfo.PARTY_EXP_DISTRIBUTION_MODE_LEVEL)
		level.SetToolTipText(localeInfo.PARTY_EXP_DISTRIBUTION_MODE_LEVEL_TOOLTIP, 70)
		level.Show()
		self.modeButtonList[player.PARTY_EXP_NON_DISTRIBUTION] = level

		parity = ui.RadioButton()
		parity.SetParent(self)
		parity.SetWindowHorizontalAlignCenter()
		parity.SetEvent(ui.__mem_func__(self.OnClickEXPDistributeParity))
		parity.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		parity.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		parity.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		parity.SetText(localeInfo.PARTY_EXP_DISTRIBUTION_MODE_PARITY)
		parity.SetToolTipText(localeInfo.PARTY_EXP_DISTRIBUTION_MODE_PARITY_TOOLTIP, 70)
		parity.Show()
		self.modeButtonList[player.PARTY_EXP_DISTRIBUTION_PARITY] = parity

		self.ChangePartyParameter(self.distributionMode)

	def __CreateButtons(self):
		for name in self.BUTTON_NAME:
			button = ui.Button()
			button.SetParent(self)
			button.SetWindowHorizontalAlignCenter()
			button.SetToolTipText(name)
			self.buttonDict[name] = button

		self.buttonDict[localeInfo.PARTY_BREAK_UP].SetEvent(net.SendPartyExitPacket)
		self.buttonDict[localeInfo.PARTY_BREAK_UP].SetUpVisual("d:/ymir work/ui/game/windows/Party_Disband_01.sub")
		self.buttonDict[localeInfo.PARTY_BREAK_UP].SetOverVisual("d:/ymir work/ui/game/windows/Party_Disband_02.sub")
		self.buttonDict[localeInfo.PARTY_BREAK_UP].SetDownVisual("d:/ymir work/ui/game/windows/Party_Disband_03.sub")

		self.buttonDict[localeInfo.PARTY_LEAVE].SetEvent(net.SendPartyExitPacket)
		self.buttonDict[localeInfo.PARTY_LEAVE].SetUpVisual("d:/ymir work/ui/game/windows/Party_Exit_01.sub")
		self.buttonDict[localeInfo.PARTY_LEAVE].SetOverVisual("d:/ymir work/ui/game/windows/Party_Exit_02.sub")
		self.buttonDict[localeInfo.PARTY_LEAVE].SetDownVisual("d:/ymir work/ui/game/windows/Party_Exit_03.sub")

	def __ClearShowingButtons(self):
		self.showingButtonList = []

	def __ArrangeButtons(self):
		STEP_SIZE = 37

		showingButtonCount = len(self.showingButtonList)
		xPos = (showingButtonCount-1) * (-STEP_SIZE//2)
		for button in self.showingButtonList:
			button.SetPosition(xPos, 15)
			button.Show()
			xPos += 37

		yPos = 85
		for button in self.modeButtonList.values():
			button.SetPosition(0, yPos)
			yPos += 25

		self.UpdateRect()

	def __ShowButton(self, name):
		if name not in self.buttonDict:
			return

		self.showingButtonList.append(self.buttonDict[name])
		self.__ArrangeButtons()

	def __HideButton(self, name):
		if name not in self.buttonDict:
			return

		searchingButton = self.buttonDict[name]
		searchingButton.Hide()
		for btn in self.showingButtonList:
			if btn == searchingButton:
				self.showingButtonList.remove(btn)

		self.__ArrangeButtons()

	def ShowLeaderButton(self):
		self.isLeader = True
		self.__ClearShowingButtons()
		self.__ShowButton(localeInfo.PARTY_BREAK_UP)

	def ShowMemberButton(self):
		self.isLeader = False
		self.__ClearShowingButtons()
		self.__ShowButton(localeInfo.PARTY_LEAVE)

	def PartyHealReady(self):
		pass

	def __UpAllModeButtons(self):
		for button in self.modeButtonList.values():
			button.SetUp()

	def __SetModeButton(self, mode):
		self.__UpAllModeButtons()
		self.modeButtonList[mode].Down()
		self.distributionMode = mode

	def OnClickEXPLevel(self):
		self.__SetModeButton(self.distributionMode)
		if self.isLeader:
			net.SendPartyParameterPacket(player.PARTY_EXP_NON_DISTRIBUTION)

	def OnClickEXPDistributeParity(self):
		self.__SetModeButton(self.distributionMode)
		if self.isLeader:
			net.SendPartyParameterPacket(player.PARTY_EXP_DISTRIBUTION_PARITY)

	def ChangePartyParameter(self, distributionMode):
		try:
			self.__SetModeButton(distributionMode)
		except:
			pass

class PartyWindow(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)

		# if app.ENABLE_EXP_EVENT:
		if True:
			self.SetPosition(10, 62+50)
		else:
			self.SetPosition(10, 52+50)

		self.partyMemberInfoBoardList = []

		self.__CreatePartyMenuButton()
		self.__CreatePartyMenu()
		# R1 look (uipartyr1): the R1 plate and chevron of the menu button; None = the original look.
		self.r1Opener = _DressR1("DressOpener", self)

	def __del__(self):
		ui.Window.__del__(self)

		print(" =============================== DESTROIED PartyWindow")

	def Destroy(self):
		self.DestroyPartyMemberInfoBoard()
		self.r1Opener = None
		self.partyMenuButton = None

		if self.partyMenu:
			self.partyMenu.Destroy()
			self.partyMenu = None

	def DestroyPartyMemberInfoBoard(self):
		for board in self.partyMemberInfoBoardList:
			board.Destroy()

		self.partyMemberInfoBoardList = []

	def __CreatePartyMenuButton(self):
		partyMenuButton = ui.Button()
		partyMenuButton.SetParent(self)
		partyMenuButton.SetWindowHorizontalAlignCenter()
		partyMenuButton.SetWindowVerticalAlignBottom()
		partyMenuButton.SetPosition(0, 20)
		partyMenuButton.SetUpVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_01.sub")
		partyMenuButton.SetOverVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_02.sub")
		partyMenuButton.SetDownVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_03.sub")
		partyMenuButton.SetEvent(ui.__mem_func__(self.OnTogglePartyMenu))
		partyMenuButton.Hide()
		self.partyMenuButton = partyMenuButton

	def __CreatePartyMenu(self):
		partyMenu = PartyMenu()
		partyMenu.SetSize(106, 70 + 70)
		partyMenu.Hide()
		self.partyMenu = partyMenu

	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def AddPartyMember(self, pid, name, mapIdx, channel):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				board = PartyMemberInfoBoard()
				board.SetParent(self)
				board.SetCharacterPID(pid)

				self.partyMemberInfoBoardList.append(board)
				self.__ArrangePartyMemberInfoBoard()
				self.UpdateRect()

			if not name:
				name = localeInfo.PARTY_MEMBER_OFFLINE

			view_channel = channel
			if 99 == channel or mapIdx > 10000:
				view_channel = 0

			if mapIdx > 10000:
				mapIdx = mapIdx // 10000;

			board.SetCharacterName(name)
			if mapIdx == 0:
				MapName = localeInfo.PARTY_MEMBER_OFFLINE
				board.SetCurrentMapName(MapName)
			elif mapIdx in localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX:
				MapName = localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX[mapIdx]
				board.SetCurrentMapName("CH-" + str(view_channel) + " " + MapName)
			else:
				board.SetCurrentMapName(str(mapIdx))

			board.SetOnline(channel != 0)
			if channel == 0 or not board.GetCharacterVID():
				board.Unlink()

			self.Show()
			self.partyMenuButton.Show()
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def AddPartyMember(self, pid, name, mapIdx):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				board = PartyMemberInfoBoard()
				board.SetParent(self)
				board.SetCharacterPID(pid)

				self.partyMemberInfoBoardList.append(board)
				self.__ArrangePartyMemberInfoBoard()
				self.UpdateRect()

			if not name:
				name = localeInfo.PARTY_MEMBER_OFFLINE

			if mapIdx > 10000:
				mapIdx = mapIdx // 10000;

			board.SetCharacterName(name)
			if mapIdx == 0:
				MapName = localeInfo.PARTY_MEMBER_OFFLINE
				board.SetCurrentMapName(MapName)
			elif mapIdx in localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX:
				MapName = localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX[mapIdx]
				board.SetCurrentMapName(MapName)
			else:
				board.SetCurrentMapName(str(mapIdx))

			board.SetOnline(mapIdx != 0)
			if mapIdx == 0 or not board.GetCharacterVID():
				board.Unlink()

			self.Show()
			self.partyMenuButton.Show()
	else:
		def AddPartyMember(self, pid, name):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				board = PartyMemberInfoBoard()
				board.SetParent(self)
				board.SetCharacterPID(pid)

				self.partyMemberInfoBoardList.append(board)
				self.__ArrangePartyMemberInfoBoard()
				self.UpdateRect()

			if not name:
				name = localeInfo.PARTY_MEMBER_OFFLINE

			board.SetCharacterName(name)

			board.Unlink()

			self.Show()
			self.partyMenuButton.Show()

	def RemovePartyMember(self, pid):
		board = self.__FindPartyMemberInfoBoardByPID(pid)

		if None == board:
			return

		vid = board.GetCharacterVID()

		if None != vid and player.IsMainCharacterIndex(vid):
			self.ExitParty()
			player.ExitParty()
		else:
			board.Destroy()
			player.RemovePartyMember(pid)
			self.partyMemberInfoBoardList.remove(board)
			self.__ArrangePartyMemberInfoBoard()
			self.UpdateRect()

	def UpdatePartyMemberInfo(self, pid):
		board = self.__FindPartyMemberInfoBoardByPID(pid)

		if None == board:
			return

		state = player.GetPartyMemberState(pid)
		hpPercentage = player.GetPartyMemberHPPercentage(pid)
		affectsList = player.GetPartyMemberAffects(pid)

		board.SetCharacterState(state)
		board.SetCharacterHP(hpPercentage)
		for i in range(len(affectsList)):
			board.SetAffect(i, affectsList[i])

		vid = board.GetCharacterVID()
		if None != vid:
			if player.IsMainCharacterIndex(vid):
				if player.PARTY_STATE_LEADER == player.GetPartyMemberState(pid):
					self.partyMenu.ShowLeaderButton()
				else:
					self.partyMenu.ShowMemberButton()

	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def LinkPartyMember(self, pid, vid, mapIdx, channel):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				return

			board.SetOnline(channel != 0)

			if 99 == channel or mapIdx > 10000:
				channel = 0

			if mapIdx > 10000:
				mapIdx = mapIdx // 10000

			board.Link()
			board.SetCharacterVID(vid)

			if mapIdx == 0:
				MapName = localeInfo.PARTY_MEMBER_OFFLINE
				board.SetCurrentMapName(MapName)
			elif mapIdx in localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX:
				MapName = localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX[mapIdx]
				board.SetCurrentMapName("CH-" + str(channel) + " " + MapName)
			else:
				board.SetCurrentMapName(str(mapIdx))
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def LinkPartyMember(self, pid, vid, mapIdx):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				return

			board.SetOnline(mapIdx != 0)

			if mapIdx > 10000:
				mapIdx = mapIdx // 10000

			board.Link()
			board.SetCharacterVID(vid)

			if mapIdx == 0:
				MapName = localeInfo.PARTY_MEMBER_OFFLINE
				board.SetCurrentMapName(MapName)
			elif mapIdx in localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX:
				MapName = localeInfo.MINIMAP_ZONE_NAME_DICT_BY_IDX[mapIdx]
				board.SetCurrentMapName(MapName)
			else:
				board.SetCurrentMapName(str(mapIdx))
	else:
		def LinkPartyMember(self, pid, vid):
			board = self.__FindPartyMemberInfoBoardByPID(pid)

			if None == board:
				return

			board.Link()
			board.SetCharacterVID(vid)

	def UnlinkPartyMember(self, pid):
		board = self.__FindPartyMemberInfoBoardByPID(pid)

		if None == board:
			return

		board.Unlink()

	def UnlinkAllPartyMember(self):
		for board in self.partyMemberInfoBoardList:
			board.Unlink()

	def ExitParty(self):
		self.partyMenu.Hide()
		self.DestroyPartyMemberInfoBoard()
		self.Hide()
		self.partyMenuButton.Hide()

	def __ArrangePartyMemberInfoBoard(self):
		count = 0
		newHeight = 20

		for board in self.partyMemberInfoBoardList:
			board.SetPosition(0, count * (board.GetHeight() + 2))
			count += 1
			newHeight += board.GetHeight() + 2

		self.SetSize(PartyMemberInfoBoard.BOARD_WIDTH, newHeight)

		(x, y) = self.GetGlobalPosition()
		self.partyMenu.SetPosition(10, y + newHeight + 2)

	def __FindPartyMemberInfoBoardByVID(self, vid):
		for board in self.partyMemberInfoBoardList:
			if vid == board.GetCharacterVID():
				return board

		return None

	def __FindPartyMemberInfoBoardByPID(self, pid):
		for board in self.partyMemberInfoBoardList:
			if pid == board.GetCharacterPID():
				return board

		return None

	def PartyHealReady(self):
		self.partyMenu.PartyHealReady()

	def ChangePartyParameter(self, distributionMode):
		self.partyMenu.ChangePartyParameter(distributionMode)

	def OnTogglePartyMenu(self):
		if self.partyMenu.IsShow():
			self.partyMenuButton.SetUpVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_01.sub")
			self.partyMenuButton.SetOverVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_02.sub")
			self.partyMenuButton.SetDownVisual("d:/ymir work/ui/game/windows/Party_Menu_Open_03.sub")
			self.partyMenu.Hide()
		else:
			self.partyMenuButton.SetUpVisual("d:/ymir work/ui/game/windows/Party_Menu_Close_01.sub")
			self.partyMenuButton.SetOverVisual("d:/ymir work/ui/game/windows/Party_Menu_Close_02.sub")
			self.partyMenuButton.SetDownVisual("d:/ymir work/ui/game/windows/Party_Menu_Close_03.sub")
			self.partyMenu.Show()
