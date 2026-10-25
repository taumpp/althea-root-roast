# -*- coding: utf-8 -*-
"""Woodcutting rhythm bar, version 2 (Dřevorubectví, concept D "rytmický pruh" with a direction per strike) and the
session controller behind it (the mode chosen in the craft book, the server lines, the direction keys).

Look: no window frame, the visual language of the mining ring. A dark translucent core with a soft shadow, a graphite
track, the bone "dobře" zone and the blood red (#D30D0E) "výborně" zone around a vertical hit line in the left part
of the bar (their widths follow great_ms / good_ms, which the server sets by the Dřevorubec level). Every strike is a
small steel plate with the bold arrow of its direction (← ↑ → ↓) sliding from the right to
the hit line: it shows lead_ms before its strike and crosses the line exactly at its due time (woodcheckmodel.MarkX),
white-hot with a blood red arrow inside the "dobře" window. A sent strike leaves the bar and the hit line flashes.
Under the bar one pip per strike, three per cut cycle ("seč") grouped: blood red VÝBORNĚ, ivory DOBŘE, grey VEDLE
(also a strike nobody pressed once its window passed). The plates and the bar are ui.Bar rectangles and a text line,
no new image files.

The server's answer (woodcheckmodel.Look, taken over from the mining ring): VÝBORNĚ = a white-hot flare on the hit
line, sparks and brownish wood chips (the mining spark / chip art, tinted with SetDiffuseColor), the bar jerks up
(the 112 % punch of the ring as a short vertical jerk: scaling a bar of ui.Bar rectangles is not possible), the
"výborně" zone flashes white-hot then blood red and a blood red ring (the mining burst, scaled down) flies out of the
hit line; the headline VÝBORNĚ in blood red rises into place; from the third VÝBORNĚ in a row diamonds under the text
and the brighter streak sound. DOBŘE softer (ivory), VEDLE = the bar jerks sideways and greys (grey headline). Sounds
as the mining ring (uiminingcheck.SOUNDS). Every strike VÝBORNĚ = "ČISTÁ SEČ" at the end. Under the headline the
running bonus "+N % dřeva"; the first bars of a session say what to do instead.

Where: centred above the woodcutter (chr.GetProjectPosition, woodcheckmodel.Anchor) clear of the name tag, following
it smoothly; when the character is not on the screen, above the quick slots in the middle; never over the bottom HUD.

Input: the arrows and W / A / S / D (game.OnKeyDown -> interface.MinigameDirectionKey -> WoodCheck.KeyDown, before
the keybindings and the movement) - while the bar is shown the key is taken: it never moves the character
(a step would cancel the cut) and its key up is swallowed as well (game.OnKeyUp -> MinigameDirectionKeyUp), so the
movement state cannot get stuck; a key the bar did not take keeps its key up. A press sends
"/wcheck hit <id> <strike> <elapsed_ms> <dir>" for the nearest strike not sent yet whose due time is within
good_ms + 120 ms with the direction of the pressed key, whatever the strike's own direction (the server judges a
wrong key as VEDLE); else nothing. Space and the mining hit key do not hit the bar. The click area (WoodCheckPad, a top window of its own over the bar
only, like MiningCheckPad) still takes the clicks on the bar so they never walk the character. Not modal, never
focused.

Low frame rates: the marks are drawn in OnRender at the time of that frame (time.perf_counter) and elapsed_ms of a
press is the time of the frame the player saw (woodcheckmodel.SeenTime), counted from the arrival of the check line.

Ends: about LINGER s after the last answer (a clean cut a little longer), or after the last window when answers are
missing (a sent strike waits RESULT_WAIT s for its answer); at once on WoodCheckEndV1 (the cut was cancelled) and a
new check line replaces the shown bar.

The controller (WoodCheck) mirrors uiminingcheck.MiningCheck: after the main character is in the world it loads the
mode of this character (woodcheckmodel.ModeStore, UserData; no stored choice = on) and sends "/wcheck mode <n>"
(again after RETRY seconds while the server has not confirmed it, at most ATTEMPTS times); SetMode (the craft book
switch) sends and stores it; WoodCheckModeV1 is the server's word. A failure while building the window is traced once
and the bars are then ignored in this session (woodcutting goes on without the bonus).
"""
import time

import ui

import uikit
import uir1
import uir1tokens as T
import uiremeslaart as A
import uiminingcheck as MCUI

import miningcheckmodel as MC
import woodcheckmodel as M

