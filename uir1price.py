# -*- coding: utf-8 -*-
"""The one R1 yang price of the client ("Krvavá žíla") and the R1 OK / Zrušit row of the R1 dialogs that
show a price.

Every R1 window that shows a yang price uses Price (or PriceField): the yang coin, the amount with the thousand
separators of the game's money format (localeInfo.NumberToMoneyString of the European locales: dots, "31.250.000")
and the unit ("Yang", localeInfo.MONETARY_UNIT0), in Tahoma 12 with the outline. The colour is the R1 ink, the red of "not enough" (SHORT, the crafting window's red) when the window
knows the player cannot pay it.

    price = uir1price.Price(parent, x, y, align='right')     # x is the right edge (align 'left': the left edge)
    price.SetPrice(31250000, uir1price.CanAfford(31250000))   # "31.250.000 Yang", red when the player has less
    price.Clear()                                             # nothing shown (no preview yet)
    field = uir1price.PriceField(parent, x, y, w)             # the same price right-aligned in an R1 well

ConfirmButtons draws the confirm / cancel pair of a dialog that keeps its native buttons (their events, Enable /
Disable, positions in the window code) as R1 buttons of the R1 dialogs (uir1dialog.DialogButton, 96 x 26): the
confirm on the LEFT with the vein, P['gap'] px between them, the row BUTTON_BOTTOM (P['pad'], 12) px above the bottom
edge. A click
runs the native button's event as the window wired it at click time; a Disable of the native button disables its R1
twin (uir1.TrackEnabled). Restore() gives the native buttons back.

Engine rules kept: a text line gets its font while it is empty (uir1.SetFont); Hide / Show / SetPrice are safe
before __init__ finished (class-level defaults); nothing is created per frame (SetPrice only sets the text).
"""
import ui

import uir1
import uir1layout as L
import uir1tokens as T

FONT = 'Tahoma:12'          # the classic Metin font for every text and number
ICON = 'd:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png'    # 16 x 16, the coin of the R1 inventory
ICON_W = ICON_H = 16
ICON_GAP = 4                # px between the coin and the amount
SEPARATOR = '.'             # the thousand separator of the game's money format (localeInfo.NumberToMoneyString)
UNIT = 'Yang'               # localeInfo.MONETARY_UNIT0 when the locale has one
COLOR = T.INK
SHORT = 0xFFDC443C          # not enough Yang (the red of the R1 crafting window)
FIELD_PAD = 8               # px between the amount and the right end of the R1 well
P = T.PROFILE_DIALOG        # the layout profile of these dialogs (docs/ALTHEA_R1_KIT.md chap. 0)
BUTTON_GAP = P['gap']       # px between the confirm and the cancel button
BUTTON_BOTTOM = P['pad']    # px between the button row and the bottom edge of the dialog (= the gap above the row)


TraceFailure = uir1.TraceFailure      # for the windows that use the price without importing the kit themselves


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def FormatAmount(amount):
    """The amount with the thousand separators of the game's money format: 0, 999, 1.000, 6.800.000, 31.250.000."""
    try:
        number = int(amount)
    except Exception:
        number = 0
    digits = str(max(0, number))
    head = len(digits) % 3 or 3
    return SEPARATOR.join([digits[:head]] + [digits[i:i + 3] for i in range(head, len(digits), 3)])


def Unit():
    """The money unit of the locale ("Yang")."""
    try:
        import localeInfo
        unit = getattr(localeInfo, 'MONETARY_UNIT0', None)
        if unit and isinstance(unit, (type(''), type(u''))):
            return unit
    except Exception:
        pass
    return UNIT


def FormatYang(amount):
    """The text of a yang price: "31.250.000 Yang"."""
    return '%s %s' % (FormatAmount(amount), Unit())


def Text(amount, legacy=None):
    """The yang amount as a text line of a window shows it (a tooltip line, a sentence, a label without room for the
    coin): "31.250.000 Yang" in the R1 look; ``legacy`` (the window's own text, or a callable that makes it) for
    "Starý vzhled", which keeps the original texts ()."""
    if uir1.UseR1() or legacy is None:
        return FormatYang(amount)
    return legacy() if callable(legacy) else legacy


def StyleLine(line, color=None):
    """An existing text line of a window that keeps its own coin (the inventory money bar, a dialog's cost line) in
    the style of the R1 price: Tahoma 12 with the outline, the R1 ink (``color`` packed, e.g. SHORT). The window
    restores its own font on its undo (UnstyleLine)."""
    uir1.SetFont(line, FONT, line.GetText())
    line.SetOutline()
    line.SetPackedFontColor(_Signed(COLOR if color is None else color))


