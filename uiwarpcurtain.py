# -*- coding: utf-8 -*-
"""Top-most warp curtain drawn while a seamless warp reconnects.

Owned by networkModule.MainStream (one instance per client run), driven by
the EXE's BINARY_WarpCurtainBegin/End and BINARY_SeamlessWarpLeave/Arrive
hooks. The timing lives in warpcurtainmodel; this module only draws: the
shared intro atmosphere art (or a per-map wallpaper listed in
MAP_WALLPAPERS), the loading logo and the destination's title. The window
is pickable and full screen, so it swallows mouse input while it covers the
world; the game window asks IsInputLocked() for keyboard input.
"""

import app
import background
import dbg
import grp
import player
import chr
import ui
import wndMgr

import introbackground
import localeInfo
import warpcurtainmodel

# Map index (base map, i.e. private index // 10000) -> wallpaper image path.
# Empty: every map uses the shared atmosphere art. Add reviewed art here.
MAP_WALLPAPERS = {}


def BaseMapIndex(mapIndex):
	mapIndex = int(mapIndex)
	return mapIndex // 10000 if mapIndex >= 10000 else mapIndex


def ResolveWallpaper(mapIndex):
	return MAP_WALLPAPERS.get(BaseMapIndex(mapIndex))


def ResolveMapTitle(mapIndex):
	try:
		import gmmapcatalog
		import maparrivalnames
		base = BaseMapIndex(mapIndex)
		for index, internalName in gmmapcatalog.RUNTIME_MAPS:
			if index == base:
				return maparrivalnames.resolve(internalName) or ""
	except Exception:
		pass
	return ""


def _MarkWarpTimeline(stage):
	mark = getattr(app, "MarkWarpTimeline", None)
	if mark:
		try:
			mark(stage)
		except Exception:
			pass