WHAT = 'woodcheck'
W, H = 420, 150                     # owner 12. 10. DR7 = B: the bar 380 x 42, plates 37, arrows 27 px
BAR_X, BAR_Y, BAR_W, BAR_H = 20, 70, 380, 42
BAR_MID = BAR_Y + BAR_H // 2
HIT_X = BAR_X + 77                  # the hit line (the carved notch)
MARK = 37                           # the iron plate of a mark (art: wood_check/plate_<dir>_<state>.png)
TRAVEL = BAR_X + BAR_W - 3 - MARK // 2 - HIT_X     # a mark enters here lead_ms before its strike
HEAD_Y = BAR_Y - 36                 # the headline above the plank (VÝBORNĚ / DOBŘE / VEDLE / ČISTÁ SEČ)
LINE_Y = BAR_Y + BAR_H + 8          # the bonus or the hint of the first bars, under the plank
ART = 'wood_check/'                 # AI-painted plank, iron plates with bone arrows, chips, slash (kolo 8)
DIR_NAME = {0: 'left', 1: 'up', 2: 'right', 3: 'down'}
PAD_MARGIN = 6                      # the pad takes clicks on the bar and this much around it
BOTTOM_GAP = 236                    # the fallback place above the task bar and the quick slots
HUD_BOTTOM = 112                    # the window never covers the bottom HUD
MARGIN = 6
HINT_BARS = 3                       # the first bars of a session also say what to do
RETRY, ATTEMPTS = 5.0, 2            # "/wcheck mode" while the server has not confirmed it
MARKS = 8                           # marks drawn at most at once
BURST_BASE = 0.33                   # the mining burst (a RING px ring) scaled down to the bar
FLARE_SCALE = 1.0                   # the mining flare on the thinner bar
SPARK_TRAVEL = 0.8                  # the spark paths of the ring, a little shorter
CHIP_TINT = (0.78, 0.56, 0.34)      # the stone chips tinted to wood (SetDiffuseColor)
SPARK_TINT = (1.0, 0.86, 0.62)      # warm splinter sparks

ARROW_FONT = 'Tahoma:28b'            # the arrow of a mark (Tahoma has the arrows U+2190-2193)
SOUND_TABLE = 'locale/common/woodcheck_sounds.txt'   # <event> <sound>... (data, not code)
SOUND_EVENTS = {'appear': 'appear', 'mark': 'mark', 'good': M.GOOD, 'great': M.GREAT, 'streak': 'streak',
                'perfect': 'perfect', 'miss': M.MISS}


def LoadSounds(lines):
    """{event key: (sound, ...)} from the lines of SOUND_TABLE; '#' comments, unknown events ignored."""
    sounds = {}
    for line in lines:
        fields = [f.strip() for f in line.rstrip('\r\n').split('\t')]
        if not fields or not fields[0] or fields[0].startswith('#') or fields[0] not in SOUND_EVENTS:
            continue
        sounds[SOUND_EVENTS[fields[0]]] = tuple(f for f in fields[1:] if f)
    return sounds


def ReadSoundTable(path=SOUND_TABLE):
    try:
        import app
        handle = app.OpenTextFile(path)
        try:
            return LoadSounds([app.GetTextFileLine(handle, i) for i in range(app.GetTextFileLineCount(handle))])
        finally:
            app.CloseTextFile(handle)
    except Exception:
        return {}


SOUNDS = None                       # loaded on the first sound (ReadSoundTable)
FX = {                              # the result art on the hit line: (file, size, peak scale, life s)
    'flash_good': ('flash_good.png', 36, 1.0, 0.25), 'burst_good': ('burst_good.png', 40, 1.0, 0.35),
    'flash_great': ('flash_great.png', 64, 1.0, 0.30), 'ring': ('ring.png', 72, 1.25, 0.45),
    'burst_great': ('burst_great.png', 74, 1.0, 0.45), 'dust_miss': ('dust_miss.png', 44, 1.1, 0.45)}
FX_OF = {M.GOOD: ('flash_good', 'burst_good'), M.GREAT: ('flash_great', 'ring', 'burst_great'), M.MISS: ('dust_miss',)}

