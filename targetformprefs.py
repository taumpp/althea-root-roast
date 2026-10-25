# -*- coding: utf-8 -*-
"""Per-character preferences of the unified target form (uitargetform), saved like the other per-character UI
preferences under UserData (UserData/targetform/<character>.json, version 1).

  dps_auto   1 (default) / 0: the header's "DPS" switch. ON = the DPS section opens by itself on your first hit of
             a fight; OFF = it stays closed for every target, fight and relog until the player switches it ON.
             (The Settings row "Ukazatel poškození (DPS)" is a separate master switch of the whole tracker.)

Reads are cached per character; a missing or damaged file gives the defaults; a failed write keeps the value for
the session (the game never fails on it). Python 2 and 3.

The client replaces the builtin open() with its pack reader (the real one stays as builtins.old_open, see
settingsbackend.REAL_OPEN): this module reads and writes UserData through the real one. Before the main character
is known (login, character select: an empty name) nothing is read, cached or written for a character, so the
defaults of that phase never stand for the character later."""
import json
import os

try:
    import builtins as _builtins
except ImportError:                     # Python 2
    import __builtin__ as _builtins


def _Open(path, mode):
    """The real file open (the client's pack reader cannot read or write UserData)."""
    return getattr(_builtins, 'old_open', _builtins.open)(path, mode)

DIR = 'UserData/targetform'
DEFAULTS = {'dps_auto': 1}
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
    values = dict(DEFAULTS)
    if name:
        try:
            with _Open(_Path(name), 'rb') as source:
                data = json.loads(source.read(4096).decode('utf-8'))
            if isinstance(data, dict) and data.get('version') == 1:
                for key, default in DEFAULTS.items():
                    if key in data:
                        values[key] = int(bool(data[key]))
        except Exception:
            pass
    return values


def Get(key):
    name = _Name()
    if not name:
        return DEFAULTS.get(key)            # no character yet: the default, nothing cached
    if name not in _CACHE:
        _CACHE[name] = _Load(name)
    return _CACHE[name].get(key, DEFAULTS.get(key))


def Set(key, value):
    name = _Name()
    if not name:
        return False                        # no character yet: nothing to keep
    values = _CACHE.setdefault(name, _Load(name))
    values[key] = int(bool(value))
    try:
        if not os.path.isdir(DIR):
            os.makedirs(DIR)
        data = dict(values, version=1)
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
