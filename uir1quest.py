# -*- coding: utf-8 -*-
"""The NPC dialog (uiquest.QuestDialog) in the R1 look (docs/ALTHEA_R1_KIT.md).

The quest dialog stays what it is: the game creates it for every page of a conversation, the event set draws the
conversation text (the game's default font), the answers, Dále / OK / Zrušit, the input field, the quest pictures,
the cinema skin and the special skin 3 keep every event, Enter / Esc / the arrow keys keep their meaning.

R1 draws the dialog frame and the buttons and, since 9. 10. 2026 (owner: the guild village guardian, Stařenka, the
fisherman, Deokbae - "a dark box with a huge empty space below two or three buttons, labels running out of the
buttons, no title"), lays the ordinary dialog out to its content:

* the board is as tall as its content: equal margins (MARGIN) around the text and the buttons, MIN_H at least; the
  top edge stays where the 350 x 300 board had it (TOP in the 800 x 450 dialog), so the window grows downwards while
  the text is typed and moves up only when a long page would leave the dialog;
* a menu without text (the NPC chat menu: "Resetovat schopnosti", "Otevřít stánek", the guild options, ...) gets
  the NPC's name as the centred R1 title when the client knows the NPC (the clicked target next to the player) and is
  as wide as its longest answer; a dialog with text keeps the 350 px of the board (the game wraps the text by
  characters for that width) and its own title line (say_title);
* the answers are R1 buttons of ONE width - the longest label plus LABEL_PAD a side, between CHOICE_MIN and
  CHOICE_MAX - in a centred column, GAP apart; a label that would still not fit steps down to the smaller font and,
  only past that, is shortened with "..." and shown whole in the hover hint. No label leaves its button;
* the closing answer ("Zavřít", "Zrušit") is the last item: the R1 secondary dialog button, centred under a quiet
  divider (the intended separator of the R1 rules). Dále / OK are the R1 primary button, Zrušit the secondary one,
  confirm left, cancel right;
* more than MAX_ROWS answers (or what fits the dialog) scroll: the R1 scroll bar beside the column, the mouse wheel
  over the dialog, and the arrow keys bring the focused answer into view (they still cycle through all answers).
  The original pages (Zpět / Další) are not used in R1.

A quest that places the dialog itself (window size, pictures, an explicit text position) or the cinema skin keeps
the original geometry (Fix): R1 only dresses it.

Settings -> "Starý vzhled" (settingslook 'legacy') shows the original dialog; a failure while building or laying
out R1 is traced to syserr and the original geometry is used (and the original dialog for every later one in this
session).
"""
import weakref

import uikit
import uir1
import uir1layout as L
import uir1tokens as T

_failed = False
_classes = {}

MARGIN = 14            # frame edge -> text / buttons, on every side
GAP = 6                # between two answers
TEXT_GAP = 10          # last text line -> first button
HEAD_GAP = 8           # title vein -> first answer
ROW_H = L.button_height(False)
PITCH = ROW_H + GAP
LABEL_PAD = 12         # label -> button edge when the width is chosen
LABEL_ROOM = 8         # least label -> button edge before the label steps down / is shortened
CHOICE_MIN = 200       # the width of the original answer bars
CHOICE_MAX = 360
ACTION_W = T.BTN_W     # Dále / OK / Zrušit / Zavřít
ACTION_GAP = 10        # between OK and Zrušit
SEP_ABOVE = 9          # last answer -> divider, divider -> Zavřít
SEP_BELOW = 9
MAX_ROWS = 8           # answers shown at once (QuestDialog.QUEST_BUTTON_MAX_NUM)
MIN_ROWS = 3           # never fewer, however long the text above them
SCROLL_GAP = 6
MIN_H = 80
TOP = 75               # top edge of the original board in the dialog: (450 - 300) / 2
EDGE = 8               # least room between the board and the dialog's top / bottom
TITLE_PAD = 16         # title -> frame side
LINE_H = 16            # one line of the event set (PythonEventManager c_fLine_Temp)
NEXT_SPACE = 16 + 5    # the event set adds this before MakeNextButton
INPUT_SPACE = 15       # QuestDialog.OnInput adds this before the input slot
TALK_RANGE = 800.0     # the NPC must stand next to the player (clickable distance of an NPC is 500)
CLOSE_LABELS = (u'zavřít', u'zavrit', u'zrušit', u'zrusit', u'close', u'cancel', u'schließen', u'abbrechen')


