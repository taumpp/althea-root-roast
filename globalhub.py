GLOBAL_HUB_CHANNEL = 0
GLOBAL_HUB_MAP_INDEX = 1


def IsGlobalHub(channel_number, map_index):
	try:
		channel_number = int(channel_number)
		map_index = int(map_index)
	except (TypeError, ValueError):
		return False
	return (
		channel_number == GLOBAL_HUB_CHANNEL
		and map_index == GLOBAL_HUB_MAP_INDEX
	)
