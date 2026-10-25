# -*- coding: utf-8 -*-
"""The common dialogs of uicommon in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md). Visual only.

uicommon keeps every dialog class, its uiscript, size and API: PopupDialog (OK), QuestionDialog (Ano / Ne),
QuestionDialog2 and QuestionDialogWithTimeLimit (two lines + Ano / Ne), InputDialog,
InputDialogWithDescription(2) (title, description, field, OK / Zrušit) and MoneyInputDialog (title, average price,
field, the amount, OK / Zrušit). Dress() draws R1 INTO the loaded dialog:

* the dialog frame of R1 (no header, a soft shadow) under the board; the board stays the parent of every element
  (callers add their own images to dialog.board) - only its frame pieces and title bar are hidden;
* the title of a board with a title bar becomes the first line of the dialog (the question), Noto Sans;
* texts in Noto Sans; the message of the OK and Ano / Ne dialogs in the token role 'message' (the large cell, the
  dialog has room for it) and 'message_s' when the text would not fit the dialog's width - re-fitted on every text
  change (Fit) and re-layout. Fonts only through the roles of uir1tokens;
* the input slot becomes the R1 field around the SAME edit line (dialog.inputValue);
* the buttons become R1 buttons with the ui.Button API the callers use (SetEvent, SAFE_SetEvent, CallEvent,
  SetText, Enable / Disable, Down / SetUp, ...), the main action (Ano / OK) on the LEFT with the red vein, Ne /
  Zrušit on the right: the rule of the whole client (confirm left, cancel right) and of the original uicommon
  dialogs. dialog.acceptButton / cancelButton and GetChild() return them;
* Esc / Enter keep their handlers; the window keeps its size (SetWidth / SetBoardWidth re-lay it out) - except the
  Ano / Ne dialogs, which uicommon widens to their longest message line (MESSAGE_MARGIN per side, then re-laid out).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original dialog. When building R1 raises, the
dialog goes back to its original look (traced, uir1.TraceFailure) and keeps working.
"""
import weakref

import ui

import uir1
import uir1tokens as T

GAP = 10                # px between the buttons
TOP = 8                 # first stacked line from the top edge
# (button height, bottom margin) tried in this order until the stacked lines get MIN_GAP px between them
BUTTON_FITS = ((T.BTN_H, T.PAD), (T.BTN_H, 10), (T.BTN_H_S, 10), (T.BTN_H_S, 8))
MIN_GAP = 5

# A text in this role steps down to FIT_ROLES[role] when it would not fit the dialog's width minus 2 * PAD.
FIT_ROLES = {'message': 'message_s'}
MESSAGE_MARGIN = T.PAD  # px between a message line and the dialog edge (Fit; uicommon widens the Ano / Ne dialogs)

