"""Per-character presentation only; never persist bonus levels or timers here."""
import hashlib
import io
import json
import os
import tempfile

BASE_PATH = 'UserData/passive_hud'


def clamp(position, size, screen):
    return tuple(max(0, min(int(p), max(0, s - n)))
                 for p, n, s in zip(position, size, screen))


def _path(character, directory):
    if not isinstance(character, str) or not character:
        return None
    return os.path.join(directory, hashlib.sha256(character.encode('utf-8')).hexdigest() + '.json')


def load(character, directory=BASE_PATH):
    try:
        path = _path(character, directory)
        if not path:
            return None
        with io.open(path, 'rb') as stream:
            raw = stream.read(4097)
        if len(raw) > 4096:
            return None
        record = json.loads(raw.decode('utf-8'))
        if not isinstance(record, dict) or type(record.get('version')) is not int or record['version'] != 1:
            return None
        if any(type(record.get(key)) is not int for key in ('x', 'y')):
            return None
        return (record['x'], record['y'])
    except (OSError, ValueError, TypeError, RecursionError):
        return None


def save(character, position, directory=BASE_PATH):
    temporary = None
    try:
        path = _path(character, directory)
        if not path:
            return False
        x, y = position
        if type(x) is not int or type(y) is not int:
            return False
        data = json.dumps({'version': 1, 'x': x, 'y': y}).encode('utf-8')
        os.makedirs(directory, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.passive-', suffix='.tmp', dir=directory)
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        return True
    except (OSError, ValueError, TypeError):
        return False
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
