import copy
import time


SNAPSHOT_TTL_SECONDS = 120.0

_pendingSnapshot = None


def _Now():
	return time.time()


def Store(characterName, windows, now=None):
	global _pendingSnapshot

	characterName = str(characterName or "")
	if not characterName:
		_pendingSnapshot = None
		return False

	if not isinstance(windows, dict):
		_pendingSnapshot = None
		return False

	_pendingSnapshot = {
		"character": characterName,
		"created_at": float(_Now() if now is None else now),
		"windows": copy.deepcopy(windows),
	}
	return True


def Take(characterName, now=None):
	global _pendingSnapshot

	snapshot = _pendingSnapshot
	_pendingSnapshot = None
	if not snapshot:
		return None

	currentTime = float(_Now() if now is None else now)
	createdAt = float(snapshot.get("created_at", 0.0))
	if createdAt <= 0.0 or currentTime - createdAt > SNAPSHOT_TTL_SECONDS:
		return None

	if str(snapshot.get("character", "")) != str(characterName or ""):
		return None

	windows = snapshot.get("windows")
	if not isinstance(windows, dict):
		return None
	return copy.deepcopy(windows)


def UpdateWindow(characterName, key, value, now=None):
	"""Refresh one captured presenter at teardown without extending its TTL."""
	global _pendingSnapshot
	if not HasPending(now) or _pendingSnapshot.get("character") != str(characterName or ""):
		return False
	windows = _pendingSnapshot["windows"]
	if value is None:
		windows.pop(key, None)
	else:
		windows[key] = copy.deepcopy(value)
	return True


def Clear():
	global _pendingSnapshot
	_pendingSnapshot = None


def HasPending(now=None):
	global _pendingSnapshot

	if not _pendingSnapshot:
		return False

	currentTime = float(_Now() if now is None else now)
	createdAt = float(_pendingSnapshot.get("created_at", 0.0))
	if createdAt <= 0.0 or currentTime - createdAt > SNAPSHOT_TTL_SECONDS:
		_pendingSnapshot = None
		return False
	return True
