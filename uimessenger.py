import app
import chr
import ui
import grp
import net
import guild
import messenger
import localeInfo
import uiScriptLocale
import constInfo
import osfInfo
import uiToolTip
import uiGameOption

import uiCommon
from _weakref import proxy, ref

# A token supports ownership-safe teardown with older executables too.
_messengerHandlerOwner = None

FRIEND = 0
GUILD = 1
if app.ENABLE_MESSENGER_GM:
	GM = 2
if app.ENABLE_MESSENGER_BLOCK:
	BLOCK = 3


IMG_DIR = "d:/ymir work/ui/game/new_messenger/"

class MessengerItem(ui.Window):
	def __init__(self, getParentEvent):
		ui.Window.__init__(self)

		self.SetParent(getParentEvent())
		self.AddFlag("float")

		self.name = ""
		self.image = ui.ImageBox()
		self.image.AddFlag("not_pick")
		self.image.SetParent(self)
		self.image.Show()
		self.text = ui.TextLine()
		self.text.SetParent(self)
		if app.WJ_MULTI_TEXTLINE:
			self.text.DisableEnterToken()
		self.text.SetPosition(20, 2)
		self.text.Show()

		self.lovePoint = -1
		self.lovePointToolTip = None

		self.isSelected = False

		self.getParentEvent = getParentEvent

	def SetName(self, name):
		self.name = name
		if name:
			self.text.SetText(name)
			self.SetSize(20 + 6*len(name) + 4, 16)

			if localeInfo.IsARABIC():
				self.text.SetPosition(20 + 6*len(name) + 4, 2)

	def SetLovePoint(self, lovePoint):
		self.lovePoint = lovePoint

	def Select(self):
		self.isSelected = True

	def UnSelect(self):
		self.isSelected = False

	def GetName(self):
		return self.name

	def GetStepWidth(self):
		return 0

	# Whisper
	def CanWhisper(self):
		return False

	def IsOnline(self):
		return False

	def OnWhisper(self):
		pass

	# Remove
	def CanRemove(self):
		return False

	def OnRemove(self):
		return False

	# Warp
	def CanWarp(self):
		return False

	def OnWarp(self):
		pass

	def OnMouseOverIn(self):
		if -1 != self.lovePoint:
			if not self.lovePointToolTip:
				self.lovePointToolTip = uiToolTip.ToolTip(100)
				self.lovePointToolTip.SetTitle(self.name)
				self.lovePointToolTip.AppendTextLine(localeInfo.AFF_LOVE_POINT % (self.lovePoint))
				self.lovePointToolTip.ResizeToolTip()
			self.lovePointToolTip.ShowToolTip()

	def OnMouseOverOut(self):
		if self.lovePointToolTip:
			self.lovePointToolTip.HideToolTip()

	def OnMouseLeftButtonDown(self):
		self.getParentEvent().OnSelectItem(self)

	def OnMouseLeftButtonDoubleClick(self):
		self.getParentEvent().OnDoubleClickItem(self)

	def OnRender(self):
		if self.isSelected:
			x, y = self.GetGlobalPosition()
			grp.SetColor(grp.GenerateColor(0.0, 0.0, 0.7, 0.7))
			grp.RenderBar(x+16, y, self.GetWidth()-16, self.GetHeight())

class MessengerMemberItem(MessengerItem):
	STATE_OFFLINE = 0
	STATE_ONLINE = 1

	IMAGE_FILE_NAME = {
		"ONLINE" : "d:/ymir work/ui/game/windows/messenger_list_online.sub",
		"OFFLINE" : "d:/ymir work/ui/game/windows/messenger_list_offline.sub",
	}

	def __init__(self, getParentEvent):
		MessengerItem.__init__(self, getParentEvent)
		self.key = None
		self.state = self.STATE_OFFLINE
		self.Offline()

	def GetStepWidth(self):
		return 15

	def SetKey(self, key):
		self.key = key

	def IsSameKey(self, key):
		return self.key == key

	def IsOnline(self):
		if self.STATE_ONLINE == self.state:
			return True

		return False

	def Online(self):
		self.image.LoadImage(self.IMAGE_FILE_NAME["ONLINE"])
		self.state = self.STATE_ONLINE

	def Offline(self):
		self.image.LoadImage(self.IMAGE_FILE_NAME["OFFLINE"])
		self.state = self.STATE_OFFLINE

	def CanWhisper(self):
		if self.IsOnline():
			return True

		return False

	def OnWhisper(self):
		if self.IsOnline():
			self.getParentEvent().whisperButtonEvent(self.GetName())

	def Select(self):
		MessengerItem.Select(self)

class MessengerGroupItem(MessengerItem):

	IMAGE_FILE_NAME = {	"OPEN" : "d:/ymir work/ui/game/windows/messenger_list_open.sub",
						"CLOSE" : "d:/ymir work/ui/game/windows/messenger_list_close.sub", }

	def __init__(self, getParentEvent):
		self.isOpen = False
		self.memberList = []

		MessengerItem.__init__(self, getParentEvent)

	def AppendMember(self, member, key, name):
		member.SetKey(key)
		member.SetName(name)
		self.memberList.append(member)
		return member

	def RemoveMember(self, item):
		for i in range(len(self.memberList)):
			if item == self.memberList[i]:
				del self.memberList[i]
				return

	def ClearMember(self):
		self.memberList = []

	def FindMember(self, key):
		foundList = list(filter(lambda argMember, argKey = key: argMember.IsSameKey(argKey), self.memberList))
		if foundList:
			return foundList[0]

		return None

	def GetLoginMemberList(self):
		return list(filter(MessengerMemberItem.IsOnline, self.memberList))

	def GetLogoutMemberList(self):
		return list(filter(lambda arg: not arg.IsOnline(), self.memberList))

	def IsOpen(self):
		return self.isOpen

	def Open(self):
		self.image.LoadImage(self.IMAGE_FILE_NAME["OPEN"])
		self.isOpen = True

	def Close(self):
		self.image.LoadImage(self.IMAGE_FILE_NAME["CLOSE"])
		self.isOpen = False

		list(map(ui.Window.Hide, self.memberList))

	def Select(self):

		if self.IsOpen():
			self.Close()
		else:
			self.Open()

		MessengerItem.Select(self)
		self.getParentEvent().OnRefreshList()

