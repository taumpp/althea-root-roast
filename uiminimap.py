import ui
import atlaslayout
import uiScriptLocale
import wndMgr
import player
import miniMap
import localeInfo
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
import uidungeonobjective
PVP_MATCHMAKING_ENABLED = bool(getattr(app, "ENABLE_PVP_MATCHMAKING", 0))
ARENA_LAUNCHER_ENABLED = PVP_MATCHMAKING_ENABLED
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

	def SetTooltipPosition(self, PosX, PosY):
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

		def __del__(self):
			ui.Window.__del__(self)

		def OnUpdate(self):
			miniMap.UpdateAtlas()

		def OnRender(self):
			(x, y) = self.GetGlobalPosition()
			fx = float(x)
			fy = float(y)
			miniMap.RenderAtlas(fx, fy)

		def HideAtlas(self):
			miniMap.HideAtlas()

		def ShowAtlas(self):
			miniMap.ShowAtlas()

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
		if 949 == app.GetDefaultCodePage():
			try:
				self.board.SetTitleName(localeInfo.MINIMAP_ZONE_NAME_DICT[mapName])
			except:
				pass

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
		self.AtlasMainWindow.SetPosition(atlaslayout.FRAME_WIDTH, atlaslayout.TITLE_HEIGHT)
		self.tooltipInfo.SetParent(self.board)
		if app.ENABLE_ATLAS_ICON_RENEWAL:
			self.tooltipInfoEx.SetParent(self.board)

		if app.ENABLE_MAP_TELEPORT:
			self.board.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.OnMouseLeftButtonUpEvent))

		self.infoGuildMark.SetParent(self.board)
		self.SetPosition(wndMgr.GetScreenWidth() - 136 - 256 - 10 - 165, 78)
		self.Hide()

		miniMap.RegisterAtlasWindow(self)

	def Destroy(self):
		self.EndResize()
		self._resizeHandles.clear()
		miniMap.UnregisterAtlasWindow()
		self.ClearDictionary()
		self.AtlasMainWindow = None
		self.tooltipAtlasClose = 0
		self.tooltipInfo = None
		self.infoGuildMark = None
		self.board = None

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

		self._imageSize = (imageWidth, imageHeight)
		self._atlasScale = 1.0
		if canScale:
			scale, imageWidth, imageHeight = atlaslayout.fit(
				imageWidth, imageHeight, screenWidth, screenHeight, self._preferredSize)
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
		width = imageWidth + 2 * atlaslayout.FRAME_WIDTH
		height = imageHeight + atlaslayout.TITLE_HEIGHT + atlaslayout.FRAME_WIDTH
		self.SetSize(width, height)
		self.board.SetSize(width, height)
		if localeInfo.IsARABIC():
			self.board.SetPosition(width, 0)
		self.AtlasMainWindow.SetSize(imageWidth, imageHeight)
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
			self._imageSize, rect, edge, (mx - origin[0], my - origin[1]), self._screenSize, startScale)
		miniMap.SetAtlasScale(scale, scale)
		self._atlasScale = scale
		self.__SizeAtlas(iw, ih)
		self.SetPosition(x, y)
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

def __RegisterMiniMapColor(type, rgb):
	miniMap.RegisterColor(type, rgb[0], rgb[1], rgb[2])

