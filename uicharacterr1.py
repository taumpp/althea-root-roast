# -*- coding: utf-8 -*-
"""The character window in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md): the main page and the skills page.

uicharacter.CharacterWindow keeps the window (253 x 361 without the champion level, 253 x 405 with it; uiscript/
uiscript/characterwindow.py), its four pages, every control and event (the stat + / - buttons, the level switch, the
page tabs, the skill slots and groups, the quest list, the tooltips, the "Bonusy" ear); CharacterSkin re-skins it for
R1 unless Settings -> "Starý vzhled" chose the original look (uir1.UseR1()). A build failure undoes every change
(traced to syserr). The panel Bonusy / Statistiky beside the window is uicharacterdetailskit.

Main page (team decision 2026-10-06 after the redesigns A / B / C were turned down: "the original character window is
top - put the old one into the new look and change as little as possible"): the ORIGINAL layout of the uiscript.
Every label, value box, + / - button, section and tab stays where the uiscript puts it, at its size; R1 only
recolours (the graphite frame and header, R1 section headings in place of the crimson bars, dark wells for the value
boxes, 13 px R1 + / - buttons, R1 tabs over the original tab buttons) and draws the texts in the kit roles of every
R1 window (Noto Sans text / text_s, the title in Cinzel). Where Noto Sans needs more room than the original Tahoma 12,
the smallest change that keeps the arrangement is made - see the constants below (each one names its deviation).

Without the champion level (the 253 x 361 window of the DEV client) the two sections Status postavy and Vlastnosti
are ONE grid since 2026-10-08 (owner's choice B of the round postava-cech, docs/ALTHEA_R1_KIT.md): 14 equal cells
111 x 18 (two columns 111 + 5 + 111, content 13 px from the window edge on both sides), the name inside the cell at its
left edge, the value at its right edge, the + part of the cell 2 px from its edge (the reset - before it, only while
points can be taken back), the rows 23 px apart in both sections, "Volné body" = its name and a 35 px number cell at the
right end of the heading, the one-line Vlastnosti names shortened ("Rychl. pohybu", "Vyhnutí"; the full name in the
hover hint of the cell). The window keeps its size; the champion variant keeps the layout of the uiscript.
Every one of the 14 cells has its hover hint (StatHint, 2026-10-09 after the tester's 374 - 376.png: Rychl. kouzel and
Vyhnutí had none - their row lay below the 304 px Character_Page, which the engine does not pick through - and the
Rychl. útoku hint lay on the row above): the full name, a short explanation, beside the window, never over the grid.
The hint areas live in ONE not-pickable layer straight on the window, above the board (HINT_LAYER): the engine picks
them before anything of the board and no page / section / row holder can clip them (owner in game 2026-10-09 after
the first fix: the last row still answered only on a 1 px line).

* skills page: "Schopnosti | Buffy" as R1 tabs (today the hard-coded English "BUFF"), the free points as a large
  number with its label, the skill cells on the R1 item slot C (uir1.SLOT_CELL, the one R1 slot since 2026-10-07),
  "Standardní schopnosti" as a section heading; the level / grade of every learned skill (the cells, the standard
  skills, the Buffi cells, the Lov bossů / Lov meteorů icons) stays the engine's own digits, as in Starý vzhled
  (native counts retain the skill grade at the original slot position);
* actions page (Akce): the headings Normální / Interaktivní / Speciální akce as R1 section headings right above
  their slot grids instead of the crimson bars with the arrow; the action slots on the R1 item slot C.

Original text lines that the window fills (values, names, points) stay hidden and are repeated by R1 texts after
every refresh (uir1skin.Mirror); the window calls Sync() after SetState, RefreshStatus, RefreshCharacter, RefreshSkill,
the level switch and the skill group switch.
"""
import ui

import uir1
import uir1skin
import uir1tokens as T

ART = 'd:/ymir work/ui/public/althea_r1_postava/character/'
SLOT_ORIGINAL = 'd:/ymir work/ui/public/Slot_Base.sub'
SLOT_R1 = uir1.SLOT_CELL          # the R1 item slot C (skill, buff and action cells)
PLUS_ORIGINAL = ('d:/ymir work/ui/game/windows/btn_plus_up.sub', 'd:/ymir work/ui/game/windows/btn_plus_over.sub',
                 'd:/ymir work/ui/game/windows/btn_plus_down.sub')
MINUS_ORIGINAL = ('d:/ymir work/ui/game/windows/btn_minus_up.sub', 'd:/ymir work/ui/game/windows/btn_minus_over.sub',
                  'd:/ymir work/ui/game/windows/btn_minus_down.sub')
PLUS_R1 = (ART + 'plus13_normal.png', ART + 'plus13_hover.png', ART + 'plus13_pressed.png')     # the original 13 px
MINUS_R1 = (ART + 'minus13_normal.png', ART + 'minus13_hover.png', ART + 'minus13_pressed.png')
BELT = 'd:/ymir work/ui/game/belt_inventory/'
CHAR = 'd:/ymir work/ui/public/crimson/windows/character/'
WINDOWS = 'd:/ymir work/ui/game/windows/'

STATES = ('STATUS', 'SKILL', 'EMOTICON', 'QUEST')
TAB_BUTTONS = ('Tab_Button_01', 'Tab_Button_02', 'Tab_Button_03', 'Tab_Button_04')
TAB_LABELS = ('Tab_Label_01', 'Tab_Label_02', 'Tab_Label_03', 'Tab_Label_04')
# Page titles: the texts of the original title bars (uiScriptLocale name, fallback).
TITLES = (('CHARACTER_MAIN', 'Postava'), ('CHARACTER_SKILL', 'Schopnosti'), ('CHARACTER_ACTION', 'Akce'),
          ('CHARACTER_QUEST', 'Úkol'))
# Akce: (section bar, its text, the slot grid under it, fallback text (cs, en)); the heading ends 1 px above the grid
ACTION_HEADINGS = (('Action_Bar', 'Action_Bar_Text', 'SoloEmotionSlot', ('Normální akce', 'Normal actions')),
                   ('Reaction_Bar', 'Reaction_Bar_Text', 'DualEmotionSlot', ('Interaktivní akce', 'Mutual actions')),
                   ('Special_Action_Bar', 'Special_Action_Bar_Text', 'SpecialEmotionSlot',
                    ('Speciální akce', 'Special actions')))
ACTION_HEADING_GAP = 1
ACTION_HEADING_W = 233                          # the crimson section bar (section.tga)

# ---------------------------------------------------------------------------------------------------- main page
# Positions are read from the uiscript at build time (both variants: app.ENABLE_CONQUEROR_LEVEL); only these differ:
CONTENT_TOP = T.HEAD_H + T.CONTENT_GAP          # the portrait (Face_Slot 7, 25 and its face) moves down to the R1
                                                # header's content row: + 4 px (the vein of the R1 header is at y 27)
ORIGINAL_CAP = 6                                # an original Tahoma 12 text line: its letters centred 6 px below its y
BAR_H = 17                                      # the crimson section bar (section.tga, 233 x 17)
BAR_TEXT_X = 6                                  # the original section text starts 6 px inside its bar
BOX_H = 18                                      # every value box of the uiscript is 18 px tall
PAD = 3                                         # a value keeps 3 px from the edges of its box
GUTTER = 8                                      # two texts of one row (header columns, a label and the next text)
WELLS = (28, 35, 39, 52, 70, 82, 90)            # R1 wells of the champion variant: the original box widths 39 / 52 / 90;
                                                # 82 = a 90 px box that the Bonusy ear (uicharacter ExpandBtn at 240, 120)
                                                # covers by 8 px; 70 = a 52 px box grown to the left for a long value
                                                # (the grid of the standard variant uses CELL_W and CHIP_W below)