# kind -> texts (child name, font role, colour or None = keep), stacked (True: title / texts / field one under the
# other; False: the texts keep their y (QuestionDialog2: callers place icons next to them) or a single message is
# centred above the buttons), buttons (child name, dialog attribute, primary) from left to right.
KINDS = {
    'popup': dict(texts=(('message', 'message', T.INK),), stacked=False,
                  buttons=(('accept', 'accceptButton', True),)),
    # networkmodule.PopupDialog (the game's stream popup: game.PopupMessage, e.g. "Nemáš dostatek yangů" while
    # trading): it lays out its own message lines (MessageFont) and sizes its board; R1 draws the frame and the OK
    'stream_popup': dict(texts=(), stacked=False, buttons=(('accept', 'acceptButton', True),)),
    'question': dict(texts=(('message', 'message', T.INK),), stacked=False,
                     buttons=(('accept', 'acceptButton', True), ('cancel', 'cancelButton', False))),
    'question2': dict(texts=(('message1', 'message', T.INK), ('message2', 'message', T.INK)), stacked=False,
                      keep_y=True,
                      buttons=(('accept', 'acceptButton', True), ('cancel', 'cancelButton', False))),
    'input': dict(texts=(), stacked=True, title=True, field=('InputSlot', 'InputValue'),
                  buttons=(('AcceptButton', 'acceptButton', True), ('CancelButton', 'cancelButton', False))),
    'input_desc': dict(texts=(('Description', 'text_s', T.INK_DIM),), stacked=True, title=True,
                       field=('InputSlot', 'InputValue'),
                       buttons=(('AcceptButton', 'acceptButton', True), ('CancelButton', 'cancelButton', False))),
    'input_desc2': dict(texts=(('Description1', 'text_s', T.INK_DIM), ('Description2', 'text_s', T.INK_DIM)),
                        stacked=True, title=True, field=('InputSlot', 'InputValue'),
                        buttons=(('AcceptButton', 'acceptButton', True), ('CancelButton', 'cancelButton', False))),
    # the average price keeps its green, the field sits between it and the amount
    'money': dict(texts=(('AverageValue', 'text_s', None), ('@field', None, None), ('MoneyValue', 'text_s', T.INK)),
                  stacked=True, title=True, field=('InputSlot', 'InputValue'),
                  buttons=(('AcceptButton', 'acceptButton', True), ('CancelButton', 'cancelButton', False))),
}


def _sound():
    try:
        import snd
        snd.PlaySound('sound/ui/click.wav')
    except Exception:
        pass


class DialogButton(uir1.Button):
    """R1 button standing in for a dialog's ui.Button: the API the callers of uicommon use, the look of R1."""

    def __init__(self, parent, kit, native, primary, small):
        try:
            text = native.GetText()
        except Exception:
            text = ''
        self.down = False                       # read by state() while the base class paints
        uir1.Button.__init__(self, parent, kit, 0, 0, T.BTN_W, text, primary, small)
        self.native = native
        self.eventFunc = getattr(native, 'eventFunc', None)
        self.eventArgs = tuple(getattr(native, 'eventArgs', None) or ())

    # ui.Button API -----------------------------------------------------------------------------------------------
    def SetEvent(self, func, *args):
        self.eventFunc = func
        self.eventArgs = args

    def SAFE_SetEvent(self, func, *args):
        self.eventFunc = ui.__mem_func__(func)
        self.eventArgs = args

    def CallEvent(self):
        _sound()
        if self.eventFunc:
            self.eventFunc(*self.eventArgs)

    def click(self):
        if not self.down:
            self.CallEvent()

    def SetText(self, text, height=4):
        uir1.Button.SetText(self, text)

    def IsDisable(self):
        return not self.enabled

    def Down(self):
        self.down = True
        self.paint()

    def SetUp(self):
        self.down = False
        self.paint()

    def IsDown(self):
        return self.down

    def state(self):
        if self.enabled and self.down:
            return 'pressed'
        return uir1.Button.state(self)

    def _ignore(self, *args, **kwargs):
        """Native visuals, fonts and flashing of the original button: R1 draws the button itself."""

    SetUpVisual = SetOverVisual = SetDownVisual = SetDisableVisual = _ignore
    SetFontName = SetTextColor = SetOutline = Over = Flash = FlashEx = EnableFlash = DisableFlash = _ignore
    LeftRightReverse = _ignore

    def SetToolTipText(self, text, x=0, y=-19):
        pass