def UnstyleLine(line, font=None, color=-1):
    """StyleLine undone: ``font`` (None: the client's default font), no outline, ``color`` (-1: white)."""
    text = line.GetText()
    line.SetText('')
    if font is None:
        line.SetDefaultFontName()
    else:
        line.SetFontName(font)
    line.SetText(text)
    line.SetOutline(False)
    line.SetPackedFontColor(_Signed(color))


def ParseAmount(text):
    """The amount of a typed / shown yang text: the digits only ("1.000.000 Yang", "1 000 000", "1,000" -> 1000000,
    1000000, 1000); 0 when there are none. The input fields that show their value with the dots use it to read it."""
    digits = ''.join(ch for ch in '%s' % (text or '') if '0' <= ch <= '9')
    try:
        return int(digits) if digits else 0
    except Exception:
        return 0


def CanAfford(amount):
    """True / False when the player's yang is known (player.GetElk), None when it is not (the price keeps its ink)."""
    try:
        import player
        return int(player.GetElk()) >= int(amount)
    except Exception:
        return None


class Price(ui.Window):
    """The R1 yang price: the coin and "31.250.000 Yang" in Tahoma 12. ``align`` says which edge (x, y) is: 'left',
    'right' or 'center' (the price grows away from it as the amount changes). ``height``: the row the coin and the
    text are centred in (the window is that tall)."""

    amount = None               # class-level defaults: the engine may call Hide / Show before __init__ ends
    affordable = None
    align = 'left'
    anchor = (0, 0)
    height = ICON_H
    icon = None
    line = None

    def __init__(self, parent, x=0, y=0, align='left', height=ICON_H):
        ui.Window.__init__(self)
        self.align = align if align in ('left', 'right', 'center') else 'left'
        self.anchor = (int(x), int(y))
        self.height = max(ICON_H, int(height))
        self.SetParent(parent)
        self.AddFlag('not_pick')
        icon = ui.ImageBox()
        icon.SetParent(self)
        icon.AddFlag('not_pick')
        icon.LoadImage(ICON)
        icon.SetPosition(0, (self.height - ICON_H) // 2)
        icon.Show()
        self.icon = icon
        line = ui.TextLine()
        line.SetParent(self)
        line.AddFlag('not_pick')
        uir1.SetFont(line, FONT, '')            # set while the line is empty: no garbled glyphs
        line.SetOutline()
        line.SetPackedFontColor(_Signed(COLOR))
        line.SetPosition(ICON_W + ICON_GAP, uir1.CellTop(self.height, FONT))
        line.Show()
        self.line = line
        self.Clear()

    def SetAnchor(self, x, y, align=None):
        """Moves the price: (x, y) is its ``align`` edge (as in __init__)."""
        if align in ('left', 'right', 'center'):
            self.align = align
        self.anchor = (int(x), int(y))
        self._Place()

    def SetPrice(self, amount, affordable=None):
        """Shows ``amount`` Yang; ``affordable`` False paints it red (None / True: the R1 ink)."""
        if self.line is None:
            return
        self.amount = max(0, int(amount or 0))
        self.affordable = affordable
        self.line.SetText(FormatYang(self.amount))
        self.line.SetPackedFontColor(_Signed(SHORT if affordable is False else COLOR))
        self._Place()
        self.Show()

    def Clear(self):
        """No price (a dialog waiting for its preview): nothing is shown."""
        self.amount = None
        self.affordable = None
        if self.line is not None:
            self.line.SetText('')
        self.Hide()

    def GetText(self):
        return self.line.GetText() if self.line is not None else ''

    def GetColor(self):
        """The packed colour the amount has now (tests, diagnostics)."""
        return SHORT if self.affordable is False else COLOR

    def TextWidth(self):
        return uir1.TextWidth(self.line) if self.line is not None else 0

    def _Place(self):
        w = ICON_W + ICON_GAP + self.TextWidth()
        self.SetSize(w, self.height)
        x, y = self.anchor
        if self.align == 'right':
            x -= w
        elif self.align == 'center':
            x -= w // 2
        self.SetPosition(x, y)

    def Destroy(self):
        self.Hide()
        self.icon = None
        self.line = None


class PriceField(ui.Window):
    """The R1 price right-aligned in an R1 well (uir1layout.field, 24 px): the yang row of a dialog (Zlepšení,
    Rarita, Okno zušlechťování). The well is never an input: not pickable."""

    price = None
    well = None

    def __init__(self, parent, x, y, w):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), T.FIELD_H)
        self.well = uir1.Layer(self, 0, 0, int(w), T.FIELD_H, L.field('normal', int(w)))
        self.price = Price(self, int(w) - FIELD_PAD, 0, 'right', T.FIELD_H)
        self.Show()

    def SetPrice(self, amount, affordable=None):
        if self.price is not None:
            self.price.SetPrice(amount, affordable)

    def Clear(self):
        if self.price is not None:
            self.price.Clear()

    def GetText(self):
        return self.price.GetText() if self.price is not None else ''

    def Destroy(self):
        self.Hide()
        if self.well is not None:
            self.well.Destroy()
        if self.price is not None:
            self.price.Destroy()
        self.well = None
        self.price = None


