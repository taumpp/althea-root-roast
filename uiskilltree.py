# -*- coding: utf-8 -*-

import bonuscolor
import ui
import uiCommon
import uiToolTip
import uiScriptLocale
import talent_tree_layout
import talent_tree_layout_v7_900
import talent_tree_layout_v7_780
import skilltreelocale
import skilltreecatalog
import wndMgr
import weakref
import item
import player
import app
import math
import dbg
import fontconfig
import uicrimsoncontrols
import uiskilltreedismantle
import ownedcount


def _SetImageDiffuseColor(imageBox, red, green, blue, alpha):
	ui.wndMgr.SetDiffuseColor(imageBox.hWnd, red, green, blue, alpha)


def _IsMouseInsideWindowBounds(window):
	if not window:
		return False
	mouseX, mouseY = wndMgr.GetMousePosition()
	windowX, windowY = window.GetGlobalPosition()
	return (
		windowX <= mouseX <= windowX + window.GetWidth()
		and windowY <= mouseY <= windowY + window.GetHeight()
	)


SKIN_PATH = "d:/ymir work/ui/game/skill_tree_v2/"
V7_PRESET_PATH = SKIN_PATH + "preset_%s/"
V7_TREE_VERSION = skilltreecatalog.TREE_VERSION
V7_CATALOG_HASH = skilltreecatalog.CATALOG_HASH
V7_WIRE_NODE_IDS = skilltreecatalog.NODE_IDS
V7_VISIBLE_NODE_IDS = skilltreecatalog.VISIBLE_NODE_IDS
V7_HIDDEN_NODE_IDS = (2000,)
V7_EDGE_STATES = ("locked", "neutral", "active", "highlighted")

EXPECTED_EDGES = frozenset((parent, child, rank)
	for child, parents in skilltreecatalog.PARENTS_BY_ID.items()
	for parent, rank in parents if parent in skilltreecatalog.VISIBLE_NODE_IDS)


def ValidateSkillTreeV7Layout(layoutModule):
	if (
		getattr(layoutModule, "TREE_VERSION", None) != V7_TREE_VERSION
		or getattr(layoutModule, "CATALOG_HASH", None) != V7_CATALOG_HASH
		or getattr(layoutModule, "WIRE_NODE_IDS", None) != V7_WIRE_NODE_IDS
		or getattr(layoutModule, "VISIBLE_NODE_IDS", None) != V7_VISIBLE_NODE_IDS
		or getattr(layoutModule, "HIDDEN_NODE_IDS", None) != V7_HIDDEN_NODE_IDS
	):
		raise ValueError("Skill Tree V7 layout identity mismatch")
	nodes = getattr(layoutModule, "NODES", None)
	edges = getattr(layoutModule, "EDGES", None)
	assets = getattr(layoutModule, "EDGE_ASSETS", None)
	nodeAssets = getattr(layoutModule, "NODE_ASSETS", None)
	expectedGeometry = {
		"900": ((900, 600), (8, 28, 884, 516), (8, 546, 884, 46),
				 (0, 0, 0, 0), (0, 0), False),
		"780": ((780, 520), (8, 28, 764, 436), (8, 466, 764, 46),
				 (-120, 0, -80, 0), (-60, -80), True),
	}
	preset = getattr(layoutModule, "PRESET", None)
	geometry = expectedGeometry.get(preset)
	if not geometry or (
		(getattr(layoutModule, "WINDOW_WIDTH", None),
		 getattr(layoutModule, "WINDOW_HEIGHT", None)) != geometry[0]
		or (getattr(layoutModule, "CANVAS_WIDTH", None),
			getattr(layoutModule, "CANVAS_HEIGHT", None)) != (884, 516)
		or getattr(layoutModule, "VIEWPORT_RECT", None) != geometry[1]
		or getattr(layoutModule, "FOOTER_RECT", None) != geometry[2]
		or getattr(layoutModule, "CANVAS_OFFSET_BOUNDS", None) != geometry[3]
		or getattr(layoutModule, "INITIAL_CANVAS_OFFSET", None) != geometry[4]
		or getattr(layoutModule, "DRAG_ENABLED", None) is not geometry[5]
		or getattr(layoutModule, "DRAG_THRESHOLD", None) != 5
		or getattr(layoutModule, "NODE_SIZE", None) != 56
		or getattr(layoutModule, "RANK_BADGE_SIZE", None) != (23, 23)
		or getattr(layoutModule, "PLUS_VISUAL_SIZE", None) != 23
		or getattr(layoutModule, "PLUS_HIT_SIZE", None) != 30
		or getattr(layoutModule, "OVERLAY_MARGIN", None) != 5
	):
		raise ValueError("Skill Tree V7 adaptive geometry mismatch")
	if not isinstance(nodes, (list, tuple)) or len(nodes) != len(V7_VISIBLE_NODE_IDS):
		raise ValueError("Skill Tree V7 node inventory mismatch")
	if tuple(node.get("node_id") for node in nodes if isinstance(node, dict)) != V7_VISIBLE_NODE_IDS:
		raise ValueError("Skill Tree V7 node identity mismatch")
	if not isinstance(nodeAssets, dict) or frozenset(nodeAssets) != frozenset(V7_VISIBLE_NODE_IDS):
		raise ValueError("Skill Tree V7 node assets mismatch")
	for nodeId, record in nodeAssets.items():
		if (
			not isinstance(record, dict)
			or frozenset(record) != frozenset(("color", "muted"))
			or record.get("color") != "icon_%d.tga" % nodeId
			or record.get("muted") != "icon_%d_muted.tga" % nodeId
		):
			raise ValueError("Skill Tree V7 node asset is malformed")
	if not isinstance(edges, (list, tuple)) or len(edges) != len(EXPECTED_EDGES):
		raise ValueError("Skill Tree V7 edge inventory mismatch")
	actualEdges = frozenset(
		(edge.get("parent_id"), edge.get("child_id"), edge.get("required_parent_rank"))
		for edge in edges if isinstance(edge, dict)
	)
	if actualEdges != EXPECTED_EDGES or any(
		parent not in V7_VISIBLE_NODE_IDS or child not in V7_VISIBLE_NODE_IDS
		for parent, child, unusedRank in actualEdges
	):
		raise ValueError("Skill Tree V7 edge identity mismatch")
	expectedKeys = frozenset((parent, child) for parent, child, unusedRank in actualEdges)
	if not isinstance(assets, dict) or frozenset(assets) != expectedKeys:
		raise ValueError("Skill Tree V7 edge assets mismatch")
	for key, stateAssets in assets.items():
		if not isinstance(stateAssets, dict) or frozenset(stateAssets) != frozenset(V7_EDGE_STATES):
			raise ValueError("Skill Tree V7 connector states mismatch")
		for state in V7_EDGE_STATES:
			record = stateAssets[state]
			expectedName = "edge_%d_%d_%s.tga" % (key[0], key[1], state)
			if (
				not isinstance(record, dict)
				or frozenset(record) != frozenset(("path", "offset", "sha256"))
				or record.get("path") != expectedName
				or not isinstance(record.get("offset"), tuple)
				or len(record["offset"]) != 2
				or not isinstance(record.get("sha256"), _STRING_TYPES)
				or len(record["sha256"]) != 64
				or any(isinstance(value, bool) or not isinstance(value, _INTEGER_TYPES)
				       for value in record["offset"])
			):
				raise ValueError("Skill Tree V7 connector asset is malformed")
	return True


def PreflightSkillTreeV7Assets(layoutModule):
	if not skilltreelocale.HasCompleteLocale("cz", V7_WIRE_NODE_IDS):
		raise ValueError("Skill Tree V7 Czech locale is incomplete")
	if not skilltreelocale.HasCompleteLocale("en", V7_WIRE_NODE_IDS):
		raise ValueError("Skill Tree V7 English locale is incomplete")
	presetPath = V7_PRESET_PATH % layoutModule.PRESET
	paths = [presetPath + row["path"] for row in layoutModule.BACKGROUND_ASSETS]
	for nodeId in V7_VISIBLE_NODE_IDS:
		paths.extend(presetPath + layoutModule.NODE_ASSETS[nodeId][state]
			for state in ("color", "muted"))
	paths.extend(presetPath + "state_%s.tga" % state for state in (
		"locked", "available", "learned", "maxed", "hover", "selected",
	))
	paths.extend(presetPath + "control_rank-digit-%d.tga" % rank for rank in range(1, 6))
	paths.extend(presetPath + name for name in (
		"control_rank-badge.tga", "control_plus-available.tga",
		"control_plus-hover.tga", "control_plus-pressed.tga",
		"energy_spark.tga",
	))
	paths.extend(SKIN_PATH + "activation/" + name for name in (
		"status_off.png", "status_on.png",
	))
	paths.extend(SKIN_PATH + "activation/status_on_%02d.png" % frame for frame in range(32))
	for stateAssets in layoutModule.EDGE_ASSETS.values():
		paths.extend(presetPath + stateAssets[state]["path"] for state in V7_EDGE_STATES)
	preflight = ui.ImageBox()
	try:
		preflight.Hide()
		for path in paths:
			try:
				preflight.LoadImage(path)
			except Exception as error:
				raise RuntimeError(
					"Skill Tree V7 asset unavailable: %s (%s)" % (path, error),
				)
	finally:
		try:
			preflight.Hide()
		finally:
			if getattr(preflight, "hWnd", None):
				wndMgr.Destroy(preflight.hWnd)
				preflight.hWnd = None
	return True


def SelectSkillTreePreset(screenWidth, screenHeight):
	try:
		screenWidth = int(screenWidth)
		screenHeight = int(screenHeight)
	except (TypeError, ValueError):
		return talent_tree_layout_v7_780
	if screenWidth >= 900 and screenHeight >= 600:
		return talent_tree_layout_v7_900
	return talent_tree_layout_v7_780


def ClampSkillTreePosition(x, y, width, height, screenWidth, screenHeight):
	try:
		x = int(x)
		y = int(y)
		screenWidth = max(0, int(screenWidth))
		screenHeight = max(0, int(screenHeight))
	except (TypeError, ValueError):
		return 0, 0
	return (
		max(0, min(x, max(0, screenWidth - int(width)))),
		max(0, min(y, max(0, screenHeight - int(height)))),
	)


def _ClientLocaleKey():
	try:
		path = app.GetLocalePath().replace("\\", "/").lower().rstrip("/")
		if path.endswith("/cz") or path == "cz":
			return "cz"
	except Exception:
		pass
	return "en"

NODE_STATES = (
	"locked", "available", "learned", "learned_active",
	"maxed", "maxed_active",
)

PRESENTER_NODE_STATES = ("locked", "available", "learned", "maxed")

ROUND_STATE_ASSETS = {
	"locked": SKIN_PATH + "node_round_locked_v4.tga",
	"available": SKIN_PATH + "node_round_available_v4.tga",
	"learned": SKIN_PATH + "node_round_available_v4.tga",
	"learned_active": SKIN_PATH + "node_round_learned_active_v4.tga",
	"maxed": SKIN_PATH + "node_round_available_v4.tga",
	"maxed_active": SKIN_PATH + "node_round_maxed_active_v4.tga",
}

MILESTONE_STATE_ASSETS = {
	"locked": SKIN_PATH + "node_milestone_locked_v4.tga",
	"available": SKIN_PATH + "node_milestone_available_v4.tga",
	"learned": SKIN_PATH + "node_milestone_available_v4.tga",
	"learned_active": SKIN_PATH + "node_milestone_learned_active_v4.tga",
	"maxed": SKIN_PATH + "node_milestone_available_v4.tga",
	"maxed_active": SKIN_PATH + "node_milestone_maxed_active_v4.tga",
}

PLUS_UP_ASSET = SKIN_PATH + "plus_up_v4.tga"
PLUS_OVER_ASSET = SKIN_PATH + "plus_hover_v4.tga"
PLUS_DOWN_ASSET = SKIN_PATH + "plus_down_v4.tga"
PLUS_DISABLED_ASSET = SKIN_PATH + "plus_disabled_v4.tga"
RANK_BADGE_ASSET = SKIN_PATH + "rank_badge_v4.tga"
GLOW_MASK_ASSET = SKIN_PATH + "glow_mask_v4.tga"

SHORTCUT_UP_ASSET = SKIN_PATH + "minimap_launcher_normal_v4.tga"
SHORTCUT_OVER_ASSET = SKIN_PATH + "minimap_launcher_hover_v4.tga"
SHORTCUT_DOWN_ASSET = SKIN_PATH + "minimap_launcher_down_v4.tga"

ICON_ASSETS = {
	"attack": SKIN_PATH + "glyph_attack_v4.tga",
	"defense": SKIN_PATH + "glyph_defense_v4.tga",
	"health": SKIN_PATH + "glyph_health_v4.tga",
	"speed": SKIN_PATH + "glyph_speed_v4.tga",
	"critical": SKIN_PATH + "glyph_critical_v4.tga",
	"monster": SKIN_PATH + "glyph_monster_v4.tga",
	"boss": SKIN_PATH + "glyph_boss_v4.tga",
	"metin": SKIN_PATH + "glyph_metin_v4.tga",
	"drop": SKIN_PATH + "glyph_drop_v4.tga",
	"yang": SKIN_PATH + "glyph_yang_v4.tga",
	"resistance": SKIN_PATH + "glyph_resistance_v4.tga",
	"mastery": SKIN_PATH + "glyph_mastery_v4.tga",
}

FAMILY_GLOW_COLORS = {
	0: (0.80, 0.54, 0.22),
	1: (0.25, 0.63, 0.83),
	2: (0.25, 0.67, 0.54),
	3: (0.54, 0.36, 0.79),
}
STATUS_OFF_ASSET = "status_off.png"
STATUS_ON_ASSET = "status_on.png"
ACTIVATION_FRAME_SECONDS = 0.08
ACTIVATION_FRAME_COUNT = 32
RENEW_SECONDS = 8 * 3600


