# -*- coding: utf-8 -*-
"""DPS měřič (uidpsmeter.DpsMeterPanel, the damage table under the target board) in the R1 look, variant A "Tabulka
R1" of the round kolo-20261009-dps (owner 9. 10. 2026). Visual only: the panel lays itself out (columns, your pinned
row, the footer, the final state); this module re-skins it in place with uir1skin.Recorder (a failed build puts every
original back):

* the R1 window frame instead of the tooltip ThinBoard (uir1.BoardSkin, follows SetSize);
* every text in Tahoma 12 (PRAVIDLA-UI "Písmo textu"): the column labels and the ranks in the dimmed ink, the numbers
  in the readable ink (never pale), your row in ivory on the R1 row band (brightness, no red: rule 3);
* hairlines in the R1 line colour, no zebra rows;
* "Další" / "Méně" as a thin R1 button (20 px) with a chevron, and the number of hidden players as the one badge style
  (a red circle with a white number, althea_r1_lista/badge, like "Zvýšit status"). It keeps the panel's
  ToggleExpanded and the panel's expandButton attribute, so the panel shows, hides and labels it.

Your row's band is the fill of the R1 list rows (uir1.Band 'hover': T.BAND_HOVER at T.BAND_ALPHA['hover'], the
same as the boss / drop tracker, character details and switchbot list rows), not a colour of its own: the first
build had a grey (52, 47, 48) band at 92 % with two lighter hairlines, which read as a grey plate and doubled the
header's hairline 2 px above it (owner 9. 10. 2026). The panel keeps the band without lines, as wide as the rules.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the panel's own look. A failure is traced (uir1.TraceFailure),
the original look comes back and the R1 look is not tried again in this session.
"""
import weakref

import ui

import uir1
import uir1tokens as T
import uir1hud
import uir1skin

BADGE = None                     # uir1listaart: the badge art of the bottom bar (althea_r1_lista/badge), see _Build

WHAT = u'the DPS meter'
ROW_BAND_STATE = 'hover'         # your row: the uir1.Band fill of this state (the lighter R1 row, no red line)
MORE_W = 58                      # "Další" / "Méně" (the panel's MORE_WIDTH)
CHEVRON_RIGHT = 18               # the chevron's left edge from the button's right edge
BADGE_DX, BADGE_DY = -9, -6      # the badge's top left from the button's top right corner
MAX_DIGITS = 2                   # at most 19 hidden players (the server sends 20 rows)

# panel attribute -> R1 value (colours are signed for the x64 binding, uir1hud.Signed)
COLOURS = {
    'NORMAL_COLOR': uir1hud.Signed(T.INK),
    'OWN_COLOR': uir1hud.Signed(T.IVORY),
    'HEADER_COLOR': uir1hud.Signed(T.INK_DIM),
    'RANK_COLOR': uir1hud.Signed(T.INK_DIM),
    'MUTED_COLOR': uir1hud.Signed(T.MUTED),
    'FOOTER_COLOR': uir1hud.Signed(T.INK_DIM),
    'FOOTER_FINAL_COLOR': uir1hud.Signed(T.INK),
    'DIVIDER_COLOR': uir1hud.Signed(T.LINE),
}


def RowBandColour():
    """The fill of an R1 list row in ROW_BAND_STATE exactly as uir1.Band.SetState sets it on its ui.Bar
    (grp.GenerateColor already gives the engine's packed value)."""
    return uir1.GenerateColor(T.BAND_HOVER, T.BAND_ALPHA[ROW_BAND_STATE])


