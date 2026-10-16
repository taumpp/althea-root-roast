"""Native presentation contract of the owner-approved quick-equip v8."""

BODY_FONT = "Tahoma:12"
BOLD_FONT = "Tahoma:12b"
DENSE_FONT = "Tahoma:11"
BUTTON_FONT = "Tahoma:11b"
ARROW_FONT = "Tahoma:15b"


def argb(value):
    """Keep ARGB bits while satisfying wndMgr's signed C-int colour binding."""
    return value - 0x100000000 if value & 0x80000000 else value
