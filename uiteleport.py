# -*- coding: utf-8 -*-
import app
import fontconfig
import net
import player
import ui
import teleportmapdata
import teleportlistdata
import uiteleportlist
import wndMgr

if app.ENABLE_DUNGEON_INFO:
	import uiDungeonTrack


TELEPORT_SKIN_PATH = "d:/ymir work/ui/game/teleport/"
MODULAR_SKIN_PATH = TELEPORT_SKIN_PATH + "modular_c_large/"
SWITCH_SKIN_PATH = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/switch_v10/btn_"
ROW_SKIN_PATH = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/rows/location_300x24_"
NAMEPLATE_SKIN_PATH = "d:/ymir work/ui/game/crimson_ember/teleport_atlas/nameplates_baked/"
LEVEL_ICON_PATH = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/icon/level_20.png"


def ApplyCrimsonVisuals(button, path_prefix):
	button.SetUpVisual(path_prefix + "normal.png")
	button.SetOverVisual(path_prefix + "hover.png")
	button.SetDownVisual(path_prefix + "pressed.png")
	button.SetDisableVisual(path_prefix + "disabled.png")


class AtlasRegionNameplate(ui.ExpandedImageBox):

	STATES = ("normal", "hover", "selected", "disabled")

	def __init__(self, parent, destination_id, scale):
		ui.ExpandedImageBox.__init__(self)
		self.SetParent(parent)
		self.AddFlag("not_pick")
		self.destinationId = destination_id
		self.scale = scale
		self.state = None
		self.SetState("normal")
		self.Show()

	def __del__(self):
		ui.ExpandedImageBox.__del__(self)

	def SetState(self, state):
		if state not in self.STATES or state == self.state:
			return
		self.state = state
		self.LoadImage(NAMEPLATE_SKIN_PATH + self.destinationId + "/" + state + ".png")
		self.SetScale(self.scale, self.scale)


class AtlasLevelHint(ui.Window):

	WIDTH = 160
	HEIGHT = 28
	PORTAL_OFFSET_Y = 39
	AVAILABLE_HOVER_DELAY = 0.5
	LOCKED_HOVER_DELAY = 0.0

	def __init__(self, parent):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.AddFlag("not_pick")
		self.AddFlag("float")

		self.background = ui.ExpandedImageBox()
		self.background.SetParent(self)
		self.background.AddFlag("not_pick")
		self.background.LoadImage(MODULAR_SKIN_PATH + "shared/level_hint_160x28.png")
		self.background.Show()

		self.levelIcon = ui.ImageBox()
		self.levelIcon.SetParent(self)
		self.levelIcon.SetPosition(7, 4)
		self.levelIcon.AddFlag("not_pick")
		self.levelIcon.LoadImage(LEVEL_ICON_PATH)
		self.levelIcon.Show()

		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.SetPosition(31, 12)
		self.label.AddFlag("not_pick")
		self.label.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY, 0))
		self.label.SetText(u"Přístup od úrovně:")
		self.label.SetFontColor(215.0 / 255.0, 205.0 / 255.0, 186.0 / 255.0)
		self.label.SetVerticalAlignCenter()
		self.label.SetOutline()
		self.label.Show()

		self.value = ui.TextLine()
		self.value.SetParent(self)
		self.value.SetPosition(31 + self.label.GetTextSize()[0] + 2, 12)
		self.value.AddFlag("not_pick")
		self.value.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL, 0))
		self.value.SetFontColor(247.0 / 255.0, 200.0 / 255.0, 28.0 / 255.0)
		self.value.SetVerticalAlignCenter()
		self.value.SetOutline()
		self.value.Show()
		self.Hide()

	def __del__(self):
		ui.Window.__del__(self)

	def SetLevel(self, required_level, locked):
		self.value.SetText(u"%d" % int(required_level))

	def ShowHint(self):
		self.Show()
		self.SetTop()

	def HideHint(self):
		self.Hide()

	def Destroy(self):
		self.Hide()
		self.background = None
		self.levelIcon = None
		self.label = None
		self.value = None


def GetLevelHintDelay(player_level, required_level):
	if player_level < required_level:
		return AtlasLevelHint.LOCKED_HOVER_DELAY
	return AtlasLevelHint.AVAILABLE_HOVER_DELAY


