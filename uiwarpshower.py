import app
import dbg
import ui
import uiScriptLocale

class WarpShowerWindow(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.loadingWindow = None
		self.loadingAniImage = None
		self.warpLogoMark = None

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Open(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "WarpShowerWindow.py")
		except:
			dbg.TraceError("WarpShowerWindow.Open - base overlay unavailable")
			return

		try:
			self.loadingWindow = self.GetChild("LoadingWindow")
		except:
			dbg.TraceError("WarpShowerWindow.Open - loading window unavailable")
			self.Show()
			return

		self.__CreateDecorations()
		self.Show()

	def __CreateDecorations(self):
		try:
			loadingAniImage = ui.AniImageBox()
			loadingAniImage.SetParent(self.loadingWindow)
			loadingAniImage.SetPosition(0, 0)
			loadingAniImage.SetDelay(3)
			for frame in range(10, 23):
				loadingAniImage.AppendImage(uiScriptLocale.LOCALE_UISCRIPT_PATH + "loading/%d.png" % frame)
			loadingAniImage.Show()
			self.loadingAniImage = loadingAniImage
		except:
			self.loadingAniImage = None
			dbg.TraceError("WarpShowerWindow.Open - ring decoration unavailable")

		try:
			warpLogoMark = ui.ImageBox()
			warpLogoMark.SetParent(self.loadingWindow)
			warpLogoMark.SetPosition(94, 94)
			warpLogoMark.LoadImage(uiScriptLocale.LOCALE_UISCRIPT_PATH + "loading/warp_logo_mark_128.png")
			warpLogoMark.Show()
			self.warpLogoMark = warpLogoMark
		except:
			self.warpLogoMark = None
			dbg.TraceError("WarpShowerWindow.Open - logo decoration unavailable")

	def Close(self):
		self.loadingAniImage = None
		self.warpLogoMark = None
		self.loadingWindow = None
		self.Hide()

	def Destroy(self):
		self.Close()

	def OnPressEscapeKey(self):
		return True
