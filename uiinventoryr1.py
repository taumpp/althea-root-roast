# -*- coding: utf-8 -*-
"""The inventory and its shortcut rail in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md).

uiinventory.InventoryWindow keeps the window (rail + 176 x 585 body, the uiscript locale/common/ui/inventorywindow.py),
every slot, grid, tab, button, the search bar, the money slot and all their events; InventorySkin re-skins it for R1
unless Settings -> "Starý vzhled" chose the original look (uir1.UseR1()). A build failure undoes every change (traced
to syserr) and the original look stays. The team decision of 2026-10-06 for this window:

* the equipment board with its outlines (sword, shield, body silhouette), the costume board and the rail keep their
  art and shapes; only the frames are recoloured from bronze / crimson to the R1 graphite and dark blood red
  (tools/build_althea_r1_postava.py, ART). Item art, the rail function icons ("big icons", 24 px on the 37 px
  carrier), the yang and the search glyphs stay as they are;
* the item grid and the search results grid use the R1 item slot C (team choice 2026-10-07, uir1.SLOT_CELL: every
  32 px cell lightly rounded with the graphite outline, the gap at the joints) as their slot base image; the octagon
  underlay of the grid is hidden (the cells draw everything, the window background shows in the joints). The engine
  grid (5 x 9 cells of 32 px at 8, 266) is unchanged, so the items stay where they were. The equipment and costume
  boards keep their art: their slot outlines, the silhouette and the slot hints are one picture (a C cell over it
  would hide the hints or leave the old outline around it);
* (owner 11. 10. 2026, round 4b): the equipment and costume boards keep EVERY slot where the uiscript has
  it; only their look changes - the R1 panel lit from above with the R1 item slot C at each slot (a tall slot = cells
  stacked), no figure; an EMPTY slot shows the quiet outline of its type (hint_<eq|co>_<slot>.png, hidden under an
  item); a costume eye only on a worn costume (or while the costume is hidden, so it can be shown again), a hidden
  costume's eye in the R1 red (visibility_hidden.png). The empty slot's tooltip is only its name (uitooltip);
* the R1 frame and header: the title in Cinzel right of the header buttons, the vein under it, the plain X;
* the magnifier, the potion and "+" in the header on the header axis (the same buttons, recoloured);
* the selected Výbava / Kostýmy tab and the selected page I - IV get the red vein under their text (no red plate);
* the open search keeps the magnifier pressed; the search line sits in an R1 field (the vein while typing); the
  results grid uses the C cells too. Functions unchanged.

The rail (uitaskbar.ExpandedTaskBar) follows the inventory: SetR1Look(True) swaps its art directory to RAIL_ART.
"""
import ui

import uir1
import uir1skin
import uir1tokens as T

ORIGINAL = 'd:/ymir work/ui/game/crimson_ember/inventory/'
ART = 'd:/ymir work/ui/public/althea_r1_postava/inventory/'
RAIL_ART = ART                 # the rail frames (rail_*.png) are recoloured into the same directory
STATES = ('normal', 'hover', 'pressed', 'disabled')
PLUS_ORIGINAL = ('d:/ymir work/ui/game/windows/btn_plus_up.sub', 'd:/ymir work/ui/game/windows/btn_plus_over.sub',
                 'd:/ymir work/ui/game/windows/btn_plus_down.sub')
PLUS_R1 = (ART + 'plus_01.png', ART + 'plus_02.png', ART + 'plus_03.png')
RETIRED_COVER = 'd:/ymir work/ui/game/crimson_ember/inventory/retired_arrow_slot_cover.sub'

