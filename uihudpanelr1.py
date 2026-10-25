# -*- coding: utf-8 -*-
"""The resizable HUD panels in the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md), drawn INTO the original
panels, including the title bar with the lock / arrow / X, the frame, grip dots and resize corner.

One base (PanelSkin) for every panel built on the HUD chrome of uicountdownhud (ui.Board 4 px in, a red ui.TitleBar
with the lock and collapse buttons, the title grip that moves the panel, the resize grip in a bottom corner, the
collapse to the title row):

* Odpočty (uicountdownhud.CountdownWindow)             -> CountdownSkin
* Sledovaná mise (uimissionbooktracker.MissionBookTracker) -> TrackerSkin

The base gives both the R1 frame and background (uir1.BoardSkin on the original board, moved to cover the whole
panel), a compact R1 header in the 23 px row of the original title bar (the title in Cinzel in the centre of the
whole row - the glyphs do not shift it -, the red vein under it, the plain X, the padlock and the chevron as R1
glyphs: the active lock is bright, the unlocked one muted - the rule "active = brightness") and the resize corner as R1 grip dots (muted, ivory under the mouse, red while dragged, dark
while locked). Collapsed, the panel is the R1 header row alone (23 px, no vein).

The panels keep their sizes, their saved geometry and every function: the drag on the title, the lock, the collapse,
the X, the resize, the wheel, the rows and their hints, the clicks that open Biolog / Dungeony / Mise. Their own
code still drives the original controls; the skin follows them (Sync after every layout / refresh, SyncResize after
UpdateResizeVisual) and its glyphs call the same methods the original buttons call (ToggleLock, ToggleCollapse,
Close).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original panels (from their next build). A failure while
building undoes every change, keeps the original look (traced to syserr) and that panel is not tried again in this
session; a failure while following the panel is traced and never breaks the panel's own refresh.
"""
import weakref

import ui

import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T

P = T.PROFILE_HUD               # the layout profile of the HUD panels (docs/ALTHEA_R1_KIT.md chap. 0)
HEAD = P['head']                # 23: the row of the original title bar; the collapsed panel is exactly this tall
CONTROL = P['hit']              # 20: hit box of a header glyph (by the 23 px row, never into the next glyph)
CONTROLS_Y = (HEAD - CONTROL) // 2
LOCK = 'd:/ymir work/ui/public/althea_r1_cech/lock_%s.png'      # the 12 x 14 R1 padlock (normal muted, hover ivory)
LOCK_SIZE = (12, 14)
CHEVRON_SIZE = (T.CHEVRON, T.CHEVRON)
TITLE_Y = HEAD // 2 + 1         # the title's centre line (uir1layout.header: HEAD_H // 2 + 1)
DOT, DOT_STEP = 2, 4            # the resize corner: 6 dots of 2 x 2 px in a triangle, 4 px apart (10 x 10)
DOTS = ((2, 0), (1, 1), (2, 1), (0, 2), (1, 2), (2, 2))         # the triangle towards the bottom right corner
DOT_COLORS = {'normal': T.MUTED, 'hover': T.IVORY, 'pressed': T.RED, 'disabled': T.DISABLED, 'selected': T.IVORY}

_failed = set()


def UseR1(what):
    """The R1 look unless "Starý vzhled" is chosen or this panel's R1 look already failed in this session."""
    return what not in _failed and uir1.UseR1()


def Fail(what):
    _failed.add(what)
    uir1.TraceFailure(what)


def Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 font binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def SetInk(line, color):
    line.SetPackedFontColor(Signed(color))


