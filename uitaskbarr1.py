# -*- coding: utf-8 -*-
"""The bottom bar (uitaskbar.TaskBar) in the R1 look: variant A2 (owner 8. 10. 2026, design kolo-20261007-lista/A2).

Today's layout restyled into R1 like the minimap A2 (tools/build_althea_r1_lista.py, ``althea_r1_lista/``):

* the bottom-left corner stays today's: the round orb with the Althea logo (its idle, hover, heartbeat and
  flourish animations, the Item Shop click), the holder with today's HP / SP / stamina bars and the 4 round EXP
  balls; only the bronze edges of the orb ring, the holder and the EXP board become the R1 graphite, the red stays;
* the strip and the quick slot / menu panels are R1 graphite; the quick slots are the R1 slot C;
* the mouse mode buttons, Anti-EXP, the page switch and Postava / Inventář / Přátelé / Systém are rounded squares in
  the colours and ring treatment of the minimap A2 (graphite outer ring, deep dark red inner ring, ivory glyph); an
  open window lights the inner ring. The mode pop-ups above the two mouse buttons (MouseButtonWindow /
  RightMouseButtonWindow) get the same squares, so the mode picked there looks the same on the bar. "Zvýšit status / Zvýšit schopnost" (uigamebutton) become the same squares with
  a red point count.

Every control keeps its window, place, hit box, event and tooltip (the quick slots with drag and drop, cool-downs and
hotkeys, the mouse mode pop-ups, the gauges and their tooltips): the dress only reloads the art of the loaded uiscript
(TaskBar_Dominant_Orb.py). Settings -> "Starý vzhled" keeps today's bar. A failure while dressing or while updating is
traced (uir1.TraceFailure), today's art comes back (``Restore``) and R1 is not tried again in this session.
"""
import ui

import uir1
import uir1tokens as T
import uir1listaart as A

_failed = [False]
_failedButtons = [False]

# The original art of the children the dress reloads (patch_fw/uiscript/taskbar_dominant_orb.py), for Restore.
GAME = 'd:/ymir work/ui/game/'
ORB = GAME + 'crimson_ember/taskbar/dominant_orb/v2/'
ORIGINAL = {
    'Base_Board_01': 'd:/ymir work/ui/pattern/TaskBar_Base.tga',
    'QuickslotPanel': GAME + 'taskbar/crimson/taskbar_quickslot_panel.tga',
    'UtilityPanel': GAME + 'taskbar/crimson/taskbar_utility_panel.tga',
    'OrbBase': ORB + 'orb_base.tga',
    'ResourceCarrier': ORB + 'resource_carrier.tga',
    'EXP_Gauge_Board': GAME + 'taskbar/crimson/taskbar_exp_gauge.tga',
    'QuickSlotNumberBox': GAME + 'taskbar/crimson/quickslot_number_board.tga',
}
# the R1 art of the left corner: today's textures at their places, bronze -> graphite
LEFT_CORNER = (('OrbBase', 'orb/orb_base.png'), ('ResourceCarrier', 'orb/resource_carrier.png'),
               ('EXP_Gauge_Board', 'orb/exp_gauge.png'))
SLOT_BASE = 'd:/ymir work/ui/Public/Slot_Base.sub'
SKILL_SLOT_BASE = 'd:/ymir work/ui/public/slot_base.sub'
MENU = (('CharacterButton', 'character'), ('InventoryButton', 'inventory'), ('MessengerButton', 'messenger'),
        ('SystemButton', 'system'))
# interface window of every menu button (the open window lights its ring)
OPEN_WINDOWS = {'CharacterButton': 'wndCharacter', 'InventoryButton': 'wndInventory',
                'MessengerButton': 'wndMessenger', 'SystemButton': 'dlgSystem'}
PAGE_BUTTONS = (('QuickPageUpButton', 'up'), ('QuickPageDownButton', 'down'))
# the buttons of the mouse mode pop-ups (uiscript/mousebuttonwindow.py, rightmousebuttonwindow.py)
MODE_BUTTONS = ('button_move_and_attack', 'button_auto_attack', 'button_camera', 'button_metin_queue',
                'button_skill', 'button_attack', 'button_move')
