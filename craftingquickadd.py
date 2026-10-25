"""Route an unmodified inventory right-click to the visible craft basket."""
import app


def TryAddInventoryItem(interface, cell):
    if any(app.IsPressed(key) for key in (app.DIK_LCONTROL, app.DIK_RCONTROL,
                                         app.DIK_LALT, app.DIK_RALT)):
        return False
    window = getattr(interface, 'wndCubeRenewal', None) if interface else None
    return bool(window and window.TryAddInventoryItem(cell))
