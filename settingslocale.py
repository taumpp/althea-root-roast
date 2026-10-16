"""Settings A strings: Czech/English fallback, overridable by locale tables."""
import re
import app
import localeInfo


def Text(czech, english):
    key = 'SETTINGS_A_' + re.sub('[^A-Z0-9]+', '_', english.upper()).strip('_')
    czech_locale = app.GetLocalePath().replace('\\', '/').lower().endswith('/cz')
    return getattr(localeInfo, key, czech if czech_locale else english)
