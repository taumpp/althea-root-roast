"""Signed native colors shared by bonus rows, separate from UI metadata."""
import re

# Exact packed values of ToolTip's existing ordinary green/red channels.
POSITIVE = 0xff89b88d - 0x100000000
NEGATIVE = 0xffe57875 - 0x100000000
_NEGATIVE_NUMBER = re.compile(r"(?<![\w\d])[-\u2212]\d")


def Value(value):
    return NEGATIVE if value < 0 else POSITIVE


def Text(text):
    # Native/localized text can be Unicode or UTF-8/legacy bytes.
    if hasattr(text, "decode"):
        try:
            text = text.decode("utf-8")
        except UnicodeError:
            text = text.decode("latin1")
    # A range separator ("10 - 20") is not a negative number.
    return NEGATIVE if _NEGATIVE_NUMBER.search(text) else POSITIVE


def Number(value):
    """One sign convention for passive bonuses: +positive, zero, -negative."""
    return (u"+%g" if value > 0 else u"%g") % value
