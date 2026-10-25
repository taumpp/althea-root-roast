# Gameplay values are generated from the connected release's server authority.
from auraprogressiondata import CATALOG

ABSORPTION_BY_GRADE = tuple(row["absorption_percent"] for row in CATALOG["grades"])
REQUIRED_POINTS_BY_GRADE = tuple(row["required_points"] for row in CATALOG["grades"])
LEVEL_MAX_BY_GRADE = tuple(row["level_max"] for row in CATALOG["grades"])
PROGRESS_SOCKET_VERSION_BASE = 2000


def Grade(itemVnum):
	grade = int(itemVnum) % 10
	if grade < 1 or grade > len(ABSORPTION_BY_GRADE):
		return 0
	return grade


def AbsorptionPercent(itemVnum):
	grade = Grade(itemVnum)
	if grade == 0:
		return 0
	return ABSORPTION_BY_GRADE[grade - 1]


def AbsorptionPercentForGrade(grade):
	if grade < 1 or grade > len(ABSORPTION_BY_GRADE):
		return 0
	return ABSORPTION_BY_GRADE[grade - 1]


def RequiredPoints(itemVnum):
	grade = Grade(itemVnum)
	if grade == 0:
		return 0
	return REQUIRED_POINTS_BY_GRADE[grade - 1]


def GradeLevel(itemVnum):
	grade = Grade(itemVnum)
	if grade == 0:
		return 0
	return LEVEL_MAX_BY_GRADE[grade - 1]


def Progress(itemVnum, progressSocket):
	required = RequiredPoints(itemVnum)
	if required == 0:
		return (0, 0)
	expectedVersion = PROGRESS_SOCKET_VERSION_BASE + GradeLevel(itemVnum)
	if int(progressSocket) // 100000 != expectedVersion:
		return (0, required)
	current = max(0, int(progressSocket) % 100000)
	return (min(current, required), required)


def IsReadyToEvolve(itemVnum, progressSocket):
	(current, required) = Progress(itemVnum, progressSocket)
	return required > 0 and current >= required


def RefineInfo(level, info):
    # Compatibility for the native legacy window API; manual fees are retired.
    keys = ("grade", "level_min", "level_max", "required_points")
    if info < 0 or info >= len(keys):
        return 0
    for row in CATALOG["grades"]:
        if row["level_min"] <= level <= row["level_max"]:
            return row[keys[info]]
    return 0
