"""Shared presentation policy for the 50525 P1-P10 -> S stone."""

STONE_VNUM = 50525
BUFF_SKILLS = frozenset((3, 4, 19, 34, 49, 63, 64, 65, 79, 94, 95, 96, 110, 111))
STANDARD_SKILLS = (
	frozenset(range(1, 7)) | frozenset(range(16, 22)) |
	frozenset(range(31, 37)) | frozenset(range(46, 52)) |
	frozenset(range(61, 67)) | frozenset(range(76, 82)) |
	frozenset(range(91, 97)) | frozenset(range(106, 112))
)
SAGE_SKILLS = BUFF_SKILLS | STANDARD_SKILLS


def CanRead(skillVnum, grade, displayLevel, personalSources=()):
	eligible = skillVnum in SAGE_SKILLS or skillVnum in personalSources
	return bool(eligible and grade == 3 and 1 <= displayLevel <= 10)


def GradeLabel(grade, displayLevel):
	if grade == 4:
		return "S"
	if grade == 3 and 1 <= displayLevel <= 10:
		return "P%d" % displayLevel
	return None


def NextGradeLabel(grade, displayLevel):
	if grade != 3 or not 1 <= displayLevel <= 10:
		return None
	return "S" if displayLevel == 10 else "P%d" % (displayLevel + 1)


def ReadingTerms(item):
	"""The saved server/client prototype owns material and total-read cap."""
	item.SelectItem(STONE_VNUM)
	return tuple(int(item.GetValue(index)) for index in (1, 2, 3))
