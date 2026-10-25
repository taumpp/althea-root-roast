# -*- coding: utf-8 -*-
"""R1 look of the target board (the strip with the target's name and HP at the top of the screen) and of the drop
panel attached under it (uitarget.TargetBoard, uitarget.CrimsonTargetDetailsPanel). Variant A (8. 10. 2026).

Drawn INTO the existing windows like the other R1 windows: the R1 window frame instead of the tooltip ThinBoard, a
38 px header (the target's name on the left in Tahoma 12, the HP numbers above the ampoule INSIDE the frame, the
plain X without a box), and under it one row of thin R1 buttons (20 px, Tahoma 12, the label in the middle) with
shorter labels in R1 (locale keys TARGET_BUTTON_R1_*, the long label when a locale has none) and one equal 4 px gap
between every two buttons, no separator lines (variant A of 9. 10. 2026; the groups of actions only keep the order
talk, profile, relation, party). The board is as wide as its content. The HP ampoule keeps its fill, its
animation and the poison frames (the original textures and colours); only its frame and the monster details icon are
the R1 graphite (tools/build_althea_r1_cil.py), the percentage is the dimmed ivory instead of the salmon one. Every
action of TargetBoard.RefreshButton stays (the buttons keep their events). Settings -> "Starý vzhled" (uir1.UseR1()
False) keeps the original board; an exception while building or laying out is traced and puts the original look
back.
"""
import weakref

import ui
import localeInfo

import uir1
import uir1tokens as T

try:
    import uir1cilart as ART       # generated with the R1 textures; without it the board keeps the original look
except Exception:
    ART = None
try:
    import uir1formart as FORM_ART  # the "?" and "DPS" art of the unified form header (tools/build_althea_r1_form.py)
except Exception:
    FORM_ART = None
import uikit

FRAME_INSET = 2            # the frame keeps the footprint of the original ThinBoard (TARGET_CHROME_SIDE_INSET)
HEAD_H = 38                # the header: name, HP numbers above the ampoule, X (a monster board is this high)
NAME_X = 14                # the name's left edge while the HP ampoule is shown (12 px inside the frame)
GAUGE_W = 103              # TargetAnimatedHpGauge.GAUGE_FRAME_WIDTH
GAUGE_RIGHT = 131          # the ampoule starts 131 px left of the board's right edge (right aligned)
GAUGE_Y = 21
NUM_Y = 6                  # the HP numbers (Tahoma 12 like the original) inside the frame, right aligned above the
NUM_RIGHT = GAUGE_W - 2    # ampoule: their right edge 2 px left of the ampoule's right end
CLOSE_RIGHT = 27           # the X's hit box starts 27 px left of the right edge (the glyph 22 px)
CLOSE_Y = 5
ICON_ROOM = 24             # details icon (20 px) + its gap (4 px) after the name (the original placement)
# The header pair of the unified form (9. 10. 2026): "?" (opens Kořist) and the "DPS" chip (opens the DPS section),
# side by side and centred in the room between the name (with its element / race icons) and the HP block.
Q_SIZE = 20                # the "?" button (FORM_ART question_*.png)
CHIP_W = 50                # the "DPS" switch D2: label + 24 x 12 toggle (FORM_ART dps_*.png), 20 px high
PAIR_GAP = 4               # between "?" and the chip
PAIR_PAD = 11              # the least free room left and right of the pair
INFO_GAP = 5               # name -> element / race icons (uitargetinfo, variant B of 9. 10. 2026)
INFO_CAP = 400             # a monster's board grows with its name and icons up to this width, then the name gets "…"
NAME_MIN = 40              # the shortest a monster's name gets ("Lv.9…"): past it the board grows over INFO_CAP so
                           # the HP numbers never run into the name, its icons or "?"
