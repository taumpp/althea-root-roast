# -*- coding: utf-8 -*-
"""Why the market refused a purchase (dávka 8, owner 22. 10.: "dneska mi asi 10 lidí psalo s trhem").

Prod 22. 10.: 11 purchases of 10 players were cancelled before any Yang was taken and a listing bought by someone
else first was refused too - the window only said "Akce se nepovedla (kód 0, N)" and kept the sold offer. Each
refusal now has its own Czech line that says no Yang was taken; a listing that is gone reloads the offers.
Purchases stay in Trh -> Nákupy until the player claims them (owner: no automatic hand-over).
"""


# A purchase the market refused (wire values of market::client_protocol::PurchaseResult). Prod 22. 10.: 11
# purchases were cancelled before any Yang was taken and the window only said "Akce se nepovedla (kód 0, N)";
# a listing bought by someone else first said the same. (key, fallback, reload the offers).
PURCHASE_FAILURES = {
	2: ("VIRTUAL_MARKET_PURCHASE_GONE",
		"Tento předmět už mezitím koupil někdo jiný nebo nabídka skončila. Yang ti nebyl stržen.", True),
	3: ("VIRTUAL_MARKET_PURCHASE_TAKEN",
		"Tento předmět právě kupuje jiný hráč. Yang ti nebyl stržen.", True),
	4: ("VIRTUAL_MARKET_PURCHASE_CHANGED",
		"Prodejce mezitím změnil nabídku. Zkontroluj ji a kup znovu. Yang ti nebyl stržen.", True),
	5: ("VIRTUAL_MARKET_PURCHASE_CHANGED",
		"Prodejce mezitím změnil nabídku. Zkontroluj ji a kup znovu. Yang ti nebyl stržen.", True),
	6: ("VIRTUAL_MARKET_PURCHASE_OWN", "Vlastní nabídku koupit nejde.", False),
	7: ("VIRTUAL_MARKET_PURCHASE_GONE",
		"Tento předmět už mezitím koupil někdo jiný nebo nabídka skončila. Yang ti nebyl stržen.", True),
	8: ("VIRTUAL_MARKET_PURCHASE_BUSY",
		"Nákup se nezdařil: právě probíhá jiná akce s Yangy. Yang ti nebyl stržen, zkus to znovu.", False),
	9: ("VIRTUAL_MARKET_PURCHASE_NO_YANG", "Na tento nákup nemáš dost Yangů.", False),
	10: ("VIRTUAL_MARKET_PURCHASE_GONE",
		"Tento předmět už mezitím koupil někdo jiný nebo nabídka skončila. Yang ti nebyl stržen.", True),
	11: ("VIRTUAL_MARKET_PURCHASE_PENDING", "Předchozí nákup ještě probíhá. Chvíli počkej.", False),
	12: ("VIRTUAL_MARKET_PURCHASE_FAILED", "Nákup se nezdařil, Yang ti nebyl stržen. Zkus to znovu.", False),
}


def PurchaseFailure(result, text):
	"""(message, reload offers) for a refused purchase, or None for an unknown code."""
	entry = PURCHASE_FAILURES.get(int(result))
	if entry is None:
		return None
	key, fallback, reload = entry
	return text(key, fallback), reload
