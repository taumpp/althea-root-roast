"""Mission catalog mirror and server-authoritative active mission state."""
import builtins
import hashlib
import json
import os
import tempfile
from missionbookcatalog import BOOK_MISSIONS

BOOKS = (50318, 50319, 50320, 50321, 50330, 50331)
CHESTS = (50350, 50351, 50352, 50353, 50354, 50355)
VISIBLE_BOOKS = BOOKS[:4]
MIN_WIDTH, MIN_HEIGHT, ROW_HEIGHT = 260, 138, 29
_OPEN = getattr(builtins, "old_open", builtins.open)


def catalog(book):
    return tuple(tuple((vnum, count) for kind, vnum, count in row[1])
                 for row in BOOK_MISSIONS.get(book, ()))


def objectives(book, index):
    return BOOK_MISSIONS.get(book, ())[index][1]


class MissionState(object):
    def __init__(self):
        self.active = None
        self.progress = (0, 0, 0)
        self.ready = False

    def receive(self, book, mission, p1, p2, p3, ready):
        try:
            book, mission, p1, p2, p3, ready = (int(x) for x in (book, mission, p1, p2, p3, ready))
        except (TypeError, ValueError):
            return False
        if (book, mission) == (0, 0):
            self.active = None
            self.progress = (0, 0, 0)
            self.ready = False
            return True
        rows = BOOK_MISSIONS.get(book, ())
        if not 1 <= mission <= len(rows) or ready not in (0, 1):
            return False
        objectives = rows[mission - 1][1]
        counts = (p1, p2, p3)
        if any(count < 0 or count > (objectives[i][2] if i < len(objectives) else 0)
               for i, count in enumerate(counts)):
            return False
        self.active = (book, mission - 1)
        self.progress = counts
        self.ready = bool(ready)
        return True

    def targets(self):
        return catalog(self.active[0])[self.active[1]] if self.active else ()


def defaults():
    return dict(version=1, auto_track=False, x=30, y=140,
                width=260, height=170, collapsed=False, locked=False)


def normalize(raw):
    result = defaults()
    if not isinstance(raw, dict) or type(raw.get("version")) is not int or raw["version"] != 1:
        return result
    for key in ("auto_track", "collapsed", "locked"):
        if type(raw.get(key)) is bool:
            result[key] = raw[key]
    for key, low in (("x", -32768), ("y", -32768), ("width", MIN_WIDTH), ("height", MIN_HEIGHT)):
        if type(raw.get(key)) is int:
            result[key] = max(low, min(32768, raw[key]))
    return result


def clamp_geometry(x, y, width, height, screen_width, screen_height):
    def axis(position, size, minimum, screen):
        screen = max(0, int(screen))
        margin = min(8, screen // 2)
        size = min(max(0, screen - margin * 2), max(minimum, int(size)))
        return max(margin, min(int(position), screen - margin - size)), size
    x, width = axis(x, width, MIN_WIDTH, screen_width)
    y, height = axis(y, height, MIN_HEIGHT, screen_height)
    return x, y, width, height


def _path(character, folder):
    if not isinstance(character, str) or not character:
        return None
    return os.path.join(folder, hashlib.sha256(character.encode("utf-8")).hexdigest() + ".json")


def load_settings(character, folder="UserData/mission_books"):
    try:
        path = _path(character, folder)
        if path:
            with _OPEN(path, "rb") as source:
                raw = source.read(65537)
            if len(raw) <= 65536:
                return normalize(json.loads(raw.decode("utf-8")))
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    return defaults()


def save_settings(character, settings, folder="UserData/mission_books"):
    temporary = None
    try:
        path = _path(character, folder)
        if not path:
            return False
        os.makedirs(folder, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".mission-books-", dir=folder)
        with os.fdopen(descriptor, "wb") as output:
            output.write(json.dumps(normalize(settings), sort_keys=True).encode("utf-8"))
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
        temporary = None
        return True
    except (OSError, TypeError, ValueError):
        return False
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass
