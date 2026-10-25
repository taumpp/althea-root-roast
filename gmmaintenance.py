# -*- coding: utf-8 -*-
"""The "Údržba" section of the R1 GM panel: what it types and what it shows, without any client import
(the module also runs on Python 2).

The section sends the chat command the server already has, not a panel request:

    /maintenance <za> <délka> [důvod]      minutes: "15 30 update" = in 15 min, for 30 min, reason "update"
    /maintenance stop                      cancels (also after the start: reopens the login)

Authority stays with the server: the command is limited to an Implementor there (game/src/cmd.cpp), the panel only
offers the section to that level and checks the same limits so a mistake is shown before it is sent. The limits are
those of the server (game/src/maintenance_schedule.h): the start within a day, the duration up to twelve hours, the
reason at most 40 printable ASCII characters without '|'. "update", "fix" and "restart" are presets the server
translates for every player; any other text is shown to the players as written.
"""

COMMAND = u'/maintenance'
STOP = u'/maintenance stop'

# The GM level (GM_IMPLEMENTOR) the server needs for the command.
LEVEL = 5

START_MAX = 24 * 60            # minutes
DURATION_MAX = 12 * 60         # minutes
REASON_MAX = 40
FIELD_DIGITS = 4

# (the word the server translates, the Czech name on the button and in the preview)
PRESETS = (
    (u'update', u'Aktualizace hry'),
    (u'fix', u'Oprava chyb'),
    (u'restart', u'Restart serveru'),
)


def Minutes(text, maximum):
    """A plain whole number of minutes from 1 to ``maximum``, else None."""
    text = (text or u'').strip()
    if not 1 <= len(text) <= FIELD_DIGITS or text.strip(u'0123456789'):
        return None
    value = int(text)
    if value < 1 or value > maximum:
        return None
    return value


def ReasonProblem(text):
    """Why the server would refuse this reason, in Czech, or None."""
    text = (text or u'').strip()
    if len(text) > REASON_MAX:
        return u'Důvod má nejvýše %d znaků.' % REASON_MAX
    for character in text:
        if ord(character) < 32 or ord(character) >= 127 or character == u'|':
            return u'Důvod smí mít jen znaky bez diakritiky a bez svislítka.'
    return None


def Span(minutes):
    """"15 min", "1 h", "1 h 30 min": the wording of the chat lines (the server writes the same spans)."""
    hours, rest = divmod(int(minutes), 60)
    if not hours:
        return u'%d min' % rest
    return u'%d h' % hours if not rest else u'%d h %d min' % (hours, rest)


def PresetName(word):
    for preset, name in PRESETS:
        if preset == word:
            return name
    return None


def Reason(preset, text):
    """What goes after the two numbers: the chosen preset word, else the typed text, else nothing."""
    text = (text or u'').strip()
    if text:
        return text
    return preset or u''


def Command(start, duration, reason=u''):
    """The command line for a start and a duration (minutes) and an optional reason."""
    line = u'%s %d %d' % (COMMAND, start, duration)
    return u'%s %s' % (line, reason) if reason else line


def Check(startText, durationText, preset, reasonText):
    """(command, preview, problem) of the typed form: the line to send and the sentence the players will read, or
    None and the reason it cannot be sent. Empty fields are not yet a mistake (problem u'')."""
    startText, durationText = (startText or u'').strip(), (durationText or u'').strip()
    if not startText or not durationText:
        return None, u'', u''
    start = Minutes(startText, START_MAX)
    if start is None:
        return None, u'', u'Za kolik minut: celé číslo 1–%d.' % START_MAX
    duration = Minutes(durationText, DURATION_MAX)
    if duration is None:
        return None, u'', u'Délka v minutách: celé číslo 1–%d.' % DURATION_MAX
    problem = ReasonProblem(reasonText)
    if problem:
        return None, u'', problem
    reason = Reason(preset, reasonText)
    shown = PresetName(reason) or reason
    preview = u'Údržba serveru: začne za %s, potrvá asi %s.' % (Span(start), Span(duration))
    if shown:
        preview += u' Důvod: %s.' % shown
    return Command(start, duration, reason), preview, None
