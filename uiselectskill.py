import ui
import event
import constInfo
import osfinfo
import app
import uiCommon
import chat
import net
import player
import playerSettingModule
import localeInfo
import wndMgr

JOB_NAME_DICT = {
	0	:	[localeInfo.JOB_WARRIOR1,localeInfo.JOB_WARRIOR2],
	1	:	[localeInfo.JOB_ASSASSIN1,localeInfo.JOB_ASSASSIN2],
	2	:	[localeInfo.JOB_SURA1,localeInfo.JOB_SURA2],
	3	:	[localeInfo.JOB_SHAMAN1,localeInfo.JOB_SHAMAN2],
}
if not app.DISABLE_WOLFMAN_CREATION:
	JOB_NAME_DICT.update({4 : [localeInfo.JOB_WOLFMAN1,localeInfo.JOB_WOLFMAN2],})

JOB_LIST = {
	0	:	localeInfo.JOB_WARRIOR,
	1	:	localeInfo.JOB_ASSASSIN,
	2	:	localeInfo.JOB_SURA,
	3	:	localeInfo.JOB_SHAMAN,
}

FACE_IMAGE_DICT = {
	playerSettingModule.RACE_WARRIOR_M	: "icon/face/warrior_m.tga",
	playerSettingModule.RACE_WARRIOR_W	: "icon/face/warrior_w.tga",
	playerSettingModule.RACE_ASSASSIN_M	: "icon/face/assassin_m.tga",
	playerSettingModule.RACE_ASSASSIN_W	: "icon/face/assassin_w.tga",
	playerSettingModule.RACE_SURA_M		: "icon/face/sura_m.tga",
	playerSettingModule.RACE_SURA_W		: "icon/face/sura_w.tga",
	playerSettingModule.RACE_SHAMAN_M	: "icon/face/shaman_m.tga",
	playerSettingModule.RACE_SHAMAN_W	: "icon/face/shaman_w.tga",
}

if not app.DISABLE_WOLFMAN_CREATION:
	JOB_LIST.update({4 : localeInfo.JOB_WOLFMAN,})

class SkillSelectWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		try:
			PythonScriptLoader = ui.PythonScriptLoader()
			PythonScriptLoader.LoadScriptFile(self, "UIScript/selectskillwindow.py")
		except:
			import exception
			exception.Abort("SelectSkill.LoadWindow.LoadObject")

		try:
			self.__BindObjects()
		except:
			import exception
			exception.Abort("SelectSkill.LoadWindow.BindObject")

		self.__BindEvents()

	def __BindObjects(self):
		self.titlebar = self.GetChild("TitleBar")

		self.selectButtonFirst = self.GetChild("SelectButtonFirst")
		self.selectButtonSecond = self.GetChild("SelectButtonSecond")

		self.firstSkillSlotBack = self.GetChild("FirstSkillSlotBack")
		self.secondSkillSlotBack = self.GetChild("SecondSkillSlotBack")

		self.raceImage = self.GetChild("RaceImage")
		self.infoText = self.GetChild("InfoText")
		self.firstSkillSlot = self.GetChild("FirstSkillSlot")
		self.secondSkillSlot = self.GetChild("SecondSkillSlot")

	def __BindEvents(self):
		self.titlebar.SetCloseEvent(ui.__mem_func__(self.Close))

		self.selectButtonFirst.SetEvent(ui.__mem_func__(self.__SelectFirstJob))
		self.selectButtonSecond.SetEvent(ui.__mem_func__(self.__SelectSecondJob))

		self.selectButtonFirst.SetText(JOB_NAME_DICT[self.GetRealRace()][0])
		self.selectButtonSecond.SetText(JOB_NAME_DICT[self.GetRealRace()][1])

		self.infoText.SetText("%s - %s" % (player.GetName(), JOB_LIST[self.GetRealRace()]))
		self.raceImage.LoadImage(FACE_IMAGE_DICT[net.GetMainActorRace()])

		if self.GetRealRace() == 4:
			self.selectButtonSecond.SetEvent(ui.__mem_func__(__self.EmptyFunc))

			for k in range(self.GetSkillsCount()):
				self.secondSkillSlotBack.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

				self.secondSkillSlot.ClearSlot(k)
				self.secondSkillSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

		for i in range(self.GetSkillsCount()):
			self.firstSkillSlotBack.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

			self.firstSkillSlot.SetSkillSlotNew(i, self.GetSkillIndex()+i, 3, 1)
			self.firstSkillSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

		if self.GetRealRace() != 4:
			for j in range(self.GetSkillsCount()):
				self.secondSkillSlotBack.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

				self.secondSkillSlot.SetSkillSlotNew(j, self.GetSkillIndex()+j+15, 3, 1)
				self.secondSkillSlot.SetSlotStyle(wndMgr.SLOT_STYLE_NONE)

	def GetSkillIndex(self):
		if self.GetRealRace() == 4:
			return 170
		else:
			return self.GetRealRace() * 30 + 1

	def GetRealRace(self):
		race = net.GetMainActorRace()
		if race >= 4:
			return race-4
		else:
			return race

	def GetSkillsCount(self):
		if osfinfo.ARE_ENABLED_6TH_SKILLS == 1:
			return 6
		else:
			if self.GetRealRace() < 2:
				return 5
			elif self.GetRealRace() >= 2:
				return 6

	def EmptyJob(self):
		chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.JOB_SELECT_LYCAN_ERROR)

	def __SelectFirstJob(self):
		net.SendChatPacket("/selectskill_select 1")
		self.Close()

	def __SelectSecondJob(self):
		net.SendChatPacket("/selectskill_select 2")
		self.Close()

	def Open(self):
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Close(self):
		self.Hide()
		return True

	def Destroy(self):
		self.Close()
		self.ClearDictionary()
