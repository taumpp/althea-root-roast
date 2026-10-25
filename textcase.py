# -*- coding: utf-8 -*-
"""Letter case of player-facing names built from longer texts (Python 2 and 3).

CapitalFirst: a name cut out of a value-first tooltip string ("%d%% šance odrazit přímý tělesný útok" without its
value) starts with a lower-case letter, unlike its neighbours ("Šance odvrátit tělesný útok"); the bonus lists show
every name with a capital first letter.
"""


def CapitalFirst(text, encoding='cp1250'):
    """``text`` with its first letter in upper case ("šance ..." -> "Šance ...", "čas" -> "Čas"), Czech diacritics
    included; everything else unchanged, as is a text that starts with a digit or a sign ("+15% šance").

    A Python 3 str is changed directly. A byte string (the locale text of a Python 2 client) is decoded with
    ``encoding`` (the Czech locale: cp1250), changed and encoded back; it is returned unchanged when it is not
    valid in that code page."""
    if not text:
        return text
    if isinstance(text, bytes):
        try:
            decoded = text.decode(encoding)
            changed = CapitalFirst(decoded, encoding)
            return changed.encode(encoding) if changed != decoded else text
        except (UnicodeError, LookupError):
            return text
    for index, char in enumerate(text):
        if char.isspace():
            continue
        upper = char.upper()
        if len(upper) != 1 or upper == char:          # not a letter, already upper case, or no single capital (ß)
            return text
        return text[:index] + upper + text[index + 1:]
    return text


# Czech letters (and the other Latin letters of cp1250) -> their base letter. A plain table: the embedded client has
# no unicodedata (importing it aborts the interface, see craftingmodel), the same reason as marketfilters.folded.
_FOLD_GROUPS = ((u'a', u'áäàâãåąă'), (u'c', u'čćç'), (u'd', u'ďđ'), (u'e', u'éěëèêę'), (u'i', u'íïìî'),
                (u'l', u'ĺľł'), (u'n', u'ńňñ'), (u'o', u'óöòôõő'), (u'r', u'ŕř'), (u's', u'šśş'), (u't', u'ťţ'),
                (u'u', u'úůüùûű'), (u'y', u'ýÿ'), (u'z', u'žźż'))
_FOLD = dict((accent, base) for base, letters in _FOLD_GROUPS for accent in letters)


def SearchKey(text, encoding='cp1250'):
    """The search key of a player-facing name: lower case without diacritics ("Síla větru" -> "sila vetru"), so
    a query typed with or without the accents finds the same rows ("ve", "vě", "VĚ" all find "větru"). Use it on
    the query AND on the searched name.

    A Python 3 str is folded directly. A byte string (the locale text of a Python 2 client) is decoded with
    ``encoding`` (the Czech locale: cp1250) first; the key is always a text (unicode), so a byte name and a str
    query compare. A byte string that is not valid in that code page is only lower-cased."""
    if not text:
        return u''
    if isinstance(text, bytes):
        try:
            text = text.decode(encoding)
        except (UnicodeError, LookupError):
            text = text.decode('latin-1')
    return u''.join(_FOLD.get(char, char) for char in text.lower() if not 0x300 <= ord(char) <= 0x36f)