# The grid of the standard variant (see the module docstring). Window x: the content of both sections lies 13 px from
# the frame on the left and on the right; the columns 111 + 5 + 111 (x 13 and 129, the right one ends at the Bonusy ear).
CONTENT_MARGIN = 13
CELL_W, CELL_GAP = 111, 5                       # one cell: the well well_111 (tools/build_althea_r1_postava.py)
CONTENT_W = 2 * CELL_W + CELL_GAP               # 227: the width of the headings and of the grid
STATUS_PAD, EXTENT_PAD = 6, 5                   # the name / value inset of a cell of Status postavy / Vlastnosti
BUTTON = 13                                     # the original stat + / - buttons (plus13_*, minus13_*)
PLUS_INSET = 2                                  # the + lies inside its cell, 2 px from the cell's right edge
BUTTON_GAP = 2                                  # the reset - lies 2 px before the +
VALUE_GAP = 6                                   # the value ends 6 px before the button that follows it (the + always:
                                                # it does not jump when the points run out; the - while it shows)
CHIP_W, CHIP_PAD = 35, 5                        # the free points: the number cell (well_35) at the heading's right end
FREE_GAP = 6                                    # number cell -> "Volné body"
EXTENT_HEADING_SHIFT = 8                        # Vlastnosti: the heading 8 px and the rows 4 px lower than the bar and
EXTENT_ROWS_SHIFT = 4                           # rows of the uiscript (heading y 231, rows 258 / 281 / 304: the last
                                                # ends at 322, where it ended before; the rows 23 px apart as Status)
# Each Vlastnosti name is ONE line in PROPERTY_FONT (Noto Sans 14a = 10 ppem, the size of the original Tahoma 12): the
# cell is 111 px wide ("Rychlost pohybu" 78 + the number 21 + the insets = 117 px would not fit), so the three
# "Rychlost ..." names and "Hodnota vyhnutí" are shortened; the hover hint of the cell shows the full name (the two
# original lines joined). stem: (Czech, English)
PROPERTY_FONT = 'text_xs'
EXTENT_NAMES = {'MOV': ('Rychl. pohybu', 'Move spd.'), 'ASPD': ('Rychl. útoku', 'Attack spd.'),
                'CSPD': ('Rychl. kouzel', 'Cast spd.'), 'MATT': ('Útok magií', 'Magic atk.'),
                'MDEF': ('Obrana magií', 'Magic def.'), 'EVASION': ('Vyhnutí', 'Evasion')}
# The one value that can outgrow its cell: the magic attack of a magic weapon is a range ("1380-1520", 51 px even in
# text_xs, with "Útok magií" 52 px more than the cell holds). Only then the name gives way to its tight form (the full
# name stays in the hover hint), so nothing overlaps in the worst case.
EXTENT_TIGHT = {'MATT': ('Mag.', 'Mag.')}
# The hover hint of every cell of the grid (standard variant): stem -> ((name cs, en), (explanation cs, en)). The R1
# hint (uir1 HintFace, tooltip variant C: 70 % fill, no band) shows the name and, under its vein, the explanation; the
# value itself is in the cell (the original window had no breakdown of it).
STAT_HINTS = {
    'HTH': (('Vitalita (VIT)', 'Vitality (VIT)'), ('Zvyšuje maximální ZB a obranu.', 'Raises max HP and defence.')),
    'INT': (('Inteligence (INT)', 'Intelligence (INT)'),
            ('Zvyšuje maximální MB, útok magií a obranu magií.', 'Raises max MP, magic attack and magic defence.')),
    'STR': (('Síla (SÍL)', 'Strength (STR)'),
            ('Zvyšuje hodnotu útoku a poškození.', 'Raises attack value and damage.')),
    'DEX': (('Pohyblivost (POH)', 'Dexterity (DEX)'),
            ('Zvyšuje útok a šanci vyhnout se úderům.', 'Raises attack and the chance to evade hits.')),
    # The 10 cells
    # below say what the number is made of and where its cap lies (a number the player cannot see in the cell, e.g.
    # the attack speed bonus over 170 that the window already shows clipped). Server constants they quote: base HP
    # 600-700 / MP 200, +40 HP per VIT / +20 MP per INT, +36-44 HP / +18-22 MP per level (constants.cpp
    # JobInitialPoints); attack speed base 100, cap 170 (char.cpp GetLimitPoint); move speed base 140, cap
    # player_move_speed_limit of share/conf/movement_v1.json (1000); slow -30 for 20 s; cast speed cooldown x 100 /
    # value (utils.cpp CalculateDuration); evasion effect max 30 % (battle.cpp CalcAttackRating). The evasion number
    # of the cell is the EXE's own estimate (PythonPlayer __GetEvadeRate), hence "orientační".
    'HP': (('Životní body (ZB)', 'Hit points (HP)'),
           ('Max. ZB = základ povolání + 40 za každý bod VIT + 36–44 za každou úroveň + bonusy Max. ZB '
            'a Max. ZB %. Strop není.\n'
            'Základ povolání:\n'
            'Válečník: 600\n'
            'Ninja: 650\n'
            'Sura: 650\n'
            'Šaman: 700',
            'Max HP = class base + 40 per VIT point + 36-44 per level + Max HP and Max HP % bonuses. No cap.\n'
            'Class base:\n'
            'Warrior: 600\n'
            'Ninja: 650\n'
            'Sura: 650\n'
            'Shaman: 700')),
    'SP': (('Body many (MB)', 'Mana points (MP)'),
           ('Max. MB = 200 + 20 za každý bod INT + 18–22 za každou úroveň + bonusy Max. MB a Max. MB %. '
            'Strop není.',
            'Max MP = 200 + 20 per INT point + 18-22 per level + Max MP and Max MP % bonuses. No cap.')),
    'ATT': (('Hodnota útoku', 'Attack value'),
            ('2 × úroveň + útok ze statů + zbraň + bonus Hodnota útoku.\n'
             'Útok ze statů (proti příšerám):\n'
             'Válečník: 2 × SÍL (2 × SÍL)\n'
             'Ninja: (4 × SÍL + 2 × POH) / 3 (2 × POH)\n'
             'Sura: 2 × SÍL (2 × INT)\n'
             'Šaman: (4 × SÍL + 2 × INT) / 3 (2 × INT)',
             '2 x level + attack from stats + weapon + Attack value bonus.\n'
             'Attack from stats (against monsters):\n'
             'Warrior: 2 x STR (2 x STR)\n'
             'Ninja: (4 x STR + 2 x DEX) / 3 (2 x DEX)\n'
             'Sura: 2 x STR (2 x INT)\n'
             'Shaman: (4 x STR + 2 x INT) / 3 (2 x INT)')),
    'DEF': (('Obrana', 'Defence'),
            ('Úroveň + VIT + zbroj (tělo, helma, boty, štít, přívěsek, rukavice: obrana + 2 × stupeň vylepšení) + '
             'Bonus obrany.\nPronikavý zásah obranu obejde.',
             'Level + VIT + armour (body, helmet, shoes, shield, pendant, gloves: defence + 2 x upgrade grade) + '
             'Defence bonus.\nA piercing hit ignores defence.')),
    'MOV': (('Rychlost pohybu', 'Movement speed'),
            ('Základ 140, maximum 1000. Zpomalení ubere 30 na 20 s.',
             'Base 140, maximum 1000. A slow takes 30 for 20 s.')),
    'ASPD': (('Rychlost útoku', 'Attack speed'),
             ('Základ 100 %, maximum 170 %. Bonusy nad 170 % nemají účinek (okno ukazuje už oříznutou hodnotu).',
              'Base 100 %, maximum 170 %. Bonuses above 170 % have no effect (the window shows the capped value).')),
    'CSPD': (('Rychlost kouzel', 'Cast speed'),
             ('Zkracuje přebíjení schopností: přebití × 100 / hodnota (150 = 67 % času). Strop není.',
              'Shortens skill cooldowns: cooldown x 100 / value (150 = 67 % of the time). No cap.')),
    'MATT': (('Útok magií', 'Magic attack'),
             ('2 × úroveň + 2 × INT + magický útok zbraně + bonus. Na cíl pak působí jeho Obrana magií a Odolnost '
              'proti magii.',
              '2 x level + 2 x INT + weapon magic attack + bonus. The target\'s Magic defence and Magic resistance '
              'then apply.')),
    'MDEF': (('Obrana magií', 'Magic defence'),
             ('Úroveň + (3 × INT + VIT) / 3 + polovina zbroje + bonus. Odečítá se od magického poškození jako pevné '
              'číslo.',
              'Level + (3 x INT + VIT) / 3 + half the armour + bonus. Subtracted from magic damage as a flat number.')),
    'EVASION': (('Hodnota vyhnutí', 'Evasion'),
                ('Snižuje přesnost běžných útoků nepřítele, účinek max. 30 %. Číslo v okně je orientační.\n'
                 'Šípy řeší zvlášť bonus Šance vyhnout se šípům.',
                 'Lowers the accuracy of enemy normal attacks, effect max 30 %. The number in the window is an '
                 'estimate.\nArrows have their own bonus: Chance to avoid arrows.')),
}
STD_RIGHT_STEMS = ('HP', 'SP', 'ATT', 'DEF')    # the stems of STD_RIGHT (in its order)
# With the champion level the first Vlastnosti row lay under its own section bar (original 276 vs the bar 270..287):
# the rows move 14 px down, below the R1 heading (the last icon then ends where the tabs start).
CHAMPION_EXTENT_SHIFT = 14
SWITCH_TOP_SHIFT = -4                           # the R1 level switch (24 px) ends where the status heading starts
# Rows of the stat boxes: (holder / container, slot, value, label line or None, R1 label shift, is a right box)
STD_LEFT = ('HTH', 'INT', 'STR', 'DEX')
STD_RIGHT = (('HEL_Label', 'HP_Slot', 'HP_Value', 'HP_Text'), ('SP_Label', 'SP_Slot', 'SP_Value', 'MP_Text'),
             ('ATT_Label', 'ATT_Slot', 'ATT_Value', 'ATT_Text'), ('DEF_Label', 'DEF_Slot', 'DEF_Value', 'DEF_Text'))
