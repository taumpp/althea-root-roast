# -*- coding: utf-8 -*-
"""Althea R1 kit layout: pure geometry of the R1 controls, shared by the client (root/uir1.py) and offline previews.

Every function returns draw operations ``(kind, path, x, y, w, h)`` relative to the component origin, ``path``
relative to ``uir1tokens.ROOT``:

* ``image`` - native size (corners, caps, glyphs, knobs)
* ``tile``  - texture REPEATED over w x h with SetRenderingRect (edges, middles); a tile shorter than its texture
  shows only the start of it (a cropped cap of a very short control)

Nothing is stretched: R1 has no 1 px piece that the engine would have to scale. No client module is imported here.
"""
import uir1tokens as T

# Shared by the Item Shop card texture and its native-size item icons.
ITEMSHOP_ICON_SLOT = (9, 10, 42, 108)


def size(path):
    return tuple(T.SIZES[path])


def _meta(path):
    return T.META.get(path, {})


# --------------------------------------------------------------------------- frames
def frame_meta(kind):
    """(corner, pad) of a frame kind: corner = native corner size, pad = shadow margin outside the frame."""
    meta = _meta('frame/%s/lt.png' % kind)
    return meta.get('corner', 3), meta.get('pad', 0)


def frame(kind, w, h, bg=None):
    """9-slice frame of any size (kind window / dialog / tooltip / panel). bg = 'panel' or 'panel_dark': the
    background tile under the frame (1 px inside). A frame with a shadow (dialog, tooltip) starts at -pad."""
    root = 'frame/%s/' % kind
    c, pad = frame_meta(kind)
    w, h = int(w), int(h)
    x0, y0 = -pad, -pad
    W = max(w + 2 * pad, 2 * c)
    H = max(h + 2 * pad, 2 * c)
    ops = []
    if bg:
        ops.append(('tile', 'textures/%s.png' % bg, 1, 1, max(0, w - 2), max(0, h - 2)))
    ops += [('tile', root + 't.png', x0 + c, y0, W - 2 * c, c), ('tile', root + 'b.png', x0 + c, y0 + H - c, W - 2 * c, c),
            ('tile', root + 'l.png', x0, y0 + c, c, H - 2 * c), ('tile', root + 'r.png', x0 + W - c, y0 + c, c, H - 2 * c),
            ('image', root + 'lt.png', x0, y0, c, c), ('image', root + 'rt.png', x0 + W - c, y0, c, c),
            ('image', root + 'lb.png', x0, y0 + H - c, c, c), ('image', root + 'rb.png', x0 + W - c, y0 + H - c, c, c)]
    return [op for op in ops if op[4] > 0 and op[5] > 0]


def frame_inset(kind='window'):
    """Pixels of frame lines inside the rectangle (content starts there)."""
    return _meta('frame/%s/lt.png' % kind).get('lines', 3)


# --------------------------------------------------------------------------- the vein
def vein(x, y, w):
    """The vein over x .. x + w with its 1 px line on row ``y``: fading ends (64 px, or 24 px on a short vein) and the
    32 px middle tile between them."""
    vh = size('vein/m.png')[1]
    top = int(y) - T.VEIN_ROW
    x, w = int(x), int(w)
    if w <= 0:
        return []
    n = T.FADE_LONG if w >= 2 * T.FADE_LONG + 16 else T.FADE_SHORT
    if w < 2 * n:
        half = w // 2
        return [('tile', 'vein/l_%d.png' % T.FADE_SHORT, x, top, half, vh),
                ('tile', 'vein/r_%d.png' % T.FADE_SHORT, x + half, top, w - half, vh)]
    ops = [('image', 'vein/l_%d.png' % n, x, top, n, vh), ('image', 'vein/r_%d.png' % n, x + w - n, top, n, vh)]
    if w > 2 * n:
        ops.insert(0, ('tile', 'vein/m.png', x + n, top, w - 2 * n, vh))
    return ops


def band_line(x, bottom, w):
    """The red line under a selected list row: its line on row ``bottom - 1``, the glow above it."""
    lw, lh = size('band/line_l.png')
    rw = size('band/line_r.png')[0]
    x, w, top = int(x), int(w), int(bottom) - lh
    if w <= 0:
        return []
    if w < lw + rw:
        half = w // 2
        return [('tile', 'band/line_l.png', x, top, half, lh), ('tile', 'band/line_r.png', x + half, top, w - half, lh)]
    return [('tile', 'band/line_m.png', x + lw, top, w - lw - rw, lh), ('image', 'band/line_l.png', x, top, lw, lh),
            ('image', 'band/line_r.png', x + w - rw, top, rw, lh)]


