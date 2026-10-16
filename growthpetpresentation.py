"""Shared labels and visible skill slots for growth-pet UI."""

import localeInfo
import player


def ThirdBonusLabel(pet_type):
	if int(pet_type) % 2:
		return localeInfo.PET_TOOLTIP_HUMAN
	return localeInfo.PET_TOOLTIP_MONSTER


def ThirdAppliedPercent(value):
	# Server POINT_ATTBONUS_* stores integer percentages.
	return float(int(value))


def SkillSlots(pet_id):
	return [player.GetPetSkillSlotState(pet_id, slot)
		for slot in range(player.PET_SKILL_COUNT_MAX)]