class MiniMap(ui.ScriptWindow):
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

		if app.ENABLE_PLAYER_RANKING:
			self.tooltipPlayerRankingOpen = MapTextToolTip()
			self.tooltipPlayerRankingOpen.SetText(uiScriptLocale.TOOLTIP_TEXT_MINIMAP_RANKING,)
			self.tooltipPlayerRankingOpen.Show()

		self.tooltipInfo = MapTextToolTip()
		self.tooltipInfo.Show()

		if miniMap.IsAtlas():
			self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_SHOW_AREAMAP)
		else:
			self.tooltipAtlasOpen.SetText(localeInfo.MINIMAP_CAN_NOT_SHOW_AREAMAP)

		self.tooltipAtlasOpen.SetHorizontalAlignLeft()
		if app.ENABLE_EVENT_MANAGER:
			self.tooltipEventManagerOpen = MapTextToolTip()
			self.tooltipEventManagerOpen.SetText(uiScriptLocale.TOOLTIP_TEXT_MINIMAP_CALENDAR,)
			self.tooltipEventManagerOpen.Show()			

		if app.ENABLE_BATTLE_PASS:
			self.tooltipBattlePassOpen = MapTextToolTip()
			self.tooltipBattlePassOpen.SetText(uiScriptLocale.TOOLTIP_TEXT_MINIMAP_BATTLEPASS,)
			self.tooltipBattlePassOpen.Show()

		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			self.tooltipSavedPositionsOpen = MapTextToolTip()
			self.tooltipSavedPositionsOpen.SetText(uiScriptLocale.KEYBIND_ACTION_SYSTEM_CUSTOM_PORTS)
			self.tooltipSavedPositionsOpen.Show()

		if ARENA_LAUNCHER_ENABLED:
			self.tooltipArenaOpen = MapTextToolTip()
			self.tooltipArenaOpen.SetText("Hodnocená aréna")
			self.tooltipArenaOpen.Show()

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
		self.SkillTreeButton = 0
		self.AtlasShowButton = 0
		if app.ENABLE_COMBAT_ZONE:
			self.btnCombatZone = 0
			self.tooltipCombatZoneOpen = 0
		if app.ENABLE_EVENT_MANAGER:
			self.EventManagerButton = 0 
		if app.ENABLE_BATTLE_PASS:
			self.BattlePassButton = 0 
		if ARENA_LAUNCHER_ENABLED:
			self.ArenaButton = 0
		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			self.SavedPositionsButton = 0
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
		self.lastStatusUpdate = None
		self.lastStatusValue = None

		if app.ENABLE_DUNGEON_INFO:
			self.interface = None

		if app.ENABLE_GUILD_DRAGONLAIR_PARTY_SYSTEM:
			self.GuildDragonlairFirstGuildText = None
			self.GuildDragonlairFirstGuildSecond = None
			self.GuildDragonlairFirstGuildLeftTime = 0
			self.isGuildDragonLairStart = False

		if app.ENABLE_PLAYER_RANKING:
			self.PlayerRankingButton = 0 
			self.tooltipPlayerRankingOpen = 0

		if app.ENABLE_EVENT_MANAGER:
			self.tooltipEventManagerOpen = 0

		if app.ENABLE_BATTLE_PASS:
			self.tooltipBattlePassOpen = 0

		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			self.tooltipSavedPositionsOpen = 0

		if ARENA_LAUNCHER_ENABLED:
			self.tooltipArenaOpen = 0

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
			self.SkillTreeButton = self.GetChild("SkillTreeButton")
			self.positionInfo = self.GetChild("PositionInfo")
			self.observerCount = self.GetChild("ObserverCount")
			self.serverInfo = self.GetChild("ServerInfo")
			self.fpsCounter = self.GetChild("FPSCounter")
			if app.ENABLE_COMBAT_ZONE:
				self.btnCombatZone = self.GetChild("BattleButton")
			# Older locale layouts may still contain this retired row.
			if self.IsChild("PlayerCount"):
				self.GetChild("PlayerCount").Hide()

			if app.ENABLE_PLAYER_RANKING:
				self.PlayerRankingButton = self.GetChild("PlayerRankingButton")
				self.PlayerRankingButton.SetEvent(ui.__mem_func__(self.TogglePlayerRankingButton))

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

			if app.ENABLE_EVENT_MANAGER:
				self.EventManagerButton = self.GetChild("EventManagerButton")
				self.EventManagerButton.SetEvent(ui.__mem_func__(self.ToggleEventManagerButton))
				#self.EventManagerButton.SetScale(0.5,0.5)

			if app.ENABLE_BATTLE_PASS:
				self.BattlePassButton = self.GetChild("BattlePassButton")
				self.BattlePassButton.SetEvent(ui.__mem_func__(self.ToggleBattlePassButton))

			if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
				self.SavedPositionsButton = self.GetChild("SavedPositionsButton")
				self.SavedPositionsButton.SetEvent(ui.__mem_func__(self.ToggleSavedPositionsButton))

			if ARENA_LAUNCHER_ENABLED:
				self.ArenaButton = self.GetChild("ArenaButton")
				self.ArenaButton.SetEvent(ui.__mem_func__(self.ToggleArenaButton))

			if localeInfo.IsARABIC():
				(mailbox_effect_x, mailbox_effect_y) = self.MailBoxEffect.GetLocalPosition()
				self.MailBoxEffect.SetPosition(mailbox_effect_x + 26, mailbox_effect_y)
		except:
			import exception
			exception.Abort("MiniMap.LoadWindow.Bind")

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
		self.SkillTreeButton.SetToolTipText(uiScriptLocale.SKILL_TREE_TITLE)

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

		if app.ENABLE_EVENT_MANAGER:
			(ButtonPosX, ButtonPosY) = self.EventManagerButton.GetGlobalPosition()
			self.tooltipEventManagerOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)	

		if app.ENABLE_BATTLE_PASS:
			(ButtonPosX, ButtonPosY) = self.BattlePassButton.GetGlobalPosition()
			self.tooltipBattlePassOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			(ButtonPosX, ButtonPosY) = self.SavedPositionsButton.GetGlobalPosition()
			self.tooltipSavedPositionsOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if ARENA_LAUNCHER_ENABLED:
			(ButtonPosX, ButtonPosY) = self.ArenaButton.GetGlobalPosition()
			self.tooltipArenaOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)

		if app.ENABLE_PLAYER_RANKING:
			(ButtonPosX, ButtonPosY) = self.PlayerRankingButton.GetGlobalPosition()
			self.tooltipPlayerRankingOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)	

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

			if app.ENABLE_EVENT_MANAGER:
				try:
					(ButtonPosX, ButtonPosY) = self.EventManagerButton.GetGlobalPosition()
					self.tooltipEventManagerOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

			if app.ENABLE_BATTLE_PASS:
				try:
					(ButtonPosX, ButtonPosY) = self.BattlePassButton.GetGlobalPosition()
					self.tooltipBattlePassOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

			if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
				try:
					(ButtonPosX, ButtonPosY) = self.SavedPositionsButton.GetGlobalPosition()
					self.tooltipSavedPositionsOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

			if ARENA_LAUNCHER_ENABLED:
				try:
					(ButtonPosX, ButtonPosY) = self.ArenaButton.GetGlobalPosition()
					self.tooltipArenaOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

			if app.ENABLE_PLAYER_RANKING:
				try:
					(ButtonPosX, ButtonPosY) = self.PlayerRankingButton.GetGlobalPosition()
					self.tooltipPlayerRankingOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

			if app.ENABLE_COMBAT_ZONE:
				try:
					(ButtonPosX, ButtonPosY) = self.btnCombatZone.GetGlobalPosition()
					self.tooltipCombatZoneOpen.SetTooltipPosition(ButtonPosX, ButtonPosY)
				except:
					pass

	def Destroy(self):
		if self.objectivePanel:
			self.objectivePanel.Destroy()
			self.objectivePanel = None
		self.HideMiniMap()

		self.AtlasWindow.Destroy()
		self.AtlasWindow = None

		if app.ENABLE_KILL_BAR_SYSTEM:
			self.KillList = None

		self.ClearDictionary()

		self.__Initialize()

	def SetSkillTreeButtonEvent(self, event):
		self.__LoadWindow()
		self.SkillTreeButton.SetEvent(event)

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

		if app.ENABLE_PLAYER_RANKING:
			if True == self.PlayerRankingButton.IsIn():
				self.tooltipPlayerRankingOpen.Show()
			else:
				self.tooltipPlayerRankingOpen.Hide()	

		if app.ENABLE_EVENT_MANAGER:
			if True == self.EventManagerButton.IsIn():
				self.tooltipEventManagerOpen.Show()
			else:
				self.tooltipEventManagerOpen.Hide()

		if app.ENABLE_BATTLE_PASS:
			if True == self.BattlePassButton.IsIn():
				self.tooltipBattlePassOpen.Show()
			else:
				self.tooltipBattlePassOpen.Hide()

		if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
			if True == self.SavedPositionsButton.IsIn():
				self.tooltipSavedPositionsOpen.Show()
			else:
				self.tooltipSavedPositionsOpen.Hide()

		if ARENA_LAUNCHER_ENABLED:
			if True == self.ArenaButton.IsIn():
				self.tooltipArenaOpen.Show()
			else:
				self.tooltipArenaOpen.Hide()

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

	def ShowAtlas(self):
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

	if app.ENABLE_EVENT_MANAGER:
		def ToggleEventManagerButton(self):
			self.interface.OpenEventCalendar()

	if app.ENABLE_PLAYER_RANKING:
		def TogglePlayerRankingButton(self):
			self.interface.ShowRankGlobal()

	if app.ENABLE_BATTLE_PASS:
		def ToggleBattlePassButton(self):
			if self.interface:
				if self.interface.wndBattlePass:
					if self.interface.wndBattlePass.IsShow():
						self.interface.wndBattlePass.Close()
						return

			self.interface.ShowBattlePass()

	if getattr(app, "ENABLE_CUSTOM_PORTS", 0):
		def ToggleSavedPositionsButton(self):
			if self.interface:
				self.interface.ToggleCustomPortsWindow()

	if ARENA_LAUNCHER_ENABLED:
		def ToggleArenaButton(self):
			if self.interface:
				self.interface.TogglePvPMatchmakingWindow()

	def BindInterfaceClass(self, interface):
		from _weakref import proxy
		self.interface = proxy(interface)
