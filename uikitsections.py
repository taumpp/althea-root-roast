# -*- coding: utf-8 -*-
"""Section separation of the settings pages (2026-10-06): ONE place to switch the look.

The owner waits for the team's vote on the separation of sections and rows (design v5 section 1):
today's look stays ('v5'); SECTION_STYLE switches every
settings page that lays out rows (the shell rows of uisettingsc9rows, Klávesové zkratky, the heading of Fronta
kamenů) to one of the design variants:

  'v5'  today: small semibold heading + a bronze rule to the right edge, a fine line under every row
  'A'   plates without a frame: every section on a slightly lighter plate, the heading inside, faint row lines
  'B'   ornate centred heading between two full-width rules with diamonds, no row lines
  'C'   the heading as a small tab on the section rule, a faint tint under the section, no row lines
  'D'   a ruby heading band with a stripe on the left, alternating row shades, no lines
  'E'   a thin brass stripe along the whole section, rows indented, almost invisible row lines
  'F'   only air and type: a bigger heading, more space above it, no lines, no background

A–F are drawn from plain primitives (ui.Bar, text, the kit rule and diamond) as a prepared approximation of the
mock-ups for the vote - the chosen one gets its final polish afterwards. A layout calls, per section:

  style = Style(kit)
  section = style.Open(parent, x, y, w, track)          # widgets UNDER the rows (plate / stripe / tint), sized later
  y += style.Heading(parent, x, y, w, text, track)      # heading (+ the space under it)
  ... rows: style.RowBack(...) before a row, its content inset by style.Inset(), style.RowLine(...) after it ...
  y += style.Close(section, y)                          # sizes the plate to the rows, returns the padding below

``track(widget)`` registers each widget with the page (cleared on a page change). Children draw in creation order,
so everything under the rows is created by Open() / RowBack() before the rows.
"""
import ui
import uikit
import uikittokens as T

SECTION_STYLE = 'v5'


class SectionV5(object):
    """Today's look (settings v5 fix): uikit.Section heading, a fine line under every row."""
    name = 'v5'

    def __init__(self, kit):
        self.kit = kit
        self.big = kit.prof == '1080'

    # ---------------------------------------------------------------- section
    def Gap(self, first):
        """Space above a heading (none above the first one)."""
        return 0 if first else (16 if self.big else 12)

    def Open(self, parent, x, y, w, track):
        return dict(x=x, y=y, w=w, widgets=[])

    def Heading(self, parent, x, y, w, text, track):
        section = track(uikit.Section(parent, self.kit, x, y, w, text))
        return section.Height() + (6 if self.big else 4)

    def Close(self, section, y):
        return 0

    # ---------------------------------------------------------------- rows
    def Inset(self):
        """(left, right) inset of the row content inside a section."""
        return 0, 0

    def RowBack(self, parent, x, y, w, h, index, track):
        return None

    def RowLine(self, parent, x, y, w, track):
        return track(uikit.HLine(parent, x, y, w, T.ROW_LINE))


def _Rect(parent, x, y, w, h, packed, alpha, track):
    return track(uikit.Rect(parent, x, y, max(1, w), max(1, h), packed, alpha))


