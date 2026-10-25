# -*- coding: utf-8 -*-
"""Mining skill check (Řemesla krok 2 + 2b): concept A "Krvavá žíla" - a ring beside the miner's shoulder, and the
session controller behind it (the mode chosen in the craft book, the server lines, the hit).

Look (krok2-vzhled/NAVRH.md, concept A, backdrop V5): no window frame. A dark translucent core with a soft shadow,
a graphite track with ticks every 30 degrees, the bone "dobře" zone and the blood red (#D30D0E) "výborně" zone
(white ticks on its edges), a short needle across the rim with a hot trail. The middle stays empty (owner round 2,
centre A: "Klik" on a keycap was ugly; the hint of the first rings names a bound key). The ring comes in (115 % -> 100 %, 0.15 s, a quiet tick), the needle turns clockwise from the top, 360 degrees
per period_ms, and glows white-hot inside a zone (local feedback only, the server decides).
Result (miningcheckmodel.Feedback): VÝBORNĚ reads as a pickaxe striking stone - a white-hot flare where the needle
struck, steel sparks, stone chips flying out and falling, the ring punches to 112 %, the zone flashes and a blood red
ring flies out, a stony crack + "čink" (brighter from the third VÝBORNĚ in a row, with diamonds under the text), the
headline in blood red; DOBŘE - softer, no flare / sparks / chips; VEDLE - the ring jerks and turns grey, a soft
knock, no punishment. The text rises into
place under the ring.

Where: beside the shoulder of the main character (chr.GetProjectPosition, miningcheckmodel.Anchor), following it
smoothly; when the character is not on the screen, above the quick slots in the middle. Variant C (mode 3) sends a
ring every 2 swings while the mining runs: a new ring replaces the shown one at once.

Clicks: only the square of the ring takes a click, and only while the needle turns: MiningCheckPad, a top window of
its own ('float', raised over the ring on every new ring) - CWindowManager raises the top window under the mouse
before picking, so a pad inside the 'not_pick' window would lose the click to an inventory lying under the ring. The
rest of the window and the ring after the hit let a click through to what lies below, as if the ring were not there.
A click on the ring (it never reaches the ground or the vein behind it: that would move the character and cancel
variant A), Space (game.OnKeyDown -> MiningCheck.SpaceHit: while a ring is up Space hits instead of attacking, a
second press is swallowed until the answer) or the key of the action (Settings -> Klávesové zkratky -> Systémy,
unbound by default) sends "/mcheck hit <id> <elapsed_ms>" once and freezes the needle. Result 3 (the server's
timeout, or a check it closed: a mode change, a new B check, A cancelled, the end of a C mining) closes it quietly. Without a hit
it hides after timeout_ms; after a hit it waits RESULT_WAIT seconds for the answer. It is not modal and never takes
the keyboard focus: the character keeps walking and attacking.

Low frame rates (krok 2b): the needle is drawn in OnRender at the time of that frame (time.perf_counter, not the
float app.GetTime of the frame start), and elapsed_ms of a hit is the time of the frame the player saw when pressing
(miningcheckmodel.SeenTime): the game handles a click after the frame and a key in the next one, which used to cost
one to two frames - at 30 FPS 10 to 20 degrees, more than the whole "výborně" zone. The frozen needle shows that
moment. OnUpdate (at most 60 Hz) only follows the character and ends the states.

Rotation: CGraphicExpandedImageInstance::OnRender centres a rotated quad on position + origin and scales it about
that centre; at the angle 0 it draws from the position and scales from the corner. So every rotated or scaled image
is RING x RING (SPARK x SPARK) with its origin at its middle (set after every LoadImage: a new image instance resets
the origin, the rotation, the scale and the colour) and never turned by exactly 0 degrees (TURN_MIN instead).

The controller (MiningCheck): after the main character is in the world it loads the mode of this character
(miningcheckmodel.ModeStore, UserData; no stored choice = DEFAULT_MODE, i.e. on) and sends "/mcheck mode <n>" (again
after RETRY seconds while the server has not confirmed it, at most ATTEMPTS times); SetMode (the craft book switch)
sends it and stores it; MiningCheckModeV1 is the server's word, stored only once the player has an own choice. A
failure while building the window is traced once (uir1.TraceFailure) and the checks are then ignored in this session
(mining goes on with the full number of swings).
"""
import time

import ui

