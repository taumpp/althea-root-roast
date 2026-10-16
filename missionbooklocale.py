"""Locale-backed strings; common English fallback for untranslated clients."""
import app
import localeInfo

_strings = {}
localeInfo.LoadLocaleFile("locale/common/mission_books.txt", _strings)
if app.GetLocalePath().rstrip("/") == "locale/cz":
    localeInfo.LoadLocaleFile("locale/cz/mission_books.txt", _strings)


def Text(key):
    return _strings[key]
