# -*- coding: utf-8 -*-
"""Bojová propustka (the Battle Pass window, root/ui_bpass.py) in the Althea R1 look (visual only; ALTHEA_R1_KIT.md).

ui_bpass.BattlePassWindow stays the window with every function (missions by Denní / Týdenní / Měsíční, skipping a
mission, the free and premium reward tracks with their scroll bar, the premium preview, collecting, the season
timer, the level and EXP bar). This module dresses it in place and can undress it again (Settings -> "Starý
vzhled" takes effect when the window is shown next):

* the R1 frame and header on the window's board (uir1.BoardSkin: the title in Cinzel, the red vein, the plain X),
  resized when the window switches between the missions (345 px) and the rewards (320 px);
* the Denní / Týdenní / Měsíční row as one dark R1 row (the selected cell a dark well with the red line), the
  Přeskočit and premium preview buttons as dark R1 buttons (tools/build_althea_r1_trh.py, the original sizes);
* the mission list's box and both scroll bars in the R1 colours (the vertical one drawn as the narrow R1 bar), the
  season timer in the R1 text colour.

The reward art (mission rows, the Free / Premium track, the lock, the banner, the EXP gauge and its animation)
stays the original art. The window keeps its size.
"""
import grp
import localeInfo

import uir1 as R
import uir1layout as RL
import uir1tokens as T

TITLE = 'Bojová propustka'
R1_DIR = 'd:/ymir work/ui/public/althea_r1_trh/bpass/'
ORIGINAL_DIR = 'd:/ymir work/ui/game/battle_pass_reworked/'
SCROLL_DIR = 'd:/ymir work/ui/game/gameoption/scrollbar/'
TAB_NAMES = ('l', 'm', 'r')


def _packed(color, alpha=1.0):
    return grp.GenerateColor(((color >> 16) & 255) / 255.0, ((color >> 8) & 255) / 255.0, (color & 255) / 255.0,
                             alpha)


def ButtonPath(path):
    """R1 file of the original mission / preview button (slice/quest/btn_<0|1|2>.png), else None."""
    for index, state in enumerate(('normal', 'hover', 'pressed')):
        if path == ORIGINAL_DIR + 'slice/quest/btn_%d.png' % index:
            return R1_DIR + 'button_%s.png' % state
    return None


def StyleButtonText(kit, button):
    line = getattr(button, 'ButtonText', None)
    if line is not None:
        R.SetFont(line, kit.font('text_s'), line.GetText())
        line.SetPackedFontColor(T.BUTTON_TEXT)


class _Visuals(object):
    """Button visuals swapped to R1 and back (the original paths are known from ui_bpass)."""

    def __init__(self):
        self.saved = []

    def Set(self, button, up, over, down, original):
        self.saved.append((button, original))
        button.SetUpVisual(up)
        button.SetOverVisual(over)
        button.SetDownVisual(down)

    def Restore(self):
        for button, (up, over, down) in self.saved:
            button.SetUpVisual(up)
            button.SetOverVisual(over)
            button.SetDownVisual(down)
        self.saved = []