class WarpCurtain(ui.Bar):
	def __init__(self):
		ui.Bar.__init__(self, "CURTAIN")
		if getattr(wndMgr, "IME_RETURN_PRIORITY", 0) == 1:
			self.AddFlag("ime_return_priority")
		self.SetWindowName("WarpCurtain")
		self.AddFlag("float")
		self.model = warpcurtainmodel.WarpCurtainModel()
		self.lastUpdateTime = None
		# In-game frame clock feeding the model's settle baseline.
		self.lastGameFrameTime = None
		self.gameFrameSampling = True
		self.artworkSize = None
		self.artworkImage = None
		self.background = None
		self.logo = None
		self.title = None
		self.__CreateArtwork()
		self.__Apply()
		self.Hide()

	def OnIMEReturn(self):
		return True

	def __del__(self):
		ui.Bar.__del__(self)

	def Destroy(self):
		self.model.Reset()
		self.Hide()
		self.background = None
		self.logo = None
		self.title = None

	# Artwork -------------------------------------------------------------
	def __CreateArtwork(self):
		width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		self.SetSize(width, height)
		try:
			background = ui.ExpandedImageBox()
			background.SetParent(self)
			background.AddFlag("not_pick")
			logo = ui.ExpandedImageBox()
			logo.SetParent(self)
			logo.AddFlag("not_pick")
			title = ui.TextLine()
			title.SetParent(self)
			title.AddFlag("not_pick")
			title.SetFontName(getattr(localeInfo, "UI_DEF_FONT_LARGE", localeInfo.UI_DEF_FONT))
			title.SetHorizontalAlignCenter()
			title.SetOutline()
			self.background, self.logo, self.title = background, logo, title
			self.__LayoutArtwork(None)
		except Exception as error:
			# A missing decorative texture leaves the plain dark curtain.
			dbg.TraceError("WarpCurtain artwork unavailable: %s" % error)
			self.background = self.logo = self.title = None

	def __LayoutArtwork(self, mapIndex):
		width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		self.SetSize(width, height)
		self.artworkSize = (width, height)
		if not self.background:
			return
		wallpaper = ResolveWallpaper(mapIndex) if mapIndex is not None else None
		spec = introbackground.get_background_spec(width, height)
		if wallpaper:
			spec = dict(spec, image=wallpaper)
		introbackground.apply_spec(self.background, spec)
		self.artworkImage = wallpaper
		introbackground.apply_spec(self.logo, introbackground.get_logo_spec(width, height))
		self.background.Show()
		self.logo.Show()
		self.title.SetPosition(width // 2, max(0, height - 120))
		self.title.Show()

	def __SetTitle(self, mapIndex):
		if self.title:
			self.title.SetText(ResolveMapTitle(mapIndex))

	def __Apply(self):
		alpha = self.model.alpha
		self.SetColor(grp.GenerateColor(0.0, 0.0, 0.0, alpha))
		for image in (self.background, self.logo):
			if image:
				image.SetAlpha(alpha)
		if self.title:
			self.title.SetPackedFontColor(grp.GenerateColor(0.92, 0.88, 0.80, alpha))

	# Hooks (networkModule.MainStream) -----------------------------------------
	def Begin(self, mapIndex, kind):
		try:
			# Re-layout only when the screen or the wallpaper changes, so a
			# warp start never decodes artwork again on the same frame.
			if self.artworkSize != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()) or \
					ResolveWallpaper(mapIndex) != self.artworkImage:
				self.__LayoutArtwork(mapIndex)
			self.__SetTitle(mapIndex)
		except Exception as error:
			dbg.TraceError("WarpCurtain layout failed: %s" % error)
		started = self.model.Begin(app.GetTime(), mapIndex, kind)
		self.lastUpdateTime = None
		self.__Apply()
		self.SetTop()
		self.Show()
		return started

	def Leave(self):
		self.model.Leave(app.GetTime())
		self.__Apply()
		self.SetTop()
		self.Show()

	def Arrive(self):
		self.model.Arrive(app.GetTime())
		self.lastUpdateTime = None

	def End(self, result):
		self.model.End(app.GetTime(), result)

	def Abort(self):
		if self.model.Abort():
			self.__Apply()
		self.Hide()

	def SampleGameFrame(self):
		"""Called by the game window once per in-game update (not while a
		seamless warp reconnects). Never raises: a failure only stops the
		adaptive baseline, and the settle falls back to the floor."""
		if not self.gameFrameSampling:
			return
		try:
			now = app.GetTime()
			if self.model.IsActive():
				self.lastGameFrameTime = None
				return
			if self.lastGameFrameTime is not None:
				self.model.SampleGameFrame((now - self.lastGameFrameTime) * 1000.0)
			self.lastGameFrameTime = now
		except Exception as error:
			self.gameFrameSampling = False
			dbg.TraceError("WarpCurtain frame baseline disabled: %s" % error)

	def IsActive(self):
		return self.model.IsActive()

	def IsInputLocked(self):
		return self.model.IsInputLocked()

	def IsCovering(self):
		return self.model.IsCovering()

	def OnUpdate(self):
		now = app.GetTime()
		frameMs = None
		if self.lastUpdateTime is not None:
			frameMs = (now - self.lastUpdateTime) * 1000.0
		self.lastUpdateTime = now
		mainIndex = player.GetMainCharacterIndex()
		actorReady = bool(mainIndex) and bool(chr.HasInstance(mainIndex))
		worldReady = actorReady
		ready = getattr(background, "IsWorldReady", None)
		if ready:
			worldReady = worldReady and bool(ready())
		for event in self.model.Update(now, frameMs, worldReady, strictReady=bool(ready), actorReady=actorReady):
			if event == warpcurtainmodel.EVENT_REVEAL_START:
				_MarkWarpTimeline("reveal_start")
			elif event == warpcurtainmodel.EVENT_REVEAL_DONE:
				_MarkWarpTimeline("reveal_done")
				if self.model.lastRevealReason == "ready_cap":
					# A map without a rendered terrain (TerrainVisible 0) never
					# reports native readiness; leave a trace for the EXE fix.
					dbg.TraceError("WarpCurtain: native world readiness never arrived, revealed at the cap")
		self.__Apply()
		if not self.model.IsActive():
			self.Hide()
