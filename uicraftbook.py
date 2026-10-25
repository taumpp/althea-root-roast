# -*- coding: utf-8 -*-
"""R1 craft book: per-character fishing/mining/woodcutting collection, statistics, mastery tree and titles.

The window (owner TIT-KNIHA = B, 13. 10.): a side column on the left, a hairline, and right of it the craft switch
(Rybář · úr. N | Horník · úr. N | Dřevorubec · úr. N, the level from the mastery model) over the page of the selected
craft. The side column (sidebar variant B, "řemesla pod sebou", owner 13. 10.: "the sidebar looks empty"): the page
tabs Kniha / Strom / Statistiky / Tituly a vzhled (the selected one with the R1 red select line), "Řemesla" - every
craft with its emblem, level, EXP bar and the R1 badge of the free tree points, the selected craft with the red select
line, a click selects it - and "Titul": the worn title, the next one with the way of the selected craft to it, the
chosen tool look. Every number comes from the server snapshots the book asks for on Open (/craft state,
/craft_mastery state, /craft_mastery titles).

Requests /craft state; commits only complete server snapshots. Species and ore identities come from servergamedata,
chapter entries from the mastery snapshot. An optional mining controller may supply check statistics, but the ordinary book
works without a mining minigame. The Dřevorubec tab opens only with the woodcutting controller (uiwoodcheck.WoodCheck:
the rhythm bar switch); without it the tab stays locked ("Připravujeme"). The Strom and Tituly a vzhled pages are
root/uicraftmastery.py (models root/craftmasterymodel.py and root/crafttitlesmodel.py).
"""
import ui

import uir1
import uir1layout as L
import uir1tokens as T
import uiremeslaart as A

import craftbookmodel as M
import craftmasterymodel as MM
import crafttitlesmodel as TM

WHAT = 'craftbook'
PROFILE = T.PROFILE_WINDOW
W, H = 800, 440               # sidebar B: the side column is 40 px wider than the 136 px rail, the pages stay
EDGE = PROFILE['pad']       # the window edge (left, right, bottom)
GAP = PROFILE['gap']        # between the panels
TABS_Y = 37                 # the rail and the craft switch
RAIL_X, RAIL_W = EDGE, 176  # the side column: the page tabs, the crafts, the title
RAIL_ROW = PROFILE['row']
RAIL_PITCH = RAIL_ROW + 4
RAIL_TEXT_X = 10            # the tab label from the left of its row
SIDE_X = RAIL_X + 8         # the texts of the side column
SIDE_W = RAIL_W - 16
CRAFTS_Y = TABS_Y + 4 * RAIL_PITCH + 8      # the "Řemesla" overline under the page tabs
CRAFT_ROWS_Y = CRAFTS_Y + 18                # the craft rows
CRAFT_ROW_H = A.EMBLEM + 4                  # the emblem, two text lines and the thin bar
CRAFT_PITCH = CRAFT_ROW_H + 4
TITLE_Y = CRAFT_ROWS_Y + len(('fishing', 'mining', 'wood')) * CRAFT_PITCH + 8      # the "Titul" overline
SIDE_BAR_Y = 17                             # the thin bar in a row of the side column
LOOK_Y = H - EDGE - 16                      # the chosen tool look, at the bottom of the column
BAR_TRACK, BAR_FILL = 0x2A2725, 0x961C1A    # the thin bar of the chapter rows (Kapitoly), reused in the side column
SPLIT_X = RAIL_X + RAIL_W + GAP                 # the hairline between the rail and the pages
AREA_X = SPLIT_X + GAP                          # the craft switch and the pages
AREA_W = W - EDGE - AREA_X
BOOK_Y = TABS_Y + T.SEG_H + 8                   # the pages
BOOK_H = H - EDGE - BOOK_Y
PAGE_W = (AREA_W - GAP) // 2
LEFT_PAGE_X, RIGHT_PAGE_X = AREA_X, AREA_X + PAGE_W + GAP
TABS = (('overview', 'TAB_BOOK'), ('mastery', 'TAB_TREE'), ('stats', 'TAB_STATS'), ('titles', 'TAB_TITLES'))
CRAFTS = (('fishing', 'FISHER'), ('mining', 'MINER'), ('wood', 'WOODCUTTER'))      # the mastery craft index order
REQUEST = '/craft state'
REQUEST_GAP = 2.0           # seconds between two requests of one kind (client side)
ROOT = A.ROOT + 'craft_book/'
SILHOUETTE = (0.30, 0.28, 0.27, 0.85)      # diffuse colour of a species / vein not found yet
# owner 13. 10. (KNIHA-SIDEBAR = B): a craft is drawn as its tool (rod, pickaxe, axe), the item icons of item_list;
# which item stands for which craft is data: <craft><TAB><vnum>[<TAB><fallback vnum>...], the first with an icon wins
CRAFT_ICON_TABLE = 'locale/common/craft_book_icons.txt'
CRAFT_PAGE_TABLE = 'locale/common/craft_book_pages.txt'   # page -> on | soon (locked, "Připravujeme")

# the left page (the 440 px window of TIT-KNIHA = B gives the sections more air than the 380 px book had)
EMBLEM_Y = BOOK_Y + 12
FIGURES_Y = BOOK_Y + 64
FIGURES_H = 40
CHAPTERS_Y = BOOK_Y + 118                   # the "Kapitoly" overline
ROWS_TOP = CHAPTERS_Y + 20
CHAPTER_PITCH = 31
BOTTOM_Y = ROWS_TOP + 3 * CHAPTER_PITCH + 14  # the "Rekordy" / "Minihra těžby" overline
RECORD_PITCH = 28
# the right page
TILE, TILE_GAP, TILE_COLS = A.BOOK_TILE, 3, 5
TILES_Y = BOOK_Y + 32
DETAIL_Y = TILES_Y + 2 * (TILE + TILE_GAP) + 14     # the "Vybráno" overline
GOALS_Y = DETAIL_Y + 90                             # the "Další cíl" overline
GOAL_PITCH = 22

# the statistics
LEFT_X, LEFT_W = LEFT_PAGE_X, PAGE_W - 12
ROWS_Y, ROW_PITCH = BOOK_Y + 8, 21
PANEL_X = RIGHT_PAGE_X
PANEL_Y = BOOK_Y
PANEL_W, PANEL_H = PAGE_W, BOOK_H
COLUMNS_Y, LIST_Y, LIST_PITCH = 38, 60, 34
LIST_ROWS = (PANEL_H - LIST_Y - 6) // LIST_PITCH
ICON_X, NAME_X = 10, 48
ICON = 32
COUNT_RIGHT, LENGTH_RIGHT = 196, 262
SCROLL_X = PANEL_W - T.SCROLL_W - 4
METER_H = 12