STATES = ('normal', 'hover', 'pressed')
VISUAL_SETTERS = (('SetUpVisual', 'GetUpVisualFileName', 'normal'),
                  ('SetOverVisual', 'GetOverVisualFileName', 'hover'),
                  ('SetDownVisual', 'GetDownVisualFileName', 'pressed'))
OPEN_INTERVAL = 0.2


def UseR1():
    return uir1.UseR1() and not _failed[0]


def Signed(color):
    """wndMgr.SetFontColor parses a C int and silently ignores packed colours >= 0x80000000 on x64."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color >= 0x80000000 else color


def Art(name):
    return A.ROOT + name


def _Stem(path):
    name = (path or '').replace('\\', '/').rsplit('/', 1)[-1].lower()
    return name.rsplit('.', 1)[0]


MOUSE = {'mouse_button_attack': 'mouse_attack', 'mouse_button_auto_attack': 'mouse_auto_attack',
         'mouse_button_camera': 'mouse_camera', 'mouse_button_move': 'mouse_move',
         'mouse_button_move_and_attack': 'mouse_move_and_attack', 'mouse_button_skill': 'mouse_skill',
         'taskbar_mouse_button_move': 'mouse_move', 'metin_queue_mouse': 'mouse_metin_queue'}


def MouseVisual(path, state):
    """The R1 art of a mouse mode visual (what SelectMouseButtonEvent copies from the mode pop-up), else None."""
    base, unused, suffix = _Stem(path).rpartition('_')
    name = MOUSE.get(base)
    if name is None or suffix not in ('01', '02', '03'):
        return None
    return Art('button/%s_%s.png' % (name, STATES[int(suffix) - 1]))


def AntiExpVisual(path, state):
    """antiexp_button_01-03 (switched on, game.SetAntiExp) / 04-06 (off) -> the R1 square, else None."""
    base, unused, suffix = _Stem(path).rpartition('_')
    if base != 'antiexp_button' or suffix not in ('01', '02', '03', '04', '05', '06'):
        return None
    index = int(suffix) - 1
    return Art('button/antiexp_%s_%s.png' % ('on' if index < 3 else 'off', STATES[index % 3]))


def StaticVisual(name):
    return lambda path, state: Art('button/%s_%s.png' % (name, state))


def PageVisual(direction):
    return lambda path, state: Art('page/%s_%s.png' % (direction, state))


def _Image(parent, path, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(Art(path))
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


class Dress(object):
    """The R1 art on a loaded uitaskbar.TaskBar (``Apply``) and back (``Restore``)."""

    def __init__(self, taskbar):
        self.taskbar = taskbar
        self.undo = []
        self.made = []
        self.openRings = {}
        self.nextOpen = 0.0
        self.originals = {}         # R1 art -> the original visual it replaced (a mode copied from a pop-up)

    # ---------------------------------------------------------------------- recorded changes
    def Child(self, name):
        bar = self.taskbar
        return bar.GetChild(name) if bar.IsChild(name) else None

    def _Load(self, name, art, at=None, rect=None):
        """Reloads one image of the layout with R1 art (at its place unless ``at``; a tiled image gets its tiling
        rect again - LoadImage makes a new image instance)."""
        widget = self.Child(name)
        ox, oy = widget.GetLocalPosition()
        widget.LoadImage(Art(art))
        if rect is not None:
            widget.SetRenderingRect(*rect)
        if at is not None:
            widget.SetPosition(int(at[0]), int(at[1]))

        def undo():
            widget.LoadImage(ORIGINAL[name])
            if rect is not None:
                widget.SetRenderingRect(*rect)
            widget.SetPosition(ox, oy)
        self.undo.append(undo)
        return widget

    def _Wrap(self, button, mapper):
        """Every visual set on the button (now and later: the mouse mode, game.SetAntiExp) goes through ``mapper``;
        the original names are kept for Restore."""
        sources = button.__dict__.setdefault('r1Sources', {})
        originals = self.originals
        for setter, getter, state in VISUAL_SETTERS:
            original = getattr(button, setter)

            def visual(path, original=original, state=state):
                # SelectMouseButtonEvent copies the (R1) visual of a dressed pop-up button: its original name is kept
                path = originals.get(path, path)
                sources[state] = path
                art = mapper(path, state)
                if art:
                    originals[art] = path
                original(art or path)
            sources[state] = getattr(button, getter)()
            setattr(button, setter, visual)
            visual(sources[state])

        def undo():
            for setter, unused, state in VISUAL_SETTERS:
                button.__dict__.pop(setter, None)
                getattr(button, setter)(sources[state])
            button.__dict__.pop('r1Sources', None)
        self.undo.append(undo)

    def _Make(self, widget):
        self.made.append(widget)
        return widget

    # ---------------------------------------------------------------------- build
    def Apply(self):
        bar = self.taskbar
        width = bar.GetWidth()
        tile_w = A.STRIP[0]
        # the strip (a tile repeated over the width, like today's TaskBar_Base.tga) and the two panels
        self._Load('Base_Board_01', 'strip.png', rect=(0.0, 0.0, float(width - tile_w) / tile_w, 0.0))
        board_x, board_y = self.Child('quickslot_board').GetLocalPosition()
        self._Load('QuickslotPanel', 'panel/quickslot.png',
                   (board_x + A.QUICKSLOT_PANEL_AT[0], board_y + A.QUICKSLOT_PANEL_AT[1]))
        self._Load('UtilityPanel', 'panel/utility.png')
        # the left corner: today's orb ring, holder and EXP board in R1 graphite (logo, bars, EXP balls unchanged)
        for name, art in LEFT_CORNER:
            self._Load(name, art)
        anti = self.Child('AntiExp')
        if anti is not None:
            self._Wrap(anti, AntiExpVisual)
        # the middle: the original controls at their places
        for window in getattr(bar, 'mouseModeButtonList', None) or ():
            for name in MODE_BUTTONS:
                if window.IsChild(name):
                    self._Wrap(window.GetChild(name), MouseVisual)
        self._Wrap(self.Child('LeftMouseButton'), MouseVisual)
        self._Wrap(self.Child('RightMouseButton'), MouseVisual)
        for name in ('quick_slot_1', 'quick_slot_2'):
            slot = self.Child(name)
            slot.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
            self.undo.append(lambda slot=slot: slot.SetSlotBaseImage(SLOT_BASE, 1.0, 1.0, 1.0, 1.0))
        skill = getattr(bar, 'curSkillButton', None)
        if skill is not None:
            skill.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
            self.undo.append(lambda: skill.SetSlotBaseImage(SKILL_SLOT_BASE, 1.0, 1.0, 1.0, 1.0))
        self._Load('QuickSlotNumberBox', 'page/plate.png', (-1, 3))
        for name, direction in PAGE_BUTTONS:
            self._Wrap(self.Child(name), PageVisual(direction))
        number = self.Child('QuickPageNumber')
        if number is not None:
            self.undo.append(lambda: number.LoadImage(self.taskbar.QUICKPAGE_NUMBER_FILENAME[0]))
        # the menu
        for name, glyph in MENU:
            button = self.Child(name)
            self._Wrap(button, StaticVisual(glyph))
            ring = self._Make(_Image(button, 'button/open.png', 0, 0))
            ring.Hide()
            self.openRings[name] = ring
        return self

    # ---------------------------------------------------------------------- updates (TaskBar calls these)
    def PagePath(self, page):
        return Art('page/%d.png' % (max(0, min(3, int(page))) + 1))

    def SetOpen(self, opened):
        """{child name: open?} -> the brighter inner ring of the open windows."""
        for name, ring in self.openRings.items():
            (ring.Show if opened.get(name) else ring.Hide)()

    def Update(self, now=None, interface=None):
        if now is None:
            import app
            now = app.GetTime()
        if now < self.nextOpen:
            return
        self.nextOpen = now + OPEN_INTERVAL
        if interface is None:
            try:
                import osfInfo
                interface = osfInfo.GetInterfaceInstance()
            except Exception:
                interface = None
        opened = {}
        for name, attribute in OPEN_WINDOWS.items():
            window = getattr(interface, attribute, None) if interface is not None else None
            try:
                opened[name] = bool(window and window.IsShow())
            except Exception:
                opened[name] = False
        self.SetOpen(opened)

    def Call(self, method, *args):
        """Runs an update; a failure is traced, today's bar comes back and R1 is not tried again."""
        try:
            getattr(self, method)(*args)
            return True
        except Exception:
            Fail(self, 'Spodní lišta (%s)' % method)
            return False

    # ---------------------------------------------------------------------- back to today's bar
    def Restore(self):
        for widget in self.made:
            try:
                widget.Hide()
            except Exception:
                pass
        self.made = []
        for ring in self.openRings.values():
            ring.Hide()
        self.openRings = {}
        undo, self.undo = self.undo, []
        for step in reversed(undo):
            try:
                step()
            except Exception:
                pass
        bar = self.taskbar
        if bar is not None and getattr(bar, 'r1Dress', None) is self:
            bar.r1Dress = None


