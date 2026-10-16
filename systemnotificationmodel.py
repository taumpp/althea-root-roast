"""Per-character notification presentation. Never a source of live game state."""
import builtins
import hashlib
import json
import os
import tempfile

VERSION = 1
MAX_ENTRIES = 50
MAX_EVENT_KEYS = 256
MAX_STATE_BYTES = 256 * 1024
MAX_MESSAGE_LENGTH = 512
CATEGORIES = ("biolog", "dungeon", "switchbot")
PREFERENCE_KEYS = ("biolog_hud", "biolog_messages", "dungeon_hud",
                   "dungeon_messages", "switchbot_messages")
_REAL_OPEN = getattr(builtins, "old_open", builtins.open)


def default_preferences():
    return dict((key, True) for key in PREFERENCE_KEYS)


def normalize_preferences(raw, fallback=None):
    result = dict(fallback) if fallback is not None else default_preferences()
    if isinstance(raw, dict):
        for key in PREFERENCE_KEYS:
            if type(raw.get(key)) is bool:
                result[key] = raw[key]
    return dict((key, result[key]) for key in PREFERENCE_KEYS)


def _text(value, maximum):
    if not isinstance(value, str):
        return ""
    # Native text supports markup. Stored history is plain presentation text.
    return " ".join("".join(c for c in value[:maximum * 2]
                            if c >= " " and c != "|" or c in "\n\t").split())[:maximum]


def _integer(value, minimum=0, maximum=0x7FFFFFFFFFFFFFFF, default=0):
    return value if type(value) is int and minimum <= value <= maximum else default


def _entry(raw):
    if not isinstance(raw, dict) or raw.get("category") not in CATEGORIES:
        return None
    identity = _integer(raw.get("id"), 1)
    if not identity:
        return None
    category = raw["category"]
    target = _integer(raw.get("target"), -1, 0x7FFFFFFF, -1)
    if category == "switchbot" and not 0 <= target < 6:
        target = -1
    return {"id": identity, "category": category,
            "title": _text(raw.get("title"), 128),
            "message": _text(raw.get("message"), MAX_MESSAGE_LENGTH),
            "icon_vnum": _integer(raw.get("icon_vnum"), 0, 0x7FFFFFFF),
            "target": target, "created": _integer(raw.get("created"), 0, 0x7FFFFFFF),
            "read": raw.get("read") is True}


def normalize_state(raw):
    state = {"version": VERSION, "preferences": default_preferences(),
             "entries": [], "recent_keys": [], "next_id": 1}
    if not isinstance(raw, dict) or type(raw.get("version")) is not int or raw["version"] != VERSION:
        return state
    state["preferences"] = normalize_preferences(raw.get("preferences"))
    entries = raw.get("entries")
    identities = set()
    if isinstance(entries, list):
        for value in entries[:MAX_ENTRIES]:
            entry = _entry(value)
            if entry and entry["id"] not in identities:
                state["entries"].append(entry)
                identities.add(entry["id"])
    state["entries"].sort(key=lambda entry: entry["id"], reverse=True)
    state["next_id"] = max(_integer(raw.get("next_id"), 1, default=1), max(identities or {0}) + 1)
    keys = raw.get("recent_keys")
    if isinstance(keys, list):
        for key in keys[-MAX_EVENT_KEYS:]:
            key = _text(key, 160)
            if key and key not in state["recent_keys"]:
                state["recent_keys"].append(key)
    return state


def _path(character, base_path):
    if not isinstance(character, str) or not character:
        return None
    return os.path.join(base_path, hashlib.sha256(character.encode("utf-8")).hexdigest() + ".json")


def load_state(character, base_path):
    try:
        path = _path(character, base_path)
        if path:
            with _REAL_OPEN(path, "rb") as source:
                data = source.read(MAX_STATE_BYTES + 1)
            if len(data) <= MAX_STATE_BYTES:
                return normalize_state(json.loads(data.decode("utf-8")))
    except (OSError, ValueError, TypeError, RecursionError):
        pass
    return normalize_state(None)


def save_state(character, state, base_path):
    temporary = None
    try:
        path = _path(character, base_path)
        if not path:
            return False
        payload = json.dumps(normalize_state(state), ensure_ascii=False, sort_keys=True).encode("utf-8")
        if len(payload) > MAX_STATE_BYTES:
            return False
        os.makedirs(base_path, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix=".notifications-", suffix=".tmp", dir=base_path)
        with os.fdopen(descriptor, "wb") as output:
            output.write(payload)
            output.flush()
            os.fsync(output.fileno())
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


class NotificationStore:
    def __init__(self, character, base_path="UserData/system_notifications"):
        self.character = character
        self.base_path = base_path
        self.state = load_state(character, base_path)
        self.revision = 0

    @property
    def preferences(self):
        return self.state["preferences"]

    @property
    def entries(self):
        return self.state["entries"]

    @property
    def recent_keys(self):
        return self.state["recent_keys"]

    def hud_enabled(self, category):
        return self.preferences.get(category + "_hud", False)

    def unread_count(self):
        return sum(not entry["read"] for entry in self.entries)

    def save(self):
        return save_state(self.character, self.state, self.base_path)

    def apply_preferences(self, preferences):
        previous = self.state["preferences"]
        self.state["preferences"] = normalize_preferences(preferences, previous)
        if not self.save():
            self.state["preferences"] = previous
            return False
        self.revision += 1
        return True

    def add(self, category, title, message, icon_vnum, target, created, event_key=""):
        if category not in CATEGORIES:
            return False
        key = _text(event_key, 160)
        if key and key in self.recent_keys:
            return True
        if key:
            self.recent_keys.append(key)
            del self.recent_keys[:-MAX_EVENT_KEYS]
        # Muting consumes the existing ready edge; turning messages on later is
        # a presentation change, not a request to replay old ready events.
        if self.preferences[category + "_messages"]:
            entry = _entry({"id": self.state["next_id"], "category": category,
                            "title": title, "message": message, "icon_vnum": icon_vnum,
                            "target": target, "created": created, "read": False})
            self.state["next_id"] += 1
            self.entries.insert(0, entry)
            del self.entries[MAX_ENTRIES:]
        self.revision += 1
        # If disk is temporarily unavailable, retain delivery in memory and
        # retry persistence on the next mutation/teardown without re-notifying.
        self.save()
        return True

    def find(self, identity):
        for entry in self.entries:
            if entry["id"] == identity:
                return dict(entry)
        return None

    def mark_read(self, identity):
        for entry in self.entries:
            if entry["id"] == identity and not entry["read"]:
                entry["read"] = True
                self.revision += 1
                self.save()
                return

    def mark_all_read(self):
        if not self.unread_count():
            return
        for entry in self.entries:
            entry["read"] = True
        self.revision += 1
        self.save()