class MessengerFriendItem(MessengerMemberItem):
	def __init__(self, getParentEvent):
		MessengerMemberItem.__init__(self, getParentEvent)

	def CanRemove(self):
		return True

	def OnRemove(self):
		messenger.RemoveFriend(self.key)
		net.SendMessengerRemovePacket(self.key, self.name)
		return True

if app.ENABLE_MESSENGER_GM:
	class MessengerGMItem(MessengerMemberItem):
		def __init__(self, getParentEvent):
			MessengerMemberItem.__init__(self, getParentEvent)

		def CanRemove(self):
			return False

if app.ENABLE_MESSENGER_BLOCK:
	class MessengerBlockItem(MessengerMemberItem):
		def __init__(self, getParentEvent):
			MessengerMemberItem.__init__(self, getParentEvent)

		def CanRemove(self):
			return True

		def OnRemove(self):
			messenger.RemoveBlock(self.key)
			net.SendMessengerBlockRemoveByVIDPacket(self.key, self.name)
			return True

class MessengerGuildItem(MessengerMemberItem):
	def __init__(self, getParentEvent):
		MessengerMemberItem.__init__(self, getParentEvent)

	def CanWarp(self):
		if not self.IsOnline():
			return False
		return True

	def OnWarp(self):
		net.SendGuildUseSkillPacket(155, self.key)

	def CanRemove(self):
		#for i in range(guild.ENEMY_GUILD_SLOT_MAX_COUNT):
		#	if guild.GetEnemyGuildName(i) != "":
		#		return False

		if guild.MainPlayerHasAuthority(guild.AUTH_REMOVE_MEMBER):
			if guild.IsMemberByName(self.name):
				return True

		return False

	def OnRemove(self):
		net.SendGuildRemoveMemberPacket(self.key)
		return True

class MessengerTeamItem(MessengerMemberItem):

	def __init__(self, getParentEvent):
		MessengerMemberItem.__init__(self, getParentEvent)

	def CanRemove(self):
		return False

	def OnRemove(self):
		messenger.RemoveFriend(self.key)
		net.SendMessengerRemovePacket(self.key, self.name)
		return False

if app.ENABLE_MESSENGER_GM:
	class MessengerGMGroup(MessengerGroupItem):
		def __init__(self, getParentEvent):
			MessengerGroupItem.__init__(self, getParentEvent)
			self.SetName(localeInfo.MESSENGER_GM)

		def AppendMember(self, key, name):
			item = MessengerGMItem(self.getParentEvent)
			return MessengerGroupItem.AppendMember(self, item, key, name)

if app.ENABLE_MESSENGER_BLOCK:
	class MessengerBlockGroup(MessengerGroupItem):
		def __init__(self, getParentEvent):
			MessengerGroupItem.__init__(self, getParentEvent)
			self.SetName(localeInfo.MESSENGER_BLOCK)

		def AppendMember(self, key, name):
			item = MessengerBlockItem(self.getParentEvent)
			return MessengerGroupItem.AppendMember(self, item, key, name)

class MessengerFriendGroup(MessengerGroupItem):

	def __init__(self, getParentEvent):
		MessengerGroupItem.__init__(self, getParentEvent)
		self.SetName(localeInfo.MESSENGER_FRIEND)

	def AppendMember(self, key, name):
		item = MessengerFriendItem(self.getParentEvent)
		return MessengerGroupItem.AppendMember(self, item, key, name)

class MessengerGuildGroup(MessengerGroupItem):

	def __init__(self, getParentEvent):
		MessengerGroupItem.__init__(self, getParentEvent)
		self.SetName(localeInfo.MESSENGER_GUILD)
		self.AddFlag("float")

	def AppendMember(self, key, name):
		item = MessengerGuildItem(self.getParentEvent)
		return MessengerGroupItem.AppendMember(self, item, key, name)

class MessengerTeamGroup(MessengerGroupItem):

	def __init__(self, getParentEvent):
		MessengerGroupItem.__init__(self, getParentEvent)
		self.SetName(localeInfo.MESSENGER_TEAM_GROUP_NAME)

	def AppendMember(self, key, name):
		item = MessengerTeamItem(self.getParentEvent)
		return MessengerGroupItem.AppendMember(self, item, key, name)

class MessengerFamilyGroup(MessengerGroupItem):

	def __init__(self, getParentEvent):
		MessengerGroupItem.__init__(self, getParentEvent)
		self.SetName(localeInfo.MESSENGER_FAMILY)
		self.AddFlag("float")

		self.lover = None

	def AppendMember(self, key, name):
		item = MessengerGuildItem(self.getParentEvent)
		self.lover = item
		return MessengerGroupItem.AppendMember(self, item, key, name)

	def GetLover(self):
		return self.lover

