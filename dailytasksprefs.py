# -*- coding: utf-8 -*-
"""Per-character preferences of the Denní úkoly window (uidailytasks), saved like the other per-character UI
preferences under UserData (UserData/daily_tasks/<character>.json, version 1; see targetformprefs).

  tab   the last tab of the R1 switch "Denní úkoly | Řemesla" (uidailytasks.TABS); the window opens on it again.

Reads are cached per character, so Open() reads the file once per character and session; a missing, damaged or
foreign value gives the default (the first tab); a failed write keeps the value for the session (the game never
fails on it). Before the main character is known (an empty name) nothing is read, cached or written. Python 2
and 3; UserData goes through the real open() (builtins.old_open), not the client's pack reader."""
import json
import os

try:
    import builtins as _builtins
except ImportError:                     # Python 2
    import __builtin__ as _builtins


def _Open(path, mode):
    return getattr(_builtins, 'old_open', _builtins.open)(path, mode)

DIR = 'UserData/daily_tasks'
VERSION = 1
_CACHE = {}


def _Name():
    try:
        import player
        name = str(player.GetName())
    except Exception:
        return ''
    if not name or any(ch in name for ch in ('/', '\\', ':', '\x00')) or name in ('.', '..'):
        return ''
    return name


def _Path(name):
    return os.path.join(DIR, name + '.json')


def _Load(name):
    try:
        with _Open(_Path(name), 'rb') as source:
            data = json.loads(source.read(4096).decode('utf-8'))
        if isinstance(data, dict) and data.get('version') == VERSION:
            return dict((key, value) for key, value in data.items() if key != 'version')
    except Exception:
        pass
    return {}


def Get(key, allowed):
    """The stored value of key when it is one of allowed, else allowed[0] (the default)."""
    name = _Name()
    if not name:
        return allowed[0]
    if name not in _CACHE:
        _CACHE[name] = _Load(name)
    value = _CACHE[name].get(key)
    return value if value in allowed else allowed[0]


def Set(key, value):
    name = _Name()
    if not name:
        return False
    values = _CACHE.setdefault(name, _Load(name))
    if values.get(key) == value:
        return True                     # nothing new: no write
    values[key] = value
    try:
        if not os.path.isdir(DIR):
            os.makedirs(DIR)
        data = dict(values, version=VERSION)
        temporary = _Path(name) + '.tmp'
        with _Open(temporary, 'wb') as target:
            target.write(json.dumps(data, sort_keys=True).encode('utf-8'))
        if os.path.exists(_Path(name)):
            os.remove(_Path(name))
        os.rename(temporary, _Path(name))
        return True
    except Exception:
        return False


def Forget():
    """Drops the cache (a relog reads the files again)."""
    _CACHE.clear()
