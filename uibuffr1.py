# -*- coding: utf-8 -*-
"""Šamanská deska (the support shaman "Buffi" board, uibuff.SupportMainGui on uiscript/buffinformationwindow.py) in
the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

The window keeps its size (250 x 285), its flags (movable, float, not_pick, animate - the board is the drag handle)
and every control: the five skill slots with their tooltips, the locks and the upgrade buttons, the three EXP modes
(their original radio buttons stay the source of the clicks and of the state the server sends), the progress values,
the name and the intelligence, the equipment strip on the left with its six slots and the button that shows it.
This module only re-skins them:

* the R1 frame and header (Cinzel title, vein, plain X) on the dragon board (its art and the title bar hidden);
* the portrait in the recoloured portrait frame of the character window, the name in a dark R1 panel next to it
  and the intelligence under it;
* the progress panel: level and passive points on the first row, the EXP as the red vein on a dark track with the
  numbers next to it, the status on the last row (its colour still comes from the window);
* the EXP modes as an R1 segment in front of the original radio buttons; until the player reaches level 90 the
  window does not send a mode (uibuff.OnSelectExpMode), so the other two modes are drawn disabled and the hover hint
  says from which level the switch works;
* "Dovednosti" as an R1 section in a dark panel with the original skill slots and the R1 "+" buttons under them;
* the equipment strip keeps its original art (the slot shapes), framed in R1; the button that slides it out and
  back is an R1 drawer tab (dark plate, light outline, a chevron pointing where the strip goes; red under the mouse)
  on the window's left edge, or on the strip's left edge while the strip is out (the thin grey bar of the recoloured
  belt art was nearly invisible in game).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building undoes every
change, keeps the original look (traced to syserr) and the R1 look is not tried again in this session.
"""
import weakref

import ui

import uir1
import uir1layout as L
import uir1skin
import uir1tokens as T

ART = 'd:/ymir work/ui/public/althea_r1_postava/character/'
PLUS_ORIGINAL = ('d:/ymir work/ui/game/windows/btn_plus_up.sub', 'd:/ymir work/ui/game/windows/btn_plus_over.sub',
                 'd:/ymir work/ui/game/windows/btn_plus_down.sub')
PLUS_R1 = (ART + 'plus_normal.png', ART + 'plus_hover.png', ART + 'plus_pressed.png')
BELT = 'd:/ymir work/ui/game/belt_inventory/'
MINIMIZE_ORIGINAL = tuple(BELT + 'btn_minimize_%s.tga' % s for s in ('normal', 'over', 'down'))
DRAWER = dict((direction, tuple(ART + 'drawer_%s_%s.png' % (direction, s) for s in ('normal', 'hover', 'pressed')))
              for direction in ('left', 'right'))
DRAWER_W, DRAWER_H = 14, 56             # tools/build_althea_r1_postava.py drawer()
DRAWER_OVERLAP = 1                      # the tab's outline lies on the frame line of the window / strip
DRAWER_Y = 65                           # tab top under the window top: centred on the strip (y + 30, 126 px)
FACE_ORIGINAL = 'd:/ymir work/ui/game/windows/box_face.sub'
ORIGINAL_GOLD = 0xFFECC576              # the level / passive points colour of the original look

W, H = 250, 285
PORTRAIT = (11, 35)                     # Face_Slot (53 x 53, the face 4 px inside)
NAME = (72, 36, 167, 25)                # the name panel (NameWindow), right edge = the panels' right edge
INT_Y = 66                              # the intelligence line under the name
PROGRESS = (11, 92, 228, 55)            # ProgressWindow: rows at 5, the track at 23, the status at 38
PROGRESS_PAD = 10
TRACK_Y = 23
EXP_GAP = 8                             # between the track and the EXP numbers
TRACK_MIN = 60
STATUS_Y = 38
SEGMENT = (11, 153, (76, 76, 76))       # the EXP modes (24 px)
SKILLS = (11, 183, 228, 92)             # the "Dovednosti" panel
SKILL_ICONS = (19, 31)                  # Buffi_Skill_Icons inside the panel (slots at 0, 40, ... 160)
PLUS_OFFSET = (7, 36)                   # an upgrade button under its slot (x of the slot + 7)
SKILL_X = (0, 40, 80, 120, 160)
LOCKED_HINT = u'Režim BZK zvolíš od úrovně hráče 90.'

_failed = []