class TeleportMapInteraction(ui.Window):

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner
		self.hoveredDestinationId = None

	def __del__(self):
		ui.Window.__del__(self)

	def OnUpdate(self):
		if not self.owner:
			return
		x, y = self.GetMouseLocalPosition()
		destination_id = teleportmapdata.GetRegionAt(int(x / self.owner.mapScale), int(y / self.owner.mapScale))
		changed = destination_id != self.hoveredDestinationId
		if changed:
			self.hoveredDestinationId = destination_id
			self.owner.HighlightMapDestination(destination_id)
		self.owner.UpdateLevelHint(destination_id, changed)

	def OnMouseLeftButtonUp(self):
		if self.owner and self.hoveredDestinationId:
			self.owner.SelectDestination(self.hoveredDestinationId)
			return True
		return False

	def ClearOwner(self):
		self.owner = None


class AtlasSwitchButton(ui.RadioButton):

	TOOLTIP_X = 52
	TOOLTIP_Y = 10

	def __init__(self, callback, tooltip, kind):
		ui.RadioButton.__init__(self)
		self.callback = callback
		self.selected = False
		self.skinPrefix = SWITCH_SKIN_PATH + kind + "_"
		self.SetSize(36, 36)
		# Keep the compact side switch icon-only.  The default centred tooltip
		# overlaps the icon and is clipped beyond the atlas' left edge.
		self.SetToolTipText(tooltip, self.TOOLTIP_X, self.TOOLTIP_Y)
		self.SetEvent(ui.__mem_func__(self.OnClick))
		self.__ApplyState()

	def __del__(self):
		ui.RadioButton.__del__(self)

	def SetSelected(self, selected):
		self.selected = selected
		self.__ApplyState()

	def OnClick(self):
		if self.callback:
			self.callback()

	def __ApplyState(self):
		if self.selected:
			self.SetUpVisual(self.skinPrefix + "selected.png")
			self.SetOverVisual(self.skinPrefix + "selected.png")
			self.SetDownVisual(self.skinPrefix + "selected.png")
			self.Down()
		else:
			self.SetUpVisual(self.skinPrefix + "normal.png")
			self.SetOverVisual(self.skinPrefix + "hover.png")
			self.SetDownVisual(self.skinPrefix + "pressed.png")
			self.SetUp()
		self.SetDisableVisual(self.skinPrefix + "disabled.png")


class CrimsonLocationRow(ui.Button):

	WIDTH = 300

	def __init__(self, callback):
		ui.Button.__init__(self)
		self.callback = callback
		self.destinationId = None
		self.available = True
		self.SetSize(self.WIDTH, 24)
		ApplyCrimsonVisuals(self, ROW_SKIN_PATH)
		self.SetEvent(ui.__mem_func__(self.OnClick))

	def __del__(self):
		ui.Button.__del__(self)

	def SetLocation(self, label, destination_id):
		self.destinationId = destination_id
		self.available = destination_id is not None
		self.SetText(label)
		if self.available:
			self.Enable()
		else:
			self.Disable()

	def OnClick(self):
		if self.available and self.callback:
			self.callback(self.destinationId)


class TeleportDestinationDialog(ui.Window):

	WIDTH = 324
	ROW_X = 12
	ROW_WIDTH = 300
	ROW_HEIGHT = 24
	ROW_STEP = 27
	BASE_HEIGHT = 46

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = owner
		self.rows = []
		self.SetSize(self.WIDTH, self.BASE_HEIGHT + 4 * self.ROW_STEP)
		self.AddFlag("float")

		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetPosition(0, 0)
		self.board.SetSize(self.WIDTH, self.BASE_HEIGHT + 4 * self.ROW_STEP)
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def Open(self, title, choices):
		row_count = len(choices)
		while len(self.rows) < row_count:
			index = len(self.rows)
			row = CrimsonLocationRow(self.__RequestTeleport)
			row.SetParent(self.board)
			row.SetPosition(self.ROW_X, 38 + index * self.ROW_STEP)
			row.Hide()
			self.rows.append(row)
		height = self.BASE_HEIGHT + row_count * self.ROW_STEP
		self.SetSize(self.WIDTH, height)
		self.board.SetSize(self.WIDTH, height)
		self.board.SetTitleName(title)
		for index, row in enumerate(self.rows):
			if index < row_count:
				label, destination_id = choices[index]
				row.SetLocation(label, destination_id)
				row.Show()
			else:
				row.Hide()
		if self.owner:
			self.SetPosition(
				(self.owner.windowWidth - self.WIDTH) // 2,
				(self.owner.windowHeight - height) // 2,
			)
		else:
			self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def Close(self):
		self.Hide()
		if self.owner:
			self.owner.ClearSelectedDestination()
			if self.owner.activePage == "dungeons":
				self.owner.ShowMaps()
		return True

	def CloseSilently(self):
		self.Hide()

	def Destroy(self):
		self.Hide()
		if self.board:
			self.board.SetCloseEvent(None)
		for row in self.rows:
			row.callback = None
		self.owner = None
		self.rows = []
		self.board = None

	def __RequestTeleport(self, destination_id):
		if destination_id and self.owner:
			self.owner.RequestDestination(destination_id)


