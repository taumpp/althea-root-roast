"""Per-PC storage of the configurable button panels (Settings -> Panely tlačítek).

One file, ``UserData/button-panels.json``, holds one section per panel::

    {"version": 1,
     "minimap":   {"slots": [...], "hidden": [...]},
     "inventory": {...}}

Each panel owns only its section; writing one section keeps the others. A
section that equals the panel default is removed, and the file is removed
when no section is left, so a player who never customised anything follows
future defaults. Like ``UserData/keybindings.cfg`` it is presentation only:
no server state, nothing per character.

Forward compatibility (audit 2026-10-04, 1.2-1.4):

* A file of a newer version is never overwritten: this client shows the
  sections it can read and refuses every write (``LastError() ==
  ERROR_NEWER``), so a pack rollback cannot destroy a newer client's layout.
  A newer version should therefore keep ``version`` and, where it can, these
  sections readable for older clients.
* Keys this client does not know (sections of future panels, future fields)
  are written back unchanged.
* A broken or foreign file is replaced, but kept as ``button-panels.json.bak``.
* Functions stored in a section but not offered now (a feature flag, a missing
  callback, more channels than today) are kept by the panels on save
  (``KeepUnavailable``), so switching a feature off for a while never deletes
  it from a player's layout.
* Writes never raise: they return False and leave the reason in
  ``LastError()`` (a full disk, read-only ``UserData`` or a second client
  holding the file), so an in-game click can never break the UI callback.
"""
import json
import os
import shutil
import tempfile

try:
    import builtins
except ImportError:
    import __builtin__ as builtins

STORE_VERSION = 1
STORE_RELATIVE_PATH = os.path.join('UserData', 'button-panels.json')
MAX_FILE_BYTES = 32768
_REAL_OPEN = getattr(builtins, 'old_open', builtins.open)

ERROR_NEWER = 'newer'
ERROR_IO = 'io'
_last_error = [None]


def _path(path):
    return path or STORE_RELATIVE_PATH


def LastError():
    """Why the last write failed (``ERROR_NEWER`` / ``ERROR_IO``), or None."""
    return _last_error[0]


def ReadJson(path):
    """A small JSON object from disk, or None when absent, oversized or invalid."""
    try:
        with _REAL_OPEN(path, 'rb') as source:
            raw = source.read(MAX_FILE_BYTES + 1)
        if len(raw) > MAX_FILE_BYTES:
            return None
        value = json.loads(raw.decode('utf-8'))
    except (OSError, IOError, ValueError, TypeError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _version(value):
    version = value.get('version') if value else None
    return version if isinstance(version, int) and not isinstance(version, bool) else None


def _Load(path):
    """(document without 'version', writable, keep a backup before writing)."""
    value = ReadJson(path)
    version = _version(value)
    if version is None or version < STORE_VERSION:
        # Absent, broken or foreign: start empty; an existing file is kept as .bak.
        return {}, True, os.path.exists(path)
    document = dict((key, item) for key, item in value.items() if key != 'version')
    return document, version == STORE_VERSION, False


def ReadAll(path=None):
    """Every readable section ({panel: dict}), also from a newer file."""
    document = _Load(_path(path))[0]
    return dict((key, section) for key, section in document.items() if isinstance(section, dict))


def ReadSection(section, path=None):
    """The stored section (dict), or None when the panel uses its default."""
    return ReadAll(path).get(section)


def IsReadOnly(path=None):
    """True when a newer client wrote the file (shown, never overwritten)."""
    return not _Load(_path(path))[1]


def _atomic_write(path, data):
    directory = os.path.dirname(path)
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    descriptor, temporary = tempfile.mkstemp(prefix='.button-panels-', suffix='.tmp', dir=directory or '.')
    try:
        with os.fdopen(descriptor, 'wb') as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def WriteSection(section, value, path=None):
    """Store one section; ``None`` removes it (the panel follows its default).

    Returns False (see ``LastError``) instead of raising; a newer file is never written.
    """
    _last_error[0] = None
    path = _path(path)
    document, writable, backup = _Load(path)
    if value is None and section not in document:
        return True
    if not writable:
        _last_error[0] = ERROR_NEWER
        return False
    if value is None:
        document.pop(section, None)
    else:
        document[section] = value
    try:
        if backup:
            shutil.copyfile(path, path + '.bak')
        if not document:
            if os.path.exists(path):
                os.remove(path)
            return True
        document['version'] = STORE_VERSION
        _atomic_write(path, json.dumps(document, sort_keys=True).encode('utf-8'))
    except (OSError, IOError, ValueError, TypeError):
        _last_error[0] = ERROR_IO
        return False
    return True


# Temporarily unavailable functions (audit 1.2) ------------------------------------
MAX_KEPT = 64
MAX_ID_LENGTH = 64


def Unavailable(stored, known_ids):
    """Function IDs of a stored list that this client does not offer right now."""
    known = set(known_ids)
    result = []
    if not isinstance(stored, (list, tuple)):
        return result
    for action in stored:
        if (isinstance(action, str) and action and len(action) <= MAX_ID_LENGTH and action not in known
                and action not in result and len(result) < MAX_KEPT):
            result.append(action)
    return result


def KeepUnavailable(ids, stored, known_ids):
    """``ids`` with the unavailable functions of ``stored`` put back at their stored
    positions; the game and Settings skip them until they are offered again."""
    keep = set(Unavailable(stored, known_ids))
    result = [action for action in ids if action not in keep]
    if not keep:
        return result
    for index, action in enumerate(stored):
        if action in keep:
            keep.discard(action)
            result.insert(min(index, len(result)), action)
    return result
