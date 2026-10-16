UNIVERSAL_SKILL_BOOK = 50526
STANDARD_SKILL_COUNT = 6
MAX_SELECTED_BOOKS = 55
_RACE_JOBS = (0, 1, 2, 3, 0, 1, 2, 3)
_SKILL_BASES = ((1, 16), (31, 46), (61, 76), (91, 106))


def CanReadUniversal(race, group, skillIndex, skillGrade):
	if race < 0 or race >= len(_RACE_JOBS) or group not in (1, 2) or skillGrade != 1:
		return False
	base = _SKILL_BASES[_RACE_JOBS[race]][group - 1]
	return base <= skillIndex < base + STANDARD_SKILL_COUNT


def UniversalReadArguments(skillIndex, count=0, useTime=1, useLuck=1):
	return "%d %s %d %d" % (skillIndex, "all" if count == 0 else str(count), useTime, useLuck)