STEEL = 0xFFD8D2CA                  # a brighter plate for the contrast of the arrow
STEEL_HOT = 0xFFF6EEE0
PLATE_RIM = 0xFF1C1A1A
GLYPH = 0xFF000000                  # black on the bright steel: readable at a glance
SHADOW = 0xFF000000
CORE = 0xFF0E0D0E
TRACK = 0xFF383434
EDGE = 0xFF4A3E36
GREY = 0xFF6E6863
PIP_OPEN = 0xFF4A4542
PIP_COLOR = {M.GREAT: T.RED, M.GOOD: T.IVORY, M.MISS: GREY}
HEADLINE = {M.GREAT: T.RED, M.GOOD: T.IVORY, M.MISS: T.MUTED}
FLASH = {M.GREAT: T.RED_HI, M.GOOD: T.IVORY, M.MISS: GREY, 'press': 0xFFFFFFFF}

IDLE, RUNNING = 'idle', 'running'


def Hint():
    """The first bars of a session: the arrows or W / A / S / D when a mark crosses the line."""
    return M.Tr('HINT_DIRS')


def Paint(bar, color, alpha):
    """Colour of a ui.Bar with alpha; the engine is called only when it changes."""
    MCUI._set(bar, 'color', (int(color) & 0xFFFFFFFF, round(M.Clamp01(alpha), 3)),
              lambda packed, a: bar.SetColor(uikit.GenerateColor(packed, a)))


def Tint(image, rgb, alpha):
    """Diffuse colour of an image (the chips to wood, the sparks warm); without SetDiffuseColor only the alpha."""
    setter = getattr(image, 'SetDiffuseColor', None)
    if setter is not None:
        MCUI._set(image, 'paint', (rgb[0], rgb[1], rgb[2], M.Clamp01(alpha)), setter)
    else:
        MCUI._set(image, 'paint', (M.Clamp01(alpha),), image.SetAlpha)


def Box(parent, x, y, w, h, color, alpha=1.0):
    bar = uikit.Rect(parent, x, y, max(1, int(w)), max(1, int(h)), color, alpha)
    bar.__dict__.setdefault('mc_cache', {})['color'] = (int(color) & 0xFFFFFFFF, round(M.Clamp01(alpha), 3))
    return bar


def Image(parent, name, x=0, y=0):
    """A plain not pickable image of the wood art."""
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(A.ROOT + ART + name)
    image.SetPosition(x, y)
    image.Show()
    return image


class Plate(object):
    """The mark of a strike: the iron plate with the bone arrow of its direction (idle / hot inside the "dobře"
    window / miss), one image per state (wood_check/plate_<dir>_<state>.png). Centre puts its middle on (x, y)."""

    def __init__(self, parent):
        self.image = Image(parent, 'plate_up_idle.png')
        self.name = 'plate_up_idle.png'
        self.size = MARK
        self.direction = 1

    def SetDirection(self, direction):
        self.direction = direction if direction in DIR_NAME else 1

    def SetState(self, state, alpha=1.0):
        name = 'plate_%s_%s.png' % (DIR_NAME[self.direction], state)
        if name != self.name:
            self.name = name
            self.image.LoadImage(A.ROOT + ART + name)
        MCUI.Paint(self.image, 1.0, alpha)

    def Centre(self, x, y):
        half = self.size // 2
        MCUI._set(self.image, 'pos', (int(round(x)) - half, int(round(y)) - half), self.image.SetPosition)

    def Show(self):
        self.image.Show()

    def Hide(self):
        self.image.Hide()

    def IsShow(self):
        return self.image.IsShow()

    def GetLocalPosition(self):
        return self.image.GetLocalPosition()


class WoodCheckPad(ui.Window):
    """The bar's click area: a top window of its own, shown only while strikes can be hit."""

    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.SetSize(BAR_W + 2 * PAD_MARGIN, BAR_H + 2 * PAD_MARGIN)

    def OnMouseLeftButtonDown(self):
        return True     # a click on the bar never walks the character (it would cancel the cut)


