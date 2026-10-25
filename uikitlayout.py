# -*- coding: utf-8 -*-
"""Althea UI kit layout: pure geometry, shared by the client (root/uikit.py) and the offline preview
(tools/preview_althea_titlebar.py), so the preview shows exactly what the game composes.

Every function returns draw operations ``(kind, path, x, y, w, h)`` relative to the component origin;
``path`` is relative to ``uikittokens.KIT_ROOT``:

* ``image``   - native size (end caps, corners, ornaments, flourishes, icons) -> ui.ImageBox
* ``tile``    - texture REPEATED over w x h (edges, bar middle)                -> ExpandedImageBox.SetRenderingRect
* ``stretch`` - texture SCALED to w x h (plain fills only: segment middle, vignette, selection band)

No operation scales an ornament: an ornament is always drawn at its native size, only plain tiles repeat.
No client module is imported here.
"""
import uikittokens as T

TITLE_GAP = 12   # title <-> flourish
CLOSE_GAP = 8    # title area <-> close cross
END_GAP = 6      # title area <-> end cap ornament


def size(path):
    return tuple(T.SIZES[path])


def bar_height(prof, kind='window'):
    """Title bar height of a window profile: kind 'window' (main window) or 'dialog' (smaller)."""
    return T.BAR_FOR[prof][kind]


def title_texture(text, bar):
    """Baked title texture for this text and bar height, or None (then the engine draws the text)."""
    slug = T.TITLES.get((text or '').upper())
    if not slug:
        return None
    path = 'bar/%d/title_%s.png' % (bar, slug)
    return path if path in T.SIZES else None


def pick_title(text, bar, width, close=True):
    """The largest baked title texture for this text that fits a bar of this width: the bar's own size first,
    then the titles prepared for the smaller bars (a narrow dialog keeps a readable title). (path, size) or
    (None, (0, 0)) when the text has no baked texture."""
    choice = (None, (0, 0))
    for h in sorted((int(k) for k in T.BARS), reverse=True):
        if h > bar:
            continue
        path = title_texture(text, h)
        if not path:
            continue
        choice = (path, size(path))
        if titlebar(width, bar, choice[1], close)['fits']:
            break
    return choice


def min_bar_width(bar):
    root = 'bar/%d/' % bar
    return size(root + 'l.png')[0] + size(root + 'r.png')[0]


