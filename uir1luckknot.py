# -*- coding: utf-8 -*-
"""Uzel štěstí - vylepšení (uiluckknot.UpgradeDialog, the guaranteed luck knot upgrade opened from the character
window) in the R1 look "Krvavá žíla", including the title bar, frame, material rows, yang cost, chance
and Vylepšit / Zrušit buttons.

The dialog keeps its size, its layout and its behaviour (the server quote, the live availability of the materials,
the yang and the level every 0.2 s, the item tooltips of the material icons, Vylepšit only while everything is there,
Zrušit / Esc / X through its cancel event). The R1 look is drawn into it:

* the frame, the header (title in Cinzel, the red vein, the plain X) and the background: the shared R1 frame
  (uir1frame.Dress with board=None: the dialog is a ui.BoardWithTitleBar built in code); the dark inner surface of
  the dialog is hidden, the R1 background shows through;
* the material icons on the R1 item slot C (uir1.SLOT_CELL instead of slot_base.sub);
* the texts in the R1 font (Noto Sans) and readable R1 colours: the ink, the muted stage line; the yang cost as the
  one R1 yang price of the client (root/uir1price.py: the coin, "5.000.000 Yang" in Tahoma 12, the R1 ink),
  a missing material / yang / level in the R1 red (no pale red), an available one in the original green;
* Vylepšit as the R1 primary button (left, confirm first) and Zrušit as the R1 secondary one (right), driving the
  dialog's own button events; Vylepšit is disabled exactly when the original one is (RefreshAvailability).

Settings -> "Starý vzhled" keeps the original dialog. A failure while dressing is traced (uir1.TraceFailure), the
original look comes back (uir1frame FrameSkin.Fail) and the class is not dressed again in this session.
"""
import localeInfo
import ui

import uir1
import uir1frame
import uir1price
import uir1skin
import uir1tokens as T

ORIGINAL_SLOT = 'd:/ymir work/ui/public/slot_base.sub'
ORIGINAL_FONT, ORIGINAL_VALUE_FONT = 'Tahoma:12', 'Tahoma:13b'
BUTTON_GAP = 8                                  # px between the two buttons and the dialog's centre (as before)
OPTS = dict(board=None)                         # the dialog is the board (ui.BoardWithTitleBar built in code)
COLORS = (('TEXT_COLOR', T.INK), ('STAGE_COLOR', T.INK_DIM), ('PRICE_COLOR', uir1price.COLOR),
          ('MISSING_COLOR', T.RED_HI),
          ('DISABLED_TEXT_COLOR', T.DISABLED))


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def Dress(window):
    """The R1 look on a built UpgradeDialog; returns the LuckSkin or None (Starý vzhled, a failure)."""
    frame = uir1frame.Dress(window, OPTS)
    if frame is None:
        return None
    try:
        return LuckSkin(window, frame)
    except Exception:
        frame.Fail()
        return None


class ButtonProxy(object):
    """The R1 button behind the dialog's acceptButton / cancelButton: Enable / Disable reach it, SetTextColor (the
    original label colour of a disabled button) is the R1 button's own disabled look."""

    def __init__(self, button):
        self.button = button

    def SetTextColor(self, color):
        pass

    def Enable(self):
        self.button.Enable()

    def Disable(self):
        self.button.Disable()

    def __getattr__(self, name):
        return getattr(self.button, name)


class LuckSkin(object):
    def __init__(self, window, frame):
        self.frame = frame
        self.window = frame.window                     # weak proxy (the window holds its frame)
        self.kit = kit = uir1.Kit()
        self.widgets = []
        frame.undo.append(self._Undo)                  # first in, last undone: after every change below
        surface = window.surface
        if surface is not None and surface.IsShow():
            surface.Hide()
            frame.undo.append(surface.Show)
        for slot, label, count in window.materialRows:
            frame.SetSlot(slot, ORIGINAL_SLOT)
        lines = [window.stageText, window.chanceText, window.minimumLevelText]
        for slot, label, count in window.materialRows:
            lines += [label, count]
        for line in lines:
            if line is not None:
                self._Font(line, kit.font('text_s'), ORIGINAL_FONT)
        self._Font(window.chanceValue, kit.font('text_sb'), ORIGINAL_VALUE_FONT)
        self._Price(window)
        # the dialog reads its colours from the instance: the R1 ones while the frame is drawn
        for name, color in COLORS:
            setattr(window, name, _Signed(color))
        frame.undo.append(self._OriginalColors)
        window.stageText.SetPackedFontColor(window.STAGE_COLOR)
        window.chanceText.SetPackedFontColor(window.TEXT_COLOR)
        self._Buttons(window)
        window.RefreshAvailability()

    def _Price(self, window):
        """The yang cost as the one R1 yang price of the client (root/uir1price.py):
        the dialog's own coin and line, the line 4 px right of the coin, "5.000.000 Yang" in Tahoma 12 with the
        outline (the dialog's own font), the R1 ink (red while the player has less: RefreshAvailability)."""
        line, icon = window.priceText, getattr(window, 'yangIcon', None)
        if line is None or icon is None:
            return
        x, y = line.GetLocalPosition()
        text = line.GetText()
        ix = icon.GetLocalPosition()[0]
        line.SetPosition(ix + uir1price.ICON_W + uir1price.ICON_GAP, y)
        line.SetText(uir1price.FormatYang(window.state['yang']))

        def back():
            line.SetPosition(x, y)
            line.SetText(text)
        self.frame.undo.append(back)

    def _Font(self, line, font, original):
        uir1.SetFont(line, font)

        def back(line=line, original=original):
            uir1.SetFont(line, original)
        self.frame.undo.append(back)

    def _Buttons(self, window):
        kit, frame = self.kit, self.frame
        accept, cancel = window.acceptButton, window.cancelButton
        ax, ay = accept.GetLocalPosition()
        centre = window.GetWidth() // 2
        y = ay - (T.BTN_H - accept.GetHeight()) // 2
        # the dialog's own handlers (what its buttons call), held weakly like every event of the client
        ok = uir1.Button(window, kit, 0, y, accept.GetWidth(), localeInfo.LUCK_KNOT_IMPROVE, primary=True,
                         event=ui.__mem_func__(getattr(window, '_UpgradeDialog__Accept')))
        no = uir1.Button(window, kit, 0, y, cancel.GetWidth(), localeInfo.UI_CANCEL,
                         event=ui.__mem_func__(getattr(window, '_UpgradeDialog__Cancel')))
        self.widgets += [ok, no]
        for button in (ok, no):
            button.FitWidth(accept.GetWidth())
        ok.SetPosition(centre - BUTTON_GAP - ok.GetWidth(), y)
        no.SetPosition(centre + BUTTON_GAP, y)
        self.accept, self.cancel = ok, no
        for original in (accept, cancel):
            if original.IsShow():
                original.Hide()
                frame.undo.append(original.Show)
        window.acceptButton, window.cancelButton = ButtonProxy(ok), ButtonProxy(no)

        def back():
            win = self.window
            win.acceptButton, win.cancelButton = accept, cancel
        frame.undo.append(back)

    def _OriginalColors(self):
        window = self.window
        for name, unused in COLORS:
            window.__dict__.pop(name, None)
        window.stageText.SetPackedFontColor(window.STAGE_COLOR)
        window.chanceText.SetPackedFontColor(window.TEXT_COLOR)

    def _Undo(self):
        widgets, self.widgets = self.widgets, []
        uir1skin.Destroy(reversed(widgets))
        try:
            self.window.RefreshAvailability()          # the original colours and the original accept state again
        except Exception:
            pass
