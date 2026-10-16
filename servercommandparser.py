import net
import background
import stringCommander
import constInfo
import app
import featureavailability

class ServerCommandParser(object):
	def __init__(self):
		net.SetServerCommandParserWindow(self)
		self.__ServerCommand_Build()

	def __ServerCommand_Build(self):
		serverCommandList = {
			"DayMode" : self.__DayMode_Update,
			"xmas_snow" : self.__XMasSnow_Enable,
			"xmas_boom" : self.__XMasBoom_Enable,
			"xmas_tree" : self.__XMasTree_Enable,
			"newyear_boom" : self.__XMasBoom_Enable,
			"item_mall" : self.__ItemMall_Open,
			"ResonanceSealValuesV1" : self.__PreserveSealValues,
			"PetAlbumCapabilityV1" : self.__PreserveAlbumCapability,
			# Only state is kept while loading; no window exists to answer.
			"FeatureAvailabilityV1" : featureavailability.receiver.Receive,
		}

		if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
			serverCommandList["auto_loginoff"] = self.__AutoOff

		self.serverCommander = stringCommander.Analyzer()
		for serverCommandItem in serverCommandList.items():
			self.serverCommander.SAFE_RegisterCallBack(serverCommandItem[0], serverCommandItem[1])

	def BINARY_ServerCommand_Run(self, line):
		try:
			print(" BINARY_ServerCommand_Reserve", line)
			return self.serverCommander.Run(line)
		except RuntimeError as msg:
			import dbg
			dbg.TraceError(msg)
			return 0

	def __PreserveCommand(self, line):
		net.PreserveServerCommand(line)

	def __PreserveAlbumCapability(self, digest, epoch, profile, active):
		# Warp offers can arrive while the loading window owns the phase.
		# Replay only the capability; the game window requests a fresh snapshot.
		self.__PreserveCommand("PetAlbumCapabilityV1 %s %s %s %s" %
			(digest, epoch, profile, active))

	def __PreserveSealValues(self, payload):
		self.__PreserveCommand("ResonanceSealValuesV1 " + payload)

	def __DayMode_Update(self, mode):
		self.__PreserveCommand("PRESERVE_DayMode " + mode)

	def __ItemMall_Open(self):
		self.__PreserveCommand("item_mall")

	## 임시
	def __XMasBoom_Enable(self, mode):
		if "1" == mode:
			self.__PreserveCommand("PRESERVE_DayMode dark")
		else:
			self.__PreserveCommand("PRESERVE_DayMode light")

	def __XMasSnow_Enable(self, mode):
		self.__PreserveCommand("xmas_snow " + mode)

	def __XMasTree_Enable(self, grade):
		self.__PreserveCommand("xmas_tree " + grade)

	if app.ENABLE_AUTOMATIC_HUNTING_SYSTEM:
		def __AutoOff(self, enable):
			self.__PreserveCommand("auto_loginoff")

parserWnd = ServerCommandParser()