def UseR1():
    """R1 unless Settings -> "Starý vzhled" chose the original look, or R1 already failed in this session."""
    return not _failed and uir1.UseR1()


def _text(value):
    if isinstance(value, bytes):
        try:
            return value.decode('cp1250')
        except Exception:
            return value.decode('latin-1')
    return value or u''


def IsCloseLabel(text, extra=()):
    """The closing answer of a menu (the NPC chat menu ends with "Zavřít")."""
    key = _text(text).strip().strip(u'.!').strip().lower()
    labels = set(CLOSE_LABELS)
    for label in extra:
        if label:
            labels.add(_text(label).strip().lower())
    return bool(key) and key in labels


def NpcName():
    """Name of the NPC the player talks to: the target (clicking an NPC targets it first) when it is an NPC standing
    next to the player; '' when the client does not know it (a quest scroll, an item, an older EXE)."""
    try:
        import chr
        import player
        vid = player.GetTargetVID()
        if not vid or chr.GetInstanceType(vid) != chr.INSTANCE_TYPE_NPC:
            return ''
        distance = player.GetCharacterDistance(vid)
        if distance is None or distance < 0 or distance > TALK_RANGE:
            return ''
        return chr.GetNameByVID(vid) or ''
    except Exception:
        return ''


_probe = []


def Measure(text, font):
    """Width of ``text`` in ``font`` (one hidden probe line per client)."""
    import ui
    if not _probe:
        _probe.append(ui.TextLine())
    uikit.SetFont(_probe[0], font, text)
    return uikit.TextWidth(_probe[0])


