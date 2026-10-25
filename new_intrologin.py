import launcherhandoff
# -*- coding: utf-8 -*-
import dbg
import app
import net
import ui
import ime
import snd
import wndMgr
import musicInfo
import serverInfo
import systemSetting
import ServerStateChecker
import localeInfo
import constInfo
import uiCommon
import time
import ServerCommandParser
import ime
import uiScriptLocale
import winreg as _winreg
import os
import grp

BASIC_DEF = {
	"CH_NUM" : 6,
	"SAVE_ACCOUNT" : 6,
	"SOCIAL" : 3,
	"REDE_SOCIAL_1" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
	"REDE_SOCIAL_2" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
	"REDE_SOCIAL_3" : "https://discord.com",
	"CREATE_ACC" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
	"LOSE_PW" : "https://www.youtube.com/watch?v=XFwaFFeJ9k4&ab_channel=AnimeMomentzz",
	"CHANNEL_FILE" : "UserData/channel.inf",
}

DEFAULTS_TEXT = {
	"TEXT_1" : uiScriptLocale.MSG_TEXT_1,
	"MSG_SUPLOGIN" : uiScriptLocale.MSG_TEXT_2,
	"MSG_1" : uiScriptLocale.MSG_TEXT_3,
	"MSG_2" : uiScriptLocale.MSG_TEXT_4,
	"MSG_3" : uiScriptLocale.MSG_TEXT_5,
	"MSG_4" : uiScriptLocale.MSG_TEXT_6,
}

IMAGE_STATE = {
	0 : "d:/ymir work/ui/intro/login/state_button_ch/state_none.tga",
	1 : "d:/ymir work/ui/intro/login/state_button_ch/state_on.tga",
	2 : "d:/ymir work/ui/intro/login/state_button_ch/state_busy.tga",
	3 : "d:/ymir work/ui/intro/login/state_button_ch/state_full.tga",
}

IMAGE_SAVE_ACCOUNT = {
	0 : ["d:/ymir work/ui/intro/login/save_acc/save_button_1.tga","d:/ymir work/ui/intro/login/save_acc/save_button_2.tga","d:/ymir work/ui/intro/login/save_acc/save_button_3.tga"],
	1 : ["d:/ymir work/ui/intro/login/save_acc/add_acc_1.tga","d:/ymir work/ui/intro/login/save_acc/add_acc_2.tga","d:/ymir work/ui/intro/login/save_acc/add_acc_3.tga"],
}

REG_PATH = r"SOFTWARE\M2uAccounts"


