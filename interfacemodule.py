##
## Interface
##
import constInfo
import osfInfo
import systemSetting
import wndMgr
import chat
import app
import player
import uiTaskBar
import uiCharacter
import uiInventory
import uiRarity
import uiresonance
import inventoryshortcutpolicy
import uiCostumeInventory
import uiDragonSoul
import uiChat
import uiMessenger
import uiUnifiedMessenger
import unifiedmessengermodel
import unifiedmessengernotifications
import systemnotifications
import uiwarpstate
import featureavailability
import guild
import snd

CAPTCHA_V2_ENABLED = bool(getattr(app, "ENABLE_CAPTCHA_V2", 0))
CAPTCHA_WINDOW_ENABLED = bool(getattr(app, "ENABLE_CAPTCHA_V3", 0))
PERSISTENT_QUEST_BUTTON_COUNT = 1 + int(bool(getattr(app, "ENABLE_DAILY_TASKS", 0)))
PVP_MATCHMAKING_ENABLED = bool(getattr(app, "ENABLE_PVP_MATCHMAKING", 0))

try:
	import messengerHistory
except ImportError:
	messengerHistory = None

import ui
import uiHelp
import uiWhisper
import uiPointReset
import uiShop
import uiExchange
import uiSystem
import uiRestart
import uiToolTip
import uiMiniMap
import uiParty
import uiSafebox
import uiGuild
import uiGuildV2
import uiQuest
import uiPrivateShopBuilder
import uiCommon
import uiRefine
import uiEquipmentDialog
import uiGameButton
import uinoticeboard
import uiCube
import uiskilltree
import uigmpanel
import uiMountSystem
import uipermanenttasks
import uidailytasks
import uiquickbuff
import uiTalisman
import uiquickequip
if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
	import uicustomports
if getattr(app, "ENABLE_AFK_SYSTEM", 0):
	import uiafksystem
if getattr(app, "ENABLE_DROP_TRACKER", 0):
	import uidroptracker
import miniMap
# ACCESSORY_REFINE_ADD_METIN_STONE
import uiselectitem
# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE
if app.ENABLE_GEM_SYSTEM:
	import uiselectitemEx
import uiScriptLocale
import event
import localeInfo
import item
import uigamenotification
import uicountdownhud
if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
	import uiSkillBookCombination
if app.ENABLE_ACCE_COSTUME_SYSTEM:
	import uiAcce

if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
	import uiSpecialInventory

import uiMiniGame

if app.ENABLE_CHANGE_LOOK_SYSTEM:
	import uiChangeLook
	import shop

if app.ENABLE_MINI_GAME_OKEY:
	import uiMiniGameRumi

if app.ENABLE_TELEPORT_WINDOW:
	import uiTeleportPanel
	import uiTeleport

if app.ENABLE_GEM_SYSTEM:
	import uiGemShop

if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
	import uiCaptcha

if app.ENABLE_SKILL_SELECT_GUI:
	import uiselectskill

if app.ENABLE_ITEMSHOP:
	import uiItemShop

if app.ENABLE_RENDER_TARGET_PREVIEW:
	import uiRenderTargetView

if app.ENABLE_SHOP_SEARCH:
	import uishopsearch

if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
	import uivirtualmarket

if PVP_MATCHMAKING_ENABLED:
	import uipvpmatchmaking

if app.ENABLE_DUNGEON_INFO:
	import uiDungeonTrack

if app.ENABLE_RANKING_SYSTEM:
	import uiRankingBoard

if app.ENABLE_EVENT_MANAGER:
	import uiEventCalendar

if app.ENABLE_WINDOW_RESIZE:
	from resizeexpr import Expr

import net

if app.ENABLE_OFFLINE_SHOP:
	import uiOfflineShop
	import uiSellHistory

if app.ENABLE_MAINTENANCE_SYSTEM:
	import uiMaintenance

if app.ENABLE_SHOW_CHEST_DROP:
	import uiChestDrop

if app.ENABLE_GROWTH_PET_SYSTEM:
	import uiPetInfo 

if app.ENABLE_PLAYER_RANKING:
	import uirankinfo

if app.ENABLE_BIOLOG_SYSTEM:
	import uiBiolog
	import uibiologresearch

if app.ENABLE_AURA_SYSTEM:
	import uiAura

if app.ENABLE_LOADING_PERFORMANCE:
	import uiWarpShower

if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
	import uiSkillUpgrade

if app.ENABLE_KINGDOMS_WAR:
	import uikingdomswar

if app.ENABLE_WHEEL_OF_FORTUNE:
	import uiWheelofFortune

if app.ENABLE_EXCHANGE_LOG:
	import uiExchangeLog

if app.ENABLE_SCROLL_ATLAS:
	import uiScroll

if app.ENABLE_DESTROY_ITEM_RESTORE:
	import uiGetBackItem

if CAPTCHA_WINDOW_ENABLED:
	import uiCaptchaNew

if app.ENABLE_REWARD_SYSTEM:
	import uiReward

if app.ENABLE_DUNGEON_TIME_WINDOW:
	import uiDungeonTime

if app.ENABLE_BUFF_SYSTEM:
	import uiBuff
	import uiBuffUpgrade

if app.ENABLE_SWITCHBOT_SYSTEM:
	import uiSwitchbot

if app.ENABLE_MINI_GAME_CATCH_KING:
	import uiMiniGameCatchKing

if app.ENABLE_FISHING_GAME:
	import uiFishingGame

if app.ENABLE_ATTR_6TH_7TH:
	import uiAttr67Add

if app.ENABLE_WIKI:
	import uiWiki

if app.ENABLE_BOSS_TRACK:
	import uiBossTrack

if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
	import uiGuildDragonLairRanking

if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
	import uiAutoHuntingSystem

IsQBHide = 0
IsWisperHide = 0

class UnifiedMessengerRouter(object):
	def __init__(self, interface):
		self.interface = interface
		self.window = None
		self.recoveryNotices = set()
		self.notifications = unifiedmessengernotifications.NotificationController(
			messengerHistory, self.__PresentIncoming, snd, app,
			app.GetGlobalTime)

	def Available(self):
		try:
			return bool(net.IsUnifiedMessengerAvailable())
		except:
			return False

	def __Window(self):
		if not self.window:
			self.window = uiUnifiedMessenger.UnifiedMessengerWindow()
			self.window.BindInterface(self.interface)
		return self.window

	def Open(self, name=None, key=None):
		if not self.Available():
			return False
		return self.__Window().Open(name, key)

	def OpenWithDraft(self, name, draft):
		if not self.Available():
			return False
		window = self.__Window()
		if not window.Open(name):
			return False
		window.composer.SetText(draft)
		window.composer.SetFocus()
		return True

	def OpenWithoutTarget(self):
		if not self.Available():
			return False
		return self.__Window().OpenWithoutTarget()

	def Receive(self, name):
		if not self.Available():
			return False
		self.notifications.NotifyIncoming("", self.__NotificationSnapshot(), name)
		return True

	def __PresentIncoming(self, key, name):
		self.interface.ShowUnifiedMessengerNotification(key, name)

	def __NotificationSnapshot(self):
		window = self.window
		return {
			"window_exists": bool(window),
			"visible": bool(window and window.loaded and window.IsShow()),
			"selected_key": window.selectedKey if window else "",
			"selected_name": window.selectedName if window else "",
		}

	def Toggle(self):
		if not self.Available():
			return False
		return self.__Window().Toggle()

	def IsOpen(self, name):
		if not self.Available():
			return None
		return bool(self.window and self.window.IsConversationOpen(name))

	def Capability(self, enabled, pid, maxBody, pendingPerPair, pendingPerSender, retentionSeconds):
		if enabled:
			return
		self.Destroy()

	def PlayerLookupCapability(self, enabled):
		if self.window:
			self.window.OnPlayerLookupCapability(enabled)

	def PlayerLookup(self, token, mode, status, rows):
		if self.window:
			self.window.OnPlayerLookupResult(token, mode, status, rows)

	def SubmitResult(self, messageID, error):
		if self.window:
			self.window.OnSubmitResult(messageID, error)

	def Changed(self, key, event):
		if event == 3:
			self.notifications.NotifyIncoming(
				key, self.__NotificationSnapshot())
		if self.window:
			self.window.OnHistoryChanged(key, event)

	def Typing(self, pid, name, active):
		if self.window:
			self.window.OnTyping(pid, name, active)

	def Recovery(self, status):
		# The notice must not depend on a loaded Messenger window (it is usually
		# not created yet when the session starts). Show each kind once.
		key = unifiedmessengermodel.recovery_key(status)
		if self.window:
			self.window.OnRecovery(status)
		if key in self.recoveryNotices:
			return
		text = str(getattr(localeInfo, key, "") or "")
		if text:
			self.recoveryNotices.add(key)
			chat.AppendChat(chat.CHAT_TYPE_INFO, text)

	def Destroy(self):
		if self.window:
			self.window.Destroy()
		self.window = None