class MessengerWindow(ui.ScriptWindow):

	START_POSITION = 95

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.board = None
		self.groupList = []
		self.showingItemList = []
		self.selectedItem = None
		self.whisperButtonEvent = lambda *arg: None
		self.unifiedMessengerButton = None
		self.unifiedMessengerButtonEvent = lambda: None
		self.familyGroup = None
		self.scrollBar = None

		self.guildButtonEvent = None

		self.showingPageSize = 0
		self.startLine = 0

		self.isLoaded = 0

		if app.ENABLE_CHATTING_WINDOW_RENEWAL:
			self.interface = None

		self.pageIdx = 0

		self.__AddGroup()
		global _messengerHandlerOwner
		self._messengerHandlerToken = object()
		_messengerHandlerOwner = self._messengerHandlerToken
		messenger.SetMessengerHandler(self)
		getattr(messenger, "RefreshMessenger", messenger.RefreshGuildMember)()

	def Show(self):
		if self.isLoaded==0:
			self.isLoaded=1

			self.__LoadWindow()
			self.OnRefreshList()

		ui.ScriptWindow.Show(self)

	def __LoadWindow(self):
		pyScrLoader = ui.PythonScriptLoader()
		pyScrLoader.LoadScriptFile(self, "UIScript/MessengerWindow.py")

		try:
			self.board = self.GetChild("board")
			self.whisperButton = self.GetChild("WhisperButton")
			self.removeButton = self.GetChild("RemoveButton")
			self.addFriendButton = self.GetChild("AddFriendButton")
			if app.ENABLE_MESSENGER_BLOCK:
				self.addBlockButton = self.GetChild("BlockFriendButton")
			self.guildButton = self.GetChild("GuildButton")
			self.unifiedMessengerButton = self.GetChild("UnifiedMessengerButton")
		except:
			import exception
			exception.Abort("MessengerWindow.__LoadWindow.__Bind")

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))

		self.whisperButton.SetEvent(ui.__mem_func__(self.OnPressWhisperButton))
		self.removeButton.SetEvent(ui.__mem_func__(self.OnPressRemoveButton))
		self.addFriendButton.SetEvent(ui.__mem_func__(self.OnPressAddFriendButton))
		if app.ENABLE_MESSENGER_BLOCK:
			self.addBlockButton.SetEvent(ui.__mem_func__(self.OnPressAddBlockButton))
		self.guildButton.SetEvent(ui.__mem_func__(self.OnPressGuildButton))
		self.unifiedMessengerButton.SetEvent(
			ui.__mem_func__(self.OnPressUnifiedMessengerButton))
		self.scrollBar = ScrollBarSpecial()
		self.scrollBar.SetParent(self.GetChild("page_bg"))
		self.scrollBar.SetPosition(149 - 10, 32)
		self.scrollBar.SetSize(7, 175)
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))
		self.scrollBar.Show()

		for j in range(4):
			self.GetChild("page_{}_btn".format(j)).SAFE_SetEvent(self.__ClickPage, j)

		self.GetChild("search_btn").SetEvent(ui.__mem_func__(self.OnRefreshList))
		self.GetChild("clear_btn").SetEvent(ui.__mem_func__(self.__ClearSearch))
		self.GetChild("editline").OnPressEscapeKey = ui.__mem_func__(self.Close)
		self.GetChild("editline").OnIMEUpdate = ui.__mem_func__(self.OnIMEUpdate)

		self.whisperButton.Disable()
		self.removeButton.Disable()
		self.RefreshUnifiedMessengerButton()

		self.__ClickPage(0)

	def OnPressBlockButton(self):
		pass

	def __ClearSearch(self):
		self.GetChild("editline").SetText("")
		self.OnRefreshList()
	def OnIMEUpdate(self):
		editline = self.GetChild("editline")
		while True:
			if editline.GetTextSize()[0] >= 100:
				text = editline.GetText()
				editline.SetText(text[:len(text)-2])
			else:
				break
		ui.EditLine.OnIMEUpdate(editline)
		self.OnRefreshList()

	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			selButton = buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		selButton.Down()

	def __ClickPage(self, pageIdx):
		if self.pageIdx == pageIdx:
			return
		self.__ClickRadioButton([self.GetChild("page_{}_btn".format(j)) for j in range(4)], pageIdx)
		self.GetChild("page_bg").LoadImage("{}page_{}.png".format(IMG_DIR, pageIdx))
		self.pageIdx = pageIdx
		self.OnSelectItem(None)
		self.OnRefreshList()

	def __del__(self):
		self.__DetachMessengerHandler()
		ui.ScriptWindow.__del__(self)

	def __DetachMessengerHandler(self):
		global _messengerHandlerOwner
		token = getattr(self, "_messengerHandlerToken", None)
		if token is None:
			return
		clearHandler = getattr(messenger, "ClearMessengerHandler", None)
		if clearHandler:
			clearHandler(self)
		elif _messengerHandlerOwner is token:
			messenger.SetMessengerHandler(None)
		if _messengerHandlerOwner is token:
			_messengerHandlerOwner = None
		self._messengerHandlerToken = None

	if app.ENABLE_CHATTING_WINDOW_RENEWAL:
		def BindInterface(self, interface):
			self.interface = proxy(interface)

	def Destroy(self):
		self.__DetachMessengerHandler()
		self.Hide()
		for item in self.showingItemList:
			item.Hide()
		for group in self.groupList:
			for member in group.memberList:
				member.Hide()
			group.memberList = []
			group.Hide()
		self.showingItemList = []
		self.groupList = []
		self.selectedItem = None
		self.whisperButtonEvent = lambda *arg: None
		self.guildButtonEvent = None
		self.ClearDictionary()
		self.board = None
		self.scrollBar = None
		self.friendNameBoard = None
		self.questionDialog = None
		self.popupDialog = None
		self.inputDialog = None
		self.familyGroup = None
		if app.ENABLE_CHATTING_WINDOW_RENEWAL:
			self.interface = None

		self.whisperButton = None
		self.removeButton = None
		self.unifiedMessengerButton = None
		self.unifiedMessengerButtonEvent = lambda: None

	def OnCloseQuestionDialog(self):
		if self.questionDialog:
			self.questionDialog.Close()
		self.questionDialog = None
		return True

	def Close(self):
		self.questionDialog = None
		self.Hide()

	def SetSize(self, width, height):
		ui.ScriptWindow.SetSize(self, width, height)
		if self.board:
			self.board.SetSize(width, height)

	def __LocateMember(self):

		if self.isLoaded==0:
			return

		yPos = self.START_POSITION
		heightLimit = 175

		list(map(ui.Window.Hide, self.showingItemList))

		for item in self.showingItemList[self.startLine:]:
			item.SetPosition(8 + item.GetStepWidth(), yPos)
			item.SetTop()
			item.Show()
			yPos+=20
			if yPos >= self.START_POSITION + heightLimit:
				break

		totalY = len(self.showingItemList) * 20

		if totalY > heightLimit:
			self.scrollBar.SetScale(heightLimit, totalY)
		else:
			self.scrollBar.SetPos(0)
			self.scrollBar.SetScale(175, 175)

	def __AddGroup(self):
		member = MessengerFriendGroup(ui.__mem_func__(self.GetSelf))
		member.Open()
		member.Show()
		self.groupList.append(member)

		member = MessengerGuildGroup(ui.__mem_func__(self.GetSelf))
		member.Open()
		member.Show()
		self.groupList.append(member)

		if app.ENABLE_MESSENGER_GM:
			member = MessengerGMGroup(ui.__mem_func__(self.GetSelf))
			member.Open()
			member.Show()
			self.groupList.append(member)

		if app.ENABLE_MESSENGER_BLOCK:
			member = MessengerBlockGroup(ui.__mem_func__(self.GetSelf))
			member.Open()
			member.Show()
			self.groupList.append(member)

	def __AddFamilyGroup(self):
		member = MessengerFamilyGroup(ui.__mem_func__(self.GetSelf))
		member.Open()
		member.Show()

		self.familyGroup = member

	def ClearGuildMember(self):
		self.groupList[GUILD].ClearMember()

	def SetWhisperButtonEvent(self, event):
		self.whisperButtonEvent=event

	def SetUnifiedMessengerButtonEvent(self, event):
		self.unifiedMessengerButtonEvent = event

	def RefreshUnifiedMessengerButton(self):
		if not self.isLoaded or not self.unifiedMessengerButton:
			return
		if self.__UnifiedMessengerAvailable():
			self.unifiedMessengerButton.Enable()
		else:
			self.unifiedMessengerButton.Disable()

	def __UnifiedMessengerAvailable(self):
		try:
			return bool(net.IsUnifiedMessengerAvailable())
		except:
			return False

	def OnPressUnifiedMessengerButton(self):
		self.unifiedMessengerButtonEvent()

	def SetGuildButtonEvent(self, event):
		self.guildButtonEvent=event

	def OnCloseInputDialog(self):
		self.inputDialog.Close()
		self.inputDialog = None
		return True

	def OnPressGuildButton(self):
		self.guildButtonEvent()

	def OnPressAddFriendButton(self):
		friendNameBoard = uiCommon.InputDialog()
		friendNameBoard.SetTitle(localeInfo.MESSENGER_ADD_FRIEND)
		friendNameBoard.SetMaxLength(chr.PLAYER_NAME_MAX_LEN)
		friendNameBoard.SetAcceptEvent(ui.__mem_func__(self.OnAddFriend))
		friendNameBoard.SetCancelEvent(ui.__mem_func__(self.OnCancelAddFriend))
		friendNameBoard.Open()
		self.friendNameBoard = friendNameBoard

	def OnAddFriend(self):
		text = self.friendNameBoard.GetText()
		if text:
			net.SendMessengerAddByNamePacket(text)

		if self.friendNameBoard:
			self.friendNameBoard.Close()
		self.friendNameBoard = None
		return True

	def OnCancelAddFriend(self):
		self.friendNameBoard.Close()
		self.friendNameBoard = None
		return True

	if app.ENABLE_MESSENGER_BLOCK:
		def OnPressAddBlockButton(self):
			blockNameBoard = uiCommon.InputDialog()
			blockNameBoard.SetTitle(localeInfo.MESSENGER_ADD_BLOCK_FRIEND)
			blockNameBoard.SetMaxLength(chr.PLAYER_NAME_MAX_LEN)
			blockNameBoard.SetAcceptEvent(ui.__mem_func__(self.OnAddBlock))
			blockNameBoard.SetCancelEvent(ui.__mem_func__(self.OnCancelAddBlock))
			blockNameBoard.Open()
			self.blockNameBoard = blockNameBoard

		def OnAddBlock(self):
			text = self.blockNameBoard.GetText()
			if text:
				net.SendMessengerBlockAddByNamePacket(text)
			self.blockNameBoard.Close()
			self.blockNameBoard = None
			return True

		def OnCancelAddBlock(self):
			self.blockNameBoard.Close()
			self.blockNameBoard = None
			return True

	def OnPressWhisperButton(self):
		if not isinstance(self.selectedItem, MessengerMemberItem):
			return
		if self.__UnifiedMessengerAvailable():
			self.whisperButtonEvent(self.selectedItem.GetName())
		elif self.selectedItem.IsOnline():
			self.selectedItem.OnWhisper()

	def OnPressRemoveButton(self):
		if self.selectedItem:
			if self.selectedItem.CanRemove():
				self.questionDialog = uiCommon.QuestionDialog()
				self.questionDialog.SetText(localeInfo.MESSENGER_DO_YOU_DELETE)
				self.questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnRemove))
				self.questionDialog.SetCancelEvent(ui.__mem_func__(self.OnCloseQuestionDialog))
				self.questionDialog.Open()

	def OnRemove(self):
		if self.selectedItem:
			if self.selectedItem.CanRemove():
				list(map(lambda arg, argDeletingItem=self.selectedItem: arg.RemoveMember(argDeletingItem), self.groupList))
				self.selectedItem.OnRemove()
				self.selectedItem.UnSelect()
				self.selectedItem = None
				self.OnRefreshList()

		self.OnCloseQuestionDialog()

	def OnScroll(self):
		scrollLineCount = len(self.showingItemList)

		startLine = int(scrollLineCount * self.scrollBar.GetPos())

		if startLine != self.startLine:
			if startLine+9 > scrollLineCount:
				startLine = scrollLineCount - 9
			if startLine < 0:
				startLine = 0

			self.startLine = startLine
			self.__LocateMember()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	## CallBack
	def OnSelectItem(self, item):

		if self.selectedItem and item != self.selectedItem:
			self.selectedItem.UnSelect()

		self.selectedItem = item

		whisperBtn = getattr(self, "whisperButton", None)
		removeBtn = getattr(self, "removeButton", None)

		if not self.selectedItem:
			if whisperBtn:
				whisperBtn.Disable()
			if removeBtn:
				removeBtn.Disable()
			return

		self.selectedItem.Select()

		if not whisperBtn or not removeBtn:
			return

		canWhisper = self.selectedItem.CanWhisper()
		if (isinstance(self.selectedItem, MessengerMemberItem) and
				self.__UnifiedMessengerAvailable()):
			canWhisper = True
		if canWhisper:
			whisperBtn.Enable()
		else:
			whisperBtn.Disable()

		if self.selectedItem.CanRemove():
			removeBtn.Enable()
		else:
			removeBtn.Disable()

	def OnDoubleClickItem(self, item):

		if not isinstance(self.selectedItem, MessengerMemberItem):
			return

		self.OnPressWhisperButton()

	def GetSelf(self):
		return self

	def OnRefreshList(self):
		list(map(ui.Window.Hide, self.groupList))
		list(map(ui.Window.Hide, self.showingItemList))
		self.showingItemList = []

		if self.familyGroup:
			if self.familyGroup.GetLover() and self.pageIdx == 0:
				self.showingItemList.append(self.familyGroup.GetLover())

		searchText = self.GetChild("editline").GetText().lower() if self.IsChild("editline") else ""

		group = self.groupList[self.pageIdx]
		loginMemberList = group.GetLoginMemberList()
		logoutMemberList = group.GetLogoutMemberList()

		if loginMemberList or logoutMemberList:
			for member in loginMemberList:
				if searchText != "":
					if member.name.lower().find(searchText) == -1:
						continue
			
				self.showingItemList.append(member)
			for member in logoutMemberList:
				if searchText != "":
					if member.name.lower().find(searchText) == -1:
						continue
				self.showingItemList.append(member)

		self.startLine = 0
		if self.scrollBar:
			self.scrollBar.SetPos(0)
		self.__LocateMember()

		if app.ENABLE_CHATTING_WINDOW_RENEWAL:
			if self.interface:
				self.interface.RefreshWhisperMessengerButtons()

	def RefreshMessenger(self):
		self.OnRefreshList()

	## EventHandler
	def __AddList(self, groupIndex, key, name):
		group = self.groupList[groupIndex]
		member = group.FindMember(key)
		if not member:
			member = group.AppendMember(key, name)
			self.OnSelectItem(None)
		return member

	def OnRemoveList(self, groupIndex, key):
		group = self.groupList[groupIndex]
		group.RemoveMember(group.FindMember(key))
		self.OnRefreshList()

	def OnRemoveAllList(self, groupIndex):
		group = self.groupList[groupIndex]
		group.ClearMember()
		self.OnRefreshList()

	def OnLogin(self, groupIndex, key, name=None):
		if not name:
			name = key
		group = self.groupList[groupIndex]
		member = self.__AddList(groupIndex, key, name)
		member.SetName(name)
		member.Online()
		self.OnRefreshList()

	def OnLogout(self, groupIndex, key, name=None):
		group = self.groupList[groupIndex]

		member = self.__AddList(groupIndex, key, name)
		if not name:
			name = key
		member.SetName(name)
		member.Offline()
		self.OnRefreshList()

	def OnAddLover(self, name, lovePoint):
		if not self.familyGroup:
			self.__AddFamilyGroup()

		member = self.familyGroup.AppendMember(0, name)

		member.SetName(name)
		member.SetLovePoint(lovePoint)
		member.Offline()
		self.OnRefreshList()

	def OnUpdateLovePoint(self, lovePoint):
		if not self.familyGroup:
			return

		lover = self.familyGroup.GetLover()
		if not lover:
			return

		lover.SetLovePoint(lovePoint)

	def OnLoginLover(self):
		if not self.familyGroup:
			return

		lover = self.familyGroup.GetLover()
		if not lover:
			return

		lover.Online()

	def OnLogoutLover(self):
		if not self.familyGroup:
			return

		lover = self.familyGroup.GetLover()
		if not lover:
			return

		lover.Offline()

	def ClearLoverInfo(self):
		if not self.familyGroup:
			return

		self.familyGroup.ClearMember()
		self.familyGroup = None
		self.OnRefreshList()