NAME_GAP = 22              # free room between the name (or its icon) and the ampoule
NUM_GAP = 8                # free room between the name (or its icon) and the HP numbers
BUTTON_Y = 36              # the button row (20 px) under the header; the board is 64 px high with buttons
BUTTON_GAP = 4             # the one gap between every two buttons of the row, no separators (variant A)
TEXT_FONT = 'tahoma'       # the kit role of the name and the button labels: Tahoma 12 (PRAVIDLA-UI "Písmo textu")
BUTTON_PAD = 7             # label padding on each side of a button
BUTTON_MIN_W = 44
ROW_SIDE = 12              # free room left and right of the button row (10 px inside the frame)
# the own character's board (Sesednout / Konec pozorování): the ampoule, the HP numbers and the button row on one
# centre line of the board, the name left in the header as on every board (16. 10. 2026, the bar of a mounted player)
OWN_KEYS = ('TARGET_BUTTON_DISMOUNT', 'TARGET_BUTTON_EXIT_OBSERVER')
HEIGHTS = {40: HEAD_H, 65: BUTTON_Y + T.BTN_H_XS + 8}      # the original heights (plain, with buttons) in R1
PERCENT_ORIGINAL = '|cffFFA07A'
HP_TEXT_INK = T.IVORY      # the HP numbers and percentage: the name's ivory, readable over the dark header
PERCENT_R1 = '|cff%06X' % (HP_TEXT_INK & 0xFFFFFF)
DETAILS_ORIGINAL = 'local_target_board/toggle/%s.png'

# the order of the button row: talk, profile, relation, party (the rest, e.g. Sesednout, at the end)
GROUPS = (('TARGET_BUTTON_WHISPER', 'TARGET_BUTTON_EXCHANGE', 'TARGET_BUTTON_FIGHT', 'TARGET_BUTTON_ACCEPT_FIGHT',
           'TARGET_BUTTON_AVENGE'),
          ('TARGET_BUTTON_EMOTION_ALLOW',),
          ('TARGET_BUTTON_FRIEND', 'TARGET_BUTTON_BLOCK', 'TARGET_BUTTON_BLOCK_REMOVE', 'TARGET_BUTTON_INVITE_GUILD'),
          ('TARGET_BUTTON_INVITE_PARTY', 'TARGET_BUTTON_LEAVE_PARTY', 'TARGET_BUTTON_EXCLUDE',
           'TARGET_BUTTON_REQUEST_ENTER_PARTY'))
# shorter R1 labels (locale key of the original label -> locale key of the R1 label)
SHORT = {'TARGET_BUTTON_EXCHANGE': 'TARGET_BUTTON_R1_EXCHANGE',
         'TARGET_BUTTON_INVITE_PARTY': 'TARGET_BUTTON_R1_INVITE_PARTY',
         'TARGET_BUTTON_INVITE_GUILD': 'TARGET_BUTTON_R1_INVITE_GUILD',
         'TARGET_BUTTON_LEAVE_PARTY': 'TARGET_BUTTON_R1_LEAVE_PARTY',
         'TARGET_BUTTON_REQUEST_ENTER_PARTY': 'TARGET_BUTTON_R1_REQUEST_ENTER_PARTY'}


def Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def Begin(board):
    """The R1 frame, made right after the board's original chrome (so everything else draws above it); None for the
    original look or when it cannot be built."""
    if not uir1.UseR1():
        return None
    try:
        return TargetBoardLook(board)
    except Exception:
        uir1.TraceFailure('the target board')
        return None


def KeyOf(label):
    """The localeInfo key (TARGET_BUTTON_*) of an original button label, or None (e.g. "VOTE_BLOCK_CHAT")."""
    for group in GROUPS:
        for key in group:
            if getattr(localeInfo, key, None) == label:
                return key
    for key in ('TARGET_BUTTON_DISMOUNT', 'TARGET_BUTTON_EXIT_OBSERVER', 'TARGET_BUTTON_BUILDING_DESTROY'):
        if getattr(localeInfo, key, None) == label:
            return key
    return None


def ShortLabel(key, label):
    """The R1 label: the TARGET_BUTTON_R1_* text of the locale, else the original label."""
    short_key = SHORT.get(key)
    text = getattr(localeInfo, short_key, None) if short_key else None
    if not text or text == short_key:
        return label
    return text


def GroupOf(key):
    for index, group in enumerate(GROUPS):
        if key in group:
            return index
    return len(GROUPS)


