# -*- coding: utf-8 -*-
"""Alchymie Dračích kamenů (uidragonsoul.DragonSoulWindow, 287 x 525) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the window built from locale/common/ui/dragonsoulwindow.py.

The original window is one background picture (dragon_soul_bg.tga: the board, the tab strip, the grade row, the
cell grid and the button plates in one image). R1 keeps the content art and replaces the chrome:

* the R1 frame and the header (the title in Cinzel, the vein, the plain X) instead of the board edges and the title
  bar; the background picture becomes the R1 panel background (tiled), the round alchemy board with its seven
  coloured slots is drawn unchanged on the R1 panel background inside a quiet panel outline
  (tools/build_althea_r1_alchymie.py), the 8 x 4 stone cells
  (part of the background picture, ItemSlot has no slot base image) are the R1 item slot C on their panel
  (uir1.SlotGrid: the 32 px cell at the engine pitch, exactly under the ItemSlot cells);
* the seven stone kinds as R1 tabs with the original gems (a click runs the original tab button: SetDSKindIndex);
  the kind name ("Dračí diamant") as an R1 section heading;
* the grade buttons stay the original radio buttons (their pages, positions per kind, tooltips) with R1 tab cell
  visuals and the original grade glyphs; 天 / 地 keep their art recoloured;
* "Zušlechťování" and "Aktivovat" as R1 buttons; "Aktivovat" shows the vein while the stones are active.

Every slot, event and handler of the window stays. Settings -> "Starý vzhled" (settingslook 'legacy') builds the
original window; a failure while building R1 is traced to syserr, undoes every change and keeps the original look.
"""
import ui

import uir1
import uir1skin
import uir1tokens as T

ART = 'd:/ymir work/ui/public/althea_r1_alchymie/dragonsoul/'
DS = 'd:/ymir work/ui/dragonsoul/'
PANEL_TILE = 'textures/panel.png'
BOARD_POS = (31, 40)                    # board.png lies where the board lies in dragon_soul_bg.tga
BOARD_PANEL = (9, 32, 269, 245)         # the outline around the board (the set glow DSSimg 12, 34 sits in it)
TABS = (10, 280, 38)                    # the seven kind tabs: x, y, cell width (7 x 38 = 266)
GEM_POS = (9, 3)                        # the 20 x 18 gem inside a 38 x 24 tab cell
KIND_SECTION = (12, 306, 263)
GRADE_Y = 329                           # the grade cells (24 px) between the kind name and the cell grid
GRID_POS = (15, 355)                    # the cells of ItemSlot (8 x 4 x 32 px from 15, 355)
GRID_CELLS = (8, 4)
GRID_PANEL = (13, 353, 260, 132)
FOOTER_PAD = 10                         # the 26 px footer buttons end 10 px above the bottom, 4 px under the grid
EDGE_GRIP = 8                           # the frame edges beside the stone slot window (it covers 0..UPPER_H)
UPPER_H = 280                           # EquipmentSlot: 287 x 280 from 0, 0 (uiscript), pickable, no 'attach'
DECK_STATES = ('normal', 'hover', 'pressed')


def _ButtonText(button, fallback):
    """The label of an original uiscript button (ui.Button.GetText exists only with some client flags)."""
    line = getattr(button, 'ButtonText', None)
    try:
        text = line.GetText() if line is not None else ''
    except Exception:
        text = ''
    return text or fallback


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


