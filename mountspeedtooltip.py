import bonuscatalog

# The valid stored speed roll range is server data (switchbot_catalog_v1.json
# mount_speed.roll_range, sent in the bonus catalog, ALTHEA-647). Until the
# catalog arrives any positive roll is shown; the server ignores values
# outside its range.
FALLBACK_MAXIMUM_ROLL = 32767


def RollRange():
	catalog = bonuscatalog.Current()
	if catalog and catalog.mountSpeedMaximum:
		return catalog.mountSpeedMinimum, catalog.mountSpeedMaximum
	return 1, FALLBACK_MAXIMUM_ROLL


def IsValidRoll(value):
	minimum, maximum = RollRange()
	return minimum <= value <= maximum


def FormatAffect(
	is_costume_mount,
	affect_type,
	affect_value,
	move_speed_type,
	mount_formatter,
	default_formatter,
):
	formatter = default_formatter
	if is_costume_mount and affect_type == move_speed_type:
		formatter = mount_formatter
	text = formatter(affect_value)
	# Most bonus formats are "+%d"; a negative fixed apply (ALTHEA-648) shows one sign.
	if affect_value < 0:
		text = text.replace("+-", "-")
	return text


def FindValidSpeedRoll(attr_slot, move_speed_type):
	for affect_type, affect_value in attr_slot or ():
		if (
			affect_type == move_speed_type
			and IsValidRoll(affect_value)
		):
			return affect_value
	return 0


def FilterPrototypeAffects(
	is_costume_mount, prototype_affects, attr_slot, move_speed_type
):
	affects = list(prototype_affects)
	if not is_costume_mount:
		return affects
	if not FindValidSpeedRoll(attr_slot, move_speed_type):
		return affects
	return [
		affect
		for affect in affects
		if affect[0] != move_speed_type
	]


def FilterMountAttributes(attr_slot, move_speed_type):
	"""Keep only the first valid seal speed roll; historical combat attrs are inert."""
	if not attr_slot:
		return attr_slot
	result = []
	kept = False
	for kind, value in attr_slot:
		if not kept and kind == move_speed_type and IsValidRoll(value):
			result.append((kind, value))
			kept = True
		else:
			result.append((0, 0))
	return result
