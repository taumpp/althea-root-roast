GREEN_POTION_VNUMS = (
	27053, 27100, 27101, 27102, 27110, 27111, 27112, 27123,
	27207, 27208, 27209, 91053,
)

DEFAULT_CATALOG_VNUMS = (
	27866, 27868, 27870, 27873, 27880, 27881,
	71050,
	71044, 71045,
	71027, 71028, 71029, 71030,
	50830, 50831, 50832,
) + GREEN_POTION_VNUMS


def CookedFishVnums(cookedFishBuffs):
	vnums = []
	for affect, ordinary, improved, apply in cookedFishBuffs:
		vnums.extend((ordinary, improved))
	return tuple(vnums)


def DewAffects(dews):
	affects = {}
	for dew in dews:
		for tier in range(len(dew["values"])):
			affects[dew["first_vnum"] + tier] = dew["affect"]
	return affects


def AllowedVnums(cookedFishBuffs, dews):
	return frozenset(
		DEFAULT_CATALOG_VNUMS + CookedFishVnums(cookedFishBuffs) + tuple(DewAffects(dews))
	)


EXCLUDED_CATALOG_VNUMS = frozenset((72355, 72356, 72756))