# --------------------------------------------------------------------------- 3-slices
def slice3(prefix, state, w, x=0, y=0):
    """Horizontal 3-slice: native caps, the middle tile repeated between them. prefix ends before the part letter,
    e.g. 'button/primary_26/' -> button/primary_26/l_normal.png.

    A control narrower than both caps (a 26 px arrow button: caps of 16 px) keeps the border of BOTH sides: the right
    cap stays whole at the right edge (its border is its LAST column) and the left cap is cropped to the room left of
    it (its start). A tile shows the START of its texture, so cropping the right cap too (the old half and half)
    drew its inner fill and lost the right border: the right arrow of the week strip had the frame of a left one."""
    lp, mp, rp = ['%s%s_%s.png' % (prefix, part, state) for part in 'lmr']
    lw, h = size(lp)
    rw = size(rp)[0]
    w, x, y = int(w), int(x), int(y)
    if w < lw + rw:
        if w >= rw:
            ops = [('image', rp, x + w - rw, y, rw, h)]
            if w > rw:
                ops.insert(0, ('tile', lp, x, y, w - rw, h))
            return ops
        half = w // 2
        return [('tile', lp, x, y, half, h), ('tile', rp, x + w - (w - half), y, w - half, h)]
    ops = [('image', lp, x, y, lw, h), ('image', rp, x + w - rw, y, rw, h)]
    if w > lw + rw:
        ops.insert(0, ('tile', mp, x + lw, y, w - lw - rw, h))
    return ops


def button_height(small=False):
    """small: False = 26 px, True = 22 px, 'xs' = 20 px (a thin footer button, e.g. the friends list)."""
    if small == 'xs':
        return T.BTN_H_XS
    return T.BTN_H_S if small else T.BTN_H


def button(primary, small, state, w):
    return slice3('button/%s_%d/' % ('primary' if primary else 'secondary', button_height(small)), state, w)


def field(state, w):
    return slice3('field/', state, w)


def segment_cell(pos, state, w, height=T.SEG_H):
    """Tab / segment cell; pos first / mid / last ('single' = a lone cell: first cap and last cap)."""
    prefix = 'seg/wiki_' if height == T.WIKI_SEG_H else 'seg/'
    if pos == 'single':
        lp, mp = prefix+'first_l_%s.png' % state, prefix+'first_m_%s.png' % state
        rp = prefix+'last_r_%s.png' % state
        lw, h = size(lp)
        rw = size(rp)[0]
        w = max(int(w), lw + rw + 1)
        return [('tile', mp, lw, 0, w - lw - rw, h), ('image', lp, 0, 0, lw, h), ('image', rp, w - rw, 0, rw, h)]
    return slice3(prefix+'%s_' % pos, state, max(int(w), 2 * T.SEG_CAP + 1))


# --------------------------------------------------------------------------- scroll bar
def vscroll(part, state, x, y, h):
    """Vertical track ('track', state ignored) or thumb: native top / bottom caps, the 16 px middle tile."""
    tail = '' if part == 'track' else '_' + state
    tp, mp, bp = ['scroll/v_%s_%s%s.png' % (part, key, tail) for key in 'tmb']
    tw, th = size(tp)
    bh = size(bp)[1]
    h, x, y = int(h), int(x), int(y)
    if h < th + bh:
        half = h // 2
        return [('tile', tp, x, y, tw, half), ('tile', bp, x, y + half, tw, h - half)]
    ops = [('image', tp, x, y, tw, th), ('image', bp, x, y + h - bh, tw, bh)]
    if h > th + bh:
        ops.insert(0, ('tile', mp, x, y + th, tw, h - th - bh))
    return ops


def hscroll(part, state, x, y, w):
    """The same bar lying down (the horizontal bars of the wiki tables): left / right caps, the middle tile."""
    tail = '' if part == 'track' else '_' + state
    lp, mp, rp = ['scroll/h_%s_%s%s.png' % (part, key, tail) for key in 'lmr']
    lw, h = size(lp)
    rw = size(rp)[0]
    w, x, y = int(w), int(x), int(y)
    if w < lw + rw:
        half = w // 2
        return [('tile', lp, x, y, half, h), ('tile', rp, x + half, y, w - half, h)]
    ops = [('image', lp, x, y, lw, h), ('image', rp, x + w - rw, y, rw, h)]
    if w > lw + rw:
        ops.insert(0, ('tile', mp, x + lw, y, w - lw - rw, h))
    return ops