from operator import truediv
import math
class ScrollBarSpecial(ui.Window):
	BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
	CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)
	BAR_NUMB = 9 #This is static value! Please dont touch in him.
	SCROLL_WIDTH= 8
	class MiddleBar(ui.DragButton):
		MIDDLE_BAR_COLOR = grp.GenerateColor(78.0 / 255.0, 65.0 / 255.0, 51.0 / 255.0, 1.0)
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
		ui.Window.__init__(self)
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
			val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) *  self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
			self.middleBar.SetPosition(val, 1)
		self.OnScrollMove()
		return True
	def GetPos(self):
		return float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())
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
		ui.Window.SetSize(self, width, height)
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

# CRIMSON_EMBER_FRIENDS_V16_BEGIN
import messengerportraitresolver
import uicrimsonember

CRIMSON_FRIENDS_IMG_DIR = "d:/ymir work/ui/game/crimson_ember/messenger/"
IMG_DIR = CRIMSON_FRIENDS_IMG_DIR + "page/"
MessengerWindow.START_POSITION = 89
_CrimsonOriginalGroupInit = MessengerGroupItem.__init__
_CrimsonOriginalMemberOnline = MessengerMemberItem.Online
_CrimsonOriginalMemberOffline = MessengerMemberItem.Offline


class _CrimsonNullScrollBar(ui.Window):
	"""API-compatible construction placeholder; it never draws legacy pixels."""
	def __init__(self, horizontal_scroll=False):
		ui.Window.__init__(self)
		self.position = 0.0
		self.scrollEvent = None

	def SetScrollEvent(self, event):
		self.scrollEvent = event

	def GetPos(self):
		return self.position

	def SetPos(self, position, callEvent=True):
		self.position = max(0.0, min(1.0, float(position)))
		if callEvent and self.scrollEvent:
			self.scrollEvent(self.position)

	def SetScale(self, visible, total):
		return

	def SetScrollStep(self, step):
		return

	def OnMouseWheel(self, delta):
		return False