class TargetButton(uir1.Button):
    """Thin R1 button (20 px, Tahoma 12) with the event API of ui.Button (SetEvent, SAFE_SetEvent, CallEvent), so
    the target board's actions stay exactly as they are. Not centre aligned: TargetBoardLook places it from the
    left. ``key`` is the locale key of the original label (None for the chat vote)."""

    def __init__(self, parent, kit, text, key=None):
        uir1.Button.__init__(self, parent, kit, 0, BUTTON_Y, BUTTON_MIN_W, ShortLabel(key, text), small='xs',
                             font=kit.font(TEXT_FONT))
        self.key = key
        self.legacyText = text
        self.group = GroupOf(key)
        self.eventFunc = None
        self.eventArgs = ()
        self.Hide()

    def SetEvent(self, func, *args):
        self.eventFunc = func
        self.eventArgs = args

    def SAFE_SetEvent(self, func, *args):
        self.eventFunc = ui.__mem_func__(func)
        self.eventArgs = args

    def CallEvent(self):
        if self.eventFunc:
            self.eventFunc(*self.eventArgs)

    def click(self):
        self.CallEvent()

    def Fit(self):
        """Fits the width to the label; one more pixel when the free room would split unevenly, so the label sits
        exactly in the middle (the same room left and right)."""
        width = self.FitWidth(BUTTON_MIN_W, BUTTON_PAD)
        if (width - uir1.TextWidth(self.label)) % 2:
            self.SetWidth(width + 1)
        return self.w


class DetailsButton(uikit.Interactive):
    """The R1 "?" of a monster (look L0 of 9. 10. 2026): FORM_ART question_<normal|hover|open>.png at native 20 px,
    the glyph optically centred in the art. Keeps the API uitarget uses on its details icon (LoadImage picks the
    open / closed state from the original visual, SetScale is ignored, SetEvent(func, "mouse_click"))."""

    def __init__(self, board, click):
        uikit.Interactive.__init__(self)
        self.SetParent(board)
        self.SetSize(Q_SIZE, Q_SIZE)
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        self.image.Show()
        self.active = False
        self.visual = None
        self.event = (click, ('mouse_click',))
        self.callback = (lambda: click('mouse_click')) if click else None
        self.paint()
        self.Hide()

    def LoadImage(self, path):
        self.active = 'inactive' not in str(path)
        self.paint()

    def SetScale(self, *unused):
        pass

    def SetEvent(self, func, *args):
        self.event = (func, args)
        self.callback = lambda: func(*args)

    def paint(self):
        if self.active:
            state = 'open'
        else:
            state = 'hover' if (self.hovered or self.pressed) else 'normal'
        if state != self.visual:
            self.visual = state
            self.image.LoadImage(FORM_ART.ROOT + 'question_%s.png' % state)


