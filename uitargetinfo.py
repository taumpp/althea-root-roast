# -*- coding: utf-8 -*-
"""Element and race icons of a monster target in the R1 look (owner 9. 10. 2026, variant B of the round
"cil-element-rasa"): a small reusable row of native 16 px icons that the target board puts after the name, before the
details icon ("?"). The unified target form (target + loot + DPS in one frame) can reuse it unchanged.

* the icons: every element of the proto (``nonplayer.GetElement`` > 0), then EVERY race of ``RaceFlags`` that has an
  icon (monsterpresentation.RACE_ASSETS - animal ... tree, zodiac); server-only flags (SUNGMAHEE, DECO, HIDE, ...)
  are unknown to the client and get none;
* at most ``MAX_INLINE`` (3) icons in the row; a 4th and more fold into the R1 count badge ("+N" on the red pill of
  the R1 bar, althea_r1_lista/badge/count_2.png) - with today's client data a mob has at most 3, so the badge is a
  safety net;
* hover: the R1 hover band behind the row (brightness, never red) and ONE shared tooltip that lists every element
  and race, what protects against the element, the race bonus and the weaknesses / resistances of the proto
  (``nonplayer.GetResist``: fire, lightning, wind, magic - the proto has no ice / earth / dark resistance);
* players and targets without an element and a race show nothing (width 0).

Every widget is made once (the icons on the first use, at most MAX_INLINE of them) and reused; ``SetMonster`` with
the same VNUM does nothing, so the board may call it from its per-update refresh.
"""
import ui
import localeInfo
import uiToolTip

import monsterpresentation
import uikit                   # the plain hover band (uikit.Rect); a row inside the board, no R1 window of its own
import uir1tokens as T

ICON = 16                  # native size of the icons (root/monster_indicators/*_16.png)
GAP = 2                    # between two icons and before the badge
PAD = 2                    # the hover band reaches this far around the icons (the row window includes it)
MAX_INLINE = 3
ROOT = monsterpresentation.RACE_ROOT                 # "monster_indicators/"
BADGE = 'd:/ymir work/ui/public/althea_r1_lista/badge/count_2.png'
BADGE_W, BADGE_H = 19, 13  # uir1listaart.SIZES["badge/count_2.png"]
BADGE_FONT = 'Tahoma:12'
WHITE = -1                 # 0xFFFFFFFF as the signed int of the x64 binding

# lower-case names of the proto resistances for the weakness / resistance lines (resist key, locale key, fallback)
RESISTS = (('MOB_RESIST_FIRE', 'TARGET_INFO_R1_RES_FIRE', 'fire'),
           ('MOB_RESIST_ELECT', 'TARGET_INFO_R1_RES_ELEC', 'lightning'),
           ('MOB_RESIST_WIND', 'TARGET_INFO_R1_RES_WIND', 'wind'),
           ('MOB_RESIST_MAGIC', 'TARGET_INFO_R1_RES_MAGIC', 'magic'))
# what protects against an element (index = monsterpresentation.ELEMENT_NAMES)
ELEMENT_RESIST_KEYS = ('TARGET_INFO_R1_RESIST_ELEC', 'TARGET_INFO_R1_RESIST_FIRE', 'TARGET_INFO_R1_RESIST_ICE',
                       'TARGET_INFO_R1_RESIST_WIND', 'TARGET_INFO_R1_RESIST_EARTH', 'TARGET_INFO_R1_RESIST_DARK')
ELEMENT_RESIST_FALLBACK = ('Lightning resistance', 'Fire resistance', 'Ice resistance', 'Wind resistance',
                           'Earth resistance', 'Darkness resistance')
BONUS_FALLBACK = {'ANIMAL': 'Strong against animals', 'UNDEAD': 'Strong against undead',
                  'DEVIL': 'Strong against devils', 'HUMAN': 'Strong against half-humans', 'ORC': 'Strong against orcs',
                  'MILGYO': 'Strong against mystics', 'INSECT': 'Strong against insects',
                  'DESERT': '', 'TREE': '', 'ZODIAC': ''}  # no "strong against" bonus of the game for these
FALLBACK = {'TARGET_INFO_R1_ELEMENT_LINE': 'Element of attack: %s - %s helps',
            'TARGET_INFO_R1_BONUS_LINE': 'Effective bonus: %s',
            'TARGET_INFO_R1_WEAKNESS_LINE': 'Weakness: %s',
            'TARGET_INFO_R1_STRONG_LINE': 'Resistance: %s'}


def Text(key, fallback=None):
    """The locale text of ``key``, ``fallback`` (English) for a locale without it."""
    value = getattr(localeInfo, key, None)
    if not value or value == key:
        return FALLBACK.get(key, key) if fallback is None else fallback
    return value


