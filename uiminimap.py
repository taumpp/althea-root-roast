import ui
import atlaslayout
import uiScriptLocale
import wndMgr
import player
import miniMap
import localeInfo
import maparrivalnames
import net
import app
import colorInfo
import constInfo
import background
import uiToolTip
import osfInfo
import time
import chr
import cfg
import minimapstatus
import minimappanel
import minimappanelicons
import uidungeonobjective
import atlaspolicy
import chat
if app.ENABLE_KILL_BAR_SYSTEM:
	import playersettingmodule
	import item

if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
	import grp

class MapTextToolTip(ui.Window):
	def __init__(self):
		ui.Window.__init__(self)

		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetOutline()
		if app.WJ_SHOW_PARTY_ON_MINIMAP:
			if localeInfo.IsARABIC():
				textLine.SetHorizontalAlignLeft()
			else:
				textLine.SetHorizontalAlignRight()
		else:
			textLine.SetHorizontalAlignRight()
		textLine.Show()
		self.textLine = textLine

	def __del__(self):
		ui.Window.__del__(self)

	def SetText(self, text):
		self.textLine.SetText(text)

	# R1 look: the text shows as the one R1 hint (uir1.TextTooltipShow), left of the point where the original text
	# ended (or at an anchor rect, SetAnchor), never over the button; the window itself stays hidden.
	def SetParent(self, parent):
		ui.Window.SetParent(self, parent)
		self.r1Parent = parent

	def SetAnchor(self, rect, side="above"):
		self.r1Anchor = (tuple(rect), side)

	def __R1Rect(self):
		anchor = getattr(self, "r1Anchor", None)
		if anchor is None:
			return None, "left"
		(x, y, w, h), side = anchor
		parent = getattr(self, "r1Parent", None)
		if parent is not None:
			px, py = parent.GetGlobalPosition()
			x, y = x + px, y + py
		return (x, y, w, h), side

	def SetBody(self, body):
		# Status lines under the vein of the R1 hint (a launcher with a live state,
		# buttonpanelstatus.HintBody); None = the one-line hint.
		self.r1Body = body

	def Show(self):
		rect, side = self.__R1Rect()
		try:
			import uir1
			body = getattr(self, "r1Body", None)
			if rect is not None and body and uir1.UseR1():
				uir1.ShowHintAt(rect, self.textLine.GetText(), body, side, owner=self,
					title_color=getattr(self, "r1Color", None))
				return
			if rect is not None and uir1.TextTooltipShow(self, self.textLine.GetText(), rect, side,
					title_color=getattr(self, "r1Color", None)):
				return
		except Exception:
			pass
		ui.Window.Show(self)

	def Hide(self):
		try:
			import uir1
			uir1.HideHint(self)
		except Exception:
			pass
		ui.Window.Hide(self)

	def IsShow(self):
		if ui.Window.IsShow(self):
			return True
		try:
			import uir1
			return uir1.HintShownFor(self)
		except Exception:
			return False

	def SetTooltipPosition(self, PosX, PosY):
		self.r1Anchor = ((PosX - 6, PosY, 1, 14), "left")
		if app.WJ_SHOW_PARTY_ON_MINIMAP:
			self.textLine.SetPosition(PosX - 5, PosY)
		else:
			if localeInfo.IsARABIC():
				w, h = self.textLine.GetTextSize()
				self.textLine.SetPosition(PosX - w - 5, PosY)
			else:
				self.textLine.SetPosition(PosX - 5, PosY)

	def SetTextColor(self, TextColor):
		self.textLine.SetPackedFontColor(TextColor)
		self.r1Color = TextColor

	def GetTextSize(self):
		return self.textLine.GetTextSize()

	def SetHorizontalAlignLeft(self):
		if self.textLine:
			self.textLine.SetHorizontalAlignLeft()