def _SkillTreePresetAsset(layoutModule, filename):
	return (V7_PRESET_PATH % layoutModule.PRESET) + filename

WORLD_TREE_ASSETS = (
	SKIN_PATH + "canvas_00_v4.tga",
	SKIN_PATH + "canvas_01_v4.tga",
	SKIN_PATH + "canvas_02_v4.tga",
)
WORLD_TREE_Y_POSITIONS = (0, 640, 1280)

RANK_BADGE_SIZE = (22, 20)
PLUS_BUTTON_SIZE = (18, 18)

VIEWPORT_WIDTH = 692
VIEWPORT_HEIGHT = 404
VIEWPORT_CULL_MARGIN = 96
MAX_SCROLL_OFFSET = 1496
SCROLL_WHEEL_STEP = 72

MAX_VISIBLE_RENEW_COST_ROWS = 8
MAX_RENEW_COST_ROWS = 64

RENEW_TOOLTIP_WIDTH = 320
RENEW_TOOLTIP_TITLE_Y = 12
RENEW_TOOLTIP_ROWS_Y = 36
RENEW_TOOLTIP_ROW_HEIGHT = 36
RENEW_TOOLTIP_HEIGHT = RENEW_TOOLTIP_ROWS_Y + MAX_VISIBLE_RENEW_COST_ROWS * RENEW_TOOLTIP_ROW_HEIGHT + 8
# the panel is as large as its rows (RENEW_TOOLTIP_WIDTH x RENEW_TOOLTIP_HEIGHT only while it scrolls):
# at least RENEW_TOOLTIP_MIN_WIDTH wide, RENEW_TOOLTIP_PAD px right of the widest row, RENEW_TOOLTIP_BOTTOM px under
# the last row's content (an item icon is 32 px tall, the yang price RENEW_YANG_ROW_HEIGHT)
RENEW_TOOLTIP_MIN_WIDTH = 180
RENEW_TOOLTIP_PAD = 12
RENEW_TOOLTIP_BOTTOM = 10
RENEW_ITEM_ROW_HEIGHT = 32
RENEW_YANG_ROW_HEIGHT = 16
RENEW_YANG_ROW_Y = 8

try:
	_INTEGER_TYPES = (int, long)
except NameError:
	_INTEGER_TYPES = (int,)

try:
	_STRING_TYPES = (basestring,)
except NameError:
	_STRING_TYPES = (str,)


