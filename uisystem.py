import net
import player
import app
import ui
import uiOption

import uiSystemOption
import uiGameOption
import uiScriptLocale
import networkModule
import constInfo
import osfInfo
import localeInfo
import globalhub

if app.ENABLE_MOVE_CHANNEL:
	import chat

if app.ENABLE_NEW_GAMEOPTION:
	import uisettings as uiGameOptionNew

SYSTEM_MENU_FOR_PORTAL = False


def LoadChannelInfo():
	try:
		with open("UserData/channel.inf") as channel_file:
			tokens = channel_file.readline().split()
		if len(tokens) < 3:
			raise ValueError("incomplete channel info")
		server_id = int(tokens[0])
		channel_id = int(tokens[1])
		region_id = int(tokens[2])
		return region_id, server_id, channel_id
	except (OSError, ValueError, IndexError):
		print("LoadChannelInfo - OpenError")
		return -1, -1, -1


def SaveChannelInfo(channel_index):
	region_id, server_id, unused_channel_id = LoadChannelInfo()
	try:
		with open("UserData/channel.inf", "w") as channel_file:
			channel_file.write(
				"%d %d %d" % (server_id, int(channel_index), region_id)
			)
		return True
	except (OSError, TypeError, ValueError):
		print("SaveChannelInfo - SaveError")
		return False


def GetChannelCount():
	if not app.ENABLE_MOVE_CHANNEL:
		return 0
	import serverInfo
	region_id, server_id, unused_channel_id = LoadChannelInfo()
	try:
		return len(serverInfo.REGION_DICT[region_id][server_id]["channel"])
	except (KeyError, TypeError):
		return 0


def RequestChannelChange(channel_index):
	if not app.ENABLE_MOVE_CHANNEL:
		return False
	try:
		channel_index = int(channel_index)
	except (TypeError, ValueError):
		return False
	if globalhub.IsGlobalHub(
		net.GetChannelNumber(), net.GetMapIndex()
	):
		chat.AppendChat(
			chat.CHAT_TYPE_INFO,
			localeInfo.GLOBAL_HUB_CHANNEL_SWITCH_BLOCKED
		)
		return False
	if channel_index < 1 or channel_index > GetChannelCount():
		return False
	if net.GetChannelNumber() == 99 or net.GetMapIndex() >= 10000:
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.MOVE_CHANNEL_NOT_MOVE)
		return False
	if channel_index == net.GetChannelNumber():
		return False
	# Presentation guard only; the server revalidates equipped VIP and expiry.
	if channel_index in (6, 7) and not getattr(player, "IsVipActive", lambda: False)():
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.LOGIN_FAILURE_VIP_ONLY)
		return False

	net.SendChatPacket("/move_channel %d" % channel_index)
	SaveChannelInfo(channel_index)
	return True

