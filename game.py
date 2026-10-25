import os
import app
import dbg
import grp
import item
import itembonuspresentation
import characterbonuses
import bonussources
import resonanceuihelpers
import background
import miniMap
import chr
import chrmgr
import player
import servergamedata
import dungeonequipmentbinding
import snd
import chat
from switchbotoptions import options as switchbotOptions, instantOptions, memory as switchbotMemory
from bonuscatalog import receiver as bonusCatalog
import featureavailability
import npcsellprice
import attrchangecount
import growthpetpresentation
import duelchallenge
import meteorpresentation
import dropsort
import textTail
import snd
import net
import globalhub
import effect
import wndMgr
#import fly
import systemSetting
import quest
import guild
import skill
import messenger
import localeInfo
import constInfo
import osfInfo
import exchange
import ime
import event

import ui
import uiScriptLocale
import uiCommon
import uiPhaseCurtain
import uiMapNameShower
import maparrivalnames
import uiAffectShower
import uiPvMPersonal
import uiPlayerGauge
import uiCharacter
import uiTarget

# PRIVATE_SHOP_PRICE_LIST
import uiPrivateShopBuilder
# END_OF_PRIVATE_SHOP_PRICE_LIST

import mouseModule
import slotwindowpolicy
import consoleModule
import localeInfo

import playerSettingModule
import interfaceModule
import skilltreeruntime
import dungeonobjectivemodel
import inputguardapi
import petalbumstate
import keybindings
import uiwarpstate
import uidungeonrejoin
import uiguildportallobby
import uiunstuck

import musicInfo
import debugInfo
import stringCommander

if app.ENABLE_SKILL_SELECT_GUI:
	import uiselectskill

if app.ENABLE_ITEMSHOP:
	import uiItemShop

if app.ENABLE_ACCE_COSTUME_SYSTEM:
	import acce
	import uiresonance

if app.ENABLE_OFFLINE_SHOP:
	import uiOfflineShop

if app.ENABLE_WINDOW_RESIZE:
	from resizeexpr import Expr

if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
	import uiAutoHuntingSystem

if app.ENABLE_DROP_INFO_WINDOW:
	import uiDropInfo

# Show consumed dungeon tickets in the R1 notice.
import ticketnoticemodel
import uiticketnotice

from _weakref import proxy

# TEXTTAIL_LIVINGTIME_CONTROL
#if localeInfo.IsJAPAN():
#	app.SetTextTailLivingTime(8.0)
# END_OF_TEXTTAIL_LIVINGTIME_CONTROL

cameraDistance = 1550.0
cameraPitch = 27.0
cameraRotation = 0.0
cameraHeight = 100.0

testAlignment = 0

class GameWindow(ui.ScriptWindow):
	# Wall-clock length of the arrival reveal once the main actor exists. The
	# former 0.03 alpha per frame took ~0.55 s at 60 FPS and longer when slow.
	INITIAL_WORLD_REVEAL_SECONDS = 0.15

	def __init__(self, stream):
		dropsort.ResetOrder()
		ui.ScriptWindow.__init__(self, "GAME")
		self.SetWindowName("game")
		self.level104PassageClosed = False
		self.level104PassageHud = None
		self.AddFlag("game_surface")
		net.SetPhaseWindow(net.PHASE_WINDOW_GAME, self)
		if app.ENABLE_OFFLINE_SHOP:
			uiOfflineShop.GetOfflineShopManager().SetGameWindowInstance(self)
		player.SetGameWindow(self)
		resonanceuihelpers.ClearSealValues()
		# The phase router constructs us before closing a pending old window.
		# Do not touch that window's live album or send requests until Open.
		self.meteorProtection = meteorpresentation.ProtectionState()
		self.meteorToolTip = None
		self.petAlbumOwner = object()
		self.petAlbumReady = False
		self.petAlbumOffer = None
		self.petAlbumPreserving = False
		self.petAlbumClosed = False
		self.petAlbumSyncAt = 0.0

		self.quickSlotPageIndex = 0
		self.lastPKModeSendedTime = 0
		self.pressNumber = None

		if app.ENABLE_COMBAT_ZONE:
			import uicombatzone
			self.wndCombatZone = uicombatzone.CombatZoneWindow()

		self.guildWarQuestionDialog = None
		self.dungeonRejoinDialog = None
		self.guildPortal = None
		self.interface = None
		self.keybindingManager = None
		self.skillTreeRuntime = None
		self.dungeonObjectiveSubscription = dungeonobjectivemodel.ObjectiveSubscription(net.SendChatPacket, app.GetTime)
		self.targetBoard = None
		self.warpUITransition = False
		self.warpUIRestoreLoaded = False
		self.warpUIRestoreState = None
		self.warpUIRestoreDeadline = 0.0
		# Seamless warp: this window survives the reconnect (see
		# OnSeamlessWarpLeave/OnSeamlessWarpArrive); True until the
		# destination's ENTERGAME was sent.
		self.seamlessWarping = False
		self.dungeonBindingOwner = object()
		self.dungeonBindingClosed = False
		self.dungeonBindingReady = False
		self.dungeonBindingOffered = False
		self.craftIdsOffered = False
		self.craftIdsAnswered = False
		self.craftIdsRequested = False

		self.console = None
		self.mapNameShower = None
		self.affectShower = None
		self.pvmPersonal = None
		self.playerGauge = None

		if app.ENABLE_SKILL_SELECT_GUI:
			self.skillSelect = None

		if app.ENABLE_BIOLOG_SYSTEM:
			self.loopList = []

		self.stream=stream
		self.interface = interfaceModule.Interface()
		self.keybindingManager = keybindings.Manager(self.interface)
		keybindings.SetManager(self.keybindingManager)
		self.interface.MakeInterface()
		self.skillTreeRuntime = skilltreeruntime.SkillTreeRuntime(
			self.interface.wndSkillTree, net, app.GetTime,
		)
		self.interface.ShowDefaultWindows()

		if app.ENABLE_ITEMSHOP:
			osfInfo.SetGameInstance(self)
			osfInfo.SetInterfaceInstance(self.interface)

		if app.ENABLE_QUEST_OPTION:
			interfaceModule.IsQBHide = not systemSetting.GetQuestModeOption()
		# The persistent letters (Trvalé / Denní úkoly) were made in
		# MakeInterface, before the saved Ctrl+Q state was read.
		self.interface.ApplyQuestButtonVisibility()

		self.curtain = uiPhaseCurtain.PhaseCurtain()
		self.curtain.speed = 0.03
		self.curtain.Hide()
		self.initialWorldRevealPending = False
		self.initialWorldRevealStableUpdates = 0
		self.initialWorldRevealDayMode = None
		# Temporary restriction and sanctioned-automation flags
		# (docs/FEATURE_INVARIANTS.md, "InputGuard v1").
		self.inputGuardSyncFailed = False
		self.inputGuardHoverProbe = inputguardapi.HoverProbe(wndMgr.GetMousePosition)
		self.inputGuardSwitchbotProbe = self.__CreateSwitchbotProbe()
		self.__BindInputGuard()

		self.targetBoard = uiTarget.TargetBoard()
		self.targetBoard.SetWhisperEvent(ui.__mem_func__(self.interface.OpenWhisperDialog))
		self.targetBoard.Hide()
		self.interface.SettargetBoard(self.targetBoard)

		self.console = consoleModule.ConsoleWindow()
		self.console.BindGameClass(self)
		self.console.SetConsoleSize(wndMgr.GetScreenWidth(), 200)
		self.console.Hide()

		self.mapNameShower = uiMapNameShower.MapNameShower()
		self.affectShower = uiAffectShower.AffectShower()
		self.interface.SetAffectShower(self.affectShower)
		self.pvmPersonal = uiPvMPersonal.PersonalBonuses(self, self.affectShower, self.interface)

		self.playerGauge = uiPlayerGauge.PlayerGauge(self)
		self.playerGauge.Hide()
		self.skillTreeRuntime.SetPresentationObserver(ui.__mem_func__(self.__OnSkillTreePresentation))

		#wj 2014.1.2. ESC키를 누를 시 우선적으로 DropQuestionDialog를 끄도록 만들었다. 하지만 처음에 itemDropQuestionDialog가 선언되어 있지 않아 ERROR가 발생하여 init에서 선언과 동시에 초기화 시킴.
		self.itemDropQuestionDialog = None
		self.itemDestroyConfirmDialog = None
		self.itemDestroyPending = None
		self.buffiNameInputDialog = None

		self.__SetQuickSlotMode()

		self.messengerAddFriendQuestion = None
		self.pendingFriendRequests = []

		self.__ServerCommand_Build()
		import vipelfvisual
		vipelfvisual.Register()
		self.__ProcessPreservedServerCommand()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.interface.PetInfoBindAffectShower(self.affectShower)

		if app.ENABLE_SKILL_SELECT_GUI:
			self.skillSelect = uiselectskill.SkillSelectWindow()
			self.skillSelect.Hide()	

		if app.ENABLE_DROP_INFO_WINDOW:
			self.wndDropInfo = None
		self.ticketNotice = None

		self.partyRequestQuestionDialog = None
		self.partyInviteQuestionDialog = None
		if app.ENABLE_AUTO_PICKUP:
			self.lastAutoPickupTime = 0

	def __del__(self):
		player.SetGameWindow(0)
		net.ClearPhaseWindow(net.PHASE_WINDOW_GAME, self)
		ui.ScriptWindow.__del__(self)

	if app.ENABLE_WINDOW_RESIZE:
		def BINARY_UpdateUI(self):
			if self.interface:
				self.interface.UpdateUI()

	def __ArmInitialWorldReveal(self):
		self.initialWorldRevealPending = False
		self.initialWorldRevealStableUpdates = 0
		self.initialWorldRevealDayMode = None

		instantWarpCheck = getattr(net, "IsCustomPortsInstantWarpInProgress", None)
		if instantWarpCheck and instantWarpCheck():
			return

		self.initialWorldRevealPending = True
		self.curtain.CoverInstantly()

	def __UpdateInitialWorldReveal(self):
		if not self.initialWorldRevealPending:
			return

		mainCharacterIndex = player.GetMainCharacterIndex()
		if not mainCharacterIndex or not chr.HasInstance(mainCharacterIndex):
			self.initialWorldRevealStableUpdates = 0
			return

		# A created actor may still be waiting for its streamed ground height.
		# Older executables retain the existing actor-presence fallback.
		groundReady = getattr(player, "IsMainCharacterGroundReady", None)
		if groundReady and not groundReady():
			self.initialWorldRevealStableUpdates = 0
			return

		self.initialWorldRevealStableUpdates += 1
		if self.initialWorldRevealStableUpdates < 2:
			return

		self.initialWorldRevealPending = False
		pendingDayMode = self.initialWorldRevealDayMode
		self.initialWorldRevealDayMode = None
		if pendingDayMode is not None:
			self.__PRESERVE_DayMode_Update(pendingDayMode)
		self.curtain.FadeIn(self.INITIAL_WORLD_REVEAL_SECONDS)

	def Open(self):
		growthpetpresentation.ClearGrowthPreview()
		# The server replays every duel state on entering the game.
		duelchallenge.challenges.EnterGame()
		# A new game session forgets the AFK pause cause and zone list of the previous server.
		import uiafkrewardshop
		uiafkrewardshop.SetCause(0)
		uiafkrewardshop.SetZones(None)
		self.__ResetCraftIdsOffer()
		# The server of this session sends its own sale terms (EconomyViewV1).
		npcsellprice.Reset()
		attrchangecount.Reset()
		if app.ENABLE_AUTO_PICKUP:
			osfInfo.LoadPickupConfig()
		itembonuspresentation.totals.BeginSession(app.GetTime, net.SendChatPacket)
		characterbonuses.totals.BeginSession(app.GetTime, net.SendChatPacket)
		bonussources.server.BeginSession(app.GetTime, net.SendChatPacket)
		itembonuspresentation.SetTalentWeaponPercent(0)
		itembonuspresentation.SetTalentDurationPercents(0, 0)
		app.SetFrameSkip(1)

		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		if app.ENABLE_WINDOW_RESIZE:
			self.SetResizeDic({"size": (Expr("SCREEN_WIDTH"), Expr("SCREEN_HEIGHT"))})
		self.quickSlotPageIndex = 0
		self.PickingCharacterIndex = -1
		self.PickingItemIndex = -1
		self.consoleEnable = False
		self.isShowDebugInfo = False
		self.ShowNameFlag = False

		self.enableXMasBoom = False
		self.startTimeXMasBoom = 0.0
		self.indexXMasBoom = 0

		global cameraDistance, cameraPitch, cameraRotation, cameraHeight

		app.SetCamera(cameraDistance, cameraPitch, cameraRotation, cameraHeight)

		constInfo.SET_DEFAULT_CAMERA_MAX_DISTANCE()
		constInfo.SET_DEFAULT_CHRNAME_COLOR()
		constInfo.SET_DEFAULT_FOG_LEVEL()
		constInfo.SET_DEFAULT_CONVERT_EMPIRE_LANGUAGE_ENABLE()
		constInfo.SET_DEFAULT_USE_ITEM_WEAPON_TABLE_ATTACK_BONUS()
		constInfo.SET_DEFAULT_USE_SKILL_EFFECT_ENABLE()

		# TWO_HANDED_WEAPON_ATTACK_SPEED_UP
		constInfo.SET_TWO_HANDED_WEAPON_ATT_SPEED_DECREASE_VALUE()
		# END_OF_TWO_HANDED_WEAPON_ATTACK_SPEED_UP

		import event
		event.SetLeftTimeString(localeInfo.UI_LEFT_TIME)

		textTail.EnablePKTitle(constInfo.PVPMODE_ENABLE)

		#if constInfo.PVPMODE_TEST_ENABLE:
			#self.testPKMode = ui.TextLine()
			#self.testPKMode.SetFontName(localeInfo.UI_DEF_FONT)
			#self.testPKMode.SetPosition(0, 15)
			#self.testPKMode.SetWindowHorizontalAlignCenter()
			#self.testPKMode.SetHorizontalAlignCenter()
			#self.testPKMode.SetFeather()
			#self.testPKMode.SetOutline()
			#self.testPKMode.Show()

			#self.testAlignment = ui.TextLine()
			#self.testAlignment.SetFontName(localeInfo.UI_DEF_FONT)
			#self.testAlignment.SetPosition(0, 35)
			#self.testAlignment.SetWindowHorizontalAlignCenter()
			#self.testAlignment.SetHorizontalAlignCenter()
			#self.testAlignment.SetFeather()
			#self.testAlignment.SetOutline()
			#self.testAlignment.Show()

		self.__BuildKeyDict()
		self.__BuildDebugInfo()

		# PRIVATE_SHOP_PRICE_LIST
		uiPrivateShopBuilder.Clear()
		# END_OF_PRIVATE_SHOP_PRICE_LIST

		# UNKNOWN_UPDATE
		exchange.InitTrading()
		# END_OF_UNKNOWN_UPDATE

		# The engine debug overlay (coordinates, FPS, "MousePosition" at the top right) only with the explicit
		# osfInfo.DEBUG_MODE switch: a non-_DISTRIBUTE build (__DEBUG__) showed it to testers over the windows.
		if osfInfo.IsDebugMode():
			self.ToggleDebugInfo()

		## Sound
		snd.SetMusicVolume(systemSetting.GetMusicVolume()*net.GetFieldMusicVolume())
		snd.SetSoundVolume(systemSetting.GetSoundVolume())

		netFieldMusicFileName = net.GetFieldMusicFileName()
		if netFieldMusicFileName:
			snd.FadeInMusic("BGM/" + netFieldMusicFileName)
		elif musicInfo.fieldMusic != "":
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

		self.__SetQuickSlotMode()
		self.__SelectQuickPage(self.quickSlotPageIndex)

		self.__ArmInitialWorldReveal()
		self.SetFocus()
		self.Show()
		app.ShowCursor()

		net.SendEnterGamePacket()
		if self.interface:
			# craft contracts of the Denní úkoly window: only after ENTERGAME, the server drops them before
			self.interface.RequestCraftContractsAfterEnter()
		self.__StartDungeonEquipmentBindingSession()
		self.__OpenPetAlbumSession()
		self.dungeonObjectiveSubscription.start()
		self.skillTreeRuntime.Start()

		# START_GAME_ERROR_EXIT
		try:
			self.StartGame()
		except:
			import exception
			exception.Abort("GameWindow.Open")
		# END_OF_START_GAME_ERROR_EXIT

		# NPC가 큐브시스템으로 만들 수 있는 아이템들의 목록을 캐싱
		# ex) cubeInformation[20383] = [ {"rewordVNUM": 72723, "rewordCount": 1, "materialInfo": "101,1&102,2", "price": 999 }, ... ]
		self.cubeInformation = {}
		self.currentCubeNPC = 0

		if app.ENABLE_NEW_GAMEOPTION:
			if systemSetting.IsShowPet() == 0:
				net.SendChatPacket("/show_hide_pet 0")
			else:
				net.SendChatPacket("/show_hide_pet 1")

			if systemSetting.IsShowSupport() == 0:
				net.SendChatPacket("/show_hide_support 0")
			else:
				net.SendChatPacket("/show_hide_support 1")

			if systemSetting.IsShowMount() == 0:
				net.SendChatPacket("/show_hide_mount 0")
			else:
				net.SendChatPacket("/show_hide_mount 1")

			if systemSetting.IsShowShop() == 0:
				net.SendChatPacket("/show_hide_shop 0")
			else:
				net.SendChatPacket("/show_hide_shop 1")

		if systemSetting.GetCameraModeOption() == 1:
			app.SetCameraMaxDistance(3500.0 * 2)
		else:
			app.SetCameraMaxDistance(2500.0)

		mouseModule.mouseController.CreateNumberLine()

	def Close(self):
		dropsort.ResetOrder()
		uiunstuck.controller.Reset()
		self.level104PassageClosed = True
		if getattr(self, "level104PassageHud", None) is not None:
			self.level104PassageHud.Destroy()
			self.level104PassageHud = None
		if getattr(self, "serviceItemWindow", None):
			self.serviceItemWindow.Destroy()
			self.serviceItemWindow = None
		self.dungeonBindingClosed = True
		self.__StopDungeonEquipmentBindingSession()
		self.meteorProtection.clear()
		if self.meteorToolTip:
			self.meteorToolTip.Destroy()
			self.meteorToolTip = None
		self.__ClosePetAlbumSession()
		itembonuspresentation.totals.EndSession()
		characterbonuses.totals.EndSession()
		bonussources.server.EndSession()
		itembonuspresentation.SetTalentWeaponPercent(0)
		itembonuspresentation.SetTalentDurationPercents(0, 0)
		self.Hide()
		self.dungeonObjectiveSubscription.stop()
		if self.pvmPersonal:
			self.pvmPersonal.Destroy(self.warpUITransition)
			self.pvmPersonal = None
		if not self.warpUITransition:
			uiwarpstate.Clear()
			if self.interface:
				self.interface.ResetCountdownReminderState()
			if (app.ENABLE_BIOLOG_SYSTEM and self.interface
					and self.interface.wndBio):
				self.interface.wndBio.ResetReminderState()
		if self.skillTreeRuntime:
			self.skillTreeRuntime.Destroy()
			self.skillTreeRuntime = None

		if app.ENABLE_MULTI_FARM_BLOCK:
			app.SetMultiFarmExeIcon(1)

		global cameraDistance, cameraPitch, cameraRotation, cameraHeight
		(cameraDistance, cameraPitch, cameraRotation, cameraHeight) = app.GetCamera()

		if musicInfo.fieldMusic != "":
			snd.FadeOutMusic("BGM/"+ musicInfo.fieldMusic)

		self.onPressKeyDict = None
		self.onClickKeyDict = None

		chat.Close()
		snd.StopAllSound()
		grp.InitScreenEffect()
		chr.Destroy()
		textTail.Clear()
		quest.Clear()
		background.Destroy()
		guild.Destroy()
		messenger.Destroy()
		skill.ClearSkillData()
		wndMgr.Unlock()
		mouseModule.mouseController.DeattachObject()

		if self.guildWarQuestionDialog:
			self.guildWarQuestionDialog.Close()
		self.__CloseDungeonRejoinDialog()
		self.__DestroyGuildPortal()
		if self.buffiNameInputDialog:
			self.buffiNameInputDialog.Close()
			self.buffiNameInputDialog = None

		self.guildNameBoard = None
		self.partyRequestQuestionDialog = None
		self.partyInviteQuestionDialog = None
		self.guildInviteQuestionDialog = None
		self.guildWarQuestionDialog = None
		self.__ClearFriendRequests()

		# UNKNOWN_UPDATE
		if self.itemDropQuestionDialog:
			self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None
		if self.itemDestroyConfirmDialog:
			self.itemDestroyConfirmDialog.Close()
		self.itemDestroyConfirmDialog = None
		self.itemDestroyPending = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)
		# END_OF_UNKNOWN_UPDATE

		# QUEST_CONFIRM
		self.confirmDialog = None
		# END_OF_QUEST_CONFIRM

		self.PrintCoord = None
		self.FrameRate = None
		self.Pitch = None
		self.Splat = None
		self.TextureNum = None
		self.ObjectNum = None
		self.ViewDistance = None
		self.PrintMousePos = None

		self.ClearDictionary()

		self.playerGauge = None
		self.mapNameShower = None
		self.affectShower = None
		self.pvmPersonal = None

		if self.console:
			self.console.BindGameClass(0)
			self.console.Close()
			self.console = None

		if self.keybindingManager:
			self.keybindingManager.clear_pressed()
		self.keybindingManager = None
		keybindings.SetManager(None)

		self.inputGuardHoverProbe.Disable()
		inputguardapi.ClearAutomation()

		if self.interface:
			self.interface.HideAllWindows()
			self.interface.Close()
			del self.interface
			self.interface = None

		if self.targetBoard:
			self.targetBoard.Destroy()
			self.targetBoard = None

		if app.ENABLE_COMBAT_ZONE:
			if self.wndCombatZone:
				self.wndCombatZone.Close()

		if app.ENABLE_ITEMSHOP:
			osfInfo.SetInterfaceInstance(None)
			osfInfo.SetGameInstance(None)

		if app.ENABLE_OFFLINE_SHOP:
			uiOfflineShop.GetOfflineShopManager().Destroy()
			self.uiOfflineShop = None

		if app.ENABLE_DROP_INFO_WINDOW:
			if self.wndDropInfo:
				self.wndDropInfo.Hide()
			del self.wndDropInfo
		if self.ticketNotice:
			self.ticketNotice.Destroy()
			self.ticketNotice = None

		if app.ENABLE_BIOLOG_SYSTEM:
			self.loopList = []

		player.ClearSkillDict()
		player.ResetCameraRotation()

		self.KillFocus()
		app.HideCursor()

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

		if app.ENABLE_SKILL_SELECT_GUI:
			if self.skillSelect:
				self.skillSelect.Destroy()
				self.skillSelect = None

		mouseModule.mouseController.Destroy()
		#print "---------------------------------------------------------------------------- CLOSE GAME WINDOW"

	################################
	# Seamless warp (networkModule.MainStream hooks)
	#
	# The legacy warp destroys this window in Close() and builds a new one in
	# the destination's game phase. With the server warp curtain the EXE keeps
	# it: Leave runs the per-session half of Close() and Arrive the per-session
	# half of Open(), while the curtain covers the world. Windows the player
	# had open come back through the same uiwarpstate allowlist as before.
	# Every step is isolated: a failing window must not stop the warp.

	def __SeamlessStep(self, name, function, *args):
		try:
			function(*args)
		except Exception as error:
			dbg.TraceError("[SeamlessWarp] %s failed: %s" % (name, error))

	def IsSeamlessWarping(self):
		return self.seamlessWarping

	def __IsWarpInputLocked(self):
		if self.seamlessWarping:
			return True
		locked = getattr(self.stream, "IsWarpCurtainInputLocked", None)
		return bool(locked and locked())

	# InputGuard v1 ---------------------------------------------------------
	# The server alone opens and closes the temporary restriction through
	# BINARY_InputGuardPenalty; nothing here remembers it across a warp.

	def __InputGuardSystem(self):
		interface = self.interface
		return getattr(interface, "inputGuardSystem", None) if interface else None

	def __BindInputGuard(self):
		system = self.__InputGuardSystem()
		if system:
			system.BindGameWindow(ui.__mem_func__(self.__IsOtherCurtainActive),
				ui.__mem_func__(self.__OnInputGuardLock))

	def __IsOtherCurtainActive(self):
		# One curtain at a time: the warp curtain, the phase curtain and
		# this window's own reveal/day-mode curtain all go first.
		stream = self.stream
		warpActive = getattr(stream, "IsWarpCurtainActive", None)
		if warpActive and warpActive():
			return True
		if self.curtain and self.curtain.IsShow():
			return True
		phaseCurtain = getattr(stream, "curtain", None)
		return bool(phaseCurtain and phaseCurtain.IsShow())

	def __IsInputGuardLocked(self):
		system = self.__InputGuardSystem()
		return bool(system and system.IsInputLocked())

	def __OnInputGuardLock(self, locked):
		if not locked:
			return
		# Same release as a warp: nothing stays held under the curtain.
		self.__ReleaseWarpKeys()
		mouseModule.mouseController.DeattachObject()
		interface = self.interface
		if not interface:
			return
		if interface.wndChat and interface.wndChat.IsEditMode():
			interface.wndChat.CloseChat()
		if interface.dlgSystem:
			interface.dlgSystem.Close()

	def __CreateSwitchbotProbe(self):
		if not getattr(app, "ENABLE_SWITCHBOT_SYSTEM", 0):
			return None
		try:
			import switchbot
			return inputguardapi.SwitchbotProbe(switchbot.IsActive, switchbot.SLOT_COUNT,
				instantOptions.IsActive)
		except Exception:
			return None

	def __IsAutoAttackActive(self):
		interface = self.interface
		for name in ("wndAutoHunting", "wndAutoWindow"):
			window = getattr(interface, name, None)
			if window and window.GetAutoStartonoff():
				return True
		return False

	def __UpdateInputGuard(self):
		"""Mark the sanctioned automations content can see for the EXE."""
		if self.inputGuardSyncFailed or not inputguardapi.HasAutomationApi():
			return
		try:
			now = app.GetTime()
			interface = self.interface
			setAutomation = inputguardapi.SetAutomation
			queueCount = getattr(player, "GetMetinQueueCount", None)
			setAutomation(inputguardapi.AUTOMATION_METIN_QUEUE,
				bool(queueCount and queueCount() > 0))
			setAutomation(inputguardapi.AUTOMATION_AUTO_PICKUP,
				bool(app.ENABLE_AUTO_PICKUP and osfInfo.AUTOPICKUP_ENABLED))
			setAutomation(inputguardapi.AUTOMATION_QUICK_BUFF,
				bool(interface and interface.IsQuickBuffBusy()))
			setAutomation(inputguardapi.AUTOMATION_AUTO_ATTACK, self.__IsAutoAttackActive())
			probe = self.inputGuardSwitchbotProbe
			if probe:
				setAutomation(inputguardapi.AUTOMATION_SWITCHBOT, probe.Update(now))
			self.inputGuardHoverProbe.Update(now, interface)
		except Exception as error:
			self.inputGuardSyncFailed = True
			inputguardapi.ClearAutomation()
			dbg.TraceError("[IG1] automation flags disabled: %s" % error)

	def __InputGuardOffer(self, version):
		# Capability handshake: answer with the content caps. An EXE without
		# the declare packet stays silent, exactly like an older root pack.
		try:
			if inputguardapi.Declare(net, version):
				inputguardapi.ResendAutomation()
				self.inputGuardHoverProbe.Enable()
		except Exception as error:
			dbg.TraceError("[IG1] declare failed: %s" % error)

	def __InputGuardWatchState(self, pid, watchId, captureId, deadline, gap):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchState(pid, watchId, captureId, deadline, gap)

	def __InputGuardLegend(self, row):
		# One row of the GM watch viewer's legend: a single field whose parts
		# vary by row and are validated by the viewer's model.
		try:
			system = self.__InputGuardSystem()
			if system:
				system.OnWatchLegend(row)
		except Exception as error:
			dbg.TraceError("[IG1] legend row failed: %s" % error)

	def BINARY_InputGuardPenalty(self, remainingSec, reason):
		system = self.__InputGuardSystem()
		if system:
			system.OnPenalty(remainingSec, reason)

	def BINARY_InputGuardWatchBegin(self, pid, captureId, name):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchBegin(pid, captureId, name)

	def BINARY_InputGuardWatchTrace(self, pid, clientW, clientH, samples):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchTrace(pid, clientW, clientH, samples)

	def BINARY_InputGuardWatchVerdict(self, pid, verdict):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchVerdict(pid, verdict)

	def BINARY_InputGuardWatchAction(self, pid, tMs, kind, cover):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchAction(pid, tMs, kind, cover)

	def BINARY_InputGuardWatchEnd(self, pid, reason):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchEnd(pid, reason)

	def BINARY_InputGuardWatchStatus(self, pid, report, secondsSinceReport,
			missedHeartbeats, penaltyActive):
		system = self.__InputGuardSystem()
		if system:
			system.OnWatchStatus(pid, report, secondsSinceReport,
				missedHeartbeats, penaltyActive)

	def OnSeamlessMapWarpLeave(self):
		self.meteorProtection.clear()
		if self.meteorToolTip:
			self.meteorToolTip.Hide()
		self.seamlessWarping = True
		step = self.__SeamlessStep
		# The server re-acquires the talent owner with a fresh request nonce.
		if self.skillTreeRuntime:
			step("skill tree", self.skillTreeRuntime.Destroy)
			self.skillTreeRuntime = None
		step("dialogs", self.__CloseSessionDialogs)
		step("keys", self.__ReleaseWarpKeys)
		step("drag", mouseModule.mouseController.DeattachObject)
		if self.targetBoard:
			step("target board", self.__ResetTargetBoardForWarp)
		if self.interface:
			step("map windows", self.interface.OnSeamlessMapWarpLeave)
		step("unlock", wndMgr.Unlock)
		if musicInfo.fieldMusic != "":
			step("music", snd.FadeOutMusic, "BGM/" + musicInfo.fieldMusic)
		step("sounds", snd.StopAllSound)

	def OnSeamlessMapWarpArrive(self):
		self.seamlessWarping = False
		self.PickingCharacterIndex = -1
		self.PickingItemIndex = -1
		if not self.skillTreeRuntime and self.interface:
			self.__SeamlessStep("skill tree", self.__CreateSkillTreeRuntime)
		if self.skillTreeRuntime:
			self.__SeamlessStep("skill tree start", self.skillTreeRuntime.Start)
			self.__SeamlessStep("skill tree refresh", self.skillTreeRuntime.Open)
		self.__SeamlessStep("music", self.__StartFieldMusic)
		self.__SeamlessStep("refresh", self.StartGame)

	def OnSeamlessWarpLeave(self):
		self.meteorProtection.clear()
		if self.meteorToolTip:
			self.meteorToolTip.Hide()
		self.seamlessWarping = True
		# The destination session receives its own CraftIdsV1 offer.
		self.__ResetCraftIdsOffer()
		npcsellprice.Reset()
		attrchangecount.Reset()
		self.warpUITransition = True
		self.warpUIRestoreLoaded = False
		self.warpUIRestoreState = None
		step = self.__SeamlessStep

		if self.interface:
			try:
				self.interface.CaptureWarpUIState()
			except Exception:
				uiwarpstate.Clear()
				dbg.TraceError("[WarpUI] snapshot failed; continuing without restore")
		# Records the album notices into the snapshot while warpUITransition.
		step("dungeon equipment binding", self.__StopDungeonEquipmentBindingSession)
		step("pet album", self.__ClosePetAlbumSession)
		step("bonus totals", itembonuspresentation.totals.EndSession)
		step("character totals", characterbonuses.totals.EndSession)
		step("bonus sources", bonussources.server.EndSession)
		step("talent weapon", itembonuspresentation.SetTalentWeaponPercent, 0)
		step("talent durations", itembonuspresentation.SetTalentDurationPercents, 0, 0)
		step("dungeon objective", self.dungeonObjectiveSubscription.stop)
		if self.skillTreeRuntime:
			step("skill tree", self.skillTreeRuntime.Destroy)
			self.skillTreeRuntime = None
		if self.pvmPersonal:
			step("pvm personal", self.pvmPersonal.Destroy, True)
			self.pvmPersonal = None
		if self.interface:
			step("interface", self.interface.OnSeamlessWarpLeave)
		if self.targetBoard:
			step("target board", self.__ResetTargetBoardForWarp)
		if self.interface:
			step("quick buff effects", self.interface.OnQuickBuffAffectsCleared)
		if self.affectShower:
			step("affects", self.affectShower.ClearAllAffects)

		step("dialogs", self.__CloseSessionDialogs)
		step("keys", self.__ReleaseWarpKeys)
		step("drag", mouseModule.mouseController.DeattachObject)
		step("unlock", wndMgr.Unlock)
		if musicInfo.fieldMusic != "":
			step("music", snd.FadeOutMusic, "BGM/" + musicInfo.fieldMusic)
		step("sounds", snd.StopAllSound)
		step("screen effect", grp.InitScreenEffect)
		# The destination re-sends quests, guild and messenger data; the
		# native modules must not merge it into the source core's state.
		step("quest", quest.Clear)
		step("guild", guild.Destroy)
		step("messenger", messenger.Destroy)
		step("skill data", skill.ClearSkillData)
		step("skill dict", player.ClearSkillDict)
		step("bonus catalog", bonusCatalog.ClearPending)

	def OnSeamlessWarpArrive(self):
		step = self.__SeamlessStep
		if app.ENABLE_AUTO_PICKUP:
			step("pickup preferences", osfInfo.LoadPickupConfig)
		self.seamlessWarping = False
		self.warpUITransition = False
		# __RestoreWarpUIState consumes the snapshot for this character.
		self.warpUIRestoreLoaded = False
		self.warpUIRestoreState = None

		step("bonus totals", itembonuspresentation.totals.BeginSession, app.GetTime, net.SendChatPacket)
		step("character totals", characterbonuses.totals.BeginSession, app.GetTime, net.SendChatPacket)
		step("bonus sources", bonussources.server.BeginSession, app.GetTime, net.SendChatPacket)
		step("talent weapon", itembonuspresentation.SetTalentWeaponPercent, 0)
		step("talent durations", itembonuspresentation.SetTalentDurationPercents, 0, 0)
		self.PickingCharacterIndex = -1
		self.PickingItemIndex = -1
		step("private shop", uiPrivateShopBuilder.Clear)
		step("trading", exchange.InitTrading)
		step("music", self.__StartFieldMusic)
		step("quick slots", self.__SelectQuickPage, self.quickSlotPageIndex)
		if self.interface:
			step("interface", self.interface.OnSeamlessWarpArrive)
		if not self.pvmPersonal:
			step("pvm personal", self.__CreatePvmPersonal)
		if not self.skillTreeRuntime and self.interface:
			step("skill tree", self.__CreateSkillTreeRuntime)
		step("dungeon equipment binding", self.__StartDungeonEquipmentBindingSession)
		step("pet album", self.__OpenPetAlbumSession)
		step("dungeon objective", self.dungeonObjectiveSubscription.start)
		if self.skillTreeRuntime:
			step("skill tree start", self.skillTreeRuntime.Start)
		step("refresh", self.StartGame)
		self.cubeInformation = {}
		self.currentCubeNPC = 0
		step("visibility options", self.__SendVisibilityOptions)
		self.SetFocus()
		self.Show()
		app.ShowCursor()

	def __ResetTargetBoardForWarp(self):
		reset = getattr(self.targetBoard, "ResetTargetBoard", None)
		if reset:
			reset()
		self.targetBoard.Close()

	def __CloseSessionDialogs(self):
		uiunstuck.controller.Reset()
		if self.guildWarQuestionDialog:
			self.guildWarQuestionDialog.Close()
		self.guildWarQuestionDialog = None
		self.__CloseDungeonRejoinDialog()
		self.__DestroyGuildPortal()
		if self.buffiNameInputDialog:
			self.buffiNameInputDialog.Close()
			self.buffiNameInputDialog = None
		for name in ("partyRequestQuestionDialog", "partyInviteQuestionDialog", "guildInviteQuestionDialog"):
			dialog = getattr(self, name, None)
			if dialog:
				dialog.Close()
			setattr(self, name, None)
		self.__ClearFriendRequests()
		if self.itemDropQuestionDialog:
			self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None
		if self.itemDestroyConfirmDialog:
			self.itemDestroyConfirmDialog.Close()
		self.itemDestroyConfirmDialog = None
		self.itemDestroyPending = None
		confirm = getattr(self, "confirmDialog", None)
		if confirm:
			confirm.Close()
		self.confirmDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def __ReleaseWarpKeys(self):
		if self.keybindingManager:
			self.keybindingManager.clear_pressed()

	def __StartFieldMusic(self):
		snd.SetMusicVolume(systemSetting.GetMusicVolume()*net.GetFieldMusicVolume())
		snd.SetSoundVolume(systemSetting.GetSoundVolume())
		netFieldMusicFileName = net.GetFieldMusicFileName()
		if netFieldMusicFileName:
			snd.FadeInMusic("BGM/" + netFieldMusicFileName)
		elif musicInfo.fieldMusic != "":
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

	def __CreatePvmPersonal(self):
		self.pvmPersonal = uiPvMPersonal.PersonalBonuses(self, self.affectShower, self.interface)

	def __CreateSkillTreeRuntime(self):
		self.skillTreeRuntime = skilltreeruntime.SkillTreeRuntime(
			self.interface.wndSkillTree, net, app.GetTime,
		)
		self.skillTreeRuntime.SetPresentationObserver(ui.__mem_func__(self.__OnSkillTreePresentation))

	def __SendVisibilityOptions(self):
		if not app.ENABLE_NEW_GAMEOPTION:
			return
		net.SendChatPacket("/show_hide_pet %d" % (1 if systemSetting.IsShowPet() else 0))
		net.SendChatPacket("/show_hide_support %d" % (1 if systemSetting.IsShowSupport() else 0))
		net.SendChatPacket("/show_hide_mount %d" % (1 if systemSetting.IsShowMount() else 0))
		net.SendChatPacket("/show_hide_shop %d" % (1 if systemSetting.IsShowShop() else 0))

	def __PvmPersonalSnapshot(self, version, server_time, wire_job, wire_group, serial,
			attack_skill, attack_hud, attack_learned, attack_activated,
			attack_revision, attack_end, attack_value, attack_power,
			attack_notice, attack_status,
			defense_skill, defense_hud, defense_learned, defense_activated,
			defense_revision, defense_end, defense_value, defense_power,
			defense_notice, defense_status,
			reduction_skill, reduction_hud, reduction_learned, reduction_activated,
			reduction_revision, reduction_end, reduction_value, reduction_power,
			reduction_notice, reduction_status):
		# The analyzer truncates to declared positional arguments: keep all 35
		# wire fields and route them to the HUD recreated on seamless arrival.
		if self.pvmPersonal:
			return self.pvmPersonal.Snapshot(
				version, server_time, wire_job, wire_group, serial,
				attack_skill, attack_hud, attack_learned, attack_activated,
				attack_revision, attack_end, attack_value, attack_power,
				attack_notice, attack_status,
				defense_skill, defense_hud, defense_learned, defense_activated,
				defense_revision, defense_end, defense_value, defense_power,
				defense_notice, defense_status,
				reduction_skill, reduction_hud, reduction_learned, reduction_activated,
				reduction_revision, reduction_end, reduction_value, reduction_power,
				reduction_notice, reduction_status)
		return False

	def __BuildKeyDict(self):
		onPressKeyDict = {}

		# PressKey 는 누르고 있는 동안 계속 적용되는 키이다.

		## 숫자 단축키 퀵슬롯에 이용된다.(이후 숫자들도 퀵 슬롯용 예약)
		## F12 는 클라 디버그용 키이므로 쓰지 않는 게 좋다.
		onPressKeyDict[app.DIK_1] = lambda : self.__PressNumKey(1)
		onPressKeyDict[app.DIK_2] = lambda : self.__PressNumKey(2)
		onPressKeyDict[app.DIK_3] = lambda : self.__PressNumKey(3)
		onPressKeyDict[app.DIK_4] = lambda : self.__PressNumKey(4)
		onPressKeyDict[app.DIK_5] = lambda : self.__PressNumKey(5)
		onPressKeyDict[app.DIK_6] = lambda : self.__PressNumKey(6)
		onPressKeyDict[app.DIK_7] = lambda : self.__PressNumKey(7)
		onPressKeyDict[app.DIK_8] = lambda : self.__PressNumKey(8)
		onPressKeyDict[app.DIK_9] = lambda : self.__PressNumKey(9)
		onPressKeyDict[app.DIK_F1] = lambda : self.__PressQuickSlot(4)
		onPressKeyDict[app.DIK_F2] = lambda : self.__PressQuickSlot(5)
		onPressKeyDict[app.DIK_F3] = lambda : self.__PressQuickSlot(6)
		onPressKeyDict[app.DIK_F4] = lambda : self.__PressQuickSlot(7)
		onPressKeyDict[app.DIK_F10] = lambda : self.interface.ToggleGMPanelWindow()

