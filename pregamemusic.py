# -*- coding: utf-8 -*-
"""The music before the game: the login, the character select and the creation.

Exactly one track plays. The engine's fades (SoundEngine::FadeInMusic / FadeOutMusic) only move in
SoundEngine::Update, which the EXE calls from __UpdateCamera - in the game phase only. Before the game a FadeOutMusic
never fades anything: the old track went on at full volume next to the new one ("v login menu mi hrajou dvě hudby
naráz" - the hall's track left over from the select, the login music started over it). So here:
  - Only(path) frees BOTH music slots of the engine (FadeInMusic of a different file swaps the slots and destroys the
    other one: two placeholder swaps destroy both) and starts the track alone; the last placeholder is told to stop
    (it never got a volume, and stops at the first engine update in the game);
  - fades are ours: each select/create phase update ticks SetMusicVolume, independently of its UI appearance;
  - the select and the creation call Only with the same file: the playing track goes on (no restart).

The hall's tracks (bgm/bgm/althea_*.flac, seamless loops, tools/pregame_music_loop.py): pregame-hall.cfg music=
shuffle (default: a random track, at its end the next random one, faded), random (one random track per client start,
looped) or a track's key. F8 in the select (uipregamehall.Hall.CycleMusic) steps to the next track.
"""
import random

import app
import snd

try:
    import systemSetting
except ImportError:                      # the tests
    systemSetting = None

# key, name, loop length in s (the file's own length: the shuffle moves on there)
TRACKS = (('crimson_citadel', 'Crimson Citadel', 119.23), ('blood_and_steel', 'Blood and Steel', 104.72),
          ('by_blood_and_steel', 'By Blood and Steel', 58.84), ('rise_althea', 'Rise, Althea', 43.88))
MODES = ('shuffle', 'random')
FADE_IN = 1.5                            # s, the start of a track
FADE_OUT = 1.2                           # s, before a switch (F8, the shuffle)
# real files the engine can open, only as placeholders of the slot swaps (never heard: volume 0, then stopped)
SPARE = ('BGM/characterselect.mp3', 'BGM/login_window.mp3') + tuple('BGM/althea_%s.flac' % k for k, n, l in TRACKS)

state = {'path': None, 'key': None, 'mode': None, 'start': 0.0, 'fade': None, 'next': None}


def Path(key):
    return 'BGM/althea_%s.flac' % key


def Name(key):
    for k, name, unused in TRACKS:
        if k == key:
            return name
    return key


def Length(key):
    for k, unused, length in TRACKS:
        if k == key:
            return length
    return 0.0


def Volume():
    try:
        return max(0.0, min(1.0, float(systemSetting.GetMusicVolume())))
    except Exception:
        return 1.0


def Exists(path):
    import os
    name = path.split('/', 1)[-1]
    return os.path.exists(path) or os.path.exists(os.path.join('bgm', name)) or os.path.exists(os.path.join('BGM', name))


def Only(path, fade=False):
    """``path`` ('BGM/...') the one music playing; the same track already playing goes on. fade = our fade-in (only
    where the owning phase ticks every frame), else at once at the game's music volume."""
    now = app.GetTime()
    if state['path'] == path:
        snd.FadeInMusic(path)                # resumes it if the engine had stopped it
        if not fade or state['fade'] is None:
            state['fade'], state['next'] = None, None
            snd.SetMusicVolume(Volume())
        return False
    spare = [p for p in SPARE if p != path and p != state['path'] and Exists(p)]
    if len(spare) >= 2:
        w1, w2 = spare[0], spare[1]
        snd.FadeInMusic(w1)                  # swap: the other slot destroyed (or w1 already current: no swap)
        snd.FadeInMusic(w2)                  # swap: the slot of w1 / the old current destroyed
        snd.FadeInMusic(path)                # swap: the last old slot destroyed, the track alone (at volume 0)
        snd.FadeOutMusic(w2)                 # the placeholder stops at the engine's first update (in the game)
    else:
        snd.FadeInMusic(path)
    state['path'], state['start'], state['next'] = path, now, None
    if fade:
        snd.SetMusicVolume(0.0)
        state['fade'] = ('in', now, FADE_IN)
    else:
        snd.SetMusicVolume(Volume())
        state['fade'] = None
    return True


def Leave():
    """Into the game: its own music code takes over (the engine fades work there)."""
    state.update({'path': None, 'key': None, 'fade': None, 'next': None})


def Choose(mode, current=None):
    keys = [k for k, unused, unused2 in TRACKS if Exists(Path(k))] or [TRACKS[0][0]]
    others = [k for k in keys if k != current] or keys
    return random.choice(others)