class DragonSkin(object):
    """R1 look of one DragonSoulWindow. A build failure undoes every change and re-raises (the window traces it)."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.gems = []
        self.shown = {}
        self.refine = self.activate = None
        try:
            self._Build()
            self.Sync()
        except Exception:
            self.Undo()
            raise

    def _opt(self, name):
        w = self.window
        return w.GetChild(name) if w.IsChild(name) else None

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    def _image(self, parent, path, x, y):
        image = ui.ExpandedImageBox()
        image.SetParent(parent)
        image.AddFlag('not_pick')
        image.LoadImage(path)
        image.SetPosition(int(x), int(y))
        image.Show()
        return self._new(image)

    # ------------------------------------------------------------------ build
    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.GetChild('board')
        self.W, self.H = w.GetWidth(), w.GetHeight()
        for name in ('Corners', 'Lines'):                       # a ui.Board's own edges (in game)
            for part in getattr(board, name, None) or ():
                rec.Hide(part)
        self._Background(w.GetChild('Equipment_Base'))
        for name in ('TitleBar', 'GradeTabBackground'):
            if self._opt(name) is not None:
                rec.Hide(w.GetChild(name))
        self._Decks()
        self._Grades()
        # Controls drawn above the content: the kind tabs, the kind name, the footer buttons, the header last.
        self._Kinds(board)
        x, y, sw = KIND_SECTION
        self.text = w.GetChild('tab_text_area')
        rec.Hide(self.text)
        self.section = self._new(uir1.Section(board, kit, x, y, sw, self.text.GetText(), color=T.INK))
        self._Footer(board)
        # The slot window of the seven stones covers the whole upper half: a mouse-down there never reached the
        # board ('attach'). Its left and right frame edges drag the window again (the header row has its own grip).
        for x in (0, self.W - EDGE_GRIP):
            self._new(uir1.Grip(board, x, T.HEAD_H, EDGE_GRIP, UPPER_H - T.HEAD_H))
        self._new(uir1.Grip(board, 0, T.HEAD_H, self.W, BOARD_PANEL[1] - 1 - T.HEAD_H))     # down to the board panel
        title = self._opt('TitleName')
        title = (title.GetText() if title is not None else '') or _Tr('Alchymie Dračích kamenů', 'Dragon Stone Alchemy')
        self.header = self._new(uir1.Header(board, kit, self.W, title, on_close=ui.__mem_func__(w.Close)))

    def _Background(self, base):
        """The background picture (the first child of the board, under every control) becomes the R1 panel tile; its
        children - created now, so they draw above it and under every later control - are the R1 frame, the board
        on its dark panel and the cell grid on its panel. All of them are pictures (not pickable): a drag on them
        still moves the window."""
        rec = self.rec
        original = getattr(base, 'name', None) or getattr(base, 'image_path', None) or DS + 'dragon_soul_bg.tga'
        ox, oy = base.GetLocalPosition()
        tile = uir1.ROOT + PANEL_TILE
        tw, th = T.SIZES[PANEL_TILE]

        def do():
            base.LoadImage(tile)                    # a new image instance: the tiling rect is set after it
            base.SetPosition(1, 1)
            base.SetRenderingRect(0.0, 0.0, float(self.W - 2) / tw - 1.0, float(self.H - 2) / th - 1.0)

        def undo():
            base.LoadImage(original)
            base.SetPosition(ox, oy)
        rec.Call(do, undo)
        self._new(uir1.Frame(base, -1, -1, self.W, self.H, 'window', bg=None))
        # Only the quiet outline around the round board: inside it the R1 panel background of the window (testers
        # 8. 10.: the dark well behind the wheel looked pure black next to the grey R1 panels).
        px, py, pw, ph = BOARD_PANEL
        self._new(uir1.Frame(base, px - 1, py - 1, pw, ph, 'panel', bg=None))
        self._image(base, ART + 'board.png', BOARD_POS[0] - 1, BOARD_POS[1] - 1)
        px, py, pw, ph = GRID_PANEL
        self._new(uir1.Frame(base, px - 1, py - 1, pw, ph, 'panel'))
        self.grid = self._new(uir1.SlotGrid(base, GRID_POS[0] - 1, GRID_POS[1] - 1, *GRID_CELLS))

    def _Decks(self):
        for deck in (1, 2):
            button = self._opt('deck%d' % deck)
            if button is not None:
                self.rec.Visuals(button, [ART + 'deck%d_%s.png' % (deck, s) for s in DECK_STATES],
                                 [DS + 'deck%d_%d.tga' % (deck, n) for n in (1, 2, 3)])

    def _Grades(self):
        """The grade buttons keep their events, pages and tooltips: R1 visuals and the row moved under the kind
        name (SetDSKindIndex places them from inventoryTabPositions, which therefore get the R1 row too)."""
        w, rec = self.window, self.rec
        buttons = list(getattr(w, 'inventoryTab', None) or ())
        for index, button in enumerate(buttons):
            n = index + 1
            rec.Visuals(button, [ART + 'grade_%d_%s.png' % (n, s) for s in ('normal', 'hover', 'selected')],
                        [DS + 'btn_soul_%02d_%d.tga' % (n, k) for k in (1, 2, 3)])
            x, unused = button.GetLocalPosition()
            rec.Position(button, x, GRADE_Y)
        positions = getattr(w, 'inventoryTabPositions', None)
        if positions:
            saved = list(positions)

            def do():
                positions[:] = [(x, GRADE_Y) for x, unused in saved]

            def undo():
                positions[:] = saved
            rec.Call(do, undo)

    def _Kinds(self, board):
        """The seven stone kinds as R1 tabs in front of the original (hidden) tab buttons."""
        w, rec, kit = self.window, self.rec, self.kit
        rec.Hide(w.GetChild('TabControl'))
        buttons = getattr(w, 'tabButtonDict', None) or {}
        keys = sorted(buttons)
        x, y, cw = TABS
        self.tabs = self._new(uir1skin.ProxySegment(board, kit, x, y, [(key, '', buttons[key]) for key in keys],
                                                    [cw] * len(keys)))
        self.gems = []
        for cell, key in zip(self.tabs.cells, keys):
            gem = ui.ExpandedImageBox()
            gem.SetParent(cell)
            gem.AddFlag('not_pick')
            gem.SetPosition(*GEM_POS)
            gem.Show()
            self.gems.append((key, gem))

    def _Footer(self, board):
        w, rec, kit = self.window, self.rec, self.kit
        # Full 26 px footer buttons with the 21 px label (the 22 px ones with the 17 px label were too small to read).
        y = self.H - FOOTER_PAD - T.BTN_H
        refine = self._opt('refine_open')
        if refine is not None:
            rec.Hide(refine)
            self.refine = self._new(uir1.Button(board, kit, FOOTER_PAD, y, T.BTN_W,
                                                _ButtonText(refine, _Tr('Zušlechťování', 'Refine')),
                                                event=lambda: refine.CallEvent()))
            self.refine.FitWidth(T.BTN_W)
        activate = self._opt('activate')
        if activate is not None:
            rec.Hide(activate)
            button = uir1.Button(board, kit, 0, y, T.BTN_W, _ButtonText(activate, _Tr('Aktivovat', 'Activate')),
                                 event=ui.__mem_func__(w.ActivateButtonClick))
            button.FitWidth(T.BTN_W)
            button.SetPosition(self.W - FOOTER_PAD - button.w, y)
            self.activate = self._new(button)

    # ------------------------------------------------------------------ state
    def Sync(self):
        """After the window changed the kind, the deck or the activation: the selected tab and its bright gem, the
        kind name, the activation vein."""
        w = self.window
        kind = getattr(w, 'DSKindIndex', 0)
        self.tabs.SetValue(kind)
        for key, gem in self.gems:
            path = ART + 'gem_%d_%s.png' % (key + 1, 'selected' if key == kind else 'normal')
            if self._Changed(('gem', key), path):
                gem.LoadImage(path)
        text = self.text.GetText()
        if self._Changed('kind', text):
            self.section.SetText(text)
        if self.activate is not None:
            self.activate.SetPrimary(bool(getattr(w, 'isActivated', False)))

    def _Changed(self, key, value):
        if self.shown.get(key, object()) == value:
            return False
        self.shown[key] = value
        return True

    def SyncSafe(self):
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure('the dragon stone alchemy window (state)')

    # ------------------------------------------------------------------ teardown
    def Undo(self):
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets, self.gems = [], []

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets, self.gems = [], []
        self.rec.undo = []
        self.window = None


# --------------------------------------------------------------------------- Okno zušlechťování
REFINE_GRIDS = (('RefineSlot', 15, 39, 5, 3), ('ResultSlot', 207, 39, 2, 3))
REFINE_ARROW = (181, 82)                # "»" between the two grids (two R1 chevrons, 7 px apart)
CONTENT_X, CONTENT_W = 15, 256         # the span of the two slot grids (15 .. 271): the rows below line up with it
REFINE_FIELD = (CONTENT_X, 174, CONTENT_W)                              # the yang field (R1 input well, 24 px)
ROW_GAP = 11                            # the same gap between the three tabs and between the two buttons (UI rules
                                        # 9. 10.: equal gaps in a row of buttons; the uiscript had 4 / 2 px)
YANG_ICON = 'd:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png'   # 16 x 16, the coin of the R1 refine dialog
REFINE_TABS = ('GradeButton', 'StepButton', 'StrengthButton')            # 78 x 21 toggle buttons
REFINE_TAB_TITLES = ('GradeSlotTitle', 'StepSlotTitle', 'RefineSlotTitle')
REFINE_BUTTONS = (('DoAllRefineButton', 'DoAllRefineButtonTitle'), ('DoRefineButton', 'DoRefineButtonTitle'))
TAB_TITLE_COLOR = 0xFFF1E6C0            # the uiscript colour of the tab titles
LOCKED_TINT = (0.42, 0.42, 0.42, 1.0)   # a closed refine slot: the R1 cell darkened over the open cell


def _Plate(family, state):
    return uir1.ROOT + 'plate/button_%s_%s.png' % (family, state)


def _SignedColor(color):
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


class RefineSkin(object):
    """Okno zušlechťování (uidragonsoul.DragonSoulRefineWindow, 287 x 232, locale/common/ui/
    dragonsoulrefinewindow.py) in the R1 look, drawn INTO the window like the alchemy window next to it:

    * the background picture (dragon_soul_refine_bg.tga: the board, the cell grids, the tab and button plates, the
      yang bar in one image) becomes the R1 panel tile; the R1 frame and the R1 header (title, vein, plain X) instead of
      the board edges and the title bar (its X closes the window the same way: Close);
    * the 5 x 3 refine cells and the 2 x 3 result cells are the R1 item slot C at the engine pitch, exactly under the
      slot windows; a closed refine slot (the slot base the window shows past refineSlotLockStartIndex, cap.tga) is
      the same cell darkened; "»" between the grids as R1 chevrons;
    * Stupeň / Stupeň čirosti / Úroveň keep their toggle buttons (events, Down / SetUp, Disable in the attribute
      change mode) with the R1 plates of their native 78 x 21 size: the chosen one is the pressed dark well and its
      label is bright, the others muted (UI rules 8. 10.: a selection is shown by brightness, never by a red
      underline); the three tabs and the two buttons line up with the grids with equal gaps;
    * the fee as the shared R1 price (root/uir1price.py: the coin, "10.000 Yang" in Tahoma 12, red when the player
      has less) right-aligned in an R1 well;
    * Automaticky / Zušlechtit keep their buttons with the R1 plates of their 88 x 21 size.

    Every slot, event and handler of the window stays. Settings -> "Starý vzhled" builds the original window; a
    failure while building R1 is traced to syserr, undoes every change and keeps the original look."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.header = None
        try:
            self._Build()
        except Exception:
            self.Undo()
            raise

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    def _opt(self, name):
        w = self.window
        return w.GetChild(name) if w.IsChild(name) else None

    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.GetChild('board')
        W, H = w.GetWidth(), w.GetHeight()
        for name in ('Corners', 'Lines'):
            for part in getattr(board, name, None) or ():
                rec.Hide(part)
        base = w.GetChild('DragonSoulRefineWindowBaseImage')
        original = getattr(base, 'name', None) or getattr(base, 'image_path', None) or DS + 'dragon_soul_refine_bg.tga'
        ox, oy = base.GetLocalPosition()
        tile = uir1.ROOT + PANEL_TILE
        tw, th = T.SIZES[PANEL_TILE]

        def do():
            base.LoadImage(tile)                    # a new image instance: the tiling rect is set after it
            base.SetPosition(1, 1)
            base.SetRenderingRect(0.0, 0.0, float(W - 2) / tw - 1.0, float(H - 2) / th - 1.0)

        def undo():
            base.LoadImage(original)
            base.SetPosition(ox, oy)
            base.SetRenderingRect(0.0, 0.0, 0.0, 0.0)
        rec.Call(do, undo)
        # Children of the background picture (the first child of the board): under every slot and button.
        self._new(uir1.Frame(base, -1, -1, W, H, 'window', bg=None))
        self.grids = []
        for name, x, y, cols, rows in REFINE_GRIDS:
            self.grids.append(self._new(uir1.SlotGrid(base, x - 1, y - 1, cols, rows)))
        ax, ay = REFINE_ARROW
        for dx in (0, 7):
            self._new(uir1.Image(base, uir1.ChevronPath('right', 'normal'), ax + dx - 1, ay - 1))
        fx, fy, fw = REFINE_FIELD
        # the fee: the shared R1 price (root/uir1price.py) right-aligned in the R1 well
        import uir1price
        self.field = self._new(uir1price.PriceField(base, fx - 1, fy - 1, fw))
        self.price = self.field.price
        self.coin = self.price.icon
        refine = w.GetChild('RefineSlot')
        rec.Call(lambda: refine.SetSlotBaseImage(uir1.SLOT_CELL, *LOCKED_TINT),
                 lambda: refine.SetSlotBaseImage(DS + 'cap.tga', 1.0, 1.0, 1.0, 1.0))
        ink = _SignedColor(T.BUTTON_TEXT)
        self.titles = []
        for index, (name, title) in enumerate(zip(REFINE_TABS, REFINE_TAB_TITLES)):
            button = self._opt(name)
            if button is None:
                continue
            rec.Visuals(button, [_Plate('78x21', s) for s in ('normal', 'hover', 'pressed', 'disabled')],
                        [DS + 'button_0%d.tga' % n for n in (1, 2, 3)] + [None])
            rec.Position(button, CONTENT_X + index * (78 + ROW_GAP), button.GetLocalPosition()[1])
            line = self._opt(title)
            if line is not None:
                self.titles.append(line)
                rec.Call(lambda: None,
                         lambda line=line: line.SetPackedFontColor(_SignedColor(TAB_TITLE_COLOR)))
        self.chosen = None
        right = CONTENT_X + CONTENT_W
        for index, (name, title) in enumerate(REFINE_BUTTONS):
            button = self._opt(name)
            if button is None:
                continue
            rec.Visuals(button, [_Plate('88x21', s) for s in ('normal', 'hover', 'pressed', 'disabled')],
                        [DS + 'l_button0%d.tga' % n for n in (1, 2, 3)] + [None])
            # Automaticky, Zušlechtit: right-aligned with the grids, the same gap as the tabs
            x = right - (len(REFINE_BUTTONS) - index) * 88 - (len(REFINE_BUTTONS) - 1 - index) * ROW_GAP
            rec.Position(button, x, button.GetLocalPosition()[1])
            line = self._opt(title)
            if line is not None:
                rec.Call(lambda line=line: line.SetPackedFontColor(ink),
                         lambda line=line: line.SetPackedFontColor(_SignedColor(0xFFFFFFFF)))
        # Money_Slot stays the window's text line (uidragonsoul sets the fee into it): hidden, every SetText shows
        # the fee in the R1 price ("10.000 Yang" in Tahoma 12, red when the player has less)
        money = w.GetChild('Money_Slot')
        rec.Hide(money)
        self._MirrorFee(money)
        bar = self._opt('TitleBar')
        title = self._opt('TitleName')
        title = (title.GetText() if title is not None else '') or _Tr(u'Okno zušlechťování', 'Refine')
        if bar is not None:
            rec.Hide(bar)
        self.header = self._new(uir1.Header(board, kit, W, title, on_close=ui.__mem_func__(w.Close)))
        self.Sync()

    def _MirrorFee(self, money):
        """money.SetText (an instance wrapper, weak both ways: a ui.Window cycle would never be freed) also shows the
        fee in the R1 price; Undo removes the wrapper."""
        import weakref
        target, me = weakref.ref(money), weakref.ref(self)
        own = money.__dict__.get('SetText')
        method = money.__class__.SetText

        def SetText(*args):
            line = target()
            if line is None:
                return None
            result = own(*args) if own is not None else method(line, *args)
            skin = me()
            if skin is not None:
                skin.ShowFee(line.GetText())
            return result

        def undo():
            line = target()
            if line is None:
                return
            if own is not None:
                line.SetText = own
            elif 'SetText' in line.__dict__:
                del line.SetText
        self.rec.Call(lambda: setattr(money, 'SetText', SetText), undo)
        self.ShowFee(money.GetText())

    def ShowFee(self, text):
        """The fee the window wrote (localeInfo.NumberToMoneyString: "10.000") in the R1 price."""
        try:
            import uir1price
            digits = ''.join(ch for ch in (text or '') if ch in '0123456789')
            amount = int(digits) if digits else 0
            self.price.SetPrice(amount, uir1price.CanAfford(amount))
        except Exception:
            uir1.TraceFailure('the dragon stone refine window (fee)')

    def Sync(self):
        """After the window refreshed: the label of the chosen refine type bright, the others muted (the attribute
        change mode keeps the third button down)."""
        w = self.window
        chosen = getattr(w, 'currentRefineType', 0)
        chosen = chosen if chosen in (0, 1, 2) else 2
        if chosen == self.chosen:
            return
        self.chosen = chosen
        for index, line in enumerate(self.titles):
            line.SetPackedFontColor(_SignedColor(T.IVORY if index == chosen else T.INK_DIM))

    def SyncSafe(self):
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure('the dragon stone refine window (state)')

    def Undo(self):
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets = []

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets = []
        self.rec.undo = []
        self.window = None