# --------------------------------------------------------------------------- model (pure)
def IconPaths(races, elements):
    """Elements first, then every race (indices of monsterpresentation.ELEMENT_ASSETS / RACE_ASSETS)."""
    paths = [ROOT + 'element_%s_%d.png' % (monsterpresentation.ELEMENT_ASSETS[index], ICON) for index in elements]
    paths += [ROOT + '%s_%d.png' % (monsterpresentation.RACE_ASSETS[index][1], ICON) for index in races]
    return tuple(paths)


def Split(count, maximum=MAX_INLINE):
    """(icons shown in the row, the rest folded into "+N"): all of them up to ``maximum``, else ``maximum`` icons and
    the badge with the rest (3 + "+1" for four, 3 + "+2" for five)."""
    count = max(0, int(count))
    if count <= maximum:
        return count, 0
    return maximum, count - maximum


def RowWidth(count):
    """Width of the icons (and the badge), without the hover padding."""
    shown, rest = Split(count)
    if not shown:
        return 0
    width = shown * ICON + (shown - 1) * GAP
    if rest:
        width += GAP + BADGE_W
    return width


def ReadResists(mobData):
    """(resist index of RESISTS, value) of the selected mob, only the non-zero ones; nothing on an older binding."""
    out = []
    for index, (name, _key, _fallback) in enumerate(RESISTS):
        try:
            value = int(mobData.GetResist(getattr(mobData, name)))
        except Exception:
            continue
        if value:
            out.append((index, value))
    return tuple(out)


def TooltipLines(races, elements, resists, isStone):
    """(title, ((text, kind), ...)) - kind 'text', 'positive' (helps the player) or 'negative'. Uses the existing
    race / element names of the locale (TARGET_INFO_RACE_*)."""
    names = [getattr(localeInfo, 'TARGET_INFO_RACE_' + monsterpresentation.ELEMENT_NAMES[index], '')
             for index in elements]
    names += [getattr(localeInfo, monsterpresentation.RACE_ASSETS[index][2], '') for index in races]
    title = u' · '.join(name for name in names if name)
    if not title:
        title = localeInfo.TARGET_INFO_RACE_METIN if isStone else getattr(localeInfo, 'TARGET_INFO_RACE_UNKNOWN', '')
    lines = []
    for index in elements:
        element = getattr(localeInfo, 'TARGET_INFO_RACE_' + monsterpresentation.ELEMENT_NAMES[index], '')
        protect = Text(ELEMENT_RESIST_KEYS[index], ELEMENT_RESIST_FALLBACK[index])
        lines.append((Text('TARGET_INFO_R1_ELEMENT_LINE') % (element, protect), 'text'))
    bonuses = [Text('TARGET_INFO_R1_BONUS_' + monsterpresentation.RACE_ASSETS[index][0],
                    BONUS_FALLBACK.get(monsterpresentation.RACE_ASSETS[index][0], '')) for index in races]
    bonuses = [bonus for bonus in bonuses if bonus]
    if bonuses:
        lines.append((Text('TARGET_INFO_R1_BONUS_LINE') % ', '.join(bonuses), 'positive'))
    weak = [(index, value) for index, value in resists if value < 0]
    strong = [(index, value) for index, value in resists if value > 0]
    if weak:
        lines.append((Text('TARGET_INFO_R1_WEAKNESS_LINE') % ', '.join(
            '%s %d %%' % (Text(RESISTS[index][1], RESISTS[index][2]), value) for index, value in weak), 'positive'))
    if strong:
        lines.append((Text('TARGET_INFO_R1_STRONG_LINE') % ', '.join(
            '%s %d %%' % (Text(RESISTS[index][1], RESISTS[index][2]), value) for index, value in strong), 'negative'))
    return title, tuple(lines)


