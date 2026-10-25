# -*- coding: utf-8 -*-
"""The Strom and Tituly a vzhled pages of the craft book (root/uicraftbook.py), built only from the book's own R1
parts (panel frames, tiles, chapter-row backgrounds, overlines, the red meter, the R1 button and check box), so they
look like the rest of the book. Data: root/craftmasterymodel.py (server "/craft_mastery state") and
root/crafttitlesmodel.py ("/craft_mastery titles"); every number comes from the server, the client only names the
nodes, titles and looks and words their effects."""
import localeInfo
import ui

import uir1
import uir1tokens as T
import uiremeslaart as A

import craftmasterymodel as MM
import crafttitlesmodel as TM
import uicraftbook as B


def CountText(count, key):
    """count and the word in the form for it: locale_game KEY_1 (1), KEY_2_4 (2-4), KEY_5 (0, 5 and more)."""
    form = '_1' if count == 1 else ('_2_4' if 2 <= count <= 4 else '_5')
    return u'%d %s' % (count, getattr(localeInfo, key + form))

PAGE_W = B.PAGE_W
BOOK_Y = B.BOOK_Y
BOOK_H = B.BOOK_H
LEFT_X, RIGHT_X = B.LEFT_PAGE_X, B.RIGHT_PAGE_X
TILE = A.BOOK_TILE
ICON = 32
COL_W = (PAGE_W - 24) // 3
COLS_Y = BOOK_Y + 64
NODES_Y = COLS_Y + 18
NODE_PITCH = TILE + 18         # the rank line under every tile (+5 px air in the 440 px window)
ROOT = A.ROOT + 'craft_book/'
NODE_ROOT = 'd:/ymir work/ui/public/althea_craft_mastery/'
# 'custom': the painted node icons (craft_mastery/icon_<H|F>_<node id>.png, 40 px); 'items': game item icons (KS9 A/B)
ICON_SET = 'custom'
NODE_ICON = 40
SILHOUETTE = B.SILHOUETTE

