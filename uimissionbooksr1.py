# -*- coding: utf-8 -*-
"""Aktivní mise (uimissionbooks.MissionBookWindow, 302 x 344 / 390 / 566 x 344 with two or three objectives) in the
Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

The window keeps its sizes, its flags (float, movable), its state (the server-owned active mission, the objectives
with their rotating 3D previews, the progress counters, the reward, "Připnout malý přehled", "Zrušit misi" with its
question dialog) and every handler. This module only re-skins it:

* the board becomes the R1 background with the R1 frame and header (Cinzel title, vein, plain X), covering the whole
  window; the original title bar is hidden (the header grip drags the window);
* the texts in Spectral with the R1 ink, the two rules as R1 hairlines;
* the objectives keep their 3D previews in a quiet R1 panel frame instead of the mission frame art; their names and
  counters in Spectral;
* "Připnout malý přehled" as an R1 check box and "Zrušit misi" as an R1 button, both driven by the window through
  the same calls it makes on the originals (Show / Hide / SetChecked / IsChecked / SetEvent / SetPosition).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building undoes every
change, keeps the original look (traced to syserr) and the R1 look is not tried again in this session.
"""
import fontconfig
import ui

import uir1
import uir1skin
import uir1tokens as T
from missionbooklocale import Text
from uimissionbookwidgets import INK, DIM

FOOTER_PAD = 10                     # the button and the check box: 10 px above the bottom edge
TEXT_X = 18                         # the original left column (the rules, the reward label, the check box)

_failed = []


def UseR1():
    """The R1 look unless "Starý vzhled" is chosen or the R1 look of this window already failed in this session."""
    return not _failed and uir1.UseR1()


def Fail(what=u'Aktivní mise'):
    _failed.append(1)
    uir1.TraceFailure(what)


def _Packed(color):
    """(r, g, b) floats of uimissionbookwidgets -> 0xAARRGGBB."""
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in color]
    return 0xFF000000 | (r << 16) | (g << 8) | b


class CheckProxy(object):
    """The R1 check box behind the window's ``checkbox``: SetChecked / IsChecked / SetEvent / Show / Hide like
    ui.CheckBox_N; a click flips the tick and runs the window's event (ToggleTracking reads IsChecked)."""

    def __init__(self, box):
        self.box = box
        self.event = None
        box.SetEvent(self._Click)

    def _Click(self):
        self.box.SetOn(not self.box.IsOn())
        if self.event:
            self.event()

    def SetEvent(self, event, *args):
        self.event = (lambda: event(*args)) if event else None

    def SetChecked(self, on):
        self.box.SetOn(bool(on))

    def IsChecked(self):
        return self.box.IsOn()

    def Show(self):
        self.box.Show()

    def Hide(self):
        self.box.Hide()

    def IsShow(self):
        return self.box.IsShow()

    def SetPosition(self, x, y):
        pass                                        # placed by the skin

    def __getattr__(self, name):
        return getattr(self.box, name)


class ButtonProxy(object):
    """The R1 button behind the window's ``cancelButton`` (Show / Hide / SetEvent / SetPosition from the window)."""

    def __init__(self, button):
        self.button = button

    def SetEvent(self, event, *args):
        self.button.SetEvent((lambda: event(*args)) if event else None)

    def SetPosition(self, x, y):
        pass                                        # placed by the skin

    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

    def IsShow(self):
        return self.button.IsShow()

    def __getattr__(self, name):
        return getattr(self.button, name)