def titlebar(width, bar, title_size, close=True, flourish=True):
    """Title bar of any width (>= both end caps). The middle tile runs UNDER the caps (fade overlap), the centre
    ornaments and the close cross keep their size, the title is centred and moves left only to clear the close
    cross, and the flourishes take the longest prepared length that fits symmetrically (none below the shortest).

    flourish=False (a plain bar without the lines): the title stays centred on the bar, moving left only to clear
    the close cross.

    Returns dict(ops, width, height, title=(x, y, w, h), close=(x, y, w, h) or None, flourish=length or 0, fits)."""
    B = T.BARS[str(bar)]
    root = 'bar/%d/' % bar
    h, fade, end = B['height'], B['fade'], B['end']
    lw, rw = size(root + 'l.png')[0], size(root + 'r.png')[0]
    width = max(int(width), lw + rw)
    ops = [('tile', root + 'm.png', lw - fade, 0, width - lw - rw + 2 * fade, h),
           ('image', root + 'l.png', 0, 0, lw, h),
           ('image', root + 'r.png', width - rw, 0, rw, h)]
    for part in ('ct', 'cb'):
        w, hh = size(root + part + '.png')
        ops.append(('image', root + part + '.png', (width - w) // 2, 0 if part == 'ct' else h - hh, w, hh))
    left, right = end + END_GAP, width - end - END_GAP
    close_rect = None
    if close:
        c = B['close']
        close_rect = (width - end - c, (h - c) // 2, c, c)
        right = close_rect[0] - CLOSE_GAP
    tw, th = int(title_size[0]), int(title_size[1])

    def flourish_at(tx):
        room = min(tx - TITLE_GAP - left, right - (tx + tw) - TITLE_GAP)
        return next((L for L in B['flourish'] if L <= room), 0) if tw and flourish else 0
    # Centred on the bar (as the concept); when the close cross leaves no room for the lines on the right,
    # centring in the free title area may keep them - the longer lines win, the bar centre wins a tie.
    tx = min((width - tw) // 2, right - tw)
    alt = left + (right - left - tw) // 2
    if flourish_at(alt) > flourish_at(tx):
        tx = alt
    fits = tx >= left
    tx = max(left, tx)
    ty = (h - th) // 2
    length = flourish_at(tx)
    if length:
        fw, fh = size(root + 'flourish_l_%d.png' % length)
        fy = (h - fh) // 2
        ops.append(('image', root + 'flourish_l_%d.png' % length, tx - TITLE_GAP - fw, fy, fw, fh))
        ops.append(('image', root + 'flourish_r_%d.png' % length, tx + tw + TITLE_GAP, fy, fw, fh))
    return dict(ops=ops, width=width, height=h, title=(tx, ty, tw, th), close=close_rect, flourish=length,
                fits=fits)


def frame_corner(kind, prof):
    return size('%s/frames/%s/lt.png' % (prof, kind))[0]


def frame(kind, prof, w, h, bg=False, vignette=False):
    """9-slice frame of any size >= 2 x corner: fixed corners, 128 px edge tiles. kind 'window' or 'panel'.
    bg = panel texture tiled under the whole frame (window), vignette = stretched darkening (panels)."""
    root = '%s/frames/%s/' % (prof, kind)
    C = size(root + 'lt.png')[0]
    w, h = max(int(w), 2 * C), max(int(h), 2 * C)
    ops = []
    if bg:
        inset = T.META[root + 'lt.png']['bg_inset']
        ops.append(('tile', 'textures/panel.png', inset, inset, w - 2 * inset, h - 2 * inset))
    if vignette:
        ops.append(('stretch', 'textures/vignette.png', 0, 0, w, h))
    ops += [('tile', root + 't.png', C, 0, w - 2 * C, C), ('tile', root + 'b.png', C, h - C, w - 2 * C, C),
            ('tile', root + 'l.png', 0, C, C, h - 2 * C), ('tile', root + 'r.png', w - C, C, C, h - 2 * C),
            ('image', root + 'lt.png', 0, 0, C, C), ('image', root + 'rt.png', w - C, 0, C, C),
            ('image', root + 'lb.png', 0, h - C, C, C), ('image', root + 'rb.png', w - C, h - C, C, C)]
    return ops


def button(prof, role, state, w):
    """3-slice button from c9 (role 'reset' = dark plate, 'close' = ruby): own end caps, the 32 px middle TILE
    is drawn under the caps with the fade overlap."""
    root = '%s/button_%s/' % (prof, role)
    lw, h = size(root + 'l_%s.png' % state)
    rw = size(root + 'r_%s.png' % state)[0]
    fade = T.META[root + 'l_normal.png']['fade']
    w = max(int(w), lw + rw)
    return [('tile', root + 'm_%s.png' % state, lw - fade, 0, w - lw - rw + 2 * fade, h),
            ('image', root + 'l_%s.png' % state, 0, 0, lw, h),
            ('image', root + 'r_%s.png' % state, w - rw, 0, rw, h)]


def button_height(prof, role):
    return size('%s/button_%s/l_normal.png' % (prof, role))[1]


def segment_cell(prof, pos, state, w):
    """Segment cell (pos first/mid/last, or 'single' = a one-cell segment: the first cell's left cap and middle with
    the last cell's right cap): 4 px caps and a 4 px x-constant middle stretched to the width."""
    if pos == 'single':
        first, last = '%s/segment/first_' % prof, '%s/segment/last_' % prof
        lw, h = size(first + 'l_%s.png' % state)
        rw = size(last + 'r_%s.png' % state)[0]
        w = max(int(w), lw + rw + 1)
        return [('stretch', first + 'm_%s.png' % state, lw, 0, w - lw - rw, h),
                ('image', first + 'l_%s.png' % state, 0, 0, lw, h),
                ('image', last + 'r_%s.png' % state, w - rw, 0, rw, h)]
    root = '%s/segment/%s_' % (prof, pos)
    lw, h = size(root + 'l_%s.png' % state)
    rw = size(root + 'r_%s.png' % state)[0]
    w = max(int(w), lw + rw + 1)
    return [('stretch', root + 'm_%s.png' % state, lw, 0, w - lw - rw, h),
            ('image', root + 'l_%s.png' % state, 0, 0, lw, h),
            ('image', root + 'r_%s.png' % state, w - rw, 0, rw, h)]


def slider_track(prof, x, y, w):
    root = '%s/slider/track_' % prof
    lw, h = size(root + 'l_normal.png')
    rw = size(root + 'r_normal.png')[0]
    return [('stretch', root + 'm_normal.png', x + lw, y, max(1, w - lw - rw), h),
            ('image', root + 'l_normal.png', x, y, lw, h), ('image', root + 'r_normal.png', x + w - rw, y, rw, h)]


def slider_fill(prof, x, y, w):
    """Filled part from the track start to x + w (the knob centre)."""
    root = '%s/slider/fill_' % prof
    lw, h = size(root + 'l_normal.png')
    return [('image', root + 'l_normal.png', x, y, lw, h),
            ('stretch', root + 'm_normal.png', x + lw, y, max(0, int(w) - lw), h)]


def divider(prof, w):
    """Line with a centre diamond (under headings)."""
    lw, lh = size('%s/divider_line.png' % prof)
    cw, ch = size('%s/divider_center.png' % prof)
    return [('tile', '%s/divider_line.png' % prof, 0, 0, w, lh),
            ('image', '%s/divider_center.png' % prof, (w - cw) // 2, 0, cw, ch)]


# --------------------------------------------------------------------------- v5 components (settings v5)
def slice3(root, state, w):
    """Horizontal 3-slice of the v5 components (key cap, chip, edit field): native caps, the x-constant middle
    column stretched between them. root ends with the part prefix, e.g. '1080/keycap/'."""
    lw, h = size(root + 'l_%s.png' % state)
    rw = size(root + 'r_%s.png' % state)[0]
    w = max(int(w), lw + rw + 1)
    return [('stretch', root + 'm_%s.png' % state, lw, 0, w - lw - rw, h),
            ('image', root + 'l_%s.png' % state, 0, 0, lw, h),
            ('image', root + 'r_%s.png' % state, w - rw, 0, rw, h)]


def keycap(prof, state, w):
    return slice3('%s/keycap/' % prof, state, w)


def chip(prof, on, state, w):
    return slice3('%s/chip/%s_' % (prof, 'on' if on else 'off'), state, w)


def field(prof, state, w):
    return slice3('%s/field/' % prof, state, w)


def vscroll(prof, part, state, x, y, h):
    """Vertical 3-slice of the scrollbar track / thumb: native top and bottom caps, the 1 px middle stretched."""
    root = '%s/scroll/%s_' % (prof, part)
    tw, th = size(root + 't_%s.png' % state)
    bh = size(root + 'b_%s.png' % state)[1]
    h = max(int(h), th + bh)
    return [('stretch', root + 'm_%s.png' % state, x, y + th, tw, h - th - bh),
            ('image', root + 't_%s.png' % state, x, y, tw, th),
            ('image', root + 'b_%s.png' % state, x, y + h - bh, tw, bh)]


def section_rule(prof, x, y, w):
    """Rule after a section heading, x .. x + w: 128 px tiles over the whole width, up to the right edge of the
    content (owner play test 2026-10-05: the fading end read as a line stopping half way and left an odd empty
    area; the section look gets a redesign, until then a plain full-width rule). Nothing below 8 px."""
    mh = size('%s/section/rule_m.png' % prof)[1]
    w = int(w)
    return [('tile', '%s/section/rule_m.png' % prof, x, y, w, mh)] if w >= 8 else []


# --------------------------------------------------------------------------- v6 control family (2026-10-06)
def button6_height(prof, size='c'):
    """Height of the one button family: 'c' = in the content (rows, popups, panels), 'b' = the window footer."""
    return T.PROFILES[prof]['btn_c' if size == 'c' else 'btn_b']


def button6(prof, role, size, pos, state, w):
    """Button / chip cell of the v6 family: role primary / secondary / chip_on / chip_off, size 'c' / 'b', pos single
    (or first / mid / last of a joined B3 block). Native 4 px caps, the x-constant middle stretched."""
    return slice3('%s/button6/%s_%s/%s_' % (prof, role, size, pos), state, w)


def keycap6(prof, style, state, w):
    """Key cap K1-K4 of w x keycap6_h: the texture has a PAD margin (shadow), so the ops start at -PAD."""
    root = '%s/keycap_%s/' % (prof, style)
    pad = T.META[root + 'l_normal.png']['pad']
    ops = slice3(root, state, int(w) + 2 * pad)
    return [(kind, path, x - pad, y - pad, ow, oh) for kind, path, x, y, ow, oh in ops]


def check(prof, on, state='normal'):
    return '%s/check/%s_%s.png' % (prof, 'on' if on else 'off', state)
