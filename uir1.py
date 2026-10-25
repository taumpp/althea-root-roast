# -*- coding: utf-8 -*-
"""Althea R1 kit runtime ("Krvavá žíla"): compact graphite windows with the blood red vein.

The look chosen for the game windows on 2026-10-06: a graphite frame with a thin bronze hairline, the window title in
Cinzel inside the frame with the red vein under it, a plain X (red under the mouse), dark buttons (the primary one
with the vein along its bottom edge), a glowing red tick, a slider as a red vein with a small dark round knob, a
narrow scroll bar, tabs and selected rows as a dark well with a red line under them (never a red plate). Noto Sans
for the text, Cinzel for the window titles and the button labels, Tahoma only as the automatic fallback of an
older EXE (uikit.FontSet).

    import uir1
    kit = uir1.Kit()
    chrome = uir1.Chrome(self, kit, w, h, 'Přátelé', on_close=self.Close)     # frame + header + X
    y = chrome.ContentTop()
    uir1.Button(self, kit, 12, y, 96, 'Použít', primary=True, event=self.Apply)
    uir1.Button(self, kit, 114, y, 96, 'Zrušit', event=self.Close)

Textures: d:/ymir work/ui/public/althea_r1/ (tools/build_althea_r1_kit.py), geometry: uir1layout, tokens: uir1tokens.
Engine rules every widget here keeps: children draw and are picked in the order they were added (images of a
control are created before its text), LoadImage makes a new image instance (the rendering rect and the alpha are
set again after every LoadImage), a SetFontName alone does not lay the text out again (uikit.SetFont), a control
must lie inside its parent to take clicks. Nothing is stretched: variable lengths are caps plus repeated tiles, plain
fills are ui.Bar. API overview: docs/ALTHEA_R1_KIT.md.
"""
import ui
import wndMgr
from _weakref import ref as _ref

import uikit
import uir1layout as L
import uir1tokens as T
import uiwheel

ROOT = T.ROOT
Interactive = uikit.Interactive
HitArea = uikit.HitArea
SetFont = uikit.SetFont
Upper = uikit.Upper
TextWidth = uikit.TextWidth
WordGap = uikit.WordGap
FontCell = uikit.FontCell
Rect = uikit.Rect
HLine = uikit.HLine
GenerateColor = uikit.GenerateColor


class _WeakParent(object):
    """The parent attribute of a helper object (Ops, Band, TooltipFrame) that lives in an attribute of that very
    window: a strong reference back made a cycle, so the window - and everything its events hold, e.g. the NPC dialog
    behind its R1 buttons - stayed alive (and shown) until a late cyclic GC. Reads give the window (None once its
    real owners dropped it), writes keep only a weak reference."""

    def __get__(self, obj, owner=None):
        if obj is None:
            return self
        ref = obj.__dict__.get('_parent_ref')
        return ref() if ref is not None else None

    def __set__(self, obj, value):
        if value is None:
            obj.__dict__['_parent_ref'] = None
            return
        try:
            obj.__dict__['_parent_ref'] = _ref(value)
        except TypeError:                 # a type without weak references: keep it strongly as before
            obj.__dict__['_parent_ref'] = lambda value=value: value
Tr_ = uikit.Tr_


# Owner 10. 10. 2026: the R1 colour tokens (0xFF... > 0x7FFFFFFF) reach the engine as signed ints, so the texts show
# T.IVORY / T.INK / T.INK_DIM / RED ... instead of white (ui.PackedFontColor; the x64 wndMgr.SetFontColor drops them
# otherwise). One switch: False gives back the previous look (white texts, white hints) without a revert.
R1_SIGNED_COLORS = True


def UseR1():
    """The R1 look unless Settings -> "Starý vzhled" chose the original windows (settingslook 'legacy')."""
    try:
        import settingslook
        return settingslook.Get('look') != 'legacy'
    except Exception:
        return True


# --------------------------------------------------------------------------- look switch
# A window decides its look when it is built. The windows that live for the whole session (the interface built at the
# login: tooltips, inventory, character, taskbar with the quick slots, minimap, chat, ...) must follow a later switch
# too, otherwise "Starý vzhled" and back leaves a mix of both looks (owner 9. 10. 2026). Settings calls LookChanged()
# right after it stored the look: the generation goes up and every window registered with FollowLook(window) gets
# its SyncR1Look() (dress when R1 is wanted and it is not dressed, undo the R1 look when the original one is wanted).
# Tooltips compare LookGeneration() when they are filled again. Nothing is polled: no per-frame cost.
_LOOK = {'generation': 0}
_FOLLOWERS = []         # (weak reference to the window, method name)


def LookGeneration():
    """Goes up with every look switch in Settings (LookChanged)."""
    return _LOOK['generation']


def FollowLook(window, method='SyncR1Look'):
    """``window.<method>()`` runs after every look switch while the window lives (a weak reference: the list never
    keeps a window alive). UnfollowLook(window) in its Destroy."""
    try:
        reference = _ref(window)
    except TypeError:
        return False
    _FOLLOWERS[:] = [entry for entry in _FOLLOWERS if entry[0]() is not None and
                     not (entry[0]() is window and entry[1] == method)]
    _FOLLOWERS.append((reference, method))
    return True


def UnfollowLook(window):
    _FOLLOWERS[:] = [entry for entry in _FOLLOWERS if entry[0]() is not None and entry[0]() is not window]


def Following():
    """The live windows that follow the look (tests, diagnostics)."""
    return [entry[0]() for entry in _FOLLOWERS if entry[0]() is not None]


def LookChanged():
    """Settings stored a new look: every following window takes it now (a failing one is traced and the next one still
    switches). Returns the number of windows that switched without an error."""
    _LOOK['generation'] += 1
    done = 0
    for reference, method in list(_FOLLOWERS):
        window = reference()
        if window is None:
            continue
        try:
            getattr(window, method)()
            done += 1
        except Exception:
            TraceFailure('the look switch of %s' % window.__class__.__name__)
    _FOLLOWERS[:] = [entry for entry in _FOLLOWERS if entry[0]() is not None]
    return done


def Restack(parent, children):
    """Puts ``children`` (in this order) at the END of ``parent``'s children, so they draw above a frame made now (a
    look switch dresses a window whose content already exists). The engine leaves a SetParent to the same parent where
    it is and SetTop moves only a 'float' window: each child goes through a holder window and back."""
    holder = ui.Window()
    for child in children:
        if child is not None:
            child.SetParent(holder)
            child.SetParent(parent)
    holder.Hide()


def TrackEnabled(button, enabled=True, on_change=None):
    """Keeps the enabled state of an ORIGINAL button in Python: its Enable / Disable (instance wrappers) record it in
    ``button.r1_enabled`` and call ``on_change(enabled)``. Older EXEs have no wndMgr.IsDisable, so these wrappers also
    provide state tracking without requiring the new native query. UntrackEnabled(button) undoes it."""
    if 'r1_enabled' not in button.__dict__:
        enable, disable = button.Enable, button.Disable

        def Enable():
            enable()
            button.r1_enabled = True
            if button.r1_on_change:
                button.r1_on_change(True)

        def Disable():
            disable()
            button.r1_enabled = False
            if button.r1_on_change:
                button.r1_on_change(False)
        button.Enable, button.Disable = Enable, Disable
        button.r1_enabled = bool(enabled)
    button.r1_on_change = on_change
    return button


def UntrackEnabled(button):
    for name in ('Enable', 'Disable', 'r1_enabled', 'r1_on_change'):
        if name in button.__dict__:
            delattr(button, name)


def IsEnabled(widget, default=True):
    """Enabled state of an R1 control / adapter (IsEnabled), of a tracked original button (TrackEnabled), else
    ``default``. Keep this independent of ui.Button.IsDisable for older executables."""
    getter = getattr(widget, 'IsEnabled', None)
    if getter is not None:
        return bool(getter())
    if 'r1_enabled' in getattr(widget, '__dict__', {}):
        return bool(widget.r1_enabled)
    return default


def TraceFailure(what):
    """Traces why an R1 window fell back to its original look (syserr), with the traceback."""
    try:
        import dbg
        import traceback
        dbg.TraceError('R1 look of %s failed, the original look is used.' % what)
        for line in traceback.format_exc().splitlines():
            dbg.TraceError(line)
    except Exception:
        pass


class Kit(object):
    """Font set of one window: 'B' (Noto Sans + Cinzel) when the client renders the Althea families, otherwise 'A'
    (Tahoma). Font roles: title, text, text_b, text_s, text_sb, tahoma."""

    def __init__(self, font_set=None):
        self.font_set = font_set if font_set in ('A', 'B') else uikit.FontSet()

    def font(self, role='text'):
        return T.FONTS[self.font_set][role]

    def cell(self, role='text'):
        return FontCell(self.font(role))


# --------------------------------------------------------------------------- images
def _put(widget, op, dx=0, dy=0, alpha=None):
    """One op on an ExpandedImageBox. LoadImage makes a new image instance (rect, scale and alpha back to their
    defaults), so the tile rect and the alpha are set again after it every time. The same op again (a repaint that
    changes nothing, e.g. the wiki scroll thumb on every wheel step) only keeps the image shown or hidden: no new
    image instance per repaint. Only images made by Ops remember their op: an adopted native image (another owner
    may move or reload it) is drawn again every time.

    A tile also gets the window size of the area it draws (LoadImage sized the window to the texture). Inside a list
    that renders inside its rectangle the engine clips an image by its WINDOW size (CWindow::UpdateRenderBox): a
    128 px texture tiled into 51 x 44 px was clipped twice and drawn mirrored beside its place (black blocks left of
    the boss portraits), a 32 px tile scrolled more than 32 px out of the list vanished. The window is not pickable,
    so the size changes nothing else."""
    key = (op, dx, dy, alpha)
    owned = hasattr(widget, 'r1_op')
    if owned and widget.r1_op == key:
        if op[4] > 0 and op[5] > 0:
            widget.Show()
        else:
            widget.Hide()
        return
    if owned:
        widget.r1_op = key
    kind, path, x, y, w, h = op
    widget.LoadImage(ROOT + path)
    widget.SetPosition(int(x) + dx, int(y) + dy)
    if kind == 'tile':
        tw, th = L.size(path)
        widget.SetRenderingRect(0.0, 0.0, float(w) / tw - 1.0, float(h) / th - 1.0)
        if w > 0 and h > 0:
            widget.SetSize(int(w), int(h))
    if alpha is not None:
        widget.SetAlpha(alpha)
    if w > 0 and h > 0:
        widget.Show()
    else:
        widget.Hide()


