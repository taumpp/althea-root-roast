"""Can a skill point still be spent? The rule behind "Zvýšit schopnost" and the "+" in Schopnosti.

Owner 8. 10. (tester "Schovat okno zvýšit schopnost když mám všechny ability již hotové"): skill points raise a
skill only while it has no grade yet (below M); M, G and P are raised with books or spirit stones.
When no skill of the chosen group can take a point, the "+" button with its point badge stays hidden even though
"Volné body" is above 0.

This module is the one rule for both places: the "+" orb (uigamebutton), the button panel badge
(buttonpanelstatus) and the plus buttons of the skill window (uicharacter.CharacterWindow.__RefreshSkillPlusButton)
all ask CanTakePoint, so they cannot disagree.

A slot can take a point of a page when (server CHARACTER::SkillLevelUp, SKILL_UP_BY_POINT):
- a skill sits in the slot (the slots of the chosen class and group, playersettingmodule.RegisterSkill; a skill not
  learned yet is level 0 and counts),
- the skill draws on the page's point pool: the active page only class skills (skill type ACTIVE, POINT_SKILL).
  The horse skills 137-140 sit in active slots 9-15 but use the horse points (POINT_HORSE_SKILL), the support
  skills use the support points; they never make an active point spendable,
- grade 0 (M1 and above need books or spirit stones), not skill 135,
- skill.CanLevelUpSkill: below the maximum level, required skill and stats met, no CANNOT_LEVEL_UP.
Character level: the class skills have no level limit (skill_proto bLevelLimit 0); only the horse skills have one
(50/52/55), and they are excluded above. The button is re-evaluated on every status refresh (level up included),
so a skill that opens later shows the button only then.
No skill group chosen yet means no skill to raise, like the skill window. The native modules are passed in, so the
rule runs headless in the tests. Buffi skills are read only and have no points of their own; support points are
never shown (uicharacter.HIDE_SUPPORT_SKILL_POINT).
"""

PAGE_ACTIVE = "ACTIVE"
PAGE_SUPPORT = "SUPPORT"

ACTIVE_PAGE_START = 0
ACTIVE_PAGE_SLOTS = 12          # CharacterWindow.PAGE_SLOT_COUNT
NEVER_RAISED = (135,)           # CharacterWindow.CanShowPlusButton

# Page -> the skill type that spends its points (active: player.SKILL_ACTIVE, support: player.SKILL_SUPPORT).
_PAGE_SKILL_TYPE = {
    PAGE_ACTIVE: "SKILL_TYPE_ACTIVE",
    PAGE_SUPPORT: "SKILL_TYPE_SUPPORT",
}


def _Int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _SpendsPagePoints(skill, index, page):
    wanted = getattr(skill, _PAGE_SKILL_TYPE[page], None)
    if wanted is None:
        return True
    try:
        return _Int(skill.GetSkillType(index)) == _Int(wanted)
    except Exception:
        # No skill data for the index: nothing a point can raise.
        return False


def CanTakePoint(player, skill, slot, page=PAGE_ACTIVE):
    """A point of the page's pool can raise the skill in this slot (the skill window shows a "+" on it)."""
    index = _Int(player.GetSkillIndex(slot))
    if index == 0 or index in NEVER_RAISED:
        return False
    if _Int(player.GetSkillGrade(slot)) != 0:
        return False
    if not _SpendsPagePoints(skill, index, page):
        return False
    try:
        return bool(skill.CanLevelUpSkill(index, _Int(player.GetSkillLevel(slot))))
    except Exception:
        # The native call raises for a skill it has no data for: nothing a point can raise.
        return False


def HasSkillToRaise(player, skill, net=None):
    """At least one skill of the chosen group can still take an active skill point."""
    if net is not None:
        group = getattr(net, 'GetMainActorSkillGroup', None)
        if callable(group) and _Int(group()) == 0:
            return False
    for slot in range(ACTIVE_PAGE_START, ACTIVE_PAGE_START + ACTIVE_PAGE_SLOTS):
        if CanTakePoint(player, skill, slot):
            return True
    return False


def SpendablePoints(player, skill, net=None):
    """The free active skill points worth showing: 0 while no skill can take one."""
    points = _Int(player.GetStatus(player.SKILL_ACTIVE))
    if points <= 0 or not HasSkillToRaise(player, skill, net):
        return 0
    return points