class WoodCheckWindow(ui.Window):
    def __init__(self, clock=None, send=None, play=None, project=None):
        self.state = IDLE                       # ui.Window.__init__ calls Hide() first
        ui.Window.__init__(self)
        self.clock = clock
        self.send = send
        self.play = play
        self.project = project
        self.session = None
        self.check = None
        self.begun_at = self.until = 0.0
        self.shown_at = self.prev_draw = self.last_draw = None
        self.sent_at = self.result_at = self.flash_at = None
        self.flash_kind = None
        self.headline_kind = None
        self.look_kind = self.look_strike = None
        self.streak_pips = 0
        self.anchor = None
        self.followed_at = None
        self.bars = 0
        self.speed = M.Speed(TRAVEL, 1200)

    def Build(self):
        kit = self.kit = uir1.Kit()
        self.SetSize(W, H)
        self.AddFlag('float')                   # SetTop brings it to the front; never 'movable', never focused
        self.AddFlag('not_pick')                # only the pad takes a click
        bar = self.barLayer = MCUI.Layer(self, 0, 0, W, H)     # jerks on a result (the marks with it)
        self.plank = Image(bar, 'bar.png', BAR_X - 6, BAR_Y - 5)            # 392 x 52: the plank with iron ends
        self.notch = Image(bar, 'notch.png', HIT_X - 37, BAR_Y)             # the carved hit notch (74 x 42)
        self.pointers = [Image(bar, 'pointer.png', HIT_X - 8, BAR_Y - 15), Image(bar, 'pointer.png', HIT_X - 8,
                                                                                  BAR_Y + BAR_H - 1)]
        try:
            self.pointers[1].SetRotation(180.0)
        except Exception:
            pass
        self.backdrop = [self.plank, self.notch] + self.pointers
        self.flash = Box(bar, HIT_X - 3, BAR_Y + 4, 6, BAR_H - 8, T.IVORY, 0.0)     # the key press, very short
        self.marks = [Plate(bar) for unused in range(MARKS)]
        for mark in self.marks:
            mark.Hide()
        # the result art on the hit line (kolo 8: a small DOBŘE, VÝBORNĚ as the owner liked it)
        self.fxLayer = MCUI.Layer(self, 0, 0, W, H)
        self.fx = {}
        for key, (name, size, unused, unused2) in FX.items():
            image = MCUI.Rotated(self.fxLayer, ART + name, size)
            image.Hide()
            self.fx[key] = image
        self.slash = Image(self.fxLayer, 'slash.png')
        self.slash.Hide()
        self.glow = Image(self, 'glow.png', W // 2 - 100, HEAD_Y - 14)
        self.glow.Hide()
        self.headline = uir1.Text(self, '', W // 2, HEAD_Y, kit.font('button'), T.IVORY, align='center', valign='top',
                                  outline=True)
        self.detail = uir1.Text(self, '', W // 2, LINE_Y, kit.font('text_s'), T.INK_DIM, align='center', valign='top',
                                outline=True)
        self.pad = WoodCheckPad()
        self.pad.Hide()
        self.Hide()

    # ------------------------------------------------------------------ geometry
    @staticmethod
    def Screen():
        return MCUI.MiningCheckWindow.Screen()

    def Project(self, height):
        if self.project is not None:
            return self.project(height)
        import chr
        import player
        return chr.GetProjectPosition(player.GetMainCharacterIndex(), int(height))

    def Target(self):
        """The window centre wanted now: above the woodcutter, else the fallback above the quick slots; kept so the
        whole window stays on the screen and off the bottom HUD."""
        sw, sh = self.Screen()
        try:
            centre = M.Anchor(self.Project(M.HEAD_HEIGHT), (sw, sh), (W, H))
        except Exception:
            centre = None
        if centre is None:
            centre = (sw / 2.0, sh - BOTTOM_GAP - H / 2.0)
        x = max(W / 2.0 + MARGIN, min(sw - W / 2.0 - MARGIN, centre[0]))
        y = max(H / 2.0 + MARGIN, min(sh - HUD_BOTTOM - H / 2.0, centre[1]))
        return x, y

    def Follow(self, now, snap=False):
        target = self.Target()
        dt = 0.0 if self.followed_at is None else now - self.followed_at
        self.followed_at = now
        self.anchor = target if snap else M.Follow(self.anchor, target, dt)
        x, y = int(round(self.anchor[0] - W / 2.0)), int(round(self.anchor[1] - H / 2.0))
        self.SetPosition(x, y)
        self.pad.SetPosition(x + BAR_X - PAD_MARGIN, y + BAR_Y - PAD_MARGIN)

    def Now(self):
        if self.clock is not None:
            return float(self.clock())
        return time.perf_counter()

    def Sound(self, key):
        global SOUNDS
        if SOUNDS is None:
            SOUNDS = ReadSoundTable()
        for path in SOUNDS.get(key, ()):
            try:
                if self.play is not None:
                    self.play(path)
                else:
                    import snd
                    snd.PlaySound(path)
            except Exception:
                pass

    def Elapsed(self, now):
        """Milliseconds since the check line arrived."""
        return M.ElapsedMs(self.begun_at, now)

    # ------------------------------------------------------------------ states
    def Begin(self, check, now=None):
        """Shows a new bar; a shown one is replaced completely (its late answers are ignored)."""
        now = self.Now() if now is None else now
        self.check = check
        self.session = M.Session(check)
        self.state = RUNNING
        self.begun_at = now
        self.shown_at = self.prev_draw = self.last_draw = None
        self.sent_at = self.result_at = self.flash_at = None
        self.flash_kind = self.headline_kind = None
        self.look_kind = self.look_strike = None
        self.streak_pips = 0
        self.announced = set()          # strikes whose mark entered the bar (the "mark" sound once each)
        self.until = 0.0
        self.bars += 1
        self.speed = M.Speed(TRAVEL, check.lead_ms)
        self.headline.SetText('')
        self.headline.SetPosition(W // 2, HEAD_Y)
        self.detail.SetText(Hint() if self.bars <= HINT_BARS else '')
        MCUI.TextColor(self.detail, T.INK_DIM, 1.0, outline=True)
        self.Draw(now, first=False)
        self.Sound('appear')
        if not self.IsShow():
            self.Follow(now, snap=True)
            self.Show()
            self.SetTop()
        self.pad.Show()
        self.pad.SetTop()

    def Hittable(self, now):
        """True while a strike can still be hit (the direction keys belong to the bar)."""
        return self.state == RUNNING and self.check is not None and \
            self.Elapsed(now) <= self.check.End() + M.PICK_SLACK_MS

    def Hit(self, now=None, direction=None):
        """A press of a ``direction`` key (LEFT / UP / RIGHT / DOWN): sends "/wcheck hit <id> <strike> <elapsed_ms>
        <dir>" for the nearest open strike. False when the press belongs to no strike, nothing can be hit or the
        press names no direction.
        elapsed_ms counts to the frame the player saw (woodcheckmodel.SeenTime)."""
        now = self.Now() if now is None else now
        if not self.Hittable(now):
            return False
        if isinstance(direction, bool) or direction not in M.DIRECTIONS:
            return False
        seen = M.SeenTime(now, self.prev_draw, self.last_draw)
        elapsed = M.ElapsedMs(self.begun_at, max(self.begun_at, seen))
        strike = self.session.Hit(elapsed, direction)
        if strike is None:
            return False
        self.sent_at = now
        self.flash_at, self.flash_kind = now, 'press'
        command = M.HitCommand(self.check, strike, elapsed, direction)
        if self.send is not None:
            self.send(command)
        else:
            import net
            net.SendChatPacket(command)
        return True

    def ShowResult(self, result, now=None):
        """The server's answer of a strike of the shown bar; another id or a hidden bar is ignored."""
        if self.state != RUNNING or self.session is None or not self.session.SetResult(result):
            return False
        now = self.Now() if now is None else now
        self.result_at = now
        self.flash_at, self.flash_kind = now, result.result
        self.look_kind, self.look_strike = result.result, result.strike
        perfect = self.session.Perfect()
        self.headline_kind = 'perfect' if perfect else result.result
        self.headline.SetText(M.Tr('PERFECT') if perfect else M.ResultText(result.result))
        self.detail.SetText(M.BonusText(self.session.bonus))
        # a streak shows as "VÝBORNĚ ×3" (owner 12. 10.: no red dots under the bar)
        streak = self.session.Streak() if result.result == M.GREAT else 0
        self.streak_pips = streak if streak >= 3 else 0
        if self.streak_pips and not perfect:
            self.headline.SetText('%s \xc3\x97%d' % (M.ResultText(result.result), streak) if str is bytes else
                                  u'%s \u00d7%d' % (M.ResultText(result.result), streak))
        self.Sound('perfect' if perfect else ('streak' if self.streak_pips else result.result))
        self.Draw(now, first=False)
        return True

    def Until(self, now):
        """When the bar hides: LINGER after the last answer once every strike is answered (a clean cut longer);
        otherwise LINGER after the last window, later while a sent strike still waits for its answer."""
        session, check = self.session, self.check
        if session.Complete() and self.result_at is not None:
            return self.result_at + (M.PERFECT_LINGER if session.Perfect() else M.LINGER)
        until = self.begun_at + (check.End() + M.PICK_SLACK_MS) / 1000.0 + M.LINGER
        if session.Waiting() and self.sent_at is not None:
            until = max(until, self.sent_at + M.RESULT_WAIT)
        if self.result_at is not None and session.Settled(self.Elapsed(now)) and not session.Waiting():
            until = min(until, max(self.result_at, self.begun_at + check.End() / 1000.0) + M.LINGER)
        return until

    def Stop(self, invalidate=False):
        if invalidate:
            self.check = None
            self.session = None
        self.state = IDLE
        self.pad.Hide()
        self.Hide()

    # ------------------------------------------------------------------ frames
    def OnUpdate(self):
        if self.state == IDLE:
            return
        self.Tick(self.Now())

    def Tick(self, now):
        """At most 60 Hz (the UI update): the end and the place above the character."""
        self.until = self.Until(now)
        if now >= self.until:
            self.Stop()
            return
        if not self.Hittable(now):
            self.pad.Hide()
        self.Follow(now)

    def OnRender(self):
        if self.state == IDLE:
            return
        self.Draw(self.Now())

    def Draw(self, now, first=True):
        """Every rendered frame: the marks at the time of this frame, the result art and the fades.
        ``first`` = a real frame (Begin and ShowResult draw once at once without counting a frame)."""
        if self.session is None:
            return
        if first:
            if self.shown_at is None:
                self.shown_at = now
            self.prev_draw, self.last_draw = self.last_draw, now
        shown = self.shown_at if self.shown_at is not None else now
        alpha = M.Appear(now - shown)
        if self.until:
            alpha *= M.FadeOut(now, self.until)
        elapsed = self.Elapsed(now)
        since = (now - self.result_at) if self.result_at is not None else None
        look = M.Look(self.look_kind, since) if since is not None else None
        jerk = (look.shake, look.jerk) if look is not None and self.look_kind == M.MISS else (0, 0)
        MCUI._set(self.barLayer, 'pos', jerk, self.barLayer.SetPosition)
        for image in self.backdrop:
            MCUI.Paint(image, 1.0, alpha)
        flash = M.Flash(now - self.flash_at) if self.flash_at is not None and self.flash_kind == 'press' else 0.0
        Paint(self.flash, T.IVORY, 0.45 * flash * alpha)
        self.DrawMarks(elapsed, alpha)
        self.DrawFx(since, alpha)
        red = self.headline_kind == 'perfect' or self.headline_kind == M.GREAT
        if look is not None:
            self.headline.SetPosition(W // 2, HEAD_Y + look.text_rise)
            color = T.RED if red else HEADLINE.get(self.headline_kind, T.MUTED)
            MCUI.TextColor(self.headline, color, look.text_alpha * alpha, outline=True)
            MCUI.TextColor(self.detail, T.INK, alpha, outline=True)
            if red:
                MCUI.Paint(self.glow, 1.0, 0.7 * look.text_alpha * alpha)
                self.glow.Show()
            else:
                self.glow.Hide()
        else:
            self.glow.Hide()
            MCUI.TextColor(self.detail, T.INK_DIM, alpha, outline=True)

    def DrawMarks(self, elapsed, alpha):
        """The iron plates of the open strikes with the arrows of their directions: on the hit line exactly at their
        due time; red-hot inside the "dobře" window, dimmer once past it; hidden outside the plank."""
        check = self.check
        marks = M.Marks(check, elapsed, self.session.Taken()) if self.state == RUNNING else []
        index = 0
        for strike, ahead in marks:
            if index >= len(self.marks):
                break
            x = M.MarkX(check.Due(strike), elapsed, HIT_X, M.Speed(TRAVEL, check.Lead(strike)))
            if x - MARK / 2.0 < BAR_X or x + MARK / 2.0 > BAR_X + BAR_W:
                continue
            if strike not in self.announced:
                self.announced.add(strike)
                self.Sound('mark')
            mark = self.marks[index]
            index += 1
            mark.SetDirection(check.Direction(strike))
            if abs(ahead) <= check.good_ms:
                mark.SetState('hot', alpha)
            elif ahead < 0:
                mark.SetState('miss', 0.6 * alpha)
            else:
                mark.SetState('idle', alpha)
            mark.Centre(x, BAR_MID)
            mark.Show()
        for mark in self.marks[index:]:
            mark.Hide()
        # the answered strike stays on the line a moment: red-hot (VÝBORNĚ / DOBŘE) or grey and cracked (VEDLE)
        shown = index
        if self.look_kind is not None and self.result_at is not None and shown < len(self.marks):
            since = self.Now() - self.result_at
            if since < 0.35 and self.look_strike is not None:
                mark = self.marks[shown]
                mark.SetDirection(check.Direction(self.look_strike))
                mark.SetState('miss' if self.look_kind == M.MISS else 'hot', (1.0 - since / 0.35) * alpha)
                mark.Centre(HIT_X + (10 if self.look_kind == M.MISS else 0), BAR_MID + (2 if self.look_kind == M.MISS else 0))
                mark.Show()

    def DrawFx(self, since, alpha):
        """The result art on the hit line: DOBŘE small (flash + a few chips), VÝBORNĚ flash + blood red ring + chips,
        VEDLE grey dust; ČISTÁ SEČ adds one short slash across the plank."""
        keys = FX_OF.get(self.look_kind, ()) if since is not None else ()
        for key, image in self.fx.items():
            name, size, peak, life = FX[key]
            if key not in keys or since >= life:
                image.Hide()
                continue
            t = since / life
            scale = 0.7 + (peak - 0.7) * M.EaseOut(min(1.0, t * 2.0))
            image.SetPosition(int(round(HIT_X - size / 2.0)), int(round(BAR_MID - size / 2.0)) - (6 if 'burst' in key else 0))
            MCUI.Scale(image, scale)
            MCUI.Paint(image, 1.0, (1.0 - t) * alpha)
            image.Show()
        if since is not None and self.headline_kind == 'perfect' and since < 0.6:
            t = since / 0.6
            self.slash.SetPosition(BAR_X + BAR_W // 2 - 105 + 20, BAR_MID - 20)
            MCUI.Paint(self.slash, 1.0, (1.0 - t) * alpha)
            self.slash.Show()
        else:
            self.slash.Hide()

    def Destroy(self):
        self.state = IDLE
        self.Hide()
        self.check = None
        self.session = None
        self.send = None
        self.play = None
        self.project = None
        if getattr(self, 'pad', None) is not None:
            self.pad.Hide()
            self.pad.hit = None


def CreateWindow(clock=None, send=None, play=None, project=None):
    window = WoodCheckWindow(clock, send, play, project)
    window.Build()
    return window


# --------------------------------------------------------------------------- the session controller
class WoodCheck(object):
    """The mode of the character (store + server sync), the bar window and the hits (the direction keys)."""

    def __init__(self, store=None, send=None, clock=None, identity=None, play=None, project=None, keys=None):
        self.store = store or M.ModeStore()
        self._send = send
        self._clock = clock
        self._identity = identity
        self._play = play
        self._project = project
        self._keys = None if keys is None else dict(keys)     # DIK code -> LEFT / UP / RIGHT / DOWN
        self.held = set()               # the direction keys taken by the bar: their key up is swallowed
        self.confirmed = None           # the last WoodCheckModeV1 of this character
        self.name = None                # the character the mode was sent for
        self.attempts = 0
        self.sent_at = None
        self.window = None
        self.failed = False

    # ------------------------------------------------------------------ engine adapters
    def Send(self, command):
        if self._send is not None:
            self._send(command)
            return
        import net
        net.SendChatPacket(command)

    def Clock(self):
        if self._clock is not None:
            return float(self._clock())
        return time.perf_counter()

    def Identity(self):
        """The character name once the main character is in the world, else ''."""
        if self._identity is not None:
            return self._identity() or ''
        try:
            import chr
            import player
            name = player.GetName()
            index = player.GetMainCharacterIndex()
            if not name or not index or not chr.HasInstance(index):
                return ''
            return name
        except Exception:
            return ''

    # ------------------------------------------------------------------ mode
    @property
    def mode(self):
        return self.store.mode

    def Update(self):
        """Every game frame: the first frame with the main character sends its mode; a retry while unconfirmed."""
        name = self.Identity()
        if not name:
            return
        if name != self.name:
            self.name = name
            try:
                self.store.SetIdentity(name)
            except Exception:
                pass
            self.confirmed = None
            self.attempts = 0
            self.SendMode()
            return
        if self.confirmed != self.store.mode and self.attempts < ATTEMPTS and self.sent_at is not None and \
                self.Clock() - self.sent_at >= RETRY:
            self.SendMode()

    def SendMode(self):
        self.attempts += 1
        self.sent_at = self.Clock()
        self.Send(M.COMMAND_MODE % self.store.mode)

    def SetMode(self, mode):
        """The craft book switch: sent at once, then stored for this character (a failed store only loses the local
        copy; the server keeps the mode in its quest flag)."""
        if isinstance(mode, bool) or mode not in M.MODES:
            return False
        self.store.mode = mode
        self.store.explicit = True
        self.attempts = 0
        self.SendMode()
        try:
            self.store.Set(mode)
        except Exception:
            pass
        if mode == M.MODE_OFF:
            self.HideWindow()
        return True

    def ModeLabels(self):
        """[(mode, label)] of the craft book switch: Vypnuto | Zapnuto."""
        return M.ModeLabels()

    def Pending(self):
        """True while the server has not confirmed the chosen mode."""
        return self.confirmed != self.store.mode

    # ------------------------------------------------------------------ server lines
    def Feed(self, command, args=()):
        """One server line; True when it was valid."""
        args = tuple(args or ())
        if command == M.MODE:
            mode = M.ParseMode(args)
            if mode is None:
                return False
            self.confirmed = mode
            if mode != self.store.mode:
                if not getattr(self.store, 'explicit', True):
                    self.store.mode = mode      # no own choice yet: show the server's word, keep the default
                    return True
                try:
                    self.store.Set(mode)        # the server's word (its quest flag)
                except Exception:
                    self.store.mode = mode
            return True
        if command in (M.CHECK_V3, M.CHECK_V2):
            parse = {M.CHECK_V3: M.ParseCheckV3, M.CHECK_V2: M.ParseCheckV2}[command]
            check = parse(args)
            if check is None:
                return False
            window = self.Window()
            if window is not None:
                window.Begin(check, self.Clock())
            return True
        if command == M.RESULT:
            result = M.ParseResult(args)
            if result is None:
                return False
            if self.window is not None:
                self.window.ShowResult(result, self.Clock())
            return True
        if command == M.END:
            check_id = M.ParseEnd(args)
            if check_id is None:
                return False
            window = self.window
            if window is not None and window.check is not None and window.check.id == check_id:
                window.Stop(invalidate=True)
            return True
        return False

    def Window(self):
        if self.window is None and not self.failed:
            try:
                self.window = CreateWindow(self.Clock, self.Send, self._play, self._project)
            except Exception:
                self.failed = True
                self.window = None
                uir1.TraceFailure(WHAT)
        return self.window

    def Shown(self):
        window = self.window
        return window is not None and window.state == RUNNING and window.IsShow()

    def Keys(self):
        """{DIK code: direction} of the arrows and W / A / S / D (app.DIK_<name>, woodcheckmodel.KEY_DIRECTIONS)."""
        if self._keys is None:
            keys = {}
            try:
                import app
                for name, direction in M.KEY_DIRECTIONS:
                    code = getattr(app, 'DIK_' + name, None)
                    if code is not None:
                        keys[code] = direction
            except Exception:
                return {}
            self._keys = keys
        return self._keys

    def KeyDirection(self, key):
        return self.Keys().get(key)

    def KeyDown(self, key):
        """An arrow or W / A / S / D (game.OnKeyDown -> interface.MinigameDirectionKey): while the bar is shown the
        key is taken (True: no step), even when the press belongs to no strike or every window has closed; while
        strikes can still be hit the direction goes to the nearest open strike. A step or its stop
        (CPythonPlayer::NEW_Stop -> CActorInstance::Stop) clears the queued woodcut motions while the server keeps
        the cut at the tree, so a press after the last window (the chop and the linger still run) or its key up
        at the start of the next cut left the character standing. An auto-repeat of a taken key stays taken while
        the bar is shown. False for any other key or without a bar (the character walks as usual)."""
        direction = self.KeyDirection(key)
        if direction is None:
            return False
        if key in self.held:
            if self.Shown():
                return True
            self.held.discard(key)              # a lost key up: never keep a movement key swallowed
        if not self.Shown():
            return False
        now = self.Clock()
        if self.window.Hittable(now):
            self.window.Hit(now, direction)
        self.held.add(key)
        return True

    def KeyUp(self, key):
        """The key up of a key the bar took (game.OnKeyUp -> interface.MinigameDirectionKeyUp): swallowed (True), it
        never started a step; any other key up goes on (a step started before the bar still stops)."""
        if key in self.held:
            self.held.discard(key)
            return True
        return False

    def HideWindow(self):
        if self.window is not None:
            self.window.Stop(invalidate=True)

    def Destroy(self):
        if self.window is not None:
            self.window.Destroy()
        self.window = None
