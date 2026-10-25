# -*- coding: utf-8 -*-
"""Settings v5: Klávesové zkratky in the new look (2026-10-05).

The page is drawn by the settings window like every other v5 page: kit section headings (no red ribbons), one row per
action with the name on the left and a key cap on the right, the kit scrollbar over the whole content height,
Spectral everywhere, the whole content width. Key caps (2026-10-06): style uikit.KEYCAP_STYLE (K4 dark cap with
a soft shadow; K1-K3 by one constant), a fixed width in one column at the right edge, an unbound action shows "–"
with a muted "nepřiřazeno" beside the cap, a capturing cap is ruby with "stiskni novou klávesu · Esc zruší" beside it. The logic stays uikeybindings.KeybindingsPage (binding session,
capture dialog, conflict question, reserved shortcuts, auto save); KeyBindings() binds a subclass of it to the key
caps instead of the A7 script window (UIScript/game_option_0_2.py). The capture dialog, the conflict question and the
notices are the settings kit dialogs of uisettingsc9dialogs (the A7 ones, traced, when those cannot be built); the
capture dialog names the action it binds.
"""
import uikit
import uikitsections
import uikittokens as T
from settingslocale import Text as Tr
from uisettingsc9rows import Plural

PITCH = {'1080': 44, '768': 36}
CAPTURE_HINT = Tr('stiskni novou klávesu | Esc zruší', 'press a new key · Esc cancels')


def _locale(key, fallback):
    try:
        import uiScriptLocale
    except ImportError:
        return fallback
    return getattr(uiScriptLocale, key, fallback)


class CapAdapter(object):
    """bindingButtons entry: KeybindingsPage.RefreshRows() calls SetText(text) on it."""

    def __init__(self, cap, unbound):
        self.cap, self.unbound = cap, unbound

    def SetText(self, text):
        self.cap.SetText(text, empty=(text == self.unbound))


def KeyBindings(window=None):
    """The A7 binding page logic without its script window (None when the module is unavailable); its dialogs in
    the kit look of ``window`` (the settings window) when given."""
    import uikeybindings
    base = uikeybindings.KeybindingsPage

    class C9KeyBindings(base):
        def BindView(self):
            """Dialogs and the session of the A7 page, without its list widgets."""
            if not getattr(self, 'manager', None):
                return False
            if getattr(self, 'captureDialog', None) is None and hasattr(uikeybindings, 'ShortcutCaptureDialog'):
                if not self._KitDialogs():
                    import uiCommon
                    self.captureDialog = uikeybindings.ShortcutCaptureDialog()
                    self.conflictDialog = uikeybindings.ConflictDialog()
                    self.restoreDialog = uiCommon.QuestionDialog()
                    self.popupDialog = uiCommon.PopupDialog()
            self.BeginSession()
            return True

        def _KitDialogs(self):
            """The capture / conflict / restore / notice dialogs in the settings kit look; False (traced) when they
            cannot be built - the A7 dialogs open instead."""
            kit = getattr(window, 'kit', None)
            if kit is None:
                return False
            try:
                import uisettingsc9dialogs
                dialogs = uisettingsc9dialogs.KeyDialogs(kit, window)
            except Exception:
                import dbg
                import traceback
                dbg.TraceError('settings kit key dialogs: %s' % traceback.format_exc())
                return False
            if not dialogs:
                return False
            self.captureDialog, self.conflictDialog, self.restoreDialog, self.popupDialog = dialogs
            return True

        def BeginCapture(self, action_id):
            dialog = getattr(self, 'captureDialog', None)
            if dialog is not None and hasattr(dialog, 'SetAction'):
                dialog.SetAction(self.ActionName(action_id))
            base.BeginCapture(self, action_id)

        def ActionName(self, action_id):
            try:
                action = self.manager.get_action(action_id)
            except Exception:
                return ''
            return _locale(action.locale_key, action_id)

        def Dialogs(self):
            """The open dialogs of the page (capture, conflict, restore, notice)."""
            return [d for d in (getattr(self, name, None) for name in ('captureDialog', 'conflictDialog',
                                                                        'restoreDialog', 'popupDialog'))
                    if d is not None and d.IsShow()]

        def Attach(self, caps):
            unbound = _locale('KEYBIND_UNBOUND', Tr('Nepřiřazeno', 'Unbound'))
            self.bindingButtons = dict((action_id, CapAdapter(cap, unbound)) for action_id, cap in caps.items())
            self.RefreshRows()

        def Detach(self):
            self.bindingButtons = {}

        def RestoreDefaultsNow(self):
            """The confirmed restore (the settings window asked already; no second A7 question)."""
            if not getattr(self, 'session', None):
                return
            self.session.restore_defaults()
            self.dirty = True
            if self.auto_save:
                self.Save()
            self.RefreshRows()

        def Capturing(self):
            dialog = getattr(self, 'captureDialog', None)
            return bool(dialog and dialog.IsShow())

    return C9KeyBindings(auto_save=True)