BODY_W, BODY_H = 176, 585
TITLE_LEFT = 77                # header buttons left of the title: magnifier 5, potion 31, "+" 61 (13 px)
HEADER_BUTTONS = (             # (child, x, y): the three buttons centred on the header axis (HEAD_H 27)
    ('SortInventoryButton', 5, 4),
    ('QuickBuffButton', 31, 4),
    ('QuickBuffSettingsButton', 61, 7),
)
IMAGES = (                     # uiscript image -> the recoloured copy of the same file
    ('Equipment_Base', 'panel_equipment.png'),
    ('EquipmentSlotCompletionOverlay', 'equipment_slot_completion.png'),
    ('Costume_Base', 'panel_costume.png'),
    ('ModeRowFrame', 'mode_frame.png'),
    ('PageRowFrame', 'page_frame.png'),
    ('CurrencyFooter', 'currency_footer.png'),
)
GRID_UNDERLAY = 'ItemGridSlotUnderlay'   # the octagon cells under the item grid: hidden in R1 (the C cells draw them)
COMPLETION = 'EquipmentSlotCompletionOverlay'   # the old cell outlines over the board: the R1 board draws its cells
# the slots of the boards (inventorywindow.py: slot coordinates in EquipmentSlot / CostumeSlot) with the
# slot number they show - the type outline of an empty slot is drawn there. The arrow cell (+9) is retired.
EQUIPMENT_SLOT_ORIGIN = (2, 1)
COSTUME_SLOT_ORIGIN = (3 + 4, 3)
EQUIPMENT_HINTS = (    # (hint, slot number source, x, y, height)
    ('armor', ('start', 0), 39, 37, 64), ('head', ('start', 1), 39, 2, 32), ('shoes', ('start', 2), 39, 145, 32),
    ('wrist', ('start', 3), 75, 67, 32), ('weapon', ('start', 4), 3, 3, 96), ('neck', ('start', 5), 114, 67, 32),
    ('ear', ('start', 6), 114, 35, 32), ('unique1', ('start', 7), 2, 145, 32), ('unique2', ('start', 8), 75, 145, 32),
    ('shield', ('start', 10), 75, 35, 32), ('unique3', ('start', 11), 114, 106, 32),
    ('unique4', ('start', 12), 114, 145, 32), ('ring', ('item', 'EQUIPMENT_RING1'), 2, 106, 32),
    ('belt', ('item', 'EQUIPMENT_BELT'), 39, 106, 32), ('glove', ('item', 'EQUIPMENT_GLOVE'), 75, 106, 32),
    ('sash', ('costume', 3), 74, 3, 32),
)
COSTUME_HINTS = (
    ('body', ('costume', 0), 55, 72, 64), ('hair', ('costume', 1), 57, 29, 32), ('mount', ('costume', 37), 106, 92, 32),
    ('sash_skin', ('item', 'ACCE_SKIN_SLOT'), 106, 8, 32), ('weapon', ('item', 'COSTUME_SLOT_WEAPON'), 10, 15, 96),
    ('aura', ('item', 'COSTUME_SLOT_AURA'), 106, 50, 32),
    ('glow_weapon', ('item', 'COSTUME_TYPE_SLOT_EFFECT_WEAPON'), 18, 144, 32),
    ('glow_armor', ('item', 'COSTUME_TYPE_SLOT_EFFECT_ARMOR'), 97, 144, 32),
    ('pet', ('item', 'COSTUME_SLOT_PET'), 59, 147, 32),
)
# the costume eyes (uiscript children) -> the slot they hide and the osfInfo flag of the hidden state
EYES = (
    ('BodyToolTipButton', ('costume', 0), 'HIDDEN_BODY_COSTUME'),
    ('HairToolTipButton', ('costume', 1), 'HIDDEN_HAIR_COSTUME'),
    ('WeaponToolTipButton', ('item', 'COSTUME_SLOT_WEAPON'), 'HIDDEN_WEAPON_COSTUME'),
    ('AcceSkinToolTipButton', ('item', 'ACCE_SKIN_SLOT'), 'HIDDEN_ACCE_SKIN'),
    ('AcceToolTipButton', ('costume', 3), 'HIDDEN_ACCE_COSTUME'),
    ('AuraToolTipButton', ('item', 'COSTUME_SLOT_AURA'), 'HIDDEN_AURA_COSTUME'),
    ('ShiningWeaponToolTipButton', ('item', 'COSTUME_TYPE_SLOT_EFFECT_WEAPON'), 'HIDDEN_SHINING_WEAPON'),
    ('ShiningArmorToolTipButton', ('item', 'COSTUME_TYPE_SLOT_EFFECT_ARMOR'), 'HIDDEN_SHINING_ARMOR'),
    # the mount slot ('costume', 2) has no eye, hiding the mount did nothing.
)
EYE_HIDDEN = ART + 'visibility_hidden.png'
MODE_TABS = ('Costume_Tab_01', 'Costume_Tab_02')
MODE_TEXTS = ('EquipmentTabText', 'CostumeTabText')
PAGE_TABS = ('Inventory_Tab_01', 'Inventory_Tab_02', 'Inventory_Tab_03', 'Inventory_Tab_04')
TAB_STRIP = (10, 33, 78, 20)    # Výbava / Kostýmy strip: x, y, cell width, height
TAB_VEIN = (6, 66)              # the vein under the selected mode tab: inset, width (line on the strip's last row)
PAGE_ROW = (10, 244, 39, 20)    # pages I - IV
PAGE_VEIN = (4, 31)
SEARCH_FIELD = (52, 2, 104)     # R1 field on the search carrier (160 x 28): x, y, width
SEARCH_MAX = 55
MONEY_FONT = 'Tahoma:11'        # the money bar's font of the uiscript (inventorywindow.py "Money"), for the undo


