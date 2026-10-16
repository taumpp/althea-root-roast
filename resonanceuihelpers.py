RESONANCE_KEY_VNUM = 79631
EMPTY_SLOTS = ((0, 0, 0), (0, 0, 0), (0, 0, 0))
EMPTY_METADATA = (0, 0, EMPTY_SLOTS)
VALID_UNLOCKED_MASKS = (0, 1, 3, 7)
SEAL_RANK_COUNT = 6
SEAL_FAMILY_COUNT = 7
SEAL_BONUSES = {}


def ClearSealValues():
	SEAL_BONUSES.clear()


def ReceiveSealValues(payload):
	"""Replace the tooltip snapshot sent from the server's resonance catalog."""
	try:
		if len(payload) > 512:
			return False
		families = payload.split(";")
		if len(families) != SEAL_FAMILY_COUNT:
			return False
		updated = {}
		for familyIndex, row in enumerate(families):
			columns = [int(value) for value in row.split(",")]
			if len(columns) != SEAL_RANK_COUNT + 1:
				return False
			firstVnum = columns[0]
			if firstVnum <= 0 or firstVnum > 4294967295:
				return False
			for rank, value in enumerate(columns[1:]):
				vnum = firstVnum + rank
				if vnum > 4294967295 or vnum in updated or value <= 0 or value > 32767:
					return False
				updated[vnum] = (familyIndex, value)
		SEAL_BONUSES.clear()
		SEAL_BONUSES.update(updated)
		return True
	except (AttributeError, TypeError, ValueError):
		return False


def GetSealBonus(vnum):
	try:
		return SEAL_BONUSES.get(int(vnum))
	except (TypeError, ValueError):
		return None


def IsResonanceKey(vnum):
	try:
		return int(vnum) == RESONANCE_KEY_VNUM
	except (TypeError, ValueError):
		return False


def NextLockedSlot(unlockedMask):
	try:
		unlockedMask = int(unlockedMask)
	except (TypeError, ValueError):
		return None
	if unlockedMask not in VALID_UNLOCKED_MASKS or unlockedMask == 7:
		return None
	if unlockedMask == 0:
		return 0
	if unlockedMask == 1:
		return 1
	return 2


def FirstUnlockedEmptySlot(unlockedMask, slots):
	try:
		unlockedMask = int(unlockedMask)
		if unlockedMask not in VALID_UNLOCKED_MASKS or len(slots) != 3:
			return None
		for slotIndex in range(3):
			if unlockedMask & (1 << slotIndex) and not int(slots[slotIndex][0]):
				return slotIndex
	except (IndexError, TypeError, ValueError):
		return None
	return None


def NormalizeMetadata(raw):
	try:
		if len(raw) != 3:
			return EMPTY_METADATA
		instanceId, unlockedMask, slots = raw
		instanceId = int(instanceId)
		unlockedMask = int(unlockedMask)
		if instanceId < 0 or unlockedMask not in VALID_UNLOCKED_MASKS:
			return EMPTY_METADATA
		if len(slots) != 3:
			return EMPTY_METADATA
		normalizedSlots = []
		for slot in slots:
			if len(slot) != 3:
				return EMPTY_METADATA
			vnum, baseValue, effectiveValue = [int(value) for value in slot]
			if vnum < 0 or baseValue < 0 or effectiveValue < 0:
				return EMPTY_METADATA
			normalizedSlots.append((vnum, baseValue, effectiveValue))
		return instanceId, unlockedMask, tuple(normalizedSlots)
	except (TypeError, ValueError):
		return EMPTY_METADATA