# --------------------------------------------------------------------------- the row
class TargetInfoIcons(ui.Window):
    """The icon row of one target board (or form). ``SetMonster(vnum)`` returns the row's width (0 = nothing to
    show); the owner places the row with ``SetPosition`` (its top-left is the hover band's corner, the icons start
    PAD px inside)."""
    ICON = ICON
    PAD = PAD

    def __init__(self, parent):
        self.tooltip = None              # Hide is called by the base constructor before the widgets exist
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.icons = []
        self.vnum = None
        self.count = 0
        self.title = ''
        self.lines = ()
        self.band = uikit.Rect(self, 0, 0, 1, ICON + 2 * PAD, T.BAND_HOVER, T.BAND_ALPHA['hover'])
        self.band.AddFlag('not_pick')
        self.band.Hide()
        self.badge = ui.ExpandedImageBox()
        self.badge.SetParent(self)
        self.badge.LoadImage(BADGE)
        self.badge.SAFE_SetStringEvent('MOUSE_OVER_IN', self.ShowTooltip)
        self.badge.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.HideTooltip)
        self.badge.Hide()
        self.badgeText = ui.TextLine()
        self.badgeText.SetParent(self.badge)
        self.badgeText.AddFlag('not_pick')
        self.badgeText.SetFontName(BADGE_FONT)
        self.badgeText.SetPackedFontColor(WHITE)
        self.badgeText.SetHorizontalAlignCenter()
        self.badgeText.SetPosition(BADGE_W // 2, 0)
        self.badgeText.Show()
        self.tooltip = uiToolTip.ToolTip()
        self.SetSize(0, ICON + 2 * PAD)
        self.Hide()

    def _Icon(self, index):
        while len(self.icons) <= index:
            icon = ui.ExpandedImageBox()
            icon.SetParent(self)
            icon.SAFE_SetStringEvent('MOUSE_OVER_IN', self.ShowTooltip)
            icon.SAFE_SetStringEvent('MOUSE_OVER_OUT', self.HideTooltip)
            icon.Hide()
            self.icons.append(icon)
        return self.icons[index]

    def SetMonster(self, vnum, mobData=None, elementsEnabled=None, liveElements=None):
        """Reads the mob once per VNUM (monsterpresentation.ReadMonster, never the previous selection for a missing
        VNUM) and lays the row out. Returns the row's width with the hover padding, 0 when there is nothing."""
        vnum = int(vnum or 0)
        elementKey = None if liveElements is None else tuple(sorted(liveElements.items()))
        cacheKey = (vnum, elementKey)
        if cacheKey == getattr(self, "monsterCacheKey", None):
            return self.GetWidth() if self.count else 0
        self.HideTooltip()
        self.vnum = vnum
        self.monsterCacheKey = cacheKey
        if mobData is None:
            import nonplayer as mobData
        if elementsEnabled is None:
            import app
            elementsEnabled = getattr(app, 'ENABLE_ELEMENT_ADD', False)
        races, elements, isStone = monsterpresentation.ReadMonster(vnum, elementsEnabled, mobData)
        if liveElements is not None:
            elements = tuple(index for index in range(len(monsterpresentation.ELEMENT_NAMES))
                             if elementsEnabled and not isStone and liveElements.get(index, 0) > 0)
        resists = ReadResists(mobData) if (races or elements) else ()
        paths = IconPaths(races, elements)
        self.count = len(paths)
        self.title, self.lines = TooltipLines(races, elements, resists, isStone) if paths else ('', ())
        shown, rest = Split(self.count)
        for index in range(shown):
            icon = self._Icon(index)
            icon.LoadImage(paths[index])
            icon.SetPosition(PAD + index * (ICON + GAP), PAD)
            icon.Show()
        for icon in self.icons[shown:]:
            icon.Hide()
        if rest:
            self.badge.SetPosition(PAD + shown * (ICON + GAP), PAD + (ICON - BADGE_H) // 2)
            self.badgeText.SetText('+%d' % rest)
            self.badge.Show()
        else:
            self.badge.Hide()
        width = RowWidth(self.count)
        self.SetSize(width + 2 * PAD if width else 0, ICON + 2 * PAD)
        self.band.SetSize(max(1, width + 2 * PAD), ICON + 2 * PAD)
        return self.GetWidth() if width else 0

    def Clear(self):
        self.monsterCacheKey = None
        self.HideTooltip()
        self.vnum = None
        self.count = 0
        self.Hide()

    def ShowTooltip(self):
        if not self.tooltip or not self.IsShow() or not self.count:
            return
        self.band.Show()
        colors = {'text': self.tooltip.FONT_COLOR, 'positive': self.tooltip.POSITIVE_COLOR,
                  'negative': self.tooltip.NEGATIVE_COLOR}
        self.tooltip.ClearToolTip()
        self.tooltip.SetThinBoardSize(uiToolTip.ToolTip.TOOL_TIP_WIDTH)
        self.tooltip.SetTitle(self.title)
        for text, kind in self.lines:
            self.tooltip.AutoAppendTextLine(text, colors[kind])
        self.tooltip.AlignHorizonalCenter()
        self.tooltip.ShowToolTip()

    def HideTooltip(self):
        band = getattr(self, 'band', None)
        if band is not None:
            band.Hide()
        if self.tooltip:
            self.tooltip.HideToolTip()

    def Hide(self):
        self.HideTooltip()
        ui.Window.Hide(self)

    def Destroy(self):
        self.HideTooltip()
        self.icons = []
        self.tooltip = None
        self.band = None
        self.badge = None
        self.badgeText = None
