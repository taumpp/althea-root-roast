ACTION_STACK = "stack"
ACTION_LINK = "link"
ACTION_SPLIT = "split"
ACTION_MARKET = "market"
ACTION_PICK = "pick"

MULTIPLE_SELECT_FLOW_ENABLED = False

# Exorcism Scroll and Concentrated Reading are consumed only by the
# skill reading windows (character and Buffi). Using them directly does nothing.
READING_SUPPORT_VNUMS = (71001, 71094)


def ResolveLeftClick(altPressed, shiftPressed, ctrlPressed):
	if altPressed and shiftPressed:
		return ACTION_STACK
	if altPressed:
		return ACTION_LINK
	if shiftPressed:
		return ACTION_SPLIT
	if ctrlPressed:
		return ACTION_MARKET
	return ACTION_PICK


def IsMultipleSelectEnabled(binaryCapability):
	return bool(binaryCapability and MULTIPLE_SELECT_FLOW_ENABLED)


def IsReadingSupportItem(itemVnum):
	return itemVnum in READING_SUPPORT_VNUMS