def Fail(dress, what):
    _failed[0] = True
    uir1.TraceFailure(what)
    try:
        dress.Restore()
    except Exception:
        pass


def Create(taskbar):
    """The applied dress, or None (Starý vzhled, or a failure: traced, today's art back, not retried)."""
    if not UseR1():
        return None
    dress = Dress(taskbar)
    try:
        return dress.Apply()
    except Exception:
        Fail(dress, 'Spodní lišta')
        return None


# =========================================================================== Zvýšit status / Zvýšit schopnost
RAISE = (('STATUS', 'StatusPlusLabel'), ('SKILL', 'SkillPlusLabel'))
RAISE_ORIGINAL = {'normal': 'd:/ymir work/ui/game/windows/btn_bigplus_up.sub',
                  'hover': 'd:/ymir work/ui/game/windows/btn_bigplus_over.sub',
                  'pressed': 'd:/ymir work/ui/game/windows/btn_bigplus_down.sub'}
RAISE_LABEL_Y = 33          # under the square (today 28: under the old 26 px plus)
# The point count pill sits on the square's top right corner (owner 8. 10., DEV 60: the old 15 px pill with the 14 px
# text covered the plus and the plate): its left edge 6 px inside the square's right edge (texture x 30), its middle
# row on the square's top edge (texture y 1), growing to the right with more digits; the plus (11 px, centred) and
# the label stay clear. The digits are 5 x 7 textures (badge/digit_<n>.png), no font.
BADGE_AT = (24, -5)
MAX_DIGITS = 3
# Zvýšit schopnost sits 50 px from the RIGHT edge of the screen (patch_fw/uiscript/gamewindow_dominant_orb.py:
# x = SCREEN_WIDTH - 50 - 32, made for the short English "Raise Skills"), while its label and badge hang to the right of
# the 32 px square: the 92 px Czech label ends 30 px and the 3 digit pill 17 px beyond it. Owner 8. 10. (Lokal): the
# badge "8" and the label ("Zvýšit scho") end with a straight edge at the square's right edge, SCREEN_WIDTH - 50;
# Zvýšit status, 68 px from the LEFT edge, shows everything. These windows set no inside render, clip mask or scissor,
# so what ends the drawing there is outside this code; the dress keeps the whole group (square, label, widest pill)
# RAISE_EDGE px from the screen edge instead, like the left one (its label starts 51 px from it): the square moves
# left to make room.
RAISE_EDGE = 64


