# Public wardrobe catalogue policy.
#
# "validated" exposes every client costume prototype that passes the renderer,
# race and asset checks in uiwardrobe.py.  Switch to "allowlist" when a future
# live season needs a strictly curated catalogue without changing UI code.
PUBLIC_CATALOG_MODE = "validated"

# These sets are intentionally data-only.  They are the small, reviewable
# exception layer over the authoritative client item_proto catalogue.
PUBLIC_VNUM_ALLOWLIST = frozenset()
# ALTHEA-633 (owner 2026-10-02): Shining Weapon 27 is a Ghost of Samurai costume glow that
# references a missing texture (white quads) and is not sold or dropped anywhere.
# 65228, 65231 and 65067 have no shining effect or icon (no free effect set left for them).
PUBLIC_VNUM_DENYLIST = frozenset((65226, 65228, 65231, 65067))


def IsPublicVnum(vnum):
	vnum = int(vnum)
	if vnum in PUBLIC_VNUM_DENYLIST:
		return False
	if PUBLIC_CATALOG_MODE == "allowlist":
		return vnum in PUBLIC_VNUM_ALLOWLIST
	return True