class TeleportAtlasWindow(ui.ScriptWindow):

	WIDTH = 860
	HEIGHT = 513
	BOARD_X = 39
	BOARD_WIDTH = 821
	BOARD_HEIGHT = 513
	OCEAN_X = 0
	OCEAN_Y = 22
	OCEAN_WIDTH = 821
	OCEAN_HEIGHT = 491
	MAP_X = (BOARD_WIDTH - teleportmapdata.MAP_WIDTH) // 2
	MAP_Y = 8
	MAP_HEIGHT = teleportmapdata.MAP_HEIGHT + teleportmapdata.MAP_OFFSET_Y

	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.mapRegionImages = {}
		self.mapRegionStates = {}
		self.mapPortalImages = {}
		self.mapPortalStates = {}
		self.mapNameplates = {}
		self.mapSharedImages = []
		self.mapShadowOverlay = None
		self.mapShadowOverlayDestinationId = None
		self.mapHoverOverlay = None
		self.mapHoverOverlayDestinationId = None
		self.mapSelectedOverlay = None
		self.mapSelectedOverlayDestinationId = None
		self.mapInteraction = None
		self.levelHint = None
		self.levelHintDestinationId = None
		self.levelHintLocked = None
		self.levelHintHoverStartedAt = None
		self.dungeonPage = None
		self.listPage = None
		self.listToggle = None
		self.listEnabled, self.listCategory = teleportlistdata.LoadPreferences()
		self.selectedDestination = None
		self.highlightedDestinationId = None
		self.activePage = "maps"
		screen_width = wndMgr.GetScreenWidth()
		available_board_width = max(1, screen_width - self.BOARD_X - 8)
		self.mapScale = 1.0 if screen_width >= self.WIDTH else float(available_board_width) / float(self.BOARD_WIDTH)
		self.compactTitleBar = screen_width < self.WIDTH + 8
		self.windowWidth = self.WIDTH if self.mapScale >= 1.0 else self.BOARD_X + self.__Scaled(self.BOARD_WIDTH) + 4
		self.windowHeight = self.OCEAN_Y + self.__Scaled(self.OCEAN_HEIGHT)
		self.__BuildWindow()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __Scaled(self, value):
		return int(round(value * self.mapScale))

	def __ContentY(self, value):
		return self.OCEAN_Y + self.__Scaled(value - self.OCEAN_Y)

	def __BuildWindow(self):
		self.SetSize(self.windowWidth, self.windowHeight)
		self.SetCenterPosition()
		self.AddFlag("movable")
		self.AddFlag("float")

		self.__BuildSwitches()
		self.board = ui.BoardWithTitleBar()
		self.board.SetParent(self)
		self.board.SetPosition(self.BOARD_X, 0)
		self.board.SetSize(self.__Scaled(self.BOARD_WIDTH), self.windowHeight)
		if self.compactTitleBar:
			self.board.titleBar.SetPosition(0, 0)
			self.board.titleBar.SetWidth(self.__Scaled(self.BOARD_WIDTH))
		self.board.SetTitleName("Teleportace")
		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.board.Show()

		self.ocean = ui.ExpandedImageBox()
		self.ocean.SetParent(self.board)
		self.ocean.AddFlag("not_pick")
		self.ocean.SetPosition(self.OCEAN_X, self.OCEAN_Y)
		self.ocean.LoadImage(MODULAR_SKIN_PATH + "shared/ocean_full.png")
		self.ocean.SetScale(self.mapScale, self.mapScale)
		self.ocean.Show()

		self.__BuildMapAtlas()
		self.frameOverlay = ui.ExpandedImageBox()
		self.frameOverlay.SetParent(self.board)
		self.frameOverlay.AddFlag("not_pick")
		self.frameOverlay.AddFlag("float")
		self.frameOverlay.SetPosition(self.OCEAN_X, self.OCEAN_Y)
		self.frameOverlay.LoadImage(MODULAR_SKIN_PATH + "shared/frame_overlay.png")
		self.frameOverlay.SetScale(self.mapScale, self.mapScale)
		self.frameOverlay.Show()
		self.frameOverlay.SetTop()
		self.board.titleBar.AddFlag("float")
		self.board.titleBar.SetTop()
		self.destinationDialog = TeleportDestinationDialog(self)
		self.destinationDialog.SetParent(self)
		self.destinationDialog.Hide()
		if app.ENABLE_DUNGEON_INFO:
			self.dungeonPage = uiDungeonTrack.DungeonTeleportPage(self, self.mapScale)
			self.dungeonPage.SetParent(self.board)
			self.dungeonPage.SetPosition(0, self.OCEAN_Y)
			self.dungeonPage.Hide()
		self.listPage = uiteleportlist.TeleportListPage(self, self.mapScale, self.listCategory)
		self.listPage.SetParent(self.board)
		self.listPage.SetPosition(0, self.OCEAN_Y)
		self.listPage.Hide()
		self.listToggle = ui.CheckBox_N()
		self.listToggle.SetParent(self.board)
		self.listToggle.AddFlag("float")
		self.listToggle.SetPosition(self.__Scaled(614), self.__ContentY(39))
		self.listToggle.text.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY, 0))
		self.listToggle.text.AddFlag("not_pick")
		self.listToggle.SetText("Zobrazit jako seznam")
		self.listToggle.SetTextColor(0xffe8e0cf)
		self.listToggle.SetChecked(self.listEnabled)
		self.listToggle.SetEvent(ui.__mem_func__(self.ToggleListView))
		self.__ShowMaps()

	def __BuildMapAtlas(self):
		self.mapPanel = ui.Window()
		self.mapPanel.SetParent(self.board)
		self.mapPanel.SetPosition(self.__Scaled(self.MAP_X), self.__ContentY(self.MAP_Y))
		self.mapPanel.SetSize(self.__Scaled(teleportmapdata.MAP_WIDTH), self.__Scaled(self.MAP_HEIGHT))
		self.mapPanel.Show()

		for destination in teleportmapdata.DESTINATIONS:
			region = ui.ExpandedImageBox()
			region.SetParent(self.mapPanel)
			region.AddFlag("not_pick")
			region.SetPosition(
				self.__Scaled(destination["x"]),
				self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["y"]),
			)
			region.LoadImage(MODULAR_SKIN_PATH + destination["files"]["normal"])
			region.SetScale(self.mapScale, self.mapScale)
			region.Show()
			self.mapRegionImages[destination["id"]] = region
			self.mapRegionStates[destination["id"]] = "normal"

		boundary = ui.ExpandedImageBox()
		boundary.SetParent(self.mapPanel)
		boundary.AddFlag("not_pick")
		boundary.SetPosition(0, self.__Scaled(teleportmapdata.MAP_OFFSET_Y))
		boundary.LoadImage(MODULAR_SKIN_PATH + "shared/boundaries.png")
		boundary.SetScale(self.mapScale, self.mapScale)
		boundary.Show()
		self.mapSharedImages.append(boundary)

		self.mapShadowOverlay = self.__CreateMapOverlay()
		self.mapHoverOverlay = self.__CreateMapOverlay()
		self.mapSelectedOverlay = self.__CreateMapOverlay()

		for destination in teleportmapdata.DESTINATIONS:
			portal = ui.ExpandedImageBox()
			portal.SetParent(self.mapPanel)
			portal.AddFlag("not_pick")
			portal.SetPosition(
				self.__Scaled(destination["portal_x"]) - self.__Scaled(teleportmapdata.PORTAL_SIZE) // 2,
				self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["portal_y"]) - self.__Scaled(teleportmapdata.PORTAL_SIZE) // 2,
			)
			portal.LoadImage(MODULAR_SKIN_PATH + teleportmapdata.PORTAL_FILES["normal"])
			portal.SetScale(self.mapScale, self.mapScale)
			portal.Show()
			self.mapPortalImages[destination["id"]] = portal
			self.mapPortalStates[destination["id"]] = "normal"

			nameplate = AtlasRegionNameplate(self.mapPanel, destination["id"], self.mapScale)
			nameplate.SetPosition(
				self.__Scaled(destination["label_x"]) - nameplate.GetWidth() // 2,
				self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["label_y"]),
			)
			self.mapNameplates[destination["id"]] = nameplate

		self.mapInteraction = TeleportMapInteraction(self)
		self.mapInteraction.SetParent(self.mapPanel)
		self.mapInteraction.SetPosition(0, self.__Scaled(teleportmapdata.MAP_OFFSET_Y))
		self.mapInteraction.SetSize(self.__Scaled(teleportmapdata.MAP_WIDTH), self.__Scaled(teleportmapdata.MAP_HEIGHT))
		self.mapInteraction.Show()

		self.levelHint = AtlasLevelHint(self.mapPanel)

	def __CreateMapOverlay(self):
		overlay = ui.ExpandedImageBox()
		overlay.SetParent(self.mapPanel)
		overlay.AddFlag("not_pick")
		overlay.SetScale(self.mapScale, self.mapScale)
		overlay.Hide()
		return overlay

	def __BuildSwitches(self):
		self.mapSwitch = AtlasSwitchButton(self.__ShowMaps, "Mapy", "map")
		self.mapSwitch.SetParent(self)
		self.mapSwitch.SetPosition(self.BOARD_X - 30, 71)
		self.mapSwitch.Show()

		self.dungeonSwitch = AtlasSwitchButton(self.__ShowDungeons, "Dungeony", "dungeon")
		self.dungeonSwitch.SetParent(self)
		self.dungeonSwitch.SetPosition(self.BOARD_X - 30, 105)
		self.dungeonSwitch.Show()

	def __PrepareOpen(self):
		self.selectedDestination = None
		self.highlightedDestinationId = None
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.HideLevelHint()
		self.__RefreshActiveRegionOverlays()
		self.SetCenterPosition()

	def OpenMaps(self):
		self.__PrepareOpen()
		self.__ShowMaps()
		self.Show()
		self.SetTop()

	def OpenDungeons(self):
		self.__PrepareOpen()
		self.__ShowDungeons()
		self.Show()
		self.SetTop()

	def ToggleMaps(self):
		if self.IsShow():
			self.CloseAll()
		else:
			self.OpenMaps()

	def ToggleDungeons(self):
		if self.IsShow():
			self.CloseAll()
		else:
			self.OpenDungeons()

	def Open(self):
		self.selectedDestination = None
		self.highlightedDestinationId = None
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.OpenMaps()

	def Close(self):
		if self.destinationDialog and self.destinationDialog.IsShow():
			self.destinationDialog.Close()
			return True
		if self.dungeonPage:
			self.dungeonPage.ClosePage()
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.HideLevelHint()
		self.HighlightMapDestination(None)
		self.Hide()
		return True

	def CloseAll(self):
		if self.destinationDialog:
			self.destinationDialog.CloseSilently()
		if self.dungeonPage:
			self.dungeonPage.ClosePage()
		self.selectedDestination = None
		self.highlightedDestinationId = None
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.HideLevelHint()
		self.__RefreshActiveRegionOverlays()
		self.Hide()
		return True

	def Destroy(self):
		if self.listPage:
			self.listPage.Destroy()
		if self.listToggle:
			self.listToggle.SetEvent(None)
		if self.dungeonPage:
			self.dungeonPage.ClosePage()
			self.dungeonPage.Destroy()
		if self.mapInteraction:
			self.mapInteraction.ClearOwner()
		if self.levelHint:
			self.levelHint.Destroy()
		if self.destinationDialog:
			self.destinationDialog.Destroy()
		self.ClearDictionary()
		self.mapRegionImages = {}
		self.mapRegionStates = {}
		self.mapPortalImages = {}
		self.mapPortalStates = {}
		self.mapNameplates = {}
		self.mapSharedImages = []
		self.frameOverlay = None
		self.mapInteraction = None
		self.levelHint = None
		self.dungeonPage = None
		self.destinationDialog = None
		self.listPage = None
		self.listToggle = None

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __ShowMaps(self):
		if self.dungeonPage:
			self.dungeonPage.ClosePage()
		if self.destinationDialog:
			self.destinationDialog.CloseSilently()
		self.ClearSelectedDestination()
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.HideLevelHint()
		self.activePage = "maps"
		self.mapSwitch.SetSelected(True)
		self.dungeonSwitch.SetSelected(False)
		if self.listEnabled:
			self.ocean.Hide()
			self.mapPanel.Hide()
			self.listPage.Refresh()
			self.listPage.Show()
		else:
			self.listPage.Hide()
			self.ocean.Show()
			self.mapPanel.Show()
		self.listToggle.SetChecked(self.listEnabled)
		self.listToggle.Show()
		self.frameOverlay.Show()
		self.frameOverlay.SetTop()
		self.listToggle.SetTop()
		self.board.titleBar.SetTop()

	def ShowMaps(self):
		self.__ShowMaps()

	def ToggleListView(self):
		self.listEnabled = self.listToggle.IsChecked()
		self.SaveListPreferences()
		self.HighlightMapDestination(None)
		self.__ShowMaps()

	def SaveListPreferences(self):
		if self.listPage:
			self.listCategory = self.listPage.model.category
		teleportlistdata.SavePreferences(self.listEnabled, self.listCategory)

	def __ShowDungeons(self):
		if not self.dungeonPage:
			self.__ShowMaps()
			return
		self.destinationDialog.CloseSilently()
		self.ClearSelectedDestination()
		if self.mapInteraction:
			self.mapInteraction.hoveredDestinationId = None
		self.HideLevelHint()
		self.HighlightMapDestination(None)
		self.activePage = "dungeons"
		self.mapSwitch.SetSelected(False)
		self.dungeonSwitch.SetSelected(True)
		self.ocean.Hide()
		self.mapPanel.Hide()
		self.listPage.Hide()
		self.listToggle.Hide()
		self.frameOverlay.Hide()
		self.dungeonPage.OpenPage()
		self.board.titleBar.SetTop()

	def RefreshDungeons(self):
		if self.dungeonPage:
			self.dungeonPage.Refresh()

	def LoadDungeonServerData(self, mobIdx, rankIdx, cmd):
		if self.dungeonPage:
			self.dungeonPage.LoadServerData(mobIdx, rankIdx, cmd)

	def HighlightMapDestination(self, destination_id):
		if self.activePage != "maps":
			return
		if self.highlightedDestinationId == destination_id:
			return
		self.highlightedDestinationId = destination_id
		self.__RefreshActiveRegionOverlays()

	def HideLevelHint(self):
		self.levelHintDestinationId = None
		self.levelHintLocked = None
		self.levelHintHoverStartedAt = None
		if self.levelHint:
			self.levelHint.HideHint()

	def UpdateLevelHint(self, destination_id, changed=False):
		if self.activePage != "maps" or not destination_id or not self.levelHint:
			self.HideLevelHint()
			return
		destination = teleportmapdata.GetDestination(destination_id)
		if not destination:
			self.HideLevelHint()
			return
		player_level = player.GetStatus(player.LEVEL)
		locked = player_level < destination["level"]
		if changed or destination_id != self.levelHintDestinationId or locked != self.levelHintLocked:
			self.levelHintDestinationId = destination_id
			self.levelHintLocked = locked
			self.levelHintHoverStartedAt = app.GetTime()
			self.levelHint.SetLevel(destination["level"], locked)
			self.levelHint.HideHint()
		delay = GetLevelHintDelay(player_level, destination["level"])
		if app.GetTime() - self.levelHintHoverStartedAt < delay:
			return
		lift_y = 0 if locked else teleportmapdata.HOVER_LIFT_Y
		self.levelHint.SetPosition(
			self.__Scaled(destination["portal_x"]) - self.levelHint.WIDTH // 2,
			self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["portal_y"] - lift_y) - self.levelHint.PORTAL_OFFSET_Y,
		)
		if not self.levelHint.IsShow():
			self.levelHint.ShowHint()

	def SelectDestination(self, destination_id):
		destination = teleportmapdata.GetDestination(destination_id)
		if not destination or player.GetStatus(player.LEVEL) < destination["level"]:
			return
		if destination_id == "all_in_one":
			self.selectedDestination = destination
			self.__RefreshActiveRegionOverlays()
			self.destinationDialog.Open(destination["name"], teleportmapdata.ALL_IN_ONE_CHOICES)
		else:
			self.selectedDestination = None
			self.__RefreshActiveRegionOverlays()
			self.__RequestSelectedDestination(destination_id)

	def RequestDestination(self, destination_id):
		self.__RequestSelectedDestination(destination_id)

	def ClearSelectedDestination(self):
		self.selectedDestination = None
		self.__RefreshActiveRegionOverlays()

	def __SetRegionOverlay(self, overlay, destination_id, state, lift_y=0):
		if not destination_id:
			overlay.Hide()
			return
		destination = teleportmapdata.GetDestination(destination_id)
		if not destination:
			overlay.Hide()
			return
		overlay.SetPosition(
			self.__Scaled(destination["x"]),
			self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["y"] - lift_y),
		)
		relative = state == "shadow" and destination["shadow"] or destination["files"][state]
		overlay.LoadImage(MODULAR_SKIN_PATH + relative)
		overlay.SetScale(self.mapScale, self.mapScale)
		overlay.Show()

	def __RefreshActiveRegionOverlays(self):
		selected_id = self.selectedDestination and self.selectedDestination["id"]
		hover_id = self.highlightedDestinationId
		hover_destination = teleportmapdata.GetDestination(hover_id)
		if hover_destination and player.GetStatus(player.LEVEL) < hover_destination["level"]:
			hover_id = None
		if hover_id == selected_id:
			hover_id = None

		self.__SetRegionOverlay(self.mapShadowOverlay, selected_id, "shadow")
		self.__SetRegionOverlay(self.mapHoverOverlay, hover_id, "selected", teleportmapdata.HOVER_LIFT_Y)
		self.__SetRegionOverlay(self.mapSelectedOverlay, selected_id, "selected", teleportmapdata.SELECTED_LIFT_Y)

		for destination in teleportmapdata.DESTINATIONS:
			destination_id = destination["id"]
			unavailable = player.GetStatus(player.LEVEL) < destination["level"]
			base_state = unavailable and "disabled" or "normal"
			region = self.mapRegionImages[destination_id]
			if self.mapRegionStates.get(destination_id) != base_state:
				region.LoadImage(MODULAR_SKIN_PATH + destination["files"][base_state])
				region.SetScale(self.mapScale, self.mapScale)
				self.mapRegionStates[destination_id] = base_state
			if destination_id == selected_id or destination_id == hover_id:
				region.Hide()
			else:
				region.Show()

			if destination_id == selected_id:
				portal_state, nameplate_state, lift_y = "selected", "selected", teleportmapdata.SELECTED_LIFT_Y
			elif destination_id == hover_id:
				portal_state, nameplate_state, lift_y = "selected", "hover", teleportmapdata.HOVER_LIFT_Y
			elif unavailable:
				portal_state, nameplate_state, lift_y = "unavailable", "disabled", 0
			else:
				portal_state, nameplate_state, lift_y = "normal", "normal", 0
			portal = self.mapPortalImages[destination_id]
			if self.mapPortalStates.get(destination_id) != portal_state:
				portal.LoadImage(MODULAR_SKIN_PATH + teleportmapdata.PORTAL_FILES[portal_state])
				portal.SetScale(self.mapScale, self.mapScale)
				self.mapPortalStates[destination_id] = portal_state
			anchor_x = destination["portal_x"]
			anchor_y = destination["portal_y"]
			portal.SetPosition(
				self.__Scaled(anchor_x) - self.__Scaled(teleportmapdata.PORTAL_SIZE) // 2,
				self.__Scaled(teleportmapdata.MAP_OFFSET_Y + anchor_y - lift_y) - self.__Scaled(teleportmapdata.PORTAL_SIZE) // 2,
			)
			nameplate = self.mapNameplates[destination_id]
			nameplate.SetState(nameplate_state)
			nameplate.SetPosition(
				self.__Scaled(anchor_x) - nameplate.GetWidth() // 2,
				self.__Scaled(teleportmapdata.MAP_OFFSET_Y + destination["label_y"] - lift_y),
			)

	def __RequestSelectedDestination(self, destination_id):
		if not destination_id:
			return
		net.SendChatPacket("/teleport_atlas %s" % destination_id)
		self.destinationDialog.Close()
		self.Close()