import uir1
import uir1tokens as T
import uiremeslaart as A

import miningcheckmodel as M

WHAT = 'miningcheck'
W, H = 280, 248
RING = A.RING
RING_X, RING_Y = (W - RING) // 2, 24
CX, CY = RING_X + RING / 2.0, RING_Y + RING / 2.0      # the ring centre in the window
PAD = 150                                                # the square that takes the click
PAD_X, PAD_Y = int(round(CX - PAD / 2.0)), int(round(CY - PAD / 2.0))
HEAD_Y = int(CY) + 72               # the headline (VÝBORNĚ / DOBŘE / VEDLE)
LINE_Y = HEAD_Y + 24                # the detail ("-2 údery") or the hint of the first rings
PIPS_Y = LINE_Y + 24                # VÝBORNĚ in a row
TURN_MIN = 0.01                     # the engine draws the angle 0 from the corner, never use it
BOTTOM_GAP = 236                    # the fallback place above the task bar and the quick slots
HUD_BOTTOM = 112                    # the window never covers the bottom HUD
MARGIN = 6
RESULT_WAIT = 2.0                   # after a hit: how long to wait for the server's answer
HINT_RINGS = 3                      # the first rings of a session also say what to do
ACTION_ID = 'system.mining_check'   # keybindings: the hit, unbound by default (Space hits anyway)
RETRY, ATTEMPTS = 5.0, 2            # "/mcheck mode" while the server has not confirmed it

SOUNDS = {                          # layers play at once (each file has its own 2D voice, SoundEngine)
    'appear': ('sound/ui/click.wav',),                          # a quiet tick: the ring is there
    M.GREAT: ('sound/ui/make_soket.wav',),                      # the socket "tchink" (owner 8. 10.: the perfect hit
                                                                # gets the old DOBŘE sound)
    'streak': ('sound/ui/make_soket.wav', 'sound/ui/bracelet.wav'),   # 3+ in a row: brighter
    M.GOOD: ('sound/ui/make_soket.wav',),                       # a smaller "tchink"
    M.MISS: ('sound/ui/jaeryun_fail.wav',),                     # the blacksmith's failed-refine crack (owner 8. 10.)
}

IDLE, RUNNING, SENT, RESULT = 'idle', 'running', 'sent', 'result'
HEADLINE = {M.GREAT: T.RED, M.GOOD: T.IVORY, M.MISS: T.MUTED, M.TIMEOUT: T.MUTED}    # VÝBORNĚ in blood red
DETAIL = {M.GREAT: T.INK, M.GOOD: 0xFFD2CABE, M.MISS: T.MUTED, M.TIMEOUT: T.MUTED}


def KeyName():
    """The key bound to the hit action ("F8"), '' when it is unbound."""
    try:
        import keybindings
        manager = keybindings.GetManager()
        shortcut = manager._state.get(ACTION_ID) if manager is not None else None
        return shortcut.display() if shortcut is not None else ''
    except Exception:
        return ''


def Hint():
    """Space always hits a turning ring (MiningCheck.SpaceHit); a bound key is named instead when there is one."""
    return M.Tr('HINT_KEY') % (KeyName() or M.Tr('SPACE'))


def WithAlpha(color, alpha):
    """A packed ARGB colour with the alpha ``alpha`` (0..1)."""
    return (int(round(M.Clamp01(alpha) * 255)) << 24) | (int(color) & 0xFFFFFF)


