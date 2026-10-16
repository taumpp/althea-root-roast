# -*- coding: utf-8 -*-
"""Localized reasons for refused switchbot starts (ALTHEA-647).

The server answers every refused /switchbot_run and /switchbot_instant_run with
`SwitchbotRefusedV1 <slot|instant> <slot or cell> <CODE> <first> <second>`.
Codes are append-only server tokens; an unknown future code falls back to a
generic message that still names it. Texts live in
locale/common/switchbot_refusals.txt (English fallback) and the Czech override
locale/cz/switchbot_refusals.txt, both UTF-8.
"""
import app
import localeInfo

# Which numeric argument a message formats: None, 'first' or 'second'.
CODES = {
	'MALFORMED': None,
	'DUPLICATE': None,
	'NO_TARGET': None,
	'SLOT_LOCKED': None,
	'BUSY': None,
	'ITEM_MISSING': None,
	'ITEM_BUSY': None,
	'ITEM_SEALED': None,
	'ITEM_PROTECTED': None,
	'SCROLL_UNKNOWN': None,
	'SCROLL_MISMATCH': None,
	'BONUS_UNKNOWN': None,
	'VALUE_TOO_HIGH': 'second',
	'TOO_MANY': 'first',
	'ELEMENTAL': 'first',
	'ADDON': None,
	'ALREADY_MATCHED': None,
	'NO_SCROLL': None,
	'COUNT_CHANGED': 'first',
	'NO_YANG': 'first',
	'LEGACY': None,
}
FALLBACK = 'UNKNOWN'

_strings = {}


def _Load():
	if _strings:
		return _strings
	loaded = {}
	localeInfo.LoadLocaleFile("locale/common/switchbot_refusals.txt", loaded)
	if app.GetLocalePath().rstrip("/") == "locale/cz":
		localeInfo.LoadLocaleFile("locale/cz/switchbot_refusals.txt", loaded)
	_strings.update(loaded)
	return _strings


def _Number(value):
	try:
		return int(value)
	except (TypeError, ValueError):
		return 0


def _Money(value):
	try:
		return localeInfo.NumberToMoneyString(value)
	except Exception:
		return str(value)


def Message(code, first=0, second=0):
	"""The chat line for one refusal; never raises for unknown input."""
	strings = _Load()
	code = str(code)
	if code not in CODES or code not in strings:
		return strings[FALLBACK] % code
	argument = CODES[code]
	if argument is None:
		return strings[code]
	value = _Number(first if argument == 'first' else second)
	return strings[code] % (_Money(value) if code == 'NO_YANG' else value)
