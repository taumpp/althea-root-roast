# Name policies shared by character create/rename and Guild V2.
# Existing names stay valid lookup targets and are never revalidated here.
CHARACTER_MAX_BYTES = 16
GUILD_MAX_BYTES = 12

# Guild V2 names: the looser UTF-8/spacing rule (server text_name_policy.h).
def valid(value, maximum):
    if not isinstance(value, str) or not value:
        return False
    try:
        encoded = value.encode("utf-8", "strict")
    except UnicodeError:
        return False
    return (len(encoded) <= maximum and value == value.strip(" ") and
            "  " not in value and "|" not in value and
            all(ord(c) >= 32 and ord(c) != 127 for c in value))

# New character names: exact mirror of server-src common/player_name_policy.h.
# Only ASCII letters/digits, the thirty Czech letters (the set the server
# profanity blacklist folds) and "- _ .". Every allowed letter is precomposed,
# so an accepted name is always NFC; decomposed accents are refused. Escapes
# keep this module ASCII and independent of unicodedata.
CHARACTER_OK = None
CHARACTER_FORMAT = "format"
CHARACTER_RESERVED = "reserved"

_CZECH_FOLD = {
    u"\u00c1": "a", u"\u00e1": "a", u"\u010c": "c", u"\u010d": "c",
    u"\u010e": "d", u"\u010f": "d", u"\u00c9": "e", u"\u00e9": "e",
    u"\u011a": "e", u"\u011b": "e", u"\u00cd": "i", u"\u00ed": "i",
    u"\u0147": "n", u"\u0148": "n", u"\u00d3": "o", u"\u00f3": "o",
    u"\u0158": "r", u"\u0159": "r", u"\u0160": "s", u"\u0161": "s",
    u"\u0164": "t", u"\u0165": "t", u"\u00da": "u", u"\u00fa": "u",
    u"\u016e": "u", u"\u016f": "u", u"\u00dd": "y", u"\u00fd": "y",
    u"\u017d": "z", u"\u017e": "z",
}
_ASCII_LETTERS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
_DIGITS = "0123456789"
_PUNCTUATION = "-_."
_STAFF_TAGS = ("gm", "sa", "ga", "tm", "adm", "mod")
_RESERVED_WORDS = ("admin", "gamemaster", "moderator", "system", "staff", "support", "althea")


def _reserved(value, folded):
    if folded.startswith("gm") or "GM" in value:
        return True
    letters = 0
    while letters < len(folded) and folded[letters] in _ASCII_LETTERS:
        letters += 1
    if folded[:letters] in _STAFF_TAGS:
        return True
    compact = "".join(c for c in folded if c not in _PUNCTUATION)
    return any(compact.startswith(word) for word in _RESERVED_WORDS)


def character_error(value):
    """Return CHARACTER_OK, CHARACTER_FORMAT or CHARACTER_RESERVED."""
    if not isinstance(value, str) or not value:
        return CHARACTER_FORMAT
    try:
        size = len(value.encode("utf-8", "strict"))
    except UnicodeError:
        return CHARACTER_FORMAT
    if size > CHARACTER_MAX_BYTES:
        return CHARACTER_FORMAT
    folded = []
    previous = "punctuation"
    for c in value:
        if c in _ASCII_LETTERS:
            kind, base = "letter", c.lower()
        elif c in _DIGITS:
            kind, base = "digit", c
        elif c in _PUNCTUATION:
            kind, base = "punctuation", c
        elif c in _CZECH_FOLD:
            kind, base = "letter", _CZECH_FOLD[c]
        else:
            return CHARACTER_FORMAT
        if not folded and kind != "letter":
            return CHARACTER_FORMAT
        if kind == "punctuation" and previous == "punctuation":
            return CHARACTER_FORMAT
        previous = kind
        folded.append(base)
    if previous == "punctuation":
        return CHARACTER_FORMAT
    return CHARACTER_RESERVED if _reserved(value, "".join(folded)) else CHARACTER_OK


def valid_character(value):
    return character_error(value) is CHARACTER_OK


def character_message(locale, error, fallback):
    """Localized popup for a refused character name (Czech defines both keys)."""
    key = "CHARACTER_NAME_RESERVED" if error == CHARACTER_RESERVED else "CHARACTER_NAME_INVALID"
    return getattr(locale, key, fallback)