# --------------------------------------------------------------------------- confirm / cancel
def _Forward(native):
    """Runs the native button's event as the window wired it (read at click time: windows wire their buttons after
    loading the uiscript and some re-wire them later). Weak: the R1 twin never keeps the native button alive."""
    import weakref
    ref = weakref.ref(native)

    def call():
        button = ref()
        if button is None:
            return
        if 'eventFunc' in getattr(button, '__dict__', {}) or hasattr(type(button), 'eventFunc'):
            func = getattr(button, 'eventFunc', None)          # ui.Button: its event without a second click sound
            if func:
                func(*tuple(getattr(button, 'eventArgs', None) or ()))
        else:
            button.CallEvent()
    return call


class ConfirmButtons(object):
    """The R1 OK / Zrušit pair standing in for a dialog's native confirm and cancel buttons (see the module doc).
    Place(width, bottom) lays the row out centred in a dialog of ``width`` with its bottom edge at ``bottom``."""

    def __init__(self, parent, accept, cancel, kit=None):
        import uir1dialog
        self.kit = kit or uir1.Kit()
        self.pairs = []
        try:
            for native, primary in ((accept, True), (cancel, False)):
                button = uir1dialog.DialogButton(parent, self.kit, native, primary, False)
                button.SetEvent(_Forward(native))
                uir1.TrackEnabled(native, uir1.IsEnabled(native), self._Follower(button))
                if not uir1.IsEnabled(native):
                    button.Disable()
                self.pairs.append((native, button))
                import weakref
                native._confirm_visual = weakref.ref(button)
                native.Hide()
        except Exception:
            self.Restore()
            raise

    @staticmethod
    def _Follower(button):
        import weakref
        ref = weakref.ref(button)

        def changed(enabled):
            twin = ref()
            if twin is not None:
                twin.Enable() if enabled else twin.Disable()
        return changed

    def Buttons(self):
        return [button for unused, button in self.pairs]

    def RowWidth(self):
        buttons = self.Buttons()
        return sum(button.GetWidth() for button in buttons) + BUTTON_GAP * max(0, len(buttons) - 1)

    def Height(self):
        return max([button.GetHeight() for button in self.Buttons()] or [T.BTN_H])

    def Place(self, width, bottom, offset=0):
        """The row centred in ``width`` (+ ``offset``), its bottom edge at ``bottom``; returns the row's top."""
        top = int(bottom) - self.Height()
        x = int(offset) + (int(width) - self.RowWidth()) // 2
        for button in self.Buttons():
            button.SetPosition(x, top)
            x += button.GetWidth() + BUTTON_GAP
        return top

    def Restore(self):
        """The native buttons again (the original look after a failure)."""
        pairs, self.pairs = self.pairs, []
        for native, button in pairs:
            try:
                button.Hide()
                native._confirm_visual = None
                uir1.UntrackEnabled(native)
                native.Show()
            except Exception:
                pass


# --------------------------------------------------------------------------- check boxes of the price dialogs
CHECK_FONT = FONT           # Tahoma 12 like the price and every R1 text (PRAVIDLA-UI 9. 10.)
MIRRORED = ('Down', 'SetUp', 'Show', 'Hide', 'Enable', 'Disable', 'SetPosition')