COLUMN_NAMES = (u'Ruka', u'Oko', u'Vytrvalost', u'Vrchol')
# node names per craft (index) and node id; the server only sends ids
NAMES = (
    {'ruka1': u'Jistá ruka', 'ruka2': u'Pevný vlasec', 'ruka3': u'Klidná hladina', 'oko1': u'Znalec vod',
     'oko2': u'Lovec vzácných', 'oko3': u'Lovec trofejí', 'vytr1': u'Dvojitý úlovek', 'vytr2': u'Kostař',
     'vytr3': u'Cvik s prutem', 'mistr': u'Mistr rybář'},
    {'ruka1': u'Pevná ruka', 'ruka2': u'Klidná ruka', 'ruka3': u'Úder mistra', 'oko1': u'Oko pro žílu',
     'oko2': u'Sběratel rud', 'oko3': u'Zlatá žíla', 'vytr1': u'Rychlý krok', 'vytr2': u'Hornická zručnost',
     'vytr3': u'Cvik s krumpáčem', 'mistr': u'Mistr horník'},
    {'ruka1': u'Jistý rytmus', 'ruka2': u'Druhý dech', 'ruka3': u'Mistrovská seč', 'oko1': u'Znalec dřeva',
     'oko2': u'Lesník', 'oko3': u'Sběratel', 'vytr1': u'Rychlá seč', 'vytr2': u'Silná paže', 'vytr3': u'Klidná seč',
     'mistr': u'Mistr dřevorubec'},
)
# effect -> (item vnum for the "items" icon set, rank line with {values})
EFFECTS = {
    'mine_great_zone': (29101, u'zóny kruhu o {zone_pct} % širší'),
    'mine_steady': (27119, u'kruh o {slow_pct} % pomalejší'),
    'mine_forgive': (27119, u'{misses}× VEDLE nezruší sérii'),
    'mine_master_strike': (29111, u'po {streak}× VÝBORNĚ kruh o {slow_pct} % pomalejší, rudy +{yield_cap_pct} %'),
    'mine_rare': (50614, u'vzácné nálezy v žílách +{rare_pct} %'),
    'mine_yield': (50606, u'rudy +{yield_pct} %'),
    'mine_double': (50650, u'dvojitý výnos {chance_bp:bp} %'),
    'mine_swings': (15100, u'nejvýš o {swings} švihy méně'),
    'mine_success': (23000, u'úspěch těžby +{success_pp} b.'),
    'mine_overflow': (27126, u'úspěch nad 90 % → rudy, max +{yield_max_pct} %'),
    'mine_practice': (29101, u''),     # locale_game CRAFT_MASTERY_EFFECT_MINE_PRACTICE (Cvik s krumpáčem, 14. 10.)
    'fish_level': (23000, u'úroveň prutu +{level} (méně utečených)'),
    'fish_save': (27400, u'uteklá ryba zůstane na háčku: {save_bp:bp} %'),
    'fish_nothing': (27803, u'„nic“ o {cut_pct} % méně'),
    'fish_mid': (27810, u'střední ryby +{mid_pct} %'),
    'fish_rare': (27826, u'vzácné ryby +{rare_pct} %'),
    'fish_giant': (27805, u'obří kus {giant_bp:bp} % navíc'),
    'fish_double': (27805, u'dvojitý úlovek {chance_bp:bp} %'),
    'fish_bone': (27799, u'kost z ryby {bone_bp:bp} % navíc'),
    'fish_practice': (27400, u'cvik prutu o {practice_pct} % rychleji'),
    'wood_rhythm': (29201, u'okno úderu o {window_ms} ms širší'),
    'wood_forgive': (29201, u'{misses}× vedle nezruší sérii'),
    'wood_steady': (29201, u'šipky o {slow_pct} % pomalejší'),
    'wood_master_strike': (29201, u'strop dřeva z minihry +{yield_cap_pct} %'),
    'wood_rare': (50693, u'vzácné dřevo +{rare_pct} %'),
    'wood_heap': (50690, u'hromádka navíc {extra_heap_pct} %'),
    'wood_double': (50690, u'dvojitý výnos {chance_bp:bp} %'),
    'wood_cycles': (29201, u'seč o {cycles} švih kratší'),
    'wood_arm': (50690, u'dřeva +{yield_pct} %'),
    'wood_stamina': (50690, u'únava o {cuts} sečí později'),
    'apex': (50601, u''),     # the text is locale_game CRAFT_MASTERY_EFFECT_APEX (Mistr: locked until the titles come)
}
ITEM_NAMES = {27799: u'kost', 27987: u'mušle'}