def _CrimsonFriendsActionLabel(primaryName, alternateName=None):
	label = getattr(uiScriptLocale, primaryName, None)
	if label:
		return label
	label = getattr(localeInfo, primaryName, None)
	if label:
		return label
	if alternateName:
		return getattr(localeInfo, alternateName, "")
	return ""


class _CrimsonFriendsActionToolTip(uiToolTip.ToolTip):
	def __init__(self, text):
		width = max(90, len(text or "") * 7 + 20)
		uiToolTip.ToolTip.__init__(self, width)
		self.SetTitle(text)
		self.ResizeToolTip()
		self.HideToolTip()

	def ShowForButton(self, button):
		buttonX, buttonY = button.GetGlobalPosition()
		self.SetFollow(True)
		self.SetToolTipPosition(
			buttonX + button.GetWidth() // 2,
			buttonY - 4,
		)
		self.ShowToolTip()


def _CrimsonResolvePortrait(name):
	return messengerportraitresolver.ResolvePortrait(0, name)


def _CrimsonFriendsItemInit(self, getParentEvent):
	ui.Window.__init__(self)
	self.SetParent(getParentEvent())
	self.AddFlag("float")
	self.SetSize(172, 36)
	self.name = ""
	self.background = ui.ImageBox()
	self.background.SetParent(self)
	self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/member_normal.png")
	self.background.AddFlag("not_pick")
	self.background.Show()
	self.contactIcon = ui.ImageBox()
	self.contactIcon.SetParent(self)
	self.contactIcon.SetPosition(13, 9)
	self.contactIcon.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "portrait/neutral_player.png")
	self.contactIcon.AddFlag("not_pick")
	self.contactIcon.Show()
	self.image = ui.ImageBox()
	self.image.AddFlag("not_pick")
	self.image.SetParent(self)
	self.image.SetPosition(30, 25)
	self.image.Show()
	self.text = ui.TextLine()
	self.text.SetParent(self)
	if app.WJ_MULTI_TEXTLINE:
		self.text.DisableEnterToken()
	self.text.SetPosition(41, 7)
	self.text.SetLimitWidth(129)
	self.text.Show()
	self.statusText = ui.TextLine()
	self.statusText.SetParent(self)
	self.statusText.SetPosition(49, 20)
	self.statusText.SetLimitWidth(122)
	self.statusText.SetPackedFontColor(0xFF67D27A)
	self.statusText.AddFlag("not_pick")
	self.statusText.Hide()
	self.lovePoint = -1
	self.lovePointToolTip = None
	self.isSelected = False
	self.getParentEvent = getParentEvent