def BarButtonClass(base):
    """R1 variant of uiquest.BarButton (the same events: SetEvent / CallEvent / DownEvent / ShowToolTip /
    HideToolTip from the native button, the arrow keys call ShowToolTip / HideToolTip too), painted with the R1 button
    textures instead of grey bars. Role 'choice' (an answer: secondary plate, Noto Sans label) or 'action' (Dále / OK /
    Zrušit / Zavřít: the Cinzel label of the R1 dialog buttons, primary = the red vein). The label is centred and never
    leaves the plate: it steps down to the smaller font, then is shortened (the whole text in the hover hint)."""
    if base in _classes:
        return _classes[base]

    class R1BarButton(base):
        PLATE_H = L.button_height(False)

        def __init__(self, layer='UI', *colors):
            base.__init__(self, layer, *colors)
            self.kit = uir1.Kit()
            self.role, self.primary = 'choice', False
            self.fontName = self.kit.font('text')          # ui.Button.SetText creates its label in this font
            self.r1state = 'normal'
            self.fullText = ''
            self.cut = False
            self.plate = uir1.Ops(self, L.button(False, False, 'normal', 64))   # images before the label
            # Own label (ui.Button.SetText reuses an existing ButtonText): a top-aligned line centred by position on
            # the plate (uir1.CellTop) - the engine clips a text line from its y down by the text height, a line
            # vertically centred at h / 2 would lose its descenders.
            self.ButtonText = uir1.Text(self, '', 0, 0, self.fontName, T.BUTTON_TEXT, align='center', valign='top')

        def Fonts(self):
            if self.role == 'action':
                return self.kit.font('button'), self.kit.font('button_s')
            return self.kit.font('text'), self.kit.font('text_s')

        def SetRole(self, role, primary=False):
            if (role, bool(primary)) != (self.role, self.primary):
                self.role, self.primary = role, bool(primary)
                self.FitLabel()
                self.Paint()

        def NaturalWidth(self):
            """Width of the whole label in the role's larger font (cached: the layout asks every frame)."""
            font = self.Fonts()[0]
            key = (self.fullText, font)
            if getattr(self, 'natural', (None, 0))[0] != key:
                self.natural = (key, Measure(uir1.WordGap(self.fullText, font), font))
            return self.natural[1]

        def FitLabel(self):
            room = max(1, self.GetWidth() - 2 * LABEL_ROOM)
            large, small = self.Fonts()
            font = large
            if self.fullText and Measure(uir1.WordGap(self.fullText, large), large) > room:
                font = small
            shown = uir1.WordGap(self.fullText, font)
            self.fontName = font
            uir1.SetFont(self.ButtonText, font, shown)
            self.cut = False
            if self.fullText and uir1.TextWidth(self.ButtonText) > room:
                uir1.Fit(self.ButtonText, shown, room)
                self.cut = True

        def SetSize(self, width, height):
            base.SetSize(self, width, height)
            if self.fullText:
                self.FitLabel()
            self.Paint()

        def SetText(self, text, height=4):
            base.SetText(self, text, height)
            self.fullText = text or ''
            self.FitLabel()
            self.Paint()

        def GetText(self):
            return self.fullText

        def SetTextColor(self, color):
            # The dialog asks for white text on its grey bars; the R1 plate keeps the R1 button text colour.
            self.Paint()

        def Paint(self):
            w, h = self.GetWidth(), self.GetHeight()
            top = max(0, (h - self.PLATE_H) // 2)
            self.plate.dy = top
            self.plate.Apply(L.button(self.primary, False, self.r1state, max(w, 2 * T.BUTTON_CAP + 1)))
            y = top + uir1.CellTop(self.PLATE_H, self.fontName)
            if self.r1state == 'pressed' and y + uir1.FontCell(self.fontName) < top + self.PLATE_H:
                y += 1
            self.ButtonText.SetPosition(w // 2, y)
            self.ButtonText.SetPackedFontColor(T.PRIMARY_TEXT if self.primary else T.BUTTON_TEXT)

        def SetState(self, state):
            if state != self.r1state:
                self.r1state = state
                self.Paint()

        def OnRender(self):
            pass

        def CallEvent(self):
            self.SetState('normal')
            uir1.HideHint()
            base.CallEvent(self)

        def DownEvent(self):
            base.DownEvent(self)
            self.SetState('pressed')

        def ShowToolTip(self):
            base.ShowToolTip(self)
            self.SetState('hover')
            if self.cut:
                uir1.ShowHint(self.kit, self, self.fullText)

        def HideToolTip(self):
            base.HideToolTip(self)
            self.SetState('normal')
            if self.cut:
                uir1.HideHint()

    _classes[base] = R1BarButton
    return R1BarButton


def _clamp(value, low, high):
    return max(low, min(high, value))


class DialogSkin(object):
    """The R1 frame inside the quest board (created right after the board is loaded, so it lies under every button,
    picture and field the quest adds later) and the layout of the ordinary dialog."""

    def __init__(self, board, dialog=None):
        self.ref = weakref.ref(board)
        self.owner = weakref.ref(dialog) if dialog is not None else (lambda: None)
        self.kit = uir1.Kit()
        self.hidden = []
        self.frame = None
        self.size = None
        self.internal = True
        self.home = None            # board size and position as the game made them (Fix restores them)
        self.placed = False         # the board aligned left / top in the dialog (R1 places it), not centred
        self.fixed = False
        self.title = None           # NPC name, looked up once the dialog turns out to be a menu
        self.header = None
        self.divider = None
        self.scroll = None
        self.textEnd = None         # y of the end of the text (text coordinates), fixed once a control appears
        self.offset = 0             # first answer shown
        self.visible = 0
        self.choices = []
        self.key = None

    @property
    def board(self):
        return self.ref()

    def Build(self):
        board = self.board
        self.home = ((board.GetWidth(), board.GetHeight()), tuple(board.GetLocalPosition()))
        self.frame = uir1.DialogFrame(board, 0, 0, board.GetWidth(), board.GetHeight())
        self.size = (board.GetWidth(), board.GetHeight())
        for widget in list(board.Corners) + list(board.Lines) + [board.Base]:
            widget.Hide()
            self.hidden.append(widget)
        # The dialog hides / shows the board's own art (a background picture covers it): the R1 frame follows.
        board.HideInternal = self.HideInternal
        board.ShowInternal = self.ShowInternal

    def Sync(self):
        """Follows the board size (the quest changes it while the dialog is open)."""
        board = self.board
        if board is None or self.frame is None:
            return
        size = (board.GetWidth(), board.GetHeight())
        if size != self.size:
            self.size = size
            self.frame.Resize(*size)

    def HideInternal(self):
        self.internal = False
        if self.frame is not None:
            self.frame.Hide()

    def ShowInternal(self):
        self.internal = True
        if self.frame is not None:
            self.frame.Show()

    def BarButton(self, base, layer='UI', *colors):
        return BarButtonClass(base)(layer, *colors)

    # ----------------------------------------------------------------------------------------------- layout
    def TextOrigin(self):
        """Board position of the event set (the original 20 / 20 when the quest places the dialog itself)."""
        if self.fixed:
            return 20, 20
        return MARGIN, MARGIN

    def Fix(self):
        """The quest places the dialog itself (size, pictures, text position): back to the game's geometry, no
        title, the answers where uiquest put them."""
        if self.fixed:
            return
        self.fixed = True
        board = self.board
        if board is not None and self.home is not None:
            (w, h), (x, y) = self.home
            if self.placed:
                board.SetWindowHorizontalAlignCenter()
                board.SetWindowVerticalAlignCenter()
                self.placed = False
            board.SetSize(w, h)
            board.SetPosition(x, y)
            self.Sync()
        for widget in (self.header, self.divider, self.scroll):
            if widget is not None:
                widget.Hide()

    def Layout(self, dialog):
        global _failed
        if self.fixed or self.frame is None or self.board is None:
            return
        try:
            self._Layout(dialog)
        except Exception:
            _failed = True
            uir1.TraceFailure('NPC dialog layout')
            self.Fix()

    def Reveal(self, dialog, index):
        """The arrow keys focused answer ``index``: scroll it into view."""
        if self.fixed or index >= len(self.choices) or not self.visible:
            return
        offset = _clamp(self.offset, index - self.visible + 1, index)
        if offset != self.offset:
            self.offset = offset
            self.key = None
            self.Layout(dialog)

    def Wheel(self, dialog, delta):
        """Mouse wheel over the dialog: one answer per notch; False when nothing scrolls (the wheel goes on)."""
        if self.fixed or len(self.choices) <= self.visible or not delta:
            return False
        offset = _clamp(self.offset + (-1 if delta > 0 else 1), 0, len(self.choices) - self.visible)
        if offset != self.offset:
            self.offset = offset
            self.key = None
            self.Layout(dialog)
        return True

    def _OnScroll(self):
        dialog = self.owner()
        if dialog is None or self.scroll is None:
            return
        span = len(self.choices) - self.visible
        offset = _clamp(int(round(self.scroll.GetPos() * span)), 0, max(0, span))
        if offset != self.offset:
            self.offset = offset
            self.key = None
            self.Layout(dialog)

    def _Header(self, width):
        if self.title is None:
            self.title = NpcName()
        if not self.title:
            return None
        if self.header is None:
            self.header = uir1.Header(self.board, self.kit, width, self.title)
        elif self.header.w != width:
            self.header.w = width
            self.header.SetSize(width, self.header.GetHeight())
            self.header.SetTitle(self.title)
        self.header.Show()
        return self.header

    def _TitleWidth(self):
        if self.title is None:
            self.title = NpcName()
        if not self.title:
            return 0
        if getattr(self, 'title_w', None) is None:
            self.title_w = Measure(uir1.Upper(self.title), self.kit.font('title'))
        return self.title_w

    def _Layout(self, dialog):
        import event
        board = self.board
        index = getattr(dialog, 'descIndex', None)
        if index is None:
            return
        lines = event.GetLineCount(index)
        flow = event.GetEventSetLocalYPosition(index)
        answers = [b for b in (dialog.btnAnswer or []) if b is not None]
        nxt, quit, slot = dialog.btnNext, dialog.btnQuit, dialog.editSlot
        images = [image for image in (dialog.images or []) if image is not None]

        # The text ends where the first control was put (the event set has added its spaces by then).
        if self.textEnd is None:
            if slot is not None:
                self.textEnd = max(0, slot.GetLocalPosition()[1] - INPUT_SPACE)
            elif answers:
                self.textEnd = max(0, flow)
            elif nxt is not None:
                self.textEnd = max(0, flow - NEXT_SPACE)
        if self.textEnd is not None:
            text_end = self.textEnd
        else:
            text_end = flow + LINE_H if (lines or flow) else 0      # being typed: room for the current line
        tx, ty = self.TextOrigin()
        for image in images:                    # inline pictures: placed by uiquest for the text origin 20 / 20
            if getattr(image, 'r1_y0', None) is None:
                image.r1_y0 = image.GetLocalPosition()[1]
            text_end = max(text_end, image.r1_y0 - 20 + image.GetHeight())
        has_text = text_end > 0 or bool(images) or slot is not None
        menu = bool(answers) and not has_text

        # roles: the answers, the closing answer, Dále / OK / Zrušit
        close = None
        choices = answers
        if len(answers) >= 2 and IsCloseLabel(answers[-1].GetText(), _CloseExtra()):
            close, choices = answers[-1], answers[:-1]
        self.choices = choices
        for button in choices:
            button.SetRole('choice')
        if close is not None:
            close.SetRole('action', False)
        if nxt is not None:
            cancel = getattr(dialog, 'nextButtonType', None) == getattr(event, 'BUTTON_TYPE_CANCEL', -1)
            nxt.SetRole('action', not cancel)
        if quit is not None:
            quit.SetRole('action', False)

        def action_width(button):
            return _clamp(button.NaturalWidth() + 2 * LABEL_PAD, ACTION_W, CHOICE_MAX)

        choice_w = 0
        if choices:
            choice_w = _clamp(max(b.NaturalWidth() for b in choices) + 2 * LABEL_PAD, CHOICE_MIN, CHOICE_MAX)
        close_w = action_width(close) if close is not None else 0
        pair = [b for b in (nxt, quit) if b is not None]
        pair_w = max([action_width(b) for b in pair] or [0])

        # vertical plan (board coordinates)
        root_h = dialog.GetHeight() or 450
        max_h = root_h - 2 * EDGE
        header_h = 0
        if menu and self._TitleWidth():
            header_h = T.HEAD_H + T.CONTENT_GAP + HEAD_GAP - MARGIN
        y = ty + header_h
        if has_text:
            y += text_end + TEXT_GAP
        slot_y = None
        if slot is not None:
            slot_y = y
            y += slot.GetHeight() + TEXT_GAP
        close_part = (SEP_ABOVE + T.RULE_H + SEP_BELOW + ROW_H) if close is not None else 0
        n = len(choices)
        visible = 0
        if n:
            budget = (max_h - y - close_part - MARGIN + GAP) // PITCH
            visible = min(n, MAX_ROWS, max(MIN_ROWS, budget))
        scrolling = n > visible
        self.visible = visible
        self.offset = _clamp(self.offset, 0, max(0, n - visible))
        rows_top = y
        if n:
            y += visible * PITCH - GAP
        close_y = None
        if close is not None:
            close_y = (y + SEP_ABOVE + T.RULE_H + SEP_BELOW) if n else y
            divider_y = y + SEP_ABOVE
            y = close_y + ROW_H
        pair_y = None
        if pair:
            pair_y = y + (TEXT_GAP if (n or close is not None) else 0)
            y = pair_y + ROW_H
        if answers or pair or slot is not None:
            h = y + MARGIN
        else:
            h = ty + text_end + MARGIN
        h = max(MIN_H, h)

        # width
        col_w = choice_w + ((SCROLL_GAP + T.SCROLL_W) if scrolling else 0)
        base_w = CHOICE_MIN + 2 * MARGIN if menu else self.home[0][0]
        w = max(base_w, col_w + 2 * MARGIN, close_w + 2 * MARGIN,
                (2 * pair_w + (len(pair) - 1) * ACTION_GAP) + 2 * MARGIN if pair else 0)
        if slot is not None:
            w = max(w, slot.GetWidth() + 2 * MARGIN)
        if header_h:
            w = max(w, self._TitleWidth() + 2 * TITLE_PAD)

        top = TOP if TOP + h <= root_h - EDGE else max(EDGE, root_h - EDGE - h)
        left = ((dialog.GetWidth() or 800) - w) // 2
        if self._Key(w, h, (left, top), text_end, answers, (close, nxt, quit, slot), images, header_h) == self.key:
            return

        if not self.placed:
            # uiscript centres the board in the 800 x 450 dialog; R1 places it (centred horizontally, the top edge
            # fixed) - the engine recomputes an aligned window only in SetPosition, not in SetSize.
            board.SetWindowHorizontalAlignLeft()
            board.SetWindowVerticalAlignTop()
            self.placed = True
        board.SetSize(w, h)
        board.SetPosition(left, top)
        self.Sync()
        if header_h:
            self._Header(w)
        elif self.header is not None:
            self.header.Hide()

        for image in images:
            x = image.GetLocalPosition()[0]
            image.SetPosition(x, image.r1_y0 + ty - 20)

        if slot is not None:
            slot.SetPosition(0, slot_y)         # horizontally centred by the game (SetWindowHorizontalAlignCenter)

        col_x = (w - col_w) // 2
        for i, button in enumerate(choices):
            button.SetSize(choice_w, ROW_H)
            if self.offset <= i < self.offset + visible:
                button.SetPosition(col_x, rows_top + (i - self.offset) * PITCH)
                button.Show()
            else:
                button.Hide()
        self._Scroll(scrolling, col_x + choice_w + SCROLL_GAP, rows_top, visible * PITCH - GAP, n)

        if close is not None:
            if n:
                if self.divider is None:
                    self.divider = uir1.Divider(board, MARGIN, divider_y, w - 2 * MARGIN)
                else:
                    self.divider.SetPosition(MARGIN, divider_y)
                    self.divider.SetSize(w - 2 * MARGIN, T.RULE_H)
                    self.divider.Apply(L.divider(0, 0, w - 2 * MARGIN))
                self.divider.Show()
            close.SetSize(close_w, ROW_H)
            close.SetPosition((w - close_w) // 2, close_y)
            close.Show()
        elif self.divider is not None:
            self.divider.Hide()

        for button in (getattr(dialog, 'prevbutton', None), getattr(dialog, 'nextbutton', None)):
            if button is not None:
                button.Hide()                   # the original pages: R1 scrolls instead

        if pair:
            total = len(pair) * pair_w + (len(pair) - 1) * ACTION_GAP
            x = (w - total) // 2
            for button in pair:                 # OK (confirm) left, Zrušit right
                button.SetSize(pair_w, ROW_H)
                button.SetPosition(x, pair_y)
                x += pair_w + ACTION_GAP

        self.key = self._Key(w, h, (left, top), text_end, answers, (close, nxt, quit, slot), images, header_h)

    def _Key(self, w, h, place, text_end, answers, controls, images, header_h):
        """Everything the layout depends on: Layout runs every frame and changes nothing when this is unchanged."""
        return (w, h, place, text_end, self.visible, self.offset, tuple(id(c) for c in controls), len(images),
                tuple((b.GetText(), b.IsShow()) for b in answers), header_h)

    def _Scroll(self, needed, x, y, height, total):
        if not needed:
            if self.scroll is not None:
                self.scroll.Hide()
            return
        if self.scroll is None:
            self.scroll = uir1.ScrollBar(self.kit)
            self.scroll.SetParent(self.board)
            self.scroll.SetScrollEvent(self._OnScroll)
        self.scroll.SetPosition(x, y)
        if self.scroll.GetHeight() != height:
            self.scroll.SetScrollBarSize(height)
        self.scroll.SetMiddleBarSize(float(self.visible) / max(1, total))
        span = max(1, total - self.visible)
        self.scroll.SetScrollStep(1.0 / span)  # one wheel notch / arrow over the bar = one answer (default 0.4)
        self.scroll.SetPos(float(self.offset) / span, False)
        self.scroll.Show()

    def Abort(self):
        for widget in self.hidden:
            widget.Show()
        self.hidden = []
        if self.frame is not None:
            self.frame.Hide()
        self.frame = None
        board = self.board
        if board is not None:
            board.__dict__.pop('HideInternal', None)
            board.__dict__.pop('ShowInternal', None)


def _CloseExtra():
    try:
        import localeInfo
        return (getattr(localeInfo, 'UI_CLOSE', ''), getattr(localeInfo, 'CLOSE', ''),
                getattr(localeInfo, 'UI_CANCEL', ''))
    except Exception:
        return ()


def Dress(board, dialog=None, fixed=False):
    """The R1 frame in the quest board; None after a traced failure (the original board is then intact).
    fixed=True: the cinema skin - only the frame, the game's geometry."""
    global _failed
    skin = DialogSkin(board, dialog)
    try:
        skin.Build()
        if fixed:
            skin.fixed = True
        return skin
    except Exception:
        _failed = True
        uir1.TraceFailure('NPC dialog')
        skin.Abort()
        return None
