"""Consume the native, process-private launcher channel once. Never read credentials from disk."""
import app

_consumed = False


def consume():
    global _consumed
    if _consumed:
        return None
    _consumed = True
    receive = getattr(app, "ConsumeLauncherHandoff", None)
    if receive is None:
        # The connection phase requires the launcher; there is no disk fallback.
        return None
    record = receive()
    if record is None:
        return None
    if type(record) is not tuple or len(record) != 4:
        return None
    server, channel, login, password = record
    if type(channel) is not int or not 1 <= channel <= 255:
        return None
    for text, limit in ((server, 128), (login, 30), (password, 16)):
        if type(text) is not str or not text or len(text.encode("utf-8")) > limit or any(ord(c) < 32 for c in text):
            return None
    return record
