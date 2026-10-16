"""Read-only Buffi skills and measured character-skill header controls."""
import fontconfig
import localeInfo
import osfInfo
import skill
import ui
import uiScriptLocale

POINT_WIDTH = 102
POINT_X = 130
TAB_BASE = "d:/ymir work/ui/public/crimson/controls/legacy/small_thin_"
SLOT_POSITIONS = ((21, 4), (95, 4), (169, 4), (58, 78), (132, 78))
NAME_WIDTH = 70
SLOT_BASE = "d:/ymir work/ui/public/Slot_Base.sub"


def FitText(line, text, width):
    line.SetText(text)
    while text and line.GetTextSize()[0] > width:
        text = text[:-1]
        line.SetText(text + "…")
    return line.GetText()


def ConfigureHeader(window):
    header = window.GetChild("Skill_Active_Title_Bar")
    page = window.pageDict["SKILL"]
    row = ui.Window()
    row.SetParent(page)
    row.SetPosition(9, header.GetLocalPosition()[1])
    row.SetSize(page.GetWidth() - 18, 20)
    row.Show()
    window.skillHeaderRow = row
    for button, x, caption in (
        (window.skillGroupButton1, 0, uiScriptLocale.CHARACTER_SKILL),
        (window.skillGroupButton2, 64, "BUFF"),
    ):
        button.SetParent(row)
        # Native 60x20 carriers avoid scaling and generic action-button aliases.
        button.SetUpVisual(TAB_BASE + "01.tga")
        button.SetOverVisual(TAB_BASE + "02.tga")
        button.SetDownVisual(TAB_BASE + "03.tga")
        button.SetPosition(x, 0)
        button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
        button.SetText(caption)
        # SetText retains the old control's text object and anchor.
        button.ButtonText.SetPosition(button.GetWidth() // 2, button.GetHeight() // 2)
        # This thin family has a one-pixel frame on each side.
        FitText(button.ButtonText, caption, button.GetWidth() - 2)
        button.SetToolTipText(caption)
        button.Show()
    window.activeSkillGroupName.Hide()
    window.GetChild("Active_Skill_Point_Label").Hide()
    area = ui.Window()
    area.SetParent(row)
    area.SetPosition(POINT_X, 0)
    area.SetSize(min(POINT_WIDTH, row.GetWidth() - POINT_X), 20)
    area.Show()
    window.skillPointArea = area
    value = window.activeSkillPointValue
    value.SetParent(area)
    value.SetPosition(area.GetWidth(), 10)
    value.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
    value.SetHorizontalAlignRight()
    value.SetVerticalAlignCenter()
    value.SetOutline()
    value.Show()
    # All live controls now belong to the plain row, not this old decoration.
    header.Hide()


class CharacterBuffPage(ui.Window):
    def __init__(self, parent):
        # Window.__init__ dispatches to our Hide override.
        self.toolTip = None
        self.hovered = None
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.SetSize(223, 146)
        self.levels = None
        self.healingUnlocked = False
        self.names = []
        self.slots = ui.SlotWindow()
        self.slots.SetParent(self)
        self.slots.SetSize(223, 146)
        self.slots.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
        self.slots.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
        self.slots.SetOverOutItemEvent(ui.__mem_func__(self.HideToolTip))
        for index, (x, y) in enumerate(SLOT_POSITIONS):
            self.slots.AppendSlot(index, x, y, 32, 32)
            lines = []
            for row in range(2):
                line = ui.TextLine()
                line.SetParent(self)
                line.AddFlag("not_pick")
                line.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
                line.SetPosition(x + 16, y + 36 + row * 13)
                line.SetHorizontalAlignCenter()
                line.SetOutline()
                line.Show()
                lines.append(line)
            self.names.append(lines)
        self.slots.Show()
        self.Refresh()
        self.Hide()

    def SetToolTip(self, toolTip):
        self.toolTip = toolTip

    def SetLevels(self, levels):
        self.HideToolTip()
        self.levels = tuple(int(level) for level in levels)
        self.Refresh()

    def SetHealingUnlocked(self, unlocked):
        self.HideToolTip()
        self.healingUnlocked = bool(int(unlocked))
        self.Refresh()

    def Reset(self):
        self.levels = None
        self.healingUnlocked = False
        self.HideToolTip()
        self.Refresh()

    def Refresh(self):
        for index, vnum in enumerate(osfInfo.SUPPORT_SKILL_VNUMS):
            grade, level = 0, 0
            if self.levels is not None:
                realLevel = self.levels[index]
                grade = osfInfo.SkillLevelToGrade(realLevel)
                level = osfInfo.SkillLevelToLvl(realLevel)
            locked = self.levels is None or (index >= 3 and not self.healingUnlocked)
            color = (0.45, 0.45, 0.45, 1.0) if locked else (1.0, 1.0, 1.0, 1.0)
            self.slots.ClearSlot(index)
            icon = skill.GetIconImageNew(vnum, grade)
            if icon:
                self.slots.SetSlot(index, vnum, 1, 1, icon, color)
                if self.levels is not None:
                    self.slots.SetSlotCountNew(index, grade, level)
            self.SetSkillName(index, skill.GetSkillName(vnum, 0), locked)
        self.slots.RefreshSlot()

    def SetSkillName(self, index, name, locked):
        first, second = self.names[index]
        first.SetText(name)
        second.SetText("")
        if first.GetTextSize()[0] > NAME_WIDTH:
            words = name.split()
            split = len(words) - 1
            while split > 0:
                first.SetText(" ".join(words[:split]))
                if first.GetTextSize()[0] <= NAME_WIDTH:
                    break
                split -= 1
            if split:
                FitText(second, " ".join(words[split:]), NAME_WIDTH)
            else:
                FitText(first, name, NAME_WIDTH)
        for line in (first, second):
            line.SetPackedFontColor(0xff929292 if locked else 0xffeadfc8)

    def OverInItem(self, index):
        if self.toolTip is None or not 0 <= index < len(osfInfo.SUPPORT_SKILL_VNUMS):
            return
        self.hovered = index
        vnum = osfInfo.SUPPORT_SKILL_VNUMS[index]
        if self.levels is None:
            self.toolTip.AppendDefaultData(vnum, 0)
            self.toolTip.ShowToolTip()
            return
        realLevel = self.levels[index]
        self.toolTip.SetSupportSkill(vnum, osfInfo.SkillLevelToLvl(realLevel),
            osfInfo.SkillLevelToGrade(realLevel), realLevel)
        if index >= 3 and not self.healingUnlocked:
            self.toolTip.AppendTextLine(localeInfo.TOOLTIP_ITEM_LIMIT_LEVEL % 90,
                self.toolTip.DISABLE_COLOR)

    def HideToolTip(self):
        if self.hovered is not None and self.toolTip is not None:
            self.toolTip.HideToolTip()
        self.hovered = None

    def Hide(self):
        self.HideToolTip()
        ui.Window.Hide(self)
