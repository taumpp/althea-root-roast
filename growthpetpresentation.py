"""Shared labels and visible skill slots for growth-pet UI."""

import localeInfo
import player

# Authoritative bounds belong to the pet ID; quality is independent of old type.
_growth = {}


def ClearGrowthPreview():
	global _growth
	_growth = {}


def SetGrowthPreview(pet_id, *values):
	global _growth
	try:
		pet_id = int(pet_id)
		values = tuple(int(value) for value in values)
	except (ValueError, TypeError):
		return False
	if pet_id <= 0 or len(values) != 6 or any(value < 0 or value > 100000 for value in values):
		return False
	if any(values[index] > values[index + 1] for index in (0, 2, 4)):
		return False
	_growth[pet_id] = values
	return True


def GrowthBounds(index, pet_id):
	values = _growth.get(int(pet_id))
	return values[index * 2:index * 2 + 2] if values is not None else (None, None)


def ThirdBonusLabel(pet_type):
	if int(pet_type) % 2:
		return localeInfo.PET_TOOLTIP_HUMAN
	return localeInfo.PET_TOOLTIP_MONSTER


def StatValueText(value, low=None, high=None):
	# GetPetItem preserves stored tenths; do not truncate a growing pet stat.
	current = ("%.1f" % float(value)).replace(".", ",")
	if low is None or high is None:
		return "+%s %%" % current
	growth = ("%.1f-%.1f" % (low / 10.0, high / 10.0)).replace(".", ",")
	return localeInfo.PET_ALBUM_STAT_VALUE % (current, growth)


def SkillSlots(pet_id):
	return [player.GetPetSkillSlotState(pet_id, slot)
		for slot in range(player.PET_SKILL_COUNT_MAX)]
