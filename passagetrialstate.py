# -*- coding: utf-8 -*-
"""Whether the level104 passage trial runs, for a warning before a player teleport.

Any warp fails a running trial on the server (12h cooldown); a refused warp
does not. The HUD reports the server's phase here. The server still decides.
"""
# The server's last HUD phase: 0 none, 1 waiting for the first hit, 2 running.
_phase = [0]
_question = [None]


def _Text(key):
    import localeInfo  # imported on use: atlas harnesses load this module without locale data
    return getattr(localeInfo, key, key)


def SetPhase(phase):
    _phase[0] = int(phase)
    if not _phase[0]:
        _CloseQuestion()


def IsTrialRunning():
    return _phase[0] != 0


def _CloseQuestion():
    if _question[0] is not None:
        _question[0].Close()
        _question[0] = None


def ConfirmTeleport(proceed):
    """Run proceed() at once without a trial, otherwise only after the player confirms."""
    if not IsTrialRunning():
        proceed()
        return
    import uiCommon
    _CloseQuestion()
    dialog = uiCommon.QuestionDialog2()

    def accept():
        if _question[0] is not dialog:
            return
        _CloseQuestion()
        proceed()

    dialog.SetText1(_Text("LEVEL104_PASSAGE_TELEPORT_WARNING"))
    dialog.SetText2(_Text("LEVEL104_PASSAGE_TELEPORT_CONFIRM"))
    dialog.SetAcceptEvent(accept)
    dialog.SetCancelEvent(_CloseQuestion)
    _question[0] = dialog
    dialog.Open()
