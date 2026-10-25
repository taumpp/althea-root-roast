"""One tree HUD icon with a compact, time-free list of its active bonuses."""
import app
import skilltreecatalog
import skilltreelocale
import ui
import uiScriptLocale
import uieffecttooltipstyle
import uiaffecthover
from uiaffectsummary import CompactAffectSummary

ICON = "d:/ymir work/ui/game/skill_tree_v2/activation/tree_active.png"

class SkillTreeSummary(CompactAffectSummary):
    GROUP_KEY = "tree"

class SkillTreeAffectImage(ui.ExpandedImageBox):
    def __init__(self):
        ui.ExpandedImageBox.__init__(self)
        self.summary = None
        self.members = []
        self.endTime = 0
        self.LoadImage(ICON)
        self.SetScale(0.7, 0.7)
        self.SetSize(25, 26)
        self.Hide()

    def SetState(self, remaining, members):
        self.members = list(members)
        self.endTime = app.GetGlobalTimeStamp() + max(0, remaining)
        if remaining > 0:
            self.Show()
        else:
            self.Hide()
            if self.summary:
                self.summary.Close()

    def GetSummaryRows(self):
        language = app.GetLocalePath().replace("\\", "/").rstrip("/").split("/")[-1]
        rows = []
        for nodeId, value in self.members:
            texts = skilltreelocale.GetNodeText(language, nodeId) or skilltreelocale.GetNodeText("en", nodeId)
            formatted = skilltreelocale.FormatNodeValue(nodeId, value)
            if texts and formatted is not None:
                title = texts[0]
                if nodeId == skilltreecatalog.FIRST_NODE_ID:
                    # The tree node names its maximum (+10); the HUD must show
                    # the current learned amount once, including ranks 1-4.
                    title = title.rsplit(" +", 1)[0]
                rows.append(("", "%s %s" % (title, formatted), (), 0,
                             uieffecttooltipstyle.RoleForTreeNode(nodeId)))
        return rows

    def GetSummaryTitle(self):
        return uiScriptLocale.SKILL_TREE_TITLE

    def ShowHover(self):
        if self.IsShow() and self.members:
            if self.summary is None:
                self.summary = SkillTreeSummary(self)
            self.summary.Open()
            return self.summary.Close
        return None

    def HoverHeld(self):
        # The summary panel closes itself after its grace (uiaffectsummary); one surface of the bar (uiaffecthover).
        return bool(self.summary and self.summary.IsShow())

    def HoverGuard(self, other):
        try:
            # The window height (25 x 26), not ImageBox.GetHeight = the texture.
            return other.GetGlobalPosition()[1] >= self.GetGlobalPosition()[1] + ui.Window.GetHeight(self) - 1
        except Exception:
            return False

    def OnMouseOverIn(self):
        uiaffecthover.Over(self)

    def OnMouseOverOut(self):
        uiaffecthover.Out(self)

    def Destroy(self):
        if self.summary:
            self.summary.Destroy()
        self.summary = None
        self.members = []
        self.Hide()
