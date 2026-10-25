# -*- coding: utf-8 -*-
"""Unstuck (ESC -> "Odblokovat postavu"): a confirmation, the server's countdown with a cancel button and the
server's verdict, the way of the classic Escape option. The server owns every check (movement over 10 m, combat,
open windows, the cooldown) and the target (a free spot, else the village); this module only shows them.

Client -> server: "/unstuck" after the confirmation, "/unstuck_cancel" from the countdown window.
Server -> client (CHAT_TYPE_COMMAND, registered in game.py, variadic):

* UnstuckCountdown <seconds>  opens (or restarts) the countdown window "Budeš osvobozen za %d vteřin" + Zrušit;
* UnstuckCancel <reason>      closes it; the server's own localized INFO line already explains the reason
                              (with its numbers), so the client writes nothing to avoid a second line;
* UnstuckDone <mode>          closes it and lets go of the held movement keys, so a key held from before the move
                              does not walk the recreated character straight back into the obstacle.

An older server moves at once and sends none of them: the confirmation stays, no window opens.
The dialogs are the common uicommon dialogs (R1 look, "Starý vzhled", Enter / Esc of uiconfirm).
"""
import math

import app
import chat
import net
import player

import localeInfo
import uiScriptLocale
import uicommon

COMMAND_REQUEST = "/unstuck"
COMMAND_CANCEL = "/unstuck_cancel"

# the server's result modes (none of them changes what the client does)
MODES = ("ground", "lkg", "bfs", "recall", "village")

QUESTION = "UNSTUCK_QUESTION"
QUESTION_CONFIRM = "UNSTUCK_QUESTION_CONFIRM"
WAIT = "UNSTUCK_WAIT"
WAIT_FINISH = "UNSTUCK_WAIT_FINISH"
MOVE_WARNING = "UNSTUCK_MOVE_WARNING"
KEYS = (QUESTION, QUESTION_CONFIRM, WAIT, WAIT_FINISH, MOVE_WARNING)

MAX_SECONDS = 600           # a longer countdown from the server is shown as this
VERDICT_GRACE = 10.0        # s after the countdown without UnstuckDone / UnstuckCancel: the window closes quietly
WARN_DISTANCE = 500         # game units (5 m) from where the countdown began: one chat hint (the server cancels at 10 m)
MOVEMENT_KEYS = ("DIK_UP", "DIK_DOWN", "DIK_LEFT", "DIK_RIGHT")    # W / S / A / D are mapped onto these (game.py)


def _Trace(what):
    try:
        import dbg
        import traceback
        dbg.TraceError("unstuck %s: %s" % (what, traceback.format_exc()))
    except Exception:
        pass


def _Log(text):
    try:
        import dbg
        dbg.TraceError("unstuck: " + text)
    except Exception:
        pass


def Text(key):
    return getattr(localeInfo, key, key)


def WaitText(seconds):
    if seconds <= 0:
        return Text(WAIT_FINISH)
    text = Text(WAIT)
    try:
        return text % seconds
    except (TypeError, ValueError):
        return text


def ParseSeconds(args):
    """The seconds of "UnstuckCountdown <seconds>", 0 .. MAX_SECONDS; None for a missing or broken value."""
    if not args:
        return None
    try:
        seconds = int(args[0])
    except (TypeError, ValueError):
        return None
    return max(0, min(MAX_SECONDS, seconds))


def _Position():
    try:
        x, y = player.GetMainCharacterPosition()[:2]
        return float(x), float(y)
    except Exception:
        return None


def _Info(text):
    try:
        chat.AppendChat(chat.CHAT_TYPE_INFO, text)
    except Exception:
        _Trace("chat")


def ReleaseMovement():
    """Let go of the held direction keys (CPythonPlayer m_isUp / m_isDown / m_isLeft / m_isRight and m_isDirKey):
    the same call as the key up of W / A / S / D, which also stops the main actor. A key still held down stays
    released until it is pressed again (no repeat key-down). player.EndKeyWalkingImmediately would clear the
    directions but keep m_isDirKey, so the engine would stop the character every frame, also a click-to-move.
    A held mouse button (m_isSmtMov / m_isDirMov) has no Python release without a click action; see
    docs/invariants/unstuck-escape-flow.md."""
    released = 0
    for name in MOVEMENT_KEYS:
        key = getattr(app, name, None)
        if key is None:
            continue
        try:
            player.SetSingleDIKKeyState(key, False)
            released += 1
        except Exception:
            _Trace("release " + name)
    return released


def _Nothing(*args):
    pass