class AtlasWindow(ui.ScriptWindow):
	class ResizeHandle(ui.Window):
		def __init__(self, owner, edge):
			from _weakref import proxy
			ui.Window.__init__(self)
			self.owner = proxy(owner)
			self.edge = edge
			self.AddFlag("dragable")
			self.SetParent(owner)

		def OnMouseOverIn(self):
			app.SetCursor(app.HVSIZE if all(self.edge) else app.HSIZE if self.edge[0] else app.VSIZE)

		def OnMouseOver(self):
			self.OnMouseOverIn()

		def OnMouseOverOut(self):
			if not self.owner._resize:
				app.SetCursor(app.NORMAL)

		def OnMouseLeftButtonDown(self):
			self.owner.BeginResize(self.edge)
			return True

		def OnMouseDrag(self, x, y):
			self.owner.DragResize()

		def OnMouseLeftButtonUp(self):
			self.owner.EndResize()
			# Consume the captured release even after a close/resolution change.
			return True

	class AtlasRenderer(ui.Window):
		def __init__(self):
			ui.Window.__init__(self)
			self.AddFlag("not_pick")
			self.EnableScissorRect()
			self.offset = (0, 0)       # atlaslayout.view: the shown crop centred, the rest cut by the scissor

		def __del__(self):
			ui.Window.__del__(self)

		def OnUpdate(self):
			miniMap.UpdateAtlas()

		def OnRender(self):
			(x, y) = self.GetGlobalPosition()
			fx = float(x + self.offset[0])
			fy = float(y + self.offset[1])
			miniMap.RenderAtlas(fx, fy)

		def HideAtlas(self):
			miniMap.HideAtlas()

		def ShowAtlas(self):
			miniMap.ShowAtlas()

	# R1 look: R1_LOADER (set below the class) dresses the board (uir1atlas.AtlasDress) unless Settings ->
	# "Starý vzhled"; _titleHeight is the header height the atlas lies under (the R1 header is taller).
	R1_LOADER = None
	_r1 = None
	_titleHeight = atlaslayout.TITLE_HEIGHT
	_crop = (0, 0)             # origin of the shown atlas part (atlaslayout.crop), at scale 1.0
	_floor = None              # index of the shown floor (atlaslayout.ATLAS_FLOORS) or None
	_floorLabel = ""
	_title = ""
	mapName = ""

	def __init__(self):
		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Hide()
		if app.ENABLE_ATLAS_ICON_RENEWAL:
			self.tooltipInfoEx = MapTextToolTip()
			self.tooltipInfoEx.Hide()
		self.infoGuildMark = ui.MarkBox()
		self.infoGuildMark.Hide()
		self.AtlasMainWindow = None
		self.mapName = ""
		self.board = 0
		self.IsShowWindowValue = False
		self._screenSize = None
		self._imageSize = None
		self._atlasScale = 1.0
		self._preferredSize = None
		self._resize = None
		self._resizeHandles = {}

		ui.ScriptWindow.__init__(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def SetMapName(self, mapName):
		self.mapName = mapName
		self._floor = None
		self._floorLabel = ""
		try:
			# a new map starts without a floor: the plain title (__FitAtlas adds the floor, __ShowTitle)
			title = self._title = maparrivalnames.resolve(mapName) or uiScriptLocale.ZONE_MAP
			self.board.SetTitleName(title)
			if self._r1:
				self._r1.SetTitle(title)
			if self._imageSize:
				self.__FitAtlas()
		except:
			pass

	def __ShowTitle(self):
		"""The map title, with the floor of a multi-floor map: "Jeskyně přízračných pirátů · II"."""
		title = self._title
		if not title:
			return
		if self._floorLabel:
			title = title + u" \u00b7 " + self._floorLabel
		self.board.SetTitleName(title)
		if self._r1:
			self._r1.SetTitle(title)

	def __PlayerPosition(self):
		try:
			x, y, z = player.GetMainCharacterPosition()
			return x, y
		except Exception:
			return None

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/AtlasWindow.py")
		except:
			import exception
			exception.Abort("AtlasWindow.LoadWindow.LoadScript")

		try:
			self.board = self.GetChild("board")

		except:
			import exception
			exception.Abort("AtlasWindow.LoadWindow.BindObject")

		loader = self.R1_LOADER
		if loader:
			# Before the atlas renderer joins the board: the R1 frame draws under the map.
			self._r1 = loader(self)
			if self._r1:
				self._titleHeight = self._r1.TitleHeight()
				self.tooltipInfo = self._r1.Tooltip()

		# The outer hit ring may lie outside this root. Do not capture unrelated
		# world input in the rest of the root's unbounded picking region.
		self.AddFlag("ignore_size")
		self.AddFlag("not_pick")
		if getattr(miniMap, "SUPPORTS_ATLAS_SCALE_REFRESH", False):
			for edge in atlaslayout.grips(1, 1):
				self._resizeHandles[edge] = self.ResizeHandle(self, edge)

		self.AtlasMainWindow = self.AtlasRenderer()
		self.board.SetCloseEvent(self.Close)
		self.AtlasMainWindow.SetParent(self.board)
		# Keep the shared metal frame; cover its black interior up to the 2px edge.
		self.board.Base.Hide()
		self.AtlasMainWindow.SetPosition(atlaslayout.FRAME_WIDTH, self._titleHeight)
		self.tooltipInfo.SetParent(self.board)
		if app.ENABLE_ATLAS_ICON_RENEWAL:
			self.tooltipInfoEx.SetParent(self.board)

		if app.ENABLE_MAP_TELEPORT:
			self.board.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.OnMouseLeftButtonUpEvent))

		self.infoGuildMark.SetParent(self.board)
		self.SetPosition(wndMgr.GetScreenWidth() - 136 - 256 - 10 - 165, 78)
		self.Hide()

		miniMap.RegisterAtlasWindow(self)
		try:
			import uir1
			uir1.FollowLook(self)
		except Exception:
			pass

	def SyncR1Look(self):
		"""Settings switched the look (uir1.LookChanged): the R1 frame, header and hint dressed into the board or undone
		(the board's own chrome and the text tooltip back); the map, the tooltips and the guild mark stay above the
		frame, the atlas is fitted under the header of the look in use."""
		import uir1
		loader = self.R1_LOADER
		wanted = bool(loader) and uir1.UseR1()
		if not self.board or not self.AtlasMainWindow or wanted == bool(self._r1):
			return
		old_tooltip = self.tooltipInfo
		if wanted:
			r1 = loader(self)
			if not r1:
				return
			self._r1 = r1
			self._titleHeight = r1.TitleHeight()
			self.tooltipInfo = r1.Tooltip()
		else:
			r1, self._r1 = self._r1, None
			r1.Undo()
			self.__dict__.pop("_titleHeight", None)          # the class value: the original title bar
			self.tooltipInfo = MapTextToolTip()
		if old_tooltip:
			old_tooltip.Hide()
		self.tooltipInfo.Hide()
		self.tooltipInfo.SetParent(self.board)
		self.AtlasMainWindow.SetPosition(atlaslayout.FRAME_WIDTH, self._titleHeight)
		uir1.Restack(self.board, (self.AtlasMainWindow, self.tooltipInfo, getattr(self, "tooltipInfoEx", None),
			self.infoGuildMark))
		if self.IsShow():
			self.Show()

	def Destroy(self):
		try:
			import uir1
			uir1.UnfollowLook(self)
		except Exception:
			pass
		self.EndResize()
		self._resizeHandles.clear()
		miniMap.UnregisterAtlasWindow()
		self.ClearDictionary()
		self.AtlasMainWindow = None
		self.tooltipAtlasClose = 0
		self.tooltipInfo = None
		self.infoGuildMark = None
		self.board = None
		self._r1 = None

	if app.ENABLE_ATLAS_ICON_RENEWAL:
		def FormatTime(self, seconds):
			if seconds <= 0:
				return "0s"
			m, s = divmod(seconds, 60)
			h, m = divmod(m, 60)
			d, h = divmod(h, 24)
			text = ""
			if d > 0:
				text+="{}d ".format(d)
			if h > 0:
				text+="{}h ".format(h)
			if m > 0:
				text+="{}m ".format(m)
			if s > 0:
				text+="{}s ".format(s)

			return text[:len(text)-1] if len(text) > 0 else "None"


	def __IsMouseOverAtlas(self):
		# IsIn tests native pick ownership. The not_pick renderer can never own
		# the pointer, so keep the board as receiver and bound its map surface.
		if self._resize or not self.AtlasMainWindow or not self.board or not self.board.IsIn():
			return False
		mouseX, mouseY = wndMgr.GetMousePosition()
		x, y = self.AtlasMainWindow.GetGlobalPosition()
		return (x <= mouseX < x + self.AtlasMainWindow.GetWidth() and
				y <= mouseY < y + self.AtlasMainWindow.GetHeight())

	def OnUpdate(self):
		if self._screenSize != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()):
			self.EndResize()
			self.__FitAtlas()
		elif self._floor is not None and not self._resize:
			floor = atlaslayout.floor_index(self.mapName, self.__PlayerPosition())
			if floor is not None and floor != self._floor:
				self.__FitAtlas()      # teleported to another floor: show it at once (the window keeps its place)

		if not self.tooltipInfo:
			return

		if not self.infoGuildMark:
			return

		self.infoGuildMark.Hide()
		self.tooltipInfo.Hide()
		if app.ENABLE_ATLAS_ICON_RENEWAL:
			self.tooltipInfoEx.Hide()

		if not self.__IsMouseOverAtlas():
			return

		(mouseX, mouseY) = wndMgr.GetMousePosition()
		if app.ENABLE_ATLAS_ICON_RENEWAL:
			(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID, respawnTime, isBoss) = miniMap.GetAtlasInfo(mouseX, mouseY)
		else:
			(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID) = miniMap.GetAtlasInfo(mouseX, mouseY)

		if False == bFind:
			return

		if "empty_guild_area" == sName:
			sName = localeInfo.GUILD_EMPTY_AREA

		(x, y) = self.GetGlobalPosition()
		if self._r1:
			# R1 tooltip: the name in the game's colour, a short vein, the coordinates (and the respawn time).
			extra = ""
			if app.ENABLE_ATLAS_ICON_RENEWAL and isBoss:
				extra = localeInfo.ATLAS_WINDOW_RESPAWN % self.FormatTime(respawnTime)
			self.tooltipInfo.SetEntry(sName, iPosX, iPosY, dwTextColor, extra)
			self.tooltipInfo.Place(mouseX - x, mouseY - y, self.board.GetWidth(), self.board.GetHeight())
			self.tooltipInfo.Show()
			self.tooltipInfo.SetTop()
			if 0 != dwGuildID:
				self.infoGuildMark.SetIndex(dwGuildID)
				self.infoGuildMark.SetPosition(*self.tooltipInfo.MarkPosition())
				self.infoGuildMark.Show()
				self.infoGuildMark.SetScale(0.5)
			return
		if isBoss:
			self.tooltipInfoEx.SetText(localeInfo.ATLAS_WINDOW_RESPAWN % self.FormatTime(respawnTime))
			self.tooltipInfoEx.SetTooltipPosition(mouseX - x - 5, mouseY - y - 14)
			self.tooltipInfoEx.Show()
			self.tooltipInfoEx.SetTop()

			self.tooltipInfo.SetText("%s(%d, %d)" % (sName, iPosX, iPosY))
			self.tooltipInfo.SetTooltipPosition(mouseX - x - 5, mouseY - y)
		else:
			self.tooltipInfo.SetText("%s(%d, %d)" % (sName, iPosX, iPosY))
			self.tooltipInfo.SetTooltipPosition(mouseX - x, mouseY - y)
		self.tooltipInfo.SetTextColor(dwTextColor)
		self.tooltipInfo.Show()
		self.tooltipInfo.SetTop()

		if 0 != dwGuildID:
			textWidth, textHeight = self.tooltipInfo.GetTextSize()
			self.infoGuildMark.SetIndex(dwGuildID)
			self.infoGuildMark.SetPosition(mouseX - x - textWidth - 18 - 5, mouseY - y)
			self.infoGuildMark.Show()
			self.infoGuildMark.SetScale(0.5)

	def Hide(self):
		self.EndResize()
		for handle in self._resizeHandles.values():
			handle.Hide()
		if self.AtlasMainWindow:
			self.AtlasMainWindow.HideAtlas()
			self.AtlasMainWindow.Hide()
		ui.ScriptWindow.Hide(self)

	def __FitAtlas(self, initialPosition=False):
		if not self.AtlasMainWindow:
			return False

		screenWidth, screenHeight = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		canScale = getattr(miniMap, "SUPPORTS_ATLAS_SCALE_REFRESH", False)
		if canScale:
			# GetAtlasSize reports the current scaled size: reset before fitting so
			# reopening, warping and resolution changes never compound the scale.
			miniMap.SetAtlasScale(1.0, 1.0)
		bGet, imageWidth, imageHeight = miniMap.GetAtlasSize()
		if not bGet or imageWidth <= 0 or imageHeight <= 0:
			return False

		position = self.__PlayerPosition()
		x0, y0, imageWidth, imageHeight, label = atlaslayout.crop(self.mapName, imageWidth, imageHeight, position)
		self._crop = (x0, y0)
		self._floor = (atlaslayout.floor_index(self.mapName, position) or 0) if label else None
		if label != self._floorLabel:
			self._floorLabel = label
			try:
				self.__ShowTitle()
			except Exception:
				pass
		self._imageSize = (imageWidth, imageHeight)
		self._atlasScale = 1.0
		if canScale:
			scale, imageWidth, imageHeight = atlaslayout.fit(
				imageWidth, imageHeight, screenWidth, screenHeight, self._preferredSize, self._titleHeight)
			miniMap.SetAtlasScale(scale, scale)
			self._atlasScale = scale

		self.__SizeAtlas(imageWidth, imageHeight)
		width, height = self.GetWidth(), self.GetHeight()
		self._screenSize = (screenWidth, screenHeight)
		x, y = self.GetLocalPosition()
		if initialPosition:
			x, y = screenWidth - width - 200 - atlaslayout.SCREEN_MARGIN, 78
		self.SetPosition(*atlaslayout.clamp_position(
			x, y, width, height, screenWidth, screenHeight))
		return True

	def __SizeAtlas(self, imageWidth, imageHeight):
		viewWidth, offset = atlaslayout.view(imageWidth, self._crop, self._atlasScale)
		imageWidth = viewWidth
		minimum = max(240, self._r1.RequiredWidth()) if self._r1 else 240
		available = max(1, wndMgr.GetScreenWidth() - 2 * atlaslayout.SCREEN_MARGIN)
		width = max(imageWidth + 2 * atlaslayout.FRAME_WIDTH, min(minimum, available))
		height = imageHeight + self._titleHeight + atlaslayout.FRAME_WIDTH
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		if self._r1:
			self._r1.Resize(width, height)
		if localeInfo.IsARABIC():
			self.board.SetPosition(width, 0)
		self.AtlasMainWindow.SetPosition((width - imageWidth) // 2, self._titleHeight)
		self.AtlasMainWindow.SetSize(imageWidth, imageHeight)
		self.AtlasMainWindow.offset = offset
		grips = atlaslayout.grips(width, height)
		for edge, handle in self._resizeHandles.items():
			x, y, w, h = grips[edge]
			handle.SetPosition(x, y)
			handle.SetSize(w, h)
			handle.Show()

	def BeginResize(self, edge):
		if not self.IsShow() or not self._imageSize or edge not in self._resizeHandles:
			return
		self.SetTop()
		x, y = self.GetLocalPosition()
		x, y = atlaslayout.clamp_position(x, y, self.GetWidth(), self.GetHeight(), *self._screenSize)
		self.SetPosition(x, y)
		self._resize = (edge, wndMgr.GetMousePosition(),
			(x, y, self.GetWidth(), self.GetHeight()), self._atlasScale)
		self._resizeHandles[edge].OnMouseOverIn()

	def DragResize(self):
		if not self._resize:
			return
		if self._screenSize != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()):
			self.EndResize()
			self.__FitAtlas()
			return
		edge, origin, rect, startScale = self._resize
		mx, my = wndMgr.GetMousePosition()
		scale, iw, ih, x, y = atlaslayout.resize(
			self._imageSize, rect, edge, (mx - origin[0], my - origin[1]), self._screenSize, startScale,
			self._titleHeight)
		miniMap.SetAtlasScale(scale, scale)
		self._atlasScale = scale
		self.__SizeAtlas(iw, ih)
		self.SetPosition(*atlaslayout.clamp_position(
			x, y, self.GetWidth(), self.GetHeight(), *self._screenSize))
		self._preferredSize = scale * max(self._imageSize)

	def EndResize(self):
		if self._resize or any(handle.IsIn() for handle in self._resizeHandles.values()):
			app.SetCursor(app.NORMAL)
		self._resize = None

	def Show(self):
		self.EndResize()
		if not self.__FitAtlas(initialPosition=self._screenSize is None):
			return
		self.AtlasMainWindow.ShowAtlas()
		self.AtlasMainWindow.Show()
		ui.ScriptWindow.Show(self)
		self.IsShowWindowValue = True

	def Close(self):
		self.IsShowWindowValue = False
		self.Hide()

	def IsShowWindow(self):
		return self.IsShowWindowValue

	def SetCenterPositionAdjust(self, x, y):
		screenWidth, screenHeight = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		x += (screenWidth - self.GetWidth()) // 2
		y += (screenHeight - self.GetHeight()) // 2
		self.SetPosition(*atlaslayout.clamp_position(
			x, y, self.GetWidth(), self.GetHeight(), screenWidth, screenHeight))

	if app.ENABLE_MAP_TELEPORT:
		def OnMouseLeftButtonUpEvent(self):
			if not self.__IsMouseOverAtlas():
				return
			if not chr.IsGameMaster(player.GetMainCharacterIndex()):
				return

			(mouseX, mouseY) = wndMgr.GetMousePosition()
			if app.ENABLE_ATLAS_ICON_RENEWAL:
				(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID, respawnTime, isBoss) = miniMap.GetAtlasInfo(mouseX, mouseY)
			else:
				(bFind, sName, iPosX, iPosY, dwTextColor, dwGuildID) = miniMap.GetAtlasInfo(mouseX, mouseY)

			if not bFind:
				getAtlasPosition = getattr(miniMap, "GetAtlasPosition", None)
				if not getAtlasPosition:
					return
				(bValid, iPosX, iPosY) = getAtlasPosition(mouseX, mouseY)
				if not bValid:
					return

			net.SendChatPacket("/goto %d %d" % (iPosX, iPosY))

	def OnPressEscapeKey(self):
		self.Close()
		return True