class KeysView(object):
    """Rows of the key bindings page inside the settings window (window.content, window.c9_rows)."""

    def __init__(self, window):
        self.window = window
        self.caps = {}
        self.capturing = None
        self.active = False

    def Page(self):
        window = self.window
        if window.key_page is None:
            try:
                window.key_page = KeyBindings(window)
            except ImportError:
                return None
            window.key_page.BindView()
        return window.key_page

    def Active(self):
        return self.active

    def ResetText(self):
        return Tr('Vrátit všechny klávesové zkratky (%s) na výchozí klávesy?',
                  'Reset every keybinding (%s) to its default key?') % Plural(self.Count(), 'akce')

    def Count(self):
        page = self.window.key_page
        manager = getattr(page, 'manager', None) if page else None
        return sum(len(actions) for unused, actions in manager.actions_by_category()) if manager else 0

    def Build(self, width):
        window, k = self.window, self.window.kit
        self.active = True
        page = self.Page()
        manager = getattr(page, 'manager', None) if page else None
        if not manager:
            window._C9Text(Tr('Klávesové zkratky nejsou v této verzi hry dostupné.',
                              'Keybindings are not available in this client.'), 0, 4, 'M', T.MUTED, valign='top')
            return k.cell('M') + 12
        pitch = PITCH[k.prof]
        caps, y = {}, 0
        session = getattr(page, 'session', None)
        hint = Tr('Klikni na klávesu a stiskni novou; Delete přiřazení zruší, Esc zavře bez změny.',
                  'Click the key and press a new one; Delete clears it, Esc closes without a change.')
        style = uikitsections.Style(k)          # the one switch of the section look (uikitsections.SECTION_STYLE)
        track = lambda widget: window._C9Track(widget, wheel=False)
        section = None
        for category_key, actions in manager.actions_by_category():
            y += style.Close(section, y)
            y += style.Gap(not y)
            section = style.Open(window.content, 0, y, width, track)
            y += style.Heading(window.content, 0, y, width, _locale(category_key, category_key), track)
            inset_l, inset_r = style.Inset()
            for index, action in enumerate(actions):
                label = _locale(action.locale_key, action.action_id)
                default = action.default.display() if getattr(action, 'default', None) else \
                    _locale('KEYBIND_UNBOUND', Tr('Nepřiřazeno', 'Unbound'))
                style.RowBack(window.content, 0, y, width, pitch, index, track)
                row = dict(type='control', kind='key', key=action.action_id, label=label, y=y, h=pitch,
                           hint_text=hint, tip_note=Tr('Výchozí klávesa: %s', 'Default key: %s') % default)
                window.c9_rows.append(row)
                band = window._C9Track(uikit.Band(window.content, 0, y, width, pitch, 'hover'), wheel=False)
                band.Hide()
                row['band'] = band
                hit = window._C9Track(uikit.HitArea(window.content, 0, y, width, pitch))
                hit.SetHoverEvent(lambda row=row: window._C9ShowInfo(row))
                hit.SetEvent(lambda action_id=action.action_id: self.Capture(action_id))
                row['hit'] = hit
                row['label_line'] = window._C9Text(label, inset_l, y + pitch // 2, 'M', T.INK)
                cap_h = k.p('keycap6_h') if uikit.KEYCAP_STYLE != 'v5' else k.p('keycap_h')
                cap = uikit.KeyCap(window.content, k, width - inset_r, y + (pitch - cap_h) // 2, '',
                                   event=lambda action_id=action.action_id: self.Capture(action_id))
                cap.SetHint(CAPTURE_HINT)
                cap.SetHoverEvent(lambda row=row: window._C9ShowInfo(row))
                window._C9Track(cap)
                caps[action.action_id] = cap
                style.RowLine(window.content, 0, y + pitch - 1, width, track)
                y += pitch
        y += style.Close(section, y)
        self.caps = caps
        if session is not None or hasattr(page, 'Attach'):
            page.Attach(caps)
        return y

    def Capture(self, action_id):
        page = self.window.key_page
        if not page or action_id not in self.caps:
            return
        page.BeginCapture(action_id)
        if self.capturing in self.caps:
            self.caps[self.capturing].SetActive(False)
        self.capturing = action_id
        self.caps[action_id].SetActive(True)

    def OnUpdate(self):
        if self.capturing is None:
            return
        page = self.window.key_page
        if not page or not page.Capturing():
            if self.capturing in self.caps:
                self.caps[self.capturing].SetActive(False)
            self.capturing = None

    def OnPressEscapeKey(self):
        """Esc in the settings window closes an open key dialog first (the capture without a change, a question
        as its cancel)."""
        page = self.window.key_page if self.window else None
        dialogs = page.Dialogs() if page is not None and hasattr(page, 'Dialogs') else []
        for dialog in dialogs:
            dialog.OnPressEscapeKey()
        return bool(dialogs)

    def RestoreDefaults(self):
        page = self.window.key_page
        if page:
            page.RestoreDefaultsNow()

    def SearchIndex(self):
        """(page, action id, name) of every action, for the window search (the A7 index has no actions)."""
        page = self.window.key_page
        manager = getattr(page, 'manager', None) if page else None
        if manager is None:
            try:
                import keybindings
                manager = keybindings.GetManager()
            except ImportError:
                manager = None
        if not manager:
            return []
        return [('keys', action.action_id, _locale(action.locale_key, action.action_id))
                for unused, actions in manager.actions_by_category() for action in actions]

    def Clear(self):
        page = self.window.key_page
        if self.active and page and hasattr(page, 'Detach'):
            page.Detach()
        self.caps = {}
        self.capturing = None
        self.active = False

    def Destroy(self):
        self.Clear()
        self.window = None
