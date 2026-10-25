# -*- coding: utf-8 -*-
"""Settings v5: the windows that open from the settings window, in the settings kit look (root/uikit.py).

  Klávesové zkratky   capture of a new key (KitCaptureDialog), the "already used" question (KitQuestion, Nahradit /
                      Zrušit), the reserved / not saved notice (KitNotice, one button) and the restore question.
  Svět a počasí       the sky picker (SkyPicker): the twelve original thumbnails in a kit window.

Only the look changes. The capture dialog IS the A7 uikeybindings.ShortcutCaptureDialog (its key handling: Esc closes,
Delete clears the binding, held Ctrl / Shift / Alt show as "Ctrl+...", the input capture of the key manager); the kit
builds its controls instead of UIScript/keybindingcapturedialog.py. The questions keep the uiCommon dialog API the
A7 binding page calls (SetText / SetAcceptEvent / Open / Close, OpenConflict). The sky picker is the settings window's
popup like the A7 one (window.popup, _SelectSky, _ClosePopup, Esc).

The old look ("Starý vzhled", settingslook 'legacy') never gets here: it is the A7 window with the A7 dialogs. The
settings window falls back to the A7 dialogs (traced) when a kit dialog cannot be built.
"""
import ui

import uikit
import uikitlayout as L
import uikittokens as T
from settingslocale import Text as Tr

SKY_PATH = 'd:/ymir work/ui/game/graphic/jtx_skybox/sky%d.dds'
SKY_SIZE = (85, 51)                   # the original thumbnails, drawn at their native size
SKY_COLUMNS = 4
SKY_WINDOW = (388, 320)               # the A7 picker's size


def _locale(key, fallback):
    try:
        import uiScriptLocale
    except ImportError:
        return fallback
    return getattr(uiScriptLocale, key, fallback)


def DialogWidth(kit):
    """The width of the settings' own kit questions (uikit.Confirm), so every dialog of the window matches."""
    return 420 if kit.prof == '1080' else 360


def CenteredLines(parent, text, cx, y, width, font, color, line_height):
    """Word-wrapped lines centred on cx; returns (lines, next y)."""
    lines, y = uikit.Wrap(parent, text, 0, y, width, font, color, line_height)
    for line in lines:
        line.SetHorizontalAlignCenter()
        line.SetPosition(int(cx), line.GetLocalPosition()[1])
    return lines, y


def _return_focus(dialog, was_shown):
    owner = getattr(dialog, 'owner', None)
    if was_shown and owner is not None and owner.IsShow():
        owner.SetFocus()


