# -*- coding: utf-8 -*-
"""The character select as a hall ("Síň hrdinů"): the account's real 3D characters stand in an arc on the
floor of a painted hall (painted layers, parallax), the selected one in the middle of the scene's light, the others a
little darker; the hall itself is the menu (HRÁT / VYTVOŘIT / SMAZAT / UKONČIT as generated button art with the
A8 caption baked in, names and levels on the floor), red lightning in the sky behind the gate, lanterns, mist and
embers. Python only - the EXE is unchanged.

* one full-screen 3D pass (our renderer window: grp.SetEyeCamera + grp.SetPerspective matching the plate's floor,
  chr.SetPixelPosition on the arc). The stock light rig (grp.SetOmniLight) stays in the middle of the hall; the
  characters beyond its 5 m slide along their own view ray into it (same feet on the screen); the world is never
  scaled (the sash / acce ignores chr.SetScale). The selection only changes the modulate, never a position.
* every 2D layer is our own root anchored to the screen; 2D light sprites under / over the 3D pass.
* the R1 column of uir1pregame stays the fallback (a screen under 800 x 600 - MIN_SCREEN -, off=1, or any failure: Undo).

Interface for new_introselect / uir1pregame.Safe (like uir1pregame.SelectColumn): is_hall, Refresh, Select,
Step, SetEnabled, OpenDelete, CloseDelete, Destroy, Undo (+ the tuning keys of new_introselect.HALL_DEV_KEYS).
Switches in the client folder, file "pregame-hall.cfg" (key=value per line, all optional): every key of CFG below;
without the file the defaults are the released look. devkeys=1 turns the tuning keys on (H / F4-F11).
"""
import math
import random

import app
import chr
import grp
import ui
import wndMgr

import uir1
import uir1tokens as T
import uir1pregame as P

try:
    import effect
except ImportError:         # an engine without the effect module: the 2D flames
    effect = None

ASSET = 'd:/ymir work/ui/pregame_proto/'
PLATE = ASSET + 'hall_1920.png'
LAYER_DIR = ASSET + 'vrstvy/'         # the painted layers (tools/pregame_proto_vrstvy.py), optional
PLATE_W, PLATE_H = 1920, 1080
VANISH_Y = 490.0                      # the horizon of the plate (tile joints meet at (960, 490))
# feet of the 5 arc places, left to right, in plate px (R1: the bottom panel starts at y 765)
ARC = ((318.0, 615.0), (592.0, 652.0), (960.0, 720.0), (1328.0, 652.0), (1602.0, 615.0))
ARC_OF_SLOT = (2, 1, 3, 0, 4)         # display slot (0 = played last) -> arc place: the latest in the middle
# braziers: (bowl centre x, rim y, feet y) in plate px; each fire a little different
BRAZIERS = ((765.0, 510.0, 668.0), (1156.0, 510.0, 668.0))  # vrstvy-v2 L3 (scaled 1920x1080), measured 10. 10.
# the brazier fire (owner 10. 10.): fire_camp1.mse - a red column of fire dust and sparks rising from its origin (z 0
# up to ~200). It is big (particle size 300-550), so it sits on the ray through the bowl rim FARTHER than the brazier
# (apparent scale < 1: same screen point, smaller). Each brazier its own scale and start (never in sync).
FIRE_FX = 'd:/ymir work/effect/background/fire_camp1.mse'
FIRE_FX_BASE = 0.0
FIRE_SCALE = (0.55, 0.63)             # apparent scale per brazier (pregame-hall.cfg campscale multiplies both)
FIRE_DELAY = (0.0, 0.85)              # s after the hall opens
# the flame core in the bowl: the charcoal brazier flame (70-81 above its origin), 1.6x nearer = 1.6x bigger
CORE_FX = 'd:/ymir work/effect/background/fire_general_obj_charcoal.mse'
CORE_FX_BASE = 70.0
CORE_SCALE = (1.6, 1.45)
# the warm glow + sparks of the bone lantern (research efekty-ohen/RESERSE.md #4), off by default (bonelight=1)
GLOW_FX = 'd:/ymir work/effect/background/fire_ob-11-05-bonelight_01.mse'
GLOW_FX_BASE = 285.0
PORTAL = (805.0, 55.0, 1115.0, 590.0)
FADE = 0.3                            # selection crossfade, s
RED = (0.827, 0.051, 0.055)           # #D30D0E
WARM = (1.0, 0.72, 0.46)

# ---------------------------------------------------------------- v3 layer sets (owner 10. 10. evening: 'a', 'd')
# Layer sources use crop (0, 80, 1536, 944) -> 1920 x 1080, split
# by tools/pregame_proto_vrstvy.py sada into vrstvy-a/ | vrstvy-d/. Same composition, measured on both:
V3_VANISH_Y = 589.0                   # tile joints meet at (960, 586-590): Hough on a + d, 10. 10.; rows 831/876/941/1044
                                      # are equal steps in 1/(y - 589) and the tiles come out square with fov 36
V3_HORIZON = 688.0                    # floor / wall line (pillar bases reach 700-724)
# feet: clear of the niche bases (702) and of the panel (top 792 at 1080), the shadow visible under each
V3_ARC = ((318.0, 724.0), (592.0, 746.0), (960.0, 770.0), (1328.0, 746.0), (1602.0, 724.0))
V3_LANTERNS = ((295.0, 149.0), (1623.0, 149.0))           # flame centres
V3_ARCH = (770.0, 1150.0, 250.0, 6.0)                     # opening: inner left x, inner right x, spring y, crown y
# name -> (x, y, w, h) in plate px (the image may be smaller: res); = tools/pregame_proto_vrstvy.py LAYOUT
SET_LAYOUT = {
    'L0': (0, 0, 1920, 1080), 'P': (740, 0, 440, 700), 'L2': (0, 660, 1920, 420),
    'L4L': (0, 0, 200, 1080), 'L4R': (1720, 0, 200, 1080),
    'M_lamp_L': (40, 0, 520, 760), 'M_lamp_R': (1360, 0, 520, 760),
    'R_lamp_L': (100, 680, 400, 400), 'R_lamp_R': (1420, 680, 400, 400), 'R_portal': (560, 680, 800, 400),
    'G_rim': (700, 0, 520, 720), 'S_L': (0, 0, 960, 800), 'S_R': (960, 0, 960, 800),
}
SETS = {
    # mist tint left / right half, the shaft layers (d only)
    'a': {'dir': ASSET + 'vrstvy-a/', 'mist': ((0.70, 0.42, 0.40), (0.70, 0.42, 0.40)), 'shafts': False},
    'd': {'dir': ASSET + 'vrstvy-d/', 'mist': ((0.95, 0.74, 0.52), (0.62, 0.72, 0.92)), 'shafts': True},
}


CFG = {
    'off': 0, 'debug': 0,
    # camera / characters
    'fov': 36.0, 'camh': 100.0, 'body': 185.0, 'dim': 0.62, 'warm': 0.10,
    # fires (fire_camp1 + charcoal core; 'sprite' = the 2D flames)
    'fire': 'off', 'core': 1, 'campscale': 1.0, 'bonelight': 0,
    # background: layers=1 uses vrstvy/ when the pack has them (0 = always the single plate)
    'layers': 1, 'zoom': 1.03,
    # parallax: mouse sway in px (at the characters' floor), follow = how far the camera leans to the selection,
    # ease = s to settle, l4depth = depth of the foreground pillars (cm); parallax=0 switches all of it off
    'parallax': 1, 'sway': 6.0, 'follow': 0.03, 'ease': 0.6, 'l4depth': 450.0,
    # light and atmosphere strengths (0 = off)
    'firelight': 0.35, 'glow': 0.30, 'spill': 0.20, 'reflect': 0.22, 'portalreflect': 0.16, 'haze': 0.12,
    'fog': 0.08, 'dust': 0.55, 'sparks': 0.9, 'smoke': 0.22, 'shadowsway': 4.0,
    # experimental: faint upside-down character copies as floor reflections (2x the models, off by default)
    'reflectchars': 0, 'reflectalpha': 0.12,
    # whole-model warm tint of the characters from the braziers' flicker (not directional)
    'chartint': 0.08,
    # owner 10. 10.: layer switches (L3 bowls off until new art) and a neutral fill light on every character
    'l1': 1, 'l3': 0, 'l4': 1, 'fill': 0.22,
    # v3 (10. 10. evening): the layer set a | d (v2 = the vrstvy/), camera height and max layer shift (px)
    'set': 'a', 'camh3': 85.0, 'l4depth3': 520.0, 'maxshift': 8.0,
    # characters: 'stock' = every character in its own pass under the stock select light (grp.SetOmniLight at the
    # character, like new_introselect) + modulate (selected sel, the others dim3); 'add' = the old fill add mode
    'charlight': 'stock', 'sel': 1.0, 'dim3': 0.85, 'otherfill': 0.05, 'lampfill': 0.0, 'gatefill': 0.06,
    # the unselected: 'mod' = the stock light a little darker (dim3), 'add' = the flat fill, 'normal' (F4 cycles)
    'othermode': 'mod', 'chartint3': '1.0,0.84,0.80',
    # the outer ones dimmer (dimouter). NEVER a pass per character: the engine moves a model only in chr.Update,
    # and every extra chr.Update a frame plays the animations that much faster (owner 11. 10.: "4x rychlejší").
    # Instead the ones beyond the rig's 5 m slide along their own view ray towards the camera until they are
    # inside it (lightreach cm from the point light): the same feet on the screen, a little bigger (<= slidemax)
    'dimouter': 0.85, 'lightreach': 455.0, 'slidemax': 1.17,
    # the row moved towards the camera under the rig's point light (cm; F6 cycles 0 / 150 / 200), owner to choose
    'rigshift': 150,
    # the tuning keys of the select window (new_introselect.HALL_DEV_KEYS): off in the distributed client
    'devkeys': 0,
    # the banners' "A": breathing, hot under the mouse (a light band, sparks), a flash on a click (0 = off)
    'emblems': 1,
    # the character creation in the hall too (0 = the R1 creation column over the old background)
    'create': 1,
    # where the light rig stands: 'hall' = the middle place for good (positions never depend on the selection),
    # 'selected' = on the selected one (the old way: a corner selection slid the others far and big)
    'lightcentre': 'hall',
    # v3 interactive scene (0 = off): lanterns, mist, portal, banners, shafts (set d)
    'hover': 1, 'lampglow': 0.40, 'lampspill': 0.20, 'lampreflect': 0.30, 'lampflare': 1.0,
    'mist': 0.16, 'mistpuffs': 16, 'mistpart': 1.0,
    'rim': 0.22, 'embers': 12, 'embersmax': 30, 'swirl': 0.12,
    'shafts': 0.5, 'shaftbreath': 0.25,
    # v3 round 2 (owner 10. 10. late): camera breathing (px at L4), the portal's life, the character light scale
    'breath': 1.4, 'pulse': 1.0, 'bursts': 1, 'rays': 0.07, 'shimmer': 0.16, 'portalfog': 0.12, 'lightscale': 1.0,
    'portaltint': 0.04,
    # owner 10. 10. night: 'H' / F10 hides the whole UI (ui=off from the start); grounding of the characters:
    # contact shadow strength and a dark mirror streak on the glossy floor under each one
    'ui': 'on', 'contact': 0.9, 'charmirror': 0.28,
    # v4 (owner 10. 10. night, set a): the portal - ember streaks + curl, ash, crackle along the arch, a threshold
    # glow; the places - a dormant rune ring + dais under everyone, the selected: lit ring, glow, ripple, motes
    'streaks': 0.5, 'curl': 1.0, 'ash': 0.45, 'crackle': 0.8, 'threshold': 0.14,
    'runebase': 0.22, 'dais': 0.35, 'runeglow': 0.35, 'ripple': 0.45, 'motes': 0.7,
    # detail D (owner 10. 10. night): the nameplate over the head + one info line under the ring; a faint one on
    # hover over another character; backplate = the strength of the soft dark plate under the text
    'nameplate': 1, 'backplate': 0.6, 'hoverplate': 0.55, 'detail': 'dp',
    # owner 10. 10. night: the floor text without the dark band (outline + shadow only), red / white dots
    'textband': 0, 'dotcolor': 'red', 'textarc': 0,
    # owner 11. 10.: the v4 rune circles under the characters ("vrať ten červený kruh"), together with the new
    # breathing light under the selected one; runecircle=0 = only the contact shadow + that light
    'runecircle': 1,
    # the generated button set of HRÁT / VYTVOŘIT / SMAZAT / UKONČIT: obsidian | kamen | cepel | ram
    'buttons': 'obsidian',
    # the music of the select and the creation (owner 11. 10., Suno; root/pregamemusic.py): shuffle (a random track,
    # at its end the next random one) | random (one per client start, looped) | a track's key; F8 steps for now
    'music': 'shuffle',
    # the button layout (F7 cycles): a = HRÁT bottom centre, b = a column bottom right, c = HRÁT right + two left
    'btnlayout': 'a',
    # the dragon eyes: glow, hover arcs and click bolts (owner 11. 10.: off - the eyes as in the art)
    'eyefx': 0,
    # the click effect of the buttons (HRÁT: vein flash, red wave, sparks; the small ones: a soft pulse)
    'btnfx': 'crack',
    # red lightning in the sky behind the gate (every 6-15 s, sometimes twice)
    'lightning': 1, 'lightningrate': 1.0, 'lightningpower': 1.0,
    # the bolt look (Lightning): widths glow,middle,core (px at 1080), strengths, roughness main,branches
    'boltw': '28,7,3', 'bolta': '0.7,0.85,1.5', 'boltrough': '0.06,0.09,0.12,0.13,0.11,0.08',
    'boltbranchrough': '0.12,0.16,0.16,0.12',
    # every character this many cm nearer the camera (rings, light, names and the floor text go along)
    'charforward': 100.0,
    # BDO-like (owner + brother 10. 10. night): the camera eases in (zoom + a small turn) on the selection;
    # selectpose=1: the selected plays the stock intro pose (selected.msa), the one it replaces not_selected.msa.
    # Off (owner 13. 10., testers: a click / an arrow looked like logging in and players waited): a selection only
    # moves the light; the pose plays on HRÁT / Enter / a double-click (new_introselect.StartGameButton)
    'camfocus': 0, 'camzoom': 1.12, 'camcenter': 0.5, 'camease': 0.6, 'selectpose': 0,
}


# the smallest window the hall lays itself out for (DEV 11. 10., Boban: "na nižším rozlišení se nenačítá" - it
# was 1280 x 720 and a smaller window fell back to the old column); below it the R1 column
MIN_SCREEN = (800, 600)
# owner 11. 10. ("na malém okně je menu špatně čitelné"): plates and buttons never under this share of their size
# at the screen (texts: Tahoma never under 12 px, uir1pregame.Geo.noto); a short screen moves the menu up instead
READABLE = 0.85


def Config():
    cfg = dict(CFG)
    try:
        stream = open('pregame-hall.cfg', 'r')
        try:
            for line in stream.read(8192).splitlines():
                if '=' not in line or line.strip().startswith('#'):
                    continue
                key, value = [part.strip() for part in line.split('=', 1)]
                if key not in cfg:
                    continue
                try:
                    cfg[key] = value if isinstance(cfg[key], str) else type(cfg[key])(float(value))
                except ValueError:
                    pass
        finally:
            stream.close()
    except IOError:
        pass
    if cfg.get('set') in SETS:
        cfg['fire'] = 'off'         # the v3 halls have no braziers (their light = the lanterns, Ambience)
    if cfg.get('fire') == 'off':
        # no braziers (owner 10. 10.): nothing may glow, spark, smoke or reflect where they were
        for key in ('firelight', 'glow', 'spill', 'reflect', 'sparks', 'smoke', 'chartint', 'shadowsway'):
            cfg[key] = 0
    return cfg


def Tint(cfg):
    """The characters' light colour (modulate): the hall's red, never yellow (owner 11. 10.)."""
    try:
        r, g, b = [float(v) for v in str(cfg.get('chartint3', '1.0,0.84,0.80')).split(',')]
        return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))
    except ValueError:
        return 1.0, 1.0, 1.0


def ScreenOrigin(board):
    """The local position that puts a child of ``board`` at the screen's top left (0, 0)."""
    try:
        bx, by = board.GetGlobalPosition()
        return -int(bx), -int(by)
    except Exception:
        return 0, 0


def Exists(path):
    """Is ``path`` in the packs (pack.Exist, else app.IsExistFile)?"""
    try:
        import pack
        return bool(pack.Exist(path))
    except Exception:
        pass
    try:
        return bool(app.IsExistFile(path))
    except Exception:
        return False


def Smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def _hash(i, seed):
    n = (int(i) * 374761393 + int(seed) * 668265263) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def _vnoise(x, seed):
    i = math.floor(x)
    f = x - i
    f = f * f * (3.0 - 2.0 * f)
    return _hash(i, seed) * (1.0 - f) + _hash(i + 1, seed) * f


def Flicker(t, seed):
    """An irregular fire flicker around 1.0: value noise in three octaves (fast flutter, medium, slow wander) plus
    rare short dips - no visible sine period; every seed differs."""
    fast = _vnoise(t * 13.0, seed * 7 + 1) - 0.5
    mid = _vnoise(t * 4.3, seed * 7 + 2) - 0.5
    slow = _vnoise(t * 0.9, seed * 7 + 3) - 0.5
    dip = _vnoise(t * 2.1, seed * 7 + 4)
    dip = -0.18 * max(0.0, dip - 0.82) / 0.18
    return 1.0 + 0.16 * fast + 0.14 * mid + 0.10 * slow + dip


def FireBounce(point, fires, now, strength):
    """Approximate whole-model warmth, not a normal-based point light.
    Uses the same noise as the brazier sprites and world-space distance.
    """
    strength = max(0.0, min(0.18, float(strength)))
    total = 0.0
    for index, (ground, height) in enumerate(fires):
        dx, dy, dz = point[0]-ground[0], point[1]-ground[1], point[2]-height
        attenuation = 1.0 / (1.0 + (dx*dx + dy*dy + dz*dz) / (260.0*260.0))
        total += strength * Flicker(now, index + 1) * attenuation
    return min(0.16, total)


def uikit_color(packed, alpha):
    """grp colour of a packed RGB + alpha (uikit.GenerateColor without importing it at module load)."""
    try:
        import uikit
        return uikit.GenerateColor(packed, alpha)
    except Exception:
        return grp.GenerateColor(((packed >> 16) & 255) / 255.0, ((packed >> 8) & 255) / 255.0, (packed & 255) / 255.0,
                                 alpha)


def SetColor(image, rgb, alpha):
    wndMgr.SetDiffuseColor(image.hWnd, float(rgb[0]), float(rgb[1]), float(rgb[2]), max(0.0, min(1.0, float(alpha))))


# =========================================================================== camera
def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _add(a, b, k=1.0):
    return (a[0] + b[0] * k, a[1] + b[1] * k, a[2] + b[2] * k)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _scale(a, k):
    return (a[0] * k, a[1] * k, a[2] * k)


def _norm(a):
    n = math.sqrt(_dot(a, a)) or 1.0
    return (a[0] / n, a[1] / n, a[2] / n)


class Camera(object):
    """The scene camera and its exact projection (D3DXMatrixLookAtRH + D3DXMatrixPerspectiveFovRH), so 2D layers and
    the 3D pass agree. Screen = the full window; the plate is 'cover' scaled onto it (like introbackground)."""

    def __init__(self, width, height, fov, height_cm, facing, zoom=1.0, vanish_y=VANISH_Y):
        self.W, self.H = float(width), float(height)
        self.vanish = float(vanish_y)
        # the plate is cover-scaled, then zoomed about its vanishing point (a margin for the parallax shift; the
        # floor perspective stays the plate's: the camera is solved on the zoomed plate)
        self.zoom = float(zoom)
        cover = max(self.W / PLATE_W, self.H / PLATE_H)
        cx, cy = (self.W - PLATE_W * cover) / 2.0, (self.H - PLATE_H * cover) / 2.0
        vx, vy = cx + PLATE_W / 2.0 * cover, cy + self.vanish * cover
        self.scale = cover * self.zoom
        self.ox = vx - PLATE_W / 2.0 * self.scale
        self.oy = vy - self.vanish * self.scale
        self.fov = float(fov)
        self.aspect = self.W / self.H
        self.ys = 1.0 / math.tan(math.radians(self.fov) / 2.0)
        self.xs = self.ys / self.aspect
        # facing = horizontal unit vector from a character towards the camera (python rotation 0 faces it)
        back = _norm((facing[0], facing[1], 0.0))
        horizon = self.oy + self.vanish * self.scale
        tilt = math.atan((self.H / 2.0 - horizon) / (self.ys * self.H / 2.0))
        self.eye = (0.0, 0.0, float(height_cm))
        forward = (-back[0] * math.cos(tilt), -back[1] * math.cos(tilt), -math.sin(tilt))
        self.at = _add(self.eye, forward, 1000.0)
        self.up = (0.0, 0.0, 1.0)
        self.z = _norm(_sub(self.eye, self.at))
        self.x = _norm(_cross(self.up, self.z))
        self.y = _cross(self.z, self.x)
        self.back = back
        self.eye0, self.at0 = self.eye, self.at
        self.x0, self.y0, self.z0 = self.x, self.y, self.z
        self.forward = forward
        self.F = self.ys * self.H / 2.0
        self.offset = (0.0, 0.0)
        self.pivot = None           # v3: the eye orbits a point this far ahead (the back wall stays still)
        # focus (owner 10. 10. night, like BDO): a zoom (narrower lens) + a small turn towards the selection. 2D
        # layers follow it as a similarity about the screen centre, fitted so the selected one's body agrees
        self.scale0, self.xs0, self.ys0, self.F0 = self.scale, self.xs, self.ys, self.F
        self.bx, self.by, self.bz = self.x, self.y, self.z     # the axes before the focus turn
        self.zf, self.yaw, self.pitch, self.anchor = 1.0, 0.0, 0.0, None
        self.t = (0.0, 0.0)
        self.fovEff = self.fov

    def SetOffset(self, dx, dz):
        """Moves the eye (and its target) dx along the screen's right and dz up, in cm: the parallax. The scene
        points stay where they are in the world, so the 3D characters, the fires and every projected sprite shift
        with their own depth."""
        self.offset = (float(dx), float(dz))
        move = _add(_add((0.0, 0.0, 0.0), self.x0, dx), self.up, dz)
        self.eye = _add(self.eye0, move)
        if self.pivot is None:
            self.at = _add(self.at0, move)
            self.x, self.y, self.z = self.x0, self.y0, self.z0
        else:
            # v3: look at the fixed pivot point (on the back wall): points at the pivot depth stay put, nearer ones
            # move with the eye, farther ones (the portal) a little against it
            self.at = _add(self.eye0, self.forward, self.pivot)
            self.z = _norm(_sub(self.eye, self.at))
            self.x = _norm(_cross(self.up, self.z))
            self.y = _cross(self.z, self.x)
        self.bx, self.by, self.bz = self.x, self.y, self.z
        self._ApplyFocus()

    def SetFocus(self, zf, yaw, pitch, anchor):
        """Zoom ``zf`` (1 = none) and a turn (yaw right, pitch up, radians) of the view; ``anchor`` = the world point
        the 2D layers are fitted on (the selected one's body)."""
        self.zf, self.yaw, self.pitch, self.anchor = float(zf), float(yaw), float(pitch), anchor
        self.SetOffset(*self.offset)

    def _ApplyFocus(self):
        zf = self.zf
        self.xs, self.ys, self.F = self.xs0 * zf, self.ys0 * zf, self.F0 * zf
        self.scale = self.scale0 * zf
        self.fovEff = math.degrees(2.0 * math.atan(math.tan(math.radians(self.fov) / 2.0) / zf))
        if self.yaw or self.pitch:
            fb = (-self.bz[0], -self.bz[1], -self.bz[2])
            cy, sy, cp, sp = math.cos(self.yaw), math.sin(self.yaw), math.cos(self.pitch), math.sin(self.pitch)
            f = _norm(_add(_add(_scale(fb, cy * cp), self.bx, sy * cp), self.by, sp))
            self.z = (-f[0], -f[1], -f[2])
            self.x = _norm(_cross(self.up, self.z))
            self.y = _cross(self.z, self.x)
            self.at = _add(self.eye, f, 1000.0)
        else:
            self.x, self.y, self.z = self.bx, self.by, self.bz
        self.t = (0.0, 0.0)
        if self.anchor is not None and (zf != 1.0 or self.yaw or self.pitch):
            a1, a0 = self.Project(self.anchor), self.ProjectBase(self.anchor)
            if a1 is not None and a0 is not None:
                cx, cy_ = self.W / 2.0, self.H / 2.0
                self.t = (a1[0] - (cx + zf * (a0[0] - cx)), a1[1] - (cy_ + zf * (a0[1] - cy_)))

    def ProjectBase(self, p):
        """The projection without the focus (zoom, turn): the frame the plate and its layers are drawn in."""
        v = _sub(p, self.eye)
        vx, vy, vz = _dot(v, self.bx), _dot(v, self.by), _dot(v, self.bz)
        if vz > -1.0:
            return None
        nx, ny = self.xs0 * vx / -vz, self.ys0 * vy / -vz
        return (nx + 1.0) * 0.5 * self.W, (1.0 - ny) * 0.5 * self.H

    def Map(self, sx, sy):
        """base screen px -> focused screen px (the similarity the 2D layers follow)"""
        cx, cy = self.W / 2.0, self.H / 2.0
        return cx + self.zf * (sx - cx) + self.t[0], cy + self.zf * (sy - cy) + self.t[1]

    def SetPivot(self, depth):
        self.pivot = float(depth) if depth else None
        self.SetOffset(*self.offset)

    def Shift(self, depth):
        """Screen shift (px) of a flat layer at ``depth`` cm for the current offset."""
        k = self.F / max(1.0, float(depth))
        if self.pivot is not None:
            k -= self.F / self.pivot
        return -self.offset[0] * k, self.offset[1] * k

    def Screen(self, px, py):
        """plate px -> screen px (with the focus)"""
        return self.Map(self.ox + px * self.scale0, self.oy + py * self.scale0)

    def ScreenBase(self, px, py):
        return self.ox + px * self.scale0, self.oy + py * self.scale0

    def Project(self, p):
        v = _sub(p, self.eye)
        vx, vy, vz = _dot(v, self.x), _dot(v, self.y), _dot(v, self.z)
        if vz > -1.0:
            return None
        nx, ny = self.xs * vx / -vz, self.ys * vy / -vz
        return (nx + 1.0) * 0.5 * self.W, (1.0 - ny) * 0.5 * self.H

    def Ray(self, sx, sy):
        nx, ny = sx / self.W * 2.0 - 1.0, 1.0 - sy / self.H * 2.0
        d = _add(_add(_add((0.0, 0.0, 0.0), self.x, nx / self.xs), self.y, ny / self.ys), self.z, -1.0)
        return _norm(d)

    def Floor(self, px, py):
        """The floor point (z 0) under plate px (px, py) - in the base frame (the plate's own camera)."""
        sx, sy = self.ScreenBase(px, py)
        nx, ny = sx / self.W * 2.0 - 1.0, 1.0 - sy / self.H * 2.0
        d = _norm(_add(_add(_add((0.0, 0.0, 0.0), self.x0, nx / self.xs0), self.y0, ny / self.ys0), self.z0, -1.0))
        if d[2] >= -1e-4:
            d = (d[0], d[1], -1e-4)
        return _add(self.eye0, d, -self.eye0[2] / d[2])

    def Lift(self, ground, px, py):
        """Height above ``ground`` whose projection lies on plate row py (bisection, at offset 0)."""
        keep = self.offset
        self.SetOffset(0.0, 0.0)
        try:
            return self._Lift(ground, px, py)
        finally:
            self.SetOffset(*keep)

    def _Lift(self, ground, px, py):
        target = self.ScreenBase(px, py)[1]
        lo, hi = 0.0, 2000.0
        for unused in range(40):
            mid = (lo + hi) / 2.0
            s = self.ProjectBase((ground[0], ground[1], mid))
            if s is None or s[1] < target:
                hi = mid
            else:
                lo = mid
        return (lo + hi) / 2.0

    def Depth(self, p):
        return -_dot(_sub(p, self.eye), self.z)

    def PixelsPerUnit(self, p):
        return self.ys * self.H / 2.0 / max(1.0, self.Depth(p))

    def Lateral(self, p):
        return _dot(_sub(p, self.eye), self.x)

    def Ellipse(self, centre, radius):
        """Screen centre, width, height of a floor circle."""
        c = self.Project(centre)
        l, r = self.Project(_add(centre, self.x, -radius)), self.Project(_add(centre, self.x, radius))
        f = self.Project(_add(centre, self.back, radius))
        b = self.Project(_add(centre, self.back, -radius))
        if None in (c, l, r, f, b):
            return None
        return c, abs(r[0] - l[0]), abs(f[1] - b[1])


# =========================================================================== 2D sprites
def GuildLook(guild_name):
    """The guild's nameplate look remembered from the game (root/guildcosmetic.py cache), or None."""
    try:
        import guildcosmetic
        return guildcosmetic.cached_look(guild_name)
    except Exception:
        return None


def _guild_colour(look, default):
    """The text colour of a guild look (packed 0xAARRGGBB like the T.* colours)."""
    return look[0] if look else default


class GuildPlate(object):
    """The guild nameplate plate of the game (icon/guild_cosmetic/<plate>_l/_m/_r.tga) behind the hall's guild line:
    the same three textures, scaled to the hall's line height, the middle stretched to the text."""

    def __init__(self, parent):
        self.parts = []
        for unused in range(3):
            image = ui.ExpandedImageBox()
            image.SetParent(parent)
            image.AddFlag('not_pick')
            image.Hide()
            self.parts.append(image)
        self.plate = None
        self.size = [(1, 1)] * 3

    def Place(self, look, cx, top, text_w, line_h, alpha):
        plate, pad = look[3], look[4]
        if not plate or alpha <= 0.01:
            return self.Hide()
        if plate != self.plate:
            import guildcosmetic
            self.plate = plate
            for image, part in zip(self.parts, ('_l', '_m', '_r')):
                image.LoadImage(guildcosmetic.PLATE_ROOT + plate + part + '.tga')
            self.size = [(max(1, image.GetWidth()), max(1, image.GetHeight())) for image in self.parts]
        k = max(1.0, float(line_h + 6) / self.size[0][1])          # the 18 px plate grown to the hall line
        lw, rw = self.size[0][0] * k, self.size[2][0] * k
        inner = text_w + 2 * pad * k
        x0 = cx - inner / 2.0 - lw
        y0 = top + line_h / 2.0 - self.size[0][1] * k / 2.0
        for image, (w, h), x, width in zip(self.parts, self.size, (x0, x0 + lw, x0 + lw + inner), (lw, inner, rw)):
            image.SetScale(width / float(w), k)
            image.SetPosition(int(round(x)), int(round(y0)))
            try:
                image.SetDiffuseColor(1.0, 1.0, 1.0, alpha)
            except Exception:
                pass
            image.Show()

    def Hide(self):
        for image in self.parts:
            image.Hide()


class Sprite(ui.ExpandedImageBox):
    """A tinted, scaled image placed by its centre in screen px; additive (light) or normal."""

    def __init__(self, parent, name, additive=False):
        ui.ExpandedImageBox.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.LoadImage(ASSET + name)
        self.iw, self.ih = max(1, self.GetWidth()), max(1, self.GetHeight())
        if additive:
            self.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
        try:
            self.SetLinearFiltering(True)
        except Exception:
            pass
        self.Show()

    def Place(self, cx, cy, w, h, rgb=(1.0, 1.0, 1.0), alpha=1.0):
        if w < 1 or h < 1 or alpha <= 0.003:
            self.Hide()
            return
        self.SetScale(float(w) / self.iw, float(h) / self.ih)
        self.SetPosition(int(cx - w / 2.0), int(cy - h / 2.0))
        SetColor(self, rgb, alpha)
        self.Show()

    def Pivot(self):
        """For PlaceRotated: the engine's rotated quad is centred on position + origin (origin 0 = the position)."""
        self.SetOrigin(0.0, 0.0)

    def PlaceAngled(self, cx, cy, w, h, angle, rgb=(1.0, 1.0, 1.0), alpha=1.0):
        """Centre at (cx, cy), turned ``angle`` degrees about it (Pivot() first)."""
        if w < 1 or h < 1 or alpha <= 0.003:
            self.Hide()
            return
        if abs(angle) < 0.01:
            angle = 0.01
        self.SetScale(float(w) / self.iw, float(h) / self.ih)
        self.SetRotation(angle)
        self.SetPosition(int(round(cx)), int(round(cy)))
        SetColor(self, rgb, alpha)
        self.Show()

    def PlaceRotated(self, ax, ay, w, h, angle, rgb=(1.0, 1.0, 1.0), alpha=1.0):
        """Top centre of the image at (ax, ay), turned ``angle`` degrees (clockwise on screen) about that point."""
        if w < 1 or h < 1 or alpha <= 0.003:
            self.Hide()
            return
        if abs(angle) < 0.01:
            angle = 0.01            # 0 takes the engine's unrotated path (position = top left)
        a = math.radians(angle)
        cx, cy = ax - h / 2.0 * math.sin(a), ay + h / 2.0 * math.cos(a)
        self.SetScale(float(w) / self.iw, float(h) / self.ih)
        self.SetRotation(angle)
        self.SetPosition(int(round(cx)), int(round(cy)))
        SetColor(self, rgb, alpha)
        self.Show()


class Renderer(ui.Window):
    """The full-screen 3D pass: every character + the effects (fires) with the hall camera."""

    def __init__(self, parent, hall):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(0, 0)
        self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.hall = hall
        self.Show()

    def OnRender(self):
        hall = self.hall
        if hall is None or hall.failed or hall.camera is None:
            return
        cam = hall.camera
        failed = False
        grp.ClearDepthBuffer()
        grp.SetGameRenderState()
        grp.PushState()
        try:
            grp.SetViewport(0.0, 0.0, 1.0, 1.0)
            (x, y) = app.GetCursorPosition()
            grp.SetCursorPosition(x, y)
            centre = None
            if self.StockPasses():
                centre = self.LightPasses(cam)
            else:
                self.SetCamera(cam.eye, cam.at)
                chr.Deform()
                chr.Render()
            if centre is not None:
                # the effects attached to the characters (aura, sash glow) live in the same moved world
                self.SetCamera(_sub(cam.eye, centre), _sub(cam.at, centre))
            else:
                self.SetCamera(cam.eye, cam.at)
            if hall.fx and effect is not None:
                try:
                    effect.Render()
                except Exception:
                    uir1.TraceFailure('pregame hall effect render')
                    hall.scene.DeleteEffects()
                    if not hall.scene.fireSprites:
                        hall.scene.MakeFires('sprite')
        except Exception:
            uir1.TraceFailure('pregame hall render')
            failed = True
        finally:
            grp.RestoreViewport()
            grp.PopState()
            grp.SetInterfaceRenderState()
        if failed:
            hall.failed = True
            hall.Undo()

    def SetCamera(self, eye, at, scale=1.0):
        cam = self.hall.camera
        grp.SetEyeCamera(eye[0], eye[1], eye[2], at[0], at[1], at[2], 0.0, 0.0, 1.0)
        grp.SetPerspective(cam.fovEff, cam.aspect, 50.0 * scale, 8000.0 * scale)
        grp.SetOmniLight()      # after our camera: set before it, the models were lit from behind (black)

    def StockPasses(self):
        scene = self.hall.scene
        return (scene is not None and self.hall.cfg.get('charlight') == 'stock' and scene.reflections is None
                and bool(scene.places))

    def LightPasses(self, cam):
        """grp.SetOmniLight is a fixed world rig (spot at (50, 150, 350), point at (0, 200, 200), range 500) made for
        the stock select, where the character stands at the origin; ours stand 8-14 m away = unlit (dark; the old
        add-mode fill washed them out). 10. 10. late (the per-character origin passes drew copies: the engine applies
        a moved position only on its next update): ONE pass in a shrunk world - Scene.Place puts every character at
        s x (its ground - the arc centre) with chr.SetScale(s), the eye and the clip planes shrink by the same s
        (the same picture, the same depth buffer), so the whole arc stands inside the rig like the stock select."""
        s, centre = self.hall.scene.LightScale()
        eye = _scale(_sub(cam.eye, centre), s)
        at = _scale(_sub(cam.at, centre), s)
        self.SetCamera(eye, at, s)
        chr.Deform()
        chr.Render()
        return centre if s >= 0.99 else None