class GameButtons(object):
    """The plus buttons of uigamebutton.GameButtonWindow as C squares with a red point count."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.undo = []
        self.badges = {}

    def Apply(self):
        buttons = self.window.gameButtonDict
        for key, label_name in RAISE:
            button = buttons[key]
            for setter, unused, state in VISUAL_SETTERS:
                getattr(button, setter)(Art('button/plus_%s.png' % state))
            self.undo.append(lambda button=button: [getattr(button, setter)(RAISE_ORIGINAL[state])
                                                    for setter, unused, state in VISUAL_SETTERS])
            label = self.window.GetChild(label_name)
            ox, oy = label.GetLocalPosition()
            uir1.SetFont(label, self.kit.font('text_s'))
            label.SetPackedFontColor(Signed(T.INK))
            label.SetOutline()
            label.SetPosition(ox, RAISE_LABEL_Y)
            self.undo.append(lambda label=label, ox=ox, oy=oy: self._RestoreLabel(label, ox, oy))
            pill = _Image(button, 'badge/count_1.png', BADGE_AT[0], BADGE_AT[1])
            digits = [_Image(pill, 'badge/digit_0.png', A.BADGE_DIGIT_AT[0] + i * (A.DIGIT[0] + 1),
                             A.BADGE_DIGIT_AT[1]) for i in range(MAX_DIGITS)]
            pill.Hide()
            self.badges[key] = (button, pill, digits)
            self._KeepClearOfTheEdge(button, label, ox)
        return self

    def _KeepClearOfTheEdge(self, button, label, labelX):
        """Moves a square near the right edge left until its label and the widest pill end RAISE_EDGE px from the edge
        (also after a live window resize: the square's resize position is the same distance from the right edge)."""
        width = self.window.GetWidth()
        x, y = button.GetLocalPosition()
        right = max(button.GetWidth(), BADGE_AT[0] + A.BADGE_W[str(MAX_DIGITS)],
                    labelX + (uir1.TextWidth(label) + 1) // 2)
        fitted = width - RAISE_EDGE - right
        if width <= 0 or x <= fitted:
            return
        button.SetPosition(fitted, y)
        self.undo.append(lambda: button.SetPosition(x, y))
        expr, setter = getattr(ui, 'Expr', None), getattr(button, 'SetResizeDic', None)
        if expr is not None and setter is not None:
            # ui.Window.OnResize puts the square back to the script position (SCREEN_WIDTH - 82, no gem raise): keep it
            # where it is now, measured from the right and bottom edge
            old = dict(getattr(button, 'resizeDic', None) or {})
            setter({'position': (expr('SCREEN_WIDTH') - (width - fitted),
                                 expr('SCREEN_HEIGHT') - (self.window.GetHeight() - y))})
            self.undo.append(lambda: setter({'position': old['position']}) if 'position' in old else None)

    @staticmethod
    def _RestoreLabel(label, x, y):
        try:
            import localeInfo
            font = localeInfo.UI_DEF_FONT
        except Exception:
            font = 'Tahoma:12'
        uir1.SetFont(label, font)
        label.SetPackedFontColor(Signed(0xFFFFFFFF))
        label.SetPosition(x, y)

    def SetCounts(self, status, skill):
        for key, value in (('STATUS', status), ('SKILL', skill)):
            button, pill, digits = self.badges[key]
            value = max(0, int(value))
            if value <= 0:
                pill.Hide()
                continue
            label = '%d' % min(value, 10 ** MAX_DIGITS - 1)
            pill.LoadImage(Art('badge/count_%d.png' % len(label)))
            pill.SetPosition(BADGE_AT[0], BADGE_AT[1])
            for index, image in enumerate(digits):
                if index < len(label):
                    image.LoadImage(Art('badge/digit_%s.png' % label[index]))
                    image.Show()
                else:
                    image.Hide()
            pill.Show()

    def Call(self, method, *args):
        try:
            getattr(self, method)(*args)
            return True
        except Exception:
            _failedButtons[0] = True
            uir1.TraceFailure('Zvýšit status / schopnost (%s)' % method)
            self.Restore()
            return False

    def Restore(self):
        for button, pill, digits in self.badges.values():
            pill.Hide()
        self.badges = {}
        undo, self.undo = self.undo, []
        for step in reversed(undo):
            try:
                step()
            except Exception:
                pass
        if getattr(self.window, 'r1Dress', None) is self:
            self.window.r1Dress = None


def CreateGameButtons(window):
    if not uir1.UseR1() or _failedButtons[0]:
        return None
    dress = GameButtons(window)
    try:
        return dress.Apply()
    except Exception:
        _failedButtons[0] = True
        uir1.TraceFailure('Zvýšit status / schopnost')
        dress.Restore()
        return None