TEXTS = {
    'TITLE': ('Řemeslná kniha', 'Craft book'),
    'TAB_STATS': ('Statistiky', 'Statistics'),
    'TAB_BOOK': ('Kniha', 'Book'),
    'TAB_TREE': ('Strom', 'Tree'),
    'TAB_TITLES': ('Tituly a vzhled', 'Titles and looks'),
    'CRAFT_LEVEL': ('%s · úr. %d', '%s · lv. %d'),
    'LOADING': ('Načítám záznamy...', 'Loading the records...'),
    'FAILED': ('Řemeslnou knihu se nepodařilo otevřít.', 'The craft book could not be opened.'),
    'FISHER': ('Rybář', 'Fisher'),
    'MINER': ('Horník', 'Miner'),
    'WOODCUTTER': ('Dřevorubec', 'Woodcutter'),
    'SOON': ('Připravujeme', 'Coming soon'),
    'SUB_FISH': ('sbírka %d / %d druhů · %s u vody', 'collection %d / %d species · %s at the water'),
    'SUB_MINE': ('sbírka %d / %d rud · %s u žíly', 'collection %d / %d ores · %s at the veins'),
    'FIG_CATCHES': ('úlovků', 'catches'),
    'FIG_SUCCESS': ('úspěšnost', 'success'),
    'FIG_STREAK': ('série', 'streak'),
    'FIG_STREAK_VALUE': ('%s · max %s', '%s · best %s'),
    'FIG_RUNS': ('těžeb', 'runs'),
    'FIG_ORES': ('kusů rudy', 'pieces of ore'),
    'CHAPTERS': ('KAPITOLY', 'CHAPTERS'),
    'CH_FISH_1': ('Běžné ryby', 'Common fish'),
    'CH_FISH_2': ('Vzácné ryby', 'Rare fish'),
    'CH_FISH_3': ('Podivní tvorové', 'Strange creatures'),     # older server only (A2 has two chapters)
    'CH_ORE_1': ('Běžné rudy', 'Common ores'),
    'CH_ORE_2': ('Vzácné rudy', 'Rare ores'),
    'CH_ORE_3': ('Čisté rudy III', 'Pure ores III'),          # older server only
    'RECORDS': ('REKORDY', 'RECORDS'),
    'REC_BIGGEST': ('Největší', 'Biggest'),
    'REC_MOST': ('Nejčastější', 'Most caught'),
    'REC_RAREST': ('Nejvzácnější', 'Rarest'),
    'REC_EMPTY': ('Rekordy se ukážou po prvním úlovku.', 'Records show after the first catch.'),
    'REC_EMPTY_HINT': ('Prut a návnadu prodává Rybář ve městě.', 'The Fisherman in town sells a rod and bait.'),
    'MINIGAME_SHORT': ('MINIHRA TĚŽBY', 'MINING MINIGAME'),
    'RINGS': ('%s kruhů', '%s rings'),
    'MODE_SHORT_0': ('vypnuta', 'off'),
    'MODE_SHORT_1': ('varianta A - nápřah', 'variant A - swing'),
    'MODE_SHORT_2': ('varianta B - další těžba', 'variant B - next mining'),
    'MODE_SHORT_3': ('zapnuto - kruh při kopání', 'on - a ring while mining'),
    'LEG_GREAT': ('výborně %s', 'great %s'),
    'LEG_GOOD': ('dobře %s', 'good %s'),
    'LEG_MISS': ('vedle %s', 'miss %s'),
    'TIME_VEIN_LINE': ('čas u žíly %s', 'time at the veins %s'),
    'SELECTED': ('VYBRÁNO', 'SELECTED'),
    'UNKNOWN': ('Neobjeveno', 'Not found yet'),
    'UNKNOWN_FISH': ('Chyť ji a zapíše se sem', 'Catch it to record'),
    'UNKNOWN_FISH_2': ('počet a nejdelší kus.', 'the count and the longest.'),
    'UNKNOWN_VEIN': ('Vytěž ji a zapíše se sem', 'Mine it to record'),
    'UNKNOWN_VEIN_2': ('množství rudy.', 'the amount of ore.'),
    'SUB_FISH_NEW': ('sbírka %d / %d druhů', 'collection %d / %d species'),
    'SUB_MINE_NEW': ('sbírka %d / %d rud', 'collection %d / %d ores'),
    'CAUGHT': ('Chyceno', 'Caught'),
    'SHARE': ('Podíl', 'Share'),
    'SHARE_FISH': ('%s úlovků', '%s of the catches'),
    'SHARE_ORE': ('%s vytěžené rudy', '%s of the ore'),
    'MINED': ('Vytěženo', 'Mined'),
    'PIECES': ('%s kusů', '%s pieces'),
    'VEIN': ('Žíla', 'Vein'),
    'NEXT': ('DALŠÍ CÍL', 'NEXT GOAL'),
    'GOAL_FIRST_FISH': ('Chyť první rybu', 'Catch your first fish'),
    'GOAL_FIRST_MINE': ('Vytěž první rudu', 'Mine your first ore'),
    'GOAL_CHAPTER_PIECES': ('Kapitola %s: %s druhů, chybí %s ks', 'Chapter %s: %s species, %s pieces missing'),
    'GOAL_STREAK': ('Série: %d do nového rekordu', 'Streak: %d to a new record'),
    'GOAL_STREAK_FIRST': ('Série %d úlovků v řadě', 'A streak of %d catches'),
    'SPECIES_1': ('%d druh', '%d species'),
    'SPECIES_2': ('%d druhy', '%d species'),
    'SPECIES_5': ('%d druhů', '%d species'),
    'ORES_1': ('%d ruda', '%d ore'),
    'ORES_2': ('%d rudy', '%d ores'),
    'ORES_5': ('%d rud', '%d ores'),
    'HINT_TILE_FISH': ('%s · chyceno %s · nejdelší %s', '%s · caught %s · longest %s'),
    'HINT_TILE_ORE': ('%s · %s kusů', '%s · %s pieces'),
    'CASTS': ('Nahození', 'Casts'),
    'GAMES': ('Dokončené minihry', 'Finished minigames'),
    'CATCHES': ('Úlovky', 'Catches'),
    'NOTHING': ('"Nic"', '"Nothing"'),
    'ESCAPED': ('Utekly (obtížnost)', 'Escaped (difficulty)'),
    'ABANDONED': ('Nedokončené', 'Unfinished'),
    'STREAK_BEST': ('Nejdelší série bez "nic"', 'Longest streak without "nothing"'),
    'STREAK_NOW': ('Aktuální série', 'Current streak'),
    'TIME_WATER': ('Čas u vody', 'Time at the water'),
    'FISH_SUCCESS': ('Úspěšnost (úlovek z dokončené minihry)', 'Success rate (a catch of a finished minigame)'),
    'BY_SPECIES': ('Po druzích', 'By species'),
    'COL_SPECIES': ('Druh', 'Species'),
    'COL_LONGEST': ('Nejdelší', 'Longest'),
    'RUNS': ('Těžby', 'Mining runs'),
    'SUCCESSFUL': ('Úspěšné', 'Successful'),
    'ORE_TOTAL': ('Rudy celkem', 'Ores in total'),
    'TIME_VEIN': ('Čas u žil', 'Time at the veins'),
    'MINE_SUCCESS': ('Úspěšnost (úspěšné těžby ze všech)', 'Success rate (successful runs of all)'),
    'BY_VEIN': ('Po žilách', 'By vein'),
    'COL_ORE': ('Ruda', 'Ore'),
    'COL_AMOUNT': ('Získáno', 'Gained'),
    'NO_FISH': ('Zatím žádný úlovek.', 'No catch yet.'),
    'NO_ORE': ('Zatím žádná ruda.', 'No ore yet.'),
    'CHECK_GREAT': ('Skill check: výborně', 'Skill check: great'),
    'CHECK_GOOD': ('Skill check: dobře', 'Skill check: good'),
    'CHECK_MISS': ('Skill check: vedle', 'Skill check: missed'),
    'MINIGAME': ('Minihra těžby', 'Mining minigame'),
    'MINIGAME_NOTE_0': ('Těžba bez minihry. Bez trefy kruhu nepadají vzácné nálezy.',
                        'Mining without the minigame. No rare finds without a hit on the ring.'),
    'MINIGAME_NOTE_1': ('Klik na žílu ukáže kruh. Trefa ubere údery této těžby.',
                        'A click on a vein shows the ring. A hit takes swings off this mining.'),
    'MINIGAME_NOTE_2': ('Kruh se ukáže při kopání. Trefa zkrátí příští těžbu.',
                        'The ring shows while mining. A hit shortens the next mining.'),
    'MINIGAME_NOTE_3': ('Kruh během kopání, trefa zvedne výnos. Vzácné nálezy padají jen po trefě.',
                        'A ring while mining, a hit raises the yield. Rare finds drop only after a hit.'),
    'MINIGAME_PENDING': ('Čeká na potvrzení serveru...', 'Waiting for the server...'),
    'MODE_RARE_WOOD': ('Vzácné', 'Rare'),
    'MODE_SEG_0': ('Vypnuto', 'Off'),
    'MODE_SEG_1': ('A', 'A'),
    'MODE_SEG_2': ('B', 'B'),
    'MODE_SEG_3': ('Zapnuto', 'On'),
    'SUB_WOOD': ('sbírka %d / %d dřev · %s u stromů', 'collection %d / %d woods · %s at the trees'),
    'SUB_WOOD_NEW': ('sbírka %d / %d dřev', 'collection %d / %d woods'),
    'FIG_CUTS': ('sečí', 'cuts'),
    'FIG_WOOD': ('kusů dřeva', 'pieces of wood'),
    'FIG_TODAY': ('dnes', 'today'),
    'CH_WOOD_1': ('Běžná dřeva', 'Common woods'),
    'CH_WOOD_2': ('Vzácná dřeva', 'Rare woods'),
    'MINIGAME_WOOD_SHORT': ('MINIHRA SEKÁNÍ', 'WOODCUTTING MINIGAME'),
    'MARKS': ('%s značek', '%s marks'),
    'WOOD_MODE_SHORT_0': ('vypnuta', 'off'),
    'WOOD_MODE_SHORT_1': ('zapnuto - rytmický pruh', 'on - the rhythm bar'),
    'TIME_TREE_LINE': ('čisté seče %s · čas u stromů %s', 'clean cuts %s · time at the trees %s'),
    'UNKNOWN_WOOD': ('Pokácej ho a zapíše se sem', 'Cut it to record'),
    'UNKNOWN_WOOD_2': ('množství dřeva.', 'the amount of wood.'),
    'CUT': ('Nasekáno', 'Cut'),
    'SHARE_WOOD': ('%s nasekaného dřeva', '%s of the wood'),
    'TREE': ('Strom', 'Tree'),
    'TREE_TIER': ('%s (stupeň %d)', '%s (tier %d)'),
    'GOAL_FIRST_WOOD': ('Nasekej první dřevo', 'Cut your first wood'),
    'GOAL_TODAY': ('Dnes zbývá %s sečí', '%s cuts left today'),
    'TREES_1': ('%d strom', '%d tree'),
    'TREES_2': ('%d stromy', '%d trees'),
    'TREES_5': ('%d stromů', '%d trees'),
    'HINT_TILE_WOOD': ('%s · %s kusů', '%s · %s pieces'),
    'CUTS': ('Seče', 'Cuts'),
    'WOOD_TOTAL': ('Nasekané dřevo', 'Wood in total'),
    'TIME_TREE': ('Čas u stromů', 'Time at the trees'),
    'TODAY': ('Dnes / denní limit', 'Today / daily limit'),
    'TODAY_VALUE': ('%s / %s sečí', '%s / %s cuts'),
    'WCHECK_GREAT': ('Rytmus: výborně', 'Rhythm: great'),
    'WCHECK_GOOD': ('Rytmus: dobře', 'Rhythm: good'),
    'WCHECK_MISS': ('Rytmus: vedle', 'Rhythm: missed'),
    'WOOD_SUCCESS': ('Čisté seče (všechny značky výborně)', 'Clean cuts (every mark great)'),
    'BY_TREE': ('Po stromech', 'By tree'),
    'COL_WOOD': ('Dřevo', 'Wood'),
    'NO_WOOD': ('Zatím žádné dřevo.', 'No wood yet.'),
    'WOOD_MINIGAME': ('Minihra sekání', 'Woodcutting minigame'),
    'WOOD_NOTE_0': ('Sekání bez minihry, jako dosud.', 'Woodcutting without the minigame, as before.'),
    'WOOD_NOTE_1': ('Při sekání jede pruh se značkami. Trefa přidá dřevo této seče.',
                    'A bar with marks runs while cutting. A hit adds wood to this cut.'),
    'TIT_TITLE': ('Titul', 'Title'),
    'TIT_NONE': ('zatím žádný', 'none yet'),
    'TIT_NEXT': ('další: %s', 'next: %s'),
    'TIT_TOP': ('nejvyšší titul', 'the highest title'),
    'TIT_LEVEL': ('úroveň %s / %s', 'level %s / %s'),
    'TIT_BOOK_FISH': ('%s / %s úlovků', '%s / %s catches'),
    'TIT_BOOK_MINE': ('%s / %s úspěšných těžeb', '%s / %s successful runs'),
    'TIT_BOOK_WOOD': ('%s / %s sečí', '%s / %s cuts'),
    'TIT_NEED': ('úr. %d + %s', 'lv. %d + %s'),
    'TIT_EARNED': ('získáno', 'earned'),
    'TIT_WORN': ('nosí', 'worn'),
    'TIT_LOCKED': ('zamčeno', 'locked'),
    'TIT_OFF': ('Tituly jsou na tomto serveru vypnuté.', 'Titles are off on this server.'),
    'SKIN_HEAD_FISH': ('Vzhled prutu (skin, stupeň a síla zůstávají)', 'Rod look (a skin, the grade and power stay)'),
    'SKIN_HEAD_MINE': ('Vzhled krumpáče (skin, stupeň a síla zůstávají)',
                       'Pickaxe look (a skin, the grade and power stay)'),
    'SKIN_HEAD_WOOD': ('Vzhled sekery (skin, stupeň a síla zůstávají)', 'Axe look (a skin, the grade and power stay)'),
    'SKIN_NONE': ('Bez vzhledu', 'No look'),
    'SKIN_NEED_LEVEL': ('úroveň %d', 'level %d'),
    'SKIN_NEED_APEX': ('Mistr ve stromu', 'Master in the tree'),
    'SKIN_SOON': ('Vzhledy pro toto řemeslo připravujeme.', 'Looks for this craft are coming.'),
    'SIDE_CRAFTS': ('ŘEMESLA', 'CRAFTS'),
    'LEVEL_SHORT': ('úr. %d', 'lv. %d'),
    'SIDE_EXP': ('%s / %s EXP', '%s / %s EXP'),
    'SIDE_EXP_TOP': ('nejvyšší úroveň', 'the highest level'),
    'SIDE_TITLE': ('TITUL', 'TITLE'),
    'SIDE_NO_TITLE': ('Bez titulu', 'No title'),
    'SIDE_LOOK': ('Vzhled nástroje', 'Tool look'),
}

_failed = []


def Tr(key):
    """Player text: the locale table (localeInfo CRAFT_BOOK_<key>) or the Czech / English fallback."""
    czech, english = TEXTS.get(key, ('', ''))
    try:
        import localeInfo
        value = getattr(localeInfo, 'CRAFT_BOOK_' + key, None)
        if isinstance(value, str) and value:
            return value
    except Exception:
        pass
    try:
        import app
        return czech if app.GetLocalePath().replace('\\', '/').lower().endswith('/cz') else english
    except Exception:
        return czech


def LoadCraftIcons(lines):
    """{craft: (vnum, ...)} from the lines of CRAFT_ICON_TABLE; '#' comments and bad rows ignored."""
    icons = {}
    for line in lines:
        fields = [f.strip() for f in line.rstrip('\r\n').split('\t')]
        if not fields or not fields[0] or fields[0].startswith('#'):
            continue
        vnums = tuple(int(f) for f in fields[1:] if f.isdigit())
        if vnums:
            icons[fields[0]] = vnums
    return icons


def LoadCraftPages(lines):
    """{page: 'on' | 'soon'} from the lines of CRAFT_PAGE_TABLE; a page the table does not name is on."""
    pages = {}
    for line in lines:
        fields = [f.strip() for f in line.rstrip('\r\n').split('\t')]
        if len(fields) >= 2 and fields[0] and not fields[0].startswith('#') and fields[1] in ('on', 'soon'):
            pages[fields[0]] = fields[1]
    return pages


def ReadTextTable(path, load):
    try:
        import app
        handle = app.OpenTextFile(path)
        try:
            return load([app.GetTextFileLine(handle, i) for i in range(app.GetTextFileLineCount(handle))])
        finally:
            app.CloseTextFile(handle)
    except Exception:
        return load([])


def ReadBookModes():
    return ReadTextTable('locale/common/craft_book_modes.txt', M.LoadBookModes)


def ReadCraftIcons(path=CRAFT_ICON_TABLE):
    return ReadTextTable(path, LoadCraftIcons)


def ReadCraftPages(path=CRAFT_PAGE_TABLE):
    return ReadTextTable(path, LoadCraftPages)


def CraftIcon(craft, names=None, table=None):
    """The icon path of the item that stands for a craft ('' when the table or the item table has none)."""
    for vnum in (ReadCraftIcons() if table is None else table).get(craft, ()):
        icon = ItemInfo(vnum, names)[1]
        if icon:
            return icon
    return ''


