# -*- coding: utf-8 -*-
#
# Item Shop body-part chests: chest VNUM -> contents by rarity
# tier. A chest gives exactly one of them; the chances stay on the server and are
# never shown. Rare and uncommon items are chest-only and tradable.
CHESTS = {
	762500: {"key": 'body', "common": (762028, 762037, 762084, 760408, 760420, 760001, 760414, 762019, 760418, 760424), "uncommon": (), "rare": (760422, 762055, 762093)},
	762501: {"key": 'hair', "common": (762020, 762029, 762038, 762085, 760409, 760421, 760007, 760415, 760419, 760425), "uncommon": (), "rare": (760423, 762056, 762094)},
	762502: {"key": 'mount', "common": (71327, 71311, 71317, 71338, 71318, 71326, 71330, 71343), "uncommon": (71325,), "rare": (71328, 71344, 71345, 71346)},
	762503: {"key": 'weapon', "common": (762510, 762511, 762512, 762513, 762514, 762515, 762516, 762519, 762518), "uncommon": (762521,), "rare": (762517, 762520)},
	762504: {"key": 'sash', "common": (86200, 86201, 86203, 86204, 86206, 86207, 86208, 86210, 86211, 86212, 86214, 86215, 86218, 86219, 86222, 86223, 86225, 86226), "uncommon": (), "rare": (86221, 86216, 86217, 86209, 86213, 86202, 86220, 86224)},
}

# tier -> (Czech name, English name, text colour)
TIERS = {
	'common': ('Běžné', 'Common', 0xffd8d8d8),
	'uncommon': ('Neobvyklé', 'Uncommon', 0xff5fb8ff),
	'rare': ('Vzácné', 'Rare', 0xffd30d0e),
}
TIER_ORDER = ("rare", "uncommon", "common")


def IsChest(vnum):
	try:
		return int(vnum) in CHESTS
	except (TypeError, ValueError):
		return False


def Contents(vnum):
	"""[(tier, (vnum, ...)), ...] rarest first, empty tiers left out; None for other items."""
	chest = CHESTS.get(vnum) if IsChest(vnum) else None
	if not chest:
		return None
	return [(tier, chest[tier]) for tier in TIER_ORDER if chest[tier]]


def ChestsFirst(offers, vnumIndex=1):
	"""Item Shop offers with the chests first (owner: a chest leads its tab); order kept otherwise."""
	return [o for o in offers if IsChest(o[vnumIndex])] + [o for o in offers if not IsChest(o[vnumIndex])]