class SectionA(SectionV5):
    """A · plates without a frame: a lighter plate (corners cut by 1 px) under the heading and rows of a section."""
    name = 'A'
    PAD = 12

    def Gap(self, first):
        return 0 if first else (10 if self.big else 8)

    def Open(self, parent, x, y, w, track):
        # three bars = a plate with 1 px cut corners (no frame), sized in Close()
        bars = [_Rect(parent, x, y, w, 1, T.PANEL_HI, .8, track) for unused in range(3)]
        return dict(x=x, y=y, w=w, widgets=bars)

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('Sb') + (18 if self.big else 12)
        track(uikit.Text(parent, text, x + self.PAD, y + h // 2, k.font('Sb'), T.GOLD_HI))
        return h

    def Close(self, section, y):
        if section is None:
            return 0
        x, top, w = section['x'], section['y'], section['w']
        bottom = y + 4
        middle, upper, lower = section['widgets']
        middle.SetPosition(x, top + 1)
        middle.SetSize(w, max(1, bottom - top - 2))
        upper.SetPosition(x + 1, top)
        upper.SetSize(w - 2, 1)
        lower.SetPosition(x + 1, bottom - 1)
        lower.SetSize(w - 2, 1)
        return 4

    def Inset(self):
        return self.PAD, self.PAD

    def RowLine(self, parent, x, y, w, track):
        return track(uikit.HLine(parent, x + self.PAD, y, w - 2 * self.PAD, T.ROW_LINE, .7))


class SectionB(SectionV5):
    """B · ornate centred heading: rules over the whole width, diamonds beside the text; rows without lines."""
    name = 'B'

    def Gap(self, first):
        return 0 if first else (12 if self.big else 8)

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('Mb') + (16 if self.big else 10)
        cy = y + h // 2
        label = track(uikit.Text(parent, text, x + w // 2, cy, k.font('Mb'), T.GOLD, align='center'))
        tw = uikit.TextWidth(label)
        bw, bh = k.size('bullet/diamond_selected.png')
        gap = 10
        left_end = x + w // 2 - tw // 2 - gap - bw
        right_start = x + w // 2 + tw // 2 + gap
        track(uikit.Image(parent, k.rel('bullet/diamond_selected.png'), left_end, cy - bh // 2))
        track(uikit.Image(parent, k.rel('bullet/diamond_selected.png'), right_start, cy - bh // 2))
        track(uikit.HLine(parent, x, cy, max(0, left_end - 8 - x), T.BRONZE_LINE_DK))
        track(uikit.HLine(parent, right_start + bw + 8, cy, max(0, x + w - right_start - bw - 8), T.BRONZE_LINE_DK))
        return h + 2

    def RowLine(self, parent, x, y, w, track):
        return None


class SectionC(SectionV5):
    """C · heading as a tab on the section rule, a faint tint under the section; rows without lines."""
    name = 'C'

    def Gap(self, first):
        return 6 if first else (16 if self.big else 12)

    def Open(self, parent, x, y, w, track):
        return dict(x=x, y=y, w=w, widgets=[_Rect(parent, x, y, w, 1, T.PANEL_HI, .35, track)])

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('S') + (10 if self.big else 8)
        probe = ui.TextLine()            # measured first: the tab body is made before the label (draw order;
        probe.SetFontName(k.font('Sb'))  # a SetParent to the same parent does not move a window in the engine)
        probe.SetText(text)
        tw = uikit.TextWidth(probe) + 28
        _Rect(parent, x, y, tw, h, T.PANEL_HI, .95, track)
        track(uikit.Text(parent, text, x + 14, y + h // 2, k.font('Sb'), T.GOLD_HI))
        for bx, by, bw, bh in ((x + 3, y, tw - 6, 1), (x, y + 3, 1, h - 3), (x + tw - 1, y + 3, 1, h - 3)):
            track(uikit.Rect(parent, bx, by, bw, bh, T.BRASS_LINE, .75))
        track(uikit.HLine(parent, x, y + h, w, T.BRASS_LINE, .75))
        return h + 6

    def Close(self, section, y):
        if section is None:
            return 0
        tint = section['widgets'][0]
        tint.SetPosition(section['x'], section['y'])
        tint.SetSize(section['w'], max(1, y - section['y']))
        return 0

    def RowLine(self, parent, x, y, w, track):
        return None


class SectionD(SectionV5):
    """D · ruby heading band with a stripe on the left, alternating row shades; no lines."""
    name = 'D'
    PAD = 12

    def Gap(self, first):
        return 0 if first else (12 if self.big else 8)

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('Sb') + (12 if self.big else 8)
        _Rect(parent, x, y, w, h, T.WINE, .85, track)
        _Rect(parent, x, y, 3, h, T.RUBY, 1.0, track)
        track(uikit.Text(parent, text, x + self.PAD, y + h // 2, k.font('Sb'), T.GOLD_HI))
        return h

    def Inset(self):
        return self.PAD, self.PAD

    def RowBack(self, parent, x, y, w, h, index, track):
        return _Rect(parent, x, y, w, h, T.PANEL_HI, .7, track) if index % 2 else None

    def RowLine(self, parent, x, y, w, track):
        return None


class SectionE(SectionV5):
    """E · a thin brass stripe along the whole section (heading and rows), rows indented, faint row lines."""
    name = 'E'
    PAD = 14

    def Gap(self, first):
        return 0 if first else (14 if self.big else 10)

    def Open(self, parent, x, y, w, track):
        return dict(x=x, y=y, w=w, widgets=[_Rect(parent, x, y, 2, 1, T.BRASS_LINE, .8, track)])

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('Sb') + (12 if self.big else 8)
        track(uikit.Text(parent, text, x + self.PAD, y + h // 2, k.font('Sb'), T.GOLD))
        return h

    def Close(self, section, y):
        if section is None:
            return 0
        stripe = section['widgets'][0]
        stripe.SetPosition(section['x'], section['y'] + 2)
        stripe.SetSize(2, max(1, y - section['y'] - 4))
        return 0

    def Inset(self):
        return self.PAD, 0

    def RowLine(self, parent, x, y, w, track):
        return track(uikit.HLine(parent, x + self.PAD, y, w - self.PAD, T.ROW_LINE, .45))


class SectionF(SectionV5):
    """F · only air and type: a bigger lighter heading with more space above it, no lines, no background."""
    name = 'F'

    def Gap(self, first):
        return 0 if first else (22 if self.big else 16)

    def Heading(self, parent, x, y, w, text, track):
        k = self.kit
        h = k.cell('Mb') + (12 if self.big else 8)
        track(uikit.Text(parent, text, x, y + h // 2, k.font('Mb'), T.GOLD_HI))
        return h

    def RowLine(self, parent, x, y, w, track):
        return None


STYLES = dict((cls.name, cls) for cls in (SectionV5, SectionA, SectionB, SectionC, SectionD, SectionE, SectionF))


def Style(kit, name=None):
    """The section style of the settings pages (SECTION_STYLE unless a name is given)."""
    return STYLES.get(name or SECTION_STYLE, SectionV5)(kit)
