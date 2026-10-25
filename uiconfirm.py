"""Enter activates a dialog's current confirmation button, just like a click."""
import weakref
import wndMgr


def Prioritize(window):
    # Older executables keep their original dispatch without unknown-flag logs.
    if getattr(wndMgr, 'IME_RETURN_PRIORITY', 0) == 1:
        window.AddFlag('ime_return_priority')


def Visual(native, button):
    """Link a hidden native control to its visible skin; return its undo action."""
    native._confirm_visual = weakref.ref(button)
    original = weakref.ref(native)

    def restore():
        widget = original()
        if widget is not None:
            widget._confirm_visual = None
    return restore


def Activate(button):
    visual = getattr(button, '_confirm_visual', None)
    if visual is not None:
        button = visual()
    if not button or not button.IsShow():
        return True
    disabled = getattr(button, 'IsDisable', None)
    try:
        blocked = disabled and disabled()
    except AttributeError:
        # Native button-state queries need the paired executable. Do not
        # bypass a pending/disabled action on an older client.
        return True
    if blocked or not getattr(button, 'enabled', True):
        return True
    # Native and dressed ui.Button use CallEvent; the R1/kit controls use click.
    event = getattr(button, 'CallEvent', None) or getattr(button, 'click', None)
    if event:
        event()
    return True


def Bind(dialog, button_name, child=False):
    """Resolve the button on each press: skins may replace it after binding.

    The native priority flag consumes one Enter at the top visible dialog,
    before an unrelated focused edit line or the game's chat handler.
    A weak reference avoids keeping a closed dialog alive through its handler.
    """
    owner = weakref.ref(dialog)

    def confirm():
        window = owner()
        if window is not None and window.IsShow():
            button = window.GetChild(button_name) if child else getattr(window, button_name, None)
            Activate(button)
        return True

    dialog.OnIMEReturn = confirm
    Prioritize(dialog)
