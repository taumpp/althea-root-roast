"""Open Settings -> Panely tlačítek on one tab (minimap / inventory); save errors.

Shared by the small cogwheel buttons of the minimap and the inventory rail and
by the rail context menu. Uses the ESC menu path (``dlgSystem``), so the
settings window behaves exactly as when opened from the system menu.

The cogwheels use ``Toggle``: a click opens the page on its tab, the next click on
the same cogwheel closes Settings again (like the other HUD buttons). The context
menu entry keeps ``Open``: a menu item only opens.
"""


def Open(interface, tab):
    dialog = getattr(interface, 'dlgSystem', None) if interface is not None else None
    if dialog is None or not hasattr(dialog, 'OpenGameOptionDialog'):
        return False
    window = dialog.OpenGameOptionDialog()
    if window is None or not hasattr(window, 'OpenPage'):
        return False
    window.OpenPage('panels')
    # Settings v5: the Panely tlačítek page is the shell's active custom view (uisettingspanelsv5.PanelsPage);
    # the A7 / c9 v4 window keeps it in ``panels_page``.
    page = getattr(window, 'c9_view_active', None)
    if page is None or not hasattr(page, 'SelectTab'):
        page = getattr(window, 'panels_page', None)
    if page is not None and hasattr(page, 'SelectTab'):
        page.SelectTab(tab)
    return True


def _SettingsWindow(interface):
    """The Settings window of the ESC menu; None until it was opened once."""
    dialog = getattr(interface, 'dlgSystem', None) if interface is not None else None
    return getattr(dialog, 'gameOptionDlg', None)


def IsOpenOn(interface, tab):
    """True while Settings is open on the Panely tlačítek page showing ``tab``."""
    window = _SettingsWindow(interface)
    if window is None or not window.IsShow():
        return False
    if getattr(window, 'page', None) != 'panels' or getattr(window, 'searching', False):
        return False
    page = getattr(window, 'c9_view_active', None)
    if page is None or not hasattr(page, 'SelectTab'):
        page = getattr(window, 'panels_page', None)
    shown = getattr(page, 'tab', None)
    if shown is None:
        return False
    if shown == tab:
        return True
    try:
        import buttonpanelsv5
        return shown == buttonpanelsv5.TabOf(tab)
    except ImportError:
        return False


def Toggle(interface, tab):
    """The cogwheels: open Panely tlačítek on ``tab``, close Settings when it already shows that tab.

    Another page or the other tab of the panels only switches (a different request), so the second
    click on the SAME cogwheel is what closes the window.
    """
    if IsOpenOn(interface, tab):
        window = _SettingsWindow(interface)
        window.Hide()
        return not window.IsShow()
    return Open(interface, tab)


# Save errors (audit 2026-10-04, 1.3/1.4) -------------------------------------------
def StoreErrorText(error=None):
    """The player-facing reason of the last failed panel write ('' when it succeeded)."""
    import buttonpanelstore as store
    from settingslocale import Text as T
    error = error or store.LastError()
    if error == store.ERROR_NEWER:
        return T('Panely uložila novější verze hry. Tato verze je jen zobrazí a nic nezmění.',
                 'The panels were saved by a newer client: this version only shows them.')
    if error == store.ERROR_IO:
        return T('Nastavení panelů se nepodařilo uložit (disk nebo jiná spuštěná hra).',
                 'Could not save the panel settings (disk or another running client).')
    return ''


# The same reason is repeated in the chat at most once a minute: page flips by the
# mouse wheel or repeated clicks against a read-only file must not flood it.
REPORT_INTERVAL = 60.0
_last_report = [None, 0.0]


def _now():
    try:
        import app
        return float(app.GetTime())
    except Exception:
        import time
        return time.time()


def ReportStoreError():
    """In-game paths: one chat line when the last panel write failed; True if it did."""
    text = StoreErrorText()
    if not text:
        return False
    now = _now()
    if _last_report[0] == text and 0 <= now - _last_report[1] < REPORT_INTERVAL:
        return True
    _last_report[0], _last_report[1] = text, now
    try:
        import chat
        chat.AppendChat(chat.CHAT_TYPE_INFO, text)
    except Exception:
        pass
    return True
