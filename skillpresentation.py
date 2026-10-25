"""The character window has three columns for five actual skill grades."""


def CompactGrade(grade):
    return 0 if grade <= 0 else 1 if grade <= 2 else 2


def ColumnGrades(actualGrade):
    return (0, 2 if actualGrade >= 2 else 1, max(3, actualGrade))


# The rank of a skill as the PvM passives show it in the tooltip title ("Smršť meče | M1", pvmpersonal.grade):
# the level below M, then M1-M10, G1-G10, P1-P10, S1. Owner 8. 10. (tester "Spelly co nejsou pasivky neukazují
# označení ranku schopnosti"): every class skill shows it, not only the PvM passives.
RANK_LETTERS = 'MGPS'


def RankLabel(grade, level):
    grade, level = int(grade), int(level)
    if grade <= 0:
        return str(level) if level > 0 else None
    return '%s%d' % (RANK_LETTERS[min(grade, len(RANK_LETTERS)) - 1], max(1, level))


def CurrentRank(player, skill, skillIndex):
    """The player's rank of one of the class skills (the active page), None for other skills or one not learned."""
    if skill.GetSkillType(skillIndex) != skill.SKILL_TYPE_ACTIVE:
        return None
    slot = player.GetSkillSlotIndex(skillIndex)
    if player.GetSkillIndex(slot) != skillIndex:
        return None
    return RankLabel(player.GetSkillGrade(slot), player.GetSkillLevel(slot))


def TitleWithRank(name, rank):
    return '%s | %s' % (name, rank) if rank else name
