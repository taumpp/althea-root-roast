LEGACY_LAYOUT = (1, 5, 9, 45)
EXPANDED_LAYOUT = (2, 8, 8, 64)


def GetLayout(safebox):
	getterNames = (
		"GetLayoutVersion",
		"GetSlotXCount",
		"GetSlotYCount",
		"GetPageSize",
	)
	hasRuntimeLayout = all(
		hasattr(safebox, getterName) for getterName in getterNames
	)
	if hasRuntimeLayout:
		layout = (
			safebox.GetLayoutVersion(),
			safebox.GetSlotXCount(),
			safebox.GetSlotYCount(),
			safebox.GetPageSize(),
		)
	else:
		layout = (
			1,
			safebox.SAFEBOX_SLOT_X_COUNT,
			safebox.SAFEBOX_SLOT_Y_COUNT,
			safebox.SAFEBOX_PAGE_SIZE,
		)

	if layout[0] not in (1, 2) or layout[1] <= 0 or layout[2] <= 0:
		raise ValueError("invalid safebox layout")
	if layout[3] != layout[1] * layout[2]:
		raise ValueError("invalid safebox layout")

	sizeGetterNames = ("GetCurrentSafeboxSize", "GetMallSize")
	if (
		hasRuntimeLayout and
		layout == LEGACY_LAYOUT and
		all(hasattr(safebox, getterName) for getterName in sizeGetterNames) and
		safebox.GetCurrentSafeboxSize() == 0 and
		safebox.GetMallSize() == 0
	):
		# Sizes are allocated cell counts, not populated item counts. An open
		# snapshot allocates at least one page even when it contains no items,
		# so zero for both providers means that no snapshot has arrived yet.
		# This changes presentation only; native layout and capacity stay intact.
		return EXPANDED_LAYOUT

	return layout