class ProgressBar(object):
    """The R1 progress bar of the Biolog (uir1layout slider track and vein fill) for a window dressed by uir1frame,
    e.g. the practice bar of the tool mode of the refine window (owner 13. 10., NASTROJ-OKNO = A)."""

    def __init__(self, parent, x, y, width):
        import uir1
        import uir1layout as L
        import uir1tokens as T
        self.width = int(width)
        self.track = uir1.Layer(parent, x, y, self.width, T.SLIDER_H, L.slider_track(0, 0, self.width))
        self.fill = uir1.Layer(parent, x, y, self.width, T.SLIDER_H, [])

    def SetRatio(self, ratio):
        import uir1layout as L
        filled = int(round(max(0.0, min(1.0, float(ratio))) * self.width))
        self.fill.Apply(L.slider_fill(0, 0, filled) if filled > 0 else [])

    def Show(self):
        self.track.Show()
        self.fill.Show()

    def Hide(self):
        self.track.Hide()
        self.fill.Hide()

    def __iter__(self):
        return iter((self.track, self.fill))

class CheckBoxTwin(object):
    """The R1 check box (uir1.CheckBox: the box, the kit's gap, the label) standing in for a native toggle_button check
    box of a dialog ("Zrychlit vylepšování", "Použít posilovač"). On the R1 frame the native one drew its box over
    the start of its own label and the label began at the window's left edge ( owner 10. 10.).

    The window keeps driving the NATIVE toggle: its Down / SetUp / Show / Hide / Enable / Disable / SetPosition calls
    reach the twin (instance wrappers, weak both ways); the native one stays hidden. A click on the twin sets the
    native state and runs the native toggle event as the window wired it (ui.ToggleButton eventDown / eventUp with
    their arguments). ``dx`` moves the twin from the native x (the window's left margin of its rows). Restore()
    removes the wrappers and shows the native check box where the twin was shown."""

    def __init__(self, parent, native, dx=0, kit=None):
        import weakref
        self.kit = kit or uir1.Kit()
        self.native = weakref.ref(native)
        self.dx = int(dx)
        self.wrapped = []
        try:
            text = native.GetText()
        except Exception:
            text = ''
        self.box = uir1.CheckBox(parent, self.kit, 0, 0, (text or '').strip(), on=self._NativeDown(native),
                                 event=self._Clicked(), font=CHECK_FONT)
        x, y = native.GetLocalPosition()
        self.box.SetPosition(x + self.dx, y)
        shown = native.IsShow()
        if not uir1.IsEnabled(native):
            self.box.Disable()
        native.Hide()
        if not shown:
            self.box.Hide()
        for name in MIRRORED:
            self._Wrap(native, name)

    @staticmethod
    def _NativeDown(native):
        try:
            return bool(native.IsDown())
        except Exception:
            return False

    def _Clicked(self):
        import weakref
        me = weakref.ref(self)

        def clicked():
            twin = me()
            if twin is not None:
                twin.Toggle()
        return clicked

    def Toggle(self):
        native = self.native()
        if native is None or not self.box.IsEnabled():
            return
        on = not self.box.IsOn()
        (native.Down if on else native.SetUp)()            # mirrored back into the twin
        func = getattr(native, 'eventDown' if on else 'eventUp', None)
        args = getattr(native, 'eventDownArgs' if on else 'eventUpArgs', None) or ()
        if func:
            func(*tuple(args))

    def _Wrap(self, native, name):
        import weakref
        target, me = weakref.ref(native), weakref.ref(self)
        own = native.__dict__.get(name)
        method = getattr(native.__class__, name)

        def wrapper(*args):
            obj = target()
            if obj is None:
                return None
            twin = me()
            if name in ('Show', 'Hide') and twin is not None:
                return twin.Mirror(name, *args)                # the native one stays hidden
            result = own(*args) if own is not None else method(obj, *args)
            if twin is not None:
                twin.Mirror(name, *args)
            return result
        setattr(native, name, wrapper)
        self.wrapped.append((name, own))

    def Mirror(self, name, *args):
        box = self.box
        if name == 'Down':
            box.SetOn(True)
        elif name == 'SetUp':
            box.SetOn(False)
        elif name == 'Show':
            box.Show()
        elif name == 'Hide':
            box.Hide()
        elif name == 'Enable':
            box.Enable()
        elif name == 'Disable':
            box.Disable()
        elif name == 'SetPosition' and len(args) >= 2:
            box.SetPosition(int(args[0]) + self.dx, int(args[1]))

    def Restore(self):
        native = self.native()
        wrapped, self.wrapped = self.wrapped, []
        shown = self.box.IsShow()
        self.box.Hide()
        if native is None:
            return
        for name, own in wrapped:
            if own is not None:
                setattr(native, name, own)
            elif name in native.__dict__:
                delattr(native, name)
        if shown:
            native.Show()
