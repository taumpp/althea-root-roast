# -*- coding: utf-8 -*-
"""Stone queue preview v5 (2026-10-05): camera framing of the 3D marker preview.

Pure geometry, no client module: shared by the client (uimeteorpreview), the tests and the offline mock render.

Why: the native selection (CRenderTarget::SelectMetinQueuePreview, V1 appearance path used by the library
draft) frames the WHOLE supported marker envelope (3x the 240 px ring reference horizontally, 5x the stone
height vertically, 30 deg pitch, 10 deg FOV), so the stone itself is ~13 % of the preview height and sits in the
lower quarter (owner screenshot 2026-10-05: "metin je asi 2 % té plochy"). Python owns the camera instead,
through the native WikiRenderTarget.SetModelV3Eye / SetModelV3Target (RenderModelWiki uses exactly these vectors,
then the user's orbit and pan on top):

* the stone takes ~48 % of the preview height at 100 % stone size (BASE_FRACTION of its bounding box), the
  ground under it sits at BASE_NDC (room for the ground ring in front and for the overhead markers above);
* "Velikost kamenů ve světě" (100-200 %) is shown LIVE by the camera distance: the native preview actor keeps the
  scale it was created with (the world refresh CPythonCharacterManager::RefreshAllMetinstoneScale never touches
  render-target actors), the camera emulates the new size; apparent height grows with size ** 0.4 so 200 % still
  fits, the character silhouette (true 174 units, warrior_4-1.gr2) keeps the true ratio stone : character;
* the mouse wheel zoom is ours too (a factor on the distance), so size and zoom compose.

Geometry source (measured offline with gr2-tool gr2-obj, 2026-10-05): metinstone_01/05/07.gr2 used by the three
preview stones 8001/8005/8013 share one mesh, x -90.5..63.7, y -57.9..55.8, z -41.0..174.9 (z < 0 is buried);
mob_proto ScalePct 100; the metinstone_loop wait pose keeps the same bounds (gr2-tool open --anim). The render
target has no terrain, so the buried part (z < 0) IS visible in the preview: the framing uses the whole -41..175.
A different preview stone falls back to the same numbers (named fallback).
"""
import math

FOV_DEG = 10.0          # CRenderTarget::RenderModelWiki: SetPerspective(10.0, w / h, 100, far)
PITCH_DEG = 30.0        # the native base view also looks down 30 deg (kPreviewPitchDegrees)
NEAR = 100.0

STONE_TOP = 175.0       # top above the ground plane (units at 100 %)
STONE_BOTTOM = -41.0    # buried part, visible in the preview (no terrain there)
STONE_HALF_W = 77.0     # half width (x)
STONE_HALF_D = 57.0     # half depth (y)
STONE_BOUNDS = {8001: (STONE_BOTTOM, STONE_TOP, STONE_HALF_W, STONE_HALF_D),
                8005: (STONE_BOTTOM, STONE_TOP, STONE_HALF_W, STONE_HALF_D),
                8013: (STONE_BOTTOM, STONE_TOP, STONE_HALF_W, STONE_HALF_D)}
CHARACTER_HEIGHT = 174.0  # warrior_4-1.gr2 bind pose z 0..174.1
CHARACTER_GAP = 70.0      # silhouette feet centre beside the stone edge (units at 100 %)

# Stone bounding box / preview height at 100 %. The metinstone mesh leans, its real silhouette is 0.62-0.99 of
# the box depending on the (native, 12 deg/s) rotation: 0.60 box = 37-60 % of the height, 48 % on average
# (measured offline on the mesh, owner brief: 40-60 %).
BASE_FRACTION = 0.60
SIZE_EXPONENT = 0.4     # 200 % world size -> 1.32x in the preview (the stone stays inside the frame)
BASE_NDC = -0.38        # ground point under the stone in normalized device y (-1 bottom, +1 top): 69 % down;
                        # the stone's lowest point then sits ~80 % down, its top ~33 % down
ZOOM_RANGE = (0.45, 2.6)
ZOOM_STEP = 0.88
SIZE_RANGE = (1.0, 2.0)  # stone_size setting 0..1 -> world scale 100..200 %


def clamp(value, low, high):
    return max(low, min(high, value))


def bounds(vnum):
    return STONE_BOUNDS.get(int(vnum), (STONE_BOTTOM, STONE_TOP, STONE_HALF_W, STONE_HALF_D))


def fraction(view_scale):
    """Apparent stone height / preview height for the displayed world size (1.0 = 100 %)."""
    return BASE_FRACTION * clamp(float(view_scale), SIZE_RANGE[0], SIZE_RANGE[1]) ** SIZE_EXPONENT