#		if app.ENABLE_EVENT_MANAGER:
#			onPressKeyDict[app.DIK_F5]	= lambda : self.interface.OpenEventCalendar()

#		if app.ENABLE_PLAYER_RANKING:
#			onPressKeyDict[app.DIK_F6]	= lambda : self.interface.ShowRankGlobal()

#		if app.ENABLE_BATTLE_PASS:
#			onPressKeyDict[app.DIK_F7]	= lambda : self.interface.ShowBattlePass()

#		if app.ENABLE_BIOLOG_SYSTEM:
#			onPressKeyDict[app.DIK_F8] = lambda : self.OpenBio()

#		if app.ENABLE_EXCHANGE_LOG:
#			onPressKeyDict[app.DIK_F9]	= lambda : self.interface.OpenExchangeLog()

#		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
#			onPressKeyDict[app.DIK_K] = lambda : self.interface.OpenSpecialInventoryWindow()

#		if app.ENABLE_SHOP_SEARCH:
#			onPressKeyDict[app.DIK_J] = lambda : self.interface.OpenShopSearchWindow()

		onPressKeyDict[app.DIK_LALT] = lambda : self.ShowName()
		onPressKeyDict[app.DIK_LCONTROL] = lambda : self.ShowMouseImage()
		onPressKeyDict[app.DIK_SYSRQ] = lambda : self.SaveScreen()
		onPressKeyDict[app.DIK_SPACE] = lambda : self.StartAttack()

		# 캐릭터 이동키
		onPressKeyDict[app.DIK_UP] = lambda : self.MoveUp()
		onPressKeyDict[app.DIK_DOWN] = lambda : self.MoveDown()
		onPressKeyDict[app.DIK_LEFT] = lambda : self.MoveLeft()
		onPressKeyDict[app.DIK_RIGHT] = lambda : self.MoveRight()
		onPressKeyDict[app.DIK_W] = lambda : self.MoveUp()
		onPressKeyDict[app.DIK_S] = lambda : self.MoveDown()
		onPressKeyDict[app.DIK_A] = lambda : self.MoveLeft()
		onPressKeyDict[app.DIK_D] = lambda : self.MoveRight()

		onPressKeyDict[app.DIK_E] = self.__PressEKey
		onPressKeyDict[app.DIK_R] = lambda: app.ZoomCamera(app.CAMERA_TO_NEGATIVE)
		#onPressKeyDict[app.DIK_F] = lambda: app.ZoomCamera(app.CAMERA_TO_POSITIVE)
		onPressKeyDict[app.DIK_T] = lambda: app.PitchCamera(app.CAMERA_TO_NEGATIVE)
		onPressKeyDict[app.DIK_G] = self.__PressGKey
		onPressKeyDict[app.DIK_Q] = self.__PressQKey

		onPressKeyDict[app.DIK_NUMPAD9] = lambda: app.MovieResetCamera()
		onPressKeyDict[app.DIK_NUMPAD4] = lambda: app.MovieRotateCamera(app.CAMERA_TO_NEGATIVE)
		onPressKeyDict[app.DIK_NUMPAD6] = lambda: app.MovieRotateCamera(app.CAMERA_TO_POSITIVE)
		onPressKeyDict[app.DIK_PGUP] = lambda: app.MovieZoomCamera(app.CAMERA_TO_NEGATIVE)
		onPressKeyDict[app.DIK_PGDN] = lambda: app.MovieZoomCamera(app.CAMERA_TO_POSITIVE)
		onPressKeyDict[app.DIK_NUMPAD8] = lambda: app.MoviePitchCamera(app.CAMERA_TO_NEGATIVE)
		onPressKeyDict[app.DIK_NUMPAD2] = lambda: app.MoviePitchCamera(app.CAMERA_TO_POSITIVE)
		onPressKeyDict[app.DIK_GRAVE] = lambda : self.PickUpItem()
		if app.ENABLE_QUICK_PICKUP:
			onPressKeyDict[app.DIK_Z] = lambda : self.PickupSpecial()
		else:
			onPressKeyDict[app.DIK_Z] = lambda : self.PickUpItem()
		#onPressKeyDict[app.DIK_B] = lambda state = "EMOTICON": self.interface.ToggleCharacterWindow(state)
		onPressKeyDict[app.DIK_O] = lambda : self.__PressOKey()

		#onPressKeyDict[app.DIK_H] = lambda : self.interface.OpenHelpWindow()
		onPressKeyDict[app.DIK_ADD] = lambda : self.interface.MiniMapScaleUp()
		onPressKeyDict[app.DIK_SUBTRACT] = lambda : self.interface.MiniMapScaleDown()
		onPressKeyDict[app.DIK_COMMA] = lambda : self.ShowConsole() # "`" key
		onPressKeyDict[app.DIK_LSHIFT] = lambda : self.__SetQuickPageMode()

		#onPressKeyDict[app.DIK_J] = lambda : self.__PressJKey()
		onPressKeyDict[app.DIK_H] = lambda : self.__PressHKey()
		onPressKeyDict[app.DIK_B] = lambda : self.__PressBKey()
		onPressKeyDict[app.DIK_F] = lambda : self.__PressFKey()

		# CUBE_TEST
		#onPressKeyDict[app.DIK_K] = lambda : self.interface.OpenCubeWindow()
		# CUBE_TEST_END

		self.onPressKeyDict = onPressKeyDict

		onClickKeyDict = {}
		onClickKeyDict[app.DIK_UP] = lambda : self.StopUp()
		onClickKeyDict[app.DIK_DOWN] = lambda : self.StopDown()
		onClickKeyDict[app.DIK_LEFT] = lambda : self.StopLeft()
		onClickKeyDict[app.DIK_RIGHT] = lambda : self.StopRight()
		onClickKeyDict[app.DIK_SPACE] = lambda : self.EndAttack()

		onClickKeyDict[app.DIK_W] = lambda : self.StopUp()
		onClickKeyDict[app.DIK_S] = lambda : self.StopDown()
		onClickKeyDict[app.DIK_A] = lambda : self.StopLeft()
		onClickKeyDict[app.DIK_D] = lambda : self.StopRight()
		onClickKeyDict[app.DIK_Q] = lambda: app.RotateCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_E] = lambda: app.RotateCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_R] = lambda: app.ZoomCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_F] = lambda: app.ZoomCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_T] = lambda: app.PitchCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_G] = lambda: self.__ReleaseGKey()
		onClickKeyDict[app.DIK_NUMPAD4] = lambda: app.MovieRotateCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_NUMPAD6] = lambda: app.MovieRotateCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_PGUP] = lambda: app.MovieZoomCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_PGDN] = lambda: app.MovieZoomCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_NUMPAD8] = lambda: app.MoviePitchCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_NUMPAD2] = lambda: app.MoviePitchCamera(app.CAMERA_STOP)
		onClickKeyDict[app.DIK_LALT] = lambda: self.HideName()
		onClickKeyDict[app.DIK_LCONTROL] = lambda: self.HideMouseImage()
		onClickKeyDict[app.DIK_LSHIFT] = lambda: self.__SetQuickSlotMode()

		#if constInfo.PVPMODE_ACCELKEY_ENABLE:
		#	onClickKeyDict[app.DIK_B] = lambda: self.ChangePKMode()

		self.onClickKeyDict=onClickKeyDict

	def __PressNumKey(self,num):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):

			if num >= 1 and num <= 9:
				if (chrmgr.IsPossibleEmoticon(-1)):
					chrmgr.SetEmoticon(-1, int(num)-1)
					net.SendEmoticon(int(num)-1)
		else:
			if num >= 1 and num <= 4:
				self.pressNumber(num-1)

	def __ClickBKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			return
		else:
			if constInfo.PVPMODE_ACCELKEY_ENABLE:
				self.ChangePKMode()

	def __PressJKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			if player.IsMountingHorse():
				net.SendChatPacket("/unmount")
			else:
				#net.SendChatPacket("/user_horse_ride")
				if not uiPrivateShopBuilder.IsBuildingPrivateShop():
					for i in range(player.INVENTORY_PAGE_SIZE):
						if player.GetItemIndex(i) in (71114, 71116, 71118, 71120):
							net.SendItemUsePacket(i)
							break

	def	__PressHKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			net.SendChatPacket("/user_horse_ride")

	def __PressOKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			if self.interface.wndDragonSoul:
				self.interface.wndDragonSoul.ActivateButtonClick()

	def __PressBKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			net.SendChatPacket("/user_horse_back")

	def __PressFKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			net.SendChatPacket("/user_horse_feed")
		else:
			app.ZoomCamera(app.CAMERA_TO_POSITIVE)

	def __PressGKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			net.SendChatPacket("/ride")
		elif not (app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT)):
			app.PitchCamera(app.CAMERA_TO_POSITIVE)

	def __ReleaseGKey(self):
		app.PitchCamera(app.CAMERA_STOP)

	def __PressQKey(self):
		# Hiding the letters on the left is the rebindable keybinding
		# "information.quest_letters" (default Ctrl+Q, Interface.ToggleQuestLetters),
		# dispatched by keybindings.Manager before this dictionary. Ctrl+Q
		# that no binding owns does nothing here (no camera turn).
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			return
		app.RotateCamera(app.CAMERA_TO_NEGATIVE)

	def __PressEKey(self):
		if app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL):
			if 0 == interfaceModule.IsWisperHide:
				interfaceModule.IsWisperHide = 1
				self.interface.HideAllWhisperButton()
			else:
				interfaceModule.IsWisperHide= 0
				self.interface.ShowAllWhisperButton()
		else:
			app.RotateCamera(app.CAMERA_TO_POSITIVE)

	def __SetQuickSlotMode(self):
		self.pressNumber = ui.__mem_func__(self.__PressQuickSlot)

	def __SetQuickPageMode(self):
		self.pressNumber = ui.__mem_func__(self.__SelectQuickPage)

	if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
		def SetAutoCooltime(self, slotindex, cooltime):
			self.interface.SetAutoCooltime(slotindex, cooltime)

		def SetCloseGame(self):
			self.interface.SetCloseGame()

	def __PressQuickSlot(self, localSlotIndex):
		if app.ENABLE_GROWTH_PET_SYSTEM:
			if localeInfo.IsARABIC():
				if 0 <= localSlotIndex and localSlotIndex < 4:
					localSlotIndex = 3 - localSlotIndex
				else:
					localSlotIndex = 11 - localSlotIndex
			
			result = player.CanUseGrowthPetQuickSlot(localSlotIndex)
			
			if player.QUICK_SLOT_POS_ERROR == result:
				return
			elif result in [player.QUICK_SLOT_ITEM_USE_SUCCESS, player.QUICK_SLOT_IS_NOT_ITEM, player.QUICK_SLOT_PET_ITEM_USE_SUCCESS]:
				player.RequestUseLocalQuickSlot(localSlotIndex)
			elif player.QUICK_SLOT_PET_ITEM_USE_FAILED == result:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_SUMMON_BECAUSE_LIFE_TIME_END)
			elif player.QUICK_SLOT_CAN_NOT_USE_PET_ITEM == result:
				return
			
		else:
			if localeInfo.IsARABIC():
				if 0 <= localSlotIndex and localSlotIndex < 4:
					player.RequestUseLocalQuickSlot(3-localSlotIndex)
				else:
					player.RequestUseLocalQuickSlot(11-localSlotIndex)
			else:
				player.RequestUseLocalQuickSlot(localSlotIndex)	

	def __SelectQuickPage(self, pageIndex):
		self.quickSlotPageIndex = pageIndex
		player.SetQuickPage(pageIndex)

	def ToggleDebugInfo(self):
		self.isShowDebugInfo = not self.isShowDebugInfo

		if self.isShowDebugInfo:
			self.PrintCoord.Show()
			self.FrameRate.Show()
			self.Pitch.Show()
			self.Splat.Show()
			self.TextureNum.Show()
			self.ObjectNum.Show()
			self.ViewDistance.Show()
			self.PrintMousePos.Show()
		else:
			self.PrintCoord.Hide()
			self.FrameRate.Hide()
			self.Pitch.Hide()
			self.Splat.Hide()
			self.TextureNum.Hide()
			self.ObjectNum.Hide()
			self.ViewDistance.Hide()
			self.PrintMousePos.Hide()

	def __BuildDebugInfo(self):
		## Character Position Coordinate
		self.PrintCoord = ui.TextLine()
		self.PrintCoord.SetFontName(localeInfo.UI_DEF_FONT)
		self.PrintCoord.SetPosition(wndMgr.GetScreenWidth() - 270, 0)

		## Frame Rate
		self.FrameRate = ui.TextLine()
		self.FrameRate.SetFontName(localeInfo.UI_DEF_FONT)
		self.FrameRate.SetPosition(wndMgr.GetScreenWidth() - 270, 20)

		## Camera Pitch
		self.Pitch = ui.TextLine()
		self.Pitch.SetFontName(localeInfo.UI_DEF_FONT)
		self.Pitch.SetPosition(wndMgr.GetScreenWidth() - 270, 40)

		## Splat
		self.Splat = ui.TextLine()
		self.Splat.SetFontName(localeInfo.UI_DEF_FONT)
		self.Splat.SetPosition(wndMgr.GetScreenWidth() - 270, 60)

		##
		self.PrintMousePos = ui.TextLine()
		self.PrintMousePos.SetFontName(localeInfo.UI_DEF_FONT)
		self.PrintMousePos.SetPosition(wndMgr.GetScreenWidth() - 270, 80)

		# TextureNum
		self.TextureNum = ui.TextLine()
		self.TextureNum.SetFontName(localeInfo.UI_DEF_FONT)
		self.TextureNum.SetPosition(wndMgr.GetScreenWidth() - 270, 100)

		# 오브젝트 그리는 개수
		self.ObjectNum = ui.TextLine()
		self.ObjectNum.SetFontName(localeInfo.UI_DEF_FONT)
		self.ObjectNum.SetPosition(wndMgr.GetScreenWidth() - 270, 120)

		# 시야거리
		self.ViewDistance = ui.TextLine()
		self.ViewDistance.SetFontName(localeInfo.UI_DEF_FONT)
		self.ViewDistance.SetPosition(0, 0)

	def __NotifyError(self, msg):
		chat.AppendChat(chat.CHAT_TYPE_INFO, msg)

	def ChangePKMode(self):
		if not app.IsPressed(app.DIK_LCONTROL):
			return

		if player.GetStatus(player.LEVEL) < constInfo.PVPMODE_PROTECTED_LEVEL:
			self.__NotifyError(localeInfo.OPTION_PVPMODE_PROTECT % (constInfo.PVPMODE_PROTECTED_LEVEL))
			return

		curTime = app.GetTime()
		if curTime - self.lastPKModeSendedTime < constInfo.PVPMODE_ACCELKEY_DELAY:
			return

		self.lastPKModeSendedTime = curTime

		curPKMode = player.GetPKMode()
		nextPKMode = curPKMode + 1
		if nextPKMode == player.PK_MODE_PROTECT:
			if 0 == player.GetGuildID():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPTION_PVPMODE_CANNOT_SET_GUILD_MODE)
				nextPKMode = 0
			else:
				nextPKMode = player.PK_MODE_GUILD

		elif nextPKMode == player.PK_MODE_MAX_NUM:
			nextPKMode = 0

		net.SendChatPacket("/PKMode " + str(nextPKMode))
		print("/PKMode " + str(nextPKMode))

	def OnChangePKMode(self):
		self.interface.OnChangePKMode()

		try:
			if player.GetStatus(player.LEVEL) < constInfo.PVPMODE_PROTECTED_LEVEL:
				self.__NotifyError(localeInfo.OPTION_PVPMODE_MESSAGE_DICT[player.GetPKMode()])
				return
		except KeyError:
			print("UNKNOWN PVPMode[%d]" % (player.GetPKMode()))

		#if constInfo.PVPMODE_TEST_ENABLE:
		#	curPKMode = player.GetPKMode()
		#	alignment, grade = chr.testGetPKData()
		#	self.pkModeNameDict = { 0 : "PEACE", 1 : "REVENGE", 2 : "FREE", 3 : "PROTECT", }
		#	self.testPKMode.SetText("Current PK Mode : " + self.pkModeNameDict.get(curPKMode, "UNKNOWN"))
		#	self.testAlignment.SetText("Current Alignment : " + str(alignment) + " (" + localeInfo.TITLE_NAME_LIST[grade] + ")")

	###############################################################################################
	###############################################################################################
	## Game Callback Functions

	# Start
	def StartGame(self):
		if self.affectShower:
			self.affectShower.RefreshPenetrationOverflow()
		self.RefreshInventory()
		self.RefreshEquipment()
		self.RefreshCharacter()
		self.RefreshSkill()

		try:
			import uigameoptionnew
			uigameoptionnew.ApplyGraphicsConfig()
		except:
			dbg.TraceError("[Graphics] ApplyGraphicsConfig() failed at boot")

		try:
			import settingsbackend
			settingsbackend.load_tree_shadow()
		except:
			dbg.TraceError("[Graphics] tree shadow distance failed at boot")

		try:
			import settingsbackend
			settingsbackend.load_effect_switches()
		except:
			dbg.TraceError("[Graphics] effect switches failed at boot")

	if app.ENABLE_MAP_LOCATION_APP_NAME:
		def SetApplicationText(self):
			try:
				title = maparrivalnames.resolve(background.GetCurrentMapName())
				app.SetText(localeInfo.APP_TITLE + (" - " + title if title else ""))
			except:
				pass
			# Discord Rich Presence shows the same map title.
			if hasattr(net, "SetDiscordLocation"):
				try:
					net.SetDiscordLocation(title or "")
				except:
					pass

	# Refresh
	def CheckGameButton(self):
		if self.interface:
			self.interface.CheckGameButton()

	def RefreshAlignment(self):
		self.interface.RefreshAlignment()

	def __OnSkillTreePresentation(self, state, nodes):
		active = bool(state and state["enabled"] and state["remaining_seconds"] > 0)
		queue = nodes.get(2120, {}).get("current_total", 0) if active else 0
		weapon = nodes.get(2107, {}).get("current_total", 0) if active else 0
		player.SetSkillTreeBonuses(queue, weapon)
		itembonuspresentation.SetTalentWeaponPercent(weapon)
		# item tooltips show the real ore and dew time while the tree runs.
		jewelry = nodes.get(2124, {}).get("current_total", 0) if active else 0
		dew = nodes.get(2141, {}).get("current_total", 0) if active else 0
		itembonuspresentation.SetTalentDurationPercents(jewelry, dew)
		if self.interface and self.interface.wndDailyTasks:
			dailyBonus = nodes.get(2121, {}).get("current_total", 0) if active else 0
			self.interface.wndDailyTasks.SetCompletionLimit(3 + dailyBonus)
		if self.affectShower:
			members = [(key, node["current_total"]) for key, node in sorted(nodes.items())
				if key != 2000 and node["rank"] > 0] if active else []
			self.affectShower.SetSkillTreeState(state["remaining_seconds"] if active else 0, members)
		if self.interface:
			self.interface.RefreshStatus()

	def RefreshStatus(self):
		self.CheckGameButton()
		if self.affectShower and not self.seamlessWarping:
			self.affectShower.RefreshPenetrationOverflow()

		if self.interface:
			if getattr(app, "ENABLE_WIKI", False) and not self.seamlessWarping:
				self.interface.WarmWiki()
			self.interface.RefreshStatus()

		if self.playerGauge:
			self.playerGauge.RefreshGauge()

	def RefreshStamina(self):
		self.interface.RefreshStamina()

	def RefreshSkill(self):
		self.CheckGameButton()
		if self.interface:
			self.interface.RefreshSkill()
		if self.affectShower:
			# Skill affects show the skill window's tile of the current grade.
			self.affectShower.RefreshSkillIcons()

	def RefreshQuest(self):
		self.interface.RefreshQuest()

	def RefreshMessenger(self):
		self.interface.RefreshMessenger()

	def RefreshGuildInfoPage(self):
		self.interface.RefreshGuildInfoPage()

	def RefreshGuildBoardPage(self):
		self.interface.RefreshGuildBoardPage()

	def RefreshGuildMemberPage(self):
		self.interface.RefreshGuildMemberPage()

	def RefreshGuildMemberPageGradeComboBox(self):
		self.interface.RefreshGuildMemberPageGradeComboBox()

	def RefreshGuildSkillPage(self):
		self.interface.RefreshGuildSkillPage()

	def RefreshGuildGradePage(self):
		self.interface.RefreshGuildGradePage()

	def OnBlockMode(self, mode):
		self.interface.OnBlockMode(mode)

	if app.ENABLE_OFFLINE_SHOP:
		def OnShopDeco(self, iShopSkin, iShopBanner):
			osfInfo.SHOP_SKIN_VALUE = iShopSkin
			osfInfo.SHOP_BANNER_VALUE = iShopBanner
			for i in range(8):
				if 0 != (iShopSkin & (1 << i)):
					osfInfo.SHOP_SKIN_UNLOCKED[i] = True
				else:
					osfInfo.SHOP_SKIN_UNLOCKED[i] = False
					
			for i in range(5):
				if 0 != (iShopBanner & (1 << i)):
					osfInfo.SHOP_BANNER_UNLOCKED[i] = True
				else:
					osfInfo.SHOP_BANNER_UNLOCKED[i] = False

	def OpenQuestWindow(self, skin, idx):
		if osfInfo.INPUT_IGNORE == 1:
			return

		self.interface.OpenQuestWindow(skin, idx)

	def AskGuildName(self):
		if self.interface.OpenGuildCreation():
			return
		guildNameBoard = uiCommon.InputDialog()
		guildNameBoard.SetTitle(localeInfo.GUILD_NAME)
		guildNameBoard.SetAcceptEvent(ui.__mem_func__(self.ConfirmGuildName))
		guildNameBoard.SetCancelEvent(ui.__mem_func__(self.CancelGuildName))
		guildNameBoard.Open()

		self.guildNameBoard = guildNameBoard

	def ConfirmGuildName(self):
		guildName = self.guildNameBoard.GetText()
		if not guildName:
			return

		if net.IsInsultIn(guildName):
			self.PopupMessage(localeInfo.GUILD_CREATE_ERROR_INSULT_NAME)
			return

		net.SendAnswerMakeGuildPacket(guildName)
		self.guildNameBoard.Close()
		self.guildNameBoard = None
		return True

	def CancelGuildName(self):
		self.guildNameBoard.Close()
		self.guildNameBoard = None
		return True

	## Refine
	def PopupMessage(self, msg):
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, 0, localeInfo.UI_OK)

	def OpenRefineDialog(self, targetItemPos, nextGradeItemVnum, cost, prob, type, apply_random_list = None, src_vnum = 0, bonus = 0):
		self.interface.OpenRefineDialog(targetItemPos, nextGradeItemVnum, cost, prob, type, apply_random_list, src_vnum, bonus)

	def AppendMaterialToRefineDialog(self, vnum, count):
		self.interface.AppendMaterialToRefineDialog(vnum, count)

	def RunUseSkillEvent(self, slotIndex, coolTime):
		self.interface.OnUseSkill(slotIndex, coolTime)

	def ClearAffects(self):
		self.affectShower.ClearAffects()

	def SetAffect(self, affect):
		self.affectShower.SetAffect(affect)

	def ResetAffect(self, affect):
		self.affectShower.ResetAffect(affect)

	def BINARY_SetVipStatus(self, active, expires_at):
		self.affectShower.SetVipStatus(bool(active), int(expires_at))
		if self.interface:
			self.interface.SetQuickBuffVipStatus(bool(active))
		if app.ENABLE_SWITCHBOT_SYSTEM and self.interface:
			self.interface.RefreshSwitchbotWindow()

	# UNKNOWN_UPDATE
	def BINARY_NEW_AddAffect(self, type, pointIdx, value, duration):
		if self.interface:
			self.interface.OnQuickBuffAffectAdded(type, pointIdx, value, duration)
		try:
			self.affectShower.BINARY_NEW_AddAffect(type, pointIdx, value, duration)
			if chr.NEW_AFFECT_DRAGON_SOUL_DECK1 == type or chr.NEW_AFFECT_DRAGON_SOUL_DECK2 == type:
				self.interface.DragonSoulActivate(type - chr.NEW_AFFECT_DRAGON_SOUL_DECK1)
			elif chr.NEW_AFFECT_DRAGON_SOUL_QUALIFIED == type:
				self.BINARY_DragonSoulGiveQuilification()
			elif app.ENABLE_DS_SET and chr.NEW_AFFECT_DS_SET == type:
				self.interface.DragonSoulSetGrade(value)

			elif app.ENABLE_OFFLINE_SHOP and type == chr.AFFECT_OFFLINE_SHOP_DECORATION:
				osfInfo.IS_OFFLINE_SHOP_DECORATION = True
				osfInfo.OFFLINE_SHOP_DECORATION_UPDATE = True

			elif app.ENABLE_BRAVE_CAPE_RENEWAL and type == chr.NEW_AFFECT_BRAVE_CAPE:
				if self.interface:
					if self.interface.wndInventory:
						if self.interface.wndInventory.wndBraveCape:
							self.interface.wndInventory.wndBraveCape.LoadData()

			elif app.ENABLE_AUTO_PICKUP and type == chr.AFFECT_AUTO_PICKUP_ENABLED:
				osfInfo.AUTOPICKUP_ENABLED = True

			elif app.ENABLE_AUTO_PICKUP and type == chr.AFFECT_AUTO_PICKUP_DISABLED:
				osfInfo.AUTOPICKUP_ENABLED = False

		except:
			pass

	def BINARY_NEW_RemoveAffect(self, type, pointIdx):
		if self.interface:
			self.interface.OnQuickBuffAffectRemoved(type, pointIdx)
		self.affectShower.BINARY_NEW_RemoveAffect(type, pointIdx)
		if chr.NEW_AFFECT_DRAGON_SOUL_DECK1 == type or chr.NEW_AFFECT_DRAGON_SOUL_DECK2 == type:
			self.interface.DragonSoulDeactivate()
		elif app.ENABLE_DS_SET and chr.NEW_AFFECT_DS_SET == type:
			self.interface.DragonSoulSetGrade(0)

		elif app.ENABLE_OFFLINE_SHOP and type == chr.AFFECT_OFFLINE_SHOP_DECORATION:
			osfInfo.IS_OFFLINE_SHOP_DECORATION = False
			osfInfo.OFFLINE_SHOP_DECORATION_UPDATE = False

		elif app.ENABLE_AUTO_PICKUP and type == chr.AFFECT_AUTO_PICKUP_ENABLED:
			osfInfo.AUTOPICKUP_ENABLED = False

		elif app.ENABLE_AUTO_PICKUP and type == chr.AFFECT_AUTO_PICKUP_DISABLED:
			osfInfo.AUTOPICKUP_ENABLED = False

	# END_OF_UNKNOWN_UPDATE

	if app.ENABLE_SKILL_COOLTIME_UPDATE:
		def SkillClearCoolTime(self, slotIndex):
			self.interface.SkillClearCoolTime(slotIndex)

	def ActivateSkillSlot(self, slotIndex):
		if self.interface:
			self.interface.OnActivateSkill(slotIndex)

	def DeactivateSkillSlot(self, slotIndex):
		if self.interface:
			self.interface.OnDeactivateSkill(slotIndex)

	def RefreshEquipment(self):
		if self.interface:
			self.interface.RefreshInventory()

	def RefreshInventory(self):
		if self.interface:
			self.interface.RefreshInventory()
			if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
				self.interface.RefreshAutoPositionSlot()

	def RefreshCharacter(self):
		if self.interface:
			self.interface.RefreshCharacter()

	def OnGameOver(self):
		self.CloseTargetBoard()
		self.OpenRestartDialog()

	def OpenRestartDialog(self):
		self.interface.OpenRestartDialog()

	def ChangeCurrentSkill(self, skillSlotNumber):
		self.interface.OnChangeCurrentSkill(skillSlotNumber)

	## TargetBoard
	def SetPCTargetBoard(self, vid, name):
		if self.interface.IsHideUiMode == True:
			return

		self.targetBoard.Open(vid, name)

		if app.IsPressed(app.DIK_LCONTROL):
			if not player.IsSameEmpire(vid):
				return

			if player.IsMainCharacterIndex(vid):
				return
			elif chr.INSTANCE_TYPE_BUILDING == chr.GetInstanceType(vid):
				return

			self.interface.OpenWhisperDialog(name)

	def RefreshTargetBoardByVID(self, vid):
		# The native PVP packet refreshes both sides by VID: its flags drive
		# the duel rows of the chat and Messages (challenged / my request
		# waiting / fight / who won), see duelchallenge.Observe.
		try:
			if not player.IsMainCharacterIndex(vid):
				events = duelchallenge.challenges.Observe(vid, chr.GetNameByVID(vid),
					bool(player.IsChallengeInstance(vid)),
					bool(player.IsCantFightInstance(vid)),
					bool(player.IsRevengeInstance(vid)),
					bool(player.IsPVPInstance(vid)))
				if events and self.interface:
					self.interface.OnDuelEvents(events)
		except Exception as error:
			dbg.TraceError("duel state from the PVP packet failed: %s" % error)
		if self.targetBoard:
			self.targetBoard.RefreshByVID(vid)

	if getattr(app, "ENABLE_DPS_METER", False):
		def BINARY_DpsMeterSnapshot(self, victimVid, encounterId, flags, totalDamage, rows):
			if self.targetBoard:
				self.targetBoard.ApplyDpsMeterSnapshot(
					victimVid, encounterId, flags, totalDamage, rows
				)

	def RefreshTargetBoardByName(self, name):
		if self.targetBoard:
			self.targetBoard.RefreshByName(name)

	def __RefreshTargetBoard(self):
		if self.targetBoard:
			self.targetBoard.Refresh()

	if app.ENABLE_VIEW_TARGET_DECIMAL_HP:
		def SetHPTargetBoard(self, vid, hpPercentage, iMinHP, iMaxHP):
			if self.interface.IsHideUiMode == True:
				return

			if vid != self.targetBoard.GetTargetVID():
				if chr.GetInstanceType(vid) == chr.INSTANCE_TYPE_PLAYER:
					self.targetBoard.Open(vid, chr.GetNameByVID(vid))
				else:
					self.targetBoard.ResetTargetBoard()
					self.targetBoard.SetEnemyVID(vid)

			self.targetBoard.SetHP(hpPercentage, iMinHP, iMaxHP)
			self.targetBoard.Show()
	else:
		def SetHPTargetBoard(self, vid, hpPercentage):
			if self.interface.IsHideUiMode == True:
				return

			if vid != self.targetBoard.GetTargetVID():
				if chr.GetInstanceType(vid) == chr.INSTANCE_TYPE_PLAYER:
					self.targetBoard.Open(vid, chr.GetNameByVID(vid))
				else:
					self.targetBoard.ResetTargetBoard()
					self.targetBoard.SetEnemyVID(vid)

			self.targetBoard.SetHP(hpPercentage)
			self.targetBoard.Show()

	def CloseTargetBoardIfDifferent(self, vid):
		if vid != self.targetBoard.GetTargetVID():
			self.targetBoard.Close()

	def CloseTargetBoard(self):
		self.targetBoard.Close()

	if app.ENABLE_ELEMENT_ADD:
		def ShowTargetElementEnchant(self, element_enchants_dict):
			if self.targetBoard:
				self.targetBoard.ShowElementImg(element_enchants_dict)

	## View Equipment
	def OpenEquipmentDialog(self, vid):
		self.interface.OpenEquipmentDialog(vid)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def SetEquipmentDialogItem(self, vid, slotIndex, vnum, count, dwChangeLookVnum):
			self.interface.SetEquipmentDialogItem(vid, slotIndex, vnum, count, dwChangeLookVnum)
	else:
		def SetEquipmentDialogItem(self, vid, slotIndex, vnum, count):
			self.interface.SetEquipmentDialogItem(vid, slotIndex, vnum, count)

	def SetEquipmentDialogSocket(self, vid, slotIndex, socketIndex, value):
		self.interface.SetEquipmentDialogSocket(vid, slotIndex, socketIndex, value)

	def SetEquipmentDialogAttr(self, vid, slotIndex, attrIndex, type, value):
		self.interface.SetEquipmentDialogAttr(vid, slotIndex, attrIndex, type, value)

	if app.ENABLE_APPLY_RANDOM:
		def SetEquipmentDialogApplyRandom(self, vid, slotIndex, aApplyRandomIndex, type, value):
			self.interface.SetEquipmentDialogApplyRandom(vid, slotIndex, aApplyRandomIndex, type, value)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def SetEquipmentDialogRefineElement(self, vid, slotIndex, applyType, grade, values, bonusValues):
			self.interface.SetEquipmentDialogRefineElement(vid, slotIndex, applyType, grade, values, bonusValues)

	# SHOW_LOCAL_MAP_NAME
	def ShowMapName(self, mapName, x, y):
		if self.mapNameShower:
			self.mapNameShower.ShowMapName(mapName, x, y)

		if self.interface:
			self.interface.SetMapName(mapName)
	# END_OF_SHOW_LOCAL_MAP_NAME

	def BINARY_OpenAtlasWindow(self):
		self.interface.BINARY_OpenAtlasWindow()

	## Chat
	def OnRecvWhisper(self, mode, name, line):
		if mode == chat.WHISPER_TYPE_GM:
			self.interface.RegisterGameMasterName(name)
		chat.AppendWhisper(mode, name, line)
		# The executable imports chat/GM whispers into Unified Messenger history
		# and calls this only for lines it could not import. The text exists in
		# the native whisper buffer alone, so Messages keeps it for the session.
		self.interface.RecvLegacyWhisper(name, line, mode == chat.WHISPER_TYPE_GM)
		if app.ENABLE_DISCORD_STUFF:
			if self.interface:
				if self.interface.CheckWhisperIsOpen(name) == False:
					osfInfo.msgname = name

	def OnRecvWhisperSystemMessage(self, mode, name, line):
		if mode == chat.WHISPER_TYPE_SYSTEM and name == "[Switchbot]":
			from systemnotificationlocale import SwitchbotMessage, WithClientItemName
			line = WithClientItemName(line)
			if self.interface.PushSwitchbotSystemNotification(line):
				return
			line = SwitchbotMessage(line)
		if mode == chat.WHISPER_TYPE_SYSTEM and self.interface.RecvDuelChallenge(name, line):
			# A duel challenge is one chat line with [Přijmout] [Odmítnout]:
			# no whisper window and no Messages letter (it could be spammed).
			return
		chat.AppendWhisper(chat.WHISPER_TYPE_SYSTEM, name, line)
		# Other system whispers are not Messenger history; their letter opens
		# Messages with this line.
		self.interface.RecvLegacyWhisper(name, line)

	def OnRecvWhisperError(self, mode, name, line):
		if mode in localeInfo.WHISPER_ERROR:
			line = localeInfo.WHISPER_ERROR[mode](name)
		else:
			line = "Whisper Unknown Error(mode=%d, name=%s)" % (mode, name)
		chat.AppendWhisper(chat.WHISPER_TYPE_SYSTEM, name, line)
		self.interface.RecvLegacyWhisper(name, line)

	def RecvWhisper(self, name):
		self.interface.RecvWhisper(name)

	def BINARY_UnifiedMessengerCapability(self, enabled, pid, maxBody, pendingPerPair, pendingPerSender, retentionSeconds):
		if self.interface:
			self.interface.UnifiedMessengerCapability(enabled, pid, maxBody,
				pendingPerPair, pendingPerSender, retentionSeconds)

	def BINARY_UnifiedMessengerChanged(self, key, event):
		if self.interface:
			self.interface.UnifiedMessengerChanged(key, event)

	def BINARY_UnifiedMessengerPlayerLookupCapability(self, enabled):
		if self.interface:
			self.interface.UnifiedMessengerPlayerLookupCapability(enabled)

	def BINARY_UnifiedMessengerPlayerLookup(self, token, mode, status):
		if not self.interface:
			return
		rows = []
		try:
			count = min(int(net.GetUnifiedMessengerPlayerLookupCount()), 8)
			for index in range(count):
				pid, name = net.GetUnifiedMessengerPlayerLookupResult(index)
				rows.append((int(pid), str(name)))
		except:
			rows = []
		self.interface.UnifiedMessengerPlayerLookup(
			int(token), int(mode), int(status), tuple(rows))

	def BINARY_UnifiedMessengerSubmitResult(self, messageID, error):
		if self.interface:
			self.interface.UnifiedMessengerSubmitResult(messageID, error)

	def BINARY_UnifiedMessengerTyping(self, pid, name, active):
		if self.interface:
			self.interface.UnifiedMessengerTyping(pid, name, active)

	def BINARY_UnifiedMessengerRecovery(self, status):
		if self.interface:
			self.interface.UnifiedMessengerRecovery(status)

	if app.ENABLE_CHATTING_WINDOW_RENEWAL:
		def OnPickExp(self, value):
			# Keep the native callback compatible; EXP updates only the status bar.
			pass

	def OnPickMoney(self, money):
		if app.ENABLE_DROP_INFO_WINDOW:
			self.RecvDropInfo(1, money)
		else:
			if app.ENABLE_CHATTING_WINDOW_RENEWAL:
				chat.AppendChat(chat.CHAT_TYPE_MONEY_INFO, localeInfo.GAME_PICK_MONEY % (money))
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GAME_PICK_MONEY % (money))

	if app.ENABLE_GEM_SYSTEM:
		def OnPickGem(self, gem):
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GEM_SYSTEM_PICK_GEM % (gem))

		def OpenGuiGem(self):
			self.interface.OpenGuiGem()

		def GemCheck(self):
			self.interface.GemCheck()

		def OpenGuiGemMarket(self):
			self.interface.OpenGuiGemMarket()

		def GemMarketItems(self, vnums, gem, count):
			self.interface.GemMarketItems(vnums, gem, count)

		def GemMarketSlotsDesblock(self, slot0, slot1, slot2, slot3, slot4, slot5):
			self.interface.GemMarketSlotsDesblock(slot0, slot1, slot2, slot3, slot4, slot5)

		def GemMarketClear(self):
			self.interface.GemMarketClear()

		def GemTimeMarket(self, time):
			self.interface.GemTime(time)

	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		def OpenSpecialInventoryWindow(self, category):
			self.interface.OpenSpecialInventoryWindow(int(category))

	def OpenCostumeWindow(self):
		# Equipment notifications can arrive after warp UI restoration.
		# Refresh slots without overriding the player's tab or window visibility.
		self.RefreshEquipment()

	def OpenInventoryWindow(self):
		self.interface.OpenInventoryWindow()

	def OpenTeleportAtlas(self):
		self.interface.OpenTeleportAtlas()

	if app.ENABLE_MOVE_CHANNEL:
		# 2019.09.03.owsap - Load server info (server name)
		def __LoadChannelInfo(self):
			try:
				file = open("UserData/channel.inf")
				lines = file.readlines()

				if len(lines) > 0:
					tokens = lines[0].split()

					selServerID = int(tokens[0])
					selChannelID = int(tokens[1])

					if len(tokens) == 3:
						regionID = int(tokens[2])

					return regionID, selServerID, selChannelID
			except:
				print("GameWindow.__LoadChannelInfo - OpenError")
				return -1, -1, -1

		def ChannelInfo(self, channelNumber, mapIndex):
			try:
				_chNum = int(str(channelNumber).strip())
				_mapIdx = int(str(mapIndex).strip())
			except (TypeError, ValueError):
				dbg.TraceError(
					"ChannelInfo: invalid channel/map payload %r %r"
					% (channelNumber, mapIndex)
				)
				return

			is_global_hub = globalhub.IsGlobalHub(_chNum, _mapIdx)

			if is_global_hub:
				chat.AppendChat(
					chat.CHAT_TYPE_INFO,
					localeInfo.GLOBAL_HUB_ENTER_NOTICE
				)
			elif _chNum == 99 or _mapIdx >= 10000:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MOVE_CHANNEL_NOTICE % 0)
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MOVE_CHANNEL_NOTICE % _chNum)

			net.SetChannelNumber(_chNum) # 2019.09.02.owsap
			net.SetMapIndex(_mapIdx)

			# 2019.09.02.owsap - update server info
			import serverInfo
			loadRegionID, loadServerID, loadChannelID = self.__LoadChannelInfo()
			try:
				server_data = serverInfo.REGION_DICT[loadRegionID][loadServerID]
				_svName = server_data["name"]
				_chName = server_data["channel"]
			except (KeyError, TypeError):
				dbg.TraceError(
					"ChannelInfo: missing configured server region=%d server=%d"
					% (loadRegionID, loadServerID)
				)
				_svName = net.GetServerInfo().split(",", 1)[0].strip()
				_chName = {}

			if is_global_hub:
				channel_label = localeInfo.GLOBAL_HUB_NAME
			elif _chNum == 99:
				channel_label = "CH99"
			else:
				channel_data = _chName.get(_chNum, {})
				channel_label = channel_data.get(
					"name", "CH%d" % _chNum
				)
			net.SetServerInfo(
				("%s, %s" % (_svName, channel_label)).strip(", ")
			)

			self.interface.RefreshServerInfo()

	if app.ENABLE_EXPRESSING_EMOTION:
		def ClearSpecialEmotions(self):
			osfInfo.EXPRESSING_EMOTIONS = {}
			self.interface.ClearSpecialEmotions()

		def RegisterSpecialEmotion(self, emotionIdx, leftTime, notice):
			emotionIdx, leftTime, notice = int(emotionIdx), int(leftTime), int(notice)
			self.interface.RegisterSpecialEmotions(emotionIdx, leftTime)

			if notice != 0:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.OPEN_THE_SPECIAL_ACTION_KIT % osfInfo.GET_SPECIAL_EMOTION_NAME(emotionIdx))

	if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
		def IsAFKMode(self, qid):
			osfInfo.AFKMode = int(qid)

		def ShowCaptcha(self, timeLeft):
			self.interface.ShowCaptcha(int(timeLeft))

	def OnShopError(self, type):
		try:
			self.PopupMessage(localeInfo.SHOP_ERROR_DICT[type])
		except KeyError:
			self.PopupMessage(localeInfo.SHOP_ERROR_UNKNOWN % (type))

	def OnSafeBoxError(self):
		self.PopupMessage(localeInfo.SAFEBOX_ERROR)

	def OnFishingSuccess(self, isFish, fishName):
		# The catch arrives as a tracker row whose line has the count.
		if self.interface and self.interface.IsDropTrackerGatherClient():
			return
		chat.AppendChatWithDelay(chat.CHAT_TYPE_INFO, localeInfo.FISHING_SUCCESS(isFish, fishName), 2000)

	# ADD_FISHING_MESSAGE
	def OnFishingNotifyUnknown(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.FISHING_UNKNOWN)

	def OnFishingWrongPlace(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.FISHING_WRONG_PLACE)
	# END_OF_ADD_FISHING_MESSAGE

	def OnFishingNotify(self, isFish, fishName):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.FISHING_NOTIFY(isFish, fishName))

	def OnFishingFailure(self):
		chat.AppendChatWithDelay(chat.CHAT_TYPE_INFO, localeInfo.FISHING_FAILURE, 2000)

	def OnCannotPickItem(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GAME_CANNOT_PICK_ITEM)

	# MINING
	def OnCannotMining(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GAME_CANNOT_MINING)
	# END_OF_MINING

	def OnCannotUseSkill(self, vid, type):
		if type in localeInfo.USE_SKILL_ERROR_TAIL_DICT:
			textTail.RegisterInfoTail(vid, localeInfo.USE_SKILL_ERROR_TAIL_DICT[type])

		if type in localeInfo.USE_SKILL_ERROR_CHAT_DICT:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.USE_SKILL_ERROR_CHAT_DICT[type])

	def OnCannotShotError(self, vid, type):
		textTail.RegisterInfoTail(vid, localeInfo.SHOT_ERROR_TAIL_DICT.get(type, localeInfo.SHOT_ERROR_UNKNOWN % (type)))

	## PointReset
	def StartPointReset(self):
		self.interface.OpenPointResetDialog()

	## Shop
	if app.ENABLE_COMBAT_ZONE:
		def StartShop(self, vid, points, curLimit, maxLimit):
			self.interface.OpenShopDialog(vid, points, curLimit, maxLimit)
	else:
		def StartShop(self, vid, *_legacyCombatZoneArgs):
			self.interface.OpenShopDialog(vid)

	def EndShop(self):
		self.interface.CloseShopDialog()

	def RefreshShop(self):
		self.interface.RefreshShopDialog()

	def SetShopSellingPrice(self, Price):
		pass

	## Exchange
	def StartExchange(self):
		self.interface.StartExchange()

	def EndExchange(self):
		self.interface.EndExchange()

	def RefreshExchange(self):
		self.interface.RefreshExchange()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def AddExchangeItemSlotIndex(self, idx):
			self.interface.AddExchangeItemSlotIndex(idx)

	## Party
	# 파티 가입 제한 시간때문에 수정.
	if app.WJ_NEW_USER_CARE:
		def RecvPartyInviteQuestion(self, leaderVID, leaderName):
			partyInviteQuestionDialog = uiCommon.QuestionDialogWithTimeLimit()
			partyInviteQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerPartyInvite(arg))
			partyInviteQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerPartyInvite(arg))
			partyInviteQuestionDialog.Open(leaderName + localeInfo.PARTY_DO_YOU_JOIN, 10)
			partyInviteQuestionDialog.SetTimeOverMsg(localeInfo.PARTY_ANSWER_TIMEOVER)
			partyInviteQuestionDialog.SetCancelOnTimeOver()
			partyInviteQuestionDialog.partyLeaderVID = leaderVID
			self.partyInviteQuestionDialog = partyInviteQuestionDialog
	else:
		def RecvPartyInviteQuestion(self, leaderVID, leaderName):
			partyInviteQuestionDialog = uiCommon.QuestionDialog()
			partyInviteQuestionDialog.SetText(leaderName + localeInfo.PARTY_DO_YOU_JOIN)
			partyInviteQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerPartyInvite(arg))
			partyInviteQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerPartyInvite(arg))
			partyInviteQuestionDialog.Open()
			partyInviteQuestionDialog.partyLeaderVID = leaderVID
			self.partyInviteQuestionDialog = partyInviteQuestionDialog

	def AnswerPartyInvite(self, answer):
		if not self.partyInviteQuestionDialog:
			return

		partyLeaderVID = self.partyInviteQuestionDialog.partyLeaderVID

		# 파티가입에 대한 거리 제한 삭제.
		if not app.WJ_NEW_USER_CARE:
			distance = player.GetCharacterDistance(partyLeaderVID)
			if distance < 0.0 or distance > 5000:
				answer = False

		net.SendPartyInviteAnswerPacket(partyLeaderVID, answer)

		self.partyInviteQuestionDialog.Close()
		self.partyInviteQuestionDialog = None

	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def AddPartyMember(self, pid, name, mapIdx, channel):
			self.interface.AddPartyMember(pid, name, mapIdx, channel)
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def AddPartyMember(self, pid, name, mapIdx):
			self.interface.AddPartyMember(pid, name, mapIdx)
	else:
		def AddPartyMember(self, pid, name):
			self.interface.AddPartyMember(pid, name)

	def UpdatePartyMemberInfo(self, pid):
		self.interface.UpdatePartyMemberInfo(pid)

	def RemovePartyMember(self, pid):
		self.interface.RemovePartyMember(pid)
		self.__RefreshTargetBoard()

	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def LinkPartyMember(self, pid, vid, mapIdx, channel):
			self.interface.LinkPartyMember(pid, vid, mapIdx, channel)
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def LinkPartyMember(self, pid, vid, mapIdx):
			self.interface.LinkPartyMember(pid, vid, mapIdx)
	else:
		def LinkPartyMember(self, pid, vid):
			self.interface.LinkPartyMember(pid, vid)

	def UnlinkPartyMember(self, pid):
		self.interface.UnlinkPartyMember(pid)

	def UnlinkAllPartyMember(self):
		self.interface.UnlinkAllPartyMember()

	def ExitParty(self):
		self.interface.ExitParty()
		self.RefreshTargetBoardByVID(self.targetBoard.GetTargetVID())

	def ChangePartyParameter(self, distributionMode):
		self.interface.ChangePartyParameter(distributionMode)

	## Messenger
	def OnMessengerAddFriendQuestion(self, name):
		if name.startswith("h:"):
			try:
				name = bytes.fromhex(name[2:]).decode("utf-8", "strict")
			except (ValueError, UnicodeError):
				return
		if not name or name in self.pendingFriendRequests:
			return
		if self.messengerAddFriendQuestion and self.messengerAddFriendQuestion.name == name:
			return
		# Match the server's bounded pending queue. Never replace an unanswered dialog.
		if len(self.pendingFriendRequests) >= 32:
			net.SendChatPacket("/messenger_auth n h:" + name.encode("utf-8").hex())
			return
		self.pendingFriendRequests.append(name)
		self.__ShowNextFriendRequest()

	def __ShowNextFriendRequest(self):
		if self.messengerAddFriendQuestion or not self.pendingFriendRequests:
			return
		interface = getattr(self, "interface", None)
		if interface and getattr(interface, "wndQuestWindow", None):
			# Quest windows may lock input. Keep the invitation until they close.
			return
		name = self.pendingFriendRequests.pop(0)
		dialog = uiCommon.QuestionDialog2()
		dialog.name = name
		dialog.SetText1(localeInfo.MESSENGER_DO_YOU_ACCEPT_ADD_FRIEND_1 % (name))
		dialog.SetText2(localeInfo.MESSENGER_DO_YOU_ACCEPT_ADD_FRIEND_2)
		accept = ui.__mem_func__(self.OnAcceptAddFriend)
		deny = ui.__mem_func__(self.OnDenyAddFriend)
		dialog.SetAcceptEvent(lambda: accept(name))
		dialog.SetCancelEvent(lambda: deny(name))
		self.messengerAddFriendQuestion = dialog
		dialog.Open()

	def OnAcceptAddFriend(self, expectedName=None):
		dialog = self.messengerAddFriendQuestion
		if dialog and (expectedName is None or dialog.name == expectedName):
			net.SendChatPacket("/messenger_auth y h:" + dialog.name.encode("utf-8").hex())
			self.OnCloseAddFriendQuestionDialog()
		return True

	def OnDenyAddFriend(self, expectedName=None):
		dialog = self.messengerAddFriendQuestion
		if dialog and (expectedName is None or dialog.name == expectedName):
			net.SendChatPacket("/messenger_auth n h:" + dialog.name.encode("utf-8").hex())
			self.OnCloseAddFriendQuestionDialog()
		return True

	def OnCloseAddFriendQuestionDialog(self):
		if self.messengerAddFriendQuestion:
			self.messengerAddFriendQuestion.Close()
		self.messengerAddFriendQuestion = None
		self.__ShowNextFriendRequest()
		return True

	def __ClearFriendRequests(self):
		self.pendingFriendRequests = []
		if self.messengerAddFriendQuestion:
			self.messengerAddFriendQuestion.Close()
		self.messengerAddFriendQuestion = None

	## SafeBox
	def OpenSafeboxWindow(self, size):
		self.interface.OpenSafeboxWindow(size)

	def RefreshSafebox(self):
		self.interface.RefreshSafebox()

	def RefreshSafeboxMoney(self):
		self.interface.RefreshSafeboxMoney()

	# ITEM_MALL
	def OpenMallWindow(self, size):
		self.interface.OpenMallWindow(size)

	def RefreshMall(self):
		self.interface.RefreshMall()
	# END_OF_ITEM_MALL

	## Guild
	def RecvGuildInviteQuestion(self, guildID, guildName):
		guildInviteQuestionDialog = uiCommon.QuestionDialog()
		guildInviteQuestionDialog.SetText(guildName + localeInfo.GUILD_DO_YOU_JOIN)
		guildInviteQuestionDialog.SetAcceptEvent(lambda arg=True: self.AnswerGuildInvite(arg))
		guildInviteQuestionDialog.SetCancelEvent(lambda arg=False: self.AnswerGuildInvite(arg))
		guildInviteQuestionDialog.Open()
		guildInviteQuestionDialog.guildID = guildID
		self.guildInviteQuestionDialog = guildInviteQuestionDialog

	def AnswerGuildInvite(self, answer):
		if not self.guildInviteQuestionDialog:
			return

		guildLeaderVID = self.guildInviteQuestionDialog.guildID
		net.SendGuildInviteAnswerPacket(guildLeaderVID, answer)

		self.guildInviteQuestionDialog.Close()
		self.guildInviteQuestionDialog = None

	def DeleteGuild(self):
		self.interface.DeleteGuild()

	## Clock
	def ShowClock(self, second):
		self.interface.ShowClock(second)

	def HideClock(self):
		self.interface.HideClock()

	## Emotion
	def BINARY_ActEmotion(self, emotionIndex):
		if self.interface.wndCharacter:
			self.interface.wndCharacter.ActEmotion(emotionIndex)

	###############################################################################################
	###############################################################################################
	## Keyboard Functions

	def CheckFocus(self):
		if False == self.IsFocus():
			if True == self.interface.IsOpenChat():
				self.interface.ToggleChat()

			self.SetFocus()

	def SaveScreen(self):
		grp.SaveScreenShotToPath()

	def ShowConsole(self):
		if debugInfo.IsDebugMode() or True == self.consoleEnable or osfInfo.IsDebugMode():
			player.EndKeyWalkingImmediately()
			self.console.OpenWindow()

	def ShowName(self):
		self.ShowNameFlag = True
		self.playerGauge.EnableShowAlways()
		player.SetQuickPage(self.quickSlotPageIndex + 1)

	# ADD_ALWAYS_SHOW_NAME
	def __IsShowName(self):
		if systemSetting.IsAlwaysShowName():
			return True

		if self.ShowNameFlag:
			return True

		return False
	# END_OF_ADD_ALWAYS_SHOW_NAME

	if app.ENABLE_OFFLINE_SHOP:
		uiOfflineShop.GetOfflineShopManager().OnUpdate()

	def HideName(self):
		self.ShowNameFlag = False
		self.playerGauge.DisableShowAlways()
		player.SetQuickPage(self.quickSlotPageIndex)

	def ShowMouseImage(self):
		self.interface.ShowMouseImage()

	def HideMouseImage(self):
		self.interface.HideMouseImage()

	def StartAttack(self):
		if self.__StartMiningOnTargetVein():
			return
		player.SetAttackKeyState(True)

	def __StartMiningOnTargetVein(self):
		# Space (the attack key) with a pick in hand and a mining vein as the target starts the mining the way a
		# click on the vein does (the same click packet, like Space by a tree starts woodcutting in the client).
		# The veins are servergamedata.MINING_VEINS (share/conf/mining_v1.json), the pick is ITEM_TYPE_PICK as on
		# the server. The keyboard is edge-polled: one press is one request, a held key never repeats it; the server
		# keeps a running session at the same vein, checks the distance and runs the skill check and its tempo.
		vid = player.GetTargetVID()
		if not vid or chr.GetVirtualNumber(vid) not in servergamedata.MINING_VEINS:
			return False
		weapon = player.GetItemIndex(player.EQUIPMENT, item.EQUIPMENT_WEAPON)
		if not weapon:
			return False
		item.SelectItem(weapon)
		if item.GetItemType() != item.ITEM_TYPE_PICK:
			return False
		if player.IsMountingHorse():
			self.OnCannotMining()
			return True
		net.SendOnClickPacket(vid)
		return True

	def EndAttack(self):
		player.SetAttackKeyState(False)

	def MoveUp(self):
		player.SetSingleDIKKeyState(app.DIK_UP, True)

	def MoveDown(self):
		player.SetSingleDIKKeyState(app.DIK_DOWN, True)

	def MoveLeft(self):
		player.SetSingleDIKKeyState(app.DIK_LEFT, True)

	def MoveRight(self):
		player.SetSingleDIKKeyState(app.DIK_RIGHT, True)

	def StopUp(self):
		player.SetSingleDIKKeyState(app.DIK_UP, False)

	def StopDown(self):
		player.SetSingleDIKKeyState(app.DIK_DOWN, False)

	def StopLeft(self):
		player.SetSingleDIKKeyState(app.DIK_LEFT, False)

	def StopRight(self):
		player.SetSingleDIKKeyState(app.DIK_RIGHT, False)

	def PickUpItem(self):
		manager = uiOfflineShop.GetOfflineShopManager()
		if manager.IsShow():
			manager.HideAllWindows()
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			interface.CloseShopBuildWindow()
		player.PickAllCloseItems()

	if app.ENABLE_QUICK_PICKUP:
		def PickupSpecial(self):
			manager = uiOfflineShop.GetOfflineShopManager()
			if manager.IsShow():
				manager.HideAllWindows()

			interface = osfInfo.GetInterfaceInstance()
			if interface:
				interface.CloseShopBuildWindow()

			if osfInfo.PICKUP_MODE == 1:
				player.PickAllCloseItems()
			else:
				player.PickCloseItem()
		
		def PickUpAllItems(self):
			player.PickAllCloseItems()

	###############################################################################################
	###############################################################################################
	## Event Handler

	def OnKeyDown(self, key):
		if self.__IsWarpInputLocked():
			return True
		if self.__IsInputGuardLocked():
			return True

		if self.interface.wndWeb and self.interface.wndWeb.IsShow():
			return

		if self.keybindingManager and self.keybindingManager.is_capture_active():
			return True

		# The arrows / WASD while the woodcutting bar is up are the directions of its strikes, not a step
		# (a step would cancel the cut): taken before the keybindings and the movement keys.
		if self.interface and getattr(self.interface, 'MinigameDirectionKey', lambda key: False)(key):
			return True

		if self.keybindingManager and self.keybindingManager.dispatch_key_down(key):
			return True

		# Space while a minigame quick-time event is up (the mining ring, the fishing game) is its hit, not an attack.
		if key == app.DIK_SPACE and self.interface.MinigameSpaceHit():
			return True

		# Native OnKeyDown dispatches OnPressEscapeKey first. The top dialog
		# owns cancellation; a second cancel here would also close its parent.
		try:
			self.onPressKeyDict[key]()
		except KeyError:
			pass
		except:
			raise

		return True

	def OnKeyUp(self, key):
		if self.keybindingManager:
			self.keybindingManager.release_key(key)

		# the key up of an arrow / WASD the woodcutting bar took: it never started a step
		if self.interface and getattr(self.interface, 'MinigameDirectionKeyUp', lambda key: False)(key):
			return True

		if self.onClickKeyDict:
			try:
				self.onClickKeyDict[key]()
			except KeyError:
				pass
			except:
				raise

		return True

	def OnMouseLeftButtonDown(self):
		if self.__IsInputGuardLocked():
			return True

		if self.interface.BUILD_OnMouseLeftButtonDown():
			return

		if mouseModule.mouseController.isAttached():
			self.CheckFocus()
		else:
			hyperlink = ui.GetHyperlink()
			if hyperlink:
				return
			else:
				self.CheckFocus()
				player.SetMouseState(player.MBT_LEFT, player.MBS_PRESS);

		return True

	def OnMouseLeftButtonUp(self):
		if self.interface:
			if self.interface.BUILD_OnMouseLeftButtonUp():
				return

		if mouseModule.mouseController.isAttached():
			# A split stack from a special tab carries its global INVENTORY cell.
			attachedType = slotwindowpolicy.NormalizeSlotType(mouseModule.mouseController.GetAttachedType())
			attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()
			attachedItemSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemCount = mouseModule.mouseController.GetAttachedItemCount()

			## QuickSlot
			if player.SLOT_TYPE_QUICK_SLOT == attachedType:
				player.RequestDeleteGlobalQuickSlot(attachedItemSlotPos)

			## picked up from the Instaswitchbot slot: like an item picked up from a switchbot slot, the
			## ground / a character does nothing (no drop or destroy question, no exchange); the item stays put
			elif getattr(getattr(mouseModule.mouseController, 'GetAttachedOwner', lambda: None)(),
					'KEEPS_ITEM_ON_GROUND_DROP', False):
				pass

			## Inventory
			elif player.SLOT_TYPE_INVENTORY == attachedType:
				if player.ITEM_MONEY == attachedItemIndex:
					# Note : 인벤 돈 셋팅 후, 다른 유저 클릭하면 들어오는 함수
					self.__PutMoney(attachedType, attachedItemCount, self.PickingCharacterIndex)
				else:
					self.__PutItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount, self.PickingCharacterIndex)

			## DragonSoul
			elif player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedType:
				self.__PutItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount, self.PickingCharacterIndex)

			## Aura System
			elif app.ENABLE_AURA_SYSTEM and player.SLOT_TYPE_AURA == attachedType:
				self.__PutItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount, self.PickingCharacterIndex)

			elif app.ENABLE_AUTOMATIC_HUNTING_SYSTEM and player.SLOT_TYPE_AUTO == attachedType:
				if not self.interface.GetAutoStartonoff() == True:
					if attachedItemSlotPos <= player.AUTO_SKILL_SLOT_MAX:
						player.SetAutoSkillSlotIndex(attachedItemSlotPos, 0)
						self.interface.RefreshAutoSkillSlot()
					else:
						player.SetAutoPositionSlotIndex(attachedItemSlotPos, player.ITEM_SLOT_COUNT)
						self.interface.RefreshAutoPositionSlot()

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if player.SLOT_TYPE_CHANGE_LOOK == attachedType:
					self.__PutItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount, self.PickingCharacterIndex)

			mouseModule.mouseController.DeattachObject()
		else:
			hyperlink = ui.GetHyperlink()
			if hyperlink:
				if app.IsPressed(app.DIK_LALT):
					link = chat.GetLinkFromHyperlink(hyperlink)
					#ime.PasteString(link)
				else:
					self.interface.MakeHyperlinkTooltip(hyperlink)
				return
			else:
				player.SetMouseState(player.MBT_LEFT, player.MBS_CLICK)

		# player.EndMouseWalking()
		return True

	def __PutItem(self, attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount, dstChrID):
		attachedType = slotwindowpolicy.NormalizeSlotType(attachedType)
		if player.SLOT_TYPE_INVENTORY == attachedType or player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedType:

			attachedInvenType = slotwindowpolicy.ItemWindowForSlotType(attachedType)
			if True == chr.HasInstance(self.PickingCharacterIndex) and player.GetMainCharacterIndex() != dstChrID:
				if player.IsEquipmentSlot(attachedItemSlotPos) and player.SLOT_TYPE_DRAGON_SOUL_INVENTORY != attachedType:
					self.stream.popupWindow.Close()
					self.stream.popupWindow.Open(localeInfo.EXCHANGE_FAILURE_EQUIP_ITEM, 0, localeInfo.UI_OK)
				else:
					if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
						if chr.IsNPC(dstChrID) or chr.IsStone(dstChrID):
							if app.ENABLE_AUTO_REFINE:
								osfInfo.AUTO_REFINE_TYPE = 2
								osfInfo.AUTO_REFINE_DATA["NPC"][0] = dstChrID
								osfInfo.AUTO_REFINE_DATA["NPC"][1] = attachedInvenType
								osfInfo.AUTO_REFINE_DATA["NPC"][2] = attachedItemSlotPos
								osfInfo.AUTO_REFINE_DATA["NPC"][3] = attachedItemCount
							net.SendGiveItemPacket(dstChrID, attachedInvenType, attachedItemSlotPos, attachedItemCount)
						else:
							net.SendExchangeStartPacket(dstChrID)
							net.SendExchangeItemAddPacket(attachedInvenType, attachedItemSlotPos, 0)
					else:
						if chr.IsNPC(dstChrID):
							net.SendGiveItemPacket(dstChrID, attachedInvenType, attachedItemSlotPos, attachedItemCount)
						else:
							net.SendExchangeStartPacket(dstChrID)
							net.SendExchangeItemAddPacket(attachedInvenType, attachedItemSlotPos, 0)
			else:
				self.__DropItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount)

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.SLOT_TYPE_CHANGE_LOOK == attachedType:
				self.__DropItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount)

		if app.ENABLE_AURA_SYSTEM and player.SLOT_TYPE_AURA == attachedType:
			self.__DropItem(attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount)

	def __PutMoney(self, attachedType, attachedMoney, dstChrID):
		if True == chr.HasInstance(dstChrID) and player.GetMainCharacterIndex() != dstChrID:
			net.SendExchangeStartPacket(dstChrID)
			net.SendExchangeElkAddPacket(attachedMoney)
		else:
			self.__DropMoney(attachedType, attachedMoney)

	def __DropMoney(self, attachedType, attachedMoney):
		# PRIVATESHOP_DISABLE_ITEM_DROP - 개인상점 열고 있는 동안 아이템 버림 방지
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_ITEM_FAILURE_PRIVATE_SHOP)
			return
		# END_OF_PRIVATESHOP_DISABLE_ITEM_DROP

		if attachedMoney >= 1000:
			self.stream.popupWindow.Close()
			self.stream.popupWindow.Open(localeInfo.DROP_MONEY_FAILURE_1000_OVER, 0, localeInfo.UI_OK)
			return

		itemDropQuestionDialog = uiCommon.QuestionDialog()
		itemDropQuestionDialog.SetText(localeInfo.DO_YOU_DROP_MONEY % (attachedMoney))
		itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
		itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
		itemDropQuestionDialog.Open()
		itemDropQuestionDialog.dropType = attachedType
		itemDropQuestionDialog.dropCount = attachedMoney
		itemDropQuestionDialog.dropNumber = player.ITEM_MONEY
		self.itemDropQuestionDialog = itemDropQuestionDialog

	def __DropItem(self, attachedType, attachedItemIndex, attachedItemSlotPos, attachedItemCount):
		if self.itemDestroyPending is not None or self.itemDestroyConfirmDialog:
			return
		attachedType = slotwindowpolicy.NormalizeSlotType(attachedType)
		# PRIVATESHOP_DISABLE_ITEM_DROP - 개인상점 열고 있는 동안 아이템 버림 방지
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_ITEM_FAILURE_PRIVATE_SHOP)
			return
		# END_OF_PRIVATESHOP_DISABLE_ITEM_DROP

		if app.ENABLE_CAPTCHA_NEW:
			if attachedItemIndex == -3:
				mouseModule.mouseController.DeattachObject()
				return

		if player.SLOT_TYPE_INVENTORY == attachedType and player.IsEquipmentSlot(attachedItemSlotPos):
			self.stream.popupWindow.Close()
			self.stream.popupWindow.Open(localeInfo.DROP_ITEM_FAILURE_EQUIP_ITEM, 0, localeInfo.UI_OK)

		else:
			if player.SLOT_TYPE_INVENTORY == attachedType:
				dropItemIndex = player.GetItemIndex(attachedItemSlotPos)

				item.SelectItem(dropItemIndex)
				dropItemName = item.GetItemName()

				## Question Text
				questionText = localeInfo.HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, attachedItemCount)

				## Dialog
				if app.ENABLE_NEW_DROP_DIALOG:
					itemDropQuestionDialog = uiCommon.QuestionDropDialog()
					itemDropQuestionDialog.SetText(questionText)
					itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
					itemDropQuestionDialog.SetDestroyEvent(lambda arg=True: self.RequestDestroyItem(arg))
					itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
					itemDropQuestionDialog.SetItemSlot(attachedItemSlotPos)
					itemDropQuestionDialog.Open()
					itemDropQuestionDialog.dropType = attachedType
					itemDropQuestionDialog.dropNumber = attachedItemSlotPos
					itemDropQuestionDialog.dropCount = attachedItemCount
					itemDropQuestionDialog.dropVnum = dropItemIndex
					itemDropQuestionDialog.itemSignature = self.__DestroyItemSignature(attachedItemSlotPos)
					self.itemDropQuestionDialog = itemDropQuestionDialog
				else:
					itemDropQuestionDialog = uiCommon.QuestionDialog()
					itemDropQuestionDialog.SetText(questionText)
					itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
					itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
					itemDropQuestionDialog.Open()
					itemDropQuestionDialog.dropType = attachedType
					itemDropQuestionDialog.dropNumber = attachedItemSlotPos
					itemDropQuestionDialog.dropCount = attachedItemCount
					self.itemDropQuestionDialog = itemDropQuestionDialog

				constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

			elif player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == attachedType:
				dropItemIndex = player.GetItemIndex(player.DRAGON_SOUL_INVENTORY, attachedItemSlotPos)

				item.SelectItem(dropItemIndex)
				dropItemName = item.GetItemName()

				## Question Text
				questionText = localeInfo.HOW_MANY_ITEM_DO_YOU_DROP(dropItemName, attachedItemCount)

				## Dialog
				itemDropQuestionDialog = uiCommon.QuestionDialog()
				itemDropQuestionDialog.SetText(questionText)
				itemDropQuestionDialog.SetAcceptEvent(lambda arg=True: self.RequestDropItem(arg))
				itemDropQuestionDialog.SetCancelEvent(lambda arg=False: self.RequestDropItem(arg))
				itemDropQuestionDialog.Open()
				itemDropQuestionDialog.dropType = attachedType
				itemDropQuestionDialog.dropNumber = attachedItemSlotPos
				itemDropQuestionDialog.dropCount = attachedItemCount
				self.itemDropQuestionDialog = itemDropQuestionDialog

				constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if player.SLOT_TYPE_CHANGE_LOOK == attachedType:
					net.SendChangeLookCheckOut(attachedItemSlotPos)

			if app.ENABLE_AURA_SYSTEM and player.SLOT_TYPE_AURA == attachedType:
				net.SendAuraRefineCheckOut(attachedItemSlotPos, player.GetAuraRefineWindowType())

	def RequestDropItem(self, answer):
		if not self.itemDropQuestionDialog:
			return

		if answer:
			dropType = slotwindowpolicy.NormalizeSlotType(self.itemDropQuestionDialog.dropType)
			dropCount = self.itemDropQuestionDialog.dropCount
			dropNumber = self.itemDropQuestionDialog.dropNumber

			if player.SLOT_TYPE_INVENTORY == dropType:
				if dropNumber == player.ITEM_MONEY:
					net.SendGoldDropPacketNew(dropCount)
					snd.PlaySound("sound/ui/money.wav")
				else:
					# PRIVATESHOP_DISABLE_ITEM_DROP
					self.__SendDropItemPacket(dropNumber, dropCount)
					# END_OF_PRIVATESHOP_DISABLE_ITEM_DROP

			elif player.SLOT_TYPE_DRAGON_SOUL_INVENTORY == dropType:
					# PRIVATESHOP_DISABLE_ITEM_DROP
					self.__SendDropItemPacket(dropNumber, dropCount, player.DRAGON_SOUL_INVENTORY)
					# END_OF_PRIVATESHOP_DISABLE_ITEM_DROP

		self.itemDropQuestionDialog.Close()
		self.itemDropQuestionDialog = None

		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	if app.ENABLE_NEW_DROP_DIALOG:
		def __DestroyItemSignature(self, slot):
			return (
				player.GetItemIndex(player.INVENTORY, slot),
				player.GetItemCount(player.INVENTORY, slot),
				tuple(player.GetItemMetinSocket(player.INVENTORY, slot, i)
					for i in range(player.METIN_SOCKET_MAX_NUM)),
				tuple(player.GetItemAttribute(player.INVENTORY, slot, i)
					for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)),
			)

		def RequestDestroyItem(self, answer):
			if not self.itemDropQuestionDialog:
				return
			if self.itemDestroyPending is not None or self.itemDestroyConfirmDialog:
				return

			if answer:
				dropType = slotwindowpolicy.NormalizeSlotType(self.itemDropQuestionDialog.dropType)
				dropNumber = self.itemDropQuestionDialog.dropNumber

				if player.SLOT_TYPE_INVENTORY == dropType:
					if dropNumber == player.ITEM_MONEY:
						return
					signature = self.__DestroyItemSignature(dropNumber)
					if (signature[0] != 0
						and signature == self.itemDropQuestionDialog.itemSignature
						and signature[:2] == (self.itemDropQuestionDialog.dropVnum,
							self.itemDropQuestionDialog.dropCount)):
						confirm = uiCommon.QuestionDialog()
						confirm.SetWidth(400)
						confirm.SetText(localeInfo.DESTROY_ITEM_CONFIRM)
						confirm.SetAcceptEvent(lambda: self.ConfirmDestroyItem(True))
						confirm.SetCancelEvent(lambda: self.ConfirmDestroyItem(False))
						confirm.dropNumber = dropNumber
						confirm.itemSignature = signature
						self.itemDestroyConfirmDialog = confirm
						self.itemDropQuestionDialog.SetPending(True)
						confirm.Open()
						return

			self.itemDropQuestionDialog.Close()
			self.itemDropQuestionDialog = None
			constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

		def ConfirmDestroyItem(self, answer):
			confirm = self.itemDestroyConfirmDialog
			if not confirm:
				return
			self.itemDestroyConfirmDialog = None
			confirm.Close()
			if not self.itemDropQuestionDialog:
				return
			self.itemDropQuestionDialog.SetPending(False)
			if not answer or self.itemDestroyPending is not None:
				return

			slot = confirm.dropNumber
			if self.__DestroyItemSignature(slot) != confirm.itemSignature:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_DESTROY)
				return
			if self.__SendDestroyItemPacket(slot):
				self.itemDestroyPending = (player.INVENTORY, slot)
				self.itemDropQuestionDialog.Close()
				self.itemDropQuestionDialog = None
				constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

		def __SendDestroyItemPacket(self, itemVNum, itemInvenType = player.INVENTORY):
			if uiPrivateShopBuilder.IsBuildingPrivateShop():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_ITEM_FAILURE_PRIVATE_SHOP)
				return False

			if not net.SendItemDestroyPacket(itemVNum):
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_DESTROY)
				return False
			return True

		def __ItemDestroyResult(self, windowType, cell, destroyed):
			try:
				windowType = int(windowType)
				cell = int(cell)
				destroyed = int(destroyed)
			except (TypeError, ValueError):
				return 0

			if destroyed not in (0, 1):
				return 0
			if self.itemDestroyPending != (windowType, cell):
				return 0

			self.itemDestroyPending = None
			if destroyed:
				return 1

			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_DESTROY)
			return 1

	# PRIVATESHOP_DISABLE_ITEM_DROP
	def __SendDropItemPacket(self, itemVNum, itemCount, itemInvenType = player.INVENTORY):
		if uiPrivateShopBuilder.IsBuildingPrivateShop():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DROP_ITEM_FAILURE_PRIVATE_SHOP)
			return

		net.SendItemDropPacketNew(itemInvenType, itemVNum, itemCount)
	# END_OF_PRIVATESHOP_DISABLE_ITEM_DROP

	def OnMouseRightButtonDown(self):
		if self.__IsInputGuardLocked():
			return True

		self.CheckFocus()

		if True == mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
		else:
			player.SetMouseState(player.MBT_RIGHT, player.MBS_PRESS)

		return True

	def OnMouseRightButtonUp(self):
		if True == mouseModule.mouseController.isAttached():
			return True

		player.SetMouseState(player.MBT_RIGHT, player.MBS_CLICK)
		return True

	def OnMouseMiddleButtonDown(self):
		player.SetMouseMiddleButtonState(player.MBS_PRESS)

	def OnMouseMiddleButtonUp(self):
		player.SetMouseMiddleButtonState(player.MBS_CLICK)

	def OnUpdate(self):
		if (dungeonequipmentbinding.receiver.Owns(getattr(self, "dungeonBindingOwner", None))
				and dungeonequipmentbinding.receiver.Expire()):
			self.__RefreshDungeonEquipmentBindingView()
		if self.keybindingManager:
			self.keybindingManager.release_unpressed()
		if self.seamlessWarping:
			# The world, the main actor and the session belong to no server
			# until the destination's ENTERGAME; the curtain covers it all.
			return
		if ticketnoticemodel.STATE.Pending():
			self.__PollTicketNotice()
		noteFrame = getattr(self.stream, "NoteWarpCurtainFrame", None)
		if noteFrame:
			noteFrame()
		app.UpdateGame()
		bonusCatalog.Tick()
		# Tooltip work must not interrupt the world-to-interface render state.
		x, y = app.GetCursorPosition()
		self.__UpdateMeteorToolTip(chr.Pick() if wndMgr.IsPickedWindow(self.hWnd) else -1, x, y)
		self.__UpdatePetAlbumSession()
		if self.craftIdsOffered:
			self.__AnswerCraftIdsOffer()
		self.__ShowNextFriendRequest()
		if self.interface:
			self.interface.FlushItemMetadataRefresh()
			if getattr(app, "ENABLE_WIKI", False):
				self.interface.UpdateWiki()
		self.dungeonObjectiveSubscription.update()
		self.__UpdateInitialWorldReveal()
		if self.interface:
			self.interface.UpdateAfkSystem()
			self.interface.UpdateQuickBuffSystem()
			self.interface.UpdateCountdownHUD()
			self.interface.UpdateMiningCheck()
			self.interface.UpdateWoodCheck()
			self.interface.UpdateGuildInvitations(not self.initialWorldRevealPending)
		if self.skillTreeRuntime:
			self.skillTreeRuntime.Update()

		if self.mapNameShower.IsShow():
			self.mapNameShower.Update()
		if self.interface:
			self.interface.UpdateNoticeBoard(bool(self.mapNameShower and self.mapNameShower.IsShow()))
		if self.pvmPersonal:
			self.pvmPersonal.Update()

		if self.isShowDebugInfo:
			self.UpdateDebugInfo()

		if self.enableXMasBoom:
			self.__XMasBoom_Update()

		self.interface.BUILD_OnUpdate()
		self.__RestoreWarpUIState()

		if app.ENABLE_BIOLOG_SYSTEM:
			self.loopListEvent()
			if self.interface and self.interface.wndBio and not self.interface.wndBio.dataKnown:
				self.interface.wndBio.RequestState()

		if app.ENABLE_AUTO_PICKUP and osfInfo.AUTOPICKUP_ENABLED:
			if app.GetTime() >= self.lastAutoPickupTime:
				getattr(player, "AutoPickCloseItems", player.PickAllCloseItems)()
				self.lastAutoPickupTime = app.GetTime() + 0.2

		self.__UpdateInputGuard()

		if osfInfo.AffectIconState == 1 and app.ENABLE_HIDE_AFFECT_ICONS:
			self.AffectIconState()
			osfInfo.AffectIconState = 0

	def __RestoreWarpUIState(self):
		if self.warpUITransition or not self.interface:
			return

		if not self.warpUIRestoreLoaded:
			characterName = player.GetName()
			if not characterName:
				return
			self.warpUIRestoreLoaded = True
			self.warpUIRestoreState = uiwarpstate.Take(characterName)
			self.warpUIRestoreDeadline = app.GetTime() + 5.0

		if not self.warpUIRestoreState:
			return

		self.warpUIRestoreState = self.interface.RestoreWarpUIState(
			self.warpUIRestoreState)
		if self.warpUIRestoreState and \
				app.GetTime() < self.warpUIRestoreDeadline:
			return

		if self.warpUIRestoreState:
			dbg.TraceError(
				"[WarpUI] timed out while restoring: %s" %
				", ".join(sorted(self.warpUIRestoreState.keys())))
		self.warpUIRestoreState = None

	def BINARY_SkillTreeCatalog(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnCatalog(*args)
		return False

	def BINARY_SkillTreeSnapshot(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnSnapshot(*args)
		return False

	def BINARY_SkillTreeUpgradeResult(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnUpgradeResult(*args)
		return False

	def BINARY_SkillTreeDismantleResult(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnDismantleResult(*args)
		return False

	def BINARY_SkillTreeError(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnError(*args)
		return False

	def BINARY_SkillTreeActivationState(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnActivationState(*args)
		return False

	def BINARY_SkillTreeActivationResult(self, *args):
		if self.skillTreeRuntime:
			return self.skillTreeRuntime.OnActivationResult(*args)
		return False

	def BINARY_MountSystemCapability(self, enabled):
		if self.interface:
			self.interface.SetMountSystemCapability(bool(enabled))

	def __OpenPetAlbumSession(self):
		if self.petAlbumReady:
			return
		self.petAlbumClosed = False
		self.petAlbumSyncAt = 0.0
		album = petalbumstate.GetState()
		if album.ClaimPresentation(self.petAlbumOwner) and hasattr(chr, "ResetAlbumMarkers"):
			chr.ResetAlbumMarkers()
		# Loading can preserve another offer after the constructor drained it.
		# Collect it while still deferred, then use only the latest offer below.
		self.__ProcessPreservedServerCommand()
		self.petAlbumReady = True
		offer, self.petAlbumOffer = self.petAlbumOffer, None
		if offer:
			self.__PetAlbumCapability(*offer)

	def __UpdatePetAlbumSession(self):
		album = petalbumstate.GetState()
		if not self.petAlbumReady or not album.OwnsPresentation(self.petAlbumOwner):
			return
		# Loading can still receive an offer after Open, before native Game phase.
		self.__ProcessPreservedServerCommand()
		if not hasattr(net, "SendPetAlbumRequest") or not hasattr(chr, "AlbumMarker"):
			return
		# Pending hunts refresh their authoritative calendar bounds; the UI
		# remains read-only and a closed presentation owner never sends requests.
		if album.available and not any(row["phase"] == 1 for row in album.pets.values()):
			return
		now = app.GetTime()
		if now < self.petAlbumSyncAt:
			return
		self.petAlbumSyncAt = now + (30.0 if album.available else 2.0)
		# The legacy read command is safe before any capability is advertised.
		# SendChatPacket waits for native Game phase; later updates retry it.
		net.SendChatPacket("/pet_album_sync")

	def __ClosePetAlbumSession(self):
		self.petAlbumClosed = True
		album = petalbumstate.GetState()
		if album.OwnsPresentation(self.petAlbumOwner):
			if self.warpUITransition and self.interface:
				# Include events received after the initial pre-warp snapshot.
				uiwarpstate.UpdateWindow(player.GetName(), "pet_album_notices",
					self.interface.CapturePetAlbumNotices())
			if album.ReleasePresentation(self.petAlbumOwner) and hasattr(chr, "ResetAlbumMarkers"):
				chr.ResetAlbumMarkers()
		self.petAlbumReady = False
		self.petAlbumOffer = None

	def __PetAlbumCapability(self, digest, epoch, profile, active):
		if not self.petAlbumReady:
			if self.petAlbumClosed:
				return
			# A direct offer is newer than any commands still held by loading.
			if not self.petAlbumPreserving:
				self.__ProcessPreservedServerCommand()
			self.petAlbumOffer = (digest, epoch, profile, active)
			return
		album = petalbumstate.GetState()
		if not album.OwnsPresentation(self.petAlbumOwner):
			return
		previous = album.context
		enabled = album.Begin(digest, epoch, profile, active)
		if not enabled and str(active) == "1":
			dbg.TraceError("PET_ALBUM capability rejected: %s; server=%s client=%s" %
				(album.lastError, digest, album.view["hash"]))
		if previous != album.context or not enabled:
			if self.interface:
				self.interface.ClearPetAlbumNotices()
			if hasattr(chr, "ResetAlbumMarkers"):
				chr.ResetAlbumMarkers()
		if (enabled and hasattr(net, "SendPetAlbumRequest") and
			hasattr(chr, "AlbumMarker")):
			# The server advertises before this client sends any new header.
			sent = net.SendPetAlbumRequest(digest, 0)
			if profile == "qa50":
				dbg.TraceError("PET_ALBUM handshake accepted; request=%s" % sent)

	def BINARY_PetAlbumFrame(self, opcode, payload):
		album = petalbumstate.GetState()
		if not self.petAlbumReady or not album.OwnsPresentation(self.petAlbumOwner):
			return False
		wasAvailable = album.available
		result = album.Receive(opcode, payload)
		if not result:
			if opcode == 1:
				dbg.TraceError("PET_ALBUM snapshot rejected: %s" % album.lastError)
			return False
		if result[0] == "snapshot" and album.available and not wasAvailable and album.context[2] == "qa50":
			dbg.TraceError("PET_ALBUM snapshot ready; entries=%d" % len(album.pets))
		if result[0] == "actor" and hasattr(chr, "AlbumActorIdentity"):
			chr.AlbumActorIdentity(*result[1:])
		elif result[0] == "marker" and hasattr(chr, "AlbumMarker"):
			chr.AlbumMarker(*result[1:])
		elif result[0] == "snapshot" and not petalbumstate.GetState().available:
			if hasattr(chr, "ResetAlbumMarkers"):
				chr.ResetAlbumMarkers()
		if result[0] == "snapshot":
			if self.interface:
				for visual in album.ConsumeVisualNotifications():
					self.interface.ShowPetAlbumNotice(visual)
			for notice in album.ConsumeNotifications():
				if notice[0] == "clue":
					chat.AppendChat(chat.CHAT_TYPE_INFO, uiScriptLocale.PET_ALBUM_CLUE_NOTICE % notice[1:])
				elif notice[0] == "capture":
					chat.AppendChat(chat.CHAT_TYPE_INFO, uiScriptLocale.PET_ALBUM_CAPTURE_NOTICE % notice[1])
		return True

	def BINARY_GuildV2(self, payload):
		if self.interface and self.interface.wndGuild:
			self.interface.wndGuild.Receive(payload)

	def BINARY_DailyTasksCapability(self, enabled, generation):
		if self.interface:
			return self.interface.SetDailyTasksCapability(enabled, generation)
		return False

	def BINARY_DailyTasksSnapshot(self, snapshot):
		if self.interface:
			return self.interface.ApplyDailyTasksSnapshot(snapshot)
		return False

	def BINARY_DailyTasksDelta(self, delta):
		if self.interface:
			return self.interface.ApplyDailyTasksDelta(delta)
		return False

	def BINARY_DailyTasksStatus(self, statusCode):
		if self.interface:
			return self.interface.SetDailyTasksStatus(statusCode)
		return False

	def BINARY_PermanentHuntRewards(self, generation, rows):
		if self.interface:
			return self.interface.ApplyPermanentHuntRewards(generation, rows)
		return False

	def BINARY_LuckKnotSnapshot(self, snapshot):
		if self.interface:
			return self.interface.ApplyLuckKnotSnapshot(snapshot)
		return False

	def BINARY_PermanentTasksCapability(self, enabled, generation):
		if self.interface:
			return self.interface.SetPermanentTasksCapability(enabled, generation)
		return False

	def BINARY_PermanentTasksSnapshot(self, snapshot):
		if self.interface:
			return self.interface.ApplyPermanentTasksSnapshot(snapshot)
		return False

	def BINARY_PermanentTasksSubmitResult(self, result):
		if self.interface:
			return self.interface.ApplyPermanentTasksSubmitResult(result)
		return False

	def BINARY_PermanentTasksStatus(self, statusCode):
		if self.interface:
			return self.interface.SetPermanentTasksStatus(statusCode)
		return False

	def BINARY_PermanentTasksAltheaMeteorChance(self, chanceBp):
		if self.interface:
			return self.interface.SetPermanentTasksAltheaMeteorChance(chanceBp)
		return False

	def BINARY_MountSystemSnapshot(self, snapshot):
		if self.interface:
			return self.interface.ApplyMountSystemSnapshot(snapshot)
		return False

	def BINARY_MountSystemActionResult(self, result):
		if self.interface and isinstance(result, (tuple, list)) and len(result) == 3:
			self.interface.HandleMountSystemActionResult(*result)

	def BINARY_MountSystemError(self, code, messageKey, refreshRequired):
		if self.interface:
			self.interface.HandleMountSystemError(
				code, messageKey, bool(refreshRequired)
			)

	def __GMPanelCatalog(self, row):
		# One row of what the server lets this session's GM panel show: a
		# single field whose parts vary by row and are validated on receipt.
		try:
			if self.interface:
				self.interface.OnGMPanelCatalog(row)
		except Exception as error:
			dbg.TraceError("[GM panel] catalogue row failed: %s" % error)

	def BINARY_GMPanelResult(self, requestID, action, status, gmLevel, maskLow, maskHigh, message):
		if self.interface:
			self.interface.OnGMPanelResult(requestID, action, status, gmLevel, maskLow, maskHigh, message)

	def OnCustomPortsChanged(self):
		if self.interface:
			self.interface.OnCustomPortsChanged()

	def OnPvPMatchmakingChanged(self):
		if self.interface:
			self.interface.OnPvPMatchmakingChanged()

	def OnCustomPortsError(self, requestID, reason):
		if self.interface:
			self.interface.OnCustomPortsError(requestID, reason)

	def OnAfkSystemChanged(self):
		if self.interface:
			self.interface.OnAfkSystemChanged()

	def OnAfkRewardCause(self, code):
		import uiafkrewardshop
		if uiafkrewardshop.SetCause(code):
			self.OnAfkRewardsChanged()

	def OnAfkRewardZones(self, maps):
		import uiafkrewardshop
		if uiafkrewardshop.SetZones(maps):
			self.OnAfkRewardsChanged()

	def OnAfkRewardsChanged(self):
		if self.interface:
			self.interface.OnAfkRewardsChanged()

	def OnAfkRewardPurchaseResult(self, result, balance):
		if self.interface:
			self.interface.OnAfkRewardPurchaseResult(result, balance)

	def OnAfkTeleportOffer(self, offerId, expiresAt, mapIndex):
		if self.interface:
			self.interface.OnAfkTeleportOffer(offerId, expiresAt, mapIndex)

	def OnAfkTeleportResult(self, offerId, status):
		if self.interface:
			self.interface.OnAfkTeleportResult(offerId, status)

	def OnAfkSystemError(self, requestId, reason):
		if self.interface:
			self.interface.OnAfkSystemError(requestId, reason)

	def UpdateDebugInfo(self):
		#
		# 캐릭터 좌표 및 FPS 출력
		(x, y, z) = player.GetMainCharacterPosition()
		nUpdateTime = app.GetUpdateTime()
		nUpdateFPS = app.GetUpdateFPS()
		nRenderFPS = app.GetRenderFPS()
		nFaceCount = app.GetFaceCount()
		fFaceSpeed = app.GetFaceSpeed()
		nST=background.GetRenderShadowTime()
		(fAveRT, nCurRT) = app.GetRenderTime()
		(iNum, fFogStart, fFogEnd, fFarCilp) = background.GetDistanceSetInfo()
		(iPatch, iSplat, fSplatRatio, sTextureNum) = background.GetRenderedSplatNum()
		if iPatch == 0:
			iPatch = 1

		#(dwRenderedThing, dwRenderedCRC) = background.GetRenderedGraphicThingInstanceNum()

		self.PrintCoord.SetText("Coordinate: %.2f %.2f %.2f ATM: %d" % (x, y, z, app.GetAvailableTextureMemory()//(1024*1024)))
		xMouse, yMouse = wndMgr.GetMousePosition()
		self.PrintMousePos.SetText("MousePosition: %d %d" % (xMouse, yMouse))

		self.FrameRate.SetText("UFPS: %3d UT: %3d FS %.2f" % (nUpdateFPS, nUpdateTime, fFaceSpeed))

		if fAveRT>1.0:
			self.Pitch.SetText("RFPS: %3d RT:%.2f(%3d) FC: %d(%.2f) " % (nRenderFPS, fAveRT, nCurRT, nFaceCount, nFaceCount/fAveRT))

		self.Splat.SetText("PATCH: %d SPLAT: %d BAD(%.2f)" % (iPatch, iSplat, fSplatRatio))
		# self.Pitch.SetText("Pitch: %.2f" % (app.GetCameraPitch())
		# self.TextureNum.SetText("TN : %s" % (sTextureNum))
		# self.ObjectNum.SetText("GTI : %d, CRC : %d" % (dwRenderedThing, dwRenderedCRC))
		self.ViewDistance.SetText("Num : %d, FS : %f, FE : %f, FC : %f" % (iNum, fFogStart, fFogEnd, fFarCilp))

	def __UpdateMeteorToolTip(self, vid, x, y):
		presentation = self.meteorProtection.presentation(vid, app.GetGlobalTimeStamp())
		if (presentation is None or not self.IsShow() or self.seamlessWarping
				or self.__IsOtherCurtainActive() or not chr.HasInstance(vid)):
			if self.meteorToolTip:
				self.meteorToolTip.Hide()
			return
		if not self.meteorToolTip:
			import uimeteortooltip
			self.meteorToolTip = uimeteortooltip.MeteorToolTip()
		self.meteorToolTip.Present(chr.GetNameByVID(vid), presentation[0], presentation[1],
			x, y, wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

	def OnRender(self):
		# Behind an opaque warp curtain the reconnecting world is not drawn;
		# while it still fades in, the old world keeps rendering.
		if self.seamlessWarping:
			covered = getattr(self.stream, "IsWarpCurtainCovering", None)
			if covered and covered():
				return
		app.RenderGame()

		if self.console.Console.collision:
			background.RenderCollision()
			chr.RenderCollision()

		(x, y) = app.GetCursorPosition()

		########################
		# Picking
		########################
		textTail.UpdateAllTextTail()

		if True == wndMgr.IsPickedWindow(self.hWnd):
			self.PickingCharacterIndex = chr.Pick()

			if -1 != self.PickingCharacterIndex:
				if callable(getattr(systemSetting, 'GetNameVisibility', None)):
					textTail.ShowCharacterTextTail(self.PickingCharacterIndex, 1)
				else:
					textTail.ShowCharacterTextTail(self.PickingCharacterIndex)
			if 0 != self.targetBoard.GetTargetVID():
				textTail.ShowCharacterTextTail(self.targetBoard.GetTargetVID())

			# ADD_ALWAYS_SHOW_NAME
			if not self.__IsShowName():
				self.PickingItemIndex = item.Pick()
				if -1 != self.PickingItemIndex:
					textTail.ShowItemTextTail(self.PickingItemIndex)
			# END_OF_ADD_ALWAYS_SHOW_NAME

		## Show all name in the range

		# ADD_ALWAYS_SHOW_NAME
		if self.__IsShowName():
			textTail.ShowAllTextTail()
			self.PickingItemIndex = textTail.Pick(x, y)
		# END_OF_ADD_ALWAYS_SHOW_NAME

		if app.ENABLE_GRAPHIC_ON_OFF:
			if systemSetting.IsShowSalesText():
				uiPrivateShopBuilder.UpdateADBoard()

		textTail.UpdateShowingTextTail()
		textTail.ArrangeTextTail()
		if -1 != self.PickingItemIndex:
			textTail.SelectItemName(self.PickingItemIndex)

		if not app.ENABLE_DAMAGE_PRINT_IMPROVE:
			grp.PopState()
			grp.SetInterfaceRenderState()

		textTail.Render()
		textTail.HideAllTextTail()

		if app.ENABLE_DAMAGE_PRINT_IMPROVE:
			app.RenderDamageEffect()
			grp.PopState()
			grp.SetInterfaceRenderState()

	def OnPressEscapeKey(self):
		if self.__IsWarpInputLocked():
			return True
		if self.__IsInputGuardLocked():
			return True

		if app.TARGET == app.GetCursor():
			app.SetCursor(app.NORMAL)

		elif True == mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
		else:
			self.interface.OpenSystemDialog()

		return True

	def OnIMEReturn(self):
		if self.__IsWarpInputLocked():
			return True
		if self.__IsInputGuardLocked():
			return True

		if app.IsPressed(app.DIK_LSHIFT):
			self.interface.OpenMessagesNewConversation()
		else:
			self.interface.ToggleChat()
		return True

	def OnPressExitKey(self):
		if self.__IsWarpInputLocked():
			return True
		if self.__IsInputGuardLocked():
			return True

		self.interface.ToggleSystemDialog()
		return True

	## BINARY CALLBACK
	######################################################################################

	# WEDDING
	def BINARY_LoverInfo(self, name, lovePoint):
		if self.interface.wndMessenger:
			self.interface.wndMessenger.OnAddLover(name, lovePoint)
		if self.affectShower:
			self.affectShower.SetLoverInfo(name, lovePoint)

	def BINARY_UpdateLovePoint(self, lovePoint):
		if self.interface.wndMessenger:
			self.interface.wndMessenger.OnUpdateLovePoint(lovePoint)
		if self.affectShower:
			self.affectShower.OnUpdateLovePoint(lovePoint)
	# END_OF_WEDDING

	if app.ENABLE_SEND_TARGET_INFO:
		def BINARY_RefreshTargetMonsterDropInfo(self, raceNum):
			self.targetBoard.RefreshMonsterInfoBoard(raceNum)

		def __TargetDropLevelGap(self, raceNum, blocked):
			# arrives before the drop list it describes (the target-info response).
			uiTarget.SetDropLevelGap(raceNum, blocked)

	# QUEST_CONFIRM
	def BINARY_OnQuestConfirm(self, msg, timeout, pid):
		confirmDialog = uiCommon.QuestionDialogWithTimeLimit()
		confirmDialog.Open(msg, timeout)
		confirmDialog.SetAcceptEvent(lambda answer=True, pid=pid: net.SendQuestConfirmPacket(answer, pid) or self.confirmDialog.Hide())
		confirmDialog.SetCancelEvent(lambda answer=False, pid=pid: net.SendQuestConfirmPacket(answer, pid) or self.confirmDialog.Hide())
		confirmDialog.SetCancelOnTimeOver() # hotfix
		self.confirmDialog = confirmDialog
	# END_OF_QUEST_CONFIRM

	# GIFT command
	def Gift_Show(self):
		self.interface.ShowGift()

	def Gift_Hide(self):
		self.interface.HideGift()

	# CUBE
	def BINARY_Cube_Open(self, npcVNUM, reload = 0):
		self.currentCubeNPC = npcVNUM

		if reload:
			self.cubeInformation.clear()
			self.interface.wndCube.ClearOldSlots()

		self.interface.OpenCubeWindow()

		if npcVNUM not in self.cubeInformation:
			net.SendChatPacket("/cube r_info")
		else:
			cubeInfoList = self.cubeInformation[npcVNUM]

			i = 0
			for cubeInfo in cubeInfoList:
				self.interface.wndCube.AddCubeResultItem(cubeInfo["vnum"], cubeInfo["count"])

				j = 0
				for materialList in cubeInfo["materialList"]:
					for materialInfo in materialList:
						itemVnum, itemCount = materialInfo
						self.interface.wndCube.AddMaterialInfo(i, j, itemVnum, itemCount)
					j = j + 1

				i = i + 1

			self.interface.wndCube.Refresh()

	def BINARY_Cube_Close(self):
		self.interface.CloseCubeWindow()

	# 제작에 필요한 골드, 예상되는 완성품의 VNUM과 개수 정보 update
	def BINARY_Cube_UpdateInfo(self, gold, itemVnum, count):
		self.interface.UpdateCubeInfo(gold, itemVnum, count)

	def BINARY_Cube_Succeed(self, itemVnum, count):
		print("큐브 제작 성공")
		self.interface.SucceedCubeWork(itemVnum, count)
		pass

	def BINARY_Cube_Failed(self):
		print("큐브 제작 실패")
		self.interface.FailedCubeWork()
		pass

	def BINARY_Cube_ResultList(self, npcVNUM, listText):
		# ResultList Text Format : 72723,1/72725,1/72730.1/50001,5 이런식으로 "/" 문자로 구분된 리스트를 줌
		#print listText

		if npcVNUM == 0:
			npcVNUM = self.currentCubeNPC

		self.cubeInformation[npcVNUM] = []

		try:
			for eachInfoText in listText.split("/"):
				eachInfo = eachInfoText.split(",")
				itemVnum = int(eachInfo[0])
				itemCount = int(eachInfo[1])

				self.cubeInformation[npcVNUM].append({"vnum": itemVnum, "count": itemCount})
				self.interface.wndCube.AddCubeResultItem(itemVnum, itemCount)

			resultCount = len(self.cubeInformation[npcVNUM])
			requestCount = 5
			modCount = resultCount % requestCount
			splitCount = resultCount // requestCount
			for i in range(splitCount):
				#print("/cube r_info %d %d" % (i * requestCount, requestCount))
				net.SendChatPacket("/cube r_info %d %d" % (i * requestCount, requestCount))

			if 0 < modCount:
				#print("/cube r_info %d %d" % (splitCount * requestCount, modCount))
				net.SendChatPacket("/cube r_info %d %d" % (splitCount * requestCount, modCount))

		except RuntimeError as msg:
			dbg.TraceError(msg)
			return 0

		pass

	def BINARY_Cube_MaterialInfo(self, startIndex, listCount, listText):
		# Material Text Format : 125,1|126,2|127,2|123,5&555,5&555,4/120000
		try:
			#print listText

			if 3 > len(listText):
				dbg.TraceError("Wrong Cube Material Infomation")
				return 0

			eachResultList = listText.split("@")

			cubeInfo = self.cubeInformation[self.currentCubeNPC]

			itemIndex = 0
			for eachResultText in eachResultList:
				cubeInfo[startIndex + itemIndex]["materialList"] = [[], [], [], [], []]
				materialList = cubeInfo[startIndex + itemIndex]["materialList"]

				gold = 0
				splitResult = eachResultText.split("/")
				if 1 < len(splitResult):
					gold = int(splitResult[1])

				#print "splitResult : ", splitResult
				eachMaterialList = splitResult[0].split("&")

				i = 0
				for eachMaterialText in eachMaterialList:
					complicatedList = eachMaterialText.split("|")

					if 0 < len(complicatedList):
						for complicatedText in complicatedList:
							(itemVnum, itemCount) = complicatedText.split(",")
							itemVnum = int(itemVnum)
							itemCount = int(itemCount)
							self.interface.wndCube.AddMaterialInfo(itemIndex + startIndex, i, itemVnum, itemCount)

							materialList[i].append((itemVnum, itemCount))
					else:
						itemVnum, itemCount = eachMaterialText.split(",")
						itemVnum = int(itemVnum)
						itemCount = int(itemCount)
						self.interface.wndCube.AddMaterialInfo(itemIndex + startIndex, i, itemVnum, itemCount)

						materialList[i].append((itemVnum, itemCount))

					i = i + 1

				itemIndex = itemIndex + 1

			self.interface.wndCube.Refresh()

		except RuntimeError as msg:
			dbg.TraceError(msg)
			return 0

		pass

	# END_OF_CUBE

	# 용혼석
	def BINARY_Highlight_Item(self, inven_type, inven_pos):
		if self.interface:
			self.interface.Highligt_Item(inven_type, inven_pos)

	def BINARY_DragonSoulGiveQuilification(self):
		self.interface.DragonSoulGiveQuilification()

	if app.ENABLE_DS_CHANGE_ATTR:
		def BINARY_DragonSoulRefineWindow_Open(self, type):
			self.interface.OpenDragonSoulRefineWindow(type)
	else:
		def BINARY_DragonSoulRefineWindow_Open(self):
			self.interface.OpenDragonSoulRefineWindow()

	def BINARY_DragonSoulRefineWindow_RefineFail(self, reason, inven_type, inven_pos):
		self.interface.FailDragonSoulRefine(reason, inven_type, inven_pos)

	def BINARY_DragonSoulRefineWindow_RefineSucceed(self, inven_type, inven_pos):
		self.interface.SucceedDragonSoulRefine(inven_type, inven_pos)

	# END of DRAGON SOUL REFINE WINDOW

	def BINARY_SetBigMessage(self, message):
		self.interface.bigBoard.SetTip(message)

	def BINARY_SetTipMessage(self, message):
		self.interface.tipBoard.SetTip(message)

	if app.ENABLE_12ZI:
		def BINARY_SetMissionMessage(self, message):
			self.interface.missionBoard.SetMission(message)

		def BINARY_SetSubMissionMessage(self, message):
			self.interface.missionBoard.SetSubMission(message)

		def BINARY_CleanMissionMessage(self):
			self.interface.missionBoard.CleanMission()

	if app.ENABLE_HIDE_COSTUME_SYSTEM:
		def SetBodyCostumeHidden(self, hidden):
			osfInfo.HIDDEN_BODY_COSTUME = int(hidden)
			self.interface.RefreshVisibleCostume()

		def SetHairCostumeHidden(self, hidden):
			osfInfo.HIDDEN_HAIR_COSTUME = int(hidden)
			self.interface.RefreshVisibleCostume()

		def SetAuraCostumeHidden(self, hidden):
			if app.ENABLE_AURA_SYSTEM:
				osfInfo.HIDDEN_AURA_COSTUME = int(hidden)
				self.interface.RefreshVisibleCostume()
			else:
				pass

		def SetAcceCostumeHidden(self, hidden):
			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				osfInfo.HIDDEN_ACCE_COSTUME = int(hidden)
				self.interface.RefreshVisibleCostume()
			else:
				pass

		def SetWeaponCostumeHidden(self, hidden):
			if app.ENABLE_WEAPON_COSTUME_SYSTEM:
				osfInfo.HIDDEN_WEAPON_COSTUME = int(hidden)
				self.interface.RefreshVisibleCostume()
			else:
				pass

		def SetAcceSkinHidden(self, hidden):
			if app.ENABLE_ACCE_SKIN_SYSTEM:
				osfInfo.HIDDEN_ACCE_SKIN = int(hidden)
				self.interface.RefreshVisibleCostume()
			else:
				pass

		def SetShiningWeaponHidden(self, hidden):
			if app.ENABLE_SPECIAL_SHINING_SYSTEM:
				osfInfo.HIDDEN_SHINING_WEAPON = int(hidden)
				self.interface.RefreshVisibleCostume()

		def SetShiningArmorHidden(self, hidden):
			if app.ENABLE_SPECIAL_SHINING_SYSTEM:
				osfInfo.HIDDEN_SHINING_ARMOR = int(hidden)
				self.interface.RefreshVisibleCostume()

		def SetMountHidden(self, hidden):
			if app.ENABLE_MOUNT_COSTUME_SYSTEM:
				osfInfo.HIDDEN_MOUNT = int(hidden)
				self.interface.RefreshVisibleCostume()

	def BINARY_RecieveWhisperDetails(self, name, country):
		if self.interface:
			self.interface.RecieveWhisperDetails(name, country)

	def BINARY_AppendNotifyMessage(self, type):
		if not type in localeInfo.NOTIFY_MESSAGE:
			return

		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.NOTIFY_MESSAGE[type])

	def BINARY_Guild_EnterGuildArea(self, areaID):
		self.interface.BULID_EnterGuildArea(areaID)

	def BINARY_Guild_ExitGuildArea(self, areaID):
		self.interface.BULID_ExitGuildArea(areaID)

	def BINARY_GuildWar_OnSendDeclare(self, guildID):
		pass

	def BINARY_GuildWar_OnRecvDeclare(self, guildID, warType):
		mainCharacterName = player.GetMainCharacterName()
		masterName = guild.GetGuildMasterName()
		if mainCharacterName == masterName:
			self.__GuildWar_OpenAskDialog(guildID, warType)

	def BINARY_GuildWar_OnRecvPoint(self, gainGuildID, opponentGuildID, point):
		self.interface.OnRecvGuildWarPoint(gainGuildID, opponentGuildID, point)

	def BINARY_GuildWar_OnStart(self, guildSelf, guildOpp):
		self.interface.OnStartGuildWar(guildSelf, guildOpp)

	def BINARY_GuildWar_OnEnd(self, guildSelf, guildOpp):
		self.interface.OnEndGuildWar(guildSelf, guildOpp)

	def BINARY_BettingGuildWar_SetObserverMode(self, isEnable):
		self.interface.BINARY_SetObserverMode(isEnable)

	def BINARY_BettingGuildWar_UpdateObserverCount(self, observerCount):
		self.interface.wndMiniMap.UpdateObserverCount(observerCount)

	def __GuildWar_UpdateMemberCount(self, guildID1, memberCount1, guildID2, memberCount2, observerCount):
		guildID1 = int(guildID1)
		guildID2 = int(guildID2)
		memberCount1 = int(memberCount1)
		memberCount2 = int(memberCount2)
		observerCount = int(observerCount)

		self.interface.UpdateMemberCount(guildID1, memberCount1, guildID2, memberCount2)
		self.interface.wndMiniMap.UpdateObserverCount(observerCount)

	def __GuildWar_OpenAskDialog(self, guildID, warType):
		guildName = guild.GetGuildName(guildID)

		# REMOVED_GUILD_BUG_FIX
		if "Noname" == guildName:
			return
		# END_OF_REMOVED_GUILD_BUG_FIX

		import uiGuild
		questionDialog = uiGuild.AcceptGuildWarDialog()
		questionDialog.SAFE_SetAcceptEvent(self.__GuildWar_OnAccept)
		questionDialog.SAFE_SetCancelEvent(self.__GuildWar_OnDecline)
		questionDialog.Open(guildName, warType)

		self.guildWarQuestionDialog = questionDialog

	def __GuildWar_CloseAskDialog(self):
		self.guildWarQuestionDialog.Close()
		self.guildWarQuestionDialog = None

	def __GuildWar_OnAccept(self):
		guildName = self.guildWarQuestionDialog.GetGuildName()

		net.SendChatPacket("/war " + guildName)
		self.__GuildWar_CloseAskDialog()

		return 1

	def __GuildWar_OnDecline(self):
		guildName = self.guildWarQuestionDialog.GetGuildName()

		net.SendChatPacket("/nowar " + guildName)
		self.__GuildWar_CloseAskDialog()

		return 1

	def __CloseDungeonRejoinDialog(self):
		if self.dungeonRejoinDialog:
			self.dungeonRejoinDialog.Close()
			self.dungeonRejoinDialog = None

	def __DungeonRejoinOffer(self, questIdx, token, bossVnum, leftTime, channel):
		try:
			questIdx = int(questIdx)
			token = int(token)
			bossVnum = int(bossVnum)
			leftTime = max(0, int(leftTime))
			channel = int(channel)
		except (TypeError, ValueError):
			return

		self.__CloseDungeonRejoinDialog()
		osfInfo.dungeonRejoinOffer = {
			"questIdx" : questIdx,
			"token" : token,
			"bossVnum" : bossVnum,
			"expiresAt" : app.GetGlobalTimeStamp() + leftTime,
			"channel" : channel,
		}
		self.interface.RefreshDungeons()
		self.__OpenDungeonRejoinDialog(osfInfo.dungeonRejoinOffer)

	def __OpenDungeonRejoinDialog(self, offer):
		self.__CloseDungeonRejoinDialog()
		if offer["expiresAt"] <= app.GetGlobalTimeStamp():
			return None

		bossVnum = offer["bossVnum"]
		dungeonName = localeInfo.DUNGEON_REJOIN_UNKNOWN
		if app.ENABLE_DUNGEON_INFO:
			dungeonInfo = interfaceModule.uiDungeonTrack.dungeonData.get(bossVnum)
			if dungeonInfo:
				dungeonName = dungeonInfo["name"]

		# the window survives temporary refusals and closes itself
		# only when the offer expires (or on a final DungeonRejoinResult).
		dialog = uidungeonrejoin.DungeonRejoinDialog()
		dialog.SetWidth(430)
		dialog.SetText1(localeInfo.DUNGEON_REJOIN_QUESTION % dungeonName)
		dialog.SetExpiresAt(offer["expiresAt"])
		dialog.SetExpireEvent(ui.__mem_func__(self.__DungeonRejoinExpired))
		dialog.SetAcceptEvent(ui.__mem_func__(self.__DungeonRejoinAccept))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseDungeonRejoinDialog))
		dialog.OnPressEscapeKey = ui.__mem_func__(self.__DungeonRejoinEscape)
		dialog.questIdx = offer["questIdx"]
		dialog.token = offer["token"]
		dialog.channel = offer["channel"]
		dialog.Refresh()
		dialog.Open()
		self.dungeonRejoinDialog = dialog
		return dialog

	def __DungeonRejoinExpired(self):
		self.__CloseDungeonRejoinDialog()
		osfInfo.dungeonRejoinOffer = None
		self.interface.RefreshDungeons()
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.DUNGEON_REJOIN_EXPIRED)

	def __DungeonRejoinRespond(self, action):
		offer = osfInfo.dungeonRejoinOffer
		if not offer:
			return

		dialog = self.dungeonRejoinDialog
		if dialog:
			if not dialog.CanAccept():
				return
			# Keep the window until the server answers: a temporary refusal
			# (DungeonRejoinRetry) must not lose the offer.
			dialog.BeginAccept()

		questIdx = offer["questIdx"]
		token = offer["token"]
		osfInfo.dungeonRejoinCMD = "{}#{}".format(action, token)
		event.QuestButtonClick(questIdx)

	def __DungeonRejoinAccept(self):
		self.__DungeonRejoinRespond("ACCEPT")

	def __DungeonRejoinEscape(self):
		self.__CloseDungeonRejoinDialog()
		return True

	# Guild portal lobby (root/uiguildportallobby.py): the quest of the portal sends the
	# state as cmdchat, the buttons answer through the quest like the dungeon rejoin
	# (pending action + event.QuestButtonClick, then "guild_portal_cmd" asks for it).
	def __GuildPortal(self):
		if not self.guildPortal:
			def guild_model():
				router = getattr(self.interface, "wndGuild", None) if self.interface else None
				window = getattr(router, "window", None) if router else None
				return window.model if window else None

			def guild_snapshot():
				router = getattr(self.interface, "wndGuild", None) if self.interface else None
				window = router._window() if router and hasattr(router, "_window") else None
				if window and hasattr(window, "request") and not window.pending:
					import guildv2model
					window.request(guildv2model.SNAPSHOT)

			def notify(text):
				chat.AppendChat(chat.CHAT_TYPE_INFO, text)

			self.guildPortal = uiguildportallobby.PortalController(event.QuestButtonClick,
				net.SendQuestInputStringPacket, uiguildportallobby.GuildMembers(guild_model, guild_snapshot), notify)
		return self.guildPortal

	def __DestroyGuildPortal(self):
		if self.guildPortal:
			self.guildPortal.Destroy()
			self.guildPortal = None

	def __GuildPortalQuest(self, questIdx):
		self.__GuildPortal().Quest(questIdx)

	def __GuildPortalLobby(self, portalId, element, mapIndex, channel, lockLeftSec, joined, need, canJoin, isJoined,
			canStart, pids, guildName):
		self.__GuildPortal().Lobby(portalId, element, mapIndex, channel, lockLeftSec, joined, need, canJoin, isJoined,
			canStart, pids, guildName)

	def __GuildPortalLobbyOpen(self):
		self.__GuildPortal().Open()

	def __GuildPortalGolem(self, strength):
		self.__GuildPortal().Golem(strength)

	def __GuildPortalPopup(self, element, finderName, joined, need, lockLeftSec, canJoin):
		self.__GuildPortal().Popup(element, finderName, joined, need, lockLeftSec, canJoin)

	def __GuildPortalLobbyClose(self, reason):
		if self.guildPortal:
			self.guildPortal.Close(reason)

	def __GuildPortalQuestCMD(self):
		self.__GuildPortal().Command()

	def __DungeonRejoinQuestCMD(self):
		net.SendQuestInputStringPacket(osfInfo.dungeonRejoinCMD)
		osfInfo.dungeonRejoinCMD = ""

	def __DungeonRejoinRetry(self, reason, seconds):
		# a temporary refusal (trade/shop/storage cooldown, open
		# window, transfer in progress). The server kept the receipt, so the
		# offer stays and the window shows the reason with a countdown.
		offer = osfInfo.dungeonRejoinOffer
		if not offer:
			self.__CloseDungeonRejoinDialog()
			return

		dialog = self.dungeonRejoinDialog
		if not dialog:
			dialog = self.__OpenDungeonRejoinDialog(offer)
		if dialog:
			dialog.Refuse(reason, seconds)

	def __DungeonRejoinResult(self, resultCode, channel):
		self.__CloseDungeonRejoinDialog()
		if resultCode != "WRONG_CHANNEL":
			osfInfo.dungeonRejoinOffer = None
		self.interface.RefreshDungeons()

		if resultCode == "JOINED":
			return

		if resultCode == "WRONG_CHANNEL":
			try:
				targetChannel = int(channel)
			except (TypeError, ValueError):
				targetChannel = 0
			message = localeInfo.DUNGEON_REJOIN_WRONG_CHANNEL % targetChannel
		elif resultCode == "EXPIRED":
			message = localeInfo.DUNGEON_REJOIN_EXPIRED
		elif resultCode == "INVALID":
			message = localeInfo.DUNGEON_REJOIN_INVALID
		else:
			message = localeInfo.DUNGEON_REJOIN_UNAVAILABLE
		chat.AppendChat(chat.CHAT_TYPE_INFO, message)

	## BINARY CALLBACK
	######################################################################################

	def __CraftSelectionCapability(self, nonce, npc, limit):
		window = getattr(self.interface, 'wndCubeRenewal', None)
		if window:
			window.BINARY_CRAFTING_SELECTION_V1(nonce, npc, limit)

	def __CraftSelectionSource(self, nonce, windowType, cell, identity, vnum, count):
		window = getattr(self.interface, 'wndCubeRenewal', None)
		if window:
			window.BINARY_CRAFTING_SELECTION_SOURCE_V1(nonce, windowType, cell, identity, vnum, count)

	def __CraftIdsOffer(self, action, version):
		# CraftIdsV1: the server offers recipe ids at every entry into the game
		# phase. One answer per entry; the EXE enters id mode only when the
		# server confirms that answer, so both sides stay positional without it.
		if version != "1":
			return
		if action == "offer" and not self.craftIdsAnswered:
			self.craftIdsOffered = True
			self.__AnswerCraftIdsOffer()
		elif action == "on" and self.craftIdsRequested:
			self.craftIdsRequested = False
			try:
				import cube_renewal
				cube_renewal.SetIdMode(1)
			except Exception as error:
				dbg.TraceError("[CraftIds] confirm failed: %s" % error)

	def __AnswerCraftIdsOffer(self):
		# SendChatPacket drops a command before the native game phase.
		ready = getattr(net, "IsGamePhase", None)
		if not self.craftIdsOffered or (ready and not ready()):
			return
		self.craftIdsOffered = False
		self.craftIdsAnswered = True
		try:
			import cube_renewal
			# An EXE without the id API stays silent, like an older root pack.
			if hasattr(cube_renewal, 'SetIdMode'):
				net.SendChatPacket("/cube ids 1")
				self.craftIdsRequested = True
		except Exception as error:
			dbg.TraceError("[CraftIds] answer failed: %s" % error)

	def __ResetCraftIdsOffer(self):
		self.craftIdsOffered = False
		self.craftIdsAnswered = False
		self.craftIdsRequested = False

	def __ServiceItemOpen(self, kind, cell, *choices):
		import uiserviceitem
		if not getattr(self, "serviceItemWindow", None):
			self.serviceItemWindow = uiserviceitem.ServiceItemWindow()
		self.serviceItemWindow.Open(kind, cell, *choices)

	def __ServiceItemRefused(self):
		if getattr(self, "serviceItemWindow", None):
			self.serviceItemWindow.Refused()

	def __ServiceItemResult(self, code, *details):
		if getattr(self, "serviceItemWindow", None):
			self.serviceItemWindow.Result(code, *details)

	def __Level104PassageOffer(self):
		if not self.level104PassageClosed:
			net.SendChatPacket("/level104_passage_ui 1")

	def __Level104Passage(self, phase, count, goal, remaining):
		if self.level104PassageClosed:
			return
		if self.level104PassageHud is None:
			import uilevel104passage
			self.level104PassageHud = uilevel104passage.TrialHud()
		self.level104PassageHud.Receive(phase, count, goal, remaining)

	def __StartDungeonEquipmentBindingSession(self):
		if self.dungeonBindingClosed:
			return
		self.dungeonBindingReady = True
		dungeonequipmentbinding.receiver.BeginSession(self.dungeonBindingOwner)
		if self.dungeonBindingOffered:
			self.__AnswerDungeonEquipmentBindingOffer()
		else:
			self.__RefreshDungeonEquipmentBindingView()

	def __StopDungeonEquipmentBindingSession(self):
		self.dungeonBindingReady = False
		self.dungeonBindingOffered = False
		dungeonequipmentbinding.receiver.EndSession(getattr(self, "dungeonBindingOwner", None))

	def __DungeonEquipmentBindingOffer(self):
		if self.dungeonBindingClosed:
			return
		self.dungeonBindingOffered = True
		self.__AnswerDungeonEquipmentBindingOffer()

	def __AnswerDungeonEquipmentBindingOffer(self):
		if (self.dungeonBindingClosed or not self.dungeonBindingReady or not self.dungeonBindingOffered
				or not dungeonequipmentbinding.receiver.Owns(self.dungeonBindingOwner)):
			return
		self.dungeonBindingOffered = False
		dungeonequipmentbinding.receiver.Offer()
		self.__RefreshDungeonEquipmentBindingView()

	def __DungeonEquipmentBindingEnd(self, serial):
		if (dungeonequipmentbinding.receiver.Owns(self.dungeonBindingOwner)
				and dungeonequipmentbinding.receiver.End(serial)):
			self.__RefreshDungeonEquipmentBindingView()

	def __RefreshDungeonEquipmentBindingView(self):
		if self.interface:
			self.interface.RefreshInventory()
			tooltip = self.interface.tooltipItem
			view = getattr(tooltip, "dungeonBindingView", None)
			if tooltip and tooltip.IsShow() and view:
				tooltip.SetInventoryItem(view[1], view[0])

	def __ServerCommand_Build(self):
		serverCommandList = {
			"ServiceItemOpenV1": self.__ServiceItemOpen,
			"ServiceItemRefusedV1": self.__ServiceItemRefused,
			"ServiceItemResultV1": self.__ServiceItemResult,
			"Level104PassageOfferV1": self.__Level104PassageOffer,
			"Level104PassageV1": self.__Level104Passage,
			"DungeonEquipmentBindingOfferV1": self.__DungeonEquipmentBindingOffer,
			"DungeonEquipmentBindingBeginV1": dungeonequipmentbinding.receiver.Begin,
			"DungeonEquipmentBindingSlotV1": dungeonequipmentbinding.receiver.Slot,
			"DungeonEquipmentBindingEndV1": self.__DungeonEquipmentBindingEnd,
			"PetAlbumCapabilityV1": self.__PetAlbumCapability,
			"AchievementNoticeV1": self.interface.ShowAchievementNotice,
			"FeatureAvailabilityV1": featureavailability.receiver.Receive,
			"EconomyViewV1": npcsellprice.receiver.Receive,
			"AltheaMeteorLockV1": self.meteorProtection.receive,
			"AltheaMeteorLockRemoveV1": self.meteorProtection.remove,
			"AltheaMeteorNoticeV1": self.interface.ShowAltheaMeteorNotice,
			"MissionBookStateV1": self.__MissionBookState,
			"MissionBookErrorV1": self.__MissionBookError,
			"MissionBookRewardV1": self.__MissionBookReward,
			"BonusCatalogV1": bonusCatalog.Receive,
			"SwitchbotOptionsV1": switchbotOptions.Receive,
			"SwitchbotInstantOptionsV1": instantOptions.Receive,
			"SwitchbotInstantStartedV1": instantOptions.Started,
			"SwitchbotInstantResultV1": self.SwitchbotInstantResult,
			"SwitchbotRarityV1": switchbotOptions.ReceiveMetadata,
			"SwitchbotRefusedV1": self.__SwitchbotRefused,
			"PvmPersonalV1": self.__PvmPersonalSnapshot,
			"DuelResultV1": self.__DuelResult,
			"ResonanceSealValuesV1": self.__ReceiveResonanceSealValues,
			"CaptchaV4Stage" : self.CaptchaV4Stage,
			"ConsoleEnable" : self.__Console_Enable,
			"DayMode" : self.__DayMode_Update,
			"PRESERVE_DayMode" : self.__PRESERVE_DayMode_Update,
			"CloseRestartWindow" : self.__RestartDialog_Close,
			"OpenPrivateShop" : self.__PrivateShop_Open,
			"PartyHealReady" : self.PartyHealReady,
			"ShowMeSafeboxPassword" : self.AskSafeboxPassword,
			"CloseSafebox" : self.CommandCloseSafebox,

			# ITEM_MALL
			"CloseMall" : self.CommandCloseMall,
			"ShowMeMallPassword" : self.AskMallPassword,
			"item_mall" : self.__ItemMall_Open,
			# END_OF_ITEM_MALL

			"RefineSuceeded" : self.RefineSuceededMessage,
			"RefineFailed" : self.RefineFailedMessage,
			"xmas_snow" : self.__XMasSnow_Enable,
			"xmas_boom" : self.__XMasBoom_Enable,
			"xmas_song" : self.__XMasSong_Enable,
			"xmas_tree" : self.__XMasTree_Enable,
			"newyear_boom" : self.__XMasBoom_Enable,
			"PartyRequest" : self.__PartyRequestQuestion,
			"PartyRequestDenied" : self.__PartyRequestDenied,
			"horse_state" : self.__Horse_UpdateState,
			"hide_horse_state" : self.__Horse_HideState,
			"GuildV2Disband" : self.interface.OpenGuildDisband,
			"GuildV2Leave" : self.interface.OpenGuildLeave,
			"GuildPortalQuest" : self.__GuildPortalQuest,
			"GuildPortalLobby" : self.__GuildPortalLobby,
			"GuildPortalLobbyOpen" : self.__GuildPortalLobbyOpen,
			"GuildPortalGolem" : self.__GuildPortalGolem,
			"GuildPortalPopup" : self.__GuildPortalPopup,
			"GuildPortalLobbyClose" : self.__GuildPortalLobbyClose,
			"guild_portal_cmd" : self.__GuildPortalQuestCMD,
			"WarUC" : self.__GuildWar_UpdateMemberCount,
			"test_server" : self.__EnableTestServerFlag,
			"mall" : self.__InGameShop_Show,
			"SetAtlasBossState" : self.__SetAtlasBossState,

			# WEDDING
			"lover_login" : self.__LoginLover,
			"lover_logout" : self.__LogoutLover,
			"lover_near" : self.__LoverNear,
			"lover_far" : self.__LoverFar,
			"lover_divorce" : self.__LoverDivorce,
			"PlayMusic" : self.__PlayMusic,
			# END_OF_WEDDING

			"getinputbegin" : self.GetInputBegin,
			"getinputend" : self.GetInputEnd,


			# PRIVATE_SHOP_PRICE_LIST
			"MyShopPriceList" : self.__PrivateShop_PriceList,
			# END_OF_PRIVATE_SHOP_PRICE_LIST
		}

		if app.ENABLE_OFFLINE_SHOP:
			serverCommandList.update({
				"OfflineShop" : self.__OfflineShop,
				"OfflineShopDestroy" : self.__OfflineShopDestroy,
				"StartOpeningOfflineShop" : self.__StartOpeningOfflineShop,
				"CancelOpeningOfflineShop" : self.__CancelOpeningOfflineShop,
				"UpdateDecorationTime" : self.__UpdateDecorationTime,
				"AddSellLog" : self.AddSellLog,
				"RefreshSellLog" : self.RefreshSellLog,
				"RevertPageSellLog" : self.RevertPageSellLog,
				"UpdateSellLog" : self.UpdateSellLog,
			})

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			serverCommandList.update({
			"OpenSkillUpgrade" : self.__SkillUpgrade_Open,
			})

		if app.ENABLE_GEM_SYSTEM:
			serverCommandList.update({
				"OpenGuiGem" : self.OpenGuiGem,
				"GemCheck" : self.GemCheck,
				"OpenGuiGemMarket" : self.OpenGuiGemMarket,
				"GemMarketSlotsDesblock" : self.GemMarketSlotsDesblock,
				"GemMarketItems" : self.GemMarketItems,
				"GemMarketClear" : self.GemMarketClear,
				"GemMarketTime" : self.GemTimeMarket,
			})

		if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			serverCommandList.update({
				"IsAFKMode" : self.IsAFKMode,
				"ShowCaptcha" : self.ShowCaptcha,
			})

		if app.ENABLE_12ZI:
			serverCommandList.update({
				"SetMissionMessage" : self.BINARY_SetMissionMessage,
				"SetSubMissionMessage" : self.BINARY_SetSubMissionMessage,
				"CleanMissionMessage" : self.BINARY_CleanMissionMessage,
			})

		if app.ENABLE_HIDE_COSTUME_SYSTEM:
			serverCommandList.update({
				"SetBodyCostumeHidden" : self.SetBodyCostumeHidden,
				"SetHairCostumeHidden" : self.SetHairCostumeHidden,
				"SetAcceCostumeHidden" : self.SetAcceCostumeHidden,
				"SetWeaponCostumeHidden" : self.SetWeaponCostumeHidden,
				"SetAcceSkinHidden" : self.SetAcceSkinHidden,
				"SetAuraCostumeHidden" : self.SetAuraCostumeHidden,
				"SetShiningWeaponHidden" : self.SetShiningWeaponHidden,
				"SetShiningArmorHidden" : self.SetShiningArmorHidden,
				"SetMountHidden" : self.SetMountHidden,
			})

		if app.ENABLE_EXPRESSING_EMOTION:
			serverCommandList.update({
				"RegisterSpecialEmotion" : self.RegisterSpecialEmotion,
				"ClearSpecialEmotions" : self.ClearSpecialEmotions,
			})

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			serverCommandList.update({
				"OpenSpecialInventoryWindow" : self.OpenSpecialInventoryWindow,
			})

		if app.ENABLE_MULTI_FARM_BLOCK:
			serverCommandList.update({"UpdateMultiFarmAffect" : self.UpdateMultiFarmAffect})
			serverCommandList.update({"UpdateMultiFarmPlayer" : self.UpdateMultiFarmPlayer})

		serverCommandList.update({
			"OpenCostumeWindow" : self.OpenCostumeWindow,
			"OpenInventoryWindow" : self.OpenInventoryWindow,
			"OpenTeleportAtlas" : self.OpenTeleportAtlas,
		})
		if app.ENABLE_GROWTH_PET_SYSTEM:
			serverCommandList["PetGrowthPreview"] = self.interface.PetGrowthPreview

		if app.ENABLE_MOVE_CHANNEL:
			serverCommandList.update({
				"ChannelInfo" : self.ChannelInfo
			})

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			serverCommandList["ShowChangeDialog"] = self.__ChangeWindowOpen

		if app.ENABLE_SOUL_SYSTEM:
			serverCommandList["RefineSoulSuceeded"] = self.__RefineSoulSuceededMessage
			serverCommandList["RefineSoulFailed"] = self.__RefineSoulFailedMessage

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			serverCommandList["OpenSkillbookCombinationDialog"] = self.OpenSkillbookCombinationDialog

		if app.ENABLE_SKILL_SELECT_GUI:
			serverCommandList.update({
				"selectskill_open" : self.OPEN_SKILL_SELECT,
			})

		if app.ENABLE_BIOLOG_SYSTEM:
			serverCommandList.update({
				"BiologBegin2" : self.SetBioBegin2,
				"BiologRow2" : self.SetBioRow2,
				"BiologRow3" : self.SetBioRow3,
				"BiologEnd2" : self.SetBioEnd2,
				"BiologRequestV1" : self.SetBioRequestV1,
				"BiologRevisionV1" : self.SetBioRevisionV1,
				"BiologResultV1" : self.SetBioResultV1,
				"BiologData" : self.SetBioData,
				"BiologStone" : self.SetBioStone,
				"BiologReward" : self.SetBioGift,
				"BiologEmpty" : self.SetBioEmpty,				
			})

		if app.ENABLE_WIKI:
			serverCommandList["WikiCatalogV1"] = self.interface.OnWikiCatalog
			serverCommandList["LiveCatalogV1"] = self.interface.OnLiveCatalog

		# Guild catalogue applications (root/uiguildv2katalog.py).
		serverCommandList["GuildAppV1"] = self.interface.OnGuildApplication

		# Craft book (uicraftbook): the answer to "/craft state", one snapshot of CraftBeginV1 ... CraftEndV1 lines.
		serverCommandList.update({
		})


		if app.ENABLE_WHEEL_OF_FORTUNE:
			serverCommandList.update({"SetItemData" : self.interface.SetItemData})
			serverCommandList.update({"OnSetWheel" : self.interface.OnSetWheel})
			serverCommandList.update({"GetGiftData" : self.interface.GetGiftData})

		if app.ENABLE_TELEPORT_WINDOW:
			serverCommandList["teleportpanel"] = self.TeleportReciveQuestCommand

		if app.ENABLE_DISCORD_STUFF:
			serverCommandList.update({"message_" : self.GetMessage})

		if app.ENABLE_KINGDOMS_WAR:
			serverCommandList.update({"kingdoms_tp" : self.KingdomsEventCalendar})

		if app.ENABLE_PLAYER_RANKING:
			serverCommandList.update({"SetRankingResetInfo" : self.SetRankingResetInfo,
                "GlobalRankingBeginV1": self.interface.GlobalRankingBegin,
                "GlobalRankingRowV1": self.interface.GlobalRankingRow,
                "GlobalRankingEndV1": self.interface.GlobalRankingEnd,
			})

		if app.ENABLE_DESTROY_ITEM_RESTORE:
			serverCommandList.update({"LoadEmptySavedItems" : self.LoadEmptySavedItems})

		if app.ENABLE_BRAVE_CAPE_RENEWAL:
			serverCommandList.update({"SetBraveCapeStatus" : self.SetBraveCapeStatus})

		if app.ENABLE_DUNGEON_INFO:
			serverCommandList.update({
				"dungeon_info_qid" : self.interface.DungeonInfoQuestIdx,
				"dungeon_info_cmd" : self.interface.DungeonInfoQuestCMD,
				"dungeon_info_cooldown" : self.interface.DungeonInfoCooldown,
				"dungeon_log_info" : self.interface.LoadServerData,
				"DungeonRejoinOffer" : self.__DungeonRejoinOffer,
				"DungeonRejoinResult" : self.__DungeonRejoinResult,
				"DungeonRejoinRetry" : self.__DungeonRejoinRetry,
				"DungeonBossDropsBeginV1" : self.interface.DungeonBossDropsBegin,
				"DungeonBossDropsItemV1" : self.interface.DungeonBossDropsItem,
				"DungeonBossDropsEndV1" : self.interface.DungeonBossDropsEnd,
				"dungeon_rejoin_cmd" : self.__DungeonRejoinQuestCMD,
				})

		if app.ENABLE_ITEMSHOP:
			serverCommandList.update({"SetDragonCoin" : self.ItemShopSetDragonCoin})
			serverCommandList["ItemShopClosed"] = self.ItemShopClosed
			serverCommandList["ItemShopMaxCount"] = self.ItemShopMaxCount
			serverCommandList["ItemShopCostumeExchangeRules"] = self.ItemShopCostumeExchangeRules
			serverCommandList["ItemShopCostumeExchangeDone"] = self.ItemShopCostumeExchangeDone

		serverCommandList["AfkRewardCauseV1"] = self.OnAfkRewardCause
		serverCommandList["AfkRewardZonesV1"] = self.OnAfkRewardZones
		serverCommandList["TargetDropOrderV1"] = self.__TargetDropOrder
		if app.ENABLE_VIEW_EQUIPMENT_SYSTEM:
			serverCommandList["ViewEquipInfoV1"] = self.__ViewEquipInfo
		serverCommandList["DungeonObjectiveV1"] = self.__DungeonObjective
		serverCommandList["InputGuardV1"] = self.__InputGuardOffer
		serverCommandList["InputGuardLegendV1"] = self.__InputGuardLegend
		serverCommandList["InputGuardWatchState"] = self.__InputGuardWatchState
		serverCommandList["GMPanelCatalogV1"] = self.__GMPanelCatalog
		serverCommandList["EquipmentBonusesV1"] = itembonuspresentation.totals.Receive
		serverCommandList["CharacterBonusesV1"] = characterbonuses.totals.Receive
		serverCommandList["BonusSourcesV1"] = bonussources.server.Receive
		serverCommandList["QuickEquipReset"] = self.interface.QuickEquipReset
		serverCommandList["QuickEquipSet"] = self.interface.QuickEquipSet
		serverCommandList["QuickEquipItem"] = self.interface.QuickEquipItem
		serverCommandList["QuickEquipReady"] = self.interface.QuickEquipReady
		serverCommandList["QuickEquipStatus"] = self.interface.QuickEquipStatus
		serverCommandList["CraftSelectionV1"] = self.__CraftSelectionCapability
		serverCommandList["CraftSelectionSourceV1"] = self.__CraftSelectionSource
		serverCommandList["CraftIdsV1"] = self.__CraftIdsOffer
		serverCommandList["CraftToolShopV1"] = self.__CraftToolShop
		serverCommandList["CraftToolOpenV1"] = self.__CraftToolOpen
		serverCommandList["CraftToolV1"] = self.__CraftToolState
		serverCommandList["TalismanSet5V1"] = self.__TalismanSetCapability
		serverCommandList["TalismanSetError"] = self.__TalismanSetError
		# Unstuck countdown, cancel reason and result (root/uiunstuck.py)
		serverCommandList["UnstuckCountdown"] = uiunstuck.controller.OnCountdown
		serverCommandList["UnstuckCancel"] = uiunstuck.controller.OnCancel
		serverCommandList["UnstuckDone"] = uiunstuck.controller.OnDone

		if app.ENABLE_REWARD_SYSTEM:
			serverCommandList.update({"RewardInfo" : self.SetRewardPlayers})

		if app.ENABLE_ANTI_EXP:
			serverCommandList.update({"SetAntiExp" : self.SetAntiExp})

		if app.ENABLE_DUNGEON_TIME_WINDOW:
			serverCommandList["SetDungeonTime"]    = self.__SetDungeonTime
			serverCommandList["HideDungeonTime"]    = self.__HideDungeonTime

		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			serverCommandList.update({
				"CloseLoadSafeboxEvent" : self.__CloseLoadSafeboxEvent,
				"CloseLoadMallEvent" : self.__CloseLoadMallEvent,
			})

		if app.ENABLE_CAPTCHA_NEW and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			serverCommandList.update({
				"ShowCaptcha" : self.ShowCaptchaNew,
				"Captcha_index" : self.__Captcha_index,
			})

		if app.ENABLE_BUFF_SYSTEM:
			serverCommandList.update({
			"samanboard" : self.OpenSupportGui,
			"OpenSupportUpgrade" : self.OpenSupportUpgrade,
			"BuffiNameRequest" : self.OpenBuffiNameDialog,
			"SupportName" : self.SetSupportName,
			"BuffiVisual" : self.SetBuffiVisual,
			"SupportLeave" : self.SupportLeave,
			"SupporInt" : self.SetSupportInt,
			"SupportArmor" : self.SetSupportArmor,
			"SupportAcce" : self.SetSupportAcce,
			"SupportWeapon" : self.SetSupportWeapon,
			"SupportHair" : self.SetSupportHair,
			"SupportShiningArmor" : self.SetShiningArmor,
			"SupportShiningWeapon" : self.SetShiningWeapon,
			"SetBuffPremiumSkill" : self.SetBuffPremiumSkill,
			"BuffiProgress" : self.SetBuffiProgress,
			})

		if app.ENABLE_BATTLE_PASS:
			serverCommandList.update({
			"BP_CLEAR" : self.BattlePassClear,
			"BP_ACTIVATED" : self.BattlePassActive,
			"BP_UPDATE" : self.BattlePassUpdate,
			"BP_INFO" : self.BattlePassInfo,
			"BP_INFOR" : self.BattlePassInfoReward,
			"BP_INFOG" : self.BattlePassInfoGeneral,
			"BP_SHOP_COIN" : self.ShowShopCoinBattlePass,
			})

		if app.ENABLE_ATTR_6TH_7TH:
			serverCommandList["__OpenAttr67AddDlg"] = self.__OpenAttr67AddDlg

		if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
			serverCommandList["clear_guild_reddragonlair_ranking"] = self.__ClearGuildRedDragonLairRanking
			serverCommandList["check_reddragonlairranking_board"] = self.__CheckRedDragonLairRanking

		# ALTHEA-626: ignore old tracker pushes without constructing a window.
		serverCommandList["SetBossTrack"] = self.interface.SetBossTrack

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			serverCommandList["auto_off"] = self.__AutoOff
			serverCommandList["auto_on"] = self.__AutoOn
			serverCommandList["auto_loginoff"] = self.__AutoLoginOff

		if app.ENABLE_DROP_INFO_WINDOW:
			serverCommandList["DropInfo"] = self.RecvDropInfo
		if getattr(app, "ENABLE_DROP_TRACKER", 0):
			serverCommandList["DropTrackerGatherV1"] = self.__DropTrackerGatherOffer
		serverCommandList["DungeonTicketUsed"] = self.__DungeonTicketUsed
		serverCommandList["AttrChangeCountV1"] = self.__AttrChangeCount

		if app.ENABLE_SEND_TARGET_INFO:
			serverCommandList["TargetDropLevelGapV1"] = self.__TargetDropLevelGap

		if app.ENABLE_NEW_DROP_DIALOG:
			serverCommandList["ItemDestroyResultV1"] = self.__ItemDestroyResult

		if app.ENABLE_MAINTENANCE_SYSTEM:
			serverCommandList["maintenance_reason"] = self.__MaintenanceReason

		self.serverCommander = stringCommander.Analyzer()
		for serverCommandItem in serverCommandList.items():
			self.serverCommander.SAFE_RegisterCallBack(
				serverCommandItem[0], serverCommandItem[1],
				# Fixed arity drops surplus tokens; these lines keep every token.
				variadic=serverCommandItem[0] in ("WikiCatalogV1", "EconomyViewV1", "LiveCatalogV1", "GuildAppV1",
					"CraftToolShopV1", "CraftToolOpenV1", "CraftToolV1",
					"UnstuckCountdown", "UnstuckCancel", "UnstuckDone",
					"ServiceItemOpenV1", "ServiceItemResultV1")
			)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def __ChangeWindowOpen(self, type):
			self.interface.ChangeWindowOpen(type)

	def __DuelResult(self, winner, loser, winnerDamage, loserDamage, winnerHP, winnerMaxHP, durationMs):
		# Server-src feat/duel-result-20261009: the result of a duel death.
		if self.interface:
			self.interface.RecvDuelServerResult(winner, loser, winnerDamage, loserDamage,
				winnerHP, winnerMaxHP, durationMs)

	# Keep the complete record: fixed-arity stringCommander drops excess fields.
	def __CraftBookLine(self, command, *args):
		if self.interface:
			self.interface.CraftBookServerLine(command, args)

	# Preserve variadic tool records for crafttoolmodel validation.
	def __CraftToolShop(self, *args):
		if self.interface:
			self.interface.CraftToolServerLine("CraftToolShopV1", args)

	def __CraftToolOpen(self, *args):
		if self.interface:
			self.interface.CraftToolServerLine("CraftToolOpenV1", args)

	def __CraftToolState(self, *args):
		if self.interface:
			self.interface.CraftToolServerLine("CraftToolV1", args)

	def __TargetDropOrder(self, race, append, vnums):
		dropsort.ReceiveOrder(race, append, vnums)

	def __ViewEquipInfo(self, vid, level, race, special3, special4):
		# the viewed player's level and race and the vnums of the
		# special items 3 / 4, sent right after the view-equipment packet; the R1 Vyzbroj shows them.
		if not self.interface:
			return
		try:
			values = [int(value) for value in (vid, level, race, special3, special4)]
		except ValueError:
			return
		self.interface.SetEquipmentDialogInfo(*values)

	def BINARY_ServerCommand_Run(self, line):
		if line.split()[:1] == ["EventBoxV1"]:
			import eventboxmodel
			eventboxmodel.ServerLine(line)
			return 1
		if line.lstrip().startswith("GuildArena"):
			# guild wars / guild arena state for the tab Cechy of the arena window (the server's /guild_arena)
			try:
				import guildarena
				tokens = line.split()
				if tokens[0] == "GuildArenaWarriorsV1":
					guildarena.ReceiveWarriors(tokens[1:])
				else:
					guildarena.Receive(tokens[1:])
			except Exception:
				dbg.TraceError("GuildArenaV1: %s" % line)
		if line.startswith("MarketSalesV1"):
			# Sale history of "Můj obchod" (root/marketsaleshistory.py, server /market_sales).
			import marketsaleshistory
			marketsaleshistory.ServerLine(line)
			return 1
		if line.startswith("GuildCosmV1"):
			# guild cosmetics / DM treasury (root/guildcosmetic.py, server game/src/guild_cosmetic.cpp)
			import guildcosmetic
			guildcosmetic.ServerLine(line)
			return 1
		if line.lstrip().startswith("MiningCheck"):
			tokens = line.split()
			if tokens[0] in ("MiningCheckV1", "MiningCheckResultV1", "MiningCheckModeV1"):
				if self.interface:
					self.interface.MiningCheckServerLine(tokens[0], tokens[1:])
				return
		if line.lstrip().startswith("CraftMastery"):
			# craft mastery tree (root/craftmasterymodel.py)
			tokens = line.split()
			if self.interface:
				self.interface.CraftMasteryServerLine(tokens[0], tokens[1:])
			return 1
		if line.lstrip().startswith("CraftContract"):
			# craft contracts in the Denní úkoly window (root/craftcontractmodel.py)
			tokens = line.split()
			if self.interface:
				self.interface.CraftContractServerLine(tokens[0], tokens[1:])
			return 1
		if line.lstrip().startswith("CraftTitle"):
			# own craft titles and tool looks (root/crafttitlesmodel.py, the book's Tituly a vzhled page)
			tokens = line.split()
			if self.interface:
				self.interface.CraftTitlesServerLine(tokens[0], tokens[1:])
			return 1
		if line.lstrip().startswith("WoodCheck"):
			tokens = line.split()
			if tokens[0] in ("WoodCheckV3", "WoodCheckV2", "WoodCheckResultV1", "WoodCheckEndV1", "WoodCheckModeV1"):
				if self.interface:
					self.interface.WoodCheckServerLine(tokens[0], tokens[1:])
				return
		if line.lstrip().startswith("Craft"):
			import craftbookmodel
			tokens = line.split()
			if tokens[0] == "CraftChangedV1":
				if self.interface:
					self.interface.CraftBookChanged()
				return 1
			if tokens[0] in craftbookmodel.ARITY:
				self.__CraftBookLine(tokens[0], *tokens[1:])
				return 1
		#dbg.TraceError(line)
		try:
			#print " BINARY_ServerCommand_Run", line
			return self.serverCommander.Run(line)
		except RuntimeError as msg:
			dbg.TraceError(msg)
			return 0

	def __TicketNoticeWindow(self):
		if self.ticketNotice is None:
			self.ticketNotice = uiticketnotice.TicketNotice()
		return self.ticketNotice

	def __ShowTicketNotice(self, notice):
		if notice:
			vnum, count, context = notice
			self.__TicketNoticeWindow().Push(vnum, count, context)

	def __PollTicketNotice(self):
		try:
			mapName = background.GetCurrentMapName()
		except Exception:
			return
		for notice in ticketnoticemodel.STATE.Poll(player.GetItemCountByVnum, mapName, app.GetTime(), player.GetName()):
			self.__ShowTicketNotice(notice)

	def __DungeonTicketUsed(self, vnum, count):
		self.__ShowTicketNotice(ticketnoticemodel.STATE.OnServerUsed(vnum, count, app.GetTime()))

	def __AttrChangeCount(self, windowType, cell, count):
		try:
			attrchangecount.Set(int(windowType), int(cell), int(count))
		except (TypeError, ValueError):
			pass

	def __MissionBookState(self, book, mission, p1, p2, p3, ready):
		if self.interface:
			self.interface.MissionBookState(book, mission, p1, p2, p3, ready)

	def __MissionBookError(self, reason):
		from missionbooklocale import Text
		if reason in ("ACTIVE", "LEVEL", "FULL"):
			chat.AppendChat(chat.CHAT_TYPE_INFO, Text("ERROR_" + reason))

	def __MissionBookReward(self, chest):
		from missionbooklocale import Text
		if chest in ("50350", "50351", "50352", "50353", "50354", "50355"):
			chat.AppendChat(chat.CHAT_TYPE_INFO, Text("REWARD_RECEIVED"))

	def __DungeonObjective(self, sequence, instance, boss, phase, phases, key, current, target, status):
		if self.seamlessWarping:
			return
		# stringCommander dispatches co_argcount positional fields; *args loses them.
		arguments = (sequence, instance, boss, phase, phases, key, current, target, status)
		if self.interface and self.interface.wndMiniMap:
			if self.interface.wndMiniMap.SetDungeonObjective(*arguments):
				self.dungeonObjectiveSubscription.stop()

	def __TalismanSetCapability(self, enabled):
		if enabled not in ("0", "1"):
			return 0
		if not self.interface:
			return 0
		return self.interface.SetTalismanSetCapability(int(enabled))

	def __TalismanSetError(self, code, value):
		if code == "HEART_REQUIRE":
			try:
				requiredRefine = int(value)
			except (TypeError, ValueError):
				return 0
			message = localeInfo.TALISMAN_ERROR_HEART_REQUIRE % requiredRefine
		elif code == "HEART_LOCK":
			message = localeInfo.TALISMAN_ERROR_HEART_LOCK
		else:
			return 0
		chat.AppendChat(chat.CHAT_TYPE_INFO, message)
		return 1

	def BINARY_CaptchaV3(self, status, attemptsRemaining, sessionId, generation,
		deadlineAt, retryAt, pixels):
		if self.interface and getattr(app, "ENABLE_CAPTCHA_V3", 0):
			self.interface.OpenCaptchaV3(status, attemptsRemaining, sessionId,
				generation, deadlineAt, retryAt, pixels)

	def BINARY_CaptchaV4(self, status, attemptsRemaining, sessionId, generation,
        deadlineAt, retryAt, pixels, originX, originY, heldPixels):
		if self.interface and getattr(app, "ENABLE_CAPTCHA_V4", 0):
			self.interface.OpenCaptchaV4(status, attemptsRemaining, sessionId,
				generation, deadlineAt, retryAt, pixels, originX, originY, heldPixels)

	def CaptchaV4Stage(self, sessionId, generation, stage):
		if self.interface and getattr(app, "ENABLE_CAPTCHA_V4", 0):
			self.interface.SetCaptchaV4Stage(sessionId, generation, stage)

	def BINARY_CaptchaV2(self, *unused):
		# Retired answer-bearing protocol: a mixed cohort cannot resume v2.
		return

	def __ProcessPreservedServerCommand(self):
		self.petAlbumPreserving = True
		try:
			command = net.GetPreservedServerCommand()
			while command:
				print(" __ProcessPreservedServerCommand", command)
				self.serverCommander.Run(command)
				command = net.GetPreservedServerCommand()
		except RuntimeError as msg:
			dbg.TraceError(msg)
			return 0
		finally:
			self.petAlbumPreserving = False

	def __SetAtlasBossState(self, markerId, alive, remainingSeconds, activeVid):
		try:
			markerId = int(markerId)
			alive = int(alive)
			remainingSeconds = int(remainingSeconds)
			activeVid = int(activeVid)
		except (TypeError, ValueError):
			return

		if markerId < 0 or alive not in (0, 1) or remainingSeconds < 0 or activeVid < 0:
			return

		miniMap.SetAtlasBossState(markerId, alive, remainingSeconds, activeVid)

	def PartyHealReady(self):
		self.interface.PartyHealReady()

	def AskSafeboxPassword(self):
		self.interface.AskSafeboxPassword()

	if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
		def OpenSkillbookCombinationDialog(self):
			self.interface.OpenSkillbookCombinationDialog()

	# ITEM_MALL
	def AskMallPassword(self):
		self.interface.AskMallPassword()

	def __ItemMall_Open(self):
		self.interface.OpenItemMall();

	def CommandCloseMall(self):
		self.interface.CommandCloseMall()
	# END_OF_ITEM_MALL


	if app.ENABLE_TELEPORT_WINDOW:
		def TeleportReciveQuestCommand(self, command):
			self.interface.ReceiveTeleportQuestCommand(command)

	def __SwitchbotRefused(self, mode, index, code, first, second):
		# ALTHEA-647: the server says why a switchbot start was refused.
		# a start of an item that already has the bonuses is not told but asked: roll it anyway?
		if mode == "slot" and code == "SLOT_MATCHED" and self.interface:
			try:
				if self.interface.AskSwitchbotReroll(int(index)):
					return
			except ValueError:
				pass
		import switchbotrefusals
		chat.AppendChat(chat.CHAT_TYPE_INFO, switchbotrefusals.Message(code, first, second))

	def SwitchbotInstantResult(self, success, attempts):
		instantOptions.Finish()
		if int(success):
			self.PopupMessage('Předmět byl úspěšně natočen. Použil jsi %s začarování.' %
				localeInfo.NumberToString(int(attempts)))

	def RefineSuceededMessage(self):
		snd.PlaySound("sound/ui/make_soket.wav")
		if app.ENABLE_AUTO_REFINE:
			self.interface.RefineFail(False)
			if osfInfo.IS_AUTO_REFINE:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.REFINE_SUCCESS)
			else:
				self.PopupMessage(localeInfo.REFINE_SUCCESS)
		else:
			self.PopupMessage(localeInfo.REFINE_SUCCESS)

	def RefineFailedMessage(self):
		snd.PlaySound("sound/ui/jaeryun_fail.wav")
		if app.ENABLE_AUTO_REFINE:
			self.interface.RefineFail(True)
			if osfInfo.IS_AUTO_REFINE:
				msg = localeInfo.REFINE_FAILURE
				for line in msg.replace("\\n", "\n").split("\n"):
					if line.strip():
						chat.AppendChat(chat.CHAT_TYPE_INFO, line.strip())
			else:
				self.PopupMessage(localeInfo.REFINE_FAILURE)
		else:
			self.PopupMessage(localeInfo.REFINE_FAILURE)

	if app.ENABLE_SOUL_SYSTEM:
		def __RefineSoulSuceededMessage(self):
			snd.PlaySound("sound/ui/make_soket.wav")
			self.PopupMessage(localeInfo.SOUL_REFINE_SUCCESS)

		def __RefineSoulFailedMessage(self):
			snd.PlaySound("sound/ui/jaeryun_fail.wav")
			self.PopupMessage(localeInfo.SOUL_REFINE_FAILURE)

	if app.ENABLE_REFINE_FAIL_TYPE:
		def BINARY_RefineFailedTypeMessage(self, type):
			REFINE_FAILURE_DICT = {
				player.REFINE_FAIL_GRADE_DOWN : localeInfo.REFINE_FAILURE_GRADE_DOWN,
				player.REFINE_FAIL_DEL_ITEM : localeInfo.REFINE_FAILURE_DEL_ITEM,
				player.REFINE_FAIL_KEEP_GRADE : localeInfo.REFINE_FAILURE_KEEP_GRADE,
				player.REFINE_FAIL_MAX : localeInfo.REFINE_FAILURE
			}

			snd.PlaySound("sound/ui/jaeryun_fail.wav")
			msg = REFINE_FAILURE_DICT.get(type, player.REFINE_FAIL_MAX)
			if app.ENABLE_AUTO_REFINE:
				self.interface.RefineFail(True)
				if osfInfo.IS_AUTO_REFINE:
					for line in msg.replace("\\n", "\n").split("\n"):
						if line.strip():
							chat.AppendChat(chat.CHAT_TYPE_INFO, line.strip())
				else:
					self.PopupMessage(msg)
			else:
				self.PopupMessage(msg)

	def CommandCloseSafebox(self):
		self.interface.CommandCloseSafebox()

	# PRIVATE_SHOP_PRICE_LIST
	def __PrivateShop_PriceList(self, itemVNum, itemPrice):
		uiPrivateShopBuilder.SetPrivateShopItemPrice(itemVNum, itemPrice)
	# END_OF_PRIVATE_SHOP_PRICE_LIST

	def __Horse_HideState(self):
		self.affectShower.SetHorseState(0, 0, 0)

	def __Horse_UpdateState(self, level, health, battery):
		self.affectShower.SetHorseState(int(level), int(health), int(battery))

	if app.ENABLE_CONQUEROR_LEVEL:
		def BINARY_SungMaAttr(self, str, hp, move, immune):
			self.affectShower.SetSungMaAffectImage(str, hp, move, immune)

	def __IsXMasMap(self):
		mapDict = (
			"metin2_map_n_flame_01",
			"metin2_map_n_desert_01",
			"metin2_map_spiderdungeon_01",
			"metin2_map_spiderdungeon_02",
			"metin2_map_spiderdungeon_03",
			"metin2_map_deviltower1",
			"metin2_map_sungzi_flame_hill_01",
			"metin2_map_sungzi_flame_hill_02",
			"metin2_map_sungzi_flame_hill_03",
			"metin2_map_sungzi_desert_01",
			"metin2_map_sungzi_desert_hill_01",
			"metin2_map_sungzi_desert_hill_02",
			"metin2_map_sungzi_desert_hill_03",
			"metin2_map_empirewar03",
			"metin2_map_devilsCatacomb",
			"metin2_map_Mt_Thunder",
			"metin2_map_n_flame_dungeon_01",
			"metin2_map_dawnmist_dungeon_01",
			"metin2_map_Mt_Th_dungeon_01",
		)

		if background.GetCurrentMapName() in mapDict:
			return False

		return True

	def __XMasSnow_Enable(self, mode):

		self.__XMasSong_Enable(mode)

		if "1"==mode:

			if not self.__IsXMasMap():
				return

			print("XMAS_SNOW ON")
			background.EnableSnow(1)

		else:
			print("XMAS_SNOW OFF")
			background.EnableSnow(0)

	def __XMasBoom_Enable(self, mode):
		if "1"==mode:

			if not self.__IsXMasMap():
				return

			print("XMAS_BOOM ON")
			self.__DayMode_Update("dark")
			self.enableXMasBoom = True
			self.startTimeXMasBoom = app.GetTime()
		else:
			print("XMAS_BOOM OFF")
			self.__DayMode_Update("light")
			self.enableXMasBoom = False

	def __XMasTree_Enable(self, grade):

		print("XMAS_TREE ", grade)
		background.SetXMasTree(int(grade))

	def __XMasSong_Enable(self, mode):
		if "1"==mode:
			print("XMAS_SONG ON")

			XMAS_BGM = "xmas.mp3"

			if app.IsExistFile("BGM/" + XMAS_BGM)==1:
				if musicInfo.fieldMusic != "":
					snd.FadeOutMusic("BGM/" + musicInfo.fieldMusic)

				musicInfo.fieldMusic=XMAS_BGM
				snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

		else:
			print("XMAS_SONG OFF")

			if musicInfo.fieldMusic != "":
				snd.FadeOutMusic("BGM/" + musicInfo.fieldMusic)

			musicInfo.fieldMusic=musicInfo.METIN2THEMA
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

	def __RestartDialog_Close(self):
		self.interface.CloseRestartDialog()

	def __Console_Enable(self):
		self.consoleEnable = True
		app.EnableSpecialCameraMode()
		ui.EnablePaste(True)
		self.ShowConsole()

	## PrivateShop
	def __PrivateShop_Open(self):
		self.interface.OpenPrivateShopInputNameDialog()

	def BINARY_PrivateShop_Appear(self, vid, text):
		self.interface.AppearPrivateShop(vid, text)

	def BINARY_PrivateShop_Disappear(self, vid):
		self.interface.DisappearPrivateShop(vid)

	if app.ENABLE_MINI_GAME_OKEY:
		## MiniGame Rumi
		def BINARY_Cards_UpdateInfo(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, hand_4, hand_4_v, hand_5, hand_5_v, cards_left, points):
			self.interface.UpdateCardsInfo(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, hand_4, hand_4_v, hand_5, hand_5_v, cards_left, points)

		def BINARY_Cards_FieldUpdateInfo(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points):
			self.interface.UpdateCardsFieldInfo(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points)

		def BINARY_Cards_PutReward(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points):
			self.interface.CardsPutReward(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points)

		def BINARY_Cards_ShowIcon(self, active):
			IsRumiGameEvent = int(active)
			if IsRumiGameEvent > 0:
				osfInfo.RUMI_GAME_EVENT = True
			else:
				osfInfo.RUMI_GAME_EVENT = False

			if osfInfo.EVENT_BANNER == True:
				self.interface.IntegrationEventBanner()
			else:
				self.interface.MiniGameOkey()

		def BINARY_Cards_Open(self, safemode):
			self.interface.OpenCardsWindow(safemode)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def MiniGameCatchKingEvent(self, isEnable):
			if self.interface:
				self.interface.SetCatchKingEventStatus(isEnable)
				if osfInfo.EVENT_BANNER == True:
					self.interface.IntegrationEventBanner()

		def MiniGameCatchKingEventStart(self, bigScore):
			self.interface.MiniGameCatchKingEventStart(bigScore)

		def MiniGameCatchKingSetHandCard(self, cardNumber):
			self.interface.MiniGameCatchKingSetHandCard(cardNumber)

		def MiniGameCatchKingResultField(self, score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear):
			self.interface.MiniGameCatchKingResultField(score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear)

		def MiniGameCatchKingSetEndCard(self, cardPos, cardNumber):
			self.interface.MiniGameCatchKingSetEndCard(cardPos, cardNumber)

		def MiniGameCatchKingReward(self, rewardCode):
			self.interface.MiniGameCatchKingReward(rewardCode)

	## DayMode
	def __PRESERVE_DayMode_Update(self, mode):
		if "light"==mode:
			background.SetEnvironmentData(0)
		elif "dark"==mode:

			if not self.__IsXMasMap():
				return

			background.RegisterEnvironmentData(1, constInfo.ENVIRONMENT_NIGHT)
			background.SetEnvironmentData(1)

	def __DayMode_Update(self, mode):
		# One curtain at a time: under the warp curtain apply it directly.
		warpLocked = getattr(getattr(self, "stream", None), "IsWarpCurtainInputLocked", None)
		if getattr(self, "seamlessWarping", False) or (warpLocked and warpLocked()):
			self.__PRESERVE_DayMode_Update(mode)
			return

		if self.initialWorldRevealPending:
			self.initialWorldRevealDayMode = mode
			return

		if "light"==mode:
			self.curtain.SAFE_FadeOut(self.__DayMode_OnCompleteChangeToLight)
		elif "dark"==mode:

			if not self.__IsXMasMap():
				return

			self.curtain.SAFE_FadeOut(self.__DayMode_OnCompleteChangeToDark)

	def __DayMode_OnCompleteChangeToLight(self):
		background.SetEnvironmentData(background.DAY_MODE_LIGHT)
		self.curtain.FadeIn()

	def __DayMode_OnCompleteChangeToDark(self):
		background.RegisterEnvironmentData(background.DAY_MODE_DARK, constInfo.ENVIRONMENT_NIGHT)
		background.SetEnvironmentData(background.DAY_MODE_DARK)
		self.curtain.FadeIn()

	## XMasBoom
	def __XMasBoom_Update(self):
		self.BOOM_DATA_LIST = ( (2, 5), (5, 2), (7, 3), (10, 3), (20, 5) )
		if self.indexXMasBoom >= len(self.BOOM_DATA_LIST):
			return

		boomTime = self.BOOM_DATA_LIST[self.indexXMasBoom][0]
		boomCount = self.BOOM_DATA_LIST[self.indexXMasBoom][1]

		if app.GetTime() - self.startTimeXMasBoom > boomTime:
			self.indexXMasBoom += 1

			for i in range(boomCount):
				self.__XMasBoom_Boom()

	def __XMasBoom_Boom(self):
		x, y, z = player.GetMainCharacterPosition()
		randX = app.GetRandom(-150, 150)
		randY = app.GetRandom(-150, 150)

		snd.PlaySound3D(x+randX, -y+randY, z, "sound/common/etc/salute.mp3")

	if app.WJ_NEW_USER_CARE:
		def __PartyRequestQuestion(self, vid, name):
			vid = int(vid)
			partyRequestQuestionDialog = uiCommon.QuestionDialogWithTimeLimit()
			partyRequestQuestionDialog.SetAcceptText(localeInfo.UI_ACCEPT)
			partyRequestQuestionDialog.SetCancelText(localeInfo.UI_DENY)
			partyRequestQuestionDialog.SetAcceptEvent(lambda arg=True: self.__AnswerPartyRequest(arg))
			partyRequestQuestionDialog.SetCancelEvent(lambda arg=False: self.__AnswerPartyRequest(arg))
			partyRequestQuestionDialog.Open(name + localeInfo.PARTY_DO_YOU_ACCEPT, 10)
			partyRequestQuestionDialog.SetTimeOverMsg(localeInfo.PARTY_ANSWER_TIMEOVER)
			partyRequestQuestionDialog.SetCancelOnTimeOver()
			partyRequestQuestionDialog.vid = vid
			self.partyRequestQuestionDialog = partyRequestQuestionDialog
	else:
		def __PartyRequestQuestion(self, vid):
			vid = int(vid)
			partyRequestQuestionDialog = uiCommon.QuestionDialog()
			partyRequestQuestionDialog.SetText(chr.GetNameByVID(vid) + localeInfo.PARTY_DO_YOU_ACCEPT)
			partyRequestQuestionDialog.SetAcceptText(localeInfo.UI_ACCEPT)
			partyRequestQuestionDialog.SetCancelText(localeInfo.UI_DENY)
			partyRequestQuestionDialog.SetAcceptEvent(lambda arg=True: self.__AnswerPartyRequest(arg))
			partyRequestQuestionDialog.SetCancelEvent(lambda arg=False: self.__AnswerPartyRequest(arg))
			partyRequestQuestionDialog.Open()
			partyRequestQuestionDialog.vid = vid
			self.partyRequestQuestionDialog = partyRequestQuestionDialog

	def __AnswerPartyRequest(self, answer):
		if not self.partyRequestQuestionDialog:
			return

		vid = self.partyRequestQuestionDialog.vid

		if answer:
			net.SendChatPacket("/party_request_accept " + str(vid))
		else:
			net.SendChatPacket("/party_request_deny " + str(vid))

		self.partyRequestQuestionDialog.Close()
		self.partyRequestQuestionDialog = None

	def __PartyRequestDenied(self):
		self.PopupMessage(localeInfo.PARTY_REQUEST_DENIED)

	if app.ENABLE_COMBAT_ZONE:
		def BINARY_CombatZone_Manager(self, tokens, arg1 = 0, arg2 = 0, arg3 = 0, arg4 = 0):
			if tokens == "OpenWindow":
				self.wndCombatZone.Open(arg1, arg2, arg3, arg4)

			elif tokens == "RegisterRank":
				self.wndCombatZone.RegisterRanking()

			elif tokens == "StartFlashing":
				if self.interface:
					self.interface.wndMiniMap.btnCombatZone.FlashEx()

			elif tokens == "RefreshShop":
				if self.interface:
					self.interface.dlgShop.SetCombatZonePoints(arg1)
					self.interface.dlgShop.SetLimitCombatZonePoints(arg2, arg3)

	def __EnableTestServerFlag(self):
		app.EnableTestServerFlag()

	def __InGameShop_Show(self, url):
		if constInfo.IN_GAME_SHOP_ENABLE:
			self.interface.OpenWebWindow(url)

	# WEDDING
	def __LoginLover(self):
		if self.interface.wndMessenger:
			self.interface.wndMessenger.OnLoginLover()

	def __LogoutLover(self):
		if self.interface.wndMessenger:
			self.interface.wndMessenger.OnLogoutLover()
		if self.affectShower:
			self.affectShower.HideLoverState()

	def __LoverNear(self):
		if self.affectShower:
			self.affectShower.ShowLoverState()

	def __LoverFar(self):
		if self.affectShower:
			self.affectShower.HideLoverState()

	def __LoverDivorce(self):
		if self.interface.wndMessenger:
			self.interface.wndMessenger.ClearLoverInfo()
		if self.affectShower:
			self.affectShower.ClearLoverState()

	def __PlayMusic(self, flag, filename):
		flag = int(flag)
		if flag:
			snd.FadeOutAllMusic()
			musicInfo.SaveLastPlayFieldMusic()
			snd.FadeInMusic("BGM/" + filename)
		else:
			snd.FadeOutAllMusic()
			musicInfo.LoadLastPlayFieldMusic()
			snd.FadeInMusic("BGM/" + musicInfo.fieldMusic)

	if app.ENABLE_KINGDOMS_WAR:
		def ActKingdomsWar(self, act, score1, score2, score3, limitKills, deads, limiDeads, timeRemained):
			if self.interface:
				self.interface.ActKingdomsWar(act, score1, score2, score3, limitKills, deads, limiDeads, timeRemained)

		def KingdomsEventCalendar(self, questindex):
			osfInfo.KINGDOMS_TP = questindex

	# END_OF_WEDDING

	if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
		## HilightSlot Change
		def DeactivateSlot(self, slotindex, type):
			self.interface.DeactivateSlot(slotindex, type)

		## HilightSlot Change
		def ActivateSlot(self, slotindex, type):
			self.interface.ActivateSlot(slotindex, type)

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def ActAcce(self, iAct, bWindow):
			if self.interface:
				self.interface.ActAcce(iAct, bWindow)

		def AlertAcce(self, bWindow):
			snd.PlaySound("sound/ui/make_soket.wav")
			if bWindow:
				(resultVnum, unusedChance, unusedMax) = acce.GetResultItem()
				if resultVnum and uiresonance.IsSealVnum(resultVnum):
					self.PopupMessage(getattr(localeInfo, "RESONANCE_COMBINE_DESTROY", localeInfo.ACCE_DEL_SERVEITEM))
				else:
					self.PopupMessage(localeInfo.ACCE_DEL_SERVEITEM)
			else:
				self.PopupMessage(localeInfo.ACCE_DEL_ABSORDITEM)

	if app.ENABLE_ITEMSHOP:
		def ItemShopClear(self, updateTime):
			uiItemShop.ItemShopClear(int(updateTime))
		def ItemShopAppendItem(self, categoryIndex, categorySubIndex, itemID, itemVnum, itemPrice, itemDiscount, itemOffertime, itemTopSelling, itemAddedTime, itemSellingCount, itemCount=1):
			uiItemShop.ItemShopAppendItem(int(categoryIndex), int(categorySubIndex), int(itemID), int(itemVnum), int(itemPrice), int(itemDiscount), int(itemOffertime), int(itemTopSelling), int(itemAddedTime), int(itemSellingCount), int(itemCount))
		def ItemShopHideLoading(self):
			self.interface.ItemShopHideLoading()
		def ItemShopOpenMainPage(self):
			self.interface.OpenItemShopMainWindow()
		def ItemShopLogClear(self):
			uiItemShop.ItemShopLogClear()
		def ItemShopAppendLog(self, dateText, dateTime, playerName, ipAdress, itemVnum, itemCount, itemPrice):
			uiItemShop.ItemShopAppendLog(str(dateText), int(dateTime), str(playerName), str(ipAdress), int(itemVnum), int(itemCount), int(itemPrice))
		def ItemShopPurchasesWindow(self):
			self.interface.ItemShopPurchasesWindow()
		def ItemShopSetDragonCoin(self, dragonCoin):
			self.interface.ItemShopSetDragonCoin(int(dragonCoin))
		def ItemShopSetReaction(self, itemID, likes, dislikes, myVote):
			uiItemShop.ItemShopSetReaction(int(itemID), int(likes), int(dislikes), int(myVote))
		def ItemShopMaxCount(self, maxCount):
			uiItemShop.ItemShopSetMaxCount(int(maxCount))
		def ItemShopClosed(self):
			# The server refused the request: its item_shop_open gate is off
			# (owner request 2026-10-03). The server stays the authority.
			self.interface.ItemShopClosed()
			self.PopupMessage(getattr(localeInfo, "ITEMSHOP_CLOSED", "The Item Shop is temporarily closed."))
		def ItemShopCostumeExchangeRules(self, count, chests):
			import uiitemshopcostumeexchange
			uiitemshopcostumeexchange.SetRules(count, chests)
		def ItemShopCostumeExchangeDone(self, chest):
			import uiitemshopcostumeexchange
			uiitemshopcostumeexchange.OnDone(int(chest))
			item.SelectItem(int(chest))
			self.PopupMessage(localeInfo.ITEMSHOP_COSTUME_EXCHANGE_DONE % item.GetItemName())

	if app.ENABLE_SKILL_SELECT_GUI:
		def OPEN_SKILL_SELECT(self):
			self.interface.OPEN_SKILL_SELECT()

	if app.ENABLE_EVENT_MANAGER:
		def ClearEventManager(self):
			self.interface.ClearEventManager()
		def RefreshEventManager(self):
			self.interface.RefreshEventManager()
		def RefreshEventStatus(self, eventID, eventStatus, eventendTime, eventEndTimeText):
			self.interface.RefreshEventStatus(int(eventID), int(eventStatus), int(eventendTime), str(eventEndTimeText))
		def AppendEvent(self, dayIndex, eventID, eventIndex, startTime, endTime, empireFlag, channelFlag, value0, value1, value2, value3, value4, value5, value6, value7, startRealTime, endRealTime, isAlreadyStart):
			self.interface.AppendEvent(int(dayIndex),int(eventID), int(eventIndex), str(startTime), str(endTime), int(empireFlag), int(channelFlag), int(value0), int(value1), int(value2), int(value3), int(value4), int(value5), int(value6), int(value7), int(startRealTime), int(endRealTime), int(isAlreadyStart))

	if app.ENABLE_OFFLINE_SHOP:
		def __OfflineShop(self, id, name, *nameArgs):
			for namePart in nameArgs:
				name += " " + namePart

			uiOfflineShop.GetOfflineShopManager().UpdateMyShop(id, name)
		
		def __OfflineShopDestroy(self, id):
			uiOfflineShop.GetOfflineShopManager().DestroyMyShop(id)
		
		def __UpdateDecorationTime(self, skin_1_time, skin_2_time, skin_3_time, skin_4_time, skin_5_time, skin_6_time, skin_7_time, skin_8_time, banner_1_time, banner_2_time, banner_3_time, banner_4_time, banner_5_time):
			
			osfInfo.SHOP_SKIN_TIME[0] = int(skin_1_time)
			osfInfo.SHOP_SKIN_TIME[1] = int(skin_2_time)
			osfInfo.SHOP_SKIN_TIME[2] = int(skin_3_time)
			osfInfo.SHOP_SKIN_TIME[3] = int(skin_4_time)
			osfInfo.SHOP_SKIN_TIME[4] = int(skin_5_time)
			osfInfo.SHOP_SKIN_TIME[5] = int(skin_6_time)
			osfInfo.SHOP_SKIN_TIME[6] = int(skin_7_time)
			osfInfo.SHOP_SKIN_TIME[7] = int(skin_8_time)
			
			osfInfo.SHOP_BANNER_TIME[0] = int(banner_1_time)
			osfInfo.SHOP_BANNER_TIME[1] = int(banner_2_time)
			osfInfo.SHOP_BANNER_TIME[2] = int(banner_3_time)
			osfInfo.SHOP_BANNER_TIME[3] = int(banner_4_time)
			osfInfo.SHOP_BANNER_TIME[4] = int(banner_5_time)
		
		def __StartOpeningOfflineShop(self, skin_1_time, skin_2_time, skin_3_time, skin_4_time, skin_5_time, skin_6_time, skin_7_time, skin_8_time, banner_1_time, banner_2_time, banner_3_time, banner_4_time, banner_5_time):
			
			osfInfo.SHOP_SKIN_TIME[0] = int(skin_1_time)
			osfInfo.SHOP_SKIN_TIME[1] = int(skin_2_time)
			osfInfo.SHOP_SKIN_TIME[2] = int(skin_3_time)
			osfInfo.SHOP_SKIN_TIME[3] = int(skin_4_time)
			osfInfo.SHOP_SKIN_TIME[4] = int(skin_5_time)
			osfInfo.SHOP_SKIN_TIME[5] = int(skin_6_time)
			osfInfo.SHOP_SKIN_TIME[6] = int(skin_7_time)
			osfInfo.SHOP_SKIN_TIME[7] = int(skin_8_time)
			
			osfInfo.SHOP_BANNER_TIME[0] = int(banner_1_time)
			osfInfo.SHOP_BANNER_TIME[1] = int(banner_2_time)
			osfInfo.SHOP_BANNER_TIME[2] = int(banner_3_time)
			osfInfo.SHOP_BANNER_TIME[3] = int(banner_4_time)
			osfInfo.SHOP_BANNER_TIME[4] = int(banner_5_time)
			
			openingTime = 60*60*24*30
			openingGold = 0
			self.interface.OpenOfflineShopBuilder(openingTime, openingGold)
		
		def __CancelOpeningOfflineShop(self):
			self.interface.CloseOfflineShopBuilder()

		def __OnAddSellLog(self, iHelp, vnum, count, price, timeSold, buyer, metinSlot, attrSlot, applyRandom, transmutation, refineElement=None):
			if int(iHelp) == 1:
				self.interface.ClearSellHistoryWindow()
			self.interface.AddToSellHistory(
				int(vnum), int(count), int(price), buyer, int(timeSold),
				metinSlot, attrSlot, applyRandom, int(transmutation), refineElement)

		def __BuildSellLogMetinSlot(self, socket0, socket1, socket2, socket3, socket4):
			metinSlot = [int(socket0), int(socket1), int(socket2), int(socket3), int(socket4)]
			for i in range(player.METIN_SOCKET_MAX_NUM - len(metinSlot)):
				metinSlot.append(0)
			return metinSlot

		def __BuildSellLogAttrSlot(self, attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1):
			attrSlot = [
				(int(attr0_0), int(attr0_1)),
				(int(attr1_0), int(attr1_1)),
				(int(attr2_0), int(attr2_1)),
				(int(attr3_0), int(attr3_1)),
				(int(attr4_0), int(attr4_1)),
				(int(attr5_0), int(attr5_1)),
				(int(attr6_0), int(attr6_1)),
			]
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM - len(attrSlot)):
				attrSlot.append((0, 0))
			return attrSlot

		def __BuildSellLogApplyRandom(self, apply0_type, apply0_value, apply0_path, apply1_type, apply1_value, apply1_path, apply2_type, apply2_value, apply2_path, apply3_type, apply3_value, apply3_path):
			applyRandom = [
				(int(apply0_type), int(apply0_value)),
				(int(apply1_type), int(apply1_value)),
				(int(apply2_type), int(apply2_value)),
				(int(apply3_type), int(apply3_value)),
			]
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM - len(applyRandom)):
				applyRandom.append((0, 0))
			return applyRandom

		def __BuildSellLogRefineElement(self, refine_apply, refine_grade, refine_value0, refine_value1, refine_value2, refine_bonus0, refine_bonus1, refine_bonus2):
			refine_apply = int(refine_apply)
			refine_grade = int(refine_grade)
			if not refine_apply and not refine_grade:
				return None
			return (
				refine_apply,
				refine_grade,
				(int(refine_value0), int(refine_value1), int(refine_value2)),
				(int(refine_bonus0), int(refine_bonus1), int(refine_bonus2)),
			)

		if app.ENABLE_APPLY_RANDOM and app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def AddSellLog(self, iHelp, vnum, count, price, timeSold, buyer,
					socket0, socket1, socket2, socket3, socket4,
					apply0_type, apply0_value, apply0_path,
					apply1_type, apply1_value, apply1_path,
					apply2_type, apply2_value, apply2_path,
					apply3_type, apply3_value, apply3_path,
					attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1,
					transmutation,
					refine_apply, refine_grade, refine_value0, refine_value1, refine_value2, refine_bonus0, refine_bonus1, refine_bonus2):
				self.__OnAddSellLog(
					iHelp, vnum, count, price, timeSold, buyer,
					self.__BuildSellLogMetinSlot(socket0, socket1, socket2, socket3, socket4),
					self.__BuildSellLogAttrSlot(attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1),
					self.__BuildSellLogApplyRandom(
						apply0_type, apply0_value, apply0_path,
						apply1_type, apply1_value, apply1_path,
						apply2_type, apply2_value, apply2_path,
						apply3_type, apply3_value, apply3_path),
					transmutation,
					self.__BuildSellLogRefineElement(
						refine_apply, refine_grade, refine_value0, refine_value1, refine_value2,
						refine_bonus0, refine_bonus1, refine_bonus2))
		elif app.ENABLE_APPLY_RANDOM:
			def AddSellLog(self, iHelp, vnum, count, price, timeSold, buyer,
					socket0, socket1, socket2, socket3, socket4,
					apply0_type, apply0_value, apply0_path,
					apply1_type, apply1_value, apply1_path,
					apply2_type, apply2_value, apply2_path,
					apply3_type, apply3_value, apply3_path,
					attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1,
					transmutation):
				self.__OnAddSellLog(
					iHelp, vnum, count, price, timeSold, buyer,
					self.__BuildSellLogMetinSlot(socket0, socket1, socket2, socket3, socket4),
					self.__BuildSellLogAttrSlot(attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1),
					self.__BuildSellLogApplyRandom(
						apply0_type, apply0_value, apply0_path,
						apply1_type, apply1_value, apply1_path,
						apply2_type, apply2_value, apply2_path,
						apply3_type, apply3_value, apply3_path),
					transmutation)
		elif app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def AddSellLog(self, iHelp, vnum, count, price, timeSold, buyer,
					socket0, socket1, socket2, socket3, socket4,
					attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1,
					transmutation,
					refine_apply, refine_grade, refine_value0, refine_value1, refine_value2, refine_bonus0, refine_bonus1, refine_bonus2):
				self.__OnAddSellLog(
					iHelp, vnum, count, price, timeSold, buyer,
					self.__BuildSellLogMetinSlot(socket0, socket1, socket2, socket3, socket4),
					self.__BuildSellLogAttrSlot(attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1),
					[],
					transmutation,
					self.__BuildSellLogRefineElement(
						refine_apply, refine_grade, refine_value0, refine_value1, refine_value2,
						refine_bonus0, refine_bonus1, refine_bonus2))
		else:
			def AddSellLog(self, iHelp, vnum, count, price, timeSold, buyer,
					socket0, socket1, socket2, socket3, socket4,
					attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1,
					transmutation):
				self.__OnAddSellLog(
					iHelp, vnum, count, price, timeSold, buyer,
					self.__BuildSellLogMetinSlot(socket0, socket1, socket2, socket3, socket4),
					self.__BuildSellLogAttrSlot(attr0_0, attr0_1, attr1_0, attr1_1, attr2_0, attr2_1, attr3_0, attr3_1, attr4_0, attr4_1, attr5_0, attr5_1, attr6_0, attr6_1),
					[],
					transmutation)

		def RefreshSellLog(self):
			self.interface.RefreshSellHistoryWindow()
			
		def RevertPageSellLog(self):
			self.interface.RevertPageSellLog()
			
		def UpdateSellLog(self):
			self.interface.UpdateSellLog()

	if app.ENABLE_MULTI_FARM_BLOCK:
		def UpdateMultiFarmPlayer(self, multiFarmPlayer):
			self.affectShower.SetMultiFarmPlayer(str(multiFarmPlayer))
		def UpdateMultiFarmAffect(self, multiFarmStatus, isNewStatus):
			self.affectShower.SetMultiFarmInfo(int(multiFarmStatus))
			if int(isNewStatus) == 1:
				if int(multiFarmStatus) == 1:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MULTI_FARM_ACTIVE_CHAT)
				else:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MULTI_FARM_DEACTIVE_CHAT)
			app.SetMultiFarmExeIcon(int(multiFarmStatus))

	if app.ENABLE_DISCORD_STUFF:
		def GetMessage(self):
			if self.interface:
				self.interface.OpenWhisperWithMessage(osfInfo.msgname)
				osfInfo.msgname=""

	if app.ENABLE_MAINTENANCE_SYSTEM:
		def __MaintenanceReason(self, reason):
			# maintenance_reason <id>: the preset the GM chose (1 update, 2 fixes, 3 restart; 0 none), for the hint of the label.
			if self.interface:
				self.interface.SetMaintenanceReason(reason)

		def BINARY_ShowMaintenanceSign(self, timeLeft, duration):
			self.interface.ShowMaintenanceSign(timeLeft, duration)

		def BINARY_HideMaintenanceSign(self):
			self.interface.HideMaintenanceSign()

	if app.ENABLE_SHOW_CHEST_DROP:
		def BINARY_AddChestDropInfo(self, chestVnum, pageIndex, slotIndex, itemVnum, itemCount):
			if self.interface:
				self.interface.AddChestDropInfo(chestVnum, pageIndex, slotIndex, itemVnum, itemCount)
						
		def BINARY_RefreshChestDropInfo(self, chestVnum):
			if self.interface:
				self.interface.RefreshChestDropInfo(chestVnum)

	if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
		def __CloseLoadSafeboxEvent(self):
			self.interface.CloseLoadSafeboxEvent()

		def __CloseLoadMallEvent(self):
			self.interface.CloseLoadMallEvent()

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def PetHatchingWindowCommand(self, command):
			self.interface.PetHatchingWindowCommand(command)

		def PetNameChangeWindowCommand(self, command):
			self.interface.PetNameChangeWindowCommand(command)

		def PetSkillUpgradeDlgOpen(self, slot, index, gold):
			self.interface.PetSkillUpgradeDlgOpen(slot, index, gold)

		def PetFlashEvent(self, index):
			self.interface.PetFlashEvent(index)

		def PetAffectShowerRefresh(self):
			self.interface.PetAffectShowerRefresh()

		def PetFeedReuslt(self, result):
			self.interface.PetFeedReuslt(result)
			
		def PetAttrDetermineResult(self, byType):
			self.interface.PetAttrDetermineResult(byType)
			
		def PetAttrChangeResult(self, slotIndex, byType):
			self.interface.PetAttrChangeResult(slotIndex, byType)
			
		def PetReviveResult(self, result):
			self.interface.PetReviveResult(result)
			
		def PetWindowTypeResult(self, result):
			self.interface.PetWindowTypeResult(result)

		def PetHeartUpdate(self):
			self.interface.PetHeartUpdate()

	if app.ENABLE_PLAYER_RANKING:
		def BINARY_RANK_APPEND(self, my_pos, mode, pos, name, value, empire):
			self.interface.AppendInfoRankGlobal(my_pos, mode, pos, name, value, empire)
			
		def SetRankingResetInfo(self, iTime, iInterval, vnum1, count1, vnum2, count2, vnum3, count3):
			self.interface.SetRankingResetInfo(int(iTime), int(iInterval))
			self.interface.SetRankingReward(int(vnum1), int(count1), int(vnum2), int(count2), int(vnum3), int(count3))

	if app.ENABLE_BIOLOG_SYSTEM:
		def SetBioBegin2(self, count):
			self.interface.wndBio.BeginSnapshot(count)

		def SetBioRow2(self, index, level, vnum, total, interval, stone, choose,
			elixir, elixirCost, clock, clockCost, type1, value1, type2, value2,
			type3, value3, type4, value4, count, due, done, alarm, chosen):
			# stringCommander derives arity from named arguments, not *args.
			self.interface.wndBio.SnapshotRow(index, level, vnum, total, interval,
				stone, choose, elixir, elixirCost, clock, clockCost, type1, value1,
				type2, value2, type3, value3, type4, value4, count, due, done, alarm, chosen)

		def SetBioRow3(self, index, level, vnum, total, interval, stone, choose,
			elixir, elixirCost, clock, clockCost, type1, value1, type2, value2,
			type3, value3, type4, value4, type5, value5, type6, value6,
			count, due, done, alarm, chosen):
			self.interface.wndBio.SnapshotRow(index, level, vnum, total, interval,
				stone, choose, elixir, elixirCost, clock, clockCost, type1, value1,
				type2, value2, type3, value3, type4, value4, type5, value5,
				type6, value6, count, due, done, alarm, chosen)

		def SetBioRequestV1(self, version):
			self.interface.wndBio.RequestCapability(version)

		def SetBioRevisionV1(self, index, revision):
			self.interface.wndBio.SnapshotRevision(index, revision)

		def SetBioResultV1(self, index, revision, status):
			self.interface.wndBio.RequestResult(index, revision, status)

		def SetBioEnd2(self):
			self.interface.wndBio.EndSnapshot()

		def SetBioData(self, level, count, time, enableNotification):
			self.interface.wndBio.LoadData(int(level), int(count), int(time), int(enableNotification))
			
		def SetBioStone(self, level):
			self.interface.wndBio.LoadStone(int(level))
			
		def SetBioGift(self, level):
			self.interface.wndBio.LoadGift(int(level))
			
		def SetBioEmpty(self):
			self.interface.wndBio.LoadEmpty(True)

		def OpenBio(self):
			try:
				interface = osfInfo.GetInterfaceInstance()
				if interface:
					if interface.wndBio.IsShow():
						interface.wndBio.Hide()
					else:
						interface.wndBio.Show()
			except:
				pass

		def AddLoopEvent(self, name, event):
			for i in self.loopList:
				if i[0] == name:
					i[1] = event
					return
					
			list = [name,event]
			self.loopList.append(list)
			
		def RemoveLoopEvent(self, name):
			for i in range(len(self.loopList)):
				if self.loopList[i][0] == name:
					del self.loopList[i]
					return
					
		def loopListEvent(self):
			for i in range(len(self.loopList)):
				returnValue = self.loopList[i][1]()
				if returnValue == True:
					del self.loopList[i]

		def BINARY_OnRecvSendWhisper(self, content):
				content = content.replace("$", " ")
				self.interface.RegisterGameMasterName("[SYSTEM]")
				chat.AppendWhisper(chat.WHISPER_TYPE_CHAT, "[SYSTEM]", content)
				self.interface.RecvLegacyWhisper("[SYSTEM]", content)

	if app.ENABLE_AURA_SYSTEM:
		def AuraWindowOpen(self, type):
			self.interface.AuraWindowOpen(type)

		def AuraWindowClose(self):
			self.interface.AuraWindowClose()

	if app.ENABLE_CUBE_RENEWAL:
		def BINARY_CUBE_RENEWAL_OPEN(self):
			if self.interface:
				self.interface.BINARY_CUBE_RENEWAL_OPEN()

	if app.ENABLE_LOADING_PERFORMANCE:
		def PrepareInstantWarp(self):
			if self.interface:
				self.warpUITransition = True
				try:
					self.interface.CaptureWarpUIState()
				except:
					uiwarpstate.Clear()
					dbg.TraceError(
						"[WarpUI] snapshot failed; continuing without restore")
				self.interface.PrepareInstantWarp()

		def OpenWarpShowerWindow(self):
			if self.interface:
				self.warpUITransition = True
				try:
					self.interface.CaptureWarpUIState()
				except:
					uiwarpstate.Clear()
					dbg.TraceError(
						"[WarpUI] snapshot failed; continuing without restore")
				self.interface.OpenWarpShowerWindow()

		def CloseWarpShowerWindow(self):
			if self.interface:
				self.interface.CloseWarpShowerWindow()

	if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
		def __SkillUpgrade_Open(self, upgraderItem):
			if self.interface:
				self.interface.OpenSkillUpgradeWindow(int(upgraderItem))

	if app.ENABLE_KILL_BAR_SYSTEM:
		def AddKillInfo(self, killer, victim, killer_race, victim_race, weapon_type):
			if self.interface:
				self.interface.AddKillInfo(killer, victim, killer_race, victim_race, weapon_type)

	if app.ENABLE_EXCHANGE_LOG:
		def ExchangeLogClear(self, playerCode):
			self.interface.ExchangeLogClear(playerCode)
		def ExchangeLogRefresh(self, isLogItemRefresh):
			self.interface.ExchangeLogRefresh(isLogItemRefresh)
		def ExchangeLogAppend(self, logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date):
			self.interface.ExchangeLogAppend(logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date)
		if app.ENABLE_APPLY_RANDOM and app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, refineElement, isOwnerItem):
				self.interface.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, refineElement, isOwnerItem)
		elif app.ENABLE_APPLY_RANDOM:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, isOwnerItem):
				self.interface.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, isOwnerItem)
		else:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, isOwnerItem):
				self.interface.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, isOwnerItem)

	if app.ENABLE_TOOLTIP_GROUND:
		def ShowItemFromClient(self, open, itemvnum = 0, metinslot = 0, attr = 0, applyrandom = 0, refineelement = 0):
			import uiToolTip
			pos_x, pos_y = wndMgr.GetMousePosition()
			self.tlground = uiToolTip.ItemToolTip()
			self.tlground.ClearToolTip()
			self.tlground.Hide()
			if open:
				attrSlot = []
				for i in range(player.ATTRIBUTE_SLOT_MAX_NUM):
					attrSlot.append(attr[i])
				applyrandomSlot = []
				for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM):
					applyrandomSlot.append(applyrandom[i])
				refine_element = None
				if app.ENABLE_REFINE_ELEMENT_SYSTEM and refineelement and len(refineelement) >= 4 and (refineelement[0] or refineelement[1]):
					refine_element = refineelement
				self.tlground.SetToolTipPosition(pos_x + 5, pos_y - 5)
				self.tlground.AddItemData(itemvnum, metinslot, attrSlot, apply_random_list=applyrandomSlot, refine_element=refine_element)

	if app.ENABLE_SHOP_SEARCH:
		def BINARY_ShopSearch_RecvResult(self):
			self.interface.ShopSearch_RecvResult()
	
		def BINARY_ShopSearch_RecvBuyDone(self, result):
			self.interface.ShopSearch_RecvBuyDone(result)
	
		def BINARY_ShopSearch_RecvOwnerMessage(self, ownerName):
			self.interface.ShopSearch_RecvOwnerMessage(ownerName)
	
		def BINARY_ShopSearch_RecvSoldInfo(self, hasResults):
			self.interface.ShopSearch_RecvSoldInfo(hasResults)

	if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
		def BINARY_VirtualMarketSaleNotification(self, transactionHigh,
				transactionLow, listingId, itemVnum, count, totalPrice):
			self.interface.PushVirtualMarketSaleNotification(
				transactionHigh, transactionLow, listingId, itemVnum, count, totalPrice)

		def BINARY_VirtualMarketSearchResult(self, token, status, appended, hasMore):
			self.interface.VirtualMarketSearchResult(token, status, appended, hasMore)

		def BINARY_VirtualMarketSellerSuggestionsResult(self, token, status):
			self.interface.VirtualMarketSellerSuggestionsResult(token, status)

		def BINARY_VirtualMarketOwnerShopResult(self, token, status):
			self.interface.VirtualMarketOwnerShopResult(token, status)

		def BINARY_VirtualMarketOwnerListingsResult(self, token, status, appended, hasMore):
			self.interface.VirtualMarketOwnerListingsResult(token, status, appended, hasMore)

		def BINARY_VirtualMarketSellerReturnsResult(self, token, status, appended, hasMore):
			self.interface.VirtualMarketSellerReturnsResult(token, status, appended, hasMore)

		def BINARY_VirtualMarketBuyerDeliveriesResult(self, token, status, appended, hasMore):
			self.interface.VirtualMarketBuyerDeliveriesResult(token, status, appended, hasMore)

		def BINARY_VirtualMarketShopCommandResult(self, token, status, command, result, replayed):
			self.interface.VirtualMarketShopCommandResult(token, status, command, result, replayed)

		def BINARY_VirtualMarketListingCreateResult(self, token, status, result, replayed):
			self.interface.VirtualMarketListingCreateResult(token, status, result, replayed)

		def BINARY_VirtualMarketPricePreferenceResult(self, token, status, vnum,
				found, totalPrice, itemCount):
			self.interface.VirtualMarketPricePreferenceResult(
				token, status, vnum, found, totalPrice, itemCount)

		def BINARY_VirtualMarketListingMoveResult(self, token, status, result, replayed):
			self.interface.VirtualMarketListingMoveResult(token, status, result, replayed)

		def BINARY_VirtualMarketListingMutationResult(self, token, status, mutation,
				result, replayed, listingId, price):
			self.interface.VirtualMarketListingMutationResult(
				token, status, mutation, result, replayed, listingId, price)

		def BINARY_VirtualMarketItemClaimResult(self, token, status, source, result, replayed):
			self.interface.VirtualMarketItemClaimResult(token, status, source, result, replayed)

		def BINARY_VirtualMarketPurchaseResult(self, token, status, result, replayed, state):
			self.interface.VirtualMarketPurchaseResult(token, status, result, replayed, state)

		def BINARY_VirtualMarketBatchPurchaseResult(self, token, status, result, replayed, state, itemCount):
			self.interface.VirtualMarketBatchPurchaseResult(token, status, result, replayed, state, itemCount)

		def BINARY_VirtualMarketSellerWithdrawalResult(self, token, status, result, replayed):
			self.interface.VirtualMarketSellerWithdrawalResult(token, status, result, replayed)

	if app.ENABLE_DESTROY_ITEM_RESTORE:
		def OpenSaveItem(self):
			self.interface.OpenItemSaveWindow()
		def LoadEmptySavedItems(self):
			self.ClearSavedItems()
			self.SetSavedItemsPage(-1,1)
			self.RefreshSavedItems()
		def AddSaveItem(self, index, vnum, count, date):
			self.interface.AddSaveItem(int(index))
		def RemoveSaveItem(self, index):
			self.interface.RemoveSaveItem(index)
		def WriteEmptyText(self):
			self.interface.WriteEmptyText()
		def RefreshSavedItems(self):
			self.interface.RefreshSavedItemsWindow()
			
		def ClearSavedItems(self):
			self.interface.ClearSavedItemsWindow()
			
		def SetSavedItemsPage(self, curPage, maxPage):
			self.interface.SetSavedItemsPage(curPage, maxPage)
			
		def __BuildSavedItemPayload(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, refine_element, transmutation, soulbind):
			self.interface.AddToSavedItems(int(time), int(item_id), int(vnum), int(count), int(yang), int(fragments), metinSlot, attrSlot, applyRandom, int(transmutation), int(soulbind), refine_element)

		def __ParseSavedItemAttrSlot(self, attrType, attrValue):
			attrSlot = []
			for x in range(min(len(attrType), player.ATTRIBUTE_SLOT_MAX_NUM)):
				attrSlot.append((int(attrType[x]), int(attrValue[x])))
			for i in range(player.ATTRIBUTE_SLOT_MAX_NUM - len(attrSlot)):
				attrSlot.append((0, 0))
			return attrSlot

		def __ParseSavedItemMetinSlot(self, metinSlot):
			return [int(metinSlot[x]) for x in range(min(len(metinSlot), player.METIN_SOCKET_MAX_NUM))]

		def __ParseSavedItemApplyRandom(self, applyRandomList):
			applyRandom = []
			for x in range(min(len(applyRandomList), player.APPLY_RANDOM_SLOT_MAX_NUM)):
				slot = applyRandomList[x]
				if len(slot) >= 3:
					applyRandom.append((int(slot[0]), int(slot[1]), int(slot[2])))
				else:
					applyRandom.append((int(slot[0]), int(slot[1]), 0))
			for i in range(player.APPLY_RANDOM_SLOT_MAX_NUM - len(applyRandom)):
				applyRandom.append((0, 0, 0))
			return applyRandom

		if app.ENABLE_APPLY_RANDOM and app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def AddSavedItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrType, attrValue, applyRandomList, refineElement, transmutation, soulbind):
				self.__BuildSavedItemPayload(
					time, item_id, vnum, count, yang, fragments,
					self.__ParseSavedItemMetinSlot(metinSlot),
					self.__ParseSavedItemAttrSlot(attrType, attrValue),
					self.__ParseSavedItemApplyRandom(applyRandomList),
					refineElement,
					transmutation, soulbind)
		elif app.ENABLE_APPLY_RANDOM:
			def AddSavedItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrType, attrValue, applyRandomList, transmutation, soulbind):
				self.__BuildSavedItemPayload(
					time, item_id, vnum, count, yang, fragments,
					self.__ParseSavedItemMetinSlot(metinSlot),
					self.__ParseSavedItemAttrSlot(attrType, attrValue),
					self.__ParseSavedItemApplyRandom(applyRandomList),
					None,
					transmutation, soulbind)
		elif app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def AddSavedItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrType, attrValue, refineElement, transmutation, soulbind):
				self.__BuildSavedItemPayload(
					time, item_id, vnum, count, yang, fragments,
					self.__ParseSavedItemMetinSlot(metinSlot),
					self.__ParseSavedItemAttrSlot(attrType, attrValue),
					[],
					refineElement,
					transmutation, soulbind)
		else:
			def AddSavedItem(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrType, attrValue, transmutation, soulbind):
				self.__BuildSavedItemPayload(
					time, item_id, vnum, count, yang, fragments,
					self.__ParseSavedItemMetinSlot(metinSlot),
					self.__ParseSavedItemAttrSlot(attrType, attrValue),
					[],
					None,
					transmutation, soulbind)

	def GetInputBegin(self):
		osfInfo.INPUT_IGNORE = 1
		
	def GetInputEnd(self):
		osfInfo.INPUT_IGNORE = 0

	if app.ENABLE_DUNGEON_INFO:
		def BINARY_OnRecvBulkWhisper(self, content):
			content = content.replace("$", " ")
			self.interface.RegisterGameMasterName("[Dungeon Info]")
			chat.AppendWhisper(chat.WHISPER_TYPE_CHAT, "[Dungeon Info]", content)
			self.interface.RecvLegacyWhisper("[Dungeon Info]", content)

	if app.ENABLE_BRAVE_CAPE_RENEWAL:
		def SetBraveCapeStatus(self, status):
			if self.interface:
				if self.interface.wndInventory:
					if self.interface.wndInventory.wndBraveCape:
						self.interface.wndInventory.wndBraveCape.SetStatus(status)

	def SendAutoFarmInfo(self, notice, count=0):
		if notice == 1:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.QUEUE_ADD_STONE)
		elif notice == 3:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.QUEUE_REMOVE_STONE)
		elif notice == 2:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.QUEUE_MAX)
		elif notice == 4:
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.QUEUE_TRIMMED)
		elif notice == 6:
			chat.AppendChat(chat.CHAT_TYPE_INFO, getattr(localeInfo, "QUEUE_EXPIRED",
				u"[Fronta meteorů] Fronta zrušena kvůli neaktivitě."))
		elif notice == 7:
			chat.AppendChat(chat.CHAT_TYPE_INFO, getattr(localeInfo, "QUEUE_RESERVED",
				u"[Fronta meteorů] Vybrané cíle už jsou v jiné frontě."))
		elif notice == 5:
			message = getattr(
				localeInfo,
				"QUEUE_ADD_NEARBY",
				u"[Fronta meteorů] Přidány blízké cíle do fronty: %d.",
			)
			try:
				message = message % int(count)
			except (TypeError, ValueError):
				message = u"[Fronta meteorů] Přidány blízké cíle do fronty: %d." % int(count)
			chat.AppendChat(chat.CHAT_TYPE_INFO, message)

	if app.ENABLE_REWARD_SYSTEM:
		def SetRewardPlayers(self, data):
			self.interface.SetRewardPlayers(str(data))

	if app.ENABLE_ANTI_EXP:
		def SetAntiExp(self, flag):
			flag = int(flag)
			if self.interface:
				ptr = [self.interface.wndTaskBar]
				for gui in ptr:
					if gui:
						if flag:
							guiptr = gui.GetChild("AntiExp")
							guiptr.SetUpVisual("d:/ymir work/ui/game/taskbar/antiexp_button_01.tga")
							guiptr.SetOverVisual("d:/ymir work/ui/game/taskbar/antiexp_button_02.tga")
							guiptr.SetDownVisual("d:/ymir work/ui/game/taskbar/antiexp_button_03.tga")

							if gui.IsChild("RestExp_Value"):
								gui.GetChild("Exp_Value").Hide()
							if gui.IsChild("Exp_Value"):
								gui.GetChild("RestExp_Value").Hide()

							for j in range(1, 5):
								if gui.IsChild("EXPGauge_0%d" % j):
									gui.GetChild("EXPGauge_0%d" % j).SetDiffuseColor(255, 0, 0, 1)

						else:
							guiptr = gui.GetChild("AntiExp")
							guiptr.SetUpVisual("d:/ymir work/ui/game/taskbar/antiexp_button_04.tga")
							guiptr.SetOverVisual("d:/ymir work/ui/game/taskbar/antiexp_button_05.tga")
							guiptr.SetDownVisual("d:/ymir work/ui/game/taskbar/antiexp_button_06.tga")

							if gui.IsChild("RestExp_Value"):
								gui.GetChild("Exp_Value").Show()
							if gui.IsChild("Exp_Value"):
								gui.GetChild("RestExp_Value").Show()

							for j in range(1, 5):
								if gui.IsChild("EXPGauge_0%d" % j):
									gui.GetChild("EXPGauge_0%d" % j).SetDiffuseColor(201, 160, 51, 1)

	if app.ENABLE_HIDE_AFFECT_ICONS:
		def AffectIconState(self):
			index = systemSetting.IsAffectIconShow()
			if index:
				self.affectShower.Show()
			else:
				self.affectShower.Hide()

	if app.ENABLE_CAPTCHA_NEW and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
		def __Captcha_index(self, value1):
			osfInfo.CAPTCHA_QUESTINDEX = int(value1)
	
		def ShowCaptchaNew(self, timeLeft):
			if self.interface:
				self.interface.ShowCaptchaNew(int(timeLeft))

	if app.ENABLE_DUNGEON_TIME_WINDOW:
		def __SetDungeonTime(self, mapIndex, remainingTime):
			if self.interface:
				self.interface.OpenDungeonTimeWindow(int(mapIndex), int(remainingTime))
			
		def __HideDungeonTime(self):
			if self.interface:
				self.interface.HideDungeonTimeWindow()

	if app.ENABLE_BUFF_SYSTEM:
		def OpenBuffiNameDialog(self, itemID):
			try:
				itemID = int(itemID)
			except (TypeError, ValueError):
				return

			if self.buffiNameInputDialog:
				self.buffiNameInputDialog.Close()

			dialog = uiCommon.InputDialogWithDescription()
			dialog.SetTitle(localeInfo.BUFFI_NAME_DIALOG_TITLE)
			dialog.SetDescription(localeInfo.BUFFI_NAME_DIALOG_DESCRIPTION)
			dialog.SetMaxLength(20)
			dialog.SetAcceptEvent(ui.__mem_func__(self.AcceptBuffiName))
			dialog.SetCancelEvent(ui.__mem_func__(self.CancelBuffiName))
			dialog.itemID = itemID
			dialog.Open()
			self.buffiNameInputDialog = dialog

		def AcceptBuffiName(self):
			if not self.buffiNameInputDialog:
				return True

			name = self.buffiNameInputDialog.GetText().strip()
			if (len(name) < 2 or len(name) > 20 or '"' in name or
				any(character.isspace() for character in name) or
				net.IsInsultIn(name)):
				self.PopupMessage(localeInfo.BUFFI_NAME_DIALOG_INVALID)
				return True

			itemID = self.buffiNameInputDialog.itemID
			net.SendChatPacket('/support_name %d "%s"' % (itemID, name))
			self.buffiNameInputDialog.Close()
			self.buffiNameInputDialog = None
			return True

		def CancelBuffiName(self):
			if self.buffiNameInputDialog:
				self.buffiNameInputDialog.Close()
				self.buffiNameInputDialog = None
			return True

		def OpenSupportGui(self):
			self.interface.OpenSupportGui()

		def OpenSupportUpgrade(self, skillID):
			# the server, when a Buffi skill book or the Buffi soul stone (skillID 0) is used
			self.interface.OpenSupportUpgrade(int(skillID))
			
		def SetBuffiVisual(self, enabled, vid="0", race="0"):
			# Server notice of the elf-form outfit race; the races are registered at start.
			pass

		def SetSupportName(self, name):
			self.interface.SetSupportName(name)

		def SetSupportWeapon(self, weapon):
			self.interface.SetSupportWeapon(int(weapon))
			
		def SetSupportArmor(self, armor):
			self.interface.SetSupportArmor(int(armor))

		def SetSupportHair(self, hair):
			self.interface.SetSupportHair(int(hair))
			
		def SetSupportAcce(self, acce):
			acce = int(acce) + 85000
			if acce == 85000:
				return
				
			self.interface.SetSupportAcce(int(acce))
			
		def SetShiningWeapon(self, shining_weapon):
			self.interface.SetShiningWeapon(int(shining_weapon))

		def SetShiningArmor(self, shining_armor):
			self.interface.SetShiningArmor(int(shining_armor))
			
		def SetSupportSkillLvl(self, skill_1, skill_2, skill_3, skill_4, skill_5):
			self.interface.SetSupportSkillLvl(int(skill_1), int(skill_2), int(skill_3), int(skill_4), int(skill_5))

		def SupportLeave(self):
			self.interface.SupportLeave()
		
		def SetSupportInt(self , ints):
			self.interface.SetSupportInt(ints)

		def SetBuffPremiumSkill(self, isPremium):
			self.interface.SetBuffPremiumSkill(int(isPremium))

		def SetBuffiProgress(self, level, currentExp, requiredExp, passivePoints, healingUnlocked, expMode=1, form=0, hairEnabled=1):
			self.interface.SetBuffiProgress(
				int(level), int(currentExp), int(requiredExp), int(passivePoints),
				int(healingUnlocked), int(expMode), int(form), int(hairEnabled))

	if app.ENABLE_SWITCHBOT_SYSTEM:
		def RefreshSwitchbotWindow(self):
			# The EXE calls this right after the server's switchbot table replaced the client's, with or without
			# the window (a warp enters a core with the table of the last starts): put the player's bonuses back.
			switchbotMemory.Apply()
			if self.interface:
				self.interface.RefreshSwitchbotWindow()
			
		def RefreshSwitchbotItem(self, slot):
			if self.interface:
				self.interface.RefreshSwitchbotItem(slot)

	if app.ENABLE_FISHING_GAME:
		def OnFishingGameStart(self, level):
			if self.interface:
				self.interface.OpenFishingGameWindow(level)

		def OnFishingStopGame(self):
			if self.interface:
				self.interface.CloseFishingGameWindow()

	if app.ENABLE_RANKING_SYSTEM:
		def OpenRankingBoard(self, type, category):
			self.interface.OpenRankingBoardWindow(type, category)

	if app.ENABLE_ATTR_6TH_7TH:
		def __OpenAttr67AddDlg(self):
			if self.interface:
				self.interface.OpenAttr67AddDlg()

	if app.ENABLE_BATTLE_PASS:
		def BattlePassActive(self, isPremium):
			if int(isPremium) == 1:
				self.interface.wndBattlePass.UnlockPremium()

		def BattlePassUpdate(self, index, count, exp, totalExp, level, coolTime):
			self.interface.wndBattlePass.SetExperience(int(exp), int(totalExp))
			self.interface.wndBattlePass.SetLevel(int(level))
			self.interface.wndBattlePass.UpdateMission(int(index), int(count), int(coolTime))
		
		def BattlePassInfo(self, category, index, title, type, vnum, count, maxCount, expRecv, isPremium, coolTime):
			self.interface.wndBattlePass.AppendMission(int(category), int(index), title, int(type), int(vnum), int(count), int(maxCount), int(expRecv), int(isPremium), int(coolTime))
			
		def BattlePassInfoReward(self, index, vnum, count, iNecessaryLevel, status, isPremium):
			self.interface.wndBattlePass.AppendRewardItem(int(index), int(vnum), int(count), int(status), int(isPremium), int(iNecessaryLevel))

		def BattlePassInfoGeneral(self, isPremium, monthBattlePass, EXP, totalEXP, level, coins, seasonEndUnix):
			if int(isPremium) == 1:
				self.interface.wndBattlePass.UnlockPremium()
				
			self.interface.wndBattlePass.SetExperience(int(EXP), int(totalEXP))
			self.interface.wndBattlePass.SetLevel(int(level))
			self.interface.wndBattlePass.SetSeasonEndTime(int(seasonEndUnix))
			# Activation month (1-12): rewards are collectable only in that month
			# (server CollectBattlePassRewards); the panel badge reads it.
			self.interface.wndBattlePass.monthBattlePass = int(monthBattlePass)
			
			# constInfo.BATTLE_PASS_COINS = int(coins)

		def ShowShopCoinBattlePass(self):
			self.interface.dlgShop.wndTextBattlePassCoin.Show()
			self.interface.dlgShop.btnBuy.Hide()
			self.interface.dlgShop.btnSell.Hide()
		
		def BattlePassClear(self):
			self.interface.wndBattlePass.ClearBattlePass()

	if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
		def __ClearGuildRedDragonLairRanking(self):
			guild.ClearDragonLairRanking(guild.GUILD_DRAGONLAIR_TYPE_RED)

		def __CheckRedDragonLairRanking(self):
			if guild.CheckDragonLairRanking(guild.GUILD_DRAGONLAIR_TYPE_RED) == 0:
				self.interface.RefreshGuildDragonLairRanking(guild.GUILD_DRAGONLAIR_TYPE_RED)
				self.interface.OpenGuildDragonLairRanking(guild.GUILD_DRAGONLAIR_TYPE_RED)

		def OpenGuildDragonLairRanking(self, type):
			self.interface.OpenGuildDragonLairRanking(type)

		def RefreshGuildDragonLairRanking(self, type):
			self.interface.RefreshGuildDragonLairRanking(type)

		if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
			def SetGuildDragonLairFistGuildText(self, second):
				self.interface.SetGuildDragonLairFistGuildText(second)
			def SetGuildDragonLairStart(self):
				self.interface.SetGuildDragonLairStart()
			def SetGuildDragonLairSuccess(self):
				self.interface.SetGuildDragonLairSuccess()

	if app.ENABLE_PLAYER_COUNT:
		def BINARY_RefreshPlayerCount(self, count):
			if self.interface:
				self.interface.RefreshPlayerCount(count)

	def BINARY_RarityMetadataChanged(self, context, windowOrSide, slot, vid, publicId, grade):
		if self.interface:
			self.interface.RarityMetadataChanged(context, windowOrSide, slot, vid, publicId, grade)

	def BINARY_RarityPreviewResult(self, requestId, mode, result, currentGrade,
			targetGrade, chanceBp, yang, boosterAvailable, boosterSelected, costs):
		if self.interface:
			self.interface.RarityPreviewResult(requestId, mode, result, currentGrade,
				targetGrade, chanceBp, yang, boosterAvailable, boosterSelected, costs)

	def BINARY_RarityCommitResult(self, requestId, mode, result, succeeded, grade):
		if self.interface:
			self.interface.RarityCommitResult(requestId, mode, result, succeeded, grade)

	def __ReceiveResonanceSealValues(self, payload):
		resonanceuihelpers.ReceiveSealValues(payload)

	def BINARY_ResonanceCapability(self, available):
		if not available:
			resonanceuihelpers.ClearSealValues()
		if self.interface:
			self.interface.ResonanceCapabilityChanged(bool(available))

	def BINARY_ResonanceUnlockConfigChanged(self):
		if self.interface:
			self.interface.ResonanceUnlockConfigChanged()

	def BINARY_ResonanceMetadataChanged(self, context, windowOrSide, slot, vid,
			publicId, unusedUnlockedMask, unusedSlots):
		if self.interface:
			self.interface.ResonanceMetadataChanged(context, windowOrSide, slot, vid, publicId)

	def BINARY_ResonanceMutationResult(self, requestId, result, slot, vnum):
		if self.interface:
			self.interface.ResonanceMutationResult(requestId, result, slot, vnum)

	if getattr(app, "ENABLE_DROP_TRACKER", 0):
		def BINARY_DropTrackerCapability(self, available):
			if self.interface:
				self.interface.SetDropTrackerCapability(bool(available))

		def __DropTrackerGatherOffer(self, version):
			if self.interface:
				self.interface.OfferDropTrackerGather(version)

		def BINARY_DropTrackerBatch(self, rows):
			if self.interface:
				self.interface.AddDropTrackerBatch(rows)

	if app.ENABLE_DROP_INFO_WINDOW:
		def MakeDropinfoDialog(self):
			if self.wndDropInfo == None:
				self.wndDropInfo = uiDropInfo.Window()

		def RecvDropInfo(self, vnum, count):
			# The auto ticket of a dungeon entry is no pickup: the entry tells the used ticket instead.
			if ticketnoticemodel.STATE.OnGain(vnum, count, app.GetTime()):
				return
			if (
				getattr(app, "ENABLE_DROP_TRACKER", 0) and
				self.interface and
				self.interface.IsDropTrackerAvailable()
			):
				return

			if not systemSetting.IsViewDropInfo():
				return

			itemVnum = int(vnum)
			itemCount = int(count)
			
			index = systemSetting.GetDropInfomation()
			isYang = (itemVnum == 1)
			
			if index == 2:
				return

			if isYang and not systemSetting.IsShowYang():
				return

			self.MakeDropinfoDialog()

			if index == 0:
				self.wndDropInfo.AppendDropInfo(itemVnum, itemCount)
				self.wndDropInfo.Open()
			elif index == 1:
				self.wndDropInfo.AppendChatInfo(itemVnum, itemCount)

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def RefineElementProcess(self, type, refine_type, data):
			if self.interface:
				self.interface.RefineElementProcess(type, refine_type, data)

	if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
		def __AutoOff(self):
			if item.CheckAffect(chr.AFFECT_AUTO_USE, 0):
				self.BINARY_NEW_RemoveAffect(chr.AFFECT_AUTO_USE, 0)

			chrmgr.SetAutoOnOff(False)

		def __AutoOn(self):
			chrmgr.SetAutoOnOff(True)
			if item.CheckAffect(chr.AFFECT_AUTO_USE, 0):
				duration = item.GetAffectDuration(chr.AFFECT_AUTO_USE)
				if chr.AFFECT_AUTO_USE in self.affectShower.affectImageDict:
					self.affectShower.affectImageDict[chr.AFFECT_AUTO_USE].SetDuration(duration)
				else:
					self.BINARY_NEW_AddAffect(chr.AFFECT_AUTO_USE, 0, 0, duration)

		def __AutoLoginOff(self):
			chrmgr.SetAutoOnOff(False)

		def AutoException(self):
			wAuto = uiAutoHuntingSystem.AutoHuntingSystemWindow()
			wAuto.AutoOnOff(0, 1, 1)

		def AutoSlotRefresh(self):
			wAuto = uiAutoHuntingSystem.AutoHuntingSystemWindow()
			wAuto.RefreshAutoPositionSlot()
			wAuto.RefreshAutoSkillSlot()

# CRIMSON_EMBER_PROFILE_GAME_V1_BEGIN
def _CrimsonGameProfileCapability(self, enabled):
	if self.interface:
		self.interface.UnifiedMessengerPlayerProfileCapability(bool(enabled))


def _CrimsonGameProfile(self, token, status, pid, name, race):
	if self.interface:
		self.interface.UnifiedMessengerPlayerProfile(
			int(token), int(status), int(pid), str(name), int(race))


GameWindow.BINARY_UnifiedMessengerPlayerProfileCapability = _CrimsonGameProfileCapability
GameWindow.BINARY_UnifiedMessengerPlayerProfile = _CrimsonGameProfile
# CRIMSON_EMBER_PROFILE_GAME_V1_END


def _UnifiedMessengerPresenceCapability(self, enabled):
	if self.interface:
		self.interface.UnifiedMessengerPresenceCapability(bool(enabled))


def _UnifiedMessengerPresence(self, token, name, state):
	if self.interface:
		self.interface.UnifiedMessengerPresence(int(token), str(name), int(state))


GameWindow.BINARY_UnifiedMessengerPresenceCapability = _UnifiedMessengerPresenceCapability
GameWindow.BINARY_UnifiedMessengerPresence = _UnifiedMessengerPresence
