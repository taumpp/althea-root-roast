"""Validated server events and pixel-measured wrapping; no gameplay eligibility."""
import binascii


def Decode(kind, subject, value, name):
    try:
        kind, subject, value = int(kind), int(subject), int(value)
        if kind not in (1, 2, 3) or not 0 < subject <= 0xffffffff or not 0 < value <= 0xffffffffffffffff:
            return None
        if not 0 < len(name) <= 48 or len(name) % 2:
            return None
        decoded = binascii.unhexlify(name).decode("utf-8")
        if not decoded or any(ord(char) < 33 or char in "|%" for char in decoded):
            return None
        return dict(kind=kind, subject=subject, value=value, name=decoded)
    except (ValueError, TypeError, UnicodeError, binascii.Error):
        return None


def Wrap(text, width, measure):
    """Split even an unbroken long word. Every returned line fits real glyphs."""
    lines, current = [], ""
    for word in text.split():
        candidate = current + (" " if current else "") + word
        if measure(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
            current = ""
        for char in word:
            if current and measure(current + char) > width:
                lines.append(current)
                current = ""
            current += char
    if current:
        lines.append(current)
    return lines or [""]


def TimeText(seconds):
    hours, rest = divmod(int(seconds), 3600)
    minutes, seconds = divmod(rest, 60)
    return "%d:%02d:%02d" % (hours, minutes, seconds) if hours else "%02d:%02d" % (minutes, seconds)
