import ui
import wndMgr
import localeInfo
import app
import time

def MapIDToName(idx):
	if idx == 66:
		return localeInfo.DUNGEON_INFO_DEVILTOWER
	elif idx == 217:
		return localeInfo.DUNGEON_INFO_BARONESS
	elif idx == 216:
		return localeInfo.DUNGEON_INFO_DEVILS_CATACOMB
	elif idx == 208:
		return localeInfo.DUNGEON_INFO_BERAN_SETAOU
	elif idx == 351:
		return localeInfo.DUNGEON_INFO_PURGATORY
	elif idx == 352:
		return localeInfo.DUNGEON_INFO_SNOW
	elif idx == 353:
		return localeInfo.DUNGEON_INFO_EREBUS
	elif idx == 358:
		return localeInfo.DUNGEON_INFO_HYDRA
	else:
		return ""

global_t = (0,24,60)
def CalculateTimeLeft(iTime):
	if iTime <= 0:
		return "00:00:00"

	A, B = divmod(iTime, global_t[2])
	C, A = divmod(A, global_t[2])
	return "%02d:%02d:%02d" % (C, A, B)

class DungeonTimeWindow(ui.ScriptWindow):

	def __init__(self):
		self.isLoaded = 0

		self.backGround = None
		self.mapIndex = 0
		self.endTime = 0

		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/dungeontime.py")
		except:
			import exception
			exception.Abort("DungeonTimeWindow.__LoadWindow error")

		try:
			self.backGround = self.GetChild("board")
			self.remainingTime = self.GetChild("remaining")
			self.mapName = self.GetChild("mapName")

		except:
			import exception
			exception.Abort("DungeonTimeWindow.LoadWindow.BindObject")

	def Refresh(self, mapIndex, remainingTime):
		self.mapIndex = mapIndex
		self.endTime = remainingTime

		self.remainingTime.SetText(CalculateTimeLeft(remainingTime - app.GetGlobalTimeStamp()))
		self.mapName.SetText(MapIDToName(mapIndex))

	def Show(self, mapIndex, remainingTime):
		if self.backGround:
			self.mapIndex = mapIndex
			self.endTime = remainingTime

			self.backGround.LoadImage("d:/ymir work/ui/game/dungeon_info/notification/%s.png" % (str(mapIndex)))
			self.remainingTime.SetText(CalculateTimeLeft(remainingTime - app.GetGlobalTimeStamp()))
			self.mapName.SetText(MapIDToName(mapIndex))

		ui.ScriptWindow.Show(self)

	def OnUpdate(self):
		if not self.backGround:
			return

		if self.IsShow():
			self.remainingTime.SetText(CalculateTimeLeft(self.endTime - app.GetGlobalTimeStamp()))

	def Hide(self):
		ui.ScriptWindow.Hide(self)

	def Destroy(self):
		self.ClearDictionary()
		self.board = None
		self.mapIndex = 0
		self.endTime = 0

	def __del__(self):
		ui.ScriptWindow.__del__(self)
