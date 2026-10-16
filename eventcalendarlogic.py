import datetime


VISIBLE_MONTH_COUNT = 4


def IsDateAllowed(dateKey, anchorDate):
	day = datetime.date(*dateKey)
	monthStart = anchorDate.replace(day=1)
	windowStart = monthStart - datetime.timedelta(days=monthStart.weekday())
	endYear, endMonth = AddMonths(anchorDate.year, anchorDate.month, VISIBLE_MONTH_COUNT)
	return windowStart <= day < datetime.date(endYear, endMonth, 1)


def EventsForDay(rows, dateKey, startIndex, endIndex):
	dayStart = datetime.datetime(*dateKey)
	dayEnd = dayStart + datetime.timedelta(days=1)
	result = []
	for row in rows:
		start = datetime.datetime.fromtimestamp(int(row[startIndex]))
		endStamp = int(row[endIndex])
		if endStamp > int(row[startIndex]):
			end = datetime.datetime.fromtimestamp(endStamp)
			if start < dayEnd and end > dayStart:
				result.append(row)
		elif dayStart <= start < dayEnd:
			# Timed announcements without an end belong to their starting day.
			result.append(row)
	return result


def EventState(start, end, active, now):
	if int(start) > int(now):
		return "upcoming"
	if int(end) > int(start) and int(end) <= int(now):
		return "ended"
	if active:
		return "active"
	return "scheduled"


def PageBounds(count, page, pageSize):
	lastPage = max(0, (count - 1) // pageSize)
	page = max(0, min(int(page), lastPage))
	return page, page * pageSize, min(count, (page + 1) * pageSize), lastPage + 1


def AddMonths(year, month, offset):
	serial = int(year) * 12 + int(month) - 1 + int(offset)
	return serial // 12, serial % 12 + 1


def IsMonthAllowed(year, month, anchorYear, anchorMonth):
	targetSerial = int(year) * 12 + int(month) - 1
	anchorSerial = int(anchorYear) * 12 + int(anchorMonth) - 1
	return anchorSerial <= targetSerial < anchorSerial + VISIBLE_MONTH_COUNT


def ResolveEventDate(startDateTime, endDateTime, today):
	windowStart = datetime.datetime(today.year, today.month, 1)
	windowEndYear, windowEndMonth = AddMonths(today.year, today.month, VISIBLE_MONTH_COUNT)
	windowEnd = datetime.datetime(windowEndYear, windowEndMonth, 1)

	if windowStart <= startDateTime < windowEnd:
		resolved = startDateTime
	elif endDateTime is not None and windowStart <= endDateTime < windowEnd:
		resolved = endDateTime
	elif endDateTime is not None and startDateTime < windowStart and endDateTime >= windowEnd:
		resolved = windowStart
	else:
		return None

	return resolved.year, resolved.month, resolved.day


def ResolveEventTimestamp(startTimestamp, endTimestamp, today=None):
	if today is None:
		today = datetime.date.today()

	startDateTime = datetime.datetime.fromtimestamp(int(startTimestamp))
	endDateTime = None
	if endTimestamp:
		endDateTime = datetime.datetime.fromtimestamp(int(endTimestamp))

	return ResolveEventDate(startDateTime, endDateTime, today)


def BuildMonthGrid(year, month):
	monthStart = datetime.date(int(year), int(month), 1)
	gridStart = monthStart - datetime.timedelta(days=monthStart.weekday())
	cells = []

	for offset in range(42):
		day = gridStart + datetime.timedelta(days=offset)
		cells.append((day.year, day.month, day.day, day.month == monthStart.month))

	return cells


def WeekDates(dateKey):
	day = datetime.date(*dateKey)
	monday = day - datetime.timedelta(days=day.weekday())
	return [(date.year, date.month, date.day)
		for date in (monday + datetime.timedelta(days=offset) for offset in range(7))]


def ShiftWeek(dateKey, offset, anchorDate):
	target = datetime.date(*dateKey) + datetime.timedelta(days=7 * int(offset))
	key = (target.year, target.month, target.day)
	if IsDateAllowed(key, anchorDate):
		return key
	allowed = [date for date in WeekDates(key) if IsDateAllowed(date, anchorDate)]
	return (allowed[0] if int(offset) < 0 else allowed[-1]) if allowed else None