class Hit(uir1.Interactive):
    """The click area of a place in the arc (a character or a free slot)."""

    def __init__(self, parent, hall, index):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.hall, self.index = hall, index
        self.Show()

    def paint(self):
        self.hall.hover = self.index if self.hovered else (None if self.hall.hover == self.index else self.hall.hover)

    def click(self):
        self.hall.panel.OnCard(self.index)

    def OnMouseLeftButtonDoubleClick(self):
        self.hall.panel.OnCardDouble(self.index)
        return True


# =========================================================================== the background (layers / plate)
class FullLayer(ui.ExpandedImageBox):
    """A full-plate image (1920 x 1080 or a smaller copy of it, scaled up), shifted by the parallax of its depth;
    ``light`` = additive, its alpha driven every frame."""

    def __init__(self, parent, path, depth, light=None, rect=None):
        ui.ExpandedImageBox.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.LoadImage(path)
        self.iw = max(1, self.GetWidth())
        self.depth, self.light = depth, light
        self.rect = rect or (0, 0, PLATE_W, PLATE_H)      # the plate px this image covers (v3 sets: crops)
        self.nudge = (0.0, 0.0)                           # extra plate px offset (banner sway)
        if light:
            self.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
        try:
            self.SetLinearFiltering(True)
        except Exception:
            pass
        self.Show()

    def Place(self, cam, alpha=None, rgb=(1.0, 1.0, 1.0)):
        k = cam.scale * self.rect[2] / float(self.iw)
        self.SetScale(k, k)
        x, y = cam.Screen(self.rect[0] + self.nudge[0], self.rect[1] + self.nudge[1])
        dx, dy = cam.Shift(self.depth)
        self.SetPosition(int(round(x + dx)), int(round(y + dy)))
        if alpha is not None:
            if alpha <= 0.003:
                self.Hide()
                return
            SetColor(self, rgb, alpha)
        self.Show()


class Backdrop(object):
    """painted layers L0 wall, L1 columns + banners, L2 floor, L3 bowls, L4 foreground (vrstvy/) with the derived
    fire light masks and floor reflections; without them the single plate (hall_1920.png) with the same light and
    reflection images made from the plate. Each layer at its own depth = its own parallax."""

    LIGHTS = (('R_portal', 'floor', 'portal'), ('R_fire_L', 'floor', 0), ('R_fire_R', 'floor', 1))
    MASKS = (('M_fire_L', 'columns', 0), ('M_fire_R', 'columns', 1))

    def __init__(self, scene, root):
        hall = scene.hall
        cam, cfg = hall.camera, hall.cfg
        self.cam, self.cfg, self.root = cam, cfg, root
        depth = lambda px, py: cam.Depth(cam.Floor(px, py))
        self.depth = {'wall': depth(960.0, 562.0), 'columns': depth(440.0, 612.0), 'floor': depth(960.0, 690.0),
                      'braziers': depth(BRAZIERS[0][0], BRAZIERS[0][2]), 'front': float(cfg['l4depth'])}
        scene.depthWall, scene.depthFloor = self.depth['wall'], self.depth['floor']
        self.layered = bool(cfg.get('layers')) and Exists(LAYER_DIR + 'L0.png')
        self.layers = []
        if self.layered:
            base, prefix = LAYER_DIR, ''
            self._Add(base + 'L0.png', 'wall')
            if cfg.get('l1', 1):
                self._Add(base + 'L1.png', 'columns')
            self._Add(base + 'L2.png', 'floor')
        else:
            base, prefix = ASSET, 'plate_'
            self._Add(PLATE, 'floor')
            # the single plate moves as one piece: everything at the floor depth
            for key in ('wall', 'columns', 'braziers'):
                self.depth[key] = self.depth['floor']
            scene.depthWall = self.depth['floor']
        for name, where, drive in self.LIGHTS:
            self._Add(base + prefix + name + '.png', where, drive, optional=True)
        if self.layered and cfg.get('l3', 0):     # owner 10. 10.: the bowls look bad - off until new art
            self._Add(base + 'L3.png', 'braziers', optional=True)
        for name, where, drive in self.MASKS:
            self._Add(base + prefix + name + '.png', where, ('mask', drive), optional=True)
        self.front = None

    def _Add(self, path, where, light=None, optional=False):
        if optional and not Exists(path):
            return None
        layer = FullLayer(self.root, path, self.depth[where], light)
        self.layers.append(layer)
        layer.Place(self.cam)
        return layer

    def MakeFront(self, root):
        if self.layered and self.cfg.get('l4', 1) and Exists(LAYER_DIR + 'L4.png'):
            self.front = FullLayer(root, LAYER_DIR + 'L4.png', self.depth['front'])
            self.front.Place(self.cam)

    def Update(self, now, flick):
        cam, cfg = self.cam, self.cfg
        for layer in self.layers:
            drive = layer.light
            if drive is None:
                layer.Place(cam)
            elif drive == 'portal':
                layer.Place(cam, cfg['portalreflect'] * (0.9 + 0.1 * math.sin(now * 0.4)))
            elif isinstance(drive, tuple):
                layer.Place(cam, cfg['firelight'] * flick[drive[1]], (1.0, 0.62, 0.32))
            else:
                layer.Place(cam, cfg['reflect'] * flick[drive])
        if self.front is not None:
            self.front.Place(cam)


def _ease(value, target, dt, rise, fall):
    """Exponential ease towards target; ``rise`` s time constant when growing, ``fall`` when shrinking."""
    tau = rise if abs(target) > abs(value) else fall
    return value + (target - value) * (1.0 - math.exp(-dt / max(0.01, tau)))


def InArch(px, py):
    """Is plate point (px, py) inside the v3 portal opening?"""
    x0, x1, spring, crown = V3_ARCH
    if py > V3_HORIZON or px < x0 or px > x1 or py < crown:
        return False
    if py >= spring:
        return True
    cx, rx, ry = (x0 + x1) / 2.0, (x1 - x0) / 2.0, spring - crown
    return ((px - cx) / rx) ** 2 + ((py - spring) / ry) ** 2 <= 1.0


class Backdrop3(object):
    """v3 layer set a | d (vrstvy-a/ | vrstvy-d/, tools/pregame_proto_vrstvy.py sada). Owner 10. 10. late: the back
    wall (niches, banners, the arch) never moves - the camera orbits it (Camera.pivot = its depth); only what is
    nearer (floor, L4 pillars, characters) or deeper (the portal vista) moves, and little.
    L0 the whole hall (opaque, the portal floor continued flat into the fog, the statues in shadow), P the portal
    interior + a shimmer copy, L2 the floor (fades in 700-760 so nothing slips at the wall), L4L/L4R the outer dragon
    pillars; additive G_rim, M_lamp_L/R, S_L/S_R (set d), R_portal, R_lamp_L/R. Ambience sets ``levels``."""

    LIGHTS = (('G_rim', 'wall'), ('M_lamp_L', 'wall'), ('M_lamp_R', 'wall'), ('S_L', 'wall'), ('S_R', 'wall'),
              ('R_portal', 'floor'), ('R_lamp_L', 'floor'), ('R_lamp_R', 'floor'))

    def __init__(self, scene, root, key):
        hall = scene.hall
        cam, cfg = hall.camera, hall.cfg
        self.cam, self.cfg, self.root, self.key = cam, cfg, root, key
        self.set = SETS[key]
        depth = lambda px, py: cam.Depth(cam.Floor(px, py))
        wall = depth(960.0, V3_HORIZON + 8.0)
        self.depth = {'portal': wall * 2.4, 'wall': wall, 'floor': depth(960.0, 745.0),
                      'front': float(cfg['l4depth3'])}
        cam.SetPivot(wall if cfg.get('parallax') else None)
        scene.depthWall, scene.depthFloor = wall, self.depth['floor']
        self.layered = True
        self.layers, self.named, self.levels = [], {}, {}
        self.front, self.fronts = None, []
        self._Add('L0', 'wall')
        self._Add('P', 'portal', optional=True)
        self.shimmer = None
        if self.named.get('P') is not None:
            self.shimmer = FullLayer(self.root, self.set['dir'] + 'P.png', self.depth['portal'], None, SET_LAYOUT['P'])
            self.shimmer.name = 'P_shimmer'
            self.layers.append(self.shimmer)
            self.named['P_shimmer'] = self.shimmer
        self._Add('L2', 'floor', optional=True)
        for name, where in self.LIGHTS:
            if name.startswith('S_') and not self.set.get('shafts'):
                continue
            self._Add(name, where, light=True, optional=True)

    def _Add(self, name, where, light=None, optional=False, root=None):
        path = self.set['dir'] + name + '.png'
        if optional and not Exists(path):
            return None
        layer = FullLayer(root or self.root, path, self.depth[where], light, SET_LAYOUT[name])
        layer.name = name
        if root is None:
            self.layers.append(layer)
        self.named[name] = layer
        layer.Place(self.cam, 0.0 if light else None)
        return layer

    def MakeFront(self, root):
        if not self.cfg.get('l4', 1):
            return
        for name in ('L4L', 'L4R'):
            layer = self._Add(name, 'front', optional=True, root=root)
            if layer is not None:
                self.fronts.append(layer)
        self.front = self.fronts[0] if self.fronts else None

    def NearestDepth(self):
        return self.depth['front'] if self.fronts else self.depth['floor']

    def Update(self, now, flick):
        cam = self.cam
        for layer in self.layers:
            if layer.light or layer is self.shimmer:
                alpha, rgb = self.levels.get(layer.name, (0.0, (1.0, 1.0, 1.0)))
                layer.Place(cam, alpha, rgb)
            else:
                layer.Place(cam)
        for layer in self.fronts:
            layer.Place(cam)


def Pulse(t):
    """The portal's slow heartbeat: a double beat every 4.2 s, 0..1 (smooth, never a hard flash)."""
    x = t % 4.2
    return min(1.0, math.exp(-((x - 0.3) / 0.16) ** 2) + 0.6 * math.exp(-((x - 0.75) / 0.2) ** 2))


class Ambience(object):
    """v3 interactive scene. Hover = polled mouse position over plate areas (no windows: never takes a click from
    the characters or the panel; off while a character / card is hovered, a dialog is open or the mouse is on the
    panel). Lanterns flare (glow sprite + niche light + floor streak, ~250 ms), mist parts around the cursor on the
    floor, the portal lives (two-way haze swirl, fog over its floor, embers + now and then a bigger burst, rays from
    the depth, a heartbeat on the rim, a shimmer copy of the vista) and answers the hover; set d's light shafts
    breathe and follow the lantern hover. One clock drives it all: the lantern flicker lights its niche and streak,
    the portal pulse lights the rim, its floor reflection, the haze and (a touch) the characters."""

    def __init__(self, scene):
        self.scene, self.hall, self.cfg = scene, scene.hall, scene.hall.cfg
        self.back = scene.backdrop
        self.lamp, self.portal, self.pulse = [0.0, 0.0], 0.0, 0.0
        self.zone, self.last = (None, None), None
        self.lampGlow = [Sprite(scene.under, 'glow.png', True) for unused in V3_LANTERNS]
        self.lampCore = [Sprite(scene.under, 'glow.png', True) for unused in V3_LANTERNS]
        # the portal: haze clouds orbiting both ways, fog over its floor, rays from the depth
        self.swirl = [Sprite(scene.under, name, True)
                      for name in ('haze_a.png', 'haze_b.png', 'haze_a.png', 'haze_b.png', 'haze_a.png')]
        self.innerFog = [Sprite(scene.under, name, True) for name in ('haze_b.png', 'haze_a.png')]
        self.rays = [Sprite(scene.under, 'beam.png', True) for unused in range(5)]
        for ray in self.rays:
            ray.Pivot()
        rnd = random.Random(2610)
        self.embers = []
        for unused in range(max(0, int(self.cfg.get('embersmax', 30)))):
            self.embers.append([Sprite(scene.over, 'dot.png', True), rnd.random() * 4.0, rnd.uniform(2.6, 4.2),
                                rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.7, 1.3)])
        self.streaks = [Sprite(scene.over, 'dot.png', True) for unused in self.embers]
        for streak in self.streaks:
            streak.Pivot()
        self.ash = [[Sprite(scene.over, 'dot.png', False), rnd.random() * 9.0, rnd.uniform(6.0, 9.0), rnd.uniform(-1, 1),
                     rnd.uniform(0.6, 1.4)] for unused in range(12)]
        self.crackle = [[Sprite(scene.under, 'dot.png', True), rnd.random(), rnd.uniform(0.6, 1.4), rnd.randint(0, 999)]
                        for unused in range(10)]
        self.burst = [[Sprite(scene.over, 'dot.png', True), rnd.uniform(-1, 1), rnd.uniform(0.6, 1.0),
                       rnd.uniform(0.8, 1.4)] for unused in range(10)]
        self.mist = []
        for i in range(max(0, int(self.cfg.get('mistpuffs', 16)))):
            # one gentle draft out of the portal to both sides (never a random crowd of directions)
            x0 = rnd.uniform(0, 2300)
            self.mist.append({'sprite': Sprite(scene.front, ('haze_a.png', 'haze_b.png')[i % 2], False),
                              'x0': x0, 'y': rnd.uniform(704, 860), 'speed': rnd.uniform(4.0, 8.0),
                              'w': rnd.uniform(300, 480), 'h': rnd.uniform(80, 130), 'ph': rnd.uniform(0, 6.28),
                              'dx': 0.0, 'dy': 0.0, 'dip': 0.0})

    # ------------------------------------------------------------------ hover
    def Plate(self, mx, my, depth):
        """screen px -> plate px of a layer at ``depth`` (undoes the focus similarity, then the parallax shift)."""
        cam = self.hall.camera
        cx, cy = cam.W / 2.0, cam.H / 2.0
        bx = cx + (mx - cam.t[0] - cx) / cam.zf
        by = cy + (my - cam.t[1] - cy) / cam.zf
        sx, sy = cam.Shift(depth)
        return (bx - sx / cam.zf - cam.ox) / cam.scale0, (by - sy / cam.zf - cam.oy) / cam.scale0

    def Zone(self):
        hall, cfg = self.hall, self.cfg
        if not cfg.get('hover') or hall.hover is not None or hall.panel.dialog is not None:
            return None, None
        try:
            mx, my = wndMgr.GetMousePosition()
        except Exception:
            return None, None
        if not getattr(hall, 'uiHidden', False) and my >= getattr(hall.panel, 'panelTop', hall.camera.H) - 2:
            return None, None
        px, py = self.Plate(mx, my, self.back.depth['wall'])
        for i, (lx, ly) in enumerate(V3_LANTERNS):
            if abs(px - lx) <= 85 and ly - 115 <= py <= ly + 110:
                return 'lamp', i
        if InArch(px, py):
            return 'portal', 0
        fx, fy = self.Plate(mx, my, self.back.depth['floor'])
        if fy >= V3_HORIZON:
            return 'floor', (fx, fy)
        return None, None

    # ------------------------------------------------------------------ every frame
    def Update(self, now):
        cfg = self.cfg
        dt = 0.0 if self.last is None else max(0.0, min(0.1, now - self.last))
        self.last = now
        zone, arg = self.zone = self.Zone()
        for i in range(2):
            self.lamp[i] = _ease(self.lamp[i], 1.0 if zone == 'lamp' and arg == i else 0.0, dt, 0.09, 0.22)
        self.portal = _ease(self.portal, 1.0 if zone == 'portal' else 0.0, dt, 0.25, 0.6)
        self.pulse = Pulse(now) * float(cfg.get('pulse', 1.0))
        fl = [Flicker(now, 11 + i) for i in range(2)]
        flare = float(cfg.get('lampflare', 1.0))
        levels = self.back.levels
        for i, side in enumerate('LR'):
            h = self.lamp[i] * flare
            levels['M_lamp_' + side] = (min(1.0, cfg['lampspill'] * (0.85 + 0.15 * fl[i]) * (1.0 + 1.5 * h)), (1.0, 1.0, 1.0))
            levels['R_lamp_' + side] = (min(1.0, cfg['lampreflect'] * fl[i] * (1.0 + 1.0 * h)), (1.0, 1.0, 1.0))
        hp, beat = self.portal, self.pulse
        levels['R_portal'] = (min(1.0, cfg['portalreflect'] * (0.85 + 0.25 * beat) * (1.0 + 0.6 * hp)), (1.0, 1.0, 1.0))
        levels['G_rim'] = (min(1.0, cfg['rim'] * (0.8 + 0.35 * beat) * (1.0 + 1.3 * hp)), (1.0, 1.0, 1.0))
        breath = cfg['shaftbreath']
        for i, (side, w0, w1) in enumerate((('L', 0.31, 0.11), ('R', 0.29, 0.13))):
            wave = 0.65 * math.sin(now * w0 + 2.0 * i) + 0.35 * math.sin(now * w1 + 1.3 - i)
            levels['S_' + side] = (max(0.0, min(1.0, cfg['shafts'] * (1.0 + breath * wave) * (1.0 + 0.35 * self.lamp[i]))),
                                   (1.0, 1.0, 1.0))
        # the shimmer: a faint copy of the vista wobbling a pixel or two (heat over the portal)
        wob = _vnoise(now * 0.9, 31) - 0.5, _vnoise(now * 0.7, 37) - 0.5
        if self.back.shimmer is not None:
            self.back.shimmer.nudge = (wob[0] * 3.0 * (1.0 + hp), wob[1] * 2.0 * (1.0 + hp))
        levels['P_shimmer'] = (min(0.5, cfg['shimmer'] * (0.8 + 0.4 * beat) * (1.0 + 0.5 * hp)), (1.0, 0.86, 0.84))
        self.Lanterns(now, fl)
        self.Portal(now)
        self.Mist(now, dt)

    def Lanterns(self, now, fl):
        cfg, cam = self.cfg, self.hall.camera
        sc = cam.scale
        wx, wy = cam.Shift(self.back.depth['wall'])
        flare = float(cfg.get('lampflare', 1.0))
        for i, (lx, ly) in enumerate(V3_LANTERNS):
            h = self.lamp[i] * flare
            cx, cy = cam.Screen(lx, ly)
            size = 170.0 * sc * (1.0 + 0.8 * h) * (0.96 + 0.06 * fl[i])
            self.lampGlow[i].Place(cx + wx, cy + wy, size, size, (1.0, 0.6, 0.28),
                                   min(0.95, cfg['lampglow'] * (0.7 + 0.3 * fl[i]) * (1.0 + 1.2 * h)))
            core = 60.0 * sc * (1.0 + 0.5 * h) * (0.9 + 0.12 * fl[i])
            self.lampCore[i].Place(cx + wx, cy + wy, core, core * 1.3, (1.0, 0.86, 0.6),
                                   min(0.9, cfg['lampglow'] * 0.9 * fl[i] * (1.0 + 0.8 * h)))

    def Portal(self, now):
        cfg, cam = self.cfg, self.hall.camera
        sc = cam.scale
        px, py = cam.Shift(self.back.depth['portal'])
        hp, beat = self.portal, self.pulse
        cx0 = (V3_ARCH[0] + V3_ARCH[1]) / 2.0
        # haze: three clouds one way, two the other, breathing with the pulse
        for i, cloud in enumerate(self.swirl):
            way = 1.0 if i < 3 else -1.0
            ang = way * now * (0.13 + 0.04 * i) + i * 2.1
            r = (45.0 + 20.0 * i) if i < 3 else (30.0 + 25.0 * (i - 3))
            cx, cy = cam.Screen(cx0 + r * math.cos(ang), 400.0 + 0.7 * r * math.sin(ang))
            w, h = ((330.0 + 40.0 * i), 470.0) if i < 3 else (240.0, 300.0)
            cloud.Place(cx + px, cy + py, w * sc, h * sc, (0.85, 0.10, 0.07),
                        min(0.24, cfg['swirl'] * (0.7 + 0.25 * math.sin(now * (0.4 + 0.1 * i) + i) + 0.25 * beat)
                            * (1.0 + 0.8 * hp)))
        # fog drifting over the portal's floor, at its horizon
        for i, fog in enumerate(self.innerFog):
            drift = 70.0 * math.sin(now * (0.07 + 0.03 * i) + i * 2.4)
            cx, cy = cam.Screen(cx0 + drift, V3_VANISH_Y + 18.0 + 22.0 * i)
            fog.Place(cx + px, cy + py, 330.0 * sc, 95.0 * sc, (0.9, 0.16, 0.10),
                      min(0.3, cfg['portalfog'] * (0.8 + 0.3 * beat) * (1.0 + 0.6 * hp)))
        # rays from the depth: five narrow beams fanning up from the glow on the horizon, slowly turning
        ox, oy = cam.Screen(cx0, V3_VANISH_Y - 4.0)
        for i, ray in enumerate(self.rays):
            base = (-34.0, -17.0, 0.0, 17.0, 34.0)[i]
            angle = 180.0 + base + 4.0 * math.sin(now * (0.05 + 0.013 * i) + i * 1.7)
            length = (230.0 + 60.0 * _vnoise(now * 0.2, 50 + i)) * sc
            alpha = cfg['rays'] * (0.5 + 0.5 * _vnoise(now * 0.25, 60 + i)) * (0.8 + 0.4 * beat) * (1.0 + 1.0 * hp)
            ray.PlaceRotated(ox + px, oy + py, 46.0 * sc, length, angle, (1.0, 0.32, 0.18), min(0.3, alpha))
        # embers drifting out of the depth towards the viewer (more while hovered)
        base, most = float(cfg['embers']), float(len(self.embers))
        active = base + (most - base) * hp
        fx, fy = cam.Shift(self.back.NearestDepth())
        for i, ember in enumerate(self.embers):
            sprite, t0, life, ux, uy, size = ember
            on = max(0.0, min(1.0, active - i))
            if on <= 0.0:
                sprite.Hide()
                self.streaks[i].Hide()
                continue
            cycle = math.floor((now + t0) / life)
            t = ((now + t0) % life) / life
            h1, h2, h3, h4 = [_hash(cycle * 4 + k, i + 77) for k in range(4)]
            sx, sy = cx0 + (h1 - 0.5) * 240.0, 360.0 + h2 * 250.0
            dx, dy = (sx - cx0) + ux * 60.0, (sy - 470.0) + 90.0 + uy * 30.0
            n = math.sqrt(dx * dx + dy * dy) or 1.0
            dist = 260.0 + h3 * 420.0
            curl = (h4 - 0.5) * 1.6 * float(cfg.get('curl', 1.0))

            def at(tt):
                pr = tt ** 1.7
                a = curl * pr                               # the path bends a little (rising heat), never a line
                ca, sa = math.cos(a), math.sin(a)
                ux_, uy_ = (dx * ca - dy * sa) / n, (dx * sa + dy * ca) / n
                qx, qy = cam.Screen(sx + ux_ * dist * pr, sy + uy_ * dist * pr - 40.0 * pr * pr)
                return qx + px + (fx - px) * pr, qy + py + (fy - py) * pr
            ex, ey = at(t)
            prog = t ** 1.7
            d = (2.5 + 11.0 * prog) * size * sc
            alpha = Smooth(t / 0.12) * (1.0 - Smooth((t - 0.65) / 0.35)) * on * (0.75 + 0.25 * math.sin(now * 9.0 + i))
            colour = (1.0, 0.18 + 0.3 * h4, 0.08 + 0.08 * h4)
            sprite.Place(ex, ey, d, d, colour, 0.9 * alpha)
            # a short motion streak behind it (the eye reads speed, not a dot)
            bx, by = at(max(0.0, t - 0.035))
            vx, vy = ex - bx, ey - by
            length = math.sqrt(vx * vx + vy * vy)
            streak = self.streaks[i]
            if cfg.get('streaks', 0) > 0 and length > 1.5:
                streak.PlaceAngled((ex + bx) / 2.0, (ey + by) / 2.0, d * 0.45, length * 2.2 + d,
                                   math.degrees(math.atan2(-vx, vy)), colour, cfg['streaks'] * alpha)
            else:
                streak.Hide()
        # now and then a bigger burst (every ~9 s; while hovered also every ~3.7 s)
        start = None
        if cfg.get('bursts'):
            for period, weight in ((9.0, 1.0), (3.7, hp)):
                n = math.floor(now / period)
                for k in (n, n - 1):
                    s0 = k * period + _hash(int(k), int(period * 10)) * period * 0.45
                    if 0.0 <= now - s0 < 2.4 and weight > 0.05 and (start is None or s0 > start[0]):
                        start = (s0, weight, int(k) * 7 + int(period))
        for j, (sprite, ux, speed, size) in enumerate(self.burst):
            if start is None:
                sprite.Hide()
                continue
            t = (now - start[0]) / 2.4
            ang = math.radians(90.0 + ux * 70.0 + 25.0 * (_hash(start[2], j) - 0.5))
            prog = t ** 1.4
            dist = (180.0 + 320.0 * speed) * prog
            bx, by = cam.Screen(cx0 + math.cos(ang) * dist, 520.0 + math.sin(ang) * dist * 0.8 - 120.0 * prog)
            shx, shy = px + (fx - px) * prog, py + (fy - py) * prog
            d = (5.0 + 18.0 * prog) * size * sc
            alpha = Smooth(t / 0.08) * (1.0 - Smooth((t - 0.5) / 0.5)) * start[1]
            sprite.Place(bx + shx, by + shy, d, d, (1.0, 0.42, 0.14), min(1.0, 0.95 * alpha))
        self.Ash(now, px, py, fx, fy, cx0)
        self.Crackle(now, hp)

    def Ash(self, now, px, py, fx, fy, cx0):
        """Dark flakes of ash drifting slowly out of the portal and down, tumbling (the counterweight of the
        embers: not everything that comes out glows)."""
        cfg, cam = self.cfg, self.hall.camera
        sc = cam.scale
        for i, (sprite, t0, life, side, size) in enumerate(self.ash):
            if cfg.get('ash', 0) <= 0:
                sprite.Hide()
                continue
            t = ((now + t0) % life) / life
            cycle = math.floor((now + t0) / life)
            h1 = _hash(int(cycle) * 3 + i, 91)
            x = cx0 + (h1 - 0.5) * 300.0 + side * 260.0 * t + 14.0 * math.sin(now * 1.7 + i)
            y = 380.0 + 120.0 * h1 + 330.0 * t * t
            qx, qy = cam.Screen(x, y)
            k = t ** 1.5
            d = (3.0 + 5.0 * k) * size * sc
            alpha = cfg['ash'] * Smooth(t / 0.15) * (1.0 - Smooth((t - 0.75) / 0.25)) * (0.6 + 0.4 * abs(math.sin(now * 2.3 + i)))
            sprite.Place(qx + px + (fx - px) * k, qy + py + (fy - py) * k, d, d * (0.5 + 0.5 * abs(math.sin(now * 2.3 + i))),
                         (0.07, 0.03, 0.03), alpha)

    def Crackle(self, now, hp):
        """Small sparks crawling along the inner edge of the arch (left jamb up, over the crown, down the right),
        each only now and then (the rim is charged, not a neon sign)."""
        cfg, cam = self.cfg, self.hall.camera
        sc = cam.scale
        x0, x1, spring, crown = V3_ARCH
        cx0, rx, ry = (x0 + x1) / 2.0, (x1 - x0) / 2.0, spring - crown
        jamb = V3_HORIZON - spring
        arc = math.pi * (rx + ry) / 2.0
        total = 2.0 * jamb + arc
        for sprite, u0, speed, seed in self.crackle:
            on = _vnoise(now * 1.3 * speed, seed)
            strength = cfg.get('crackle', 0) * max(0.0, (on - 0.55) / 0.45) * (1.0 + 1.2 * hp)
            if strength <= 0.01:
                sprite.Hide()
                continue
            s_ = ((u0 + now * 0.035 * speed) % 1.0) * total
            if s_ < jamb:
                x, y = x0 + 3.0, V3_HORIZON - s_
            elif s_ < jamb + arc:
                a = math.pi * (s_ - jamb) / arc
                x, y = cx0 - (rx - 3.0) * math.cos(a), spring - (ry - 3.0) * math.sin(a)
            else:
                x, y = x1 - 3.0, spring + (s_ - jamb - arc)
            qx, qy = cam.Screen(x, y)
            d = (3.0 + 3.0 * _vnoise(now * 7.0, seed + 5)) * sc
            sprite.Place(qx, qy, d, d, (1.0, 0.35, 0.16), min(1.0, strength))

    def Mist(self, now, dt):
        cfg, cam = self.cfg, self.hall.camera
        sc = cam.scale
        fx, fy = cam.Shift(self.back.depth['floor'])
        zone, arg = self.zone
        cursor = arg if zone == 'floor' else None
        part = float(cfg.get('mistpart', 1.0))
        left, right = self.back.set['mist']
        for puff in self.mist:
            # the draft flows out from the middle to both sides (left half leftwards, right half rightwards)
            u0 = puff['x0'] % 2300.0
            side = -1.0 if u0 < 1150.0 else 1.0
            x = 960.0 + side * ((u0 % 1150.0 + now * puff['speed']) % 1150.0)
            y = puff['y'] + 6.0 * math.sin(now * 0.17 + puff['ph'])
            tdx = tdy = tdip = 0.0
            if cursor is not None and part > 0:
                vx, vy = x - cursor[0], (y - cursor[1]) * 1.6
                r = math.sqrt(vx * vx + vy * vy)
                if r < 260.0:
                    w = (1.0 - r / 260.0) ** 2
                    nx, ny = (vx / r, vy / r) if r > 1e-3 else (1.0, 0.0)
                    tdx = nx * 110.0 * w * part - ny * 50.0 * w * part           # pushed away + a swirl
                    tdy = (ny * 110.0 * w * part + nx * 50.0 * w * part) * 0.4
                    tdip = min(0.9, 0.65 * w * part)
            rise = 0.25 if tdip > puff['dip'] else 1.2
            k = 1.0 - math.exp(-dt / rise)
            puff['dx'] += (tdx - puff['dx']) * k
            puff['dy'] += (tdy - puff['dy']) * k
            puff['dip'] += (tdip - puff['dip']) * k
            puff['x'] = x
            u = Smooth((x - 700.0) / 520.0)
            tint = tuple(left[c] + (right[c] - left[c]) * u for c in range(3))
            cx, cy = cam.Screen(x + puff['dx'], y + puff['dy'])
            edge = Smooth((1150.0 - abs(x - 960.0)) / 160.0) * Smooth(abs(x - 960.0) / 140.0)   # fade at both ends
            alpha = cfg['mist'] * (0.7 + 0.3 * math.sin(now * 0.23 + puff['ph'])) * (1.0 - puff['dip']) * edge
            puff['sprite'].Place(cx + fx, cy + fy, puff['w'] * sc, puff['h'] * sc, tint, alpha)


def _argb(color, alpha):
    """A packed 0xAARRGGBB text colour with its alpha scaled (signed for SetPackedFontColor)."""
    a = int(max(0.0, min(1.0, alpha)) * ((color >> 24) & 255 or 255))
    return (a << 24) | (color & 0xFFFFFF)


def _Glyphs(text):
    """The characters of a text as separate strings in the engine's own encoding: UTF-8 sequences kept whole (the
    client's literals), any other byte string one byte per character (a code-page name never breaks)."""
    if not isinstance(text, str):                       # py3 bytes
        text = text.decode('utf-8', 'replace')
    try:
        uni = text.decode('utf-8')                      # py2: a byte str
    except AttributeError:
        return list(text)                               # py3: already characters
    except UnicodeDecodeError:
        return list(text)
    return [ch.encode('utf-8') for ch in uni]