def UseR1():
    """The R1 look unless "Starý vzhled" is chosen or the R1 look of this window already failed in this session."""
    return not _failed and uir1.UseR1()


def Fail():
    _failed.append(1)
    uir1.TraceFailure(u'Šamanská deska')


class GaugeAdapter(object):
    """Stands in for the original EXP gauge (owner.progressGauge): the hidden gauge keeps every value, the R1 track
    shows it."""

    def __init__(self, gauge, skin):
        self.gauge = gauge
        self.skin = skin

    def SetPercentage(self, current, maximum):
        self.gauge.SetPercentage(current, maximum)
        self.skin.SetExp(current, maximum)

    def __getattr__(self, name):
        return getattr(self.gauge, name)


class BuffSkin(object):
    """R1 look of one SupportMainGui. A build failure undoes every change and re-raises (the window traces it)."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.skins = []
        self.mirrors = []
        self.fraction = 0.0
        self.shown = {}
        try:
            self._Build()
            self.Sync()
        except Exception:
            self.Undo()
            raise

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    def _skin(self, board, **kwargs):
        skin = uir1.BoardSkin(board, self.kit, **kwargs)
        self.skins.append(skin)
        return skin

    # ------------------------------------------------------------------ build
    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.GetChild('board')
        # 'not_pick' (uiscript buffinformationwindow): the engine never raises it on a click by itself; a mouse-down
        # on the board or the header grip ('attach') reaches the window, which then comes to the front.
        uir1.Front(w, not_pick=True)
        title = w.GetChild('TitleName').GetText() if w.IsChild('TitleName') else ''
        self._skin(board, title=title or u'Šamanská deska', on_close=ui.__mem_func__(w.Close),
                   hide=[w.GetChild('TitleBar')])

        # The portrait and the full-width intelligence row have no function of their own: a drag on them moves the
        # window like a drag on the board (the engine cannot take a flag back; 'not_pick' is harmless in the old look).
        for name in ('Face_Slot', 'Shaman_Icon', 'Intelligence'):
            if w.IsChild(name):
                w.GetChild(name).AddFlag('not_pick')
        face = w.GetChild('Face_Slot')
        rec.Position(face, *PORTRAIT)
        rec.Image(face, ART + 'portrait_frame.png', FACE_ORIGINAL)

        x, y, nw, nh = NAME
        name_board = w.GetChild('NameWindow')
        rec.Position(name_board, x, y)
        rec.Size(name_board, nw, nh)
        self._skin(name_board, kind='panel', w=nw, h=nh)
        name = w.GetChild('SupportsName')
        rec.Position(name, nw // 2, uir1.CellTop(nh, kit.font('text_b')))
        rec.Font(name, kit.font('text_b'), T.IVORY)
        self._Mirror(w.GetChild('SupportInt'), board, x + nw // 2, INT_Y, 'text_s', T.INK_DIM)

        self._BuildProgress()
        self._BuildModes()
        self._BuildSkills()
        self._BuildStrip()

    def _Mirror(self, line, parent, x, y, role, color):
        mirror = Mirror(self.rec, line, parent, x, y, self.kit.font(role), color)
        self.mirrors.append(mirror)
        self.widgets.append(mirror.text)
        return mirror

    def _Restyle(self, line, role, color, x, y, align=None, keep_color=False, original_color=0xFFFFFFFF):
        """An original progress text in Noto Sans without the outline, at its R1 place (its values keep coming from
        the window; keep_color: the window sets its colour itself)."""
        rec, font = self.rec, self.kit.font(role)
        rec.Position(line, x, y)
        if keep_color:
            def do():
                uir1.SetFont(line, font)

            def undo():
                text = line.GetText()
                line.SetText('')
                line.SetDefaultFontName()
                line.SetText(text)
            rec.Call(do, undo)
        else:
            rec.Font(line, font, color, None, original_color)
        rec.Call(lambda: line.SetOutline(False), lambda: line.SetOutline(True))
        if align == 'right':
            rec.Call(line.SetHorizontalAlignRight, line.SetHorizontalAlignCenter)

    def _BuildProgress(self):
        w, rec = self.window, self.rec
        x, y, pw, ph = PROGRESS
        panel = w.progressPanel
        rec.Position(panel, x, y)
        self._skin(panel, kind='panel')
        self.panel_w = pw
        right = pw - PROGRESS_PAD
        self._Restyle(w.progressLevelText, 'text_sb', T.IVORY, PROGRESS_PAD, 5, original_color=ORIGINAL_GOLD)
        self._Restyle(w.progressPassiveText, 'text_s', T.INK_DIM, right, 5, original_color=ORIGINAL_GOLD)
        exp_y = TRACK_Y + T.SLIDER_H // 2 - uir1.FontCell(self.kit.font('text_s')) // 2
        self._Restyle(w.progressExpText, 'text_s', T.INK, right, exp_y, align='right')
        self._Restyle(w.progressStatusText, 'text_s', None, pw // 2, STATUS_Y, keep_color=True)
        gauge = w.progressGauge
        rec.Hide(gauge)
        adapter = GaugeAdapter(gauge, self)

        def attach():
            w.progressGauge = adapter

        def detach():
            w.progressGauge = gauge
        rec.Call(attach, detach)
        self.track_w = 0
        self.track = self._new(uir1.Layer(panel, PROGRESS_PAD, TRACK_Y, 1, T.SLIDER_H, []))
        self.fill = self._new(uir1.Layer(panel, PROGRESS_PAD, TRACK_Y, 1, T.SLIDER_H, []))
        percentage = getattr(gauge, 'percentage', None)
        if percentage:
            self.SetExp(*percentage)

    def _BuildModes(self):
        w, rec = self.window, self.rec
        x, y, widths = SEGMENT
        buttons = list(w.expModeButtons)
        items = [(index, button.GetText(), button) for index, button in enumerate(buttons)]
        for button in buttons:
            rec.Hide(button)
        self.modes = self._new(uir1skin.ProxySegment(w.GetChild('board'), self.kit, x, y, items, widths,
                                                     font=self.kit.font('text_s')))
        self.lock = {'on': False}
        for cell in self.modes.cells:
            _LockHint(cell, self.kit, self.lock)

    def _BuildSkills(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.GetChild('board')
        x, y, sw, sh = SKILLS
        rec.Hide(w.GetChild('shaman_board'))
        panel = self._new(uir1.Frame(board, x, y, sw, sh, 'panel'))
        # Buffi_Skill_Icons is 'attach' (a drag on it moves the window through the attached board): the panel it
        # moves into passes the drag on the same way.
        panel.AddFlag('attach')
        heading = w.GetChild('Skill').GetText() if w.IsChild('Skill') else ''
        self._new(uir1.Section(panel, kit, PROGRESS_PAD, 6, sw - 2 * PROGRESS_PAD, heading or u'Dovednosti'))
        icons = w.GetChild('Buffi_Skill_Icons')
        rec.Parent(icons, panel, SKILL_ICONS[0], SKILL_ICONS[1], board)
        for index, sx in enumerate(SKILL_X):
            button = getattr(w, 'upgradeBtn_%d' % (index + 1))
            rec.Visuals(button, PLUS_R1, PLUS_ORIGINAL)
            rec.Position(button, sx + PLUS_OFFSET[0], PLUS_OFFSET[1])

    def _BuildStrip(self):
        w, rec = self.window, self.rec
        strip = w.equipSlot
        self._new(uir1.Frame(strip, 0, 0, strip.GetWidth(), strip.GetHeight(), 'window', bg=None))
        rec.Visuals(w.minimizeBtn, DRAWER['left'], MINIMIZE_ORIGINAL)
        self.drawer = 'left'
        # uibuff.SupportMainGui.OnMoveWindow places the strip and the button (the engine calls it on a move;
        # clickMinimize and Show call it too): the tab follows right after it. Held weakly (no reference cycle).
        window, skin = weakref.ref(w), weakref.ref(self)
        original = type(w).OnMoveWindow

        def moved(x, y):
            owner = window()
            if owner is None:
                return
            original(owner, x, y)
            current = skin()
            if current is not None:
                current.PlaceDrawer()

        def undo():
            owner = window()
            if owner is not None:
                owner.__dict__.pop('OnMoveWindow', None)
                original(owner, 0, 0)
        rec.Call(lambda: setattr(w, 'OnMoveWindow', moved), undo)
        self.PlaceDrawer()

    def PlaceDrawer(self):
        """The drawer tab on the left edge of the strip while it is out (chevron right: slide it back), else on the
        window's left edge (chevron left: slide it out); the same height in both."""
        w = self.window
        button, strip = getattr(w, 'minimizeBtn', None), getattr(w, 'equipSlot', None)
        if button is None or strip is None:
            return
        out = strip.IsShow()
        direction = 'right' if out else 'left'
        if direction != self.drawer:
            self.drawer = direction
            up, over, down = DRAWER[direction]
            button.SetUpVisual(up)
            button.SetOverVisual(over)
            button.SetDownVisual(down)
        wx, wy = w.GetGlobalPosition()
        edge = strip.GetGlobalPosition()[0] if out else wx
        button.SetPosition(edge - DRAWER_W + DRAWER_OVERLAP, wy + DRAWER_Y)

    # ------------------------------------------------------------------ state
    def SetExp(self, current, maximum):
        try:
            current, maximum = float(current), float(maximum)
        except (TypeError, ValueError):
            current, maximum = 0.0, 0.0
        self.fraction = max(0.0, min(1.0, current / maximum)) if maximum > 0 else 0.0
        self._Track()

    def _Track(self):
        """The track ends EXP_GAP before the EXP numbers (they are right aligned at the panel padding)."""
        line = self.window.progressExpText
        right = self.panel_w - PROGRESS_PAD
        width = max(TRACK_MIN, right - EXP_GAP - uir1.TextWidth(line) - PROGRESS_PAD)
        fill = int(round(self.fraction * width))
        if self._Changed('track', width):
            self.track.SetSize(width, T.SLIDER_H)
            self.track.Apply(L.slider_track(0, 0, width))
        if self._Changed('fill', (width, fill)):
            self.fill.SetSize(width, T.SLIDER_H)
            self.fill.Apply(L.slider_fill(0, 0, fill) if fill >= 2 else [])

    def _Changed(self, key, value):
        if self.shown.get(key, object()) == value:
            return False
        self.shown[key] = value
        return True

    def Sync(self):
        """After the window changed its values: the mirrored texts, the selected EXP mode and the EXP track."""
        for mirror in self.mirrors:
            mirror.Sync()
        mode = getattr(self.window, 'expMode', 1)
        self.modes.SetValue(mode)
        self._Modes(mode, not getattr(self.window, 'healingSkillsUnlocked', True))
        self._Track()

    def _Modes(self, mode, locked):
        """Locked (the player below level 90: the window sends no mode): the selected mode stays shown, the other
        two are disabled; the hover hint names the level."""
        self.lock['on'] = locked
        for cell, value in zip(self.modes.cells, self.modes.values):
            enabled = not locked or value == mode
            if enabled != cell.enabled:
                cell.Enable() if enabled else cell.Disable()
        if not locked:
            uir1.HideHint()

    def SyncSafe(self):
        """Sync() for the window's hooks: a failure is traced (syserr) and never breaks the window's own refresh."""
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure(u'Šamanská deska (stav)')

    # ------------------------------------------------------------------ teardown
    def Undo(self):
        for skin in reversed(self.skins):
            try:
                skin.Restore()
            except Exception:
                pass
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        for skin in self.skins:
            try:
                skin.Destroy()
            except Exception:
                pass
        self.widgets, self.mirrors, self.skins = [], [], []

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        for skin in self.skins:
            try:
                skin.Destroy()
            except Exception:
                pass
        self.widgets, self.mirrors, self.skins = [], [], []
        self.rec.undo = []
        self.window = None


def _LockHint(cell, kit, lock):
    """The hover hint of an EXP mode cell while the switch is locked (``lock['on']``)."""
    base_in, base_out = cell.OnMouseOverIn, cell.OnMouseOverOut

    def over_in():
        base_in()
        if lock['on']:
            uir1.ShowHint(kit, cell, LOCKED_HINT)

    def over_out():
        base_out()
        uir1.HideHint()
    cell.OnMouseOverIn = over_in
    cell.OnMouseOverOut = over_out


class Mirror(object):
    """An original text line (hidden) repeated by an R1 text whose font cell starts at ``y`` (top aligned)."""

    def __init__(self, rec, line, parent, x, y, font, color):
        self.line = line
        self.text = uir1.Text(parent, '', x, y, font, color, align='center', valign='top')
        rec.Hide(line)
        self.Sync()

    def Sync(self):
        value = self.line.GetText()
        if value != self.text.GetText():
            self.text.SetText(value)


def Build(window):
    """The R1 skin of ``window`` or None (the original look: "Starý vzhled", or the build failed - traced)."""
    if not UseR1():
        return None
    try:
        return BuffSkin(window)
    except Exception:
        Fail()
        return None