class Ops(object):
    """The images of one op list under a parent, all ExpandedImageBox (they also clip inside the lists that render
    their children inside their own rectangle). Apply() re-skins in place: the same order reuses the same widgets, so
    a state change never re-creates windows and never changes the draw order."""

    parent = _WeakParent()

    def __init__(self, parent, ops=None, dx=0, dy=0):
        self.parent = parent
        self.items = []
        self.dx, self.dy = dx, dy
        self.alpha = None
        if ops:
            self.Apply(ops)

    def Apply(self, ops):
        for index, op in enumerate(ops):
            if index >= len(self.items):
                widget = ui.ExpandedImageBox()
                widget.SetParent(self.parent)
                widget.AddFlag('not_pick')
                widget.r1_op = None             # made here: _put may skip re-drawing the same op
                self.items.append(widget)
            _put(self.items[index], op, self.dx, self.dy, self.alpha)
        for widget in self.items[len(ops):]:
            widget.Hide()

    def SetAlpha(self, alpha):
        self.alpha = alpha
        for widget in self.items:
            widget.SetAlpha(alpha)

    def Show(self):
        for widget in self.items:
            widget.Show()

    def Hide(self):
        for widget in self.items:
            widget.Hide()

    def Destroy(self):
        self.Hide()
        self.items = []
        self.parent = None