class VerticalBar(object):
    """ui_bpass.ScrollBarNew (the mission list) drawn as the narrow R1 bar: its three track images show the R1 track
    and the thumb images are replaced by the R1 thumb inside its own MiddleBar; size, dragging and the wheel stay the
    bar's. Restore() brings the original images and their layout back."""

    TRACK = ('scroll_top.tga', 'scroll_mid.tga', 'scroll_bottom.tga')
    THUMB = ('top', 'topScale', 'bottom', 'bottomScale', 'middle')

    def __init__(self, bar):
        self.bar = bar
        self.track = R.Ops(bar)
        self.track.items = [bar.middleImage, bar.topImage, bar.bottomImage]
        thumb = bar.middleBar
        for name in self.THUMB:
            getattr(thumb, name).Hide()
        self.thumb = R.Ops(thumb)
        self._bar_size = bar.SetScrollBarSize
        self._thumb_size = thumb.SetSize
        bar.SetScrollBarSize = self.SetScrollBarSize
        thumb.SetSize = self.SetThumbSize
        self._Track()
        self._Thumb()

    def SetScrollBarSize(self, height):
        self._bar_size(height)
        self._Track()

    def SetThumbSize(self, height):
        self._thumb_size(height)
        self._Thumb()

    def _Track(self):
        self.track.Apply(RL.vscroll('track', 'normal', 0, 0, max(T.SCROLL_MIN, self.bar.GetHeight())))

    def _Thumb(self):
        thumb = self.bar.middleBar
        self.thumb.dx = max(0, (thumb.GetWidth() - T.THUMB_W) // 2)
        self.thumb.Apply(RL.vscroll('thumb', 'normal', 0, 0, max(1, thumb.GetHeight())))

    def Restore(self):
        bar, thumb = self.bar, self.bar.middleBar
        for name in ('SetScrollBarSize',):
            bar.__dict__.pop(name, None)
        thumb.__dict__.pop('SetSize', None)
        self.thumb.Hide()
        for image, name in zip((bar.topImage, bar.middleImage, bar.bottomImage), self.TRACK):
            image.LoadImage(SCROLL_DIR + name)
            image.Show()
        bar.middleImage.SetPosition(0, bar.topImage.GetHeight())
        for name in self.THUMB:
            getattr(thumb, name).Show()
        height = bar.GetHeight()
        bar.SetScrollBarSize(height)
        thumb.SetSize(thumb.GetHeight())


class HorizontalBar(object):
    """ui.WikiScrollBar (the reward tracks) in the R1 colours: a dark track with a graphite outline and the graphite
    thumb (the bars are ui.Bar fills; nothing else changes)."""

    def __init__(self, bar):
        self.bar = bar
        last = len(bar.bars) - 1
        for index, piece in enumerate(bar.bars):
            piece.SetColor(_packed(0xFF0A0909) if index == last else _packed(0xFF3A3636))
        bar.middleBar.middle.SetColor(_packed(0xFF5C5654))

    def Restore(self):
        bar = self.bar
        last = len(bar.bars) - 1
        for index, piece in enumerate(bar.bars):
            piece.SetColor(bar.BASE_COLOR if index == last else bar.CORNERS_AND_LINES_COLOR)
        bar.middleBar.middle.SetColor(bar.middleBar.MIDDLE_BAR_COLOR)


class BattlePassSkin(object):
    """The R1 dressing of one BattlePassWindow. If dressing raises, what was dressed is undressed before the
    exception goes on (the window then stays in its original look)."""

    def __init__(self, window, kit=None):
        self.window = window
        self.kit = kit or R.Kit()
        self.board = None
        self.visuals = _Visuals()
        self.bars = []
        self.box = None
        try:
            self._Dress()
        except Exception:
            self.Restore()
            raise

    def _Dress(self):
        window, kit = self.window, self.kit
        self.board = R.BoardSkin(window.Board, kit, TITLE, on_close=window.Close)
        for name, button in zip(TAB_NAMES, window.categories):
            original = tuple(ORIGINAL_DIR + 'slice/quest/btn_%s_%d.png' % (name, n) for n in (0, 1, 1))
            self.visuals.Set(button, R1_DIR + 'tab_%s_normal.png' % name, R1_DIR + 'tab_%s_hover.png' % name,
                             R1_DIR + 'tab_%s_selected.png' % name, original)
            StyleButtonText(kit, button)
        original = tuple(ORIGINAL_DIR + 'slice/quest/btn_%d.png' % n for n in (0, 1, 2))
        self.visuals.Set(window.btnPreviewPremium, *(tuple(ButtonPath(path) for path in original) + (original,)))
        StyleButtonText(kit, window.btnPreviewPremium)
        box = window.board_Base
        box.SetBorderColor(_packed(T.LINE))
        box.SetBaseColor(_packed(0xFF0A0909, 0.85))
        self.box = box
        self.bars.append(VerticalBar(window.ScrollBarItem))
        self.bars.append(HorizontalBar(window.ScrollBarItems))
        window.wndSeasonRemain.SetPackedFontColor(T.INK_DIM)
        self.Resize()

    def Resize(self):
        board = self.window.Board
        if self.board is not None:
            self.board.Resize(board.GetWidth(), board.GetHeight())

    def Restore(self):
        window = self.window
        if self.board is not None:
            self.board.Restore()
            self.board = None
        self.visuals.Restore()
        for button in list(getattr(window, 'categories', ())) + [getattr(window, 'btnPreviewPremium', None)]:
            line = getattr(button, 'ButtonText', None)
            if line is not None:
                R.SetFont(line, localeInfo.UI_DEF_FONT, line.GetText())
                line.SetPackedFontColor(0xFFFFFFFF)
        if self.box is not None:
            self.box.SetBorderColor(self.box.DEFAULT_BORDER_COLOR)
            self.box.SetBaseColor(self.box.DEFAULT_BASE_COLOR)
            self.box = None
        for bar in self.bars:
            bar.Restore()
        self.bars = []
        season = getattr(window, 'wndSeasonRemain', None)
        if season is not None:
            season.SetPackedFontColor(0xFFC6B38D)