def HallTrack(cfg_value):
    """The key the hall plays: the one already playing (select <-> creation), else from the cfg."""
    value = str(cfg_value or 'shuffle').strip().lower()
    if state['key'] is not None and state['path'] == Path(state['key']):
        return state['key']
    keys = [k for k, unused, unused2 in TRACKS]
    state['mode'] = value if value in MODES else None
    if value in keys:
        return value
    return Choose(value)


def PlayHall(cfg_value, fade=True):
    """The select / creation music: Only(track); musicinfo follows (the game's fade at the start uses it).
    Returns the file name (in BGM/) or None when the hall's tracks are missing."""
    key = HallTrack(cfg_value)
    path = Path(key)
    if not Exists(path):
        return None
    state['key'] = key
    Only(path, fade)
    return _Musicinfo(path)


def _Musicinfo(path):
    name = path.split('/', 1)[1]
    try:
        import musicInfo
        musicInfo.selectMusic = musicInfo.createMusic = name
    except Exception:
        pass
    return name


def Switch(key):
    """F8 / the shuffle: the current track fades out (FADE_OUT), then ``key`` fades in."""
    if not Exists(Path(key)):
        return False
    state['next'] = key
    state['fade'] = ('out', app.GetTime(), FADE_OUT)
    return True


def Step():
    """F8: the next track of TRACKS (the mode stays: shuffle goes on from it)."""
    keys = [k for k, unused, unused2 in TRACKS]
    cur = state['next'] or state['key']
    key = keys[(keys.index(cur) + 1) % len(keys)] if cur in keys else keys[0]
    return key if Switch(key) else None


CFG = 'pregame-hall.cfg'
# the settings' "Hudba v menu" (settingsbackend: menu_music): shuffle or one track
MENU_CHOICES = ('shuffle',) + tuple(k for k, unused, unused2 in TRACKS)


def MenuLabels(shuffle_label):
    return [('shuffle', shuffle_label)] + [(k, name) for k, name, unused in TRACKS]


def ReadSetting():
    """music= of pregame-hall.cfg as the settings show it (shuffle when unset / random / unknown)."""
    try:
        with open(CFG, 'r') as stream:
            for line in stream.read(65536).splitlines():
                if '=' in line and not line.strip().startswith('#'):
                    key, value = [part.strip() for part in line.split('=', 1)]
                    if key == 'music' and value.lower() in MENU_CHOICES:
                        return value.lower()
    except (IOError, OSError):
        pass
    return 'shuffle'


def WriteSetting(value):
    """music=<value> into pregame-hall.cfg (the other lines kept) and at once into the music playing in the hall."""
    if value not in MENU_CHOICES:
        raise ValueError('Unknown menu music: %r' % (value,))
    try:
        with open(CFG, 'r') as stream:
            lines = stream.read(65536).splitlines()
    except (IOError, OSError):
        lines = []
    out, done = [], False
    for line in lines:
        if '=' in line and not line.strip().startswith('#') and line.split('=', 1)[0].strip() == 'music':
            if not done:
                out.append('music=%s' % value)
                done = True
            continue
        out.append(line)
    if not done:
        out.append('music=%s' % value)
    tmp = CFG + '.tmp'
    with open(tmp, 'w') as stream:
        stream.write('\n'.join(out) + '\n')
    import os
    os.replace(tmp, CFG)
    # the hall's music now (the settings open over the select / the creation)
    if state['key'] is not None and state['path'] == Path(state['key']):
        state['mode'] = 'shuffle' if value == 'shuffle' else None
        if value != 'shuffle' and value != (state['next'] or state['key']):
            Switch(value)
    return value


def UpdatePhase(window):
    """The phase owns playback; a missing or failed hall only removes the track toast."""
    started = Tick(app.GetTime())
    if started is None or state['mode'] != 'shuffle':
        return
    presentation = getattr(window, 'r1', None)
    hall = presentation if getattr(presentation, 'is_hall', False) else getattr(presentation, 'hall', None)
    if hall is not None and not getattr(hall, 'failed', False):
        hall.ShowMusic('Hudba: %s' % Name(started))


def Tick(now):
    """Every phase frame: our fades and shuffle. Returns the key of a track that has just started."""
    started = None
    fade = state['fade']
    if fade is not None:
        kind, t0, length = fade
        u = max(0.0, min(1.0, (now - t0) / length))
        if kind == 'in':
            snd.SetMusicVolume(Volume() * u)
            if u >= 1.0:
                state['fade'] = None
        else:
            snd.SetMusicVolume(Volume() * (1.0 - u))
            if u >= 1.0:
                key, state['next'] = state['next'], None
                state['key'] = key
                Only(Path(key), True)
                _Musicinfo(Path(key))
                started = key
    elif state['mode'] == 'shuffle' and state['key'] is not None and state['path'] == Path(state['key']):
        length = Length(state['key'])
        if length and now - state['start'] >= length - FADE_OUT:
            Switch(Choose('shuffle', state['key']))
    return started