class Layer(ui.Window):
    """Not-pickable container that draws an op list. Keep a reference to it."""

    def __init__(self, parent, x, y, w, h, ops=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(max(0, int(w)), max(0, int(h)))
        self.ops = Ops(self, ops)
        self.Show()

    def Apply(self, ops):
        self.ops.Apply(ops)

    def Destroy(self):
        self.ops.Destroy()


def Image(parent, path, x, y):
    """Native-size R1 image (path relative to the R1 root), not pickable."""
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(ROOT + path)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


def ChevronPath(direction='right', state='normal'):
    return 'chevron/%s_%s.png' % (direction, state)


def Text(parent, text, x, y, font, color=T.INK, align='left', valign='center', outline=False, limit=None):
    return uikit.Text(parent, text, x, y, font, color, align, valign, outline, limit)


def CellTop(height, font):
    """y of a top-aligned text line whose font cell is centred in a row of ``height`` px."""
    return max(0, (int(height) - FontCell(font)) // 2)


def RowText(parent, text, x, height, font, color=T.INK, align='left'):
    """Text of a list row, vertically centred by its POSITION (top-aligned line at CellTop), never by the engine's
    vertical centre. Inside a list that renders its children inside its own rectangle (the wiki lists,
    SetInsideRender) the engine clips a text line to its parent as if the text ran from the line's y down by the text
    height (CWindow::UpdateTextLineRenderBox): a line at y = height / 2 with the vertical centre lost the bottom of
    its cell - the descenders ("Kostýmv" for "Kostýmy"). The whole cell stays inside the row this way."""
    return Text(parent, text, x, CellTop(height, font), font, color, align=align, valign='top')


def Fit(line, text, width, ellipsis='...'):
    """Sets ``text`` on ``line``, shortened with ``ellipsis`` to ``width`` px; returns the shown text."""
    line.SetText(text)
    if TextWidth(line) <= width:
        return text
    cut = text
    while len(cut) > 1:
        cut = cut[:-1]
        shown = cut.rstrip() + ellipsis
        line.SetText(shown)
        if TextWidth(line) <= width:
            return shown
    return line.GetText()


# --------------------------------------------------------------------------- frames, vein, rules
# The tooltip fill, variant C of the transparent tooltips: 70 % of the graphite, so the world shows through; no band
# under the text (the fill alone, the 1 px outline of the text lines). Menus and settings popups drawn with the
# tooltip frame are no tooltips: they keep the near opaque MENU_FILL_ALPHA.
TOOLTIP_FILL = 0x0C0B0C
TOOLTIP_FILL_ALPHA = 0.70
MENU_FILL_ALPHA = 0.94


class Frame(Layer):
    """9-slice frame: kind 'window' (graphite with the bronze hairline, the panel background), 'dialog' (the same
    with a soft shadow), 'tooltip' (thin outline, the see-through dark fill, shadow) or 'panel' (inner panel / content
    tile). The shadow lies outside the rectangle and is never pickable. Resize(w, h) re-lays it out.
    fill_alpha: the tooltip fill of a menu / settings popup on the tooltip frame (MENU_FILL_ALPHA)."""

    BG = {'window': 'panel', 'dialog': 'panel', 'panel': 'panel_dark', 'tooltip': None}

    def __init__(self, parent, x, y, w, h, kind='window', bg='auto', fill_alpha=None):
        self.kind = kind
        self.bg = self.BG.get(kind) if bg == 'auto' else bg
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.fill = None
        if kind == 'tooltip':           # made before the frame images: drawn under them
            alpha = TOOLTIP_FILL_ALPHA if fill_alpha is None else fill_alpha
            self.fill = Rect(self, 1, 1, 1, 1, TOOLTIP_FILL, alpha)
        self.ops = Ops(self)
        self.Resize(w, h)
        self.Show()

    def Resize(self, w, h):
        w, h = max(0, int(w)), max(0, int(h))
        self.SetSize(w, h)
        if self.fill is not None:
            self.fill.SetSize(max(1, w - 2), max(1, h - 2))
        self.ops.Apply(L.frame(self.kind, w, h, self.bg))


def DialogFrame(parent, x, y, w, h):
    """Frame of a dialog without a header (Ano / Ne, OK, a number): Esc / the cancel button close it."""
    return Frame(parent, x, y, w, h, 'dialog')


class Vein(Layer):
    """The red vein with its line on row ``y`` (the layer starts VEIN_ROW px above it)."""

    def __init__(self, parent, x, y, w):
        Layer.__init__(self, parent, x, int(y) - T.VEIN_ROW, w, L.size('vein/m.png')[1])
        self.SetWidth(w)

    def SetWidth(self, w):
        self.SetSize(max(0, int(w)), L.size('vein/m.png')[1])
        self.ops.Apply([(k, p, x, y + T.VEIN_ROW, ow, oh) for k, p, x, y, ow, oh in L.vein(0, 0, w)])


def Divider(parent, x, y, w):
    """Quiet hairline that fades in and out (the line on row y + 1)."""
    return Layer(parent, x, y, w, T.RULE_H, L.divider(0, 0, w))


# --------------------------------------------------------------------------- item slots (style C)
# The one item slot of R1 (team choice 7. 10. 2026, "C"): a lightly rounded 32 px cell with the graphite outline of
# the R1 buttons and a smooth dark well; its transparent corners leave the small gap where cells meet. The engine
# grid stays as it is (cell pitch 32, a tall item over 2 or 3 cells): the cell is drawn inside its own 32 x 32.
SLOT_CELL = ROOT + L.SLOT_CELL      # SetSlotBaseImage(SLOT_CELL, ...) on every R1 item grid / slot window


def SlotBase(height=T.SLOT):
    """The slot base image for a slot window whose slots are ``height`` px tall: the 32 px cell (every grid; the
    engine draws the base at every slot position) or the single tall slot of 64 / 96 px (a slot window with ONE tall
    slot draws its base once, at the slot's top left)."""
    return ROOT + L.slot_path(height)


def SlotGrid(parent, x, y, cols, rows):
    """Item cells for a grid whose cells were part of a picture (no slot base image): a not-pickable layer of
    cols x rows cells at the engine pitch from (x, y); nothing outside cols * 32 x rows * 32."""
    return Layer(parent, x, y, int(cols) * T.SLOT, int(rows) * T.SLOT, L.slot_grid(0, 0, cols, rows))


def SlotCell(parent, x, y, height=T.SLOT):
    """One item slot (32 x 32, or a single tall slot of 64 / 96 px; native size), not pickable: a single slot
    drawn as a picture."""
    ops = L.slot_cell(0, 0, height)
    return Layer(parent, x, y, ops[0][4], ops[0][5], ops)


def FitIcon(image, path, x, y, w, h):
    """Loads an item icon into ``image`` (an ExpandedImageBox) and centres it in the box (x, y, w, h); an icon larger
    than the box is scaled down uniformly to fit (the aspect ratio kept, linear filtering where the EXE has it). A list
    row shows a tall item (1 x 2, 1 x 3) this way in ONE slot cell. LoadImage makes a new image instance (scale and
    alpha reset), so the scale is set after it every time. Returns the scale."""
    image.LoadImage(path)
    iw, ih = max(1, image.GetWidth()), max(1, image.GetHeight())
    scale = min(1.0, float(w) / iw, float(h) / ih)
    if scale < 1.0:
        image.SetScale(scale, scale)
        try:
            image.SetLinearFiltering(True)
        except Exception:
            pass
    sw, sh = int(iw * scale), int(ih * scale)
    image.SetPosition(int(x) + (int(w) - sw) // 2, int(y) + (int(h) - sh) // 2)
    return scale


class Section(ui.Window):
    """Section heading: small text (text_sb) and a hairline after it that fades out to the right. Not pickable."""

    def __init__(self, parent, kit, x, y, w, text, color=T.INK_DIM):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit = kit
        self.h = kit.cell('text_sb') + 6
        self.w = int(w)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, self.h)
        self.rule = Ops(self, L.rule(0, 0, self.w))        # images before the label (the widest op list)
        self.label = RowText(self, '', 0, self.h, kit.font('text_sb'), color)
        self.SetText(text)
        self.Show()

    def SetText(self, text):
        self.label.SetText(text)
        rx = TextWidth(self.label) + 10
        self.rule.Apply(L.rule(rx, self.h // 2 - T.RULE_H // 2, self.w - rx))

    def Height(self):
        return self.h


class Band(object):
    """List row state: 'hover' = a lighter graphite fill, 'selected' = a dark fill with the red line under the row,
    'normal' = nothing. Plain ui.Bar fill + tiled line images (both clip inside lists). Create it before the row's
    texts."""

    parent = _WeakParent()

    def __init__(self, parent, x, y, w, h, state='normal'):
        self.parent = parent
        self.fill = Rect(parent, x, y, max(1, w), max(1, h), T.BAND_HOVER, T.BAND_ALPHA['hover'])
        self.line = Ops(parent, L.band_line(x, y + h, w))   # made now: under the texts made after the band
        self.line.Hide()
        self.rect = (int(x), int(y), int(w), int(h))
        self.state = None
        self.SetState(state)

    def Resize(self, x, y, w, h):
        self.rect = (int(x), int(y), int(w), int(h))
        state, self.state = self.state, None
        self.SetState(state)

    def SetState(self, state):
        if state == self.state:
            return
        self.state = state
        x, y, w, h = self.rect
        self.fill.SetPosition(x, y)
        self.fill.SetSize(max(1, w), max(1, h))
        if state in ('hover', 'selected'):
            colour = T.BAND_HOVER if state == 'hover' else T.BAND_SELECTED
            self.fill.SetColor(GenerateColor(colour, T.BAND_ALPHA[state]))
            self.fill.Show()
        else:
            self.fill.Hide()
        self.line.Apply(L.band_line(x, y + h, w) if state == 'selected' else [])

    def Show(self):
        self.SetState(self.state)

    def Hide(self):
        self.fill.Hide()
        self.line.Hide()

    def IsShow(self):
        return self.state in ('hover', 'selected')


# --------------------------------------------------------------------------- header and window chrome
class Close(Interactive):
    """The plain X (no box), red under the mouse; a 20 px hit box around the 10 px glyph."""

    def __init__(self, parent, x, y, event=None):
        Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(T.X_HIT, T.X_HIT)
        self.image = Image(self, 'close/x_normal.png', (T.X_HIT - T.X_SIZE) // 2, (T.X_HIT - T.X_SIZE) // 2)
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        self.image.LoadImage(ROOT + 'close/x_%s.png' % self.state())


class Grip(ui.Window):
    """Invisible drag handle: 'attach', so the engine hands a mouse-down on it to the ROOT window (CWindowManager::
    RunMouseLeftButtonDown -> CWindow::GetRoot), which comes to the front ('float') and moves ('movable') - the job
    of the original title bar."""

    def __init__(self, parent, x, y, w, h):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('attach')
        self.Place(x, y, w, h)
        self.Show()

    def Place(self, x, y, w, h):
        self.SetPosition(int(x), int(y))
        self.SetSize(max(0, int(w)), max(0, int(h)))


class Header(ui.Window):
    """Header INSIDE a window frame (no bar): the title in Cinzel upper case, the red vein under it on row HEAD_H and
    the plain X. Not pickable itself; its first child is a Grip over the whole header row (from left_reserved, the
    room of header buttons on the left), so a mouse-down anywhere on the row but the X - the frame edges, the corners,
    the title - raises and drags the window even where the window's own content (a slot grid, a board without
    'attach') lies under the header. The title and the X are made later and draw above it; the X picks first."""

    def __init__(self, parent, kit, w, title, on_close=None, align='center', left_reserved=0, x=0, y=0):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit = kit
        self.w = int(w)
        self.align, self.left_reserved = align, int(left_reserved)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, T.HEAD_H + T.VEIN_H // 2 + 1)
        self.grip = Grip(self, self.left_reserved, 0, self.w - self.left_reserved, T.HEAD_H)
        # The vein images first (their count depends only on the width): the title and the X draw above them.
        self.vein = Ops(self, L.header(self.w, 0, bool(on_close), self.left_reserved, align)['vein'])
        self.title = Text(self, '', 0, 0, kit.font('title'), T.IVORY)
        self.close = Close(self, 0, 0, on_close) if on_close else None
        self.SetTitle(title)
        self.Show()

    def SetTitle(self, title):
        self.title.SetText(Upper(title or ''))
        layout = L.header(self.w, TextWidth(self.title), self.close is not None, self.left_reserved, self.align)
        self.grip.Place(self.left_reserved, 0, self.w - self.left_reserved, T.HEAD_H)
        tx, ty = layout['title']
        self.title.SetPosition(tx, ty)
        self.vein.Apply(layout['vein'])
        if self.close is not None:
            cx, cy = layout['close'][:2]
            self.close.SetPosition(cx, cy)
        self.layout = layout

    def Height(self):
        return T.HEAD_H

    def ContentTop(self):
        return self.layout['content_top']


class Chrome(object):
    """The R1 window chrome drawn INTO an existing window of size w x h: the frame (with the background) and, with a
    title, the header with the vein and the X. Created first, so the window's own content draws above it.
    title=None: a dialog without a header (kind 'dialog')."""

    def __init__(self, window, kit, w, h, title=None, on_close=None, kind=None, align='center', left_reserved=0):
        self.kit = kit
        kind = kind or ('window' if title is not None else 'dialog')
        self.frame = Frame(window, 0, 0, w, h, kind)
        self.header = None
        if title is not None:
            self.header = Header(window, kit, w, title, on_close, align, left_reserved)

    def ContentTop(self):
        return self.header.ContentTop() if self.header else L.frame_inset() + 1

    def SetTitle(self, title):
        if self.header:
            self.header.SetTitle(title)

    def Widgets(self):
        return [w for w in (self.frame, self.header) if w is not None]

    def Show(self):
        for widget in self.Widgets():
            widget.Show()

    def Hide(self):
        for widget in self.Widgets():
            widget.Hide()

    def Destroy(self):
        self.Hide()
        self.frame.Destroy()
        self.frame = self.header = None


class Window(ui.Window):
    """A new R1 window (float + movable): Chrome with the title and the X (Close hides it, Esc closes it)."""

    def __init__(self, kit, w, h, title=None, close=True):
        ui.Window.__init__(self)
        self.kit = kit
        self.AddFlag('float')
        self.AddFlag('movable')
        self.SetSize(int(w), int(h))
        self.chrome = Chrome(self, kit, w, h, title, self.Close if close else None)

    def ContentTop(self):
        return self.chrome.ContentTop()

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True


# --------------------------------------------------------------------------- controls
class Button(Interactive):
    """R1 button: secondary (dark, graphite outline) or primary (dark with the red vein along the bottom edge; one per
    screen; in a row of confirm and cancel the main action stands on the LEFT, the cancel right). small=True: 22 px for rows and content, small='xs': 20 px (a thin footer
    button such as "Zprávy" of the friends list), else 26 px (window footer, dialogs). Cinzel label
    (the 'button' / 'button_s' roles)."""

    def __init__(self, parent, kit, x, y, w, text='', primary=False, small=False, event=None, font=None):
        Interactive.__init__(self)
        self.kit = kit
        self.primary, self.small = bool(primary), (small if small == 'xs' else bool(small))
        self.role = 'primary' if self.primary else 'secondary'
        self.w, self.h = int(w), L.button_height(small)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, self.h)
        self.ops = Ops(self, L.button(self.primary, self.small, 'normal', self.w))     # plate before the label
        self.custom_font = font
        self.given_text = text
        self.font = font or self.LabelFont(text)
        self.label = Text(self, WordGap(text, self.font), self.w // 2, 0, self.font,
                          T.PRIMARY_TEXT if self.primary else T.BUTTON_TEXT, align='center', valign='top')
        self.callback = event
        self.paint()
        self.Show()

    def LabelFont(self, text=''):
        """'button' (Cinzel 17 px) on a 26 px button; 'button_s' (Cinzel 15 px) on the small ones and whenever the
        larger label would not fit the width (a fixed-width button keeps its size, its label steps down)."""
        small = self.kit.font('button_s')
        large = self.kit.font('button')
        if self.small or FontCell(large) > self.h - 2:
            return small
        if text and self.w:
            probe = ui.TextLine()
            probe.SetFontName(large)
            probe.SetText(WordGap(text, large))
            if TextWidth(probe) > self.w - 12:
                return small
        return large

    def _SyncFont(self):
        font = self.custom_font or self.LabelFont(self.label.GetText())
        if font != self.font:
            self.font = font
            SetFont(self.label, font)

    def SetText(self, text):
        self.given_text = text
        self.label.SetText(WordGap(text, self.font))
        self.paint()

    def GetText(self):
        """The text as given (the label shows it with the word gaps of WordGap: Cinzel's space is only 3 px)."""
        shown = self.label.GetText()
        return self.given_text if shown == WordGap(self.given_text, self.font) else shown

    def SetWidth(self, w):
        self.w = int(w)
        self.SetSize(self.w, self.h)
        self.paint()

    def FitWidth(self, minimum=0, pad=12):
        """As wide as the label in the largest font the height allows, at least ``minimum``."""
        font = self.custom_font or (self.kit.font('button') if self.LabelFont() == self.kit.font('button') else
                                    self.kit.font('button_s'))
        probe = ui.TextLine()
        probe.SetFontName(font)
        probe.SetText(self.label.GetText())
        self.SetWidth(max(int(minimum), TextWidth(probe) + 2 * pad))
        return self.w

    def SetToolTipText(self, text, *unused_position):
        """A hover hint (uir1.Hint above the button), like ui.Button.SetToolTipText."""
        self.tooltip = text

    def OnMouseOverIn(self):
        Interactive.OnMouseOverIn(self)
        if getattr(self, 'tooltip', None):
            ShowHint(self.kit, self, self.tooltip)

    def OnMouseOverOut(self):
        Interactive.OnMouseOverOut(self)
        if getattr(self, 'tooltip', None):
            HideHint(self)

    def SetPrimary(self, primary):
        """Switches the role in place (a toggle that is on shows the vein, e.g. the shop's Koupit / Prodat)."""
        if bool(primary) != self.primary:
            self.primary = bool(primary)
            self.role = 'primary' if self.primary else 'secondary'
            self.paint()

    def paint(self):
        state = self.state()
        self.ops.Apply(L.button(self.primary, self.small, state, self.w))
        self._SyncFont()
        self.label.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                      (T.PRIMARY_TEXT if self.primary else T.BUTTON_TEXT))
        # Top-aligned and centred by position (CellTop): the whole label cell stays inside the plate; pressed moves
        # it 1 px down only while the cell still fits.
        top = CellTop(self.h, self.font)
        if self.pressed and top + FontCell(self.font) < self.h:
            top += 1
        self.label.SetPosition(self.w // 2, top)


class CheckBox(Interactive):
    """15 px check box with a glowing red tick, optional label right of it; the box + label is the hit area."""

    def __init__(self, parent, kit, x, y, text='', on=False, event=None, font=None, color=T.INK):
        Interactive.__init__(self)
        self.kit = kit
        self.on = bool(on)
        self.color = color
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        s = T.CHECK
        self.box = Image(self, 'check/off_normal.png', 0, 0)
        self.label = None
        w, h = s, s
        if text:
            font = font or kit.font('text')
            h = max(s, FontCell(font))
            self.label = Text(self, text, s + 7, h // 2, font, color)
            w = s + 7 + TextWidth(self.label)
        self.box.SetPosition(0, (h - s) // 2)
        self.w, self.h = w, h
        self.SetSize(w, h)
        self.callback = event
        self.paint()
        self.Show()

    def Width(self):
        return self.w

    def SetOn(self, on):
        if bool(on) != self.on:
            self.on = bool(on)
            self.paint()

    def IsOn(self):
        return self.on

    def paint(self):
        state = {'pressed': 'hover'}.get(self.state(), self.state())
        self.box.LoadImage(ROOT + 'check/%s_%s.png' % ('on' if self.on else 'off', state))
        if self.label is not None:
            self.label.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                          (T.IVORY if state == 'hover' else self.color))


class Slider(ui.Window):
    """Slider: a dark track, the red vein filled up to the knob, a small dark round knob with a red centre
    (ui.DragButton). Width() = track + knob; SetSliderPos / GetSliderPos like ui.SliderBar; a programmatic position
    never re-announces a change."""

    def __init__(self, parent, kit, x, y, track_w, event=None):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.track_w = int(track_w)
        self.knob_w = self.knob_h = T.KNOB
        self.h = max(T.KNOB, T.SLIDER_H)
        self.SetSize(self.track_w + self.knob_w, self.h)
        self.track_x, self.track_y = self.knob_w // 2, (self.h - T.SLIDER_H) // 2
        self.track = Ops(self, L.slider_track(self.track_x, self.track_y, self.track_w))
        self.fill = Ops(self)
        self.pos = 0.0
        self.hit = HitArea(self, 0, 0, self.track_w + self.knob_w, self.h)
        self.hit.OnMouseLeftButtonDown = self._Jump
        self.knob = ui.DragButton()
        self.knob.SetParent(self)
        self._Visuals('normal')
        self.knob.SetSize(self.knob_w, self.knob_h)
        self.knob_y = (self.h - self.knob_h) // 2
        self.knob.SetRestrictMovementArea(0, self.knob_y, self.track_w + self.knob_w, self.knob_h)
        self.knob.SetPosition(0, self.knob_y)
        self.knob.SetMoveEvent(ui.__mem_func__(self._OnMove))
        self.knob.Show()
        self.callback = event
        self._Fill()
        self.Show()

    def _Visuals(self, base):
        if base == 'disabled':
            for setter in (self.knob.SetUpVisual, self.knob.SetOverVisual, self.knob.SetDownVisual):
                setter(ROOT + 'slider/knob_disabled.png')
            return
        self.knob.SetUpVisual(ROOT + 'slider/knob_normal.png')
        self.knob.SetOverVisual(ROOT + 'slider/knob_hover.png')
        self.knob.SetDownVisual(ROOT + 'slider/knob_pressed.png')

    def Width(self):
        return self.track_w + self.knob_w

    def Enable(self):
        self.hit.Enable()
        self.knob.Enable()
        self._Visuals('normal')
        self.knob.SetRestrictMovementArea(0, self.knob_y, self.track_w + self.knob_w, self.knob_h)

    def Disable(self):
        self.hit.Disable()
        self.knob.Disable()
        self._Visuals('disabled')
        x = self.knob.GetLocalPosition()[0]
        self.knob.SetRestrictMovementArea(x, self.knob_y, self.knob_w, self.knob_h)

    def SetEvent(self, callback):
        self.callback = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback
        self.knob.OnMouseWheel = callback
        self.hit.OnMouseWheel = callback

    def _Fill(self):
        self.fill.Apply(L.slider_fill(self.track_x, self.track_y, int(round(self.pos * self.track_w))))

    def _OnMove(self):
        x = self.knob.GetLocalPosition()[0]
        self.pos = max(0.0, min(1.0, float(x) / max(1, self.track_w)))
        self._Fill()
        if self.callback:
            self.callback()

    def _Jump(self):
        try:
            mx = wndMgr.GetMousePosition()[0] - self.GetGlobalPosition()[0]
        except Exception:
            return True
        self.knob.SetPosition(max(0, min(self.track_w, int(mx - self.knob_w // 2))), self.knob_y)
        self._OnMove()
        return True

    def SetSliderPos(self, pos):
        enabled = getattr(self.knob, 'callbackEnable', True)
        self.knob.TurnOffCallBack()
        try:
            self.pos = max(0.0, min(1.0, float(pos)))
            self.knob.SetPosition(int(round(self.pos * self.track_w)), self.knob_y)
        finally:
            if enabled:
                self.knob.TurnOnCallBack()
        self._Fill()

    def GetSliderPos(self):
        return self.pos


class ScrollThumb(ui.DragButton):
    """The graphite thumb of ScrollBar with the red vein in its middle column (brighter under the mouse)."""

    def __init__(self, inset):
        ui.DragButton.__init__(self)
        self.AddFlag('movable')
        self.inset = inset
        self.state = 'normal'
        self.ops = Ops(self, L.vscroll('thumb', 'normal', inset, 0, T.SCROLL_MIN))
        self.h = 0

    def SetHeight(self, h):
        self.h = int(h)
        ui.DragButton.SetSize(self, T.SCROLL_W, self.h)
        self.paint()

    def paint(self):
        self.ops.Apply(L.vscroll('thumb', self.state, self.inset, 0, self.h))

    def OnMouseOverIn(self):
        self.state = 'hover'
        self.paint()

    def OnMouseOverOut(self):
        self.state = 'normal'
        self.paint()


class ScrollBar(ui.Window):
    """Narrow 8 px scroll bar: a dark track over the whole height and the graphite thumb (6 px, 1 px inside the
    track). The API of uikit.ScrollBar (SetScrollBarSize, SetMiddleBarSize, SetScrollStep, SetPos / GetPos, OnUp /
    OnDown, SetScrollEvent, Width); a click into the track jumps there. The window it is placed in scrolls it with
    the mouse wheel, one step per notch (uiwheel; an owner that also forwards the wheel keeps working)."""

    def __init__(self, kit=None):
        ui.Window.__init__(self)
        self.kit = kit
        self.w = T.SCROLL_W
        self.pageSize = 1
        self.curPos = 0.0
        self.scrollStep = 0.4
        self.eventScroll = None
        self.lockFlag = False
        self.track = Ops(self, L.vscroll('track', 'normal', 0, 0, 2 * T.SCROLL_MIN))   # before the thumb
        self.middleBar = ScrollThumb((T.SCROLL_W - T.THUMB_W) // 2)
        self.middleBar.SetParent(self)
        self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
        self.middleBar.SetHeight(T.SCROLL_MIN)
        self.middleBar.Show()
        self.SetScrollBarSize(2 * T.SCROLL_MIN)

    def Width(self):
        return self.w

    def SetParent(self, parent):
        ui.Window.SetParent(self, parent)
        uiwheel.Follow(self, parent)

    def SetScrollEvent(self, event):
        self.eventScroll = event

    def SetScrollBarSize(self, height):
        height = max(int(height), T.SCROLL_MIN)
        self.SetSize(self.w, height)
        self.track.Apply(L.vscroll('track', 'normal', 0, 0, height))
        self.pageSize = max(0, height - self.middleBar.h)
        self.middleBar.SetRestrictMovementArea(0, 0, self.w, height)
        self.middleBar.SetPosition(0, 0)
        self.curPos = 0.0

    def SetMiddleBarSize(self, pageScale):
        height = self.GetHeight()
        self.middleBar.SetHeight(max(T.SCROLL_MIN, min(height, int(float(pageScale) * height))))
        self.pageSize = max(0, height - self.middleBar.h)
        self.middleBar.SetRestrictMovementArea(0, 0, self.w, height)

    def SetScrollStep(self, step):
        self.scrollStep = step

    def GetScrollStep(self):
        return self.scrollStep

    def GetPos(self):
        return self.curPos

    def SetPos(self, pos, moveEvent=True):
        pos = max(0.0, min(1.0, float(pos)))
        self.middleBar.SetPosition(0, int(round(self.pageSize * pos)))
        self.curPos = pos
        if moveEvent:
            self.OnMove()

    def OnUp(self):
        self.SetPos(self.curPos - self.scrollStep)

    def OnDown(self):
        self.SetPos(self.curPos + self.scrollStep)

    def OnMove(self):
        if self.lockFlag or not self.pageSize:
            return
        self.curPos = max(0.0, min(1.0, float(self.middleBar.GetLocalPosition()[1]) / self.pageSize))
        if self.eventScroll:
            uikit.DispatchScroll(self, self.eventScroll)      # never nested while the thumb is dragged

    def OnMouseLeftButtonDown(self):
        try:
            y = wndMgr.GetMousePosition()[1] - self.GetGlobalPosition()[1]
        except Exception:
            return True
        if self.pageSize:
            self.SetPos(float(y - self.middleBar.h // 2) / self.pageSize)
        return True

    def Destroy(self):
        self.eventScroll = None


class Field(Interactive):
    """Edit field 24 px: a dark well with a graphite outline and a native ui.EditLine inside (self.edit); the red vein
    runs along its bottom while the line has the keyboard focus. A click anywhere in the well focuses the line. The
    placeholder (SetHint) is drawn in the field's font (not the EditLine's small default font)."""

    def __init__(self, parent, kit, x, y, w, hint='', edit=None, max_len=40, number=False, lead=0, trail=0,
                 font=None):
        Interactive.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.w, self.h = int(w), T.FIELD_H
        self.SetSize(self.w, self.h)
        self.ops = Ops(self, L.field('normal', self.w))
        self.font = font or kit.font('text')
        self.pad = 8
        self.edit = edit if edit is not None else ui.EditLine()
        self.edit.SetParent(self)
        cell = FontCell(self.font)
        self.lead, self.trail = int(lead), int(trail)
        self.edit.SetPosition(self.pad + lead, (self.h - cell) // 2)
        self.edit.SetSize(self.w - 2 * self.pad - lead - trail, cell + 2)
        self.edit.SetMax(max_len)
        # a handed-over edit line may already show text (the crafting amount "1", a dialog's count): SetFontName alone
        # would draw its old glyphs from the new atlas (in-game 9. 10.: "C" instead of "1")
        SetFont(self.edit, self.font)
        if number:
            self.edit.SetNumberMode()
        if hint:
            self.SetHint(hint)
        self.edit.Show()
        self.callback = self.Focus
        self.focused = False
        self.paint()
        self.Show()

    def SetWidth(self, w):
        """New width of the well (the edit line follows it); the height stays FIELD_H."""
        self.w = int(w)
        self.SetSize(self.w, self.h)
        self.edit.SetSize(max(1, self.w - 2 * self.pad - self.lead - self.trail), FontCell(self.font) + 2)
        self.paint()

    def SetHint(self, text):
        self.edit.SetInfoMessage(text)
        self._StyleHint()

    def _StyleHint(self):
        back = getattr(self.edit, 'backText', None)
        message = getattr(self.edit, 'infoMsg', '') or ''
        if back is None or getattr(back, '_r1_hint', None) == (self.font, message):
            return
        SetFont(back, self.font, message)
        back.SetPackedFontColor(T.MUTED)
        back._r1_hint = (self.font, message)

    def Focus(self):
        self.edit.SetFocus()
        self.SetFocused(True)

    def SetFocused(self, focused):
        if bool(focused) != self.focused:
            self.focused = bool(focused)
            self.paint()

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.focused:
            return 'focus'
        return 'hover' if self.hovered else 'normal'

    def paint(self):
        self.ops.Apply(L.field(self.state(), self.w))

    def OnUpdate(self):
        self._StyleHint()
        try:
            focused = bool(self.edit.IsFocus())
        except Exception:
            return
        if focused != self.focused:
            self.SetFocused(focused)


class Glyph(Interactive):
    """Small clickable R1 glyph (pattern with '%s' for normal / hover / pressed / disabled), e.g. the magnifier."""

    def __init__(self, parent, pattern, x, y, size, event=None, hit=None):
        Interactive.__init__(self)
        self.pattern = pattern
        hit = int(hit or size)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(hit, hit)
        self.image = Image(self, pattern % 'normal', (hit - size) // 2, (hit - size) // 2)
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        self.image.LoadImage(ROOT + self.pattern % self.state())

    def SetToolTipText(self, text, *unused_position):
        """A hover hint (uir1.Hint above the glyph), like ui.Button.SetToolTipText."""
        self.tooltip = text

    def OnMouseOverIn(self):
        Interactive.OnMouseOverIn(self)
        if getattr(self, 'tooltip', None):
            ShowHint(Kit(), self, self.tooltip)

    def OnMouseOverOut(self):
        Interactive.OnMouseOverOut(self)
        if getattr(self, 'tooltip', None):
            HideHint(self)


class SearchField(Field):
    """Search field: the magnifier (a click on it = on_search), the text and placeholder, and the small clear X only
    while there is something to clear (on_clear runs after the text was emptied)."""

    def __init__(self, parent, kit, x, y, w, hint='', edit=None, max_len=40, on_search=None, on_clear=None, font=None,
                 trail=None, lead=None):
        # trail: room kept free for the clear X on the right (a narrow field may let the placeholder run under it,
        # the X shows only once there is text); lead: the magnifier and the gap before the text.
        Field.__init__(self, parent, kit, x, y, w, hint=hint, edit=edit, max_len=max_len,
                       lead=T.ICON + 6 if lead is None else lead,
                       trail=T.CLEAR + 8 if trail is None else trail, font=font)
        self.icon = Glyph(self, 'icon/search_%s.png', 5, (self.h - T.ICON) // 2, T.ICON, on_search)
        self.on_clear = on_clear
        hit = T.CLEAR + 6
        self.clear = Glyph(self, 'icon/clear_%s.png', self.w - hit - 3, (self.h - hit) // 2, T.CLEAR, self.Clear, hit)
        self.clear.Hide()

    def Clear(self):
        self.edit.SetText('')
        self.clear.Hide()
        if self.on_clear:
            self.on_clear()

    def SyncClear(self):
        has_text = bool(self.edit.GetText())
        if has_text != bool(self.clear.IsShow()):
            self.clear.Show() if has_text else self.clear.Hide()

    def OnUpdate(self):
        Field.OnUpdate(self)
        self.SyncClear()


class SegmentCell(Interactive):
    def __init__(self, segment, index, pos, text):
        Interactive.__init__(self)
        self.segment, self.index, self.pos = segment, index, pos
        self.selected = False
        self.SetParent(segment)
        self.ops = Ops(self, L.segment_cell(pos, 'normal', 16, segment.height))        # images before the label
        self.label = (RowText(self, text, 0, segment.height, segment.font, T.INK_DIM, align='center')
                      if segment.height == T.WIKI_SEG_H else
                      Text(self, text, 0, 0, segment.font, T.INK_DIM, align='center'))
        self.w = 0
        self.Show()

    def Place(self, x, w, h=None):
        h = self.segment.height if h is None else h
        self.w = int(w)
        self.SetPosition(int(x), 0)
        self.SetSize(self.w, h)
        self.label.SetPosition(self.w // 2, CellTop(h, self.segment.font)
                               if self.segment.height == T.WIKI_SEG_H else h // 2 - 1)
        self.paint()

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.selected:
            return 'selected'
        return 'hover' if self.hovered else 'normal'

    def paint(self):
        if not self.w:
            return
        state = self.state()
        self.ops.Apply(L.segment_cell(self.pos, state, self.w, self.segment.height))
        self.label.SetPackedFontColor({'selected': T.IVORY, 'hover': T.INK, 'disabled': T.DISABLED}.get(state,
                                                                                                         T.INK_DIM))

    def click(self):
        self.segment.Select(self.index)

    def OnMouseOverIn(self):
        Interactive.OnMouseOverIn(self)
        if self.segment.on_hover:
            self.segment.on_hover()


class Segment(ui.Window):
    """One-of-N switch / tab row (24 px): one outline around the row; the selected cell is a dark well with the red
    line under its label. width = the whole row width shared by the cells (else each cell fits its label, at least
    min_cell). Width() is known after construction."""
    PAD = 12

    def __init__(self, parent, kit, options, event=None, font=None, width=None, min_cell=56, height=T.SEG_H):
        ui.Window.__init__(self)
        self.height = height
        self.kit = kit
        self.SetParent(parent)
        self.options = list(options)
        self.values = [value for value, unused in self.options]
        self.callback = event
        self.on_hover = None
        self.font = font or kit.font('text')
        n = len(self.options)
        self.cells = [SegmentCell(self, i, 'single' if n == 1 else ('first' if i == 0 else
                                                                   ('last' if i == n - 1 else 'mid')), label)
                      for i, (unused, label) in enumerate(self.options)]
        if width:
            base = int(width) // max(1, n)
            widths = [base] * n
            widths[-1] = int(width) - base * (n - 1)
        else:
            widths = [max(min_cell, TextWidth(cell.label) + 2 * self.PAD) for cell in self.cells]
        x = 0
        for cell, w in zip(self.cells, widths):
            cell.Place(x, w)
            x += w
        self.width = x
        self.SetSize(x, self.height)
        self.Show()

    def Width(self):
        return self.width

    def SetHoverEvent(self, callback):
        self.on_hover = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback
        for cell in self.cells:
            cell.OnMouseWheel = callback

    def SetValue(self, value):
        for cell, v in zip(self.cells, self.values):
            selected = v == value
            if selected != cell.selected:
                cell.selected = selected
                cell.paint()

    def Select(self, index):
        if self.callback:
            self.callback(self.values[index])

    def Enable(self):
        for cell in self.cells:
            cell.Enable()

    def Disable(self):
        for cell in self.cells:
            cell.Disable()


Tabs = Segment


# --------------------------------------------------------------------------- tooltip
class TooltipFrame(object):
    """Frame of a floating tooltip: soft shadow, the see-through dark fill, thin graphite outline. Create it FIRST in
    the tooltip window; Apply(w, h) resizes. Vein(x, y, w) draws the short vein under the item name.
    fill_alpha=MENU_FILL_ALPHA: a popup that is no tooltip (settings, a menu)."""

    parent = _WeakParent()

    def __init__(self, parent, fill_alpha=None):
        self.parent = parent
        self.frame = Frame(parent, 0, 0, 1, 1, 'tooltip', fill_alpha=fill_alpha)
        self.veins = []

    def Apply(self, w, h):
        self.frame.Resize(w, h)

    def Vein(self, x, y, w):
        vein = Vein(self.parent, x, y, w)
        self.veins.append(vein)
        return vein

    def Widgets(self):
        return [self.frame] + self.veins

    def Destroy(self):
        for widget in self.Widgets():
            widget.Hide()
        self.frame.Destroy()
        self.veins = []


# --------------------------------------------------------------------------- original boards in R1
def TitleBarParts(bar, board=None):
    """The shown parts of a ui.TitleBar that draw (its images, X and title texts), or None when ``bar`` is no title bar.

    A title bar is the window's drag handle: it has 'attach', so the engine hands a mouse-down on it to the root
    window, which moves when it is 'movable' (CWindowManager::RunMouseLeftButtonDown / RunMouseMove). R1 hides only
    these parts and keeps the bar shown, so the window is dragged where and in the child order the original was; the
    R1 header over it is not pickable and its X (made later) picks first."""
    parts = [getattr(bar, name, None) for name in ('imgLeft', 'imgCenter', 'imgRight', 'btnClose')]
    if parts[1] is None:
        return None
    parts += list(getattr(bar, 'Children', None) or ()) + [getattr(board, 'titleName', None)]
    return [part for part in parts if part is not None and hasattr(part, 'Hide') and part.IsShow()]


class BoardSkin(object):
    """R1 drawn INTO an original board in place (ui.Board / BoardWithTitleBar / ThinBoard / ThinBoardCircle, the board
    of a uiscript window): its own corner and line images and the title bar are hidden, its base (the first image it
    made, so it lies under every child of the window) becomes the R1 background, the R1 frame edges and - with a
    title - the R1 header with the X are drawn above. Nothing of the window's content is re-created, moved or
    re-parented, so every original control and its events keep working.

    kind 'window' (graphite frame, the panel background) or 'panel' (inner panel: thin outline, the dark well).
    hide: more original widgets to hide (e.g. a uiscript TitleBar that is not the board's own titleBar).
    Resize(w, h) after the owner resized the board; Restore() brings the original look back."""

    BASE_COLOR = {'window': 0xFF141213, 'panel': 0xFF0C0B0C}

    def __init__(self, board, kit, title=None, on_close=None, kind='window', hide=(), w=None, h=None):
        self.board = board
        self.kit = kit
        self.kind = kind
        self.hidden = []
        for name in ('Corners', 'Lines'):
            for widget in getattr(board, name, None) or ():
                self._Hide(widget)
        for widget in [getattr(board, 'titleBar', None)] + list(hide or ()):
            if widget is not None:
                self._HideTitleBar(widget, board)
        self.base = getattr(board, 'Base', None)
        self.base_path = getattr(self.base, 'name', None) or getattr(self.base, 'image_path', None)
        self.base_pos = self.base.GetLocalPosition() if self.base is not None else (0, 0)
        w = int(board.GetWidth() if w is None else w)
        h = int(board.GetHeight() if h is None else h)
        self.frame = Frame(board, 0, 0, w, h, kind, bg=None)       # the edges only: above the content
        self.header = Header(board, kit, w, title, on_close) if title is not None else None
        self.w, self.h = w, h
        self._Base()

    def _Hide(self, widget):
        widget.Hide()
        self.hidden.append(widget)

    def _HideTitleBar(self, bar, board):
        """A title bar stays shown as the invisible drag handle (TitleBarParts); other widgets are hidden."""
        parts = TitleBarParts(bar, board)
        if parts is None:
            self._Hide(bar)
            return
        for part in parts:
            self._Hide(part)
        bar.Show()

    def _Base(self):
        base, w, h = self.base, self.w, self.h
        if base is None:
            return
        base.SetPosition(1, 1)
        if hasattr(base, 'SetRenderingRect'):           # ui.Board: an ExpandedImageBox, tiled like uir1 tiles
            tile = 'textures/%s.png' % ('panel' if self.kind == 'window' else 'panel_dark')
            base.LoadImage(ROOT + tile)
            tw, th = L.size(tile)
            base.SetRenderingRect(0.0, 0.0, float(max(0, w - 2)) / tw - 1.0, float(max(0, h - 2)) / th - 1.0)
        else:                                            # ThinBoard(Circle): a ui.Bar
            base.SetSize(max(1, w - 2), max(1, h - 2))
            base.SetColor(GenerateColor(self.BASE_COLOR.get(self.kind, 0xFF141213), 1.0))
        base.Show()

    def ContentTop(self):
        return self.header.ContentTop() if self.header else L.frame_inset() + 1

    def SetTitle(self, title):
        if self.header is not None:
            self.header.SetTitle(title)

    def Resize(self, w, h):
        self.w, self.h = int(w), int(h)
        self.frame.Resize(self.w, self.h)
        if self.header is not None:
            self.header.w = self.w
            self.header.SetSize(self.w, self.header.GetHeight())
            self.header.SetTitle(self.header.title.GetText())
        self._Base()

    def Widgets(self):
        return [widget for widget in (self.frame, self.header) if widget is not None]

    def Restore(self):
        """The original look again: the hidden widgets shown, the base back, the R1 frame and header hidden."""
        for widget in self.Widgets():
            widget.Hide()
        for widget in self.hidden:
            widget.Show()
        base = self.base
        if base is not None:
            base.SetPosition(*self.base_pos)
            if hasattr(base, 'SetRenderingRect') and self.base_path:
                base.LoadImage(self.base_path)
        board = self.board
        board.SetSize(board.GetWidth(), board.GetHeight())   # the board lays its corners, lines and base out again
        if base is not None and not hasattr(base, 'SetRenderingRect'):
            try:
                base.SetColor(board.BOARD_COLOR)
            except Exception:
                pass

    def Destroy(self):
        for widget in self.Widgets():
            widget.Hide()
        self.frame.Destroy()
        self.frame = self.header = None
        self.board = self.base = None
        self.hidden = []


# --------------------------------------------------------------------------- bringing a window to the front
def Front(window, not_pick=False):
    """The window comes to the front when it is clicked. On a left mouse-down the engine first raises the top window
    under the mouse (CWindowManager::SetTopUIWindow -> CWindow::PickTopWindow of the "UI" layer, CWindow::SetTop),
    but moves it only when it has 'float', and a 'not_pick' top window is never picked for it. Then the window under
    the mouse takes the mouse-down; an 'attach' child (a title bar) hands it to the root window, whose
    OnMouseLeftButtonDown the engine calls. Front adds 'float'; not_pick=True (a window that is 'not_pick' itself,
    e.g. the pet and mount windows) also lets the window raise itself when a mouse-down reaches it through an
    'attach' child. The engine cannot remove a flag, so this stays when the original look is chosen again."""
    window.AddFlag('float')
    if not_pick:
        RaiseOnPress(window)


def RaiseOnPress(window):
    """The window's OnMouseLeftButtonDown first brings it to the front (idempotent, the window is held weakly;
    ``window`` may be a weak proxy, which forwards __class__ and attributes to the window)."""
    from _weakref import ref
    if window.__dict__.get('_r1RaiseOnPress'):
        return
    original = getattr(window.__class__, 'OnMouseLeftButtonDown', None)
    try:
        target = ref(window)
    except TypeError:                   # already a weak proxy
        target = lambda: window

    def down(*args):
        owner = target()
        if owner is None:
            return 0
        owner.SetTop()
        return original(owner, *args) if original is not None else 0

    window.OnMouseLeftButtonDown = down
    window._r1RaiseOnPress = True


# --------------------------------------------------------------------------- hover hint (the one R1 tooltip style)
# Variant C "Hlavička": every hover box of the R1 look
# is this hint - the tooltip frame, the name in ivory, optional dimmer lines under it. The red vein lies ONLY under a
# name that has lines below it: the bright glow, the name's width + HINT_VEIN_OVERHANG on each side with soft fading
# ends, centred, a clear gap to the first line; a one-line hint ("Otevřít okno cechu") is the frame and the centred
# text, no vein. The font is the item tooltip's (fontconfig ROLE_BODY: Tahoma 12, 14 with the
# larger font option), outlined, every line centred. "Starý vzhled" keeps every original tooltip.
HINT_PAD_X = 10          # text <-> frame, left and right
HINT_PAD_TOP = 5         # frame -> the name's cell
HINT_VEIN_GAP = 4        # the name's cell -> the vein line
HINT_BODY_GAP = 8        # the vein line -> the first line under it (a clear gap)
HINT_LINE_GAP = 5        # line pitch = font cell + this (17 px with Tahoma 12, the item tooltip's TEXT_LINE_HEIGHT)
HINT_PAD_BOTTOM = 5      # the vein line / the last line -> frame
HINT_GAP = 4             # anchor <-> hint: a hint never lies over the control it describes
HINT_MAX_W = 320         # a line wider than this wraps at word gaps
HINT_VEIN_MIN = 28       # narrowest hint (an empty or one-letter name)
HINT_VEIN_OVERHANG = 12  # the vein reaches this far past the name on each side, its ends fading there
HINT_BEAT = 0.25         # s: a TextTip whose button stopped updating (its window closed) loses its hint
HINT_WHITE = -1          # 0xFFFFFFFF as the signed int the engine takes: the hint text colour without a given one


def SignedColor(color):
    """A packed 0xAARRGGBB colour as the signed C int of the x64 wndMgr.SetFontColor binding: a Python int above
    0x7FFFFFFF (every 0xFF... token) does not fit, and the binding drops it silently (Py_BuildException() without
    a message clears the error), so the text keeps its previous colour."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def _HintShown(color):
    """The colour of a hint line, set on every show so nothing stays from the previous hint. R1_SIGNED_COLORS: the
    colour itself, signed. Off: what the engine showed before - a signed int as it is, an unsigned 0xFF... token
    (dropped by the engine, the line stayed white) as HINT_WHITE."""
    try:
        color = int(color)
    except (TypeError, ValueError):
        return HINT_WHITE
    if R1_SIGNED_COLORS:
        return SignedColor(color)
    return color if -0x80000000 <= color <= 0x7FFFFFFF else HINT_WHITE


def _HintTitleColor(color):
    """The hint name's colour: a given one (the minimap name) signed; without one T.IVORY with R1_SIGNED_COLORS,
    plain white (HINT_WHITE, the look before) without."""
    if color is not None:
        return SignedColor(color)
    return SignedColor(T.IVORY) if R1_SIGNED_COLORS else HINT_WHITE


def HintFont():
    """The item tooltip's font (fontconfig ROLE_BODY), so hints and item tooltips read alike."""
    try:
        import fontconfig
        return fontconfig.FontForRole(fontconfig.ROLE_BODY)
    except Exception:
        return 'Tahoma:12'


def _Screen():
    try:
        return wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
    except Exception:
        return 1920, 1080


def _Now():
    try:
        import app
        return app.GetTime()
    except Exception:
        return 0.0


def HintPlace(rect, w, h, side='above', edge=None, screen=None):
    """(x, y) of a w x h hint for the anchor rect (global x, y, w, h), never over the anchor.
    side 'above': centred above the anchor, below it when the screen has no room above.
    side 'left' / 'right': beside the anchor, vertically centred - for the vertical rails and panels at a screen
    edge, where a hint above would cover the next button; 'left' starts at ``edge`` (the global left edge of the
    whole rail) so it never covers the rail's other column; the other side when the screen has no room.
    Then clamped to the screen."""
    rx, ry, rw, rh = [int(v) for v in rect]
    w, h = int(w), int(h)
    sw, sh = screen or _Screen()
    if side in ('left', 'right'):
        left = (rx if edge is None else min(rx, int(edge))) - w - HINT_GAP
        right = rx + rw + HINT_GAP
        if side == 'left':
            x = left if left >= 0 else right
        else:
            x = right if right + w <= sw else left
        y = ry + (rh - h) // 2
    else:
        x = rx + (rw - w) // 2
        y = ry - h - HINT_GAP
        if y < 0:
            y = ry + rh + HINT_GAP
    return max(0, min(x, sw - w)), max(0, min(y, sh - h))


def HintLines(body, color=None):
    """[(text, colour)] from None, a text (lines split at "\n"), or a list of texts / (text, colour)."""
    color = T.INK_DIM if color is None else color
    if not body:
        return []
    if not isinstance(body, (list, tuple)):
        body = [body]
    lines = []
    for item in body:
        text, col = (item[0], item[1]) if isinstance(item, (list, tuple)) else (item, color)
        if text is None:
            continue
        if isinstance(text, bytes):
            parts = text.split(b'\n')
        elif hasattr(text, 'split'):
            parts = text.split('\n')
        else:
            parts = [str(text)]
        for part in parts:
            if part:
                lines.append((part, col))
    return lines


class HintFace(object):
    """The look of THE R1 hover hint, drawn into a window: the tooltip frame, the name in ivory, the lines under it
    dimmer with the red vein (the name's width + HINT_VEIN_OVERHANG on each side) between them; a name alone has no
    vein. Every line is centred in the item tooltip's font (HINT_*).
    Hint is the floating hover hint; a marker tooltip that follows the mouse inside a window (uir1atlas) has the same
    face and places itself. Call _InitFace() in the constructor before any other child (the frame lies under all)."""

    def _InitFace(self):
        self.frame = TooltipFrame(self)                      # first: under the vein and the text
        self.vein = Vein(self, 0, 0, HINT_VEIN_MIN)
        self.font = None
        self.title = None
        self.title_more = []                                 # the name's further lines when it wraps
        self.lines = []
        self.probe = None
        self.size = (0, 0)

    text = property(lambda self: self.title)          # the name line (the one line of the former hint)

    # ------------------------------------------------------------------ content
    def _Fonts(self):
        font = HintFont()
        if font != self.font:
            self.font = font
            for line in [self.title] + self.title_more + self.lines + [self.probe]:
                if line is not None:
                    line.Hide()
            self.title = Text(self, '', 0, 0, font, T.IVORY, align='center', valign='top', outline=True)
            self.title_more = []
            self.lines = []
            self.probe = Text(self, '', 0, 0, font, T.INK, valign='top', outline=True)
            self.probe.Hide()
        return font

    def _Width(self, text):
        self.probe.SetText(text)
        return TextWidth(self.probe)

    def _Wrap(self, text, max_w):
        if self._Width(text) <= max_w or ' ' not in text:
            return [text]
        out, cur = [], ''
        for word in text.split(' '):
            cand = (cur + ' ' + word) if cur else word
            if cur and self._Width(cand) > max_w:
                out.append(cur)
                cur = word
            else:
                cur = cand
        return out + ([cur] if cur else [])

    def SetContent(self, title, body=None, title_color=None, max_w=HINT_MAX_W):
        """Lays the hint out for ``title`` and the lines under the vein; returns (w, h). The hint is as wide as its
        widest line; a line wider than ``max_w`` (the name too) wraps at word gaps, so no text runs past the frame
        (a single word wider than max_w widens the hint instead)."""
        font = self._Fonts()
        cell = FontCell(font)
        pitch = cell + HINT_LINE_GAP
        title = title or ''
        # Set on every show (owner 10. 10.: button hints yellow / orange after a minimap name): a given colour (the
        # minimap name) only for this hint, signed so the engine takes it; without one ivory / white (_HintTitleColor).
        title_color = _HintTitleColor(title_color)
        heads = self._Wrap(title, max_w) if title else ['']
        self.title.SetText(heads[0])
        self.title.SetPackedFontColor(title_color)
        while len(self.title_more) < len(heads) - 1:
            self.title_more.append(Text(self, '', 0, 0, font, T.IVORY, align='center', valign='top', outline=True))
        widths = [TextWidth(self.title) if title else 0]
        for line, text in zip(self.title_more, heads[1:]):
            line.SetText(text)
            line.SetPackedFontColor(title_color)
            widths.append(TextWidth(line))
        title_w = max(widths)
        rows = []
        for text, color in HintLines(body):
            rows.extend((part, color) for part in self._Wrap(text, max_w))
        while len(self.lines) < len(rows):
            self.lines.append(Text(self, '', 0, 0, font, T.INK_DIM, align='center', valign='top',
                                   outline=True))
        for line, (text, color) in zip(self.lines, rows):
            line.SetText(text)
            line.SetPackedFontColor(_HintShown(color))
            widths.append(TextWidth(line))
        vein_w = (title_w + 2 * HINT_VEIN_OVERHANG) if (title and rows) else 0
        w = max(max(widths + [HINT_VEIN_MIN]) + 2 * HINT_PAD_X, vein_w + 8)
        self.title.SetPosition(w // 2, HINT_PAD_TOP)
        for index, line in enumerate(self.title_more):
            if index < len(heads) - 1:
                line.SetPosition(w // 2, HINT_PAD_TOP + (index + 1) * pitch)
                line.Show()
            else:
                line.Hide()
        name_bottom = HINT_PAD_TOP + (len(heads) - 1) * pitch + cell
        vein_row = name_bottom + HINT_VEIN_GAP
        y = vein_row + HINT_BODY_GAP
        for index, line in enumerate(self.lines):
            if index < len(rows):
                line.SetPosition(w // 2, y)
                line.Show()
                y += pitch
            else:
                line.Hide()
        if rows and title:
            h = y - HINT_LINE_GAP + HINT_PAD_BOTTOM
            self.vein.SetPosition((w - vein_w) // 2, vein_row - T.VEIN_ROW)     # centred under the name
            self.vein.SetWidth(vein_w)
            self.vein.Show()
        else:
            if not title:                                    # lines only: they start where the name would
                for line in self.lines:
                    if line.IsShow():
                        lx, ly = line.GetLocalPosition()
                        line.SetPosition(lx, ly - (vein_row + HINT_BODY_GAP - HINT_PAD_TOP))
                y -= vein_row + HINT_BODY_GAP - HINT_PAD_TOP
            h = (y - HINT_LINE_GAP + HINT_PAD_BOTTOM) if rows else (name_bottom + HINT_PAD_BOTTOM)
            self.vein.Hide()
        self.SetSize(w, h)
        self.frame.Apply(w, h)
        self.size = (w, h)
        return w, h


class Hint(HintFace, ui.Window):
    """THE R1 hover hint (HintFace). Floating, TOP_MOST and never pickable, so it never steals the hover of what it
    describes. One shared instance shows every hint of a control (SharedHint / ShowHint / ShowHintAt).

    ShowAt(rect, title, body, side, edge): placed by HintPlace. ``owner`` (any object) marks who showed it, so a
    HideHint(owner) of another control never hides it; ``watch`` = a widget: the hint goes away as soon as the mouse
    is not over that widget or it is hidden; ``beat`` = an object with a ``beat`` time (TextTip): the hint goes away
    when the beat is older than HINT_BEAT (the window of the button closed)."""

    def __init__(self, kit=None):
        ui.Window.__init__(self, 'TOP_MOST')
        self.kit = kit
        self.AddFlag('float')
        self.AddFlag('not_pick')
        self._InitFace()
        self.content = None
        self.follow = False
        self.owner = None
        self.watch = None
        self.beat = None
        self.Hide()

    # ------------------------------------------------------------------ showing
    def ShowAt(self, rect, title, body=None, side='above', edge=None, owner=None, watch=None, beat=None,
               title_color=None, follow=False):
        self.follow = bool(follow)                          # above the mouse cursor, moving with it
        content = (title, repr(body), title_color, HintFont())
        if content == self.content and self.IsShow():
            w, h = self.size                                 # shown every frame (a hover poll): only placed
        else:
            w, h = self.SetContent(title, body, title_color)
            self.content = content
        self.SetPosition(*HintPlace(rect, w, h, side, edge))
        self.owner = owner
        self.watch = _ref(watch) if watch is not None and _Weakable(watch) else None
        self.beat = _ref(beat) if beat is not None and _Weakable(beat) else None
        self.Show()
        self.SetTop()
        return self

    def ShowFor(self, widget, title, body=None, side='above', edge=None, owner=None, watch=False, title_color=None):
        """Placed at ``widget`` (its global rect); watch=True hides it once the mouse leaves the widget."""
        x, y = widget.GetGlobalPosition()
        return self.ShowAt((x, y, widget.GetWidth(), widget.GetHeight()), title, body, side, edge,
                           owner if owner is not None else widget, widget if watch else None, None, title_color)

    def HideFor(self, owner=None):
        """Hides the hint when ``owner`` showed it (any hint for owner=None)."""
        if owner is None or owner is self.owner:
            self.Hide()

    def IsShownFor(self, owner):
        return self.IsShow() and owner is self.owner

    def Hide(self):
        self.owner = self.watch = self.beat = None
        self.follow = False
        ui.Window.Hide(self)

    def OnUpdate(self):
        if self.follow:
            rect = _MouseRect()
            if rect is not None:
                self.SetPosition(*HintPlace(rect, self.size[0], self.size[1]))
        watch = self.watch() if self.watch is not None else None
        if self.watch is not None:
            try:
                if watch is None or not watch.IsShow() or not watch.IsIn():
                    self.Hide()
                    return
            except Exception:
                self.Hide()
                return
        if self.beat is not None:
            beat = self.beat()
            if beat is None or _Now() - getattr(beat, 'beat', 0.0) > HINT_BEAT:
                self.Hide()

    def Destroy(self):
        self.Hide()
        self.frame.Destroy()


def _Weakable(obj):
    try:
        _ref(obj)
        return True
    except TypeError:
        return False


_HINT = []


def SharedHint(kit=None):
    """The one hint of the client (only one control is hovered at a time)."""
    if not _HINT:
        _HINT.append(Hint(kit))
    return _HINT[0]


def ShowHint(kit, widget, text, body=None, side='above', edge=None, watch=False):
    """The shared hint at ``widget``. A ``text`` with line breaks and no ``body``: the first line is the name, the
    others go under the vein (the system notifications pass "title\nmessage")."""
    if body is None and text and '\n' in text:
        text, body = text.split('\n', 1)
    return SharedHint(kit).ShowFor(widget, text, body, side, edge, watch=watch)


def ShowHintAt(rect, title, body=None, side='above', edge=None, owner=None, watch=None, beat=None,
               title_color=None, follow=False):
    """The shared hint at a global rect (x, y, w, h); follow=True: above the mouse cursor, moving with it."""
    return SharedHint().ShowAt(rect, title, body, side, edge, owner, watch, beat, title_color, follow)


def _MouseRect():
    try:
        mx, my = wndMgr.GetMousePosition()
    except Exception:
        return None
    return (mx, my, 1, 1)


def HideHint(owner=None):
    if _HINT:
        _HINT[0].HideFor(owner)


def HintShownFor(owner):
    return bool(_HINT) and _HINT[0].IsShownFor(owner)


def TextTooltipShow(owner, text, rect=None, side='above', edge=None, title_color=None):
    """For the original frameless text tooltips (a TextLine at a point or at the mouse: the minimap buttons, the
    taskbar gauges, the party map name): True when the R1 look shows ``text`` as the shared hint for ``owner`` -
    at the global ``rect`` (by ``side``), above the mouse cursor without one; False in the original look, where the
    caller draws its text line as before. No text: nothing shows."""
    if not UseR1():
        return False
    if not text:
        HideHint(owner)
        return True
    if rect is None:
        rect = _MouseRect()
        if rect is None:
            return False
    ShowHintAt(rect, text, side=side, edge=edge, owner=owner, title_color=title_color)
    return True


class HintTooltip(object):
    """Stand-in for a uiToolTip.ToolTip that only lists lines (an info box without item data, e.g. the mount
    window's locked slots and its prismatic core): the first line (or SetTitle) is the name above the vein, the
    others go under it; ShowToolTip shows the shared hint above the mouse cursor, following it. Long lines wrap
    inside HINT_MAX_W (the old board kept a fixed width and long lines ran past its edges)."""

    def __init__(self, width=None, *unused):
        self.title = ''
        self.body = []

    def ClearToolTip(self):
        self.title = ''
        self.body = []

    def SetTitle(self, text):
        self.title = text

    def AppendTextLine(self, text, color=None, centerAlign=True):
        if not self.title:
            self.title = text
        else:
            self.body.append((text, T.INK_DIM if color is None else color))

    AutoAppendTextLine = AppendTextLine
    AutoAppendNewTextLineResize = AppendTextLine

    def AppendSpace(self, size):
        pass

    def ResizeToolTip(self):
        pass

    def SetFollow(self, flag):
        pass

    def ShowToolTip(self):
        rect = _MouseRect()
        if rect is not None and self.title:
            ShowHintAt(rect, self.title, list(self.body), owner=self, follow=True)

    def HideToolTip(self):
        HideHint(self)

    def IsShow(self):
        return HintShownFor(self)

    Show, Hide = ShowToolTip, HideToolTip


# --------------------------------------------------------------------------- button tooltips in the R1 look
class TextTip(ui.TextLine):
    """The hover text of an original button (ui.Button.SetToolTipText, a uiscript "tooltip_text") in the R1 look.

    ui.Button makes its tooltip window through ui.RegisterToolTipWindow("TEXT", ...): a TextLine child 19 px above
    the button, without a frame, drawn under the neighbouring buttons. In the R1 look that factory makes this
    TextLine instead: it keeps the TextLine API (text, alignment, colour, position - other code reads them), and
    when the button shows it on hover, the shared R1 hint shows the text above the button (HintPlace). Shown by code
    while the mouse is NOT over the shown button (uiwhisper's buttons keep their tooltip as a permanent name label),
    it stays the original text line for good; a hidden button (an original an R1 stand-in replaced) shows nothing.
    While its hint is up, a TextTipPulse beside it on the button beats as long as the button's window is updated: a
    window closed under the mouse drops the hint. (The line itself cannot beat: the engine's CTextLine::OnUpdate
    never calls Python, so a beat kept by the line alone dropped every button hint 0.25 s after it showed.)"""

    pulse = None    # Hide() runs from ui.Window.__init__ before our __init__ sets it

    def __init__(self):
        ui.TextLine.__init__(self)
        self.hint_text = ''
        self.label = False
        self.parent_ref = None
        self.beat = 0.0
        self.pulse = None

    def SetParent(self, parent):
        ui.TextLine.SetParent(self, parent)
        self.parent_ref = _ref(parent) if parent is not None and _Weakable(parent) else (lambda: parent)
        if self.pulse is not None:
            if parent is None:
                self.pulse.Hide()
            else:
                self.pulse.SetParent(parent)

    def _Pulse(self):
        """The TextTipPulse on the button (made on the first hover)."""
        if self.pulse is None:
            owner = self._Owner()
            if owner is None:
                return None
            self.pulse = TextTipPulse(self)
            self.pulse.SetParent(owner)
        return self.pulse

    def SetText(self, text):
        self.hint_text = text
        ui.TextLine.SetText(self, text if self.label else '')
        if HintShownFor(self):
            self._ShowHint()

    def GetText(self):
        return self.hint_text

    def GetTextSize(self):
        if self.label:
            return ui.TextLine.GetTextSize(self)
        ui.TextLine.SetText(self, self.hint_text)
        size = ui.TextLine.GetTextSize(self)
        ui.TextLine.SetText(self, '')
        return size

    def _Owner(self):
        return self.parent_ref() if self.parent_ref is not None else None

    def _Hovered(self, owner):
        try:
            return bool(owner.IsShow() and owner.IsIn())
        except Exception:
            return False

    def _ShowHint(self):
        owner = self._Owner()
        if owner is None or not self.hint_text:
            return
        self.beat = _Now()
        x, y = owner.GetGlobalPosition()
        ShowHintAt((x, y, owner.GetWidth(), owner.GetHeight()), self.hint_text, owner=self, beat=self)

    def Show(self):
        owner = self._Owner()
        if not self.label and owner is not None and UseR1():
            try:
                shown = owner.IsShow()
            except Exception:
                shown = False
            if not shown:
                return                      # a hidden (replaced) original button: its R1 stand-in shows the hint
            if self._Hovered(owner):
                ui.TextLine.SetText(self, '')
                ui.TextLine.Show(self)
                pulse = self._Pulse()
                if pulse is not None:
                    pulse.Show()
                self._ShowHint()
                return
        if not self.label:
            self.label = True               # shown by code, not by a hover: the original text line for good
            ui.TextLine.SetText(self, self.hint_text)
        ui.TextLine.Show(self)

    def Hide(self):
        HideHint(self)
        if self.pulse is not None:
            self.pulse.Hide()
        ui.TextLine.Hide(self)

    def OnUpdate(self):
        if not self.label:
            self.beat = _Now()


class TextTipPulse(ui.Window):
    """The heartbeat of a TextTip's hint: an empty, not pickable plain window on the button, shown while the hint is
    up. A plain window gets OnUpdate from the engine (CWindow::OnUpdate) every frame its parents are shown, a
    TextLine does not (CTextLine::OnUpdate overrides it without calling Python), so this window - not the line -
    keeps the TextTip's beat. Holds the TextTip weakly (the TextTip owns it)."""

    def __init__(self, tip):
        ui.Window.__init__(self)
        self.AddFlag('not_pick')
        self.SetSize(0, 0)
        self.tip_ref = _ref(tip)

    def OnUpdate(self):
        tip = self.tip_ref()
        if tip is not None:
            tip.OnUpdate()


def _TextTipFactory():
    return TextTip() if UseR1() else ui.TextLine()


def InstallTextTips():
    """Original buttons made from now on show their tooltip as the R1 hint (ui.Button.SetToolTipText)."""
    register = getattr(ui, 'RegisterToolTipWindow', None)
    if register is not None:
        register('TEXT', _TextTipFactory)


InstallTextTips()