class LoginWindow(ui.ScriptWindow):
	def __init__(self, stream):
		ui.ScriptWindow.__init__(self)
		
		net.SetPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
		net.SetAccountConnectorHandler(self)
		
		self.button_ch = {
			"channel" : [],
			"text_channel" : [],
			
			"channel_state" : [],
			"channel_state_text" : [],
		}
		self.save_acc = {
			"buttons" : [],
			"save_acc_buttons" : [],
			"del_account_buttons" : [],
			"text_buttons" : [],
			
			"image_toggle" : [],
		}
		self.r_s = []
		self.exit = None
		self.login = None
		#self.langList = ["en", "de","cz","fr","ro", "es", "hu", "it", "pl", "pt", "tr", "ru", "ae"]
		self.languageList = [ None, None, None, None, None, None, None, None, None, None, None, None, None ] #x11 languages
		#self.langBtnList=[]
		self.act_ch = None
		self.server_id = 1
		self.auto_login = False
		
		self.stream = stream
		
		self.onPressKeyDict = None
		self.__BuildKeyDict()
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
		
		net.ClearPhaseWindow(net.PHASE_WINDOW_LOGIN, self)
		net.SetAccountConnectorHandler(0)

		self.button_ch = {}
		self.save_acc = {}
		self.r_s = []
		self.act_ch = None
		self.onPressKeyDict = None
	
	def Close(self):
		ServerStateChecker.Initialize(self)
		
		if musicInfo.loginMusic != "" and musicInfo.selectMusic != "":
			snd.FadeOutMusic("BGM/"+musicInfo.loginMusic)
		
		if self.stream.popupWindow:
			self.stream.popupWindow.Close()

		self.KillFocus()
		self.Username.KillFocus()
		self.Password.KillFocus()
		self.languageList = [ None, None, None, None, None, None, None, None, None, None, None, None, None ] #x11 languages
		self.Hide()
		app.HideCursor()
		ime.ClearExceptKey()
	
	def Open(self):
		ServerStateChecker.Create(self)
		
		self.loginFailureMsgDict={
			#"DEFAULT" : localeInfo.LOGIN_FAILURE_UNKNOWN,

			"ALREADY" : localeInfo.LOGIN_FAILURE_ALREAY,
			"NOID" : localeInfo.LOGIN_FAILURE_NOT_EXIST_ID,
			"WRONGPWD" : localeInfo.LOGIN_FAILURE_WRONG_PASSWORD,
			"FULL" : localeInfo.LOGIN_FAILURE_TOO_MANY_USER,
			"SHUTDOWN" : localeInfo.LOGIN_FAILURE_SHUTDOWN,
			"REPAIR" : localeInfo.LOGIN_FAILURE_REPAIR_ID,
			"BLOCK" : localeInfo.LOGIN_FAILURE_BLOCK_ID,
			"BESAMEKEY" : localeInfo.LOGIN_FAILURE_BE_SAME_KEY,
			"NOTAVAIL" : localeInfo.LOGIN_FAILURE_NOT_AVAIL,
			"NOBILL" : localeInfo.LOGIN_FAILURE_NOBILL,
			"BLKLOGIN" : localeInfo.LOGIN_FAILURE_BLOCK_LOGIN,
			"WEBBLK" : localeInfo.LOGIN_FAILURE_WEB_BLOCK,
			"BADSCLID" : localeInfo.LOGIN_FAILURE_WRONG_SOCIALID,
			"AGELIMIT" : localeInfo.LOGIN_FAILURE_SHUTDOWN_TIME,
			"HWID_BAN" : localeInfo.LOGIN_FAILURE_BLOCK_ID,
			"VIP_ONLY" : localeInfo.LOGIN_FAILURE_VIP_ONLY,
			"DEVICE_LIMIT" : localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
			"DEVICE_L" : localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
			"DEVLIM" : localeInfo.LOGIN_FAILURE_DEVICE_LIMIT,
			"DEVICE_ID" : localeInfo.LOGIN_FAILURE_DEVICE_ID,
			"DEVICE_I" : localeInfo.LOGIN_FAILURE_DEVICE_ID,
			"DEVID" : localeInfo.LOGIN_FAILURE_DEVICE_ID,
			"DEVAPPR" : localeInfo.LOGIN_FAILURE_DEVICE_APPROVAL,
			"DEVWAIT" : localeInfo.LOGIN_FAILURE_DEVICE_COOLDOWN,
			"DEVERR" : localeInfo.LOGIN_FAILURE_DEVICE_UNAVAILABLE
		}

		self.loginFailureFuncDict = {
			"WRONGPWD"	: localeInfo.LOGIN_FAILURE_WRONG_PASSWORD,
			"QUIT"		: app.Exit,
		}
		
		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.SetWindowName("LoginWindow")
		
		self.__LoadScript()
		regionID, serverID, channelID = self.__LoadChannelInfo()
		if regionID in serverInfo.REGION_DICT and serverID in serverInfo.REGION_DICT[regionID]:
			self.server_id = serverID

		self.auto_login = False
		self.stream.isAutoLogin = 0
		self.stream.isAutoSelect = 0
		xmlChannelID = self.__LoadLauncherHandoff()
		if xmlChannelID is not None:
			channelID = xmlChannelID
		self.__RequestServerStateList()

		if musicInfo.loginMusic != "":
			# the login music alone (root/pregamemusic.py): the engine does not fade before the game, so the select's
			# track coming back here (a failed / closed connection) played on next to it
			try:
				import pregamemusic
				pregamemusic.Only("BGM/" + musicInfo.loginMusic)
			except Exception:
				snd.SetMusicVolume(systemSetting.GetMusicVolume())
				snd.FadeInMusic("BGM/" + musicInfo.loginMusic)
		
		self.ChannelButtonArray(int(channelID)) ##CH Load
		self.Username.SetFocus()

		#import uiSystemOption
		#localeName = app.GetLoca()
		#for i, k in uiSystemOption.LOCALE_LANG_DICT.items():
		#	if localeName in uiSystemOption.LOCALE_LANG_DICT[i]["locale"]:
		#		net.SendChangeLanguagePacket(i)
		#		# net.SetLanguage(i)
		#		break

		self.RefreshLanguagesBtn()

		ime.AddExceptKey(91)
		ime.AddExceptKey(93)
		
		self.Show()
		app.ShowCursor()

		if self.auto_login:
			self.LoginFunc()

	def OnConnectFailure(self):
		snd.PlaySound("sound/ui/loginfail.wav")
		self.PopupNotifyMessage(localeInfo.LOGIN_CONNECT_FAILURE, self.PassFunc)
	
	def OnHandShake(self):
		snd.PlaySound("sound/ui/loginok.wav")
		self.PopupDisplayMessage(localeInfo.LOGIN_CONNECT_SUCCESS)
	
	def OnLoginStart(self):
		self.PopupDisplayMessage(localeInfo.LOGIN_PROCESSING)
	
	def OnLoginFailure(self, error):
		try:
			loginFailureMsg = self.loginFailureMsgDict[error]
		except KeyError:
			loginFailureMsg = localeInfo.LOGIN_FAILURE_UNKNOWN  + error
		loginFailureFunc = self.loginFailureFuncDict.get(error, self.PassFunc)
		self.PopupNotifyMessage(loginFailureMsg, loginFailureFunc)
		snd.PlaySound("sound/ui/loginfail.wav")

	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "uiscript/new_loginwindow.py")
		except:
			import exception
			exception.Abort("LoginWindow.__LoadScript.LoadObject")
		
		try:
			GetObject=self.GetChild
			for i in range(BASIC_DEF["CH_NUM"]):
				self.button_ch["channel"].append(self.GetChild("button_ch_%d" % (i+1)))
				self.button_ch["channel"][i].SetEvent(ui.__mem_func__(self.buttonchannel), i)
				
				self.button_ch["channel_state"].append(self.GetChild("ch_%d_state" % (i+1)))
				self.button_ch["channel_state"][i].LoadImage(IMAGE_STATE[0])
				
				self.button_ch["text_channel"].append(self.GetChild("ch_name_button_%d" % (i+1)))
				self.button_ch["text_channel"][i].SetText(str(DEFAULTS_TEXT["TEXT_1"]).format(i+1))
				
				self.button_ch["channel_state_text"].append(self.GetChild("ch_state_button_%d" % (i+1)))
				self.button_ch["channel_state_text"][i].SetText(str(serverInfo.STATE_NONE))
				
			for i in range(BASIC_DEF["SAVE_ACCOUNT"]):
				self.save_acc["buttons"].append(self.GetChild("save_button_%d" % (i+1)))
				self.save_acc["buttons"][i].SetEvent(ui.__mem_func__(self.buttonsave), i)

				self.save_acc["save_acc_buttons"].append(self.GetChild("add_acc_button_%d" % (i+1)))
				self.save_acc["save_acc_buttons"][i].SetEvent(ui.__mem_func__(self.buttonsave), i)
				
				self.save_acc["del_account_buttons"].append(self.GetChild("delete_account_button_%d" % (i+1)))
				self.save_acc["del_account_buttons"][i].SetEvent(ui.__mem_func__(self.DelAcc), i)
				self.save_acc["del_account_buttons"][i].Hide()
				
				self.save_acc["text_buttons"].append(self.GetChild("acc_name_text_%d" % (i+1)))
				self.save_acc["text_buttons"][i].Hide()	

				self.save_acc["image_toggle"].append(self.GetChild("save_image_f%d" % (i+1)))
				self.save_acc["image_toggle"][i].Hide()

				self.languageList[0] = GetObject("flag_1")
				self.languageList[1] = GetObject("flag_2")
				self.languageList[2] = GetObject("flag_3")
				self.languageList[3] = GetObject("flag_4")
				self.languageList[4] = GetObject("flag_5")
				self.languageList[5] = GetObject("flag_6")
				self.languageList[6] = GetObject("flag_7")
				self.languageList[7] = GetObject("flag_8")
				self.languageList[8] = GetObject("flag_9")
				self.languageList[9] = GetObject("flag_10")
				self.languageList[10] = GetObject("flag_11")
				self.languageList[11] = GetObject("flag_12")
				self.languageList[12] = GetObject("flag_13")
				self.languageList[12].Hide()
			for i in range(BASIC_DEF["SOCIAL"]):
				self.r_s.append(self.GetChild("rs_%d" % (i+1)))
				self.r_s[i].SetEvent(ui.__mem_func__(self.__Link), BASIC_DEF["REDE_SOCIAL_%d" % (i+1)])
			
			self.exit = self.GetChild("exit")
			self.exit.SetEvent(ui.__mem_func__(self.exitFunc))
			
			self.login = self.GetChild("button_login")
			self.login.SetEvent(ui.__mem_func__(self.LoginFunc))

			self.create_account = self.GetChild("create_account")
			self.create_account.SetEvent(ui.__mem_func__(self.__Link), BASIC_DEF["CREATE_ACC"])

			self.lost_pw = self.GetChild("lost_pw")
			self.lost_pw.SetEvent(ui.__mem_func__(self.__Link), BASIC_DEF["LOSE_PW"])

			self.Username = self.GetChild("ID_EditLine")
			self.Password = self.GetChild("Password_EditLine")
			
			self.Username.SetReturnEvent(ui.__mem_func__(self.Password.SetFocus))
			self.Username.SetTabEvent(ui.__mem_func__(self.Password.SetFocus))
			
			self.Password.SetReturnEvent(ui.__mem_func__(self.LoginFunc))
			self.Password.SetTabEvent(ui.__mem_func__(self.Username.SetFocus))
		except:
			import exception
			exception.Abort("LoginWindow.__LoadScript.BindObject")

		#for lang in self.langList:
		#	index = self.langList.index(lang)
		#	self.langBtnList[index].SetEvent(ui.__mem_func__(self.__OnClickChangeLanguage),lang)
		#
		#	if ("locale/%s"%lang) == app.GetLocalePath():
		#		self.__ClickRadioButton(self.langBtnList, index)

		self.languageList[0].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("en"))
		self.languageList[1].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("de"))
		self.languageList[2].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("cz"))
		self.languageList[3].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("fr"))
		self.languageList[4].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("ro"))
		self.languageList[5].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("es"))
		self.languageList[6].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("hu"))
		self.languageList[7].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("it"))
		self.languageList[8].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("pl"))
		self.languageList[9].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("pt"))
		self.languageList[10].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("tr"))
		self.languageList[11].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("ru"))
		self.languageList[12].SetEvent(lambda:ui.__mem_func__(self.__QuestionChangeLanguage)("ae"))

	def LoginFunc(self):
		id = self.Username.GetText()
		pwd = self.Password.GetText()
		if len(id)==0:
			self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_ID, self.PassFunc)
			return
		if len(pwd)==0:
			self.PopupNotifyMessage(localeInfo.LOGIN_INPUT_PASSWORD, self.PassFunc)
			return
		self.Connect(id, pwd)

	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			selButton = buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		selButton.Down()

	def Connect(self, id, pwd):
		if constInfo.SEQUENCE_PACKET_ENABLE:
			net.SetPacketSequenceMode()
			
		constInfo.LastAccount = id.lower()
		
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(localeInfo.LOGIN_CONNETING, self.PassFunc, localeInfo.UI_CANCEL)
		
		self.stream.SetLoginInfo(id, pwd)
		self.stream.Connect()
	
	def __BuildKeyDict(self):
		onPressKeyDict = {}
		onPressKeyDict[app.DIK_F1]	= lambda : self.buttonsave(0, True)
		onPressKeyDict[app.DIK_F2]	= lambda : self.buttonsave(1, True)
		onPressKeyDict[app.DIK_F3]	= lambda : self.buttonsave(2, True)
		onPressKeyDict[app.DIK_F4]	= lambda : self.buttonsave(3, True)
		onPressKeyDict[app.DIK_F5]	= lambda : self.buttonsave(4, True)
		onPressKeyDict[app.DIK_F6]	= lambda : self.buttonsave(5, True)
		self.onPressKeyDict = onPressKeyDict

	def __LoadLauncherHandoff(self):
		record = launcherhandoff.consume()
		if record is None:
			return None
		serverName, channelID, login, password = record
		for serverID, serverData in serverInfo.REGION_DICT[0].items():
			if serverData["name"] == serverName and channelID in serverData["channel"]:
				self.server_id = serverID
				break
		else:
			return None
		self.Username.SetText(login)
		self.Password.SetText(password)
		self.auto_login = True
		self.stream.SetCharacterSlot(0)
		self.stream.isAutoLogin = 1
		self.stream.isAutoSelect = 0
		return channelID - 1

	def OnKeyDown(self, key):
		try:
			self.onPressKeyDict[key]()
		except KeyError:
			pass
		except:
			raise

		return True
	
	def buttonsave(self, arg, dikCut = False):
		if self.get_reg("account%d.cfg" % (arg+1)):
			self.Username.SetText("%s" % str(self.get_reg("account%d.cfg" % (arg+1)).split("|")[0]))
			self.Password.SetText("%s" % str(self.get_reg("account%d.cfg" % (arg+1)).split("|")[1]))
			self.LoginFunc()
			return
		
		if dikCut:	return
		
		if len(self.Username.GetText()) == 0 or len(self.Password.GetText()) == 0:
			self.PopupNotifyMessage(DEFAULTS_TEXT["MSG_1"], False)
			return
		for i in range(BASIC_DEF["SAVE_ACCOUNT"]):
			if self.get_reg("account%d.cfg" % (i+1)):
				if str(self.get_reg("account%d.cfg" % (i+1)).split("|")[0]) == str(self.Username.GetText()):
					self.PopupNotifyMessage(DEFAULTS_TEXT["MSG_3"], False)
					return
		self.set_reg("account%d.cfg" % (arg+1), self.Username.GetText() + "|" + self.Password.GetText())
		self.PopupNotifyMessage(DEFAULTS_TEXT["MSG_2"], False)
	
	def DelAcc(self, arg):
		try:
			if str(self.Username.GetText()) == str(self.get_reg("account%d.cfg" % (arg+1)).split("|")[0]):
				self.Username.SetText("")
				self.Password.SetText("")
				self.Username.SetFocus()
			self.del_reg("account%d.cfg" % (arg+1))
			self.save_acc["text_buttons"][arg]
		except:
			pass
	
	def LoadSavedAccount(self):
		for i in range(BASIC_DEF["SAVE_ACCOUNT"]):
			try:
				self.save_acc["save_acc_buttons"][i].Hide()
				self.save_acc["buttons"][i].Show()
				self.save_acc["del_account_buttons"][i].Show()
				self.save_acc["text_buttons"][i].SetText("%s" % str(self.get_reg("account%d.cfg" % (i+1)).split("|")[0]))
				self.save_acc["text_buttons"][i].Show()
				self.__CheckNameLenght(i) #@Fix-Check name size
				self.save_acc["image_toggle"][i].Show()
			except:
				self.save_acc["text_buttons"][i].Hide()
				self.save_acc["del_account_buttons"][i].Hide()
				self.save_acc["image_toggle"][i].Hide()
				self.save_acc["buttons"][i].Hide()
				self.save_acc["save_acc_buttons"][i].Show()
	
	def set_reg(self, name, value):
		try:
			_winreg.CreateKey(_winreg.HKEY_CURRENT_USER, REG_PATH)
			registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_WRITE)
			_winreg.SetValueEx(registry_key, name, 0, _winreg.REG_SZ, value)
			_winreg.CloseKey(registry_key)
			return True
		except WindowsError:
			return False
	
	def get_reg(self, name):
		try:
			registry_key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_READ)
			value, regtype = _winreg.QueryValueEx(registry_key, name)
			_winreg.CloseKey(registry_key)
			return value
		except WindowsError:
			return None
	
	def del_reg(self, name):
		try:
			key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, REG_PATH, 0, _winreg.KEY_ALL_ACCESS)
			_winreg.DeleteValue(key, name) 
			_winreg.CloseKey(key)
		except WindowsError:
			return None
	
	def __SaveChannelInfo(self):
		try:
			file=open(BASIC_DEF["CHANNEL_FILE"], "w")
			file.write("%d %d 0" % (self.server_id, self.act_ch))
		except:
			print("LoginWindow.__SaveChannelInfo - SaveError")
	
	def __LoadChannelInfo(self):
		try:
			file=open(BASIC_DEF["CHANNEL_FILE"])
			lines=file.readlines()
			
			if len(lines)>0:
				tokens=lines[0].split()
			
				selServerID=int(tokens[0])
				selChannelID=int(tokens[1])
				
				if len(tokens) == 3:
					regionID = int(tokens[2])
				
				return regionID, selServerID, selChannelID
		except:
			print("LoginWindow.__LoadChannelInfo - OpenError")
			return 1, 0, 0
	
	def OnUpdate(self):
		ServerStateChecker.Update()
		self.LoadSavedAccount()
	
	def __RequestServerStateList(self):
		try:
			channelDict = serverInfo.REGION_DICT[0][self.server_id]["channel"]
		except:
			print(" __RequestServerStateList - serverInfo.REGION_DICT(%d, %d)" % (0, self.server_id))
			return
		
		ServerStateChecker.Initialize();
		for id, channelDataDict in channelDict.items():
			if not 1 <= id <= len(self.button_ch.get("channel", ())):
				continue
			key=channelDataDict["key"]
			ip=channelDataDict["ip"]
			udp_port=channelDataDict["udp_port"]
			ServerStateChecker.AddChannel(key, ip, udp_port)
		ServerStateChecker.Request()
	
	def NotifyChannelState(self, addrKey, state, count=0):
		# Native connection/send failures use two arguments, even when counts
		# are enabled. Ignore replies without a visible row, including teardown.
		texts = self.button_ch.get("channel_state_text", ())
		images = self.button_ch.get("channel_state", ())
		channels = serverInfo.REGION_DICT.get(0, {}).get(self.server_id, {}).get("channel", {})
		for channelID, channel in channels.items():
			if channel.get("key") != addrKey:
				continue
			index = channelID - 1
			if not 0 <= index < min(len(texts), len(images)):
				return
			if state not in IMAGE_STATE:
				state = 0
			texts[index].SetText(str(serverInfo.STATE_DICT.get(state, serverInfo.STATE_NONE)))
			images[index].LoadImage(IMAGE_STATE[state])
			return

	def GetCodePage(self, lang):
		codePageDict = {
			"en" : 1252,
			"ro" : 1250,
			"it" : 1252,
			"tr" : 1254,
			"de" : 1252,
			"pl" : 1250,
			"pt" : 1252,
			"es" : 1252,
			"cz" : 1250,
			"hu" : 1250,
			"fr" : 1252,
			"ru" : 1251,
			"ae" : 1256,

		}
		try:
			return codePageDict[lang]
		except:
			return 1252

	def GetIndexByName(self, lang):
		langCode = {
			"en" : 0, # 0
			"de" : 1, # 1
			"cz" : 2, # 2
			"fr" : 3, # 3
			"ro" : 4, # 4
			"es" : 5, # 5
			"hu" : 6, # 6
			"it" : 7, # 7
			"pl" : 8, # 8
			"pt" : 9, # 9
			"tr" : 10, # 10
			"ru" : 11, # 11
			"ae" : 12, # 12
		}
		try:
			return langCode[lang]
		except:
			return 2

	def buttonchannel(self, arg):
		self.ChannelButtonArray(arg)
		self.__SaveChannelInfo()
	
	def ChannelButtonArray(self, arg):
		if not arg or arg < 0 or arg >= BASIC_DEF["CH_NUM"]:
			arg = 0

		channelDict = serverInfo.REGION_DICT[0][self.server_id]["channel"]
		if int(arg + 1) not in channelDict:
			arg = 0
		
		self.act_ch = arg
		for i in range(BASIC_DEF["CH_NUM"]):
			if i != arg:
				self.button_ch["channel"][i].SetUp()
		self.button_ch["channel"][arg].Down()
		
		try:
			serverName = serverInfo.REGION_DICT[0][self.server_id]["name"]
			channelName = channelDict[int(arg + 1)]["name"]
		except:
			print(" ERROR __OnClickSelectServerButton(%d, %d, %d)" % (0, 1, (arg + 1)))
			serverName = localeInfo.CHANNEL_EMPTY_SERVER
			channelName = localeInfo.CHANNEL_NORMAL % int(arg + 1)
		
		name_tos = ("|cFFFF8C00%s |cFFFFFFFF- |cFFFFD700%s " % (serverName, channelName))
		net.SetServerInfo(name_tos.strip())
		
		try:
			ip = channelDict[int(arg + 1)]["ip"]
			tcp_port = channelDict[int(arg + 1)]["tcp_port"]
		except:
			import exception
			exception.Abort("LoginWindow.__OnClickSelectServerButton")
		
		try:
			account_ip = serverInfo.REGION_AUTH_SERVER_DICT[0][self.server_id]["ip"]
			account_port = serverInfo.REGION_AUTH_SERVER_DICT[0][self.server_id]["port"]
		except:
			account_ip = 0
			account_port = 0
		
		self.stream.SetConnectInfo(ip, tcp_port, account_ip, account_port)
		constInfo.ch = int(arg + 1)
		
		try:
			markAddrValue=serverInfo.MARKADDR_DICT[self.server_id * 10]
			net.SetMarkServer(markAddrValue["ip"], markAddrValue["tcp_port"])
			app.SetGuildMarkPath(markAddrValue["mark"])
			app.SetGuildSymbolPath(markAddrValue["symbol_path"])
		except:
			import exception
			exception.Abort("LoginWindow.__OnClickSelectServerButton")

	def __OnClickExitButton(self):
		self.stream.SetPhaseWindow(0)

	def __CheckNameLenght(self, arg):
		count = len(self.save_acc["text_buttons"][arg].GetText())
		addSup = False
		while (self.save_acc["text_buttons"][arg].GetTextSize()[0] >= 40):
			base_text = self.save_acc["text_buttons"][arg].GetText()
			self.save_acc["text_buttons"][arg].SetText(base_text[:count] + base_text[count+1:])
			count -= 1
			addSup = True
		
		if addSup:	self.save_acc["text_buttons"][arg].SetText(base_text + "(...)")
	
	def __Link(self, arg):
		os.system("start \"\" %s" % arg)
	
	def PassFunc(self):
		pass
	
	def exitFunc(self):
		app.Exit()
		return False
	
	def PopupNotifyMessage(self, msg, exit, func=0):
		if not func:
			func=self.PassFunc
		
		if exit == True:
			func=self.exitFunc
		
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg, func, localeInfo.UI_OK)
	
	def PopupDisplayMessage(self, msg):
		self.stream.popupWindow.Close()
		self.stream.popupWindow.Open(msg)

	#def __OnClickChangeLanguage(self, language):
	#	self.Languages = { "en" : "1252 en", "de" : "1252 de", "cz" : "1250 cz", "fr" : "1252 fr", "ro" : "1250 ro", "es" : "1252 es", "hu" : "1250 hu", "it" : "1252 it", "pl" : "1250 pl", "pt" : "1252 pt", "tr" : "1254 tr"}
	#	file = open("loca.cfg", "w")
	#	file.write(self.Languages[str(language)])
	#	file.close()
	#	self.PopupNotifyMessage("Please restart the client", self.__OnClickExitButton)

	def RefreshLanguagesBtn(self):
		langs = ["en", "de","cz","fr","ro", "es", "hu", "it", "pl", "pt", "tr", "ru", "ae"]
		for i in range(13):
			if app.GetLocaleName() != langs[i]:
				self.languageList[i].SetUp()
			else:
				self.languageList[i].Down()

	def OnClickLanguageButton(self, lang):
		if app.GetLocaleName() != lang:
			with open("UserData/lang.cfg", "w+") as localeConfig:
				localeConfig.write("%d %s" % (self.GetCodePage(lang), lang))
			
			app.SetDefaultCodePage(self.GetCodePage(lang))
			app.ForceSetLocale(lang, "locale/%s" % (lang))
			self.stream.SetPhaseWindow(0)
			app.ShellExecute("Metin2Release.exe")
			self.OnCloseQuestionDialog()
			app.Exit()

	def OnCloseQuestionDialog(self):
		if not self.questionDialog:
			return
		
		self.RefreshLanguagesBtn()
		self.questionDialog.Close()
		self.questionDialog = None
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)

	def __QuestionChangeLanguage(self, lang):
		if app.GetLocaleName() == lang:
			return
		
		langs = ["en", "de","cz","fr","ro", "es", "hu", "it", "pl", "pt", "tr", "ru", "ae"]
		for i in range(13):
			if lang != langs[i]:
				self.languageList[i].SetUp()
			else:
				self.languageList[i].Down()
		
		self.stream.popupWindow.Close()
		self.questionDialog = uiCommon.QuestionDialog()
		self.questionDialog.SetText(localeInfo.QUESTION_DLG_CHANGELANGUAGE)
		self.questionDialog.SetAcceptEvent(lambda arg = lang: self.OnClickLanguageButton(arg))
		self.questionDialog.SetCancelEvent(self.OnCloseQuestionDialog)
		self.questionDialog.Open()
		sw, sh = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		w, h = self.questionDialog.GetWidth(), self.questionDialog.GetHeight()
		self.questionDialog.SetPosition((sw - w) // 2, (sh - h) // 2)
		constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)

	def OnPressExitKey(self):
		app.Exit()
		return True
