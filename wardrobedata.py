# Public wardrobe catalogue policy (data: tools/data/wardrobe_public_catalog.json).
#
# The denylist takes precedence over a live Item Shop offer.
# Other supported costumes with a live Item Shop offer are listed by uiwardrobe.
# Any other costume is listed with the "ve hre" label only when IsPublicVnum lets it through:
# "allowlist" = only costumes a player can really obtain in the game,
# "validated" = every client costume prototype that passes the renderer, race and asset checks.
PUBLIC_CATALOG_MODE = "allowlist"

# Obtainable in the game (drop, chest, cube, quest); the source of each VNUM is in the manifest.
PUBLIC_VNUM_ALLOWLIST = frozenset((85001, 85002, 85003, 85004, 85015, 85016, 85017, 85018,))
# Always hidden: retired Andun Glory, removed pets, incomplete wings and broken glows.
PUBLIC_VNUM_DENYLIST = frozenset((44510, 44511, 44512, 44513, 44514, 44515, 44516, 44517, 44518, 44519, 44520, 86124, 760002, 760008, 760026, 760027, 760028, 760029, 760030, 760031, 760032, 760108, 760109, 760110, 760111, 760132, 760133, 760134, 760135, 760176, 760177, 760178, 760179, 760180, 760181, 760182, 760183, 760184, 760185, 760186, 760187, 760188, 760189, 65226, 65228, 65231, 65067, 53016, 53017, 53020, 86205,))


def IsPublicVnum(vnum):
	vnum = int(vnum)
	if vnum in PUBLIC_VNUM_DENYLIST:
		return False
	if PUBLIC_CATALOG_MODE == "allowlist":
		return vnum in PUBLIC_VNUM_ALLOWLIST
	return True