class TalentNodeWidget(ui.Window):

	def __init__(self, owner, nodeData, rank, state):
		ui.Window.__init__(self)

		self.owner = owner
		self.nodeData = nodeData
		self.nodeSize = (
			talent_tree_layout.MILESTONE_NODE_SIZE
			if nodeData["milestone"]
			else talent_tree_layout.REGULAR_NODE_SIZE
		)
		nodeCenter = self.nodeSize // 2
		rankBadgePosition = (
			nodeCenter + nodeData["rank_offset"][0] - RANK_BADGE_SIZE[0] // 2,
			nodeCenter + nodeData["rank_offset"][1] - RANK_BADGE_SIZE[1] // 2,
		)
		rankTextPosition = (
			rankBadgePosition[0] + RANK_BADGE_SIZE[0] // 2,
			rankBadgePosition[1] + 2,
		)
		plusButtonPosition = (
			nodeCenter + nodeData["plus_offset"][0] - PLUS_BUTTON_SIZE[0] // 2,
			nodeCenter + nodeData["plus_offset"][1] - PLUS_BUTTON_SIZE[1] // 2,
		)
		self.maxRank = nodeData["max_rank"]
		self.rank = 0
		self.state = "locked"
		self.visualState = None
		self.snapshotReady = False
		self.presenter = None

		self.SetSize(self.nodeSize, self.nodeSize)
		self.AddFlag("dragable")

		self.glowMask = ui.ImageBox()
		self.glowMask.SetParent(self)
		self.glowMask.SetPosition((self.nodeSize - 76) // 2, (self.nodeSize - 76) // 2)
		self.glowMask.SetSize(76, 76)
		self.glowMask.LoadImage(GLOW_MASK_ASSET)
		self.glowMask.AddFlag("not_pick")
		self.glowMask.Hide()

		self.icon = ui.ImageBox()
		self.icon.SetParent(self)
		iconOffsetX, iconOffsetY = nodeData.get("icon_offset", (0, 0))
		self.icon.SetPosition(
			(self.nodeSize - 40) // 2 + iconOffsetX,
			(self.nodeSize - 40) // 2 + iconOffsetY,
		)
		self.icon.SetSize(40, 40)
		self.icon.LoadImage(ICON_ASSETS[nodeData["icon_key"]])
		self.icon.AddFlag("not_pick")
		self.icon.Show()

		self.frame = ui.ImageBox()
		self.frame.SetParent(self)
		self.frame.SetPosition(0, 0)
		self.frame.SetSize(self.nodeSize, self.nodeSize)
		self.frame.AddFlag("not_pick")
		self.frame.Show()

		self.rankBadge = ui.ImageBox()
		self.rankBadge.SetParent(self)
		self.rankBadge.SetPosition(*rankBadgePosition)
		self.rankBadge.LoadImage(RANK_BADGE_ASSET)
		self.rankBadge.AddFlag("not_pick")
		self.rankBadge.Show()

		self.rankText = ui.TextLine()
		self.rankText.SetParent(self)
		self.rankText.SetPosition(*rankTextPosition)
		self.rankText.SetHorizontalAlignCenter()
		self.rankText.SetOutline()
		self.rankText.AddFlag("not_pick")
		self.rankText.Show()

		self.plusButton = ui.Button()
		self.plusButton.SetParent(self)
		self.plusButton.SetPosition(*plusButtonPosition)
		self.plusButton.SetSize(*PLUS_BUTTON_SIZE)
		self.plusButton.SetUpVisual(PLUS_UP_ASSET)
		self.plusButton.SetOverVisual(PLUS_OVER_ASSET)
		self.plusButton.SetDownVisual(PLUS_DOWN_ASSET)
		self.plusButton.SetDisableVisual(PLUS_DISABLED_ASSET)
		self.plusButton.SetEvent(ui.__mem_func__(self.__OnUpgrade))
		self.plusButton.Show()

		if rank is None:
			self.SetLoadingState()
		else:
			self.SetState(rank, state)

	def SetLoadingState(self):
		self.snapshotReady = False
		self.presenter = None
		self.rank = 0
		self.state = "locked"
		if self.nodeData["milestone"]:
			self.frame.LoadImage(MILESTONE_STATE_ASSETS["locked"])
		else:
			self.frame.LoadImage(ROUND_STATE_ASSETS["locked"])
		_SetImageDiffuseColor(self.icon, 0.72, 0.76, 0.78, 0.92)
		self.glowMask.Hide()
		self.visualState = "locked"
		self.rankText.SetText("0")
		self.plusButton.Disable()

	def SetPresenter(self, presenter, treeActive):
		if not isinstance(presenter, dict) or not isinstance(treeActive, bool):
			return False
		rank = presenter.get("rank")
		maxRank = presenter.get("max_rank")
		if isinstance(rank, bool) or not isinstance(rank, _INTEGER_TYPES):
			return False
		if isinstance(maxRank, bool) or not isinstance(maxRank, _INTEGER_TYPES):
			return False
		state = presenter.get("state")
		if treeActive and state == "learned":
			state = "learned_active"
		elif treeActive and state == "maxed":
			state = "maxed_active"
		if not self.SetState(
			rank, state, maxRank,
		):
			return False
		self.presenter = dict(presenter)
		self.presenter["activation_enabled"] = bool(treeActive)
		return True

	def SetState(self, rank, state, maxRank=None):
		if state not in NODE_STATES:
			return False
		if isinstance(rank, bool) or not isinstance(rank, _INTEGER_TYPES):
			return False
		if maxRank is not None:
			if isinstance(maxRank, bool) or not isinstance(maxRank, _INTEGER_TYPES):
				return False
			if maxRank < 1 or maxRank > 5:
				return False
			self.maxRank = int(maxRank)

		wasSnapshotReady = self.snapshotReady
		self.snapshotReady = True
		self.rank = max(0, min(int(rank), self.maxRank))
		self.state = state
		if state != self.visualState or not wasSnapshotReady:
			if self.nodeData["milestone"]:
				self.frame.LoadImage(MILESTONE_STATE_ASSETS[state])
			else:
				self.frame.LoadImage(ROUND_STATE_ASSETS[state])
			if state == "locked":
				_SetImageDiffuseColor(self.icon, 0.72, 0.76, 0.78, 0.92)
			elif state in ("learned_active", "maxed_active"):
				_SetImageDiffuseColor(self.icon, 0.68, 0.94, 1.0, 1.0)
			elif state in ("learned", "maxed"):
				red, green, blue = FAMILY_GLOW_COLORS[self.nodeData.get("family_id", 0)]
				_SetImageDiffuseColor(
					self.icon,
					0.72 + red * 0.28,
					0.72 + green * 0.28,
					0.72 + blue * 0.28,
					1.0,
				)
			else:
				_SetImageDiffuseColor(self.icon, 1.0, 1.0, 1.0, 1.0)
			self.__RefreshGlow(state)
			self.visualState = state
		self.rankText.SetText(str(self.rank))
		canUpgrade = (
			self.owner
			and self.owner.CanUpgradeNode(self.nodeData["node_id"])
			and state in ("available", "learned", "learned_active")
			and self.rank < self.maxRank
		)
		if canUpgrade:
			self.plusButton.Enable()
		else:
			self.plusButton.Disable()
		return True

	def __RefreshGlow(self, state):
		if state == "locked":
			alpha = 0.18
		elif state == "available":
			alpha = 0.42
		elif state in ("learned_active", "maxed_active"):
			alpha = 0.95
		else:
			self.glowMask.Hide()
			return
		red, green, blue = FAMILY_GLOW_COLORS[self.nodeData.get("family_id", 0)]
		_SetImageDiffuseColor(self.glowMask, red, green, blue, alpha)
		self.glowMask.Show()

	def __OnUpgrade(self):
		if self.owner:
			self.owner.RequestNodeUpgrade(self.nodeData["node_id"])

	def OnMouseOverIn(self):
		if self.owner:
			self.owner.ShowNodeToolTip(self)

	def OnMouseOverOut(self):
		if self.owner:
			self.owner.HideNodeToolTip()

	def OnMouseLeftButtonDown(self):
		beginDrag = getattr(self.owner, "BeginTreeDrag", None)
		if beginDrag:
			return beginDrag()
		return False

	def OnMouseDrag(self, x, y):
		dragTree = getattr(self.owner, "DragTree", None)
		if dragTree:
			return dragTree(x, y)
		return False

	def OnMouseLeftButtonUp(self):
		endDrag = getattr(self.owner, "EndTreeDrag", None)
		if endDrag:
			return endDrag()
		return False


class TalentTreeCanvas(ui.Window):

	def __init__(self, owner):
		ui.Window.__init__(self)

		self.owner = owner
		self.SetSize(talent_tree_layout.CANVAS_WIDTH, talent_tree_layout.CANVAS_HEIGHT)
		self.AddFlag("not_pick")

		self.treeTiles = []
		for tileIndex, tilePath in enumerate(WORLD_TREE_ASSETS):
			tile = ui.ImageBox()
			tile.SetParent(self)
			tile.SetPosition(0, WORLD_TREE_Y_POSITIONS[tileIndex])
			tile.LoadImage(tilePath)
			tile.AddFlag("not_pick")
			tile.Show()
			self.treeTiles.append(tile)

		self.connectors = []
		self.connectorsByChildId = {}
		for edgeData in talent_tree_layout.EDGES:
			childId = edgeData["child_id"]
			connector = ui.ImageBox()
			connector.SetParent(self)
			connector.SetPosition(edgeData["offset_x"], edgeData["offset_y"])
			connector.LoadImage(SKIN_PATH + edgeData["asset"])
			connector.AddFlag("not_pick")
			connector.skillTreeY = edgeData["offset_y"]
			connector.skillTreeHeight = edgeData["height"]
			connector.skillTreeParentId = edgeData["parent_id"]
			connector.skillTreeChildId = childId
			connector.skillTreeBridge = bool(edgeData.get("bridge", False))
			connector.skillTreeActive = False
			connector.Hide()
			self.connectors.append(connector)
			self.connectorsByChildId.setdefault(childId, []).append(connector)

		self.junctions = []
		self.junctionsByChildId = {}
		for junctionData in talent_tree_layout.JUNCTIONS:
			junction = ui.ImageBox()
			junction.SetParent(self)
			junction.SetPosition(junctionData["offset_x"], junctionData["offset_y"])
			junction.LoadImage(SKIN_PATH + junctionData["asset"])
			junction.AddFlag("not_pick")
			junction.skillTreeY = junctionData["offset_y"]
			junction.skillTreeHeight = junctionData["height"]
			junction.skillTreeActive = False
			junction.Hide()
			self.junctions.append(junction)
			self.junctionsByChildId[junctionData["child_id"]] = junction

		self.nodesById = {}
		for nodeData in talent_tree_layout.NODES:
			nodeWidget = TalentNodeWidget(self.owner, nodeData, None, "locked")
			nodeWidget.SetParent(self)
			nodeWidget.SetPosition(
				nodeData["x"] - nodeWidget.nodeSize // 2,
				nodeData["y"] - nodeWidget.nodeSize // 2,
			)
			nodeWidget.Show()
			self.nodesById[nodeData["node_id"]] = nodeWidget
		self.viewportTop = None
		self.viewportHeight = VIEWPORT_HEIGHT

	def ApplyNodeStates(self, nodeStates, treeActive):
		presenters = {}
		for nodeId, nodeWidget in self.nodesById.items():
			rank, state = nodeStates[nodeId]
			presenters[nodeId] = {
				"node_id": nodeId,
				"rank": rank,
				"max_rank": nodeWidget.maxRank,
				"state": state,
			}
		return self.ApplyPresenters(presenters, treeActive)

	def ApplyPresenters(self, presenters, treeActive):
		if not isinstance(treeActive, bool):
			return False
		if not isinstance(presenters, dict) or set(presenters) != set(self.nodesById):
			return False
		validated = {}
		for nodeId in self.nodesById:
			presenter = presenters[nodeId]
			if not isinstance(presenter, dict):
				return False
			if presenter.get("node_id") != nodeId:
				return False
			rank = presenter.get("rank")
			state = presenter.get("state")
			maxRank = presenter.get("max_rank")
			if isinstance(rank, bool) or not isinstance(rank, _INTEGER_TYPES):
				return False
			if isinstance(maxRank, bool) or not isinstance(maxRank, _INTEGER_TYPES):
				return False
			if maxRank < 1 or maxRank > 5 or rank < 0 or rank > maxRank:
				return False
			if state not in PRESENTER_NODE_STATES:
				return False
			if rank == maxRank and state != "maxed":
				return False
			if 0 < rank < maxRank and state != "learned":
				return False
			if rank == 0 and state not in ("locked", "available"):
				return False
			validated[nodeId] = dict(presenter)

		activeBridgeChildren = set()
		for nodeId, nodeWidget in self.nodesById.items():
			presenter = validated[nodeId]
			rank = int(presenter["rank"])
			state = presenter["state"]
			learnedState = state in ("learned", "maxed")
			if not nodeWidget.SetPresenter(presenter, treeActive):
				return False
			for connector in self.connectorsByChildId.get(nodeId, ()):
				parentId = connector.skillTreeParentId
				parentLearned = parentId in validated and validated[parentId]["rank"] > 0
				showActiveEdge = bool(treeActive) and learnedState and rank > 0 and parentLearned
				connector.skillTreeActive = showActiveEdge
				if showActiveEdge and connector.skillTreeBridge:
					activeBridgeChildren.add(nodeId)
				self.__RefreshConnectorVisibility(connector)
		for childId, junction in self.junctionsByChildId.items():
			junction.skillTreeActive = childId in activeBridgeChildren
			self.__RefreshConnectorVisibility(junction)
		return True

	def SetLoadingState(self):
		for nodeWidget in self.nodesById.values():
			nodeWidget.SetLoadingState()
		for connector in self.connectors:
			connector.skillTreeActive = False
			connector.Hide()
		for junction in self.junctions:
			junction.skillTreeActive = False
			junction.Hide()

	def SetViewportRange(self, scrollOffset, viewportHeight):
		self.viewportTop = int(scrollOffset)
		self.viewportHeight = int(viewportHeight)
		for nodeWidget in self.nodesById.values():
			nodeY = nodeWidget.nodeData["y"] - nodeWidget.nodeSize // 2
			if self.__IntersectsViewport(nodeY, nodeWidget.nodeSize):
				nodeWidget.Show()
			else:
				nodeWidget.Hide()
		for connector in self.connectors:
			self.__RefreshConnectorVisibility(connector)
		for junction in self.junctions:
			self.__RefreshConnectorVisibility(junction)

	def __IntersectsViewport(self, elementY, elementHeight):
		if self.viewportTop is None:
			return True
		visibleTop = self.viewportTop - VIEWPORT_CULL_MARGIN
		visibleBottom = self.viewportTop + self.viewportHeight + VIEWPORT_CULL_MARGIN
		return elementY + elementHeight >= visibleTop and elementY <= visibleBottom

	def __RefreshConnectorVisibility(self, connector):
		if connector.skillTreeActive and self.__IntersectsViewport(
			connector.skillTreeY,
			connector.skillTreeHeight,
		):
			connector.Show()
		else:
			connector.Hide()

	def RefreshControls(self):
		for nodeWidget in self.nodesById.values():
			if nodeWidget.snapshotReady:
				nodeWidget.SetState(nodeWidget.rank, nodeWidget.state)
			else:
				nodeWidget.SetLoadingState()

	def __GetNodeSize(self, nodeData):
		if nodeData["milestone"]:
			return talent_tree_layout.MILESTONE_NODE_SIZE
		return talent_tree_layout.REGULAR_NODE_SIZE


class SkillTreeViewport(ui.Window):

	def __init__(self, owner):
		ui.Window.__init__(self)

		self.SetSize(VIEWPORT_WIDTH, VIEWPORT_HEIGHT)
		self.EnableScissorRect()
		self.AddFlag("dragable")

		self.scrollOffset = 0
		self.scrollCallback = None
		self.dragMouseY = None

		self.canvas = TalentTreeCanvas(owner)
		self.canvas.SetParent(self)
		self.canvas.SetPosition(0, 0)
		self.canvas.Show()
		self.SetScrollOffset(MAX_SCROLL_OFFSET)

	def SetScrollCallback(self, callback):
		self.scrollCallback = callback

	def SetScrollOffset(self, offset):
		offset = max(0, min(MAX_SCROLL_OFFSET, int(offset)))
		self.scrollOffset = offset
		self.canvas.SetPosition(0, -self.scrollOffset)
		self.canvas.SetViewportRange(self.scrollOffset, VIEWPORT_HEIGHT)
		if self.scrollCallback:
			self.scrollCallback(float(self.scrollOffset) / float(MAX_SCROLL_OFFSET))

	def OnMouseWheel(self, delta):
		if delta > 0:
			self.SetScrollOffset(self.scrollOffset - SCROLL_WHEEL_STEP)
		else:
			self.SetScrollOffset(self.scrollOffset + SCROLL_WHEEL_STEP)
		return True

	def BeginDrag(self):
		self.dragMouseY = self.GetMouseLocalPosition()[1]
		return True

	def ContinueDrag(self, _x, _y):
		if self.dragMouseY is None:
			return False
		currentMouseY = self.GetMouseLocalPosition()[1]
		delta = self.dragMouseY - currentMouseY
		self.dragMouseY = currentMouseY
		self.SetScrollOffset(self.scrollOffset + delta)
		return True

	def EndDrag(self):
		self.dragMouseY = None
		return True

	def OnMouseLeftButtonDown(self):
		return self.BeginDrag()

	def OnMouseDrag(self, x, y):
		return self.ContinueDrag(x, y)

	def OnMouseLeftButtonUp(self):
		return self.EndDrag()


# V5 fixed-canvas implementation. These definitions intentionally replace the archived
# scrolling classes above while leaving the renewal-cost tooltip independent.
class TalentPlusButton(ui.Button):

	def __init__(self, owner, nodeWidget):
		ui.Button.__init__(self)
		self.owner = owner
		self.nodeWidget = nodeWidget

	def OnMouseOverIn(self):
		if self.owner:
			self.owner.ShowNodeToolTip(self.nodeWidget)
		return True

	def OnMouseOverOut(self):
		if self.owner:
			self.owner.HideNodeToolTip()
		return True

	def Destroy(self):
		self.owner = None
		self.nodeWidget = None


class TalentNodeWidget(ui.Window):

	def __init__(self, owner, nodeData, presetPath, layoutModule):
		ui.Window.__init__(self)
		self.owner = owner
		self.nodeData = nodeData
		self.nodeSize = nodeData["size"]
		self.presetPath = presetPath
		self.layout = layoutModule
		self.rank = 0
		self.maxRank = 5
		self.state = "locked"
		self.presenter = None
		self.snapshotReady = False
		self.selected = False

		margin = layoutModule.OVERLAY_MARGIN
		widgetSize = self.nodeSize + margin * 2
		self.SetSize(widgetSize, widgetSize)
		self.AddFlag("dragable")
		self.SetPosition(
			nodeData["x"] - self.nodeSize // 2 - margin,
			nodeData["y"] - self.nodeSize // 2 - margin,
		)

		self.icon = self.__Image(
			margin, margin, layoutModule.NODE_ASSETS[nodeData["node_id"]]["muted"],
		)
		self.stateImage = self.__Image(margin, margin, "state_locked.tga")
		self.hoverImage = self.__Image(margin, margin, "state_hover.tga")
		self.hoverImage.Hide()
		self.selectedImage = self.__Image(margin, margin, "state_selected.tga")
		self.selectedImage.Hide()
		self.levelLock = ui.ImageBox()
		self.levelLock.SetParent(self)
		self.levelLock.SetPosition(
			margin + (self.nodeSize - 15) // 2,
			margin + (self.nodeSize - 20) // 2,
		)
		self.levelLock.LoadImage("d:/ymir work/ui/game/biolog/locked.png")
		self.levelLock.AddFlag("not_pick")
		self.levelLock.Hide()

		nodeCenter = margin + self.nodeSize // 2
		badgeWidth, badgeHeight = layoutModule.RANK_BADGE_SIZE
		rankPosition = (
			nodeCenter + nodeData["rank_offset"][0] - badgeWidth // 2,
			nodeCenter + nodeData["rank_offset"][1] - badgeHeight // 2,
		)
		plusSize = layoutModule.PLUS_HIT_SIZE
		plusPosition = (
			nodeCenter + nodeData["plus_offset"][0] - plusSize // 2,
			nodeCenter + nodeData["plus_offset"][1] - plusSize // 2,
		)
		self.rankBadge = self.__Image(
			rankPosition[0], rankPosition[1], "control_rank-badge.tga",
		)
		self.rankBadge.SetSize(badgeWidth, badgeHeight)
		self.rankBadge.Hide()
		self.rankDigit = self.__Image(
			rankPosition[0], rankPosition[1], "control_rank-digit-1.tga",
		)
		self.rankDigit.SetSize(badgeWidth, badgeHeight)
		self.rankDigit.Hide()
		self.rankBadge.SetTop()
		self.rankDigit.SetTop()

		self.plusButton = TalentPlusButton(owner, self)
		self.plusButton.SetParent(self)
		self.plusButton.SetPosition(*plusPosition)
		self.plusButton.SetSize(plusSize, plusSize)
		self.plusButton.SetUpVisual(presetPath + "control_plus-available.tga")
		self.plusButton.SetOverVisual(presetPath + "control_plus-hover.tga")
		self.plusButton.SetDownVisual(presetPath + "control_plus-pressed.tga")
		self.plusButton.SetDisableVisual(presetPath + "control_plus-available.tga")
		self.plusButton.SetEvent(ui.__mem_func__(self.__OnUpgrade))
		self.plusButton.Hide()
		self.plusButton.SetTop()
		self.RefreshControl()

	def __Image(self, x, y, filename):
		image = ui.ImageBox()
		image.SetParent(self)
		image.SetPosition(x, y)
		image.LoadImage(self.presetPath + filename)
		image.AddFlag("not_pick")
		image.Show()
		return image

	def SetLoadingState(self):
		self.presenter = None
		self.snapshotReady = False
		self.rank = 0
		self.maxRank = 5
		self.state = "locked"
		self.rankDigit.Hide()
		self.rankBadge.Hide()
		self.icon.LoadImage(
			self.presetPath + self.layout.NODE_ASSETS[self.nodeData["node_id"]]["muted"]
		)
		_SetImageDiffuseColor(self.icon, 0.52, 0.52, 0.52, 0.78)
		self.stateImage.LoadImage(self.presetPath + "state_locked.tga")
		self.levelLock.Hide()
		self.RefreshControl()

	def SetPresenter(self, presenter, treeActive):
		self.presenter = dict(presenter)
		self.snapshotReady = True
		self.rank = presenter["rank"]
		self.maxRank = presenter["max_rank"]
		self.state = presenter["state"]
		assets = self.layout.NODE_ASSETS[self.nodeData["node_id"]]
		if self.rank >= self.maxRank:
			visualState = "maxed"
			self.icon.LoadImage(self.presetPath + assets["color"])
			_SetImageDiffuseColor(self.icon, 1.0, 1.0, 1.0, 1.0)
		elif self.rank > 0:
			visualState = "learned"
			self.icon.LoadImage(self.presetPath + assets["color"])
			_SetImageDiffuseColor(self.icon, 1.0, 1.0, 1.0, 1.0)
		elif self.state == "available":
			visualState = "available"
			self.icon.LoadImage(self.presetPath + assets["muted"])
			_SetImageDiffuseColor(self.icon, 0.86, 0.86, 0.86, 0.92)
		else:
			visualState = "locked"
			self.icon.LoadImage(self.presetPath + assets["muted"])
			_SetImageDiffuseColor(self.icon, 0.52, 0.52, 0.52, 0.78)
		self.stateImage.LoadImage(self.presetPath + "state_%s.tga" % visualState)
		if self.rank > 0:
			self.rankDigit.LoadImage(
				self.presetPath + "control_rank-digit-%d.tga" % self.rank
			)
			self.rankBadge.Show()
			self.rankDigit.Show()
		else:
			self.rankBadge.Hide()
			self.rankDigit.Hide()
		self.rankBadge.SetTop()
		self.rankDigit.SetTop()
		self.plusButton.SetTop()
		self.RefreshControl()

	def SetSelected(self, selected):
		self.selected = bool(selected)
		if self.selected:
			self.selectedImage.Show()
		else:
			self.selectedImage.Hide()

	def RefreshControl(self):
		levelLocked = bool(
			self.snapshotReady and self.presenter and self.rank == 0
			and player.GetStatus(player.LEVEL) < self.presenter.get("required_level", 0)
		)
		if levelLocked:
			self.levelLock.Show()
			self.levelLock.SetTop()
		else:
			self.levelLock.Hide()
		canUpgrade = bool(
			self.snapshotReady
			and self.owner
			and not levelLocked
			and self.state in ("available", "learned")
			and self.rank < self.maxRank
			and self.owner.CanUpgradeNode(self.nodeData["node_id"])
		)
		if canUpgrade:
			self.plusButton.Enable()
			self.plusButton.Show()
		else:
			self.plusButton.Disable()
			self.plusButton.Hide()

	def __OnUpgrade(self):
		if self.owner:
			return self.owner.RequestNodeUpgrade(self.nodeData["node_id"])
		return False

	def OnMouseOverIn(self):
		self.hoverImage.Show()
		if self.owner:
			self.owner.ShowNodeToolTip(self)
		return True

	def OnMouseOverOut(self):
		self.hoverImage.Hide()
		if self.owner:
			self.owner.HideNodeToolTip()
		return True

	def OnMouseLeftButtonDown(self):
		if self.owner:
			return self.owner.BeginTreeDrag(self.nodeData["node_id"])
		return False

	def OnMouseDrag(self, x, y):
		if self.owner:
			return self.owner.DragTree(x, y)
		return False

	def OnMouseLeftButtonUp(self):
		if self.owner:
			return self.owner.EndTreeDrag()
		return False


class TalentTreeCanvas(ui.Window):

	def __init__(self, owner, layoutModule):
		ui.Window.__init__(self)
		self.owner = owner
		self.layout = layoutModule
		self.presetPath = V7_PRESET_PATH % layoutModule.PRESET
		self.nodesById = {}
		self.connectors = []
		self.connectorsByChildId = {}
		self.selectedNodeId = None
		self.lastPresenters = None
		self.treeActive = False
		self.animationSnapshots = {}
		self.SetSize(layoutModule.CANVAS_WIDTH, layoutModule.CANVAS_HEIGHT)
		self.AddFlag("dragable")

		self.backgrounds = []
		for record in layoutModule.BACKGROUND_ASSETS:
			background = ui.ImageBox()
			background.SetParent(self)
			background.SetPosition(record["offset"][0], record["offset"][1])
			background.LoadImage(self.presetPath + record["path"])
			background.AddFlag("not_pick")
			background.Show()
			self.backgrounds.append(background)

		for edgeData in layoutModule.EDGES:
			assetStates = layoutModule.EDGE_ASSETS[
				(edgeData["parent_id"], edgeData["child_id"])
			]
			images = {}
			for state in V7_EDGE_STATES:
				asset = assetStates[state]
				connector = ui.ImageBox()
				connector.SetParent(self)
				connector.SetPosition(asset["offset"][0], asset["offset"][1])
				connector.LoadImage(self.presetPath + asset["path"])
				connector.AddFlag("not_pick")
				connector.Hide()
				images[state] = connector
			spark = ui.ExpandedImageBox()
			spark.SetParent(self)
			spark.LoadImage(self.presetPath + "energy_spark.tga")
			spark.AddFlag("not_pick")
			spark.Hide()
			key = (edgeData["parent_id"], edgeData["child_id"])
			record = {
				"key": key,
				"images": images,
				"edge": edgeData,
				"spark": spark,
				"learned": False,
				"visible_state": "locked",
				"phase": ((key[0] * 31 + key[1] * 17) % 1000) / 1000.0,
			}
			self.connectors.append(record)
			self.connectorsByChildId.setdefault(edgeData["child_id"], []).append(record)

		for nodeData in layoutModule.NODES:
			nodeWidget = TalentNodeWidget(owner, nodeData, self.presetPath, layoutModule)
			nodeWidget.SetParent(self)
			nodeWidget.Show()
			self.nodesById[nodeData["node_id"]] = nodeWidget
		self.SetLoadingState()

	def ApplyPresenters(self, presenters, treeActive):
		if type(treeActive) is not bool or not isinstance(presenters, dict):
			return False
		if frozenset(presenters) != frozenset(V7_WIRE_NODE_IDS):
			return False
		for nodeId, presenter in presenters.items():
			rank = presenter.get("rank") if isinstance(presenter, dict) else None
			maxRank = presenter.get("max_rank") if isinstance(presenter, dict) else None
			if (
				not isinstance(presenter, dict)
				or presenter.get("node_id") != nodeId
				or presenter.get("state") not in ("locked", "available", "learned", "maxed")
				or isinstance(rank, bool)
				or not isinstance(rank, _INTEGER_TYPES)
				or isinstance(maxRank, bool)
				or not isinstance(maxRank, _INTEGER_TYPES)
				or rank < 0
				or rank > maxRank
				or (nodeId == 2000 and (maxRank != 1 or rank != 1))
				or (maxRank != skilltreecatalog.MAX_RANK_BY_ID[nodeId])
			):
				return False
		self.lastPresenters = dict((nodeId, dict(presenter)) for nodeId, presenter in presenters.items())
		self.treeActive = treeActive
		for nodeId in V7_VISIBLE_NODE_IDS:
			self.nodesById[nodeId].SetPresenter(presenters[nodeId], treeActive)
		self.__RefreshConnectors()
		self.RefreshControls()
		return True

	def ApplyNodeStates(self, nodeStates, treeActive):
		if not isinstance(nodeStates, dict):
			return False
		presenters = {}
		for nodeId in V7_WIRE_NODE_IDS:
			state = nodeStates.get(nodeId)
			if not isinstance(state, tuple) or len(state) != 2:
				return False
			presenters[nodeId] = {
				"node_id": nodeId, "rank": state[0],
				"max_rank": skilltreecatalog.MAX_RANK_BY_ID[nodeId],
				"state": state[1], "eligible": state[1] == "available",
			}
		return self.ApplyPresenters(presenters, treeActive)

	def SetLoadingState(self):
		self.lastPresenters = None
		self.treeActive = False
		for widget in self.nodesById.values():
			widget.SetLoadingState()
		for record in self.connectors:
			record["learned"] = False
			record["visible_state"] = "locked"
			record["spark"].Hide()
			self.__ShowConnectorState(record["images"], "locked")

	def SelectNode(self, nodeId):
		if nodeId not in self.nodesById:
			return False
		self.selectedNodeId = nodeId
		for currentId, widget in self.nodesById.items():
			widget.SetSelected(currentId == nodeId)
		self.__RefreshConnectors()
		return True

	def __ConnectorState(self, edgeData):
		parent = self.lastPresenters[edgeData["parent_id"]]
		child = self.lastPresenters[edgeData["child_id"]]
		if (
			child["rank"] > 0
			and parent["rank"] >= edgeData["required_parent_rank"]
		):
			return "active"
		if child["rank"] == 0 and child.get("eligible"):
			return "neutral"
		return "locked"

	def __SelectedAncestry(self):
		if self.selectedNodeId not in self.nodesById:
			return frozenset()
		selectedEdges = set()
		pending = [self.selectedNodeId]
		visited = set()
		while pending:
			childId = pending.pop()
			if childId in visited:
				continue
			visited.add(childId)
			for record in self.connectorsByChildId.get(childId, ()):
				edgeData = record["edge"]
				key = (edgeData["parent_id"], edgeData["child_id"])
				selectedEdges.add(key)
				pending.append(edgeData["parent_id"])
		return frozenset(selectedEdges)

	def __ShowConnectorState(self, images, visibleState):
		for state, image in images.items():
			if state == visibleState:
				image.Show()
			else:
				image.Hide()

	def __RefreshConnectors(self):
		if self.lastPresenters is None:
			return
		selectedEdges = self.__SelectedAncestry()
		for record in self.connectors:
			images = record["images"]
			edgeData = record["edge"]
			state = self.__ConnectorState(edgeData)
			key = (edgeData["parent_id"], edgeData["child_id"])
			record["learned"] = state == "active"
			if state == "active" and key in selectedEdges:
				state = "highlighted"
			record["visible_state"] = state
			self.__ShowConnectorState(images, state)

	def UpdateAnimation(self, now):
		try:
			now = float(now)
		except (TypeError, ValueError):
			return False
		selectedEdges = self.__SelectedAncestry()
		for record in self.connectors:
			key = record["key"]
			learned = bool(record["learned"])
			selected = key in selectedEdges
			visibleImage = record["images"][record["visible_state"]]
			if not learned:
				alpha = 1.0
				record["spark"].Hide()
				sparkPosition = None
			elif not self.treeActive:
				alpha = 0.82 if selected else 0.62
				record["spark"].Hide()
				sparkPosition = None
			else:
				base = 0.82 if selected else 0.72
				alpha = base + 0.18 * math.sin(
					now * 3.0 + record["phase"] * math.pi * 2.0,
				)
				sparkPosition = self.__PointAlongRoute(
					record["edge"]["points"],
					(now * 0.35 + record["phase"]) % 1.0,
				)
				record["spark"].SetPosition(
					int(round(sparkPosition[0] - 6)),
					int(round(sparkPosition[1] - 6)),
				)
				_SetImageDiffuseColor(record["spark"], 1.0, 1.0, 1.0, alpha)
				record["spark"].Show()
			_SetImageDiffuseColor(visibleImage, 1.0, 1.0, 1.0, alpha)
			self.animationSnapshots[key] = {
				"alpha": round(alpha, 6),
				"spark_visible": bool(learned and self.treeActive),
				"spark_position": sparkPosition,
			}
		return True

	def AnimationSnapshot(self, edgeKey):
		snapshot = self.animationSnapshots.get(tuple(edgeKey))
		return dict(snapshot) if snapshot is not None else None

	def __PointAlongRoute(self, points, progress):
		segments = []
		total = 0.0
		for start, end in zip(points, points[1:]):
			length = math.hypot(end[0] - start[0], end[1] - start[1])
			segments.append((start, end, length))
			total += length
		if total <= 0.0:
			return tuple(points[0])
		target = max(0.0, min(1.0, progress)) * total
		travelled = 0.0
		for start, end, length in segments:
			if target <= travelled + length or length <= 0.0:
				ratio = 0.0 if length <= 0.0 else (target - travelled) / length
				return (
					start[0] + (end[0] - start[0]) * ratio,
					start[1] + (end[1] - start[1]) * ratio,
				)
			travelled += length
		return tuple(points[-1])

	def RefreshControls(self):
		for widget in self.nodesById.values():
			widget.RefreshControl()

	def OnMouseLeftButtonDown(self):
		if self.owner:
			return self.owner.BeginTreeDrag()
		return False

	def OnMouseDrag(self, x, y):
		if self.owner:
			return self.owner.DragTree(x, y)
		return False

	def OnMouseLeftButtonUp(self):
		if self.owner:
			return self.owner.EndTreeDrag()
		return False


class SkillTreeViewport(ui.Window):

	def __init__(self, owner, layoutModule):
		ui.Window.__init__(self)
		self.owner = owner
		self.layout = layoutModule
		self.SetSize(layoutModule.VIEWPORT_RECT[2], layoutModule.VIEWPORT_RECT[3])
		self.EnableScissorRect()
		self.AddFlag("dragable")
		self.canvasOffset = tuple(layoutModule.INITIAL_CANVAS_OFFSET)
		self.dragStartMouse = None
		self.dragStartOffset = None
		self.pendingNodeId = None
		self.dragged = False
		self.canvas = TalentTreeCanvas(owner, layoutModule)
		self.canvas.SetParent(self)
		self.SetCanvasOffset(*self.canvasOffset)
		self.canvas.Show()

	def SetCanvasOffset(self, x, y):
		minX, maxX, minY, maxY = self.layout.CANVAS_OFFSET_BOUNDS
		x = max(minX, min(maxX, int(x)))
		y = max(minY, min(maxY, int(y)))
		self.canvasOffset = (x, y)
		self.canvas.SetPosition(x, y)
		return self.canvasOffset

	def BeginDrag(self, nodeId=None):
		self.SetFocus()
		self.dragStartMouse = wndMgr.GetMousePosition()
		self.dragStartOffset = self.canvasOffset
		self.pendingNodeId = nodeId
		self.dragged = False
		return True

	def ContinueDrag(self, unusedX, unusedY):
		if self.dragStartMouse is None:
			return False
		if not self.layout.DRAG_ENABLED:
			return True
		mouseX, mouseY = wndMgr.GetMousePosition()
		deltaX = mouseX - self.dragStartMouse[0]
		deltaY = mouseY - self.dragStartMouse[1]
		if not self.dragged:
			distance = (deltaX * deltaX + deltaY * deltaY) ** 0.5
			if distance <= self.layout.DRAG_THRESHOLD:
				return True
			self.dragged = True
			if self.owner:
				self.owner.HideNodeToolTip()
		self.SetCanvasOffset(self.dragStartOffset[0] + deltaX,
							 self.dragStartOffset[1] + deltaY)
		return True

	def EndDrag(self):
		nodeId = self.pendingNodeId
		shouldSelect = nodeId is not None and not self.dragged
		if shouldSelect:
			nodeWidget = self.canvas.nodesById.get(nodeId)
			shouldSelect = bool(nodeWidget and _IsMouseInsideWindowBounds(nodeWidget))
		self.dragStartMouse = None
		self.dragStartOffset = None
		self.pendingNodeId = None
		self.dragged = False
		self.KillFocus()
		if shouldSelect and self.owner:
			return bool(self.owner.ActivateNode(nodeId))
		return True

	def CancelDrag(self):
		self.dragStartMouse = None
		self.dragStartOffset = None
		self.pendingNodeId = None
		self.dragged = False
		self.KillFocus()
		return True

	def OnMouseLeftButtonDown(self):
		return self.BeginDrag()

	def OnMouseDrag(self, x, y):
		return self.ContinueDrag(x, y)

	def OnMouseLeftButtonUp(self):
		return self.EndDrag()


class RenewToolTipAnchor(ui.Window):

	def __init__(self, toolTip, clickHandler=None):
		ui.Window.__init__(self)
		self.toolTip = toolTip
		self.clickHandler = clickHandler if callable(clickHandler) else None
		self.SetSize(176, 21)

	def OnMouseOverIn(self):
		if self.toolTip:
			self.toolTip.Show()

	def OnMouseOverOut(self):
		if self.toolTip:
			self.toolTip.Hide()

	def OnMouseLeftButtonUp(self):
		if not self.clickHandler:
			return False
		return bool(self.clickHandler())

	def Destroy(self):
		self.Hide()
		self.toolTip = None
		self.clickHandler = None


def _TextWidth(line):
	try:
		return int(line.GetTextSize()[0])
	except Exception:
		return len(line.GetText()) * 7


def _MoneyText(amount):
	"""The yang amount with the game's thousand separators ("6.800.000"), the format of the R1 price."""
	try:
		import uir1price
		return uir1price.FormatAmount(amount)
	except Exception:
		return str(amount)


class RenewCostToolTip(uiToolTip.ToolTip):
	yangPrice = None	# class-level: the base class may hide the tooltip before __init__ made the price

	def __init__(self):
		uiToolTip.ToolTip.__init__(self, RENEW_TOOLTIP_WIDTH, isPickable=True)

		self.itemCosts = ()
		self.yangCost = 0
		self.costRows = ()
		self.startLine = 0
		self.rowWidgets = []
		self.anchorButton = None
		self._syncingScroll = False
		self._hideRequested = False

		self.toolTipHeight = RENEW_TOOLTIP_HEIGHT
		self.SetSize(RENEW_TOOLTIP_WIDTH, RENEW_TOOLTIP_HEIGHT)

		self.titleText = ui.TextLine()
		self.titleText.SetParent(self)
		self.titleText.SetPosition(RENEW_TOOLTIP_WIDTH // 2, RENEW_TOOLTIP_TITLE_Y)
		self.titleText.SetHorizontalAlignCenter()
		self.titleText.SetDefaultFontName()
		self.titleText.SetPackedFontColor(self.TITLE_COLOR)
		self.titleText.SetOutline()
		self.titleText.SetText(uiScriptLocale.SKILL_TREE_RENEW_COST)
		self.titleText.Show()

		for index in range(MAX_VISIBLE_RENEW_COST_ROWS):
			rowY = RENEW_TOOLTIP_ROWS_Y + index * RENEW_TOOLTIP_ROW_HEIGHT

			icon = ui.ImageBox()
			icon.SetParent(self)
			icon.SetPosition(12, rowY)
			icon.Hide()

			name = ui.TextLine()
			name.SetParent(self)
			name.SetPosition(50, rowY + 1)
			name.SetDefaultFontName()
			name.SetPackedFontColor(self.NORMAL_COLOR)
			name.SetOutline()
			name.Hide()

			count = ui.TextLine()
			count.SetParent(self)
			count.SetPosition(50, rowY + 18)
			count.SetDefaultFontName()
			count.SetPackedFontColor(self.NORMAL_COLOR)
			count.SetOutline()
			count.Hide()

			self.rowWidgets.append({
				"icon": icon,
				"name": name,
				"count": count,
			})

		self.scrollBar = ui.SmallThinScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(RENEW_TOOLTIP_WIDTH - 18, RENEW_TOOLTIP_ROWS_Y)
		self.scrollBar.SetScrollBarSize(MAX_VISIBLE_RENEW_COST_ROWS * RENEW_TOOLTIP_ROW_HEIGHT)
		self.scrollBar.SetScrollStep(1.0 / float(MAX_VISIBLE_RENEW_COST_ROWS))
		self.scrollBar.SetScrollEvent(ui.__mem_func__(self.__OnScroll))
		self.scrollBar.upButton.SetEvent(ui.__mem_func__(self.__OnScrollUp))
		self.scrollBar.downButton.SetEvent(ui.__mem_func__(self.__OnScrollDown))
		self.scrollBar.Hide()
		self.__CreateYangPrice()
		self.Hide()

	def __CreateYangPrice(self):
		"""R1 look: the yang row is the shared R1 price (root/uir1price.py: the coin, "6.800.000 Yang" in Tahoma 12, red
		when the player has less). "Starý vzhled" keeps the original "Yang: 6.800.000" line."""
		if getattr(self, "r1Frame", None) is None:
			return
		try:
			import uir1price
			self.yangPrice = uir1price.Price(self, 12, RENEW_TOOLTIP_ROWS_Y + RENEW_YANG_ROW_Y, "left")
		except Exception:
			self.yangPrice = None
			try:
				import uir1
				uir1.TraceFailure("the skill tree renewal price")
			except Exception:
				pass

	def SetAnchorButton(self, button):
		if button:
			self.anchorButton = weakref.proxy(button)
		else:
			self.anchorButton = None

	def SetRenewCosts(self, itemCosts, yangCost):
		validatedItems, validatedYang = self.__ValidateCosts(itemCosts, yangCost)
		self.__PreflightIconPaths(validatedItems)

		rows = []
		for vnum, requiredCount, ownedCount, displayName, iconPath in validatedItems:
			rows.append(("item", vnum, requiredCount, ownedCount, displayName, iconPath))
		if validatedYang > 0:
			rows.append(("yang", validatedYang))
		if not rows:
			rows.append(("empty",))

		self.itemCosts = validatedItems
		self.yangCost = validatedYang
		self.costRows = tuple(rows)
		self.startLine = 0
		maxStartLine = max(0, len(self.costRows) - MAX_VISIBLE_RENEW_COST_ROWS)
		if maxStartLine > 0:
			self.scrollBar.SetScrollStep(1.0 / float(maxStartLine))
		else:
			self.scrollBar.SetScrollStep(1.0)
		self._syncingScroll = True
		self.scrollBar.SetPos(0.0)
		self._syncingScroll = False
		self.__RefreshRows()

	def __PreflightIconPaths(self, itemCosts):
		preflight = ui.ImageBox()
		try:
			preflight.Hide()
			for unusedVnum, unusedRequired, unusedOwned, unusedName, iconPath in itemCosts:
				if iconPath:
					preflight.LoadImage(iconPath)
		finally:
			try:
				preflight.Hide()
			finally:
				if getattr(preflight, "hWnd", None):
					wndMgr.Destroy(preflight.hWnd)
					preflight.hWnd = None

	def __ValidateCosts(self, itemCosts, yangCost):
		if isinstance(yangCost, bool) or not isinstance(yangCost, _INTEGER_TYPES):
			raise TypeError("yangCost must be an integer")
		if yangCost < 0:
			raise ValueError("yangCost must not be negative")

		try:
			costIterator = iter(itemCosts)
		except TypeError:
			raise TypeError("itemCosts must be iterable")

		costRecords = []
		for index in range(MAX_RENEW_COST_ROWS + 1):
			try:
				record = next(costIterator)
			except StopIteration:
				break
			if index >= MAX_RENEW_COST_ROWS:
				raise ValueError("too many item cost records")
			costRecords.append(record)

		validatedItems = []
		for record in costRecords:
			if not isinstance(record, tuple) or len(record) != 5:
				raise TypeError("item cost records must be five-value tuples")

			vnum, requiredCount, ownedCount, displayName, iconPath = record
			for fieldName, value in (
				("vnum", vnum),
				("requiredCount", requiredCount),
				("ownedCount", ownedCount),
			):
				if isinstance(value, bool) or not isinstance(value, _INTEGER_TYPES):
					raise TypeError("%s must be an integer" % fieldName)
			if vnum <= 0:
				raise ValueError("vnum must be positive")
			if requiredCount < 0 or ownedCount < 0:
				raise ValueError("item counts must not be negative")
			if not isinstance(displayName, _STRING_TYPES) or not displayName:
				raise TypeError("displayName must be a non-empty string")
			if not isinstance(iconPath, _STRING_TYPES):
				raise TypeError("iconPath must be a string")

			validatedItems.append((vnum, requiredCount, ownedCount, displayName, iconPath))

		return tuple(validatedItems), int(yangCost)

	def __OnScroll(self):
		if self._syncingScroll:
			return
		maxStartLine = max(0, len(self.costRows) - MAX_VISIBLE_RENEW_COST_ROWS)
		self.startLine = max(0, min(
			maxStartLine,
			int(maxStartLine * self.scrollBar.GetPos() + 0.5),
		))
		self.__RefreshRows()

	def __OnScrollUp(self):
		self.__SetStartLine(self.startLine - 1)

	def __OnScrollDown(self):
		self.__SetStartLine(self.startLine + 1)

	def __SetStartLine(self, startLine):
		maxStartLine = max(0, len(self.costRows) - MAX_VISIBLE_RENEW_COST_ROWS)
		self.startLine = max(0, min(maxStartLine, int(startLine)))
		self._syncingScroll = True
		if maxStartLine > 0:
			self.scrollBar.SetPos(float(self.startLine) / float(maxStartLine))
		else:
			self.scrollBar.SetPos(0.0)
		self._syncingScroll = False
		self.__RefreshRows()

	def __RefreshRows(self):
		maxStartLine = max(0, len(self.costRows) - MAX_VISIBLE_RENEW_COST_ROWS)
		self.startLine = max(0, min(maxStartLine, int(self.startLine)))
		pageRows = self.costRows[
			self.startLine:self.startLine + MAX_VISIBLE_RENEW_COST_ROWS
		]

		if self.yangPrice is not None:
			self.yangPrice.Clear()
		contentWidth = 0
		contentBottom = RENEW_TOOLTIP_ROWS_Y
		for index, widgets in enumerate(self.rowWidgets):
			widgets["icon"].Hide()
			widgets["name"].Hide()
			widgets["count"].Hide()
			if index >= len(pageRows):
				continue

			row = pageRows[index]
			rowY = RENEW_TOOLTIP_ROWS_Y + index * RENEW_TOOLTIP_ROW_HEIGHT
			if row[0] == "item":
				unusedKind, vnum, requiredCount, unusedOwned, displayName, iconPath = row
				# counted now, not when the server sent the price: the inventory may have changed since
				ownedCount = ownedcount.Owned(vnum)
				if iconPath:
					widgets["icon"].LoadImage(iconPath)
					widgets["icon"].Show()
					widgets["name"].SetPosition(50, rowY + 1)
				else:
					widgets["name"].SetPosition(12, rowY + 1)
				widgets["name"].SetPackedFontColor(self.NORMAL_COLOR)
				widgets["name"].SetText(displayName)
				widgets["name"].Show()
				ownedcount.Paint(widgets["count"], ownedCount, requiredCount)	# "12 / 25" green / red
				widgets["count"].Show()
				nameX = widgets["name"].GetLocalPosition()[0]
				contentWidth = max(contentWidth, nameX + _TextWidth(widgets["name"]), 50 + _TextWidth(widgets["count"]))
				contentBottom = rowY + RENEW_ITEM_ROW_HEIGHT
			elif row[0] == "yang":
				if self.yangPrice is not None:
					import uir1price
					self.yangPrice.SetAnchor(12, rowY + RENEW_YANG_ROW_Y)
					self.yangPrice.SetPrice(row[1], uir1price.CanAfford(row[1]))
					contentWidth = max(contentWidth, 12 + self.yangPrice.GetWidth())
				else:
					widgets["name"].SetPosition(12, rowY + 9)
					widgets["name"].SetPackedFontColor(self.NORMAL_COLOR)
					widgets["name"].SetText(uiScriptLocale.SKILL_TREE_YANG_COST % _MoneyText(row[1]))
					widgets["name"].Show()
					contentWidth = max(contentWidth, 12 + _TextWidth(widgets["name"]))
				contentBottom = rowY + RENEW_YANG_ROW_Y + RENEW_YANG_ROW_HEIGHT
			else:
				widgets["name"].SetPosition(12, rowY + 9)
				widgets["name"].SetPackedFontColor(self.NORMAL_COLOR)
				widgets["name"].SetText(uiScriptLocale.SKILL_TREE_COST_UNAVAILABLE)
				widgets["name"].Show()
				contentWidth = max(contentWidth, 12 + _TextWidth(widgets["name"]))
				contentBottom = rowY + RENEW_YANG_ROW_Y + RENEW_YANG_ROW_HEIGHT

		if len(self.costRows) <= MAX_VISIBLE_RENEW_COST_ROWS:
			self.startLine = 0
			self.scrollBar.Hide()
		else:
			self.scrollBar.Show()
		self.__FitToContent(contentWidth, contentBottom)

	def __FitToContent(self, contentWidth, contentBottom):
		"""The panel as large as its rows (an item and the yang drew a 320 x 332 box): the widest row plus
		RENEW_TOOLTIP_PAD (the title fits too), RENEW_TOOLTIP_BOTTOM under the last row. A list that scrolls keeps the
		full size, so the panel does not jump while scrolling."""
		if len(self.costRows) > MAX_VISIBLE_RENEW_COST_ROWS:
			width, height = RENEW_TOOLTIP_WIDTH, RENEW_TOOLTIP_HEIGHT
		else:
			titleWidth = _TextWidth(self.titleText)
			width = max(RENEW_TOOLTIP_MIN_WIDTH, contentWidth + RENEW_TOOLTIP_PAD, titleWidth + 2 * RENEW_TOOLTIP_PAD)
			width = min(RENEW_TOOLTIP_WIDTH, width)
			height = contentBottom + RENEW_TOOLTIP_BOTTOM
		self.toolTipWidth = width
		self.toolTipHeight = height
		self.titleText.SetPosition(width // 2, RENEW_TOOLTIP_TITLE_Y)
		self.scrollBar.SetPosition(width - 18, RENEW_TOOLTIP_ROWS_Y)
		self.SetSize(width, height)

	def OnMouseWheel(self, delta):
		if delta > 0:
			self.__SetStartLine(self.startLine - 1)
		else:
			self.__SetStartLine(self.startLine + 1)
		return True

	def __UpdateAnchorPosition(self):
		anchorButton = self.anchorButton
		if anchorButton is not None:
			try:
				buttonX, buttonY = anchorButton.GetGlobalPosition()
			except ReferenceError:
				self.anchorButton = None
				return
			anchorX = buttonX + anchorButton.GetWidth() // 2
			parentWindow = self.GetParentProxy()
			if parentWindow and parentWindow.GetWidth() >= self.GetWidth() + 16:
				parentX, unusedParentY = parentWindow.GetGlobalPosition()
				toolTipLeft = anchorX - self.GetWidth() // 2
				toolTipLeft = max(parentX + 8, min(
					toolTipLeft,
					parentX + parentWindow.GetWidth() - self.GetWidth() - 8,
				))
				anchorX = toolTipLeft + self.GetWidth() // 2
			self.SetToolTipPosition(
				anchorX,
				buttonY,
			)

	def Show(self):
		self.__UpdateAnchorPosition()
		self._hideRequested = False
		if self.costRows:
			self.__RefreshRows()		# the owned counts as they are now
		uiToolTip.ToolTip.Show(self)

	def RefreshOwnedCounts(self):
		"""The rows' "owned / need" again (the inventory changed)."""
		if self.costRows and self.IsShow():
			self.__RefreshRows()

	def Hide(self):
		self._hideRequested = True

	def ForceHide(self):
		self._hideRequested = False
		uiToolTip.ToolTip.Hide(self)

	def OnMouseOverIn(self):
		self._hideRequested = False

	def OnMouseOverOut(self):
		self._hideRequested = True

	def OnUpdate(self):
		self.__UpdateAnchorPosition()
		uiToolTip.ToolTip.OnUpdate(self)
		if not self._hideRequested:
			return
		if _IsMouseInsideWindowBounds(self.anchorButton):
			return
		if _IsMouseInsideWindowBounds(self):
			return
		uiToolTip.ToolTip.Hide(self)

	def Destroy(self):
		self.ForceHide()
		self.anchorButton = None
		self.parentWindow = 0
		self.scrollBar = None
		self.titleText = None
		if self.yangPrice is not None:
			self.yangPrice.Destroy()
		self.yangPrice = None
		self.rowWidgets = []
		self.itemCosts = ()
		self.costRows = ()
		self.yangCost = 0


def _CostItemName(vnum):
	try:
		item.SelectItem(vnum)
		return item.GetItemName()
	except Exception:
		return uiScriptLocale.SKILL_TREE_NODE_UNKNOWN_ITEM % vnum


def _CostItemText(vnum, count):
	"""One item price of a node: "Name  12 / 25" with the count green / red (root/ownedcount.py)."""
	return "%s  %s" % (_CostItemName(vnum), ownedcount.Tagged(ownedcount.Owned(vnum), count))


class SkillTreeWindow(ui.ScriptWindow):

	def __init__(self, model=None):
		ui.ScriptWindow.__init__(self)

		self.layout = SelectSkillTreePreset(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
		self.board = None
		self.treeAnchor = None
		self.treeErrorText = None
		self.footerBoard = None
		self.viewport = None
		self.toolTip = None
		self.pointIcon = None
		self.pointBalanceText = None
		self.selectedNodeId = None
		self.activationStatus = None
		self.activationStatusAsset = None
		self.activationButton = None
		self.remainingTimeText = None
		self.renewButton = None
		self.dismantleButton = None
		self.dismantleWindow = None
		self.dismantleHandler = None
		self.renewHoverArea = None
		self.renewToolTip = None
		self.renewCostFingerprint = None
		self.activationEnabled = False
		self.activationRemainingSeconds = 0
		self.activationMaxSeconds = 1
		self.activationRevision = 0
		self.activationSnapshotReady = False
		self.activationMutationPending = False
		self.upgradeHandler = None
		self.upgradeDialog = None
		self.upgradeDialogNodeId = None
		self.upgradeDialogRevision = None
		self.upgradeDialogPending = False
		self.upgradeDialogMaxed = False
		self.activationHandler = None
		self.renewHandler = None
		self.openHandler = None
		self.model = model
		self.presentationReady = False
		self.presentationError = False
		self.lastCharacterLevel = None
		self.r1 = None
		self.r1Failed = False

		self.__LoadWindow()

	def __LoadWindow(self):
		loader = ui.PythonScriptLoader()
		loader.LoadScriptFile(self, "UIScript/skilltreewindow.py")

		self.board = self.GetChild("Board")
		self.treeAnchor = self.GetChild("TreeAnchor")
		self.treeErrorText = self.GetChild("TreeErrorText")
		self.footerBoard = self.GetChild("FooterBoard")
		self.activationStatus = self.GetChild("ActivationStatus")
		self.activationButton = self.GetChild("ActivationButton")
		self.remainingTimeText = self.GetChild("RemainingTimeText")
		self.renewButton = self.GetChild("RenewButton")
		self.dismantleButton = self.GetChild("DismantleButton")
		self.SetSize(self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT)
		self.board.SetSize(self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT)
		self.pointIcon = ui.ImageBox()
		self.pointIcon.SetParent(self.board.titleBar)
		self.pointIcon.SetPosition(self.layout.WINDOW_WIDTH - 122, 4)
		self.pointIcon.LoadImage(SKIN_PATH + "point_currency.tga")
		self.pointIcon.AddFlag("not_pick")
		self.pointIcon.Show()
		self.pointBalanceText = ui.TextLine()
		self.pointBalanceText.SetParent(self.board.titleBar)
		self.pointBalanceText.SetPosition(self.layout.WINDOW_WIDTH - 102, 4)
		self.pointBalanceText.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
		self.pointBalanceText.SetText(u"0")
		self.pointBalanceText.AddFlag("not_pick")
		self.pointBalanceText.Show()
		self.treeAnchor.SetPosition(self.layout.VIEWPORT_RECT[0],
								self.layout.VIEWPORT_RECT[1])
		self.treeAnchor.SetSize(self.layout.VIEWPORT_RECT[2],
							self.layout.VIEWPORT_RECT[3])
		self.footerBoard.SetPosition(self.layout.FOOTER_RECT[0],
								 self.layout.FOOTER_RECT[1])
		self.footerBoard.SetSize(self.layout.FOOTER_RECT[2],
							 self.layout.FOOTER_RECT[3])
		self.activationStatus.SetPosition(12, 11)
		self.activationButton.SetPosition(42, 12)
		self.remainingTimeText.SetPosition(self.layout.FOOTER_RECT[2] // 2, 15)
		self.remainingTimeText.SetHorizontalAlignCenter()
		self.renewButton.SetPosition(self.layout.FOOTER_RECT[2] - 188, 12)
		self.dismantleButton.SetPosition(self.layout.FOOTER_RECT[2] - 290, 12)
		uicrimsoncontrols.ApplyVisuals(self.activationButton, "100x21")
		uicrimsoncontrols.ApplyVisuals(self.renewButton, "176x21")
		uicrimsoncontrols.ApplyVisuals(self.dismantleButton, "88x21")
		regularFont = fontconfig.FontForRole(fontconfig.ROLE_BODY)
		for button in (self.activationButton, self.renewButton, self.dismantleButton):
			text = button.GetText()
			button.SetFontName(regularFont)
			button.SetText("")
			button.SetText(text)
			# The script created these labels before the final 100/176px visuals.
			# SetText reuses ButtonText and does not update its original anchor.
			button.ButtonText.SetHorizontalAlignCenter()
			button.ButtonText.SetVerticalAlignCenter()
			button.ButtonText.SetPosition(button.GetWidth() // 2, button.GetHeight() // 2)
		self.renewButton.SetText(uiScriptLocale.SKILL_TREE_RENEW_EIGHT_HOURS)
		self.dismantleButton.SetText(skilltreelocale.GetDismantleText("open", _ClientLocaleKey()))

		self.board.SetCloseEvent(ui.__mem_func__(self.Close))
		self.activationButton.SetEvent(ui.__mem_func__(self.__OnActivationButton))
		self.renewButton.SetEvent(ui.__mem_func__(self.__OnRenewButton))
		self.dismantleButton.SetEvent(ui.__mem_func__(self.__OpenDismantle))

		try:
			ValidateSkillTreeV7Layout(self.layout)
			PreflightSkillTreeV7Assets(self.layout)
			self.viewport = SkillTreeViewport(self, self.layout)
			self.viewport.SetParent(self.treeAnchor)
			self.viewport.SetPosition(0, 0)
			self.viewport.Show()
			titleBar = getattr(self.board, "titleBar", None)
			if titleBar:
				titleBar.SetTop()
			self.treeErrorText.Hide()
			self.presentationReady = True
		except Exception as error:
			self.viewport = None
			self.presentationReady = False
			self.presentationError = True
			dbg.TraceError(
				"SkillTreeWindow: presentation initialization failed: %s" % error,
			)
			self.treeErrorText.SetText(uiScriptLocale.SKILL_TREE_LOCALIZATION_ERROR)
			self.treeErrorText.Show()

		self.toolTip = uiToolTip.ToolTip()
		try:
			self.renewToolTip = RenewCostToolTip()
			self.renewToolTip.SetAnchorButton(self.renewButton)
			self.renewButton.SetToolTipWindow(self.renewToolTip)
			# A pickable tooltip cannot remain a child of the small disabled button:
			# the native picker clips child hit-testing to the parent's bounds.
			self.renewToolTip.SetParentProxy(self)
			self.renewHoverArea = RenewToolTipAnchor(
				self.renewToolTip,
				ui.__mem_func__(self.__OnRenewButton),
			)
			self.renewHoverArea.SetParent(self.renewButton)
			self.renewHoverArea.SetPosition(0, 0)
			self.SetRenewCosts((), 0)
			self.SetActivationLoadingState()
		except:
			self.__CleanupRenewToolTip()
			raise

	def __CleanupRenewToolTip(self):
		if self.renewButton:
			self.renewButton.ToolTipText = None
		if self.renewHoverArea:
			self.renewHoverArea.Destroy()
		if self.renewToolTip:
			self.renewToolTip.Destroy()
		self.renewHoverArea = None
		self.renewToolTip = None

	def __LoadActivationStatusImage(self, asset):
		if self.activationStatusAsset == asset:
			return True
		path = SKIN_PATH + "activation/" + asset
		try:
			self.activationStatus.LoadImage(path)
			self.activationStatus.Show()
			self.activationStatusAsset = asset
			return True
		except Exception:
			self.activationStatus.Hide()
			dbg.TraceError(
				"SkillTreeWindow: optional activation status image unavailable: %s" % path,
			)
			return False

	def __RefreshActivationStatus(self, now):
		if not self.activationStatus:
			return
		asset = STATUS_ON_ASSET if self.activationEnabled else STATUS_OFF_ASSET
		if self.activationEnabled and self.activationSnapshotReady and not self.activationMutationPending:
			frame = int(now / ACTIVATION_FRAME_SECONDS) % ACTIVATION_FRAME_COUNT
			asset = "status_on_%02d.png" % frame
		self.__LoadActivationStatusImage(asset)

	def SetActivationState(self, enabled, remainingSeconds, maxSeconds, revision):
		maxSeconds = max(1, int(maxSeconds))
		remainingSeconds = max(0, min(int(remainingSeconds), maxSeconds))
		revision = max(0, int(revision))
		enabled = bool(enabled) and remainingSeconds > 0

		self.activationEnabled = enabled
		self.activationRemainingSeconds = remainingSeconds
		self.activationMaxSeconds = maxSeconds
		self.activationRevision = revision
		self.activationSnapshotReady = True
		self.activationMutationPending = False
		_SetImageDiffuseColor(self.activationStatus, 1.0, 1.0, 1.0, 1.0)

		if enabled:
			self.activationButton.SetText(uiScriptLocale.SKILL_TREE_DISABLE)
		else:
			self.activationButton.SetText(uiScriptLocale.SKILL_TREE_ENABLE)
		self.__RefreshActivationStatus(app.GetTime())
		self.remainingTimeText.SetText(self.__FormatRemainingTime(remainingSeconds))
		self.__RefreshActivationButtons()
		renewHoverArea = getattr(self, "renewHoverArea", None)
		if renewHoverArea:
			renewHoverArea.Show()

	def SetActivationLoadingState(self):
		self.activationEnabled = False
		self.activationRemainingSeconds = 0
		self.activationMaxSeconds = 1
		self.activationRevision = 0
		self.activationSnapshotReady = False
		self.activationMutationPending = False
		self.__LoadActivationStatusImage(STATUS_OFF_ASSET)
		self.activationButton.SetText(uiScriptLocale.SKILL_TREE_ENABLE)
		self.remainingTimeText.SetText(u"-")
		self.activationButton.Disable()
		self.renewButton.Disable()
		if self.renewHoverArea:
			self.renewHoverArea.Hide()
		if self.renewToolTip:
			self.renewToolTip.ForceHide()

	def SetActivationPending(self, pending):
		self.activationMutationPending = bool(pending)
		self.remainingTimeText.SetText(self.__FormatRemainingTime(self.activationRemainingSeconds))
		self.__RefreshActivationStatus(app.GetTime())
		self.__RefreshActivationButtons()

	def __RefreshActivationButtons(self):
		canActivate = bool(
			self.activationSnapshotReady
			and not getattr(self, "activationMutationPending", False)
			and getattr(self, "activationHandler", None)
			and self.activationRemainingSeconds > 0
		)
		canRenew = bool(
			self.activationSnapshotReady
			and not getattr(self, "activationMutationPending", False)
			and getattr(self, "renewHandler", None)
			and self.activationRemainingSeconds <= self.activationMaxSeconds - RENEW_SECONDS
		)
		if canActivate:
			self.activationButton.Enable()
		else:
			self.activationButton.Disable()
		renewButton = getattr(self, "renewButton", None)
		if renewButton:
			if canRenew:
				renewButton.Enable()
			else:
				renewButton.Disable()

	def SetInteractionHandlers(self, upgradeHandler, activationHandler, renewHandler):
		self.upgradeHandler = upgradeHandler if callable(upgradeHandler) else None
		self.activationHandler = activationHandler if callable(activationHandler) else None
		self.renewHandler = renewHandler if callable(renewHandler) else None
		if self.viewport:
			self.viewport.canvas.RefreshControls()
		if self.activationSnapshotReady:
			self.SetActivationState(
				self.activationEnabled,
				self.activationRemainingSeconds,
				self.activationMaxSeconds,
				self.activationRevision,
			)
		else:
			self.SetActivationLoadingState()

	def SetOpenHandler(self, openHandler):
		self.openHandler = openHandler if callable(openHandler) else None

	def SetDismantleHandler(self, handler):
		self.dismantleHandler = handler if callable(handler) else None

	def GetPointSources(self):
		return self.model.GetPointSources() if self.model else {}

	def GetPointSourceOrder(self):
		return self.model.GetPointSourceOrder() if self.model else ()

	def GetDismantlePointBudget(self):
		if not self.model:
			return None
		balance = self.model.GetPointBalance()
		if balance is None:
			return None
		return balance, self.model.pointCap

	def CanDismantle(self, points):
		budget = self.GetDismantlePointBudget()
		return bool(self.model and self.model.CanBeginDismantle()
			and self.dismantleHandler
			and budget is not None and 0 < points <= budget[1] - budget[0])

	def RequestDismantle(self, slots):
		return bool(self.dismantleHandler and self.dismantleHandler(slots))

	def OnDismantleResult(self, success):
		if self.dismantleWindow:
			self.dismantleWindow.OnResult(success)

	def __OpenDismantle(self):
		if not self.model or not self.model.IsReady():
			return False
		if self.dismantleWindow is None:
			self.dismantleWindow = uiskilltreedismantle.SkillTreeDismantleWindow(self)
		self.dismantleWindow.Open()
		return True

	def SetModel(self, model):
		if model is None:
			return False
		if not callable(getattr(model, "IsReady", None)):
			return False
		if not callable(getattr(model, "GetNodePresenters", None)):
			return False
		if not callable(getattr(model, "CanUpgrade", None)):
			return False
		if not callable(getattr(model, "IsLocalizationReady", None)):
			return False
		self.model = model
		return True

	def ApplyModel(self, treeActive=False):
		if (
			not self.presentationReady
			or not self.viewport
			or not self.model
			or not self.model.IsReady()
		):
			if self.viewport:
				self.viewport.canvas.SetLoadingState()
			return False
		presenters = self.model.GetNodePresenters()
		if not self.viewport.canvas.ApplyPresenters(presenters, bool(treeActive)):
			self.viewport.canvas.SetLoadingState()
			return False
		if self.selectedNodeId not in self.viewport.canvas.nodesById:
			self.selectedNodeId = skilltreecatalog.FIRST_NODE_ID
		self.viewport.canvas.SelectNode(self.selectedNodeId)
		self.pointBalanceText.SetText(skilltreelocale.FormatPointAmount(
			self.model.GetPointBalance(),
		))
		if self.dismantleWindow and self.dismantleWindow.IsShow():
			self.dismantleWindow.Refresh()
		self.__RefreshUpgradeDialog()
		return True

	def SelectNode(self, nodeId):
		if (
			not self.presentationReady
			or not self.viewport
			or nodeId not in self.viewport.canvas.nodesById
		):
			return False
		self.selectedNodeId = nodeId
		self.viewport.canvas.SelectNode(nodeId)
		return True

	def ActivateNode(self, nodeId):
		if not self.SelectNode(nodeId):
			return False
		if self.CanUpgradeNode(nodeId):
			return self.RequestNodeUpgrade(nodeId)
		return True

	def CanUpgradeNode(self, nodeId):
		model = getattr(self, "model", None)
		if (
			not self.presentationReady
			or self.upgradeHandler is None
			or not self.viewport
			or not model
		):
			return False
		return bool(
			nodeId in self.viewport.canvas.nodesById
			and model.CanUpgrade(nodeId)
		)

	def __CanAffordNextCost(self, nodeId):
		cost = self.model.GetNextCost(nodeId)
		if not isinstance(cost, dict):
			return False
		balance = self.model.GetPointBalance()
		if balance is None or balance < cost.get("points", 0):
			return False
		try:
			if player.GetElk() < cost.get("yang", 0):
				return False
		except Exception:
			return False
		for row in cost.get("items", ()):
			try:
				if not ownedcount.IsEnough(ownedcount.Owned(row["vnum"]), row["count"]):
					return False
			except Exception:
				return False
		return True

	def RequestNodeUpgrade(self, nodeId, keepPosition=None):
		if not self.CanUpgradeNode(nodeId):
			return False
		presenter = self.model.GetNodePresenters().get(nodeId)
		cost = self.model.GetNextCost(nodeId)
		texts = skilltreelocale.GetNodeText(_ClientLocaleKey(), nodeId)
		if not presenter or not cost or not texts:
			return False
		current = skilltreelocale.FormatNodeValue(nodeId, presenter["current_total"])
		nextValue = skilltreelocale.FormatNodeValue(nodeId, presenter["next_total"])
		if current is None or nextValue is None:
			return False
		self.__CloseUpgradeDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(u"%s: %s -> %s" % (texts[0], current, nextValue))
		dialog.SetText2(skilltreelocale.GetPointCostText(
			_ClientLocaleKey(), cost["points"],
		))
		dialog.textLine2.SetPackedFontColor(0xffe6bd78)
		yangLine = ui.TextLine()
		yangLine.SetParent(dialog.board)
		yangLine.AddFlag("not_pick")
		yangLine.SetWindowHorizontalAlignCenter()
		yangLine.SetHorizontalAlignCenter()
		yangLine.SetVerticalAlignCenter()
		yangLine.SetPosition(0, 72)
		yangLine.SetText(skilltreelocale.GetYangCostText(
			_ClientLocaleKey(), cost.get("yang", 0),
		))
		try:
			hasYang = player.GetElk() >= cost.get("yang", 0)
		except Exception:
			hasYang = False
		yangLine.SetPackedFontColor(0xffe6bd78 if hasYang else 0xffef7070)
		yangLine.Show()
		dialog.yangLine = yangLine
		# the item price under the yang line, one row each: "Name  12 / 25" with the count green / red (it was not
		# listed at all; root/ownedcount.py)
		itemLines = []
		rowHeight = 20		# px per item price row
		for index, itemCost in enumerate(cost.get("items", ())):
			itemLine = ui.TextLine()
			itemLine.SetParent(dialog.board)
			itemLine.AddFlag("not_pick")
			itemLine.SetWindowHorizontalAlignCenter()
			itemLine.SetHorizontalAlignCenter()
			itemLine.SetVerticalAlignCenter()
			itemLine.SetPosition(0, 72 + rowHeight * (index + 1))
			itemLine.SetPackedFontColor(0xffe6bd78)
			itemLine.SetText(_CostItemText(itemCost["vnum"], itemCost["count"]))
			itemLine.Show()
			itemLines.append(itemLine)
		dialog.itemLines = itemLines
		extraHeight = rowHeight * len(itemLines)
		pointWidth = dialog.textLine2.GetTextSize()[0]
		width = max(340, dialog.textLine1.GetTextSize()[0] + 40,
			pointWidth + 59, yangLine.GetTextSize()[0] + 40,
			max([line.GetTextSize()[0] for line in itemLines] or [0]) + 40)
		dialog.SetSize(width, 132 + extraHeight)
		dialog.SetWidth(width)
		dialog.acceptButton.SetPosition(-40, 94 + extraHeight)
		dialog.cancelButton.SetPosition(40, 94 + extraHeight)
		acceptText, cancelText = skilltreelocale.GetUpgradeActionText(_ClientLocaleKey())
		dialog.SetAcceptText(acceptText)
		dialog.SetCancelText(cancelText)
		uicrimsoncontrols.ApplyVisuals(dialog.acceptButton, "61x21")
		uicrimsoncontrols.ApplyVisuals(dialog.cancelButton, "61x21")
		if not self.__CanAffordNextCost(nodeId):
			dialog.acceptButton.Disable()
		pointIcon = ui.ImageBox()
		pointIcon.SetParent(dialog.board)
		pointIcon.LoadImage(SKIN_PATH + "point_currency.tga")
		pointIcon.SetPosition((width - pointWidth - pointIcon.GetWidth() - 5) // 2, 43)
		dialog.textLine2.SetPosition((pointIcon.GetWidth() + 5) // 2, 50)
		pointIcon.AddFlag("not_pick")
		pointIcon.Show()
		dialog.pointIcon = pointIcon
		dialog.yangPrice = None
		if getattr(dialog, "r1skin", None) is not None:
			# R1 look (the dialog dressed by uir1dialog): the yang line is the shared R1 price (root/uir1price.py:
			# the coin, "1.000.000 Yang" in Tahoma 12, red when the player has less) centred where the line was
			try:
				import uir1price
				price = uir1price.Price(dialog.board, width // 2, 72 - uir1price.ICON_H // 2, "center")
				price.SetPrice(cost.get("yang", 0), hasYang)
				yangLine.Hide()
				dialog.yangPrice = price
			except Exception:
				yangLine.Show()
				try:
					import uir1
					uir1.TraceFailure("the skill tree upgrade price")
				except Exception:
					pass
		dialog.SetAcceptEvent(ui.__mem_func__(self.__ConfirmNodeUpgrade))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseUpgradeDialog))
		self.upgradeDialog = dialog
		self.upgradeDialogNodeId = nodeId
		self.upgradeDialogRevision = self.model.progressRevision
		self.upgradeDialogPending = False
		self.upgradeDialogMaxed = False
		dialog.Open()
		if keepPosition:
			# The refreshed dialog opens where the previous one stood (same centre, same top)
			try:
				dialog.SetPosition(keepPosition[0] - dialog.GetWidth() // 2, keepPosition[1])
			except Exception:
				pass
		return True

	def __UpgradeDialogPosition(self):
		"""Where the open dialog stands (its centre x and top y), so the refreshed one opens on the same spot."""
		dialog = self.upgradeDialog
		try:
			x, y = dialog.GetGlobalPosition()
			return x + dialog.GetWidth() // 2, y
		except Exception:
			return None

	def __OpenMaxedDialog(self, nodeId, keepPosition=None):
		"""The node reached its highest rank while its upgrade dialog was open. The dialog stays open
		with "Max" (the value it now gives, no price, Vylepšit off) until the player closes it (X, Esc, the close button)."""
		presenter = self.model.GetNodePresenters().get(nodeId) if self.model else None
		texts = skilltreelocale.GetNodeText(_ClientLocaleKey(), nodeId)
		if not presenter or not texts:
			return False
		current = skilltreelocale.FormatNodeValue(nodeId, presenter["current_total"])
		if current is None:
			return False
		self.__CloseUpgradeDialog()
		dialog = uiCommon.QuestionDialog2()
		dialog.SetText1(u"%s: %s" % (texts[0], current))
		dialog.SetText2(skilltreelocale.GetMaxRankText(
			_ClientLocaleKey(), presenter["rank"], presenter["max_rank"],
		))
		dialog.textLine2.SetPackedFontColor(0xff75d98c)
		width = max(340, dialog.textLine1.GetTextSize()[0] + 40, dialog.textLine2.GetTextSize()[0] + 40)
		dialog.SetSize(width, 132)
		dialog.SetWidth(width)
		dialog.acceptButton.SetPosition(-40, 94)
		dialog.cancelButton.SetPosition(40, 94)
		acceptText, unusedCancelText = skilltreelocale.GetUpgradeActionText(_ClientLocaleKey())
		dialog.SetAcceptText(acceptText)
		dialog.SetCancelText(skilltreelocale.GetCloseText(_ClientLocaleKey()))
		uicrimsoncontrols.ApplyVisuals(dialog.acceptButton, "61x21")
		uicrimsoncontrols.ApplyVisuals(dialog.cancelButton, "61x21")
		dialog.acceptButton.Disable()
		dialog.yangLine = None
		dialog.pointIcon = None
		dialog.yangPrice = None
		dialog.SetAcceptEvent(ui.__mem_func__(self.__CloseUpgradeDialog))
		dialog.SetCancelEvent(ui.__mem_func__(self.__CloseUpgradeDialog))
		self.upgradeDialog = dialog
		self.upgradeDialogNodeId = nodeId
		self.upgradeDialogRevision = self.model.progressRevision
		self.upgradeDialogPending = False
		self.upgradeDialogMaxed = True
		dialog.Open()
		if keepPosition:
			# The refreshed dialog opens where the previous one stood (same centre, same top)
			try:
				dialog.SetPosition(keepPosition[0] - dialog.GetWidth() // 2, keepPosition[1])
			except Exception:
				pass
		return True

	def RefreshOwnedCounts(self):
		"""The item prices' "owned / need" of the renew tooltip and the open upgrade dialog again (the interface
		calls it when the inventory changes)."""
		if self.renewToolTip:
			self.renewToolTip.RefreshOwnedCounts()
		dialog = self.upgradeDialog
		if dialog and self.upgradeDialogNodeId is not None and getattr(dialog, "itemLines", None):
			cost = self.model.GetNextCost(self.upgradeDialogNodeId) if self.model else None
			items = cost.get("items", ()) if isinstance(cost, dict) else ()
			for line, itemCost in zip(dialog.itemLines, items):
				line.SetText(_CostItemText(itemCost["vnum"], itemCost["count"]))
			if not self.upgradeDialogPending and not self.upgradeDialogMaxed and self.__CanAffordNextCost(self.upgradeDialogNodeId):
				dialog.acceptButton.Enable()
			else:
				dialog.acceptButton.Disable()

	def __ConfirmNodeUpgrade(self):
		nodeId = self.upgradeDialogNodeId
		revision = self.upgradeDialogRevision
		if (
			nodeId is not None
			and not self.upgradeDialogPending
			and not self.upgradeDialogMaxed
			and self.model
			and self.model.progressRevision == revision
			and self.CanUpgradeNode(nodeId)
			and self.__CanAffordNextCost(nodeId)
		):
			# The dialog stays open while the server answers; the next model refresh reopens it on the
			# same spot with the new rank and price (or "Max"), so the player can click Vylepšit again.
			if self.upgradeHandler(nodeId) is False:
				self.__CloseUpgradeDialog()
				return False
			self.upgradeDialogPending = True
			if self.upgradeDialog:
				self.upgradeDialog.acceptButton.Disable()
			return True
		self.__CloseUpgradeDialog()
		return False

	def __RefreshUpgradeDialog(self):
		"""After the server answered a confirmed upgrade: the same dialog again with the new rank and price, the
		"Max" dialog when the node is full, nothing while the answer is still pending."""
		dialog = self.upgradeDialog
		nodeId = self.upgradeDialogNodeId
		if not dialog or nodeId is None or not self.upgradeDialogPending or not self.model:
			return False
		presenter = self.model.GetNodePresenters().get(nodeId)
		position = self.__UpgradeDialogPosition()
		if presenter and presenter.get("state") == "maxed":
			return self.__OpenMaxedDialog(nodeId, position)
		if self.CanUpgradeNode(nodeId):
			if not self.RequestNodeUpgrade(nodeId, position):
				self.__CloseUpgradeDialog()
				return False
			return True
		return False

	def __CloseUpgradeDialog(self):
		if self.upgradeDialog:
			self.upgradeDialog.Close()
		self.upgradeDialog = None
		self.upgradeDialogNodeId = None
		self.upgradeDialogRevision = None
		self.upgradeDialogPending = False
		self.upgradeDialogMaxed = False

	def BeginTreeDrag(self, nodeId=None):
		if not self.viewport:
			return False
		return self.viewport.BeginDrag(nodeId)

	def DragTree(self, x, y):
		if not self.viewport:
			return False
		return self.viewport.ContinueDrag(x, y)

	def EndTreeDrag(self):
		if not self.viewport:
			return False
		return self.viewport.EndDrag()

	def __OnActivationButton(self):
		if (
			not self.activationSnapshotReady
			or self.activationMutationPending
			or not self.activationHandler
		):
			return False
		if self.activationRemainingSeconds <= 0:
			return False
		self.activationHandler(not self.activationEnabled, self.activationRevision)
		return True

	def __OnRenewButton(self):
		if (
			not self.activationSnapshotReady
			or self.activationMutationPending
			or not self.renewHandler
			or self.activationRemainingSeconds > self.activationMaxSeconds - RENEW_SECONDS
		):
			return False
		self.renewHandler(self.activationRevision)
		return True

	def __FormatRemainingTime(self, remainingSeconds):
		remainingSeconds = max(0, int(remainingSeconds))
		hours = remainingSeconds // 3600
		minutes = (remainingSeconds % 3600) // 60
		seconds = remainingSeconds % 60
		return uiScriptLocale.SKILL_TREE_TIME_REMAINING % (hours, minutes, seconds)

	def SetRenewCosts(self, itemCosts, yangCost):
		self.renewToolTip.SetRenewCosts(itemCosts, yangCost)

	def SetRenewCostPayload(self, renewCost):
		if not isinstance(renewCost, dict) or frozenset(renewCost) != frozenset(("yang", "items")):
			raise TypeError("renewCost must contain exact yang and items fields")
		yangCost = renewCost["yang"]
		items = renewCost["items"]
		if isinstance(yangCost, bool) or not isinstance(yangCost, _INTEGER_TYPES) or yangCost < 0:
			raise ValueError("renew Yang must be a non-negative integer")
		if not isinstance(items, (list, tuple)) or len(items) > MAX_RENEW_COST_ROWS:
			raise ValueError("renew items must contain at most 64 records")

		validatedItems = []
		seen = set()
		for itemCost in items:
			if not isinstance(itemCost, dict) or frozenset(itemCost) != frozenset(("vnum", "count")):
				raise TypeError("renew item must contain exact vnum and count fields")
			vnum = itemCost["vnum"]
			requiredCount = itemCost["count"]
			if (
				isinstance(vnum, bool) or not isinstance(vnum, _INTEGER_TYPES) or vnum <= 0
				or isinstance(requiredCount, bool)
				or not isinstance(requiredCount, _INTEGER_TYPES) or requiredCount <= 0
				or vnum in seen
			):
				raise ValueError("renew item has invalid or duplicate fields")
			seen.add(vnum)
			validatedItems.append((vnum, requiredCount))

		fingerprint = (yangCost, tuple(validatedItems))
		if fingerprint == self.renewCostFingerprint:
			return True

		records = []
		for vnum, requiredCount in validatedItems:
			try:
				ownedCount = ownedcount.Owned(vnum)
			except Exception:
				ownedCount = 0
			try:
				item.SelectItem(vnum)
				displayName = item.GetItemName()
			except Exception:
				displayName = uiScriptLocale.SKILL_TREE_NODE_UNKNOWN_ITEM % vnum
			try:
				iconPath = item.GetIconImageFileName()
			except Exception:
				iconPath = ""
			records.append((vnum, requiredCount, ownedCount, displayName, iconPath))
		self.SetRenewCosts(tuple(records), yangCost)
		self.renewCostFingerprint = fingerprint
		return True

	def __OnScrollBar(self):
		if self.syncingScroll:
			return
		self.syncingScroll = True
		self.viewport.SetScrollOffset(int(self.scrollBar.GetPos() * MAX_SCROLL_OFFSET))
		self.syncingScroll = False

	def __OnViewportScroll(self, normalizedPosition):
		if self.syncingScroll:
			return
		self.syncingScroll = True
		self.scrollBar.SetPos(normalizedPosition)
		self.syncingScroll = False

	def ShowNodeToolTip(self, nodeWidget):
		if not self.toolTip:
			return
		self.toolTip.ClearToolTip()
		presenter = getattr(nodeWidget, "presenter", None)
		if not nodeWidget.snapshotReady or not isinstance(presenter, dict):
			self.toolTip.AppendTextLine(uiScriptLocale.SKILL_TREE_NODE_LOADING)
			self.toolTip.ResizeToolTip()
			self.toolTip.ShowToolTip()
			return

		texts = skilltreelocale.GetNodeText(_ClientLocaleKey(), presenter["node_id"])
		if texts is None:
			self.toolTip.AppendTextLine(self.model.GetLocalizationError(_ClientLocaleKey()))
			self.toolTip.ResizeToolTip()
			self.toolTip.ShowToolTip()
			return
		rank = presenter["rank"]
		maxRank = presenter["max_rank"]
		self.toolTip.SetThinBoardSize(max(190, min(330, 24 + len(texts[0]) * 7)))
		self.toolTip.AppendTextLine(texts[0], self.toolTip.TITLE_COLOR)
		self.toolTip.AppendTextLine(u"%d / %d" % (rank, maxRank), self.toolTip.TITLE_COLOR)
		current = skilltreelocale.FormatNodeValue(
			presenter["node_id"], presenter.get("current_total", 0),
		) or u"-"
		if rank < maxRank and presenter.get("next_total") is not None:
			nextTotal = skilltreelocale.FormatNodeValue(
				presenter["node_id"], presenter["next_total"],
			) or u"-"
			self.toolTip.AppendTextLine(current + u"  ->  " + nextTotal, bonuscolor.Text(current + nextTotal))
		else:
			self.toolTip.AppendTextLine(current, bonuscolor.Text(current))
		if player.GetStatus(player.LEVEL) < presenter["required_level"]:
			self.toolTip.AppendTextLine(
				skilltreelocale.GetGateText(_ClientLocaleKey(), presenter["required_level"]),
				self.toolTip.DISABLE_COLOR,
			)
		if rank < maxRank:
			cost = self.model.GetNextCost(presenter["node_id"])
			if isinstance(cost, dict):
				balance = self.model.GetPointBalance()
				hasPoints = balance is not None and balance >= cost.get("points", 0)
				try:
					hasYang = player.GetElk() >= cost.get("yang", 0)
				except Exception:
					hasYang = False
				self.toolTip.AppendSpace(5)
				self.toolTip.AppendTextLine(
					skilltreelocale.GetPointCostText(_ClientLocaleKey(), cost["points"]),
					0xffe6bd78 if hasPoints else 0xffef7070,
				)
				self.toolTip.AppendTextLine(
					skilltreelocale.GetYangCostText(_ClientLocaleKey(), cost.get("yang", 0)),
					0xffe6bd78 if hasYang else 0xffef7070,
				)
				for itemCost in cost.get("items", ()):
					self.toolTip.AppendTextLine(_CostItemText(itemCost["vnum"], itemCost["count"]), 0xffe6bd78)
		self.toolTip.ResizeToolTip()
		self.toolTip.ShowToolTip()

	def ShowNodeCostToolTip(self, nodeWidget):
		if not self.toolTip:
			return
		self.toolTip.ClearToolTip()
		presenter = getattr(nodeWidget, "presenter", None)
		if not nodeWidget.snapshotReady or not isinstance(presenter, dict):
			self.toolTip.AppendTextLine(uiScriptLocale.SKILL_TREE_NODE_LOADING)
			self.toolTip.ResizeToolTip()
			self.toolTip.ShowToolTip()
			return
		cost = presenter.get("next_rank_cost", {"yang": 0, "items": []})
		for itemCost in cost["items"]:
			# "Name  12 / 25", the count green / red (root/ownedcount.py)
			self.toolTip.AppendTextLine(_CostItemText(itemCost["vnum"], itemCost["count"]), self.toolTip.NORMAL_COLOR)
		yangCost = cost["yang"]
		if yangCost > 0:
			ownedYang = player.GetElk()
			color = self.toolTip.NORMAL_COLOR if ownedYang >= yangCost else self.toolTip.DISABLE_COLOR
			self.toolTip.AppendTextLine(
				uiScriptLocale.SKILL_TREE_NODE_YANG_OWNED % (ownedYang, yangCost),
				color,
			)
		self.toolTip.ResizeToolTip()
		self.toolTip.ShowToolTip()

	def HideNodeCostToolTip(self):
		self.HideNodeToolTip()

	def HideNodeToolTip(self):
		if self.toolTip:
			self.toolTip.HideToolTip()

	def OnUpdate(self):
		now = app.GetTime()
		if self.IsShow():
			self.__RefreshActivationStatus(now)
		if (
			self.IsShow()
			and self.presentationReady
			and self.viewport
			and self.viewport.canvas.lastPresenters is not None
		):
			level = player.GetStatus(player.LEVEL)
			if level != self.lastCharacterLevel:
				self.lastCharacterLevel = level
				self.viewport.canvas.RefreshControls()
			self.viewport.canvas.UpdateAnimation(now)

	def __SyncLook(self):
		"""The R1 look (root/uiskilltreer1.py) unless Settings -> "Starý vzhled" chose the original window; the switch
		takes effect on the next opening. A failure traces to syserr and keeps the original look (not retried)."""
		try:
			import uir1
			wanted = uir1.UseR1() and not self.r1Failed
		except Exception:
			return
		if wanted and not self.r1:
			try:
				import uiskilltreer1
				self.r1 = uiskilltreer1.SkillTreeSkin(self)
			except Exception:
				uir1.TraceFailure("the skill tree window")
				self.r1Failed = True
				self.r1 = None
		elif not wanted and self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def Open(self):
		wasShown = self.IsShow()
		self.__SyncLook()
		self.SetCenterPosition()
		x, y = self.GetLocalPosition()
		x, y = ClampSkillTreePosition(
			x, y, self.layout.WINDOW_WIDTH, self.layout.WINDOW_HEIGHT,
			wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight(),
		)
		self.SetPosition(x, y)
		self.Show()
		self.SetTop()
		if not wasShown and self.openHandler:
			self.openHandler()

	def Close(self):
		self.__CloseUpgradeDialog()
		if self.dismantleWindow:
			self.dismantleWindow.Close()
		self.HideNodeToolTip()
		if self.viewport:
			self.viewport.CancelDrag()
		if self.renewToolTip:
			self.renewToolTip.ForceHide()
		self.Hide()
		return True

	def Destroy(self):
		if getattr(self, "r1", None):
			r1, self.r1 = self.r1, None
			r1.Destroy()
		self.__CloseUpgradeDialog()
		if self.dismantleWindow:
			self.dismantleWindow.Destroy()
			self.dismantleWindow = None
		self.HideNodeToolTip()
		if self.viewport:
			self.viewport.CancelDrag()
			for record in self.viewport.canvas.connectors:
				record["spark"].Hide()
		self.__CleanupRenewToolTip()
		self.ClearDictionary()
		self.board = None
		self.treeAnchor = None
		self.treeErrorText = None
		self.footerBoard = None
		self.viewport = None
		self.toolTip = None
		self.pointIcon = None
		self.pointBalanceText = None
		self.selectedNodeId = None
		self.lastCharacterLevel = None
		self.activationStatus = None
		self.activationButton = None
		self.activationStatusAsset = None
		self.remainingTimeText = None
		self.renewButton = None
		self.dismantleButton = None
		self.dismantleHandler = None
		self.activationSnapshotReady = False
		self.activationMutationPending = False
		self.renewHoverArea = None
		self.renewToolTip = None
		self.renewCostFingerprint = None
		self.upgradeHandler = None
		self.activationHandler = None
		self.renewHandler = None
		self.openHandler = None
		self.model = None
		self.presentationReady = False
		self.presentationError = False

	def OnPressEscapeKey(self):
		self.Close()
		return True