def _R1AtlasDress(window):
	"""uir1atlas.AtlasDress of the atlas board (R1 look), None for Settings -> "Starý vzhled" or after a failure."""
	try:
		import uir1atlas
		if not uir1atlas.UseR1():
			return None
	except Exception:
		try:
			import uir1
			uir1.TraceFailure("Velká mapa")
		except Exception:
			pass
		return None
	dress = uir1atlas.Dress(window)
	if dress:
		# The atlas root is 'not_pick' (its hit ring reaches outside it), which the engine never brings to the front
		# on a click: a mouse-down on the header row (the 'attach' strip) raises it.
		import uir1
		uir1.Front(window, not_pick=True)
	return dress


AtlasWindow.R1_LOADER = staticmethod(_R1AtlasDress)


def _R1MinimapDress(window):
	"""uiminimapr1 dress of the minimap (R1 look), None for Settings -> "Starý vzhled" or after a failure."""
	try:
		import uiminimapr1
	except Exception:
		return None
	return uiminimapr1.Create(window, MapTextToolTip)

def __RegisterMiniMapColor(type, rgb):
	miniMap.RegisterColor(type, rgb[0], rgb[1], rgb[2])

class MiniMap(ui.ScriptWindow):
	# R1 look: R1_LOADER (set below the class) dresses the loaded window (uiminimapr1.Create).
	R1_LOADER = None

	CANNOT_SEE_INFO_MAP_DICT = {
		"metin2_map_monkeydungeon" : False,
		"metin2_map_monkeydungeon_02" : False,
		"metin2_map_monkeydungeon_03" : False,
		"metin2_map_devilsCatacomb" : False,
		"metin2_12zi_stage" : False,
	}

	if app.ENABLE_KILL_BAR_SYSTEM:
		KILL_BAR_COOLTIME = 4.0
		KILL_BAR_MOVE_SPEED = 3.0
		KILL_BAR_MOVE_DISTANCE = 33.0
		KILL_BAR_MAX_ITEM = 5

		KILL_BAR_RACE = {
			playersettingmodule.RACE_WARRIOR_M: "|Ikill_bar/warrior_m|i",
			playersettingmodule.RACE_ASSASSIN_W	: "|Ikill_bar/assassin_w|i",
			playersettingmodule.RACE_SURA_M		: "|Ikill_bar/sura_m|i",
			playersettingmodule.RACE_SHAMAN_W	: "|Ikill_bar/shaman_w|i",
			playersettingmodule.RACE_WARRIOR_W	: "|Ikill_bar/warrior_w|i",
			playersettingmodule.RACE_ASSASSIN_M	: "|Ikill_bar/assassin_m|i",
			playersettingmodule.RACE_SURA_W		: "|Ikill_bar/sura_w|i",
			playersettingmodule.RACE_SHAMAN_M	: "|Ikill_bar/shaman_m|i",
		}

		KILL_BAR_WEAPON_TYPE = {
			"FIST": "|Ikill_bar/fist|i",
			item.WEAPON_SWORD: "|Ikill_bar/sword|i",
			item.WEAPON_DAGGER: "|Ikill_bar/dagger|i",
			item.WEAPON_BOW: "|Ikill_bar/bow|i",
			item.WEAPON_TWO_HANDED: "|Ikill_bar/twohand|i",
			item.WEAPON_BELL: "|Ikill_bar/bell|i",
			item.WEAPON_FAN: "|Ikill_bar/fan|i",
		}

	def __init__(self):
		ui.ScriptWindow.__init__(self)

		self.__Initialize()
		self.objectivePanel = None

		miniMap.Create()
		miniMap.SetScale(2.0)

		self.AtlasWindow = AtlasWindow()
		self.AtlasWindow.LoadWindow()
		self.AtlasWindow.Hide()

		self.tooltipMiniMapOpen = MapTextToolTip()
		self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP)
		self.tooltipMiniMapOpen.Show()
		self.tooltipMiniMapClose = MapTextToolTip()
		self.tooltipMiniMapClose.SetText(localeInfo.UI_CLOSE)
		self.tooltipMiniMapClose.Show()
		self.tooltipScaleUp = MapTextToolTip()
		self.tooltipScaleUp.SetText(localeInfo.MINIMAP_INC_SCALE)
		self.tooltipScaleUp.Show()
		self.tooltipScaleDown = MapTextToolTip()
		self.tooltipScaleDown.SetText(localeInfo.MINIMAP_DEC_SCALE)
		self.tooltipScaleDown.Show()
		self.tooltipAtlasOpen = MapTextToolTip()
		self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_SHOW_AREAMAP)
		self.tooltipAtlasOpen.Show()

		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Show()

		if miniMap.IsAtlas():
			self.atlasTooltipText = localeInfo.MINIMAP_SHOW_AREAMAP
		else:
			self.atlasTooltipText = localeInfo.MINIMAP_CAN_NOT_SHOW_AREAMAP
		self.tooltipAtlasOpen.SetText(self.atlasTooltipText)
		# On a map without the large map (atlaspolicy) the hover text is the notice (__SyncAtlasTooltip).
		self.atlasTooltipBlocked = None

		self.tooltipAtlasOpen.SetHorizontalAlignLeft()
		# One hover text per configurable launcher slot (root/minimappanel.py)
		# plus the fixed "More" control.
		self.launcherTooltips = []
		for unused in range(minimappanel.MAX_SLOTS):
			tooltip = MapTextToolTip()
			tooltip.Hide()
			self.launcherTooltips.append(tooltip)
		self.tooltipMoreOpen = MapTextToolTip()
		self.tooltipMoreOpen.SetText(minimappanel.MoreLabel())
		self.tooltipMoreOpen.Hide()

		if app.ENABLE_COMBAT_ZONE:
			self.tooltipCombatZoneOpen = MapTextToolTip()
			self.tooltipCombatZoneOpen.SetText(localeInfo.MAP_BATTLE_FIELD)
			self.tooltipCombatZoneOpen.Show()
			self.tooltipCombatZoneOpen.SetHorizontalAlignLeft()

		self.mapName = ""

		self.isLoaded = 0
		self.canSeeInfo = True

		# AUTOBAN
		self.imprisonmentDuration = 0
		self.imprisonmentEndTime = 0
		self.imprisonmentEndTimeText = ""
		# END_OF_AUTOBAN

	def __del__(self):
		miniMap.Destroy()
		ui.ScriptWindow.__del__(self)

		self.interface = None

	def __Initialize(self):
		self.positionInfo = 0
		self.observerCount = 0

		self.OpenWindow = 0
		self.CloseWindow = 0
		self.ScaleUpButton = 0
		self.ScaleDownButton = 0
		self.MiniMapHideButton = 0
		self.MiniMapShowButton = 0
		self.AtlasShowButton = 0
		self.launcherOrbit = None
		self.launcherOrbitOuter = None
		self.launcherSlots = []
		self.launcherTooltips = []
		self.launcherLayout = ()
		self.launcherEntries = {}
		self.launcherMoreButton = None
		self.launcherSettingsButton = None
		self.tooltipMoreOpen = None
		self.launcherMenu = None
		self.launcherContext = None
		self.launcherBadges = None
		self.skillTreeEvent = None
		if app.ENABLE_COMBAT_ZONE:
			self.btnCombatZone = 0
			self.tooltipCombatZoneOpen = 0
		self.tooltipMiniMapOpen = 0
		self.tooltipMiniMapClose = 0
		self.tooltipScaleUp = 0
		self.tooltipScaleDown = 0
		self.tooltipAtlasOpen = 0
		self.tooltipInfo = None
		self.serverInfo = None
		self.fpsCounter = None
		self.lastFPSCounterUpdate = 0.0
		self.dateTimeTextLine = None
		self.statusClock = None
		self.statusDate = None
		self.statusNotice = None
		self.r1Dress = None
		self.lastStatusUpdate = None
		self.lastStatusValue = None

		if app.ENABLE_DUNGEON_INFO:
			self.interface = None

		if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
			self.GuildDragonlairFirstGuildText = None
			self.GuildDragonlairFirstGuildSecond = None
			self.GuildDragonlairFirstGuildLeftTime = 0
			self.isGuildDragonLairStart = False

		if app.ENABLE_KILL_BAR_SYSTEM:
			self.KillList = list()

	def SetMapName(self, mapName):
		self.mapName = mapName
		self.AtlasWindow.SetMapName(mapName)

		if mapName in self.CANNOT_SEE_INFO_MAP_DICT:
			self.canSeeInfo = False
			self.HideMiniMap()
			self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP_CANNOT_SEE)
		else:
			self.canSeeInfo = True
			self.ShowMiniMap()
			self.tooltipMiniMapOpen.SetText(localeInfo.MINIMAP)

	# AUTOBAN
	def SetImprisonmentDuration(self, duration):
		self.imprisonmentDuration = duration
		self.imprisonmentEndTime = app.GetGlobalTimeStamp() + duration

		self.__UpdateImprisonmentDurationText()

	def __UpdateImprisonmentDurationText(self):
		restTime = max(self.imprisonmentEndTime - app.GetGlobalTimeStamp(), 0)

		imprisonmentEndTimeText = localeInfo.SecondToDHM(restTime)
		if imprisonmentEndTimeText != self.imprisonmentEndTimeText:
			self.imprisonmentEndTimeText = imprisonmentEndTimeText
			# Keep the channel readable while the legacy quiz notice is active.
			notice = self.statusNotice or self.serverInfo
			if notice:
				notice.SetText("%s: %s" % (uiScriptLocale.AUTOBAN_QUIZ_REST_TIME, self.imprisonmentEndTimeText))
				if self.statusNotice:
					if restTime:
						notice.Show()
					else:
						notice.Hide()
	# END_OF_AUTOBAN

	def Show(self):
		self.__LoadWindow()

		ui.ScriptWindow.Show(self)

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			pyScrLoader = ui.PythonScriptLoader()
			if localeInfo.IsARABIC():
				pyScrLoader.LoadScriptFile(self, uiScriptLocale.LOCALE_UISCRIPT_PATH + "Minimap.py")
			else:
				pyScrLoader.LoadScriptFile(self, "UIScript/MiniMap.py")
		except:
			import exception
			exception.Abort("MiniMap.LoadWindow.LoadScript")

		try:
			self.OpenWindow = self.GetChild("OpenWindow")
			self.OpenWindowBGI = self.GetChild("OpenWindowBGI")
			self.MiniMapWindow = self.GetChild("MiniMapWindow")
			self.objectivePanel = uidungeonobjective.ObjectivePanel(
				self.GetChild("DungeonObjectiveLayer") if self.IsChild("DungeonObjectiveLayer") else self.OpenWindowBGI)
			self.ScaleUpButton = self.GetChild("ScaleUpButton")
			self.ScaleDownButton = self.GetChild("ScaleDownButton")
			self.MiniMapHideButton = self.GetChild("MiniMapHideButton")
			self.AtlasShowButton = self.GetChild("AtlasShowButton")
			self.CloseWindow = self.GetChild("CloseWindow")
			self.MiniMapShowButton = self.GetChild("MiniMapShowButton")
			# Older locale layouts without configurable slots show no launchers.
			self.launcherSlots = []
			for index in range(minimappanel.MAX_SLOTS):
				name = "LauncherSlot%d" % index
				if not self.IsChild(name):
					break
				self.launcherSlots.append(self.GetChild(name))
			if self.IsChild("LauncherOrbit"):
				self.launcherOrbit = self.GetChild("LauncherOrbit")
			if self.IsChild("LauncherOrbitOuter"):
				self.launcherOrbitOuter = self.GetChild("LauncherOrbitOuter")
			if self.IsChild("LauncherMoreButton"):
				self.launcherMoreButton = self.GetChild("LauncherMoreButton")
				self.launcherMoreButton.SetEvent(ui.__mem_func__(self.ToggleLauncherMenu))
			if self.IsChild("LauncherSettingsButton"):
				self.launcherSettingsButton = self.GetChild("LauncherSettingsButton")
				self.launcherSettingsButton.SetEvent(ui.__mem_func__(self.ToggleLauncherSettings))
				self.launcherSettingsButton.SetToolTipText(minimappanel.SettingsLabel())
			self.positionInfo = self.GetChild("PositionInfo")
			self.observerCount = self.GetChild("ObserverCount")
			self.serverInfo = self.GetChild("ServerInfo")
			self.fpsCounter = self.GetChild("FPSCounter")
			if app.ENABLE_COMBAT_ZONE:
				self.btnCombatZone = self.GetChild("BattleButton")
			# Older locale layouts may still contain this retired row.
			if self.IsChild("PlayerCount"):
				self.GetChild("PlayerCount").Hide()

			if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
				self.GuildDragonlairFirstGuildText = self.GetChild("GuildDragonlairFirstGuildText")
				self.GuildDragonlairFirstGuildText.Hide()
				self.GuildDragonlairFirstGuildSecond = self.GetChild("GuildDragonlairFirstGuildSecond")
				self.GuildDragonlairFirstGuildSecond.SetFontName(localeInfo.UI_BOLD_FONT)
				self.GuildDragonlairFirstGuildSecond.Hide()
				self.observerCount.Hide()

			if localeInfo.IsARABIC():
				self.OpenWindowBGI.LeftRightReverse()

			# Smooth only the reduced pennant artwork; labels use native fonts.
			for name in ("StatusPennant", "StatusMark", "StatusWordmark"):
				if self.IsChild(name):
					setFiltering = getattr(self.GetChild(name), "SetLinearFiltering", None)
					if setFiltering:
						setFiltering(True)

			if self.IsChild("StatusClock"):
				self.statusClock = self.GetChild("StatusClock")
				self.statusDate = self.GetChild("StatusDate")
				self.statusNotice = self.GetChild("StatusNotice")
				self.statusNotice.Hide()
			elif self.IsChild("DateTimeTextLine"):
				self.dateTimeTextLine = self.GetChild("DateTimeTextLine")
				self.dateTimeTextLine.SetOutline()

			if localeInfo.IsARABIC():
				(mailbox_effect_x, mailbox_effect_y) = self.MailBoxEffect.GetLocalPosition()
				self.MailBoxEffect.SetPosition(mailbox_effect_x + 26, mailbox_effect_y)
		except:
			import exception
			exception.Abort("MiniMap.LoadWindow.Bind")

		# R1 look (uiminimapr1, minimap A2): R1 art on the ring, controls and pennant, unless "Starý vzhled".
		loader = MiniMap.R1_LOADER
		if loader:
			self.r1Dress = loader(self)
		try:
			import uir1
			uir1.FollowLook(self)
		except Exception:
			pass

		if constInfo.MINIMAP_POSITIONINFO_ENABLE == 0:
			self.positionInfo.Hide()

		self.__RefreshStatus(True)
		try:
			self.SetFPSCounterVisible(bool(int(cfg.Get(cfg.SAVE_OPTION, "show_fps", "0"))))
		except (TypeError, ValueError):
			self.SetFPSCounterVisible(False)
		self.ScaleUpButton.SetEvent(ui.__mem_func__(self.ScaleUp))
		self.ScaleDownButton.SetEvent(ui.__mem_func__(self.ScaleDown))
		self.MiniMapHideButton.SetEvent(ui.__mem_func__(self.HideMiniMap))
		self.MiniMapShowButton.SetEvent(ui.__mem_func__(self.ShowMiniMap))
		self.RefreshLauncherPanel()

		if app.ENABLE_COMBAT_ZONE:
			self.btnCombatZone.SetEvent(ui.__mem_func__(self.OpenCombatZoneWindow))
			self.btnCombatZone.Down()

		if miniMap.IsAtlas():
			self.AtlasShowButton.SetEvent(ui.__mem_func__(self.ShowAtlas))


		if app.ENABLE_COMBAT_ZONE:
			(ButtonPosX, ButtonPosY) = self.btnCombatZone.GetGlobalPosition()
			self.tooltipCombatZoneOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		(ButtonPosX, ButtonPosY) = self.MiniMapShowButton.GetGlobalPosition()
		self.tooltipMiniMapOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		(ButtonPosX, ButtonPosY) = self.MiniMapHideButton.GetGlobalPosition()
		self.tooltipMiniMapClose.SetTooltipPosition(ButtonPosX, ButtonPosY)

		(ButtonPosX, ButtonPosY) = self.ScaleUpButton.GetGlobalPosition()
		self.tooltipScaleUp.SetTooltipPosition(ButtonPosX, ButtonPosY)

		(ButtonPosX, ButtonPosY) = self.ScaleDownButton.GetGlobalPosition()
		self.tooltipScaleDown.SetTooltipPosition(ButtonPosX, ButtonPosY)

		(ButtonPosX, ButtonPosY) = self.AtlasShowButton.GetGlobalPosition()
		self.tooltipAtlasOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		self.__PlaceLauncherTooltips()

		self.ShowMiniMap()

	if app.ENABLE_WINDOW_RESIZE:
		def OnResize(self):
			try:
				self.SetPosition(wndMgr.GetScreenWidth() - self.GetWidth(), 0)
			except:
				pass

			try:
				(ButtonPosX, ButtonPosY) = self.MiniMapShowButton.GetGlobalPosition()
				self.tooltipMiniMapOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
			except:
				pass

			try:
				(ButtonPosX, ButtonPosY) = self.MiniMapHideButton.GetGlobalPosition()
				self.tooltipMiniMapClose.SetTooltipPosition(ButtonPosX, ButtonPosY)
			except:
				pass

			try:
				(ButtonPosX, ButtonPosY) = self.ScaleUpButton.GetGlobalPosition()
				self.tooltipScaleUp.SetTooltipPosition(ButtonPosX, ButtonPosY)
			except:
				pass

			try:
				(ButtonPosX, ButtonPosY) = self.ScaleDownButton.GetGlobalPosition()
				self.tooltipScaleDown.SetTooltipPosition(ButtonPosX, ButtonPosY)
			except:
				pass

			try:
				(ButtonPosX, ButtonPosY) = self.AtlasShowButton.GetGlobalPosition()
				self.tooltipAtlasOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
			except:
				pass

			try:
				self.__PlaceLauncherTooltips()
			except:
				pass

			if app.ENABLE_COMBAT_ZONE:
				try:
					(ButtonPosX, ButtonPosY) = self.btnCombatZone.GetGlobalPosition()
					self.tooltipCombatZoneOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

	def SyncR1Look(self):
		"""Settings switched the look (uir1.LookChanged): the R1 art of the ring, controls and pennant applied or the
		original art restored in place; the launcher panel and the status lines drawn again in that look."""
		import uir1
		loader = MiniMap.R1_LOADER
		wanted = bool(loader) and uir1.UseR1()
		dress = getattr(self, "r1Dress", None)
		if wanted and not dress:
			self.r1Dress = loader(self)
		elif not wanted and dress:
			self.r1Dress = None
			try:
				dress.Restore()
			finally:
				dress.Destroy()
		else:
			return
		for refresh in (self.RefreshLauncherPanel, lambda: self.__RefreshStatus(True)):
			try:
				refresh()
			except Exception:
				uir1.TraceFailure("the minimap (look switch)")

	def Destroy(self):
		try:
			import uir1
			uir1.UnfollowLook(self)
		except Exception:
			pass
		if self.objectivePanel:
			self.objectivePanel.Destroy()
			self.objectivePanel = None
		self.HideMiniMap()

		self.AtlasWindow.Destroy()
		self.AtlasWindow = None

		if app.ENABLE_KILL_BAR_SYSTEM:
			self.KillList = None

		if self.launcherBadges:
			self.launcherBadges.Destroy()
			self.launcherBadges = None
		if self.launcherMenu:
			self.launcherMenu.Destroy()
			self.launcherMenu = None
		if self.launcherContext:
			self.launcherContext.Destroy()
			self.launcherContext = None
		if self.r1Dress:
			self.r1Dress.Destroy()
			self.r1Dress = None
		try:
			import uichannelbar
			uichannelbar.DestroyAll()
		except ImportError:
			pass

		self.ClearDictionary()

		self.__Initialize()

	def SetSkillTreeButtonEvent(self, event):
		# Kept for interfacemodule: the skill-tree launcher uses this callback
		# in whichever slot the player placed it.
		self.skillTreeEvent = event

	def RefreshLauncherPanel(self):
		"""Re-read the per-PC panel state and apply it to the launcher slots."""
		if not self.launcherSlots:
			return
		interface = getattr(self, "interface", None)
		# No VIP channel without VIP in game (root/minimappanel.py ShownInGame).
		minimappanel.MarkVip(self)
		entries = dict((entry.action_id, entry) for entry in minimappanel.ShownInGame(minimappanel.Catalog(interface)))
		self.ApplyLauncherLayout(minimappanel.LoadLayout(tuple(entries)), entries)
		if self.launcherMenu and self.launcherMenu.IsShow():
			self.launcherMenu.Refresh()

	def __ClipOrbit(self, orbit, slots):
		"""End a ring connector under the centre of its last shown launcher."""
		if not orbit:
			return
		if len(slots) < 2:
			orbit.Hide()
			return
		lastY = slots[-1].GetLocalPosition()[1] + 14
		top = orbit.GetLocalPosition()[1]
		height = max(1, orbit.GetHeight())
		orbit.SetRenderingRect(0.0, 0.0, 0.0, float(lastY - top - height) / height)
		orbit.Show()

	def ApplyLauncherLayout(self, layout, entries):
		# An empty place ('') from Settings keeps its slot, so a function put into
		# ring 2 shows there exactly as in the Settings preview (audit 1.5).
		# Functions not shown now (feature flag, VIP channel without VIP) are
		# skipped and the following ones move up.
		layout = [actionId for actionId in layout if actionId == "" or actionId in entries]
		while layout and layout[-1] == "":
			layout.pop()
		layout = tuple(layout[:len(self.launcherSlots)])
		self.launcherLayout = layout
		self.launcherEntries = entries
		for index, slot in enumerate(self.launcherSlots):
			tooltip = self.launcherTooltips[index] if index < len(self.launcherTooltips) else None
			if index >= len(layout) or not layout[index]:
				slot.Hide()
				if tooltip:
					tooltip.Hide()
				continue
			actionId = layout[index]
			slot.SetUpVisual(minimappanelicons.Visual(actionId, "normal"))
			slot.SetOverVisual(minimappanelicons.Visual(actionId, "hover"))
			slot.SetDownVisual(minimappanelicons.Visual(actionId, "pressed"))
			mark = minimappanelicons.Mark(actionId)
			if mark or slot.ButtonText:
				slot.SetText(mark)
			slot.SetEvent(ui.__mem_func__(self.__OnClickLauncher), index)
			# ui.Button.OnMouseRightButtonUp only dispatches its string-event table.
			slot.SAFE_SetStringEvent("MOUSE_RIGHT_BUTTON_UP", self.OpenLauncherContext, index)
			if tooltip:
				tooltip.SetText(minimappanel.TooltipText(entries[actionId]))
			slot.Show()
		ringSize = minimappanel.RING_SIZES[0]
		shown = [slot if index < len(layout) and layout[index] else None
			for index, slot in enumerate(self.launcherSlots)]
		# Each ring keeps its own connector; a single launcher needs none.
		self.__ClipOrbit(self.launcherOrbit, [slot for slot in shown[:ringSize] if slot])
		self.__ClipOrbit(self.launcherOrbitOuter, [slot for slot in shown[ringSize:] if slot])
		dress = getattr(self, "r1Dress", None)
		if dress:
			dress.Orbits(self.launcherOrbit, self.launcherOrbitOuter)   # R1: no arc (minimappanelicons.R1_ARC)
		self.__PlaceLauncherTooltips()
		self.__SyncLauncherBadges()

	def __SyncLauncherBadges(self):
		"""Badges and states on the shown launchers; the "More" control gets one dot
		for the functions behind it (root/uibuttonpanelbadges.py)."""
		import uibuttonpanelbadges
		if getattr(self, "launcherBadges", None) is None:
			self.launcherBadges = uibuttonpanelbadges.PanelBadges("medallion")
		self.launcherBadges.Sync(list(zip(self.launcherSlots, self.launcherLayout)))
		known = tuple(self.launcherEntries)
		try:
			menu = minimappanel.MenuIds(minimappanel.LoadState(known), known)
		except Exception:
			menu = ()
		more = [(self.launcherMoreButton, (13, -3))] if self.launcherMoreButton else []
		self.launcherBadges.SetMore(more, menu)

	def __LauncherPicker(self):
		if self.launcherMenu is None:
			import uibuttonpanelpicker
			self.launcherMenu = uibuttonpanelpicker.FunctionPicker()
		return self.launcherMenu

	def __PickerPosition(self):
		"""Left of both launcher rings, top-aligned with the "More" control."""
		(x, y) = self.launcherMoreButton.GetGlobalPosition() if self.launcherMoreButton else self.GetGlobalPosition()
		picker = self.__LauncherPicker()
		return (x - 111 - 90 - picker.GetWidth(), y - 50)

	def ToggleLauncherMenu(self):
		"""Open or close the "More" window with every function outside the rings."""
		import uiminimappanelmenu
		picker = self.__LauncherPicker()
		if picker.IsShow():
			picker.Close()
			return
		picker.EnableBadges(getattr(self, "interface", None))
		uiminimappanelmenu.OpenMore(picker, getattr(self, "interface", None),
			ui.__mem_func__(self.RunLauncherAction), self.__PickerPosition())

	def OpenLauncherPicker(self, index):
		"""Choose the function of launcher slot ``index`` (assign, swap or empty)."""
		import uiminimappanelmenu
		# Functions not shown now are skipped in game, so the following launchers
		# move up: map the shown launcher back to its stored slot.
		if index < len(self.launcherLayout):
			stored = minimappanel.LoadLayout(tuple(self.launcherEntries))
			actionId = self.launcherLayout[index]
			if actionId in stored:
				index = stored.index(actionId)
		uiminimappanelmenu.OpenSlotPicker(self.__LauncherPicker(), getattr(self, "interface", None), index,
			ui.__mem_func__(self.RefreshLauncherPanel), self.__PickerPosition())

	def OpenLauncherSettings(self):
		"""The small cogwheel: Settings -> Panely tlačítek -> Minimapa."""
		import buttonpanelsettings
		return buttonpanelsettings.Open(getattr(self, "interface", None), "minimap")

	def ToggleLauncherSettings(self):
		"""The small cogwheel opens Settings -> Panely tlačítek -> Minimapa; a second click closes it."""
		import buttonpanelsettings
		return buttonpanelsettings.Toggle(getattr(self, "interface", None), "minimap")

	def OpenLauncherContext(self, index):
		"""Right click (or Shift+click) on a launcher: Change… / Remove / Move to More."""
		if index >= len(self.launcherLayout) or not self.launcherLayout[index]:
			return
		# Like the inventory rail: a right click while an item is on the cursor
		# belongs to the item, not to the panel (audit 2.4).
		import mouseModule
		if mouseModule.mouseController.isAttached():
			return
		import uibuttonpanelcontext
		import uiminimappanelmenu
		if self.launcherContext is None:
			self.launcherContext = uibuttonpanelcontext.ContextMenu()
		entries = uiminimappanelmenu.SlotMenuEntries(lambda selected=index: self.OpenLauncherPicker(selected),
			getattr(self, "interface", None), self.launcherLayout[index], ui.__mem_func__(self.RefreshLauncherPanel))
		import uibuttonpanelbadges
		entries = tuple(entries) + uibuttonpanelbadges.ContextEntries(self.launcherLayout[index])
		(x, y) = self.launcherSlots[index].GetGlobalPosition()
		self.launcherContext.Open(entries, (x - 184 - 4, y))

	def RunLauncherAction(self, actionId):
		if actionId == "information.skill_tree" and self.skillTreeEvent:
			self.skillTreeEvent()
			return True
		return minimappanel.Invoke(actionId, getattr(self, "interface", None))

	def __LauncherHintBody(self, actionId):
		if actionId != "system.pvp_matchmaking":
			return None
		try:
			import buttonpanelstatus
			return buttonpanelstatus.HintBody(actionId, buttonpanelstatus.Context(getattr(self, "interface", None)))
		except Exception:
			return None

	def __PlaceLauncherTooltips(self):
		for index, slot in enumerate(self.launcherSlots):
			if index < len(self.launcherTooltips):
				(ButtonPosX, ButtonPosY) = slot.GetGlobalPosition()
				self.launcherTooltips[index].SetTooltipPosition(ButtonPosX, ButtonPosY)
		if self.launcherMoreButton and self.tooltipMoreOpen:
			(ButtonPosX, ButtonPosY) = self.launcherMoreButton.GetGlobalPosition()
			self.tooltipMoreOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

	def __OnClickLauncher(self, index):
		if index >= len(self.launcherLayout) or not self.launcherLayout[index]:
			return
		shift = [getattr(app, name, None) for name in ("DIK_LSHIFT", "DIK_RSHIFT")]
		if any(key is not None and app.IsPressed(key) for key in shift):
			self.OpenLauncherContext(index)
			return
		self.RunLauncherAction(self.launcherLayout[index])

	def UpdateObserverCount(self, observerCount):
		if observerCount>0:
			self.observerCount.Show()
		elif observerCount<=0:
			self.observerCount.Hide()

		self.observerCount.SetText(localeInfo.MINIMAP_OBSERVER_COUNT % observerCount)

	def SetFPSCounterVisible(self, visible):
		self.__LoadWindow()
		if not self.fpsCounter:
			return
		if visible:
			self.lastFPSCounterUpdate = 0.0
			self.fpsCounter.Show()
		else:
			self.fpsCounter.Hide()

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		miniMap.Update(x, y)

		self.positionInfo.SetText("(%.0f, %.0f)" % (x/100, y/100))

		if self.fpsCounter and self.fpsCounter.IsShow():
			currentTime = app.GetTime()
			if currentTime - self.lastFPSCounterUpdate >= 0.5:
				self.lastFPSCounterUpdate = currentTime
				fps = app.GetRenderFPS()
				frameTime = 1000.0 / fps if fps > 0 else 0.0
				self.fpsCounter.SetText(uiScriptLocale.OPTION_FPS_COUNTER % (fps, frameTime))

		self.__RefreshStatus()
		self.__CloseBlockedAtlas()

		if self.launcherSlots and minimappanel.VipChanged(self):
			self.RefreshLauncherPanel()   # VIP channels appear / disappear
		if self.launcherBadges:
			self.launcherBadges.Update(getattr(self, "interface", None))

		if self.tooltipInfo:
			if (not self.HasDungeonObjective()) and 1 == self.MiniMapWindow.IsIn():
				(mouseX, mouseY) = wndMgr.GetMousePosition()
				(bFind, sName, iPosX, iPosY, dwTextColor) = miniMap.GetInfo(mouseX, mouseY)
				if bFind == 0:
					self.tooltipInfo.Hide()
				elif not self.canSeeInfo:
					self.tooltipInfo.SetText("%s(%s)" % (sName, localeInfo.UI_POS_UNKNOWN))
					self.tooltipInfo.SetTooltipPosition(mouseX - 5, mouseY)
					self.tooltipInfo.SetTextColor(dwTextColor)
					self.tooltipInfo.Show()
				else:
					if localeInfo.IsARABIC() and sName[-1].isalnum():
						self.tooltipInfo.SetText("(%s)%d, %d" % (sName, iPosX, iPosY))
					else:
						self.tooltipInfo.SetText("%s(%d, %d)" % (sName, iPosX, iPosY))
					self.tooltipInfo.SetTooltipPosition(mouseX - 5, mouseY)
					self.tooltipInfo.SetTextColor(dwTextColor)
					self.tooltipInfo.Show()
			else:
				self.tooltipInfo.Hide()

			# AUTOBAN
			if self.imprisonmentDuration:
				self.__UpdateImprisonmentDurationText()
			# END_OF_AUTOBAN

		if True == self.MiniMapShowButton.IsIn():
			self.tooltipMiniMapOpen.Show()
		else:
			self.tooltipMiniMapOpen.Hide()

		if True == self.MiniMapHideButton.IsIn():
			self.tooltipMiniMapClose.Show()
		else:
			self.tooltipMiniMapClose.Hide()

		if True == self.ScaleUpButton.IsIn():
			self.tooltipScaleUp.Show()
		else:
			self.tooltipScaleUp.Hide()

		if True == self.ScaleDownButton.IsIn():
			self.tooltipScaleDown.Show()
		else:
			self.tooltipScaleDown.Hide()

		if True == self.AtlasShowButton.IsIn():
			self.__SyncAtlasTooltip()
			self.tooltipAtlasOpen.Show()
		else:
			self.tooltipAtlasOpen.Hide()

		if app.ENABLE_KILL_BAR_SYSTEM:
			if self.KillList:
				self.KillList = list(filter(
					lambda obj: obj["CoolTime"] > app.GetTime(), self.KillList))
				for obj in self.KillList:
					(xLocal, yLocal) = obj["ThinBoard"].GetLocalPosition()
					if obj["MOVE_X"] > 0.0:
						obj["ThinBoard"].SetPosition(xLocal - MiniMap.KILL_BAR_MOVE_SPEED, yLocal)
						obj["MOVE_X"] -= MiniMap.KILL_BAR_MOVE_SPEED
					if obj["MOVE_Y"] > 0.0:
						obj["ThinBoard"].SetPosition(xLocal, yLocal + MiniMap.KILL_BAR_MOVE_SPEED)
						obj["MOVE_Y"] -= MiniMap.KILL_BAR_MOVE_SPEED

		if app.ENABLE_COMBAT_ZONE:
			if True == self.btnCombatZone.IsIn():
				self.tooltipCombatZoneOpen.Show()
			else:
				self.tooltipCombatZoneOpen.Hide()

		for index, slot in enumerate(self.launcherSlots):
			if index >= len(self.launcherTooltips):
				break
			if index < len(self.launcherLayout) and self.launcherLayout[index] and True == slot.IsIn():
				tooltip = self.launcherTooltips[index]
				body = self.__LauncherHintBody(self.launcherLayout[index])
				if body != getattr(tooltip, "r1Body", None):
					tooltip.SetBody(body)   # a live state (the rated arena): shown again with the new lines
					tooltip.Hide()
				if not tooltip.IsShow():
					tooltip.Show()
					tooltip.SetTop()  # above every other window, like game tooltips
			else:
				self.launcherTooltips[index].Hide()
		if self.launcherMoreButton and self.tooltipMoreOpen:
			if True == self.launcherMoreButton.IsIn():
				self.tooltipMoreOpen.Show()
			else:
				self.tooltipMoreOpen.Hide()

		if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
			self.GuildTextUpdate()

	def HasDungeonObjective(self):
		return bool(self.objectivePanel and self.objectivePanel.state.visible)

	def SetDungeonObjective(self, *arguments):
		self.__LoadWindow()
		wasActive = self.HasDungeonObjective()
		if not self.objectivePanel.Receive(arguments):
			return False
		if self.HasDungeonObjective() and not wasActive:
			self.ShowMiniMap()
		elif not self.HasDungeonObjective() and not self.canSeeInfo:
			self.HideMiniMap()
		return True

	def OnRender(self):
		if self.HasDungeonObjective():
			return
		(x, y) = self.GetGlobalPosition()
		miniMap.Render(float(x) + 4.0, float(y) + 5.0)

	def Close(self):
		self.HideMiniMap()

	def HideMiniMap(self):
		miniMap.Hide()
		self.OpenWindow.Hide()
		self.CloseWindow.Show()

	def ShowMiniMap(self):
		if not self.canSeeInfo and not self.HasDungeonObjective():
			return

		miniMap.Show()
		self.OpenWindow.Show()
		self.CloseWindow.Hide()

	if app.ENABLE_KILL_BAR_SYSTEM:
		def RepositionKillBar(self, obj):
			obj["MOVE_Y"] += MiniMap.KILL_BAR_MOVE_DISTANCE
			return obj

		def AddKillInfo(self, killer, victim, killer_race, victim_race, weapon_type):
			if len(self.KillList) >= MiniMap.KILL_BAR_MAX_ITEM:
				self.KillList.sort(
					key=lambda obj: obj["CoolTime"], reverse=True)
				del self.KillList[-1]
			
			if self.KillList:
				self.KillList = list(map(self.RepositionKillBar, self.KillList))

			TBoard = ui.ThinBoard()
			TBoard.SetParent(self)
			TBoard.SetSize(170, 10)
			TBoard.SetPosition(0, 240)
			TBoard.Show()

			KillText = ui.TextLine()
			KillText.SetText("{} {} {} {} {}".format(MiniMap.KILL_BAR_RACE.get(int(killer_race), ""), killer, MiniMap.KILL_BAR_WEAPON_TYPE.get(
				int(weapon_type), MiniMap.KILL_BAR_WEAPON_TYPE.get("FIST")), victim, MiniMap.KILL_BAR_RACE.get(int(victim_race), "")))
			KillText.SetParent(TBoard)
			KillText.SetWindowHorizontalAlignCenter()
			KillText.SetWindowVerticalAlignCenter()
			KillText.SetHorizontalAlignCenter()
			KillText.SetVerticalAlignCenter()
			KillText.Show()

			KillDict = dict()
			KillDict["ThinBoard"] = TBoard
			KillDict["TextLine"] = KillText
			KillDict["CoolTime"] = app.GetTime() + MiniMap.KILL_BAR_COOLTIME
			KillDict["MOVE_X"] = MiniMap.KILL_BAR_MOVE_DISTANCE
			KillDict["MOVE_Y"] = 0.0

			self.KillList.append(KillDict)

	def isShowMiniMap(self):
		return miniMap.isShow()

	if app.ENABLE_COMBAT_ZONE:
		def OnAskCombatZoneQuestionDialog(self):
			import uiCommon
			self.combatZoneLeaveQuestionDialog = uiCommon.QuestionDialog2()
			self.combatZoneLeaveQuestionDialog.SetText1(uiScriptLocale.EXIT_BATTLE_FIELD_COLLECTED_POINTS % (player.GetCombatZonePoints()))
			self.combatZoneLeaveQuestionDialog.SetText2(uiScriptLocale.EXIT_BATTLE_FIELD)
			self.combatZoneLeaveQuestionDialog.SetWidth(320)
			self.combatZoneLeaveQuestionDialog.SetAcceptEvent(lambda arg = True: self.OnToggleCombatZoneQuestionDialog(arg))
			self.combatZoneLeaveQuestionDialog.SetCancelEvent(lambda arg = False: self.OnToggleCombatZoneQuestionDialog(arg))
			self.combatZoneLeaveQuestionDialog.Open()

		def OnToggleCombatZoneQuestionDialog(self, answer):
			if not self.combatZoneLeaveQuestionDialog:
				return

			self.combatZoneLeaveQuestionDialog.Close()
			self.combatZoneLeaveQuestionDialog = None

			if not answer:
				return

			net.SendCombatZoneRequestActionPacket(net.COMBAT_ZONE_ACTION_LEAVE, net.COMBAT_ZONE_EMPTY_DATA)
			return True

		def OpenCombatZoneWindow(self):
			if player.IsCombatZoneMap():
				self.OnAskCombatZoneQuestionDialog()
			else:
				net.SendCombatZoneRequestActionPacket(net.COMBAT_ZONE_ACTION_OPEN_RANKING, net.COMBAT_ZONE_EMPTY_DATA)

	def ScaleUp(self):
		miniMap.ScaleUp()

	def ScaleDown(self):
		miniMap.ScaleDown()

	if app.ENABLE_PLAYER_COUNT:
		def RefreshPlayerCount(self, count):
			# Preserve the network callback; ONLINE is never a minimap state.
			pass

	def __AtlasBlockedText(self):
		"""Notice text when the large map stays closed on this map (atlaspolicy), otherwise None."""
		key = atlaspolicy.BlockedMessage(net.GetMapIndex())
		if not key:
			return None
		return getattr(localeInfo, key, localeInfo.MINIMAP_CAN_NOT_SHOW_AREAMAP)

	def __AtlasBlocked(self):
		"""True, with the notice in chat, when the player may not open the large map here (atlaspolicy)."""
		text = self.__AtlasBlockedText()
		if text is None:
			return False
		chat.AppendChat(chat.CHAT_TYPE_INFO, text)
		return True

	def IsAtlasBlocked(self):
		"""True when the large map stays closed on this map; no notice (warp window restore)."""
		return self.__AtlasBlockedText() is not None

	def __CloseBlockedAtlas(self):
		# A warp restore or re-shown windows must not leave the large map open on a blocked map.
		if self.AtlasWindow and self.AtlasWindow.IsShow() and self.__AtlasBlockedText() is not None:
			self.AtlasWindow.Close()

	def __SyncAtlasTooltip(self):
		text = self.__AtlasBlockedText()
		if text == self.atlasTooltipBlocked:
			return
		self.atlasTooltipBlocked = text
		if text is not None:
			self.tooltipAtlasOpen.SetText(text)
		elif self.atlasTooltipText is not None:
			self.tooltipAtlasOpen.SetText(self.atlasTooltipText)

	def ShowAtlas(self):
		if not self.AtlasWindow.IsShow() and self.__AtlasBlocked():
			return
		if not miniMap.IsAtlas():
			return
		if self.AtlasWindow.IsShow():
			self.AtlasWindow.Hide()
		else:
			self.AtlasWindow.Show()

	if app.ENABLE_LOADING_PERFORMANCE:
		def IsShowingAtlas(self):
			return self.AtlasWindow.IsShow()

	def ToggleAtlasWindow(self):
		if not self.AtlasWindow.IsShow() and self.__AtlasBlocked():
			return
		if not miniMap.IsAtlas():
			return

		if self.AtlasWindow.IsShow():
			self.AtlasWindow.Hide()
		else:
			self.AtlasWindow.Show()

	def __RefreshStatus(self, force=False):
		if not self.serverInfo:
			return
		# Compare wall-second buckets so fractional frame timing cannot skip ticks.
		now = int(time.time())
		if not force and now == self.lastStatusUpdate:
			return
		self.lastStatusUpdate = now
		localTime = time.localtime(now)
		channelNumber, mapIndex = net.GetChannelNumber(), net.GetMapIndex()
		statusValue = (
			time.strftime("%H:%M:%S", localTime),
			minimapstatus.FormatDate(localTime),
			minimapstatus.FormatChannel(channelNumber, mapIndex),
		)
		previous = self.lastStatusValue
		self.lastStatusValue = statusValue
		if self.statusClock:
			# Fonts are fixed by the layout before the first glyph run is created.
			if force or previous is None or statusValue[0] != previous[0]:
				self.statusClock.SetText(statusValue[0])
			if force or previous is None or statusValue[1] != previous[1]:
				self.statusDate.SetText(statusValue[1])
		elif self.dateTimeTextLine:
			if force or previous is None or statusValue[:2] != previous[:2]:
				self.dateTimeTextLine.SetText(time.strftime('[%H:%M:%S - %d/%m/%Y]', localTime))
		if force or previous is None or statusValue[2] != previous[2]:
			self.serverInfo.SetText(statusValue[2])

	if app.ENABLE_MOVE_CHANNEL:
		def RefreshServerInfo(self):
			self.__RefreshStatus(True)

	if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
		def SetGuildDragonLairStart(self):
			self.isGuildDragonLairStart = True
			if self.GuildDragonlairFirstGuildLeftTime != 0:
				self.GuildDragonlairFirstGuildLeftTime = app.GetTime() + self.GuildDragonlairFirstGuildLeftTime

		def SetGuildDragonLairSuccess(self):
			self.GuildDragonlairFirstGuildSecond.SetPackedFontColor(grp.GenerateColor(0.0, 0.5, 1.0, 1.0))
			self.GuildDragonlairFirstGuildSecond.SetText(localeInfo.GUILD_DRAGONLAIR_RANKING_SUCCESS)
			self.isGuildDragonLairStart = False

		def SetGuildDragonLairFistGuildText(self, second):
			self.GuildDragonlairFirstGuildText.Show()
			self.GuildDragonlairFirstGuildSecond.Show()

			if second == 0:
				self.GuildDragonlairFirstGuildSecond.SetText(localeInfo.GUILD_DRAGONLAIR_RANKING_NONE)
			else:
				self.GuildDragonlairFirstGuildSecond.SetText(localeInfo.SecondToColonTypeMS(second))
				self.GuildDragonlairFirstGuildLeftTime = second

			self.isGuildDragonLairStart = False

			if self.positionInfo.IsShow():
				(x, y) = self.GuildDragonlairFirstGuildText.GetLocalPosition()
				self.GuildDragonlairFirstGuildText.SetPosition(x, y + 20)
				(x, y) = self.GuildDragonlairFirstGuildSecond.GetLocalPosition()
				self.GuildDragonlairFirstGuildSecond.SetPosition(x, y + 20)

			if self.observerCount.IsShow():
				(x, y) = self.GuildDragonlairFirstGuildText.GetLocalPosition()
				self.GuildDragonlairFirstGuildText.SetPosition(x, y + 20)
				(x, y) = self.GuildDragonlairFirstGuildSecond.GetLocalPosition()
				self.GuildDragonlairFirstGuildSecond.SetPosition(x, y + 20)

		def GuildTextUpdate(self):
			if self.isGuildDragonLairStart == True:
				if self.GuildDragonlairFirstGuildLeftTime != 0:
					leftTime = self.GuildDragonlairFirstGuildLeftTime - app.GetTime()
					if leftTime <= 0:
						self.GuildDragonlairFirstGuildSecond.SetPackedFontColor(grp.GenerateColor(1.0, 0.0, 0.0, 1.0))
						self.GuildDragonlairFirstGuildSecond.SetText(localeInfo.GUILD_DRAGONLAIR_RANKING_FAIL)
						self.isGuildDragonLairStart = False
					else:
						self.GuildDragonlairFirstGuildSecond.SetText(localeInfo.SecondToColonTypeMS(leftTime))
						if leftTime < 60:
							self.GuildDragonlairFirstGuildSecond.SetPackedFontColor(grp.GenerateColor(1.0, 0.0, 0.0, 1.0))

	if app.ENABLE_DUNGEON_INFO:
		def ShowDungeonInfo(self):
			interface = osfInfo.GetInterfaceInstance()
			if interface != None:
				interface.OpenDungeonInfo()

	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)
		self.RefreshLauncherPanel()
		# A pinned channel bar (root/uichannelbar.py) shows again after login.
		try:
			import uichannelbar
			uichannelbar.RestorePinned(self.interface)
		except ImportError:
			pass


MiniMap.R1_LOADER = staticmethod(_R1MinimapDress)