class Glyph(uir1.Interactive):
    """An R1 header glyph (padlock, chevron) with a 20 px hit box. ``paths(state, active)`` gives the image; the hint
    goes through the panel's own ShowHint / HideHint with the glyph as the anchor: the one R1 hint (uir1.ShowHint)
    above it, like the rest of the panel."""

    def __init__(self, parent, panel, size, paths, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetSize(CONTROL, CONTROL)
        self.panel = panel                          # weak proxy of the panel
        self.size = size
        self.paths = paths
        self.active = False
        self.hint = ''
        self.shown = None
        self.image = ui.ExpandedImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        self.image.Show()
        self.callback = event
        self.paint()
        self.Show()

    def SetActive(self, active, hint):
        self.hint = hint
        if bool(active) != self.active:
            self.active = bool(active)
            self.paint()

    def paint(self):
        path = self.paths(self.state(), self.active)
        if path != self.shown:
            self.shown = path
            self.image.LoadImage(path)
            self.image.SetPosition((CONTROL - self.size[0]) // 2, (CONTROL - self.size[1]) // 2)

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        try:
            if self.hint:
                self.panel.ShowHint(self.hint, self)
        except ReferenceError:
            pass

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        try:
            self.panel.HideHint()
        except ReferenceError:
            pass

    def Destroy(self):
        self.callback = None
        self.panel = None


def LockPath(state, active):
    return LOCK % ('hover' if active or state in ('hover', 'pressed') else 'normal')


def ClosePath(state, active):
    """The plain X of the kit (uir1.Close: close/x_<state>.png, red under the mouse) as a header glyph."""
    return uir1.ROOT + 'close/x_%s.png' % state


def ChevronPaths(direction):
    def paths(state, active):
        return uir1.ROOT + uir1.ChevronPath(direction(), {'pressed': 'active'}.get(state, state))
    return paths


class ResizeDots(ui.Window):
    """The R1 resize corner: six 2 x 2 px dots in a triangle towards the panel's corner (mirrored for the left one),
    plain ui.Bar fills (nothing to stretch, no texture). Not pickable: the original resize grip under it takes the
    mouse."""

    def __init__(self, parent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetSize(3 * DOT_STEP - (DOT_STEP - DOT), 3 * DOT_STEP - (DOT_STEP - DOT))
        self.dots = [uir1.Rect(self, 0, 0, DOT, DOT, DOT_COLORS['normal'] & 0xFFFFFF) for unused in DOTS]
        self.look = None
        self.Show()

    def Set(self, side, state):
        look = (side, state)
        if look == self.look:
            return
        self.look = look
        color = uir1.GenerateColor(DOT_COLORS.get(state, T.MUTED) & 0xFFFFFF, 1.0)
        for dot, (col, row) in zip(self.dots, DOTS):
            col = 2 - col if side == 'left' else col
            dot.SetPosition(col * DOT_STEP, row * DOT_STEP)
            dot.SetColor(color)


class PanelSkin(object):
    """R1 look of one HUD panel (the shared base, see the module doc). A build failure undoes every change and
    re-raises (Build traces it)."""

    WHAT = u'HUD panel'

    def __init__(self, window, title, settings):
        self.window = weakref.proxy(window)
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.settings = settings                    # () -> the panel's settings dict (locked, collapsed)
        self.titleText = title
        self.widgets = []
        self.board = None
        self.titleLook = None
        try:
            self._Build(window)
            self._BuildContent(window)
            self.Sync()
        except Exception:
            self.Undo()
            raise

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    # ------------------------------------------------------------------ build
    def _Build(self, w):
        rec, kit = self.rec, self.kit
        W, H = w.GetWidth(), w.GetHeight()
        board = w.board
        rec.Position(board, 0, 0)
        rec.Size(board, W, H)
        rec.Hide(w.titleBar)                        # its title, lock, collapse and X: the R1 header below
        grip = getattr(w, 'gripImage', None)
        if grip is not None:
            rec.Hide(grip)                          # the grip dots of the title: the whole R1 header row drags
        # no "Tažením přesuň okno" on the header row - the R1 header has no drag control to name (the
        # grip dots are hidden), so the hint flashed in every gap between the title and the glyphs
        title_grip = w.titleGrip
        move_hint = title_grip.tooltipText
        rec.Call(lambda: setattr(title_grip, 'tooltipText', ''),
                 lambda: setattr(title_grip, 'tooltipText', move_hint))
        rec.Hide(w.resizeImage)
        self.board = uir1.BoardSkin(board, kit, title=None, kind='window', w=W, h=H)
        self.dots = self._new(ResizeDots(w.resizeGrip))
        # The header: made after the panel's content, so it draws above it; the title is not pickable (a drag on it
        # reaches the panel's title grip, which Sync spreads over the whole row), the glyphs above the grip take
        # their clicks.
        self.vein = self._new(uir1.Vein(w, 6, HEAD, max(0, W - 12)))
        self.title = self._new(uir1.Text(w, '', W // 2, TITLE_Y, kit.font('title'), T.IVORY, align='center'))
        me = weakref.proxy(w)
        # the X is a Glyph like the padlock and the chevron (the same 20 px hit box and hover state), but
        # without a hint - owner 10. 10.: the X needs no tooltip
        self.close = self._new(Glyph(w, me, (T.X_SIZE, T.X_SIZE), ClosePath, ui.__mem_func__(w.Close)))
        self.collapse = self._new(Glyph(w, me, CHEVRON_SIZE, ChevronPaths(self._Arrow),
                                        ui.__mem_func__(w.ToggleCollapse)))
        self.lock = self._new(Glyph(w, me, LOCK_SIZE, LockPath, ui.__mem_func__(w.ToggleLock)))

    def _BuildContent(self, w):
        """The panel's own content (CountdownSkin, TrackerSkin)."""

    def Hint(self, key):
        """The header hints (LOCK / UNLOCK / COLLAPSE / EXPAND) of this panel; Odpočty's own texts by default."""
        import uicountdownhud
        return uicountdownhud.Text(key)

    def _Arrow(self):
        # the original buttons: "up" while collapsed (expand), "down" while expanded (collapse)
        return 'up' if self.settings()['collapsed'] else 'down'

    # ------------------------------------------------------------------ state
    def Sync(self):
        """After the panel laid itself out or refreshed: the frame size, the collapsed row, the header controls."""
        w = self.window
        s = self.settings()
        W, H = w.GetWidth(), w.GetHeight()
        collapsed = bool(s['collapsed'])
        board = w.board
        moved = board.GetLocalPosition() != (0, 0) or (board.GetWidth(), board.GetHeight()) != (W, H)
        if moved:
            # the panel lays its board out again (4 px in, 8 px narrower, its own base tiling): the R1 board covers
            # the whole panel again and its base is tiled again
            board.SetPosition(0, 0)
            board.SetSize(W, H)
        if moved or (self.board.w, self.board.h) != (W, H):
            self.board.Resize(W, H)
        if not board.IsShow():
            board.Show()                            # collapsed: the R1 frame is the header row
        # the panel's title grip (w - 71 wide, the 3 px before the padlock and the gaps around the glyphs dead): the
        # whole header row; the glyphs, made after it, lie above it and still take their own clicks
        w.titleGrip.SetSize(W, HEAD)
        self.vein.SetWidth(max(0, W - 12))
        self.vein.Hide() if collapsed else self.vein.Show()
        layout = L.header(W, 0, True)
        cx, cy = layout['close'][:2]
        self.close.SetPosition(cx, CONTROLS_Y)
        self.collapse.SetPosition(cx - CONTROL - 2, CONTROLS_Y)
        self.lock.SetPosition(cx - 2 * (CONTROL + 2), CONTROLS_Y)
        hint = self.Hint
        self.close.SetActive(False, '')
        self.lock.SetActive(s['locked'], hint('UNLOCK' if s['locked'] else 'LOCK'))
        self.collapse.SetActive(False, hint('EXPAND' if collapsed else 'COLLAPSE'))
        self.collapse.paint()                       # the arrow follows the collapsed state
        # UI rules 9. 10. ("Vystředění"): the title in the centre of the WHOLE header row, the glyphs on the right do
        # not shift it; it is shortened symmetrically so that it never reaches the padlock
        centre = W // 2
        room = 2 * max(0, self.lock.GetLocalPosition()[0] - 4 - centre)
        look = (self.titleText, W)
        if look != self.titleLook:
            self.titleLook = look
            uir1.Fit(self.title, (self.titleText or '').upper(), room)
            self.title.SetPosition(centre, TITLE_Y)
        self.SyncResize()
        self._SyncContent(w, W, H, collapsed)

    def _SyncContent(self, w, W, H, collapsed):
        """The panel's own content after a refresh (CountdownSkin, TrackerSkin)."""

    def SyncResize(self):
        """The R1 dots in the resize grip in the state the panel chose (UpdateResizeVisual -> resizeState)."""
        w = self.window
        side, state = getattr(w, 'resizeState', None) or ('right', 'normal')
        self.dots.Set(side, state)
        self.dots.SetPosition(8 if side == 'right' else 7, 10)

    def SyncSafe(self):
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure(u'%s (stav)' % self.WHAT)

    def SyncResizeSafe(self):
        try:
            self.SyncResize()
        except Exception:
            uir1.TraceFailure(u'%s (stav)' % self.WHAT)

    # ------------------------------------------------------------------ teardown
    def Undo(self):
        if self.board is not None:
            try:
                self.board.Restore()
            except Exception:
                pass
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        if self.board is not None:
            try:
                self.board.Destroy()
            except Exception:
                pass
        self.widgets, self.board = [], None

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        if self.board is not None:
            self.board.Destroy()
        self.widgets, self.board = [], None
        self.rec.undo = []


# --------------------------------------------------------------------------- Odpočty
class CountdownSkin(PanelSkin):
    """Odpočty: the Biolog / Dungeony bands as R1 section headings (the label in the R1 ink, a hairline after it; the
    band icons stay), the rows' dividers, progress and ready mark in R1 colours, the time in the R1 ink (waiting /
    locked muted) instead of copper, "Připraveno" in the panel's own ready green (uicountdownhud.READY, the Biolog
    green: the same colour and font in Biolog and Dungeony), the thin scroll bar in R1 graphite."""

    WHAT = u'Odpočty'
    TRACK, THUMB = T.LINE, T.MUTED
    SEPARATOR, PROGRESS_BACK, PROGRESS, READY_MARK = T.LINE, T.INNER, T.RED_DK, T.RED

    def _BuildContent(self, w):
        import fontconfig
        import uicountdownhud as C
        rec = self.rec
        section = fontconfig.FontForRole(fontconfig.ROLE_SECTION)       # the bands' labels (uicountdownhud._Line)
        self.rules = []
        for band, surface, label, color in ((w.bioBand, w.bioSurface, w.bioLabel, C.BIO),
                                            (w.dungeonBand, w.dungeonSurface, w.dungeonLabel, C.COPPER)):
            rec.Hide(surface)
            rec.Font(label, self.kit.font('text_sb'), Signed(T.INK_DIM), section, Signed(_Packed(color)))
            self.rules.append((band, label, self._new(uir1.Layer(band, 0, 0, 1, T.RULE_H, []))))
        for bar, color, original in ((w.scrollBack, self.TRACK, 0xff29231e), (w.scrollThumb, self.THUMB, 0xff937b59)):
            rec.Call(lambda bar=bar, color=color: bar.SetColor(color),
                     lambda bar=bar, original=original: bar.SetColor(original))
        self.rows = {}

    def _SyncContent(self, w, W, H, collapsed):
        for band, label, rule in self.rules:
            x = label.GetLocalPosition()[0] + uir1.TextWidth(label) + 8
            width = band.GetWidth() - x
            look = (x, width)
            if getattr(rule, 'look', None) != look:
                rule.look = look
                rule.SetSize(max(1, band.GetWidth()), band.GetHeight())
                rule.Apply(L.rule(x, band.GetHeight() // 2 - T.RULE_H // 2, width))
        # the Biolog rows () are drawn like the dungeon rows: the same divider, ready mark and inks
        for row in list(w.rows) + list(getattr(w, 'bioRows', ())):
            key = id(row)
            if key not in self.rows:
                row.separator.SetColor(self.SEPARATOR)
                if hasattr(row, 'progress'):
                    row.progressBack.SetColor(self.PROGRESS_BACK)
                    row.progress.SetColor(self.PROGRESS)
                row.readyMark.SetColor(self.READY_MARK)
                self.rows[key] = None
            signature = row.signature
            if signature is None or self.rows[key] == signature:
                continue
            self.rows[key] = signature
            state = signature[2]
            SetInk(row.time, ReadyInk() if state == 'ready' else T.INK if state == 'cooldown' else T.MUTED)
            SetInk(row.name, T.MUTED if state == 'locked' else T.INK)


def ReadyInk():
    """The "Připraveno" ink of every Odpočty section: the panel's ready green, the colour the Biolog row keeps."""
    import uicountdownhud as C
    return _Packed(C.READY)


def _Packed(color):
    """(r, g, b) floats of the original panels -> 0xAARRGGBB."""
    r, g, b = [max(0, min(255, int(round(c * 255)))) for c in color]
    return 0xFF000000 | (r << 16) | (g << 8) | b


# --------------------------------------------------------------------------- Sledovaná mise
class TrackerSkin(PanelSkin):
    """Sledovaná mise: the mission book icon on the R1 item slot C, the target names in the R1 ink and the counters
    bright, the narrow R1 scroll bar (uir1.ScrollBar, the same API) in place of the crimson one."""

    WHAT = u'Sledovaná mise'

    def Hint(self, key):
        """The chevron says what it folds: "Sbalit / Rozbalit sledovanou misi" (it said "Sbalit odpočty" here,
        ); the padlock keeps the shared "Zamknout / Odemknout polohu a velikost"."""
        if key in ('COLLAPSE', 'EXPAND'):
            from missionbooklocale import Text
            return Text('TRACKER_' + key)
        return PanelSkin.Hint(self, key)

    def _BuildContent(self, w):
        rec = self.rec
        self.cell = self._new(uir1.SlotCell(w.bookHit, 0, 0))       # under the book image the panel makes later
        original = w.scroll
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(w)
        bar.SetScrollEvent(ui.__mem_func__(w.Refresh))
        try:
            bar.SetScrollStep(original.GetScrollStep())
        except Exception:
            pass
        bar.Hide()
        self.bar = self._new(bar)
        self.originalScroll = original
        rec.Hide(original)

        def attach():
            w.scroll = bar

        def detach():
            w.scroll = original
        rec.Call(attach, detach)
        self.styled = 0

    def _SyncContent(self, w, W, H, collapsed):
        bar = self.bar
        if bar.GetLocalPosition() != (W - 18, 33):
            bar.SetPosition(W - 18, 33)
        rows = w.rows
        for name, count in rows[self.styled:]:
            SetInk(name, T.INK)
            SetInk(count, T.IVORY)
        self.styled = len(rows)

    def Undo(self):
        PanelSkin.Undo(self)
        self.originalScroll = None

    def Destroy(self):
        original, self.originalScroll = self.originalScroll, None
        if original is not None:
            try:
                original.Destroy()
            except Exception:
                pass
        PanelSkin.Destroy(self)


def Build(window, kind, title, settings):
    """The R1 skin of a HUD panel or None (the original look: "Starý vzhled", or the build failed - traced).
    kind: CountdownSkin or TrackerSkin; title: the panel's title text; settings: () -> its settings dict."""
    if not UseR1(kind.WHAT):
        return None
    try:
        return kind(window, title, settings)
    except Exception:
        Fail(kind.WHAT)
        return None