def _CrimsonFriendsSetName(self, name):
	self.name = name
	self.text.SetText(name or "")
	self.contactIcon.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "portrait/neutral_player.png")
	self.contactIcon.SetPosition(2, 2)
	self.SetSize(172, 36)


def _CrimsonFriendsRefreshPortrait(self):
	if not self.name or not hasattr(self, "contactIcon"):
		return
	self.contactIcon.LoadImage(_CrimsonResolvePortrait(self.name))
	self.contactIcon.SetPosition(2, 2)


def _CrimsonFriendsOnline(self):
	self.state = self.STATE_ONLINE
	self.image.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "icon/presence_online.png")
	self.image.SetPosition(25, 24)
	self.statusText.SetText("")
	self.statusText.Hide()


def _CrimsonFriendsOffline(self):
	self.state = self.STATE_OFFLINE
	self.image.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "icon/presence_offline.png")
	self.image.SetPosition(25, 24)
	self.statusText.SetText("")
	self.statusText.Hide()


def _CrimsonFriendsSelect(self):
	self.isSelected = True
	self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/member_selected.png")


def _CrimsonFriendsUnselect(self):
	self.isSelected = False
	self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/member_normal.png")


def _CrimsonFriendsOverIn(self):
	if not self.isSelected:
		self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/member_hover.png")
	if -1 != self.lovePoint:
		if not self.lovePointToolTip:
			self.lovePointToolTip = uiToolTip.ToolTip(100)
			self.lovePointToolTip.SetTitle(self.name)
			self.lovePointToolTip.AppendTextLine(localeInfo.AFF_LOVE_POINT % self.lovePoint)
			self.lovePointToolTip.ResizeToolTip()
		self.lovePointToolTip.ShowToolTip()


def _CrimsonFriendsOverOut(self):
	self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/member_" + ("selected" if self.isSelected else "normal") + ".png")
	if self.lovePointToolTip:
		self.lovePointToolTip.HideToolTip()


def _CrimsonFriendsRender(self):
	return


def _CrimsonFriendsGroupInit(self, getParentEvent):
	_CrimsonOriginalGroupInit(self, getParentEvent)
	self.SetSize(172, 18)
	self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/group_divider.png")
	self.contactIcon.Hide()
	self.statusText.Hide()
	self.image.SetPosition(3, 1)
	self.text.SetPosition(22, 1)


class _CrimsonFriendsDivider(ui.Window):
	def __init__(self, owner, groupKey, label, count, collapsed):
		ui.Window.__init__(self)
		self.owner = ref(owner)
		self.groupKey = groupKey
		self.SetParent(owner)
		self.AddFlag("float")
		self.SetSize(172, 18)
		self.background = ui.ImageBox()
		self.background.SetParent(self)
		self.background.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "row/group_divider.png")
		self.background.AddFlag("not_pick")
		self.background.Show()
		self.text = ui.TextLine()
		self.text.SetParent(self)
		self.text.SetPosition(5, 1)
		self.text.SetText("%s (%d)" % (label, int(count)))
		self.text.SetPackedFontColor(0xFFFFE9BD)
		self.text.AddFlag("not_pick")
		self.text.Show()
		self.arrow = ui.ImageBox()
		self.arrow.SetParent(self)
		self.arrow.SetPosition(156, 5)
		iconPath = "icon/group_closed.png" if collapsed else "icon/group_open.png"
		self.arrow.LoadImage(CRIMSON_FRIENDS_IMG_DIR + iconPath)
		self.arrow.AddFlag("not_pick")
		self.arrow.Show()

	def GetStepWidth(self):
		return 0

	def OnMouseLeftButtonDown(self):
		owner = self.owner()
		if owner is not None:
			owner._CrimsonFriendsToggleGroup(self.groupKey)


