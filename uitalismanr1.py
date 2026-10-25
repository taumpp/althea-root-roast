# -*- coding: utf-8 -*-
"""Talismany (uitalisman.TalismanWindow, a BoardWithTitleBar of 177 x 227) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the original window:

* the R1 frame and header (TALISMANY, the plain X closing through the window's own close request); the original
  title bar stays as an invisible drag handle, the window flags do not change;
* the body is the R1 panel of every R1 window (uir1.BoardSkin: the board's own base becomes the R1 panel tile). The
  original talisman board picture (TalismanBase: stone, vine ornament and the bronze slot frames) is hidden in R1 -
  it is not part of the R1 look (tester 8. 10. 2026);
* the six talisman slots are the R1 item slot C (uir1.SlotCell, 32 x 32) at the slot positions of the uiscript,
  drawn as children of the board base, so they lie under the slot window and its item icons;
* an empty slot shows which talisman goes there: the icon of the first item of that slot's family (Lovec, Strážce,
  Ničitel, Ochránce, Dobyvatel, Srdce), dimmed like an unavailable icon in the other R1 windows (alpha 0.35,
  uicustomportsr1 / uibiologr1). It is the slot's own watermark image showing that icon in R1, so the window's
  Refresh keeps showing it on an empty slot and hiding it under a talisman, exactly as with the original grey
  watermarks.

The slot positions, the six slots, the heart glow (TalismanActive), drag and drop, tooltips and Esc are unchanged.
Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps the
original look.
"""
import ui

import uir1
import uir1vybava as V

BOARD_Y = 23                   # the talisman board (and the slot window) start below the title bar
ORIGINAL_ASSETS = 'd:/ymir work/ui/game/crimson_ember/talisman/'
EMPTY_ALPHA = 0.35             # a dimmed icon in R1 (uicustomportsr1, uibiologr1)
# watermark of a slot -> (slot x, slot y in the slot window, the first item of the family) - locale/common/ui/
# talismanwindow.py and uitalisman.TALISMAN_FAMILY_RANGES (the heart: 10750 - 10754)
SLOTS = (
    ('TalismanWatermarkHunter', 'hunter', 72, 32, 9600),
    ('TalismanWatermarkGuardian', 'guardian', 22, 73, 9830),
    ('TalismanWatermarkBreaker', 'breaker', 123, 73, 10060),
    ('TalismanWatermarkProtector', 'protector', 41, 133, 10290),
    ('TalismanWatermarkConqueror', 'conqueror', 104, 133, 10520),
    ('TalismanWatermarkHeart', 'heart', 72, 88, 10750),
)


def IconPath(vnum):
    """The inventory icon of an item (item_list.txt), icon/item/<vnum>.tga when the client cannot tell."""
    try:
        import item
        item.SelectItem(vnum)
        path = item.GetIconImageFileName()
        if path:
            return path
    except Exception:
        pass
    return 'icon/item/%d.tga' % vnum


class TalismanSkin(object):
    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.skin = self.handle = None
        self.art = None
        self.cells = []
        self.marks = []                # (watermark, original path, original position)
        title = window.titleName.GetText()
        close = ui.__mem_func__(getattr(window, '_TalismanWindow__RequestClose'))
        try:
            self.skin = uir1.BoardSkin(window, kit, title, on_close=close)
            self.handle = V.DragHandle(window.titleBar, (window.titleName,))
            art = window.GetChild('TalismanBase')
            art.Hide()
            self.art = art
            base = self.skin.base
            bx, by = base.GetLocalPosition()
            for name, stem, x, y, vnum in SLOTS:
                self.cells.append(uir1.SlotCell(base, x - bx, BOARD_Y + y - by))
                mark = window.GetChild(name)
                self.marks.append((mark, ORIGINAL_ASSETS + 'watermark_%s.png' % stem, mark.GetLocalPosition()))
                mark.LoadImage(IconPath(vnum))          # a new image instance: the alpha is set after it
                mark.SetPosition(x, BOARD_Y + y)
                mark.SetAlpha(EMPTY_ALPHA)
        except Exception:
            self.Restore()
            raise

    def Restore(self):
        window = self.window
        if window is None:
            return
        for mark, path, (x, y) in self.marks:
            mark.LoadImage(path)
            mark.SetPosition(x, y)
            mark.SetAlpha(1.0)
        for cell in self.cells:
            cell.Hide()
            cell.Destroy()
        if self.art is not None:
            self.art.Show()
        if self.handle is not None:
            self.handle.Restore()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = self.handle = self.art = None
        self.cells, self.marks = [], []
        self.window = None

    Destroy = Restore