# --------------------------------------------------------------------------- slider
def slider_track(x, y, w):
    h = size('slider/track_m.png')[1]
    return [('tile', 'slider/track_m.png', int(x), int(y), max(1, int(w)), h)]


def slider_fill(x, y, w):
    """Filled vein from the track start to x + w (the knob centre)."""
    lw, h = size('slider/fill_l.png')
    w = int(w)
    if w <= 0:
        return []
    if w <= lw:
        return [('tile', 'slider/fill_l.png', int(x), int(y), w, h)]
    return [('tile', 'slider/fill_m.png', int(x) + lw, int(y), w - lw, h), ('image', 'slider/fill_l.png', int(x), int(y), lw, h)]


# --------------------------------------------------------------------------- rules
def rule(x, y, w):
    """Section heading rule: a hairline from x that fades out at x + w (the line on row y + 1)."""
    ew, h = size('rule/end.png')
    x, y, w = int(x), int(y), int(w)
    if w <= 0:
        return []
    if w <= ew:
        return [('tile', 'rule/end.png', x, y, w, h)] if w >= 8 else []
    return [('tile', 'rule/m.png', x, y, w - ew, h), ('image', 'rule/end.png', x + w - ew, y, ew, h)]


def divider(x, y, w):
    """Quiet divider: fades in and out at both ends (the line on row y + 1)."""
    sw, h = size('rule/start.png')
    ew = size('rule/end.png')[0]
    x, y, w = int(x), int(y), int(w)
    if w < sw + ew:
        return rule(x, y, w)
    ops = [('image', 'rule/start.png', x, y, sw, h), ('image', 'rule/end.png', x + w - ew, y, ew, h)]
    if w > sw + ew:
        ops.insert(0, ('tile', 'rule/m.png', x + sw, y, w - sw - ew, h))
    return ops


# --------------------------------------------------------------------------- item slots (style C)
SLOT_CELL = 'slot/cell.png'


def slot_path(height=None):
    """The C slot texture for a slot ``height`` px tall: the cell, or the single tall slot of 2 / 3 cells."""
    n = T.SLOT
    height = n if height is None else int(height)
    tall = 'slot/cell_%dx%d.png' % (n, height)
    return tall if height != n and tall in T.SIZES else SLOT_CELL


def slot_grid(x, y, cols, rows):
    """Item cells of a grid drawn as a picture (where no slot base image draws them): the 32 px cell repeated at the
    engine pitch, cell (i, j) at x + 32 i, y + 32 j; nothing outside cols * 32 x rows * 32."""
    n = T.SLOT
    cols, rows = max(0, int(cols)), max(0, int(rows))
    if not cols or not rows:
        return []
    return [('tile', SLOT_CELL, int(x), int(y), cols * n, rows * n)]


def slot_cell(x, y, height=None):
    """One item slot at its native size (a single slot drawn as a picture; 32, 64 or 96 px tall)."""
    path = slot_path(height)
    w, h = size(path)
    return [('image', path, int(x), int(y), w, h)]


# --------------------------------------------------------------------------- header
def header(w, title_w=0, close=True, left_reserved=0, align='center'):
    """Header inside a window frame of width w: dict(title=(x, y centre), vein=ops, close=(x, y, w, h) or None).
    The title is centred (align 'left': 10 px from the frame; left_reserved = room for header buttons on the left,
    the title centred in the rest); the vein runs 6 px from both frame sides on row HEAD_H; the plain X sits at the
    right with a 20 px hit box."""
    w = int(w)
    close_rect = None
    right = w - 6
    if close:
        gx = w - 10 - T.X_SIZE + 1
        gy = (T.HEAD_H - T.X_SIZE) // 2 + 1
        pad = (T.X_HIT - T.X_SIZE) // 2
        # the click area by the header row (T.X_HIT = hit_area(HEAD_H), owner 13. 10.), kept inside the frame lines
        close_rect = (min(gx - pad, w - frame_inset() - T.X_HIT), gy - pad, T.X_HIT, T.X_HIT)
        right = close_rect[0] - 4
    if left_reserved:
        tx = int(left_reserved) + max(2, (right - int(left_reserved) - int(title_w)) // 2)
    elif align == 'left':
        tx = 10
    else:
        tx = (w - int(title_w)) // 2
        if close and tx + title_w > right:
            tx = max(10, right - int(title_w))
    return dict(title=(tx, T.HEAD_H // 2 + 1), vein=vein(6, T.HEAD_H, w - 12), close=close_rect,
                content_top=T.HEAD_H + T.CONTENT_GAP)