def Words(node, rank):
    """The effect of one rank in words ("rudy +8 %"), values from the server."""
    icon, text = EFFECTS.get(node.effect, (0, u''))
    try:
        import localeInfo
        text = getattr(localeInfo, 'CRAFT_MASTERY_EFFECT_' + node.effect.upper(), None) or text
    except Exception:
        pass
    out = text
    for key, ranks in node.values.items():
        value = ranks[rank - 1] if 0 < rank <= len(ranks) else 0
        out = out.replace(u'{%s:bp}' % key, (u'%d' % (value // 100)) if value % 100 == 0 else (u'%.1f' % (value / 100.0)).replace(u'.', u','))
        out = out.replace(u'{%s:x}' % key, (u'%.1f' % (value / 100.0)).rstrip(u'0').rstrip(u'.,').replace(u'.', u','))
        out = out.replace(u'{%s}' % key, u'%d' % value)
    return out[:1].upper() + out[1:]       # a rank line starts with a capital letter ("Rudy +8 %")


def CraftName(index):
    """Rybář / Horník / Dřevorubec of a craft index (the book's texts)."""
    return B.Tr(B.CRAFTS[index][1])


def NodeName(craft, node):
    return NAMES[craft].get(node.id, node.id) if 0 <= craft < len(NAMES) else node.id


def ItemIcon(vnum):
    try:
        import item
        item.SelectItem(vnum)
        return item.GetIconImageFileName()
    except Exception:
        return ''


def Img(parent, path, x=0, y=0):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


class NodeTile(uir1.Interactive):
    """One node: the book's tile with the item icon, "1/2" in the corner, hover / selected frames."""

    def __init__(self, page, kit, x, y, on_click):
        uir1.Interactive.__init__(self)
        self.kit = kit
        self.SetParent(page)
        self.SetPosition(int(x), int(y))
        self.SetSize(TILE, TILE)
        self.selected = False
        self.hint = u''
        self.SetEvent(on_click)
        self.frames = dict((state, Img(self, NODE_ROOT + 'node_%s.png' % state))
                           for state in ('locked', 'available', 'owned', 'maxed'))
        self.state = 'locked'
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon_path = None
        self.frameHover = Img(self, NODE_ROOT + 'node_hover.png')
        self.frameSelected = Img(self, NODE_ROOT + 'node_selected.png')
        self.rank = uir1.Text(page, '', int(x) + TILE // 2, int(y) + TILE, kit.font('text_xs'), T.INK_DIM,
                              align='center', valign='top')
        self.Show()
        self.paint()

    def Set(self, icon, rank, max_rank, active, can_buy, hint):
        self.hint = hint
        size = NODE_ICON if ICON_SET == 'custom' else ICON
        if icon and icon != self.icon_path:
            B.FitIcon(self.icon, icon, (TILE - size) // 2, (TILE - size) // 2, size, size)
            self.icon_path = icon
        if icon:
            B.Tint(self.icon, (1.0, 1.0, 1.0, 1.0) if (active and (rank or can_buy)) else
                   ((0.55, 0.53, 0.52, 1.0) if active else SILHOUETTE))
            self.icon.Show()
        self.state = ('maxed' if rank >= max_rank else 'owned') if (active and rank) else \
            ('available' if can_buy else 'locked')
        for state, image in self.frames.items():
            if state == self.state:
                image.Show()
            else:
                image.Hide()
        self.rank.SetText(u'%d / %d' % (rank, max_rank) if active else u'připravujeme')
        self.rank.SetPackedFontColor(T.RED_HI if (active and rank) else (T.INK_DIM if active else T.MUTED))

    def Hide(self):
        uir1.Interactive.Hide(self)
        if hasattr(self, 'rank'):
            self.rank.Hide()

    def Show(self):
        uir1.Interactive.Show(self)
        if hasattr(self, 'rank'):
            self.rank.Show()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        if not hasattr(self, 'frameSelected'):
            return
        self.frameSelected.Hide()
        self.frameHover.Hide()
        if self.selected:
            self.frameSelected.Show()
        if self.hovered:
            self.frameHover.Show()

    def OnMouseOverIn(self):
        uir1.Interactive.OnMouseOverIn(self)
        if self.hint:
            uir1.ShowHint(self.kit, self, self.hint)

    def OnMouseOverOut(self):
        uir1.Interactive.OnMouseOverOut(self)
        uir1.HideHint()

    def OnMouseLeftButtonUp(self):
        if self.enabled and self.callback:
            self.callback()
        return True


def NodeIcon(craft, node):
    """The icon path of a node: the painted set (craft_mastery/icon_H_ruka1.png) or the game item."""
    if ICON_SET == 'custom' and craft in (0, 1, 2):
        return NODE_ROOT + 'icon_%s_%s.png' % ('FHW'[craft], node.id)
    return ItemIcon(EFFECTS.get(node.effect, (0, u''))[0])


class MasteryView(ui.Window):
    """The two pages: the tree of the selected craft (left) and the selected node (right)."""

    def __init__(self, window, kit):
        ui.Window.__init__(self)
        self.SetParent(window)
        self.AddFlag('not_pick')
        self.SetPosition(0, 0)
        self.SetSize(B.W, B.H)
        self.window = window
        self.kit = kit
        self.selected = {}
        self.keep = []                  # an unreferenced window is destroyed by the engine
        page = self
        # ---- left page: level, EXP, points, the three columns, the apex row
        self.keep.append(uir1.Frame(page, LEFT_X, BOOK_Y, PAGE_W, BOOK_H, 'panel'))
        x, w = LEFT_X + 12, PAGE_W - 24
        self.level = uir1.Text(page, '', x, BOOK_Y + 8, kit.font('text_b'), T.IVORY, valign='top')
        self.points = uir1.Text(page, '', x + w, BOOK_Y + 10, kit.font('text_s'), T.INK, align='right', valign='top')
        self.meter = B.Meter(page, x, BOOK_Y + 30, w)
        self.exp = uir1.Text(page, '', x + w, BOOK_Y + 44, kit.font('text_xs'), T.INK_DIM, align='right', valign='top')
        self.columns = []
        self.tiles = []
        for column in range(3):
            cx = x + column * COL_W
            self.keep.append(B.Overline(page, kit, cx + 2, COLS_Y, COL_W - 8, COLUMN_NAMES[column].upper()))
            for row in range(3):
                tile = NodeTile(page, kit, cx + (COL_W - TILE) // 2, NODES_Y + row * NODE_PITCH,
                                lambda column=column, row=row: self.Select((column, row + 1)))
                self.tiles.append(((column, row + 1), tile))
        apex_y = NODES_Y + 3 * NODE_PITCH + 1
        self.apex = B.ChapterRow(page, kit, LEFT_X + 8, apex_y, lambda: self.Select((3, 0)))
        # ---- right page: the selected node
        self.keep.append(uir1.Frame(page, RIGHT_X, BOOK_Y, PAGE_W, BOOK_H, 'panel'))
        rx, rw = RIGHT_X + 12, PAGE_W - 24
        self.keep.append(B.Overline(page, kit, rx, BOOK_Y + 8, rw, B.Tr('SELECTED')))
        self.keep.append(Img(page, ROOT + 'tile.png', rx, BOOK_Y + 26))
        self.detailIcon = ui.ExpandedImageBox()
        self.detailIcon.SetParent(page)
        self.detailIcon.AddFlag('not_pick')
        self.detailIconPath = None
        self.name = uir1.Text(page, '', rx + 60, BOOK_Y + 27, kit.font('text_b'), T.IVORY, valign='top')
        self.where = uir1.Text(page, '', rx + 60, BOOK_Y + 51, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.keep.append(B.Overline(page, kit, rx, BOOK_Y + 86, rw, u'STUPNĚ'))
        self.stages = []
        for index in range(2):
            y = BOOK_Y + 104 + index * 22
            mark = uir1.Text(page, '', rx, y, kit.font('text_xs'), T.INK_DIM, valign='top')
            text = uir1.Text(page, '', rx + 22, y, kit.font('text_xs'), T.INK, valign='top')
            self.stages.append((mark, text))
        self.need = uir1.Text(page, '', rx, BOOK_Y + 156, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.cost = uir1.Text(page, '', rx, BOOK_Y + 186, kit.font('text_s'), T.INK, valign='top')
        self.buy = uir1.Button(page, kit, rx + rw - 120, BOOK_Y + 182, 120, u'Odemknout', primary=True, small=True,
                               event=self.Buy)
        self.keep.append(B.Overline(page, kit, rx, BOOK_Y + 220, rw, u'MÁŠ TEĎ'))
        self.owned = []
        for index in range(3):
            y = BOOK_Y + 238 + index * 19
            dot = uir1.Rect(page, rx + 2, y + 6, 5, 5, 0x961C1A)
            text = uir1.Text(page, '', rx + 12, y, kit.font('text_xs'), T.INK, valign='top')
            self.owned.append((dot, text))

    # ------------------------------------------------------------------ fill
    def CraftIndex(self):
        return self.window.CraftIndex()

    def Craft(self):
        snapshot = self.window.MasteryModel().snapshot if hasattr(self.window, 'MasteryModel') else None
        return snapshot.Craft(self.CraftIndex()) if snapshot else None

    def Node(self, craft, cell):
        column, row = cell
        for node in craft.nodes:
            if node.column == column and node.row == row:
                return node
        return None

    def Select(self, cell):
        self.selected[self.CraftIndex()] = cell
        self.Refresh()

    def Buy(self):
        craft = self.Craft()
        node = craft and self.Node(craft, self.selected.get(self.CraftIndex(), (0, 1)))
        if node and node.can_buy == 'ok':
            try:
                import net
                net.SendChatPacket(MM.BuyCommand(self.CraftIndex(), node.id))
            except Exception:
                pass

    def Refresh(self):
        index = self.CraftIndex()
        craft = self.Craft()
        if craft is None:
            self.level.SetText(CraftName(index))
            self.points.SetText(u'')
            self.exp.SetText(u'načítám…')
            return
        self.level.SetText(u'%s · úroveň %d' % (CraftName(index), craft.level))
        self.points.SetText(u'body %d' % craft.Free())
        self.points.SetPackedFontColor(T.RED_HI if craft.Free() else T.INK_DIM)
        if craft.exp_next:
            self.exp.SetText(u'%s / %s EXP' % (Thousands(craft.exp_into), Thousands(craft.exp_next)))
            self.meter.SetRatio(float(craft.exp_into) / craft.exp_next)
        else:
            self.exp.SetText(u'nejvyšší úroveň')
            self.meter.SetRatio(1.0)
        cell = self.selected.setdefault(index, self.FirstBuyable(craft))
        for (column, row), tile in self.tiles:
            node = self.Node(craft, (column, row))
            if node is None:
                tile.Hide()
                continue
            name = NodeName(index, node)
            hint = name if node.active else name + u' – připravujeme'
            tile.Set(NodeIcon(index, node), node.rank, node.max_rank, node.active,
                     node.can_buy == 'ok', hint)
            tile.SetSelected(cell == (column, row))
            tile.Show()
        apex = self.Node(craft, (3, 0))
        if apex and not apex.active:
            # Mistr is shown but locked until the titles and tool looks come (server data active false)
            self.apex.Set(u'', NodeName(index, apex), 0, 1)
            self.apex.count.SetText(B.Tr('SOON'))
        elif apex:
            self.apex.Set(u'', NodeName(index, apex), min(craft.points_spent, craft.apex_threshold),
                          craft.apex_threshold or 1)
            self.apex.SetSelected(cell == (3, 0))
        self.RefreshDetail(index, craft, self.Node(craft, cell))

    def FirstBuyable(self, craft):
        for node in sorted(craft.nodes, key=lambda n: (n.row == 0, n.row, n.column)):
            if node.can_buy == 'ok':
                return (node.column, node.row)
        return (0, 1)

    def RefreshDetail(self, index, craft, node):
        if node is None:
            return
        rx = RIGHT_X + 12
        icon = NodeIcon(index, node)
        if icon and icon != self.detailIconPath:
            B.FitIcon(self.detailIcon, icon, rx + 1, BOOK_Y + 27, TILE - 2, TILE - 2)
            self.detailIconPath = icon
            self.detailIcon.Show()
        self.name.SetText(NodeName(index, node))
        if node.column == 3 and not node.active:
            self.where.SetText(u'vrchol stromu · %s' % B.Tr('SOON'))
        elif node.column == 3:
            self.where.SetText(u'vrchol stromu · %d / %s' % (min(craft.points_spent, craft.apex_threshold),
                                                         CountText(craft.apex_threshold, 'CRAFT_MASTERY_SPENT')))
        else:
            self.where.SetText(u'%s · %d. uzel · stupeň %d / %d' % (COLUMN_NAMES[node.column], node.row, node.rank,
                                                                   node.max_rank))
        for rank, (mark, text) in enumerate(self.stages, 1):
            if rank <= node.max_rank:
                mark.SetText((u'I', u'II', u'III')[rank - 1])
                uir1.Fit(text, Words(node, rank), PAGE_W - 24 - 22)
                color = T.IVORY if rank <= node.rank else (T.INK if rank == node.rank + 1 else T.MUTED)
                text.SetPackedFontColor(color)
                mark.SetPackedFontColor(T.RED_HI if rank <= node.rank else T.INK_DIM)
                mark.Show()
                text.Show()
            else:
                mark.Hide()
                text.Hide()
        reasons = {'ok': u'Lze odemknout', 'items': u'Chybí kosti nebo mušle', 'max': u'Hotovo', 'inactive': u'Připravujeme',
                   'level': u'Chce úroveň %d' % node.min_level, 'prerequisite': u'Nejdřív uzel nad ním',
                   'apex': u'Chce %s' % CountText(craft.apex_threshold, 'CRAFT_MASTERY_SPENT'), 'points': u'Málo bodů',
                   'disabled': u'Řemeslo zatím nejde', 'unknown': u''}
        uir1.Fit(self.need, reasons.get(node.can_buy, u''), PAGE_W - 24)
        cost = CountText(node.next_cost, 'CRAFT_MASTERY_POINT') if node.next_cost else u''
        for vnum, count in getattr(node, 'items', ()):
            cost += u' + %d× %s' % (count, ITEM_NAMES.get(vnum, u'předmět'))
        uir1.Fit(self.cost, cost, PAGE_W - 24 - 128)
        if node.can_buy == 'ok':
            self.buy.Show()
        else:
            self.buy.Hide()
        owned = [n for n in sorted(craft.nodes, key=lambda n: (n.column, n.row)) if n.active and n.rank]
        for (dot, text), owned_node in zip(self.owned, owned + [None] * 3):
            if owned_node is None:
                dot.Hide()
                text.Hide()
            else:
                uir1.Fit(text, Words(owned_node, owned_node.rank), PAGE_W - 24 - 12)
                dot.Show()
                text.Show()


def Thousands(value):
    text = u'%d' % value
    groups = []
    while len(text) > 3:
        groups.insert(0, text[-3:])
        text = text[:-3]
    groups.insert(0, text)
    return u'\xa0'.join(groups)


# --------------------------------------------------------------------------- Tituly a vzhled
# The page under the craft switch, no panel (owner mockup TIT-KNIHA = B): the current and the next title with the
# progress of the selected craft (Strom: level, Kniha: the book counter), the titles with their requirement and
# state, the looks of the craft's tool (check boxes, one at a time; locked ones dimmed with their requirement).
PROFILE = T.PROFILE_WINDOW
TIT_X = B.AREA_X + 6                    # the text column (the switch edge + a little)
TIT_RIGHT = B.AREA_X + B.AREA_W - 6     # right-aligned values
TIT_VALUE_X = TIT_X + 60                # the title name and the meters after "Titul" / "Strom" / "Kniha"
TIT_NEED_X = TIT_X + 190                # the requirement column of the titles and the looks
TIT_VALUE_W = 190                       # the meter values ("3 100 / 4 500 úlovků") right of the meters
TIT_ROW_S = PROFILE['row_s']            # the summary rows
TIT_ROW = PROFILE['row']                # the title and look rows
TIT_Y = BOOK_Y + 4
TIT_RULE_GAP = 6
TITLES_TOP = TIT_Y + 3 * TIT_ROW_S + 2 * TIT_RULE_GAP
TITLE_ROWS = 4
SKINS_RULE_Y = TITLES_TOP + TITLE_ROWS * TIT_ROW + TIT_RULE_GAP
SKINS_HEAD_Y = SKINS_RULE_Y + 2 * TIT_RULE_GAP
SKINS_TOP = SKINS_HEAD_Y + TIT_ROW_S + 4
SKIN_ROWS = 4                           # Bez vzhledu + three looks of one craft
TIT_BOOK_KEYS = ('TIT_BOOK_FISH', 'TIT_BOOK_MINE', 'TIT_BOOK_WOOD')
SKIN_HEAD_KEYS = ('SKIN_HEAD_FISH', 'SKIN_HEAD_MINE', 'SKIN_HEAD_WOOD')


def TitleName(title_id):
    return B.DataText('CRAFT_TITLE_', title_id)


def SkinName(skin_id):
    return B.DataText('CRAFT_SKIN_', skin_id)


def SetCheckText(box, text, width):
    """A new label of an R1 check box (shortened to ``width``); the hit area follows it."""
    uir1.Fit(box.label, text, width - T.CHECK - 7)
    box.w = T.CHECK + 7 + uir1.TextWidth(box.label)
    box.SetSize(box.w, box.h)


class TitlesView(ui.Window):
    def __init__(self, window, kit):
        ui.Window.__init__(self)
        self.SetParent(window)
        self.AddFlag('not_pick')
        self.SetPosition(0, 0)
        self.SetSize(B.W, B.H)
        self.window = window
        self.kit = kit
        page = self
        text = kit.font('text')
        meter_w = TIT_RIGHT - TIT_VALUE_W - 10 - TIT_VALUE_X
        # ---- the current title and the progress of the selected craft
        self.titleLabel = B.Label(page, kit, B.Tr('TIT_TITLE'), TIT_X, TIT_Y, TIT_ROW_S)
        self.title = B.Label(page, kit, '', TIT_VALUE_X, TIT_Y, TIT_ROW_S, color=T.IVORY)
        self.next = B.Label(page, kit, '', TIT_RIGHT, TIT_Y, TIT_ROW_S, 'text_s', T.INK_DIM, 'right')
        self.meters = []
        for index, key in enumerate(('TAB_TREE', 'TAB_BOOK')):
            y = TIT_Y + (index + 1) * TIT_ROW_S
            label = B.Label(page, kit, B.Tr(key), TIT_X, y, TIT_ROW_S)
            meter = B.Meter(page, TIT_VALUE_X, y + (TIT_ROW_S - B.METER_H) // 2, meter_w)
            value = B.Label(page, kit, '', TIT_RIGHT, y, TIT_ROW_S, 'text_s', T.IVORY, 'right')
            self.meters.append((label, meter, value))
        self.rule = uir1.Divider(page, TIT_X, TITLES_TOP - TIT_RULE_GAP - 2, TIT_RIGHT - TIT_X)
        # ---- the titles
        self.rows = []
        for index in range(TITLE_ROWS):
            y = TITLES_TOP + index * TIT_ROW
            name = B.Label(page, kit, '', TIT_X, y, TIT_ROW, 'text')
            need = B.Label(page, kit, '', TIT_NEED_X, y, TIT_ROW, 'text_s')
            state = B.Label(page, kit, '', TIT_RIGHT, y, TIT_ROW, 'text_s', align='right')
            self.rows.append((name, need, state))
        self.wornRule = uir1.Divider(page, TIT_X, TITLES_TOP, TIT_RIGHT - TIT_X)
        # ---- the looks of the craft's tool
        self.skinsRule = uir1.Divider(page, TIT_X, SKINS_RULE_Y, TIT_RIGHT - TIT_X)
        self.skinsHead = B.Label(page, kit, '', TIT_X, SKINS_HEAD_Y, TIT_ROW_S, 'text_s')
        self.skins = []
        for index in range(SKIN_ROWS):
            y = SKINS_TOP + index * TIT_ROW
            box = uir1.CheckBox(page, kit, TIT_X, y, B.Tr('SKIN_NONE'), font=text)
            box.SetPosition(TIT_X, y + (TIT_ROW - box.h) // 2)
            need = B.Label(page, kit, '', TIT_NEED_X, y, TIT_ROW, 'text_s')
            self.skins.append([box, need, None])
        self.skinsSoon = B.Label(page, kit, B.Tr('SKIN_SOON'), TIT_X, SKINS_TOP + TIT_ROW, TIT_ROW, 'text_s', T.MUTED)

    # ------------------------------------------------------------------ fill
    def Snapshot(self):
        return self.window.TitlesModel().snapshot

    def Refresh(self):
        craft = self.window.CraftIndex()
        snapshot = self.Snapshot()
        level = self.window.CraftLevel(craft)
        number = B.M.FormatNumber
        rows_shown = snapshot is not None and snapshot.enabled and bool(snapshot.titles)
        if snapshot is None or not snapshot.enabled:
            self.title.SetText(B.Tr('LOADING') if snapshot is None else B.Tr('TIT_OFF'))
            self.title.SetPackedFontColor(T.MUTED)
            self.next.SetText('')
            for unused, meter, value in self.meters:
                meter.SetRatio(0.0)
                value.SetText('')
        else:
            current, target = snapshot.Current(), snapshot.Target()
            self.title.SetText(TitleName(current.id) if current else B.Tr('TIT_NONE'))
            self.title.SetPackedFontColor(T.IVORY if current else T.INK_DIM)
            nxt = snapshot.Next()
            uir1.Fit(self.next, B.Tr('TIT_NEXT') % TitleName(nxt.id) if nxt else
                     (B.Tr('TIT_TOP') if current else ''), TIT_RIGHT - TIT_VALUE_X - 200)
            count = snapshot.BookCount(craft)
            goals = ((level, target.level if target else 0,
                      B.Tr('TIT_LEVEL') % (u'–' if level is None else level, target.level if target else 0)),
                     (count, target.Book(craft) if target else 0,
                      B.Tr(TIT_BOOK_KEYS[craft]) % (number(count), number(target.Book(craft) if target else 0))))
            for (unused, meter, value), (have, need, line) in zip(self.meters, goals):
                meter.SetRatio(float(have or 0) / need if need else 0.0)
                uir1.Fit(value, line, TIT_VALUE_W)
        # the titles
        worn = -1
        for index, (name, need, state) in enumerate(self.rows):
            title = snapshot.titles[index] if rows_shown and index < len(snapshot.titles) else None
            if title is None:
                for widget in (name, need, state):
                    widget.Hide()
                continue
            kind = snapshot.State(index)
            worn = index if kind == TM.WORN else worn
            color = {TM.WORN: T.IVORY, TM.EARNED: T.INK}.get(kind, T.MUTED)
            uir1.Fit(name, TitleName(title.id), TIT_NEED_X - TIT_X - 10)
            name.SetPackedFontColor(color)
            need.SetText(B.Tr('TIT_NEED') % (title.level, number(title.Book(craft))))
            need.SetPackedFontColor(T.INK_DIM if kind in (TM.WORN, TM.EARNED) else T.MUTED)
            state.SetText({TM.WORN: B.Tr('TIT_WORN'), TM.EARNED: B.Tr('TIT_EARNED'),
                           TM.LOCKED: B.Tr('TIT_LOCKED')}.get(kind, ''))
            state.SetPackedFontColor({TM.WORN: T.IVORY, TM.EARNED: T.INK_DIM}.get(kind, T.MUTED))
            for widget in (name, need, state):
                widget.Show()
        if worn >= 0 and worn + 1 < min(TITLE_ROWS, len(snapshot.titles)):
            self.wornRule.SetPosition(TIT_X, TITLES_TOP + (worn + 1) * TIT_ROW - 2)
            self.wornRule.Show()
        else:
            self.wornRule.Hide()
        self.RefreshSkins(craft, snapshot if rows_shown else None)

    def RefreshSkins(self, craft, snapshot):
        if snapshot is None:
            for widget in [self.skinsRule, self.skinsHead, self.skinsSoon] + [w for row in self.skins for w in row[:2]]:
                widget.Hide()
            return
        self.skinsRule.Show()
        uir1.Fit(self.skinsHead, B.Tr(SKIN_HEAD_KEYS[craft]), TIT_RIGHT - TIT_X)
        self.skinsHead.Show()
        skins = snapshot.Skins(craft)
        chosen = snapshot.Chosen(craft)
        entries = [(None, B.Tr('SKIN_NONE'), '', True)]
        for skin in skins[:SKIN_ROWS - 1]:
            need = B.Tr('SKIN_NEED_LEVEL') % skin.need_level if skin.need == 'level' else B.Tr('SKIN_NEED_APEX')
            entries.append((skin.id, SkinName(skin.id), need, skin.unlocked))
        for index, row in enumerate(self.skins):
            box, need = row[0], row[1]
            if index >= len(entries):
                box.Hide()
                need.Hide()
                continue
            skin_id, name, need_text, unlocked = entries[index]
            row[2] = skin_id
            SetCheckText(box, name, TIT_NEED_X - TIT_X - 10)
            box.SetOn(skin_id == chosen)
            box.SetEvent(lambda skin_id=skin_id: self.window.ChooseSkin(skin_id))
            if unlocked:
                box.Enable()
            else:
                box.Disable()
            need.SetText(need_text)
            need.SetPackedFontColor(T.INK_DIM if unlocked else T.MUTED)
            box.Show()
            need.Show()
        if skins:
            self.skinsSoon.Hide()
        else:
            self.skinsSoon.Show()