def ItemInfo(vnum, cache=None):
    """(name, icon path) of an item vnum from the client item table; ('', '') when it is unknown."""
    if cache is not None and vnum in cache:
        return cache[vnum]
    name, icon = '', ''
    try:
        import item
        item.SelectItem(int(vnum))
        name = item.GetItemName() or ''
        icon = item.GetIconImageFileName() or ''
    except Exception:
        pass
    if cache is not None:
        cache[vnum] = (name, icon)
    return name, icon


def DataText(prefix, ident):
    """The name of an id the server sends (locale_game <prefix><ID>, e.g. CRAFT_TITLE_MISTR, CRAFT_SKIN_PRUTBAMBUS);
    the id itself when the locale does not know it."""
    try:
        import localeInfo
        value = getattr(localeInfo, prefix + ident.upper(), None)
        if value:
            return value
    except Exception:
        pass
    return ident


# --------------------------------------------------------------------------- request throttle
class Requester(object):
    """Sends one chat command at most once per ``gap`` seconds (the window asks on Open and when a page needs it)."""

    def __init__(self, command, gap=REQUEST_GAP):
        self.command = command
        self.gap = float(gap)
        self.last = None

    def Clock(self):
        import app
        return float(app.GetTime())

    def Send(self):
        import net
        net.SendChatPacket(self.command)

    def Request(self):
        try:
            now = self.Clock()
        except Exception:
            now = None
        if now is not None and self.last is not None and 0.0 <= now - self.last < self.gap:
            return False
        self.last = now
        self.Send()
        return True


REQUESTER = Requester(REQUEST)                      # the book and the statistics
MASTERY_REQUESTER = Requester(MM.REQUEST)           # the levels of the craft switch and the Strom page
TITLES_REQUESTER = Requester(TM.REQUEST)            # the Tituly a vzhled page


# --------------------------------------------------------------------------- small parts
def Label(parent, kit, text, x, y, h, role='text', color=T.INK_DIM, align='left'):
    """A top-aligned text line centred in a row of ``h`` px from ``y`` (uir1.CellTop)."""
    return uir1.Text(parent, text, x, y + uir1.CellTop(h, kit.font(role)), kit.font(role), color, align=align,
                     valign='top')


# The item icon in a box: the shared R1 helper (docs/ALTHEA_R1_KIT.md, Item slots).
FitIcon = uir1.FitIcon


class Meter(object):
    """Success meter: a dark well (R1 panel frame) with the red vein filled to the ratio."""

    def __init__(self, parent, x, y, w):
        self.w = int(w)
        self.frame = uir1.Frame(parent, x, y, self.w, METER_H, 'panel')
        self.fill = uir1.Layer(parent, x + 2, y, self.w - 4, METER_H)
        self.SetRatio(0.0)

    def SetRatio(self, ratio):
        self.ratio = max(0.0, min(1.0, float(ratio or 0.0)))
        self.fill.Apply(L.slider_fill(0, 0, int(round(self.ratio * (self.w - 4)))))

    def Show(self):
        self.frame.Show()
        self.fill.Show()

    def Hide(self):
        self.frame.Hide()
        self.fill.Hide()


class Page(ui.Window):
    """Not pickable container of one page (window coordinates)."""

    def __init__(self, parent, x=0, y=0, w=W, h=H):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))


class Counters(object):
    """The label / value rows of a statistics page, the success label with its percent and the meter under them."""

    def __init__(self, page, kit, labels, success_label):
        self.labels, self.values = [], []
        for index, text in enumerate(labels):
            y = ROWS_Y + index * ROW_PITCH
            self.labels.append(Label(page, kit, text, LEFT_X + 12, y, ROW_PITCH, 'text_s', T.INK_DIM))
            self.values.append(Label(page, kit, '', LEFT_X + LEFT_W, y, ROW_PITCH, 'text_s', T.IVORY, 'right'))
        y = ROWS_Y + len(labels) * ROW_PITCH + 6
        self.success = Label(page, kit, success_label, LEFT_X + 12, y, ROW_PITCH, 'text_xs', T.INK_DIM)
        self.percent = Label(page, kit, '', LEFT_X + LEFT_W, y, ROW_PITCH, 'text_s', T.IVORY, 'right')
        self.meter = Meter(page, LEFT_X + 12, y + ROW_PITCH + 2, LEFT_W - 12)
        self.bottom = y + ROW_PITCH + 2 + METER_H

    def SetValues(self, values, ratio):
        for line, value in zip(self.values, values):
            line.SetText(value)
            line.SetPackedFontColor(T.MUTED if value in ('0', '0 min') else T.IVORY)
        self.meter.SetRatio(ratio)
        self.percent.SetText(M.FormatPercent(ratio))
        self.percent.SetPackedFontColor(T.IVORY if ratio > 0 else T.MUTED)


