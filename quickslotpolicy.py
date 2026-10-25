import item
import player
import skill
import slotwindowpolicy


QUICK_SLOT_UNKNOWN = 0
QUICK_SLOT_ALLOWED = 1
QUICK_SLOT_DENIED = 2


# Passive skills (skilldesc PASSIVE: riding, mining, fishing, languages, dew mastery...) cannot be used,
# so they never belong on the taskbar; a stored one is removed on the next refresh. A skill slot the
# client cannot resolve yet (index 0, missing skill data) waits without deleting anything.
def _GetSkillQuickSlotState(slotPosition):
	try:
		skillIndex = player.GetSkillIndex(slotPosition)
	except RuntimeError:
		return QUICK_SLOT_UNKNOWN
	if skillIndex <= 0:
		return QUICK_SLOT_UNKNOWN

	try:
		canUse = skill.CanUseSkill(skillIndex)
	except RuntimeError:
		return QUICK_SLOT_UNKNOWN

	if canUse:
		return QUICK_SLOT_ALLOWED
	return QUICK_SLOT_DENIED


def GetQuickSlotState(slotType, slotPosition):
	slotType = slotwindowpolicy.NormalizeSlotType(slotType)
	if slotType == player.SLOT_TYPE_SKILL:
		return _GetSkillQuickSlotState(slotPosition)

	if slotType != player.SLOT_TYPE_INVENTORY:
		return QUICK_SLOT_DENIED

	itemVnum = player.GetItemIndex(slotPosition)
	if itemVnum <= 0:
		return QUICK_SLOT_UNKNOWN

	try:
		canAdd = item.CanAddToQuickSlotItem(itemVnum)
	except RuntimeError:
		return QUICK_SLOT_UNKNOWN

	if canAdd:
		return QUICK_SLOT_ALLOWED
	return QUICK_SLOT_DENIED


def CanRegisterQuickSlot(slotType, slotPosition):
	return GetQuickSlotState(slotType, slotPosition) == QUICK_SLOT_ALLOWED


def ReconcileStoredQuickSlot(
		slotType,
		slotPosition,
		globalSlotIndex,
		pendingDeletes):
	if slotType == player.SLOT_TYPE_NONE:
		pendingDeletes.discard(globalSlotIndex)
		return False

	state = GetQuickSlotState(slotType, slotPosition)
	if state == QUICK_SLOT_DENIED:
		if globalSlotIndex not in pendingDeletes:
			pendingDeletes.add(globalSlotIndex)
			player.RequestDeleteGlobalQuickSlot(globalSlotIndex)
		return False

	if state == QUICK_SLOT_ALLOWED:
		pendingDeletes.discard(globalSlotIndex)
		return True

	return False
