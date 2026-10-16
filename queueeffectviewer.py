"""Local native queue editor, selected before the normal network bootstrap."""
import app
import dbg
import fontconfig
import grp
import localeInfo
import mouseModule
import systemSetting
import ui
import wndMgr
import WikiRenderTarget

import metinqueuepresets
import uimetinqueueeditor


class OfflinePreviewHost(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("not_pick")
		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		# Release frames clear depth only. Paint the entire backbuffer before
		# the editor children so moving the window or cursor leaves no trails.
		self.background = ui.Bar()
		self.background.SetParent(self)
		self.background.AddFlag("not_pick")
		self.background.SetColor(grp.GenerateColor(0.045, 0.043, 0.052, 1.0))
		self.background.SetSize(self.GetWidth(), self.GetHeight())
		self.background.Show()

	def OnUpdate(self):
		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.background.SetSize(self.GetWidth(), self.GetHeight())

	def OnRender(self):
		# A parent renders before its editor children sample the native texture.
		# Match the existing character-selection renderer's state boundary.
		grp.SetGameRenderState()
		grp.PushState()
		try:
			grp.SetOmniLight()
			# UI updates are capped at 60 Hz; effect time must advance once per
			# actual render frame, matching the live 120/240 Hz native path.
			WikiRenderTarget.UpdateOfflineMetinQueuePreview()
			WikiRenderTarget.RenderOfflineMetinQueuePreview()
		finally:
			grp.PopState()
			grp.SetInterfaceRenderState()


def RunQueueEffectViewer():
	if not metinqueuepresets.HasV2() or not all(hasattr(WikiRenderTarget, name) for name in (
		"InitializeOfflineMetinQueuePreview", "UpdateOfflineMetinQueuePreview",
		"RenderOfflineMetinQueuePreview")):
		dbg.LogBox(u"Náhled fronty vyžaduje klienta a balíčky s podporou editoru V2.")
		return
	# ui has already loaded the owner's font preference through the normal loader.
	localeInfo.UI_DEF_FONT = fontconfig.FontForRole(fontconfig.ROLE_BODY)
	localeInfo.UI_DEF_FONT_SMALL = fontconfig.FontForRole(fontconfig.ROLE_DENSE)
	localeInfo.UI_DEF_FONT_BOLD = fontconfig.FontForRole(fontconfig.ROLE_CONTROL)
	localeInfo.UI_DEF_FONT_LARGE_BOLD = fontconfig.FontForRole(fontconfig.ROLE_LARGE_BOLD)
	localeInfo.UI_DEF_FONT_LARGE = fontconfig.FONT_LARGE
	width, height = systemSetting.GetWidth(), systemSetting.GetHeight()
	app.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(width, height)
	try:
		if app.ENABLE_DISCORD_STUFF:
			app.Create(u"Althea — náhled fronty", localeInfo.APP_MINI_TITLE, width, height, 1)
		else:
			app.Create(u"Althea — náhled fronty", width, height, 1)
	except RuntimeError as error:
		dbg.LogBox(u"Náhled nelze otevřít: %s" % error)
		return
	app.SetCamera(1500.0, 30.0, 0.0, 180.0)
	if not mouseModule.mouseController.Create():
		return
	ui.SetCrimsonGameControlsEnabled(True)
	editor = None
	host = None
	try:
		# Normal local prototypes, then the narrow native npclist/race-height and
		# queue-effect bootstrap. Neither path starts a stream or login phase.
		localeInfo.LoadLocaleData()
		if not WikiRenderTarget.InitializeOfflineMetinQueuePreview():
			raise RuntimeError("Offline queue model/effect initialization failed")
		host = OfflinePreviewHost()
		host.Show()
		editor = uimetinqueueeditor.MetinQueueEditor(
			metinqueuepresets.OfflineBackend(), app.Exit)
		editor.SetParent(host)
		editor.Open()
		app.Loop()
	finally:
		if editor:
			editor.Destroy()
		if host:
			host.Hide()
		ui.SetCrimsonGameControlsEnabled(False)
		mouseModule.mouseController.Destroy()


RunQueueEffectViewer()
