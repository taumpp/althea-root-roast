"""Bounded, data-only local presets. Legacy executable formats are never read."""
import builtins
import json
import os

_DISK_OPEN = getattr(builtins, "old_open", builtins.open)
MAX_BYTES = 256 * 1024
MAX_PRESETS = 128
_PATHS = {
    "switchbot": "UserData/switchbot.json",
    "fast_equip": "UserData/fast_equip/presets.json",
}


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Invalid preset integer")
    return value


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate preset field")
        result[key] = value
    return result


def validate(kind, records, alternatives=3, attributes=7):
    if kind not in _PATHS or type(records) is not dict or len(records) > MAX_PRESETS:
        raise ValueError("Invalid preset collection")
    result = {}
    for key, record in records.items():
        if type(key) is str:
            if not key.isascii() or not key.isdecimal() or str(int(key)) != key:
                raise ValueError("Invalid preset key")
            key = int(key)
        _integer(key, 0 if kind == "switchbot" else 1, MAX_PRESETS - 1)
        if key in result or type(record) is not dict:
            raise ValueError("Invalid preset record")
        fields = {"name", "alternatives"} if kind == "switchbot" else {"name"}
        if set(record) != fields:
            raise ValueError("Invalid preset fields")
        name = record["name"]
        if type(name) is not str or not 1 <= len(name) <= 32 or any(ord(c) < 32 for c in name):
            raise ValueError("Invalid preset name")
        entry = {"name": name}
        if kind == "switchbot":
            rows = record["alternatives"]
            if type(rows) not in (list, tuple) or len(rows) != alternatives:
                raise ValueError("Invalid preset alternatives")
            entry["alternatives"] = []
            for row in rows:
                if type(row) not in (list, tuple) or len(row) != attributes:
                    raise ValueError("Invalid preset attributes")
                normalized = []
                for pair in row:
                    if type(pair) not in (list, tuple) or len(pair) != 2:
                        raise ValueError("Invalid preset attribute")
                    normalized.append([_integer(pair[0], 0, 65535), _integer(pair[1], -2147483648, 2147483647)])
                entry["alternatives"].append(normalized)
        result[key] = entry
    return result


def load(kind, alternatives=3, attributes=7):
    try:
        with _DISK_OPEN(_PATHS[kind], "rb") as source:
            raw = source.read(MAX_BYTES + 1)
    except FileNotFoundError:
        return {}
    if len(raw) > MAX_BYTES:
        raise ValueError("Preset file exceeds size limit")
    document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
    if type(document) is not dict or set(document) != {"version", "presets"} or type(document["version"]) is not int or document["version"] != 1:
        raise ValueError("Unsupported preset version")
    return validate(kind, document["presets"], alternatives, attributes)


def save(kind, records, alternatives=3, attributes=7):
    records = validate(kind, records, alternatives, attributes)
    raw = json.dumps({"version": 1, "presets": records}, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    if len(raw) > MAX_BYTES:
        raise ValueError("Preset file exceeds size limit")
    path = _PATHS[kind]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + "." + os.urandom(12).hex() + ".tmp"
    # Exclusive creation avoids following an existing temporary symlink. Replace
    # only after a complete write; failed saves preserve the previous JSON.
    with _DISK_OPEN(temporary, "xb") as target:
        try:
            target.write(raw)
            target.flush()
            os.fsync(target.fileno())
        except BaseException:
            target.close()
            os.remove(temporary)
            raise
    try:
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)