class ListRow(object):
    """One table row: icon, name (shortened to its column), one or two right-aligned numbers."""

    def __init__(self, box, kit, y, two_numbers):
        self.y = y
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(box)
        self.icon.AddFlag('not_pick')
        self.icon_path = None
        self.name_w = (COUNT_RIGHT - 64 if two_numbers else LENGTH_RIGHT - 64) - NAME_X
        self.name = Label(box, kit, '', NAME_X, y, LIST_PITCH, 'text', T.INK)
        self.count = Label(box, kit, '', COUNT_RIGHT if two_numbers else LENGTH_RIGHT, y, LIST_PITCH, 'text',
                           T.IVORY, 'right')
        self.length = Label(box, kit, '', LENGTH_RIGHT, y, LIST_PITCH, 'text', T.INK_DIM, 'right') \
            if two_numbers else None
        self.Hide()

    def Set(self, icon, name, count, length=None):
        if icon:
            if icon != self.icon_path:
                FitIcon(self.icon, icon, ICON_X, self.y + (LIST_PITCH - ICON) // 2, ICON, ICON)
                self.icon_path = icon
            self.icon.Show()
        else:
            self.icon.Hide()
        self.name.Show()
        uir1.Fit(self.name, name, self.name_w)
        self.count.SetText(count)
        self.count.Show()
        if self.length is not None:
            self.length.SetText(length or '')
            self.length.Show()

    def Hide(self):
        for widget in (self.icon, self.name, self.count, self.length):
            if widget is not None:
                widget.Hide()


class Table(object):
    """The right panel of a statistics page: a section heading, column headings, LIST_ROWS rows and the R1 scroll
    bar (shown only when there are more rows than fit; the window forwards the mouse wheel)."""

    def __init__(self, page, kit, heading, columns, empty_text, two_numbers):
        self.frame = uir1.Frame(page, PANEL_X, PANEL_Y, PANEL_W, PANEL_H, 'panel')
        self.box = Page(page, PANEL_X, PANEL_Y, PANEL_W, PANEL_H)
        self.box.Show()
        box = self.box
        self.section = uir1.Section(box, kit, 12, 10, PANEL_W - 24, heading)
        font = kit.font('text_s')
        self.columns = []
        for text, x, align in columns:
            self.columns.append(uir1.Text(box, text, x, COLUMNS_Y, font, T.MUTED, align=align, valign='top'))
        self.rows = [ListRow(box, kit, LIST_Y + index * LIST_PITCH, two_numbers) for index in range(LIST_ROWS)]
        self.empty = uir1.Text(box, empty_text, PANEL_W // 2, LIST_Y + 40, kit.font('text'), T.MUTED, align='center',
                               valign='top')
        self.scroll = uir1.ScrollBar(kit)
        self.scroll.SetParent(box)
        self.scroll.SetPosition(SCROLL_X, LIST_Y)
        self.scroll.SetScrollBarSize(LIST_ROWS * LIST_PITCH)
        self.scroll.SetScrollEvent(self.OnScroll)
        self.scroll.Hide()
        self.items = []
        self.offset = 0

    def SetItems(self, items):
        """items: [(icon, name, count text, length text or None)] in display order."""
        self.items = list(items)
        overflow = max(0, len(self.items) - LIST_ROWS)
        self.offset = min(self.offset, overflow)
        if overflow:
            self.scroll.SetScrollBarSize(LIST_ROWS * LIST_PITCH)
            self.scroll.SetMiddleBarSize(float(LIST_ROWS) / len(self.items))
            self.scroll.SetScrollStep(1.0 / overflow)
            self.scroll.SetPos(float(self.offset) / overflow, False)
            self.scroll.Show()
        else:
            self.offset = 0
            self.scroll.Hide()
        if self.items:
            self.empty.Hide()
        else:
            self.empty.Show()
        self.Fill()

    def Overflow(self):
        return max(0, len(self.items) - LIST_ROWS)

    def Fill(self):
        for index, row in enumerate(self.rows):
            position = self.offset + index
            if position < len(self.items):
                row.Set(*self.items[position])
            else:
                row.Hide()

    def ScrollTo(self, offset):
        overflow = self.Overflow()
        offset = max(0, min(overflow, int(offset)))
        if offset != self.offset:
            self.offset = offset
            self.Fill()
        if overflow:
            self.scroll.SetPos(float(self.offset) / overflow, False)
        return self.offset

    def OnScroll(self):
        overflow = self.Overflow()
        if overflow:
            offset = int(round(self.scroll.GetPos() * overflow))
            if offset != self.offset:
                self.offset = offset
                self.Fill()

    def OnWheel(self, delta):
        if not self.Overflow():
            return False
        self.ScrollTo(self.offset + (-1 if delta > 0 else 1))
        return True


# --------------------------------------------------------------------------- the book parts
def Img(parent, path, x=0, y=0):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


def Tint(image, color):
    """Diffuse colour of an item icon (a dark silhouette for a species not found yet; white = the icon itself)."""
    try:
        image.SetDiffuseColor(*color)
    except Exception:
        try:
            image.SetAlpha(color[3])
        except Exception:
            pass


def Overline(page, kit, x, y, w, text):
    """A small section label with a quiet hairline after it (one text line high; the R1 Section is 28 px)."""
    label = uir1.Text(page, text, x, y, kit.font('text_xs'), T.INK_DIM, valign='top')
    rule = uir1.Divider(page, x + uir1.TextWidth(label) + 8, y + 9, max(0, w - uir1.TextWidth(label) - 8))
    return label, rule


class ChapterRow(uir1.Interactive):
    """One chapter of the left page: the seal with the numeral, the name, "8 / 10" and a thin bar; hover and selected
    backgrounds; a click opens it on the right page."""

    W, H = A.BOOK_ROW

    def __init__(self, page, kit, x, y, on_click):
        uir1.Interactive.__init__(self)
        self.SetParent(page)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.W, self.H)
        self.selected = False
        self.done = False
        self.SetEvent(on_click)
        self.hover = Img(self, ROOT + 'row_hover.png')
        self.select = Img(self, ROOT + 'row_selected.png')
        self.sealOpen = Img(self, ROOT + 'seal_open.png', 4, (self.H - A.SEAL) // 2)
        self.sealDone = Img(self, ROOT + 'seal_done.png', 4, (self.H - A.SEAL) // 2)
        self.numeral = uir1.Text(self, '', 4 + A.SEAL // 2, self.H // 2, kit.font('text_xs'), T.INK_DIM,
                                 align='center')
        self.name = uir1.Text(self, '', 32, 1, kit.font('text_s'), T.INK, valign='top')
        self.count = uir1.Text(self, '', self.W - 8, 2, kit.font('text_xs'), T.INK_DIM, align='right', valign='top')
        self.track = uir1.Rect(self, 32, self.H - 6, self.W - 40, 3, BAR_TRACK)
        self.fill = uir1.Rect(self, 32, self.H - 6, 1, 3, BAR_FILL)
        self.Show()
        self.paint()

    def Set(self, numeral, name, got, total):
        self.numeral.SetText(numeral)
        self.name.SetText(name)
        self.count.SetText('%d / %d' % (got, total))
        self.done = total > 0 and got >= total
        w = int(round((self.W - 40) * (float(got) / total if total else 0.0)))
        if w > 0:
            self.fill.SetSize(w, 3)
            self.fill.Show()
        else:
            self.fill.Hide()
        self.paint()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        if not hasattr(self, 'select'):
            return
        if self.selected:
            self.select.Show()
            self.hover.Hide()
        elif self.hovered:
            self.hover.Show()
            self.select.Hide()
        else:
            self.hover.Hide()
            self.select.Hide()
        if self.done:
            self.sealDone.Show()
            self.sealOpen.Hide()
        else:
            self.sealOpen.Show()
            self.sealDone.Hide()
        self.numeral.SetPackedFontColor(T.IVORY if (self.done or self.selected) else T.INK_DIM)
        self.name.SetPackedFontColor(T.IVORY if self.selected else T.INK)

    def OnMouseLeftButtonUp(self):
        if self.enabled and self.callback:
            self.callback()
        return True


class Tile(uir1.Interactive):
    """One species / vein of the right page: the icon (a dark silhouette until found), its count, hover and selected
    frames; a click selects it, a hover shows a one-line hint."""

    def __init__(self, page, kit, x, y, on_click):
        uir1.Interactive.__init__(self)
        self.kit = kit
        self.SetParent(page)
        self.SetPosition(int(x), int(y))
        self.SetSize(TILE, TILE)
        self.selected = False
        self.vnum = None
        self.hint = ''
        self.SetEvent(on_click)
        self.frame = Img(self, ROOT + 'tile.png')
        self.frameHover = Img(self, ROOT + 'tile_hover.png')
        self.frameSelected = Img(self, ROOT + 'tile_selected.png')
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon_path = None
        self.count = uir1.Text(self, '', TILE - 4, TILE - 17, kit.font('text_xs'), T.INK, align='right', valign='top',
                               outline=True)
        self.Show()
        self.paint()

    def Set(self, vnum, icon, found, count_text, hint):
        self.vnum = vnum
        self.hint = hint
        if icon:
            if icon != self.icon_path:
                FitIcon(self.icon, icon, (TILE - ICON) // 2, (TILE - ICON) // 2, ICON, ICON)
                self.icon_path = icon
            Tint(self.icon, (1.0, 1.0, 1.0, 1.0) if found else SILHOUETTE)
            self.icon.Show()
        else:
            self.icon.Hide()
        self.count.SetText(count_text if found else '')
        self.Show()

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
        elif self.hovered:
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


class BookView(Page):
    """The two pages of the book for the selected craft (the window fills them in Refresh)."""

    def __init__(self, window, kit):
        Page.__init__(self, window)
        self.window = window
        page = self
        # ---- left page
        self.leftFrame = uir1.Frame(page, LEFT_PAGE_X, BOOK_Y, PAGE_W, BOOK_H, 'panel')
        x, w = LEFT_PAGE_X + 12, PAGE_W - 24
        self.emblem = ui.ExpandedImageBox()             # the craft's tool icon (CRAFT_ICON_TABLE)
        self.emblem.SetParent(page)
        self.emblem.AddFlag('not_pick')
        self.emblem.Hide()
        self.emblemCraft = None
        self.title = uir1.Text(page, '', x + A.EMBLEM + 10, EMBLEM_Y + 1, kit.font('text_b'), T.IVORY, valign='top')
        self.sub = uir1.Text(page, '', x + A.EMBLEM + 10, EMBLEM_Y + 24, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.figuresFrame = uir1.Frame(page, x - 4, FIGURES_Y, w + 8, FIGURES_H, 'panel')
        self.figures = []
        for index in range(3):
            cx = x + w * (2 * index + 1) // 6
            value = uir1.Text(page, '', cx, FIGURES_Y + 4, kit.font('text_b'), T.IVORY, align='center', valign='top')
            label = uir1.Text(page, '', cx, FIGURES_Y + 24, kit.font('text_xs'), T.INK_DIM, align='center',
                              valign='top')
            self.figures.append((value, label))
            if index:
                uir1.Rect(page, x + w * index // 3, FIGURES_Y + 8, 1, FIGURES_H - 16, 0x302C2A)
        self.chaptersLabel = Overline(page, kit, x, CHAPTERS_Y, w, Tr('CHAPTERS'))
        self.rows = []
        for index in range(3):
            row = ChapterRow(page, kit, LEFT_PAGE_X + 8, ROWS_TOP + index * CHAPTER_PITCH,
                             lambda index=index: window.SelectChapter(index))
            self.rows.append(row)
        # records (fishing)
        self.recordsLabel = Overline(page, kit, x, BOTTOM_Y, w, Tr('RECORDS'))
        self.records = []
        for index, key in enumerate(('REC_BIGGEST', 'REC_MOST', 'REC_RAREST')):
            y = BOTTOM_Y + 16 + index * RECORD_PITCH
            well = Img(page, ROOT + 'well_small.png', x, y)
            icon = ui.ExpandedImageBox()
            icon.SetParent(page)
            icon.AddFlag('not_pick')
            label = uir1.Text(page, Tr(key), x + 32, y + 3, kit.font('text_xs'), T.INK_DIM, valign='top')
            name = uir1.Text(page, '', x + 112, y + 3, kit.font('text_xs'), T.INK, valign='top')
            value = uir1.Text(page, '', x + w, y + 3, kit.font('text_xs'), T.IVORY, align='right', valign='top')
            self.records.append([well, icon, label, name, value, None])
        self.recordsEmpty = uir1.Text(page, Tr('REC_EMPTY'), x, BOTTOM_Y + 20, kit.font('text_xs'), T.INK_DIM,
                                      valign='top')
        self.recordsHint = uir1.Text(page, Tr('REC_EMPTY_HINT'), x, BOTTOM_Y + 40, kit.font('text_xs'), T.MUTED,
                                     valign='top')
        # minigame (mining)
        self.miniLabel = Overline(page, kit, x, BOTTOM_Y, w, Tr('MINIGAME_SHORT'))
        self.miniWoodLabel = Overline(page, kit, x, BOTTOM_Y, w, Tr('MINIGAME_WOOD_SHORT'))
        self.miniRings = uir1.Text(page, '', x, BOTTOM_Y + 18, kit.font('text_xs'), T.INK, valign='top')
        self.miniMode = uir1.Text(page, '', x + w, BOTTOM_Y + 18, kit.font('text_xs'), T.INK_DIM, align='right',
                                  valign='top')
        self.miniTrack = uir1.Rect(page, x, BOTTOM_Y + 40, w, 5, 0x141313)
        self.miniParts = [uir1.Rect(page, x, BOTTOM_Y + 41, 1, 3, color) for color in (0xD30D0E, 0xA39C94, 0x4A4542)]
        self.miniLegend = []
        for color in (0xD30D0E, 0xA39C94, 0x4A4542):
            dot = uir1.Rect(page, x, BOTTOM_Y + 56, 6, 6, color)
            text = uir1.Text(page, '', x, BOTTOM_Y + 50, kit.font('text_xs'), T.INK_DIM, valign='top')
            self.miniLegend.append((dot, text))
        self.miniTime = uir1.Text(page, '', x, BOTTOM_Y + 70, kit.font('text_xs'), T.INK_DIM, valign='top')
        # ---- right page
        self.rightFrame = uir1.Frame(page, RIGHT_PAGE_X, BOOK_Y, PAGE_W, BOOK_H, 'panel')
        rx, rw = RIGHT_PAGE_X + 12, PAGE_W - 24
        self.chapterTitle = uir1.Text(page, '', rx, BOOK_Y + 8, kit.font('text'), T.IVORY, valign='top')
        self.chapterCount = uir1.Text(page, '', rx + rw, BOOK_Y + 10, kit.font('text_xs'), T.INK_DIM, align='right',
                                      valign='top')
        self.modeSwitch = uir1.Segment(page, kit,
            ((False, Tr('MODE_NORMAL')), (True, Tr('MODE_GLOWING'))),
            ui.__mem_func__(window.SelectBookMode), font=kit.font('text_xs'), width=T.CRAFT_BOOK_MODE_W,
            height=T.CRAFT_BOOK_MODE_H)
        self.modeSwitch.SetPosition(rx + rw - T.CRAFT_BOOK_COUNT_W - T.CRAFT_BOOK_MODE_W,
                                    BOOK_Y + T.CRAFT_BOOK_MODE_Y)
        self.modeSwitch.Hide()
        gx = RIGHT_PAGE_X + (PAGE_W - (TILE_COLS * TILE + (TILE_COLS - 1) * TILE_GAP)) // 2
        self.tiles = []
        for index in range(2 * TILE_COLS):
            tile = Tile(page, kit, gx + (index % TILE_COLS) * (TILE + TILE_GAP),
                        TILES_Y + (index // TILE_COLS) * (TILE + TILE_GAP),
                        lambda index=index: window.SelectTile(index))
            self.tiles.append(tile)
        self.detailLabel = Overline(page, kit, rx, DETAIL_Y, rw, Tr('SELECTED'))
        self.detailWell = Img(page, ROOT + 'tile.png', rx, DETAIL_Y + 16)
        self.detailIcon = ui.ExpandedImageBox()
        self.detailIcon.SetParent(page)
        self.detailIcon.AddFlag('not_pick')
        self.detailName = uir1.Text(page, '', rx + 60, DETAIL_Y + 14, kit.font('text_s'), T.IVORY, valign='top')
        self.detailRows = []
        for index in range(3):
            y = DETAIL_Y + 34 + index * 15
            key = uir1.Text(page, '', rx + 60, y, kit.font('text_xs'), T.INK_DIM, valign='top')
            value = uir1.Text(page, '', rx + rw, y, kit.font('text_xs'), T.INK, align='right', valign='top')
            self.detailRows.append((key, value))
        self.goalsLabel = Overline(page, kit, rx, GOALS_Y, rw, Tr('NEXT'))
        self.goals = []
        for index in range(3):
            y = GOALS_Y + 18 + index * GOAL_PITCH
            dot = uir1.Rect(page, rx + 2, y + 6, 5, 5, 0x961C1A)
            text = uir1.Text(page, '', rx + 12, y, kit.font('text_xs'), T.INK, valign='top')
            self.goals.append((dot, text))

    # ------------------------------------------------------------------ fill
    def ShowPart(self, widgets, show):
        for widget in widgets:
            if widget is None:
                continue
            if show:
                widget.Show()
            else:
                widget.Hide()

    def SetRecords(self, rows):
        """rows: [(icon path, name, value)] or [] (no catch yet: the hint instead)."""
        self.ShowPart(self.recordsLabel, True)
        self.ShowPart(self.miniParts + [self.miniTrack, self.miniRings, self.miniMode, self.miniTime] +
                      [w for pair in self.miniLegend for w in pair] + list(self.miniLabel) +
                      list(self.miniWoodLabel), False)
        empty = not rows
        self.ShowPart((self.recordsEmpty, self.recordsHint), empty)
        for index, record in enumerate(self.records):
            well, icon, label, name, value, unused = record
            if index < len(rows):
                path, text, number = rows[index]
                if path and path != record[5]:
                    FitIcon(icon, path, well.GetLocalPosition()[0] + 1, well.GetLocalPosition()[1] + 1,
                            A.SMALL_WELL - 2, A.SMALL_WELL - 2)
                    record[5] = path
                uir1.Fit(name, text, PAGE_W - 24 - 112 - 52)
                value.SetText(number)
                self.ShowPart((well, label, name, value), True)
                self.ShowPart((icon,), bool(path))
            else:
                self.ShowPart((well, icon, label, name, value), False)

    def SetMiningSummary(self, time_text):
        self.SetRecords([])
        self.ShowPart(list(self.recordsLabel) + [self.recordsEmpty, self.recordsHint], False)
        self.miniTime.SetText(time_text)
        self.miniTime.Show()

    def SetMinigame(self, rings, mode_text, parts, legend, time_text, wood=False):
        """The minigame summary of mining (or of woodcutting with ``wood``: its own heading)."""
        self.ShowPart(list(self.recordsLabel) + [self.recordsEmpty, self.recordsHint] +
                      [w for record in self.records for w in record[:5]], False)
        self.ShowPart(list(self.miniWoodLabel if wood else self.miniLabel) +
                      [self.miniTrack, self.miniRings, self.miniMode, self.miniTime], True)
        self.ShowPart(list(self.miniLabel if wood else self.miniWoodLabel), False)
        self.miniRings.SetText(rings)
        self.miniMode.SetText(mode_text)
        self.miniTime.SetText(time_text)
        x, w = LEFT_PAGE_X + 12, PAGE_W - 24
        total = float(sum(parts))
        px = x + 1
        for index, (rect, part) in enumerate(zip(self.miniParts, parts)):
            pw = int(round((w - 2) * part / total)) if total else 0
            if index == len(parts) - 1 and total:
                pw = x + w - 1 - px
            if pw > 1:
                rect.SetPosition(px, BOTTOM_Y + 41)
                rect.SetSize(pw - 1, 3)
                rect.Show()
            else:
                rect.Hide()
            px += max(0, pw)
        lx = x
        for (dot, text), label in zip(self.miniLegend, legend):
            dot.SetPosition(lx, BOTTOM_Y + 56)
            text.SetText(label)
            text.SetPosition(lx + 10, BOTTOM_Y + 50)
            dot.Show()
            text.Show()
            lx += 10 + uir1.TextWidth(text) + 14


class Badge(object):
    """The R1 badge: the red circle with the white number (the bottom bar art althea_r1_lista/badge, as the DPS meter
    and the task bar draw it); hidden at 0."""

    H = 13
    MAX_DIGITS = 2

    def __init__(self, parent):
        import uir1listaart as art
        self.art = art
        self.H = art.BADGE_H
        self.pill = Img(parent, art.ROOT + 'badge/count_1.png')
        self.digits = [Img(self.pill, art.ROOT + 'badge/digit_0.png') for unused in range(self.MAX_DIGITS)]
        self.value = 0
        self.pill.Hide()

    def SetValue(self, value):
        art = self.art
        value = max(0, min(int(value or 0), 10 ** self.MAX_DIGITS - 1))
        self.value = value
        label = '%d' % value
        self.pill.LoadImage(art.ROOT + 'badge/count_%d.png' % len(label))
        for index, image in enumerate(self.digits):
            if index < len(label):
                image.LoadImage(art.ROOT + 'badge/digit_%s.png' % label[index])
                image.SetPosition(art.BADGE_DIGIT_AT[0] + index * (art.DIGIT[0] + 1), art.BADGE_DIGIT_AT[1])
                image.Show()
            else:
                image.Hide()

    def Width(self):
        return self.art.BADGE_W[str(len('%d' % self.value))]

    def Place(self, x, y, shown):
        self.pill.SetPosition(int(x), int(y))
        if shown and self.value:
            self.pill.Show()
        else:
            self.pill.Hide()

    def IsShow(self):
        return self.pill.IsShow()


class SideRow(object):
    """One row of the side column: the label left, the value right, the thin bar of the chapter rows under them."""

    def __init__(self, parent, kit, y):
        self.label = uir1.Text(parent, '', SIDE_X, y, kit.font('text_xs'), T.INK, valign='top')
        self.value = uir1.Text(parent, '', SIDE_X + SIDE_W, y, kit.font('text_xs'), T.IVORY, align='right',
                               valign='top')
        self.track = uir1.Rect(parent, SIDE_X, y + SIDE_BAR_Y, SIDE_W, 3, BAR_TRACK)
        self.fill = uir1.Rect(parent, SIDE_X, y + SIDE_BAR_Y, 1, 3, BAR_FILL)

    def Set(self, y, label, value, ratio):
        self.value.SetText(value)
        self.value.SetPosition(SIDE_X + SIDE_W, y)
        uir1.Fit(self.label, label, SIDE_W - uir1.TextWidth(self.value) - 8)
        self.label.SetPosition(SIDE_X, y)
        self.track.SetPosition(SIDE_X, y + SIDE_BAR_Y)
        w = int(round(SIDE_W * max(0.0, min(1.0, ratio))))
        self.fill.SetPosition(SIDE_X, y + SIDE_BAR_Y)
        self.fill.SetSize(max(1, w), 3)
        for widget in (self.label, self.value, self.track):
            widget.Show()
        if w > 0:
            self.fill.Show()
        else:
            self.fill.Hide()

    def Hide(self):
        for widget in (self.label, self.value, self.track, self.fill):
            widget.Hide()


class CraftRow(uir1.Interactive):
    """One craft of the side column (sidebar B): the emblem, the name, "úr. 12", the thin EXP bar of the chapter
    rows with "300 / 1 080 EXP" under it and the R1 badge of the free tree points; the R1 list band (hover lighter,
    the selected craft the dark well with the red select line); a click selects the craft like the craft switch.
    A craft the client cannot open yet (woodcutting without its controller) is dimmed with "Připravujeme"."""

    H = CRAFT_ROW_H
    TEXT_X = A.EMBLEM + 12

    def __init__(self, parent, kit, window, y, craft, on_click):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(RAIL_X, int(y))
        self.SetSize(RAIL_W, self.H)
        self.window = window
        self.craft = craft
        self.selected = False
        self.band = uir1.Band(self, 0, 0, RAIL_W, self.H - 1)            # before the texts
        top = (self.H - A.EMBLEM) // 2
        self.emblem = ui.ExpandedImageBox()     # the craft's tool icon (CRAFT_ICON_TABLE)
        self.emblem.SetParent(self)
        self.emblem.AddFlag('not_pick')
        icon = CraftIcon(craft, window.names, window.craftIcons)
        if icon:
            FitIcon(self.emblem, icon, 4, top, A.EMBLEM, A.EMBLEM)
            self.emblem.Show()
        right = RAIL_W - 8
        self.name = uir1.Text(self, '', self.TEXT_X, 5, kit.font('text_s'), T.INK, valign='top')
        self.level = uir1.Text(self, '', right, 6, kit.font('text_xs'), T.INK_DIM, align='right', valign='top')
        self.track = uir1.Rect(self, self.TEXT_X, 24, right - self.TEXT_X, 3, BAR_TRACK)
        self.fill = uir1.Rect(self, self.TEXT_X, 24, 1, 3, BAR_FILL)
        self.exp = uir1.Text(self, '', self.TEXT_X, 30, kit.font('text_xs'), T.MUTED, valign='top')
        self.badge = Badge(self)
        self.SetEvent(on_click)
        self.paint()
        self.Show()

    def Set(self, name, craft, locked):
        """``craft``: the craftmasterymodel craft (None before the snapshot); ``locked``: not open in this client."""
        number = M.FormatNumber
        right = RAIL_W - 8
        self.level.SetText(Tr('LEVEL_SHORT') % craft.level if craft is not None and not locked else '')
        uir1.Fit(self.name, name, right - self.TEXT_X - uir1.TextWidth(self.level) - 8)
        if locked or craft is None:
            self.track.Hide()
            self.fill.Hide()
            self.badge.SetValue(0)
            self.badge.Place(0, 0, False)
            self.exp.SetText(Tr('SOON') if locked else '')
            self.exp.Show()
        else:
            top = craft.level >= craft.max_level or not craft.exp_next
            ratio = 1.0 if top else M.Ratio(craft.exp_into, craft.exp_next)
            w = int(round((right - self.TEXT_X) * ratio))
            self.track.Show()
            self.fill.SetSize(max(1, w), 3)
            if w > 0:
                self.fill.Show()
            else:
                self.fill.Hide()
            self.badge.SetValue(craft.Free())
            self.badge.Place(right - self.badge.Width(), 30 + (self.window.kit.cell('text_xs') - self.badge.H) // 2,
                             True)
            room = right - self.TEXT_X - (self.badge.Width() + 6 if self.badge.IsShow() else 0)
            uir1.Fit(self.exp, Tr('SIDE_EXP_TOP') if top else
                     Tr('SIDE_EXP') % (number(craft.exp_into), number(craft.exp_next)), room)
            self.exp.Show()
        if locked:
            self.Disable()
        self.paint()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        if not hasattr(self, 'exp'):
            return
        hover = self.state() in ('hover', 'pressed')
        self.band.SetState('selected' if self.selected else ('hover' if hover else 'normal'))
        self.name.SetPackedFontColor(T.IVORY if self.selected or hover else (T.INK if self.enabled else T.MUTED))
        try:
            self.emblem.SetAlpha(1.0 if self.enabled else 0.4)
        except Exception:
            pass


class SideColumn(object):
    """The side column under the page tabs (sidebar variant B, "řemesla pod sebou", like the profession lists of
    WoW / OSRS / GW2): "Řemesla" - every craft with its level, EXP and free tree points, the selected one with the
    red select line (a click selects it, the craft switch follows) - then "Titul": the worn title (the server's, of
    the best craft), the next one with the way of the selected craft to it, and the chosen tool look."""

    def __init__(self, window, kit):
        self.window = window
        parent = window
        self.craftsLabel = Overline(parent, kit, SIDE_X, CRAFTS_Y, SIDE_W, Tr('SIDE_CRAFTS'))
        self.crafts = [CraftRow(parent, kit, window, CRAFT_ROWS_Y + index * CRAFT_PITCH, craft,
                                lambda craft=craft: window.SelectCraft(craft))
                       for index, (craft, unused) in enumerate(CRAFTS)]
        self.titleLabel = Overline(parent, kit, SIDE_X, TITLE_Y, SIDE_W, Tr('SIDE_TITLE'))
        self.title = uir1.Text(parent, '', SIDE_X, TITLE_Y + 18, kit.font('text_b'), T.IVORY, valign='top')
        self.next = SideRow(parent, kit, TITLE_Y + 38)
        self.look = uir1.Text(parent, '', SIDE_X, LOOK_Y, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.lookValue = uir1.Text(parent, '', SIDE_X + SIDE_W, LOOK_Y, kit.font('text_xs'), T.INK, align='right',
                                   valign='top')

    def Refresh(self):
        window = self.window
        mastery = window.MasteryModel().snapshot
        for index, (row, (craft, key)) in enumerate(zip(self.crafts, CRAFTS)):
            data = mastery.Craft(index) if mastery is not None and mastery.enabled else None
            row.Set(Tr(key), data if data is not None and data.enabled else None,
                    craft == 'wood' and window.wood is None)
            row.SetSelected(craft == window.craft)
        index = window.CraftIndex()
        titles = window.TitlesModel().snapshot
        soon = window.PageSoon('titles')
        if soon or titles is None or not (titles.enabled and titles.titles):
            self.title.SetText(Tr('SOON') if soon else (Tr('LOADING') if titles is None else Tr('SIDE_NO_TITLE')))
            self.title.SetPackedFontColor(T.INK_DIM)
            self.next.Hide()
            self.look.Hide()
            self.lookValue.Hide()
            return
        current = titles.Current()
        uir1.Fit(self.title, DataText('CRAFT_TITLE_', current.id) if current else Tr('SIDE_NO_TITLE'), SIDE_W)
        self.title.SetPackedFontColor(T.IVORY if current else T.INK_DIM)
        following = titles.Next()
        if following is None:
            self.next.Set(TITLE_Y + 38, Tr('TIT_TOP'), '', 1.0)
        else:
            craft = mastery.Craft(index) if mastery is not None else None
            level = craft.level if craft is not None else 0
            ratio = min(M.Ratio(level, following.level) if following.level else 1.0,
                        M.Ratio(titles.BookCount(index), following.Book(index)) if following.Book(index) else 1.0)
            self.next.Set(TITLE_Y + 38, Tr('TIT_NEXT') % DataText('CRAFT_TITLE_', following.id),
                          M.FormatPercent(ratio), ratio)
        if not titles.Skins(index):
            self.look.Hide()
            self.lookValue.Hide()
            return
        chosen = titles.Chosen(index)
        self.lookValue.SetText(DataText('CRAFT_SKIN_', chosen) if chosen else Tr('SKIN_NONE'))
        uir1.Fit(self.look, Tr('SIDE_LOOK'), SIDE_W - uir1.TextWidth(self.lookValue) - 8)
        self.look.Show()
        self.lookValue.Show()


class RailTab(uir1.Interactive):
    """One page tab of the rail: the R1 list band (hover lighter, the selected one the dark well with the red select
    line under it) and the label; a click selects the page."""

    def __init__(self, parent, kit, x, y, text, on_click):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(RAIL_W, RAIL_ROW)
        self.selected = False
        self.band = uir1.Band(self, 0, 0, RAIL_W, RAIL_ROW - 1)          # before the label
        self.label = uir1.RowText(self, '', RAIL_TEXT_X, RAIL_ROW, kit.font('text'), T.INK_DIM)
        uir1.Fit(self.label, text, RAIL_W - 2 * RAIL_TEXT_X)
        self.SetEvent(on_click)
        self.paint()
        self.Show()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        self.paint()

    def paint(self):
        if not hasattr(self, 'label'):
            return
        state = self.state()
        hover = state in ('hover', 'pressed')
        self.band.SetState('selected' if self.selected else ('hover' if hover else 'normal'))
        self.label.SetPackedFontColor(T.DISABLED if state == 'disabled' else
                                      (T.IVORY if self.selected or hover else T.INK_DIM))


class CraftBookWindow(uir1.Window):
    def __init__(self, model, mining=None, wood=None):
        self.built = False
        self.model = model
        self.mining = mining                    # uiminingcheck.MiningCheck: the minigame switch (None: no switch)
        self.wood = wood                        # uiwoodcheck.WoodCheck: the Dřevorubec tab and its switch (None: locked)
        self.kit = uir1.Kit()
        uir1.Window.__init__(self, self.kit, W, H, Tr('TITLE'))
        self.names = {}
        self.craftIcons = ReadCraftIcons()          # craft -> tool item vnums (CRAFT_ICON_TABLE)
        self.pages = ReadCraftPages()               # page -> on | soon (CRAFT_PAGE_TABLE)
        self.tab = 'overview'
        self.craft = 'fishing'
        self.chapter = {'fishing': 0, 'mining': 0, 'wood': 0}
        self.selected = {'fishing': None, 'mining': None, 'wood': None}
        self.shown_revision = None
        self.positioned = False
        self.bookModes = ReadBookModes()
        self.bookMode = dict((craft, False) for craft, unused in CRAFTS)
        self.modeRows = []
        self.pendingRequests = {}
        self.awaitingRequests = {}
        self.liveTicker = None
        veins, self.vein_ores = self.Veins()

    @staticmethod
    def Veins():
        try:
            import servergamedata
            return tuple(servergamedata.MINING_VEINS), dict(getattr(servergamedata, 'MINING_VEIN_ORES', {}))
        except Exception:
            return (), {}

    # ------------------------------------------------------------------ build
    def Build(self):
        import uicraftmastery
        kit = self.kit
        self.side = SideColumn(self, kit)
        self.rail = []
        for index, (tab, key) in enumerate(TABS):
            self.rail.append(RailTab(self, kit, RAIL_X, TABS_Y + index * RAIL_PITCH, Tr(key),
                                     lambda tab=tab: self.SelectTab(tab)))
        for (tab, unused), row in zip(TABS, self.rail):
            if self.PageSoon(tab):                  # shown, locked: the hint says "Připravujeme"
                row.Disable()
                row.SetHoverEvent(lambda row=row: uir1.ShowHint(kit, row, Tr('SOON')))
                row.OnMouseOverOut = lambda row=row: (uir1.Interactive.OnMouseOverOut(row), uir1.HideHint())
        self.hairline = uir1.Rect(self, SPLIT_X, TABS_Y, 1, H - EDGE - TABS_Y, T.LINE)
        self.crafts = uir1.Segment(self, kit, [(craft, Tr(key)) for craft, key in CRAFTS], self.SelectCraft,
                                   width=AREA_W)
        self.crafts.SetPosition(AREA_X, TABS_Y)
        wood = self.crafts.cells[2]
        if self.wood is None:
            wood.Disable()
            wood.SetHoverEvent(lambda: uir1.ShowHint(kit, wood, Tr('SOON')))
            wood.OnMouseOverOut = lambda: (uir1.Interactive.OnMouseOverOut(wood), uir1.HideHint())
        self.book = BookView(self, kit)
        self.BuildStats()
        self.masteryPage = uicraftmastery.MasteryView(self, kit)
        self.titlesPage = uicraftmastery.TitlesView(self, kit)
        self.liveTicker = ui.Window()
        self.liveTicker.SetParent(self)
        self.liveTicker.AddFlag('not_pick')
        self.liveTicker.SetSize(0, 0)
        self.liveTicker.OnUpdate = ui.__mem_func__(self.LiveTick)
        self.liveTicker.Hide()
        self.built = True
        self.SelectTab('overview')
        self.SelectCraft('fishing')

    def BuildMinigame(self, page, y):
        """The temporary switch of the mining skill check (owner 7. 10.: may look plain, it is a trial)."""
        kit = self.kit
        x = LEFT_X + 12
        self.minigame = Overline(page, kit, x, y, LEFT_W - 12, Tr('MINIGAME').upper())
        self.minigameMode = uir1.Segment(page, kit, [(mode, Tr('MODE_SEG_%d' % mode)) for mode, unused in
                                                     self.mining.ModeLabels()], self.SelectMiningMode,
                                         font=kit.font('text_xs'), width=LEFT_W - 12)
        self.minigameMode.SetPosition(x, y + 18)
        self.minigamePending = uir1.Text(page, Tr('MINIGAME_PENDING'), x, y + 18 + T.SEG_H + 20, kit.font('text_xs'),
                                         T.MUTED, valign='top')
        self.minigameNote = uir1.Text(page, '', x, y + 18 + T.SEG_H + 4, kit.font('text_xs'), T.INK_DIM,
                                      valign='top')
        self.minigameNote2 = uir1.Text(page, '', x, y + 18 + T.SEG_H + 20, kit.font('text_xs'), T.INK_DIM,
                                       valign='top')
        self.RefreshMiningMode()

    def SelectMiningMode(self, mode):
        if self.mining is not None:
            self.mining.SetMode(mode)
        self.RefreshMiningMode()

    def RefreshMiningMode(self):
        """The switch shows the chosen mode, what it does or that the server has not confirmed it yet."""
        if self.minigame is None or self.mining is None:
            return
        mode = self.mining.mode
        self.minigameMode.SetValue(mode)
        note = Tr('MINIGAME_NOTE_%d' % mode) if mode in (0, 1, 2, 3) else ''
        first, dot, rest = note.partition('. ')
        uir1.Fit(self.minigameNote, first + ('.' if dot else ''), LEFT_W - 12)
        uir1.Fit(self.minigameNote2, rest, LEFT_W - 12)
        self.minigameNote.Show()
        if self.mining.Pending():                   # the second line waits for the server's word
            self.minigameNote2.Hide()
            self.minigamePending.Show()
        else:
            self.minigamePending.Hide()
            self.minigameNote2.Show()

    def BuildWoodMinigame(self, page, y):
        """The switch of the woodcutting rhythm bar (Vypnuto | Zapnuto), like the mining one."""
        kit = self.kit
        x = LEFT_X + 12
        self.woodMinigame = Overline(page, kit, x, y, LEFT_W - 12, Tr('WOOD_MINIGAME').upper())
        self.woodMode = uir1.Segment(page, kit, [(mode, Tr('MODE_SEG_%d' % (3 if mode else 0))) for mode, unused in
                                                 self.wood.ModeLabels()], self.SelectWoodMode,
                                     font=kit.font('text_xs'), width=LEFT_W - 12)
        self.woodMode.SetPosition(x, y + 18)
        self.woodPending = uir1.Text(page, Tr('MINIGAME_PENDING'), x, y + 18 + T.SEG_H + 20, kit.font('text_xs'),
                                     T.MUTED, valign='top')
        self.woodNote = uir1.Text(page, '', x, y + 18 + T.SEG_H + 4, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.woodNote2 = uir1.Text(page, '', x, y + 18 + T.SEG_H + 20, kit.font('text_xs'), T.INK_DIM, valign='top')
        self.RefreshWoodMode()

    def SelectWoodMode(self, mode):
        if self.wood is not None:
            self.wood.SetMode(mode)
        self.RefreshWoodMode()

    def RefreshWoodMode(self, book=True):
        """The woodcutting switch shows the chosen mode, what it does or that the server has not confirmed it yet;
        ``book``: the Dřevorubec book page names the mode too."""
        if getattr(self, 'woodMinigame', None) is None or self.wood is None:
            return
        mode = self.wood.mode
        self.woodMode.SetValue(mode)
        note = Tr('WOOD_NOTE_%d' % mode) if mode in (0, 1) else ''
        first, dot, rest = note.partition('. ')
        uir1.Fit(self.woodNote, first + ('.' if dot else ''), LEFT_W - 12)
        uir1.Fit(self.woodNote2, rest, LEFT_W - 12)
        self.woodNote.Show()
        if self.wood.Pending():
            self.woodNote2.Hide()
            self.woodPending.Show()
        else:
            self.woodPending.Hide()
            self.woodNote2.Show()
        if book and self.built and self.craft == 'wood':
            self.RefreshBook()

    def BuildStats(self):
        kit = self.kit
        page = self.stats = Page(self)
        self.fish_page = Page(page)
        self.fish_counters = Counters(self.fish_page, kit, [Tr(key) for key in (
            'CASTS', 'GAMES', 'CATCHES', 'NOTHING', 'ESCAPED', 'ABANDONED', 'STREAK_BEST', 'STREAK_NOW',
            'TIME_WATER')], Tr('FISH_SUCCESS'))
        self.fish_table = Table(self.fish_page, kit, Tr('BY_SPECIES'), (
            (Tr('COL_SPECIES'), NAME_X, 'left'), (Tr('CATCHES'), COUNT_RIGHT, 'right'),
            (Tr('COL_LONGEST'), LENGTH_RIGHT, 'right')), Tr('NO_FISH'), True)
        self.mine_page = Page(page)
        mine_keys = ['RUNS', 'SUCCESSFUL', 'ORE_TOTAL', 'TIME_VEIN']
        if self.mining is not None:
            mine_keys.extend(('CHECK_GREAT', 'CHECK_GOOD', 'CHECK_MISS'))
        self.mine_counters = Counters(self.mine_page, kit, [Tr(key) for key in mine_keys], Tr('MINE_SUCCESS'))
        self.mine_table = Table(self.mine_page, kit, Tr('BY_VEIN'), (
            (Tr('COL_ORE'), NAME_X, 'left'), (Tr('COL_AMOUNT'), LENGTH_RIGHT, 'right')), Tr('NO_ORE'), False)
        self.minigame = None
        if self.mining is not None:
            self.BuildMinigame(self.mine_page, self.mine_counters.bottom + 10)
        self.wood_page = Page(page)
        self.woodMinigame = None
        if self.wood is not None:
            self.wood_counters = Counters(self.wood_page, kit, [Tr(key) for key in (
                'CUTS', 'WOOD_TOTAL', 'TIME_TREE', 'TODAY', 'WCHECK_GREAT', 'WCHECK_GOOD', 'WCHECK_MISS')],
                Tr('WOOD_SUCCESS'))
            self.wood_table = Table(self.wood_page, kit, Tr('BY_TREE'), (
                (Tr('COL_WOOD'), NAME_X, 'left'), (Tr('CUT'), LENGTH_RIGHT, 'right')), Tr('NO_WOOD'), False)
            self.BuildWoodMinigame(self.wood_page, self.wood_counters.bottom + 10)

    # ------------------------------------------------------------------ navigation
    def Pages(self):
        return (('overview', self.book), ('mastery', self.masteryPage), ('stats', self.stats),
                ('titles', self.titlesPage))

    def SelectTab(self, tab):
        """A page of the rail: 'overview' = the book, 'mastery' = the tree, 'stats' = the statistics, 'titles' = the
        titles and tool looks, each of the selected craft."""
        if tab not in [name for name, unused in TABS] or self.PageSoon(tab):
            return
        self.tab = tab
        for (name, unused), row in zip(TABS, self.rail):
            row.SetSelected(name == tab)
        for name, page in self.Pages():
            if name == tab:
                page.Show()
            else:
                page.Hide()
        if tab == 'stats':
            self.Request()
        elif tab == 'mastery':
            self.RequestMastery()
            self.masteryPage.Refresh()
        elif tab == 'titles':
            self.RequestTitles()
            self.titlesPage.Refresh()
        uir1.HideHint()

    # the levels of the craft switch, the Strom page (root/craftmasterymodel.py)
    def MasteryModel(self):
        model = getattr(self, 'masteryModel', None)
        if model is None:
            model = self.masteryModel = MM.CraftMasteryModel()
        return model

    def SetMasteryModel(self, model):
        self.masteryModel = model
        self.RefreshMastery()

    def RequestMastery(self):
        return self.QueueRequest(MASTERY_REQUESTER)

    def RefreshMastery(self):
        """A new mastery snapshot: the levels on the craft switch and the pages that show them."""
        if not self.built:
            return
        self.RefreshBook()
        self.RefreshCraftLabels()
        self.side.Refresh()
        if self.tab == 'mastery':
            self.masteryPage.Refresh()
        elif self.tab == 'titles':
            self.titlesPage.Refresh()

    def CraftLevel(self, index):
        """The mastery level of a craft (CRAFTS index), None before the first snapshot or for a craft the server does
        not send."""
        snapshot = self.MasteryModel().snapshot
        craft = snapshot.Craft(index) if snapshot is not None else None
        return craft.level if craft is not None else None

    def RefreshCraftLabels(self):
        for index, (cell, (unused, key)) in enumerate(zip(self.crafts.cells, CRAFTS)):
            level = self.CraftLevel(index) if cell.enabled else None
            uir1.Fit(cell.label, Tr(key) if level is None else Tr('CRAFT_LEVEL') % (Tr(key), level),
                     cell.GetWidth() - 2 * uir1.Segment.PAD)

    # the Tituly a vzhled page (root/crafttitlesmodel.py)
    def TitlesModel(self):
        model = getattr(self, 'titlesModel', None)
        if model is None:
            model = self.titlesModel = TM.CraftTitlesModel()
        return model

    def SetTitlesModel(self, model):
        self.titlesModel = model
        self.RefreshTitles()

    def PageSoon(self, page):
        """A page CRAFT_PAGE_TABLE marks soon: its tab is shown but locked and the server is not asked for it."""
        return self.pages.get(page) == 'soon'

    def RequestTitles(self):
        if self.PageSoon('titles'):
            return False
        return self.QueueRequest(TITLES_REQUESTER)

    def RefreshTitles(self):
        if not self.built:
            return
        self.side.Refresh()
        if self.tab == 'titles':
            self.titlesPage.Refresh()

    def ChooseSkin(self, skin_id):
        """A click on a look of the selected craft (None = Bez vzhledu): the command to the server, the page at once."""
        command = self.TitlesModel().Choose(self.CraftIndex(), skin_id)
        if command:
            try:
                import net
                net.SendChatPacket(command)
            except Exception:
                pass
            self.RefreshTitles()

    def CraftIndex(self):
        return [craft for craft, unused in CRAFTS].index(self.craft)

    def SelectCraft(self, craft):
        if craft not in ('fishing', 'mining', 'wood') or (craft == 'wood' and self.wood is None):
            return
        self.craft = craft
        self.crafts.SetValue(craft)
        for name, page in (('fishing', self.fish_page), ('mining', self.mine_page), ('wood', self.wood_page)):
            if name == craft:
                page.Show()
            else:
                page.Hide()
        self.Refresh()
        if self.tab == 'mastery':
            self.masteryPage.Refresh()
        elif self.tab == 'titles':
            self.titlesPage.Refresh()

    def SelectChapter(self, index):
        self.chapter[self.craft] = index
        self.selected[self.craft] = None
        self.RefreshBook()

    def SelectTile(self, index):
        if 0 <= index < len(self.modeRows):
            self.selected[self.craft] = self.modeRows[index][0]
            self.RefreshBook()

    def SelectBookMode(self, rare):
        if self.craft not in self.bookModes:
            return
        self.bookMode[self.craft] = bool(rare)
        self.RefreshBook()

    def Chapters(self):
        return M.Chapters(self.MasteryModel().snapshot, [craft for craft, unused in CRAFTS].index(self.craft))

    def Table(self):
        if self.craft == 'wood':
            return self.wood_table
        return self.mine_table if self.craft == 'mining' else self.fish_table

    # ------------------------------------------------------------------ open / close
    def Open(self):
        if not self.positioned:
            self.SetCenterPosition()
            self.positioned = True
        self.Show()
        self.SetTop()
        self.SetFocus()
        self.Refresh()
        self.Request()
        self.RequestMastery()
        self.RequestTitles()                    # the side column shows the worn title on every page

    def Close(self):
        uir1.HideHint()
        self.pendingRequests.clear()
        self.awaitingRequests.clear()
        if self.liveTicker is not None:
            self.liveTicker.Hide()
        self.Hide()

    def Request(self):
        return self.QueueRequest(REQUESTER)

    def QueueRequest(self, requester):
        now = requester.Clock()
        sent = requester.Request()
        if sent:
            self.pendingRequests.pop(requester, None)
            # An old server can silently throttle too. Retry twice if no End arrives.
            self.awaitingRequests[requester] = (now + requester.gap + 0.25, 2)
        else:
            self.pendingRequests.setdefault(requester, now)
        if self.liveTicker is not None:
            self.liveTicker.Show()
        return sent

    def RequestLive(self):
        if not self.built or not self.IsShow():
            return False
        # Same CraftChangedV1 path as kniha-atlas-zive. EXP and multiple events coalesce.
        now = REQUESTER.Clock()
        self.pendingRequests.setdefault(REQUESTER, now + 0.15)
        self.liveTicker.Show()
        return True

    def Reply(self, command):
        for requester, end in ((REQUESTER, M.END), (MASTERY_REQUESTER, MM.END),
                               (TITLES_REQUESTER, TM.END)):
            if command == end:
                self.awaitingRequests.pop(requester, None)
        if not self.pendingRequests and not self.awaitingRequests and self.liveTicker is not None:
            self.liveTicker.Hide()

    def LiveTick(self):
        if not self.IsShow():
            self.pendingRequests.clear()
            self.awaitingRequests.clear()
            self.liveTicker.Hide()
            return
        now = REQUESTER.Clock()
        for requester, due in list(self.pendingRequests.items()):
            if now >= due and requester.Request():
                self.pendingRequests.pop(requester, None)
                self.awaitingRequests[requester] = (now + requester.gap + 0.25, 2)
        for requester, (due, retries) in list(self.awaitingRequests.items()):
            if now >= due:
                if retries and requester.Request():
                    self.awaitingRequests[requester] = (now + requester.gap + 0.25, retries - 1)
                elif not retries:
                    self.awaitingRequests.pop(requester, None)
        if not self.pendingRequests and not self.awaitingRequests:
            self.liveTicker.Hide()

    def OnMouseWheel(self, delta):
        if self.built and self.tab == 'stats' and self.Table().OnWheel(delta):
            return True
        return False

    def Destroy(self):
        self.Close()
        if self.liveTicker is not None:
            self.liveTicker.OnUpdate = None
        self.model = None

    def ShowEmblem(self, craft):
        """The craft's tool icon in the emblem place of the book page (CRAFT_ICON_TABLE)."""
        book = self.book
        if book.emblemCraft != craft:
            book.emblemCraft = craft
            icon = CraftIcon(craft, self.names, self.craftIcons)
            book.emblemCraft = craft if icon else ''
            if icon:
                FitIcon(book.emblem, icon, LEFT_PAGE_X + 12, EMBLEM_Y, A.EMBLEM, A.EMBLEM)
        if book.emblemCraft:
            book.emblem.Show()
        else:
            book.emblem.Hide()

    # ------------------------------------------------------------------ data
    def Name(self, vnum):
        name, icon = ItemInfo(vnum, self.names)
        return (name or '#%d' % vnum), icon

    def VeinName(self, row):
        """The raw ore of a vein (item name and icon); without an ore the vein's own name (no icon)."""
        if row.ore_vnum:
            return self.Name(row.ore_vnum)
        try:
            import nonplayer
            name = nonplayer.GetMonsterName(row.vein_vnum)
        except Exception:
            name = ''
        return (name or '#%d' % row.vein_vnum), ''

    def WoodName(self, wood_vnum):
        """(name, icon) of a wood item from the item table."""
        name, icon = ItemInfo(wood_vnum, self.names)
        return (name or '#%d' % wood_vnum), icon

    def VeinTitle(self, vein):
        try:
            import nonplayer
            return nonplayer.GetMonsterName(vein) or ''
        except Exception:
            return ''

    def Refresh(self):
        if not self.built:
            return
        snapshot = self.model.snapshot if self.model is not None else None
        self.shown_revision = getattr(self.model, 'revision', None)
        data = snapshot or M.Snapshot()
        fish, mine, check = data.fish, data.mine, data.check
        number = M.FormatNumber
        self.fish_counters.SetValues((number(fish.casts), number(fish.games_completed), number(fish.catches),
                                      number(fish.nothing), number(fish.escaped), number(fish.abandoned),
                                      number(fish.best_streak), number(fish.current_streak),
                                      M.FormatDuration(fish.seconds_at_water)), data.FishSuccess())
        mine_values = [number(mine.attempts), number(mine.successes), number(mine.ore_total),
                       M.FormatDuration(mine.seconds_at_vein)]
        if self.mining is not None:
            mine_values.extend((number(check.great), number(check.good), number(check.miss)))
        self.mine_counters.SetValues(mine_values, data.MineSuccess())
        fish_items = []
        for row in data.FishRows():
            name, icon = self.Name(row.vnum)
            fish_items.append((icon, name, number(row.count), M.FormatLength(row.best_length)))
        self.fish_table.SetItems(fish_items)
        mine_items = []
        for row in data.MineRows():
            name, icon = self.VeinName(row)
            mine_items.append((icon, name, number(row.amount)))
        self.mine_table.SetItems(mine_items)
        if self.wood is not None:
            wood, marks = data.wood, data.wood_check
            self.wood_counters.SetValues((number(wood.cuts), number(wood.wood), M.FormatDuration(wood.seconds),
                                          Tr('TODAY_VALUE') % (number(wood.cuts_today), number(wood.daily_limit))
                                          if wood.daily_limit else number(wood.cuts_today),
                                          number(marks.great), number(marks.good), number(marks.miss)),
                                         M.Ratio(marks.perfect, wood.cuts))
            wood_items = []
            for row in data.WoodRows():
                name, icon = self.WoodName(row.wood_vnum)
                wood_items.append((icon, name, number(row.pieces)))
            self.wood_table.SetItems(wood_items)
        changed = snapshot is not getattr(self, 'snapshot', None)
        self.snapshot = snapshot
        if changed and snapshot is not None and self.IsShow():
            self.RequestMastery()  # every piece can reach a configured threshold, including pure ore
        self.RefreshCraftLabels()
        self.side.Refresh()
        self.RefreshBook()
        self.RefreshMiningMode()
        self.RefreshWoodMode(book=False)

    def RefreshBook(self):
        if not self.built:
            return
        snapshot = getattr(self, 'snapshot', None)
        data = snapshot or M.Snapshot()
        book = self.book
        fishing = self.craft == 'fishing'
        woodcut = self.craft == 'wood'
        chapters = self.Chapters()
        all_entries = [entry for c in chapters for entry in c[2]]
        all_vnums = [entry.identity for entry in all_entries]
        collection = M.BookModeCollection(snapshot, [], all_entries)
        found = M.Got(all_entries)
        number = M.FormatNumber
        self.ShowEmblem(self.craft)
        if snapshot is None:
            sub = Tr('LOADING')
        elif woodcut:
            sub = Tr('SUB_WOOD') % (found, len(all_vnums), M.FormatDuration(data.wood.seconds)) \
                if data.wood.seconds else Tr('SUB_WOOD_NEW') % (found, len(all_vnums))
        elif fishing:
            sub = Tr('SUB_FISH') % (found, len(all_vnums), M.FormatDuration(data.fish.seconds_at_water)) \
                if data.fish.seconds_at_water else Tr('SUB_FISH_NEW') % (found, len(all_vnums))
        else:
            sub = Tr('SUB_MINE') % (found, len(all_vnums), M.FormatDuration(data.mine.seconds_at_vein)) \
                if data.mine.seconds_at_vein else Tr('SUB_MINE_NEW') % (found, len(all_vnums))
        book.title.SetText(Tr('FISHER') if fishing else (Tr('WOODCUTTER') if woodcut else Tr('MINER')))
        uir1.Fit(book.sub, sub, PAGE_W - 24 - A.EMBLEM - 10)
        if fishing:
            fish = data.fish
            figures = ((number(fish.catches), Tr('FIG_CATCHES')),
                       (M.FormatPercent(data.FishSuccess()) if fish.games_completed else u'–', Tr('FIG_SUCCESS')),
                       (Tr('FIG_STREAK_VALUE') % (number(fish.current_streak), number(fish.best_streak))
                        if fish.best_streak else number(fish.current_streak), Tr('FIG_STREAK')))
        elif woodcut:
            wood = data.wood
            figures = ((number(wood.cuts), Tr('FIG_CUTS')), (number(wood.wood), Tr('FIG_WOOD')),
                       ('%s / %s' % (number(wood.cuts_today), number(wood.daily_limit)) if wood.daily_limit else
                        number(wood.cuts_today), Tr('FIG_TODAY')))
        else:
            mine = data.mine
            figures = ((number(mine.attempts), Tr('FIG_RUNS')),
                       (M.FormatPercent(data.MineSuccess()) if mine.attempts else u'–', Tr('FIG_SUCCESS')),
                       (number(mine.ore_total), Tr('FIG_ORES')))
        for (value, label), (v, l) in zip(book.figures, figures):
            value.SetText(v)
            value.SetPackedFontColor(T.IVORY if v not in ('0', u'–') else T.MUTED)
            label.SetText(l)
        index = min(self.chapter[self.craft], len(chapters) - 1)
        for i, row in enumerate(book.rows):
            if i < len(chapters):
                numeral, key, vnums = chapters[i]
                row.Set(numeral, Tr(key), M.Got(vnums), len(vnums))
                row.SetSelected(i == index)
                row.Show()
            else:
                row.Hide()
        # bottom of the left page
        if fishing:
            rows = []
            for record, value in ((data.LongestFish(), lambda r: M.FormatLength(r.best_length)),
                                  (data.MostCaughtFish(), lambda r: number(r.count) + u'×'),
                                  (M.LeastCaughtFish(data), lambda r: number(r.count) + u'×')):
                if record is not None:
                    name, icon = self.Name(record.vnum)
                    rows.append((icon, name, value(record)))
            book.SetRecords(rows if snapshot is not None else [])
        elif woodcut:
            marks = data.wood_check
            total_marks = data.WoodMarks()
            mode = self.wood.mode if self.wood is not None else None
            pct = ('%d %%' % int(round(100.0 * marks.great / total_marks))) if total_marks else '0 %'
            book.SetMinigame(Tr('MARKS') % number(total_marks),
                             Tr('WOOD_MODE_SHORT_%d' % mode) if mode in (0, 1) else '',
                             (marks.great, marks.good, marks.miss),
                             (Tr('LEG_GREAT') % ('%s (%s)' % (number(marks.great), pct)),
                              Tr('LEG_GOOD') % number(marks.good), Tr('LEG_MISS') % number(marks.miss)),
                             Tr('TIME_TREE_LINE') % (number(marks.perfect), M.FormatDuration(data.wood.seconds)),
                             wood=True)
        elif self.mining is None:
            book.SetMiningSummary(Tr('TIME_VEIN_LINE') % M.FormatDuration(data.mine.seconds_at_vein))
        else:
            check = data.check
            rings = check.great + check.good + check.miss
            mode = self.mining.mode if self.mining is not None else None
            mode_text = Tr('MODE_SHORT_%d' % mode) if mode in (0, 1, 2, 3) else ''
            pct = ('%d %%' % int(round(100.0 * check.great / rings))) if rings else '0 %'
            book.SetMinigame(Tr('RINGS') % number(rings), mode_text, (check.great, check.good, check.miss),
                             (Tr('LEG_GREAT') % ('%s (%s)' % (number(check.great), pct)),
                              Tr('LEG_GOOD') % number(check.good), Tr('LEG_MISS') % number(check.miss)),
                             Tr('TIME_VEIN_LINE') % M.FormatDuration(data.mine.seconds_at_vein))
        # right page; an older server has no chapter definitions.
        if not chapters:
            book.chapterTitle.SetText(Tr('LOADING'))
            book.chapterCount.SetText('')
            self.modeRows = []
            for widget in [book.modeSwitch, book.detailIcon, book.detailName] + book.tiles + \
                          [w for pair in book.detailRows for w in pair] + [w for pair in book.goals for w in pair]:
                widget.Hide()
            return
        book.detailName.Show()
        numeral, key, entries = chapters[index]
        mode_map = self.bookModes.get(self.craft, {})
        ores = self.vein_ores if self.craft == 'mining' else None
        if woodcut and not mode_map:
            # an older export without glowing wood: the switch splits the tiers (normal | rare)
            kinds = self.bookModes.get('wood_kind', {})
            available = M.WoodModeSwitchRows(entries, kinds)
            rare = bool(available) and self.bookMode[self.craft]
            self.modeRows = M.WoodModeRows(entries, kinds if available else {}, rare)
        else:
            available = M.BookModeRows(entries, mode_map, True, ores) if mode_map else []
            rare = bool(available) and self.bookMode[self.craft]
            self.modeRows = M.BookModeRows(entries, mode_map, rare, ores)
        shown_items = dict(self.modeRows)
        collection = M.BookModeCollection(snapshot, self.modeRows, entries,
                                          rare and not (woodcut and 'wood' not in self.bookModes))
        by_identity = dict((e.identity, e) for e in entries)
        vnums = [identity for identity, unused in self.modeRows]
        book.modeSwitch.SetValue(rare)
        book.modeSwitch.cells[1].label.SetText(Tr('MODE_GLOWING' if fishing else ('MODE_RARE_WOOD' if woodcut else 'MODE_RARE')))
        book.ShowPart((book.modeSwitch,), bool(available))
        title_width = PAGE_W - 24 - T.CRAFT_BOOK_COUNT_W
        if available:
            title_width -= T.CRAFT_BOOK_MODE_W + T.CRAFT_BOOK_HEADER_GAP
        uir1.Fit(book.chapterTitle, '%s. %s' % (numeral, Tr(key)), title_width)
        book.chapterCount.SetText('%d / %d' % (M.Got(entries), len(entries)))
        selected = self.selected[self.craft]
        if selected not in vnums:
            caught = [v for v in vnums if v in collection]
            selected = caught[0] if caught else vnums[0]
        self.selected[self.craft] = selected
        rare_counts = M.FishCollection(snapshot) if fishing else {}
        for i, tile in enumerate(book.tiles):
            if i < len(vnums):
                vnum = vnums[i]
                got = vnum in collection
                if fishing:
                    name, icon = self.Name(shown_items[vnum])
                    count, best = collection.get(vnum, (0, 0))
                    hint = Tr('HINT_TILE_FISH') % (name, number(count), M.FormatLength(best)) if got else \
                        Tr('UNKNOWN')
                elif woodcut:
                    name, icon = self.WoodName(shown_items[vnum])
                    count = collection.get(vnum, (0, 0))[0]
                    hint = Tr('HINT_TILE_WOOD') % (name, number(count)) if got else Tr('UNKNOWN')
                else:
                    ore = shown_items[vnum]
                    name, icon = self.Name(ore) if ore else (self.VeinTitle(vnum[1]), '')
                    count = collection.get(vnum, (0, 0))[0]
                    hint = Tr('HINT_TILE_ORE') % (name, number(count)) if got else Tr('UNKNOWN')
                if fishing and not rare and not got:
                    counterpart = mode_map.get(vnum[1])
                    if counterpart in rare_counts:
                        rare_count, rare_best = rare_counts[counterpart]
                        hint = Tr('MODE_HINT_VARIANT') % (hint, self.Name(counterpart)[0], number(rare_count))
                if not rare:
                    entry = by_identity[vnum]
                    hint = '%s | %s / %s' % (name, number(entry.have), number(entry.need))
                tile.Set(vnum, icon, got, number(count), hint)
                tile.SetSelected(vnum == selected)
            else:
                tile.Hide()
        self.RefreshDetail(selected, collection, shown_items.get(selected), rare, by_identity[selected], data)
        goals = M.Goals(chapters, data.fish.current_streak if fishing else None,
                        data.fish.best_streak if fishing else None)
        if woodcut and snapshot is not None and data.wood.daily_limit:
            left = max(0, data.wood.daily_limit - data.wood.cuts_today)
            goals = (goals + [('GOAL_TODAY', (number(left),))])[:3]
        for i, (dot, text) in enumerate(book.goals):
            if i < len(goals):
                goal, values = goals[i]
                if goal == 'GOAL_CHAPTER':
                    line = Tr('GOAL_CHAPTER_PIECES') % (values[0], number(values[1]), number(values[2]))
                else:
                    line = Tr(goal) % values
                uir1.Fit(text, line, PAGE_W - 24 - 12)
                dot.Show()
                text.Show()
            else:
                dot.Hide()
                text.Hide()

    def RefreshDetail(self, identity, collection, shown_item, rare, entry, data):
        book = self.book
        have, best = collection.get(identity, (0, 0))
        name, icon = self.Name(shown_item) if shown_item else (self.VeinTitle(entry.vnum), '')
        wx, wy = book.detailWell.GetLocalPosition()
        if icon:
            FitIcon(book.detailIcon, icon, wx + 1, wy + 1, TILE - 2, TILE - 2)
            Tint(book.detailIcon, (1.0, 1.0, 1.0, 1.0) if have else SILHOUETTE)
            book.detailIcon.Show()
        else:
            book.detailIcon.Hide()
        book.detailName.SetText(name if have or not rare else Tr('UNKNOWN'))
        book.detailName.SetPackedFontColor(T.IVORY if have else T.INK_DIM)
        if rare and not have:
            kind = {'fish': 'FISH', 'wood': 'WOOD'}.get(entry.counter, 'VEIN')
            rows = [(Tr('UNKNOWN_' + kind), ''), (Tr('UNKNOWN_%s_2' % kind), '')]
        elif rare:
            rows = [(Tr({'fish': 'CAUGHT', 'wood': 'CUT'}.get(entry.counter, 'MINED')), Tr('PIECES') % M.FormatNumber(have))]
            if entry.counter == 'fish':
                rows.append((Tr('COL_LONGEST'), M.FormatLength(best)))
        else:
            rows = [(Tr('CHAPTERS'), '%s / %s' % (M.FormatNumber(entry.have), M.FormatNumber(entry.need)))]
            if entry.counter == 'fish':
                rows += [(Tr('SHARE'), Tr('SHARE_FISH') % M.Share(entry.have, data.fish.catches)),
                         (Tr('COL_LONGEST'), M.FormatLength(best))]
            elif entry.counter in ('vein', 'wood'):
                total = data.mine.ore_total if entry.counter == 'vein' else data.wood.wood
                rows.append((Tr('SHARE'), Tr('SHARE_ORE' if entry.counter == 'vein' else 'SHARE_WOOD') %
                             M.Share(entry.have, total)))
        uir1.Fit(book.detailName, book.detailName.GetText(), PAGE_W - 24 - 60)
        for i, (key, value) in enumerate(book.detailRows):
            if i < len(rows):
                k, v = rows[i]
                if v:
                    key.SetText(k)
                    uir1.Fit(value, v, PAGE_W - 24 - 60 - 64)
                else:
                    uir1.Fit(key, k, PAGE_W - 24 - 60)
                    value.SetText('')
                key.Show()
                value.Show()
            else:
                key.Hide()
                value.Hide()


# --------------------------------------------------------------------------- module entry points
def Notify():
    """One chat line instead of the window (it has no original look to fall back to)."""
    try:
        import chat
        chat.AppendChat(chat.CHAT_TYPE_INFO, Tr('FAILED'))
    except Exception:
        pass


def Create(model, mining=None, wood=None):
    """The craft book window, or None after a failure (traced once, a chat line every time it is asked for).
    ``mining``: the uiminingcheck.MiningCheck controller for the minigame switch (Statistiky, Horník); ``wood``: the
    uiwoodcheck.WoodCheck controller - it opens the Dřevorubec tab and its rhythm bar switch."""
    if _failed:
        Notify()
        return None
    window = None
    try:
        window = CraftBookWindow(model, mining, wood)
        window.Build()
        return window
    except Exception:
        _failed.append(WHAT)
        uir1.TraceFailure(WHAT)
        if window is not None:
            try:
                window.Hide()
            except Exception:
                pass
        Notify()
        return None
