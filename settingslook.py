# -*- coding: utf-8 -*-
"""Look of the settings window (c9 v4 2026-10-05, settings v5 the same evening).

UserData/settings-look.json = {"look": "c9" | "legacy", "row_icons": false | true,
                               "channel_bar_style": "stepper" | "list"}
  look       c9 (default) = new window (root/uisettingsc9.py); legacy = the original Settings A7 window.
  row_icons  icons in front of the options (Rozhraní › Vzhled nastavení); off by default (owner, v5) - the labels
             then start on the left axis. The sidebar group icons stay either way.
  channel_bar_style  the R1 channel bar (root/uichannelbarr1.py): stepper "‹ CH 3 ›" (default) or the list with
             the load of every channel; "Starý vzhled" (look legacy) keeps the original bar either way.
The font is no longer a choice (v5: Spectral only); a "font_set" key from the c9 v4 trial is ignored. The Tahoma
fallback for an older EXE is automatic (uikit.FontSet).
Presentation only: a missing, unreadable or invalid file means the defaults, a failed write keeps the previous file
and the in-memory choice.

ALLOW_LEGACY_TOGGLE (owner 9. 10. 2026, "zatím"): players get no "Starý vzhled" switch - the R1 Settings footer button
and the Vzhled nastavení row are not built. A file that still says "legacy" is moved to "c9" once when it is read
(one syserr line). The legacy code paths stay (the look 'legacy' set in code, every window's original look and the
fallback of a failed R1 build, uir1.TraceFailure): True brings the switch back.
"""
import builtins
import json
import os
import tempfile

PATH = 'UserData/settings-look.json'
DEFAULTS = {'look': 'c9', 'row_icons': False, 'channel_bar_style': 'stepper'}
CHOICES = {'look': ('c9', 'legacy'), 'row_icons': (False, True), 'channel_bar_style': ('stepper', 'list')}
REAL_OPEN = getattr(builtins, 'old_open', builtins.open)
ALLOW_LEGACY_TOGGLE = False
_cache = None


def _valid(key, value):
    allowed = CHOICES[key]
    return type(value) is type(allowed[0]) and value in allowed


def _normalized(data):
    result = dict(DEFAULTS)
    if isinstance(data, dict):
        for key in CHOICES:
            if _valid(key, data.get(key)):
                result[key] = data[key]
    return result


def Load(refresh=False):
    global _cache
    if _cache is None or refresh:
        try:
            with REAL_OPEN(PATH, 'rb') as source:
                _cache = _normalized(json.loads(source.read().decode('utf-8')))
        except (OSError, ValueError, TypeError):
            _cache = dict(DEFAULTS)
        if _cache['look'] == 'legacy' and not ALLOW_LEGACY_TOGGLE:
            _MigrateLegacy()
    return dict(_cache)


def _MigrateLegacy():
    """The stored "Starý vzhled" while players have no switch back (ALLOW_LEGACY_TOGGLE False): the new look, written
    back once, one syserr line. A failed write keeps the new look in memory (and migrates again on the next start)."""
    written = Set('look', 'c9')
    try:
        import dbg
        dbg.TraceError('settings look: the stored "legacy" look was moved to "c9" (no Stary vzhled switch for players, '
                       'settingslook.ALLOW_LEGACY_TOGGLE)%s' % ('' if written else '; the file could not be written'))
    except Exception:
        pass
    return written


def Get(key):
    """One choice; a key an older cache does not have yet gives its default."""
    return Load().get(key, DEFAULTS.get(key))


def Set(key, value):
    """Store one choice; returns True when the file was written."""
    global _cache
    if key not in CHOICES or not _valid(key, value):
        raise ValueError('invalid %s' % key)
    data = Load()
    data[key] = value
    _cache = dict(data)
    try:
        directory = os.path.dirname(PATH)
        if directory:
            os.makedirs(directory, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.settings-look-', suffix='.tmp', dir=directory or '.')
        try:
            with os.fdopen(descriptor, 'wb') as target:
                target.write(json.dumps(data, sort_keys=True).encode('utf-8'))
            os.replace(temporary, PATH)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    except (OSError, ValueError, TypeError):
        return False
    return True