def _BadgeImage(parent, name, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(BADGE.ROOT + name)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


class Badge(object):
    """The red circle with the white number (badge/count_<digits>.png + badge/digit_<n>.png), on the panel."""

    def __init__(self, parent):
        self.pill = _BadgeImage(parent, 'badge/count_1.png', 0, 0)
        self.digits = [_BadgeImage(self.pill, 'badge/digit_0.png',
                                   BADGE.BADGE_DIGIT_AT[0] + index * (BADGE.DIGIT[0] + 1), BADGE.BADGE_DIGIT_AT[1])
                       for index in range(MAX_DIGITS)]
        self.value = 0
        self.pill.Hide()

    def SetValue(self, value):
        value = max(0, min(int(value), 10 ** MAX_DIGITS - 1))
        self.value = value
        if not value:
            self.pill.Hide()
            return
        label = '%d' % value
        self.pill.LoadImage(BADGE.ROOT + 'badge/count_%d.png' % len(label))
        for index, image in enumerate(self.digits):
            if index < len(label):
                image.LoadImage(BADGE.ROOT + 'badge/digit_%s.png' % label[index])
                image.SetPosition(BADGE.BADGE_DIGIT_AT[0] + index * (BADGE.DIGIT[0] + 1), BADGE.BADGE_DIGIT_AT[1])
                image.Show()
            else:
                image.Hide()

    def Place(self, x, y, shown):
        self.pill.SetPosition(int(x), int(y))
        if shown and self.value:
            self.pill.Show()
        else:
            self.pill.Hide()

    def IsShow(self):
        return self.pill.IsShow()

    def Destroy(self):
        self.pill.Hide()


class MoreButton(uir1.Button):
    """ "Další" (chevron down, the badge with the hidden players) / "Méně" (chevron up): a thin R1 button in Tahoma 12
    with the calls the panel makes (SetMore, SetPosition, Show / Hide, SetText, SetEvent)."""

    def __init__(self, panel, kit, text, event):
        self.chevron = None
        self.badge = None
        self.direction = 'down'
        uir1.Button.__init__(self, panel, kit, 0, 0, MORE_W, text, small='xs', font=kit.font('tahoma'), event=event)
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), self.w - CHEVRON_RIGHT, (self.h - T.CHEVRON) // 2)
        self.badge = Badge(panel)
        self.Hide()

    def SetEvent(self, func, *args):
        self.callback = (lambda: func(*args)) if args else func

    def paint(self):
        uir1.Button.paint(self)
        x, y = self.label.GetLocalPosition()
        self.label.SetPosition((self.w - CHEVRON_RIGHT) // 2 + 2, y)       # the label left of the chevron
        if self.chevron is not None:
            state = self.state()
            self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath(
                self.direction, 'hover' if state in ('hover', 'pressed') else 'normal'))
            self.chevron.SetPosition(self.w - CHEVRON_RIGHT, (self.h - T.CHEVRON) // 2)

    def SetMore(self, expanded, hidden):
        import uidpsmeter
        self.direction = 'up' if expanded else 'down'
        self.SetText(uidpsmeter._Text('DPS_METER_LESS' if expanded else 'DPS_METER_MORE'))
        self.badge.SetValue(0 if expanded else hidden)
        self._PlaceBadge()

    def SetPosition(self, x, y):
        uir1.Button.SetPosition(self, x, y)
        self._PlaceBadge()

    def _PlaceBadge(self):
        if self.badge is not None:
            x, y = self.GetLocalPosition()
            self.badge.Place(x + self.w + BADGE_DX, y + BADGE_DY, self.IsShow())

    def Show(self):
        uir1.Button.Show(self)
        self._PlaceBadge()

    def Hide(self):
        uir1.Button.Hide(self)
        self._PlaceBadge()


class DpsSkin(object):
    def __init__(self, panel):
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.frame = None
        self.badge = None
        self.embedded = False      # inside the unified target form: its one frame is the board's (uitargetform)
        self.panelRef = weakref.ref(panel)
        try:
            self._Build(panel)
        except Exception:
            self.Undo(panel)
            raise

    def _Build(self, panel):
        global BADGE
        import uir1listaart
        BADGE = uir1listaart
        rec, kit = self.rec, uir1.Kit()
        import uir1frame
        holder = uir1frame._BoardSkin(uir1, panel, kit, kind='window')     # weak board, restorable half way
        self.frame = holder.skin
        rec.Call(lambda: None, holder.Restore)
        ref = weakref.ref(panel)

        colours_r1 = dict(COLOURS, OWN_ROW_COLOR=RowBandColour())

        def colours():
            owner = ref()
            for name, value in colours_r1.items():
                setattr(owner, name, value)

        def original_colours():
            owner = ref()
            for name in colours_r1:
                if owner is not None and name in owner.__dict__:
                    delattr(owner, name)
        rec.Call(colours, original_colours)
        cls = panel.__class__
        tahoma = kit.font('tahoma')
        lines = list(panel.headerWidgets) + [panel.gapMark, panel.footerText]
        for widgets in panel.rowWidgets:
            lines.extend(widgets)
        for line in lines:
            rec.Font(line, tahoma, COLOURS['NORMAL_COLOR'], None, cls.NORMAL_COLOR)

        original = panel.expandButton
        button = MoreButton(panel, kit, original.GetText() or u'',
                            event=lambda: (ref() is not None and ref().ToggleExpanded()))
        self.widgets.append(button)
        self.badge = button.badge
        rec.Hide(original)

        def use_r1():
            ref().expandButton = button

        def use_original():
            owner = ref()
            button.Hide()
            if owner is not None:
                owner.expandButton = original
        rec.Call(use_r1, use_original)
        if panel.snapshotRows:
            panel._Refresh()

    def FitName(self, line, name, width):
        return uir1.Fit(line, name, width, u'…')

    def SetEmbedded(self, embedded):
        """The unified target form (variant A of 9. 10. 2026): the table is a section of the target board's one R1
        frame, so its own frame edges and background hide (True) or come back (False)."""
        embedded = bool(embedded)
        if embedded == self.embedded or self.frame is None:
            self.embedded = embedded
            return
        self.embedded = embedded
        try:
            if embedded:
                self.frame.frame.Hide()
                if self.frame.base is not None:
                    self.frame.base.Hide()
            else:
                panel = self.panelRef()
                if panel is not None:
                    self.frame.Resize(panel.GetWidth(), panel.GetHeight())
                self.frame.frame.Show()
        except Exception:
            uir1hud.Fail(WHAT)
            panel = self.panelRef()
            if panel is not None:
                self.Undo(panel)

    def Resize(self, w, h):
        if self.frame is None:
            return
        if self.embedded:
            return                 # no frame of its own inside the form
        try:
            self.frame.Resize(w, h)
        except Exception:
            uir1hud.Fail(WHAT)
            panel = self.panelRef()
            if panel is not None:
                self.Undo(panel)

    def Undo(self, panel):
        self.rec.Undo()
        if self.badge is not None:
            self.badge.Destroy()
            self.badge = None
        uir1skin.Destroy(self.widgets)
        self.widgets = []
        self.frame = None
        if panel.__dict__.get('r1') is self:
            panel.r1 = None
        try:
            if panel.snapshotRows:
                panel._Refresh()
        except Exception:
            pass


def Dress(panel):
    """The R1 look of the DPS panel, or None (original look / failure: traced, the original panel)."""
    if not uir1hud.UseR1(WHAT):
        return None
    try:
        skin = DpsSkin(panel)
        panel.r1 = skin
        return skin
    except Exception:
        uir1hud.Fail(WHAT)
        return None