class TargetBoardLook(object):
    """The R1 dressing of one TargetBoard. Keeps only a weak reference to the board (the board owns it)."""

    def __init__(self, board):
        self.boardRef = weakref.ref(board)
        self.kit = uir1.Kit()
        self.frame = uir1.Frame(board, FRAME_INSET, 0, max(0, board.GetWidth() - 2 * FRAME_INSET),
                                max(0, board.GetHeight()), 'window')
        self.close = None
        self.info = None           # uitargetinfo.TargetInfoIcons, made on the first monster
        self.infoState = (0, False)                 # (row width, a monster target) of the last refresh
        self.infoRefit = False
        self.infoBroken = False
        self.nameFull = None       # the name measured for the board's width (and its width)
        self.nameFullW = 0
        self.nameShown = None      # the name as shown after fitting it before the icons
        self.legacyButtons = None
        self.finished = False
        self.failed = False
        self.detailsActive = False
        self.hpRoom = 0
        self.formExtra = 0         # the unified target form: its sections' height under the header (uitargetform)
        self.legacyDetails = None  # the original details icon while the R1 "?" (DetailsButton) replaces it
        self.chip = None           # the form's "DPS" chip (uitargetform.DpsChip), placed here next to "?"

    @property
    def board(self):
        return self.boardRef()

    # ------------------------------------------------------------------ build
    def Finish(self):
        """After the board made its original widgets (name, ampoule, close, buttons) and before it binds the button
        events: hides the original chrome and close, restyles the name, the ampoule's frame and the HP numbers and
        swaps in the R1 buttons. Returns self, or None after a failure (the original look is back)."""
        try:
            if ART is None:
                raise ImportError('uir1cilart')
            board = self.board
            board.chrome.Hide()
            arabic = localeInfo.IsARABIC()
            self.close = uir1.Close(board, CLOSE_RIGHT - T.X_HIT if arabic else 0, CLOSE_Y,
                                    ui.__mem_func__(board.OnPressedCloseButton))
            board.closeButton.Hide()
            uir1.SetFont(board.name, self.kit.font(TEXT_FONT))
            board.name.SetPackedFontColor(Signed(T.IVORY))
            gauge = board.hpGauge
            gauge.background.LoadImage(ART.ROOT + 'hp_gauge_frame.png')
            gauge.SetPosition(GAUGE_RIGHT - GAUGE_W if arabic else GAUGE_RIGHT, GAUGE_Y)
            numbers = getattr(board, 'hpDecimal', None)
            if numbers is not None:
                numbers.SetPackedFontColor(Signed(HP_TEXT_INK))
            details = getattr(board, 'target_details_button', None)
            if details is not None and FORM_ART is not None and not arabic:
                # the R1 "?" (look L0 with a readable, centred glyph; hover / open states) in place of the icon
                click = getattr(board, '_TargetBoard__OnClickTargetDetailsButton', None)
                button = DetailsButton(board, click)
                if details.IsShow():
                    button.Show()
                details.Hide()
                self.legacyDetails = details
                board.target_details_button = button
            elif details is not None:
                self._LoadDetails(details, ART.ROOT + 'details_%s.png')
            buttons = {}
            for name, legacy in board.buttonDict.items():
                buttons[name] = TargetButton(board, self.kit, legacy.GetText(), KeyOf(name))
            showing = [buttons[self._NameOf(button)] for button in board.showingButtonList]
            self.legacyButtons = dict(board.buttonDict)
            board.showingButtonList = showing
            board.buttonDict = buttons
            self.finished = True
            for legacy in self.legacyButtons.values():
                legacy.Hide()
            self.Layout(board.GetWidth(), board.GetHeight())
            return self
        except Exception:
            uir1.TraceFailure('the target board')
            self.Revert()
            return None

    def _NameOf(self, button):
        for name, other in self.board.buttonDict.items():
            if other is button:
                return name
        raise KeyError('button not in the board')

    def _LoadDetails(self, details, pattern):
        board = self.board
        details.LoadImage(pattern % ('active' if self.detailsActive else 'inactive'))
        details.SetScale(board.TARGET_DETAILS_ICON_SCALE, board.TARGET_DETAILS_ICON_SCALE)

    def Revert(self):
        """The original look again: chrome, close button, name font, ampoule frame, HP numbers, details icon and the
        original buttons (with the events and the visibility the R1 buttons had). Used when building or a later
        layout fails."""
        self.failed = True
        board = self.board
        if self.info is not None:
            self.info.Hide()                    # the original row again (uitarget.__RefreshMonsterIndicators)
        try:
            if self.frame is not None:
                self.frame.Hide()
            if self.close is not None:
                self.close.Hide()
            board.chrome.Show()
            board.closeButton.Show()
            text = board.name.GetText()
            board.name.SetText('')
            board.name.SetDefaultFontName()
            board.name.SetText(text)
            board.name.SetPackedFontColor(Signed(0xFFFFFFFF))
            arabic = localeInfo.IsARABIC()
            gauge_shown = board.hpGauge.IsShow()
            if gauge_shown:
                board.name.SetPosition(board.GetWidth() - 23 if arabic else 23, board.TARGET_NAME_ROW_Y)
            else:
                board.name.SetPosition(0, board.TARGET_NAME_ROW_Y)
            board.hpGauge.background.LoadImage(board.hpGauge.HUD_FRAME)
            board.hpGauge.SetPosition(51 if arabic else 144, 17)
            numbers = getattr(board, 'hpDecimal', None)
            if numbers is not None:
                numbers.SetPackedFontColor(Signed(0xFFFFFFFF))
                value = numbers.GetText()
                if PERCENT_R1 in value:
                    numbers.SetText(value.replace(PERCENT_R1, PERCENT_ORIGINAL))
                    width = numbers.GetTextSize()[0]
                    numbers.SetPosition(GAUGE_W // 2 + width // 2 if arabic else GAUGE_W // 2 - width // 2, -15)
            if self.legacyDetails is not None:
                shown = board.target_details_button.IsShow()
                board.target_details_button.Hide()
                board.target_details_button = self.legacyDetails
                self.legacyDetails = None
                if shown:
                    board.target_details_button.Show()
            if self.chip is not None:
                self.chip.Hide()
            details = getattr(board, 'target_details_button', None)
            if details is not None:
                self._LoadDetails(details, DETAILS_ORIGINAL)
            if self.legacyButtons is not None and self.finished:
                names = dict((id(button), name) for name, button in board.buttonDict.items())
                for name, r1button in board.buttonDict.items():
                    legacy = self.legacyButtons[name]
                    legacy.eventFunc = r1button.eventFunc
                    legacy.eventArgs = r1button.eventArgs
                    legacy.Show() if r1button.IsShow() else legacy.Hide()
                    r1button.Hide()
                board.showingButtonList = [self.legacyButtons[names[id(button)]] for button in board.showingButtonList]
                board.buttonDict = dict(self.legacyButtons)
        except Exception:
            uir1.TraceFailure('the target board (restoring the original look)')
        form = getattr(board, 'form', None)
        if form is not None:
            board.form = None
            form.Destroy(restore=True)          # the three boxes of the original look again
        board.r1look = None

    # ------------------------------------------------------------------ hooks of uitarget
    def DetailsVisual(self, active, visual):
        """The details icon of a monster (uitarget __SetTargetDetailsButtonState): the R1 graphite one."""
        self.detailsActive = bool(active)
        if not self.finished or self.failed:
            return visual
        return ART.ROOT + 'details_%s.png' % ('active' if active else 'inactive')

    def PlaceHp(self):
        """After SetHP wrote the HP numbers: the percentage in the same ivory as the numbers, the numbers right
        aligned above the ampoule inside the frame; the board grows (never shrinks while the target stays) when they
        would reach the name."""
        if not self.finished or self.failed:
            return
        try:
            board = self.board
            numbers = board.hpDecimal
            value = numbers.GetText()
            if PERCENT_ORIGINAL in value:
                numbers.SetText(value.replace(PERCENT_ORIGINAL, PERCENT_R1))
            width = numbers.GetTextSize()[0]
            self._PlaceNumbers(numbers, width)
            if width > self.hpRoom:
                self.hpRoom = width
                # a monster's name may need a shorter "…" before its icons even when the capped width stays
                if self.FitWidth(board.GetWidth(), board.GetHeight()) != board.GetWidth() or self.infoState[1]:
                    board.UpdatePosition()
        except Exception:
            uir1.TraceFailure('the target board (HP numbers)')
            self.Revert()

    def _PlaceNumbers(self, numbers, width):
        """The HP numbers above the ampoule (``width`` = their text width): centred over it on the own character's
        board, else right aligned inside the frame."""
        arabic = localeInfo.IsARABIC()
        if self.Centred():
            numbers.SetPosition(GAUGE_W // 2 + width // 2 if arabic else (GAUGE_W - width) // 2, NUM_Y - GAUGE_Y)
        elif arabic:
            numbers.SetPosition(GAUGE_W - NUM_RIGHT + width, NUM_Y - GAUGE_Y)
        else:
            numbers.SetPosition(NUM_RIGHT - width, NUM_Y - GAUGE_Y)

    def Centred(self):
        """True on the own character's board with the ampoule (only Sesednout / Konec pozorování shown, not a
        monster): the ampoule, the HP numbers and the button row share the board's centre line."""
        board = self.board
        if board is None or self.infoState[1] or not board.hpGauge.IsShow():
            return False
        keys = [getattr(button, 'key', None) for button in board.showingButtonList if button.IsShow()]
        return bool(keys) and all(key in OWN_KEYS for key in keys)

    # ------------------------------------------------------------------ element and race (variant B)
    def ShowTargetInfo(self, vnum):
        """uitarget.__RefreshMonsterIndicators: the element and race icons of a monster (``vnum``) in the header,
        after the name, or nothing (0: a player, an NPC). True = shown here, the original floating row stays
        hidden; False = the R1 look is off or failed (the board keeps the original row). Cheap when nothing
        changed (uitargetinfo caches the VNUM): the board calls it on every UpdatePosition."""
        if not self.finished or self.failed or self.infoBroken or localeInfo.IsARABIC():
            return False
        board = self.board
        try:
            if self.info is None:
                import uitargetinfo           # the reusable icon row (also for the later unified target form)
                self.info = uitargetinfo.TargetInfoIcons(board)
            if vnum:
                width = self.info.SetMonster(vnum, liveElements=board.GetTargetElements())
            else:
                self.info.Clear()
                width = 0
            state = (width, bool(vnum))
            if state != self.infoState:
                self.infoState = state
                if not self.infoRefit:
                    self.infoRefit = True
                    try:
                        board.UpdatePosition()          # the width with (or without) the icons, centred again
                    finally:
                        self.infoRefit = False
            self._PlaceInfo(board.GetWidth())
            return True
        except Exception:
            uir1.TraceFailure('the target board (element and race)')
            if self.info is not None:
                self.info.Hide()
            self.info = None
            self.infoState = (0, False)
            self.infoBroken = True                     # traced once; the original row from now on
            return False

    # ------------------------------------------------------------------ the header pair ("?" + "DPS")
    def PairActive(self):
        board = self.board
        return self.legacyDetails is not None and board is not None and not self.failed

    def PairWidth(self):
        """Width of the pair: "?" (shown for a monster) and the "DPS" chip after it (when the form shows it)."""
        if not self.PairActive() or not self.board.target_details_button.IsShow():
            return 0
        width = Q_SIZE
        if self.chip is not None and self.chip.IsShow():
            width += PAIR_GAP + CHIP_W
        return width

    def PairRoom(self):
        width = self.PairWidth()
        return width + 2 * PAIR_PAD if width else 0

    def _Gaps(self):
        """(room before the ampoule, room before the HP numbers) after the name and its icons: the pair with its
        padding, at least the plain gaps; the original look keeps the details icon right after the name."""
        if self.PairActive():
            pair = self.PairRoom()
            return max(NAME_GAP, pair), max(NUM_GAP, pair)
        board = self.board
        icon = ICON_ROOM if getattr(board, 'target_details_button', None) is not None and \
            board.target_details_button.IsShow() else 0
        return icon + NAME_GAP, icon + NUM_GAP

    def PlacePair(self):
        """Centres "?" and the chip between the name (with its icons) and the HP block. False = not placed here
        (no ampoule yet, the original look): uitarget places the icon after the name as before."""
        board = self.board
        width = self.PairWidth()
        if not width or not board.hpGauge.IsShow():
            return False
        w = board.GetWidth()
        left = NAME_X + uir1.TextWidth(board.name) + (self.InfoRoom() if self.infoState[1] else 0)
        right = w - GAUGE_RIGHT
        numbers = getattr(board, 'hpDecimal', None)
        if numbers is not None and numbers.IsShow():
            right = min(right, w - GAUGE_RIGHT + NUM_RIGHT - uir1.TextWidth(numbers))
        x = (left + right - width) // 2
        y = (HEAD_H - Q_SIZE) // 2
        board.target_details_button.SetPosition(x, y)
        board.target_details_button.SetWindowHorizontalAlignLeft()
        if self.chip is not None and self.chip.IsShow():
            self.chip.SetPosition(x + Q_SIZE + PAIR_GAP, y)
        return True

    def InfoRoom(self):
        """The room the icons take after the name (with the gap before them), 0 without icons."""
        width = self.infoState[0]
        return width - 2 * self.info.PAD + INFO_GAP if width and self.info is not None else 0

    def _FullNameWidth(self):
        """Width of the whole name (uitarget.SetTargetName), measured once per name."""
        board = self.board
        full = getattr(board, 'nameString', None) or board.name.GetText()
        if full != self.nameFull:
            board.name.SetText(full)
            self.nameFull = full
            self.nameFullW = uir1.TextWidth(board.name)
            self.nameShown = None
        return self.nameFullW

    def _PlaceInfo(self, width):
        """A monster's name shortened with "…" to the room the cap leaves before the icons and the details icon,
        the icons right after the name. Nothing changes when the name and the room are the same as last time."""
        board = self.board
        info = self.info
        if not self.infoState[1] or not board.hpGauge.IsShow():
            if info is not None:
                info.Hide()
            return
        full = getattr(board, 'nameString', None) or board.name.GetText()
        self._FullNameWidth()
        room = self.InfoRoom()
        gap_g, gap_n = self._Gaps()
        budget = width - NAME_X - room - gap_g - GAUGE_RIGHT
        if self.hpRoom:
            budget = min(budget, width - NAME_X - room - gap_n - self.hpRoom - (GAUGE_RIGHT - NUM_RIGHT))
        key = (full, int(budget))
        if self.nameShown is None or self.nameShown[0] != key or board.name.GetText() != self.nameShown[1]:
            shown = uir1.Fit(board.name, full, max(1, budget), u'…') if self.nameFullW > budget else full
            if shown == full:
                board.name.SetText(full)
            self.nameShown = (key, shown)
        if info is None or not self.infoState[0]:
            if info is not None:
                info.Hide()
            return
        size = info.ICON + 2 * info.PAD
        info.SetPosition(NAME_X + uir1.TextWidth(board.name) + INFO_GAP - info.PAD, (HEAD_H - size) // 2)
        info.Show()

    # ------------------------------------------------------------------ layout
    def _Buttons(self):
        """The shown buttons in the order of the row: by group (stable, so the original order within a group)."""
        shown = [button for button in self.board.showingButtonList if button.IsShow()]
        return sorted(shown, key=lambda button: button.group)

    def RowWidth(self, buttons=None):
        buttons = self._Buttons() if buttons is None else buttons
        if not buttons:
            return 0
        return sum(button.Fit() for button in buttons) + BUTTON_GAP * (len(buttons) - 1)

    def NameRoom(self):
        """The width the board needs for the name (and the details icon) next to the ampoule and under / beside the
        HP numbers, or centred."""
        board = self.board
        name_w = self._FullNameWidth() if self.infoState[1] else uir1.TextWidth(board.name)
        icon = ICON_ROOM if getattr(board, 'target_details_button', None) is not None and \
            board.target_details_button.IsShow() else 0
        if self.Centred():
            # the name left (NAME_X) and the X right keep the same free room to the centred block on both sides
            side = max(NAME_X + name_w, CLOSE_RIGHT)
            return max(2 * (side + NAME_GAP) + GAUGE_W, 2 * (side + NUM_GAP) + self.hpRoom)
        if board.hpGauge.IsShow():
            room = self.InfoRoom()
            gap_g, gap_n = self._Gaps()
            need = NAME_X + name_w + room + gap_g + GAUGE_RIGHT
            if self.hpRoom:
                need = max(need, NAME_X + name_w + room + gap_n + self.hpRoom + GAUGE_RIGHT - NUM_RIGHT)
            if self.infoState[1]:
                # a monster: the name gets "…" past the cap (_PlaceInfo), but never shorter than NAME_MIN; the cap
                # grows by the room the centred pair takes beyond the original icon + gap (the name keeps its length)
                cap = INFO_CAP + max(0, gap_g - ICON_ROOM - NAME_GAP)
                floor = NAME_X + min(name_w, NAME_MIN) + room + max(
                    gap_g + GAUGE_RIGHT, gap_n + self.hpRoom + GAUGE_RIGHT - NUM_RIGHT)
                need = max(min(need, cap), floor)
            return need
        self.hpRoom = 0
        return name_w + 2 * (icon + NAME_GAP + CLOSE_RIGHT)

    def FitWidth(self, width, height):
        """The board's width: as wide as its content (the header, the button row, a stone's queue line)."""
        if not self.finished or self.failed:
            return width
        try:
            board = self.board
            need = self.NameRoom()
            row = self.RowWidth()
            if row:
                need = max(need, row + 2 * ROW_SIDE)
            queue = getattr(board, 'autoFarmText', None)
            if queue is not None and queue.IsShow():
                need = max(need, queue.GetTextSize()[0] + 2 * ROW_SIDE)
            return int(need)
        except Exception:
            uir1.TraceFailure('the target board (width)')
            self.Revert()
            return width

    def FitHeight(self, height):
        """The board's height: the 38 px header (40 originally), 64 px with the button row (65); others stay."""
        if not self.finished or self.failed:
            return height
        return HEIGHTS.get(int(height), int(height))

    def Refit(self):
        """Called by the board's UpdatePosition (after SetHP showed the ampoule and placed the name, which happens
        after its SetSize): fits the board to its content again and places the header."""
        board = self.board
        if not self.finished or self.failed or board is None:
            return
        width = self.FitWidth(board.GetWidth(), board.GetHeight())
        height = self.FitHeight(board.GetHeight())
        if self.failed:
            return
        if (width, height) != (board.GetWidth(), board.GetHeight()):
            board.SetSize(width, height)
        else:
            self.Layout(width, height)
        if self.infoState[1] and not self.failed:
            self._PlaceInfo(board.GetWidth())       # the name's "…" before uitarget places the details icon
        if not self.failed:
            self.PlacePair()

    def ArrangeButtons(self):
        """Called by the board's __ArrangeButtonPosition: True when the R1 row takes over the placing (the board's
        SetSize then lays it out at the final width)."""
        return self.finished and not self.failed

    def SetFormExtra(self, extra):
        """The unified target form (variant A): the frame runs on under the header over the open sections (the
        board clips it to the header, the form's body draws the rest), so header and sections are one frame."""
        extra = max(0, int(extra))
        if extra == self.formExtra or self.failed:
            self.formExtra = extra
            return
        self.formExtra = extra
        board = self.board
        if board is not None and self.frame is not None:
            self.frame.Resize(max(0, board.GetWidth() - 2 * FRAME_INSET), board.GetHeight() + extra)

    def Layout(self, width, height):
        if not self.finished or self.failed:
            if self.frame is not None and not self.failed:
                self.frame.Resize(max(0, width - 2 * FRAME_INSET), height)
            return
        try:
            board = self.board
            self.frame.Resize(max(0, width - 2 * FRAME_INSET), height + self.formExtra)
            arabic = localeInfo.IsARABIC()
            self.close.SetPosition(CLOSE_RIGHT - T.X_HIT if arabic else width - CLOSE_RIGHT, CLOSE_Y)
            name_y = uir1.CellTop(HEAD_H, self.kit.font(TEXT_FONT)) - 1
            if board.hpGauge.IsShow():
                board.name.SetPosition(width - NAME_X if arabic else NAME_X, name_y)
            else:
                board.name.SetPosition(0, name_y)
            # the ampoule: centred on the own character's board, else right aligned (its window aligns right, the
            # left one in Arabic); the numbers follow it
            left = (width - GAUGE_W) // 2 if self.Centred() else None
            if arabic:
                board.hpGauge.SetPosition(GAUGE_RIGHT - GAUGE_W if left is None else left, GAUGE_Y)
            else:
                board.hpGauge.SetPosition(GAUGE_RIGHT if left is None else width - left, GAUGE_Y)
            numbers = getattr(board, 'hpDecimal', None)
            if numbers is not None and numbers.IsShow():
                self._PlaceNumbers(numbers, numbers.GetTextSize()[0])
            buttons = self._Buttons()
            x = (width - self.RowWidth(buttons)) // 2
            for button in buttons:
                button.SetPosition(x, BUTTON_Y)
                x += button.w + BUTTON_GAP
        except Exception:
            uir1.TraceFailure('the target board (layout)')
            self.Revert()


def MakeForm(board):
    """The unified target form, variant A (uitargetform), for an R1 board; None when it cannot be built (traced):
    the drop panel and the DPS table then stay the separate boxes."""
    try:
        import uitargetform
        return uitargetform.Make(board)
    except Exception:
        uir1.TraceFailure('the target form')
        return None


class DropPanelLook(object):
    """R1 frame of the drop panel attached under the target board (same size) and the R1 item slot C as the base of
    its drop grid (the engine grid and the shown / hidden cells stay those of the panel)."""

    def __init__(self, panel):
        self.embedded = False
        self.frame = uir1.Frame(panel, 0, 0, max(0, panel.GetWidth()), max(0, panel.GetHeight()), 'window')
        panel.chrome.Hide()

    def Layout(self, width, height):
        if self.embedded:
            return                  # a section of the target form: the board's frame is the frame
        self.frame.Resize(width, height)

    def SetEmbedded(self, embedded):
        self.embedded = bool(embedded)
        if self.embedded:
            self.frame.Hide()
        else:
            self.frame.Show()

    @staticmethod
    def Slots(slot_window):
        """The drop grid's slot base: the R1 item slot C (set after the panel set its original base)."""
        slot_window.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)


def DressDropPanel(panel):
    """The R1 frame for the drop panel, or None (original look / failure: the original ThinBoard stays)."""
    if not uir1.UseR1():
        return None
    try:
        return DropPanelLook(panel)
    except Exception:
        uir1.TraceFailure('the target drop panel')
        try:
            panel.chrome.Show()
        except Exception:
            pass
        return None