def Signed(color):
    """A packed colour as the signed int the engine's PyTuple_GetInteger takes (DWORD(iColor) keeps the bits)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color >= 0x80000000 else color


def TextColor(line, color, alpha, outline=False):
    """Text colour with alpha. CGraphicTextInstance draws the outline in its own colour (opaque black by default):
    a fading outlined text would leave hollow black letters, so the outline gets the same alpha
    (wndMgr.SetOutlineColor with a packed colour)."""
    # signed: wndMgr.SetFontColor parses a C int and silently ignores 0x80000000+ (an opaque colour), so without it
    # the text stayed at the half-transparent colour of the fade-in under an opaque black outline (dark in game)
    _set(line, 'color', Signed(WithAlpha(color, alpha)), line.SetPackedFontColor)
    if outline:
        def outline_color(value):
            try:
                import wndMgr
                wndMgr.SetOutlineColor(line.hWnd, Signed(value))
            except Exception:
                pass
        _set(line, 'outline', WithAlpha(0, alpha), outline_color)


def Turn(image, angle):
    """SetRotation that never draws through the angle-0 branch (corner origin, corner scaling)."""
    angle = float(angle) % 360.0
    if angle < TURN_MIN or angle > 360.0 - TURN_MIN:
        angle = TURN_MIN
    _set(image, 'turn', angle, image.SetRotation)


def _set(image, key, value, setter):
    """Calls the engine only when the value changes (the ring updates ~30 images a frame)."""
    cache = image.__dict__.setdefault('mc_cache', {})
    if cache.get(key) == value:
        return
    cache[key] = value
    setter(*value) if isinstance(value, tuple) else setter(value)


def Scale(image, scale):
    _set(image, 'scale', (scale, scale), image.SetScale)


def Paint(image, grey, alpha):
    """Diffuse colour: ``grey`` darkens (VEDLE), ``alpha`` fades. Without SetDiffuseColor only the alpha."""
    setter = getattr(image, 'SetDiffuseColor', None)
    if setter is not None:
        _set(image, 'paint', (grey, grey, grey, alpha), setter)
    else:
        _set(image, 'paint', (alpha,), image.SetAlpha)


def Additive(image):
    try:
        import wndMgr
        mode = getattr(wndMgr, 'RENDERING_MODE_MODULATE', None)
        if mode is not None:
            image.SetRenderingMode(mode)
    except Exception:
        pass


class Layer(ui.Window):
    """Not pickable layer over the ring (its images draw in the order of the layers, whatever is made later)."""

    def __init__(self, parent, x=RING_X, y=RING_Y, w=RING, h=RING):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.home = (x, y)
        self.SetPosition(x, y)
        self.SetSize(w, h)
        self.Show()


def Rotated(parent, name, size=RING, additive=False):
    """A size x size image that turns and scales about its middle (origin = half the texture, set after LoadImage)."""
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(A.ROOT + name)
    image.SetOrigin(size / 2.0, size / 2.0)
    image.SetPosition(0, 0)
    try:
        image.SetLinearFiltering(True)          # a turned texture point-sampled is jagged
    except Exception:
        pass
    if additive:
        Additive(image)
    Turn(image, TURN_MIN)
    image.Show()
    return image


class MiningCheckPad(ui.Window):
    """The square of the ring that takes the click: a top window of its own, shown only while the needle turns."""

    def __init__(self, hit):
        ui.Window.__init__(self)
        self.hit = hit
        self.AddFlag('float')
        self.SetSize(PAD, PAD)

    def OnMouseLeftButtonDown(self):
        if self.hit is not None:
            self.hit()
        return True


class MiningCheckWindow(ui.Window):
    def __init__(self, clock=None, send=None, play=None, project=None):
        self.state = IDLE                       # ui.Window.__init__ calls Hide() first
        ui.Window.__init__(self)
        self.clock = clock
        self.send = send
        self.play = play
        self.project = project
        self.check = None
        self.result = None
        self.resolved = False
        self.begun_at = self.deadline = self.until = 0.0
        self.shown_at = self.prev_draw = self.last_draw = None
        self.hit_at = self.result_at = None
        self.hit_ms = None
        self.angle = 0.0
        self.anchor = None
        self.followed_at = None
        self.streak = 0
        self.rings = 0

    def Build(self):
        kit = self.kit = uir1.Kit()
        self.SetSize(W, H)
        self.AddFlag('float')                   # SetTop brings it to the front; never 'movable', never focused
        self.AddFlag('not_pick')                # only the pad takes a click
        self.coreLayer = Layer(self)
        self.core = Rotated(self.coreLayer, 'mining_check/core.png')
        self.ringLayer = Layer(self)
        self.ring = Rotated(self.ringLayer, 'mining_check/ring.png')
        self.goodLayer = Layer(self)
        self.greatLayer = Layer(self)
        self.good, self.great = [], []
        self.ticks = [Rotated(self.greatLayer, 'mining_check/great_tick.png') for unused in range(2)]
        self.flashLayer = Layer(self)
        self.flash = Rotated(self.flashLayer, 'mining_check/zone_flash.png', additive=True)
        self.needleLayer = Layer(self)
        self.trail = Rotated(self.needleLayer, 'mining_check/needle_trail.png', additive=True)
        self.needle = Rotated(self.needleLayer, 'mining_check/needle.png')
        self.needleHot = Rotated(self.needleLayer, 'mining_check/needle_hot.png')
        self.needleHot.Hide()
        self.burstLayer = Layer(self)
        self.burst = Rotated(self.burstLayer, 'mining_check/burst.png', additive=True)
        self.layers = [self.coreLayer, self.ringLayer, self.goodLayer, self.greatLayer, self.flashLayer,
                       self.needleLayer, self.burstLayer]
        self.sparkLayer = Layer(self, 0, 0, W, H)
        self.sparks = [Rotated(self.sparkLayer, 'mining_check/spark.png', A.SPARK, additive=True) for unused in range(8)]
        self.chips = [Rotated(self.sparkLayer, 'mining_check/chip_%d.png' % (1 + index % 3), A.CHIP)
                      for index in range(6)]
        self.flare = Rotated(self.sparkLayer, 'mining_check/flare.png', A.FLARE, additive=True)
        for image in self.sparks + self.chips + [self.flare]:
            image.Hide()
        self.headline = uir1.Text(self, '', W // 2, HEAD_Y, kit.font('button'), T.IVORY, align='center',
                                  valign='top', outline=True)
        self.line = uir1.Text(self, '', W // 2, LINE_Y, kit.font('text_s'), T.INK_DIM, align='center', valign='top',
                              outline=True)
        self.pips = []
        for unused in range(5):
            pip = ui.ExpandedImageBox()
            pip.SetParent(self)
            pip.AddFlag('not_pick')
            pip.LoadImage(A.ROOT + 'mining_check/pip.png')
            self.pips.append(pip)
        self.pad = MiningCheckPad(ui.__mem_func__(self.Hit))
        self.pad.Hide()
        self.Hide()

    # ------------------------------------------------------------------ geometry
    def Centre(self):
        """The rotation centre in window coordinates (the middle of the ring)."""
        return CX, CY

    @staticmethod
    def Screen():
        try:
            import wndMgr
            return wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        except Exception:
            return 1024, 768

    def Project(self, height):
        if self.project is not None:
            return self.project(height)
        import chr
        import player
        return chr.GetProjectPosition(player.GetMainCharacterIndex(), int(height))

    def Target(self):
        """The ring centre wanted now: beside the character, else the fallback above the quick slots; kept so the
        whole window stays on the screen and off the bottom HUD."""
        sw, sh = self.Screen()
        centre = None
        try:
            centre = M.Anchor(self.Project(M.HEAD_HEIGHT), self.Project(0), (sw, sh))
        except Exception:
            centre = None
        if centre is None:
            centre = ((sw - W) // 2 + CX, sh - BOTTOM_GAP - H + CY)
        x = max(CX + MARGIN, min(sw - (W - CX) - MARGIN, centre[0]))
        y = max(CY + MARGIN, min(sh - HUD_BOTTOM - (H - CY), centre[1]))
        return x, y

    def Follow(self, now, snap=False):
        target = self.Target()
        dt = 0.0 if self.followed_at is None else now - self.followed_at
        self.followed_at = now
        self.anchor = target if snap else M.Follow(self.anchor, target, dt)
        x, y = int(round(self.anchor[0] - CX)), int(round(self.anchor[1] - CY))
        self.SetPosition(x, y)
        self.pad.SetPosition(x + PAD_X, y + PAD_Y)

    def Place(self):
        self.Follow(self.Now(), snap=True)

    def Zone(self, pool, layer, name, width):
        centres = M.Wedges(self.check.zone_center, width, A.WEDGE_STEP)
        while len(pool) < len(centres):
            pool.append(Rotated(layer, name))
        for index, image in enumerate(pool):
            if index < len(centres):
                Turn(image, centres[index])
                image.Show()
            else:
                image.Hide()

    def SetNeedle(self, angle, hot=False, trail=True):
        self.angle = angle
        for image in (self.needle, self.needleHot, self.trail):
            Turn(image, angle)
        if hot:
            self.needle.Hide()
            self.needleHot.Show()
        else:
            self.needleHot.Hide()
            self.needle.Show()
        if trail:
            self.trail.Show()
        else:
            self.trail.Hide()

    def Now(self):
        if self.clock is not None:
            return float(self.clock())
        return time.perf_counter()

    def Sound(self, key):
        for path in SOUNDS.get(key, ()):
            try:
                if self.play is not None:
                    self.play(path)
                else:
                    import snd
                    snd.PlaySound(path)
            except Exception:
                pass

    def Begin(self, check, now=None):
        """Shows a ring. A ring that is still shown (turning, waiting for its answer or showing its result; variant C
        sends one every 2 swings) is replaced completely: the old result text goes, the needle starts at the top and
        a late answer of the old id is ignored."""
        now = self.Now() if now is None else now
        self.check = check
        self.result = None
        self.state = RUNNING
        self.resolved = False
        self.hit_ms = self.hit_at = self.result_at = None
        self.begun_at = now
        self.shown_at = self.prev_draw = self.last_draw = None
        self.until = 0.0
        self.deadline = now + check.timeout_ms / 1000.0
        self.rings += 1
        self.Zone(self.good, self.goodLayer, 'mining_check/good.png', check.good_deg)
        self.Zone(self.great, self.greatLayer, 'mining_check/great.png', check.great_deg)
        half = check.great_deg / 2.0
        Turn(self.ticks[0], check.zone_center - half)
        Turn(self.ticks[1], check.zone_center + half)
        Turn(self.flash, check.zone_center)
        self.SetNeedle(0.0, check.Zone(0) != M.MISS)
        self.headline.SetText('')
        self.headline.SetPosition(W // 2, HEAD_Y)
        self.line.SetText(Hint() if self.rings <= HINT_RINGS else '')
        self.line.SetPosition(W // 2, LINE_Y)
        TextColor(self.line, T.INK_DIM, 1.0, outline=True)
        for pip in self.pips:
            pip.Hide()
        self.Draw(now, first=False)
        self.Sound('appear')
        if not self.IsShow():
            self.Follow(now, snap=True)
            self.Show()
            self.SetTop()
        self.pad.Show()
        self.pad.SetTop()

    def Hit(self, now=None):
        """The click / the key: sends "/mcheck hit <id> <elapsed_ms>" once. False when there is nothing to hit.
        elapsed_ms counts to the frame the player saw at the press (miningcheckmodel.SeenTime)."""
        if self.state != RUNNING or self.check is None:
            return False
        now = self.Now() if now is None else now
        if now > self.deadline:
            return False
        shown = self.shown_at if self.shown_at is not None else self.begun_at
        seen = M.SeenTime(now, self.prev_draw, self.last_draw)
        self.hit_ms = M.ElapsedMs(shown, seen)
        self.hit_at = now
        self.state = SENT
        self.until = max(self.deadline, now + RESULT_WAIT)
        self.pad.Hide()                         # the next click goes to the world again
        self.SetNeedle(self.check.Angle(self.hit_ms), self.check.Zone(self.hit_ms) != M.MISS, trail=False)
        if self.send is not None:
            self.send(M.COMMAND_HIT % (self.check.id, self.hit_ms))
        else:
            import net
            net.SendChatPacket(M.COMMAND_HIT % (self.check.id, self.hit_ms))
        return True

    def ShowResult(self, result, now=None):
        """The server's answer for the shown check (also after a timeout hid it); another id is ignored."""
        if self.check is None or result.id != self.check.id or self.resolved:
            return False
        now = self.Now() if now is None else now
        self.resolved = True
        if result.result == M.TIMEOUT:
            # The server closes a check without a real result the same way as its timeout (a mode change, a new
            # B check replacing this one, A cancelled by walking away or clicking the vein again): a quiet close.
            self.Stop()
            return True
        self.state = RESULT
        self.result = result.result
        self.result_at = now
        self.until = now + M.RESULT_SECONDS
        self.pad.Hide()
        self.streak = self.streak + 1 if result.result == M.GREAT else 0
        headline, detail = M.ResultTexts(result.result, result.swings_saved, self.check.mode)
        self.headline.SetText(headline)
        self.line.SetText(detail)
        pips = M.Pips(self.streak) if result.result == M.GREAT else 0
        x = W // 2 - (pips * 11 - 2) // 2
        for index, pip in enumerate(self.pips):
            if index < pips:
                pip.SetPosition(x + index * 11, PIPS_Y)
                pip.Show()
            else:
                pip.Hide()
        self.Sound('streak' if pips else result.result)
        if not self.IsShow():
            self.Follow(now, snap=True)
            self.Show()
            self.SetTop()
        self.Draw(now, first=False)
        return True

    def Stop(self, invalidate=False):
        if invalidate:
            self.check = None
            self.resolved = True
        if self.state == RUNNING:
            self.streak = 0                     # a ring left to run out breaks a series
        self.state = IDLE
        self.pad.Hide()
        self.Hide()

    # ------------------------------------------------------------------ frames
    def OnUpdate(self):
        if self.state == IDLE:
            return
        self.Tick(self.Now())

    def Tick(self, now):
        """At most 60 Hz (the UI update): the end of the states and the place beside the character."""
        if self.state == RUNNING and now >= self.deadline:
            self.Stop()
            return
        if self.state in (SENT, RESULT) and now >= self.until:
            self.Stop()
            return
        self.Follow(now)

    def OnRender(self):
        if self.state == IDLE:
            return
        self.Draw(self.Now())

    def Draw(self, now, first=True):
        """Every rendered frame: the needle at the time of this frame and the animations. ``first`` = a real
        frame (Begin and ShowResult draw once at once without counting a frame)."""
        if first:
            if self.shown_at is None:
                self.shown_at = now
            self.prev_draw, self.last_draw = self.last_draw, now
        shown = self.shown_at if self.shown_at is not None else now
        scale, alpha = M.Appear(now - shown)
        grey, dx = 1.0, 0
        flash = burst_alpha = 0.0
        burst_scale = 1.0
        sparks = chips = flare = None
        text_alpha, rise = 1.0, 0
        if self.state == RUNNING:
            elapsed = M.ElapsedMs(shown, now)
            self.SetNeedle(self.check.Angle(elapsed), self.check.Zone(elapsed) != M.MISS)
        elif self.state == SENT and self.hit_at is not None:
            scale *= M.Press(now - self.hit_at)
        elif self.state == RESULT:
            look = M.Feedback(self.result, now - self.result_at)
            scale *= look.scale
            alpha *= look.ring_alpha
            grey, dx = look.grey, look.shake
            flash, burst_scale, burst_alpha, sparks = look.flash, look.burst_scale, look.burst_alpha, look.sparks
            chips, flare = look.chips, look.flare
            text_alpha, rise = look.text_alpha, look.text_rise
        for layer in self.layers:
            layer.SetPosition(layer.home[0] + dx, layer.home[1])
        for image in [self.core, self.ring, self.needle, self.needleHot] + self.good + self.great + self.ticks:
            Scale(image, scale)
            Paint(image, grey, alpha)
        Scale(self.trail, scale)
        Paint(self.trail, 1.0, alpha)
        Scale(self.flash, scale)
        Paint(self.flash, 1.0, flash)
        if burst_alpha > 0.0:
            Scale(self.burst, burst_scale)
            Paint(self.burst, 1.0, burst_alpha)
            self.burst.Show()
        else:
            self.burst.Hide()
        self.DrawSparks(sparks)
        self.DrawChips(chips)
        self.DrawFlare(flare)
        result = self.result if self.state == RESULT else None
        if result is not None:
            self.headline.SetPosition(W // 2, HEAD_Y + rise)
            self.line.SetPosition(W // 2, LINE_Y + rise)
            TextColor(self.headline, HEADLINE.get(result, T.MUTED), text_alpha, outline=True)
            TextColor(self.line, DETAIL.get(result, T.MUTED), text_alpha, outline=True)
            for pip in self.pips:
                Paint(pip, 1.0, text_alpha)

    def DrawSparks(self, progress):
        if progress is None or self.check is None:
            for spark in self.sparks:
                spark.Hide()
            return
        k = M.EaseOut(progress)
        for spark, (angle, travel, length) in zip(self.sparks, M.Sparks(self.check.id, self.angle)):
            x, y = M.Polar(CX, CY, A.TRACK_R + 3.0 * A.SCALE + travel * A.SCALE * k, angle)
            spark.SetPosition(int(round(x - A.SPARK / 2.0)), int(round(y - A.SPARK / 2.0)))
            Turn(spark, angle)
            Scale(spark, length * (1.0 - 0.4 * progress))
            Paint(spark, 1.0, 1.0 - progress)
            spark.Show()

    def DrawChips(self, progress):
        """Stone chips out of the struck point: thrown out and up, falling, turning; kept inside the window."""
        if progress is None or self.check is None:
            for chip in self.chips:
                chip.Hide()
            return
        t = progress * M.CHIP_LIFE
        x0, y0 = M.Polar(CX, CY, A.TRACK_R + 2.0, self.angle)
        fade = 1.0 - M.Clamp01((t - 0.18) / (M.CHIP_LIFE - 0.18))
        half = A.CHIP / 2.0
        for chip, data in zip(self.chips, M.Chips(self.check.id, self.angle)):
            dx, dy, turn = M.ChipAt(data, t)
            dx, dy = dx * A.SCALE, dy * A.SCALE
            x = max(half + 1.0, min(W - half - 1.0, x0 + dx))
            y = max(half + 1.0, min(H - half - 1.0, y0 + dy))
            chip.SetPosition(int(round(x - half)), int(round(y - half)))
            Turn(chip, turn)
            Scale(chip, data[4] * (1.0 - 0.3 * progress))
            Paint(chip, 1.0, fade)
            chip.Show()

    def DrawFlare(self, flare):
        """The white-hot star where the pickaxe struck: on the track at the struck angle, popping and fading."""
        if flare is None:
            self.flare.Hide()
            return
        scale, alpha = flare
        x, y = M.Polar(CX, CY, A.TRACK_R, self.angle)
        self.flare.SetPosition(int(round(x - A.FLARE / 2.0)), int(round(y - A.FLARE / 2.0)))
        Turn(self.flare, self.angle)
        Scale(self.flare, scale)
        Paint(self.flare, 1.0, alpha)
        self.flare.Show()

    def Destroy(self):
        self.state = IDLE
        self.Hide()
        self.check = None
        self.send = None
        self.play = None
        self.project = None
        if getattr(self, 'pad', None) is not None:
            self.pad.Hide()
            self.pad.hit = None


def CreateWindow(clock=None, send=None, play=None, project=None):
    window = MiningCheckWindow(clock, send, play, project)
    window.Build()
    return window


# --------------------------------------------------------------------------- the session controller
class MiningCheck(object):
    """The mode of the character (store + server sync), the check window and the hit."""

    def __init__(self, store=None, send=None, clock=None, identity=None, play=None, project=None):
        self.store = store or M.ModeStore()
        self._send = send
        self._clock = clock
        self._identity = identity
        self._play = play
        self._project = project
        self.confirmed = None           # the last MiningCheckModeV1 of this character
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
        """The craft book switch: sent at once, then stored for this character. The send never depends on the
        store: a failed or raising UserData write (a missing folder, a read-only file, an embedded os module) only
        loses the local copy, the server still gets the mode (it keeps it in its quest flag anyway)."""
        if isinstance(mode, bool) or mode not in (M.MODE_OFF, M.MODE_C):
            return False
        self.store.mode = mode
        self.store.explicit = True
        self.attempts = 0
        self.SendMode()
        try:
            self.store.Set(mode)
        except Exception:
            pass
        return True

    def ModeLabels(self):
        """[(mode, label)] of the craft book switch: Vypnuto | A - nápřah | B - další těžba | C - během kopání."""
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
            if M.Migrate(mode) != mode:             # the server still has A or B: switch it to C
                self.SetMode(M.Migrate(mode))
                return True
            if mode != self.store.mode:
                if not getattr(self.store, 'explicit', True):
                    self.store.mode = mode      # no own choice yet: show the server's word, keep the default
                    return True
                try:
                    self.store.Set(mode)        # the server's word (quest flag craft.mc_mode)
                except Exception:
                    self.store.mode = mode
            return True
        if command == M.CHECK:
            check = M.ParseCheck(args)
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

    def Hit(self):
        """The keybinding action: hits the shown check (nothing without one)."""
        if self.window is None:
            return False
        return self.window.Hit(self.Clock())

    def SpaceHit(self):
        """Space (game.OnKeyDown -> interface.MinigameSpaceHit): the hit instead of an attack. True (Space taken)
        while a ring turns or waits for its answer - a second press must not attack either, that would break the
        mining; False without a ring (Space attacks as usual)."""
        window = self.window
        if window is None or window.state not in (RUNNING, SENT) or not window.IsShow():
            return False
        window.Hit(self.Clock())
        return True

    def HideWindow(self):
        if self.window is not None:
            self.window.Stop(invalidate=True)

    def Destroy(self):
        if self.window is not None:
            self.window.Destroy()
        self.window = None