def _CrimsonFriendsValidStarts(items, heightLimit):
	if not items:
		return [0]
	remainingHeight = sum(item.GetHeight() for item in items)
	lastStart = 0
	while lastStart < len(items) - 1 and remainingHeight > heightLimit:
		remainingHeight -= items[lastStart].GetHeight()
		lastStart += 1
	return list(range(lastStart + 1))


def _CrimsonFriendsLocate(self):
	if self.isLoaded == 0:
		return
	heightLimit = 184
	list(map(ui.Window.Hide, self.showingItemList))
	totalY = sum(item.GetHeight() for item in self.showingItemList)
	validStarts = _CrimsonFriendsValidStarts(self.showingItemList, heightLimit)
	position = self.scrollBar.GetPos() if self.scrollBar else 0.0
	maximumStart = validStarts[-1]
	startIndex = validStarts[int(round(position * (len(validStarts) - 1)))]
	self.startLine = min(startIndex, maximumStart)
	yPos = self.START_POSITION
	for item in self.showingItemList[self.startLine:]:
		itemHeight = item.GetHeight()
		if yPos + itemHeight > self.START_POSITION + heightLimit:
			break
		if hasattr(item, "RefreshPortrait"):
			item.RefreshPortrait()
		item.SetPosition(14, yPos)
		item.SetTop()
		item.Show()
		yPos += itemHeight
	if totalY > heightLimit:
		self.scrollBar.Show()
		self.scrollBar.SetScale(heightLimit, totalY)
		if len(validStarts) > 1:
			self.scrollBar.SetScrollStep(1.0 / float(len(validStarts) - 1))
	else:
		self.scrollBar.SetPos(0, False)
		self.scrollBar.SetScale(heightLimit, heightLimit)
		self.scrollBar.Hide()


def _CrimsonFriendsPixelScroll(self):
	self._MessengerWindow__LocateMember()


def _CrimsonFriendsPresence(self, name):
	needle = str(name or "").lower()
	if not needle:
		return None
	for group in self.groupList:
		for member in getattr(group, "memberList", []):
			if str(member.GetName()).lower() == needle:
				return bool(member.IsOnline())
	return None


def _CrimsonFriendsRefreshPortraits(self):
	for group in self.groupList:
		for member in getattr(group, "memberList", []):
			if hasattr(member, "RefreshPortrait"):
				member.RefreshPortrait()


def _CrimsonFriendsToggleGroup(self, groupKey):
	if not hasattr(self, "crimsonCollapsedGroups"):
		self.crimsonCollapsedGroups = {"online": False, "offline": False}
	if groupKey not in self.crimsonCollapsedGroups:
		return
	self.crimsonCollapsedGroups[groupKey] = not self.crimsonCollapsedGroups[groupKey]
	self.OnSelectItem(None)
	self.OnRefreshList()


def _CrimsonFriendsRefreshList(self):
	list(map(ui.Window.Hide, self.groupList))
	list(map(ui.Window.Hide, self.showingItemList))
	self.showingItemList = []
	searchText = self.GetChild("editline").GetText().lower() if self.IsChild("editline") else ""
	group = self.groupList[self.pageIdx]
	onlineMembers = list(group.GetLoginMemberList())
	offlineMembers = list(group.GetLogoutMemberList())
	if self.familyGroup and self.pageIdx == 0 and self.familyGroup.GetLover():
		lover = self.familyGroup.GetLover()
		(onlineMembers if lover.IsOnline() else offlineMembers).insert(0, lover)
	if searchText:
		onlineMembers = [member for member in onlineMembers if searchText in member.name.lower()]
		offlineMembers = [member for member in offlineMembers if searchText in member.name.lower()]
	if not hasattr(self, "crimsonCollapsedGroups"):
		self.crimsonCollapsedGroups = {"online": False, "offline": False}
	onlineLabel = getattr(localeInfo, "MESSENGER_ONLINE", "Online")
	offlineLabel = getattr(localeInfo, "MESSENGER_OFFLINE", "Offline")
	self.showingItemList.append(_CrimsonFriendsDivider(
		self, "online", onlineLabel, len(onlineMembers),
		self.crimsonCollapsedGroups["online"]))
	if not self.crimsonCollapsedGroups["online"]:
		self.showingItemList.extend(onlineMembers)
	self.showingItemList.append(_CrimsonFriendsDivider(
		self, "offline", offlineLabel, len(offlineMembers),
		self.crimsonCollapsedGroups["offline"]))
	if not self.crimsonCollapsedGroups["offline"]:
		self.showingItemList.extend(offlineMembers)
	self.startLine = 0
	if self.scrollBar:
		try:
			self.scrollBar.SetPos(0, False)
		except TypeError:
			self.scrollBar.SetPos(0)
	self._MessengerWindow__LocateMember()
	self.RefreshCrimsonPortraits()
	if app.ENABLE_CHATTING_WINDOW_RENEWAL and self.interface:
		self.interface.RefreshWhisperMessengerButtons()
	router = getattr(self.interface, "unifiedMessengerRouter", None) if self.interface else None
	window = getattr(router, "window", None) if router else None
	if window and getattr(window, "loaded", False):
		window.RefreshConversations()


def _CrimsonFriendsClickPage(self, pageIdx):
	self._MessengerWindow__ClickRadioButton(
		[self.GetChild("page_{}_btn".format(j)) for j in range(4)], pageIdx)
	self.pageIdx = pageIdx
	self.OnSelectItem(None)
	self.OnRefreshList()


def _CrimsonFriendsMouseInList(self):
	mouseX, mouseY = self.GetMouseLocalPosition()
	return mouseX >= 14 and mouseX < 186 and mouseY >= 89 and mouseY < 273


def _CrimsonFriendsMouseWheel(self, isDown):
	if _CrimsonFriendsMouseInList(self):
		self.scrollBar.OnMouseWheel(-1 if isDown else 1)
	return True


_CrimsonOriginalFriendsLoadWindow = MessengerWindow._MessengerWindow__LoadWindow
_CrimsonOriginalFriendsDestroy = MessengerWindow.Destroy