# --------------------------------------------------------------------------- key capture
class CaptureCap(uikit.KeyCap):
    """The key cap of the capture dialog: always capturing (ruby) and showing what the dialog captured - "...",
    the held modifiers ("Ctrl+...") or the new shortcut - centred on cx. Not pickable (the dialog takes the keys)."""

    def __init__(self, parent, kit, cx, y):
        self.cx = int(cx)
        uikit.KeyCap.__init__(self, parent, kit, cx, y, '...', min_w=150 if kit.prof == '1080' else 120, align='left')
        self.AddFlag('not_pick')
        self.active = True
        self.paint()

    def SetText(self, text, empty=False):
        if getattr(self, 'w', None) is not None and text == self.text and bool(empty) == self.empty:
            return                     # the dialog repeats the held modifiers every frame
        uikit.KeyCap.SetText(self, text, empty)
        self.SetPosition(self.cx - self.w // 2, self.top)

    def paint(self):
        uikit.KeyCap.paint(self)
        if self.active:
            self.label.SetText(self.text or '...')


def CaptureDialogClass():
    """The kit subclass of uikeybindings.ShortcutCaptureDialog (None when that module has no capture dialog)."""
    import uikeybindings
    base = getattr(uikeybindings, 'ShortcutCaptureDialog', None)
    if base is None:
        return None

    class KitCaptureDialog(base):
        def __init__(self, kit, owner=None):
            self.kit, self.owner = kit, owner
            self.action_name = ''
            base.__init__(self)

        def _LoadWindow(self):
            k = self.kit
            self.AddFlag('movable')
            self.AddFlag('float')
            self.w = w = DialogWidth(k)
            self.frame = uikit.Frame(self, k, 'window', 0, 0, w, 200, bg=True)
            self.board = uikit.TitleBar(self, k, 5, 5, w - 10, Tr('Nová klávesa', 'New key'), kind='dialog',
                                        on_close=self.Close)
            self.action_line = uikit.Text(self, '', w // 2, 0, k.font('Mb'), T.GOLD_HI, align='center', valign='top')
            self.instruction, self.instruction_h = CenteredLines(
                self, Tr('Stiskni novou klávesu nebo zkratku s Ctrl, Shift či Alt.',
                         'Press a new key or a shortcut with Ctrl, Shift or Alt.'),
                w // 2, 0, w - 48, k.font('M'), T.INK, k.cell('M') + 4)
            self.capturedShortcut = CaptureCap(self, k, w // 2, 0)
            self.cap_h = k.p('keycap6_h')
            self.note = uikit.Text(self, Tr('Delete zruší přiřazení | Esc zavře bez změny',
                                            'Delete clears the key | Esc closes without a change'),
                                   w // 2, 0, k.font('S'), T.MUTED, align='center', valign='top')
            bw = 150 if k.prof == '1080' else 128
            self.cancelButton = uikit.Button(self, k, 0, 0, bw, _locale('KEYBIND_CANCEL', Tr('Zrušit', 'Cancel')),
                                             role='secondary', event=self.Close, size='bar')
            self.cancelButton.FitWidth(bw)
            self._Layout()

        def _Layout(self):
            k, w = self.kit, self.w
            y = 5 + self.board.Height() + (16 if k.prof == '1080' else 12)
            if self.action_name:
                self.action_line.SetText(self.action_name)
                self.action_line.SetPosition(w // 2, y)
                self.action_line.Show()
                y += k.cell('Mb') + 4
            else:
                self.action_line.Hide()
            for index, line in enumerate(self.instruction):
                line.SetPosition(w // 2, y + index * (k.cell('M') + 4))
            y += self.instruction_h + 10
            self.capturedShortcut.top = y
            self.capturedShortcut.SetPosition(self.capturedShortcut.cx - self.capturedShortcut.w // 2, y)
            y += self.cap_h + 10
            self.note.SetPosition(w // 2, y)
            y += k.cell('S') + 14
            button = self.cancelButton
            button.SetPosition((w - button.w) // 2, y)
            h = y + button.h + 16
            self.SetSize(w, h)
            self.frame.SetSize(w, h)
            self.frame.Apply(L.frame('window', k.prof, w, h, bg=True))

        def SetAction(self, name):
            """Name of the action that gets the new key (the dialog may cover its row)."""
            self.action_name = name or ''
            self._Layout()

        def Close(self):
            shown = self.IsShow()
            base.Close(self)
            _return_focus(self, shown)

        def Destroy(self):
            base.Destroy(self)
            self.owner = None

    return KitCaptureDialog


# --------------------------------------------------------------------------- questions
class KitQuestion(uikit.Confirm):
    """uiCommon.QuestionDialog API (and ConflictDialog.OpenConflict) on the settings kit confirmation: ruby accept on
    the left, cancel on the right, Esc and the cross cancel."""

    def __init__(self, kit, owner, title, accept_text, cancel_text):
        uikit.Confirm.__init__(self, kit, title, accept_text, cancel_text)
        self.owner = owner
        self.text = ''
        self.accept_event = self.cancel_event = None

    def SetText(self, text):
        self.text = text or ''

    SetText1 = SetText

    def SetText2(self, text):
        if text:
            self.text = (self.text + ' ' + text).strip()

    def SetAcceptText(self, text):
        self.accept_text = text

    def SetCancelText(self, text):
        self.cancel.SetText(text)
        self.cancel.FitWidth(150 if self.kit.prof == '1080' else 128)

    def SetAcceptEvent(self, event):
        self.accept_event = event

    def SetCancelEvent(self, event):
        self.cancel_event = event

    def Open(self, text=None, on_accept=None, on_cancel=None, **extra):
        if text is None:
            text, on_accept, on_cancel = self.text, self.accept_event, self.cancel_event
        uikit.Confirm.Open(self, text, on_accept, on_cancel, **extra)

    def OpenConflict(self, message, replace_event, cancel_event):
        self.Open(message, replace_event, cancel_event)


class KitNotice(KitQuestion):
    """uiCommon.PopupDialog API: a message and one button; Esc and the cross close it too."""

    def __init__(self, kit, owner, capture=None):
        KitQuestion.__init__(self, kit, owner, Tr('Upozornění', 'Notice'), Tr('Rozumím', 'OK'), '')
        self.capture = capture          # a refused key keeps the capture open: it gets the keyboard back
        self.cancel.Hide()

    def Close(self):
        capture = self.capture
        if capture is not None and capture.IsShow():
            self.KillFocus()
            self.Hide()
            capture.SetFocus()
            return
        KitQuestion.Close(self)

    def Open(self, text=None, on_accept=None, on_cancel=None, **extra):
        KitQuestion.Open(self, text, on_accept, on_cancel, **extra)
        self.cancel.Hide()
        x, y = self.accept.GetLocalPosition()
        self.accept.SetPosition((self.w - self.accept.w) // 2, y)


def KeyDialogs(kit, owner):
    """(capture, conflict, restore, popup) dialogs of the key bindings page in the kit look; None when the A7
    binding page has no capture dialog in this client."""
    capture_class = CaptureDialogClass()
    if capture_class is None:
        return None
    cancel = _locale('KEYBIND_CANCEL', Tr('Zrušit', 'Cancel'))
    capture = capture_class(kit, owner)
    conflict = KitQuestion(kit, owner, Tr('Potvrzení', 'Confirm'), _locale('KEYBIND_REPLACE', Tr('Nahradit', 'Replace')),
                           cancel)
    restore = KitQuestion(kit, owner, Tr('Potvrzení', 'Confirm'), Tr('Obnovit', 'Reset'), cancel)
    popup = KitNotice(kit, owner, capture)
    return capture, conflict, restore, popup


# --------------------------------------------------------------------------- sky picker
class SkyTile(uikit.Interactive):
    """One sky: the original thumbnail at its native size in a thin frame (bronze, gold on hover, ruby = the sky in
    use) and its name under it. A click selects it."""
    RING = 2

    def __init__(self, picker, kit, index, label, x, y, selected, event):
        uikit.Interactive.__init__(self)
        self.kit, self.index, self.selected = kit, index, bool(selected)
        r, (sw, sh) = self.RING, SKY_SIZE
        self.w, self.h = sw + 2 * r, sh + 2 * r + 4 + kit.cell('S')
        self.SetParent(picker)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, self.h)
        self.ring = [uikit.Rect(self, 0, 0, 1, 1, T.BRONZE_LINE) for unused in range(4)]
        self.image = ui.ImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        self.image.LoadImage(SKY_PATH % (index + 1))
        self.image.SetPosition(r, r)
        self.image.Show()
        self.label = uikit.Text(self, label, self.w // 2, sh + 2 * r + 3, kit.font('S'), T.INK, align='center',
                                valign='top')
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        state = self.state()
        if self.selected:
            color, t = T.RUBY_HI, 2
        elif state in ('hover', 'pressed'):
            color, t = T.GOLD_HI, 2
        else:
            color, t = T.BRONZE_LINE, 1
        r, (sw, sh) = self.RING, SKY_SIZE
        for bar, (x, y, w, h) in zip(self.ring, ((r - t, r - t, sw + 2 * t, t), (r - t, r + sh, sw + 2 * t, t),
                                                 (r - t, r, t, sh), (r + sw, r, t, sh))):
            bar.SetPosition(x, y)
            bar.SetSize(w, h)
            bar.SetColor(uikit.GenerateColor(color))
        self.label.SetPackedFontColor(T.GOLD_HI if self.selected or state in ('hover', 'pressed') else T.INK)


class SkyPicker(ui.Window):
    """Kit window of the sky choice: dialog title bar with the cross, 4 x 3 thumbnails, the current one framed."""

    def __init__(self, kit, owner, skies, current):
        ui.Window.__init__(self)
        self.kit, self.owner = kit, owner
        self.AddFlag('float')
        self.AddFlag('movable')
        w, h = SKY_WINDOW
        self.SetSize(w, h)
        self.frame = uikit.Frame(self, kit, 'window', 0, 0, w, h, bg=True)
        self.bar = uikit.TitleBar(self, kit, 5, 5, w - 10, Tr('Vybrat oblohu', 'Choose sky'), kind='dialog',
                                  on_close=owner._ClosePopup)
        self.tiles = []
        top = 5 + self.bar.Height()
        rows = (len(skies) + SKY_COLUMNS - 1) // SKY_COLUMNS
        tile_w = SKY_SIZE[0] + 2 * SkyTile.RING
        tile_h = SKY_SIZE[1] + 2 * SkyTile.RING + 4 + kit.cell('S')
        gap_x, gap_y = 2, 6
        grid_w = SKY_COLUMNS * tile_w + (SKY_COLUMNS - 1) * gap_x
        grid_h = rows * tile_h + (rows - 1) * gap_y
        x0 = (w - grid_w) // 2
        y0 = top + max(6, (h - 6 - top - grid_h) // 2)     # centred between the bar and the frame's bottom edge
        for index, label in enumerate(skies):
            x = x0 + (index % SKY_COLUMNS) * (tile_w + gap_x)
            y = y0 + (index // SKY_COLUMNS) * (tile_h + gap_y)
            self.tiles.append(SkyTile(self, kit, index, label, x, y, index == current,
                                      lambda selected=index: owner._SelectSky(selected)))
        self.OnPressEscapeKey = owner._ClosePopup

    def Open(self):
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()


def OpenSkyPicker(window, skies):
    """Opens the kit sky picker as the settings window's popup (closed by _ClosePopup, Esc or a choice)."""
    window._ClosePopup()
    picker = SkyPicker(window.kit, window, skies, window.value('sky'))
    window.popup = picker
    picker.Open()
    return picker