def projected_height(vnum, pitch=PITCH_DEG):
    bottom, top, half_w, half_d = bounds(vnum)
    p = math.radians(pitch)
    return (top - bottom) * math.cos(p) + 2.0 * half_d * math.sin(p)


class Framing(object):
    """Camera of one preview: eye / target in world units of the native actor (created at actor_scale)."""

    def __init__(self, vnum, aspect, actor_scale=1.0, view_scale=1.0, zoom=1.0, pitch=PITCH_DEG):
        self.vnum = int(vnum)
        self.aspect = max(0.2, float(aspect))
        self.actor_scale = max(0.05, float(actor_scale))
        self.view_scale = clamp(float(view_scale), SIZE_RANGE[0], SIZE_RANGE[1])
        self.zoom = clamp(float(zoom), ZOOM_RANGE[0], ZOOM_RANGE[1])
        self.pitch = float(pitch)
        self.tan = math.tan(math.radians(FOV_DEG * 0.5))
        p = math.radians(self.pitch)
        self.cos, self.sin = math.cos(p), math.sin(p)
        self.fraction = fraction(self.view_scale)
        height = projected_height(self.vnum, self.pitch) * self.actor_scale
        self.base_distance = height / (2.0 * self.fraction * self.tan)
        # Target above the stone axis so the base lands on BASE_NDC (exact perspective, before the zoom).
        self.target_z = -BASE_NDC * self.tan * self.base_distance / (self.cos + BASE_NDC * self.tan * self.sin)
        self.distance = self.base_distance * self.zoom

    def target(self):
        return (0.0, 0.0, self.target_z)

    def eye(self):
        return (0.0, -self.distance * self.cos, self.target_z + self.distance * self.sin)

    def far_plane(self):
        return self.distance + 4000.0

    # ---- projection (the same perspective as the native preview, without orbit; pan is a screen offset)
    def project(self, point):
        """World point -> (ndc_x, ndc_y) in -1..1, +y up."""
        x, y, z = point
        tx, ty, tz = self.target()
        dx, dy, dz = x - tx, y - ty, z - tz
        up = dy * self.sin + dz * self.cos
        forward = dy * self.cos - dz * self.sin
        depth = max(NEAR, self.distance + forward)
        return dx / (depth * self.tan * self.aspect), up / (depth * self.tan)

    def emulated(self):
        """Actual world units per emulated unit: the actor is actor_scale big, the player sees view_scale."""
        return self.actor_scale / self.view_scale

    def stone_box(self):
        """(left, top, right, bottom) of the stone in ndc (a box around its visible part)."""
        bottom, top, half_w, half_d = bounds(self.vnum)
        s = self.actor_scale
        points = [(sx * half_w * s, sy * half_d * s, z * s)
                  for sx in (-1, 1) for sy in (-1, 1) for z in (bottom, top)]
        projected = [self.project(point) for point in points]
        xs, ys = [p[0] for p in projected], [p[1] for p in projected]
        return min(xs), max(ys), max(xs), min(ys)

    def companion_world(self):
        """(x, y, scale) of the 3D companion actor (WikiRenderTarget.SetMetinQueueCompanion) in the
        native scene: the same spot as the silhouette feet, scaled by the emulated factor so that 174 units of the
        warrior keep the true ratio to the displayed stone size (the size slider moves the camera, not the stone)."""
        bottom, top, half_w, half_d = bounds(self.vnum)
        k = self.emulated()
        return -(half_w * self.view_scale + CHARACTER_GAP) * k, 0.0, k

    def silhouette(self, pitch=0.0, yaw=0.0):
        """Character beside the stone: (feet_x_ndc, feet_y_ndc, height_ndc) at the true size ratio, seen from the
        orbited camera (pitch / yaw as WikiRenderTarget.RotateEyeAroundTarget gets them)."""
        bottom, top, half_w, half_d = bounds(self.vnum)
        k = self.emulated()
        x = -(half_w * self.view_scale + CHARACTER_GAP) * k
        feet = self.orbit_project((x, 0.0, 0.0), pitch, yaw)
        head = self.orbit_project((x, 0.0, CHARACTER_HEIGHT * k), pitch, yaw)
        return feet[0], feet[1], head[1] - feet[1]

    # ---- the orbit of the native preview (CRenderTarget::RenderModelWiki)
    def elevation(self, pitch=0.0):
        """Camera elevation after the drag: CCamera::RotateEyeAroundTarget clamps base pitch + drag to +-80 deg."""
        return clamp(self.pitch + float(pitch), -ELEVATION_LIMIT, ELEVATION_LIMIT)

    def orbit_basis(self, pitch=0.0, yaw=0.0):
        """(right, up, back) of the view after RotateEyeAroundTarget(pitch, yaw): the eye turns about the camera's
        right axis (elevation), then by -yaw about Z (D3DXMatrixRotationZ(-roll)); D3DXMatrixLookAtRH with up = +Z.
        back = unit vector target -> eye. yaw 0 / pitch 0 = project()."""
        e, r = math.radians(self.elevation(pitch)), math.radians(float(yaw))
        ce, se, cr, sr = math.cos(e), math.sin(e), math.cos(r), math.sin(r)
        back = (-ce * sr, -ce * cr, se)
        right = (cr, -sr, 0.0)
        up = (se * sr, se * cr, ce)
        return right, up, back

    def orbit_project(self, point, pitch=0.0, yaw=0.0):
        """World point -> (ndc_x, ndc_y) seen from the orbited camera (pan is a screen offset, to_pixels)."""
        right, up, back = self.orbit_basis(pitch, yaw)
        tx, ty, tz = self.target()
        d = (point[0] - tx, point[1] - ty, point[2] - tz)
        x = sum(a * b for a, b in zip(d, right))
        y = sum(a * b for a, b in zip(d, up))
        depth = max(NEAR, self.distance - sum(a * b for a, b in zip(d, back)))
        return x / (depth * self.tan * self.aspect), y / (depth * self.tan)

    def orbit_depth(self, point, pitch=0.0, yaw=0.0):
        right, up, back = self.orbit_basis(pitch, yaw)
        tx, ty, tz = self.target()
        d = (point[0] - tx, point[1] - ty, point[2] - tz)
        return self.distance - sum(a * b for a, b in zip(d, back))

    def character_behind(self, pitch=0.0, yaw=0.0):
        """True when the character stands behind the stone and its feet / head fall inside the stone's screen box
        (the 2D image cannot be occluded - the view draws it fainter)."""
        bottom, top, half_w, half_d = bounds(self.vnum)
        k = self.emulated()
        x = -(half_w * self.view_scale + CHARACTER_GAP) * k
        if self.orbit_depth((x, 0.0, 0.0), pitch, yaw) <= self.orbit_depth((0.0, 0.0, 0.0), pitch, yaw):
            return False
        s = self.actor_scale
        corners = [self.orbit_project((sx * half_w * s, sy * half_d * s, z * s), pitch, yaw)
                   for sx in (-1, 1) for sy in (-1, 1) for z in (bottom, top)]
        left, right = min(c[0] for c in corners), max(c[0] for c in corners)
        low, high = min(c[1] for c in corners), max(c[1] for c in corners)
        feet = self.orbit_project((x, 0.0, 0.0), pitch, yaw)
        head = self.orbit_project((x, 0.0, CHARACTER_HEIGHT * k), pitch, yaw)
        return left <= feet[0] <= right and not (max(feet[1], head[1]) < low or min(feet[1], head[1]) > high)