def _CrimsonFriendsLoadWindow(self):
	global ScrollBarSpecial
	legacyScrollBarClass = ScrollBarSpecial
	ScrollBarSpecial = _CrimsonNullScrollBar
	try:
		result = _CrimsonOriginalFriendsLoadWindow(self)
	finally:
		ScrollBarSpecial = legacyScrollBarClass
	self.crimsonSearchBackground = self.GetChild("SearchBG")
	self.crimsonSearchHint = self.GetChild("FriendsSearchHint")
	self.GetChild("editline").SetOnFocusEvent(ui.__mem_func__(self._CrimsonSearchFocus))
	self.GetChild("editline").SetKillFocusEvent(ui.__mem_func__(self._CrimsonSearchBlur))
	self.GetChild("editline").OnIMEUpdate = ui.__mem_func__(self._CrimsonSearchIMEUpdate)
	self.scrollBar.Hide()
	self.scrollBar = uicrimsonember.CrimsonScrollBar()
	self.scrollBar.SetParent(self)
	self.scrollBar.SetPosition(184, 89)
	self.scrollBar.SetScrollBarSize(184)
	self.scrollBar.SetScrollEvent(ui.__mem_func__(self._CrimsonFriendsPixelScroll))
	self.scrollBar.Hide()
	self.SetOnRunMouseWheelEvent(
		ui.__mem_func__(self._CrimsonFriendsMouseWheel))
	self.crimsonCollapsedGroups = {"online": False, "offline": False}
	self.crimsonActionToolTips = []
	self.crimsonTooltipButtons = []
	actionButtons = (
		(self.addFriendButton,
			_CrimsonFriendsActionLabel("MESSENGER_ADD_FRIEND")),
		(self.whisperButton,
			_CrimsonFriendsActionLabel("MESSENGER_WHISPER", "WHISPER_NAME")),
		(self.removeButton,
			_CrimsonFriendsActionLabel("MESSENGER_DELETE_FRIEND")),
		(self.guildButton,
			_CrimsonFriendsActionLabel("MESSENGER_OPEN_GUILD")),
	)
	if app.ENABLE_MESSENGER_BLOCK:
		actionButtons += ((self.addBlockButton,
			_CrimsonFriendsActionLabel("MESSENGER_BLOCK_FRIEND", "WHISPER_BAN")),)
	for button, label in actionButtons:
		if button.ToolTipText:
			button.ToolTipText.Hide()
		tooltip = _CrimsonFriendsActionToolTip(label)
		button.ToolTipText = None
		button.SetShowToolTipEvent(tooltip.ShowForButton, button)
		button.SetHideToolTipEvent(tooltip.HideToolTip)
		self.crimsonActionToolTips.append(tooltip)
		self.crimsonTooltipButtons.append(button)
	self.OnRefreshList()
	return result


def _CrimsonFriendsDestroy(self):
	for tooltip in getattr(self, "crimsonActionToolTips", []):
		tooltip.HideToolTip()
	for button in getattr(self, "crimsonTooltipButtons", []):
		button.SetShowToolTipEvent(None)
		button.SetHideToolTipEvent(None)
	self.crimsonActionToolTips = []
	self.crimsonTooltipButtons = []
	_CrimsonOriginalFriendsDestroy(self)


def _CrimsonFriendsSearchFocus(self):
	self.crimsonSearchBackground.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "field/search_focused.png")
	self.crimsonSearchHint.Hide()


def _CrimsonFriendsSearchBlur(self):
	self.crimsonSearchBackground.LoadImage(CRIMSON_FRIENDS_IMG_DIR + "field/search_normal.png")
	if not self.GetChild("editline").GetText():
		self.crimsonSearchHint.Show()


def _CrimsonFriendsSearchIMEUpdate(self):
	ui.EditLine.OnIMEUpdate(self.GetChild("editline"))
	if self.GetChild("editline").GetText():
		self.crimsonSearchHint.Hide()
	else:
		self.crimsonSearchHint.Show()
	self.OnRefreshList()


def _CrimsonFriendsOnUpdate(self):
	messengerportraitresolver.Pump()


MessengerItem.__init__ = _CrimsonFriendsItemInit
MessengerItem.SetName = _CrimsonFriendsSetName
MessengerItem.RefreshPortrait = _CrimsonFriendsRefreshPortrait
MessengerItem.Select = _CrimsonFriendsSelect
MessengerItem.UnSelect = _CrimsonFriendsUnselect
MessengerItem.OnMouseOverIn = _CrimsonFriendsOverIn
MessengerItem.OnMouseOverOut = _CrimsonFriendsOverOut
MessengerItem.OnRender = _CrimsonFriendsRender
MessengerMemberItem.Online = _CrimsonFriendsOnline
MessengerMemberItem.Offline = _CrimsonFriendsOffline
MessengerGroupItem.__init__ = _CrimsonFriendsGroupInit
MessengerWindow.START_POSITION = 89
MessengerWindow._MessengerWindow__LocateMember = _CrimsonFriendsLocate
MessengerWindow._MessengerWindow__LoadWindow = _CrimsonFriendsLoadWindow
MessengerWindow.Destroy = _CrimsonFriendsDestroy
MessengerWindow._MessengerWindow__ClickPage = _CrimsonFriendsClickPage
MessengerWindow.OnRefreshList = _CrimsonFriendsRefreshList
MessengerWindow._CrimsonFriendsPixelScroll = _CrimsonFriendsPixelScroll
MessengerWindow._CrimsonFriendsMouseWheel = _CrimsonFriendsMouseWheel
MessengerWindow.GetCrimsonPresence = _CrimsonFriendsPresence
MessengerWindow.RefreshCrimsonPortraits = _CrimsonFriendsRefreshPortraits
MessengerWindow._CrimsonFriendsToggleGroup = _CrimsonFriendsToggleGroup
MessengerWindow._CrimsonSearchFocus = _CrimsonFriendsSearchFocus
MessengerWindow._CrimsonSearchBlur = _CrimsonFriendsSearchBlur
MessengerWindow._CrimsonSearchIMEUpdate = _CrimsonFriendsSearchIMEUpdate
MessengerWindow.OnUpdate = _CrimsonFriendsOnUpdate
# CRIMSON_EMBER_FRIENDS_V16_END