class Nameplates(object):
    """The character detail in the scene (owner 10. 10. night, in game: "D udělat ... musí to jít číst"; then
    "variantu s výškou dej do píči", "ten pod nohama ... zahnutá v prostoru, trochu větší písmo", "to okno níž víc k
    hlavě, divný dolní odsek"). Two modes, cfg detail=d|a, F9 switches them (VYZKUM-D.md):
      d  the nameplate over the selected one's head (red name lighter than the brand red, <guild>) + its info on
         the floor around the rune ring: two lines of upright letters following the ring's ellipse (Lv · job, then
         VIT · INT · SÍL · POH), labels muted and values bright, outline + a dark copy + a soft dark band under
         them; laid out once per selection, moved as one piece (no letter jumps on its own);
      a  a compact card beside the head (the side with room, never on a neighbour): red underlined name,
         Lv · job, a divider, Cech / Odehráno in two aligned columns, a divider, the four stats in four columns.
    Every text: the engine outline (+ a soft dark plate under the nameplate). Hovering another character shows its
    name + level faintly. Everything fades / slides on a change, stays on screen, under the title, above the strip;
    H hides it."""

    ORDER = ('d', 'darc', 'dp', 'a')
    NAMES = {'d': 'jmenovka + text pod kruhem', 'darc': 'text po oblouku kolem kruhu',
             'dp': 'text u všech postav (vybraná plně)', 'a': 'karta u hlavy'}
    D_MODES = ('d', 'darc', 'dp')
    CARD_W = 184
    SHADOW = ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 2))  # a 4-way outline + a 2 px drop, all under the line
    ARC_R = 110.0                                      # cm: the text circle around the rune ring (58)

    def __init__(self, scene):
        self.scene, self.hall = scene, scene.hall
        g = self.hall.panel.g
        self.g = g
        self.mode = str(self.hall.cfg.get('detail', 'd')).lower()
        if self.mode == 'd' and self.hall.cfg.get('textarc'):
            self.mode = 'darc'
        if self.mode not in self.ORDER:
            self.mode = 'd'
        self.plates = []
        for unused in ARC:
            self.plates.append({
                'back': Sprite(scene.over, 'shadow.png'),
                'glow': Sprite(scene.over, 'glow.png', True),
                'plate': GuildPlate(scene.over),            # guild cosmetics (made before the texts: drawn under)
                'name': P.Text(scene.over, '', 0, 0, g.noto(24, True), T.RED_HI, align='center'),
                'guild': P.Text(scene.over, '', 0, 0, g.noto(16), T.IVORY, align='center'),
                'a': 0.0, 'texts': None,
            })
        # d: two straight lines centred under the ring (owner 11. 10.: the per-letter / per-segment tricks broke in
        # the engine - "fLv. 100f"): ONE TextLine per line, label / value colours and the red dots by text tags,
        # a black copy 1 px down-right as the shadow
        # owner 11. 10.: "vždyť to je napsané černě?" - the black copy was made AFTER the line, so it was drawn over
        # it. Now the shadow copies are made first (drawn under), the line's colour is set for the whole line
        # (SetPackedFontColor, no colour tags), both lines nearly the same size
        self.arcFonts = (g.noto(26, True), g.noto(24, True))
        # owner 11. 10.: the stats under the selected one hard to read on the red floor - a soft dark panel under
        # them (made before the lines: drawn under them)
        self.statPanel = Sprite(scene.under, 'shadow.png')
        self.arcs = []
        for font in self.arcFonts:
            shadows = [P.Text(scene.under, '', 0, 0, font, 0xFF000000, align='center') for unused in self.SHADOW]
            line = P.Text(scene.under, '', 0, 0, font, T.IVORY, align='center')
            self.arcs.append({'font': font, 'line': line, 'shadows': shadows, 'shadow': shadows[0],
                              'text': '', 'alpha': None})
        # textarc (owner 11. 10. "zkus ještě jednou natočit"): WORD segments on the ring's ellipse, each one
        # TextLine in one colour (SetPackedFontColor), its shadows made first, placed from a common BASELINE (the
        # font's line height measured once on "ÁÍgy"), no padding glyphs
        self.segs = []
        for k, font in enumerate(self.arcFonts):
            for unused in range(2 if k == 0 else 4):
                shadows = [P.Text(scene.under, '', 0, 0, font, 0xFF000000) for unused2 in self.SHADOW]
                line = P.Text(scene.under, '', 0, 0, font, T.IVORY)
                self.segs.append({'font': font, 'row': k, 'line': line, 'shadows': shadows, 'text': '', 'alpha': None})
        self.segDots = [uir1.Rect(scene.under, 0, 0, 4, 4, 0xD30D0E, 0.0) for unused in range(4)]
        self.refHeight = {}
        # d+ (owner 11. 10. "uvidíš furt i ty staty dole"): one smaller line under every other character
        # (owner 11. 10. "ať jdou vidět jména postav u všech furt": the NAME above that line, muted but clear)
        self.smallFont = g.noto(20, True)
        self.nameFont = g.noto(22, True)
        self.small = []
        for unused in ARC:
            nshadows = [P.Text(scene.under, '', 0, 0, self.nameFont, 0xFF000000, align='center') for unused2 in self.SHADOW]
            name = P.Text(scene.under, '', 0, 0, self.nameFont, T.INK_DIM, align='center')
            shadows = [P.Text(scene.under, '', 0, 0, self.smallFont, 0xFF000000, align='center') for unused2 in self.SHADOW]
            line = P.Text(scene.under, '', 0, 0, self.smallFont, T.INK_DIM, align='center')
            self.small.append({'line': line, 'shadows': shadows, 'text': '', 'alpha': None, 'a': 0.0,
                               'name': {'line': name, 'shadows': nshadows, 'text': '', 'alpha': None}})
        self.band = [Sprite(scene.under, 'shadow.png') for unused in range(9)]
        self.layout = None
        self.arcA, self.arcSlot = 0.0, None
        # a: the card
        c = self.card = {
            'box': uir1.Rect(scene.over, 0, 0, 1, 1, 0x0A0707, 0.0),
            'accent': uir1.Rect(scene.over, 0, 0, 1, 2, 0xD30D0E, 0.0),
            'div': [uir1.Rect(scene.over, 0, 0, 1, 1, 0x4A2A26, 0.0) for unused in range(2)],
            'name': P.Text(scene.over, '', 0, 0, g.noto(22, True), T.RED_HI),
            'under': uir1.Rect(scene.over, 0, 0, 1, 2, 0xD30D0E, 0.0),
            'line': P.Text(scene.over, '', 0, 0, g.noto(16), T.INK_DIM),
            'labels': [P.Text(scene.over, text, 0, 0, g.noto(14), T.MUTED) for text in ('Cech', 'Odehráno')],
            'values': [P.Text(scene.over, '', 0, 0, g.noto(16, True), T.IVORY, align='right') for unused in range(2)],
            'statLabels': [P.Text(scene.over, text, 0, 0, g.noto(13), T.MUTED, align='center')
                           for text in ('VIT', 'INT', 'SÍL', 'POH')],
            'statValues': [P.Text(scene.over, '', 0, 0, g.noto(18, True), T.IVORY, align='center') for unused in range(4)],
            'slot': None, 'a': 0.0, 'side': 1.0,
        }
        for text in self.Texts():
            try:
                text.SetOutline(True)
            except Exception:
                pass
        for rect in self.Rects():
            rect.Hide()
        self.toast = P.Text(scene.over, '', int(scene.W / 2), g.P(14), g.noto(15, True), T.IVORY, align='center')
        try:
            self.toast.SetOutline(True)
        except Exception:
            pass
        self.toast.Hide()
        self.toastAt = None
        self.last = None

    # ------------------------------------------------------------------ pieces
    def Rects(self):
        c = self.card
        return [c['box'], c['accent'], c['under']] + c['div']

    def Texts(self):
        out = []
        for item in self.plates:
            out += [item['name'], item['guild']]
        for arc in self.arcs + self.segs + self.small + [item['name'] for item in self.small]:
            out += [arc['line']] + arc['shadows']
        c = self.card
        return out + [c['name'], c['line']] + c['labels'] + c['values'] + c['statLabels'] + c['statValues']

    def Widgets(self):
        out = list(self.Texts()) + self.Rects()
        for item in self.plates:
            out += [item['back'], item['glow']]
        return out + self.band + self.segDots

    def Data(self, slot):
        hall = self.hall
        name, level, guild, played, family, job = hall.panel.Detail(slot)
        stats = list(getattr(hall.window, 'statpoint', None) or [])[:4]
        return {'name': name, 'level': level, 'guild': guild, 'played': played, 'job': job, 'stats': stats}

    def Cycle(self):
        """F9: d <-> a, named for 1.5 s at the top."""
        order = self.ORDER
        self.mode = order[(order.index(self.mode) + 1) % len(order)] if self.mode in order else order[0]
        self.hall.cfg['detail'] = self.mode
        self.card['slot'], self.card['a'] = None, 0.0
        self.arcSlot, self.arcA = None, 0.0
        self.layout = None
        for item in self.plates:
            item['texts'] = None
        self.toast.SetText('Detail postavy (F9): %s  –  %s' % (self.mode, self.NAMES.get(self.mode, '')))
        self.toastAt = self.last if self.last is not None else app.GetTime()
        return self.mode

    def Text(self, line, x, y, color, alpha):
        P.SetColor(line, _argb(color, alpha))
        try:
            line.SetOutline(alpha > 0.35)               # the engine outline does not fade: off while faint
        except Exception:
            pass
        P.Move(line, int(x), int(y))
        line.Show()

    def Rect(self, rect, x, y, w, h, packed, alpha):
        if alpha <= 0.01 or w < 1 or h < 1:
            rect.Hide()
            return
        rect.SetPosition(int(x), int(y))
        rect.SetSize(int(w), int(h))
        rect.SetColor(uikit_color(packed, alpha))
        rect.Show()

    # ------------------------------------------------------------------ every frame
    def Update(self, now):
        dt = 0.0 if self.last is None else max(0.0, min(0.1, now - self.last))
        self.last = now
        hidden = getattr(self.hall, 'uiHidden', False)
        for slot, place, ground in self.scene.places:
            self.UpdatePlate(slot, ground, dt, hidden)
        self.UpdateArcs(dt, hidden)
        self.UpdateCard(dt, hidden)
        self.UpdateToast(now)

    def UpdateToast(self, now):
        if self.toastAt is None:
            self.toast.Hide()
            return
        t = now - self.toastAt
        if t > 1.8:
            self.toastAt = None
            self.toast.Hide()
            return
        P.SetColor(self.toast, _argb(T.IVORY, 1.0 if t < 1.5 else max(0.0, 1.0 - (t - 1.5) / 0.3)))
        self.toast.Show()

    def UpdatePlate(self, slot, ground, dt, hidden):
        hall, scene, cam, cfg, g = self.hall, self.scene, self.hall.camera, self.hall.cfg, self.g
        item = self.plates[slot]
        count = hall.Count()
        sel = slot == hall.selected and slot < count
        hov = hall.hover == slot and slot < count and not sel
        target = 1.0 if (sel and self.mode in self.D_MODES) else (float(cfg.get('hoverplate', 0.55)) if hov else 0.0)
        if hidden or slot >= count:
            target = 0.0
        item['a'] = _ease(item['a'], target, dt, 0.16, 0.12) if dt > 0 else target
        a = item['a']
        if a < 0.02:
            for key in ('back', 'glow', 'name', 'guild', 'plate'):
                item[key].Hide()
            item['texts'] = None
            return
        if sel and self.mode in self.D_MODES:
            d = self.Data(slot)
            texts = (d['name'], ('<%s>' % d['guild']) if d['guild'] else '')
        elif hov or item['texts'] is None:
            d = self.Data(slot)
            texts = ('Lv. %d  %s' % (d['level'], d['name']), '')
        else:
            texts = item['texts']                       # fading out: keep what it said
        if texts != item['texts']:
            item['name'].SetText(texts[0])
            item['guild'].SetText(texts[1])
            item['texts'] = texts
        feet_g = scene.Feet(slot, ground)
        head = cam.Project((feet_g[0], feet_g[1], cfg['body'] + 26.0))
        if head is None:
            return
        rise = (1.0 - Smooth(a)) * g.P(10)
        nw = max(P.Width(item['name']), P.Width(item['guild'])) or g.P(120)
        cell = uir1.FontCell(g.noto(24, True))
        gcell = uir1.FontCell(g.noto(16)) if texts[1] else 0
        ph = cell + gcell + g.P(4)
        x = max(g.P(16) + nw / 2.0, min(cam.W - g.P(16) - nw / 2.0, head[0]))
        y = max(g.P(150), head[1] - ph) + rise
        item['back'].Place(x, y + ph / 2.0, nw + g.P(70), ph + g.P(26), (1.0, 1.0, 1.0),
                           float(cfg.get('backplate', 0.6)) * a)
        item['glow'].Place(x, y + cell / 2.0, nw * 0.9, cell * 1.6, (0.9, 0.08, 0.06), 0.16 * a if sel else 0.0)
        self.Text(item['name'], x, y, T.RED_HI if sel else T.INK_DIM, a)
        look = GuildLook(texts[1][1:-1]) if texts[1].startswith('<') else None      # texts[1] = '<guild>'
        if texts[1]:
            gw = P.Width(item['guild'])
            if look:
                item['plate'].Place(look, x, y + cell + g.P(2), gw, gcell, a)
            else:
                item['plate'].Hide()
            self.Text(item['guild'], x, y + cell + g.P(2), _guild_colour(look, T.IVORY), a)
        else:
            item['guild'].Hide()
            item['plate'].Hide()

    # ------------------------------------------------------------------ d: the text under the ring
    def ArcTexts(self, slot):
        """Two plain lines: "Lv. 100  ·  Válečník" and "VIT 4  ·  INT 3  ·  SÍL 6  ·  POH 3" (one colour each)."""
        d = self.Data(slot)
        first = 'Lv. %d  ·  %s' % (d['level'], d['job'])
        if len(d['stats']) == 4:
            second = '  ·  '.join('%s %s' % pair for pair in zip(('VIT', 'INT', 'SÍL', 'POH'), d['stats']))
        else:
            second = 'Odehráno %s' % d['played']
        return first, second

    def UpdateArcs(self, dt, hidden):
        hall, scene = self.hall, self.scene
        count, sel = hall.Count(), hall.selected
        on = self.mode in self.D_MODES and not hidden and 0 <= sel < count
        if self.arcSlot != sel or not on:
            self.arcA = max(0.0, self.arcA - dt / 0.12) if dt > 0 else 0.0
            if self.arcA <= 0.0 and on:
                self.arcSlot = sel
                texts = self.ArcTexts(sel)
                for arc, text in zip(self.arcs, texts):
                    self.SetLine(arc, text)
                self.FillSegments(texts)
                self.layout = None
        elif on:
            self.arcA = min(1.0, self.arcA + dt / 0.3) if dt > 0 else 1.0
        a, slot = self.arcA, self.arcSlot
        box = None
        if a <= 0.01 or slot is None or slot >= count:
            self.HideArcs()
        else:
            ground = scene.Feet(slot, scene.places[slot][2])
            if self.mode == 'darc':
                self.HideLines(self.arcs)
                box = self.PlaceSegments(ground, a)
            else:
                self.HideLines(self.segs)
                for dot in self.segDots:
                    dot.Hide()
                box = self.PlaceArcs(ground, a)
        self.UpdateSmall(dt, hidden, box)

    def SetLine(self, arc, text):
        arc['text'], arc['alpha'] = text, None
        arc['line'].SetText(text)
        for shadow in arc['shadows']:
            shadow.SetText(text)

    def HideLines(self, arcs):
        for arc in arcs:
            arc['line'].Hide()
            for shadow in arc['shadows']:
                shadow.Hide()

    def HideArcs(self):
        self.statPanel.Hide()
        self.HideLines(self.arcs)
        self.HideLines(self.segs)
        for widget in self.band + self.segDots:
            widget.Hide()

    def Tint(self, arc, colour, a):
        q = int(round(a * 16)) / 16.0
        if arc['alpha'] != (q, colour):
            arc['alpha'] = (q, colour)
            P.SetColor(arc['line'], _argb(colour, q))
            for shadow in arc['shadows']:
                P.SetColor(shadow, _argb(0xFF000000, 0.9 * q))

    def Put(self, arc, x, y):
        for (ox, oy), shadow in zip(self.SHADOW, arc['shadows']):
            shadow.SetPosition(x + ox, y + oy)
            shadow.Show()
        arc['line'].SetPosition(x, y)
        arc['line'].Show()

    def PlaceArcs(self, ground, a):
        """Both lines straight, centred under the rune ring (one rounding for the whole block), kept above the strip
        and inside the screen; bright ivory over a black 4-way outline + 2 px drop. Returns the block's box."""
        cam, g = self.hall.camera, self.g
        ring = cam.Ellipse(ground, 58.0)
        c = cam.Project(ground)
        if c is None:
            self.HideArcs()
            return None
        below = (ring[0][1] + ring[2] / 2.0) if ring else c[1]
        cells = [uir1.FontCell(arc['font']) for arc in self.arcs]
        total = sum(cells) + g.P(4)
        bottom = getattr(self.hall.panel, 'panelTop', cam.H)
        for bx0, by0, bx1, by1 in getattr(self.hall.panel, 'ButtonBoxes', lambda: [])():
            if bx0 - g.P(20) < c[0] < bx1 + g.P(20):
                bottom = min(bottom, by0 - g.P(4))     # a button right under it (layout a): the text above it
        y = int(round(min(below + g.P(8), bottom - total - g.P(6)))) + int(round((1.0 - Smooth(a)) * g.P(8)))
        widest = max([P.Width(arc['line']) for arc in self.arcs] + [g.P(200)])
        x = int(round(max(g.P(16) + widest / 2.0, min(cam.W - g.P(16) - widest / 2.0, c[0]))))
        box = (x - widest / 2.0, y, x + widest / 2.0, y + total)
        self.statPanel.Place(x, y + total / 2.0, widest + g.P(90), total + g.P(46), (1.0, 1.0, 1.0), 0.85 * a)
        colours = (T.IVORY, 0xFFF2E6D8)          # the stats line cream like the A8 captions
        for arc, cell, colour in zip(self.arcs, cells, colours):
            self.Tint(arc, colour, a)
            self.Put(arc, x, y)
            y += cell + g.P(4)
        return box

    # ------------------------------------------------------------------ d (textarc): word segments on the arc
    def RefHeight(self, font):
        """The font's line height measured once on "ÁÍgy" (accent above, descender below) - every segment of that
        font is placed from the same baseline with it, whatever its own letters are."""
        if font not in self.refHeight:
            probe = self.segs[0]['line']
            keep = probe.GetText() if hasattr(probe, 'GetText') else ''
            P.Font(probe, font, 'ÁÍgy')
            try:
                h = int(probe.GetTextSize()[1])
            except Exception:
                h = 0
            self.refHeight[font] = h or uir1.FontCell(font)
            P.Font(probe, self.segs[0]['font'], keep)
        return self.refHeight[font]

    def FillSegments(self, texts):
        first, second = texts
        rows = [[w for w in first.split('  ·  ')], [w for w in second.split('  ·  ')]]
        for seg in self.segs:
            seg['text'] = ''
        used = {0: 0, 1: 0}
        for seg in self.segs:
            row = rows[seg['row']]
            i = used[seg['row']]
            text = row[i] if i < len(row) else ''
            used[seg['row']] += 1
            self.SetLine(seg, text)

    def PlaceSegments(self, ground, a):
        """The words of both lines on the front of a circle around the feet: spaced like normal text (red dots
        between), each word's BASELINE on the ellipse's front curve at its centre, the second row one line lower.
        Laid out once per selection (whole px); per frame only the centre moves. Returns the block's box."""
        cam, g = self.hall.camera, self.g
        if self.layout is None or self.layout[0] != self.arcSlot:
            self.layout = (self.arcSlot, self.LayOutSegments(ground))
        lay = self.layout[1]
        c = cam.Project(ground)
        if c is None or not lay['segments']:
            self.HideArcs()
            return None
        cx, cy = int(round(c[0])), int(round(c[1]))
        bottom = getattr(self.hall.panel, 'panelTop', cam.H)
        lowest = max(dy + self.RefHeight(seg['font']) for seg, dx, dy, w in lay['segments'])
        left = min(dx for seg, dx, dy, w in lay['segments'])
        right = max(dx + w for seg, dx, dy, w in lay['segments'])
        cy = min(cy, int(bottom - 4 - lowest))
        cx = max(g.P(16) - left, min(int(cam.W - g.P(16) - right), cx))
        rise = int(round((1.0 - Smooth(a)) * g.P(8)))
        shown = set()
        for seg, dx, dy, w in lay['segments']:
            self.Tint(seg, T.IVORY if seg['row'] == 0 else 0xFFE6DED2, a)
            self.Put(seg, cx + dx, cy + dy + rise)
            shown.add(id(seg))
        for seg in self.segs:
            if id(seg) not in shown:
                seg['line'].Hide()
                for shadow in seg['shadows']:
                    shadow.Hide()
        for dot, (dx, dy) in zip(self.segDots, lay['dots']):
            self.Rect(dot, cx + dx, cy + dy + rise, g.P(4), g.P(4), 0xD30D0E, a)
        for dot in self.segDots[len(lay['dots']):]:
            dot.Hide()
        return (cx + left, cy + min(dy for seg, dx, dy, w in lay['segments']), cx + right, cy + lowest)

    def LayOutSegments(self, ground):
        cam, g = self.hall.camera, self.g
        keep = cam.offset
        cam.SetOffset(0.0, 0.0)
        try:
            c = cam.ProjectBase(ground)
            f = cam.ProjectBase(_add(ground, cam.back, self.ARC_R))
            sp = cam.ProjectBase(_add(ground, cam.x0, self.ARC_R))
        finally:
            cam.SetOffset(*keep)
        out = {'segments': [], 'dots': []}
        if c is None or f is None or sp is None:
            return out
        rx, ry = max(1.0, abs(sp[0] - c[0])), f[1] - c[1]
        gap = g.P(30)
        baseY = 0
        for row in (0, 1):
            segs = [seg for seg in self.segs if seg['row'] == row and seg['text']]
            if not segs:
                continue
            ref = self.RefHeight(segs[0]['font'])
            widths = [P.Width(seg['line']) or g.P(40) for seg in segs]
            total = float(sum(widths) + gap * (len(segs) - 1))
            x = -total / 2.0
            for i, (seg, w) in enumerate(zip(segs, widths)):
                u = max(-0.98, min(0.98, (x + w / 2.0) / rx))
                base = ry * math.sqrt(1.0 - u * u) + baseY       # this word's baseline on the curve
                out['segments'].append((seg, int(round(x)), int(round(base - ref)), int(w)))
                x += w
                if i < len(segs) - 1:
                    du = max(-0.98, min(0.98, (x + gap / 2.0) / rx))
                    db = ry * math.sqrt(1.0 - du * du) + baseY
                    out['dots'].append((int(round(x + gap / 2.0 - 2)), int(round(db - ref * 0.45))))
                    x += gap
            baseY += ref + g.P(2)
        return out

    # ------------------------------------------------------------------ d+: a line under every other character
    def UpdateSmall(self, dt, hidden, selbox):
        """d+: under every other occupied place its NAME (muted, clear) and one smaller dimmed line "Lv. 98 ·
        Šaman"; a block that would touch the selected one's block or a neighbour's is shortened to the name +
        "Lv. 98", then to the name alone (the names always stay where it fits at all)."""
        hall, scene, cam, g = self.hall, self.scene, self.hall.camera, self.g
        count, sel = hall.Count(), hall.selected
        boxes = ([selbox] if selbox else []) + list(getattr(hall.panel, 'ButtonBoxes', lambda: [])())
        cell, ncell = uir1.FontCell(self.smallFont), uir1.FontCell(self.nameFont)
        bottom = getattr(hall.panel, 'panelTop', cam.H)
        order = sorted(range(len(self.small)), key=lambda s_: abs(ARC_OF_SLOT[s_] - ARC_OF_SLOT[sel]) if 0 <= sel < len(ARC_OF_SLOT) else s_)
        for slot in order:
            item = self.small[slot]
            on = self.mode == 'dp' and not hidden and slot < count and slot != sel
            item['a'] = _ease(item['a'], 0.75 if on else 0.0, dt, 0.25, 0.12) if dt > 0 else (0.75 if on else 0.0)
            if item['a'] < 0.02 or not on and item['a'] < 0.05:
                self.HideLines([item, item['name']])
                continue
            ground = scene.Feet(slot, scene.places[slot][2])
            ring = cam.Ellipse(ground, 58.0)
            c = cam.Project(ground)
            if c is None:
                continue
            d = self.Data(slot)
            if item['name']['text'] != d['name']:
                self.SetLine(item['name'], d['name'])
            nw = P.Width(item['name']['line']) or g.P(100)
            placed = False
            for text in ('Lv. %d  ·  %s' % (d['level'], d['job']), 'Lv. %d' % d['level'], ''):
                if item['text'] != text:
                    self.SetLine(item, text)
                w = max(nw, (P.Width(item['line']) or g.P(100)) if text else 0)
                hgt = ncell + (cell + g.P(2) if text else 0)
                y = int(round(min(((ring[0][1] + ring[2] / 2.0) if ring else c[1]) + g.P(8), bottom - hgt - g.P(6))))
                x = int(round(max(g.P(16) + w / 2.0, min(cam.W - g.P(16) - w / 2.0, c[0]))))
                box = (x - w / 2.0 - g.P(6), y, x + w / 2.0 + g.P(6), y + hgt)
                if not any(b[0] < box[2] and box[0] < b[2] and b[1] < box[3] and box[1] < b[3] for b in boxes):
                    boxes.append(box)
                    self.Tint(item['name'], 0xFFD8CFC4, item['a'])
                    self.Put(item['name'], x, y)
                    if text:
                        self.Tint(item, T.INK_DIM, item['a'])
                        self.Put(item, x, y + ncell + g.P(2))
                    else:
                        self.HideLines([item])
                    placed = True
                    break
            if not placed:
                self.HideLines([item, item['name']])

    # ------------------------------------------------------------------ a: the card beside the head
    def UpdateCard(self, dt, hidden):
        hall, scene, cam, cfg, g = self.hall, self.scene, self.hall.camera, self.hall.cfg, self.g
        c = self.card
        count, sel = hall.Count(), hall.selected
        on = self.mode == 'a' and not hidden and 0 <= sel < count
        if c['slot'] != sel or not on:
            c['a'] = max(0.0, c['a'] - dt / 0.12) if dt > 0 else 0.0
            if c['a'] <= 0.0 and on:
                c['slot'] = sel
                self.FillCard(sel)
        elif on:
            c['a'] = min(1.0, c['a'] + dt / 0.25) if dt > 0 else 1.0
        a = c['a']
        widgets = ([c['name'], c['line']] + c['labels'] + c['values'] + c['statLabels'] + c['statValues'])
        if a <= 0.01 or c['slot'] is None or c['slot'] >= count:
            for widget in widgets + self.Rects():
                widget.Hide()
            return
        slot = c['slot']
        ground = scene.Feet(slot, scene.places[slot][2])
        head = cam.Project((ground[0], ground[1], cfg['body']))
        feet = cam.Project(ground)
        if head is None or feet is None:
            return
        W = cam.W
        pad, cw = g.P(14), g.P(self.CARD_W)
        nameH = uir1.FontCell(g.noto(22, True))
        lineH = uir1.FontCell(g.noto(16))
        rowH = max(uir1.FontCell(g.noto(14)), uir1.FontCell(g.noto(16, True))) + g.P(6)
        statH = uir1.FontCell(g.noto(13)) + uir1.FontCell(g.noto(18, True)) + g.P(2)
        gapS = g.P(10)
        ch = pad + nameH + g.P(6) + lineH + gapS + 1 + gapS + 2 * rowH + gapS + 1 + gapS + statH + pad
        # beside the head: the side with more free room up to the next character (or the screen edge)
        half = cfg['body'] * 0.17 * cam.PixelsPerUnit(ground)
        free = {1.0: W - g.P(16) - (feet[0] + half), -1.0: (feet[0] - half) - g.P(16)}
        for other, unused, og in scene.places:
            if other == slot or other >= count:
                continue
            o = cam.Project(scene.Feet(other, og))
            if o is None:
                continue
            ohalf = cfg['body'] * 0.17 * cam.PixelsPerUnit(scene.Feet(other, og))
            if o[0] > feet[0]:
                free[1.0] = min(free[1.0], (o[0] - ohalf) - (feet[0] + half))
            else:
                free[-1.0] = min(free[-1.0], (feet[0] - half) - (o[0] + ohalf))
        side = 1.0 if free[1.0] >= free[-1.0] else -1.0
        if c['side'] != side and a < 0.3:
            c['side'] = side
        side = c['side']
        gap = g.P(14)
        x = feet[0] + half + gap if side > 0 else feet[0] - half - gap - cw
        x = max(g.P(16), min(W - g.P(16) - cw, x))
        y = head[1] - g.P(4)                            # level with the head, not above the neighbours
        y = max(g.P(150), min(getattr(hall.panel, 'panelTop', cam.H) - ch - g.P(10), y))
        x += (1.0 - Smooth(a)) * g.P(14) * side
        self.Rect(c['box'], x, y, cw, ch, 0x0A0707, 0.74 * a)
        self.Rect(c['accent'], x, y, cw, 2, 0xD30D0E, a)
        ix, iw = x + pad, cw - 2 * pad
        yy = y + pad
        self.Text(c['name'], ix, yy, T.RED_HI, a)
        self.Rect(c['under'], ix, yy + nameH + g.P(2), min(iw, P.Width(c['name']) or g.P(120)), 2, 0xD30D0E, a)
        yy += nameH + g.P(6)
        self.Text(c['line'], ix, yy, T.INK_DIM, a)
        yy += lineH + gapS
        self.Rect(c['div'][0], ix, yy, iw, 1, 0x4A2A26, a)
        yy += 1 + gapS
        for label, value in zip(c['labels'], c['values']):
            self.Text(label, ix, yy + g.P(2), T.MUTED, a)
            self.Text(value, ix + iw, yy, T.IVORY, a)    # right-aligned: one clean column of values
            yy += rowH
        yy += gapS - g.P(6)
        self.Rect(c['div'][1], ix, yy, iw, 1, 0x4A2A26, a)
        yy += 1 + gapS
        colW = iw / 4.0
        for i, (label, value) in enumerate(zip(c['statLabels'], c['statValues'])):
            cx = ix + colW * (i + 0.5)
            self.Text(label, cx, yy, T.MUTED, a)
            self.Text(value, cx, yy + uir1.FontCell(g.noto(13)) + g.P(2), T.IVORY, a)

    def FillCard(self, slot):
        c, d = self.card, self.Data(slot)
        c['name'].SetText(d['name'])
        c['line'].SetText('Lv. %d  ·  %s' % (d['level'], d['job']))
        c['values'][0].SetText(d['guild'] or '–')
        c['values'][1].SetText(d['played'])
        stats = d['stats'] if len(d['stats']) == 4 else ['–'] * 4
        for line, value in zip(c['statValues'], stats):
            line.SetText(str(value))


class CharacterReflections(object):
    """EXPERIMENTAL (reflectchars=1): an upside-down, faint copy of every character under its feet (chr.SetScale
    with z -1 + chr.SetBlendRenderMode). Doubles the drawn models; the mirrored winding may show back faces."""

    BASE = 60

    def __init__(self, hall):
        self.hall = hall
        self.vids = {}
        window = hall.window
        for slot in range(hall.Count()):
            data = window.mycharacters.GetDisplayData(slot) or {}
            vid = self.BASE + slot
            try:
                chr.CreateInstance(vid)
                chr.SelectInstance(vid)
                chr.SetVirtualID(vid)
                chr.SetRace(data.get('RACE', 0))
                chr.SetArmor(data.get('FORM', 0))
                chr.SetHair(data.get('HAIR', 0))
                if hasattr(chr, 'SetAcce'):
                    chr.SetAcce(data.get('ACCE', 0))
                chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
                chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
                chr.SetScale(1.0, 1.0, -1.0)
                chr.Show()
                chr.SetBlendRenderMode(vid, float(hall.cfg['reflectalpha']))
                self.vids[slot] = vid
            except Exception:
                uir1.TraceFailure('pregame hall reflection')

    def Place(self, slot, ground, rotation):
        vid = self.vids.get(slot)
        if vid is None or not chr.HasInstance(vid):
            return
        chr.SelectInstance(vid)
        chr.SetPixelPosition(int(round(ground[0])), int(round(-ground[1])), 0)
        chr.SetRotation(rotation)
        chr.Show()

    def Gesture(self, slot):
        vid = self.vids.get(slot)
        if vid is not None and chr.HasInstance(vid):
            chr.SelectInstance(vid)
            try:
                chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED, 0.1)
            except Exception:
                pass

    def Update(self, now):
        hall = self.hall
        for slot, vid in self.vids.items():
            if chr.HasInstance(vid):
                light = hall.Light(slot, now)
                chr.SetBlendRenderMode(vid, float(hall.cfg['reflectalpha']) * (0.6 + 0.4 * light))

    def Destroy(self):
        for vid in self.vids.values():
            try:
                if chr.HasInstance(vid):
                    chr.DeleteInstance(vid)
            except Exception:
                pass
        self.vids = {}


