"""Pickable icon-only row with one shared, safely owned hover tooltip."""
import app
import ui
import uiToolTip
import nonplayer
import localeInfo
import monsterpresentation

# This fork predates the optional community lifecycle decorator.
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)


class MonsterIndicators(ui.Window):
    def __init__(self, parent=None, size=31, gap=4):
        # Hide is called by the base constructor before widgets exist.
        self.tooltip = None
        ui.Window.__init__(self)
        if parent is not None:
            self.SetParent(parent)
        else:
            self.AddFlag("float")
        self.iconSize = int(size)
        self.gap = int(gap)
        self.icons = []
        self.tooltip = uiToolTip.ToolTip()
        self.lines = ()
        self.monsterVnum = None
        self.presentationKey = None
        self.elements = ()
        self.races = ()
        self.SetSize(0, self.iconSize)
        self.Hide()

    def SetMonster(self, vnum, dungeonElements=None, liveElements=None):
        key = (vnum, dungeonElements, None if liveElements is None else tuple(sorted(liveElements.items())))
        if self.presentationKey == key:
            return self.GetWidth()
        self.HideTooltip()
        self.monsterVnum = vnum
        self.presentationKey = key
        self.races, self.elements, isStone = monsterpresentation.ReadMonster(
            vnum, getattr(app, "ENABLE_ELEMENT_ADD", False), nonplayer)
        if dungeonElements is not None:
            # The boss race remains a boss property. The dungeon's elements
            # come from the live, complete server catalogue, including adds.
            self.elements = dungeonElements if getattr(app, "ENABLE_ELEMENT_ADD", False) else ()
        if liveElements is not None:
            # The target's own element packet wins over its prototype, as in uitargetinfo.
            enabled = getattr(app, "ENABLE_ELEMENT_ADD", False)
            self.elements = tuple(index for index in range(len(monsterpresentation.ELEMENT_NAMES))
                                  if enabled and not isStone and liveElements.get(index, 0) > 0)
        self.lines = monsterpresentation.TooltipLines(self.races, self.elements, isStone, localeInfo)
        assetSize = self.iconSize if self.iconSize in (24, 31) else 39
        elementAssetSize = 24 if self.iconSize == 24 else 39
        paths = monsterpresentation.IndicatorAssets(self.races, self.elements, assetSize)
        for icon in self.icons:
            icon.Hide()
        for index, path in enumerate(paths):
            if index == len(self.icons):
                icon = ui.ExpandedImageBox()
                icon.SetParent(self)
                icon.SAFE_SetStringEvent("MOUSE_OVER_IN", self.ShowTooltip)
                icon.SAFE_SetStringEvent("MOUSE_OVER_OUT", self.HideTooltip)
                self.icons.append(icon)
            icon = self.icons[index]
            icon.LoadImage(path)
            # Absolute native size: do not compound the previous load's scale.
            sourceSize = assetSize if path.startswith(monsterpresentation.RACE_ROOT) else elementAssetSize
            icon.SetScale(float(self.iconSize) / sourceSize, float(self.iconSize) / sourceSize)
            icon.SetSize(self.iconSize, self.iconSize)
            icon.SetPosition(index * (self.iconSize + self.gap), 0)
            icon.Show()
        self.SetSize(monsterpresentation.RowWidth(len(paths), self.iconSize, self.gap), self.iconSize)
        return self.GetWidth()

    def ShowTooltip(self):
        if not self.tooltip or not self.IsShow():
            return
        self.tooltip.ClearToolTip()
        self.tooltip.SetThinBoardSize(uiToolTip.ToolTip.TOOL_TIP_WIDTH)
        for line in self.lines:
            self.tooltip.AutoAppendTextLine(line)
        # AutoAppendTextLine measures text but does not resize the board.
        self.tooltip.AlignHorizonalCenter()
        self.tooltip.ShowToolTip()

    def HideTooltip(self):
        if self.tooltip:
            self.tooltip.HideToolTip()

    def Hide(self):
        self.HideTooltip()
        ui.Window.Hide(self)

    @WindowDestroy
    def Destroy(self):
        self.HideTooltip()
        self.icons = []
        self.tooltip = None
        self.lines = ()
        self.monsterVnum = None
        self.presentationKey = None
        self.races = ()
        self.elements = ()