def to_pixels(ndc_x, ndc_y, width, height, pan=(0.0, 0.0)):
    """ndc -> widget pixels (origin top-left); pan = native PanMetinQueuePreview fractions (scene follows)."""
    return ((ndc_x + 1.0) * 0.5 * width + pan[0] * width, (1.0 - ndc_y) * 0.5 * height + pan[1] * height)


# Backdrops are stretched over the whole render target (CRenderTarget::CreateBackground scales the image to the
# screen and the interface projection maps the screen onto the target): one texture per aspect class.
BACKDROPS = ((2.1, 'backdrop_21.png'), (1.75, 'backdrop_175.png'), (1.45, 'backdrop_145.png'),
             (1.2, 'backdrop_120.png'))
BACKDROP_SIZE = 1024   # width of every backdrop; height = width / aspect
ASSET_ROOT = 'd:/ymir work/ui/public/althea_meteor/'

# The orbit of the preview. The pitch the player can drag is limited so the stone is never seen from below the
# ground (there is no terrain). The warrior beside it is one still front view (kolo 3) - the orbit helpers below
# (silhouette / elevation / character_behind) keep the world geometry of a turn for tests and a future 3D actor.
PITCH_RANGE = (-25.0, 30.0)   # added to PITCH_DEG -> camera elevation 5..60 deg
ELEVATION_LIMIT = 80.0        # CCamera::RotateEyeAroundTarget clamps the elevation to +-80 deg


def backdrop(aspect):
    best = min(BACKDROPS, key=lambda item: abs(math.log(max(0.2, float(aspect)) / item[0])))
    return ASSET_ROOT + best[1]


def backdrop_anchor():
    """Where the default camera puts the stone base on the backdrop (0..1, 0..1 from the top-left)."""
    return 0.5, (1.0 - BASE_NDC) * 0.5