class WaitDialog(uicommon.PopupDialog):
    """uicommon.PopupDialog (one message line and one button) with an update tick: its button and Esc end in the
    accept event (PopupDialog.Close), which the controller sets to its cancel. Enter is taken without an action:
    the dialog has no confirmation, and an Enter meant for the chat must not cancel the unstuck."""

    def __init__(self, tick):
        uicommon.PopupDialog.__init__(self)
        self.tick = tick
        self.OnIMEReturn = _Consumed            # after uiconfirm.Bind of PopupDialog

    def OnUpdate(self):
        if self.tick:
            self.tick()


def _Consumed():
    return True

class Controller(object):
    def __init__(self):
        self.question = None
        self.wait = None
        self.waiting = False
        self.endTime = 0.0
        self.origin = None
        self.warned = False
        self.shownText = None

    # ------------------------------------------------------------------ ESC menu
    def Request(self):
        """ESC -> "Odblokovat postavu": the confirmation (the countdown window instead while one runs)."""
        if self.waiting and self.wait is not None:
            self.wait.SetTop()
            return
        dialog = self.question
        if dialog is None:
            dialog = uicommon.QuestionDialog2()
            dialog.SetAcceptEvent(self.__OnAccept)
            dialog.SetCancelEvent(self.__OnRefuse)
            self.question = dialog
        dialog.SetText1(Text(QUESTION))
        dialog.SetText2(Text(QUESTION_CONFIRM))
        dialog.Open()

    def __OnAccept(self):
        if self.question is None or not self.question.IsShow():
            return
        self.question.Close()
        net.SendChatPacket(COMMAND_REQUEST)

    def __OnRefuse(self):
        if self.question is not None:
            self.question.Close()

    # ------------------------------------------------------------------ server commands
    def OnCountdown(self, *args):
        seconds = ParseSeconds(args)
        if seconds is None:
            _Log("UnstuckCountdown without seconds: %r" % (args,))
            return
        self.__CloseQuestion()
        wait = self.wait
        if wait is None:
            wait = WaitDialog(self.__Tick)
            self.wait = wait
        wait.SetButtonName(getattr(uiScriptLocale, "CANCEL", "Cancel"))
        wait.SetAcceptEvent(self.__OnUserCancel)
        now = app.GetTime()
        self.waiting = True
        self.endTime = now + seconds
        self.origin = _Position()
        self.warned = False
        self.shownText = None
        self.__Refresh(now)
        wait.Open()

    def OnCancel(self, *args):
        # The reason (args[0]) is explained by the server's localized INFO line.
        self.__CloseQuestion()
        self.__CloseWait()

    def OnDone(self, *args):
        self.__CloseQuestion()
        self.__CloseWait()
        ReleaseMovement()

    # ------------------------------------------------------------------ countdown window
    def __OnUserCancel(self):
        """Zrušit or Esc in the countdown window (already hidden by PopupDialog.Close). The server answers
        with UnstuckCancel cancelled, whose line is written then."""
        if not self.waiting:
            return
        self.waiting = False
        net.SendChatPacket(COMMAND_CANCEL)

    def __Tick(self):
        if not self.waiting:
            return
        now = app.GetTime()
        if now > self.endTime + VERDICT_GRACE:
            self.__CloseWait()
            return
        self.__Refresh(now)
        self.__CheckDistance()

    def __Refresh(self, now):
        remaining = self.endTime - now
        text = WaitText(int(math.ceil(remaining)) if remaining > 0 else 0)
        if text != self.shownText and self.wait is not None:
            self.wait.SetText(text)
            self.shownText = text

    def __CheckDistance(self):
        if self.warned or self.origin is None:
            return
        position = _Position()
        if position is None:
            return
        if math.hypot(position[0] - self.origin[0], position[1] - self.origin[1]) > WARN_DISTANCE:
            self.warned = True
            _Info(Text(MOVE_WARNING))

    def __CloseWait(self):
        self.waiting = False
        wait = self.wait
        if wait is not None:
            wait.SetAcceptEvent(_Nothing)         # PopupDialog.Close runs the accept event: never a cancel packet
            wait.Close()

    def __CloseQuestion(self):
        if self.question is not None:
            self.question.Close()

    def IsWaiting(self):
        return self.waiting

    def Reset(self):
        """The game phase ends or a warp leaves the map: close both windows without a packet and build them again
        in the next phase."""
        try:
            self.__CloseQuestion()
            self.__CloseWait()
        except Exception:
            _Trace("reset")
        self.question = None
        self.wait = None
        self.waiting = False
        self.origin = None


controller = Controller()
