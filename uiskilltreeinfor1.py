# -*- coding: utf-8 -*-
"""Hodnoty rozkladu (uiskilltreedismantle.SkillTreePointInfo, opened by the book button of the skill tree window
"Rozklad") in the Althea R1 look "Krvavá žíla".

The window keeps its flags (movable, float), its list of the accepted items with their points (fifteen rows, the
mouse wheel, the scroll bar) and every function: uiskilltreedismantle keeps all of that logic; this module only draws
it in R1, with the attribute names the window drives:

* the R1 frame and the red R1 header (title, vein, plain X) on the window's own board (uir1.BoardSkin);
* the column headings as R1 labels over a quiet divider, the rows without the black well and the bronze lines: the
  item icon (the original scaled item icon), the name and the points in Noto Sans and the R1 ink, a hairline under
  every row;
* the narrow R1 scroll bar instead of the flat 11 px one, so the hint "posuň seznam" is gone: the footer shows only
  the range "1-15 z 23";
* compact: the window is 300 x 386 px instead of 320 x 400, the list starts 10 px higher.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building R1 restores
the original look (traced to syserr) and R1 is not tried again in this session. The look is chosen when the window
is built.
"""
import ui

import uir1
import uir1tokens as T

import uiskilltreedismantle as D
import uipermanenttasksr1 as R

WHAT = u'Hodnoty rozkladu'
TITLE = u'Hodnoty rozkladu'
ORIGINAL_SIZE = (320, 400)
WIDTH = 300
LEFT = T.PAD                                    # the content's left edge
HEADINGS_Y = 31                                 # the column headings (text_sb, top-aligned)
DIVIDER_Y = 49                                  # the divider under them
LIST_Y = 54                                     # the first row (64 in the original)
ROWS, ROW_H = D.INFO_VISIBLE_ROWS, D.INFO_ROW_HEIGHT
SCROLL_GAP = 6
SCROLL_X = WIDTH - T.PAD - T.SCROLL_W           # the narrow R1 bar at the right edge of the content
LIST_RIGHT = SCROLL_X - SCROLL_GAP              # the rows' right edge
ICON_X, ICON = LEFT + 2, 16                     # the item icon (a 32 px icon at half scale)
NAME_X = ICON_X + ICON + 8
POINTS_RIGHT = LIST_RIGHT - 4                   # the points are right aligned here
FOOTER_Y = LIST_Y + ROWS * ROW_H + 5            # "1-15 z 23"
FOOTER_H = 16
HEIGHT = FOOTER_Y + FOOTER_H + T.PAD - 3
ROW_LINE = 0x3A3636                             # the hairline under a row (a dim graphite, over the window base)
FOOTER_KEY = 'info_range'                       # skilltreelocale: the range without the hint "posuň seznam"


class Skin(R.SkinBase):
    def Build(self):
        win, kit = self.window, self.kit
        self.reload(lambda: win.SetSize(*ORIGINAL_SIZE), lambda: win.SetSize(WIDTH, HEIGHT))
        title = TITLE
        try:
            title = win.titleName.GetText() or TITLE
        except Exception:
            pass
        self.board = uir1.BoardSkin(win, kit, title, on_close=ui.__mem_func__(win.Close))

        # the black well and the bronze divider of the original: the R1 base and a quiet divider instead
        self.hide(win.body)
        self.hide(win.divider)
        heading = kit.font('text_sb')
        self.swap(win, 'itemHeader', uir1.Text(win, win.itemHeader.GetText(), ICON_X, HEADINGS_Y, heading,
                                               R.Signed(T.MUTED), valign='top'))
        self.swap(win, 'pointHeader', uir1.Text(win, win.pointHeader.GetText(), POINTS_RIGHT, HEADINGS_Y, heading,
                                                R.Signed(T.MUTED), align='right', valign='top'))
        self.own(uir1.Divider(win, LEFT, DIVIDER_Y, WIDTH - 2 * LEFT))

        font = kit.font('text_s')
        top = uir1.CellTop(ROW_H - 1, font)
        old_rows, rows = win.rows, []
        for index, row in enumerate(old_rows):
            for widget in row:
                self.hide(widget)
            y = LIST_Y + index * ROW_H
            icon = self.own(ui.ExpandedImageBox())
            icon.SetParent(win)
            icon.AddFlag('not_pick')
            icon.SetPosition(ICON_X, y + (ROW_H - 1 - ICON) // 2)
            name = self.own(uir1.Text(win, u'', NAME_X, y + top, font, R.Signed(T.INK), valign='top'))
            points = self.own(uir1.Text(win, u'', POINTS_RIGHT, y + top, font, R.Signed(T.IVORY), align='right',
                                        valign='top'))
            line = self.own(uir1.Rect(win, LEFT, y + ROW_H - 1, LIST_RIGHT - LEFT, 1, ROW_LINE))
            for widget in (icon, name, points, line):
                widget.Hide()                       # the window shows the rows it fills (Open / _RefreshRows)
            rows.append((icon, name, points, line))
        self.reload(lambda: setattr(win, 'rows', old_rows), lambda: setattr(win, 'rows', rows))

        footer = win.footer
        self.swap(win, 'footer', uir1.Text(win, footer.GetText(), LEFT + (LIST_RIGHT - LEFT) // 2, FOOTER_Y, font,
                                           R.Signed(T.MUTED), align='center', valign='top'))
        self.reload(lambda: setattr(win, 'footerKey', D.INFO_FOOTER_KEY), lambda: setattr(win, 'footerKey', FOOTER_KEY))

        bar = uir1.ScrollBar(kit)
        bar.SetParent(win)
        bar.SetPosition(SCROLL_X, LIST_Y)
        bar.SetScrollBarSize(ROWS * ROW_H)
        bar.SetScrollEvent(ui.__mem_func__(win._OnScroll))
        self.swap(win, 'scroll', bar)
        return self

    def Destroy(self):
        self.window = None
        self.widgets, self.swaps, self.hidden, self.moved, self.reloads = [], [], [], [], []
        self.board = None


def Build(window):
    """The R1 look of a SkillTreePointInfo (its original widgets already made), or None for the original look
    ("Starý vzhled", or R1 failed: then the original look is back)."""
    if not R.UseR1(WHAT):
        return None
    skin = Skin(window)
    try:
        skin.Build()
    except Exception:
        R.Fail(WHAT)
        skin.Undo()
        return None
    return skin
