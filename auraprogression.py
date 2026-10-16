ABSORPTION_BY_GRADE = (1, 5, 10, 15, 20, 25)
REQUIRED_POINTS_BY_GRADE = (500, 1500, 3500, 6000, 10000, 0)
LEVEL_MAX_BY_GRADE = (49, 99, 149, 199, 249, 250)
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
