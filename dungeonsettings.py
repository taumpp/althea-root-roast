"""Data-only dungeon preferences. The old extensionless pickle is never read."""
import os
import presetstorage

# Parser resource bounds, independent of the server's dungeon population.
MAX_RECORDS = 1024
_FIELDS = {"listIndex", "showStatus", "alarm", "autoTicket", "selected"}


def path(character):
    if (type(character) is not str or not character or len(character) > 128
            or any(ord(c) < 32 or c in '/\\:*?"<>|' for c in character)
            or character in (".", "..")):
        raise ValueError("Invalid dungeon settings character")
    return os.path.join("UserData", "dungeon_info", character + "_track.json")


def validate(document, current_version):
    if type(document) is not dict:
        raise ValueError("Invalid dungeon settings document")
    version = document.get("version", 0)
    if type(version) is not int or not 0 <= version <= current_version:
        raise ValueError("Unsupported dungeon settings version")
    if version:
        if set(document) != {"version", "dungeons"}:
            raise ValueError("Invalid dungeon settings envelope")
        records = document["dungeons"]
    else:
        # Historical order migrations may consume JSON data, never pickle.
        records = document
    if type(records) is not dict or len(records) > MAX_RECORDS:
        raise ValueError("Invalid dungeon settings collection")
    normalized = {}
    for key, record in records.items():
        if type(key) is str:
            if not key.isascii() or not key.isdecimal() or str(int(key)) != key:
                raise ValueError("Invalid dungeon settings key")
            key = int(key)
        if type(key) is not int or not 1 <= key <= 0xFFFFFFFF or key in normalized:
            raise ValueError("Invalid dungeon settings key")
        if type(record) is not dict or (version and not set(record) <= _FIELDS):
            raise ValueError("Invalid dungeon settings fields")
        entry = {}
        for field in _FIELDS & set(record):
            value = record[field]
            if field == "listIndex":
                if type(value) is not int or not 0 <= value < MAX_RECORDS:
                    raise ValueError("Invalid dungeon list index")
            elif type(value) is not bool:
                raise ValueError("Invalid dungeon settings flag")
            entry[field] = value
        normalized[key] = entry
    return {"version": version, "dungeons": normalized} if version else normalized


def load(file_path, current_version):
    document = presetstorage.load_document(file_path)
    return None if document is None else validate(document, current_version)


def save(file_path, document, current_version):
    presetstorage.save_document(file_path, validate(document, current_version))