###################################################################################################
## System
class SystemDialog(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Initialize(self):
		self.eventOpenHelpWindow = None
		self.eventPrepareExit = None
		self.systemOptionDlg = None
		self.gameOptionDlg = None

		if app.ENABLE_MOVE_CHANNEL:
			self.channelButtons = []
			self.globalHubChannelLabel = None

	def LoadDialog(self):
		if SYSTEM_MENU_FOR_PORTAL:
			self.__LoadSystemMenu_ForPortal()
		else:
			self.__LoadSystemMenu_Default()

	def __LoadSystemMenu_Default(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/systemdialog_crimson_ember.py")

		self.GetChild("game_option_button").SAFE_SetEvent(self.__ClickGameOptionButton)
		self.GetChild("change_button").SAFE_SetEvent(self.__ClickChangeCharacterButton)
		self.GetChild("logout_button").SAFE_SetEvent(self.__ClickLogOutButton)
		self.GetChild("debug_button").SAFE_SetEvent(self.__ClickDebugButton)
		self.GetChild("exit_button").SAFE_SetEvent(self.__ClickExitButton)
		self.GetChild("help_button").SAFE_SetEvent(self.__ClickHelpButton)
		self.GetChild("cancel_button").SAFE_SetEvent(self.Close)
		self.GetChild("board").SetCloseEvent(self.Close)

		if app.ENABLE_ITEMSHOP:
			self.GetChild("mall_button").SAFE_SetEvent(self.__ClickInGameShopButton)
		else:
			self.GetChild("mall_button").Disable()

		if app.ENABLE_WIKI:
			self.GetChild("wiki_button").SAFE_SetEvent(self.__ClickWikiButton)
		else:
			self.GetChild("wiki_button").Disable()

		if app.ENABLE_MOVE_CHANNEL:
			self.globalHubChannelLabel = self.GetChild(
				"global_hub_channel_label"
			)
			self.globalHubChannelLabel.Hide()
			self.__BindChannelButtons()

	def __LoadSystemMenu_ForPortal(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "uiscript/systemdialog_forportal.py")

		# self.GetChild("system_option_button").SAFE_SetEvent(self.__ClickSystemOptionButton)
		self.GetChild("game_option_button").SAFE_SetEvent(self.__ClickGameOptionButton)
		self.GetChild("change_button").SAFE_SetEvent(self.__ClickChangeCharacterButton)
		self.GetChild("debug_button").SAFE_SetEvent(self.__ClickDebugButton)
		self.GetChild("exit_button").SAFE_SetEvent(self.__ClickExitButton)
		self.GetChild("help_button").SAFE_SetEvent(self.__ClickHelpButton)
		self.GetChild("cancel_button").SAFE_SetEvent(self.Close)

	def Destroy(self):
		self.ClearDictionary()

		if self.gameOptionDlg:
			self.gameOptionDlg.Destroy()

		if self.systemOptionDlg:
			self.systemOptionDlg.Destroy()

		self.__Initialize()

	def SetOpenHelpWindowEvent(self, event):
		self.eventOpenHelpWindow = event

	def SetPrepareExitEvent(self, event):
		self.eventPrepareExit = event

	def __PrepareExit(self):
		if self.eventPrepareExit:
			self.eventPrepareExit()

	def OpenDialog(self):
		if app.ENABLE_MOVE_CHANNEL:
			self.__RefreshChannelButtons()
		self.Show()

	def __BindChannelButtons(self):
		self.channelButtons = []
		for channel_index in range(1, 8):
			button = self.GetChild("channel_button_%d" % channel_index)
			button.SetEvent(
				ui.__mem_func__(self.__ClickChannelButton), channel_index
			)
			self.channelButtons.append(button)
		self.__RefreshChannelButtons()

	def __RefreshChannelButtons(self):
		channel_count = GetChannelCount()
		current_channel = net.GetChannelNumber()
		is_global_hub = globalhub.IsGlobalHub(
			current_channel, net.GetMapIndex()
		)
		if self.globalHubChannelLabel:
			if is_global_hub:
				self.globalHubChannelLabel.Show()
			else:
				self.globalHubChannelLabel.Hide()
		for channel_index, button in enumerate(self.channelButtons, 1):
			button.SetUp()
			button.Enable()
			if is_global_hub:
				button.Disable()
				button.Show()
				continue
			if channel_index > channel_count:
				button.Disable()
				button.Hide()
				continue
			button.Show()
			if current_channel == 99:
				button.Disable()
			elif channel_index == current_channel:
				button.Down()
				button.Disable()

	def __ClickChannelButton(self, channel_index):
		if RequestChannelChange(channel_index):
			self.Close()

	def __ClickChangeCharacterButton(self):
		self.Close()
		self.__PrepareExit()
		net.ExitGame()

	def __OnClosePopupDialog(self):
		self.popup = None

	def __ClickLogOutButton(self):
		self.Close()
		self.__PrepareExit()
		net.ExitApplication()

	def __ClickDebugButton(self):
		self.Close()
		net.SendChatPacket("/unstuck")

	def __ClickExitButton(self):
		self.Close()
		self.__PrepareExit()
		import chr
		import player
		#if chr.IsGameMaster(player.GetMainCharacterIndex()):
		#	app.Exit()
		#else:
		#	net.ExitApplication()
		net.ExitApplication()

	# def __ClickSystemOptionButton(self):
		# self.Close()

		# if not self.systemOptionDlg:
			# self.systemOptionDlg = uiSystemOption.OptionDialog()

		# self.systemOptionDlg.Show()

	def __ClickGameOptionButton(self):
		self.Close()

		if not self.gameOptionDlg:
			if app.ENABLE_NEW_GAMEOPTION:
				self.gameOptionDlg = uiGameOptionNew.GameOptionWindow()
			else:
				self.gameOptionDlg = uiGameOption.OptionDialog()

		self.gameOptionDlg.Open()

	def OpenGameOptionDialog(self):
		"""Open game options through the same path as the system-menu button."""
		self.__ClickGameOptionButton()
		return self.gameOptionDlg

	def __ClickHelpButton(self):
		self.Close()
		if None != self.eventOpenHelpWindow:
			self.eventOpenHelpWindow()

	def __ClickWikiButton(self):
		self.Close()
		if app.ENABLE_WIKI:
			osfInfo.GetInterfaceInstance().OpenWikiWindow()

	def __ClickInGameShopButton(self):
		self.Close()
		if app.ENABLE_ITEMSHOP:
			osfInfo.GetInterfaceInstance().OpenItemShopWindow()		

	def Close(self):
		self.Hide()
		return True

	def OnBlockMode(self, mode):
		uiGameOptionNew.blockMode = mode
		if self.gameOptionDlg:
			self.gameOptionDlg.OnBlockMode(mode)
		#self.optionDialog.OnBlockMode(mode)

	def OnChangePKMode(self):
		if self.gameOptionDlg:
			self.gameOptionDlg.OnChangePKMode()
		#self.optionDialog.OnChangePKMode()

	def OnPressExitKey(self):
		self.Close()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def GetSystemOption(self):
		return self.systemOptionDlg

	def HideAllSystemOptioin(self):
		if self.systemOptionDlg:
			self.systemOptionDlg.Hide()
		if self.gameOptionDlg:
			self.gameOptionDlg.Hide()

	def ShowAllSystemOptioin(self):
		if self.systemOptionDlg and self.systemOptionDlg.IsShow():
			self.systemOptionDlg.Show()
		if self.gameOptionDlg and self.gameOptionDlg.IsShow():
			self.gameOptionDlg.Open()

if __name__ == "__main__":
	import app
	import wndMgr
	import systemSetting
	import mouseModule
	import grp
	import ui
	import chr
	import background
	import player

	# wndMgr.SetOutlineFlag(True)

	app.SetMouseHandler(mouseModule.mouseController)
	app.SetHairColorEnable(True)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())
	app.Create("METIN2 CLOSED BETA", systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
	mouseModule.mouseController.Create()

	wnd = SystemDialog()
	wnd.LoadDialog()
	wnd.Show()

	app.Loop()