class MissionSkin(object):
    """R1 look of one MissionBookWindow. A build failure undoes every change and re-raises (Build traces it)."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.board = None
        self.styled = []
        try:
            self._Build()
            self.Sync()
        except Exception:
            self.Undo()
            raise

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    # ------------------------------------------------------------------ build
    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        W, H = w.GetWidth(), w.GetHeight()
        board = w.board
        rec.Position(board, 0, 0)
        rec.Size(board, W, H)
        rec.Hide(w.titleBar)                        # the header grip drags the window; the X is the R1 one
        self.board = uir1.BoardSkin(board, kit, title=w.title.GetText(), on_close=ui.__mem_func__(w.Close),
                                    w=W, h=H)
        body = fontconfig.FontForRole(fontconfig.ROLE_BODY)
        ink, dim = _Packed(INK), _Packed(DIM)
        for line, role, color, original in ((w.bookName, 'text_b', T.IVORY, ink),
                                            (w.rewardLabel, 'text_s', T.INK_DIM, dim),
                                            (w.rewardText, 'text_s', T.INK, ink),
                                            (w.empty, 'text_b', T.INK, ink),
                                            (w.emptyHint, 'text_r', T.INK_DIM, dim)):
            rec.Font(line, kit.font(role), color, body, original)
        for rule in (w.topRule, w.rewardRule):
            rec.Call(lambda rule=rule: rule.SetColor(T.LINE), lambda rule=rule: rule.SetColor(0xff522c2c))

        original_box = w.checkbox
        box = self._new(uir1.CheckBox(w, kit, TEXT_X, 0, Text('PIN_TRACKER'), on=original_box.IsChecked(),
                                      font=kit.font('text_s')))
        check = CheckProxy(box)
        check.SetEvent(ui.__mem_func__(w.ToggleTracking))
        original_button = w.cancelButton
        button = self._new(uir1.Button(w, kit, 0, 0, T.BTN_W, Text('CANCEL_MISSION'),
                                       event=ui.__mem_func__(w.CancelMission)))
        button.FitWidth(T.BTN_W)
        cancel = ButtonProxy(button)
        self.check, self.cancel = box, button
        for proxy, original, name in ((check, original_box, 'checkbox'), (cancel, original_button, 'cancelButton')):
            shown = original.IsShow()
            proxy.Show() if shown else proxy.Hide()
            rec.Hide(original)

            def attach(proxy=proxy, name=name):
                setattr(w, name, proxy)

            def detach(original=original, name=name):
                setattr(w, name, original)
            rec.Call(attach, detach)

    # ------------------------------------------------------------------ state
    def Sync(self):
        """After the window refreshed or resized: the frame size, the footer places, the new objectives."""
        w = self.window
        W, H = w.GetWidth(), w.GetHeight()
        board = w.board
        # ResizeForTargets lays the original board out again (4 px in, 8 px narrower, its own base tiling): the R1
        # board covers the whole window again and its base is tiled again.
        moved = board.GetLocalPosition() != (0, 0) or (board.GetWidth(), board.GetHeight()) != (W, H)
        if moved:
            board.SetPosition(0, 0)
            board.SetSize(W, H)
        if moved or (self.board.w, self.board.h) != (W, H):
            self.board.Resize(W, H)
        y = H - FOOTER_PAD - T.BTN_H
        self.cancel.SetPosition(W - FOOTER_PAD - self.cancel.GetWidth(), y)
        self.check.SetPosition(TEXT_X, y + (T.BTN_H - self.check.GetHeight()) // 2)
        for target in list(w.targets):
            if target not in self.styled:
                self._Target(target)
        self.styled = [target for target in self.styled if target in w.targets]

    def _Target(self, target):
        """An objective: the mission frame art hidden, an R1 panel outline around the 3D preview, the name and the
        counter in Spectral (made again with every new mission: the window re-creates its objectives)."""
        kit = self.kit
        frame = target.frame
        for widget in (getattr(frame, 'Corners', None) or []) + (getattr(frame, 'Lines', None) or []):
            widget.Hide()
        outline = uir1.Frame(target, 0, 0, frame.GetWidth(), frame.GetHeight(), 'panel', bg=None)
        target.r1Outline = outline
        uir1.SetFont(target.name, kit.font('text_s'))
        target.name.SetPackedFontColor(T.INK)
        uir1.SetFont(target.count, kit.font('text_sb'))
        target.count.SetPackedFontColor(T.IVORY)
        self.styled.append(target)

    def SyncSafe(self):
        """Sync() for the window's hooks: a failure is traced (syserr) and never breaks the window's own refresh."""
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure(u'Aktivní mise (stav)')

    # ------------------------------------------------------------------ teardown
    def Undo(self):
        if self.board is not None:
            try:
                self.board.Restore()
            except Exception:
                pass
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        if self.board is not None:
            try:
                self.board.Destroy()
            except Exception:
                pass
        self.widgets, self.board, self.styled = [], None, []

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        if self.board is not None:
            self.board.Destroy()
        self.widgets, self.board, self.styled = [], None, []
        self.rec.undo = []
        self.window = None


def Build(window):
    """The R1 skin of ``window`` or None (the original look: "Starý vzhled", or the build failed - traced)."""
    if not UseR1():
        return None
    try:
        return MissionSkin(window)
    except Exception:
        Fail()
        return None
