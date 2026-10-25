# -*- coding: utf-8 -*-
"""Okno vylepšení dovedností (uiskillupgrade.SkillUpgradeWindow) and Vylepšování buffy (uibuffupgrade.SupportUpgrade,
the same window for the Buffi skills): its CONTROLS in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md). The shared
R1 frame (root/uir1frame.py) already draws the header and the item slot C; the two buttons and the count slider were
still the original art (the bronze-brown 100 x 21 plates, the old bar with the orange knob).

* Potvrdit is the primary R1 button (the red vein along its bottom edge), Zrušit the secondary one; both 26 px high,
  slightly rounded, the label in Cinzel like every R1 button (uir1dialog.DialogButton: the R1 button with the ui.Button
  calls the window uses). The main action stands on the left, as in every dialog of the client (confirm left, cancel
  right);
* the count slider ("1x" ... "100x", at the end "Do G" for the books) is uir1.Slider (the red vein with the small
  round dark knob) with the calls of the native ui.SliderBar (SetSliderPos / GetSliderPos / SetEvent); the count text
  stands right of it.

Nothing of the window's logic moves: the window keeps its attributes (confirmBtn, cancelBtn, countControl, countText)
and its handlers (Confirm, Hide, OnChangeCount), only the objects behind the first three are the R1 ones. A caller that
sets the event of a button or of the slider reaches the R1 control.

"Starý vzhled" (settingslook 'legacy') and a window the shared R1 frame did not dress keep the original controls. A
failure while building, or the shared frame falling back to the original look later, brings every original control
back (traced, uir1.TraceFailure), and this look is not tried again in the session; the window keeps working.
"""
import weakref

import uir1
import uir1dialog
import uir1tokens as T

SLIDER_TRACK = 140       # px of the slider track (the slider is the track plus one knob wide)
LABEL_GAP = 10           # px between the slider and the count text
LABEL_ROOM = 36          # px the count text may take ("100x", "Do G")
BUTTON_W = 108           # px of Zrušit and Potvrdit
BUTTON_GAP = 10          # px between them
ROW_BOTTOM = 62          # px from the bottom of the board to the centre of the count row
TEXT_BOTTOM = 68         # px from the bottom of the board to the top of the count text (the window's own place)
_failed = [False]


def Dress(window):
    """The R1 controls on a freshly loaded skill upgrade window (its buttons and the slider already bound): the skin,
    or None ("Starý vzhled", no R1 frame on the window, a failure)."""
    if _failed[0] or not uir1.UseR1():
        return None
    if window.__dict__.get('r1frame') is None:        # no R1 frame (Starý vzhled, a frame failure): the original window
        return None
    try:
        return ControlsSkin(window)
    except Exception:
        Fail(window)
        return None


def Fail(window):
    _failed[0] = True
    uir1.TraceFailure('the controls of the skill upgrade window')
    skin = window.__dict__.get('r1controls')
    if skin is not None:
        skin.Undo()
    try:
        window.r1controls = None
    except Exception:
        pass


class CountSlider(uir1.Slider):
    """uir1.Slider that also takes the calls of the window that only fit the art of the native ui.SliderBar."""

    def _ignore(self, *args, **kwargs):
        """The art of the native slider (SetButtonVisual / SetBackgroundVisual): R1 draws the slider itself."""

    SetButtonVisual = SetBackgroundVisual = _ignore


class ControlsSkin(object):
    """The R1 buttons and the slider of one window. Layout() puts them in place, Undo() brings the originals back."""

    # window attribute, uiscript child, the red-vein plate - from left to right (the main action left)
    BUTTONS = (('confirmBtn', 'confirm', True), ('cancelBtn', 'cancel', False))

    def __init__(self, window):
        self.window = weakref.proxy(window)
        self.kit = uir1.Kit()
        self.undo = []
        self.buttons = {}       # window attribute -> the R1 button
        self.natives = {}       # window attribute -> the hidden original control
        self.slider = None
        self.done = False
        window.r1controls = self
        try:
            self._Build(window)
            window.r1frame.undo.append(self.Undo)     # the shared frame going back to the original look takes this along
            self.Layout()
        except Exception:
            self.Undo()
            window.r1controls = None
            raise

    # build -----------------------------------------------------------------------------------------------------
    def _Build(self, window):
        board, kit = window.board, self.kit
        elements = getattr(window, 'ElementDictionary', None)
        for attr, name, primary in self.BUTTONS:
            native = getattr(window, attr)
            button = uir1dialog.DialogButton(board, kit, native, primary, False)
            button.SetWidth(BUTTON_W)
            self.undo.append(lambda attr=attr, name=name, native=native, button=button, shown=native.IsShow():
                             self._RestoreButton(attr, name, native, button, shown))
            native.Hide()
            self.buttons[attr] = button
            self.natives[attr] = native
            setattr(window, attr, button)
            if elements is not None:
                elements[name] = button
        native = window.countControl
        slider = CountSlider(board, kit, 0, 0, SLIDER_TRACK)
        slider.SetSliderPos(native.GetSliderPos())
        self.undo.append(lambda native=native, slider=slider, shown=native.IsShow():
                         self._RestoreSlider(native, slider, shown))
        native.Hide()
        self.slider = slider
        self.natives['countControl'] = native
        window.countControl = slider
        if elements is not None:
            elements['CountController'] = slider

    # the way back ----------------------------------------------------------------------------------------------
    def _RestoreButton(self, attr, name, native, button, shown):
        window = self.window
        button.Hide()
        setattr(window, attr, native)
        elements = getattr(window, 'ElementDictionary', None)
        if elements is not None:
            elements[name] = native
        if button.eventFunc:                             # what the window wired meanwhile goes to the native button
            native.SetEvent(button.eventFunc, *button.eventArgs)
        native.SetText(button.GetText())
        if shown:
            native.Show()

    def _RestoreSlider(self, native, slider, shown):
        window = self.window
        slider.Hide()
        window.countControl = native
        elements = getattr(window, 'ElementDictionary', None)
        if elements is not None:
            elements['CountController'] = native
        if slider.callback:
            native.SetEvent(slider.callback)
        native.SetSliderPos(slider.GetSliderPos())
        if shown:
            native.Show()

    def Undo(self):
        """The original buttons and slider again, at the places the window gives them."""
        if self.done:
            return
        self.done = True
        undo, self.undo = self.undo, []
        for step in reversed(undo):
            try:
                step()
            except Exception:
                pass
        try:
            window = self.window
            window.r1controls = None
            window.PlaceControls(window.GetHeight())
        except Exception:
            pass

    # layout ----------------------------------------------------------------------------------------------------
    def Layout(self, height=None):
        """The count row and the button row of a board ``height`` px high (the window's own SetPosition calls run
        before, ConfigureReadingControls)."""
        window = self.window
        width = window.GetWidth()
        height = height if height else window.GetHeight()
        slider = self.slider
        block = slider.Width() + LABEL_GAP + LABEL_ROOM
        x = (width - block) // 2
        slider.SetPosition(x, height - ROW_BOTTOM - slider.GetHeight() // 2)
        window.countText.SetPosition(x + slider.Width() + LABEL_GAP, height - TEXT_BOTTOM)
        row = 2 * BUTTON_W + BUTTON_GAP
        x = (width - row) // 2
        y = height - T.PAD - T.BTN_H
        for attr, name, primary in self.BUTTONS:
            self.buttons[attr].SetPosition(x, y)
            x += BUTTON_W + BUTTON_GAP