STD_EXTENT = (('MOV', 'MOV_Label', 'MSPD_Slot', 'MSPD_Value'), ('ASPD', 'ASPD_Label', 'ASPD_Slot', 'ASPD_Value'),
              ('CSPD', 'CSPD_Label', 'CSPD_Slot', 'CSPD_Value'), ('MATT', 'MATT_Label', 'MATT_Slot', 'MATT_Value'),
              ('MDEF', 'MDEF_Label', 'MDEF_Slot', 'MDEF_Value'), ('EVASION', 'ER_Label', 'ER_Slot', 'ER_Value'))
CHAMPION_ROWS = (('base_info', ('HTH_Slot', 'HTH_Value'), ('INT_Slot', 'INT_Value'), ('STR_Slot', 'STR_Value'),
                  ('DEX_Slot', 'DEX_Value')),
                 ('sungma_info', ('sungma_str_slot', 'sungma_str_value'), ('sungma_hp_slot', 'sungma_hp_value'),
                  ('sungma_move_slot', 'sungma_move_value'), ('sungma_immune_slot', 'sungma_immune_value')))
CHAMPION_PLUS = ('HTH_Plus', 'INT_Plus', 'STR_Plus', 'DEX_Plus', 'sungma_str_plus', 'sungma_hp_plus',
                 'sungma_move_plus', 'sungma_immune_plus')
CHAMPION_RIGHT = (('HEL_Label', 'HP_Slot', 'HP_Value'), ('SP_Label', 'SP_Slot', 'SP_Value'),
                  ('ATT_Label', 'ATT_Slot', 'ATT_Value'), ('DEF_Label', 'DEF_Slot', 'DEF_Value'))
CHAMPION_EXTENT = (('MSPD_IMG', 'MOV_Label', 'MSPD_Slot', 'MSPD_Value'),
                   ('ASPD_IMG', 'ASPD_Label', 'ASPD_Slot', 'ASPD_Value'),
                   ('CSPD_IMG', 'CSPD_Label', 'CSPD_Slot', 'CSPD_Value'),
                   ('MATT_IMG', 'MATT_Label', 'MATT_Slot', 'MATT_Value'),
                   ('MDEF_IMG', 'MDEF_Label', 'MDEF_Slot', 'MDEF_Value'),
                   ('ER_IMG', 'ER_Label', 'ER_Slot', 'ER_Value'))
FRAME_INSET = 6                                 # a grown box keeps 6 px from the window edge (the frame lines)
ICON_W = 25                                     # the champion variant's stat icons (windows.dds cuts)
FREE_ICON = 11                                  # its free points "+" (char_info_status_plus_img.sub, 11 x 11)
# Header row: (label line, value line) with the uiscript chain of each (the page is at 0, 0).
STD_HEADER = ((('Status_Header', 'Status_Lv', 'Level_Header'), ('Status_Header', 'Status_Lv', 'Level_Value')),
              (('Status_Header', 'Status_CurExp', 'Exp_Slot'), ('Status_Header', 'Status_CurExp', 'Exp_Value')),
              (('Status_Header', 'Status_RestExp', 'RestExp_Slot'),
               ('Status_Header', 'Status_RestExp', 'RestExp_Value')))
CHAMPION_HEADER = ((('Level_Label',), ('Level_Value',)), (('Exp_Label',), ('Status_CurExp', 'Exp_Value')),
                   (('NextExp_Label',), ('Status_RestExp', 'RestExp_Value')))

# Skills page (page coordinates; the page is at 0, 24). The rows follow the uiscript of the variant: the tabs
# centred on the header row of uicharacterbuff, the dark panel from the skill cells to the heading of the
# standard skills (the old title bar of that row).
SKILL_TAB_WIDTHS = (68, 60)                     # "Schopnosti" (Noto Sans 16a: 61 px) needs the wider cell
SKILL_PANEL_X, SKILL_PANEL_W = 10, 233
SKILL_INSET = 6                                 # tabs and heading: the inner padding of the panel (x 16, the cells 17)
SKILL_FIRST_ROW = 4                             # the first skill cell row inside Skill_Active_Slot (both variants)
SKILL_GAP = 3                                   # panel top -> cells, tabs -> panel top
PAGE_Y = 24                                     # the skills page inside the window (content starts at HEAD_H + 2)


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


def _Locale(name, fallback):
    try:
        import uiScriptLocale
        return getattr(uiScriptLocale, name, fallback) or fallback
    except Exception:
        return fallback


def LastNumber(text):
    """The free skill points: the window shows 'Zbývající body: 3' or just '3'."""
    return (text or '').rsplit(':', 1)[-1].strip()


def Well(width):
    return ART + 'well_%d.png' % width