def Art(name, r1=True):
    """Path of an inventory texture in the chosen look (the original when no recoloured copy exists)."""
    return (ART if r1 and name in RECOLOURED else ORIGINAL) + name


RECOLOURED = frozenset(
    ['mode_active.png', 'mode_inactive.png', 'mode_frame.png', 'page_active.png', 'page_inactive.png',
     'page_frame.png', 'panel_equipment.png', 'equipment_slot_completion.png', 'panel_costume.png',
     'item_grid_underlay.png', 'item_slot.png', 'item_slot_framed.png', 'currency_footer.png',
     'currency_footer_wide.png', 'search_carrier.png', 'costume_slot_transparent.png',
     'retired_arrow_slot_cover.png', 'plus_01.png', 'plus_02.png', 'plus_03.png', 'rail_background.png']
    + ['%s_%s.png' % (stem, state) for stem in ('quick_buff_toggle', 'search_toggle', 'search_utility', 'rail_button')
       for state in STATES]
    + ['search_input_%s.png' % state for state in ('normal', 'focused', 'disabled')]
    + ['rail_%s_%s.png' % (stem, state) for stem in ('more_bar', 'settings') for state in ('normal', 'hover', 'pressed')]
    + ['rail_tab_%s_%s.png' % (k, s) for k in ('expand', 'minimize') for s in ('normal', 'over', 'down')]
    + ['rail_head_%s_%s.png' % (k, s) for k in ('expand', 'minimize', 'more') for s in ('normal', 'hover', 'pressed')]
    + ['rail_%s_%s_%s.png' % (bar, k, s) for bar in ('page', 'pagebar') for k in ('up', 'down')
       for s in ('normal', 'hover', 'pressed')]
    + ['rail_%s_num_%d.png' % (bar, n) for bar in ('page', 'pagebar') for n in (1, 2, 3)])


def SlotNumber(source):
    """The slot number of a hint / eye source: ('start', n) = the n-th equipment cell, ('costume', n) = the n-th
    costume cell, ('item', NAME) = the item module's constant (None when the client has no such constant)."""
    try:
        import item
        import player
    except ImportError:            # a tool / test without the client modules: no hints
        return None
    kind, value = source
    if kind == 'start':
        return player.EQUIPMENT_SLOT_START + value
    if kind == 'costume':
        return item.COSTUME_SLOT_START + value
    number = getattr(item, value, None)
    return None if number is None else int(number)


def HintImage(parent, path, x, y):
    """The type outline of one slot: a not-pickable image over the board (shown only while the slot is empty)."""
    image = ui.ImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.Hide()
    return image


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


def _child(window, name):
    getter = getattr(window, 'GetChild2', None)
    if getter is not None:
        return getter(name)
    return window.GetChild(name) if window.IsChild(name) else None