class Interface(object):
	CHARACTER_STATUS_TAB = 1
	CHARACTER_SKILL_TAB = 2

	def ShowPetAlbumNotice(self, notice):
		if self.petAlbumNotice is None:
			import uipetalbumnotice
			self.petAlbumNotice = uipetalbumnotice.PetAlbumNoticeWindow()
		if self.IsHideUiMode or self.petAlbumArrivalVisible:
			self.petAlbumNotice.Suspend()
		self.petAlbumNotice.Add(notice)

	def CapturePetAlbumNotices(self):
		window = getattr(self, "petAlbumNotice", None)
		import petalbumstate
		album = petalbumstate.GetState()
		context = album.context
		notices = window.Pending() if window else []
		if not context or not (notices or album.unreadCaptures):
			return None
		return {"hash": context[0], "profile": context[2], "notices": notices,
			"unread_captures": album.unreadCaptures}

	def __RestoreWarpPetAlbumNotices(self, value):
		import petalbumstate
		context = petalbumstate.GetState().context
		if not context:
			return False
		if value.get("hash") == context[0] and value.get("profile") == context[2]:
			petalbumstate.GetState().RestoreUnreadCaptures(value.get("unread_captures", 0))
			for notice in value.get("notices", []):
				self.ShowPetAlbumNotice(notice)
		return True

	def ClearPetAlbumNotices(self):
		if self.petAlbumNotice:
			self.petAlbumNotice.Close()

	def __init__(self):
		self._metadataInventoryDirty = False
		self._metadataRarityDirty = False
		systemSetting.SetInterfaceHandler(self)
		self.unifiedMessengerRouter = UnifiedMessengerRouter(self)
		self.wndFeatureComingSoon = None
		self.featureAvailabilityListener = None
		self.windowOpenPosition = 0
		self.dlgWhisperWithoutTarget = None
		self.inputDialog = None
		self.noticeBoard = None
		self.petAlbumNotice = None
		self.petAlbumArrivalVisible = False
		self.tipBoard = None
		self.bigBoard = None

		if app.ENABLE_LOADING_PERFORMANCE:
			self.wndWarpShower = None

		if CAPTCHA_WINDOW_ENABLED:
			self.wndCaptchaNew = None

		if app.ENABLE_12ZI:
			self.missionBoard = None

		if app.ENABLE_WHEEL_OF_FORTUNE:
			self.wndWheelofFortune=None

		if app.ENABLE_EXCHANGE_LOG:
			self.wndExchangeLog = None

		if app.ENABLE_REWARD_SYSTEM:
			self.wndReward = None

		# ITEM_MALL
		self.mallPageDlg = None
		# END_OF_ITEM_MALL
		if app.ENABLE_OFFLINE_SHOP:
			self.wndOfflineShopBuilder = None
			self.wndSellHistory = None
		if app.ENABLE_SHOP_SEARCH:
			self.wndShopSearch = None
		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			self.wndVirtualMarket = None
		self.wndWeb = None
		self.wndTaskBar = None
		self.wndCharacter = None
		self.wndInventory = None
		self.wndTalisman = None
		self.wndQuickEquip = None
		self.talismanSetAvailable = False
		self.wndRarity = None
		self.wndTargetedRarity = None
		self.wndResonance = None
		self.wndCostumeInventory = None
		self.separateCostumeInventory = \
			uiCostumeInventory.IsSeparateModeEnabled()
		self.wndExpandedTaskBar = None
		self.wndDragonSoul = None
		self.wndDragonSoulRefine = None
		self.wndChat = None
		self.wndMessenger = None
		self.wndMiniMap = None
		self.wndSkillTree = None
		self.wndMountSystem = None
		self.wndPermanentTasks = None
		self.permanentTasksAvailable = False
		self.permanentTasksGeneration = 0
		self.permanentTasksSnapshot = None
		self.permanentTasksHunts = {}
		self.permanentTasksSnapshotPending = False
		self.permanentTasksSubmitPending = False
		self.wndDailyTasks = None
		self.dailyTasksAvailable = False
		self.dailyTasksGeneration = 0
		self.dailyTasksSnapshot = None
		self.dailyTasksSnapshotPending = False
		self.wndGMPanel = None
		self.wndCustomPorts = None
		self.afkSystem = None
		self.dropTrackerSystem = None
		self.quickBuffSystem = None
		self.wndGuild = None
		self.wndGuildBuilding = None
		if app.ENABLE_SKILL_SELECT_GUI:
			self.wndSkillSelect = None
		if app.WJ_ENABLE_TRADABLE_ICON or app.ENABLE_MOVE_COSTUME_ATTR:
			self.OnTopWindow = None
			self.dlgShop = None
			self.dlgExchange = None
			self.privateShopBuilder = None
			self.wndSafebox = None
		self.listGMName = {}
		self.wndQuestWindow = {}
		self.wndQuestWindowNewKey = 0
		self.privateShopAdvertisementBoardDict = {}
		self.guildScoreBoardDict = {}
		self.equipmentDialogDict = {}

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			self.wndSkillBookCombination = None

		self.wndMiniGame = None

		if app.ENABLE_SWITCHBOT_SYSTEM:
			self.wndSwitchbot = None

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.wndChangeLook = None

		if app.ENABLE_TELEPORT_WINDOW:
			self.wndTeleportPanel = None
			self.wndTeleportAtlas = None

		if app.ENABLE_AURA_SYSTEM:
			self.wndAura = None

		if app.ENABLE_GEM_SYSTEM:
			self.wndExpandedMoneyTaskBar = None

		if app.ENABLE_MINI_GAME_CATCH_KING:
			self.wndCatchKingGame = None
			self.wndCatchKingIcon = None

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			self.wndUpgradeSkill = None

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.wndRenderTargetView = None

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndSpecialInventory = None

		if app.ENABLE_BUFF_SYSTEM:
			self.wndSupportPG = None
			self.wndSupportUpgrade = None

		if app.ENABLE_CUBE_RENEWAL:
			self.wndCubeRenewal = None

		if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			self.wndCaptcha = None

		if app.ENABLE_DUNGEON_TIME_WINDOW:
			self.wndDungeonTime = None

		if app.ENABLE_ITEMSHOP:
			self.wndItemShop = None
			self.itemShopDragonCoin = 0

		if app.ENABLE_EVENT_MANAGER:
			self.wndEventManager = None
			self.wndEventIcon = None

		if app.ENABLE_MAINTENANCE_SYSTEM:
			self.wndMaintenance = None

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndSpecialInventory = None

		if app.ENABLE_SHOW_CHEST_DROP:
			self.dlgChestDrop = None

		if app.ENABLE_DUNGEON_INFO:
			self.wndDungeonTrack = None
			self.wndDungeonManager = None

		self.wndGameNotification = None
		self.wndCountdownHUD = None
		self.wndMissionBooks = None
		self.systemNotifications = None
		self.countdownLaunchers = []
		self.countdownKnownDungeons = set()
		if app.ENABLE_BIOLOG_SYSTEM:
			self.wndBio = None

		if PVP_MATCHMAKING_ENABLED:
			self.wndPvPMatchmaking = None

		if app.ENABLE_WIKI:
			self.wndWiki = None

		if app.ENABLE_DESTROY_ITEM_RESTORE:
			self.wndSaveItem = None

		if app.ENABLE_ATTR_6TH_7TH:
			self.wndAttr67Add = None

		if app.ENABLE_FISHING_GAME:
			self.wndFishingGame = None

		if app.ENABLE_RANKING_SYSTEM:
			self.wndRankingBoardWindow = None

		if app.ENABLE_BOSS_TRACK:
			self.wndBossTrack = None

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting = None

		event.SetInterfaceWindow(self)

		self.uiAffectshower = None
		self.uitargetBoard = None
		self.IsHideUiMode = False

	def __del__(self):
		systemSetting.DestroyInterfaceHandler()
		event.SetInterfaceWindow(None)

	if app.ENABLE_WINDOW_RESIZE:
		def UpdateUI(self):
			self.__ArrangeQuestButton()
			self.__ArrangeWhisperButton()
			if self.wndChat:
				self.wndChat.Refresh()
				try:
					self.wndChat.chatInputSet.RefreshPosition()
				except:
					pass
			try:
				if self.uitargetBoard and self.uitargetBoard.IsShow():
					self.uitargetBoard.UpdatePosition()
			except:
				pass

			if self.wndInventory:
				try:
					if app.ENABLE_BRAVE_CAPE_RENEWAL and self.wndInventory.wndBraveCape:
						self.wndInventory.wndBraveCape.AdjustPosition(*self.wndInventory.GetInventoryBodyGlobalPosition())
				except:
					pass

	################################
	## Make Windows & Dialogs
	def __MakeUICurtain(self):
		wndUICurtain = ui.Bar("TOP_MOST")
		wndUICurtain.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		if app.ENABLE_WINDOW_RESIZE:
			wndUICurtain.SetResizeDic({"size": (Expr("SCREEN_WIDTH"), Expr("SCREEN_HEIGHT"))})
		wndUICurtain.SetColor(0x77000000)
		wndUICurtain.Hide()
		self.wndUICurtain = wndUICurtain

	def __MakeMessengerWindow(self):
		self.wndMessenger = uiMessenger.MessengerWindow()
		if app.ENABLE_CHATTING_WINDOW_RENEWAL:
			self.wndMessenger.BindInterface(self)

		from _weakref import proxy
		self.wndMessenger.SetWhisperButtonEvent(lambda n,i=proxy(self):i.OpenWhisperDialog(n))
		self.wndMessenger.SetUnifiedMessengerButtonEvent(
			ui.__mem_func__(self.OpenUnifiedMessenger))
		self.wndMessenger.SetGuildButtonEvent(ui.__mem_func__(self.ToggleGuildWindow))

	def __MakeGuildWindow(self):
		self.wndGuild = uiGuildV2.GuildWindowRouter(self, uiGuild.GuildWindow())

	def __MakeChatWindow(self):
		if hasattr(chat, "GetRecentMessages"):
			import uicompactchat
			wndChat = uicompactchat.ChatWindow()
		else:
			# Older executables can read the pack during a controlled promotion.
			wndChat = uiChat.ChatWindow()
			wndChat.SetSize(wndChat.CHAT_WINDOW_WIDTH, 0)
			wndChat.SetPosition(wndMgr.GetScreenWidth()//2 - wndChat.CHAT_WINDOW_WIDTH//2, wndMgr.GetScreenHeight() - wndChat.EDIT_LINE_HEIGHT - 37)
			if app.ENABLE_WINDOW_RESIZE:
				wndChat.SetResizeDic({"position": (Expr("SCREEN_WIDTH")/2 - wndChat.CHAT_WINDOW_WIDTH//2, Expr("SCREEN_HEIGHT") - wndChat.EDIT_LINE_HEIGHT - 37)})
			wndChat.SetHeight(200)
		wndChat.Refresh()
		wndChat.Show()

		self.wndChat = wndChat
		self.wndChat.BindInterface(self)
		self.wndChat.SetSendWhisperEvent(ui.__mem_func__(self.OpenWhisperDialogWithoutTarget))
		self.wndChat.SetOpenChatLogEvent(ui.__mem_func__(self.ToggleChatLogWindow))

	if app.ENABLE_WIKI:
		def OpenWikiWindow(self):
			self.MakeWiki()
			if self.wndWiki.IsShow():
				self.wndWiki.Close()
			else:
				self.wndWiki.Open()
		def MakeWiki(self):
			# if not chr.IsGameMaster(player.GetMainCharacterIndex()):
			# 	return chat.AppendChat(chat.CHAT_TYPE_INFO, "Feature deactivated during Beta period. The reason was taken to keep the HYPE!")
			
			if self.wndWiki == None:
				self.wndWiki = uiWiki.EncyclopediaofGame()
				self.wndWiki.LoadGuidePage()

	def __MakeTaskBar(self):
		wndTaskBar = uiTaskBar.TaskBar()
		wndTaskBar.LoadWindow()
		self.wndTaskBar = wndTaskBar
		if self.dropTrackerSystem:
			self.dropTrackerSystem.BindTaskBar(self.wndTaskBar)
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_CHARACTER, ui.__mem_func__(self.ToggleCharacterWindowStatusPage))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_INVENTORY, ui.__mem_func__(self.ToggleInventoryWindow))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_MESSENGER, ui.__mem_func__(self.ToggleMessenger))
		self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_SYSTEM, ui.__mem_func__(self.ToggleSystemDialog))
		if self.wndTaskBar.HasPrimaryAuxButton():
			if uiTaskBar.TaskBar.IS_EXPANDED:
				self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_EXPAND, ui.__mem_func__(self.ToggleExpandedButton))
			else:
				self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_CHAT, ui.__mem_func__(self.ToggleChat))

		self.wndExpandedTaskBar = uiTaskBar.ExpandedTaskBar()
		self.wndExpandedTaskBar.LoadWindow()
		self.wndExpandedTaskBar.BindInventoryWindow(self.wndInventory)
		self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_QUICK_EQUIP, ui.__mem_func__(self.ToggleQuickEquipWindow))
		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_SPECIAL_INVENTORY, ui.__mem_func__(self.ToggleSpecialInventoryWindow))
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_DRAGON_SOUL, ui.__mem_func__(self.ToggleDragonSoulWindow))
		if app.ENABLE_CUBE_RENEWAL:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_DEW, ui.__mem_func__(self.ToggleDewCraftWindow))
		if app.ENABLE_TELEPORT_WINDOW:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_TELEPORT, ui.__mem_func__(self.ToggleTeleportAtlas))
		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_PET, ui.__mem_func__(self.TogglePetInformationWindow))
		if app.ENABLE_SWITCHBOT_SYSTEM:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_SWITCHBOT, ui.__mem_func__(self.ToggleSwitchbotWindow))
		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_SHOP_SEARCH, ui.__mem_func__(self.OpenVirtualMarketWindow))
		if app.ENABLE_BIOLOG_SYSTEM:
			self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_BIOLOG, ui.__mem_func__(self.ToggleBiologWindow))
		self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN, ui.__mem_func__(self.ToggleTalismanWindow))
		self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_MISSION_BOOKS, ui.__mem_func__(self.ToggleMissionBooks))
		self.wndExpandedTaskBar.SetToggleButtonEvent(uiTaskBar.ExpandedTaskBar.BUTTON_MOUNT, ui.__mem_func__(self.ToggleMountSystemWindow))
		self.wndExpandedTaskBar.SetButtonEnabled(
			uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN,
			self.talismanSetAvailable,
		)

		self.wndEnergyBar = None

		if app.ENABLE_GEM_SYSTEM:
			self.wndTaskBar.SetToggleButtonEvent(uiTaskBar.TaskBar.BUTTON_EXPAND_MONEY, ui.__mem_func__(self.ToggleExpandedMoneyButton))
			self.wndExpandedMoneyTaskBar = uiTaskBar.ExpandedMoneyTaskBar()
			self.wndExpandedMoneyTaskBar.LoadWindow()
			if self.wndInventory:
				self.wndInventory.SetExpandedMoneyBar(self.wndExpandedMoneyTaskBar)

	def __MakeParty(self):
		wndParty = uiParty.PartyWindow()
		wndParty.Hide()
		self.wndParty = wndParty

	def __MakeGameButtonWindow(self):
		wndGameButton = uiGameButton.GameButtonWindow()
		wndGameButton.SetTop()
		wndGameButton.Show()
		wndGameButton.SetButtonEvent("STATUS", ui.__mem_func__(self.__OnClickStatusPlusButton))
		wndGameButton.SetButtonEvent("SKILL", ui.__mem_func__(self.__OnClickSkillPlusButton))
		wndGameButton.SetButtonEvent("QUEST", ui.__mem_func__(self.__OnClickQuestButton))
		wndGameButton.SetButtonEvent("HELP", ui.__mem_func__(self.__OnClickHelpButton))
		wndGameButton.SetButtonEvent("BUILD", ui.__mem_func__(self.__OnClickBuildButton))

		self.wndGameButton = wndGameButton

	def __IsChatOpen(self):
		return True

	def __MakeSkillTreeWindow(self):
		self.wndSkillTree = uiskilltree.SkillTreeWindow()
		self.wndSkillTree.Hide()
		self.wndMiniMap.SetSkillTreeButtonEvent(ui.__mem_func__(self.ToggleSkillTreeWindow))

	def __MakeGMPanelWindow(self):
		self.wndGMPanel = uigmpanel.GMPanelWindow()
		self.wndGMPanel.Hide()

	def __MakeWindows(self):
		self.wndCharacter = uiCharacter.CharacterWindow()
		self.wndCharacter.SetPermanentTaskBonuses(0, 0)
		self.wndPermanentTasks = uipermanenttasks.PermanentTasksWindow()
		self.wndPermanentTasks.SetSnapshotRequestEvent(
			ui.__mem_func__(self.RequestPermanentTasksSnapshot),
		)
		self.wndPermanentTasks.SetCollectorCapability(
			self.permanentTasksAvailable
		)
		if getattr(app, "ENABLE_DAILY_TASKS", 0):
			self.wndDailyTasks = uidailytasks.DailyTasksWindow()
			self.wndDailyTasks.SetSnapshotRequestEvent(
				ui.__mem_func__(self.RequestDailyTasksSnapshot)
			)
			self.wndDailyTasks.SetHandInEvent(
				ui.__mem_func__(self.RequestDailyTaskHandIn)
			)

		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			self.wndCustomPorts = uicustomports.CustomPortsWindow()

		if getattr(app, "ENABLE_AFK_SYSTEM", 0):
			self.afkSystem = uiafksystem.AfkSystem()
			self.afkSystem.BindTipBoard(self.tipBoard)

		if getattr(app, "ENABLE_DROP_TRACKER", 0):
			self.dropTrackerSystem = uidroptracker.DropTrackerSystem()

		self.quickBuffSystem = uiquickbuff.QuickBuffSystem()
		self.wndInventory = uiInventory.InventoryWindow()
		self.wndInventory.BindInterfaceClass(self)
		self.wndQuickEquip = uiquickequip.QuickEquipWindow()
		self.wndQuickEquip.SetCloseEvent(ui.__mem_func__(self.__QuickEquipClosed))
		if uiTalisman.IsSupported():
			candidate = uiTalisman.TalismanWindow()
			if candidate.IsLoaded():
				self.wndTalisman = candidate
				self.wndTalisman.SetCloseEvent(
					ui.__mem_func__(self.CloseTalismanWindow)
				)
		self.talismanSetAvailable = self.wndTalisman is not None
		if self.wndTalisman:
			self.wndTalisman.SetCapability(self.talismanSetAvailable)
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonEnabled(
				uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN,
				self.talismanSetAvailable,
			)
		self.wndRarity = uiRarity.RarityDialog()
		self.wndRarity.BindInterface(self)
		self.wndResonance = uiresonance.ResonanceWindow()
		self.wndCostumeInventory = \
			uiCostumeInventory.CostumeInventoryWindow(self.wndInventory)

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul = uiDragonSoul.DragonSoulWindow()
			self.wndDragonSoul.BindInterfaceClass(self)
			self.wndDragonSoulRefine = uiDragonSoul.DragonSoulRefineWindow()
		else:
			wndDragonSoul = None
			wndDragonSoulRefine = None

		self.wndMiniMap = uiMiniMap.MiniMap()
		self.wndMountSystem = uiMountSystem.MountSystemWindow()
		if app.ENABLE_DUNGEON_INFO:
			self.wndMiniMap.BindInterfaceClass(self)
		if not osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndSafebox = uiSafebox.SafeboxWindow()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndSafebox.BindInterface(self)

		if app.ENABLE_SWITCHBOT_SYSTEM:
			self.wndSwitchbot = uiSwitchbot.SwitchbotWindow()

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			self.wndSkillBookCombination = uiSkillBookCombination.SkillBookCombinationWindow()

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.wndChangeLook = uiChangeLook.ChangeLookWindow()

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.wndRenderTargetView = uiRenderTargetView.RenderTargetWindow()

		if app.ENABLE_DUNGEON_TIME_WINDOW:
			self.wndDungeonTime = uiDungeonTime.DungeonTimeWindow()

		if app.ENABLE_RANKING_SYSTEM:
			self.wndRankingBoardWindow = uiRankingBoard.RankingBoardWindow()

		if app.ENABLE_BUFF_SYSTEM:
			self.wndSupportPG = uiBuff.SupportMainGui()
			self.wndSupportUpgrade = uiBuffUpgrade.SupportUpgrade()

		if app.ENABLE_ATTR_6TH_7TH:
			wndAttr67Add = uiAttr67Add.Attr67AddWindow()
			if app.WJ_ENABLE_TRADABLE_ICON:
				wndAttr67Add.BindInterface(self)
				wndAttr67Add.SetInven(self.wndInventory)
			self.wndAttr67Add = wndAttr67Add

		if not osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndMall = uiSafebox.MallWindow()
		wndChatLog = uiChat.ChatLogWindow()
		wndChatLog.BindInterface(self)
		self.wndChatLog = wndChatLog

		if app.ENABLE_SHOP_SEARCH:
			self.wndShopSearch = uishopsearch.ShopSearchWindow(self)

		if app.ENABLE_KINGDOMS_WAR:
			self.wndKingdomsWar = uikingdomswar.Window()

		if app.ENABLE_MINI_GAME_CATCH_KING:
			self.wndCatchKingGame = uiMiniGameCatchKing.MiniGameCatchKing()

		if app.ENABLE_SKILL_SELECT_GUI:
			self.wndSkillSelect = uiselectskill.SkillSelectWindow()

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.SetDragonSoulRefineWindow(self.wndDragonSoulRefine)
			self.wndDragonSoulRefine.SetInventoryWindows(self.wndInventory, self.wndDragonSoul)
			self.wndInventory.SetDragonSoulRefineWindow(self.wndDragonSoulRefine)

		if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
			self.wndGuildDragonLairRanking = uiGuildDragonLairRanking.GuildDragonLairRankingDialog()

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				self.wndSpecialInventory = uiSpecialInventory.SpecialInventoryWindow(self.wndInventory)
			else:
				self.wndSpecialInventory = uiSpecialInventory.SpecialInventoryWindow(self.wndInventory)
			self.wndSpecialInventory.BindInterfaceClass(self)
			if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
				self.wndSafebox = uiSafebox.SafeboxWindow(self.wndSpecialInventory)
				self.wndMall = uiSafebox.MallWindow(self.wndSpecialInventory)
				if app.WJ_ENABLE_TRADABLE_ICON:
					self.wndSafebox.BindInterface(self)
				self.wndSpecialInventory.BindSafeboxAndMallClass(self.wndSafebox, self.wndMall)

		if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			self.wndCaptcha = uiCaptcha.CaptchaDialog()
			self.wndCaptcha.BindInterface(self)

		if app.ENABLE_OFFLINE_SHOP:
			self.wndSellHistory = uiSellHistory.SellLogWindow()

		if app.ENABLE_SHOW_CHEST_DROP:
			self.dlgChestDrop = uiChestDrop.ChestDropWindow()

		if app.ENABLE_MAINTENANCE_SYSTEM:
			self.wndMaintenance = uiMaintenance.MaintenanceBoard()

		if app.ENABLE_AURA_SYSTEM:
			wndAura = uiAura.AuraWindow()
			self.wndAura = wndAura

			if self.wndInventory:
				self.wndInventory.SetAuraWindow(self.wndAura)

			if self.wndSpecialInventory:
				self.wndSpecialInventory.SetAuraWindow(self.wndAura)
				
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndAura.BindInterface(self)
				if self.wndInventory:
					self.wndAura.SetInven(self.wndInventory)
				if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
					if self.wndSpecialInventory:
						self.wndAura.SetSpecialInven(self.wndSpecialInventory)

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			self.wndUpgradeSkill = uiSkillUpgrade.SkillUpgradeWindow()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.wndPetInfoWindow = uiPetInfo.PetInformationWindow()
			self.wndPetInfoWindow.BindInterfaceClass(self)
			self.wndInventory.SetPetHatchingWindow(self.wndPetInfoWindow.GetPetHatchingWindow())
			self.wndInventory.SetPetFeedWindow(self.wndPetInfoWindow.GetPetFeedWindow())
			self.wndInventory.SetPetNameChangeWindow(self.wndPetInfoWindow.GetPetNameChangeWindow())

		if app.ENABLE_PLAYER_RANKING:
			self.wndRankInfo = uirankinfo.RankInfo()

		if app.ENABLE_LOADING_PERFORMANCE:
			self.wndWarpShower = uiWarpShower.WarpShowerWindow()

		if app.ENABLE_FISHING_GAME:
			self.wndFishingGame = uiFishingGame.FishGame()

		if CAPTCHA_WINDOW_ENABLED:
			self.wndCaptchaNew = uiCaptchaNew.CaptchaWindow()

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting = uiAutoHuntingSystem.AutoHuntingSystemWindow()
			self.wndAutoHunting.LoadAutoWindow()

	def __MakeDialogs(self):
		self.dlgExchange = uiExchange.ExchangeDialog()
		self.dlgExchange.LoadDialog()
		self.dlgExchange.SetCenterPosition()
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.dlgExchange.BindInterface(self)
		self.dlgExchange.Hide()

		self.dlgPointReset = uiPointReset.PointResetDialog()
		self.dlgPointReset.LoadDialog()
		self.dlgPointReset.Hide()

		self.dlgShop = uiShop.ShopDialog()
		self.dlgShop.LoadDialog()
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.dlgShop.BindInterface(self)
		self.dlgShop.Hide()

		self.dlgRestart = uiRestart.RestartDialog()
		self.dlgRestart.LoadDialog()
		self.dlgRestart.Hide()

		if app.ENABLE_TELEPORT_WINDOW:
			self.wndTeleportPanel = uiTeleportPanel.TeleportPanel()
			self.wndTeleportAtlas = uiTeleport.TeleportAtlasWindow()

		self.dlgSystem = uiSystem.SystemDialog()
		self.dlgSystem.LoadDialog()
		self.dlgSystem.SetOpenHelpWindowEvent(ui.__mem_func__(self.OpenHelpWindow))
		self.dlgSystem.SetPrepareExitEvent(
			ui.__mem_func__(self.CloseTransactionalWindowsForExit)
		)

		self.dlgSystem.Hide()

		self.dlgPassword = uiSafebox.PasswordDialog()
		self.dlgPassword.Hide()

		self.hyperlinkItemTooltip = uiToolTip.HyperlinkItemToolTip()
		self.hyperlinkItemTooltip.Hide()

		self.tooltipItem = uiToolTip.ItemToolTip()
		if app.ENABLE_DS_SET or app.ENABLE_RENDER_TARGET_PREVIEW:
			self.tooltipItem.BindInterface(self)
		self.tooltipItem.Hide()
		if self.wndMountSystem:
			self.wndMountSystem.SetItemToolTip(self.tooltipItem)
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetItemToolTip(self.tooltipItem)
		if self.wndDailyTasks:
			self.wndDailyTasks.SetItemToolTip(self.tooltipItem)
		if self.wndResonance:
			self.wndResonance.SetItemToolTip(self.tooltipItem)

		self.tooltipSkill = uiToolTip.SkillToolTip()
		self.tooltipSkill.Hide()

		self.privateShopBuilder = uiPrivateShopBuilder.PrivateShopBuilder()
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.privateShopBuilder.BindInterface(self)
		self.privateShopBuilder.Hide()

		self.dlgRefineNew = uiRefine.RefineDialogNew()
		self.dlgRefineNew.BindInterface(self)
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.dlgRefineNew.SetInven(self.wndInventory)
		self.dlgRefineNew.Hide()

		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			self.dlgRefineElement = uiRefine.RefineElementDialog()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.dlgRefineElement.SetInven(self.wndInventory)
			self.dlgRefineElement.Hide()

			self.dlgRefineElementChange = uiRefine.RefineElementChangeDialog()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.dlgRefineElementChange.SetInven(self.wndInventory)
			self.dlgRefineElementChange.Hide()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.tooltipPetSkill = uiToolTip.PetSkillToolTip()
			self.tooltipPetSkill.Hide()

		if app.ENABLE_BUFF_SYSTEM:
			self.wndSupportPG.SetItemToolTip(self.tooltipItem)
			self.wndSupportPG.SetSkillToolTip(self.tooltipSkill)	
			self.wndSupportPG.BindInterface(self)
			self.wndSupportUpgrade.SetItemToolTip(self.tooltipItem)	
			self.wndSupportUpgrade.SetSkillToolTip(self.tooltipSkill)

	def GetInventoryWnd(self):
		return self.wndInventory

	def OpenRarityDialog(self, scrollVnum, targetSlot):
		if int(scrollVnum) == 79632:
			if self.wndRarity and self.wndRarity.IsBusy():
				return False
			if self.wndTargetedRarity is None:
				import uiTargetedRarity
				self.wndTargetedRarity = uiTargetedRarity.TargetedRarityDialog()
			return self.wndTargetedRarity.Open(int(targetSlot))
		if self.wndTargetedRarity and self.wndTargetedRarity.IsBusy():
			return False
		if not self.wndRarity:
			return False
		mode = uiRarity.MODE_REROLL if int(scrollVnum) == 79630 else uiRarity.MODE_PROMOTION
		return self.wndRarity.Open(mode, int(targetSlot))

	def RarityMetadataChanged(self, context, windowOrSide, slot, vid, publicId, grade):
		if int(context) == getattr(net, "RARITY_CONTEXT_INVENTORY", 1):
			self._metadataInventoryDirty = True
		self._metadataRarityDirty = True

	def RarityPreviewResult(self, requestId, mode, result, currentGrade, targetGrade,
			chanceBp, yang, boosterAvailable, boosterSelected, costs):
		if int(mode) == 2:
			if self.wndTargetedRarity:
				self.wndTargetedRarity.OnPreviewResult(requestId, mode, result, currentGrade,
					targetGrade, chanceBp, yang, boosterAvailable, boosterSelected, costs)
			return
		if self.wndRarity:
			self.wndRarity.OnPreviewResult(requestId, mode, result, currentGrade,
				targetGrade, chanceBp, yang, boosterAvailable, boosterSelected, costs)

	def RarityCommitResult(self, requestId, mode, result, succeeded, grade):
		if int(mode) == 2:
			if self.wndTargetedRarity:
				self.wndTargetedRarity.OnCommitResult(requestId, mode, result, succeeded, grade)
			return
		if self.wndRarity:
			self.wndRarity.OnCommitResult(requestId, mode, result, succeeded, grade)

	def InsertResonanceSealDirect(self, targetCell, sourceCell):
		if not self.wndResonance:
			return False
		return self.wndResonance.InsertResonanceSealDirect(targetCell, sourceCell)

	def OpenResonanceUnlockDialog(self, targetCell, sourceKeyCell):
		if not self.wndResonance:
			return False
		return self.wndResonance.OpenUnlockFromKey(targetCell, sourceKeyCell)

	def ResonanceCapabilityChanged(self, available):
		if self.wndResonance and not available:
			self.wndResonance.ResetRuntime()

	def ResonanceMetadataChanged(self, context, windowOrSide, slot, vid, publicId):
		if self.wndResonance:
			self.wndResonance.OnMetadataChanged(context, windowOrSide, slot, vid, publicId)
		if int(context) == 1:
			self._metadataInventoryDirty = True

	def FlushItemMetadataRefresh(self):
		# Item state has already been applied natively. A chest burst must not
		# rebuild every slot for each rarity and resonance metadata packet.
		inventoryDirty = self._metadataInventoryDirty
		rarityDirty = self._metadataRarityDirty
		self._metadataInventoryDirty = False
		self._metadataRarityDirty = False
		if inventoryDirty and self.wndInventory:
			self.wndInventory.RefreshItemSlot()
		if rarityDirty and self.wndTargetedRarity and self.wndTargetedRarity.IsShow():
			self.wndTargetedRarity.Refresh()

	def ResonanceUnlockConfigChanged(self):
		if self.wndResonance:
			self.wndResonance.OnUnlockConfigChanged()

	def ResonanceMutationResult(self, requestId, result, slot, vnum):
		if self.wndResonance:
			self.wndResonance.OnMutationResult(requestId, result, slot, vnum)

	def GetSpecialInventoryWnd(self):
		return self.wndSpecialInventory

	def __MakeHelpWindow(self):
		self.wndHelp = uiHelp.HelpWindow()
		self.wndHelp.LoadDialog()
		self.wndHelp.SetCloseEvent(ui.__mem_func__(self.CloseHelpWindow))
		self.wndHelp.Hide()

	def __MakeTipBoard(self):
		self.noticeBoard = uinoticeboard.NoticeBoard()
		self.tipBoard = uinoticeboard.NoticeSink(self.noticeBoard, 1)
		self.bigBoard = uinoticeboard.NoticeSink(self.noticeBoard, 4)
		if app.ENABLE_12ZI:
			self.missionBoard = uinoticeboard.MissionSink(self.noticeBoard)

	def UpdateNoticeBoard(self, arrivalVisible=False):
		self.petAlbumArrivalVisible = bool(arrivalVisible)
		if self.petAlbumNotice:
			if arrivalVisible or self.IsHideUiMode:
				self.petAlbumNotice.Suspend()
			else:
				self.petAlbumNotice.Resume()
		if self.noticeBoard:
			self.noticeBoard.Update(arrivalVisible)

	def __MakeWebWindow(self):
		if constInfo.IN_GAME_SHOP_ENABLE:
			import uiWeb
			self.wndWeb = uiWeb.WebWindow()
			self.wndWeb.LoadWindow()
			self.wndWeb.Hide()

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def __MakeAcceWindow(self):
			self.wndAcceCombine = uiAcce.CombineWindow()
			self.wndAcceCombine.LoadWindow()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndAcceCombine.BindInterface(self)
				if self.wndInventory:
					self.wndAcceCombine.SetInven(self.wndInventory)
				if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
					if self.wndSpecialInventory:
						self.wndAcceCombine.SetSpecialInven(self.wndSpecialInventory)
			self.wndAcceCombine.Hide()

			self.wndAcceAbsorption = uiAcce.AbsorbWindow()
			self.wndAcceAbsorption.LoadWindow()
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.wndAcceAbsorption.BindInterface(self)
				if self.wndInventory:
					self.wndAcceAbsorption.SetInven(self.wndInventory)
				if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
					if self.wndSpecialInventory:
						self.wndAcceAbsorption.SetSpecialInven(self.wndSpecialInventory)

			self.wndAcceAbsorption.Hide()

			if self.wndInventory:
				self.wndInventory.SetAcceWindow(self.wndAcceCombine, self.wndAcceAbsorption)

			if self.wndSpecialInventory:
				self.wndSpecialInventory.SetAcceWindow(self.wndAcceCombine, self.wndAcceAbsorption)

	def MakeGameNotification(self):
		self.wndGameNotification = uigamenotification.GameNotificationManager()

	def PushGameNotification(self, title, message, iconVnum=0):
		if not self.wndGameNotification:
			return False
		return self.wndGameNotification.Add(title, message, iconVnum)

	def PushVirtualMarketSaleNotification(self, transactionHigh, transactionLow,
			listingId, itemVnum, count, totalPrice):
		if not self.wndGameNotification:
			return False
		return self.wndGameNotification.AddSale(
			transactionHigh, transactionLow, listingId, itemVnum, count, totalPrice)

	if app.ENABLE_BIOLOG_SYSTEM:
		def MakeBioWindow(self):
			self.wndBio = uibiologresearch.BiologWindow()
			self.wndBio.dataKnown = False  # constructor placeholder, no server snapshot yet
			self.wndBio.Hide()

		def ToggleBiologWindow(self):
			if self.wndBio.IsShow():
				self.wndBio.Hide()
			else:
				self.wndBio.Show()
				self.wndBio.SetTop()

	if PVP_MATCHMAKING_ENABLED:
		def MakePvPMatchmakingWindow(self):
			self.wndPvPMatchmaking = uipvpmatchmaking.PvPMatchmakingWindow()

		def TogglePvPMatchmakingWindow(self):
			if not self.wndPvPMatchmaking:
				return
			if self.wndPvPMatchmaking.IsShow():
				self.wndPvPMatchmaking.Close()
			elif not featureavailability.IsAvailable(featureavailability.RANKED_ARENA):
				featureavailability.NotifyRefused(featureavailability.RANKED_ARENA)
			else:
				self.wndPvPMatchmaking.Show()

		def OnPvPMatchmakingChanged(self):
			if self.wndPvPMatchmaking:
				self.wndPvPMatchmaking.OnServerChanged()

	# The server owns the pause state of rankings and the rated arena
	# (featureavailability.py). A paused feature closes its windows; a refused
	# request of this player, or a pause while the window was open, answers
	# with the "coming soon" window. A mere state update never opens it.
	def __FeatureWindows(self, name):
		windows = []
		if name == featureavailability.RANKINGS:
			if app.ENABLE_PLAYER_RANKING:
				windows.append(getattr(self, "wndRankInfo", None))
			if app.ENABLE_RANKING_SYSTEM:
				windows.append(getattr(self, "wndRankingBoardWindow", None))
			if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
				windows.append(getattr(self, "wndGuildDragonLairRanking", None))
		elif name == featureavailability.RANKED_ARENA and PVP_MATCHMAKING_ENABLED:
			windows.append(getattr(self, "wndPvPMatchmaking", None))
		return [window for window in windows if window]

	def OnFeatureAvailability(self, name, available, refused):
		if available:
			return
		wasOpen = False
		for window in self.__FeatureWindows(name):
			if window.IsShow():
				wasOpen = True
				if hasattr(window, "Close"):
					window.Close()
				else:
					window.Hide()
		if refused or wasOpen:
			self.ShowFeatureComingSoon()

	def ShowFeatureComingSoon(self):
		if not self.wndFeatureComingSoon:
			self.wndFeatureComingSoon = uiCommon.PopupDialog()
			self.wndFeatureComingSoon.SetWidth(320)
		self.wndFeatureComingSoon.SetText(getattr(localeInfo, "FEATURE_COMING_SOON",
			"Coming soon. This feature is being prepared."))
		self.wndFeatureComingSoon.Open()

	def __MakeCubeWindow(self):
		self.wndCube = uiCube.CubeWindow()
		self.wndCube.LoadWindow()
		self.wndCube.Hide()

	def __MakeCubeResultWindow(self):
		self.wndCubeResult = uiCube.CubeResultWindow()
		self.wndCubeResult.LoadWindow()
		self.wndCubeResult.Hide()

	if app.ENABLE_MINI_GAME_OKEY:
		def __MakeCardsInfoWindow(self):
			self.wndCardsInfo = uiMiniGameRumi.CardsInfoWindow()
			self.wndCardsInfo.LoadWindow()
			self.wndCardsInfo.Hide()

		def __MakeCardsWindow(self):
			self.wndCards = uiMiniGameRumi.CardsWindow()
			self.wndCards.LoadWindow()
			self.wndCards.Hide()

		def __MakeCardsIconWindow(self):
			self.wndCardsIcon = uiMiniGameRumi.IngameWindow()
			self.wndCardsIcon.LoadWindow()
			self.wndCardsIcon.Hide()

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def __MakeCatchKingIconWindow(self):
			self.wndCatchKingIcon = uiMiniGameCatchKing.IngameWindow()
			self.wndCatchKingIcon.LoadWindow()
			self.wndCatchKingIcon.BindInterface(self)
			self.wndCatchKingIcon.Hide()

	# ACCESSORY_REFINE_ADD_METIN_STONE
	def __MakeItemSelectWindow(self):
		self.wndItemSelect = uiselectitem.SelectItemWindow()
		self.wndItemSelect.Hide()

	if app.ENABLE_BATTLE_PASS:
		def __BoardBattlePass(self):
			import ui_bpass
			self.wndBattlePass = ui_bpass.BattlePassWindow()
			self.wndBattlePass.Hide()

	if app.ENABLE_GEM_SYSTEM:
		def __MakeItemSelectWindowEx(self):
			self.wndItemSelectEx = uiselectitemEx.SelectItemWindowEx()
			self.wndItemSelectEx.Hide()

		def __MakeGemGui(self):
			self.wndGemG = uiGemShop.SelectGems()
			self.wndGemG.LoadWindow()
			self.wndGemG.Hide()

			self.wndGemM = uiGemShop.SelectGemsShop()
			self.wndGemM.LoadWindow()
			self.wndGemM.Hide()

	if app.ENABLE_CUBE_RENEWAL:
		def __MakeCubeRenewal(self):
			import uicuberenewal
			self.wndCubeRenewal = uicuberenewal.CubeRenewalWindows()
			self.wndCubeRenewal.Hide()

	# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

	def MakeInterface(self):
		ui.SetCrimsonGameControlsEnabled(True)
		self.__MakeTipBoard() # ENABLE_12ZI 미션 표시가 다른ui 밑에 오도록 위치 이동.
		self.__MakeMessengerWindow()
		self.__MakeGuildWindow()
		self.__MakeChatWindow()
		self.__MakeParty()
		self.__MakeWindows()
		self.__MakeSkillTreeWindow()
		self.__MakeGMPanelWindow()
		self.__MakeDialogs()

		if app.ENABLE_CUBE_RENEWAL:
			self.__MakeCubeRenewal()

		if app.ENABLE_GEM_SYSTEM:
			self.__MakeGemGui()

		if app.ENABLE_AURA_SYSTEM:
			self.wndAura.SetItemToolTip(self.tooltipItem)

		self.MakeGameNotification()

		if app.ENABLE_BIOLOG_SYSTEM:
			self.MakeBioWindow()

		if PVP_MATCHMAKING_ENABLED:
			self.MakePvPMatchmakingWindow()

		self.featureAvailabilityListener = ui.__mem_func__(self.OnFeatureAvailability)
		featureavailability.SetListener(self.featureAvailabilityListener)

		if app.ENABLE_MINI_GAME_CATCH_KING:
			self.__MakeCatchKingIconWindow()

		self.__MakeUICurtain()
		self.__MakeTaskBar()
		self.__MakeGameButtonWindow()
		self.__MakeHelpWindow()
		self.__MakeWebWindow()
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			self.__MakeAcceWindow()
		self.__MakeCubeWindow()
		self.__MakeCubeResultWindow()
		if app.ENABLE_SHOW_CHEST_DROP:
			self.dlgChestDrop.SetItemToolTip(self.tooltipItem)
		# ACCESSORY_REFINE_ADD_METIN_STONE
		self.__MakeItemSelectWindow()
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

		if app.ENABLE_MINI_GAME_OKEY:
			self.__MakeCardsInfoWindow()
			self.__MakeCardsWindow()
			self.__MakeCardsIconWindow()

		if app.ENABLE_GEM_SYSTEM:
			self.__MakeItemSelectWindowEx()

		if app.ENABLE_BATTLE_PASS:
			self.__BoardBattlePass()

		self.questButtonList = []
		self.__CreatePermanentTasksQuestButton()
		if self.wndDailyTasks:
			self.__CreateDailyTasksQuestButton()
		self.wndCharacter.SetQuestShortcuts([
			(btn.index, btn.name, localeInfo.GetQuestScrollNormalImageName(), btn.CallEvent)
			for btn in self.questButtonList[:PERSISTENT_QUEST_BUTTON_COUNT]
		])
		self.whisperButtonList = []
		self.whisperDialogDict = {}
		self.privateShopAdvertisementBoardDict = {}

		self.wndInventory.SetItemToolTip(self.tooltipItem)
		if self.wndTalisman:
			self.wndTalisman.SetItemToolTip(self.tooltipItem)
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.SetItemToolTip(self.tooltipItem)
			self.wndDragonSoulRefine.SetItemToolTip(self.tooltipItem)
		self.wndSafebox.SetItemToolTip(self.tooltipItem)
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			self.wndAcceCombine.SetItemToolTip(self.tooltipItem)
			self.wndAcceAbsorption.SetItemToolTip(self.tooltipItem)
		self.wndCube.SetItemToolTip(self.tooltipItem)
		self.wndCubeResult.SetItemToolTip(self.tooltipItem)

		# MT-818 [GF] 아이템 - 제조 성공된 아이템이 펫먹이가 되는 이슈
		self.wndCube.SetInven(self.wndInventory)
		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndCube.SetSpecialInven(self.wndSpecialInventory)

		# ITEM_MALL
		self.wndMall.SetItemToolTip(self.tooltipItem)
		# END_OF_ITEM_MALL

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			self.wndSkillBookCombination.SetInven(self.wndInventory)
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.wndSkillBookCombination.SetSpecialInven(self.wndSpecialInventory)

		self.wndCharacter.SetSkillToolTip(self.tooltipSkill)
		self.wndTaskBar.SetItemToolTip(self.tooltipItem)
		self.wndTaskBar.SetSkillToolTip(self.tooltipSkill)
		self.wndGuild.SetSkillToolTip(self.tooltipSkill)

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			self.wndChangeLook.SetItemToolTip(self.tooltipItem)

		# ACCESSORY_REFINE_ADD_METIN_STONE
		self.wndItemSelect.SetItemToolTip(self.tooltipItem)
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE
		if app.ENABLE_GEM_SYSTEM:
			self.wndItemSelectEx.SetItemToolTip(self.tooltipItem)

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndSpecialInventory.SetItemToolTip(self.tooltipItem)

		self.dlgShop.SetItemToolTip(self.tooltipItem)

		self.dlgExchange.SetItemToolTip(self.tooltipItem)
		self.privateShopBuilder.SetItemToolTip(self.tooltipItem)
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.privateShopBuilder.SetInven(self.wndInventory)
			self.dlgExchange.SetInven(self.wndInventory)
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.privateShopBuilder.SetSpecialInven(self.wndSpecialInventory)
				self.dlgExchange.SetSpecialInven(self.wndSpecialInventory)

		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.wndPetInfoWindow.SetItemToolTip(self.tooltipItem)
			self.wndPetInfoWindow.SetInven(self.wndInventory)
			self.wndPetInfoWindow.SetPetSkillToolTip(self.tooltipPetSkill)

		if app.ENABLE_BATTLE_PASS:
			self.wndBattlePass.SetItemToolTip(self.tooltipItem)

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			self.wndUpgradeSkill.SetSkillToolTip(self.tooltipSkill)	

		if app.ENABLE_PLAYER_RANKING:
			self.wndRankInfo.SetItemToolTip(self.tooltipItem)

		if app.ENABLE_SWITCHBOT_SYSTEM:
			self.wndSwitchbot.SetItemToolTip(self.tooltipItem)

		if app.ENABLE_SCROLL_ATLAS:
			self.__MakeScroolWindow()

		self.__InitWhisper()
		self.DRAGON_SOUL_IS_QUALIFIED = False

		#self.IntegrationEventBanner()

		if app.ENABLE_GEM_SYSTEM:
			self.wndGemM.SetItemToolTip(self.tooltipItem)

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting.SetSkillToolTip(self.tooltipSkill)
			self.wndAutoHunting.SetItemToolTip(self.tooltipItem)

		self.systemNotifications = systemnotifications.NotificationManager(self)
		self.MakeCountdownHUD()

	def MakeCountdownHUD(self):
		if not (app.ENABLE_DUNGEON_INFO or app.ENABLE_BIOLOG_SYSTEM):
			return
		self.wndCountdownHUD = uicountdownhud.CountdownWindow(self)
		for window in (getattr(self, "wndBio", None), getattr(self, "wndTeleportAtlas", None)):
			if window is None:
				continue
			board = getattr(window, "board", window)
			title = getattr(board, "titleBar", None)
			if title:
				self.countdownLaunchers.append(uicountdownhud.CreateLauncher(
					title, ui.__mem_func__(self.OpenCountdownHUD)))

	def OpenCountdownHUD(self):
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Open()

	def OpenMissionBooks(self):
		if self.wndMissionBooks is None:
			from uimissionbooks import MissionBookWindow
			self.wndMissionBooks = MissionBookWindow(self)
		self.wndMissionBooks.Open()

	def ToggleMissionBooks(self):
		if self.wndMissionBooks and self.wndMissionBooks.IsShow():
			self.wndMissionBooks.Close()
		else:
			self.OpenMissionBooks()

	def MissionBookState(self, book, mission, p1, p2, p3, ready):
		if self.wndMissionBooks is None:
			from uimissionbooks import MissionBookWindow
			self.wndMissionBooks = MissionBookWindow(self)
		self.wndMissionBooks.ReceiveState(book, mission, p1, p2, p3, ready)

	def ToggleCountdownHUD(self):
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Toggle()

	def UpdateCountdownHUD(self):
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Tick()
		if getattr(self, "systemNotifications", None):
			self.systemNotifications.Tick()

	def IsCountdownCategoryEnabled(self, category):
		manager = getattr(self, "systemNotifications", None)
		return manager.IsHUDEnabled(category) if manager else True

	def OpenSystemNotificationSettings(self):
		if getattr(self, "systemNotifications", None) and self.dlgSystem:
			window = self.dlgSystem.OpenGameOptionDialog()
			if window:
				window.OpenPage("notifications")

	def ArrangeMessageDock(self):
		self.__ArrangeWhisperButton()

	def PushBiologReadyNotification(self, title, message, iconVnum=0, signature=None):
		if getattr(self, "systemNotifications", None):
			return self.systemNotifications.AddBiolog(title, message, iconVnum, signature)
		return False

	def PushSwitchbotSystemNotification(self, message):
		if getattr(self, "systemNotifications", None):
			return self.systemNotifications.AddSwitchbot(message)
		return False

	def RefreshCountdownHUDSelection(self, reveal=False):
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.RefreshSelection(reveal)

	def ResetCountdownReminderState(self):
		uicountdownhud.ResetReminderState()

	def PushDungeonCountdownNotification(self, title, message, bossVnum, cooldownEnd=None):
		if getattr(self, "systemNotifications", None):
			return self.systemNotifications.AddDungeon(title, message, bossVnum, cooldownEnd)
		return False

	def MakeHyperlinkTooltip(self, hyperlink):
		if hyperlink.startswith("guildinvite:"):
			import guildv2model
			identifier = guildv2model.invitation_link_id(hyperlink)
			if identifier and self.wndGuild:
				self.wndGuild.OpenInvitation(identifier)
			return
		if hyperlink.startswith(("chatweb:", "chatplayer:")):
			import compactchatmodel
			kind, target = compactchatmodel.link_target(hyperlink)
			if target and kind == "chatweb":
				app.ShellExecute(target)
			elif target and target.casefold() != player.GetName().casefold():
				self.OpenWhisperDialog(target)
			return
		tokens = hyperlink.split(":")
		if tokens and len(tokens):
			type = tokens[0]
			if "item" == type:
				self.hyperlinkItemTooltip.SetHyperlinkItem(tokens)
			elif app.ENABLE_WIKI and type == "wiki":
				self.MakeWiki()
				self.wndWiki.RunHistoryArgument(str(tokens[1]))
				self.wndWiki.Open()
			if "msg" == type:
				self.OpenWhisperDialog(str(tokens[1]))
			if app.ENABLE_GROWTH_PET_SYSTEM and "petitem" == type:
				self.hyperlinkItemTooltip.SetHyperlinkPetItem(tokens)

	## Make Windows & Dialogs
	################################

	def Close(self):
		ui.SetCrimsonGameControlsEnabled(False)
		if self.featureAvailabilityListener:
			featureavailability.ClearListener(self.featureAvailabilityListener)
			self.featureAvailabilityListener = None
		if self.wndFeatureComingSoon:
			self.wndFeatureComingSoon.Destroy()
			self.wndFeatureComingSoon = None
		if self.petAlbumNotice:
			self.petAlbumNotice.Destroy()
			self.petAlbumNotice = None
		if getattr(self, "wndMissionBooks", None):
			self.wndMissionBooks.Destroy()
			self.wndMissionBooks = None
		self._metadataInventoryDirty = False
		self._metadataRarityDirty = False
		if getattr(self, "systemNotifications", None):
			self.systemNotifications.Destroy()
			self.systemNotifications = None
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Destroy()
			self.wndCountdownHUD = None
		for button in getattr(self, "countdownLaunchers", ()):
			button.SetEvent(None)
			button.Hide()
		self.countdownLaunchers = []
		self.HideAllQuestButton()
		self.unifiedMessengerRouter.Destroy()
		if app.ENABLE_LOADING_PERFORMANCE:
			if self.wndWarpShower:
				self.wndWarpShower.Destroy()
				del self.wndWarpShower

		if app.ENABLE_WHEEL_OF_FORTUNE:
			if self.wndWheelofFortune:
				self.wndWheelofFortune.Hide()
				self.wndWheelofFortune.Destroy()
				self.wndWheelofFortune=None

		if app.ENABLE_REWARD_SYSTEM:
			if self.wndReward:
				self.wndReward.Hide()
				self.wndReward.Destroy()
				self.wndReward = None

		if app.ENABLE_EXCHANGE_LOG:
			if self.wndExchangeLog:
				self.wndExchangeLog.Close()
				self.wndExchangeLog.Destroy()
				self.wndExchangeLog = None

		if app.ENABLE_DUNGEON_INFO:
			if self.wndDungeonTrack:
				self.wndDungeonTrack.Close()
				self.wndDungeonTrack.Destroy()
				self.wndDungeonTrack = None
			if self.wndDungeonManager:
				self.wndDungeonManager.Destroy()
				self.wndDungeonManager = None

		if app.ENABLE_BOSS_TRACK:
			if self.wndBossTrack:
				self.wndBossTrack.Destroy()
				self.wndBossTrack.Hide()
				self.wndBossTrack = None

		if self.dlgWhisperWithoutTarget:
			self.dlgWhisperWithoutTarget.Destroy()
			del self.dlgWhisperWithoutTarget

		if "QuestCurtain" in uiQuest.QuestDialog.__dict__:
			uiQuest.QuestDialog.QuestCurtain.Close()

		if self.wndQuestWindow:
			for key, eachQuestWindow in list(self.wndQuestWindow.items()):
				eachQuestWindow.nextCurtainMode = -1
				eachQuestWindow.Hide()
				eachQuestWindow.CloseSelf()
				eachQuestWindow = None
		self.wndQuestWindow = {}

		if self.wndChat:
			self.wndChat.Destroy()

		if self.quickBuffSystem:
			self.quickBuffSystem.Destroy()
			self.quickBuffSystem = None

		if self.dropTrackerSystem:
			self.dropTrackerSystem.Destroy()
			self.dropTrackerSystem = None

		if self.wndTaskBar:
			self.wndTaskBar.Destroy()

		if app.ENABLE_BATTLE_PASS:
			if self.wndBattlePass:
				self.wndBattlePass.Hide()
				self.wndBattlePass.Destroy()
				del self.wndBattlePass

		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.Destroy()

		if self.wndTalisman:
			self.wndTalisman.Destroy()
			self.wndTalisman = None
		if self.wndQuickEquip:
			self.wndQuickEquip.Destroy()
			self.wndQuickEquip = None
		self.talismanSetAvailable = False

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyTaskBar:
				self.wndExpandedMoneyTaskBar.Destroy()

		if self.wndEnergyBar:
			self.wndEnergyBar.Destroy()

		if app.ENABLE_WIKI:
			if self.wndWiki:
				self.wndWiki.Close()
				self.wndWiki.Destroy()
				self.wndWiki=None

		if self.wndPermanentTasks:
			self.wndPermanentTasks.Close()
			self.wndPermanentTasks.Destroy()
			self.wndPermanentTasks = None
		self.permanentTasksAvailable = False
		self.permanentTasksGeneration = 0
		self.permanentTasksSnapshot = None
		self.permanentTasksHunts = {}
		self.permanentTasksSnapshotPending = False
		self.permanentTasksSubmitPending = False

		if self.wndDailyTasks:
			self.wndDailyTasks.Close()
			self.wndDailyTasks.Destroy()
			self.wndDailyTasks = None

		if self.wndCharacter:
			if app.ENABLE_DETAILS_UI:
				self.wndCharacter.Hide()
			self.wndCharacter.Destroy()

		if self.wndCostumeInventory:
			self.wndCostumeInventory.Hide()
			self.wndCostumeInventory.Destroy()

		if self.wndInventory:
			self.wndInventory.Hide()
			self.wndInventory.Destroy()

		if self.wndTargetedRarity:
			self.wndTargetedRarity.Close()
		if self.wndRarity:
			self.wndRarity.Close()
			self.wndRarity.Destroy()
			self.wndRarity = None
		if self.wndTargetedRarity:
			self.wndTargetedRarity.Destroy()
			self.wndTargetedRarity = None

		if self.wndResonance:
			self.wndResonance.Close()
			self.wndResonance.Destroy()
			self.wndResonance = None

		if self.wndDragonSoul:
			self.wndDragonSoul.Destroy()

		if self.wndDragonSoulRefine:
			self.wndDragonSoulRefine.Destroy()

		if self.dlgExchange:
			self.dlgExchange.Destroy()

		if self.dlgPointReset:
			self.dlgPointReset.Destroy()

		if self.dlgShop:
			self.dlgShop.Destroy()

		if self.dlgRestart:
			self.dlgRestart.Destroy()

		if self.dlgSystem:
			self.dlgSystem.Destroy()

		if self.dlgPassword:
			self.dlgPassword.Destroy()

		if self.wndSkillTree:
			self.wndSkillTree.Destroy()
			self.wndSkillTree = None

		if self.wndMountSystem:
			self.wndMountSystem.Destroy()
			self.wndMountSystem = None

		if self.wndGMPanel:
			self.wndGMPanel.Destroy()
			self.wndGMPanel = None

		if self.wndCustomPorts:
			self.wndCustomPorts.Destroy()
			self.wndCustomPorts = None

		if self.afkSystem:
			self.afkSystem.Destroy()
			self.afkSystem = None

		if self.wndMiniMap:
			self.wndMiniMap.Destroy()

		if self.wndSafebox:
			self.wndSafebox.Destroy()

		if self.wndWeb:
			self.wndWeb.Destroy()
			self.wndWeb = None

		if self.wndMall:
			self.wndMall.Destroy()

		if self.wndParty:
			self.wndParty.Destroy()

		if self.wndHelp:
			self.wndHelp.Destroy()

		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			if self.wndAcceCombine:
				self.wndAcceCombine.Destroy()

			if self.wndAcceAbsorption:
				self.wndAcceAbsorption.Destroy()

		if self.wndCube:
			self.wndCube.Destroy()

		if self.wndCubeResult:
			self.wndCubeResult.Destroy()

		if self.wndMessenger:
			self.wndMessenger.Destroy()

		if self.wndGuild:
			self.wndGuild.Destroy()

		if self.privateShopBuilder:
			self.privateShopBuilder.Destroy()

		if self.dlgRefineNew:
			self.dlgRefineNew.Destroy()

		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			if self.dlgRefineElement:
				self.dlgRefineElement.Destroy()

			if self.dlgRefineElementChange:
				self.dlgRefineElementChange.Destroy()

		if self.wndGuildBuilding:
			self.wndGuildBuilding.Destroy()

		if self.wndGameButton:
			self.wndGameButton.Destroy()

		# ITEM_MALL
		if self.mallPageDlg:
			self.mallPageDlg.Destroy()
		# END_OF_ITEM_MALL

		# ACCESSORY_REFINE_ADD_METIN_STONE
		if self.wndItemSelect:
			self.wndItemSelect.Destroy()
		# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			self.wndSkillBookCombination.Destroy()
			del self.wndSkillBookCombination

		if app.ENABLE_TELEPORT_WINDOW:
			if self.wndTeleportPanel:
				self.wndTeleportPanel.Destroy()
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.Destroy()

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if self.wndChangeLook:
				del self.wndChangeLook

		if app.ENABLE_MINI_GAME_OKEY:
			if self.wndCardsInfo:
				self.wndCardsInfo.Destroy()

			if self.wndCards:
				self.wndCards.Destroy()

			if self.wndCardsIcon:
				self.wndCardsIcon.Destroy()

		if app.ENABLE_GEM_SYSTEM:
			if self.wndItemSelectEx:
				self.wndItemSelectEx.Destroy()

		if app.ENABLE_GEM_SYSTEM:
			if self.wndGemG:
				self.wndGemG.Destroy()
				del self.wndGemG

			if self.wndGemM:
				self.wndGemM.Destroy()
				del self.wndGemM

		if app.ENABLE_CUBE_RENEWAL:
			if self.wndCubeRenewal:
				self.wndCubeRenewal.Destroy()
				self.wndCubeRenewal.Close()

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if self.wndSpecialInventory:
				self.wndSpecialInventory.Hide() ## Fix Ghost Window
				self.wndSpecialInventory.Destroy()

		if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			if self.wndCaptcha:
				self.wndCaptcha.Destroy()

		if app.ENABLE_AURA_SYSTEM:
			if self.wndAura:
				self.wndAura.Destroy()
				del self.wndAura

		if self.wndGameNotification:
			self.wndGameNotification.Destroy()
			del self.wndGameNotification

		if app.ENABLE_BIOLOG_SYSTEM:
			if self.wndBio:
				self.wndBio.Close()
				self.wndBio.Destroy()
				del self.wndBio

		if PVP_MATCHMAKING_ENABLED:
			if self.wndPvPMatchmaking:
				self.wndPvPMatchmaking.Destroy()
				del self.wndPvPMatchmaking

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			if self.wndUpgradeSkill:
				self.wndUpgradeSkill.Destroy()

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.Destroy()

		if app.ENABLE_SCROLL_ATLAS:
			if self.wndScrollWarp:
				self.wndScrollWarp.Hide()
				self.wndScrollWarp.Destroy()
				del self.wndScrollWarp

		if app.ENABLE_SHOW_CHEST_DROP:
			if self.dlgChestDrop:
				self.dlgChestDrop.Destroy()

		if app.ENABLE_EVENT_MANAGER:
			if self.wndEventManager:
				self.wndEventManager.Hide()
				self.wndEventManager.Destroy()
				self.wndEventManager = None

			if self.wndEventIcon:
				self.wndEventIcon.Hide()
				self.wndEventIcon.Destroy()
				self.wndEventIcon = None

		if app.ENABLE_MAINTENANCE_SYSTEM:
			if self.wndMaintenance:
				self.wndMaintenance.Hide()
				self.wndMaintenance.Destroy()

		if app.ENABLE_PLAYER_RANKING:
			if self.wndRankInfo:
				self.wndRankInfo.Hide()
				self.wndRankInfo.Destroy()
				del self.wndRankInfo

		if app.ENABLE_SHOP_SEARCH:
			if self.wndShopSearch:
				self.wndShopSearch.Hide()
				self.wndShopSearch.Destroy()

		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.Close()
				self.wndVirtualMarket.Destroy()
				self.wndVirtualMarket = None

		if app.ENABLE_SWITCHBOT_SYSTEM:
			if self.wndSwitchbot:
				self.wndSwitchbot.Destroy()

		if app.ENABLE_MINI_GAME_CATCH_KING:
			if self.wndCatchKingGame:
				self.wndCatchKingGame.Destroy()
				del self.wndCatchKingGame
			if self.wndCatchKingIcon:
				self.wndCatchKingIcon.Destroy()
				del self.wndCatchKingIcon

		if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
			if self.wndGuildDragonLairRanking:
				self.wndGuildDragonLairRanking.Destory()

		if app.ENABLE_FISHING_GAME:
			if self.wndFishingGame:
				self.wndFishingGame.Destroy()
				del self.wndFishingGame

		if app.ENABLE_ATTR_6TH_7TH:
			if self.wndAttr67Add:
				self.wndAttr67Add.Destroy()
				del self.wndAttr67Add

		if app.ENABLE_RANKING_SYSTEM:
			if self.wndRankingBoardWindow:
				self.wndRankingBoardWindow.Destroy()

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			if self.wndAutoHunting:
				self.wndAutoHunting.Destroy()

		self.wndChatLog.Destroy()
		for btn in self.questButtonList:
			btn.Hide()
			btn.ForceHideToolTip()
			btn.SetEvent(0)
		for btn in self.whisperButtonList:
			btn.SetEvent(0)
		for dlg in self.whisperDialogDict.values():
			dlg.Destroy()
		for brd in self.guildScoreBoardDict.values():
			brd.Destroy()
		for dlg in self.equipmentDialogDict.values():
			dlg.Destroy()

		# ITEM_MALL
		del self.mallPageDlg
		# END_OF_ITEM_MALL

		del self.wndGuild
		del self.wndMessenger
		del self.wndUICurtain
		del self.wndChat
		del self.wndTaskBar
		if self.wndExpandedTaskBar:
			del self.wndExpandedTaskBar

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyTaskBar:
				del self.wndExpandedMoneyTaskBar

		if app.ENABLE_CUBE_RENEWAL:
			del self.wndCubeRenewal

		if app.ENABLE_SKILL_SELECT_GUI:
			del self.wndSkillSelect
		del self.wndEnergyBar
		del self.wndCharacter
		if self.wndCostumeInventory:
			del self.wndCostumeInventory
		del self.wndInventory
		if self.wndDragonSoul:
			del self.wndDragonSoul
		if self.wndDragonSoulRefine:
			del self.wndDragonSoulRefine

		if app.ENABLE_RANKING_SYSTEM:
			if self.wndRankingBoardWindow:
				del self.wndRankingBoardWindow

		if app.ENABLE_ITEMSHOP:
			if self.wndItemShop:
				self.wndItemShop.Hide()
				self.wndItemShop.Destroy()
				self.wndItemShop = None

		if app.ENABLE_OFFLINE_SHOP:
			if self.wndOfflineShopBuilder:
				self.wndOfflineShopBuilder.Hide()
				self.wndOfflineShopBuilder.Destroy()

			if self.wndSellHistory:
				self.wndSellHistory.Hide()
				self.wndSellHistory.Destroy()

		del self.dlgExchange
		del self.dlgPointReset
		del self.dlgShop
		del self.dlgRestart
		del self.dlgSystem
		del self.dlgPassword
		del self.hyperlinkItemTooltip
		del self.tooltipItem
		del self.tooltipSkill
		del self.wndMiniMap
		del self.wndSafebox
		del self.wndMall
		del self.wndParty
		del self.wndHelp
		if app.ENABLE_ACCE_COSTUME_SYSTEM:
			del self.wndAcceCombine
			del self.wndAcceAbsorption
		del self.wndCube
		del self.wndCubeResult
		del self.privateShopBuilder
		del self.inputDialog
		del self.wndChatLog
		del self.dlgRefineNew
		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			del self.dlgRefineElement
			del self.dlgRefineElementChange
		del self.wndGuildBuilding
		del self.wndGameButton
		if self.noticeBoard:
			self.noticeBoard.Destroy()
			self.noticeBoard = None
		del self.tipBoard
		del self.bigBoard
		del self.wndItemSelect

		if app.ENABLE_TELEPORT_WINDOW:
			del self.wndTeleportPanel
			del self.wndTeleportAtlas

		if self.wndMiniGame:
			self.wndMiniGame.Destroy()
			del self.wndMiniGame

		if app.ENABLE_SWITCHBOT_SYSTEM:
			del self.wndSwitchbot

		if app.ENABLE_MINI_GAME_OKEY:
			del self.wndCardsInfo
			del self.wndCards
			del self.wndCardsIcon

		if app.ENABLE_GEM_SYSTEM:
			del self.wndItemSelectEx

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if self.wndSpecialInventory:
				del self.wndSpecialInventory

		if app.ENABLE_12ZI:
			del self.missionBoard

		if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
			if self.wndCaptcha:
				del self.wndCaptcha

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			if self.wndRenderTargetView:
				self.wndRenderTargetView.Destroy()
				del self.wndRenderTargetView

		if app.ENABLE_DUNGEON_TIME_WINDOW:
			if self.wndDungeonTime:
				self.wndDungeonTime.Destroy()
				del self.wndDungeonTime

		if app.ENABLE_OFFLINE_SHOP:
			del self.wndOfflineShopBuilder
			del self.wndSellHistory

		if app.ENABLE_SHOP_SEARCH:
			del self.wndShopSearch

		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			del self.wndVirtualMarket

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if self.wndPetInfoWindow:
				del self.wndPetInfoWindow
			self.wndPetInfoWindow = None
			del self.tooltipPetSkill

		if app.ENABLE_MAINTENANCE_SYSTEM:
			del self.wndMaintenance

		if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
			del self.wndUpgradeSkill

		if app.ENABLE_SHOW_CHEST_DROP:
			if self.dlgChestDrop:
				del self.dlgChestDrop

		if CAPTCHA_WINDOW_ENABLED:
			if self.wndCaptchaNew:
				self.wndCaptchaNew.Destroy()
			del self.wndCaptchaNew

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			if self.wndAutoHunting:
				del self.wndAutoHunting

		if app.ENABLE_DESTROY_ITEM_RESTORE:
			if self.wndSaveItem:
				self.wndSaveItem.Hide()
				self.wndSaveItem.Destroy()
				self.wndSaveItem=None

		if app.ENABLE_BUFF_SYSTEM:
			if self.wndSupportPG:
				self.wndSupportPG.Close()
				self.wndSupportPG.Destroy()
				del self.wndSupportPG

		if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
			del self.wndGuildDragonLairRanking

		self.questButtonList = []
		self.whisperButtonList = []
		self.whisperDialogDict = {}
		self.privateShopAdvertisementBoardDict = {}
		self.guildScoreBoardDict = {}
		self.equipmentDialogDict = {}

		uiChat.DestroyChatInputSetWindow()

		if app.ENABLE_KINGDOMS_WAR:
			if self.wndKingdomsWar:
				self.wndKingdomsWar.Destroy()
			
			del self.wndKingdomsWar

	## Skill
	def OnUseSkill(self, slotIndex, coolTime):
		self.wndCharacter.OnUseSkill(slotIndex, coolTime)
		self.wndTaskBar.OnUseSkill(slotIndex, coolTime)
		self.wndGuild.OnUseSkill(slotIndex, coolTime)
		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting.OnUseSkill(slotIndex, coolTime)

	def OnActivateSkill(self, slotIndex):
		self.wndCharacter.OnActivateSkill(slotIndex)
		self.wndTaskBar.OnActivateSkill(slotIndex)
		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting.OnActivateSkill()

	def OnDeactivateSkill(self, slotIndex):
		self.wndCharacter.OnDeactivateSkill(slotIndex)
		self.wndTaskBar.OnDeactivateSkill(slotIndex)
		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			self.wndAutoHunting.OnDeactivateSkill(slotIndex)

	def OnChangeCurrentSkill(self, skillSlotNumber):
		self.wndTaskBar.OnChangeCurrentSkill(skillSlotNumber)

	if app.ENABLE_SKILL_COOLTIME_UPDATE:
		def SkillClearCoolTime(self, slotIndex):
			self.wndCharacter.SkillClearCoolTime(slotIndex)
			self.wndTaskBar.SkillClearCoolTime(slotIndex)

	def SelectMouseButtonEvent(self, dir, event):
		self.wndTaskBar.SelectMouseButtonEvent(dir, event)

	## Refresh
	def RefreshAlignment(self):
		self.wndCharacter.RefreshAlignment()

	def RefreshStatus(self):
		self.wndTaskBar.RefreshStatus()
		self.wndCharacter.RefreshStatus()
		self.wndInventory.RefreshStatus()
		if self.wndEnergyBar:
			self.wndEnergyBar.RefreshStatus()
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.RefreshStatus()
		if app.ENABLE_GROWTH_PET_SYSTEM:
			self.wndPetInfoWindow.RefreshStatus()

	def RefreshStamina(self):
		self.wndTaskBar.RefreshStamina()

	def RefreshSkill(self):
		self.wndCharacter.RefreshSkill()
		self.wndTaskBar.RefreshSkill()

	def RefreshInventory(self):
		self._metadataInventoryDirty = False
		if (app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK and self.wndUpgradeSkill
				and self.wndUpgradeSkill.IsShow()):
			self.wndUpgradeSkill.RefreshItemCounts()
		self.wndTaskBar.RefreshQuickSlot()
		self.wndInventory.RefreshItemSlot()
		if self.wndQuickEquip and self.wndQuickEquip.IsShow():
			self.wndQuickEquip.Refresh()
		if self.wndMountSystem:
			self.wndMountSystem.RefreshEquipment()
		if self.wndTalisman and self.wndTalisman.IsShow():
			self.wndTalisman.Refresh()
		if self.wndCostumeInventory and \
				self.wndCostumeInventory.IsShow():
			self.wndCostumeInventory.RefreshItemSlot()
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.RefreshItemSlot()
		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			self.wndSpecialInventory.RefreshItemSlot()
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			if player.GetChangeLookWindowOpen() == 1:
				self.wndChangeLook.RefreshChangeLookWindow()

		if app.ENABLE_AURA_SYSTEM:
			if player.IsAuraRefineWindowOpen():
				if self.wndAura and self.wndAura.IsShow():
					self.wndAura.RefreshAuraWindow()

	def SetVirtualMarketDraftSlot(self, slotIndex, locked):
		if self.wndInventory:
			self.wndInventory.SetVirtualMarketDraftSlot(slotIndex, locked)

	def RefreshCharacter(self): ## Character 페이지의 얼굴, Inventory 페이지의 전신 그림 등의 Refresh
		self.wndCharacter.RefreshCharacter()
		self.wndTaskBar.RefreshQuickSlot()

	def RefreshQuest(self):
		self.wndCharacter.RefreshQuest()

	def RefreshSafebox(self):
		self.wndSafebox.RefreshSafebox()

	# ITEM_MALL
	def RefreshMall(self):
		self.wndMall.RefreshMall()

	def OpenItemMall(self):
		if not self.mallPageDlg:
			self.mallPageDlg = uiShop.MallPageDialog()

		self.mallPageDlg.Open()
	# END_OF_ITEM_MALL

	if app.ENABLE_CHATTING_WINDOW_RENEWAL:
		def RefreshWhisperMessengerButtons(self):
			if self.whisperDialogDict:
				for dlg in self.whisperDialogDict.values():
					dlg.RefreshMessengerButtons()

	def RefreshMessenger(self):
		self.wndMessenger.RefreshMessenger()

	def RefreshGuildInfoPage(self):
		self.wndGuild.RefreshGuildInfoPage()

	def RefreshGuildBoardPage(self):
		self.wndGuild.RefreshGuildBoardPage()

	def RefreshGuildMemberPage(self):
		self.wndGuild.RefreshGuildMemberPage()

	def RefreshGuildMemberPageGradeComboBox(self):
		self.wndGuild.RefreshGuildMemberPageGradeComboBox()

	def RefreshGuildSkillPage(self):
		self.wndGuild.RefreshGuildSkillPage()

	def RefreshGuildGradePage(self):
		self.wndGuild.RefreshGuildGradePage()

	def DeleteGuild(self):
		self.wndMessenger.ClearGuildMember()
		self.wndGuild.DeleteGuild()

	def OnBlockMode(self, mode):
		self.dlgSystem.OnBlockMode(mode)

	## Calling Functions
	# PointReset
	def OpenPointResetDialog(self):
		self.dlgPointReset.Show()
		self.dlgPointReset.SetTop()

	def ClosePointResetDialog(self):
		self.dlgPointReset.Close()

	# Shop
	if app.ENABLE_COMBAT_ZONE:
		def OpenShopDialog(self, vid, points, curLimit, maxLimit):
			self.wndInventory.Show()
			self.wndInventory.SetTop()
			self.dlgShop.Open(vid, points, curLimit, maxLimit)
			self.dlgShop.SetTop()
	else:
		def OpenShopDialog(self, vid):
			self.wndInventory.Show()
			self.wndInventory.SetTop()
			self.dlgShop.Open(vid)
			self.dlgShop.SetTop()

	def CloseShopDialog(self):
		self.dlgShop.Close()

	def CloseTransactionalWindowsForExit(self):
		if self.dlgShop:
			self.dlgShop.Close()

		if app.ENABLE_CUBE_RENEWAL and self.wndCubeRenewal:
			self.wndCubeRenewal.Close()

		net.SendExchangeExitPacket()

	def RefreshShopDialog(self):
		self.dlgShop.Refresh()

	## Quest
	def OpenCharacterWindowQuestPage(self):
		self.wndCharacter.Show()
		self.wndCharacter.SetState("QUEST")

	def OpenQuestWindow(self, skin, idx):
		wnds = ()

		q = uiQuest.QuestDialog(skin, idx)
		q.SetWindowName("QuestWindow" + str(idx))
		q.Show()
		if skin:
			q.Lock()
			wnds = self.__HideWindows()

			# UNKNOWN_UPDATE
			q.AddOnDoneEvent(lambda tmp_self, args=wnds: self.__ShowWindows(args))
			# END_OF_UNKNOWN_UPDATE

		if skin:
			q.AddOnCloseEvent(q.Unlock)
		q.AddOnCloseEvent(lambda key = self.wndQuestWindowNewKey:ui.__mem_func__(self.RemoveQuestDialog)(key))
		self.wndQuestWindow[self.wndQuestWindowNewKey] = q

		self.wndQuestWindowNewKey = self.wndQuestWindowNewKey + 1

		# END_OF_UNKNOWN_UPDATE

	def RemoveQuestDialog(self, key):
		del self.wndQuestWindow[key]
		# A command-chat handoff can close the last quest without DoneEvent.
		# Mode 0 would leave the cinema bars on screen until the next login.
		if not self.wndQuestWindow and "QuestCurtain" in uiQuest.QuestDialog.__dict__:
			curtain = uiQuest.QuestDialog.QuestCurtain
			if curtain.CurtainMode == 0:
				curtain.CurtainMode = -1

	## Exchange
	def StartExchange(self):
		self.dlgExchange.OpenDialog()
		self.dlgExchange.Refresh()

	def EndExchange(self):
		self.dlgExchange.CloseDialog()

	def RefreshExchange(self):
		self.dlgExchange.Refresh()

	if app.WJ_ENABLE_TRADABLE_ICON:
		def AddExchangeItemSlotIndex(self, idx):
			self.dlgExchange.AddExchangeItemSlotIndex(idx)

	## Party
	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def AddPartyMember(self, pid, name, mapIdx, channel):
			self.wndParty.AddPartyMember(pid, name, mapIdx, channel)
			self.__ArrangeQuestButton()
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def AddPartyMember(self, pid, name, mapIdx):
			self.wndParty.AddPartyMember(pid, name, mapIdx)
			self.__ArrangeQuestButton()
	else:
		def AddPartyMember(self, pid, name):
			self.wndParty.AddPartyMember(pid, name)
			self.__ArrangeQuestButton()

	def UpdatePartyMemberInfo(self, pid):
		self.wndParty.UpdatePartyMemberInfo(pid)

	def RemovePartyMember(self, pid):
		self.wndParty.RemovePartyMember(pid)

		##!! 20061026.levites.퀘스트_위치_보정
		self.__ArrangeQuestButton()

	if app.WJ_SHOW_PARTY_ON_MINIMAP and app.ENABLE_PARTY_CHANNEL_FIX:
		def LinkPartyMember(self, pid, vid, mapIdx, channel):
			self.wndParty.LinkPartyMember(pid, vid, mapIdx, channel)
	elif app.WJ_SHOW_PARTY_ON_MINIMAP:
		def LinkPartyMember(self, pid, vid, mapIdx):
			self.wndParty.LinkPartyMember(pid, vid, mapIdx)
	else:
		def LinkPartyMember(self, pid, vid):
			self.wndParty.LinkPartyMember(pid, vid)

	def UnlinkPartyMember(self, pid):
		self.wndParty.UnlinkPartyMember(pid)

	def UnlinkAllPartyMember(self):
		self.wndParty.UnlinkAllPartyMember()

	def ExitParty(self):
		self.wndParty.ExitParty()

		##!! 20061026.levites.퀘스트_위치_보정
		self.__ArrangeQuestButton()

	def PartyHealReady(self):
		self.wndParty.PartyHealReady()

	def ChangePartyParameter(self, distributionMode):
		self.wndParty.ChangePartyParameter(distributionMode)

	## Safebox
	def AskSafeboxPassword(self):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			return

		if self.wndSafebox.IsShow():
			return

		# SAFEBOX_PASSWORD
		self.dlgPassword.SetTitle(localeInfo.PASSWORD_TITLE)
		self.dlgPassword.SetSendMessage("/safebox_password ")
		# END_OF_SAFEBOX_PASSWORD

		self.dlgPassword.ShowDialog()

	def OpenSafeboxWindow(self, size):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndSpecialInventory.ShowSafeboxWindow(size)
			return

		self.dlgPassword.CloseDialog()
		self.wndSafebox.ShowWindow(size)

	def RefreshSafeboxMoney(self):
		self.wndSafebox.RefreshSafeboxMoney()

	def CommandCloseSafebox(self):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndSpecialInventory.CommandCloseSafebox()
			return

		self.wndSafebox.CommandCloseSafebox()

	## HilightSlot Change
	def DeactivateSlot(self, slotindex, type):
		self.wndInventory.DeactivateSlot(slotindex, type)

	## HilightSlot Change
	def ActivateSlot(self, slotindex, type):
		self.wndInventory.ActivateSlot(slotindex, type)

	if app.ENABLE_CHANGE_LOOK_SYSTEM:
		def ChangeWindowOpen(self, type):
			if shop.GetNameDialogOpen():
				return

			if self.dlgRefineNew and self.dlgRefineNew.IsShow():
				return

			if app.ENABLE_REFINE_ELEMENT_SYSTEM and self.IsRefineElementDialogOpen():
				return

			if self.wndChangeLook:
				self.wndChangeLook.Open(type)

	if app.ENABLE_GEM_SYSTEM:
		def OpenGuiGem(self):
			self.wndGemG.Open()

		def GemCheck(self):
			self.wndGemG.SucceedGem()

		def OpenGuiGemMarket(self):
			self.wndGemM.Open()

		def GemMarketItems(self, vnums, gem, count):
			self.wndGemM.Information(vnums, gem, count)
			self.wndGemM.LoadInformation()

		def GemMarketSlotsDesblock(self, slot0, slot1, slot2, slot3, slot4, slot5):
			self.wndGemM.SlotsDesblock(slot0, slot1, slot2, slot3, slot4, slot5)

		def GemMarketClear(self):
			self.wndGemM.Clear()

		def GemTime(self,time):
			self.wndGemM.Time(time)

	if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
		def OpenSkillbookCombinationDialog(self):
			if self.wndSkillBookCombination.IsShow():
				return

			if self.privateShopBuilder.IsShow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.COMB_NOTICE_NOT_OPEN)
				return

			self.wndSkillBookCombination.Open()
			self.wndSkillBookCombination.Show()

			if not self.wndInventory.IsShow():
				self.wndInventory.Show()

	# ITEM_MALL
	def AskMallPassword(self):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			return

		if self.wndMall.IsShow():
			return

		self.dlgPassword.SetTitle(localeInfo.MALL_PASSWORD_TITLE)
		self.dlgPassword.SetSendMessage("/mall_password ")
		self.dlgPassword.ShowDialog()

	def OpenMallWindow(self, size):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndSpecialInventory.ShowMallWindow(size)
			return
		self.dlgPassword.CloseDialog()
		self.wndMall.ShowWindow(size)

	def CommandCloseMall(self):
		if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
			self.wndSpecialInventory.CommandCloseMall()
			return

		self.wndMall.CommandCloseMall()
	# END_OF_ITEM_MALL

	## Guild
	def OnStartGuildWar(self, guildSelf, guildOpp):
		self.wndGuild.OnStartGuildWar(guildSelf, guildOpp)

		guildWarScoreBoard = uiGuild.GuildWarScoreBoard()
		guildWarScoreBoard.Open(guildSelf, guildOpp)
		guildWarScoreBoard.Show()
		self.guildScoreBoardDict[uiGuild.GetGVGKey(guildSelf, guildOpp)] = guildWarScoreBoard

	def OnEndGuildWar(self, guildSelf, guildOpp):
		self.wndGuild.OnEndGuildWar(guildSelf, guildOpp)

		key = uiGuild.GetGVGKey(guildSelf, guildOpp)

		if not key in self.guildScoreBoardDict:
			return

		self.guildScoreBoardDict[key].Destroy()
		del self.guildScoreBoardDict[key]

	# GUILDWAR_MEMBER_COUNT
	def UpdateMemberCount(self, gulidID1, memberCount1, guildID2, memberCount2):
		key = uiGuild.GetGVGKey(gulidID1, guildID2)

		if not key in self.guildScoreBoardDict:
			return

		self.guildScoreBoardDict[key].UpdateMemberCount(gulidID1, memberCount1, guildID2, memberCount2)
	# END_OF_GUILDWAR_MEMBER_COUNT

	def OnRecvGuildWarPoint(self, gainGuildID, opponentGuildID, point):
		key = uiGuild.GetGVGKey(gainGuildID, opponentGuildID)
		if not key in self.guildScoreBoardDict:
			return

		guildBoard = self.guildScoreBoardDict[key]
		guildBoard.SetScore(gainGuildID, opponentGuildID, point)

	## PK Mode
	def OnChangePKMode(self):
		self.wndCharacter.RefreshAlignment()
		self.dlgSystem.OnChangePKMode()

	## Refine
	def OpenRefineDialog(self, targetItemPos, nextGradeItemVnum, cost, prob, type, apply_random_list, src_vnum, bonus=0):
		self.dlgRefineNew.Open(targetItemPos, nextGradeItemVnum, cost, prob, type, apply_random_list, src_vnum, bonus)

	if app.ENABLE_AUTO_REFINE:
		def RefineFail(self, isFail):
			self.dlgRefineNew.CheckRefine(isFail)

	def AppendMaterialToRefineDialog(self, vnum, count):
		self.dlgRefineNew.AppendMaterial(vnum, count)

	def SetAffectShower(self, shower):
		#from _weakref import proxy
		#self.uiAffectshower = proxy(shower)
		self.uiAffectshower = shower
		if self.quickBuffSystem:
			self.quickBuffSystem.SetAffectShower(shower)
		if self.afkSystem:
			self.afkSystem.BindAffectShower(shower)

	def SettargetBoard(self, targetBoard):
		#from _weakref import proxy
		#self.uitargetBoard = proxy(targetBoard)
		self.uitargetBoard = targetBoard

	## Show & Hide
	def __CaptureWarpWindow(self, window, extra=None):
		if not window or not window.IsShow():
			return None

		x, y = window.GetGlobalPosition()
		state = {
			"position": (int(x), int(y)),
		}
		if extra:
			state.update(extra)
		return state

	def CaptureWarpUIState(self):
		windows = {}

		inventory = self.wndInventory
		state = self.__CaptureWarpWindow(inventory, {
			"page": int(inventory.GetInventoryPageIndex()),
			"equipment_page": int(getattr(inventory, "ExtraPageIndex", 0)),
		})
		if state:
			windows["inventory"] = state

		if self.IsSeparateCostumeInventory():
			state = self.__CaptureWarpWindow(self.wndCostumeInventory)
			if state:
				windows["costume_inventory"] = state

		character = self.wndCharacter
		state = self.__CaptureWarpWindow(character, {
			"state": character.GetState(),
		})
		if state:
			windows["character"] = state

		gameOption = getattr(self.dlgSystem, "gameOptionDlg", None)
		if gameOption and gameOption.IsShow():
			state = self.__CaptureWarpWindow(gameOption, {
				"mode": "game_options",
				"option_type": int(
					getattr(gameOption, "children", {}).get(
						"optionType", 0)),
				"category": int(
					getattr(gameOption, "children", {}).get(
						"categoryType", 0)),
			})
		else:
			state = self.__CaptureWarpWindow(self.dlgSystem, {
				"mode": "system_menu",
			})
		if state:
			windows["system"] = state

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			dragonSoul = self.wndDragonSoul
			state = self.__CaptureWarpWindow(dragonSoul, {
				"kind": int(getattr(dragonSoul, "DSKindIndex", 0)),
				"inventory_page": int(
					getattr(dragonSoul, "inventoryPageIndex", 0)),
				"deck_page": int(
					getattr(dragonSoul, "deckPageIndex", 0)),
			})
			if state:
				windows["dragon_soul"] = state

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			specialInventory = self.wndSpecialInventory
			inventoryType = int(specialInventory.GetInventoryType())
			if inventoryType in (0, 1, 2, 3, 4):
				state = self.__CaptureWarpWindow(specialInventory, {
					"inventory_type": inventoryType,
					"page": int(specialInventory.GetInventoryPageIndex()),
				})
				if state:
					windows["special_inventory"] = state

		state = self.__CaptureWarpWindow(self.wndMessenger, {
			"page": int(getattr(self.wndMessenger, "pageIdx", 0)),
		})
		if state:
			windows["messenger"] = state

		state = self.__CaptureWarpWindow(self.wndGuild, {
			"page": str(getattr(self.wndGuild, "currentPage", "")),
		})
		if state:
			windows["guild"] = state

		state = self.__CaptureWarpWindow(self.wndChatLog, {
			"size": (
				int(self.wndChatLog.GetWidth()),
				int(self.wndChatLog.GetHeight()),
			),
		})
		if state:
			windows["chat_log"] = state

		if self.wndSkillTree:
			state = self.__CaptureWarpWindow(self.wndSkillTree)
			if state:
				windows["skill_tree"] = state

		if app.ENABLE_WIKI and self.wndWiki:
			state = self.__CaptureWarpWindow(self.wndWiki)
			if state:
				windows["wiki"] = state

		if app.ENABLE_LOADING_PERFORMANCE and self.wndMiniMap:
			atlas = self.wndMiniMap.AtlasWindow
			state = self.__CaptureWarpWindow(atlas)
			if state:
				windows["atlas"] = state

		state = self.__CaptureWarpWindow(self.wndHelp)
		if state:
			windows["help"] = state

		if app.ENABLE_SWITCHBOT_SYSTEM:
			state = self.__CaptureWarpWindow(self.wndSwitchbot)
			if state:
				windows["switchbot"] = state

		if app.ENABLE_BIOLOG_SYSTEM:
			state = self.__CaptureWarpWindow(self.wndBio)
			if state:
				windows["biolog"] = state

		if app.ENABLE_GROWTH_PET_SYSTEM:
			petWindow = self.wndPetInfoWindow
			petState = int(getattr(
				petWindow, "state", player.PET_WINDOW_INFO))
			if petState == player.PET_WINDOW_INFO:
				state = self.__CaptureWarpWindow(petWindow, {
					"state": petState,
				})
				if state:
					windows["pet_info"] = state

		if app.ENABLE_RANKING_SYSTEM:
			rankingWindow = self.wndRankingBoardWindow
			state = self.__CaptureWarpWindow(rankingWindow, {
				"type": int(getattr(rankingWindow, "curType", 0)),
				"category": int(
					getattr(rankingWindow, "curCategory", 0)),
			})
			if state:
				windows["ranking_board"] = state

		if app.ENABLE_EVENT_MANAGER and self.wndEventManager:
			state = self.__CaptureWarpWindow(self.wndEventManager)
			if state:
				windows["event_calendar"] = state

		if app.ENABLE_BOSS_TRACK and self.wndBossTrack:
			state = self.__CaptureWarpWindow(self.wndBossTrack)
			if state:
				windows["boss_track"] = state

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			state = self.__CaptureWarpWindow(self.wndAutoHunting)
			if state:
				windows["auto_hunting"] = state

		if app.ENABLE_PLAYER_RANKING:
			state = self.__CaptureWarpWindow(self.wndRankInfo, {
				"page": int(getattr(self.wndRankInfo, "bCurPage", 0)),
			})
			if state:
				windows["rank_info"] = state

		if app.ENABLE_BUFF_SYSTEM:
			state = self.__CaptureWarpWindow(self.wndSupportPG)
			if state:
				windows["support"] = state

		if app.ENABLE_BATTLE_PASS:
			state = self.__CaptureWarpWindow(self.wndBattlePass)
			if state:
				windows["battle_pass"] = state

		if self.dropTrackerSystem and self.dropTrackerSystem.window:
			dropTracker = self.dropTrackerSystem.window
			state = self.__CaptureWarpWindow(dropTracker, {
				"detailed": bool(dropTracker.detailed),
				"advanced": bool(dropTracker.showAdvanced),
				"show_hidden": bool(dropTracker.showHidden),
				"expanded_item_vnum": int(dropTracker.expandedItemVnum),
				"page": int(dropTracker.model.page),
			})
			if state:
				windows["drop_tracker"] = state

		unifiedWindow = self.unifiedMessengerRouter.window
		state = self.__CaptureWarpWindow(unifiedWindow, {
			"selected_key": str(getattr(unifiedWindow, "selectedKey", "")),
			"selected_name": str(getattr(unifiedWindow, "selectedName", "")),
		} if unifiedWindow else None)
		if state:
			windows["unified_messenger"] = state

		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0) and self.wndVirtualMarket:
			state = self.__CaptureWarpWindow(
				self.wndVirtualMarket,
				self.wndVirtualMarket.CaptureWarpState(),
			)
			if state:
				windows["virtual_market"] = state

		if self.wndCustomPorts:
			state = self.__CaptureWarpWindow(self.wndCustomPorts, {
				"page": int(getattr(self.wndCustomPorts, "page", 0)),
			})
			if state:
				windows["custom_ports"] = state

		albumNotices = self.CapturePetAlbumNotices()
		if albumNotices:
			windows["pet_album_notices"] = albumNotices

		uiwarpstate.Store(player.GetName(), windows)

	def __RestoreWarpWindowPosition(self, window, state):
		if not window:
			return
		position = state.get("position")
		if not isinstance(position, (tuple, list)) or len(position) != 2:
			return

		screenWidth = max(0, int(wndMgr.GetScreenWidth()))
		screenHeight = max(0, int(wndMgr.GetScreenHeight()))
		windowWidth = max(0, int(window.GetWidth()))
		windowHeight = max(0, int(window.GetHeight()))
		x = max(0, min(int(position[0]), max(0, screenWidth - windowWidth)))
		y = max(0, min(int(position[1]), max(0, screenHeight - windowHeight)))
		window.SetPosition(x, y)
		window.UpdateRect()

	def __RestoreWarpInventory(self, state):
		window = self.wndInventory
		window.Show()
		window.SetInventoryPage(max(0, int(state.get("page", 0))))
		window.SetEquipmentPage(max(0, int(state.get("equipment_page", 0))))
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpCostumeInventory(self, state):
		if not self.IsSeparateCostumeInventory():
			return True
		window = self.wndCostumeInventory
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpCharacter(self, state):
		window = self.wndCharacter
		characterState = state.get("state", "STATUS")
		if characterState in getattr(window, "tabDict", {}):
			window.SetState(characterState)
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpSystem(self, state):
		mode = state.get("mode", "system_menu")
		if mode == "game_options":
			window = self.dlgSystem.OpenGameOptionDialog()
			if not window:
				return False
			optionType = max(0, int(state.get("option_type", 0)))
			category = max(0, int(state.get("category", 0)))
			window.SetCategoryTypeForOption(optionType, category)
		else:
			self.dlgSystem.OpenDialog()
			window = self.dlgSystem
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpDragonSoul(self, state):
		if not app.ENABLE_DRAGON_SOUL_SYSTEM:
			return True
		if not self.DRAGON_SOUL_IS_QUALIFIED:
			return False
		window = self.wndDragonSoul
		window.Show()
		window.SetDSKindIndex(max(0, int(state.get("kind", 0))))
		window.SetInventoryPage(max(
			0, int(state.get("inventory_page", 0))))
		window.SetDeckPage(max(0, int(state.get("deck_page", 0))))
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpSpecialInventory(self, state):
		if not app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			return True
		inventoryType = int(state.get("inventory_type", 0))
		if inventoryType not in (0, 1, 2, 3, 4):
			return True
		window = self.wndSpecialInventory
		window.SetInventoryType(inventoryType)
		window.SetInventoryPage(max(0, int(state.get("page", 0))))
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpMessenger(self, state):
		window = self.wndMessenger
		window.Show()
		page = max(0, min(3, int(state.get("page", 0))))
		selectPage = getattr(window, "_MessengerWindow__ClickPage", None)
		if selectPage:
			selectPage(page)
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpGuild(self, state):
		window = self.wndGuild
		restoreV2 = getattr(window, "RestoreGuildV2Warp", None)
		if restoreV2 and restoreV2(state, self.__RestoreWarpWindowPosition):
			return True
		if not window.CanOpen():
			return False
		window.Open()
		page = state.get("page", "")
		if page and page in getattr(window, "pageWindow", {}):
			window.SelectPage(page)
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpChatLog(self, state):
		window = self.wndChatLog
		size = state.get("size")
		if isinstance(size, (tuple, list)) and len(size) == 2:
			width = max(
				window.CHAT_LOG_WINDOW_MINIMUM_WIDTH,
				int(size[0]),
			)
			height = max(
				window.CHAT_LOG_WINDOW_MINIMUM_HEIGHT,
				int(size[1]),
			)
			window.btnSizing.SetPosition(
				width - window.btnSizing.GetWidth(),
				height - window.btnSizing.GetHeight() + 2,
			)
			window.OnResize()
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpSkillTree(self, state):
		if not self.wndSkillTree:
			return True
		self.wndSkillTree.Open()
		self.__RestoreWarpWindowPosition(self.wndSkillTree, state)
		self.wndSkillTree.SetTop()
		return True

	def __RestoreWarpWiki(self, state):
		if not app.ENABLE_WIKI:
			return True
		self.MakeWiki()
		if not self.wndWiki:
			return False
		self.wndWiki.Open()
		self.__RestoreWarpWindowPosition(self.wndWiki, state)
		self.wndWiki.SetTop()
		return True

	def __RestoreWarpHelp(self, state):
		self.OpenHelpWindow()
		self.__RestoreWarpWindowPosition(self.wndHelp, state)
		self.wndHelp.SetTop()
		return True

	def __RestoreWarpSwitchbot(self, state):
		if not app.ENABLE_SWITCHBOT_SYSTEM:
			return True
		window = self.wndSwitchbot
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpBiolog(self, state):
		if not app.ENABLE_BIOLOG_SYSTEM:
			return True
		window = self.wndBio
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpPetInfo(self, state):
		if not app.ENABLE_GROWTH_PET_SYSTEM:
			return True
		window = self.wndPetInfoWindow
		window.Show()
		window.SetState(player.PET_WINDOW_INFO)
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpRankingBoard(self, state):
		if not app.ENABLE_RANKING_SYSTEM:
			return True
		if not featureavailability.IsAvailable(featureavailability.RANKINGS):
			return True
		window = self.wndRankingBoardWindow
		window.Open(
			int(state.get("type", 0)),
			int(state.get("category", 0)),
		)
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpEventCalendar(self, state):
		if not app.ENABLE_EVENT_MANAGER:
			return True
		self.MakeEventCalendar()
		window = self.wndEventManager
		if not window:
			return False
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpBossTrack(self, state):
		if not app.ENABLE_BOSS_TRACK:
			return True
		if not self.wndBossTrack:
			self.wndBossTrack = uiBossTrack.Window()
		window = self.wndBossTrack
		window.Open()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpAutoHunting(self, state):
		if not app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			return True
		window = self.wndAutoHunting
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpRankInfo(self, state):
		if not app.ENABLE_PLAYER_RANKING:
			return True
		if not featureavailability.IsAvailable(featureavailability.RANKINGS):
			return True
		window = self.wndRankInfo
		window.bCurPage = max(0, int(state.get("page", 0)))
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpSupport(self, state):
		if not app.ENABLE_BUFF_SYSTEM:
			return True
		window = self.wndSupportPG
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpBattlePass(self, state):
		if not app.ENABLE_BATTLE_PASS:
			return True
		window = self.wndBattlePass
		window.Show()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpAtlas(self, state):
		if not app.ENABLE_LOADING_PERFORMANCE or not self.wndMiniMap:
			return True
		atlas = self.wndMiniMap.AtlasWindow
		if not atlas.IsShow():
			self.wndMiniMap.ToggleAtlasWindow()
		if not atlas.IsShow():
			return False
		self.__RestoreWarpWindowPosition(atlas, state)
		atlas.SetTop()
		return True

	def __RestoreWarpDropTracker(self, state):
		if not self.dropTrackerSystem or not self.dropTrackerSystem.window:
			return True
		window = self.dropTrackerSystem.window
		window.Open()
		window.SetDetailed(bool(state.get("detailed", False)))
		window.showAdvanced = bool(
			state.get("advanced", False) and window.detailed)
		window.showHidden = bool(state.get("show_hidden", False))
		window.expandedItemVnum = max(
			0, int(state.get("expanded_item_vnum", 0)))
		window.model.page = max(0, int(state.get("page", 0)))
		window.Refresh()
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpUnifiedMessenger(self, state):
		if not self.unifiedMessengerRouter.Available():
			return False
		name = state.get("selected_name", "")
		key = state.get("selected_key", "")
		if not self.unifiedMessengerRouter.Open(name, key):
			return False
		window = self.unifiedMessengerRouter.window
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def __RestoreWarpVirtualMarket(self, state):
		if not getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			return True
		if not self.wndVirtualMarket:
			self.wndVirtualMarket = uivirtualmarket.VirtualMarketWindow(self)
		self.wndVirtualMarket.RestoreWarpState(state)
		self.__RestoreWarpWindowPosition(self.wndVirtualMarket, state)
		self.wndVirtualMarket.SetTop()
		return True

	def __RestoreWarpCustomPorts(self, state):
		if not getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			return True

		window = self.wndCustomPorts
		if not window:
			return True

		pageCount = max(1, int(getattr(uicustomports, "PAGE_COUNT", 1)))
		page = max(0, min(
			pageCount - 1, int(state.get("page", 0))))
		window.Open()
		window.SetPage(page)
		self.__RestoreWarpWindowPosition(window, state)
		window.SetTop()
		return True

	def RestoreWarpUIState(self, windows):
		if not isinstance(windows, dict):
			return {}

		handlers = (
			("character", self.__RestoreWarpCharacter),
			("inventory", self.__RestoreWarpInventory),
			("costume_inventory", self.__RestoreWarpCostumeInventory),
			("system", self.__RestoreWarpSystem),
			("dragon_soul", self.__RestoreWarpDragonSoul),
			("special_inventory", self.__RestoreWarpSpecialInventory),
			("messenger", self.__RestoreWarpMessenger),
			("guild", self.__RestoreWarpGuild),
			("chat_log", self.__RestoreWarpChatLog),
			("skill_tree", self.__RestoreWarpSkillTree),
			("wiki", self.__RestoreWarpWiki),
			("atlas", self.__RestoreWarpAtlas),
			("help", self.__RestoreWarpHelp),
			("switchbot", self.__RestoreWarpSwitchbot),
			("biolog", self.__RestoreWarpBiolog),
			("pet_info", self.__RestoreWarpPetInfo),
			("ranking_board", self.__RestoreWarpRankingBoard),
			("event_calendar", self.__RestoreWarpEventCalendar),
			("boss_track", self.__RestoreWarpBossTrack),
			("auto_hunting", self.__RestoreWarpAutoHunting),
			("rank_info", self.__RestoreWarpRankInfo),
			("support", self.__RestoreWarpSupport),
			("battle_pass", self.__RestoreWarpBattlePass),
			("drop_tracker", self.__RestoreWarpDropTracker),
			("unified_messenger", self.__RestoreWarpUnifiedMessenger),
			("virtual_market", self.__RestoreWarpVirtualMarket),
			("custom_ports", self.__RestoreWarpCustomPorts),
			("pet_album_notices", self.__RestoreWarpPetAlbumNotices),
		)
		remaining = {}
		for key, handler in handlers:
			if key not in windows:
				continue
			try:
				if not handler(windows[key]):
					remaining[key] = windows[key]
			except:
				import dbg
				dbg.TraceError(
					"[WarpUI] failed to restore window '%s'" % key)
		return remaining

	def ShowDefaultWindows(self):
		if self.petAlbumNotice and not self.petAlbumArrivalVisible:
			self.petAlbumNotice.Resume()
		if getattr(self, "wndMissionBooks", None):
			self.wndMissionBooks.Resume()
		if self.noticeBoard:
			self.noticeBoard.Resume()
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Resume()
		self.wndTaskBar.Show()
		self.wndMiniMap.Show()
		self.wndMiniMap.ShowMiniMap()
		if getattr(self, "systemNotifications", None):
			self.systemNotifications.Resume()
		if self.wndEnergyBar:
			self.wndEnergyBar.Show()
		if self.wndGameButton:
			self.wndGameButton.Show()

		if self.uiAffectshower:
			self.uiAffectshower.Show()

		#if self.wndParty:
			#self.wndParty.Show()

		if app.ENABLE_CAPTCHA_SYSTEM:
			if self.wndChat:
				self.wndChat.Show()

		self.IsHideUiMode = False

	def IsHideUiMode(self):
		return self.IsHideUiMode

	def ShowAllWindows(self):
		self.wndTaskBar.Show()
		self.wndCharacter.Show()
		self.wndInventory.Show()

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.Show()
			self.wndDragonSoulRefine.Show()

		self.wndChat.Show()
		self.wndMiniMap.Show()

		if self.wndEnergyBar:
			self.wndEnergyBar.Show()

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyTaskBar:
				self.wndExpandedMoneyTaskBar.Show()
				self.wndExpandedMoneyTaskBar.SetTop()

	def HideAllWindows(self):
		if self.petAlbumNotice:
			self.petAlbumNotice.Suspend()
		if getattr(self, "wndMissionBooks", None):
			self.wndMissionBooks.Suspend()
		if getattr(self, "systemNotifications", None):
			self.systemNotifications.Suspend()
		if self.noticeBoard:
			self.noticeBoard.Suspend()
		if getattr(self, "wndCountdownHUD", None):
			self.wndCountdownHUD.Suspend()
		if self.wndParty:
			self.wndParty.Hide()

		if self.uiAffectshower:
			self.uiAffectshower.Hide()

		if self.uitargetBoard:
			self.uitargetBoard.Hide()

		if self.wndMiniGame:
			self.wndMiniGame.hide_mini_game_dialog()

		if self.wndTaskBar:
			self.wndTaskBar.Hide()

		if self.wndGameButton:
			self.wndGameButton.Hide()

		if self.wndEnergyBar:
			self.wndEnergyBar.Hide()

		if app.ENABLE_DETAILS_UI or app.ENABLE_SKILL_COLOR_SYSTEM:
			if self.wndCharacter:
				self.wndCharacter.Close()
		else:
			if self.wndCharacter:
				self.wndCharacter.Hide()

		if self.wndPermanentTasks:
			self.wndPermanentTasks.Close()

		if self.wndDailyTasks:
			self.wndDailyTasks.Close()

		if self.wndInventory:
			self.wndInventory.Hide()
		self.CloseTalismanWindow()
		self.CloseQuickEquipWindow()

		if self.wndTargetedRarity:
			self.wndTargetedRarity.Close()
		if self.wndRarity:
			self.wndRarity.Close()

		if self.wndResonance:
			self.wndResonance.Close()

		if self.quickBuffSystem and self.quickBuffSystem.window:
			self.quickBuffSystem.window.Close()

		if self.wndCostumeInventory:
			self.wndCostumeInventory.Hide()

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.Hide()
			self.wndDragonSoulRefine.Hide()

		if app.ENABLE_RANKING_SYSTEM:
			if self.wndRankingBoardWindow:
				self.wndRankingBoardWindow.Hide()

		if app.ENABLE_DUNGEON_INFO:
			if self.wndDungeonTrack:
				self.wndDungeonTrack.Close()

		if self.wndChat:
			self.wndChat.hide_btnChatSizing()
			self.wndChat.Hide()

		if self.wndMiniMap:
			self.wndMiniMap.Hide()

		if self.wndMessenger:
			self.wndMessenger.Hide()

		if self.wndGuild:
			self.wndGuild.Hide()

		if app.ENABLE_WIKI:
			if self.wndWiki:
				self.wndWiki.Hide()

		if app.ENABLE_TELEPORT_WINDOW:
			if self.wndTeleportPanel:
				self.wndTeleportPanel.Hide()
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.CloseAll()

		if self.wndCustomPorts:
			self.wndCustomPorts.Close()

		if self.wndGMPanel:
			self.wndGMPanel.Close()

		if self.dropTrackerSystem:
			self.dropTrackerSystem.CloseWindow()

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyTaskBar:
				self.wndExpandedMoneyTaskBar.Hide()

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			if self.wndSkillBookCombination:
				self.wndSkillBookCombination.Hide()

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if self.wndSpecialInventory:
				self.wndSpecialInventory.Hide()

		if app.ENABLE_OFFLINE_SHOP:
			uiOfflineShop.GetOfflineShopManager().HideAllWindows()
			self.CloseOfflineShopBuilder()

		self.IsHideUiMode = True

		if app.ENABLE_AURA_SYSTEM:
			if self.wndAura:
				self.wndAura.Hide()

		if app.ENABLE_SWITCHBOT_SYSTEM:
			if self.wndSwitchbot:
				self.wndSwitchbot.Hide()

		if self.wndSkillTree:
			self.wndSkillTree.Close()

		if self.wndMountSystem:
			self.wndMountSystem.Close()

		if app.ENABLE_GROWTH_PET_SYSTEM: 	
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.Hide()

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			if self.wndAutoHunting:
				self.wndAutoHunting.Hide()

	def ShowMouseImage(self):
		self.wndTaskBar.ShowMouseImage()

	def HideMouseImage(self):
		self.wndTaskBar.HideMouseImage()

	def ToggleChat(self):
		if True == self.wndChat.IsEditMode():
			self.wndChat.CloseChat()
		else:
			# 웹페이지가 열렸을때는 채팅 입력이 안됨
			if self.wndWeb and self.wndWeb.IsShow():
				pass
			else:
				self.wndChat.OpenChat()

	def IsOpenChat(self):
		return self.wndChat.IsEditMode()

	def SetChatFocus(self):
		self.wndChat.SetChatFocus()

	def OpenRestartDialog(self):
		self.dlgRestart.OpenDialog()
		self.dlgRestart.SetTop()

	def CloseRestartDialog(self):
		self.dlgRestart.Close()

	def ToggleSystemDialog(self):
		if False == self.dlgSystem.IsShow():
			self.dlgSystem.OpenDialog()
			self.dlgSystem.SetTop()
		else:
			self.dlgSystem.Close()

	def OpenSystemDialog(self):
		self.dlgSystem.OpenDialog()
		self.dlgSystem.SetTop()

	def ToggleMessenger(self):
		if self.wndMessenger.IsShow():
			self.wndMessenger.Hide()
		else:
			self.wndMessenger.SetTop()
			self.wndMessenger.Show()

	def IsUnifiedMessengerAvailable(self):
		return self.unifiedMessengerRouter.Available()

	def OpenUnifiedMessenger(self):
		return self.unifiedMessengerRouter.Open()

	def UnifiedMessengerCapability(self, enabled, pid, maxBody, pendingPerPair, pendingPerSender, retentionSeconds):
		self.unifiedMessengerRouter.Capability(enabled, pid, maxBody,
			pendingPerPair, pendingPerSender, retentionSeconds)
		self.wndMessenger.RefreshUnifiedMessengerButton()

	def UnifiedMessengerChanged(self, key, event):
		self.unifiedMessengerRouter.Changed(key, event)

	def UnifiedMessengerPlayerLookupCapability(self, enabled):
		self.unifiedMessengerRouter.PlayerLookupCapability(enabled)

	def UnifiedMessengerPlayerLookup(self, token, mode, status, rows):
		self.unifiedMessengerRouter.PlayerLookup(token, mode, status, rows)

	def UnifiedMessengerSubmitResult(self, messageID, error):
		self.unifiedMessengerRouter.SubmitResult(messageID, error)

	def UnifiedMessengerTyping(self, pid, name, active):
		self.unifiedMessengerRouter.Typing(pid, name, active)

	def UnifiedMessengerRecovery(self, status):
		self.unifiedMessengerRouter.Recovery(status)

	def ToggleAtlasWindow(self):
		self.wndMiniMap.ToggleAtlasWindow()

	def ToggleMiniMapVisibility(self):
		if False == self.wndMiniMap.isShowMiniMap():
			self.wndMiniMap.ShowMiniMap()
			self.wndMiniMap.SetTop()
		else:
			self.wndMiniMap.HideMiniMap()

	def ToggleMiniMap(self):
		if app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT):
			self.ToggleMiniMapVisibility()
		else:
			self.ToggleAtlasWindow()

	def PressMKey(self):
		if app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT):
			self.ToggleMessenger()
		elif app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT):
			self.ToggleMiniMapVisibility()
		else:
			self.ToggleAtlasWindow()

	def SetMapName(self, mapName):
		self.wndMiniMap.SetMapName(mapName)

	def MiniMapScaleUp(self):
		self.wndMiniMap.ScaleUp()

	def MiniMapScaleDown(self):
		self.wndMiniMap.ScaleDown()

	def OpenSkillTreeWindow(self):
		if self.wndSkillTree and not self.wndSkillTree.IsShow():
			self.wndSkillTree.Open()

	def ToggleSkillTreeWindow(self):
		if not self.wndSkillTree:
			return

		if self.wndSkillTree.IsShow():
			self.wndSkillTree.Close()
		else:
			self.OpenSkillTreeWindow()

	def ToggleMountSystemWindow(self):
		if self.wndMountSystem:
			return self.wndMountSystem.Toggle()
		return False

	def SetMountSystemCapability(self, enabled):
		if self.wndMountSystem:
			self.wndMountSystem.SetCapability(enabled)

	def ApplyMountSystemSnapshot(self, snapshot):
		if self.wndMountSystem:
			return self.wndMountSystem.ApplySnapshot(snapshot)
		return False

	def HandleMountSystemActionResult(self, sequence, revision, result):
		if self.wndMountSystem:
			self.wndMountSystem.HandleActionResult(sequence, revision, result)

	def HandleMountSystemError(self, code, messageKey, refreshRequired):
		if self.wndMountSystem:
			self.wndMountSystem.HandleError(code, messageKey, refreshRequired)

	def ToggleGMPanelWindow(self):
		if self.wndGMPanel:
			self.wndGMPanel.Toggle()

	def OnGMPanelResult(self, requestID, action, status, gmLevel, maskLow, maskHigh, message):
		if self.wndGMPanel:
			self.wndGMPanel.OnServerResult(requestID, action, status, gmLevel, maskLow, maskHigh, message)

	def ToggleCustomPortsWindow(self):
		if self.wndCustomPorts:
			self.wndCustomPorts.Toggle()

	def OnCustomPortsChanged(self):
		if self.wndCustomPorts:
			self.wndCustomPorts.OnChanged()

	def OnCustomPortsError(self, requestID, reason):
		if self.wndCustomPorts:
			self.wndCustomPorts.OnError(requestID, reason)

	def OnAfkSystemChanged(self):
		if self.afkSystem:
			self.afkSystem.OnChanged()

	def OnAfkRewardsChanged(self):
		if getattr(self, "wndItemShop", None):
			self.wndItemShop.RefreshAfkRewards()

	def OnAfkRewardPurchaseResult(self, result, balance):
		if getattr(self, "wndItemShop", None):
			self.wndItemShop.OnAfkRewardPurchaseResult(result, balance)

	def OnAfkTeleportOffer(self, offerId, expiresAt, mapIndex):
		if self.afkSystem:
			self.afkSystem.OnTeleportOffer(offerId, expiresAt, mapIndex)

	def OnAfkTeleportResult(self, offerId, status):
		if self.afkSystem:
			self.afkSystem.OnTeleportResult(offerId, status)

	def OnAfkSystemError(self, requestId, reason):
		if self.afkSystem:
			self.afkSystem.OnError(requestId, reason)

	def UpdateGuildInvitations(self, worldReady):
		if not self.wndGuild:
			return
		blocked = not worldReady or ui.IsEditLineFocused() or constInfo.GET_ITEM_QUESTION_DIALOG_STATUS()
		for name in ("wndCaptchaNew", "wndCaptcha", "inputDialog", "dlgExchange",
			"dlgShop", "dlgRestart", "dlgSystem", "dlgPassword", "dlgRefineNew",
			"dlgRefineElement", "dlgRefineElementChange", "wndTargetedRarity", "wndRarity",
			"wndVirtualMarket", "wndCubeRenewal", "wndSafebox", "wndMall"):
			window = getattr(self, name, None)
			if window and window.IsShow():
				blocked = True
		if any(window.IsShow() for window in self.wndQuestWindow.values()):
			blocked = True
		self.wndGuild.UpdateInvitations(not blocked)

	def UpdateAfkSystem(self):
		if self.afkSystem:
			self.afkSystem.OnUpdate()

	def ActivateQuickBuffs(self):
		if self.quickBuffSystem:
			self.quickBuffSystem.Activate()

	def OpenQuickBuffSettings(self):
		if self.quickBuffSystem:
			self.quickBuffSystem.OpenSettings()

	def UpdateQuickBuffSystem(self):
		if self.quickBuffSystem:
			self.quickBuffSystem.Tick()

	def SetQuickBuffVipStatus(self, active):
		if self.quickBuffSystem:
			self.quickBuffSystem.OnVipStatus(active)

	def ToggleDropTrackerWindow(self):
		if self.dropTrackerSystem:
			self.dropTrackerSystem.ToggleWindow()

	def GetDropTrackerRecentLifetime(self):
		if self.dropTrackerSystem:
			return self.dropTrackerSystem.model.recent_lifetime
		return 7

	def SetDropTrackerRecentLifetime(self, seconds):
		if self.dropTrackerSystem:
			return self.dropTrackerSystem.SetRecentLifetime(seconds)
		return False

	def GetDropTrackerPlacementMode(self):
		if self.dropTrackerSystem:
			return self.dropTrackerSystem.GetPlacementMode()
		return "taskbar"

	def SetDropTrackerPlacementMode(self, mode):
		if self.dropTrackerSystem:
			self.dropTrackerSystem.SetPlacementMode(mode)

	def BeginDropTrackerPlacementEdit(self):
		if self.dropTrackerSystem:
			return self.dropTrackerSystem.BeginPlacementEdit()
		return False

	def ResetDropTrackerFloatingPlacement(self):
		if self.dropTrackerSystem:
			self.dropTrackerSystem.ResetFloatingPlacement()

	def SetDropTrackerCapability(self, available):
		if self.dropTrackerSystem:
			self.dropTrackerSystem.SetCapability(available)

	def AddDropTrackerBatch(self, rows):
		if self.dropTrackerSystem:
			self.dropTrackerSystem.AddBatch(rows)

	def IsDropTrackerAvailable(self):
		return bool(
			self.dropTrackerSystem and self.dropTrackerSystem.available
		)

	def ToggleCharacterWindow(self, state):
		if False == player.IsObserverMode():
			if False == self.wndCharacter.IsShow():
				self.OpenCharacterWindowWithState(state)
			else:
				if state == self.wndCharacter.GetState():
					self.wndCharacter.OverOutItem()
					if app.ENABLE_DETAILS_UI or app.ENABLE_SKILL_COLOR_SYSTEM:
						self.wndCharacter.Close()
					else:
						self.wndCharacter.Hide()
				else:
					self.wndCharacter.SetState(state)

	def OpenCharacterWindowWithState(self, state):
		if False == player.IsObserverMode():
			self.wndCharacter.SetState(state)
			self.wndCharacter.Show()
			self.wndCharacter.SetTop()

	def OpenPermanentTasks(self, category=None):
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetCollectorCapability(
				self.permanentTasksAvailable
			)
			if self.permanentTasksSnapshot:
				self.wndPermanentTasks.SetCollectorSnapshot(
					self.permanentTasksSnapshot
				)
			if self.permanentTasksHunts:
				self.wndPermanentTasks.SetHuntSnapshots(
					tuple(self.permanentTasksHunts.values())
				)
			opened = self.wndPermanentTasks.Open(category)
			if self.permanentTasksSnapshot is None:
				self.RequestPermanentTasksSnapshot()
			return opened
		return False

	def RequestPermanentTasksSnapshot(self):
		if not self.permanentTasksAvailable or \
				self.permanentTasksSnapshotPending:
			return bool(self.permanentTasksSnapshotPending)
		self.permanentTasksSnapshotPending = True
		if not net.RequestPermanentTasksSnapshot():
			self.permanentTasksSnapshotPending = False
			return False
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetCollectorLoading(True)
		return True

	def SetPermanentTasksCapability(self, enabled, generation):
		enabled = bool(enabled)
		generation = max(0, int(generation))
		changed = (
			enabled != self.permanentTasksAvailable or
			generation != self.permanentTasksGeneration
		)
		self.permanentTasksAvailable = enabled
		self.permanentTasksGeneration = generation if enabled else 0
		if self.wndCharacter and changed:
			self.wndCharacter.SetLuckKnotCapability(enabled and generation >= 5)
		if changed and enabled and generation >= 5:
			net.RequestLuckKnotSnapshot()
		if changed:
			if self.wndCharacter:
				self.wndCharacter.SetPermanentTaskBonuses(0, 0)
		if changed:
			self.permanentTasksSnapshot = None
			self.permanentTasksHunts = {}
			self.permanentTasksSnapshotPending = False
			self.permanentTasksSubmitPending = False
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetCollectorCapability(enabled)
			if changed and enabled:
				self.wndPermanentTasks.SetCollectorLoading(True)
		if enabled and self.permanentTasksSnapshot is None:
			self.RequestPermanentTasksSnapshot()
		return True


	def ApplyPermanentHuntRewards(self, generation, rows):
		if not self.permanentTasksAvailable or generation != self.permanentTasksGeneration:
			return False
		if self.wndPermanentTasks:
			return self.wndPermanentTasks.SetHuntRewards(rows)
		return False

	def ApplyLuckKnotSnapshot(self, snapshot):
		if not isinstance(snapshot, dict) or snapshot.get("generation") != self.permanentTasksGeneration:
			return False
		effects = snapshot.get("effects_bp", ())
		costs = snapshot.get("costs", ())
		if len(effects) != 4 or any(value < 0 or value > 10000 for value in effects):
			return False
		if self.wndCharacter:
			self.wndCharacter.SetLuckKnotSnapshot(snapshot)
		code = snapshot.get("code", 7)
		messages = {3: localeInfo.LUCK_KNOT_MISSING, 4: localeInfo.LUCK_KNOT_LOW_LEVEL,
			5: localeInfo.LUCK_KNOT_MAXIMUM, 6: localeInfo.LUCK_KNOT_UNAVAILABLE}
		if code in messages:
			chat.AppendChat(chat.CHAT_TYPE_INFO, messages[code])
		if code in (2, 3, 4, 5):
			net.RequestLuckKnotSnapshot()
		return True

	def SetPermanentTasksAltheaMeteorChance(self, chanceBp):
		# Kept for protocol v3 clients; the retired collector has no UI bonus.
		return True

	def ApplyPermanentTasksSnapshot(self, snapshot):
		row = uipermanenttasks._NormalizeCollectorRow(snapshot)
		hunts = uipermanenttasks._NormalizeHuntRows(snapshot.get("hunts", ())
			if isinstance(snapshot, dict) else ())
		if row is None or hunts is None:
			self.permanentTasksSnapshotPending = False
			return self.RequestPermanentTasksSnapshot()
		if row["generation"] != self.permanentTasksGeneration:
			self.permanentTasksSnapshotPending = False
			return self.RequestPermanentTasksSnapshot()
		completedCategory = None
		for category, hunt in hunts.items():
			previous = self.permanentTasksHunts.get(category)
			if previous and previous["state"] == uipermanenttasks.COLLECTOR_STATE_ACTIVE and \
					hunt["revision"] > previous["revision"] and \
					hunt["stage"] > previous["stage"]:
				completedCategory = category
		self.permanentTasksSnapshot = row
		self.permanentTasksHunts = hunts
		self.permanentTasksSnapshotPending = False
		bossBonus = hunts["bossologie"]["completed_bonus_percent"]
		stoneBonus = hunts["kamenologie"]["completed_bonus_percent"]
		if self.wndCharacter:
			self.wndCharacter.SetPermanentTaskBonuses(bossBonus, stoneBonus,
				hunts["bossologie"]["stage"] - 1, hunts["kamenologie"]["stage"] - 1)
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetCollectorSnapshot(row)
			self.wndPermanentTasks.SetHuntSnapshots(tuple(hunts.values()))
			if completedCategory is not None:
				self.OpenPermanentTasks(completedCategory)
		return True

	def ApplyPermanentTasksSubmitResult(self, result):
		row = uipermanenttasks._NormalizeCollectorRow(result)
		if row is None or row["generation"] != self.permanentTasksGeneration:
			self.permanentTasksSubmitPending = False
			return self.RequestPermanentTasksSnapshot()
		self.permanentTasksSnapshot = row
		self.permanentTasksSubmitPending = False
		normalizedResult = dict(result)
		normalizedResult.update(row)
		if self.wndPermanentTasks:
			return self.wndPermanentTasks.SetCollectorSubmitResult(normalizedResult)
		return True

	def SetPermanentTasksStatus(self, statusCode):
		statusCode = int(statusCode)
		if statusCode == uipermanenttasks.COLLECTOR_STATUS_UNAVAILABLE:
			self.permanentTasksSnapshotPending = False
			self.permanentTasksSubmitPending = False
			self.permanentTasksSnapshot = None
			self.permanentTasksHunts = {}
			if self.wndCharacter:
				self.wndCharacter.SetPermanentTaskBonuses(0, 0)
		elif statusCode in (
				uipermanenttasks.COLLECTOR_STATUS_LOADING,
				uipermanenttasks.COLLECTOR_STATUS_RESYNC_REQUIRED):
			self.permanentTasksSnapshotPending = False
			self.permanentTasksSnapshot = None
			self.permanentTasksHunts = {}
			if self.wndCharacter:
				self.wndCharacter.SetPermanentTaskBonuses(0, 0)
			if statusCode == uipermanenttasks.COLLECTOR_STATUS_RESYNC_REQUIRED:
				self.permanentTasksSubmitPending = False
		if self.wndPermanentTasks:
			self.wndPermanentTasks.SetCollectorStatus(statusCode)
		if statusCode in (
				uipermanenttasks.COLLECTOR_STATUS_LOADING,
				uipermanenttasks.COLLECTOR_STATUS_RESYNC_REQUIRED):
			return self.RequestPermanentTasksSnapshot()
		return True

	def OpenDailyTasks(self):
		if self.wndDailyTasks:
			self.wndDailyTasks.SetAvailable(self.dailyTasksAvailable)
			if self.dailyTasksSnapshot:
				self.wndDailyTasks.SetSnapshot(self.dailyTasksSnapshot)
			return self.wndDailyTasks.Open()
		return False

	def RequestDailyTaskHandIn(self, taskId):
		if not self.dailyTasksAvailable or not self.dailyTasksSnapshot:
			return False
		if not isinstance(taskId, str) or not taskId.startswith("d2_chest_") or len(taskId) > 32:
			return False
		if any(char not in "abcdefghijklmnopqrstuvwxyz0123456789_" for char in taskId):
			return False
		for task in self.dailyTasksSnapshot.get("tasks", ()):
			if task.get("id") == taskId and task.get("status") == uidailytasks.TASK_STATUS_ACTIVE:
				net.SendChatPacket("/daily_handin " + taskId)
				return True
		return False

	def RequestDailyTasksSnapshot(self):
		if not self.dailyTasksAvailable or self.dailyTasksSnapshotPending:
			return bool(self.dailyTasksSnapshotPending)
		self.dailyTasksSnapshotPending = True
		if not net.RequestDailyTasksSnapshot():
			self.dailyTasksSnapshotPending = False
			return False
		if self.wndDailyTasks:
			self.wndDailyTasks.SetLoading()
		return True

	def SetDailyTasksCapability(self, enabled, generation):
		enabled = bool(enabled)
		generation = max(0, int(generation))
		changed = (
			enabled != self.dailyTasksAvailable or
			generation != self.dailyTasksGeneration
		)
		self.dailyTasksAvailable = enabled
		self.dailyTasksGeneration = generation if enabled else 0
		if changed:
			self.dailyTasksSnapshot = None
			self.dailyTasksSnapshotPending = False
		if self.wndDailyTasks:
			self.wndDailyTasks.SetAvailable(enabled)
		if enabled and self.dailyTasksSnapshot is None:
			self.RequestDailyTasksSnapshot()
		return True

	def ApplyDailyTasksSnapshot(self, snapshot):
		if not isinstance(snapshot, dict):
			return False
		if int(snapshot.get("generation", 0)) != self.dailyTasksGeneration:
			self.dailyTasksSnapshotPending = False
			return self.RequestDailyTasksSnapshot()
		self.dailyTasksSnapshot = dict(snapshot)
		self.dailyTasksSnapshot["tasks"] = tuple(snapshot.get("tasks", ()))
		self.dailyTasksSnapshotPending = False
		if self.wndDailyTasks:
			self.wndDailyTasks.SetSnapshot(self.dailyTasksSnapshot)
		return True

	def ApplyDailyTasksDelta(self, delta):
		merged = uidailytasks._ApplyDeltaToSnapshot(
			self.dailyTasksSnapshot, delta
		)
		if merged is None:
			self.dailyTasksSnapshotPending = False
			return self.RequestDailyTasksSnapshot()
		if merged is self.dailyTasksSnapshot:
			return False
		self.dailyTasksSnapshot = merged
		if self.wndDailyTasks:
			self.wndDailyTasks.SetSnapshot(merged)
		return True

	def SetDailyTasksStatus(self, statusCode):
		statusCode = int(statusCode)
		if statusCode in (
			uidailytasks.STATUS_LOADING,
			uidailytasks.STATUS_RESYNC_REQUIRED,
		):
			self.dailyTasksSnapshotPending = False
			self.dailyTasksSnapshot = None
			if self.wndDailyTasks:
				self.wndDailyTasks.SetStatus(statusCode)
			return self.RequestDailyTasksSnapshot()
		if statusCode == uidailytasks.STATUS_UNAVAILABLE:
			self.dailyTasksSnapshotPending = False
			self.dailyTasksSnapshot = None
		if self.wndDailyTasks:
			self.wndDailyTasks.SetStatus(statusCode)
		return True

	def ToggleCharacterWindowStatusPage(self):
		self.ToggleCharacterWindow("STATUS")

	def ToggleInventoryWindow(self):
		if False == player.IsObserverMode():
			if False == self.wndInventory.IsShow():
				self.wndInventory.Show()
				self.wndInventory.SetTop()
			else:
				self.wndInventory.OverOutItem()
				self.wndInventory.Close()

	def ToggleTalismanWindow(self):
		if not self.wndTalisman or not self.talismanSetAvailable:
			return False
		result = self.wndTalisman.Toggle()
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonSelected(
				uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN,
				self.wndTalisman.IsShow(),
			)
		return result

	def ToggleQuickEquipWindow(self):
		if not self.wndQuickEquip:
			return
		self.wndQuickEquip.Toggle()
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonSelected(
				uiTaskBar.ExpandedTaskBar.BUTTON_QUICK_EQUIP,
				self.wndQuickEquip.IsShow(),
			)

	def CloseQuickEquipWindow(self):
		if self.wndQuickEquip:
			self.wndQuickEquip.Close()

	def __QuickEquipClosed(self):
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonSelected(
				uiTaskBar.ExpandedTaskBar.BUTTON_QUICK_EQUIP, False
			)

	def QuickEquipReset(self):
		if self.wndQuickEquip:
			self.wndQuickEquip.Reset()

	def QuickEquipSet(self, index, nameHex):
		if self.wndQuickEquip:
			self.wndQuickEquip.ReceiveSet(index, nameHex)

	def QuickEquipItem(self, index, wear, vnum):
		if self.wndQuickEquip:
			self.wndQuickEquip.ReceiveItem(index, wear, vnum)

	def QuickEquipReady(self):
		if self.wndQuickEquip:
			self.wndQuickEquip.Ready()

	def QuickEquipStatus(self, code):
		if self.wndQuickEquip:
			self.wndQuickEquip.Status(code)

	def CloseTalismanWindow(self):
		if self.wndTalisman:
			self.wndTalisman.Close()
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonSelected(
				uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN, False
			)

	def SetTalismanSetCapability(self, enabled):
		self.talismanSetAvailable = (
			uiTalisman.IsSupported() and self.wndTalisman is not None
		)
		if self.wndTalisman:
			self.wndTalisman.SetCapability(self.talismanSetAvailable)
		if self.wndExpandedTaskBar:
			self.wndExpandedTaskBar.SetButtonEnabled(
				uiTaskBar.ExpandedTaskBar.BUTTON_TALISMAN,
				self.talismanSetAvailable,
			)
		return True

	if app.ENABLE_TELEPORT_WINDOW:
		def ToggleTeleportPanel(self):
			if False == self.wndTeleportPanel.IsShow():
				self.wndTeleportPanel.Show()
				self.wndTeleportPanel.SetTop()
			else:
				self.wndTeleportPanel.Close()
		
		def ReceiveTeleportQuestCommand(self, command):
			self.wndTeleportPanel.ReceiveQuestCommand(command)

		def ToggleTeleportAtlas(self):
			self.wndTeleportAtlas.ToggleMaps()

		def OpenTeleportAtlas(self):
			self.wndTeleportAtlas.OpenMaps()

	def ToggleExpandedButton(self):
		if player.IsObserverMode():
			return
		self.ToggleInventoryWindow()

		if app.ENABLE_GEM_SYSTEM:
			# self.wndExpandedMoneyTaskBar.LoadWindow()
			pass

	if app.ENABLE_GEM_SYSTEM:
		def ToggleExpandedMoneyButton(self):
			if False == self.wndExpandedMoneyTaskBar.IsShow():
				self.wndExpandedMoneyTaskBar.Show()
				self.wndExpandedMoneyTaskBar.SetTop()
			else:
				self.wndExpandedMoneyTaskBar.Close()

	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		def ToggleSpecialInventoryWindow(self):
			if False == player.IsObserverMode():
				if False == self.wndSpecialInventory.IsShow():
					self.wndSpecialInventory.Show()
					self.wndSpecialInventory.SetTop()
				else:
					self.wndSpecialInventory.OverOutItem()
					self.wndSpecialInventory.Close()

		def OpenSpecialInventoryWindow(self, category = 0):
			if int(category) == uiSpecialInventory.RETIRED_COSTUME_BUTTON_NUM:
				if False == player.IsObserverMode():
					self.OpenInventoryWindow()
				return

			if False == player.IsObserverMode():
				if False == self.wndSpecialInventory.IsShow():
					self.wndSpecialInventory.Show()
					self.wndSpecialInventory.SetTop()
					self.wndSpecialInventory.SetInventoryType(category)
				else:
					self.wndSpecialInventory.OverOutItem()
					self.wndSpecialInventory.Close()

		def OpenItemShopMallFromSpecInv(self):
			if False == player.IsObserverMode():
			
				mall_idx = self.wndSpecialInventory.GetMallButtonIDX()
				
				if self.wndSpecialInventory.IsShow():
					if self.wndSpecialInventory.GetInventoryType() == mall_idx:
						self.wndSpecialInventory.OverOutItem()
						self.wndSpecialInventory.Close()
						
						self.wndSpecialInventory.Show()
						self.wndSpecialInventory.SetTop()
						self.wndSpecialInventory.SetInventoryType(mall_idx)
					else:
						self.wndSpecialInventory.SetTop()
						self.wndSpecialInventory.SetInventoryType(mall_idx)
				else:
					self.wndSpecialInventory.Show()
					self.wndSpecialInventory.SetTop()
					self.wndSpecialInventory.SetInventoryType(mall_idx)

	def OpenCostumeWindow(self):
		if self.IsSeparateCostumeInventory():
			self.ShowCostumeInventoryWindow()
			return
		self.wndInventory.Show()
		self.wndInventory.ShowCostumeInventory()
		self.wndInventory.SetTop()

	def IsSeparateCostumeInventory(self):
		return bool(self.separateCostumeInventory)

	def SetSeparateCostumeInventory(self, enabled):
		enabled = bool(enabled)
		wasEmbeddedCostumeVisible = bool(
			self.wndInventory and self.wndInventory.IsShow() and
			int(getattr(self.wndInventory, "ExtraPageIndex", 0)) == 1)
		wasSeparateVisible = bool(
			self.wndCostumeInventory and
			self.wndCostumeInventory.IsShow())

		self.separateCostumeInventory = enabled
		uiCostumeInventory.SetSeparateModeEnabled(enabled)

		if enabled:
			self.wndInventory.SetEquipmentPage(0)
			if wasEmbeddedCostumeVisible:
				self.ShowCostumeInventoryWindow()
		else:
			if self.wndCostumeInventory:
				self.wndCostumeInventory.Close()
			if wasSeparateVisible:
				self.wndInventory.Show()
				self.wndInventory.SetEquipmentPage(1)
				self.wndInventory.SetTop()

	def ShowCostumeInventoryWindow(self):
		if self.wndCostumeInventory:
			self.wndCostumeInventory.Open()

	def ToggleCostumeInventoryWindow(self):
		if self.wndCostumeInventory:
			self.wndCostumeInventory.Toggle()

	def OpenInventoryWindow(self):
		self.wndInventory.ShowInventory()

	if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
		def RefreshSpecialInventory(self):
			self.wndSpecialInventory.RefreshBagSlotWindow()
			
		def SpecialInventoryDisableEffect(self):
			self.wndSpecialInventory.DisableMultipleEffect()

	# wj.2014.12.2. 인벤토리와 DS인벤 간의 상태를 확인 및 설정하기 위한 함수.
	def IsShowDlgQuestionWindow(self):
		if self.wndInventory.IsDlgQuestionShow():
			return True
		elif self.wndDragonSoul.IsDlgQuestionShow():
			return True
		else:
			return False

	def CloseDlgQuestionWindow(self):
		if self.wndInventory.IsDlgQuestionShow():
			self.wndInventory.CancelDlgQuestion()
		if self.wndDragonSoul.IsDlgQuestionShow():
			self.wndDragonSoul.CancelDlgQuestion()

	def SetUseItemMode(self, bUse):
		self.wndInventory.SetUseItemMode(bUse)
		self.wndDragonSoul.SetUseItemMode(bUse)

	# 용혼석
	def DragonSoulActivate(self, deck):
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.ActivateDragonSoulByExtern(deck)

	def DragonSoulDeactivate(self):
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.wndDragonSoul.DeactivateDragonSoul()

	if app.ENABLE_DS_SET:
		def DragonSoulSetGrade(self, grade):
			self.wndDragonSoul.SetDSSetGrade(grade)

	def Highligt_Item(self, inven_type, inven_pos):
		if player.DRAGON_SOUL_INVENTORY == inven_type:
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				self.wndDragonSoul.HighlightSlot(inven_pos)
		elif app.WJ_ENABLE_PICKUP_ITEM_EFFECT and player.INVENTORY == inven_type:
			self.wndInventory.HighlightSlot(inven_pos)
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.wndSpecialInventory.HighlightSlot(inven_pos)

	def DragonSoulGiveQuilification(self):
		self.DRAGON_SOUL_IS_QUALIFIED = True
		self.wndExpandedTaskBar.SetToolTipText(uiTaskBar.ExpandedTaskBar.BUTTON_DRAGON_SOUL, uiScriptLocale.TASKBAR_DRAGON_SOUL)

	def ToggleDragonSoulWindow(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if False == self.wndDragonSoul.IsShow():
					if self.DRAGON_SOUL_IS_QUALIFIED:
						self.wndDragonSoul.Show()
					else:
						try:
							self.wndPopupDialog.SetText(localeInfo.DRAGON_SOUL_UNQUALIFIED)
							self.wndPopupDialog.Open()
						except:
							self.wndPopupDialog = uiCommon.PopupDialog()
							self.wndPopupDialog.SetText(localeInfo.DRAGON_SOUL_UNQUALIFIED)
							self.wndPopupDialog.Open()
				else:
					self.wndDragonSoul.Close()

	def ToggleDragonSoulWindowWithNoInfo(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if False == self.wndDragonSoul.IsShow():
					if self.DRAGON_SOUL_IS_QUALIFIED:
						self.wndDragonSoul.Show()
				else:
					self.wndDragonSoul.Close()

	def FailDragonSoulRefine(self, reason, inven_type, inven_pos):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow() or \
					(app.ENABLE_EXTENDED_DRAGON_SOUL and self.wndDragonSoulRefine.autoRefinePending):
					self.wndDragonSoulRefine.RefineFail(reason, inven_type, inven_pos)

	def SucceedDragonSoulRefine(self, inven_type, inven_pos):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow() or \
					(app.ENABLE_EXTENDED_DRAGON_SOUL and self.wndDragonSoulRefine.autoRefinePending):
					self.wndDragonSoulRefine.RefineSucceed(inven_type, inven_pos)

	if app.ENABLE_DS_CHANGE_ATTR:
		def OpenDragonSoulRefineWindow(self, type):
			if False == player.IsObserverMode():
				if app.ENABLE_DRAGON_SOUL_SYSTEM:
					if False == self.wndDragonSoulRefine.IsShow():
						self.wndDragonSoulRefine.SetWindowType(type)
						self.wndDragonSoulRefine.Show()
						if None != self.wndDragonSoul:
							if False == self.wndDragonSoul.IsShow():
								self.wndDragonSoul.Show()
	else:
		def OpenDragonSoulRefineWindow(self):
			if False == player.IsObserverMode():
				if app.ENABLE_DRAGON_SOUL_SYSTEM:
					if False == self.wndDragonSoulRefine.IsShow():
						self.wndDragonSoulRefine.Show()
						if None != self.wndDragonSoul:
							if False == self.wndDragonSoul.IsShow():
								self.wndDragonSoul.Show()

	def CloseDragonSoulRefineWindow(self):
		if False == player.IsObserverMode():
			if app.ENABLE_DRAGON_SOUL_SYSTEM:
				if True == self.wndDragonSoulRefine.IsShow():
					self.wndDragonSoulRefine.Close()

	# 용혼석 끝

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def PetInformationActivate(self):
			pass

		def TogglePetInformationWindow(self):
			if False == player.IsObserverMode():
				if not self.wndPetInfoWindow.IsShow():
					self.wndPetInfoWindow.Show()
				else:
					self.wndPetInfoWindow.Close()

		def SetAutoCooltime(self, slotindex, cooltime):
			self.wndAutoWindow.SetAutoCooltime(slotindex, cooltime)

		def GetAutoStartonoff(self):
			return self.wndAutoWindow.GetAutoStartonoff()

		def RefreshAutoSkillSlot(self):
			if self.wndAutoWindow:
				self.wndAutoWindow.RefreshAutoSkillSlot()

		def RefreshAutoPotionSlot(self):
			if self.wndAutoWindow:
				self.wndAutoWindow.RefreshAutoPotionSlot()

		def AutoOff(self):
			if self.wndAutoWindow:
				self.wndAutoWindow.Close()

		def AutoOn(self):
			pass

	if app.ENABLE_RANKING_SYSTEM:
		def OpenRankingBoardWindow(self, type, category):
			if self.wndRankingBoardWindow:
				self.wndRankingBoardWindow.Open(type, category)

	def OpenGuildDisband(self):
		return self.wndGuild.OpenDisbandDialog()

	def OpenGuildCreation(self):
		return self.wndGuild.OpenCreateDialog()

	def ToggleGuildWindow(self):
		if not self.wndGuild.IsShow():
			if self.wndGuild.CanOpen():
				self.wndGuild.Open()
			else:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.GUILD_YOU_DO_NOT_JOIN)
		else:
			self.wndGuild.OverOutItem()
			self.wndGuild.Hide()

	def ToggleChatLogWindow(self):
		if hasattr(self.wndChat, "ToggleHistory"):
			self.wndChat.ToggleHistory()
			return
		if self.wndChatLog.IsShow():
			self.wndChatLog.Hide()
		else:
			self.wndChatLog.Show()

	def CheckGameButton(self):
		if self.wndGameButton:
			self.wndGameButton.CheckGameButton()

	def __OnClickStatusPlusButton(self):
		self.ToggleCharacterWindow("STATUS")

	def __OnClickSkillPlusButton(self):
		self.ToggleCharacterWindow("SKILL")

	def __OnClickQuestButton(self):
		self.ToggleCharacterWindow("QUEST")

	def __OnClickHelpButton(self):
		player.SetPlayTime(1)
		self.CheckGameButton()
		self.OpenHelpWindow()

	def __OnClickBuildButton(self):
		self.BUILD_OpenWindow()

	def OpenHelpWindow(self):
		self.wndHelp.Open()
		self.wndUICurtain.Show()

	def CloseHelpWindow(self):
		self.wndHelp.Close()
		self.wndUICurtain.Hide()

	def OpenWebWindow(self, url):
		self.wndWeb.Open(url)
		# 웹페이지를 열면 채팅을 닫는다
		self.wndChat.CloseChat()

	if app.ENABLE_SWITCHBOT_SYSTEM:
		def ToggleSwitchbotWindow(self):
			if self.wndSwitchbot.IsShow():
				self.wndSwitchbot.Close()
			else:
				self.wndSwitchbot.Open()
				
		def RefreshSwitchbotWindow(self):
			if self.wndSwitchbot and self.wndSwitchbot.IsShow():
				self.wndSwitchbot.RefreshSwitchbotWindow()

		def RefreshSwitchbotItem(self, slot):
			if self.wndSwitchbot and self.wndSwitchbot.IsShow():
				self.wndSwitchbot.RefreshSwitchbotItem(slot)

	if app.ENABLE_MINI_GAME_OKEY:
		def OpenCardsInfoWindow(self):
			self.wndCardsInfo.Open()

		def OpenCardsWindow(self, safemode):
			self.wndCards.Open(safemode)

		def UpdateCardsInfo(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, hand_4, hand_4_v, hand_5, hand_5_v, cards_left, points):
			self.wndCards.UpdateCardsInfo(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, hand_4, hand_4_v, hand_5, hand_5_v, cards_left, points)

		def UpdateCardsFieldInfo(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points):
			self.wndCards.UpdateCardsFieldInfo(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points)

		def CardsPutReward(self, hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points):
			self.wndCards.CardsPutReward(hand_1, hand_1_v, hand_2, hand_2_v, hand_3, hand_3_v, points)

		def CardsShowIcon(self):
			self.wndCardsIcon.Show()

	# Show GIFT
	def ShowGift(self):
		self.wndTaskBar.ShowGift()

	def HideGift(self):
		self.wndTaskBar.HideGift()

	def CloseWbWindow(self):
		self.wndWeb.Close()

	if app.ENABLE_FISHING_GAME:
		def OpenFishingGameWindow(self, level):
			if self.wndFishingGame:
				self.wndFishingGame.Open(level)

		def CloseFishingGameWindow(self):
			if self.wndFishingGame:
				self.wndFishingGame.Close()

		def IsFishGameOpen(self):
			if self.wndFishingGame and self.wndFishingGame.IsShow():
				return True
			return False

	if app.ENABLE_ACCE_COSTUME_SYSTEM:
		def ActAcce(self, iAct, bWindow):
			if iAct == 1:
				if bWindow == True:
					if not self.wndAcceCombine.IsOpened():
						self.wndAcceCombine.Open()

					if not self.wndInventory.IsShow():
						self.wndInventory.Show()

				else:
					if not self.wndAcceAbsorption.IsOpened():
						self.wndAcceAbsorption.Open()

					if not self.wndInventory.IsShow():
						self.wndInventory.Show()

				self.wndInventory.RefreshBagSlotWindow()
				self.wndSpecialInventory.RefreshBagSlotWindow()
			elif iAct == 2:
				if bWindow == True:
					if self.wndAcceCombine.IsOpened():
						self.wndAcceCombine.Close()
				else:
					if self.wndAcceAbsorption.IsOpened():
						self.wndAcceAbsorption.Close()

				self.wndInventory.RefreshBagSlotWindow()
				self.wndSpecialInventory.RefreshBagSlotWindow()
			elif iAct == 3 or iAct == 4:
				if bWindow == True:
					if self.wndAcceCombine.IsOpened():
						self.wndAcceCombine.Refresh(iAct)
				else:
					if self.wndAcceAbsorption.IsOpened():
						self.wndAcceAbsorption.Refresh(iAct)

				self.wndInventory.RefreshBagSlotWindow()
				self.wndSpecialInventory.RefreshBagSlotWindow()

	if app.ENABLE_CAPTCHA_SYSTEM and not getattr(app, "ENABLE_CAPTCHA_V2", 0):
		def ShowCaptcha(self, timeLeft):
			self.wndCaptcha.Open(timeLeft)

	def OpenCubeWindow(self):
		self.wndCube.Open()

		if False == self.wndInventory.IsShow():
			self.wndInventory.Show()

	def UpdateCubeInfo(self, gold, itemVnum, count):
		self.wndCube.UpdateInfo(gold, itemVnum, count)

	def CloseCubeWindow(self):
		self.wndCube.Close()

	def FailedCubeWork(self):
		self.wndCube.Refresh()

	def SucceedCubeWork(self, itemVnum, count):
		self.wndCube.Clear()

		if 0: # 결과 메시지 출력은 생략 한다
			self.wndCubeResult.SetPosition(*self.wndCube.GetGlobalPosition())
			self.wndCubeResult.SetCubeResultItem(itemVnum, count)
			self.wndCubeResult.Open()
			self.wndCubeResult.SetTop()

	def __HideWindows(self):
		hideWindows = self.wndTaskBar,\
						self.wndCharacter,\
						self.wndInventory,\
						self.wndMiniMap,\
						self.wndGuild,\
						self.wndMessenger,\
						self.wndChat,\
						self.wndParty,\
						self.wndGameButton,

		if self.wndMiniGame:
			hideWindows += self.wndMiniGame,

		if self.dlgSystem:
			hideWindows += self.dlgSystem,

		if self.wndEnergyBar:
			hideWindows += self.wndEnergyBar,

		if app.ENABLE_GEM_SYSTEM:
			if self.wndExpandedMoneyTaskBar:
				hideWindows += self.wndExpandedMoneyTaskBar,

		if app.ENABLE_RANKING_SYSTEM:
			if self.wndRankingBoardWindow:
				hideWindows += self.wndRankingBoardWindow,

		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			hideWindows += self.wndDragonSoul,\
				self.wndDragonSoulRefine,

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			if self.wndSpecialInventory:
				hideWindows += self.wndSpecialInventory,

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if self.wndPetInfoWindow:
				hideWindows += self.wndPetInfoWindow,

		if app.ENABLE_TELEPORT_WINDOW:
			if self.wndTeleportPanel:
				hideWindows += self.wndTeleportPanel,
			if self.wndTeleportAtlas:
				hideWindows += self.wndTeleportAtlas,

		if self.wndCustomPorts:
			hideWindows += self.wndCustomPorts,

		if getattr(self, "wndMissionBooks", None):
			hideWindows += self.wndMissionBooks,
			if self.wndMissionBooks.tracker:
				hideWindows += self.wndMissionBooks.tracker,

		if self.dropTrackerSystem and self.dropTrackerSystem.window:
			hideWindows += self.dropTrackerSystem.window,

		if self.quickBuffSystem and self.quickBuffSystem.window:
			hideWindows += self.quickBuffSystem.window,

		if app.ENABLE_SWITCHBOT_SYSTEM and self.wndSwitchbot:
			hideWindows += self.wndSwitchbot,

		if app.ENABLE_ATTR_6TH_7TH:
			if self.wndAttr67Add:
				hideWindows += self.wndAttr67Add,

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			if self.wndAutoHunting:
				hideWindows += self.wndAutoHunting,

		hideWindows = [x for x in hideWindows if x.IsShow()]
		for x in hideWindows:
			x.Hide()
		import sys

		self.HideAllQuestButton()
		self.HideAllWhisperButton()

		if self.wndChat.IsEditMode():
			self.wndChat.CloseChat()

		if self.dlgSystem:
			self.dlgSystem.HideAllSystemOptioin()

		self.wndMiniMap.AtlasWindow.Hide()

		if self.wndWeb:
			self.wndWeb.CloseWhenOpenQuest()

		return hideWindows

	def __ShowWindows(self, wnds):
		import sys
		for x in wnds:
			x.Show()
		global IsQBHide
		if not IsQBHide:
			self.ShowAllQuestButton()
		else:
			self.HideAllQuestButton()

		self.ShowAllWhisperButton()

		if self.dlgSystem:
			self.dlgSystem.ShowAllSystemOptioin()

		if self.wndMiniMap.AtlasWindow and self.wndMiniMap.AtlasWindow.IsShowWindow():
			self.wndMiniMap.AtlasWindow.Show()

		if self.wndWeb:
			self.wndWeb.OpenWhenOpenQuest()

	def BINARY_OpenAtlasWindow(self):
		if self.wndMiniMap:
			self.wndMiniMap.ShowAtlas()

	def BINARY_SetObserverMode(self, flag):
		self.wndGameButton.SetObserverMode(flag)

	# ACCESSORY_REFINE_ADD_METIN_STONE
	def BINARY_OpenSelectItemWindow(self):
		self.wndItemSelect.Open()
	# END_OF_ACCESSORY_REFINE_ADD_METIN_STONE

	if app.ENABLE_GEM_SYSTEM:
		def BINARY_OpenSelectItemWindowEx(self):
			self.wndItemSelectEx.Open()

		def BINARY_RefreshSelectItemWindowEx(self):
			self.wndItemSelectEx.RefreshSlot()

	#####################################################################################
	### Private Shop ###
	def OpenPrivateShopInputNameDialog(self):
		#if player.IsInSafeArea():
		#	chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.CANNOT_OPEN_PRIVATE_SHOP_IN_SAFE_AREA)
		#	return

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			if self.wndSkillBookCombination.IsShow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.COMB_NOTICE)
				return

		if app.ENABLE_AURA_SYSTEM:
			if self.wndAura and self.wndAura.IsShow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_OPEN_OTHER_WINDOW)
				return

		if app.ENABLE_GROWTH_PET_SYSTEM:
			pet_id = player.GetActivePetItemId()
			if pet_id:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.PET_CAN_NOT_OPEN_SHOP_BECAUSE_SUMMON)
				return

		inputDialog = uiCommon.InputDialog()
		inputDialog.SetTitle(localeInfo.PRIVATE_SHOP_INPUT_NAME_DIALOG_TITLE)
		inputDialog.SetMaxLength(32)
		inputDialog.SetAcceptEvent(ui.__mem_func__(self.OpenPrivateShopBuilder))
		inputDialog.SetCancelEvent(ui.__mem_func__(self.ClosePrivateShopInputNameDialog))
		inputDialog.Open()
		self.inputDialog = inputDialog

	def ClosePrivateShopInputNameDialog(self):
		self.inputDialog = None
		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			shop.SetNameDialogOpen(False)
		return True

	def OpenPrivateShopBuilder(self):
		if not self.inputDialog:
			return True

		if not len(self.inputDialog.GetText()):
			return True

		if app.ENABLE_SKILLBOOK_COMB_SYSTEM:
			if self.wndSkillBookCombination.IsShow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.COMB_NOTICE)
				return

		if app.ENABLE_AURA_SYSTEM:
			if self.wndAura and self.wndAura.IsShow():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_OPEN_OTHER_WINDOW)
				return

		self.privateShopBuilder.Open(self.inputDialog.GetText())
		self.ClosePrivateShopInputNameDialog()

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			shop.SetNameDialogOpen(True)

		return True

	def AppearPrivateShop(self, vid, text):
		board = uiPrivateShopBuilder.PrivateShopAdvertisementBoard()
		board.Open(vid, text)
		self.privateShopAdvertisementBoardDict[vid] = board

	def DisappearPrivateShop(self, vid):

		if not vid in self.privateShopAdvertisementBoardDict:
			return

		del self.privateShopAdvertisementBoardDict[vid]
		uiPrivateShopBuilder.DeleteADBoard(vid)

	#####################################################################################
	### Equipment ###

	if app.ENABLE_VIEW_EQUIPMENT_SYSTEM:
		def OpenEquipmentDialog(self, vid):
			if vid in self.equipmentDialogDict:
				self.equipmentDialogDict[vid].Destroy()
				self.CloseEquipmentDialog(vid)
			dlg = uiEquipmentDialog.EquipmentDialog()
			dlg.SetItemToolTip(self.tooltipItem)
			dlg.SetCloseEvent(ui.__mem_func__(self.CloseEquipmentDialog))
			dlg.Open(vid)

			self.equipmentDialogDict[vid] = dlg

		if app.ENABLE_CHANGE_LOOK_SYSTEM:
			def SetEquipmentDialogItem(self, vid, slotIndex, vnum, count, dwChangeLookVnum):
				if not vid in self.equipmentDialogDict:
					return
				self.equipmentDialogDict[vid].SetEquipmentDialogItem(slotIndex, vnum, count, dwChangeLookVnum)
		else:
			def SetEquipmentDialogItem(self, vid, slotIndex, vnum, count):
				if not vid in self.equipmentDialogDict:
					return
				self.equipmentDialogDict[vid].SetEquipmentDialogItem(slotIndex, vnum, count)

		def SetEquipmentDialogSocket(self, vid, slotIndex, socketIndex, value):
			if not vid in self.equipmentDialogDict:
				return
			self.equipmentDialogDict[vid].SetEquipmentDialogSocket(slotIndex, socketIndex, value)

		def SetEquipmentDialogAttr(self, vid, slotIndex, attrIndex, type, value):
			if not vid in self.equipmentDialogDict:
				return
			self.equipmentDialogDict[vid].SetEquipmentDialogAttr(slotIndex, attrIndex, type, value)

		if app.ENABLE_APPLY_RANDOM:
			def SetEquipmentDialogApplyRandom(self, vid, slotIndex, aApplyRandomIndex, type, value):
				if not vid in self.equipmentDialogDict:
					return
				self.equipmentDialogDict[vid].SetEquipmentDialogApplyRandom(slotIndex, aApplyRandomIndex, type, value)

		if app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def SetEquipmentDialogRefineElement(self, vid, slotIndex, applyType, grade, values, bonusValues):
				if not vid in self.equipmentDialogDict:
					return
				self.equipmentDialogDict[vid].SetEquipmentDialogRefineElement(slotIndex, applyType, grade, values, bonusValues)

		def CloseEquipmentDialog(self, vid):
			if not vid in self.equipmentDialogDict:
				return
			del self.equipmentDialogDict[vid]

	#####################################################################################

	#####################################################################################
	### Quest ###
	def __CreatePermanentTasksQuestButton(self):
		btn = uiWhisper.WhisperButton()
		btn.SetUpVisual(localeInfo.GetQuestScrollNormalImageName())
		btn.SetOverVisual(localeInfo.GetQuestScrollHoverImageName())
		btn.SetDownVisual(localeInfo.GetQuestScrollPressedImageName())
		btn.SetToolTipText(u"Trvalé úkoly", -20, 35)
		if localeInfo.IsARABIC():
			btn.ToolTipText.SetHorizontalAlignRight()
		else:
			btn.ToolTipText.SetHorizontalAlignLeft()
		btn.SetEvent(ui.__mem_func__(self.OpenPermanentTasks))
		btn.index = "permanent_tasks"
		btn.name = u"Trvalé úkoly"
		btn.Show()
		self.questButtonList.insert(0, btn)
		self.__ArrangeQuestButton()

	def __CreateDailyTasksQuestButton(self):
		btn = uiWhisper.WhisperButton()
		btn.SetUpVisual(localeInfo.GetQuestScrollNormalImageName())
		btn.SetOverVisual(localeInfo.GetQuestScrollHoverImageName())
		btn.SetDownVisual(localeInfo.GetQuestScrollPressedImageName())
		btn.SetToolTipText(u"Denní úkoly", -20, 35)
		if localeInfo.IsARABIC():
			btn.ToolTipText.SetHorizontalAlignRight()
		else:
			btn.ToolTipText.SetHorizontalAlignLeft()
		btn.SetEvent(ui.__mem_func__(self.OpenDailyTasks))
		btn.index = "daily_tasks"
		btn.name = u"Denní úkoly"
		btn.Show()
		self.questButtonList.insert(1, btn)
		self.__ArrangeQuestButton()

	def BINARY_ClearQuest(self, index):
		btn = self.__FindQuestButton(index)
		if 0 != btn:
			self.__DestroyQuestButton(btn)

	def RecvQuest(self, index, name):
		# QUEST_LETTER_IMAGE
		self.BINARY_RecvQuest(index, name, "file", localeInfo.GetLetterImageName())
		# END_OF_QUEST_LETTER_IMAGE

	def BINARY_RecvQuest(self, index, name, iconType, iconName):
		btn = self.__FindQuestButton(index)
		if 0 != btn:
			self.__DestroyQuestButton(btn)

		btn = uiWhisper.WhisperButton()

		# QUEST_LETTER_IMAGE
		##!! 20061026.levites.퀘스트_이미지_교체
		import item

		if "item" == iconType:
			item.SelectItem(int(iconName))
			buttonImageFileName = item.GetIconImageFileName()
			btn.SetUpVisual(buttonImageFileName)
			btn.SetOverVisual(buttonImageFileName)
			btn.SetDownVisual(buttonImageFileName)
		else:
			btn.SetUpVisual(localeInfo.GetQuestScrollNormalImageName())
			btn.SetOverVisual(localeInfo.GetQuestScrollHoverImageName())
			btn.SetDownVisual(localeInfo.GetQuestScrollPressedImageName())
			if name and name[0] == "*":
				name = name[1:]
			if not localeInfo.IsEUROPE():
				btn.Flash()
		# END_OF_QUEST_LETTER_IMAGE

		if localeInfo.IsARABIC():
			btn.SetToolTipText(name, -20, 35)
			btn.ToolTipText.SetHorizontalAlignRight()
		else:
			btn.SetToolTipText(name, -20, 35)
			btn.ToolTipText.SetHorizontalAlignLeft()

		btn.SetEvent(ui.__mem_func__(self.__StartQuest), btn)
		btn.Show()

		btn.index = index
		btn.name = name

		self.questButtonList.insert(PERSISTENT_QUEST_BUTTON_COUNT, btn)
		self.__ArrangeQuestButton()

		#chat.AppendChat(chat.CHAT_TYPE_NOTICE, localeInfo.QUEST_APPEND)

	if app.ENABLE_QUEST_OPTION:
		def DynamicArrangeQuestBtn(self):
			self.__ArrangeQuestButton()

	def __ArrangeQuestButton(self):
		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()

		##!! 20061026.levites.퀘스트_위치_보정
		if self.wndParty.IsShow():
			xPos = 100 + 30
		else:
			xPos = 20

		if localeInfo.IsARABIC():
			xPos = xPos + 15

		yPos = 170 * screenHeight // 600
		yCount = (screenHeight - 330) // 63

		count = 0
		for btn in self.questButtonList:
			btn.SetPosition(xPos + (int(count // yCount) * 100), yPos + (count % yCount * 63))
			count += 1

			global IsQBHide
			if IsQBHide:
				btn.Hide()
				btn.ForceHideToolTip()
			else:
				btn.Show()
				btn.ShowToolTip()

	def __StartQuest(self, btn):
		event.QuestButtonClick(btn.index)
		self.__DestroyQuestButton(btn)

	def __FindQuestButton(self, index):
		for btn in self.questButtonList:
			if btn.index == index:
				return btn

		return 0

	def __DestroyQuestButton(self, btn):
		btn.Hide()
		btn.ForceHideToolTip()
		btn.SetEvent(0)
		self.questButtonList.remove(btn)
		self.__ArrangeQuestButton()

	def HideAllQuestButton(self):
		for btn in self.questButtonList:
			btn.Hide()
			btn.ForceHideToolTip()

	def ShowAllQuestButton(self):
		if app.ENABLE_KINGDOMS_WAR:
			if self.wndKingdomsWar.IsShow():
				return
		
		for btn in self.questButtonList:
			btn.Show()
			btn.ShowToolTip()

	#####################################################################################

	#####################################################################################
	### Whisper ###

	def __InitWhisper(self):
		#chat.InitWhisper(self)
		from _weakref import proxy
		chat.InitWhisper(proxy(self))

	## 채팅창의 "메시지 보내기"를 눌렀을때 이름 없는 대화창을 여는 함수
	## 이름이 없기 때문에 기존의 WhisperDialogDict 와 별도로 관리된다.
	def OpenWhisperDialogWithoutTarget(self):
		if self.unifiedMessengerRouter.OpenWithoutTarget():
			return
		if not self.dlgWhisperWithoutTarget:
			dlgWhisper = uiWhisper.WhisperDialog(self.MinimizeWhisperDialog, self.CloseWhisperDialog)
			dlgWhisper.BindInterface(self)
			dlgWhisper.LoadDialog()
			dlgWhisper.OpenWithoutTarget(self.RegisterTemporaryWhisperDialog)
			dlgWhisper.SetPosition(self.windowOpenPosition * 30,self.windowOpenPosition * 30)
			dlgWhisper.Show()
			self.dlgWhisperWithoutTarget = dlgWhisper

			self.windowOpenPosition = (self.windowOpenPosition + 1) % 5

		else:
			self.dlgWhisperWithoutTarget.SetTop()
			self.dlgWhisperWithoutTarget.OpenWithoutTarget(self.RegisterTemporaryWhisperDialog)

	## 이름 없는 대화창에서 이름을 결정했을때 WhisperDialogDict에 창을 넣어주는 함수
	def RegisterTemporaryWhisperDialog(self, name):
		if not self.dlgWhisperWithoutTarget:
			return

		btn = self.__FindWhisperButton(name)
		if 0 != btn:
			self.__DestroyWhisperButton(btn)

		elif name in self.whisperDialogDict:
			oldDialog = self.whisperDialogDict[name]
			oldDialog.Destroy()
			del self.whisperDialogDict[name]

		self.whisperDialogDict[name] = self.dlgWhisperWithoutTarget
		self.dlgWhisperWithoutTarget.OpenWithTarget(name)
		self.dlgWhisperWithoutTarget = None
		self.__CheckGameMaster(name)

	def RecieveWhisperDetails(self, name, country):
		if name in self.whisperDialogDict:
			self.whisperDialogDict[name].SetCountryFlag(country)
		else:
			btn = self.__FindWhisperButton(name)
			if btn != 0:
				btn.countryID = country

	## 캐릭터 메뉴의 1:1 대화 하기를 눌렀을때 이름을 가지고 바로 창을 여는 함수
	def OpenWhisperDialog(self, name):
		if self.unifiedMessengerRouter.Open(name):
			return
		if not name in self.whisperDialogDict:
			dlg = self.__MakeWhisperDialog(name)
			dlg.OpenWithTarget(name)
			dlg.chatLine.SetFocus()
			dlg.Show()

			self.__CheckGameMaster(name)
			btn = self.__FindWhisperButton(name)
			if 0 != btn:
				self.__DestroyWhisperButton(btn)

	def OpenWhisperWithMarketItem(self, name, itemReference):
		draft = "[Trh] %s " % itemReference
		if self.unifiedMessengerRouter.OpenWithDraft(name, draft):
			return
		self.OpenWhisperDialog(name)
		dialog = self.whisperDialogDict.get(name)
		if dialog:
			dialog.chatLine.SetText(draft)
			dialog.chatLine.SetFocus()

	## 다른 캐릭터로부터 메세지를 받았을때 일단 버튼만 띄워 두는 함수
	def RecvWhisper(self, name):
		if self.unifiedMessengerRouter.Receive(name):
			return
		self.RecvLegacyWhisper(name)

	def RecvLegacyWhisper(self, name):
		# Whispers that exist only in the native whisper buffer (system/error
		# notices, [SYSTEM]/[Dungeon Info], duel invitations and chat lines the
		# executable could not import) stay in the classic dialog even while
		# Unified Messenger is active; otherwise their text would be invisible.
		# A pending Messenger letter for the same name keeps its own button.
		if not name in self.whisperDialogDict:
			btn = self.__FindWhisperButtonOfKind(name, False)
			if 0 == btn:
				btn = self.__MakeWhisperButton(name)
				btn.Flash()
				app.FlashApplication() #osp. flash application
				chat.AppendChat(chat.CHAT_TYPE_NOTICE, localeInfo.RECEIVE_MESSAGE % (name))
			else:
				btn.Flash()
		elif self.IsGameMasterName(name):
			dlg = self.whisperDialogDict[name]
			dlg.SetGameMasterLook()

	def MakeWhisperButton(self, name):
		self.__MakeWhisperButton(name)

	## 버튼을 눌렀을때 창을 여는 함수
	def ShowWhisperDialog(self, btn):
		try:
			self.__MakeWhisperDialog(btn.name)
			dlgWhisper = self.whisperDialogDict[btn.name]
			dlgWhisper.OpenWithTarget(btn.name)
			dlgWhisper.Show()
			self.__CheckGameMaster(btn.name)
		except:
			import dbg
			dbg.TraceError("interface.ShowWhisperDialog - Failed to find key")

		## 버튼 초기화
		self.__DestroyWhisperButton(btn)

	def ShowUnifiedMessengerNotification(self, key, name):
		name = str(name or "")
		if not name:
			return
		# Never take over a classic whisper letter (e.g. a duel invitation).
		button = self.__FindWhisperButtonOfKind(name, True)
		if 0 == button:
			button = self.__MakeWhisperButton(name)
		if key:
			button.unifiedMessengerKey = key
		elif not hasattr(button, "unifiedMessengerKey"):
			button.unifiedMessengerKey = ""
		button.SetEvent(ui.__mem_func__(
			self.ShowUnifiedMessengerNotificationConversation), button)
		button.Flash()

	def ClearUnifiedMessengerNotifications(self):
		for button in self.whisperButtonList[:]:
			if hasattr(button, "unifiedMessengerKey"):
				button.Hide()
				self.__DestroyWhisperButton(button)

	def ShowUnifiedMessengerNotificationConversation(self, button):
		name = getattr(button, "name", "")
		key = getattr(button, "unifiedMessengerKey", "")
		if self.unifiedMessengerRouter.Open(name, key):
			if button in self.whisperButtonList:
				self.__DestroyWhisperButton(button)
			return
		self.ShowWhisperDialog(button)

	## WhisperDialog 창에서 최소화 명령을 수행했을때 호출되는 함수
	## 창을 최소화 합니다.
	def MinimizeWhisperDialog(self, name):
		if 0 != name:
			self.__MakeWhisperButton(name)

		self.CloseWhisperDialog(name)

	## WhisperDialog 창에서 닫기 명령을 수행했을때 호출되는 함수
	## 창을 지웁니다.
	def CloseWhisperDialog(self, name):
		if 0 == name:
			if self.dlgWhisperWithoutTarget:
				self.dlgWhisperWithoutTarget.Destroy()
				self.dlgWhisperWithoutTarget = None

			return

		try:
			dlgWhisper = self.whisperDialogDict[name]
			dlgWhisper.Destroy()
			del self.whisperDialogDict[name]
		except:
			import dbg
			dbg.TraceError("interface.CloseWhisperDialog - Failed to find key")

	## 버튼의 개수가 바뀌었을때 버튼을 재정렬 하는 함수
	def __ArrangeWhisperButton(self):
		screenWidth = wndMgr.GetScreenWidth()
		screenHeight = wndMgr.GetScreenHeight()

		xPos = screenWidth - 70
		yPos = 170 * screenHeight // 600
		yCount = (screenHeight - 330) // 63
		#yCount = (screenHeight - 285) // 63

		count = 0
		manager = getattr(self, "systemNotifications", None)
		if manager and manager.DockReserved():
			xPos, yPos = manager.Dock()
			xPos += 4  # Existing PM image is 32px; align its center with the 40px bell.
			yCount = max(1, (manager._Screen()[2] - yPos - 40) // 63 + 1)
			count = 1
		yCount = max(1, yCount)
		for button in self.whisperButtonList:

			button.SetPosition(xPos + (int(count//yCount) * -50), yPos + (count%yCount * 63))
			count += 1

	## 이름으로 Whisper 버튼을 찾아 리턴해 주는 함수
	## 버튼은 딕셔너리로 하지 않는 것은 정렬 되어 버려 순서가 유지 되지 않으며
	## 이로 인해 ToolTip들이 다른 버튼들에 의해 가려지기 때문이다.
	def __FindWhisperButtonOfKind(self, name, unified):
		for button in self.whisperButtonList:
			if button.name == name and hasattr(button, "unifiedMessengerKey") == unified:
				return button
		return 0

	def __FindWhisperButton(self, name):
		for button in self.whisperButtonList:
			if button.name == name:
				return button

		return 0

	## 창을 만듭니다.
	def __MakeWhisperDialog(self, name):
		dlgWhisper = uiWhisper.WhisperDialog(self.MinimizeWhisperDialog, self.CloseWhisperDialog)
		dlgWhisper.BindInterface(self)
		dlgWhisper.LoadDialog()
		dlgWhisper.SetPosition(self.windowOpenPosition*30,self.windowOpenPosition*30)
		self.whisperDialogDict[name] = dlgWhisper

		self.windowOpenPosition = (self.windowOpenPosition+1) % 5

		return dlgWhisper

	## 버튼을 만듭니다.
	def __MakeWhisperButton(self, name):
		whisperButton = uiWhisper.WhisperButton()
		if osfInfo.USE_NEW_WHISPER_LETTER_CATEGORY == True:
			if self.IsGameMasterName(name):
				whisperButton.SetUpVisual("d:/ymir work/ui/game/windows/btn_gm_mail_01.tga")
				whisperButton.SetOverVisual("d:/ymir work/ui/game/windows/btn_gm_mail_02.tga")
				whisperButton.SetDownVisual("d:/ymir work/ui/game/windows/btn_gm_mail_02.tga")
			else:
				whisperButton.SetUpVisual("d:/ymir work/ui/game/windows/btn_normal_mail_01.tga")
				whisperButton.SetOverVisual("d:/ymir work/ui/game/windows/btn_normal_mail_02.tga")
				whisperButton.SetDownVisual("d:/ymir work/ui/game/windows/btn_normal_mail_02.tga")
		else:
			whisperButton.SetUpVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
			whisperButton.SetOverVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
			whisperButton.SetDownVisual("d:/ymir work/ui/game/windows/btn_mail_up.sub")
		if self.IsGameMasterName(name):
			whisperButton.SetToolTipTextWithColor(name, 0xffffa200)
		else:
			whisperButton.SetToolTipText(name)
		whisperButton.ToolTipText.SetHorizontalAlignCenter()
		whisperButton.SetEvent(ui.__mem_func__(self.ShowWhisperDialog), whisperButton)
		whisperButton.Show()
		whisperButton.name = name

		self.whisperButtonList.insert(0, whisperButton)
		self.__ArrangeWhisperButton()

		return whisperButton

	def __DestroyWhisperButton(self, button):
		button.SetEvent(0)
		self.whisperButtonList.remove(button)
		self.__ArrangeWhisperButton()

	def HideAllWhisperButton(self):
		for btn in self.whisperButtonList:
			btn.Hide()

	def ShowAllWhisperButton(self):
		for btn in self.whisperButtonList:
			btn.Show()

	def __CheckGameMaster(self, name):
		if not name in self.listGMName:
			return
		if name in self.whisperDialogDict:
			dlg = self.whisperDialogDict[name]
			dlg.SetGameMasterLook()

	def RegisterGameMasterName(self, name):
		if name in self.listGMName:
			return
		self.listGMName[name] = "GM"

	def IsGameMasterName(self, name):
		if name in self.listGMName:
			return True
		else:
			return False

	#####################################################################################

	#####################################################################################
	### Guild Building ###

	def BUILD_OpenWindow(self):
		self.wndGuildBuilding = uiGuild.BuildGuildBuildingWindow()
		self.wndGuildBuilding.Open()
		self.wndGuildBuilding.wnds = self.__HideWindows()
		self.wndGuildBuilding.SetCloseEvent(ui.__mem_func__(self.BUILD_CloseWindow))

	def BUILD_CloseWindow(self):
		self.__ShowWindows(self.wndGuildBuilding.wnds)
		self.wndGuildBuilding = None

	def BUILD_OnUpdate(self):
		if not self.wndGuildBuilding:
			return

		if self.wndGuildBuilding.IsPositioningMode():
			import background
			x, y, z = background.GetPickingPoint()
			self.wndGuildBuilding.SetBuildingPosition(x, y, z)

	def BUILD_OnMouseLeftButtonDown(self):
		if not self.wndGuildBuilding:
			return

		# GUILD_BUILDING
		if self.wndGuildBuilding.IsPositioningMode():
			self.wndGuildBuilding.SettleCurrentPosition()
			return True
		elif self.wndGuildBuilding.IsPreviewMode():
			pass
		else:
			return True
		# END_OF_GUILD_BUILDING
		return False

	def BUILD_OnMouseLeftButtonUp(self):
		if not self.wndGuildBuilding:
			return

		if not self.wndGuildBuilding.IsPreviewMode():
			return True

		return False

	def BULID_EnterGuildArea(self, areaID):
		# GUILD_BUILDING
		mainCharacterName = player.GetMainCharacterName()
		masterName = guild.GetGuildMasterName()

		if mainCharacterName != masterName:
			return

		if areaID != player.GetGuildID():
			return
		# END_OF_GUILD_BUILDING

		self.wndGameButton.ShowBuildButton()

	def BULID_ExitGuildArea(self, areaID):
		self.wndGameButton.HideBuildButton()

	#####################################################################################

	def IsEditLineFocus(self):
		if self.ChatWindow.chatLine.IsFocus():
			return 1

		if self.ChatWindow.chatToLine.IsFocus():
			return 1

		return 0

	def EmptyFunction(self):
		pass

	if app.ENABLE_MINI_GAME_OKEY:
		def MiniGameOkey(self):
			isOpen = osfInfo.RUMI_GAME_EVENT

			if isOpen == True:
				if not self.wndMiniGame:
					self.wndMiniGame = uiMiniGame.MiniGameWindow()

				self.wndMiniGame.MiniGameOkeyEvent(True)
			else:
				if self.wndMiniGame:
					self.wndMiniGame.MiniGameOkeyEvent(False)

	if app.ENABLE_EVENT_MANAGER:
		def OpenGameOkey(self):
			if not self.wndMiniGame:
				self.wndMiniGame = uiMiniGame.MiniGameWindow()
				
			self.wndMiniGame.SpecialMiniGameOkeyEvent(True)
				
			if self.wndMiniGame:
				self.wndMiniGame.SpecialOpenOkeyCard()
				
		def OpenGameCatchKing(self):
			if not self.wndMiniGame:
				self.wndMiniGame = uiMiniGame.MiniGameWindow()

			if self.wndMiniGame:
				self.wndMiniGame.SpecialOpenCatchKing()
	
		def MiniGameOkey(self):
			isOpen = osfInfo.RUMI_GAME_EVENT

			if isOpen == True:
				if not self.wndMiniGame:
					self.wndMiniGame = uiMiniGame.MiniGameWindow()

				self.wndMiniGame.MiniGameOkeyEvent(True)
			else:
				if self.wndMiniGame:
					self.wndMiniGame.MiniGameOkeyEvent(False)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def SetCatchKingEventStatus(self, isEnable):
			if isEnable:
				osfInfo.CATCH_KING_GAME_EVENT = True
			else:
				osfInfo.CATCH_KING_GAME_EVENT = False

		def MiniGameCatchKingEventStart(self, bigScore):
			if self.wndMiniGame:
				self.wndMiniGame.MiniGameCatchKingEventStart(bigScore)

		def MiniGameCatchKingSetHandCard(self, cardNumber):
			if self.wndMiniGame:
				self.wndMiniGame.MiniGameCatchKingSetHandCard(cardNumber)

		def MiniGameCatchKingResultField(self, score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear):
			if self.wndMiniGame:
				self.wndMiniGame.MiniGameCatchKingResultField(score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear)

		def MiniGameCatchKingSetEndCard(self, cardPos, cardNumber):
			if self.wndMiniGame:
				self.wndMiniGame.MiniGameCatchKingSetEndCard(cardPos, cardNumber)

		def MiniGameCatchKingReward(self, rewardCode):
			if self.wndMiniGame:
				self.wndMiniGame.MiniGameCatchKingReward(rewardCode)

	def IntegrationEventBanner(self):
		isOpen = []

		if app.ENABLE_MINI_GAME_OKEY:
			isOpen.append(osfInfo.RUMI_GAME_EVENT)

		if app.ENABLE_MINI_GAME_CATCH_KING:
			isOpen.append(osfInfo.CATCH_KING_GAME_EVENT)

		if True in isOpen:
			if not self.wndMiniGame:
				self.wndMiniGame = uiMiniGame.MiniGameWindow()

				if self.tooltipItem:
					self.wndMiniGame.SetItemToolTip(self.tooltipItem)

			self.wndMiniGame.IntegrationMiniGame(True)
		else:
			if self.wndMiniGame:
				self.wndMiniGame.IntegrationMiniGame(False)

	if app.WJ_ENABLE_TRADABLE_ICON:
		def AttachInvenItemToOtherWindowSlot(self, slotIndex):
			# Used for (ENABLE_MOVE_COSTUME_ATTR, ENABLE_GROWTH_PET_SYSTEM)
			return False

		def MarkUnusableInvenSlotOnTopWnd(self, onTopWnd, InvenSlot):
			if app.WJ_ENABLE_TRADABLE_ICON:
				if onTopWnd == player.ON_TOP_WND_SHOP and self.dlgShop and self.dlgShop.CantSellInvenItem(InvenSlot):
					return True
				elif onTopWnd == player.ON_TOP_WND_SAFEBOX and self.wndSafebox and self.wndSafebox.CantCheckInItem(InvenSlot):
					return True
				elif onTopWnd == player.ON_TOP_WND_PRIVATE_SHOP and self.privateShopBuilder and self.privateShopBuilder.CantTradableItem(InvenSlot):
					return True
				elif onTopWnd == player.ON_TOP_WND_EXCHANGE and self.dlgExchange and self.dlgExchange.CantTradableItem(InvenSlot):
					return True
			if app.ENABLE_GROWTH_PET_SYSTEM:
				if onTopWnd == player.ON_TOP_WND_PET_FEED and self.wndPetInfoWindow and self.wndPetInfoWindow.CantFeedItem(InvenSlot):
					return True
					
				if onTopWnd == player.ON_TOP_WND_PET_ATTR_CHANGE and self.wndPetInfoWindow and self.wndPetInfoWindow.CantAttrChangeItem(InvenSlot):
					return True
					
				if onTopWnd == player.ON_TOP_WND_PET_PRIMIUM_FEEDSTUFF and self.wndPetInfoWindow and self.wndPetInfoWindow.CantPremiumFeedItem(InvenSlot):
					return True

			if app.ENABLE_ACCE_COSTUME_SYSTEM:
				if onTopWnd == player.ON_TOP_WND_ACCE_COMBINE and self.wndAcceCombine and self.wndAcceCombine.CantTradableItem(InvenSlot):
					return True
				elif onTopWnd == player.ON_TOP_WND_ACCE_ABSORB and self.wndAcceAbsorption and self.wndAcceAbsorption.CantTradableItem(InvenSlot):
					return True

			if app.ENABLE_CHANGE_LOOK_SYSTEM:
				if onTopWnd == player.ON_TOP_WND_CHANGE_LOOK and self.wndChangeLook and self.wndChangeLook.CantTradableItem(InvenSlot):
					return True
					
			if app.ENABLE_AURA_SYSTEM:
				auraOnTopWnd = [player.ON_TOP_WND_AURA_ABSORB, player.ON_TOP_WND_AURA_REFINE, player.ON_TOP_WND_AURA_EVOLVE]
				if onTopWnd in auraOnTopWnd and self.wndAura and self.wndAura.CantUseItem(InvenSlot):
					return True

			if app.ENABLE_ATTR_6TH_7TH:
				if onTopWnd == player.ON_TOP_WND_ATTR67 and self.wndAttr67Add and self.wndAttr67Add.CantAttachToAttrSlot(InvenSlot):
					return True

			if inventoryshortcutpolicy.IsMultipleSelectEnabled(app.ENABLE_MULTIPLE_SELECT):
				if onTopWnd == player.ON_TOP_WND_MULTIPLE_SELECT and self.wndInventory and self.wndInventory.wndMultiple:
					if self.wndInventory.wndMultiple.IsTypeSell() and not osfInfo.CanSellItem(InvenSlot):
						return True
					if self.wndInventory.wndMultiple.IsTypeDestroy() and not osfInfo.CanDestroyItem(InvenSlot):
						return True

			return False

		def SetOnTopWindow(self, onTopWnd):
			self.OnTopWindow = onTopWnd

		def GetOnTopWindow(self):
			return self.OnTopWindow

		def RefreshMarkInventoryBag(self):
			if self.wndInventory:
				try:
					if self.wndInventory.IsShow() and hasattr(self.wndInventory, "RefreshBagSlotWindow"):
						self.wndInventory.RefreshBagSlotWindow()
				except AttributeError:
					pass

			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if self.wndSpecialInventory:
					try:
						if self.wndSpecialInventory.IsShow() and hasattr(self.wndSpecialInventory, "RefreshBagSlotWindow"):
							self.wndSpecialInventory.RefreshBagSlotWindow()
					except AttributeError:
						pass

	if app.ENABLE_HIDE_COSTUME_SYSTEM:
		def RefreshVisibleCostume(self):
			self.wndInventory.RefreshVisibleCostume()
			if self.wndCostumeInventory:
				self.wndCostumeInventory.RefreshVisibleCostume()

	if app.ENABLE_MOVE_CHANNEL:
		def RefreshServerInfo(self):
			if self.wndMiniMap:
				self.wndMiniMap.RefreshServerInfo()

	if app.ENABLE_EXPRESSING_EMOTION:
		def ClearSpecialEmotions(self):
			if self.wndCharacter:
				self.wndCharacter.ClearSpecialEmotions()

		def RegisterSpecialEmotions(self, emotionIdx, leftTime):
			if self.wndCharacter:
				self.wndCharacter.RegisterSpecialEmotions(emotionIdx, leftTime)

	if app.ENABLE_ITEMSHOP:
		def MakeItemShopWindow(self):
			if self.wndItemShop == None:
				self.wndItemShop = uiItemShop.ItemShopWindow()
		def OpenItemShopWindow(self):
			self.MakeItemShopWindow()
			if self.wndItemShop.IsShow():
				self.wndItemShop.Close()
			else:
				self.wndItemShop.Open()
		def OpenItemShopMainWindow(self):
			self.MakeItemShopWindow()
			self.wndItemShop.Open()
			self.wndItemShop.LoadFirstOpening()
		def ItemShopHideLoading(self):
			self.MakeItemShopWindow()
			self.wndItemShop.Open()
			self.wndItemShop.CloseLoading()
		def ItemShopClosed(self):
			if self.wndItemShop:
				self.wndItemShop.OnItemShopClosed()
		def ItemShopPurchasesWindow(self):
			self.MakeItemShopWindow()
			self.wndItemShop.Open()
			self.wndItemShop.OpenPurchasesWindow()
		def ItemShopSetDragonCoin(self,dragonCoin):
			self.itemShopDragonCoin = max(0, int(dragonCoin))
			if self.wndInventory:
				self.wndInventory.SetDragonCoin(self.itemShopDragonCoin)
			self.MakeItemShopWindow()
			self.wndItemShop.SetDragonCoin(self.itemShopDragonCoin)

	if app.ENABLE_RENDER_TARGET_PREVIEW:
		def OpenRenderTargetWindow(self):
			if False == player.IsObserverMode():
				if False == self.wndRenderTargetView.IsShow():
					self.wndRenderTargetView.Show()
					self.wndRenderTargetView.SetTop()
				else:
					self.wndRenderTargetView.SetTop()

	if app.ENABLE_SKILL_SELECT_GUI:
		def OPEN_SKILL_SELECT(self):
			self.wndSkillSelect.Open()

	if app.ENABLE_EVENT_MANAGER:
		def MakeEventIcon(self):
			if self.wndEventIcon == None:
				self.wndEventIcon = uiEventCalendar.MovableImage()
				self.wndEventIcon.Show()
		def MakeEventCalendar(self):
			if self.wndEventManager == None:
				self.wndEventManager = uiEventCalendar.EventCalendarWindow()
		def OpenEventCalendar(self):
			self.MakeEventCalendar()
			if self.wndEventManager.IsShow():
				self.wndEventManager.Close()
			else:
				self.wndEventManager.Open()
		def RefreshEventStatus(self, eventID, eventStatus, eventendTime, eventEndTimeText):
			uiEventCalendar.SetEventStatus(eventID, eventStatus, eventendTime+app.GetGlobalTimeStamp(), eventEndTimeText)
			self.RefreshEventManager()
		def ClearEventManager(self):
			uiEventCalendar.server_event_data={}
		def RefreshEventManager(self):
			if self.wndEventManager:
				self.wndEventManager.Refresh()
			if self.wndEventIcon:
				self.wndEventIcon.Refresh()
		def AppendEvent(self, dayIndex, eventID, eventIndex, startTime, endTime, empireFlag, channelFlag, value0, value1, value2, value3, value4, value5, value6, value7, startRealTime, endRealTime, isAlreadyStart):
			self.MakeEventCalendar()
			self.MakeEventIcon()
			if startRealTime != 0:
				startRealTime += app.GetGlobalTimeStamp()
			if endRealTime != 0:
				endRealTime += app.GetGlobalTimeStamp()
			uiEventCalendar.SetServerData(dayIndex, eventID, eventIndex, startTime, endTime, empireFlag, channelFlag, value0, value1, value2, value3, value4, value5, value6, value7, startRealTime, endRealTime, isAlreadyStart)

	if app.ENABLE_OFFLINE_SHOP:
		def OpenOfflineShopBuilder(self, openingTime, openingGold):
			import dbg
			if not self.wndOfflineShopBuilder:
				self.wndOfflineShopBuilder = uiOfflineShop.BuilderWindow()
				self.wndOfflineShopBuilder.BindInterfaceClass(self)

			self.wndOfflineShopBuilder.Open(openingTime, openingGold)
		
		def CloseOfflineShopBuilder(self):
			if not self.wndOfflineShopBuilder:
				return
			
			self.wndOfflineShopBuilder.Destroy()

		def CloseShopBuildWindow(self):
			if self.wndOfflineShopBuilder and self.wndOfflineShopBuilder.IsShow():
				self.wndOfflineShopBuilder.Close()

		def IsBuildingOfflineShop(self):
			return self.wndOfflineShopBuilder and self.wndOfflineShopBuilder.IsShow()
		
		def OSB_OnMouseLeftButtonDown(self):
			if not self.wndOfflineShopBuilder:
				return False
			
			return self.wndOfflineShopBuilder.IsPositioningMode()
		
		def OSB_OnMouseLeftButtonUp(self):
			if not self.wndOfflineShopBuilder:
				return False
			
			return self.wndOfflineShopBuilder.POSITIONING_OnMouseLeftButtonUp()

		def OpenSellHistoryWindow(self):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			if self.wndSellHistory.IsShow():
				self.wndSellHistory.Close()
			else:
				self.wndSellHistory.Open()
				
		def ClearSellHistoryWindow(self):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			self.wndSellHistory.ClearItems()
			
		def AddToSellHistory(self, vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement=None):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			self.wndSellHistory.AddSaveItem(vnum, count, price, buyer, when, metinSlot, attrSlot, applyRandom, transmutation, refineElement)
			
		def RefreshSellHistoryWindow(self):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			self.wndSellHistory.RefreshList()
			
		def RevertPageSellLog(self):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			self.wndSellHistory.RevertPage()
			
		def UpdateSellLog(self):
			if not self.wndSellHistory:
				self.wndSellHistory = uiSellHistory.SellLogWindow(self)

			self.wndSellHistory.UpdateNewItems()

	if app.ENABLE_DISCORD_STUFF:
		def OpenWhisperWithMessage(self, name):
			self.OpenWhisperDialog(name)

	def CheckWhisperIsOpen(self, name):
		unified = self.unifiedMessengerRouter.IsOpen(name)
		if unified is not None:
			return unified
		try:
			if isinstance(self.whisperDialogDict, dict):
				if name in self.whisperDialogDict:
					return self.whisperDialogDict[name].IsShow()
		except:
			pass
		return False

	if app.ENABLE_MAINTENANCE_SYSTEM:
		def ShowMaintenanceSign(self, timeLeft, duration):
			if self.wndMaintenance:
				self.wndMaintenance.Open(timeLeft, duration)

		def HideMaintenanceSign(self):
			if self.wndMaintenance:
				self.wndMaintenance.Close()

	if app.ENABLE_SHOW_CHEST_DROP:
		def AddChestDropInfo(self, chestVnum, pageIndex, slotIndex, itemVnum, itemCount):
			self.dlgChestDrop.AddChestDropItem(int(chestVnum), int(pageIndex), int(slotIndex), int(itemVnum), int(itemCount))
			
		def RefreshChestDropInfo(self, chestVnum):
			self.dlgChestDrop.RefreshItems(chestVnum)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def PetHatchingWindowCommand(self, command):
			if self.wndPetInfoWindow:
				if self.wndPetInfoWindow.wndPetHatching:
					self.wndPetInfoWindow.wndPetHatching.PetHatchingWindowCommand(command)
		
		def PetNameChangeWindowCommand(self, command):
			if self.wndPetInfoWindow:
				if self.wndPetInfoWindow.wndPetNameChange:
					self.wndPetInfoWindow.wndPetNameChange.PetNameChangeWindowCommand(command)

		def PetSkillUpgradeDlgOpen(self, slot, index, gold):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.OpenPetSkillUpGradeQuestionDialog(slot, index, gold)

		def PetFlashEvent(self, index):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetFlashEvent(index)

		def PetInfoBindAffectShower(self, affect_shower):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetInfoBindAffectShower(affect_shower)

		def PetAffectShowerRefresh(self):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetAffectShowerRefresh()

		def PetFeedReuslt(self, result):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetFeedReuslt(result)
				
		def PetAttrDetermineResult(self, byType):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetAttrDetermineResult(byType)
			
		def PetAttrChangeResult(self, slotIndex, byType):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetAttrChangeResult(slotIndex, byType)
				
		def PetReviveResult(self, result):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetReviveResult(result)
				
		def PetWindowTypeResult(self, result):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetWindowTypeResult(result)

		def PetHeartUpdate(self):
			if self.wndPetInfoWindow:
				self.wndPetInfoWindow.PetHeartUpdate()

		def PetGrowthPreview(self, petID, hpMin, hpMax, defMin, defMax, spMin, spMax):
			if self.wndPetInfoWindow and self.wndPetInfoWindow.compact:
				self.wndPetInfoWindow.compact.SetGrowthPreview(
					petID, hpMin, hpMax, defMin, defMax, spMin, spMax)

	if app.ENABLE_PLAYER_RANKING:
		def ShowRankGlobal(self):
			if False == player.IsObserverMode():
				if self.wndRankInfo.IsShow():
					self.wndRankInfo.Close()
				elif not featureavailability.IsAvailable(featureavailability.RANKINGS):
					featureavailability.NotifyRefused(featureavailability.RANKINGS)
				else:
					self.wndRankInfo.Show()
					
		def AppendInfoRankGlobal(self, my_pos, mode, pos, name, value, empire):
			self.wndRankInfo.AppendInfo(my_pos, mode, pos, name, value, empire)
			
		def SetRankingResetInfo(self, iTime, iInterval):
			self.wndRankInfo.SetResetTime(iTime, iInterval)
			
		def SetRankingReward(self, vnum1, count1, vnum2, count2, vnum3, count3):
			self.wndRankInfo.SetRewardItem(0, vnum1, count1)
			self.wndRankInfo.SetRewardItem(1, vnum2, count2)
			self.wndRankInfo.SetRewardItem(2, vnum3, count3)

	if app.ENABLE_AURA_SYSTEM:
		def AuraWindowOpen(self, type):
			if self.wndAura.IsShow():
				return

			if self.inputDialog or self.privateShopBuilder.IsShow():# or shop.GetNameDialogOpen():
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_OPEN_PRIVATE_SHOP)
				return

			if self.dlgRefineNew:
				if self.dlgRefineNew.IsShow():
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.ACCE_NOT_OPEN_REFINE)
					return

			self.wndAura.Open(type)

			if not self.wndInventory.IsShow():
				self.wndInventory.Show()

		def AuraWindowClose(self):
			if not self.wndAura.IsShow():
				return

			self.wndAura.CloseWindow()

	if app.ENABLE_CUBE_RENEWAL:
		def ToggleDewCraftWindow(self):
			window = self.wndCubeRenewal
			if window.IsShow():
				was_dew = window.IsDewCatalogue()
				window.Close()
				if was_dew:
					return
			# The server supplies the dedicated catalogue and authorizes opening.
			net.SendChatPacket("/cube dews")

		def BINARY_CUBE_RENEWAL_OPEN(self):
			window = self.wndCubeRenewal
			if window.IsDewCatalogue() and self.wndInventory:
				x, y = self.wndInventory.GetGlobalPosition()
				window.SetPosition(max(0, min(x-window.GetWidth()-8, wndMgr.GetScreenWidth()-window.GetWidth())),
					max(0, min(y, wndMgr.GetScreenHeight()-window.GetHeight())))
			window.Show()

	if app.ENABLE_REWARD_SYSTEM:
		def MakeRewardWindow(self):
			if self.wndReward == None:
				self.wndReward = uiReward.RewardWindow()
		def SetRewardPlayers(self, data):
			self.MakeRewardWindow()
			self.wndReward.SetRewardPlayers(data)
		def OpenRewardWindow(self):
			self.MakeRewardWindow()
			if self.wndReward.IsShow():
				self.wndReward.Close()
			else:
				self.wndReward.Open()

	if app.ENABLE_LOADING_PERFORMANCE:
		def PrepareInstantWarp(self):
			if self.wndMiniMap and self.wndMiniMap.IsShowingAtlas():
				self.wndMiniMap.ToggleAtlasWindow()

			if self.dlgSystem:
				self.dlgSystem.Close()
				self.dlgSystem.Destroy()

			self.HideAllQuestButton()
			self.HideAllWhisperButton()

			self.HideAllWindows()

		def OpenWarpShowerWindow(self):
			if self.wndMiniMap and self.wndMiniMap.IsShowingAtlas():
				self.wndMiniMap.ToggleAtlasWindow()

			if self.dlgSystem:
				self.dlgSystem.Close()
				self.dlgSystem.Destroy()

			self.HideAllQuestButton()
			self.HideAllWhisperButton()

			self.HideAllWindows()

			self.wndWarpShower.Open()

		def CloseWarpShowerWindow(self):
			if self.wndWarpShower:
				self.wndWarpShower.Close()

	if app.ENABLE_FAST_READ_STONE_AND_SKILLBOOK:
		def OpenSkillUpgradeWindow(self, upgraderItem):
			if player.IsObserverMode():
				return

			self.wndUpgradeSkill.SetUpgradeItem(upgraderItem)
			self.wndUpgradeSkill.Show()
			self.wndUpgradeSkill.SetTop()


	if app.ENABLE_KINGDOMS_WAR:
		def ActKingdomsWar(self, act, score1, score2, score3, limitKills, deads, limiDeads, timeRemained):
			if self.wndKingdomsWar:
				if act == 1:
					self.wndKingdomsWar.ShowWindow(score1, score2, score3, limitKills, deads, limiDeads, timeRemained)
					global IsQBHide
					IsQBHide = 1
					for btn in self.questButtonList:
						btn.Hide()
						btn.ForceHideToolTip()
				elif act == 2:
					self.wndKingdomsWar.RefreshScore(score1, score2, score3, limitKills)
				elif act == 3:
					self.wndKingdomsWar.RefreshDeads(deads, limiDeads)

	if app.ENABLE_KILL_BAR_SYSTEM:
		def AddKillInfo(self, killer, victim, killer_race, victim_race, weapon_type):
			self.wndMiniMap.AddKillInfo(killer, victim, killer_race, victim_race, weapon_type)

	if app.ENABLE_WHEEL_OF_FORTUNE:
		def MakeWheelofFortune(self):
			if self.wndWheelofFortune == None:
				self.wndWheelofFortune = uiWheelofFortune.WheelofFortune()
		def OpenWheelofFortune(self):
			self.MakeWheelofFortune()
			if self.wndWheelofFortune.IsShow():
				self.wndWheelofFortune.Close()
			else:
				self.wndWheelofFortune.Open()
		def SetItemData(self, cmd):
			self.MakeWheelofFortune()
			self.wndWheelofFortune.SetItemData(str(cmd))
		def OnSetWheel(self, giftIndex):
			self.MakeWheelofFortune()
			self.wndWheelofFortune.OnSetWheel(int(giftIndex))
		def GetGiftData(self, itemVnum, itemCount):
			self.MakeWheelofFortune()
			self.wndWheelofFortune.GetGiftData(int(itemVnum), int(itemCount))

	if app.ENABLE_EXCHANGE_LOG:
		def MakeExchangeLogWindow(self):
			if self.wndExchangeLog == None:
				self.wndExchangeLog = uiExchangeLog.ExchangeLog()
		def OpenExchangeLog(self):
			self.MakeExchangeLogWindow()
			if self.wndExchangeLog.IsShow():
				self.wndExchangeLog.Close()
			else:
				self.wndExchangeLog.Open()
		def ExchangeLogClear(self, playerCode):
			if self.wndExchangeLog:
				self.wndExchangeLog.Clear(playerCode)
		def ExchangeLogRefresh(self, isLogItemRefresh):
			if self.wndExchangeLog:
				if isLogItemRefresh:
					self.wndExchangeLog.RefreshItems(isLogItemRefresh)
				else:
					self.wndExchangeLog.Refresh()
		def ExchangeLogAppend(self, logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date):
			if self.wndExchangeLog:
				self.wndExchangeLog.ExchangeLogAppend(logID, ownerName, ownerGold, ownerIP, targetName, targetGold, targetIP, date)
		if app.ENABLE_APPLY_RANDOM and app.ENABLE_REFINE_ELEMENT_SYSTEM:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, refineElement, isOwnerItem):
				if self.wndExchangeLog:
					self.wndExchangeLog.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, refineElement, isOwnerItem)
		elif app.ENABLE_APPLY_RANDOM:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, isOwnerItem):
				if self.wndExchangeLog:
					self.wndExchangeLog.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, applyRandomType, applyRandomValue, None, isOwnerItem)
		else:
			def ExchangeLogItemAppend(self, logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, isOwnerItem):
				if self.wndExchangeLog:
					self.wndExchangeLog.ExchangeLogItemAppend(logID, itemPos, itemVnum, itemCount, metinSlot, attrType, attrValue, [], [], None, isOwnerItem)


	if app.ENABLE_SCROLL_ATLAS:
		def __MakeScroolWindow(self):
			self.wndScrollWarp = uiScroll.ScrollWindow()

	if app.ENABLE_SHOP_SEARCH:
		def _OpenLegacyShopSearchWindow(self):
			if not self.wndShopSearch:
				self.wndShopSearch = uishopsearch.ShopSearchWindow(self)

			if self.wndShopSearch.IsShow():
				self.wndShopSearch.Close()
			else:
				self.wndShopSearch.Open()
	
		def ShopSearch_RecvResult(self):
			if not self.wndShopSearch:
				self.wndShopSearch = uishopsearch.ShopSearchWindow(self)
	
			self.wndShopSearch.RefreshResult()
	
		def ShopSearch_RecvBuyDone(self, result):
			if self.wndShopSearch:
				self.wndShopSearch.Refresh()
				self.wndShopSearch.ShowBuyResult(result)
	
		def ShopSearch_RecvOwnerMessage(self, ownerName):
			if ownerName:
				self.OpenWhisperDialog(ownerName)
	
		def ShopSearch_RecvSoldInfo(self, hasResults):
			if self.wndShopSearch:
				self.wndShopSearch.ShowSoldInfoResult(hasResults)

	if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
		def OpenVirtualMarketWindow(self):
			if not self.wndVirtualMarket:
				self.wndVirtualMarket = uivirtualmarket.VirtualMarketWindow(self)
			if self.wndVirtualMarket.IsShow():
				self.wndVirtualMarket.Close()
			else:
				self.wndVirtualMarket.Open()

		def OpenVirtualMarketForSeller(self, sellerName):
			sellerName = str(sellerName).strip()
			if not sellerName:
				return False
			if not self.wndVirtualMarket:
				self.wndVirtualMarket = uivirtualmarket.VirtualMarketWindow(self)
			opener = getattr(self.wndVirtualMarket, "OpenSeller", None)
			if not opener:
				return False
			return bool(opener(sellerName))

		def SearchVirtualMarketInventoryItem(self, vnum):
			if not self.wndVirtualMarket:
				self.wndVirtualMarket = uivirtualmarket.VirtualMarketWindow(self)
			if not self.wndVirtualMarket.IsShow():
				# Only the exact search below may use the per-player search slot.
				self.wndVirtualMarket.Open(loadMarket=False)
			else:
				self.wndVirtualMarket.SetTop()
			return self.wndVirtualMarket.SearchExactVnum(vnum)

		def VirtualMarketSearchResult(self, token, status, appended, hasMore):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnSearchResult(token, status, appended, hasMore)

		def VirtualMarketSellerSuggestionsResult(self, token, status):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnSellerSuggestionsResult(token, status)

		def VirtualMarketOwnerShopResult(self, token, status):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnOwnerShopResult(token, status)

		def VirtualMarketOwnerListingsResult(self, token, status, appended, hasMore):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnOwnerListingsResult(token, status, appended, hasMore)

		def VirtualMarketSellerReturnsResult(self, token, status, appended, hasMore):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnSellerReturnsResult(token, status, appended, hasMore)

		def VirtualMarketBuyerDeliveriesResult(self, token, status, appended, hasMore):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnBuyerDeliveriesResult(token, status, appended, hasMore)

		def VirtualMarketShopCommandResult(self, token, status, command, result, replayed):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnShopCommandResult(token, status, command, result, replayed)

		def VirtualMarketListingCreateResult(self, token, status, result, replayed):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnListingCreateResult(token, status, result, replayed)

		def VirtualMarketPricePreferenceResult(self, token, status, vnum, found,
				totalPrice, itemCount):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnPricePreferenceResult(
					token, status, vnum, found, totalPrice, itemCount)

		def VirtualMarketListingMoveResult(self, token, status, result, replayed):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnListingMoveResult(token, status, result, replayed)

		def VirtualMarketListingMutationResult(self, token, status, mutation, result,
				replayed, listingId, price):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnListingMutationResult(
					token, status, mutation, result, replayed, listingId, price)

		def VirtualMarketItemClaimResult(self, token, status, source, result, replayed):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnItemClaimResult(token, status, source, result, replayed)

		def VirtualMarketPurchaseResult(self, token, status, result, replayed, state):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnPurchaseResult(token, status, result, replayed, state)

		def VirtualMarketBatchPurchaseResult(self, token, status, result, replayed, state, itemCount):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnBatchPurchaseResult(token, status, result, replayed, state, itemCount)

		def VirtualMarketSellerWithdrawalResult(self, token, status, result, replayed):
			if self.wndVirtualMarket:
				self.wndVirtualMarket.OnSellerWithdrawalResult(token, status, result, replayed)

	def OpenShopSearchWindow(self):
		"""Compatibility entry point for older content callers.

		The supported client always routes this historical name to the virtual
		market.  The legacy window is reachable only when this content is rolled
		out ahead of an executable that does not export ENABLE_VIRTUAL_MARKET.
		"""
		if getattr(app, "ENABLE_VIRTUAL_MARKET", 0):
			self.OpenVirtualMarketWindow()
			return
		if app.ENABLE_SHOP_SEARCH:
			self._OpenLegacyShopSearchWindow()

	if app.ENABLE_DESTROY_ITEM_RESTORE:
		def MakeSaveItem(self):
			if self.wndSaveItem == None:
				self.wndSaveItem = uiGetBackItem.SaveWindow()
				
		def OpenItemSaveWindow(self):
			self.MakeSaveItem()
			if self.wndSaveItem.IsShow():
				self.wndSaveItem.Hide()
			else:
				self.wndSaveItem.Open()
				
		def LoadSaveItemGUI(self):
			self.MakeSaveItem()
			self.wndSaveItem.LoadSaveItemGUI()
			
		def AddSaveItem(self, index):
			self.MakeSaveItem()
			self.wndSaveItem.AddSaveItem(index)
			
		def RemoveSaveItem(self, index):
			self.MakeSaveItem()
			self.wndSaveItem.RemoveSaveItem(index)
			
		def WriteEmptyText(self):
			self.MakeSaveItem()
			self.wndSaveItem.WriteEmptyText()
			
		def RefreshSavedItemsWindow(self):
			self.MakeSaveItem()
			self.wndSaveItem.RefreshList()
			
		def ClearSavedItemsWindow(self):
			self.MakeSaveItem()
			self.wndSaveItem.ClearItems()
			
		def SetSavedItemsPage(self, curPage, maxPage):
			self.MakeSaveItem()
			self.wndSaveItem.SetPage(curPage, maxPage)
			
		def AddToSavedItems(self, time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refine_element=None):
			self.MakeSaveItem()
			self.wndSaveItem.AddSaveItem(time, item_id, vnum, count, yang, fragments, metinSlot, attrSlot, applyRandom, transmutation, soulbind, refine_element)

	if app.ENABLE_DSS_ACTIVE_EFFECT:
		def UseDSSButtonEffect(self, enable):
			if self.wndInventory:
				self.wndInventory.UseDSSButtonEffect(enable)

	if app.ENABLE_DUNGEON_INFO:
		def _DungeonBossDropWindow(self):
			atlas = self.wndTeleportAtlas
			page = atlas.dungeonPage if atlas else None
			return page.dropWindow if page else None
		def DungeonBossDropsBegin(self, bossVnum, requestId):
			window = self._DungeonBossDropWindow()
			if window:
				window.OnServerBegin(bossVnum, requestId)
		def DungeonBossDropsItem(self, bossVnum, requestId, itemVnum, count):
			window = self._DungeonBossDropWindow()
			if window:
				window.OnServerItem(bossVnum, requestId, itemVnum, count)
		def DungeonBossDropsEnd(self, bossVnum, requestId):
			window = self._DungeonBossDropWindow()
			if window:
				window.OnServerEnd(bossVnum, requestId)
		def DungeonInfoQuestIdx(self, questIdx):
			osfInfo.dungeonInfoQuestIdx = int(questIdx)
		def DungeonInfoQuestCMD(self):
			net.SendQuestInputStringPacket(osfInfo.dungeonInfoCMD)
			osfInfo.dungeonInfoCMD = ""
		def ToggleDungeonInfo(self):
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.ToggleDungeons()
		def OpenDungeonInfo(self):
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.OpenDungeons()
		def RefreshDungeons(self):
			atlas = getattr(self, "wndTeleportAtlas", None)
			if atlas:
				atlas.RefreshDungeons()
		def DungeonInfoCooldown(self, clean, data):
			if not hasattr(self, "countdownKnownDungeons"):
				self.countdownKnownDungeons = set()
			if int(clean):
				self.countdownKnownDungeons.clear()
			dungeonData = uiDungeonTrack.dungeonData
			if int(clean):
				for mobIdx, dungeonInfo in dungeonData.items():
					dungeonInfo["server_cooldown"] = 0
					dungeonInfo["server_completed"] = 0
					dungeonInfo["server_fastest"] = 0
					dungeonInfo["server_damage"] = 0
					dungeonInfo["whisper_info"] = False
			if data != "" and data != "-":
				dungeonList = data[:len(data)-1].split("#")
				for dungeonInfo in dungeonList:
					dungeonSplitData = dungeonInfo.split("|")
					if len(dungeonSplitData) == 5:
						bossIdx = int(dungeonSplitData[0])
						if bossIdx in dungeonData:
							if dungeonData[bossIdx]["server_cooldown"] != app.GetGlobalTimeStamp() + int(dungeonSplitData[1]):
								dungeonData[bossIdx]["whisper_info"] = False
							dungeonData[bossIdx]["server_cooldown"] = 0 if int(dungeonSplitData[1]) <= 0 else app.GetGlobalTimeStamp() + int(dungeonSplitData[1])
							dungeonData[bossIdx]["server_completed"] = int(dungeonSplitData[2])
							dungeonData[bossIdx]["server_fastest"] = int(dungeonSplitData[3])
							dungeonData[bossIdx]["server_damage"] = int(dungeonSplitData[4])
							self.countdownKnownDungeons.add(bossIdx)
			if self.wndDungeonManager == None:
				self.wndDungeonManager = uiDungeonTrack.DungeonManager()
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.RefreshDungeons()
		def LoadServerData(self, mobIdx, rankIdx, cmd):
			if self.wndTeleportAtlas:
				self.wndTeleportAtlas.LoadDungeonServerData(int(mobIdx), int(rankIdx), cmd)
			if self.wndDungeonTrack != None:
				self.wndDungeonTrack.LoadServerData(int(mobIdx), int(rankIdx), cmd)

	def ClickEquipmentButton(self):
		if self.wndInventory:
			self.wndInventory.SetEquipmentPage(0)

	def ClickCostumeButton(self):
		self.OpenCostumeWindow()

	if osfInfo.OPEN_SAFEBOX_MALL_IN_SPECIAL_INV:
		def CloseLoadSafeboxEvent(self):
			if not self.wndSpecialInventory:
				return
			self.wndSpecialInventory.CloseLoadSafeboxEvent()

		def CloseLoadMallEvent(self):
			if not self.wndSpecialInventory:
				return
			self.wndSpecialInventory.CloseLoadMallEvent()

	def OpenCaptchaV4(self, status, attemptsRemaining, sessionId, generation,
        deadlineAt, retryAt, pixels, originX, originY, heldPixels):
		if CAPTCHA_WINDOW_ENABLED and getattr(app, "ENABLE_CAPTCHA_V4", 0):
			if not isinstance(self.wndCaptchaNew, uiCaptchaNew.CaptchaUncoverWindow):
				if self.wndCaptchaNew:
					self.wndCaptchaNew.Destroy()
				self.wndCaptchaNew = uiCaptchaNew.CaptchaUncoverWindow()
			self.wndCaptchaNew.OpenChallenge(status, attemptsRemaining, sessionId,
				generation, deadlineAt, retryAt, pixels, originX, originY, heldPixels)

	def SetCaptchaV4Stage(self, sessionId, generation, stage):
		if (CAPTCHA_WINDOW_ENABLED and getattr(app, "ENABLE_CAPTCHA_V4", 0) and
			isinstance(self.wndCaptchaNew, uiCaptchaNew.CaptchaUncoverWindow)):
			self.wndCaptchaNew.SetStage(sessionId, generation, stage)

	def OpenCaptchaV3(self, status, attemptsRemaining, sessionId, generation,
		deadlineAt, retryAt, pixels):
		if CAPTCHA_WINDOW_ENABLED and self.wndCaptchaNew:
			self.wndCaptchaNew.OpenChallenge(status, attemptsRemaining, sessionId,
				generation, deadlineAt, retryAt, pixels)


	if app.ENABLE_DUNGEON_TIME_WINDOW:
		def OpenDungeonTimeWindow(self, mapIndex, remainingTime):
			# Baroness keeps its server deadline without the legacy minimap card.
			if mapIndex == 217:
				self.wndDungeonTime.Hide()
				return
			if False == self.wndDungeonTime.IsShow():
				self.wndDungeonTime.Show(mapIndex, remainingTime)
			else:
				self.wndDungeonTime.Refresh(mapIndex, remainingTime)
				
		def HideDungeonTimeWindow(self):
			if self.wndDungeonTime.IsShow():
				self.wndDungeonTime.Hide()

	if app.ENABLE_BUFF_SYSTEM:
		def OpenSupportGui(self, onlyOpen = False):
			if self.wndSupportPG.IsShow():
				if onlyOpen:
					self.wndSupportPG.SetTop()
				else:
					self.wndSupportPG.Close()
			else:
				self.wndSupportPG.Show()
				self.wndSupportPG.SetTop()
				
		def OpenSupportUpgrade(self, skillID):
			self.wndSupportUpgrade.SetSkill(skillID)
			
			if False == self.wndSupportUpgrade.IsShow():
				self.wndSupportUpgrade.Show()
				self.wndSupportUpgrade.SetTop()
			else:
				# self.wndSupportUpgrade.Refresh()
				self.wndSupportUpgrade.SetTop()
				
		def SetSupportName(self, name):
			self.wndSupportPG.SetName(name)
			
		def SetSupportWeapon(self, weapon):
			self.wndSupportPG.SetWeapon(weapon)
			osfInfo.SUPPORT_WEAPON = int(weapon)
				
		def SetSupportArmor(self, armor):
			self.wndSupportPG.SetArmor(armor)
			osfInfo.SUPPORT_ARMOR = int(armor)
			
		def SetSupportHair(self, hair):
			self.wndSupportPG.SetHair(hair)
			osfInfo.SUPPORT_HAIR = int(hair)
			
		def SetSupportAcce(self, acce):
			self.wndSupportPG.SetAcce(acce)
			osfInfo.SUPPORT_ACCE = int(acce)
			
		def SetShiningWeapon(self, shining_weapon):
			self.wndSupportPG.SetWeaponShining(shining_weapon)
			osfInfo.SUPPORT_SHINING_WEAPON = int(shining_weapon)
			
		def SetShiningArmor(self, shining_armor):
			self.wndSupportPG.SetArmorShining(shining_armor)
			osfInfo.SUPPORT_SHINING_ARMOR = int(shining_armor)
			
		def SetSupportSkillLvl(self, skill_1, skill_2, skill_3, skill_4, skill_5):
			self.wndSupportPG.SetSkillLvl(skill_1, skill_2, skill_3, skill_4, skill_5)
			self.wndCharacter.SetBuffSkillLevels((skill_1, skill_2, skill_3, skill_4, skill_5))

		def SetSupportInt(self, inteligence):
			self.wndSupportPG.SetInteligence(inteligence)
			
		def SupportLeave(self):
			self.wndSupportPG.SetDefaultInfo()
			self.wndSupportPG.Close()
			self.wndCharacter.ResetBuffSkills()
			
		def SetBuffPremiumSkill(self, isPremium):
			self.wndSupportPG.SetPremiumSkill(isPremium)
			self.wndCharacter.SetBuffHealingUnlocked(isPremium)

		def SetBuffiProgress(self, level, currentExp, requiredExp, passivePoints, healingUnlocked, expMode=1, form=0, hairEnabled=1):
			self.wndSupportPG.SetProgress(
				level, currentExp, requiredExp, passivePoints,
				healingUnlocked, expMode, form, hairEnabled)
			self.wndCharacter.SetBuffHealingUnlocked(healingUnlocked)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def MiniGameCatchKingEventStart(self, bigScore):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.GameStart(bigScore)

		def MiniGameCatchKingSetHandCard(self, cardNumber):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.CatchKingSetHandCard(cardNumber)

		def MiniGameCatchKingResultField(self, score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.CatchKingResultField(score, rowType, cardPos, cardValue, keepFieldCard, destroyHandCard, getReward, isFiveNear)

		def MiniGameCatchKingSetEndCard(self, cardPos, cardNumber):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.CatchKingSetEndCard(cardPos, cardNumber)

		def MiniGameCatchKingReward(self, rewardCode):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.CatchKingReward(rewardCode)

		def ClickCatchKingEventButton(self):
			if self.wndCatchKingGame:
				self.wndCatchKingGame.Open()

		def MiniGameCatchKing(self, value):
			import dbg
			if int(value) == 0:
				self.wndCatchKingIcon.Hide()
			else:
				self.wndCatchKingIcon.Show()

	if app.ENABLE_ATTR_6TH_7TH:
		def OpenAttr67AddDlg(self):
			if self.wndAttr67Add.IsShow():
				return

			self.wndAttr67Add.Show()

	if app.ENABLE_BATTLE_PASS:
		def ShowBattlePass(self):
			if self.wndBattlePass.IsShow() == FALSE:
				self.wndBattlePass.Show()
			else:
				self.wndBattlePass.Close()

	if app.ENABLE_GUILD_DRAGONLAIR_SYSTEM:
		def OpenGuildDragonLairRanking(self,type):
			self.wndGuildDragonLairRanking.Open(type)

		def RefreshGuildDragonLairRanking(self, type):
			self.wndGuildDragonLairRanking.RefreshGuildDragonLairRanking(type)

		def GetDragonLairType(self):
			self.wndGuildDragonLairRanking.GetDragonLairType()

		if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
			def SetGuildDragonLairFistGuildText(self, second):
				self.wndMiniMap.SetGuildDragonLairFistGuildText(second)
			def SetGuildDragonLairStart(self):
				self.wndMiniMap.SetGuildDragonLairStart()
			def SetGuildDragonLairSuccess(self):
				self.wndMiniMap.SetGuildDragonLairSuccess()

	if app.ENABLE_PLAYER_COUNT:
		def RefreshPlayerCount(self, count):
			if self.wndMiniMap:
				self.wndMiniMap.RefreshPlayerCount(count)

	if app.ENABLE_BOSS_TRACK:
		def SetBossTrack(self, data, needClean):
			if self.wndBossTrack:
				self.wndBossTrack.SetServerData(data, int(needClean))
		def OpenBossTrack(self):
			if self.wndBossTrack == None:
				self.wndBossTrack = uiBossTrack.Window()
			if self.wndBossTrack.IsShow():
				self.wndBossTrack.Close()
			else:
				self.wndBossTrack.Open()

	if app.ENABLE_REFINE_ELEMENT_SYSTEM:
		def IsRefineElementDialogOpen(self):
			if self.dlgRefineElement and self.dlgRefineElement.IsShow():
				return True

			if self.dlgRefineElementChange and self.dlgRefineElementChange.IsShow():
				return True

			return False

		def RefineElementProcess(self, type, refine_type, data):
			if not self.dlgRefineElement or not self.dlgRefineElementChange:
				return

			if refine_type == player.REFINE_ELEMENT_CHANGE:
				self.dlgRefineElementChange.RefineElementChangeProcess(type, refine_type, data)
			else:
				self.dlgRefineElement.RefineElementProcess(type, refine_type, data)

	if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
		def ToggleAutoHuntingWindow(self):
			if False == player.IsObserverMode():
				if not self.wndAutoHunting.IsShow():
					self.wndAutoHunting.Show()
				else:
					self.wndAutoHunting.Close()

		def SetAutoCooltime(self, slotindex, cooltime):
			self.wndAutoHunting.SetAutoCooltime(slotindex, cooltime)

		def SetCloseGame(self):
			self.wndAutoHunting.SetCloseGame()

		def GetAutoStartonoff(self):
			return self.wndAutoHunting.GetAutoStartonoff()

		def RefreshAutoSkillSlot(self):
			if self.wndAutoHunting:
				self.wndAutoHunting.RefreshAutoSkillSlot()

		def RefreshAutoPositionSlot(self):
			if self.wndAutoHunting:
				self.wndAutoHunting.RefreshAutoPositionSlot()

		def AutoOff(self):
			if self.wndAutoHunting:
				self.wndAutoHunting.AutoOnOff(0, self.wndAutoHunting.AUTO_ONOFF_START, 1, True)

		def AutoOn(self):
			pass

# CRIMSON_EMBER_PROFILE_INTERFACE_V1_BEGIN
import messengerportraitresolver


def _CrimsonRouterPlayerProfileCapability(self, enabled):
	messengerportraitresolver.SetCapability(bool(enabled))
	if self.window:
		self.window.OnPlayerProfileChanged()
	if self.interface.wndMessenger:
		self.interface.wndMessenger.RefreshCrimsonPortraits()


def _CrimsonRouterPlayerProfile(self, token, status, pid, name, race):
	if not messengerportraitresolver.OnResponse(token, status, pid, name, race):
		return
	if self.window:
		self.window.OnPlayerProfileChanged()
	if self.interface.wndMessenger:
		self.interface.wndMessenger.RefreshCrimsonPortraits()


def _CrimsonInterfacePlayerProfileCapability(self, enabled):
	self.unifiedMessengerRouter.PlayerProfileCapability(enabled)


def _CrimsonInterfacePlayerProfile(self, token, status, pid, name, race):
	self.unifiedMessengerRouter.PlayerProfile(token, status, pid, name, race)


UnifiedMessengerRouter.PlayerProfileCapability = _CrimsonRouterPlayerProfileCapability
UnifiedMessengerRouter.PlayerProfile = _CrimsonRouterPlayerProfile
Interface.UnifiedMessengerPlayerProfileCapability = _CrimsonInterfacePlayerProfileCapability
Interface.UnifiedMessengerPlayerProfile = _CrimsonInterfacePlayerProfile
# CRIMSON_EMBER_PROFILE_INTERFACE_V1_END