class Box(object):
    """One value box of the main page: the original slot image (recoloured to an R1 well) inside its holder and the R1
    text of its value, centred where the original value was. A value too long for the box grows the box (the next
    wider well): to the left, its right edge kept, while it stays GUTTER px right of ``limit()`` (window x of the
    text or icon before it); otherwise to the right up to ``right_limit`` (window x) when the box has free room there."""

    def __init__(self, skin, holder, slot, value, width, origin, limit, right_limit=None):
        self.skin, self.holder, self.slot = skin, holder, slot
        self.sx, self.sy = slot.GetLocalPosition()
        self.base = int(width)
        self.right = self.sx + self.base
        self.origin = origin                         # window x of the holder
        self.limit, self.right_limit = limit, right_limit
        anchor = value.GetLocalPosition()[0]
        if self.base != slot.GetWidth():             # the box shortened at the ear: its value centred in what is left
            anchor = self.sx + self.base // 2
        self.anchor = anchor
        self.cy = self.sy + BOX_H // 2
        self.width, self.left = self.base, self.sx
        self.base_left = self.sx
        skin.rec.Image(slot, Well(self.base), skin.original_image(slot))
        skin.rec.Position(slot, self.sx, self.sy)    # Fit moves the well: the way back to the original place
        self.mirror = skin._mirror(value, holder, anchor, self.cy, 'text_s', T.IVORY)

    def _Grown(self, needed):
        """(width, left) of the well for a value ``needed`` px wide (with its padding)."""
        wider = [w for w in WELLS if w > self.base]
        room = self.origin + self.right - (self.limit() + GUTTER)
        for w in wider:
            if needed <= w <= room:
                return w, self.right - w
        if self.right_limit is not None:
            for w in wider:
                if needed <= w and self.origin + self.sx + w <= self.right_limit:
                    return w, self.sx
        left = [w for w in wider if w <= room]
        if left:
            return left[-1], self.right - left[-1]
        return self.base, self.base_left

    def Plan(self):
        """(width, left, value x) of the well for the current value (holder coordinates), without applying it."""
        needed = uir1.TextWidth(self.mirror.text) + 2 * PAD
        width, left = self.base, self.base_left
        if needed > self.base:
            width, left = self._Grown(needed)
        return width, left, (self.anchor if width == self.base else left + width // 2)

    def Fit(self):
        width, left, x = self.Plan()
        if (width, left) != (self.width, self.left):
            if width != self.width:
                self.slot.LoadImage(Well(width))
            self.slot.SetPosition(left, self.sy)
            self.width, self.left = width, left
        if self.mirror.text.GetLocalPosition() != (x, self.cy):
            self.mirror.text.SetPosition(x, self.cy)


class Cell(object):
    """One cell of the grid (standard variant): the well CELL_W x 18 of the original slot image, the name at its left
    edge (an R1 text of the holder: the mirror of the original label, or the joined Vlastnosti name) and the value at
    its right edge (the mirror of the original value line), in the holder of the row so that everything moves and hides
    with it. ``right()`` = holder x where the value ends. The value is drawn in text_s, in text_xs when it would come
    closer than GUTTER px to the name. A name with a tight form (JoinedName.SetTight) takes it only when the value does
    not fit even in text_xs."""

    def __init__(self, skin, holder, slot, value, name, pad, right=None):
        self.skin, self.holder, self.slot, self.name, self.pad = skin, holder, slot, name, pad
        self.cy = BOX_H // 2
        self.right = right or (lambda: CELL_W - pad)
        self.font = 'text_s'
        skin.rec.Image(slot, Well(CELL_W), skin.original_image(slot))
        skin.rec.Size(holder, CELL_W, holder.GetHeight())
        self.mirror = skin._mirror(value, holder, CELL_W - pad, self.cy, 'text_s', T.IVORY, 'right')

    def Fit(self):
        text, skin, name = self.mirror.text, self.skin, self.name
        right, value = self.right(), self.mirror.line.GetText()
        short = getattr(name, 'short', None)             # a JoinedName is measured in its normal form
        taken = self.pad + GUTTER + (skin.Width(short, PROPERTY_FONT) if short is not None else uir1.TextWidth(name.text))
        wide, narrow = skin.Width(value, 'text_s'), skin.Width(value, 'text_xs')
        small = taken + wide > right
        if short is not None:
            name.SetTight(small and taken + narrow > right)
        font = 'text_xs' if small else 'text_s'
        if font != self.font:
            uir1.SetFont(text, skin.kit.font(font))
            self.font = font
        if text.GetLocalPosition() != (right, self.cy):
            text.SetPosition(right, self.cy)


class JoinedName(object):
    """A Vlastnosti name as ONE R1 line: the uiscript writes it on two lines (<stem>_Text_Top / _Bottom: "Rychlost" /
    "pohybu"), which are hidden; the cell shows the short name of the stem (EXTENT_NAMES), Full() is the two lines
    joined (the hover hint). SetTight(True) shows the tight form of the stem (EXTENT_TIGHT), if it has one."""

    def __init__(self, skin, holder, pair, short, tight, pad, cy):
        self.pair, self.short, self.tight = pair, short, tight
        for line in pair:
            skin.rec.Hide(line)
        self.text = skin._new(uir1.Text(holder, short, pad, cy, skin.kit.font(PROPERTY_FONT), T.INK_DIM))

    def Full(self):
        return ' '.join(part for part in (line.GetText().strip() for line in self.pair) if part)

    def SetTight(self, tight):
        shown = self.tight if tight and self.tight else self.short
        if self.text.GetText() != shown:
            self.text.SetText(shown)


# owner 10. 10.: a class-dependent hint lists the line of the player's own class only (all four while the class is unknown)
CLASS_LABELS = (('Válečník:', 'Warrior:'), ('Ninja:', 'Ninja:'), ('Sura:', 'Sura:'), ('Šaman:', 'Shaman:'))


def _PlayerJob():
    try:
        import chr
        import player
        job = chr.RaceToJob(player.GetRace())
        return job if 0 <= job < len(CLASS_LABELS) else None
    except Exception:
        return None


def _OwnClassLines(body, job=None):
    job = _PlayerJob() if job is None else job
    if job is None:
        return body
    other = tuple(l for i, pair in enumerate(CLASS_LABELS) if i != job for l in pair)
    return '\n'.join(line for line in body.split('\n') if not line.startswith(other))



class StatHint(uir1.HitArea):
    """The hover hint of one cell of the grid (standard variant): STAT_HINTS of its stem in THE R1 hint (uir1 HintFace,
    tooltip variant C). It lies BESIDE the window - left of it, right of it when the screen has no room there -
    vertically centred on the row, so it never covers the hovered row nor the other cells of the grid (above the cell,
    as before, it lay on the row above).

    The area is a child of the hint layer on the window (not of the row): ``holder`` is the row it covers, ``dx`` /
    ``width`` its part of the row; Place() puts it over the row in window coordinates. The engine's IsIn includes the
    right and bottom edge, so the area is 1 px narrower and lower than the cell it covers (exactly the cell's pixels)."""

    def __init__(self, parent, holder, dx, width, window, stem):
        uir1.HitArea.__init__(self, parent, 0, 0, max(1, width - 1), BOX_H - 1)
        self.window, self.stem = window, stem
        self.holder, self.dx = holder, dx
        self.Place()

    def Place(self):
        hx, hy = self.holder.GetGlobalPosition()
        wx, wy = self.window.GetGlobalPosition()
        at = (hx - wx + self.dx, hy - wy)
        if self.GetLocalPosition() != at:
            self.SetPosition(*at)

    def Content(self):
        name, body = STAT_HINTS[self.stem]
        return _Tr(*name), _OwnClassLines(_Tr(*body))

    def Rect(self):
        """The anchor of the hint (global x, y, w, h): the window's columns on the row of this cell."""
        wx = self.window.GetGlobalPosition()[0]
        y = self.GetGlobalPosition()[1]
        return wx, y, self.window.GetWidth(), self.GetHeight()

    def OnMouseOverIn(self):
        uir1.HitArea.OnMouseOverIn(self)
        title, body = self.Content()
        rect = self.Rect()
        uir1.ShowHintAt(rect, title, body, side='left', edge=rect[0], owner=self)

    def OnMouseOverOut(self):
        uir1.HitArea.OnMouseOverOut(self)
        uir1.HideHint(self)

    def Destroy(self):
        if self.hovered:
            uir1.HideHint(self)
        self.hovered = False


class CharacterSkin(object):
    """R1 look of one CharacterWindow. A build failure undoes every change and re-raises (the window traces it)."""

    def __init__(self, window):
        self.window = window
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.mirrors = []
        self.boxes = []
        self.cells = []            # the cells of the grid without the champion level (Cell)
        self.names = []            # their Vlastnosti names (JoinedName)
        self.hints = []            # the hover hint of every cell of the grid (StatHint)
        self.hint_rows = []        # (row holder, width, stem) collected while the grid is built
        self.hint_layer = None     # their not-pickable layer on the window, above the board
        self.free_font = 'text_s'
        self.probes = {}           # font -> a hidden text line that measures widths
        self.quest = None
        self.level_type = None
        self.shown = {}            # last applied title / vein width / section: an image swap only on a change
        try:
            self._Build()
            self.Sync()
        except Exception:
            self.Undo()
            raise

    def _opt(self, name):
        """A child of the uiscript, None when this variant has no such element."""
        w = self.window
        return w.GetChild(name) if w.IsChild(name) else None

    def _new(self, widget):
        self.widgets.append(widget)
        return widget

    def _mirror(self, line, parent, x, y, font, color, align='center', fmt=None):
        mirror = uir1skin.Mirror(self.rec, line, parent, x, y, self.kit.font(font), color, align, fmt)
        self.mirrors.append(mirror)
        self.widgets.append(mirror.text)
        return mirror

    def _At(self, *names):
        """Window coordinates of the last named element from the local positions of its uiscript chain (the main page
        is at 0, 0): the exact place the uiscript gives an original control."""
        x = y = 0
        for name in names:
            lx, ly = self.window.GetChild(name).GetLocalPosition()
            x, y = x + lx, y + ly
        return x, y

    @staticmethod
    def original_image(slot):
        """The original texture of a value box (its width: value_small / value_middle / value_large)."""
        return CHAR + {39: 'value_small.tga', 52: 'value_middle.tga'}.get(slot.GetWidth(), 'value_large.tga')

    # ------------------------------------------------------------------ build
    def _Build(self):
        w, rec, kit = self.window, self.rec, self.kit
        board = w.GetChild('board')
        self.W, self.H = w.GetWidth(), w.GetHeight()
        self.champion = w.IsChild('base_info') and w.IsChild('change_base_button')
        # The frame draws inside the original background image (the first child of the board): every page and
        # control of the board draws above it in its own order.
        self._new(uir1.Frame(w.GetChild('Character_Background'), 0, 0, self.W, self.H, 'window'))
        overlay = self._opt('Character_Frame_Overlay')
        if overlay is not None:
            rec.Hide(overlay)
        self._BuildStatus()
        self._BuildSkills()
        self._BuildOtherPages()
        # Bottom tabs and the header last: above the pages (the X and the tabs take their clicks). The tabs lie over
        # the original tab buttons (their left edges, the original texts), centred on their 27 px height.
        control = w.GetChild('TabControl')
        rec.Hide(control)
        buttons = [w.GetChild(name) for name in TAB_BUTTONS]
        lefts = [b.GetLocalPosition()[0] for b in buttons]
        widths = [b - a for a, b in zip(lefts, lefts[1:])] + [buttons[-1].GetWidth()]
        first = buttons[0]
        x = control.GetLocalPosition()[0] + lefts[0]
        y = control.GetLocalPosition()[1] + first.GetLocalPosition()[1] + (first.GetHeight() - T.SEG_H) // 2
        labels = [w.GetChild(name).GetText() for name in TAB_LABELS]
        self.tabs = self._new(uir1skin.ProxySegment(board, kit, x, y, [(state, label, button) for state, label, button
                                                                        in zip(STATES, labels, buttons)], widths))
        self.titles = dict(zip(STATES, [_Locale(name, fallback) for name, fallback in TITLES]))
        self.header = self._new(uir1.Header(board, kit, self.W, self.titles['STATUS'],
                                            on_close=ui.__mem_func__(w.Close)))
        for button, stem in ((getattr(w, 'ExpandBtn', None), 'minimize'), (getattr(w, 'MinimizeBtn', None), 'expand')):
            if button is not None:          # the "Bonusy" ear (its art is mirrored: minimize = open)
                rec.Visuals(button, [ART + '%s_%s.png' % (stem, s) for s in ('normal', 'hover', 'pressed')],
                            [BELT + 'btn_%s_%s.tga' % (stem, s) for s in ('normal', 'over', 'down')])
        if self.hint_rows:
            # Last child of the window: picked before the board and everything in it (the tabs, the ear, a page or a
            # row holder too short for its cell); not pickable itself, so between the areas the board gets the mouse.
            self.hint_layer = layer = self._new(uir1.Layer(w, 0, 0, self.W, self.H, None))
            for holder, width, stem in self.hint_rows:
                self.hints.append(self._new(StatHint(layer, holder, 0, width, w, stem)))

    def _BuildStatus(self):
        """The main page in its original layout: portrait, name and guild, the row Úroveň | EXP | Potřebné, the
        sections Status postavy (with the free points inside its heading) and Vlastnosti."""
        w, rec = self.window, self.rec
        self.page = page = w.GetChild('Character_Page')
        self.layer = self._new(uir1.Layer(page, 0, 0, self.W, self.H, None))    # the header row texts
        face_slot, face = w.GetChild('Face_Slot'), w.GetChild('Face_Image')
        fx, fy = face_slot.GetLocalPosition()
        dy = max(0, CONTENT_TOP - fy)
        rec.Position(face_slot, fx, fy + dy)
        rec.Image(face_slot, ART + 'portrait_frame.png', CHAR + 'portrait_frame.tga')
        x, y = face.GetLocalPosition()
        rec.Position(face, x, y + dy)
        # Name and guild centred in their slots (RefreshCharacter places the slots, as in the original).
        for slot, line, role, color in (('Character_Name_Slot', 'Character_Name', 'text', T.IVORY),
                                        ('Guild_Name_Slot', 'Guild_Name', 'text_s', T.INK_DIM)):
            holder = w.GetChild(slot)
            self._mirror(w.GetChild(line), holder, (holder.GetWidth() or 90) // 2, (holder.GetHeight() or BOX_H) // 2,
                         role, color)
        self.header_rows = ([], [])                 # (R1 text, original centre x) of the labels and the values
        for label, value in (CHAMPION_HEADER if self.champion else STD_HEADER):
            for row, chain, role, color in ((0, label, 'text_s', T.INK_DIM), (1, value, 'text', T.IVORY)):
                x, y = self._At(*chain)
                mirror = self._mirror(w.GetChild(chain[-1]), self.layer, x, y + ORIGINAL_CAP, role, color)
                self.header_rows[row].append((mirror.text, x))
        for name in ('Lv_Exp_BackImg',):
            if self._opt(name) is not None:
                rec.Hide(w.GetChild(name))
        self.switch = None
        self.free_label = self.free_value = None
        if self.champion:
            self._BuildSwitch(page)
            self._BuildStatsChampion()
            self._BuildExtentChampion()
        else:
            self._BuildStatsStandard()
            self._BuildExtentStandard()
            # The uiscript's Character_Page is 304 px tall, the last Vlastnosti row (Rychl. kouzel, Vyhnutí) lies at
            # 304..322: the engine picks a child only inside its parent, so that row had no hover. The page reaches
            # down to the tabs.
            top = page.GetGlobalPosition()[1] - w.GetGlobalPosition()[1]
            if page.GetHeight() < self._TabsTop() - top:
                rec.Size(page, page.GetWidth(), self._TabsTop() - top)

    def _Section(self, container, bar, text, width):
        """An R1 section heading in place of a crimson bar: its text where the bar's text started, its height centred
        on the bar."""
        bx, by = bar.GetLocalPosition()
        section = uir1.Section(container, self.kit, bx + BAR_TEXT_X, 0, width, text)
        section.SetPosition(bx + BAR_TEXT_X, by - (section.Height() - BAR_H + 1) // 2)
        return self._new(section)

    def _Heading(self, container, bar, text, width, shift=0):
        """An R1 section heading of the grid (standard variant): its text CONTENT_MARGIN px from the window edge, where
        the grid starts, its height centred on the row of the bar of the uiscript (``shift`` px lower)."""
        x = CONTENT_MARGIN - self._Origin(container)
        section = uir1.Section(container, self.kit, x, 0, width, text)
        by = bar.GetLocalPosition()[1]
        section.SetPosition(x, by - (section.Height() - BAR_H + 1) // 2 + shift)
        return self._new(section)

    def Width(self, text, role):
        """Width in px of ``text`` in the font of the kit role (a hidden text line measures it)."""
        font = self.kit.font(role)
        probe = self.probes.get(font)
        if probe is None:
            probe = self.probes[font] = ui.TextLine()
            probe.SetFontName(font)
        probe.SetText(text)
        return uir1.TextWidth(probe)

    def _Buttons(self, names, visuals, originals):
        for name in names:
            if self._opt(name) is not None:
                self.rec.Visuals(self.window.GetChild(name), visuals, originals)

    def _BuildStatsStandard(self):
        """Without the champion level: the heading with "Volné body" and its number cell, the 8 cells of Status postavy
        (the original holders of the rows moved to the grid columns)."""
        w, rec = self.window, self.rec
        standard = w.GetChild('Status_Standard')
        sx, sy = standard.GetLocalPosition()
        rec.Size(standard, self.W - sx, w.GetChild('Status_Extent').GetLocalPosition()[1] - sy)
        bar, title = w.GetChild('Character_Bar_01'), self._opt('Character_Bar_01_Text')
        text = title.GetText() if title is not None else _Tr('Status postavy', 'Character status')
        for widget in (bar, title):
            if widget is not None:
                rec.Hide(widget)
        self.status_section = section = self._Heading(standard, bar, text, CONTENT_W)
        # Free points: the number in a cell (well_35) at the right end of the heading, "Volné body" right-aligned before
        # it (_FitFreePoints); the holder of the uiscript shows / hides all of it.
        plus = w.GetChild('Status_Plus_Label')
        ox = self._Origin(standard)
        top = section.GetLocalPosition()[1] + (section.Height() - BOX_H) // 2
        rec.Position(plus, self.W - CONTENT_MARGIN - CHIP_W - ox, top)
        rec.Size(plus, CHIP_W, BOX_H)
        chip = ui.ExpandedImageBox()
        chip.SetParent(plus)
        chip.AddFlag('not_pick')
        chip.LoadImage(Well(CHIP_W))
        chip.SetPosition(0, 0)
        chip.Show()
        self._new(chip)
        centre = BOX_H // 2
        self.free_value = self._mirror(w.GetChild('Status_Plus_Value'), plus, CHIP_W - CHIP_PAD, centre, 'text_s',
                                       T.IVORY, 'right')
        label = self._opt('Status_Plus_Text')
        if label is not None:
            self.free_label = self._mirror(label, plus, -FREE_GAP, centre, 'text_s', T.INK_DIM, 'right')
        self.free_holder = plus
        # The cells: name | value | + (left column), name | value (right column); the rows keep the y of the uiscript.
        left, right = CONTENT_MARGIN - ox, self.W - CONTENT_MARGIN - CELL_W - ox
        plus_x = CELL_W - PLUS_INSET - BUTTON
        for name in STD_LEFT:
            holder, slot = w.GetChild('%s_Label' % name), w.GetChild('%s_Slot' % name)
            rec.Position(holder, left, holder.GetLocalPosition()[1])
            button, minus = w.GetChild('%s_Plus' % name), w.GetChild('%s_Minus' % name)
            rec.Position(button, plus_x, button.GetLocalPosition()[1])
            rec.Position(minus, left + plus_x - BUTTON_GAP - BUTTON, minus.GetLocalPosition()[1])
            label = self._mirror(w.GetChild('%s_Text' % name), holder, STATUS_PAD, BOX_H // 2, 'text_s', T.INK_DIM,
                                 'left')
            self.cells.append(Cell(self, holder, slot, w.GetChild('%s_Value' % name), label, STATUS_PAD,
                                   lambda minus=minus: plus_x - VALUE_GAP -
                                   (BUTTON_GAP + BUTTON if minus.IsShow() else 0)))
            # the hint area ends where the reset - starts: the + / - keep their clicks and their own tooltips
            self.hint_rows.append((holder, plus_x - BUTTON_GAP - BUTTON, name))
        for stem, (holder, slot, value, text) in zip(STD_RIGHT_STEMS, STD_RIGHT):
            holder = w.GetChild(holder)
            rec.Position(holder, right, holder.GetLocalPosition()[1])
            label = self._mirror(w.GetChild(text), holder, STATUS_PAD, BOX_H // 2, 'text_s', T.INK_DIM, 'left')
            self.cells.append(Cell(self, holder, w.GetChild(slot), w.GetChild(value), label, STATUS_PAD))
            self.hint_rows.append((holder, CELL_W, stem))
        self._Buttons(['%s_Plus' % n for n in STD_LEFT], PLUS_R1, PLUS_ORIGINAL)
        self._Buttons(['%s_Minus' % n for n in STD_LEFT], MINUS_R1, MINUS_ORIGINAL)

    def _AddBox(self, holder, slot, value, limit=None, right_limit=None):
        """A value box. ``limit``: window x of what lies left of it (a name, an icon) - the box may grow up to
        GUTTER px after it; None = it never grows to the left. ``right_limit``: window x it may grow up to on the
        right (None: never)."""
        origin = self._Origin(holder)
        sx = slot.GetLocalPosition()[0]
        width = slot.GetWidth()
        ear = self._Ear()
        if ear is not None and origin + sx + width > ear[0]:
            top = holder.GetGlobalPosition()[1] - self.window.GetGlobalPosition()[1] + slot.GetLocalPosition()[1]
            if top < ear[1] + ear[3] and ear[1] < top + BOX_H:
                width = ear[0] - origin - sx
        box = Box(self, holder, slot, value, width, origin, limit or (lambda: origin + sx + width), right_limit)
        self.boxes.append(box)
        return box

    def _Origin(self, widget):
        """Window x of a page element (its global position minus the window's)."""
        return widget.GetGlobalPosition()[0] - self.window.GetGlobalPosition()[0]

    def _Ear(self):
        """(x, y, w, h) of the Bonusy ear in window coordinates, None without it."""
        w = self.window
        for button in (getattr(w, 'ExpandBtn', None), getattr(w, 'MinimizeBtn', None)):
            if button is not None:
                x, y = button.GetLocalPosition()
                return x, y, button.GetWidth() or 10, button.GetHeight() or 108
        return None

    def _TabsTop(self):
        """Window y of the original tab buttons (the R1 tabs lie over them)."""
        w = self.window
        return w.GetChild('TabControl').GetLocalPosition()[1] + w.GetChild(TAB_BUTTONS[0]).GetLocalPosition()[1]

    def _BuildExtentStandard(self):
        """Vlastnosti without the champion level: the heading and 6 cells (the original holders of the rows moved to the
        grid columns, EXTENT_ROWS_SHIFT px lower), each name ONE short line, its full name in the hover hint."""
        w, rec = self.window, self.rec
        extent = w.GetChild('Status_Extent')
        ex, ey = extent.GetLocalPosition()
        rec.Size(extent, self.W - ex, self._TabsTop() - ey)
        bar, title = w.GetChild('Status_Extent_Bar'), self._opt('Status_Extent_Label')
        text = title.GetText() if title is not None else _Tr('Vlastnosti', 'Properties')
        for widget in (bar, title):
            if widget is not None:
                rec.Hide(widget)
        self.extent_section = self._Heading(extent, bar, text, CONTENT_W, EXTENT_HEADING_SHIFT)
        ox = self._Origin(extent)
        columns = (CONTENT_MARGIN - ox, self.W - CONTENT_MARGIN - CELL_W - ox)
        per_column = len(STD_EXTENT) // 2
        cy = BOX_H // 2
        for index, (stem, holder, slot, value) in enumerate(STD_EXTENT):
            holder = w.GetChild(holder)
            rec.Position(holder, columns[index // per_column], holder.GetLocalPosition()[1] + EXTENT_ROWS_SHIFT)
            pair = [line for line in (self._opt('%s_Text_%s' % (stem, part)) for part in ('Top', 'Bottom'))
                    if line is not None]
            tight = EXTENT_TIGHT.get(stem)
            name = JoinedName(self, holder, pair, _Tr(*EXTENT_NAMES[stem]), _Tr(*tight) if tight else None,
                              EXTENT_PAD, cy)
            cell = Cell(self, holder, w.GetChild(slot), w.GetChild(value), name, EXTENT_PAD)
            self.cells.append(cell)
            self.names.append(name)
            self.hint_rows.append((holder, CELL_W, stem))

    def _BuildSwitch(self, page):
        """With the champion level: R1 tabs over the two original level buttons (their events and tooltips), from the
        first button's left edge to the second one's right edge."""
        levels = getattr(self.window, 'tabLevelInfoButtonDict', None)
        if not levels:
            return
        keys = sorted(levels)
        buttons = [levels[key] for key in keys]
        for button in buttons:
            self.rec.Hide(button)
        lefts = [b.GetLocalPosition()[0] for b in buttons]
        widths = [b - a for a, b in zip(lefts, lefts[1:])] + [lefts[1] - lefts[0] if len(lefts) > 1 else 79]
        y = buttons[0].GetLocalPosition()[1] + SWITCH_TOP_SHIFT
        names = (_Tr('Úroveň', 'Level'), _Tr('Šampión', 'Champion'))
        self.switch = self._new(uir1skin.ProxySegment(page, self.kit, lefts[0], y, [
            (key, label, button) for key, label, button in zip(keys, names, buttons)], widths))

    def _BuildStatsChampion(self):
        """With the champion level: the stat icons (original art) and boxes where the uiscript has them; the free
        points as the R1 + and the number in the heading."""
        w, rec = self.window, self.rec
        standard = w.GetChild('Status_Standard')
        sx, sy = standard.GetLocalPosition()
        rec.Size(standard, self.W - sx, w.GetChild('Status_Extent').GetLocalPosition()[1] - sy)
        bar, image = w.GetChild('Base_Info_bar'), w.GetChild('Char_Info_Status_img')
        for widget in (bar, image):
            rec.Hide(widget)
        plus = w.GetChild('Status_Plus_Label')
        px, py = plus.GetLocalPosition()
        width = px - GUTTER - bar.GetLocalPosition()[0] - BAR_TEXT_X
        section = self.status_section = self._Section(standard, bar, _Tr('Status postavy', 'Character status'), width)
        self._new(uir1skin.TooltipProxy(standard, section.GetLocalPosition()[0], section.GetLocalPosition()[1],
                                        uir1.TextWidth(section.label) + 4, section.Height(), image))
        nx, ny = px - (13 - FREE_ICON) // 2, py - (13 - FREE_ICON) // 2
        rec.Image(plus, PLUS_R1[0], WINDOWS + 'char_info_status_plus_img.sub')
        rec.Position(plus, nx, ny)
        rec.Hide(w.GetChild('Status_Plus_Btn_Img'))        # the 24 x 11 field: Noto Sans digits are 10 px tall
        value = w.GetChild('Status_Plus_Value')
        centre = section.GetLocalPosition()[1] + section.Height() // 2 - ny
        self.free_value = self._mirror(value, plus, value.GetLocalPosition()[0] + px - nx, centre, 'text_s', T.IVORY)
        for container in CHAMPION_ROWS:
            name, rows = container[0], container[1:]
            if not w.IsChild(name):
                continue
            holder = w.GetChild(name)
            for slot, value in rows:
                icon = self._Origin(holder) + 20 + ICON_W     # the stat icons of the uiscript at x 20
                self._AddBox(holder, w.GetChild(slot), w.GetChild(value), lambda icon=icon: icon)
        for holder, slot, value in CHAMPION_RIGHT:
            self._AddBox(w.GetChild(holder), w.GetChild(slot), w.GetChild(value))
        self._Buttons(CHAMPION_PLUS, PLUS_R1, PLUS_ORIGINAL)
        self._Buttons(['%s_Minus' % n for n in STD_LEFT], MINUS_R1, MINUS_ORIGINAL)

    def _BuildExtentChampion(self):
        """Vlastnosti with the champion level: the original icons and boxes, CHAMPION_EXTENT_SHIFT px lower (below
        the heading that took the bar's place)."""
        w, rec = self.window, self.rec
        extent = w.GetChild('Status_Extent')
        ex, ey = extent.GetLocalPosition()
        rec.Size(extent, self.W - ex, self._TabsTop() - ey)
        bar = w.GetChild('Status_Extent_Bar')
        for name in ('Status_Extent_Bar', 'Status_Extent_Label'):
            if self._opt(name) is not None:
                rec.Hide(w.GetChild(name))
        self.extent_section = self._Section(extent, bar, _Tr('Vlastnosti', 'Properties'),
                                            bar.GetWidth() - BAR_TEXT_X)
        for icon, holder, slot, value in CHAMPION_EXTENT:
            for name in (icon, holder):
                widget = w.GetChild(name)
                x, y = widget.GetLocalPosition()
                rec.Position(widget, x, y + CHAMPION_EXTENT_SHIFT)
            right = self._Origin(w.GetChild(icon)) + ICON_W
            box = self._AddBox(w.GetChild(holder), w.GetChild(slot), w.GetChild(value), lambda right=right: right)
            if box.origin > self.W // 2:          # the right column: free room up to the frame
                box.right_limit = self.W - FRAME_INSET

    def _BuildSkills(self):
        w, rec, kit = self.window, self.rec, self.kit
        page = w.GetChild('Skill_Page')
        board = w.GetChild('Skill_Board')
        bar = w.GetChild('Skill_ETC_Title_Bar')
        slot_y = w.GetChild('Skill_Active_Slot').GetLocalPosition()[1]
        bar_y = bar.GetLocalPosition()[1]
        # Tabs above the panel (never over it, never into the header), the panel 3 px above the first cell row.
        tabs_y = max(slot_y + SKILL_FIRST_ROW - 2 * SKILL_GAP - T.SEG_H, T.HEAD_H + T.CONTENT_GAP - PAGE_Y)
        x, y, pw = SKILL_PANEL_X, max(slot_y + SKILL_FIRST_ROW - SKILL_GAP, tabs_y + T.SEG_H + 2), SKILL_PANEL_W
        ph = bar_y - 2 - y
        self.skill_panel = (x, y, pw, ph)
        rec.Position(board, x, y)
        rec.Image(board, uir1.ROOT + 'textures/panel_dark.png', WINDOWS + 'skill_board.sub')
        self._new(uir1.Frame(board, 0, 0, pw, ph, 'panel'))
        self.board_expanded = self._opt('Skill_Board_expanded')
        if self.board_expanded is not None:
            rec.Hide(self.board_expanded)
        for name in ('Skill_Active_Slot', 'Skill_ETC_Slot'):
            rec.SlotBase(w.GetChild(name), SLOT_R1, SLOT_ORIGINAL)
        buff = getattr(w, 'buffPage', None)
        if buff is not None and getattr(buff, 'slots', None) is not None:
            rec.SlotBase(buff.slots, SLOT_R1, SLOT_ORIGINAL)
        # Schopnosti | Buffy in front of the original group buttons (their events: __SelectSkillGroup).
        groups = list(getattr(w, 'skillGroupButton', ()) or ())
        self.skill_tabs = None
        if len(groups) == 2:
            for button in groups:
                rec.Hide(button)
            x, y = SKILL_PANEL_X + SKILL_INSET, tabs_y
            row = getattr(w, 'skillHeaderRow', None)
            if row is not None:                 # the free points (row of uicharacterbuff) on the tabs' axis
                rec.Position(row, row.GetLocalPosition()[0], y + T.SEG_H // 2 - row.GetHeight() // 2)
            widths = SKILL_TAB_WIDTHS
            self.skill_tabs = self._new(uir1skin.ProxySegment(page, kit, x, y, [
                (0, _Tr('Schopnosti', 'Skills'), groups[0]), (1, _Tr('Buffy', 'Buffs'), groups[1])], widths))
        # Free skill points: label + large number inside the original point area (its tooltip, shown with the
        # skills group only).
        area = getattr(w, 'skillPointArea', None)
        self.points = None
        self.points_area = area
        if area is not None:
            aw = area.GetWidth()
            self.points = self._mirror(w.activeSkillPointValue, area, aw, 10, 'text_b', T.IVORY, 'right',
                                       fmt=LastNumber)
            self.points_label = self._new(uir1.Text(area, _Tr('Volné body', 'Free points'), 0, 11,
                                                    kit.font('text_s'), T.INK_DIM, align='right'))
        rec.Hide(bar)
        x, y, sw = SKILL_PANEL_X + SKILL_INSET, bar_y - 1, SKILL_PANEL_W - 2 * SKILL_INSET
        self.skill_section_box = (x, y, sw)
        self.skill_section = self._new(uir1.Section(page, kit, x, y, sw, _Tr('Standardní schopnosti', 'Standard skills')))
        support = self._opt('Support_Skill_ToolTip')
        if support is not None:
            self._new(uir1skin.TooltipProxy(page, x, y, 120, self.skill_section.Height(), support))

    def _BuildOtherPages(self):
        w, rec = self.window, self.rec
        for name in ('SoloEmotionSlot', 'DualEmotionSlot', 'SpecialEmotionSlot'):
            if w.IsChild(name):
                rec.SlotBase(w.GetChild(name), SLOT_R1, SLOT_ORIGINAL)
        self._BuildActionHeadings()
        if w.IsChild('Quest_Page') and w.IsChild('Quest_Row_00'):
            import uicharacterr1quest
            self.quest = uicharacterr1quest.QuestPage(self)

    def _BuildActionHeadings(self):
        """Akce: each crimson section bar (an image with the arrow) and its text become one R1 section heading that
        ends ACTION_HEADING_GAP above its slot grid, across the bar's width (both uiscript variants)."""
        self.action_headings = []
        page = self._opt('Emoticon_Page')
        if page is None:
            return
        for bar_name, text_name, slot_name, fallback in ACTION_HEADINGS:
            bar, text, slot = self._opt(bar_name), self._opt(text_name), self._opt(slot_name)
            if bar is None or slot is None:
                continue
            label = text.GetText() if text is not None else ''
            for widget in (bar, text):
                if widget is not None:
                    self.rec.Hide(widget)
            x, unused = bar.GetLocalPosition()
            section = uir1.Section(page, self.kit, x, 0, bar.GetWidth() or ACTION_HEADING_W, label or _Tr(*fallback))
            section.SetPosition(x, slot.GetLocalPosition()[1] - section.Height() - ACTION_HEADING_GAP)
            self.action_headings.append(self._new(section))


    # ------------------------------------------------------------------ state
    def Sync(self):
        """After the window changed its state or values: the title, the tabs, the hidden originals the window shows
        again (title bars, the second skill board), the mirrored values and what depends on their widths."""
        w = self.window
        state = getattr(w, 'state', 'STATUS')
        if state not in self.titles:
            state = 'STATUS'
        if self._Changed('title', state):
            self.header.SetTitle(self.titles[state])
        self.tabs.SetValue(state)
        self._SyncHints()
        for bar in (getattr(w, 'titleBarDict', None) or {}).values():
            bar.Hide()
        if self.board_expanded is not None:
            self.board_expanded.Hide()
        for mirror in self.mirrors:
            mirror.Sync()
        self._FitHeader()
        for box in self.boxes:
            box.Fit()
        self._FitCells()
        self._FitFreePoints()
        self.level_type = getattr(w, 'levelType', 0)
        if self.switch is not None:
            self.switch.SetValue(self.level_type)
        if self.skill_tabs is not None:
            self.skill_tabs.SetValue(getattr(w, 'selectedSkillTab', 0))
        if self.points is not None:
            right = self.points_area.GetWidth()
            self.points_label.SetPosition(right - uir1.TextWidth(self.points.text) - GUTTER, 11)
        self._FitSkillSection()
        if self.quest is not None:
            self.quest.Sync()

    def _FitHeader(self):
        """Úroveň | EXP | Potřebné: each text centred where the original was; a long number (EXP of a high level)
        moves right just enough to keep GUTTER px after the text before it."""
        for row in self.header_rows:
            right = None
            for text, anchor in row:
                width = uir1.TextWidth(text)
                x = anchor
                if right is not None and width and x - width // 2 < right + GUTTER:
                    x = right + GUTTER + width // 2
                y = text.GetLocalPosition()[1]
                if text.GetLocalPosition()[0] != x:
                    text.SetPosition(x, y)
                if width:
                    right = x - width // 2 + width

    def _FitCells(self):
        """Without the champion level: the value of every cell of the grid at its place, in its size."""
        for cell in self.cells:
            cell.Fit()

    def _FitFreePoints(self):
        """Without the champion level: the number inside its cell at the right end of the heading, "Volné body" FREE_GAP
        px before the cell, the heading's hairline GUTTER px before "Volné body" (the whole width without points)."""
        if self.free_label is None or self.free_value is None:
            return
        value, label = self.free_value.text, self.free_label.text
        font = 'text_s' if self.Width(self.free_value.line.GetText(), 'text_s') <= CHIP_W - 2 * PAD else 'text_xs'
        if font != self.free_font:
            uir1.SetFont(value, self.kit.font(font))
            self.free_font = font
        section = self.status_section
        width = CONTENT_W
        if self.free_holder.IsShow():
            left = self._Origin(self.free_holder) - FREE_GAP - uir1.TextWidth(label)
            width = min(CONTENT_W, left - GUTTER - self._Origin(section))
        if self._Changed('status_section', width):
            section.w = width
            section.SetSize(width, section.Height())
            section.SetText(section.label.GetText())

    def _FitSkillSection(self):
        """The heading ends before the permanent task / luck knot icons that share its row."""
        w = self.window
        x, y, sw = self.skill_section_box
        right = x + sw
        bottom = y + self.skill_section.Height()
        icons = list((getattr(w, 'permanentTaskButtons', None) or {}).values())
        icons.append(getattr(w, 'luckKnotButton', None))
        for icon in icons:
            if icon is not None and icon.IsShow():
                ix, iy = icon.GetLocalPosition()
                if iy < bottom and iy + icon.GetHeight() > y:
                    right = min(right, ix - 4)
        width = max(0, right - x)
        if not self._Changed('section', width):
            return
        section = self.skill_section
        for text in (_Tr('Standardní schopnosti', 'Standard skills'), _Tr('Standardní', 'Standard'), ''):
            section.label.SetText(text)
            if uir1.TextWidth(section.label) + 10 <= width or not text:
                break
        if section.w != width:
            section.w = width
        section.SetText(section.label.GetText())

    def _Changed(self, key, value):
        if self.shown.get(key, object()) == value:
            return False
        self.shown[key] = value
        return True

    def SyncSafe(self):
        """Sync() for the window's hooks: a failure is traced (syserr) and never breaks the window's own refresh."""
        try:
            self.Sync()
        except Exception:
            uir1.TraceFailure('the character window (state)')

    def SyncQuestSafe(self):
        """After RefreshQuest: only the quest page (its rows, lines and scroll bar)."""
        try:
            if self.quest is not None:
                self.quest.Sync()
        except Exception:
            uir1.TraceFailure('the character window (quests)')

    # ------------------------------------------------------------------ teardown
    def _SyncHints(self):
        """The hint areas only while the main page shows, each over its row."""
        layer = self.hint_layer
        if layer is None:
            return
        if self.page.IsShow():
            for hint in self.hints:
                hint.Place()
            if not layer.IsShow():
                layer.Show()
        elif layer.IsShow():
            for hint in self.hints:
                hint.Destroy()          # its hint goes away with it (no mouse-out from a hidden area)
            layer.Hide()

    def Undo(self):
        self.rec.Undo()
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets, self.mirrors, self.boxes, self.cells, self.names, self.quest = [], [], [], [], [], None
        self.hints, self.hint_rows, self.hint_layer = [], [], None

    def Destroy(self):
        uir1skin.Destroy(reversed(self.widgets))
        self.widgets, self.mirrors, self.boxes, self.cells, self.names = [], [], [], [], []
        self.rec.undo = []
        self.window = None