class DialogSkin(object):
    """R1 drawn into one loaded uicommon dialog (see the module doc). Layout() after a size or text change,
    Destroy() when the dialog loads another script, Undo() restores the original look."""

    def __init__(self, dialog, kind):
        # A proxy: the dialog holds its skin, a strong reference back would keep a dropped dialog (and its native
        # windows) alive until the cyclic garbage collector runs.
        self.dialog, self.kind, self.spec = weakref.proxy(dialog), kind, KINDS[kind]
        self.board = dialog.board
        self.kit = uir1.Kit()
        self.undo = []
        self.frame = self.title = self.field = None
        self.buttons = []
        self.texts = []
        self.fitted = {}                # child name -> (text, width, font) of the last Fit
        self.roles = {}                 # child name -> font role
        self.probe = None
        try:
            self._Build(dialog)
            self.Layout()
        except Exception:
            self.Undo()
            raise

    # build -----------------------------------------------------------------------------------------------------
    def _Child(self, name):
        return self.dialog.GetChild(name)

    def _Hide(self, widget):
        if widget is not None and widget.IsShow():
            widget.Hide()
            self.undo.append(widget.Show)

    def _Build(self, dialog):
        board, spec, kit = self.board, self.spec, self.kit
        w, h = board.GetWidth(), board.GetHeight()
        self.frame = uir1.DialogFrame(dialog, 0, 0, w, h)
        self.undo.append(self.frame.Hide)
        # The board with everything on it above the frame: a re-parent to another window moves it to the end of the
        # dialog's children (a SetParent to the same parent would not move it).
        holder = ui.Window()
        board.SetParent(holder)
        board.SetParent(dialog)
        for piece in list(getattr(board, 'Corners', ())) + list(getattr(board, 'Lines', ())) + \
                [getattr(board, 'Base', None)]:
            self._Hide(piece)
        bar = getattr(board, 'titleBar', None)
        parts = uir1.TitleBarParts(bar, board) if bar is not None else None
        for piece in parts if parts is not None else [bar]:      # the title bar stays: the drag handle
            self._Hide(piece)
        self.small, self.bottom = self._ButtonFit(h)
        for name, role, color in spec['texts']:
            if name == '@field':
                continue
            line = self._Child(name)
            self.undo.append(lambda line=line, at=line.GetLocalPosition(), recolour=color is not None:
                             self._RestoreText(line, at, recolour))
            uir1.SetFont(line, kit.font(role))
            self.fitted[name] = (None, None, kit.font(role))
            if color is not None:
                line.SetPackedFontColor(color)
            line.SetVerticalAlignCenter()
            self.texts.append((name, line))
            self.roles[name] = role
        if spec.get('title'):
            name = ''
            title_line = getattr(board, 'titleName', None)
            if title_line is not None:
                name = title_line.GetText()
            self.title = uir1.Text(board, name, w // 2, 0, kit.font('text'), T.INK, align='center')
            self.undo.append(self.title.Hide)
        if spec.get('field'):
            slot_name, edit_name = spec['field']
            slot, edit = self._Child(slot_name), self._Child(edit_name)
            self._Hide(slot)
            restore = (edit.GetLocalPosition(), edit.GetWidth(), edit.GetHeight())

            def put_back(edit=edit, slot=slot, restore=restore):
                edit.SetParent(slot)
                edit.SetPosition(*restore[0])
                edit.SetSize(restore[1], restore[2])
            self.undo.append(put_back)
            self.field = uir1.Field(board, kit, T.PAD, 0, max(10, w - 2 * T.PAD), edit=edit, max_len=12)
            self.undo.append(self.field.Hide)
        elements = getattr(dialog, 'ElementDictionary', None)
        for name, attr, primary in spec['buttons']:
            native = self._Child(name)
            button = DialogButton(board, kit, native, primary, self.small)
            self._Hide(native)
            self.buttons.append(button)
            if elements is not None:
                elements[name] = button
            setattr(dialog, attr, button)
            self.undo.append(lambda name=name, attr=attr, native=native, button=button: self._Restore(
                name, attr, native, button))

    @staticmethod
    def _RestoreText(line, at, recolour):
        """Back in the default font at its place; a recoloured text gets the original white again."""
        import fontconfig
        uir1.SetFont(line, fontconfig.FontForRole(fontconfig.ROLE_BODY))
        if recolour:
            line.SetPackedFontColor(0xFFFFFFFF)
        line.SetPosition(*at)

    def _Restore(self, name, attr, native, button):
        """The original button back with what the callers set on the R1 one (event, text, disabled)."""
        button.Hide()
        if button.eventFunc is not None:
            native.SetEvent(button.eventFunc, *button.eventArgs)
        try:
            native.SetText(button.GetText())
            if not button.enabled:
                native.Disable()
        except Exception:
            pass
        elements = getattr(self.dialog, 'ElementDictionary', None)
        if elements is not None and elements.get(name) is button:
            elements[name] = native
        if getattr(self.dialog, attr, None) is button:
            setattr(self.dialog, attr, native)

    def _ButtonFit(self, h):
        """(small buttons, bottom margin): the first of BUTTON_FITS leaving MIN_GAP between the stacked lines."""
        if not self.spec['stacked']:
            return False, T.PAD
        need = self._StackHeights(True)
        for bh, bottom in BUTTON_FITS:
            if self._Gap(h, bh, bottom, need) >= MIN_GAP:
                return bh == T.BTN_H_S, bottom
        bh, bottom = BUTTON_FITS[-1]
        return bh == T.BTN_H_S, bottom

    def _StackHeights(self, with_title):
        heights = []
        if self.spec.get('title') and with_title:
            heights.append(self.kit.cell('text'))
        for name, role, color in self.spec['texts']:
            heights.append(T.FIELD_H if name == '@field' else self.kit.cell(role))
        if self.spec.get('field') and not any(name == '@field' for name, role, color in self.spec['texts']):
            heights.append(T.FIELD_H)
        return heights

    @staticmethod
    def _Gap(h, bh, bottom, heights):
        return float(h - bottom - bh - TOP - sum(heights)) / max(1, len(heights))

    # layout ----------------------------------------------------------------------------------------------------
    def Fit(self):
        """The message lines in their large role, or the smaller one when the text would not fit the width (the
        callers set the text before or after Open, the time-limit dialog every frame: nothing is done while the text
        and the width stay the same)."""
        w = self.board.GetWidth()
        for name, line in self.texts:
            role = self.roles.get(name)
            if role not in FIT_ROLES:
                continue
            text = line.GetText()
            last_text, last_w, font = self.fitted.get(name, (None, None, None))
            if (text, w) == (last_text, last_w):
                continue
            large = self.kit.font(role)
            wanted = large if self._Width(text, large) <= w - 2 * MESSAGE_MARGIN else self.kit.font(FIT_ROLES[role])
            if wanted != font:
                uir1.SetFont(line, wanted, text)
            self.fitted[name] = (text, w, wanted)

    def _Width(self, text, font):
        if not text:
            return 0
        if self.probe is None:
            self.probe = ui.TextLine()
        if getattr(self, 'probe_font', None) != font:
            uir1.SetFont(self.probe, font, '')
            self.probe_font = font
        self.probe.SetText(text)
        return uir1.TextWidth(self.probe)

    def Layout(self):
        board = self.board
        w, h = board.GetWidth(), board.GetHeight()
        self.Fit()
        self.frame.Resize(w, h)
        bh = T.BTN_H_S if self.small else T.BTN_H
        by = h - self.bottom - bh
        count = len(self.buttons)
        bw = max(40, min(T.BTN_W, (w - 2 * T.PAD - (count - 1) * GAP) // count))
        x = (w - (count * bw + (count - 1) * GAP)) // 2
        for button in self.buttons:
            button.SetPosition(x, by)
            button.SetWidth(bw)
            x += bw + GAP
        if self.field is not None:
            self.field.SetWidth(max(10, w - 2 * T.PAD))
        if self.spec['stacked']:
            self._Stack(w, h, by)
        elif not self.spec.get('keep_y'):
            for name, line in self.texts:
                self._Place(line, by // 2 + 1)

    @staticmethod
    def _Place(line, y):
        x = line.GetLocalPosition()[0]
        line.SetPosition(x, int(y))

    def _Stack(self, w, h, by):
        items = []
        if self.title is not None and self.title.GetText():
            items.append(('title', self.title, self.kit.cell('text')))
        field_listed = False
        lines = dict(self.texts)
        for name, role, color in self.spec['texts']:
            if name == '@field':
                items.append(('field', self.field, T.FIELD_H))
                field_listed = True
            else:
                items.append(('text', lines[name], self.kit.cell(role)))
        if self.field is not None and not field_listed:
            items.append(('field', self.field, T.FIELD_H))
        gap = max(2.0, float(by - TOP - sum(i[2] for i in items)) / max(1, len(items)))
        y = float(TOP)
        for kind, widget, height in items:
            if kind == 'field':
                widget.SetPosition(T.PAD, int(round(y)))
            elif kind == 'title':
                widget.SetPosition(w // 2, int(round(y + height / 2.0)))
            else:
                self._Place(widget, round(y + height / 2.0))
            y += height + gap

    def SetTitle(self, name):
        if self.title is not None:
            self.title.SetText(name or '')
            self.Layout()

    # teardown --------------------------------------------------------------------------------------------------
    def Destroy(self):
        """The dialog loaded another script (QuestionDialog2 over QuestionDialog): drop this skin's own widgets."""
        for widget in [self.frame, self.title, self.field] + self.buttons:
            if widget is not None:
                widget.Hide()
        self.undo = []
        self.buttons, self.texts = [], []
        self.frame = self.title = self.field = None
        self.board = self.dialog = None

    def Undo(self):
        for step in reversed(self.undo):
            try:
                step()
            except Exception:
                pass
        self.undo = []


# --------------------------------------------------------------------------- entry points for uicommon
def Dress(dialog, kind):
    """R1 into a freshly loaded dialog (replaces the skin of an earlier load); None in the original look."""
    old = getattr(dialog, 'r1skin', None)
    if old is not None:
        old.Destroy()
    dialog.r1skin = None
    if not uir1.UseR1():
        return None
    try:
        dialog.r1skin = DialogSkin(dialog, kind)
    except Exception:
        uir1.TraceFailure('dialog %s' % kind)
        dialog.r1skin = None
    return dialog.r1skin


def DressPopup(dialog, kind='popup'):
    """R1 into a dialog loaded from UIScript/PopupDialog.py outside uicommon (networkmodule, uiuploadmark,
    uiselectmusic, uigameoptionnew), after its buttons got their events; None in the original look. Never raises."""
    try:
        dialog.board = dialog.GetChild('board')
    except Exception:
        uir1.TraceFailure('dialog %s board' % kind)
        return None
    return Dress(dialog, kind)


def MessageFont(dialog, default):
    """(font, signed packed colour or None) of the message lines a dressed stream popup lays out itself: the R1
    message role in the ink colour; ``default`` and None (keep the colour) in the original look."""
    skin = getattr(dialog, 'r1skin', None)
    if skin is None:
        return default, None
    color = int(T.INK) & 0xFFFFFFFF
    return skin.kit.font('message'), color - 0x100000000 if color > 0x7FFFFFFF else color


def Layout(dialog):
    skin = getattr(dialog, 'r1skin', None)
    if skin is None or getattr(dialog, 'board', None) is not skin.board:
        return
    try:
        skin.Layout()
    except Exception:
        uir1.TraceFailure('dialog %s layout' % skin.kind)
        skin.Undo()
        dialog.r1skin = None


def Fit(dialog):
    """After a caller changed a message text: the message font role that fits (see DialogSkin.Fit)."""
    skin = getattr(dialog, 'r1skin', None)
    if skin is None or getattr(dialog, 'board', None) is not skin.board:
        return
    try:
        skin.Fit()
    except Exception:
        uir1.TraceFailure('dialog %s fit' % skin.kind)
        skin.Undo()
        dialog.r1skin = None


def SetTitle(dialog, name):
    skin = getattr(dialog, 'r1skin', None)
    if skin is None:
        return
    try:
        skin.SetTitle(name)
    except Exception:
        uir1.TraceFailure('dialog %s title' % skin.kind)
        skin.Undo()
        dialog.r1skin = None