class InventorySkin(object):
    """R1 look of one InventoryWindow. Build failures undo every change and re-raise (the window traces them)."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.frame = self.header = self.tab_vein = self.page_vein = self.field = None
        self.rail = None
        self.hints = []            # (image, slot number) - the type outlines of the empty slots
        self.eyes = []             # (button, slot number, osfInfo flag)
        try:
            self._Build()
            self.Sync()
        except Exception:
            self.Undo()
            raise

    # ------------------------------------------------------------------ build
    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.wndInventoryBody
        # The window is 'not_pick' (inventorywindow.py): the engine never raises it on a click by itself; a mouse-down
        # on its body or header ('attach') reaches it and brings it to the front.
        uir1.Front(w, not_pick=True)
        # The frame draws inside the old body background (its first child), so every control of the body draws
        # above it - the body keeps its order and its controls.
        background = w.GetChild('AltheaInventoryBackground')
        self.frame = uir1.Frame(background, 0, 0, BODY_W, BODY_H, 'window')
        for name in ('TitleBar', 'TitleName'):
            rec.Hide(w.GetChild(name))
        for name, x, y in HEADER_BUTTONS:
            button = _child(w, name)
            if button is not None:
                rec.Position(button, x, y)
        for name, stem in (('SortInventoryButton', 'search_toggle'), ('QuickBuffButton', 'quick_buff_toggle')):
            button = _child(w, name)
            if button is not None:
                rec.Visuals(button, [Art('%s_%s.png' % (stem, s)) for s in STATES],
                            [ORIGINAL + '%s_%s.png' % (stem, s) for s in STATES])
        plus = _child(w, 'QuickBuffSettingsButton')
        if plus is not None:
            rec.Visuals(plus, PLUS_R1, PLUS_ORIGINAL)
        for name, art in IMAGES:
            image = _child(w, name)
            if image is not None:
                rec.Image(image, Art(art), ORIGINAL + art)
        completion = _child(w, COMPLETION)
        if completion is not None:
            rec.Hide(completion)
        self._BuildSlots()
        cover = getattr(w, 'retiredArrowSlotCover', None)
        if cover is not None:
            rec.Image(cover, Art('retired_arrow_slot_cover.png'), RETIRED_COVER)
        for names, active, inactive in ((MODE_TABS, 'mode_active.png', 'mode_inactive.png'),
                                        (PAGE_TABS, 'page_active.png', 'page_inactive.png')):
            for name in names:
                tab = _child(w, name)
                if tab is not None:
                    rec.Visuals(tab, (Art(inactive), Art(inactive), Art(active)),
                                (ORIGINAL + inactive, ORIGINAL + inactive, ORIGINAL + active))
        rec.SlotBase(w.wndItem, uir1.SLOT_CELL, ORIGINAL + 'item_slot_framed.sub')
        underlay = _child(w, GRID_UNDERLAY)
        if underlay is not None:
            rec.Hide(underlay)
        self._BuildSearch()
        self._BuildMoney()
        x, y, cell, h = TAB_STRIP
        self.tab_vein = uir1.Vein(board, x + TAB_VEIN[0], y + h - 1, TAB_VEIN[1])
        x, y, cell, h = PAGE_ROW
        self.page_vein = uir1.Vein(board, x + PAGE_VEIN[0], y + h - 1, PAGE_VEIN[1])
        title = w.GetChild('TitleName').GetText()
        # The header is the last child of the body: its X takes the clicks over the title row, the rest of the
        # header lets them through (not_pick) to the three header buttons.
        self.header = uir1.Header(board, kit, BODY_W, title, on_close=ui.__mem_func__(w.Close),
                                  left_reserved=TITLE_LEFT)
        self.mode_texts = [_child(w, name) for name in MODE_TEXTS]
        self.page_texts = [_child(w, name + '_Print') for name in PAGE_TABS]
        self.fonts = {}
        # The fonts of the original look, for Undo: the mode texts use the control font of the uiscript, the page
        # numbers the client's default font.
        try:
            import fontconfig
            control = fontconfig.FontForRole(fontconfig.ROLE_CONTROL)
        except Exception:
            control = None
        self.legacy_fonts = dict((id(line), control) for line in self.mode_texts if line is not None)
        strip_h = TAB_STRIP[3]
        for line in self.mode_texts:          # centred in the 20 px strip (the uiscript puts the old font at y 3)
            if line is not None:
                rec.Position(line, line.GetLocalPosition()[0], max(0, (strip_h - kit.cell('text_s')) // 2))

    def _BuildSlots(self):
        """the type outline of every slot of both boards (shown while the slot is empty) and the costume
        eyes this skin shows / hides; SyncSlots() sets them from the worn items."""
        w = self.window
        for board_name, slot_name, origin, table, side in (
                ('Equipment_Base', 'EquipmentSlot', EQUIPMENT_SLOT_ORIGIN, EQUIPMENT_HINTS, 'eq'),
                ('Costume_Base', 'CostumeSlot', COSTUME_SLOT_ORIGIN, COSTUME_HINTS, 'co')):
            board = _child(w, board_name)
            if board is None:
                continue
            ox, oy = origin
            for key, source, x, y, unused in table:
                number = SlotNumber(source)
                if number is None:
                    continue
                self.hints.append((HintImage(board, ART + 'hint_%s_%s.png' % (side, key), ox + x, oy + y), number))
        for name, source, flag in EYES:
            button = _child(w, name)
            number = SlotNumber(source)
            if button is not None and number is not None:
                self.eyes.append((button, number, flag))
        eyes = list(self.eyes)

        def back():
            for button, unused, unused2 in eyes:
                button.Show()
            refresh = getattr(w, 'RefreshVisibleCostume', None)
            if refresh is not None:
                refresh()      # the original eye visuals
        self.rec.Call(lambda: None, back)

    def SyncSlots(self):
        """The type outline only on an empty slot; a costume eye only on a worn costume or a hidden one (so it can be
        shown again); a hidden costume's eye in the R1 red."""
        if not self.hints and not self.eyes:
            return
        import player
        get = player.GetItemIndex
        for image, number in self.hints:
            if get(number):
                image.Hide()
            else:
                image.Show()
        try:
            import osfInfo
        except Exception:
            osfInfo = None
        for button, number, flag in self.eyes:
            hidden = bool(getattr(osfInfo, flag, 0)) if osfInfo is not None else False
            if hidden:
                button.SetUpVisual(EYE_HIDDEN)
                button.SetOverVisual(EYE_HIDDEN)
                button.SetDownVisual(EYE_HIDDEN)
            if hidden or get(number):
                button.Show()
            else:
                button.Hide()

    def SyncSlotsSafe(self):
        """SyncSlots() for the window's refresh hooks: a failure is traced and never breaks the refresh."""
        try:
            self.SyncSlots()
        except Exception:
            uir1.TraceFailure('the inventory (slots)')

    def _BuildMoney(self):
        """The money bar: the amount as the one R1 yang price (root/uir1price.py):
        "1.234.567 Yang" in Tahoma 12 with the outline, 4 px right of the bar's own coin (the coin stays, as the team
        decided 6. 10.). The window writes the text (InventoryWindow.RefreshStatus, FormatYang while dressed)."""
        w = self.window
        line, icon = _child(w, 'Money'), _child(w, 'Money_Icon')
        if line is None or icon is None:
            return
        import uir1price
        ix, iy = icon.GetLocalPosition()
        lx, ly = line.GetLocalPosition()
        # the line lives in Money_Slot (at 0, 0 of the icon's parent): the coin's row is the icon's y
        slot = _child(w, 'Money_Slot')
        sx, sy = slot.GetLocalPosition() if slot is not None else (0, 0)
        x = ix + uir1price.ICON_W + uir1price.ICON_GAP - sx
        y = iy + uir1.CellTop(uir1price.ICON_H, uir1price.FONT) - sy

        def do():
            uir1price.StyleLine(line)
            line.SetPosition(x, y)

        def back():
            line.SetPosition(lx, ly)
            uir1price.UnstyleLine(line, MONEY_FONT)
            refresh = getattr(w, 'RefreshStatus', None)
            if refresh is not None:
                refresh()
        self.rec.Call(do, back)

    def _BuildSearch(self):
        w, rec = self.window, self.rec
        base = getattr(w, 'wndSearchBarBase', None)
        if base is None:
            return
        rec.Image(base, Art('search_carrier.png'), ORIGINAL + 'search_carrier.png')
        for button in (getattr(w, 'btnSearchStack', None), getattr(w, 'btnSearchSort', None)):
            if button is not None:
                rec.Visuals(button, [Art('search_utility_%s.png' % s) for s in STATES],
                            [ORIGINAL + 'search_utility_%s.png' % s for s in STATES])
        grid = getattr(w, 'wndItemSRC', None)
        if grid is not None:
            rec.SlotBase(grid, uir1.SLOT_CELL, ORIGINAL + 'item_slot.sub')
        edit, slot = getattr(w, 'wndSearchEdit', None), getattr(w, 'wndNameSlot', None)
        if edit is None or slot is None:
            return
        # The search line keeps its object (IME update, Escape, focus events of the window) inside an R1 field.
        hint = getattr(edit, 'infoMsg', '') or ''
        x, y, fw = SEARCH_FIELD
        ex, ey = edit.GetLocalPosition()
        ew, eh = edit.GetWidth(), edit.GetHeight()

        def back():
            edit.SetParent(slot)
            edit.SetPosition(ex, ey)
            edit.SetSize(ew, eh)
            text = edit.GetText()
            edit.SetText('')
            edit.SetDefaultFontName()
            edit.SetText(text)
            field = self.field
            self.field = None
            if field is not None:
                field.Hide()
        rec.Call(lambda: None, back)
        self.field = uir1.Field(base, self.kit, x, y, fw, hint=hint, edit=edit, max_len=SEARCH_MAX)
        rec.Hide(slot)

    # ------------------------------------------------------------------ state
    def _Style(self, line, selected):
        """text_sb + ivory on the selected tab / page, text_s + dim on the others."""
        if line is None:
            return
        font = self.kit.font('text_sb' if selected else 'text_s')
        if self.fonts.get(id(line)) != font:
            if id(line) not in self.fonts:
                self.rec.Font(line, font, T.IVORY if selected else T.INK_DIM, self.legacy_fonts.get(id(line)))
            else:
                uir1.SetFont(line, font)
            self.fonts[id(line)] = font
        line.SetPackedFontColor(T.IVORY if selected else T.INK_DIM)

    def Sync(self):
        """Veins under the selected tab and page, the tab texts, the pressed magnifier while the search is open."""
        w = self.window
        searching = bool(getattr(w, '_searchFieldBarVisible', False))
        mode = 1 if getattr(w, 'ExtraPageIndex', 0) == 1 else 0
        x, y, cell, h = TAB_STRIP
        if searching:
            self.tab_vein.Hide()
        else:
            self.tab_vein.SetPosition(x + mode * cell + TAB_VEIN[0], y + h - 1 - T.VEIN_ROW)
            self.tab_vein.Show()
        for index, line in enumerate(self.mode_texts):
            self._Style(line, index == mode)
        page = int(getattr(w, 'inventoryPageIndex', 0) or 0)
        x, y, cell, h = PAGE_ROW
        self.page_vein.SetPosition(x + page * cell + PAGE_VEIN[0], y + h - 1 - T.VEIN_ROW)
        for index, line in enumerate(self.page_texts):
            self._Style(line, index == page)
        toggle = _child(w, 'SortInventoryButton')
        if toggle is not None:
            toggle.Down() if searching else toggle.SetUp()

    def BindRail(self, rail):
        """The shortcut rail of this inventory (uitaskbar.ExpandedTaskBar) takes the R1 art too."""
        self.rail = rail
        rail.SetR1Look(True)

    def SyncSafe(self):
        """Sync() for the window's hooks: a failure is traced (syserr) and never breaks the window's own refresh."""
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure('the inventory (state)')

    # ------------------------------------------------------------------ teardown
    def _DestroyHints(self):
        for image, unused in self.hints:
            try:
                image.Hide()
            except Exception:
                pass
        self.hints = []
        self.eyes = []

    def Undo(self):
        self.rec.Undo()
        self._DestroyHints()
        uir1skin.Destroy([self.field, self.tab_vein, self.page_vein, self.header, self.frame])
        self.frame = self.header = self.tab_vein = self.page_vein = self.field = None

    def Destroy(self):
        self._DestroyHints()
        uir1skin.Destroy([self.tab_vein, self.page_vein, self.header, self.frame])
        self.rec.undo = []
        self.rail = None
        self.window = None