# =========================================================================== the scene
class Scene(object):
    def __init__(self, hall):
        self.hall = hall
        hall.scene = self
        self.roots = []
        window = hall.window
        cfg = hall.cfg
        board = window.dlgBoard
        W, H = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        self.W, self.H = W, H
        # the background: the painted layers (vrstvy/) when the pack has them, else the single plate; both in our own
        # root under everything so they can shift (parallax). The uiscript BackGround is hidden meanwhile.
        self.background = window.backGround
        self.background.Hide()
        key = cfg.get('set')
        self.v3 = key if (key in SETS and cfg.get('layers') and Exists(SETS[key]['dir'] + 'L0.png')) else None
        self.arc = V3_ARC if self.v3 else ARC
        self.fogY = (712.0, 770.0, 880.0) if self.v3 else (600.0, 650.0, 735.0)
        self.ambience = None
        self.lightning = None
        cam = self.Camera()
        if self.v3:
            # narrow screens (4:3, 5:4): the cover-scaled plate loses its sides - the row closes in so the outer
            # characters and their names stay inside (owner 11. 10.: other resolutions / aspect ratios)
            half = W / 2.0 / max(0.01, cam.scale)
            k = max(0.5, min(1.0, (half - 190.0) / (960.0 - V3_ARC[0][0])))
            if k < 1.0:
                self.arc = tuple((960.0 + (x - 960.0) * k, y) for x, y in V3_ARC)
        hall.camera = cam
        for name in ('giant_brand_mark',):
            try:
                board.GetChild(name).Hide()
            except Exception:
                pass
        if self.v3:
            self.backdrop = Backdrop3(self, self._root(board), self.v3)
        else:
            self.backdrop = Backdrop(self, self._root(board))
        # layers: under (floor, lights, back glow) -> 3D -> over (dust, sparks) -> UI (the panel, made later)
        self.under = self._root(board)
        self.haze = [Sprite(self.under, 'haze_a.png', True), Sprite(self.under, 'haze_b.png', True)]
        self.portalPool = Sprite(self.under, 'pool.png', True)
        self.fireGlow, self.firePool, self.fireSprites = [], [], []
        for unused in BRAZIERS:
            self.fireGlow.append(Sprite(self.under, 'glow.png', True))
            self.firePool.append(Sprite(self.under, 'pool.png', True))
        self.beam, self.back, self.pool, self.ring, self.hoverRing, self.shadow = [], [], [], [], [], []
        for unused in ARC:
            self.beam.append(Sprite(self.under, 'beam.png', True))
        self.contact, self.mirror = [], []
        # the places: a stone dais + a dormant rune ring under everyone; the selected: glow disc, ripple, motes
        self.dais, self.runeBase, self.glowDisc, self.ripple = [], [], [], []
        for unused in ARC:
            self.dais.append(Sprite(self.under, 'shadow.png'))
            self.runeBase.append(Sprite(self.under, 'ring.png'))
            self.glowDisc.append(Sprite(self.under, 'pool.png', True))
            self.ripple.append(Sprite(self.under, 'ring.png', True))
        # owner 11. 10. ("ještě bych ho vylepšil"): the light under the selected one without any drawing - a hot
        # core and a tall soft reflection on the glossy floor, both pulsing with the gate
        self.glowCore = [Sprite(self.under, 'pool.png', True) for unused in ARC]
        self.sheen = [Sprite(self.under, 'back.png', True) for unused in ARC]
        for unused in ARC:
            self.mirror.append(Sprite(self.under, 'back.png'))
            self.contact.append(Sprite(self.under, 'shadow.png'))
        for unused in ARC:
            self.shadow.append(Sprite(self.under, 'shadow.png'))
            self.pool.append(Sprite(self.under, 'pool.png', True))
            self.back.append(Sprite(self.under, 'back.png', True))
            self.ring.append(Sprite(self.under, 'ring.png'))
            self.hoverRing.append(Sprite(self.under, 'ring_hover.png'))
        self.renderer = Renderer(board, hall)
        self.reflections = CharacterReflections(hall) if cfg.get('reflectchars') else None
        self.over = self._root(board)
        self.motes = [[Sprite(self.over, 'dot.png', True), i / 10.0, 0.6 + 0.08 * (i % 5)] for i in range(10)]
        # ground fog in front of the feet, then the foreground pillars (L4) over everything but the UI
        self.front = self._root(board)
        self.fog = []
        for i in range(3):
            self.fog.append(Sprite(self.front, 'fog.png'))
        if self.v3:
            self.ambience = MakeAmbience(self)      # lantern glows (under), embers (over), mist (front, under L4)
            self.lightning = Lightning(self)
        # the banners' emblems (set a: their light layers come from its L0)
        self.emblems = None
        if self.v3 == 'a' and cfg.get('emblems', 1) and Exists(ASSET + 'emblem/mask_L.png'):
            self.emblems = BannerEmblems(self)
        self.backdrop.MakeFront(self.front)
        self.flames = []
        self.sparks = []
        self.smoke = []
        rnd = random.Random(1010)
        for b in range(len(BRAZIERS)):
            for unused in range(9):
                self.sparks.append([b, Sprite(self.over, 'dot.png', True), rnd.random() * 3.0, rnd.uniform(0.9, 1.8),
                                    rnd.uniform(-1, 1), rnd.uniform(0.5, 1.0)])
            for unused in range(4):
                self.smoke.append([b, Sprite(self.under, 'smoke.png'), rnd.random() * 6.0, rnd.uniform(5.0, 7.5),
                                   rnd.uniform(-1, 1)])
        self.dust = []
        for unused in range(18):
            self.dust.append([Sprite(self.over, 'dot.png', True), rnd.random(), rnd.random(), rnd.uniform(0.02, 0.06),
                              rnd.uniform(0, 6.28), rnd.uniform(0.5, 1.3)])
        self.labels = []
        self.plus = []
        self.hits = []
        for index in range(len(ARC)):
            self.labels.append(P.Text(self.over, '', 0, 0, 'Tahoma:12b', T.INK_DIM, align='center'))
            self.hits.append(Hit(self.over, hall, index))
        self.places = []
        self.nameplates = None
        if self.v3 and cfg.get('nameplate', 1):
            self.nameplates = Nameplates(self)
        # the free places of the bare hall: "+ nová postava" on the floor (shadows first, then the line)
        self.free = []
        font = hall.panel.g.noto(20, True)
        for unused in ARC:
            shadows = [P.Text(self.under, '+  nová postava', 0, 0, font, 0xFF000000, align='center')
                       for unused2 in Nameplates.SHADOW]
            line = P.Text(self.under, '+  nová postava', 0, 0, font, T.INK_DIM, align='center')
            for widget in shadows + [line]:
                widget.Hide()
            self.free.append({'line': line, 'shadows': shadows})
        self.Place()
        self.MakeFires(cfg.get('fire', 'mse'))

    def _root(self, board):
        root = ui.Window()
        self.roots.append(root)
        root.SetParent(board)
        root.SetPosition(*ScreenOrigin(board))
        root.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        root.AddFlag('not_pick')
        root.Show()
        return root

    def Camera(self):
        cfg = self.hall.cfg
        facing = (0.0, 1.0)
        try:
            # the legacy select camera (python rotation 0 faces it): only to learn which side the characters face
            app.SetCenterPosition(0.0, 0.0, 0.0)
            app.SetCamera(1550.0, 15.0, 180.0, 95.0)
            ex, ey, ez = grp.GetCameraPosition()
            tx, ty, tz = grp.GetTargetPosition()
            if abs(ex - tx) + abs(ey - ty) > 1.0:
                facing = (ex - tx, ey - ty)
        except Exception:
            pass
        zoom = cfg['zoom'] if cfg.get('parallax') else 1.0
        if self.v3:
            return Camera(self.W, self.H, cfg['fov'], cfg['camh3'], facing, zoom, V3_VANISH_Y)
        return Camera(self.W, self.H, cfg['fov'], cfg['camh'], facing, zoom)

    # ------------------------------------------------------------------ placement
    def Place(self):
        """Every instance at its arc point, turned a little towards the camera; labels and free places."""
        hall, cam = self.hall, self.hall.camera
        count = hall.Count()
        keep = cam.offset
        cam.SetOffset(0.0, 0.0)
        self.places = []
        for slot in range(len(ARC)):
            place = ARC_OF_SLOT[slot]
            px, py = self.arc[place]
            ground = cam.Floor(px, py)
            if self.v3 and hall.cfg.get('charforward'):
                # owner 11. 10. "zkus všechny posunout třeba metr dopředu": towards the camera on the floor
                ground = _add(ground, cam.back, float(hall.cfg['charforward']))
            self.places.append((slot, place, ground))
            if slot < count and chr.HasInstance(slot):
                turn = math.degrees(math.atan2(cam.Lateral(ground), cam.Depth(ground)))
                chr.SelectInstance(slot)
                chr.SetRotation(-0.7 * turn)
                chr.Show()
                if self.reflections is not None:
                    self.reflections.Place(slot, ground, -0.7 * turn)
            label = self.labels[slot]
            if slot < count:
                name, level = hall.panel.Detail(slot)[:2]
                label.SetText('Lv. %d  %s' % (level, name))
            elif slot < hall.rows:
                label.SetText('Volný slot')
            else:
                label.SetText('')
            if slot >= count and slot < hall.rows:
                if len(self.plus) <= slot:
                    self.plus.extend([None] * (slot + 1 - len(self.plus)))
                if self.plus[slot] is None:
                    box = max(24, int(30 * hall.panel.g.s))
                    plate = P.Plate(self.over, 0, 0, box, box)
                    plate.label = P.Text(plate, '+', box // 2, box // 2, hall.panel.g.noto(20, True), T.INK, align='center',
                                         valign='center')
                    self.plus[slot] = plate
            elif slot < len(self.plus) and self.plus[slot] is not None:
                self.plus[slot].Hide()
        cam.SetOffset(*keep)
        self.PlaceInstances()
        self.PlaceOverlays()
        # the window's later chr.* calls (delete motion, start) act on the selected instance
        if 0 <= hall.selected < count and chr.HasInstance(hall.selected):
            chr.SelectInstance(hall.selected)

    def LightScale(self):
        """(s, centre): the shrunk render world of Renderer.LightPasses (s 1 = the plain world: charlight=add or the
        experimental mirrored copies)."""
        cfg = self.hall.cfg
        if cfg.get('charlight') != 'stock' or self.reflections is not None:
            return 1.0, (0.0, 0.0, 0.0)
        # owner 11. 10. (bug): with a shrunk world (lightscale < 1) the sash (acce) is drawn unscaled - huge, over
        # the head (CGraphicThingInstance::RecalcAccePositionMatrixFromBoneMatrix: its scale centre comes from the
        # bone matrix of the unscaled skeleton). So the world stays 1 : 1 (lightscale=1) and only the light rig moves:
        # the selected one stands at the rig's origin (the stock look), the others get a small fill (otherfill)
        return max(0.05, min(1.0, float(cfg.get('lightscale', 1.0)))), getattr(self, 'lightCentre', (0.0, 0.0, 0.0))

    def PlaceInstances(self):
        """Every character at its arc point (in the render world: shrunk about the arc centre, see LightScale)."""
        hall = self.hall
        count = hall.Count()
        grounds = [ground for slot, unused, ground in self.places if slot < count]
        sel = hall.selected
        dy = int(self.hall.cfg.get('rigshift', 0))
        middle = [ground for unused, place, ground in self.places if place == 2]
        if str(self.hall.cfg.get('lightcentre', 'hall')) == 'hall' and middle:
            # owner 11. 10. (bug: a corner one selected -> the others slid far and grew): the rig stays in the
            # middle of the hall for good; who is selected changes only the modulate (LightCharacters), never a
            # position or a size
            self.lightCentre = (middle[0][0], middle[0][1] - dy, 0.0)
        elif sel is not None and 0 <= sel < len(grounds):
            # the selected stands at the rig's origin = exactly the stock select light (and no rounding); rigshift
            # (F6) moves the whole row that many cm towards the camera, under the rig's point light (0, 200, 200;
            # range 5 m): at 200 the outer ones come inside its range and get real shaded light (dimmer, from the
            # front-top), the selected stands right under it
            self.lightCentre = (grounds[sel][0], grounds[sel][1] - dy, 0.0)
        elif grounds:
            self.lightCentre = (sum(g[0] for g in grounds) / len(grounds), sum(g[1] for g in grounds) / len(grounds), 0.0)
        s, centre = self.LightScale()
        self.feet = {}
        for slot, unused, ground in self.places:
            if slot < count and chr.HasInstance(slot):
                p = _scale(_sub(ground, centre), s)
                px, py = int(round(p[0])), int(round(-p[1]))
                # where the engine really puts the feet (whole units only): shadows, rings and labels go there
                self.feet[slot] = (px / s + centre[0], -py / s + centre[1], 0.0)
                pz = 0
                if s >= 0.99 and (slot != sel or str(self.hall.cfg.get('lightcentre', 'hall')) == 'hall'):
                    px, py, pz = self.Slide(px, py, centre)
                chr.SelectInstance(slot)
                chr.SetPixelPosition(px, py, pz)
                try:
                    chr.SetScale(s, s, s)
                except Exception:
                    pass

    # the stock rig's point light (grp.SetOmniLight: (0, 200, 200), range 500) in the render world (y = - pixel y)
    RIG_POINT = (0.0, 200.0, 200.0)

    def Slide(self, px, py, centre):
        """A character standing beyond the rig's light: moved along its view ray towards the eye until its chest is
        lightreach cm from the point light - the feet stay on the same screen point (the floor is a picture), the
        model grows by eye distance (at most slidemax). Returns the new whole-unit (px, py, pz)."""
        cfg = self.hall.cfg
        reach, most = float(cfg.get('lightreach', 430.0)), float(cfg.get('slidemax', 1.17))
        cam = self.hall.camera
        # the eye at rest (eye0, without the parallax lean towards the selection): the slide never depends on it
        eye = _sub(getattr(cam, 'eye0', cam.eye), centre)
        feet = (float(px), float(-py), 0.0)
        chest = 100.0
        dist = lambda q: math.sqrt(sum((a - b) ** 2 for a, b in zip((q[0], q[1], q[2] + chest), self.RIG_POINT)))
        if dist(feet) <= reach:
            return px, py, 0
        best = feet
        for k in range(1, 61):
            t = k * 0.005
            q = tuple(f + (e - f) * t for f, e in zip(feet, eye))
            if 1.0 / max(1e-3, 1.0 - t) > most:
                break
            best = q
            if dist(q) <= reach:
                break
        return int(round(best[0])), int(round(-best[1])), int(round(best[2]))

    def Feet(self, slot, ground):
        """The ground point the engine really stands ``slot`` on (PlaceInstances), else the arc point."""
        return getattr(self, 'feet', {}).get(slot, ground)

    def PlaceOverlays(self):
        """Labels over the heads, click areas over the bodies, the + of free places (every frame: parallax)."""
        hall, cam = self.hall, self.hall.camera
        count = hall.Count()
        body = hall.cfg['body']
        for slot, place, ground in self.places:
            ground = self.Feet(slot, ground)
            head = cam.Project((ground[0], ground[1], body + 22.0))
            feet = cam.Project(ground)
            label, hit = self.labels[slot], self.hits[slot]
            if not (head and feet):
                continue
            P.Move(label, int(head[0]), int(head[1]))
            w = int(body * 0.45 * cam.PixelsPerUnit(ground))
            bare = getattr(hall.panel, 'bare', False) and self.nameplates is not None
            # the click area covers the body AND the name / text under the feet (owner: "klikem na jméno")
            extra = hall.panel.g.P(80) if bare else 0
            hit.SetPosition(int(feet[0] - w / 2), int(head[1]))
            hit.SetSize(w, int(feet[1] - head[1]) + extra)
            hit.Show() if slot < hall.rows else hit.Hide()
            if bare and count <= slot < hall.rows:
                # an empty place: "+ nová postava" on the floor where a character would stand (no plate)
                if slot < len(self.plus) and self.plus[slot] is not None:
                    self.plus[slot].Hide()
                self.PlaceFree(slot, feet, hall.hover == slot)
                hit.SetPosition(int(feet[0] - w / 2), int(feet[1] - w))
                hit.SetSize(w, int(w + extra))
                continue
            if slot < len(self.free):
                self.HideFree(slot)
            if count <= slot < hall.rows and slot < len(self.plus) and self.plus[slot] is not None:
                mid = cam.Project((ground[0], ground[1], body * 0.5))
                plate = self.plus[slot]
                plate.SetState('hover' if hall.hover == slot else 'normal')
                plate.SetPosition(int(mid[0]) - plate.GetWidth() // 2, int(mid[1]) - plate.GetHeight() // 2)
                plate.Hide() if getattr(hall, 'uiHidden', False) else plate.Show()

    def PlaceFree(self, slot, feet, hovered):
        hall, g = self.hall, self.hall.panel.g
        item = self.free[slot]
        if getattr(hall, 'uiHidden', False):
            self.HideFree(slot)
            return
        x, y = int(round(feet[0])), int(round(feet[1] - g.P(6)))
        colour = _argb(T.IVORY if hovered else T.INK_DIM, 0.95 if hovered else 0.75)
        for (ox, oy), shadow in zip(Nameplates.SHADOW, item['shadows']):
            shadow.SetPosition(x + ox, y + oy)
            shadow.Show()
        P.SetColor(item['line'], colour)
        item['line'].SetPosition(x, y)
        item['line'].Show()

    def HideFree(self, slot):
        item = self.free[slot]
        item['line'].Hide()
        for shadow in item['shadows']:
            shadow.Hide()

    # ------------------------------------------------------------------ parallax
    def Parallax(self, now):
        """Eases the eye offset to: a few px of mouse sway + a lean towards the selected character."""
        hall, cam, cfg = self.hall, self.hall.camera, self.hall.cfg
        if not cfg.get('parallax'):
            return
        floor = max(1.0, self.depthFloor)
        per_px = floor / cam.F                                   # cm of eye move per px at the characters' floor
        try:
            mx, my = wndMgr.GetMousePosition()
            nx = max(-1.0, min(1.0, float(mx) / max(1.0, cam.W) * 2.0 - 1.0))
            ny = max(-1.0, min(1.0, float(my) / max(1.0, cam.H) * 2.0 - 1.0))
        except Exception:
            nx = ny = 0.0
        if self.v3:
            self.Parallax3(now, nx, ny)
            return
        tx = nx * cfg['sway'] * per_px
        tz = -ny * cfg['sway'] * 0.5 * per_px
        sel = hall.selected
        if 0 <= sel < len(self.places) and sel < hall.Count():
            ground = self.places[sel][2]
            tx += _dot(_sub(ground, cam.eye0), cam.x) * cfg['follow']
        dt = max(0.0, min(0.1, now - getattr(self, 'lastNow', now)))
        self.lastNow = now
        k = 1.0 - math.exp(-dt * 4.0 / max(0.05, cfg['ease']))
        ox, oz = cam.offset
        cam.SetOffset(ox + (tx - ox) * k, oz + (tz - oz) * k)

    def Parallax3(self, now, nx, ny):
        """v3 motion plan (PROTOTYP-V3.md): the eye orbits the back wall (it never moves); the mouse sways it a few px,
        the selection leans it, a slow breathing (two incommensurate sines) keeps the room alive when nothing
        happens; every flat layer then moves by its own depth, never more than maxshift px (the L4 pillars)."""
        hall, cam, cfg = self.hall, self.hall.camera, self.hall.cfg
        front = self.backdrop.NearestDepth()
        k_front = cam.F * (1.0 / max(1.0, front) - 1.0 / max(1.0, cam.pivot or 1e9))
        k_floor = cam.F * (1.0 / max(1.0, self.depthFloor) - 1.0 / max(1.0, cam.pivot or 1e9))
        per_px = 1.0 / max(1e-6, k_floor)                        # cm of eye move per px at the characters' floor
        tx = nx * cfg['sway'] * per_px
        tz = -ny * cfg['sway'] * 0.5 * per_px
        sel = hall.selected
        if 0 <= sel < len(self.places) and sel < hall.Count():
            ground = self.places[sel][2]
            tx += _dot(_sub(ground, cam.eye0), cam.x0) * cfg['follow']
        b = cfg.get('breath', 0.0) / max(1e-6, k_front)
        tx += b * (0.6 * math.sin(now * 0.21) + 0.4 * math.sin(now * 0.13 + 1.0))
        tz += b * 0.6 * math.sin(now * 0.17 + 2.0)
        limit = cfg['maxshift'] / max(1e-6, k_front)
        tx, tz = max(-limit, min(limit, tx)), max(-limit, min(limit, tz))
        dt = max(0.0, min(0.1, now - getattr(self, 'lastNow', now)))
        self.lastNow = now
        k = 1.0 - math.exp(-dt * 4.0 / max(0.05, cfg['ease']))
        ox, oz = cam.offset
        cam.SetOffset(ox + (tx - ox) * k, oz + (tz - oz) * k)
        self.Focus(dt)

    def Focus(self, dt):
        """BDO-like camera focus (owner + brother 10. 10. night): on the selected one the lens zooms in (camzoom)
        and the view turns a little so it moves camcenter of the way to the screen centre horizontally, its feet
        staying on their screen row; eased in ~camease s, re-aimed on every selection change. The 2D layers follow
        as a similarity fitted on its body; the shift is clamped so the plate always covers the screen."""
        hall, cam, cfg = self.hall, self.hall.camera, self.hall.cfg
        sel, count = hall.selected, hall.Count()
        if not cfg.get('camfocus') or not (0 <= sel < count) or not self.places:
            target = (1.0, 0.0, 0.0)
            anchor = cam.anchor
        else:
            ground = self.Feet(sel, self.places[sel][2])
            anchor = (ground[0], ground[1], cfg['body'] * 0.5)
            zf = max(1.0, float(cfg.get('camzoom', 1.12)))
            a0 = cam.ProjectBase(anchor)
            f0 = cam.ProjectBase(ground)
            if a0 is None or f0 is None:
                target = (1.0, 0.0, 0.0)
            else:
                C = (cam.W / 2.0, cam.H / 2.0)
                want_x = a0[0] + (C[0] - a0[0]) * float(cfg.get('camcenter', 0.5))
                # after the zoom alone the anchor would be at C + zf (a0 - C); the turn makes up the rest
                sx = want_x - (C[0] + zf * (a0[0] - C[0]))
                sy = f0[1] - (C[1] + zf * (f0[1] - C[1]))          # the feet stay on their row
                # the plate (cover-scaled, zoom margin) must keep covering the screen after the shift
                left = C[0] + zf * (cam.ox - C[0])
                right = C[0] + zf * (cam.ox + PLATE_W * cam.scale0 - C[0])
                top = C[1] + zf * (cam.oy - C[1])
                bottom = C[1] + zf * (cam.oy + PLATE_H * cam.scale0 - C[1])
                margin = float(cfg.get('maxshift', 8.0)) + 2.0
                sx = max(cam.W - right + margin, min(-left - margin, sx))
                sy = max(cam.H - bottom + margin, min(-top - margin, sy))
                F = cam.F0 * zf
                ax = math.atan((a0[0] - C[0]) / cam.F0)
                yaw = ax - math.atan((C[0] + zf * (a0[0] - C[0]) + sx - C[0]) / F)
                ay = math.atan(-(f0[1] - C[1]) / cam.F0)
                pitch = ay - math.atan(-(C[1] + zf * (f0[1] - C[1]) + sy - C[1]) / F)
                target = (zf, yaw, pitch)
        k = 1.0 - math.exp(-dt * 3.0 / max(0.05, float(cfg.get('camease', 0.6)))) if dt > 0 else 0.0
        cur = (cam.zf, cam.yaw, cam.pitch)
        new = tuple(c + (t - c) * k for c, t in zip(cur, target))
        if abs(new[0] - 1.0) < 1e-4 and abs(new[1]) < 1e-5 and abs(new[2]) < 1e-5 and target == (1.0, 0.0, 0.0):
            new = (1.0, 0.0, 0.0)
        cam.SetFocus(new[0], new[1], new[2], anchor)

    # ------------------------------------------------------------------ fires
    def MakeFires(self, mode):
        hall, cam = self.hall, self.hall.camera
        self.fires = []
        for index, (bx, rim, feet) in enumerate(BRAZIERS):
            ground = cam.Floor(bx, feet)
            lift = cam.Lift(ground, bx, rim)
            self.fires.append((ground, lift))
        if mode == 'off':
            return
        made = False
        if mode in ('mse', 'both') and effect is not None and hall.Count() > 0:
            made = self.MakeEffects()
        if mode in ('sprite', 'both') or not made:
            for index in range(len(BRAZIERS)):
                self.fireSprites.append(Sprite(self.under, 'flame_00.png', True))
            self.flames = [ASSET + 'flame_%02d.png' % i for i in range(16)]

    def MakeEffects(self):
        """The flame cores now; the fire_camp1 columns each at its own start (Update -> _StartPending)."""
        hall = self.hall
        try:
            if not self._PickInstance():
                return False
            effect.RegisterEffect(FIRE_FX)
            if hall.cfg.get('core'):
                effect.RegisterEffect(CORE_FX)
                for index in range(len(self.fires)):
                    self._Spawn(CORE_FX, index, CORE_SCALE[index], CORE_FX_BASE, (2.0, -3.0)[index])
            if hall.cfg.get('bonelight'):
                effect.RegisterEffect(GLOW_FX)
                self._Spawn(GLOW_FX, 1, 1.0, GLOW_FX_BASE, 0.0)
            now = app.GetTime()
            self.pending = [(now + FIRE_DELAY[index], index) for index in range(len(self.fires))]
            self._StartPending(now)
            self._Reselect()
            return True
        except Exception:
            uir1.TraceFailure('pregame hall fire')
            self.DeleteEffects()
            return False

    def _PickInstance(self):
        """effect.CreateEffect starts at the selected character (and needs one): select one that exists."""
        for slot in range(self.hall.Count()):
            if chr.HasInstance(slot):
                chr.SelectInstance(slot)
                return True
        return False

    def _Reselect(self):
        sel = self.hall.selected
        if sel is not None and sel >= 0 and chr.HasInstance(sel):
            chr.SelectInstance(sel)

    def _Spawn(self, name, index, scale, base, dx):
        """One effect at brazier ``index``: on the ray through the bowl rim at 1/scale of its distance (looks
        ``scale`` x bigger at the same screen point), the effect's own flame height ``base`` taken off, ``dx`` units
        aside (along the screen)."""
        cam = self.hall.camera
        ground, lift = self.fires[index]
        rim = (ground[0], ground[1], lift)
        point = _add(cam.eye, _sub(rim, cam.eye), 1.0 / max(0.05, scale))
        point = _add(point, cam.x, dx)
        idx = effect.CreateEffect(name)
        self.hall.fx.append(idx)
        effect.SetPosition(idx, point[0], point[1], point[2] - base)
        return idx

    def _StartPending(self, now):
        pending = getattr(self, 'pending', [])
        if not pending:
            return
        due = [item for item in pending if item[0] <= now]
        if not due or not self._PickInstance():
            return
        self.pending = [item for item in pending if item[0] > now]
        k = float(self.hall.cfg.get('campscale', 1.0) or 1.0)
        for unused, index in due:
            self._Spawn(FIRE_FX, index, FIRE_SCALE[index] * k, FIRE_FX_BASE, 0.0)
        self._Reselect()

    def DeleteEffects(self):
        self.pending = []
        if effect is None:
            return
        for idx in self.hall.fx:
            try:
                effect.DeleteEffect(idx)
            except Exception:
                pass
        self.hall.fx = []

    # ------------------------------------------------------------------ every frame
    def Update(self, now):
        hall, cam, cfg = self.hall, self.hall.camera, self.hall.cfg
        sc = cam.scale
        self.Parallax(now)
        flick = [Flicker(now, index + 1) for index in range(len(BRAZIERS))]
        if self.ambience is not None:
            self.ambience.Update(now)
        if self.lightning is not None:
            self.lightning.Update(now)          # after the ambience's levels, before the backdrop reads them
        self.backdrop.Update(now, flick)
        if getattr(self, 'emblems', None) is not None:
            self.emblems.Update(now)
        self.PlaceOverlays()
        if self.reflections is not None:
            self.reflections.Update(now)
        # low ground fog drifting slowly sideways along the floor (wraps), shifted with the floor
        fx, fy = cam.Shift(self.depthFloor)
        for i, sprite in enumerate(self.fog):
            if cfg['fog'] <= 0:
                sprite.Hide()
                continue
            speed = (9.0, -6.0, 4.0)[i]
            width = PLATE_W * 1.3 * sc
            x = ((now * speed * sc + i * width / 3.0) % (width + cam.W)) - width / 2.0
            py = self.fogY[i]
            cx, cy = cam.Screen(PLATE_W / 2.0, py)
            sprite.Place(x + fx, cy + fy, width, (120.0, 140.0, 170.0)[i] * sc, (0.62, 0.50, 0.48),
                         cfg['fog'] * (0.8 + 0.2 * math.sin(now * 0.21 + i * 1.7)))
        if hall.fx and effect is not None:
            try:
                self._StartPending(now)
                effect.Update()
            except Exception:
                uir1.TraceFailure('pregame hall fire update')
                self.DeleteEffects()
        # portal haze: two clouds drifting up slowly, breathing out of phase (never a full-screen flicker)
        x0, y0, x1, y1 = PORTAL
        for i, cloud in enumerate(self.haze if not self.v3 else ()):
            ph = now * (0.09 + i * 0.05) + i * 2.1
            cx, cy = cam.Screen((x0 + x1) / 2.0 + 14 * math.sin(ph * 1.3), (y0 + y1) / 2.0 - 26 * math.sin(ph) - 20 * i)
            wx, wy = cam.Shift(self.depthWall)
            cloud.Place(cx + wx, cy + wy, (x1 - x0) * sc * (1.05 + 0.05 * i), (y1 - y0) * sc * 1.05, (0.85, 0.10, 0.07),
                        cfg['haze'] * (0.85 + 0.4 * math.sin(now * (0.55 + 0.2 * i) + i)))
        cx, cy = cam.Screen((x0 + x1) / 2.0, y1 + 30)
        wx, wy = cam.Shift(self.depthWall)
        if self.v3:
            # owner 10. 10.: no red oval inside the gate - the portal's light spills over the threshold instead
            for cloud in self.haze:
                cloud.Hide()
            amb = self.ambience
            beat, hp = (amb.pulse, amb.portal) if amb is not None else (0.0, 0.0)
            cx, cy = cam.Screen(960.0, V3_HORIZON + 10.0)
            fx_, fy_ = cam.Shift(self.depthFloor)
            self.portalPool.Place(cx + fx_, cy + fy_, 760 * sc, 70 * sc, RED,
                                  cfg.get('threshold', 0.14) * (0.8 + 0.4 * beat) * (1.0 + 0.6 * hp))
        else:
            self.portalPool.Place(cx + wx, cy + wy, 520 * sc, 120 * sc, RED, 0.16 + 0.03 * math.sin(now * 0.4))
        # the fires: light glow on the wall and the floor, sparks, smoke
        for index, (ground, lift) in enumerate(self.fires):
            f = flick[index]
            rim = cam.Project((ground[0], ground[1], lift))
            foot = cam.Project(ground)
            if rim is None or foot is None:
                continue
            k = cam.PixelsPerUnit(ground)
            self.fireGlow[index].Place(rim[0], rim[1] - 20 * sc, 420 * sc * (0.96 + 0.06 * f), 420 * sc * (0.96 + 0.06 * f),
                                       (1.0, 0.55, 0.22), cfg['glow'] * f)
            self.firePool[index].Place(foot[0], foot[1] + 8 * sc, 360 * sc, 74 * sc, (1.0, 0.5, 0.2), cfg['spill'] * f)
            if self.flames:
                frame = self.flames[int(now * 18 + index * 7) % len(self.flames)]
                sprite = self.fireSprites[index]
                sprite.LoadImage(frame)
                sprite.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
                fh = 120 * sc * (0.94 + 0.08 * f)
                sprite.Place(rim[0], rim[1] - fh / 2 + 6 * sc, fh * 0.5, fh, (1.0, 1.0, 1.0), 0.95)
        for spark in self.sparks:
            b, sprite, t0, life, drift, size = spark
            ground, lift = self.fires[b]
            rim = cam.Project((ground[0], ground[1], lift))
            if rim is None:
                continue
            t = ((now + t0) % life) / life
            x = rim[0] + (drift * 14 + 9 * math.sin(now * 3 + t0 * 5)) * t * sc
            y = rim[1] - (20 + 170 * t) * sc
            sprite.Place(x, y, 5 * size * sc, 5 * size * sc, (1.0, 0.62, 0.25), (1.0 - t) * cfg['sparks'] * (0.6 + 0.4 * math.sin(now * 23 + t0)))
        for puff in self.smoke:
            b, sprite, t0, life, drift = puff
            ground, lift = self.fires[b]
            rim = cam.Project((ground[0], ground[1], lift))
            if rim is None:
                continue
            t = ((now + t0) % life) / life
            size = (40 + 120 * t) * sc
            sprite.Place(rim[0] + drift * 30 * t * sc, rim[1] - (70 + 230 * t) * sc, size, size, (1.0, 1.0, 1.0),
                         cfg['smoke'] * math.sin(math.pi * t))
        # the selection light of every place (crossfade), the hover ring, contact shadows
        count = hall.Count()
        body = hall.cfg['body']
        for slot, place, ground in self.places:
            ground = self.Feet(slot, ground)
            occupied = slot < count
            light = hall.Light(slot, now) if occupied else 0.0
            shadow = cam.Ellipse(ground, 38.0)
            if shadow and occupied:
                c, w, h = shadow
                # the nearer brazier's flicker sways the contact shadow away from it a little
                near = min(range(len(self.fires)), key=lambda i: abs(_dot(_sub(self.fires[i][0], ground), cam.x)))
                side = 1.0 if _dot(_sub(ground, self.fires[near][0]), cam.x) >= 0 else -1.0
                sway = (flick[near] - 1.0) * cfg['shadowsway'] * sc
                lamp = self.LampLight(ground, now)[0] if self.v3 else 0.0
                # under a lantern (light from above) the contact shadow is short and dense
                self.shadow[slot].Place(c[0] + side * sway, c[1], w * (1.0 + (flick[near] - 1.0) * 0.12) * (1.0 - 0.15 * lamp),
                                        max(h, w * 0.18), (1.0, 1.0, 1.0),
                                        min(1.0, cfg.get('contact', 0.78) * (1.0 + 0.15 * lamp)))
                # the tight dark core right under the soles (ambient occlusion): what makes the feet touch
                core = cam.Ellipse(ground, 16.0)
                if core:
                    self.contact[slot].Place(core[0][0], core[0][1], core[1], max(core[2], core[1] * 0.2),
                                             (1.0, 1.0, 1.0), cfg.get('contact', 0.78))
                head = cam.Project((ground[0], ground[1], body))
                if head and cfg.get('charmirror', 0) > 0:
                    # a dark smear of the figure mirrored on the glossy floor, fading downwards
                    bh = c[1] - head[1]
                    # the gate behind throws a long faint shadow towards the camera; under a lantern it is short
                    long_ = 1.0 - 0.6 * lamp
                    self.mirror[slot].Place(c[0], c[1] + bh * 0.16 * long_, bh * 0.2, bh * 0.34 * long_, (0.0, 0.0, 0.0),
                                            cfg['charmirror'])
                else:
                    self.mirror[slot].Hide()
            else:
                self.shadow[slot].Hide()
                self.contact[slot].Hide()
                self.mirror[slot].Hide()
            pool = cam.Ellipse(ground, 95.0)
            ring = cam.Ellipse(ground, 58.0)
            head = cam.Project((ground[0], ground[1], body))
            feet = cam.Project(ground)
            if pool and occupied:
                c, w, h = pool
                self.pool[slot].Place(c[0], c[1], w, h, WARM, 0.42 * light)
            else:
                self.pool[slot].Hide()
            if ring and occupied:
                c, w, h = ring
                pulse = 0.88 + 0.12 * math.sin(now * 1.6)
                drawn = bool(cfg.get('runecircle', 0))          # owner 11. 10.: "ten kruh na zemi se mi nelíbí"
                if drawn:
                    self.ring[slot].Place(c[0], c[1], w, h, RED, light * pulse)
                else:
                    self.ring[slot].Hide()
                # everyone stands on a dark dais with a dormant rune ring; the selection wakes it
                dais = cam.Ellipse(ground, 74.0)
                if dais:
                    self.dais[slot].Place(dais[0][0], dais[0][1], dais[1], dais[2], (1.0, 1.0, 1.0), cfg.get('dais', 0.35))
                if drawn:
                    self.runeBase[slot].Place(c[0], c[1], w, h, (0.42, 0.06, 0.05), cfg.get('runebase', 0.22) * (1.0 - light))
                else:
                    self.runeBase[slot].Hide()
                beat = self.ambience.pulse if self.ambience is not None else 0.5 + 0.5 * math.sin(now * 1.5)
                glow = cam.Ellipse(ground, 105.0)
                if glow:
                    # a soft elliptical light pool in perspective, breathing with the gate's heartbeat
                    self.glowDisc[slot].Place(glow[0][0], glow[0][1], glow[1], glow[2] * 1.15, (1.0, 0.16, 0.08),
                                              cfg.get('runeglow', 0.35) * light * (0.8 + 0.3 * beat))
                core = cam.Ellipse(ground, 46.0)
                if core and light > 0.01:
                    self.glowCore[slot].Place(core[0][0], core[0][1], core[1], core[2] * 1.2, (1.0, 0.36, 0.16),
                                              0.24 * light * (0.85 + 0.3 * beat))
                    # the glossy floor reflects it as a tall soft streak in front of the feet
                    self.sheen[slot].Place(core[0][0], core[0][1] + core[1] * 0.42, core[1] * 0.42, core[1] * 1.0,
                                           (1.0, 0.22, 0.1), 0.13 * light * (0.85 + 0.3 * beat))
                else:
                    self.glowCore[slot].Hide()
                    self.sheen[slot].Hide()
                # a slow ripple running out of the ring every 3.2 s (selected only)
                rt = (now % 3.2) / 3.2
                rip = cam.Ellipse(ground, 58.0 + 40.0 * rt)
                if rip and light > 0.01 and drawn:
                    self.ripple[slot].Place(rip[0][0], rip[0][1], rip[1], rip[2], RED,
                                            cfg.get('ripple', 0.45) * light * (1.0 - rt) * Smooth(rt / 0.1))
                else:
                    self.ripple[slot].Hide()
            else:
                self.ring[slot].Hide()
                for group in (self.dais, self.runeBase, self.glowDisc, self.ripple, self.glowCore, self.sheen):
                    group[slot].Hide()
            if (ring and cfg.get('runecircle', 0) and slot < hall.rows and hall.hover == slot
                    and not (occupied and slot == hall.selected)):
                c, w, h = ring
                self.hoverRing[slot].Place(c[0], c[1], w, h, (0.75, 0.72, 0.70), 0.55)
            else:
                self.hoverRing[slot].Hide()
            if head and feet and occupied and light > 0.003:
                bh = feet[1] - head[1]
                self.back[slot].Place(feet[0], head[1] + bh * 0.42, bh * 0.62, bh * 1.12, RED, 0.38 * light)
                top = 0.0
                self.beam[slot].Place(feet[0], (top + feet[1]) / 2.0, bh * 0.95, feet[1] - top + bh * 0.05, WARM,
                                      0.11 * light)
            else:
                self.back[slot].Hide()
                self.beam[slot].Hide()
            label = self.labels[slot]
            if occupied:
                P.SetColor(label, T.IVORY if slot == hall.selected else T.INK_DIM)
                if self.nameplates is not None:
                    label.Hide()            # the nameplates speak for the characters
        # dust in the light shaft of the selection
        sel = hall.selected
        if 0 <= sel < count:
            ground = self.Feet(sel, self.places[sel][2])
            head = cam.Project((ground[0], ground[1], body * 1.15))
            feet = cam.Project(ground)
            light = hall.Light(sel, now)
            if head and feet:
                bh = feet[1] - head[1]
                for mote in self.dust:
                    sprite, u, v, speed, ph, size = mote
                    vv = (v - now * speed) % 1.0
                    uu = u + 0.08 * math.sin(now * 0.3 + ph)
                    x = feet[0] + (uu - 0.5) * bh * 0.55 * (0.4 + 0.6 * vv)
                    y = head[1] - bh * 0.25 + vv * bh * 1.2
                    tw = 0.5 + 0.5 * math.sin(now * 1.7 + ph * 3)
                    sprite.Place(x, y, 4 * size * sc, 4 * size * sc, WARM, cfg['dust'] * light * tw * math.sin(math.pi * vv))
        else:
            for mote in self.dust:
                mote[0].Hide()
        self.Motes(now)
        if self.nameplates is not None:
            self.nameplates.Update(now)

    def Motes(self, now):
        """Sparks rising from the selected one's rune ring (real 3D points on its circle, so they sit in the scene)."""
        hall, cam, cfg = self.hall, self.hall.camera, self.hall.cfg
        sel, count = hall.selected, hall.Count()
        if not (0 <= sel < count) or cfg.get('motes', 0) <= 0:
            for mote in self.motes:
                mote[0].Hide()
            return
        ground = self.Feet(sel, self.places[sel][2])
        light = hall.Light(sel, now)
        sc = cam.scale
        for i, (sprite, u0, speed) in enumerate(self.motes):
            t = (u0 + now * 0.22 * speed) % 1.0
            cycle = math.floor(u0 + now * 0.22 * speed)
            a = 6.2832 * _hash(int(cycle) * 10 + i, 17)
            r = 58.0
            p = _add(_add(ground, cam.x0, r * math.cos(a)), cam.back, r * math.sin(a))
            q = cam.Project((p[0], p[1], 6.0 + 150.0 * t))
            if q is None:
                sprite.Hide()
                continue
            d = (3.5 - 1.5 * t) * sc * (1.0 + 0.3 * math.sin(now * 5.0 + i))
            alpha = cfg['motes'] * light * Smooth(t / 0.1) * (1.0 - t) * (0.6 + 0.4 * math.sin(now * 7.0 + i * 2.0))
            sprite.Place(q[0] + 4.0 * math.sin(now * 1.3 + i) * sc, q[1], d, d, (1.0, 0.32, 0.14), alpha)
        # the dimming / warm key of the 3D characters
        self.LightCharacters(now)

    def LampLight(self, ground, now):
        """(lantern, gate, flicker) for a character standing on ``ground``: how much it stands under the nearer
        lantern (1 = right under it), how near the gate's axis, and that lantern's flame flicker (the same noise as the
        lantern sprites, so the light on the character breathes with the flame)."""
        cam = self.hall.camera
        p = cam.Project(ground)
        if p is None or not self.v3:
            return 0.0, 0.0, 1.0
        best, side = None, 0
        for i, (lx, ly) in enumerate(V3_LANTERNS):
            sx = cam.Screen(lx, ly)[0]
            d = abs(p[0] - sx)
            if best is None or d < best:
                best, side = d, i
        lamp = max(0.0, min(1.0, 1.0 - best / (0.14 * cam.W)))
        gate = max(0.0, min(1.0, 1.0 - abs(p[0] - cam.W / 2.0) / (0.36 * cam.W)))
        return lamp, gate, Flicker(now, 11 + side)

    def LightCharacters(self, now):
        """'stock' (Renderer.LightPasses lights each like the stock select): modulate only - the selected at sel (1 =
        exactly the stock look), the others at dim3 (a little darker, never washed out or see-through); the
        braziers' bounce warms the red channel. 'add' = the old neutral fill (owner 10. 10. afternoon: washed out)."""
        hall, cfg = self.hall, self.hall.cfg
        count, body = hall.Count(), cfg['body']
        stock = cfg.get('charlight') == 'stock' and self.reflections is None
        dim, warm = cfg['dim'], cfg['warm']
        for slot in range(count):
            if not chr.HasInstance(slot):
                continue
            light = hall.Light(slot, now)
            ground = self.places[slot][2]
            point = (ground[0], ground[1], ground[2] + body * 0.55)
            bounce = FireBounce(point, self.fires, now, cfg.get('chartint', 0.08))
            try:
                plain = stock and self.LightScale()[0] >= 0.99
                tint = Tint(cfg)
                mode = str(cfg.get('othermode', 'mod'))
                if plain and light < 0.5 and mode == 'normal':
                    chr.testRestoreRenderMode(slot)
                elif plain and light < 0.5 and mode == 'mod':
                    # owner 11. 10.: "aspoň trochu normálně", "trochu červené", not yellow: the stock look, a little
                    # darker than the selected, the hall's red tint - no add colour (that flattens the textures)
                    k = float(cfg.get('dim3', 0.8))
                    if ARC_OF_SLOT[slot] in (0, 4):
                        k = float(cfg.get('dimouter', 0.68))      # "v tom rohu ještě trochu víc"
                    chr.testSetModulateRenderModeRGB(slot, k * tint[0], k * tint[1], k * tint[2])
                elif plain and light < 0.5:
                    # 1 : 1 world (the sash): the others stand outside the stock rig's 5 m. Owner 11. 10. "a jsou pod
                    # lampou": the ones under a lantern take its warm light, flickering with its flame; the inner
                    # ones the red of the gate; a little neutral fill for all (one add colour per character - the
                    # engine has one light rig and moves positions only on its update)
                    lamp, gate, fl = self.LampLight(ground, now)
                    lk = float(cfg.get('lampfill', 0.26)) * lamp * fl
                    gk = float(cfg.get('gatefill', 0.10)) * gate
                    n = float(cfg.get('otherfill', 0.05))
                    # owner 11. 10. "to světlo moc nefunguje": 0.26 burned them flat - the add is a constant (no
                    # shading), so only a gentle warm lift; the volume must come from the rig (rigshift)
                    chr.SetAddRenderMode(slot, min(0.2, n + lk * 1.0 + gk * 0.9 + bounce),
                                         min(0.2, n * 0.96 + lk * 0.70 + gk * 0.2 + bounce * 0.48),
                                         min(0.2, n * 0.92 + lk * 0.45 + gk * 0.12 + bounce * 0.16))
                elif stock:
                    sel, low = float(cfg.get('sel', 1.0)), float(cfg.get('dim3', 0.8))
                    k = low + (sel - low) * light
                    # a touch of the portal's red heartbeat on everyone (modulate: green / blue dip, red stays)
                    pt = float(cfg.get('portaltint', 0.0)) * (self.ambience.pulse if self.ambience is not None else 0.0)
                    chr.testSetModulateRenderModeRGB(slot, min(1.0, (k + bounce) * tint[0]),
                                                     min(1.0, (k * (1.0 - 0.02 * light - pt) + bounce * 0.48) * tint[1]),
                                                     min(1.0, (k * (1.0 - 0.05 * light - 1.3 * pt) + bounce * 0.16) * tint[2]))
                else:
                    # owner 10. 10.: the models read too dark - every character gets a neutral fill light (add mode);
                    # the unselected get less of it (dim), the selected the full fill + the warm key
                    fill = cfg.get('fill', 0.22)
                    f = fill * (dim + (1.0 - dim) * light)
                    a = warm * light
                    chr.SetAddRenderMode(slot, f + a * WARM[0] + bounce, f + a * WARM[1] * 0.85 + bounce * 0.48,
                                         f + a * WARM[2] * 0.6 + bounce * 0.16)
            except Exception:
                pass

    def Destroy(self):
        self.DeleteEffects()
        if getattr(self, 'reflections', None) is not None:
            self.reflections.Destroy()
        for root in self.roots:
            root.Hide()
        if getattr(self, 'background', None) is not None:
            self.background.Show()
        if getattr(self, 'renderer', None) is not None:
            self.renderer.Hide()
            self.renderer.hall = None
        for slot in range(len(ARC)):
            try:
                if chr.HasInstance(slot):
                    chr.testRestoreRenderMode(slot)
                    chr.SelectInstance(slot)
                    chr.SetScale(1.0, 1.0, 1.0)
            except Exception:
                pass
        try:
            import introbackground
            introbackground.apply_background(self.background, wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        except Exception:
            pass



# =========================================================================== the banners' emblems (set a)
# owner 11. 10.: "logo A na rudých vlajkách udělej nějak interaktivní" - the emblems painted into L0 as their own
# light layers (tools/pregame_banner_emblem.py): plate px (x, y, w, h) of each, = the tool's BOXES
EMBLEM_BOXES = {'L': (520, 131, 101, 101), 'R': (1300, 131, 99, 101)}
EMBLEM_GLOW_PAD = 0.35
EMBLEM_FRAMES = 12


class EmblemHit(uir1.Interactive):
    """The mouse area of one banner's emblem (a little larger than it): hover heats it, a click flashes it."""

    def __init__(self, parent, emblem, side):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.emblem, self.side = emblem, side
        self.Show()

    def click(self):
        self.emblem.Flash(self.side)


class BannerEmblems(object):
    """The "A" on both red banners: at rest it breathes - a slow red glow and a faint lift of its own shape; under the
    mouse it heats (the shape glows warm, the glow grows), a band of light sweeps over it every 1.8 s and sparks
    rise from it; a click: a short bright flash and a sound. Its own sprites over L0 at the wall's depth (the wall
    never moves - the parallax shift of the wall still applies), the mouse areas in the scene's top root."""

    def __init__(self, scene):
        self.scene, self.hall = scene, scene.hall
        self.rnd = random.Random(2026)
        self.sides = {}
        for side in ('L', 'R'):
            item = {
                'glow': Sprite(scene.under, 'emblem/glow_%s.png' % side, True),
                'shape': Sprite(scene.under, 'emblem/mask_%s.png' % side, True),
                'wave': Sprite(scene.under, 'emblem/wave_%s_00.png' % side, True),
                'sparks': [[Sprite(scene.under, 'dot.png', True), None, 0.0, 0.0, 0.0] for unused in range(10)],
                'hit': EmblemHit(scene.over, self, side),
                'heat': 0.0, 'flash': 0.0, 'waveAt': None, 'frame': None,
                'phase': 0.0 if side == 'L' else 2.1,
            }
            for key in ('glow', 'shape', 'wave'):
                item[key].Hide()
            for spark in item['sparks']:
                spark[0].Hide()
            self.sides[side] = item
        self.last = None

    def Flash(self, side):
        self.sides[side]['flash'] = 1.0
        try:
            import snd
            snd.PlaySound('sound/ui/click.wav')
        except Exception:
            pass

    def Update(self, now):
        cam = self.hall.camera
        dt = 0.0 if self.last is None else max(0.0, min(0.1, now - self.last))
        self.last = now
        depth = self.scene.backdrop.depth['wall']
        sx, sy = cam.Shift(depth)
        sc = cam.scale
        hidden = getattr(self.hall, 'uiHidden', False)
        for side, item in self.sides.items():
            x, y, w, h = EMBLEM_BOXES[side]
            left, top = cam.Screen(x, y)
            left, top = left + sx, top + sy
            ww, hh = w * sc, h * sc
            cx, cy = left + ww / 2.0, top + hh / 2.0
            hit = item['hit']
            hit.SetPosition(int(left - 20 * sc), int(top - 40 * sc))
            hit.SetSize(int(ww + 40 * sc), int(hh + 100 * sc))
            hit.Hide() if hidden else hit.Show()
            target = 1.0 if (hit.hovered and not hidden) else 0.0
            rate = dt / (0.25 if target > item['heat'] else 0.6)
            item['heat'] = target if abs(target - item['heat']) <= rate else \
                item['heat'] + (rate if target > item['heat'] else -rate)
            item['flash'] = max(0.0, item['flash'] - dt / 0.5)
            heat, flash = item['heat'], item['flash']
            breath = 0.5 + 0.5 * math.sin(now * 1.3 + item['phase'])
            gw, gh = ww * (1 + 2 * EMBLEM_GLOW_PAD), hh * (1 + 2 * EMBLEM_GLOW_PAD)
            item['glow'].Place(cx, cy, gw * (1.0 + 0.15 * flash), gh * (1.0 + 0.15 * flash), RED,
                               min(1.0, 0.10 + 0.08 * breath + 0.45 * heat + 0.7 * flash))
            item['shape'].Place(cx, cy, ww, hh, (1.0, 0.45 + 0.4 * flash, 0.30 + 0.5 * flash),
                                min(1.0, 0.05 + 0.05 * breath + 0.55 * heat + 0.9 * flash))
            # the band of light: every 1.8 s while it is hot
            if heat > 0.5 and (item['waveAt'] is None or now - item['waveAt'] > 1.8):
                item['waveAt'] = now
            t = (now - item['waveAt']) / 0.9 if item['waveAt'] is not None else 2.0
            if 0.0 <= t < 1.0 and heat > 0.05:
                frame = min(EMBLEM_FRAMES - 1, int(t * EMBLEM_FRAMES))
                if frame != item['frame']:
                    item['frame'] = frame
                    item['wave'].LoadImage(ASSET + 'emblem/wave_%s_%02d.png' % (side, frame))
                    item['wave'].iw, item['wave'].ih = max(1, item['wave'].GetWidth()), max(1, item['wave'].GetHeight())
                    item['wave'].SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
                item['wave'].Place(cx, cy, ww, hh, (1.0, 0.85, 0.70), min(1.0, 0.9 * heat))
            else:
                item['wave'].Hide()
            # sparks rising from it while it is hot
            for spark in item['sparks']:
                sprite, t0, ox, speed, size = spark
                if t0 is None or now - t0 > 1.1:
                    if heat > 0.3 and self.rnd.random() < dt * 6.0:
                        spark[1:] = [now, self.rnd.uniform(-0.4, 0.4), self.rnd.uniform(40, 80), self.rnd.uniform(3, 6)]
                    else:
                        spark[1] = None
                        sprite.Hide()
                        continue
                sprite, t0, ox, speed, size = spark
                u = (now - t0) / 1.1
                sprite.Place(cx + ox * ww + 8 * sc * math.sin(now * 5 + ox * 9), cy - u * speed * sc,
                             size * sc, size * sc, (1.0, 0.55, 0.35), (1.0 - u) * (0.4 + 0.6 * heat))

    def Hide(self):
        for item in self.sides.values():
            for key in ('glow', 'shape', 'wave'):
                item[key].Hide()
            for spark in item['sparks']:
                spark[0].Hide()
            item['hit'].Hide()

# =========================================================================== the bottom panel (R1)
BUTTON_SETS = ('obsidian', 'kamen', 'cepel', 'ram')
# the dragons' eyes of a set (x, y fractions of the button; tools/pregame_proto_tlacitka.py prints them): they glow,
# arc on hover and throw the lightning of a click
EYES = {('obsidian', 'hrat'): ((0.170, 0.412), (0.827, 0.421)),
        ('obsidian', 'maly'): ((0.168, 0.406), (0.826, 0.413))}
LABEL_Y = {('ram', 'hrat'): 0.42}
# owner 11. 10.: the buttons bigger (+35 %, then +18 %), the captions bigger. THE one place for the captions: a font
# per kind here (TextLine over the art); a set whose art has the text baked in lists its kinds in BAKED_TEXT
BUTTON_W = {'hrat': 405, 'maly': 224, 'exit': 180}
BUTTON_FONT = {'hrat': 40, 'maly': 21, 'exit': 18}
# owner 11. 10.: font A8 ("dýchající záře") baked into the button art: btn/<set>/text_<word>_calm.png (the whole
# button, the caption with a soft glow) and _glow.png (strong glow, hover); crossfaded, breathing while hovered.
# A set listed here draws these instead of its state images + the TextLine
BAKED_TEXT = {'obsidian': True}
# owner 11. 10. ("moc tmavá, splývají s podlahou" -> "nech ten, co je šedý"): the controls are the grey obsidian of
# tools/pregame_button_looks.py; with it brighter labels and a light frame round the creation's name field
TEXT_DIM, TEXT_MUTED = 0xFFD8CFC8, 0xFFB8ACA6
FIELD_EDGE = (0x9A908C, 0.75)
TEXT_SLUG = {'HRÁT': 'hrat', 'VYTVOŘIT': 'vytvorit', 'SMAZAT': 'smazat', 'UKONČIT': 'ukoncit'}       # the caption's row in the art (the winged frame's panel sits high)


class ImageButton(uir1.Interactive):
    """A button from the generated art (owner 11. 10.: "chci actual rozhraní"; ui/.../pregame_proto/btn/<set>/):
    one image per state (normal / hover / pressed / disabled), scaled to the button, the caption a Cinzel line with
    the engine outline over it (1 px lower while pressed). kind 'hrat' = HRÁT, 'maly' = the small ones."""

    @staticmethod
    def Path(name, kind, state):
        return ASSET + 'btn/%s/%s_%s.png' % (name, kind, state)

    def __init__(self, parent, kind, text, font, event, name, slug=None):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.kind, self.set, self.font = kind, name, font
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        try:
            self.image.SetLinearFiltering(True)
        except Exception:
            pass
        self.shown = None
        # the button's own red (crack / inlay / gems) as light: additive, driven by ButtonFX (hover, click)
        self.veins = ui.ExpandedImageBox()
        self.veins.SetParent(self)
        self.veins.AddFlag('not_pick')
        self.veinsKey = None
        self.veins.Hide()
        # the baked caption (BAKED_TEXT): calm under, glow over it, the glow's alpha eased / breathing (Breathe)
        self.word = slug or TEXT_SLUG.get(text)
        self.glowImage = ui.ExpandedImageBox()
        self.glowImage.SetParent(self)
        self.glowImage.AddFlag('not_pick')
        try:
            self.glowImage.SetLinearFiltering(True)
        except Exception:
            pass
        self.glowImage.Hide()
        self.glow, self.glowAt, self.glowKey = 0.0, None, None
        self.label = P.Text(self, text, 0, 0, font, T.IVORY, align='center', valign='center')
        try:
            self.label.SetOutline(True)
        except Exception:
            pass
        self.w, self.h = 10, 10
        self.callback = event
        self.image.Show()
        self.Show()
        self.paint()

    def SetSet(self, name):
        self.set, self.shown, self.veinsKey, self.glowKey = name, None, None, None
        self.paint()

    def Aspect(self):
        """width / height of this set's art (the winged frame is taller than the blade)."""
        probe = ui.ExpandedImageBox()
        try:
            probe.LoadImage(self.Path(self.set, self.kind, 'normal'))
            w, h = probe.GetWidth(), probe.GetHeight()
        except Exception:
            w, h = 0, 0
        return (float(w) / h) if (w and h) else 3.2

    def SetText(self, text):
        self.label.SetText(text)

    def click(self):
        # the effect starts at the mouse, the action goes at once (HRÁT never waits for it)
        fx = getattr(self, 'fx', None)
        if fx is not None:
            try:
                try:
                    point = wndMgr.GetMousePosition()
                except Exception:
                    point = None
                fx.Trigger(self, self.kind == 'hrat', point)
            except Exception:
                pass
        if self.callback:
            self.callback()

    def SetVeins(self, alpha):
        """The red light of the button itself (0 = off)."""
        if alpha <= 0.01:
            self.veins.Hide()
            return
        key = (self.set, self.w, self.h)
        if key != self.veinsKey:
            self.veinsKey = key
            self.veins.LoadImage(self.Path(self.set, self.kind, 'veins'))
            try:
                self.veins.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
            except Exception:
                pass
            iw, ih = max(1, self.veins.GetWidth()), max(1, self.veins.GetHeight())
            self.veins.SetScale(float(self.w) / iw, float(self.h) / ih)
            self.veins.SetPosition(0, 0)
        SetColor(self.veins, (1.0, 1.0, 1.0), min(1.0, alpha))
        self.veins.Show()

    def Resize(self, w, h):
        self.SetSize(int(w), int(h))
        self.w, self.h = int(w), int(h)
        self.shown = None
        self.paint()

    def TextPath(self, state):
        return ASSET + 'btn/%s/text_%s_%s.png' % (self.set, self.word, state)

    def Baked(self):
        return bool(BAKED_TEXT.get(self.set)) and self.word is not None and Exists(self.TextPath('calm'))

    def Breathe(self, now):
        """The A8 glow: up in ~0.18 s on hover, breathing 0.8-1.0 while hovered, down in ~0.3 s."""
        if not self.Baked():
            self.glowImage.Hide()
            return
        dt = 0.0 if self.glowAt is None else max(0.0, min(0.1, now - self.glowAt))
        self.glowAt = now
        state = self.state() if self.enabled else 'disabled'
        target = (0.9 + 0.1 * math.sin(now * 3.2)) if state in ('hover', 'pressed') else 0.0
        rate = 1.0 / (0.18 if target > self.glow else 0.3)
        step = rate * dt
        self.glow = target if abs(target - self.glow) <= step else self.glow + step * (1 if target > self.glow else -1)
        key = (self.set, self.word, self.w, self.h)
        if key != self.glowKey:
            self.glowKey = key
            self.glowPath = self.TextPath('glow')
            self.glowImage.LoadImage(self.glowPath)
            iw, ih = max(1, self.glowImage.GetWidth()), max(1, self.glowImage.GetHeight())
            self.glowImage.SetScale(float(self.w) / iw, float(self.h) / ih)
        self.glowImage.SetPosition(0, 1 if state == 'pressed' else 0)
        if self.glow <= 0.01:
            self.glowImage.Hide()
        else:
            SetColor(self.glowImage, (1.0, 1.0, 1.0), min(1.0, self.glow))
            self.glowImage.Show()

    def paint(self):
        state = self.state()
        image = {'disabled': 'disabled', 'pressed': 'pressed', 'hover': 'hover'}.get(state, 'normal')
        if self.Baked():
            # the caption is in the art: always the calm image (the hover is the glow layer, Breathe)
            key = (self.set, 'text', self.word, self.w, self.h, state == 'pressed')
            if key != self.shown:
                self.shown = key
                self.imagePath = self.TextPath('calm')
                self.image.LoadImage(self.imagePath)
                iw, ih = max(1, self.image.GetWidth()), max(1, self.image.GetHeight())
                self.image.SetScale(float(self.w) / iw, float(self.h) / ih)
                self.image.SetPosition(0, 1 if state == 'pressed' else 0)
            SetColor(self.image, (1.0, 1.0, 1.0) if self.enabled else (0.45, 0.42, 0.42), 1.0)
            self.label.Hide()
            return
        key = (self.set, image, self.w, self.h)
        if key != self.shown:
            self.shown = key
            self.image.LoadImage(self.Path(self.set, self.kind, image))
            iw, ih = max(1, self.image.GetWidth()), max(1, self.image.GetHeight())
            self.image.SetScale(float(self.w) / iw, float(self.h) / ih)
            self.image.SetPosition(0, 0)
        colour = T.DISABLED if not self.enabled else (T.IVORY if state in ('hover', 'pressed') else 0xFFE6DED2)
        P.SetColor(self.label, colour)
        row = int(self.h * LABEL_Y.get((self.set, self.kind), 0.5))
        P.Move(self.label, self.w // 2, row + (1 if state == 'pressed' else 0))
        self.label.Show()


def BoltPhase(order, n, t, grow=0.15, hold=0.06, fade=0.45):
    """(reveal, alpha) of the segment ``order`` of an n-step bolt at age t (owner 11. 10. "plynuleji"): it grows
    from the start to the tip in ``grow`` s (a segment half-grown is drawn half long), holds, then fades segment by
    segment - the tips first - over ``fade`` s (the glow lingers)."""
    n = max(1, n)
    reveal = max(0.0, min(1.0, t / max(0.01, grow) * n - order))
    start = grow + hold + (n - 1 - order) / float(n) * 0.12
    return reveal, 1.0 - Smooth((t - start) / max(0.01, fade))


class ButtonFX(object):
    """The click effect of the hall buttons (owner 11. 10.: "cool efekt na kliknutí", "kdyby ty, co mají červenou
    prasklinu ... zářilo z toho místa", "jako v cechovním portálu"). btnfx=crack (default) | portal | 0.
      crack   from the point clicked: a red glow, the button's own red (the stone's crack, the blade's inlay, the
              frame's gems; btn/<set>/<kind>_veins.png) flares up through the button, a soft wave runs out of the
              point and sparks fly from it like the hall's embers;
      portal  the guild portal's language: a red spiral spinning out of the point, a burning ring (the portal's
              flame rim) widening from it, a glow and sparks.
    HRÁT gets the full effect, the small buttons a smaller one. Hover: the button's own red glows faintly and
    flickers. Drawn over the panel, driven by Hall.Update; the action itself never waits for it."""

    SPARKS = 16

    def __init__(self, panel, mode):
        self.panel, self.mode = panel, mode
        root = panel.root
        self.spot = Sprite(root, 'glow.png', True)
        self.wave = Sprite(root, 'pool.png', True)
        self.swirl = Sprite(root, 'btn/fx/swirl.png', True)
        self.swirl.Pivot()
        self.ring = Sprite(root, 'btn/fx/ring_00.png', True)
        rnd = random.Random(808)
        self.sparks = [[Sprite(root, 'btn/fx/spark.png', True), rnd.uniform(0, 6.2832), rnd.uniform(0.5, 1.0),
                        rnd.uniform(0.45, 0.8), rnd.uniform(0.7, 1.3)] for unused in range(self.SPARKS)]
        # the obsidian dragons (owner 11. 10. "ty lightning efekty"): the eyes glow, arc on hover, throw lightning
        self.eyes = [Sprite(root, 'glow.png', True) for unused in range(8)]
        self.boltCore = [Sprite(root, 'dot.png', True) for unused in range(48)]
        self.boltGlow = [Sprite(root, 'dot.png', True) for unused in range(48)]
        for sprite in self.boltCore + self.boltGlow:
            sprite.Pivot()
        self.rnd = random.Random(4242)
        self.arc = None             # the hover arc between the eyes: (button, start, path)
        self.nextArc = 0.0
        self.bolts = []             # the click lightning: paths from the eyes to the point
        for sprite in self.Sprites():
            sprite.Hide()
        self.active = None          # (button, big, start, point)
        self.buttons = []

    def Sprites(self):
        return ([self.spot, self.wave, self.swirl, self.ring] + [p[0] for p in self.sparks] + self.eyes
                + self.boltCore + self.boltGlow)

    @staticmethod
    def Eyes(button):
        eyes = EYES.get((button.set, button.kind))
        if not eyes:
            return None
        x, y = button.GetGlobalPosition()
        return [(x + fx * button.w, y + fy * button.h) for fx, fy in eyes]

    def Jagged(self, a, b, n, amp):
        """A jagged path a -> b (screen px), like the bolts behind the gate: n steps, sideways jitter."""
        (ax, ay), (bx, by) = a, b
        dx, dy = bx - ax, by - ay
        ln = math.sqrt(dx * dx + dy * dy) or 1.0
        nx, ny = -dy / ln, dx / ln
        pts = [a]
        for i in range(1, n):
            t = float(i) / n
            off = self.rnd.uniform(-amp, amp) * math.sin(math.pi * t)
            pts.append((ax + dx * t + nx * off, ay + dy * t + ny * off))
        pts.append(b)
        return pts

    def Bolt(self, a, b, n, amp):
        """A bolt as segments (p0, p1, order, weight): the jagged main path + 1-2 short branches near its end that
        run out and fade."""
        main = self.Jagged(a, b, n, amp)
        segs = [(p0, p1, i, 1.0) for i, (p0, p1) in enumerate(zip(main, main[1:]))]
        for unused in range(self.rnd.randint(1, 2)):
            i = self.rnd.randint(max(1, n // 2), n - 1)
            bx, by = main[i]
            ang = math.atan2(main[i + 1][1] - main[i][1], main[i + 1][0] - main[i][0]) + \
                self.rnd.choice((-1, 1)) * self.rnd.uniform(0.5, 0.9)
            for k in range(self.rnd.randint(2, 3)):
                ln = amp * self.rnd.uniform(1.2, 2.0)
                nx, ny = bx + math.cos(ang) * ln, by + math.sin(ang) * ln
                segs.append(((bx, by), (nx, ny), i + 1 + k, 0.5 - 0.12 * k))
                bx, by = nx, ny
                ang += self.rnd.uniform(-0.5, 0.5)
        return segs

    def DrawSegments(self, segments, t, n, core_w, glow_w, alpha=1.0, phase=None):
        """Draw bolt segments: a white-red core and a wide soft red glow, grown / faded by BoltPhase."""
        used = 0
        for p0, p1, order, weight in segments:
            if used >= len(self.boltCore):
                break
            reveal, a = (phase or BoltPhase)(order, n, t)
            a *= alpha * weight
            if reveal <= 0.0 or a <= 0.01:
                continue
            ex, ey = p0[0] + (p1[0] - p0[0]) * reveal, p0[1] + (p1[1] - p0[1]) * reveal
            dx, dy = ex - p0[0], ey - p0[1]
            length = math.sqrt(dx * dx + dy * dy) + 1.0
            angle = math.degrees(math.atan2(-dx, dy))
            cx, cy = (p0[0] + ex) / 2.0, (p0[1] + ey) / 2.0
            self.boltCore[used].PlaceAngled(cx, cy, max(1, core_w * (0.6 + 0.4 * weight)), length, angle,
                                            (1.0, 0.9, 0.85), min(1.0, a))
            self.boltGlow[used].PlaceAngled(cx, cy, glow_w * (0.6 + 0.4 * weight), length * 1.15, angle,
                                            (1.0, 0.14, 0.06), min(0.75, 0.6 * a))
            used += 1
        return used

    def UpdateEyes(self, now):
        """Always: the eyes glow softly (flicker). Hover: brighter, and soft smouldering arcs over the frame from one
        eye to the other, each fading in and out (two overlapping). A click (owner 11. 10. "hezčí, plynuleji"): a
        full bolt from each eye to the point clicked - it grows out of the eye in 0.15 s, branches run out near the
        end, everything fades segment by segment with a lingering glow; the impact sparks start when it arrives."""
        g = self.panel.g
        if not self.panel.hall.cfg.get('eyefx', 0):
            # owner 11. 10.: the eyes stay as they are in the art - no glow, no arcs, no bolts
            for sprite in self.eyes + self.boltCore + self.boltGlow:
                sprite.Hide()
            self.bolts = []
            return
        used = 0
        hovered = None
        for i, button in enumerate(self.buttons):
            eyes = self.Eyes(button) if button.IsShow() else None
            if not eyes or not button.enabled:
                continue
            hot = button.state() in ('hover', 'pressed')
            if hot:
                hovered = button
            click = 0.0
            if self.active is not None and self.active[0] is button:
                click = 1.0 - Smooth((now - self.active[2] - 0.05) / 0.5)
            for j, (ex, ey) in enumerate(eyes):
                if used >= len(self.eyes):
                    break
                f = Flicker(now, 90 + i * 2 + j)
                size = button.h * (0.32 if button.kind == 'hrat' else 0.38) * (1.0 + 0.5 * click + (0.25 if hot else 0))
                alpha = (0.32 + 0.08 * (f - 1.0) * 3) + (0.38 if hot else 0.0) + 0.5 * click
                self.eyes[used].Place(ex, ey, size, size, (1.0, 0.12, 0.06), min(1.0, alpha))
                used += 1
        for sprite in self.eyes[used:]:
            sprite.Hide()
        drawn = 0
        if self.active is not None and self.bolts:
            t = now - self.active[2]
            if t < 0.8:
                big = self.active[1]
                n = 7 if big else 5
                drawn = self.DrawSegments([seg for bolt in self.bolts for seg in bolt], t, n + 3,
                                          g.P(4) if big else g.P(2.5), g.P(24) if big else g.P(14))
            else:
                self.bolts = []
        arcs = getattr(self, 'arcs', [])
        if not drawn and hovered is not None:
            # two smouldering arcs, each living 1.6 s (a sine fade in and out), a new one every ~0.8 s
            if arcs and arcs[0][0] is not hovered:
                arcs = []
            if now >= self.nextArc:
                a, b = self.Eyes(hovered)
                mid = hovered.GetGlobalPosition()[1] + hovered.h * 0.16
                c = ((a[0] + b[0]) / 2.0, mid)
                path = self.Jagged(a, c, 4, g.P(4)) + self.Jagged(c, b, 4, g.P(4))[1:]
                arcs = (arcs + [(hovered, now, path)])[-2:]
                self.nextArc = now + self.rnd.uniform(0.7, 1.0)
            segs = []
            for button, start, path in arcs:
                u = (now - start) / 1.6
                if 0.0 <= u < 1.0:
                    k = math.sin(math.pi * u) * (0.75 + 0.25 * math.sin(now * 9.0 + start))
                    segs += [(p0, p1, 0, 0.32 * k) for p0, p1 in zip(path, path[1:])]
            drawn = self.DrawSegments(segs, 1.0, 1, g.P(1.5), g.P(10), phase=lambda order, n, t: (1.0, 1.0))
        elif hovered is None:
            arcs = []
        self.arcs = arcs
        for sprite in self.boltCore[drawn:] + self.boltGlow[drawn:]:
            sprite.Hide()

    def Trigger(self, button, big, point=None):
        x, y = button.GetGlobalPosition()
        if point is None or not (x <= point[0] <= x + button.w and y <= point[1] <= y + button.h):
            point = (x + button.w / 2.0, y + button.h / 2.0)
        self.active = (button, bool(big), app.GetTime(), (float(point[0]), float(point[1])))
        eyes = self.Eyes(button) if self.panel.hall.cfg.get('eyefx', 0) else None
        g = self.panel.g
        self.bolts = [self.Bolt(e, self.active[3], 7 if big else 5, g.P(9) if big else g.P(6))
                      for e in eyes] if eyes else []

    def Update(self, now):
        # hover: the button's own red glows faintly and flickers; a click flares it
        for i, button in enumerate(self.buttons):
            hover = 0.0
            if button.enabled and button.state() in ('hover', 'pressed'):
                hover = 0.28 + 0.1 * (Flicker(now, 70 + i) - 1.0) * 3.0
            flare = 0.0
            if self.active is not None and self.active[0] is button and (self.mode == 'crack' or self.Eyes(button)):
                t = now - self.active[2]
                flare = Smooth(t / 0.12) * (1.0 - Smooth((t - 0.15) / 0.55))
            button.SetVeins(max(hover, flare))
        self.UpdateEyes(now)
        if self.active is None:
            return
        button, big, start, (px, py) = self.active
        t = now - start
        if t > 0.95:
            self.active = None
            for sprite in [self.spot, self.wave, self.swirl, self.ring] + [p[0] for p in self.sparks]:
                sprite.Hide()
            return
        g = self.panel.g
        h = float(button.h)
        k = 1.0 if big else 0.6
        fade = 1.0 - Smooth(t / 0.7)
        if self.mode == 'portal':
            spin = t * 900.0
            ss = h * (0.7 + 1.8 * Smooth(t / 0.5)) * k
            self.swirl.PlaceAngled(px, py, ss, ss, spin, (1.0, 0.3, 0.12), 0.9 * fade * Smooth(t / 0.05))
            frame = int(t * 26) % 8
            self.ring.LoadImage(ASSET + 'btn/fx/ring_%02d.png' % frame)
            self.ring.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)
            rs = h * (0.6 + 2.6 * Smooth(t / 0.6)) * k
            self.ring.Place(px, py, rs * 1.6, rs, (1.0, 1.0, 1.0), 0.95 * fade)
            self.wave.Hide()
        else:
            ws = Smooth(t / 0.6)
            self.wave.Place(px, py, button.w * (0.2 + 1.5 * ws) * k, h * (0.4 + 2.2 * ws) * k, (1.0, 0.14, 0.06),
                            0.55 * (1.0 - ws) * Smooth(t / 0.04))
            self.swirl.Hide()
            self.ring.Hide()
        sp = h * (0.5 + 1.4 * Smooth(t / 0.35)) * k
        self.spot.Place(px, py, sp * 1.4, sp, (1.0, 0.28, 0.1), 0.95 * (1.0 - Smooth(t / 0.45)))
        count = self.SPARKS if big else 6
        ts = t - (0.13 if self.bolts else 0.0)          # with eye bolts the sparks fly where they hit
        for i, (sprite, ang, speed, life, size) in enumerate(self.sparks):
            u = ts / life
            if i >= count or u >= 1.0 or u < 0.0:
                sprite.Hide()
                continue
            dist = (g.P(30) + g.P(90) * speed) * k * (1.0 - (1.0 - u) ** 2)
            sx = px + math.cos(ang) * dist
            sy = py + math.sin(ang) * dist * 0.6 - g.P(50) * u * u
            d = g.P(6) * size * (1.0 - 0.5 * u)
            sprite.Place(sx, sy, d, d, (1.0, 1.0, 1.0), (1.0 - u) * 0.95)


class Lightning(object):
    """Red lightning in the sky behind the gate (owner 11. 10.: "dal bych ty blesky do oblohy v pozadí za tou
    gatou?"; lightning=1), every 4-10 s (lightningrate). Owner 11. 10. night ("zblízka vypadají špatně", reference
    Shape, colours and flicker follow the guild portal
    fx2/funnel.py branch_bolt_frames / PALETTES['red'] / extras.burst_vis):
      shape   - midpoint displacement (the offset ~ N(0, rough x the local segment length): coarse wander, fine
                teeth), 3-5 branches between 1/5 and 4/5 of the channel at 25-45 deg, shorter further down, each
                tapering (width and alpha) to nothing, every other one with a sub-branch;
      drawing - three additive layers of a soft cross-gradient strip (bolt_line.png) per segment: a wide crimson
                glow, a light red middle, a thin white-hot core;
      timing  - a dim stepped leader grows from the cloud (0.14 s), the return stroke flashes the whole channel,
                1-3 re-strikes 40-80 ms apart down the same channel (dimmer, without most of the branches), the
                core dies in ~0.07 s per stroke, the glow lingers ~0.25 s; the sky flashes with each stroke (soft
                attack, long tail) and lifts the rim a little. Only inside the arch opening, at the portal's depth."""

    POOL = 200                      # segments drawn at once (x 3 layers)
    LEVELS = 6                      # main channel 2^6 = 64 segments
    GROW = 0.14                     # the stepped leader, s
    # PALETTES['red'] of the portal: the ramp at 0.7 / 0.88 and its white-hot end
    GLOW, MID, CORE = (1.0, 0.2, 0.1), (1.0, 0.58, 0.45), (1.0, 0.97, 0.93)

    def __init__(self, scene):
        self.scene, self.hall = scene, scene.hall
        self.rnd = random.Random(1111)
        tex = 'bolt_line.png' if Exists(ASSET + 'bolt_line.png') else 'dot.png'
        self.glows = [Sprite(scene.under, tex, True) for unused in range(self.POOL)]
        self.mids = [Sprite(scene.under, tex, True) for unused in range(self.POOL)]
        self.cores = [Sprite(scene.under, tex, True) for unused in range(self.POOL)]
        for sprite in self.glows + self.mids + self.cores:
            sprite.Pivot()
            sprite.Hide()
        self.sky = Sprite(scene.under, 'glow.png', True)
        self.sky.Hide()
        cfg = self.hall.cfg

        def floats(key, default):
            try:
                return [float(v) for v in str(cfg.get(key, default)).split(',')]
            except ValueError:
                return [float(v) for v in default.split(',')]
        # tuning (pregame-hall.cfg + F5): glow / middle / core widths (px at 1080) and strengths, the roughness
        self.widths = floats('boltw', '28,7,3')
        self.alphas = floats('bolta', '0.7,0.85,1.5')
        # per level of the midpoint displacement: a gently wandering channel (small first offsets), fine teeth
        self.rough = floats('boltrough', '0.06,0.09,0.12,0.13,0.11,0.08')
        self.branchRough = floats('boltbranchrough', '0.12,0.16,0.16,0.12')
        self.bolt = None                # the newest bolt's segments ((x, y), (x, y), weight, order) in plate px
        self.bolts = []                 # {'segs', 't0', 'strokes': [(t, strength, branches)]} still drawn
        self.next = None

    # ------------------------------------------------------------------ shape
    def Inside(self, x, y, margin=18.0):
        x0, x1, spring, crown = V3_ARCH
        cx, rx, ry = (x0 + x1) / 2.0, (x1 - x0) / 2.0 - margin, spring - crown - margin
        if y >= spring:
            return max(x0 + margin, min(x1 - margin, x))
        k = max(0.0, 1.0 - ((y - spring) / ry) ** 2)
        half = rx * math.sqrt(k)
        return max(cx - half, min(cx + half, x))

    def Path(self, a, b, rough, levels):
        rough = rough if isinstance(rough, (list, tuple)) else [rough]
        """Midpoint displacement a -> b: every level halves each segment and pushes the middle sideways by
        N(0, rough x its length) - so the big bends come first and the teeth get finer (funnel.branch_bolt_frames)."""
        pts = [a, b]
        for level in range(levels):
            new = [pts[0]]
            r = rough[min(level, len(rough) - 1)]
            for p, q in zip(pts, pts[1:]):
                dx, dy = q[0] - p[0], q[1] - p[1]
                ln = math.sqrt(dx * dx + dy * dy) or 1.0
                off = self.rnd.gauss(0.0, r * ln)
                mx, my = (p[0] + q[0]) / 2.0 - dy / ln * off, (p[1] + q[1]) / 2.0 + dx / ln * off
                new += [(self.Inside(mx, my), my), q]
            pts = new
        return pts

    def MakeBolt(self):
        rnd = self.rnd
        x0, x1, spring, crown = V3_ARCH
        top = (rnd.uniform(x0 + 80, x1 - 80), rnd.uniform(crown + 60, crown + 120))
        end_y = rnd.uniform(320.0, 450.0)
        end = (self.Inside(top[0] + rnd.uniform(-50, 50), end_y), end_y)
        main = self.Path(top, end, self.rough, self.LEVELS)
        n = len(main) - 1
        segs = [(p, q, 1.0, i) for i, (p, q) in enumerate(zip(main, main[1:]))]
        length = math.sqrt((end[0] - top[0]) ** 2 + (end[1] - top[1]) ** 2)
        side = rnd.choice((-1, 1))
        for b in range(rnd.randint(3, 6)):
            i = rnd.randint(n // 5, n * 4 // 5)
            p0 = main[i]
            # off the bolt's overall direction (the local one is noise), outwards and down like blesk-1..4
            d = math.atan2(end[1] - top[1], end[0] - top[0])
            side = -side if rnd.random() < 0.7 else side
            ang = d + side * math.radians(rnd.uniform(28, 48))
            ln = length * (1.0 - 0.5 * i / float(n)) * rnd.uniform(0.4, 0.7)
            p1 = (p0[0] + math.cos(ang) * ln, p0[1] + math.sin(ang) * ln)
            p1 = (self.Inside(p1[0], p1[1]), p1[1])
            path = self.Path(p0, p1, self.branchRough, 4)
            m = len(path) - 1
            for k, (p, q) in enumerate(zip(path, path[1:])):
                # tapering: 0.55 at the root -> ~0.08 at the tip
                segs.append((p, q, 0.38 * (1.0 - k / float(m)) + 0.05, i + 1 + k))
            for unused2 in range(rnd.randint(1, 2) if m >= 8 else 0):
                j = rnd.randint(2, m - 4)
                s0 = path[j]
                a2 = ang + rnd.choice((-1, 1)) * math.radians(rnd.uniform(20, 40))
                l2 = ln * rnd.uniform(0.3, 0.45)
                s1 = (self.Inside(s0[0] + math.cos(a2) * l2, s0[1] + math.sin(a2) * l2), s0[1] + math.sin(a2) * l2)
                sub = self.Path(s0, s1, self.branchRough[1:], 3)
                w0 = 0.55 * (1.0 - j / float(m)) * 0.6
                for k, (p, q) in enumerate(zip(sub, sub[1:])):
                    segs.append((p, q, w0 * (1.0 - k / 8.0) + 0.04, i + 1 + j + k))
                    if len(segs) >= self.POOL:
                        break
        return segs[:self.POOL]

    def Strike(self, now):
        """A whole flash: the leader, the return stroke, 1-3 re-strikes (40-80 ms, the same channel)."""
        rnd = self.rnd
        self.bolt = self.MakeBolt()
        strokes = [(self.GROW, 1.0, 1.0)]
        t = self.GROW
        for unused in range(rnd.choice((1, 1, 2, 2, 3))):
            t += rnd.uniform(0.04, 0.08)
            strokes.append((t, rnd.uniform(0.55, 0.85), 0.25))
        self.bolts = (self.bolts + [{'segs': self.bolt, 't0': now, 'strokes': strokes}])[-2:]

    # ------------------------------------------------------------------ time
    @staticmethod
    def Levels(strokes, t):
        """(core, glow, branches) light at age t: the dim leader, then each stroke's spike - the core decays fast
        (0.07 s), the glow lingers (0.25 s)."""
        core = glow = 0.0
        branch = 1.0
        for ts, a, br in strokes:
            if t >= ts:
                core = max(core, a * math.exp(-(t - ts) / 0.07))
                g = a * math.exp(-(t - ts) / 0.25)
                if g > glow:
                    glow, branch = g, br
        if t < strokes[0][0]:
            core, glow = 0.35, 0.3          # the stepped leader
        return core, glow, branch

    def Update(self, now):
        cfg, cam = self.hall.cfg, self.hall.camera
        if not cfg.get('lightning', 1):
            self.Hide()
            return
        rate = max(0.1, float(cfg.get('lightningrate', 1.0)))
        if self.next is None:
            self.next = now + self.rnd.uniform(2.0, 5.0) / rate
        if now >= self.next:
            self.Strike(now)
            self.next = now + self.rnd.uniform(4.0, 10.0) / rate
        self.bolts = [b for b in self.bolts if now - b['t0'] < b['strokes'][-1][0] + 1.2]
        if not self.bolts:
            self.bolt = None
            self.Hide()
            return
        power = max(0.0, float(cfg.get('lightningpower', 1.0)))
        px, py = cam.Shift(self.scene.backdrop.depth['portal'])
        sc = cam.scale
        sky = 0.0
        used = 0
        for bolt in self.bolts:
            t = now - bolt['t0']
            strokes = bolt['strokes']
            for ts, a, br in strokes:
                if t >= ts:   # the sky: a soft attack (0.06 s), a long tail (0.6 s), every stroke
                    sky = max(sky, a * Smooth((t - ts) / 0.06) * math.exp(-max(0.0, t - ts - 0.06) / 0.6))
            core, glow, branch = self.Levels(strokes, t)
            n = 2 ** self.LEVELS
            for (ax, ay), (bx, by), weight, order in bolt['segs']:
                if used >= self.POOL:
                    break
                reveal = max(0.0, min(1.0, t / self.GROW * n - order)) if t < self.GROW + 0.05 else 1.0
                if reveal <= 0.0:
                    continue
                w = weight if weight >= 1.0 else weight * branch
                # the branches: thin red twigs - their white core falls off faster than their glow
                c, g = core * w * (w if weight < 1.0 else 1.0) * power, glow * w * power
                if g <= 0.01 and c <= 0.01:
                    continue
                a = cam.Screen(ax, ay)
                b = cam.Screen(ax + (bx - ax) * reveal, ay + (by - ay) * reveal)
                dx, dy = b[0] - a[0], b[1] - a[1]
                length = math.sqrt(dx * dx + dy * dy)
                angle = math.degrees(math.atan2(-dx, dy))
                cx, cy = (a[0] + b[0]) / 2.0 + px, (a[1] + b[1]) / 2.0 + py
                taper = 0.35 + 0.65 * min(1.0, weight)
                (wg, wm, wc), (ag, am, ac) = self.widths[:3], self.alphas[:3]
                self.glows[used].PlaceAngled(cx, cy, wg * sc * taper, length + wg * 0.5 * sc * taper, angle, self.GLOW,
                                             min(0.6, ag * g))
                self.mids[used].PlaceAngled(cx, cy, max(1.0, wm * sc * taper), length + wm * 0.6 * sc, angle, self.MID,
                                            min(0.9, am * max(g, c)))
                self.cores[used].PlaceAngled(cx, cy, max(1.0, wc * sc * taper), length + wc * sc, angle, self.CORE,
                                             min(1.0, ac * c))
                used += 1
        for sprite in self.glows[used:] + self.mids[used:] + self.cores[used:]:
            sprite.Hide()
        I = min(1.0, sky * power)
        x0, x1, spring, crown = V3_ARCH
        sx, sy = cam.Screen((x0 + x1) / 2.0, 280.0)
        self.sky.Place(sx + px, sy + py, (x1 - x0) * 1.15 * sc, 620.0 * sc, (1.0, 0.25, 0.18), min(0.6, 0.45 * I))
        levels = self.scene.backdrop.levels
        if 'G_rim' in levels:
            alpha, rgb = levels['G_rim']
            levels['G_rim'] = (min(1.0, alpha * (1.0 + 0.8 * I)), rgb)

    def Hide(self):
        for sprite in self.glows + self.mids + self.cores + [self.sky]:
            sprite.Hide()


class HallLink(uir1.Interactive):
    """A text link of the bare hall (VYTVOŘIT / SMAZAT / UKONČIT): Cinzel caps in ivory-dim with an outline, a
    short red accent line under it that runs out to the full width on hover; disabled = dim, no line."""

    def __init__(self, parent, text, font, event=None, align='left'):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.label = P.Text(self, text, 0, 0, font, T.INK_DIM)
        try:
            self.label.SetOutline(True)
        except Exception:
            pass
        w = max(20, P.Width(self.label))
        h = uir1.FontCell(font) + 8
        self.SetSize(w, h)
        self.w, self.h = w, h
        self.line = uir1.Rect(self, 0, h - 2, max(1, w // 3), 2, 0xD30D0E, 1.0)
        self.line.AddFlag('not_pick')
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        state = self.state()
        full = state in ('hover', 'pressed')
        if not self.enabled:
            P.SetColor(self.label, T.DISABLED)
            self.line.Hide()
            return
        P.SetColor(self.label, T.IVORY if full else T.INK_DIM)
        lw = self.w if full else max(8, self.w // 3)
        self.line.SetSize(lw, 2)
        self.line.SetPosition((self.w - lw) // 2, self.h - 2)
        self.line.Show()


class HallButton(P.PlateButton):
    """VYTVOŘIT / SMAZAT next to HRÁT (owner 11. 10.): the same window plate and Cinzel caps as HRÁT, an ivory
    label, the red only as a short vein under it (a third of the width) that runs out to the whole width on hover /
    press; no fill, no keycap."""

    def __init__(self, parent, x, y, w, h, text, font, event=None):
        P.PlateButton.__init__(self, parent, x, y, w, h, text, font, event=event, primary=True)

    def Resize(self, w, h):
        self.SetSize(int(w), int(h))
        self.w, self.h = int(w), int(h)
        self.plate.Resize(w, h)
        self.fill.SetSize(max(1, w - 4), max(1, h - 4))
        self.paint()

    def paint(self):
        P.PlateButton.paint(self)
        if self.vein is None:
            return
        state = self.state()
        full = state in ('hover', 'pressed')
        vw = (self.w - 6) if full else max(10, self.w // 3)
        self.vein.SetPosition((self.w - vw) // 2, self.h - 2 - T.VEIN_ROW)
        self.vein.SetWidth(vw)
        if self.enabled:
            P.SetColor(self.label, T.IVORY if full else T.INK_DIM)



class Card(uir1.Interactive):
    """A slot card: portrait, name, Lv. + level, job, played; a free one: + Vytvořit postavu."""

    def __init__(self, panel, index):
        uir1.Interactive.__init__(self)
        self.panel, self.index = panel, index
        g = panel.g
        self.SetParent(panel.root)
        self.plate = P.Plate(self, 0, 0, 10, 10)
        self.face = P.Portrait(self, 0, 0, g.P(52))
        self.name = P.Text(self, '', 0, 0, g.noto(19, True), T.INK_DIM)
        self.meta = [P.Text(self, '', 0, 0, g.noto(15), T.MUTED) for unused in range(3)]
        self.plus = P.Plate(self, 0, 0, g.P(40), g.P(40))
        self.plusLabel = P.Text(self.plus, '+', g.P(20), g.P(20), g.noto(24, True), T.INK, align='center', valign='center')
        self.empty = P.Text(self, 'Vytvořit postavu', 0, 0, g.noto(17), T.INK_DIM, valign='center')
        self.data, self.selected = None, False
        self.Show()

    def Place(self, x, y, w, h):
        g = self.panel.g
        self.SetPosition(x, y)
        self.SetSize(w, h)
        self.w, self.h = w, h
        self.plate.Resize(w, h)
        size = g.P(52)
        self.face.SetPosition(g.P(12), (h - size) // 2)
        tx = g.P(12) + size + g.P(14)
        self.name.SetPosition(tx, g.P(12))
        for i, line in enumerate(self.meta):
            line.SetPosition(tx, g.P(36) + i * g.P(18))
        self.plus.SetPosition(g.P(16), (h - g.P(40)) // 2)
        P.Move(self.empty, g.P(16) + g.P(40) + g.P(12), h // 2)

    def SetData(self, data, face, selected):
        self.data, self.selected = data, bool(selected)
        if data is None:
            for widget in [self.face, self.name] + self.meta:
                widget.Hide()
            self.plus.Show()
            self.empty.Show()
        else:
            name, level, job, played = data
            self.plus.Hide()
            self.empty.Hide()
            self.face.Load(face)
            self.face.Show()
            self.name.SetText(name)
            self.name.Show()
            for line, text in zip(self.meta, ('Lv. %d' % level, job, played)):
                line.SetText(text)
                line.Show()
            P.SetColor(self.name, T.IVORY if selected else T.INK_DIM)
            for line in self.meta:
                P.SetColor(line, T.INK_DIM if selected else T.MUTED)
        self.paint()

    def paint(self):
        if self.data is None:
            self.plate.SetState('hover' if self.hovered else 'empty')
        else:
            self.plate.SetState('selected' if self.selected else ('hover' if self.hovered else 'normal'))
        hall = self.panel.hall
        if self.hovered:
            hall.hover = self.index
        elif hall.hover == self.index:
            hall.hover = None

    def click(self):
        self.panel.OnCard(self.index)

    def OnMouseLeftButtonDoubleClick(self):
        self.panel.OnCardDouble(self.index)
        return True


class Panel(object):
    """R1: the linked bottom panel (detail row above, 5 slot cards + Vytvořit / Smazat / HRÁT below), the
    logo + title + hint top left, Ukončit top right. R1 pieces only (uir1pregame: Plate, PlateButton, Text)."""

    STATS = ('VIT', 'INT', 'SÍL', 'POH')

    def __init__(self, hall, rows):
        self.hall = hall
        hall.panel = self
        self.root = None
        self.dialog = None
        self.hidden = []
        self.window = window = hall.window
        W, H = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        s = max(0.72, min(float(W) / 1920.0, float(H) / 1080.0))
        self.g = g = P.Geo(W, H, s)
        self.rows = rows
        self.keep = ()
        self.hidden = P._hide_column(window)
        self.root = P._root(window, g)
        # the select board may be placed off the screen origin (a centred design width): every root is anchored to
        # the SCREEN (owner 11. 10.: "R POSTAVY" / the hint cut on the left at 1788 px)
        self.root.SetPosition(*ScreenOrigin(window.dlgBoard))
        self.dialog = None
        # owner 10. 10. night ("určitě varianta B"): no framed panel - a see-through strip along the bottom edge
        # (a dark gradient rising into the scene) with the slot cards and the actions; panel=r1 = the old panel
        self.strip = str(hall.cfg.get('panel', 'scene')) != 'r1'
        # owner 11. 10.: "nech jen ten text, zbytek hoď do píči" - panel=scene (default): no bar at all; the
        # characters are chosen on the scene (click, arrows, their names / text, "+ nová postava" on the floor);
        # HRÁT bottom right, VYTVOŘIT / SMAZAT as links over it, Ukončit as a link top right. panel=strip = the bar
        self.bare = str(hall.cfg.get('panel', 'scene')) == 'scene'
        # owner 11. 10.: "chci actual rozhraní" - the generated button sets (tools/pregame_proto_tlacitka.py)
        self.buttonSet = str(hall.cfg.get('buttons', 'obsidian')).lower()
        if self.buttonSet not in BUTTON_SETS:
            self.buttonSet = 'obsidian'
        self.images = self.bare and Exists(ImageButton.Path(self.buttonSet, 'hrat', 'normal'))
        self.shade = [uir1.Rect(self.root, 0, 0, 1, 1, 0x0A0606, 0.0) for unused in range(18)] if self.strip else []
        self.title = P.Text(self.root, 'Výběr postavy', 0, 0, g.title(), T.IVORY)
        self.titleVein = uir1.Vein(self.root, 0, 0, g.P(170))
        self.hint = P.Text(self.root, 'Klikni na postavu  ·  šipky vlevo a vpravo  ·  Enter = hrát', 0, 0, g.noto(15), T.MUTED)
        if self.images:
            self.exit = ImageButton(self.root, 'maly', 'UKONČIT', g.caps(BUTTON_FONT['exit']), self.OnExit, self.buttonSet)
        elif self.bare:
            self.exit = HallLink(self.root, 'UKONČIT', g.caps(15), event=self.OnExit, align='right')
        else:
            self.exit = P.PlateButton(self.root, 0, 0, g.P(150), g.P(36), 'UKONČIT', g.caps(15), event=self.OnExit)
        self.frame = uir1.Frame(self.root, 0, 0, 10, 10, 'window')
        self.name = P.Text(self.root, '', 0, 0, g.noto(30, True), T.IVORY)
        self.nameVein = uir1.Vein(self.root, 0, 0, g.P(200))
        self.lv = P.Text(self.root, 'Lv.', 0, 0, g.noto(17), T.MUTED)
        self.level = P.Text(self.root, '', 0, 0, g.noto(24, True), T.IVORY)
        self.job = P.Text(self.root, '', 0, 0, g.noto(19), T.INK_DIM)
        self.seps = [uir1.Rect(self.root, 0, 0, 1, g.P(44), 0x383434, 1.0) for unused in range(3)]
        self.infoLabels = [P.Text(self.root, text, 0, 0, g.noto(15), T.MUTED)
                           for text in ('Rodové jméno', 'Cech', 'Odehráno')]
        self.infoValues = [P.Text(self.root, '', 0, 0, g.noto(18, True), T.IVORY) for unused in range(3)]
        self.statLabels = [P.Text(self.root, text, 0, 0, g.noto(15), T.MUTED) for text in self.STATS]
        self.statValues = [P.Text(self.root, '', 0, 0, g.noto(18, True), T.IVORY) for unused in self.STATS]
        self.divider = uir1.Divider(self.root, 0, 0, 10)
        self.cards = [Card(self, index) for index in range(rows)]
        if self.images:
            self.create = ImageButton(self.root, 'maly', 'VYTVOŘIT', g.caps(BUTTON_FONT['maly']), self.OnCreate,
                                      self.buttonSet)
            self.delete = ImageButton(self.root, 'maly', 'SMAZAT', g.caps(BUTTON_FONT['maly']), self.OnDelete,
                                      self.buttonSet)
        elif self.bare:
            self.create = HallLink(self.root, 'VYTVOŘIT', g.caps(15), event=self.OnCreate)
            self.delete = HallLink(self.root, 'SMAZAT', g.caps(15), event=self.OnDelete)
        elif self.strip:
            # owner 11. 10.: "ten čudlík Vytvořit je tak strašně bad" - the same language as HRÁT (the window plate,
            # Cinzel caps), the red only as an accent: a short vein that runs out to the full width on hover
            self.create = HallButton(self.root, 0, 0, 10, g.P(40), 'VYTVOŘIT', g.caps(16), event=self.OnCreate)
            self.delete = HallButton(self.root, 0, 0, 10, g.P(40), 'SMAZAT', g.caps(16), event=self.OnDelete)
        else:
            self.create = P.PlateButton(self.root, 0, 0, 10, g.P(36), 'VYTVOŘIT', g.caps(15), event=self.OnCreate)
            self.delete = P.PlateButton(self.root, 0, 0, 10, g.P(36), 'SMAZAT', g.caps(15), event=self.OnDelete)
        if self.images:
            self.play = ImageButton(self.root, 'hrat', 'HRÁT', g.caps(BUTTON_FONT['hrat']), self.OnPlay, self.buttonSet)
        else:
            self.play = P.PlateButton(self.root, 0, 0, 10, g.P(70), 'HRÁT', g.caps(30), event=self.OnPlay,
                                      primary=True)
        self.fx = None
        mode = str(hall.cfg.get('btnfx', 'crack')).lower()
        if self.images and mode not in ('0', 'off', 'no', ''):
            self.fx = ButtonFX(self, 'portal' if mode == 'portal' else 'crack')
            self.fx.buttons = [self.play, self.create, self.delete, self.exit]
            for button in self.fx.buttons:
                button.fx = self.fx
        self.Layout()
        P.SetColor(self.hint, TEXT_MUTED)

    # ------------------------------------------------------------------ layout
    def Layout(self):
        g, W, H = self.g, self.g.W, self.g.H
        m = g.P(28)
        try:
            logo = self.window.dlgBoard.GetChild('brand_logo')
            logo.SetPosition(g.P(40), g.P(26))
            logo.SetScale(g.s * 0.8, g.s * 0.8)
            logo.Show()
            logoBottom = g.P(26) + int(96 * g.s * 0.8)
        except Exception:
            logoBottom = g.P(100)
        self.title.SetPosition(g.P(44), logoBottom + g.P(18))
        self.titleVein.SetPosition(g.P(40), logoBottom + g.P(18) + uir1.FontCell(g.title()) + 6 - T.VEIN_ROW)
        self.hint.SetPosition(g.P(44), logoBottom + g.P(52))
        if self.images:
            pass                                    # LayoutBare places it
        elif self.bare:
            self.exit.SetPosition(W - m - self.exit.GetWidth(), g.P(34))
        else:
            self.exit.SetPosition(W - m - g.P(150), g.P(34))
        if self.strip:
            self.LayoutStrip()
            return
        # the panel: full width less the margins, 252 px high at 1080
        ph = g.P(252)
        px, py, pw = m, H - ph - g.P(36), W - 2 * m
        self.frame.Resize(pw, ph)
        self.frame.SetPosition(px, py)
        x = px + g.P(26)
        top = py + g.P(20)
        self.name.SetPosition(x, top)
        self.nameY = top
        self.lv.SetPosition(x + g.P(330), top + g.P(10))
        self.level.SetPosition(x + g.P(358), top + g.P(2))
        self.job.SetPosition(x + g.P(410), top + g.P(7))
        sx = x + g.P(590)
        self.seps[0].SetPosition(sx, top)
        cx = sx + g.P(30)
        for label, value, step in zip(self.infoLabels, self.infoValues, (175, 130, 0)):
            label.SetPosition(cx, top)
            value.SetPosition(cx, top + g.P(22))
            cx += g.P(step)
        sx = cx + g.P(150)
        self.seps[1].SetPosition(sx, top)
        cx = sx + g.P(30)
        for label, value in zip(self.statLabels, self.statValues):
            label.SetPosition(cx, top)
            value.SetPosition(cx, top + g.P(22))
            cx += g.P(84)
        self.seps[2].Hide()
        self.divider.SetPosition(px + g.P(16), py + g.P(84))
        self.divider.Apply(uir1.L.divider(0, 0, pw - g.P(32)) if hasattr(uir1, 'L') else [])
        # the bottom row: cards, then the action column
        actionW = g.P(360)
        cardsW = pw - g.P(26) * 2 - actionW - g.P(24)
        gap = g.P(12)
        cw = (cardsW - gap * (self.rows - 1)) // self.rows
        cy, ch = py + g.P(102), g.P(124)
        for index, card in enumerate(self.cards):
            card.Place(x + index * (cw + gap), cy, cw, ch)
        ax = px + pw - g.P(26) - actionW
        bw = (actionW - g.P(10)) // 2
        for button, bx in ((self.create, ax), (self.delete, ax + bw + g.P(10))):
            button.SetSize(bw, g.P(36))
            button.w = bw
            button.plate.Resize(bw, g.P(36))
            button.fill.SetSize(max(1, bw - 4), max(1, g.P(36) - 4))
            button.SetPosition(bx, cy)
            button.paint()
        self.play.SetSize(actionW, g.P(76))
        self.play.w, self.play.h = actionW, g.P(76)
        self.play.plate.Resize(actionW, g.P(76))
        self.play.fill.SetSize(max(1, actionW - 4), max(1, g.P(76) - 4))
        if self.play.vein is not None:
            self.play.vein.SetPosition(3, g.P(76) - 2 - T.VEIN_ROW)
            self.play.vein.SetWidth(actionW - 6)
        self.play.SetPosition(ax, cy + ch - g.P(76))
        self.play.paint()
        self.panelTop = py

    def ButtonBoxes(self):
        """Screen rectangles of HRÁT / VYTVOŘIT / SMAZAT (the floor texts keep clear of them)."""
        out = []
        for button in (self.play, self.create, self.delete):
            try:
                if button.IsShow():
                    x, y = button.GetGlobalPosition()
                    out.append((x, y, x + button.GetWidth(), y + button.GetHeight()))
            except Exception:
                pass
        return out

    def CycleLayout(self):
        """F7: the next button layout (a / b / c)."""
        order = ('a', 'b', 'c')
        cur = str(self.hall.cfg.get('btnlayout', 'a')).lower()
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else 'a'
        self.hall.cfg['btnlayout'] = nxt
        self.LayoutBare()
        return nxt

    def SetButtonSet(self, name):
        """F8: another generated set for HRÁT / VYTVOŘIT / SMAZAT / UKONČIT."""
        if not self.images or name not in BUTTON_SETS:
            return None
        self.buttonSet = name
        self.hall.cfg['buttons'] = name
        for button in (self.play, self.create, self.delete, self.exit):
            button.SetSet(name)
        self.LayoutBare()                       # the sets differ in shape (height)
        return name

    def DetailWidgets(self):
        return ([self.frame, self.divider, self.name, self.nameVein, self.lv, self.level, self.job] + self.seps
                + self.infoLabels + self.infoValues + self.statLabels + self.statValues)

    def LayoutBare(self):
        """panel=scene: no bar - the cards hidden, no gradient; HRÁT bottom right, the two links over it."""
        g, W, H = self.g, self.g.W, self.g.H
        m = g.P(28)
        for widget in self.DetailWidgets() + list(self.cards) + list(self.shade):
            widget.Hide()
        self.nameY = 0
        if self.images:
            # the generated buttons (owner 11. 10.: "větší, pohraj si s rozložením"): HRÁT ~35 % bigger, the small
            # ones in proportion; three layouts (cfg btnlayout, F7): a = HRÁT big at the bottom centre with
            # VYTVOŘIT / SMAZAT at its sides, b = a column bottom right, c = HRÁT bottom right, the two bottom left
            pw = g.P(BUTTON_W['hrat'])
            ph = int(round(pw / max(1.5, self.play.Aspect())))
            sw = g.P(BUTTON_W['maly'])
            sh = int(round(sw / max(1.5, self.create.Aspect())))
            ew = g.P(BUTTON_W['exit'])
            self.play.Resize(pw, ph)
            for button in (self.create, self.delete):
                button.Resize(sw, sh)
            self.exit.Resize(ew, int(round(ew / max(1.5, self.exit.Aspect()))))
            self.exit.SetPosition(W - m - ew, g.P(28))
            layout = str(self.hall.cfg.get('btnlayout', 'a')).lower()
            bottom = H - g.P(26)
            if layout == 'a':
                px, py = (W - pw) // 2, bottom - ph
                self.play.SetPosition(px, py)
                cy = py + (ph - sh) // 2
                self.create.SetPosition(px - g.P(24) - sw, cy)
                self.delete.SetPosition(px + pw + g.P(24), cy)
            elif layout == 'c':
                px, py = W - m - pw, bottom - ph
                self.play.SetPosition(px, py)
                cy = bottom - sh - (ph - sh) // 2
                self.create.SetPosition(m, cy)
                self.delete.SetPosition(m + sw + g.P(16), cy)
            else:
                px, py = W - m - pw, bottom - ph
                self.play.SetPosition(px, py)
                cx = px + (pw - sw) // 2
                self.delete.SetPosition(cx, py - g.P(8) - sh)
                self.create.SetPosition(cx, py - 2 * (g.P(8) + sh))
            self.layout = layout
            self.panelTop = H - g.P(24)
            return
        actionW, playH = g.P(260), g.P(64)
        ax, py = W - m - actionW, H - g.P(30) - playH
        self.play.SetSize(actionW, playH)
        self.play.w, self.play.h = actionW, playH
        self.play.plate.Resize(actionW, playH)
        self.play.fill.SetSize(max(1, actionW - 4), max(1, playH - 4))
        if self.play.vein is not None:
            self.play.vein.SetPosition(3, playH - 2 - T.VEIN_ROW)
            self.play.vein.SetWidth(actionW - 6)
        self.play.SetPosition(ax, py)
        self.play.paint()
        ly = py - g.P(12) - self.delete.GetHeight()
        self.delete.SetPosition(W - m - self.delete.GetWidth(), ly)
        self.create.SetPosition(W - m - self.delete.GetWidth() - g.P(28) - self.create.GetWidth(), ly)
        # nothing sits along the bottom any more: the scene may reach down to just over the screen edge
        self.panelTop = H - g.P(24)

    def LayoutStrip(self):
        """Variant B: the cards in one row along the bottom, HRÁT at the right end, VYTVOŘIT / SMAZAT above it;
        under them a gradient (transparent at the top, dark at the screen edge) instead of a framed panel. The detail
        row of the r1 panel is gone (the cards carry name, level, job, played)."""
        if self.bare:
            self.LayoutBare()
            return
        g, W, H = self.g, self.g.W, self.g.H
        m = g.P(28)
        for widget in self.DetailWidgets():
            widget.Hide()
        self.nameY = 0
        ch = g.P(100)
        cy = H - g.P(30) - ch
        actionW = g.P(300)
        gap = g.P(12)
        cardsW = W - 2 * m - actionW - g.P(24)
        cw = (cardsW - gap * (self.rows - 1)) // self.rows
        for index, card in enumerate(self.cards):
            card.Place(m + index * (cw + gap), cy, cw, ch)
        ax = W - m - actionW
        playH = g.P(70)
        self.play.SetSize(actionW, playH)
        self.play.w, self.play.h = actionW, playH
        self.play.plate.Resize(actionW, playH)
        self.play.fill.SetSize(max(1, actionW - 4), max(1, playH - 4))
        if self.play.vein is not None:
            self.play.vein.SetPosition(3, playH - 2 - T.VEIN_ROW)
            self.play.vein.SetWidth(actionW - 6)
        self.play.SetPosition(ax, cy + ch - playH)
        self.play.paint()
        bw = (actionW - g.P(10)) // 2
        bh = g.P(40)
        by = cy + ch - playH - g.P(10) - bh
        for button, bx in ((self.create, ax), (self.delete, ax + bw + g.P(10))):
            button.Resize(bw, bh) if hasattr(button, 'Resize') else None
            button.SetPosition(bx, by)
            button.paint()
        self.panelTop = min(cy, by) - g.P(8)
        # the gradient: from clear (top) to dark (bottom edge), in bands
        top = self.panelTop - g.P(110)
        n = len(self.shade)
        step = max(1, (H - top + n - 1) // n)
        for i, band in enumerate(self.shade):
            y = top + i * step
            k = float(i + 1) / n
            band.SetPosition(0, y)
            band.SetSize(W, step + 1)
            band.SetColor(uikit_color(0x0A0606, 0.82 * k ** 1.4))

    # ------------------------------------------------------------------ data
    def Count(self):
        try:
            return int(self.window.mycharacters.GetMyCharacterCount())
        except Exception:
            return 0

    def Detail(self, slot):
        window = self.window
        data = window.mycharacters.GetDisplayData(slot) or {}
        conqueror = int(data.get('CONQUEROR_LEVEL', 0) or 0)
        level = conqueror if conqueror > 0 else int(data.get('LEVEL', 0) or 0)
        guild = (data.get('GUILDNAME') or '').strip()
        played = window.FormatPlayTime(data.get('PLAYTIME', 0))
        try:
            job = window.JOB_LIST.get(window.mycharacters.GetJob(slot), '')
        except Exception:
            job = ''
        family = getattr(window, 'familyName', '') or '–'
        return data.get('NAME', ''), level, guild, played, family, job

    def Refresh(self):
        window, g = self.window, self.g
        self.hidden.extend(P._hide_column(window, self.keep))
        count = self.Count()
        selected = getattr(window, 'SelectSlot', -1)
        selected = selected if selected is not None else -1
        for index, card in enumerate(self.cards):
            if index < count:
                name, level, guild, played, family, job = self.Detail(index)
                race = window.mycharacters.GetRace(index)
                face = window.RACE_FACE_PATH.get(race, '') + ('1.sub' if index == selected else '2.sub')
                card.SetData((name, level, job, played), face, index == selected)
            else:
                card.SetData(None, None, False)
        has = 0 <= selected < count
        widgets = ([self.name, self.nameVein, self.lv, self.level, self.job] + self.infoLabels + self.infoValues
                   + self.statLabels + self.statValues + self.seps[:2])
        for widget in widgets:
            widget.Show() if (has and not self.strip) else widget.Hide()
        if has:
            name, level, guild, played, family, job = self.Detail(selected)
            self.name.SetText(name)
            self.nameVein.SetPosition(self.name.GetLocalPosition()[0] - 4,
                                      self.nameY + uir1.FontCell(g.noto(30, True)) + 4 - T.VEIN_ROW)
            self.nameVein.SetWidth(max(g.P(120), P.Width(self.name) + 8))
            self.level.SetText(str(level))
            self.job.SetText(job)
            jx = self.level.GetLocalPosition()[0] + P.Width(self.level) + g.P(12)
            self.job.SetPosition(jx, self.job.GetLocalPosition()[1])
            for value, text in zip(self.infoValues, (family, guild or '–', played)):
                value.SetText(text)
            for value, number in zip(self.statValues, window.statpoint):
                value.SetText(str(number))
            self.play.Enable()
            self.delete.Enable()
        else:
            self.play.Disable()
            self.delete.Disable()

    # ------------------------------------------------------------------ actions
    def OnCard(self, index):
        window = self.window
        if getattr(window, 'Disable', False):
            return
        if index < self.Count():
            if index != window.SelectSlot:
                try:
                    import snd
                    snd.PlaySound('sound/ui/click.wav')
                except Exception:
                    pass
                window.SelectButton(index)
        else:
            window.CreateCharacterInRow(index)

    def OnCardDouble(self, index):
        if index < self.Count():
            self.OnCard(index)
            self.OnPlay()
        else:
            self.window.CreateCharacterInRow(index)

    def OnPlay(self):
        if not getattr(self.window, 'Disable', False):
            self.window.StartGameButton()

    def OnCreate(self):
        if not getattr(self.window, 'Disable', False):
            self.window.CreateCharacterButton()

    def OnDelete(self):
        if not getattr(self.window, 'Disable', False):
            self.window.InputPrivateCode()

    def OnExit(self):
        self.window.ExitButton()

    def SetEnabled(self, enabled):
        for widget in [self.play, self.create, self.delete, self.exit] + self.cards:
            widget.Enable() if enabled else widget.Disable()
        if enabled:
            self.Refresh()

    def OpenDelete(self, number_mode, max_len, accept, cancel):
        self.CloseDelete()
        selected = self.window.SelectSlot
        name, level, guild, played, family, job = self.Detail(selected)
        race = self.window.mycharacters.GetRace(selected)
        self.dialog = P.DeleteDialog(self, (name, level, guild, played), self.window.RACE_FACE_PATH.get(race, '') + '1.sub',
                                     number_mode, max_len, accept, cancel)
        return self.dialog

    def CloseDelete(self):
        if self.dialog is not None:
            self.dialog.Destroy()
            self.dialog = None

    def Destroy(self):
        P.CancelOwnedDelete(self)
        self.CloseDelete()
        if self.root is not None:
            self.root.Hide()
        self.root = None


# =========================================================================== the hall (scene + panel)
MUSIC_TOAST = 3.0                     # s the track's name shows in the corner (F8, the shuffle's next track)


def ApplyMusic(fade=True):
    """The select / creation music (root/pregamemusic.py: exactly one track, the same one in both screens, so the
    switch between them never restarts it). Playback is ticked by the select/create phase."""
    import pregamemusic
    return pregamemusic.PlayHall(Config().get('music', 'shuffle'), fade)


class Hall(object):
    is_hall = True

    def __init__(self, window, rows, cfg):
        self.window, self.rows, self.cfg = window, rows, cfg
        self.fx = []
        self.hover = None
        self.camera = None
        self.selected = getattr(window, 'SelectSlot', -1)
        self.fade = {}                  # slot -> (from, to, start)
        self.failed = False
        self.oldRenderer = getattr(window, 'chrRenderer', None)
        self.scene = None
        self.panel = None
        self.ticker = None
        self.destroyed = False
        self.panel = Panel(self, rows)          # the panel first: the scene labels use its fonts and data
        self.scene = Scene(self)
        self.panel.root.AddFlag('float')    # wndMgr.SetTop only lifts float windows; else L0 covers the panel
        self.panel.root.SetTop()
        if self.oldRenderer is not None:
            self.oldRenderer.Hide()
        self.ticker = Ticker(self)
        now = app.GetTime()
        for slot in range(self.Count()):
            self.fade[slot] = (1.0 if slot == self.selected else 0.0,) * 2 + (now - FADE,)
        self.uiHidden = False
        self.Refresh()
        if str(cfg.get('ui', 'on')).lower() in ('off', '0', 'no'):
            self.ToggleUI()

    def Count(self):
        return self.panel.Count()

    # ------------------------------------------------------------------ selection
    def Light(self, slot, now):
        start, end, t0 = self.fade.get(slot, (0.0, 0.0, 0.0))
        return start + (end - start) * Smooth((now - t0) / FADE)

    def Select(self, prev, slot):
        """window.SelectButton: the selection is instant, the light follows in FADE s; with selectpose=1 the selected
        plays the short MOTION_INTRO_SELECTED gesture and returns to its idle loop (off: only the light)."""
        now = app.GetTime()
        self.selected = slot
        for index in range(self.Count()):
            current = self.Light(index, now)
            self.fade[index] = (current, 1.0 if index == slot else 0.0, now)
            if chr.HasInstance(index):
                chr.SelectInstance(index)
                chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
                chr.Show()
        pose = self.cfg.get('selectpose', 0)
        if pose and prev is not None and 0 <= prev < self.Count() and prev != slot and chr.HasInstance(prev):
            # the one it replaces bows out (stock not_selected.msa), then back to its idle loop
            chr.SelectInstance(prev)
            try:
                chr.PushOnceMotion(chr.MOTION_INTRO_NOT_SELECTED, 0.1)
            except Exception:
                pass
        if pose and prev is not None and prev >= 0 and prev != slot and chr.HasInstance(slot):
            # the stock intro pose (selected.msa: the one the old select plays before entering the world); a
            # once-motion returns to the MOTION_INTRO_WAIT loop by itself
            chr.SelectInstance(slot)
            try:
                chr.PushOnceMotion(chr.MOTION_INTRO_SELECTED, 0.1)
            except Exception:
                pass
            if self.scene is not None and self.scene.reflections is not None:
                self.scene.reflections.Gesture(slot)
        if self.scene is not None and self.scene.places:
            self.scene.PlaceInstances()       # the light rig follows the selection (Renderer.LightPasses)
        if chr.HasInstance(slot):
            chr.SelectInstance(slot)          # the window's later chr.* calls act on the selection

    def Step(self, direction):
        """← → walk the arc by its places (left to right), skipping the free ones."""
        count = self.Count()
        if count <= 1:
            return
        order = sorted(range(count), key=lambda s: ARC_OF_SLOT[s])
        try:
            pos = order.index(self.window.SelectSlot)
        except ValueError:
            pos = 0
        self.panel.OnCard(order[(pos + direction) % len(order)])

    # ------------------------------------------------------------------ the R1 column interface
    def Refresh(self):
        self.selected = getattr(self.window, 'SelectSlot', -1)
        now = app.GetTime()
        for slot in range(self.Count()):
            if slot not in self.fade:
                self.fade[slot] = (0.0, 1.0 if slot == self.selected else 0.0, now)
        self.panel.Refresh()
        self.scene.Place()
        if getattr(self, 'uiHidden', False):
            self.uiHidden = False
            self.ToggleUI()

    def Update(self):
        now = app.GetTime()
        self.scene.Update(now)
        self.MusicToast(now)
        if getattr(self.panel, 'fx', None) is not None:
            self.panel.fx.Update(now)
        for button in (getattr(self.panel, name, None) for name in ('play', 'create', 'delete', 'exit')):
            if isinstance(button, ImageButton):
                button.Breathe(now)

    def Toast(self, text):
        np_ = self.scene.nameplates if self.scene is not None else None
        if np_ is not None:
            np_.toast.SetText(text)
            np_.toastAt = np_.last if np_.last is not None else app.GetTime()

    def CycleOther(self):
        """F4 (new_introselect): how the unselected are lit - mod / add / normal."""
        order = ('mod', 'add', 'normal')
        cur = str(self.cfg.get('othermode', 'mod'))
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else 'mod'
        self.cfg['othermode'] = nxt
        for slot in range(self.Count()):
            try:
                chr.testRestoreRenderMode(slot)
            except Exception:
                pass
        self.Toast('Nevybrané (F4): %s' % nxt)
        return nxt

    def CycleRig(self):
        """F6 (new_introselect): the row's shift under the light rig (named for 1.5 s)."""
        order = (0, 100, 125, 150, 175, 200)
        cur = int(self.cfg.get('rigshift', 0))
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else 0
        self.cfg['rigshift'] = nxt
        if self.scene is not None:
            self.scene.PlaceInstances()
            np_ = self.scene.nameplates
            if np_ is not None:
                np_.toast.SetText('Světlo postav (F6): posun %d cm' % nxt)
                np_.toastAt = np_.last if np_.last is not None else app.GetTime()
        return nxt

    def StrikeNow(self):
        """F11 (new_introselect, debug): a lightning flash behind the gate right now."""
        ln = self.scene.lightning if self.scene is not None else None
        if ln is None:
            return False
        ln.Strike(app.GetTime())
        return True

    def CycleLayout(self):
        """F7 (new_introselect): the next button layout, named for 1.5 s."""
        if not getattr(self.panel, 'images', False):
            return None
        name = self.panel.CycleLayout()
        np_ = self.scene.nameplates if self.scene is not None else None
        if np_ is not None:
            np_.toast.SetText('Rozložení tlačítek (F7): %s' % {'a': 'HRÁT uprostřed', 'b': 'sloupec vpravo',
                                                                 'c': 'HRÁT vpravo, ostatní vlevo'}[name])
            np_.toastAt = np_.last if np_.last is not None else app.GetTime()
        return name

    def CycleButtons(self):
        """The next generated button set (kamen -> cepel -> ram), named for 1.5 s (tuning only)."""
        panel = self.panel
        if not getattr(panel, 'images', False):
            return None
        order = BUTTON_SETS
        name = order[(order.index(panel.buttonSet) + 1) % len(order)] if panel.buttonSet in order else order[0]
        panel.SetButtonSet(name)
        np_ = self.scene.nameplates if self.scene is not None else None
        if np_ is not None:
            np_.toast.SetText('Tlačítka: %s' % name)
            np_.toastAt = np_.last if np_.last is not None else app.GetTime()
        return name

    def CycleMusic(self):
        """F8 (new_introselect, temporary - the owner picks the track): the next track (the current one fades out, the
        next in); its name in the top right corner for MUSIC_TOAST s."""
        import pregamemusic
        key = pregamemusic.Step()
        if key is None:
            self.ShowMusic('Hudba (F8): skladby chybí')
            return None
        self.ShowMusic('Hudba (F8): %s' % pregamemusic.Name(key))
        return key

    def ShowMusic(self, text):
        if self.scene is None:
            return
        label = getattr(self, 'musicLabel', None)
        if label is None:
            g = self.panel.g
            label = self.musicLabel = P.Text(self.scene.over, '', self.scene.W - g.P(28), g.P(18), g.noto(16, True),
                                             T.IVORY, align='right')
            try:
                label.SetOutline(True)
            except Exception:
                pass
        label.SetText(text)
        label.Show()
        self.musicAt = app.GetTime()

    def MusicToast(self, now):
        label, at = getattr(self, 'musicLabel', None), getattr(self, 'musicAt', None)
        if label is None or at is None:
            return
        t = now - at
        if t >= MUSIC_TOAST:
            self.musicAt = None
            label.Hide()
            return
        P.SetColor(label, _argb(T.IVORY, 1.0 if t < MUSIC_TOAST - 0.4 else max(0.0, (MUSIC_TOAST - t) / 0.4)))

    def CycleDetail(self):
        """F9 (new_introselect): d <-> a, see Nameplates."""
        if self.scene is not None and self.scene.nameplates is not None:
            return self.scene.nameplates.Cycle()
        return None

    def ToggleUI(self):
        """'H' / F10 (owner 10. 10. night): the whole UI away and back - the panel with the cards, the title, the
        logo, Ukončit, the names over the heads and the + of the free places. The scene stays: a click on a character,
        the arrows and Enter still select / play. Not while the delete dialog is open."""
        if self.panel.dialog is not None:
            return self.uiHidden
        self.uiHidden = not self.uiHidden
        self.ApplyUI()
        return self.uiHidden

    def ApplyUI(self):
        hidden = self.uiHidden
        widgets = [self.panel.root] + list(self.scene.labels) + [plate for plate in self.scene.plus if plate is not None]
        if hidden and self.scene.nameplates is not None:
            widgets += self.scene.nameplates.Widgets()      # shown again by their own Update
        if hidden:
            for item in self.scene.free:
                widgets += [item['line']] + item['shadows']
        try:
            widgets.append(self.window.dlgBoard.GetChild('brand_logo'))
        except Exception:
            pass
        for widget in widgets:
            widget.Hide() if hidden else widget.Show()
        if not hidden:
            self.panel.Refresh()
            self.scene.Place()

    def SetEnabled(self, enabled):
        self.panel.SetEnabled(enabled)
        for hit in self.scene.hits:
            hit.Enable() if enabled else hit.Disable()

    def OpenDelete(self, *args):
        return self.panel.OpenDelete(*args)

    def CloseDelete(self):
        self.panel.CloseDelete()

    def Destroy(self):
        if self.destroyed:
            return
        self.destroyed = True
        if self.ticker is not None:
            self.ticker.Hide()
            self.ticker.hall = None
        if self.scene is not None:
            self.scene.Destroy()
        if self.panel is not None:
            self.panel.Destroy()
            for widget in self.panel.hidden:
                widget.Show()
        # Both a resize and a failure can return to a single-actor renderer.
        selected = getattr(self.window, 'SelectSlot', -1)
        for slot in range(self.rows):
            if chr.HasInstance(slot):
                chr.SelectInstance(slot)
                chr.SetPixelPosition(0, 0, 0)
                chr.SetScale(1.0, 1.0, 1.0)
                chr.SetRotation(0.0)
                chr.Show() if slot == selected else chr.Hide()
        if chr.HasInstance(selected):
            chr.SelectInstance(selected)
        try:
            self.window.dlgBoard.GetChild('giant_brand_mark').Show()
        except Exception:
            pass
        if self.oldRenderer is not None:
            self.oldRenderer.Show()

    def Undo(self):
        """Replace a failed hall with the R1 column without retrying the failed scene."""
        self.Destroy()
        self.window.r1 = P.AttachSelect(self.window, allow_hall=False)


class Ticker(ui.Window):
    """Drives the scene every frame (OnUpdate of a hidden-from-picking window on the board)."""

    def __init__(self, hall):
        ui.Window.__init__(self)
        self.hall = hall
        self.SetParent(hall.window.dlgBoard)
        self.AddFlag('not_pick')
        self.SetSize(1, 1)
        self.Show()

    def OnUpdate(self):
        hall = self.hall
        if hall is None or hall.failed:
            return
        try:
            hall.Update()
        except Exception:
            uir1.TraceFailure('pregame hall update')
            hall.failed = True
            hall.Undo()


def Attach(window, rows):
    """The hall for the select window, or None (switched off, too small a screen, or it failed: the R1 column)."""
    cfg = Config()
    if cfg['off'] or wndMgr.GetScreenWidth() < MIN_SCREEN[0] or wndMgr.GetScreenHeight() < MIN_SCREEN[1]:
        return None
    # Keep ownership even when a nested constructor fails after hiding legacy UI.
    hall = Hall.__new__(Hall)
    try:
        hall.__init__(window, rows, cfg)
        return hall
    except Exception:
        uir1.TraceFailure('pregame hall')
        hall.Destroy()
        return None



# =========================================================================== character creation in the hall

# the creation choices (tools/pregame_create_controls.py): obsidian plates in two layouts and four kinds; sizes at 1080p
CREATE_DIR = ASSET + 'create/'
# owner 11. 10.: "ať ty 4 dole vypadají jako HRÁT a SMAZAT" - every plate is SMAZAT's frame at SMAZAT's height (60)
CREATE_SIZE = {'job': (460, 60, 14), 'small': (225, 60, 14)}    # w, h, glow margin (= the tool)
CREATE_LOWER = ('nameLabel', 'counter', 'field', 'error', 'errorMark', 'create', 'back')  # moved under the plates


class Choice(uir1.Interactive):
    """One class / gender / look button of the creation in the hall: the calm image under the hot one (selected =
    hot, hover = half), crossfaded; a click selects through the creation window like the column's rows."""

    def __init__(self, parent, kind, index, action):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.kind, self.index, self.action = kind, index, action
        self.calm = ui.ExpandedImageBox()
        self.hot = ui.ExpandedImageBox()
        for image in (self.calm, self.hot):
            image.SetParent(self)
            image.AddFlag('not_pick')
            try:
                image.SetLinearFiltering(True)
            except Exception:
                pass
        self.key = None
        self.selected = False
        self.glow, self.at = 0.0, None
        self.box = (0, 0, 1, 1, 0)
        self.Show()

    def Load(self, name):
        """name = the image without _calm / _hot, e.g. 'b5_kruh/job_1_w'"""
        path = CREATE_DIR + name
        if path == self.key:
            return
        self.key = name
        self.path = path
        self.calm.LoadImage(path + '_calm.png')
        self.hot.LoadImage(path + '_hot.png')
        self.Fit()

    def Place(self, x, y, w, h, pad):
        self.box = (int(x), int(y), int(w), int(h), int(pad))
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.Fit()

    def Fit(self):
        x, y, w, h, pad = self.box
        for image in (self.calm, self.hot):
            iw, ih = max(1, image.GetWidth()), max(1, image.GetHeight())
            image.SetScale(float(w + 2 * pad) / iw, float(h + 2 * pad) / ih)
            image.SetPosition(-pad, -pad)
            image.Show()

    def Breathe(self, now):
        dt = 0.0 if self.at is None else max(0.0, min(0.1, now - self.at))
        self.at = now
        target = 1.0 if self.selected else (0.45 if self.hovered and self.enabled else 0.0)
        step = dt / (0.15 if target > self.glow else 0.25)
        self.glow = target if abs(target - self.glow) <= step else self.glow + (step if target > self.glow else -step)
        SetColor(self.calm, (1.0, 1.0, 1.0) if self.enabled else (0.5, 0.47, 0.47), 1.0)
        if self.glow <= 0.01:
            self.hot.Hide()
        else:
            SetColor(self.hot, (1.0, 1.0, 1.0), min(1.0, self.glow))
            self.hot.Show()

    def click(self):
        if self.enabled and self.action is not None:
            self.action(self.index)


class CreateChoices(object):
    """The class, gender and type choices of the creation over the column's rows (which are hidden): the class plates
    across the column from where "Povolání" was (the label gone), gender and type in two rows of wide plates
    (owner 11. 10.: the one layout, the dragon plates without portraits, silver captions - tools/
    pregame_create_controls.py)."""

    def __init__(self, hall):
        self.hall, self.column, self.window = hall, hall.column, hall.window
        self.root = ui.Window()
        self.root.SetParent(self.window.dlgBoard)
        self.root.SetPosition(*ScreenOrigin(self.window.dlgBoard))
        self.root.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.root.AddFlag('not_pick')
        self.root.AddFlag('float')
        self.root.Show()
        window = self.window
        jobs = len(self.column.jobRows)
        self.jobs = [Choice(self.root, 'job', i, window.SelectJob) for i in range(jobs)]
        self.genders = [Choice(self.root, 'gender', i, window.SelectGender) for i in range(2)]
        self.shapes = [Choice(self.root, 'shape', i, window.SelectShape) for i in range(2)]
        self.hidden = []
        for widget in list(self.column.jobRows) + list(self.column.gender) + list(self.column.shape) + \
                [self.column.jobLabel]:
            if widget.IsShow():
                widget.Hide()
                self.hidden.append(widget)
        self.home = {}
        for name in ('genderLabel', 'shapeLabel', 'title', 'titleVein') + CREATE_LOWER:
            widget = getattr(self.column, name, None)
            if widget is not None:
                self.home[name] = widget.GetLocalPosition()
        self.root.SetTop()
        self.Layout()
        self.Refresh()

    def Layout(self):
        column = self.column
        x0, top = column.jobRows[0].GetGlobalPosition()
        cw = column.g.cw
        s = cw / 458.0                         # the plates are drawn for a 458 px wide column (1080p)
        jw, jh, jpad = cw, CREATE_SIZE['job'][1] * s, CREATE_SIZE['job'][2] * s
        sw, sh, spad = (cw - 8 * s) / 2.0, CREATE_SIZE['small'][1] * s, CREATE_SIZE['small'][2] * s
        # the title a little higher (owner: "klidně posuň nadpis výš"), the plates from where "Povolání" was
        for name in ('title', 'titleVein'):
            if name in self.home:
                hx, hy = self.home[name]
                getattr(column, name).SetPosition(hx, int(hy - 14 * s))
        ly = column.jobLabel.GetGlobalPosition()[1] - 8 * s
        # the plates as tall as SMAZAT (its dragons whole), small gaps; the name field and the buttons under them.
        # A short screen (DEV 11. 10.: 1280 x 720, 1024 x 768, 800 x 600) shrinks the plates as a whole (width and
        # height together - the dragons are never squashed) so that everything ends above the screen's bottom.
        def label_h(label):
            try:
                return max(16 * s, label.GetTextSize()[1] + 2)
            except Exception:
                return 16 * s
        gap = 4 * s
        lo = [label_h(column.genderLabel), label_h(column.shapeLabel)]
        lower = self.hall.LowerHeight(s) if hasattr(self.hall, 'LowerHeight') else 0
        bottom = column.g.H - 10 * s
        fixed = 4 * gap + gap + lo[0] + 8 * s + lo[1] + 8 * s + 6 * s + lower
        plates = float(4 * jh + 2 * sh)
        k = min(1.0, (bottom - ly - fixed) / plates)
        if k < READABLE:
            # owner 11. 10.: never under the readable minimum - the title and the plates go up towards the top edge
            # instead (the free band above the title), only then the plates shrink under it
            title = column.title.GetGlobalPosition()[1]
            up = min((READABLE - k) * plates, max(0.0, title - 12 * s))
            for name in ('title', 'titleVein'):
                widget = getattr(column, name, None)
                if widget is not None:
                    wx, wy = widget.GetLocalPosition()
                    widget.SetPosition(wx, int(wy - up))
            ly -= up
            k = min(1.0, (bottom - ly - fixed) / plates)
        k = max(0.5, k)
        self.k = k
        jw_k, jh_k, sw_k, sh_k = jw * k, jh * k, sw * k, sh * k
        for i, choice in enumerate(self.jobs):
            choice.Place(x0 + (jw - jw_k) / 2.0, ly + i * (jh_k + gap), jw_k, jh_k, jpad * k)
        y = ly + 4 * (jh_k + gap) + gap
        for n, (label, choices) in enumerate(((column.genderLabel, self.genders), (column.shapeLabel, self.shapes))):
            P.Move(label, int(x0), int(y))
            row = (2 * sw_k + 8 * s * k)
            for i, choice in enumerate(choices):
                choice.Place(x0 + (jw - row) / 2.0 + i * (sw_k + 8 * s * k), y + lo[n], sw_k, sh_k, spad * k)
            y += lo[n] + sh_k + 8 * s
        if 'nameLabel' in self.home:
            ny = column.nameLabel.GetGlobalPosition()[1] - column.nameLabel.GetLocalPosition()[1] + \
                self.home['nameLabel'][1]
            shift = int(round(y + 6 * s - ny))
            for name in CREATE_LOWER:
                if name in self.home:
                    hx, hy = self.home[name]
                    getattr(column, name).SetPosition(hx, hy + shift)

    def Refresh(self):
        window = self.window
        # the column shows its own rows / buttons again on its refresh (e.g. ŽENA for a class that has one)
        for widget in list(self.column.jobRows) + list(self.column.gender) + list(self.column.shape) + \
                [self.column.jobLabel]:
            if widget.IsShow():
                widget.Hide()
                if widget not in self.hidden:
                    self.hidden.append(widget)
        for i, choice in enumerate(self.jobs):
            choice.Load('job_%d' % min(i, 3))
            choice.selected = i == window.job_id
        for i, choice in enumerate(self.genders):
            choice.Load('gender_%d' % i)
            choice.selected = i == window.gender
        try:
            female = window.M2_CONST_ID[window.job_id][1] != -1
        except Exception:
            female = True
        self.genders[1].Show() if female else self.genders[1].Hide()
        for i, choice in enumerate(self.shapes):
            choice.Load('shape_%d' % i)
            choice.selected = i == window.shape

    def SetEnabled(self, enabled):
        for choice in self.jobs + self.genders + self.shapes:
            choice.Enable() if enabled else choice.Disable()

    def Update(self, now):
        for choice in self.jobs + self.genders + self.shapes:
            choice.Breathe(now)

    def Destroy(self):
        self.root.Hide()
        for widget in self.hidden:
            widget.Show()
        for name, pos in self.home.items():
            try:
                getattr(self.column, name).SetPosition(*pos)
            except Exception:
                pass

class CreatePanel(object):
    """What the Scene asks of a panel, for the creation (no rows, no cards: the R1 creation column is the form)."""

    def __init__(self, hall, column):
        self.hall, self.column = hall, column
        W, H = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        s = max(0.72, min(float(W) / 1920.0, float(H) / 1080.0))
        self.g = P.Geo(W, H, s)
        self.bare, self.dialog, self.fx = True, None, None
        self.panelTop = H
        self.hidden = []

    def Count(self):
        return 0

    def ButtonBoxes(self):
        return []

    def OnCard(self, index):
        pass

    def OnCardDouble(self, index):
        pass

    def Detail(self, slot):
        return ('', 0, '')

    def Refresh(self):
        pass

    def SetEnabled(self, enabled):
        pass

    def Destroy(self):
        pass


def BrightBar(bar):
    """A uir1pregame.StatBar readable on the hall's floor: a light edge, a lighter track, a brighter red fill."""
    for name, packed, alpha in (('edge', 0x9A8A84, 1.0), ('track', 0x1A1212, 0.92), ('fill', 0xC0161A, 1.0),
                                ('top', 0xFF5A48, 1.0)):
        widget = getattr(bar, name, None)
        if widget is not None:
            widget.SetColor(uir1.GenerateColor(packed, alpha))


class CreateHall(Hall):
    """Owner 11. 10. ("zkopíruj hlavní menu a spoj ho s vytvořením"): the creation in the same hall as the select -
    the layers, the gate, the light rig, the lightning and the mist of the Scene, the new character in the middle
    place under the light (the same place, size and red light as the selected one in the select), the R1 creation
    column on the left (unchanged in what it does) over a soft shade, VYTVOŘIT (big) and ZPĚT as the obsidian A8
    buttons, the job name and its starting stats under the character. column = uir1pregame.CreateColumn."""

    is_hall = False

    def __init__(self, window, column, cfg):
        self.window, self.rows, self.cfg = window, 0, cfg
        self.column = column
        self.fx = []
        self.hover = None
        self.camera = None
        self.selected = -1
        self.fade = {}
        self.failed = False
        self.uiHidden = False
        self.oldRenderer = getattr(window, 'chrRenderer', None)
        self.placed = None
        # every owner first: a constructor failing half way still tears down what it made (Destroy)
        self.scene = self.panel = self.ticker = self.shadeRoot = self.buttonRoot = self.choices = None
        self.create = self.back = None
        self.destroyed = False
        self.panel = CreatePanel(self, column)
        self.scene = Scene(self)
        self.scene.Place()
        if self.oldRenderer is not None:
            self.oldRenderer.Hide()
        g = self.panel.g
        board = window.dlgBoard
        # the left column over a soft dark shade (the hall stays visible through it)
        self.shadeRoot = ui.Window()
        self.shadeRoot.SetParent(board)
        self.shadeRoot.SetPosition(*ScreenOrigin(board))
        self.shadeRoot.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.shadeRoot.AddFlag('not_pick')
        self.shadeRoot.AddFlag('float')
        self.shadeRoot.Show()
        width = column.g.margin * 2 + column.g.cw + g.P(60)
        steps = 16
        self.shade = []
        for i in range(steps):
            u = i / float(steps - 1)
            rect = uir1.Rect(self.shadeRoot, int(width * i / steps), 0, int(width / steps) + 1, wndMgr.GetScreenHeight(),
                             0x070303, 0.62 * (1.0 - u) ** 1.6)
            self.shade.append(rect)
        self.shadeRoot.SetTop()
        column.root.AddFlag('float')
        column.root.SetTop()
        # the buttons: VYTVOŘIT big (the HRÁT art), ZPĚT small, both with the A8 caption baked in
        self.buttonRoot = ui.Window()
        self.buttonRoot.SetParent(board)
        self.buttonRoot.SetPosition(*ScreenOrigin(board))
        self.buttonRoot.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.buttonRoot.AddFlag('not_pick')
        self.buttonRoot.AddFlag('float')
        self.buttonRoot.Show()
        name = str(cfg.get('buttons', 'obsidian')).lower()
        name = name if name in BUTTON_SETS else 'obsidian'
        self.create = ImageButton(self.buttonRoot, 'hrat', 'VYTVOŘIT', g.caps(BUTTON_FONT['hrat']), column.OnCreate,
                                  name, slug='vytvorit_velke')
        self.back = ImageButton(self.buttonRoot, 'maly', 'ZPĚT', g.caps(BUTTON_FONT['maly']), column.OnBack, name,
                                slug='zpet')
        self.buttonRoot.SetTop()
        for widget in (column.create, column.back):
            widget.Hide()
        # the class / gender / type choices (dragon plates, silver captions)
        self.choices = CreateChoices(self)
        # a thin frame round the name field (the brighter looks)
        self.fieldEdge = []
        field = getattr(column, 'field', None)
        if field is not None:
            fx, fy = field.GetGlobalPosition()
            fw, fh = field.GetWidth(), field.GetHeight()
            for x, y, w, h in ((fx - 1, fy - 1, fw + 2, 1), (fx - 1, fy + fh, fw + 2, 1), (fx - 1, fy, 1, fh),
                               (fx + fw, fy, 1, fh)):
                self.fieldEdge.append(uir1.Rect(self.buttonRoot, x, y, w, h, 0x9A908C, 0.75))
        self.buttonRoot.SetTop()
        self.ApplyStyle()
        self.contact = Sprite(self.scene.under, 'shadow.png')
        self.glow = Sprite(self.scene.under, 'pool.png', True)
        self.statPanel = Sprite(self.shadeRoot, 'shadow.png')          # under the column's stats (its root is above)
        self.Layout()
        self.ticker = Ticker(self)
        self.PlaceCharacter(force=True)

    def Count(self):
        return 0

    def Middle(self):
        for unused, place, ground in self.scene.places:
            if place == 2:
                return ground
        return self.scene.places[0][2]

    def ButtonSizes(self):
        """(w, h) of VYTVOŘIT and of ZPĚT at this screen (the art's own aspect)."""
        g, cw = self.panel.g, self.column.g.cw
        bw = min(cw, g.P(BUTTON_W['hrat']))
        bh = int(round(bw / max(1.5, self.create.Aspect())))
        sw = g.P(BUTTON_W['maly']) * 3 // 4
        sh = int(round(sw / max(1.5, self.back.Aspect())))
        return bw, bh, sw, sh

    def CreateTop(self):
        """y of VYTVOŘIT: under the name field and the line of its error."""
        column = self.column
        field = getattr(column, 'field', None)
        cg = column.g
        if field is not None:
            return field.GetGlobalPosition()[1] + field.GetHeight() + cg.P(8) + cg.P(18)
        return column.create.GetGlobalPosition()[1]

    def LowerHeight(self, s):
        """The name label, the field with its error line and both buttons, from the label's top (CreateChoices)."""
        column, g = self.column, self.panel.g
        unused, bh, unused2, sh = self.ButtonSizes()
        name = column.nameLabel.GetGlobalPosition()[1]
        field = getattr(column, 'field', None)
        fh = (field.GetGlobalPosition()[1] + field.GetHeight() - name) if field is not None else column.g.P(48)
        return fh + column.g.P(8) + column.g.P(18) + bh + g.P(8) + sh

    def Layout(self):
        """The buttons under the form where the column had them; the job name and the stats under the feet."""
        column, g = self.column, self.panel.g
        cg = column.g
        cw = cg.cw
        bw, bh, sw, sh = self.ButtonSizes()
        x = column.nameLabel.GetGlobalPosition()[0]
        y = self.CreateTop()
        # what does not fit above the bottom edge (a short screen) makes both buttons smaller, never cut
        room = cg.H - 10 - y
        need = bh + g.P(8) + sh
        if need > room:
            k = max(READABLE, room / float(need))
            bw, bh, sw, sh = int(bw * k), int(bh * k), int(sw * k), int(sh * k)
        self.create.Resize(bw, bh)
        self.create.SetPosition(x + (cw - bw) // 2, y)
        self.back.Resize(sw, sh)
        self.back.SetPosition(x + (cw - sw) // 2, y + bh + g.P(8))
        cam = self.camera
        feet = cam.Project(self.Middle())
        fx, fy = (feet if feet else (cam.W / 2.0, cam.H * 0.75))
        fy = int(fy) + g.P(14)
        # the job name and the stats right of the column when the screen is narrow (4:3, 800 px): never over it
        lw0, bw0 = cg.P(44), cg.P(136)
        half = (lw0 + bw0 + cg.P(10) + cg.P(22) + cg.P(30) + lw0 + bw0 + cg.P(10) + cg.P(22)) / 2.0 + g.P(55)
        fx = max(fx, x + cw + half + g.P(10))
        fx = min(fx, cam.W - half)
        P.Move(column.jobName, int(fx), fy)
        P.Move(column.statsLabel, int(fx), fy + g.P(38))
        lw, bwid = cg.P(44), cg.P(136)
        colw = lw + bwid + cg.P(10) + cg.P(22) + cg.P(30)
        column.stats.Place(int(fx) - (colw + lw + bwid + cg.P(10) + cg.P(22)) // 2, fy + g.P(62), colw)
        # owner 11. 10.: readable on the red floor - a soft dark panel under the stats block, cream texts, the bars
        # with a brighter red fill and a light edge (the job name stays as it is)
        blockw = colw + lw + bwid + cg.P(10) + cg.P(22)
        blockh = g.P(62) + cg.P(30) + cg.P(20) - g.P(30)
        self.statPanel.Place(int(fx), fy + g.P(30) + blockh / 2, blockw + g.P(110), blockh + g.P(60), (1.0, 1.0, 1.0),
                             0.88)
        P.SetColor(column.statsLabel, 0xFFE4D6CA)
        for widget in list(column.stats.labels) + list(column.stats.values):
            P.SetColor(widget, 0xFFF2E6D8)
        for bar in column.stats.bars:
            BrightBar(bar)

    def Races(self):
        """Every race instance the creation window made (new_introcreate.MakeCharacter: per job and sex)."""
        races = set()
        for pair in getattr(self.window, 'M2_CONST_ID', ()) or ():
            try:
                for race in pair:
                    if race is not None and race >= 0:
                        races.add(race)
            except TypeError:
                pass
        return sorted(races)

    def OnlyRace(self, restore=False):
        """Only the selected race shown (VPS 11. 10., owner: after shrinking the window the preview characters of
        the classes stood on top of each other until a class was clicked): the others hidden; restore = the selected
        one shown again in its idle loop, as after a click (new_introcreate.SelectShape)."""
        race = getattr(self.window, 'race', -1)
        for other in self.Races():
            if other != race and chr.HasInstance(other):
                chr.SelectInstance(other)
                chr.Hide()
        if race is not None and race >= 0 and chr.HasInstance(race):
            chr.SelectInstance(race)
            if restore:
                try:
                    chr.SetMotionMode(chr.MOTION_MODE_GENERAL)
                    chr.SetLoopMotion(chr.MOTION_INTRO_WAIT)
                except Exception:
                    pass
                chr.Show()

    def PlaceCharacter(self, force=False):
        """The window's current race instance on the middle place (the rig's light), turned to the camera."""
        race = getattr(self.window, 'race', -1)
        if race is None or race < 0 or not chr.HasInstance(race):
            return
        if force:
            self.OnlyRace(restore=True)
        if not force and race == self.placed:
            return
        s, centre = self.scene.LightScale()
        ground = self.Middle()
        p = _sub(ground, centre)
        cam = self.camera
        turn = math.degrees(math.atan2(cam.Lateral(ground), cam.Depth(ground)))
        chr.SelectInstance(race)
        chr.SetPixelPosition(int(round(p[0])), int(round(-p[1])), 0)
        chr.SetRotation(-0.7 * turn)
        tint = Tint(self.cfg)
        chr.testSetModulateRenderModeRGB(race, *tint)
        self.placed = race

    def Refresh(self):
        self.PlaceCharacter(force=True)
        self.Layout()
        if self.choices is not None:
            self.choices.Refresh()

    def SetEnabled(self, enabled):
        if self.back is not None:
            self.back.Enable() if enabled else self.back.Disable()
        if self.choices is not None:
            self.choices.SetEnabled(enabled)

    def ApplyStyle(self):
        """The grey look's companions on the creation: brighter labels of the column, a lighter shade, a light frame
        round the name field."""
        column = self.column
        for name, colour in (('title', T.IVORY), ('jobLabel', TEXT_DIM), ('genderLabel', TEXT_DIM),
                             ('shapeLabel', TEXT_DIM), ('nameLabel', TEXT_DIM), ('counter', TEXT_MUTED),
                             ('statsLabel', TEXT_MUTED)):
            widget = getattr(column, name, None)
            if widget is not None:
                P.SetColor(widget, colour)
        for i, rect in enumerate(self.shade):
            u = i / float(max(1, len(self.shade) - 1))
            rect.SetColor(uir1.GenerateColor(0x070303, 0.40 * (1.0 - u) ** 1.6))
        for rect in self.fieldEdge:
            rect.SetColor(uir1.GenerateColor(*FIELD_EDGE))
            rect.Show()

    def Update(self):
        now = app.GetTime()
        self.PlaceCharacter()
        if now - getattr(self, 'onlyAt', -1.0) >= 0.5:      # nothing else shows a class's preview behind our back
            self.onlyAt = now
            self.OnlyRace()
        self.scene.Update(now)
        self.MusicToast(now)
        # VYTVOŘIT follows the column's own (the name rules decide)
        enabled = getattr(self.column.create, 'enabled', True)
        if enabled != self.create.enabled:
            self.create.Enable() if enabled else self.create.Disable()
        cam, sc = self.camera, self.camera.scale
        feet = cam.Project(self.Middle())
        if feet is not None:
            self.contact.Place(feet[0], feet[1], 150 * sc, 34 * sc, (1.0, 1.0, 1.0), 0.75)
            self.glow.Place(feet[0], feet[1] + 4 * sc, 260 * sc, 60 * sc, RED,
                            0.22 + 0.06 * math.sin(now * 1.7))
        for button in (self.create, self.back):
            button.Breathe(now)
        if self.choices is not None:
            self.choices.Update(now)

    def Destroy(self):
        """Back to the creation as before the hall (also after a partial construction): the column's own buttons,
        the old renderer, background and emblem, the actor at the old renderer's origin."""
        if self.destroyed:
            return
        self.destroyed = True
        if self.ticker is not None:
            self.ticker.Hide()
            self.ticker.hall = None
        if self.scene is not None:
            self.scene.Destroy()
        for root in (self.shadeRoot, self.buttonRoot):
            if root is not None:
                root.Hide()
        if self.choices is not None:
            self.choices.Destroy()
        for widget in (getattr(self.column, 'create', None), getattr(self.column, 'back', None)):
            try:
                widget.Show()
            except Exception:
                pass
        if self.oldRenderer is not None:
            self.oldRenderer.Show()
        try:
            self.window.brandMark.Show()
        except Exception:
            pass
        race = getattr(self.window, 'race', None)
        try:
            self.OnlyRace()
        except Exception:
            pass
        # Every visited race keeps its hall transform while hidden. The fallback's
        # SelectShape only shows it again, so restore all creation actors here.
        actors = set(self.Races())
        actors.update(r for r in (self.placed, race) if r is not None and r >= 0)
        for actor in actors:
            if chr.HasInstance(actor):
                chr.testRestoreRenderMode(actor)
                chr.SelectInstance(actor)
                chr.SetPixelPosition(0, 0, 0)
                chr.SetRotation(-7.0)
        if race is not None and race >= 0 and chr.HasInstance(race):
            chr.SelectInstance(race)          # the window's later chr.* calls act on its actor

    def Undo(self):
        """A failed creation hall: the column alone (its layout, its buttons), never the hall again here."""
        try:
            self.Destroy()
        except Exception:
            pass
        if getattr(self.column, 'hall', None) is self:
            self.column.hall = None
        try:
            self.column.Layout()
        except Exception:
            pass


def AttachCreate(window, column):
    """The creation in the hall for new_introcreate (column = uir1pregame.CreateColumn), or None (switched off, too
    small a screen, or it failed: the column alone as before)."""
    cfg = Config()
    if cfg['off'] or not cfg.get('create', 1) or wndMgr.GetScreenWidth() < MIN_SCREEN[0] or \
            wndMgr.GetScreenHeight() < MIN_SCREEN[1]:
        return None
    # keep ownership even when a nested constructor fails after hiding the old scene
    hall = CreateHall.__new__(CreateHall)
    try:
        hall.__init__(window, column, cfg)
        return hall
    except Exception:
        uir1.TraceFailure('pregame hall create')
        hall.Undo()
        return None

# =========================================================================== v5 particles + gate hover (fx-v5)
# Owner 10. 10. night: "the red ones that are there all the time" - sparks, glowing embers, ash and mist in the hall and
# at the gate - livelier and less flat; the gate answers the mouse more clearly but with taste. Everything below is
# one block (merge friendly): Scene builds the Ambience through MakeAmbience; particles=v4 brings back the old ones.
FX5_CFG = {
    # v5 = the particles below; v4 = the previous portal embers / streaks / bursts / ash
    'particles': 'v5',
    # counts (0 = off): glowing embers in the hall air, sparks out of the gate (idle / while the gate is hovered),
    # ash flakes, mist puffs rolling out of the gate over the floor
    'fxembers': 20, 'fxsparks': 9, 'fxsparksmax': 18, 'fxash': 9, 'fxgatemist': 6,
    # brightness of the embers + sparks (1 = default), depth of field (0 = everything sharp), brightness flicker
    # depth, ash and gate mist strength
    'fxglow': 1.0, 'fxdof': 1.0, 'fxflicker': 1.0, 'fxashalpha': 0.7, 'fxmist': 0.09,
    # gate hover: pull of the particles into the gate, the wave from its centre, the short breath of light
    'fxpull': 0.0, 'fxwave': 0.0, 'fxbreath': 0.0,
    # owner 11. 10.: "efekt výbuchu v portálu se mi nelíbí, to vrať, ale partikly jsou dobré" - the gate answers the
    # hover as in v4 again (rim, haze, more sparks); the wave, the breath of light, the pull and the sparks released
    # on every heartbeat are off (fxwave / fxbreath / fxpull / fxbeat > 0 bring them back)
    'fxbeat': 0,
}
CFG.update(FX5_CFG)

FX5_TEX = {'spark': 'fx_spark.png', 'bokeh': 'fx_bokeh.png', 'streak': 'fx_streak.png', 'flake': 'fx_flake.png',
           'wave': 'fx_wave.png'}
FX5_FALLBACK = {'spark': 'dot.png', 'bokeh': 'glow.png', 'streak': 'dot.png', 'flake': 'dot.png', 'wave': 'ring.png'}
# ember colours by heat: cool blood red -> red -> hot orange; additive red on the red portal would vanish, so the
# cores burn hotter (orange) than their red glow
FX5_COOL, FX5_MID, FX5_HOT = (0.78, 0.07, 0.04), (1.0, 0.24, 0.08), (1.0, 0.62, 0.32)


def MakeAmbience(scene):
    if str(scene.hall.cfg.get('particles', 'v5')) == 'v4':
        return Ambience(scene)
    return Ambience5(scene)


def FxTexture(key):
    name = FX5_TEX[key]
    return name if Exists(ASSET + name) else FX5_FALLBACK[key]


def Heat(heat):
    """Ember colour for heat 0 (cooling) .. 1 (hot)."""
    heat = max(0.0, min(1.0, heat))
    if heat < 0.5:
        a, b, k = FX5_COOL, FX5_MID, heat / 0.5
    else:
        a, b, k = FX5_MID, FX5_HOT, (heat - 0.5) / 0.5
    return (a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k)


class Duo(object):
    """One particle image in two roots: behind the characters (Scene.under) or in front of them (Scene.over), picked
    by the particle's depth each frame - a particle flying past the characters crosses them correctly."""

    def __init__(self, back, front, name, additive, angled=False):
        self.sprites = (Sprite(back, name, additive), Sprite(front, name, additive))
        self.angled = angled
        for sprite in self.sprites:
            if angled:
                sprite.Pivot()
            sprite.Hide()

    def Place(self, front, cx, cy, w, h, rgb, alpha, angle=0.0):
        on, off = (self.sprites[1], self.sprites[0]) if front else self.sprites
        if off.IsShow():
            off.Hide()
        if self.angled:
            on.PlaceAngled(cx, cy, w, h, angle, rgb, alpha)
        else:
            on.Place(cx, cy, w, h, rgb, alpha)

    def Hide(self):
        for sprite in self.sprites:
            if sprite.IsShow():
                sprite.Hide()

    def IsShow(self):
        return self.sprites[0].IsShow() or self.sprites[1].IsShow()

    def Shown(self):
        for sprite in self.sprites:
            if sprite.IsShow():
                return sprite
        return None


class Particle(object):
    __slots__ = ('kind', 'p', 'v', 'age', 'life', 'size', 'seed', 'heat', 'fade', 'wait', 'prev', 'spin')

    def __init__(self, seed):
        self.kind, self.p, self.v = None, (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
        self.age, self.life, self.size, self.seed, self.heat = 0.0, 1.0, 1.0, seed, 1.0
        self.fade, self.wait, self.prev, self.spin = 0.0, 0.0, None, 0.0


class Ambience5(Ambience):
    """The v3 scene (Ambience) with the v5 particles (HallFX) in place of the v4 portal embers, streaks, bursts and
    ash; the lanterns, the haze, rays, crackle and the floor mist stay the base class's."""

    def __init__(self, scene):
        Ambience.__init__(self, scene)
        retired = [e[0] for e in self.embers] + list(self.streaks) + [b[0] for b in self.burst] + [a[0] for a in self.ash]
        for sprite in retired:
            sprite.Hide()
        self.retired = retired
        self.embers, self.streaks, self.burst, self.ash = [], [], [], []
        self.fx = HallFX(self)

    def Update(self, now):
        Ambience.Update(self, now)
        self.fx.Update(now)


class HallFX(object):
    """Real 3D particles in the hall air (projected by the hall camera, so they sit in depth and shift with the
    parallax like the characters):
      embers  - glowing embers rising slowly on a gentle draft out of the gate, turbulent but smooth paths (the
                velocity eases towards a slowly changing flow, never jumps), each its own size, heat and flicker;
      sparks  - quick sparks out of the gate's depth with a motion streak, released with the gate's heartbeat;
      ash     - dark flakes tumbling down, a few still smouldering;
      mist    - low puffs rolling out of the gate over the floor.
    Depth: the nearer, the bigger; out of the focus plane (the characters) a particle grows into a soft disc and its
    light spreads (dimmer core: the same energy), the far ones are small, dimmer and redder (the haze). Additive.
    The gate hover (Ambience.portal / zone 'portal'): a wave runs out of its centre (the arch and the floor), the
    gate takes a short breath of light (rim, inner glow, floor reflection) and pulls the particles in, spiralling
    (embers, sparks, ash, the mist rolls back); on leaving everything eases back - nothing snaps."""

    BEAT = 0.8                      # Pulse() level that releases waiting sparks

    def __init__(self, amb):
        self.amb, self.scene, self.hall, self.cfg = amb, amb.scene, amb.hall, amb.cfg
        cfg, scene, cam = self.cfg, self.scene, self.hall.camera
        self.rnd = random.Random(5005)
        back, front = scene.under, scene.over
        # the hall frame: x to the right, y towards the eye (the wall at y < 0), z up, origin on the floor under the
        # eye - whatever way the engine's select camera faces (Scene.Camera), the particles live in this frame
        self.origin = (cam.eye0[0], cam.eye0[1], 0.0)
        self.right, self.toEye = _scale(cam.x0, -1.0), cam.back
        foot = cam.Floor(960.0, V3_HORIZON + 8.0)
        ground = self.Local(foot)
        self.wallY = ground[1]
        self.centre = (ground[0], ground[1] - 40.0, cam.Lift(foot, 960.0, 430.0))      # the gate's heart, just inside
        self.archZ = cam.Lift(foot, 960.0, V3_ARCH[3])
        self.archX = abs(self.Local(cam.Floor(V3_ARCH[0], V3_HORIZON + 8.0))[0] - ground[0])
        self.threshold = (ground[0], ground[1] + 30.0, 0.0)
        self.focus = scene.depthFloor
        self.hover = 0.0            # eased gate hover 0..1 (rise 0.3 s, fall 0.9 s)
        self.breath = 0.0           # the breath of light (envelope after each wave)
        self.waves = []             # start times
        self.lastWave, self.wasIn, self.lastBeat, self.weight = -99.0, False, 0.0, {}
        self.last = None
        tex = dict((key, FxTexture(key)) for key in FX5_TEX)
        n = lambda key: max(0, int(cfg.get(key, 0)))
        # the gate's light: a soft glow in its heart (the breath), waves (arch ring + floor ripple)
        self.heart = [Sprite(back, 'glow.png', True), Sprite(back, 'glow.png', True)]
        self.waveArch = [Sprite(back, tex['wave'], True) for unused in range(2)]
        self.waveFloor = [Sprite(back, tex['wave'], True) for unused in range(2)]
        self.mist = []
        for i in range(n('fxgatemist')):
            self.mist.append([Sprite(back, ('haze_b.png', 'haze_a.png')[i % 2], True), (i + 0.5) / max(1, n('fxgatemist')),
                              self.rnd.uniform(-1.0, 1.0), self.rnd.uniform(0.8, 1.25)])
        self.embers = []
        for i in range(n('fxembers')):
            part = Particle(100 + i)
            part.wait = 0.0
            self.embers.append((part, Duo(back, front, 'glow.png', True), Duo(back, front, tex['spark'], True),
                                Duo(back, front, tex['bokeh'], True)))
        self.sparks = []
        for i in range(max(n('fxsparks'), n('fxsparksmax'))):
            part = Particle(300 + i)
            part.wait = self.rnd.uniform(0.0, 2.0)
            self.sparks.append((part, Duo(back, front, tex['streak'], True, angled=True), Duo(back, front, tex['spark'], True)))
        self.ash = []
        for i in range(n('fxash')):
            part = Particle(500 + i)
            self.ash.append((part, Duo(back, front, tex['flake'], False, angled=True), Duo(back, front, 'glow.png', False),
                             Duo(back, front, tex['spark'], True)))
        # the hall is never empty: every ember / flake starts somewhere in its life
        for part, a, b, c in self.embers:
            self.SpawnEmber(part, 0.0, scatter=True)
        for part, a, b, c in self.ash:
            self.SpawnAsh(part, scatter=True)

    # ------------------------------------------------------------------ helpers
    def World(self, p):
        o, r, b = self.origin, self.right, self.toEye
        return (o[0] + r[0] * p[0] + b[0] * p[1], o[1] + r[1] * p[0] + b[1] * p[1], p[2])

    def Local(self, w):
        d = (w[0] - self.origin[0], w[1] - self.origin[1], 0.0)
        return (_dot(d, self.right), _dot(d, self.toEye), w[2])

    def Depth(self, p):
        return self.hall.camera.Depth(self.World(p))

    def HalfWidth(self, depth):
        cam = self.hall.camera
        return depth * cam.W / 2.0 / cam.F

    def Top(self, depth):
        return min(560.0, 85.0 + 0.33 * depth)

    def Visible(self, p):
        """Behind the wall a particle shows only through the gate's opening."""
        if p[1] >= self.wallY:
            return 1.0
        cam = self.hall.camera
        q = cam.Project(self.World(p))
        if q is None:
            return 0.0
        px, py = self.amb.Plate(q[0], q[1], self.amb.back.depth['wall'])
        return 1.0 if InArch(px, py) else 0.0

    def Look(self, p, radius):
        """(screen x, y, core px, blur px, depth) of a particle of ``radius`` cm, or None."""
        cam = self.hall.camera
        q = cam.Project(self.World(p))
        if q is None:
            return None
        depth = cam.Depth(self.World(p))
        core = max(2.0, 2.0 * radius * cam.PixelsPerUnit(self.World(p)))
        k = (16.0 if depth < self.focus else 5.0) * float(self.cfg.get('fxdof', 1.0)) * cam.H / 1080.0
        blur = k * abs(depth - self.focus) / max(1.0, depth)
        return q[0], q[1], core, blur, depth

    def Flow(self, p, now, seed):
        """The slow air of the hall at p: a draft out of the gate towards the viewer + smooth turbulence."""
        dx, dy = p[0] - self.centre[0], p[1] - self.wallY
        draft = 16.0 * math.exp(-max(0.0, dy) / 700.0)
        s = seed * 1.7
        tx = 13.0 * math.sin(p[2] * 0.011 + now * 0.31 + s) + 6.0 * math.sin(p[1] * 0.006 - now * 0.23 + s * 2.1)
        ty = 8.0 * math.sin(p[0] * 0.009 + now * 0.27 + s * 1.3)
        tz = 9.0 * math.sin(p[0] * 0.013 + p[1] * 0.007 + now * 0.37 + s * 0.7)
        return (dx * 0.015 + tx, draft + ty, tz)

    def Pull(self, p, strength):
        """Velocity (cm/s) into the gate: towards its heart and around it (a slow spiral), stronger near it."""
        c = self.centre
        d = (c[0] - p[0], c[1] - p[1], c[2] - p[2])
        dist = math.sqrt(_dot(d, d)) or 1.0
        u = (d[0] / dist, d[1] / dist, d[2] / dist)
        speed = strength * (0.45 + 0.55 * math.exp(-dist / 700.0))
        swirl = (u[2], 0.0, -u[0])
        return (u[0] * speed + swirl[0] * speed * 0.45, u[1] * speed, u[2] * speed + swirl[2] * speed * 0.45)

    @staticmethod
    def Ease(v, target, dt, tau):
        k = 1.0 - math.exp(-dt / max(0.01, tau))
        return (v[0] + (target[0] - v[0]) * k, v[1] + (target[1] - v[1]) * k, v[2] + (target[2] - v[2]) * k)

    # ------------------------------------------------------------------ spawning
    def SpawnEmber(self, part, now, scatter=False):
        rnd = self.rnd
        part.seed = rnd.randint(0, 99999)
        part.size = 0.6 + 1.5 * rnd.random() ** 2.2            # many small, a few big (radius, cm)
        part.life = rnd.uniform(7.0, 13.0)
        part.age = rnd.uniform(0.0, part.life * 0.8) if scatter else 0.0
        part.heat = rnd.uniform(0.55, 1.0)
        part.fade = 0.0
        part.prev = None
        pull = self.hover * float(self.cfg.get('fxpull', 1.0))
        roll = rnd.random()
        if roll < 0.35 and pull < 0.5:
            # out of the gate's glow on the threshold
            x = self.centre[0] + rnd.uniform(-1.0, 1.0) * self.archX * 1.2
            y = self.wallY + rnd.uniform(10.0, 220.0)
            z = rnd.uniform(0.0, 90.0)
            part.kind = 'gate'
        else:
            # the hall air; a quarter of them close to the eye (big, out of focus: the depth)
            depth = rnd.uniform(330.0, 520.0) if roll > 0.75 else rnd.uniform(560.0, 1220.0)
            y = -depth
            x = self.centre[0] + rnd.uniform(-0.85, 0.85) * self.HalfWidth(depth)
            z = rnd.uniform(0.0, 0.4) ** 1.3 * self.Top(depth)
            part.kind = 'hall'
        if scatter:
            z = min(self.Top(-y) * 0.9, z + 11.0 * part.age)
            y += 9.0 * part.age if part.kind == 'gate' else 0.0
        part.p = (x, y, z)
        part.v = (0.0, 12.0, 10.0)

    def SpawnSpark(self, part, now, inward):
        rnd = self.rnd
        part.seed = rnd.randint(0, 99999)
        part.size = 0.35 + 0.6 * rnd.random() ** 2
        part.age, part.fade, part.prev = 0.0, 0.0, None
        part.heat = 1.0
        c = self.centre
        if inward:
            # somewhere in the hall air in front of the gate: it is drawn in
            side = 1.0 if rnd.random() < 0.5 else -1.0
            x = c[0] + side * rnd.uniform(self.archX * 1.3, self.archX * 3.6)
            y = self.wallY + rnd.uniform(60.0, 520.0)
            z = rnd.uniform(40.0, self.archZ * 0.8)
            part.p, part.v = (x, y, z), (0.0, 0.0, 0.0)
            part.life = 2.6
            part.kind = 'in'
        else:
            for unused in range(4):
                x = c[0] + rnd.uniform(-0.8, 0.8) * self.archX
                y = self.wallY - rnd.uniform(60.0, 480.0)
                z = rnd.uniform(60.0, self.archZ * 0.75)
                if self.Visible((x, y, z)):
                    break
            part.p = (x, y, z)
            part.v = ((x - c[0]) * 0.6 + rnd.uniform(-60.0, 60.0), rnd.uniform(300.0, 560.0), rnd.uniform(15.0, 70.0))
            part.life = rnd.uniform(2.2, 3.4)
            part.kind = 'out'

    def SpawnAsh(self, part, scatter=False):
        rnd = self.rnd
        part.seed = rnd.randint(0, 99999)
        part.size = 1.6 + 2.2 * rnd.random() ** 1.5
        depth = rnd.uniform(450.0, 1250.0)
        top = self.Top(depth)
        z = rnd.uniform(0.15, 1.0) * top if scatter else rnd.uniform(0.8, 1.0) * top
        # most of it falls in front of the gate: there it reads, dark against the glow
        spread = self.archX * 2.2 if rnd.random() < 0.6 else 0.8 * self.HalfWidth(depth)
        part.p = (self.centre[0] + rnd.uniform(-1.0, 1.0) * spread, -depth, z)
        part.v = (0.0, 0.0, -8.0)
        part.age, part.fade, part.prev = 0.0, 0.0, None
        part.life = 999.0
        part.heat = rnd.random() if rnd.random() < 0.35 else 0.0     # a third still smoulder
        part.spin = rnd.uniform(1.2, 2.8) * (1.0 if rnd.random() < 0.5 else -1.0)
        part.kind = 'ash'

    # ------------------------------------------------------------------ every frame
    def Update(self, now):
        cfg = self.cfg
        dt = 0.0 if self.last is None else max(0.0, min(0.1, now - self.last))
        self.last = now
        inside = self.amb.zone[0] == 'portal'
        target = 1.0 if inside else 0.0
        self.hover = self.hover + (target - self.hover) * (1.0 - math.exp(-dt / (0.3 if inside else 0.9)))
        if inside and (not self.wasIn or now - self.lastWave >= 2.6) and now - self.lastWave >= 0.8:
            # the first wave of a hover is full, the repeats while the mouse stays only about half
            self.weight[now] = 1.0 if not self.wasIn else 0.55
            self.waves.append(now)
            self.waves = self.waves[-2:]
            self.weight = dict((t, self.weight[t]) for t in self.waves)
            self.lastWave = now
        self.wasIn = inside
        # the breath of light: in 0.3 s up, then back down over ~1 s; the newest wave drives it
        b = 0.0
        for start in self.waves:
            t = now - start
            b = max(b, Smooth(t / 0.3) * math.exp(-max(0.0, t - 0.3) / 0.9) * self.weight.get(start, 1.0))
        self.breath = b * float(cfg.get('fxbreath', 1.0))
        self.Light(now)
        self.Waves(now)
        self.Mist(now, dt)
        self.Embers(now, dt)
        self.Sparks(now, dt)
        self.Ash(now, dt)

    def Light(self, now):
        """The breath on the rim, the floor reflection and the shimmer (Backdrop3 reads ``levels`` after us) and a
        soft glow in the gate's heart."""
        levels, b, h = self.amb.back.levels, self.breath, self.hover
        for name, k in (('G_rim', 0.9), ('R_portal', 0.8), ('P_shimmer', 0.6)):
            if name in levels:
                alpha, rgb = levels[name]
                levels[name] = (min(0.5 if name == 'P_shimmer' else 1.0, alpha * (1.0 + k * b)), rgb)
        cam = self.hall.camera
        q = cam.Project(self.World(self.centre))
        if q is None:
            for sprite in self.heart:
                sprite.Hide()
            return
        ppu = cam.PixelsPerUnit(self.World(self.centre))
        beat = self.amb.pulse
        k = min(1.0, float(self.cfg.get('fxbreath', 1.0)))
        size = 2.2 * self.archX * ppu * (0.85 + 0.25 * b + 0.1 * h)
        self.heart[0].Place(q[0], q[1], size, size * 1.35, (1.0, 0.18, 0.08),
                            min(0.4, k * (0.06 * h + 0.02 * beat) + 0.24 * b))
        core = size * 0.38
        self.heart[1].Place(q[0], q[1] + core * 0.1, core, core * 1.2, (1.0, 0.45, 0.2), min(0.35, 0.18 * b + 0.04 * h * k))

    def Waves(self, now):
        cam, cfg = self.hall.camera, self.cfg
        strength = float(cfg.get('fxwave', 0.5))
        for i in range(2):
            ring, floor = self.waveArch[i], self.waveFloor[i]
            if i >= len(self.waves) or strength <= 0:
                ring.Hide()
                floor.Hide()
                continue
            t = (now - self.waves[-1 - i]) / 1.5
            if t >= 1.0:
                ring.Hide()
                floor.Hide()
                continue
            grow = 1.0 - (1.0 - t) ** 3
            fade = Smooth(t / 0.08) * (1.0 - t) ** 1.6 * self.weight.get(self.waves[-1 - i], 1.0)
            q = cam.Project(self.World(self.centre))
            if q is not None:
                r = (0.12 + 1.15 * grow) * self.archX * cam.PixelsPerUnit(self.World(self.centre)) * 2.0
                ring.Place(q[0], q[1] - r * 0.08, r, r * 1.3, (1.0, 0.36, 0.16), min(1.0, strength * fade))
            e = cam.Ellipse(self.World(self.threshold), 40.0 + 420.0 * grow)
            if e is not None:
                floor.Place(e[0][0], e[0][1], e[1], e[2], (1.0, 0.32, 0.14), min(1.0, 0.7 * strength * fade))

    def Mist(self, now, dt):
        """Puffs rolling out of the gate over the floor; while hovered they roll back in."""
        cam, cfg = self.hall.camera, self.cfg
        strength = float(cfg.get('fxmist', 0.09))
        pull = self.hover * float(cfg.get('fxpull', 1.0))
        rate = 0.055 * (1.0 - 2.4 * pull)
        for puff in self.mist:
            sprite, u, side, size = puff
            u = (u + dt * rate * size) % 1.0
            puff[1] = u
            if strength <= 0:
                sprite.Hide()
                continue
            x = self.centre[0] + side * (40.0 + 240.0 * u) * (0.4 + 0.6 * u)
            y = self.wallY + 20.0 + 520.0 * u
            p = (x, y, 6.0)
            q = cam.Project(self.World(p))
            if q is None:
                sprite.Hide()
                continue
            w = (180.0 + 260.0 * u) * size * cam.PixelsPerUnit(self.World(p))
            alpha = strength * math.sin(math.pi * u) ** 1.5 * (0.85 + 0.3 * self.amb.pulse) * (1.0 + 0.6 * pull)
            sprite.Place(q[0], q[1] - w * 0.06, w, w * 0.26, (0.95, 0.14, 0.08), min(0.4, alpha))

    def Embers(self, now, dt):
        cam, cfg = self.hall.camera, self.cfg
        glow, flick_k = float(cfg.get('fxglow', 1.0)), float(cfg.get('fxflicker', 1.0))
        pull = self.hover * float(cfg.get('fxpull', 1.0))
        focus = self.focus
        wallDepth = self.amb.back.depth['wall']
        for part, halo, core, soft in self.embers:
            if glow <= 0:
                halo.Hide(), core.Hide(), soft.Hide()
                continue
            part.age += dt
            flow = self.Flow(part.p, now, part.seed)
            buoy = 6.0 + 12.0 * part.heat
            want = (flow[0], flow[1], flow[2] + buoy)
            if pull > 0.001:
                pv = self.Pull(part.p, 260.0 * pull)
                want = (want[0] * (1.0 - pull) + pv[0], want[1] * (1.0 - pull) + pv[1], want[2] * (1.0 - pull) + pv[2])
            part.v = self.Ease(part.v, want, dt, 0.9 - 0.55 * pull)
            part.p = _add(part.p, part.v, dt)
            depth = self.Depth(part.p)
            gone = part.age >= part.life or part.p[2] > self.Top(depth) or part.p[2] < -5.0 or depth < 250.0
            if part.p[1] < self.wallY:          # drawn into the gate: it fades in its depth
                part.fade = min(1.0, part.fade + dt / 0.45)
                if part.fade >= 1.0 or not self.Visible(part.p):
                    gone = True
            elif abs(part.p[0] - self.centre[0]) > self.HalfWidth(depth) * 1.1:
                gone = True
            if gone:
                self.SpawnEmber(part, now)
                halo.Hide(), core.Hide(), soft.Hide()
                continue
            look = self.Look(part.p, part.size)
            if look is None:
                halo.Hide(), core.Hide(), soft.Hide()
                continue
            x, y, c, blur, depth = look
            life = Smooth(part.age / 1.2) * (1.0 - Smooth((part.age - part.life + 2.5) / 2.5)) * (1.0 - part.fade)
            n = _vnoise(now * 1.7 + part.seed * 0.01, part.seed)
            flare = max(0.0, _vnoise(now * 0.6, part.seed + 7) - 0.8) * 3.0           # now and then it flares up
            bright = 1.0 + flick_k * (0.45 * (n - 0.5) + 0.6 * flare)
            heat = part.heat * (1.0 - 0.55 * part.age / part.life) * (0.85 + 0.3 * n)
            haze = Smooth((depth - focus) / max(1.0, wallDepth - focus))
            colour = Heat(heat)
            colour = (colour[0], colour[1] * (1.0 - 0.5 * haze), colour[2] * (1.0 - 0.5 * haze))
            hot = Heat(heat + 0.4 * (1.0 - haze))                  # the core burns hotter than its glow
            size = math.sqrt(c * c + blur * blur)
            energy = max(0.12, (c / size) ** 1.4)
            w = Smooth((blur / c - 0.7) / 1.6)
            alpha = glow * life * bright * (1.0 - 0.35 * haze)
            front = depth < focus
            core.Place(front, x, y, c * 5.0, c * 5.0, hot, min(1.0, alpha * energy * (1.0 - w)))
            soft.Place(front, x, y, size * 1.1, size * 1.1, colour, min(0.55, 0.75 * alpha * energy * w))
            hs = c * 9.0 + blur * 1.5
            halo.Place(front, x, y, hs, hs, colour, min(0.4, 0.3 * alpha * (0.5 + heat) * (1.0 - 0.6 * w)))

    def Sparks(self, now, dt):
        cam, cfg = self.hall.camera, self.cfg
        glow = float(cfg.get('fxglow', 1.0))
        pull = self.hover * float(cfg.get('fxpull', 1.0))
        idle, most = float(cfg.get('fxsparks', 9)), float(cfg.get('fxsparksmax', 18))
        active = int(round(idle + (max(idle, most) - idle) * self.hover))
        beat = self.amb.pulse
        released = beat >= self.BEAT > self.lastBeat
        self.lastBeat = beat
        free = 3 if (released and cfg.get('fxbeat', 0)) else 0
        for i, (part, streak, core) in enumerate(self.sparks):
            if glow <= 0 or i >= active and part.kind is None:
                streak.Hide(), core.Hide()
                continue
            if part.kind is None:
                part.wait -= dt
                inward = pull > 0.3 and self.rnd.random() < pull
                if part.wait <= 0.0 and (free > 0 or inward or part.wait < -2.5):
                    if not inward:
                        free -= 1
                    self.SpawnSpark(part, now, inward)
                else:
                    streak.Hide(), core.Hide()
                    continue
            part.age += dt
            if part.kind == 'in':
                pv = self.Pull(part.p, 330.0 + 160.0 * pull)
                part.v = self.Ease(part.v, pv, dt, 0.35)
            else:
                drift = self.Flow(part.p, now, part.seed)
                want = (drift[0], drift[1] + 20.0, drift[2] + 25.0)
                if pull > 0.001:
                    pv = self.Pull(part.p, 300.0 * pull)
                    want = (want[0] * (1.0 - pull) + pv[0], want[1] * (1.0 - pull) + pv[1],
                            want[2] * (1.0 - pull) + pv[2])
                part.v = self.Ease(part.v, want, dt, 2.2 - 1.6 * pull)
            prev = part.p
            part.p = _add(part.p, part.v, dt)
            part.heat = max(0.0, 1.0 - part.age / part.life)
            depth = self.Depth(part.p)
            gone = part.age >= part.life or depth < 260.0
            if part.p[1] < self.wallY and not self.Visible(part.p):
                gone = gone or part.kind == 'in' or part.age > 0.3
            if part.kind == 'in' and part.p[1] < self.wallY - 60.0:
                part.fade = min(1.0, part.fade + dt / 0.3)
                gone = gone or part.fade >= 1.0
            if gone:
                part.kind, part.wait = None, (0.0 if self.hover > 0.5 else self.rnd.uniform(0.2, 1.4))
                streak.Hide(), core.Hide()
                continue
            look = self.Look(part.p, part.size)
            q0 = cam.Project(self.World(prev))
            if look is None or q0 is None:
                streak.Hide(), core.Hide()
                continue
            x, y, c, blur, depth = look
            if part.kind == 'in':
                env = Smooth(part.age / 0.35) * (1.0 - part.fade)
            else:
                env = Smooth(part.age / 0.06) * (1.0 - Smooth((part.age - part.life * 0.55) / (part.life * 0.45)))
            colour = Heat(0.35 + 0.65 * part.heat)
            alpha = glow * env * (0.8 + 0.2 * _vnoise(now * 9.0, part.seed))
            front = depth < self.focus
            size = math.sqrt(c * c + blur * blur)
            energy = max(0.15, (c / size) ** 1.2)
            core.Place(front, x, y, size * 4.5, size * 4.5, Heat(0.6 + 0.6 * part.heat), min(1.0, alpha * energy))
            vx, vy = (x - q0[0]) / max(1e-3, dt), (y - q0[1]) / max(1e-3, dt)
            speed = math.sqrt(vx * vx + vy * vy)
            length = min(70.0, speed * 0.05)
            if length > 2.0:
                # the streak trails behind: its head (texture bottom) at the spark, along the screen velocity
                ux, uy = vx / speed, vy / speed
                streak.Place(front, x - ux * length * 0.45, y - uy * length * 0.45, max(1.5, size * 1.1),
                             length + size, colour, min(1.0, 0.85 * alpha * energy), math.degrees(math.atan2(-vx, vy)))
            else:
                streak.Hide()

    def Ash(self, now, dt):
        cam, cfg = self.hall.camera, self.cfg
        strength = float(cfg.get('fxashalpha', 0.7))
        pull = self.hover * float(cfg.get('fxpull', 1.0)) * 0.6
        for part, flake, soft, ember in self.ash:
            if strength <= 0:
                flake.Hide(), soft.Hide(), ember.Hide()
                continue
            part.age += dt
            flow = self.Flow(part.p, now, part.seed)
            want = (flow[0] * 0.8, flow[1] * 0.6, -7.0 - 4.0 * part.size + 0.4 * flow[2])
            if pull > 0.001:
                pv = self.Pull(part.p, 200.0 * pull)
                want = (want[0] * (1.0 - pull) + pv[0], want[1] * (1.0 - pull) + pv[1], want[2] * (1.0 - pull) + pv[2])
            part.v = self.Ease(part.v, want, dt, 1.2 - 0.6 * pull)
            part.p = _add(part.p, part.v, dt)
            depth = self.Depth(part.p)
            if part.p[1] < self.wallY:
                part.fade = min(1.0, part.fade + dt / 0.4)
            landed = part.p[2] < 2.0
            if landed:
                part.fade = min(1.0, part.fade + dt / 0.8)
                part.p = (part.p[0], part.p[1], 2.0)
            if part.fade >= 1.0 or depth < 300.0 or abs(part.p[0] - self.centre[0]) > self.HalfWidth(depth) * 1.1 \
                    or (part.p[1] < self.wallY and not self.Visible(part.p)):
                self.SpawnAsh(part)
                flake.Hide(), soft.Hide(), ember.Hide()
                continue
            look = self.Look(part.p, part.size)
            if look is None:
                flake.Hide(), soft.Hide(), ember.Hide()
                continue
            x, y, c, blur, depth = look
            tumble = abs(math.cos(now * part.spin + part.seed))
            env = Smooth(part.age / 1.5) * (1.0 - part.fade)
            size = math.sqrt(c * c + blur * blur)
            energy = max(0.15, (c / size) ** 1.2)
            w = Smooth((blur / c - 0.7) / 1.6)
            front = depth < self.focus
            alpha = strength * env * energy
            angle = math.degrees(now * part.spin * 0.6 + part.seed)
            flake.Place(front, x, y, c * 1.6, c * 1.6 * (0.25 + 0.75 * tumble), (0.06, 0.035, 0.03),
                        min(1.0, alpha * (1.0 - w) * (0.6 + 0.4 * tumble)), angle)
            soft.Place(front, x, y, size * 1.4, size * 1.4 * (0.4 + 0.6 * tumble), (0.05, 0.03, 0.03),
                       min(0.5, 0.6 * alpha * w))
            if part.heat > 0.0:
                n = _vnoise(now * 1.1, part.seed)
                ember.Place(front, x, y, c * 2.2, c * 2.2, Heat(0.2 + 0.3 * part.heat),
                            min(1.0, 0.7 * alpha * part.heat * max(0.0, n - 0.3) * (1.0 - w)))
            else:
                ember.Hide()
