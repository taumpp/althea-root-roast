# -*- coding: utf-8 -*-
"""Dungeon info (Teleportace -> Dungeony, F7) in the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md).

uidungeontrack.DungeonTeleportPage stays the page (821 x 491 inside the Teleportace window) and keeps every function:
the dungeon list (select, move up / down, hide / restore, "Zobrazit i zamčené", "Skryté (n)", scrolling by the bar
and the mouse wheel, the rejoin offer and the cooldown timers), the detail column (boss preview, elements, required
level, group, cooldown, ticket with the shop and the VIP auto ticket, alarm, guide, drop window, enter) and the
statistics with the server ranking (Počet / Čas / Poškození). This module only draws the R1 look INTO the page:

* the three columns are dark R1 panels with Noto Sans headings and a hairline (no crimson header plates);
* a dungeon row is an R1 list row: hover = lighter graphite, the selected dungeon = dark well with the red line;
  portraits, the level badge, the status text and the up / down / eye controls stay;
* the narrow R1 scroll bar, R1 check boxes, quiet info and statistics rows (hairlines, the original icons),
  the ticket block as a dark panel, Obchod / Průvodce / alarm / drop as secondary buttons (icons kept), "Vstoupit"
  as the primary button and the ranking switch as an R1 segment;
* the values keep their colours: completed 72C66A, fastest 69A7D7, max. damage DEA435, status 83D45B / FF4F5F,
  rank positions FFCB67. The boss 3D preview with its frame, the element icons and the portraits stay.

The page code keeps driving its controls: the original buttons stay as hidden models whose Show / Hide / Enable /
Disable / SetText reach their R1 counterparts, and the R1 state (rows, scroll bar, check boxes, alarm, ranking) is
read from the page after each of its refreshes.

Settings -> "Starý vzhled" (settingslook 'legacy') shows the original page; so does a page scaled for a screen
narrower than the window (the R1 textures are drawn in their native size). A failure while building the R1 look
keeps the original page (traced to syserr) and is not retried.
"""
import ui

import uir1
import uir1tokens as T

IMG = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/"
ELLIPSIS = u"\u2026"

# Page geometry (the page is 821 x 491; the columns are the original CATALOG / DETAIL / STATS rects).
COLUMNS = ((6, 18, 247, 455), (259, 18, 307, 455), (572, 18, 239, 455))
HEADING_POS = ((21, 31), (274, 31), (587, 31))     # where the original column headings were drawn
HEADING_RULE = 34                                  # hairline under the heading
LIST_X, LIST_Y = 14, 60                            # the page's catalogue list
ROW_W, ROW_H = 227, 54                             # R1 row band (the list minus the scroll bar)
SCROLL_X, SCROLL_Y, SCROLL_H = 243, 60, 340
INFO_ROWS = (246, 277, 308)                        # Požadovaná úroveň / Požadavek na skupinu / Čekací doba
INFO_X, INFO_W = 268, 289
STAT_ROWS = (86, 117, 148)                         # Dokončeno / Nejrychlejší / Max. poškození
STAT_X, STAT_W = 581, 221
ROW_LINE_DY = 27                                   # hairline under an info / statistics row
TICKET = (268, 340, 289, 48)
RANK_SEGMENT = (581, 213, 214)
RANK_RULE_Y = 266
CHECKS = {'showLockedButton': (17, 440), 'showHiddenButton': (138, 440), 'autoTicketCheck': (334, 366)}
CHECK_GAP = 12                                     # label of a check -> the next check box
# Statistics rows: (label position, value attribute). A label is shortened (ellipsis) only when its value would
# run into it (the kit font is wider than the original Tahoma, a boss damage can have 10 digits).
STAT_LABELS = (((612, 93), 'completedValue'), ((612, 124), 'fastestValue'), ((612, 155), 'damageValue'))
STAT_GAP = 6
BUTTONS = {                                        # page attribute: (x, y, w, small, primary, icon)
    'shopButton': (465, 353, 86, True, False, None),
    'alarmButton': (320, 393, 28, False, False, 'icon/alarm_20.png'),
    'guideButton': (358, 393, 110, False, False, None),
    'dropButton': (478, 393, 28, False, False, 'icon/shop_20.png'),
    'enterButton': (315, 430, 196, False, True, None),
}
# Original decoration replaced by R1 (images of the page, relative to IMG).
HIDDEN_IMAGES = ('surface/', 'panel/', 'header/', 'info/', 'scrollbar/', 'icon/alarm_20.png', 'icon/shop_20.png')
TEXT_DY = -2                                       # the kit cell (text_s 16) is taller than Tahoma 12: keep the centre
# Every text stays a top-aligned line (never the engine's vertical centre) whose whole font cell lies inside its row:
# the catalogue list clips its rows, and the engine clips a line as if it ran down from its y by the text height.
NAME_Y, STATUS_Y = 6, 33                           # dungeon row (54 px): name and status cells 6..21 / 33..48

FAILED = False


def UseR1(page=None):
    """R1 unless the original look is chosen, a previous build failed or the page is scaled for a small screen."""
    if FAILED or not uir1.UseR1():
        return False
    return page is None or abs(float(getattr(page, 'scale', 1.0)) - 1.0) < 1e-6


def Sentence(text):
    """'OSOBNÍ STATISTIKY' -> 'Osobní statistiky' (the R1 headings are not upper case); other texts unchanged."""
    text = text or ''
    if text.isupper():
        return text[:1] + text[1:].lower()
    return text


def Begin(page):
    """Called before the page builds its widgets: the R1 backdrop must be the page's first child (drawn under the
    content). Returns the skin or None (original look)."""
    global FAILED
    if not UseR1(page):
        return None
    skin = None
    try:
        skin = Skin(page)
        return skin
    except Exception:
        FAILED = True
        uir1.TraceFailure('Dungeon info')
        if skin is not None:
            skin.Abort()
        return None


def Finish(skin):
    """Called after the page built its widgets: dresses them. Returns the skin or None (original look)."""
    global FAILED
    if skin is None:
        return None
    try:
        skin.Dress()
        return skin
    except Exception:
        FAILED = True
        uir1.TraceFailure('Dungeon info')
        skin.Abort()
        return None


class RowHit(ui.Button):
    """Invisible click area of a dungeon row (an ui.Button without visuals): select, the row tooltip and the hover
    band. Replaces the row's crimson plate."""

    def __init__(self, skin, row):
        ui.Button.__init__(self)
        self.skin = skin
        self.mobIdx = row.mobIdx

    def OnMouseOverIn(self):
        self.skin.Hover(self.mobIdx)
        base = getattr(ui.Button, 'OnMouseOverIn', None)
        if base:
            base(self)

    def OnMouseOverOut(self):
        self.skin.Hover(None)
        base = getattr(ui.Button, 'OnMouseOverOut', None)
        if base:
            base(self)


class TipButton(uir1.Button):
    """R1 button with the original button's tooltip (alarm, drop window): uir1.Button's own hint (``tooltip``), the
    one source of its R1 hint."""

    def SetTip(self, text):
        self.tooltip = text or ''

    def Hide(self):
        uir1.HideHint(self)
        uir1.Button.Hide(self)


class Skin(object):
    def __init__(self, page):
        import _weakref
        self.page = _weakref.proxy(page)
        self.cls = type(page)
        # The page's own module object: the client imports it as uiDungeonTrack, a second import under another
        # spelling would be a second module with its own dungeonData.
        import sys
        self.module = sys.modules[self.cls.__module__]
        self.real = page                 # the real page while building (recorders compare parents); dropped after
        self.kit = uir1.Kit()
        self.undo = []
        self.widgets = []
        self.images = []                 # (relative path, widget) of the page's images
        self.texts = {}                  # position -> text line of the page's _Text
        self.hover = None
        self.slots = []                  # mobIdx shown in each list slot
        self.dragging = False
        self.controls = {}
        # Recorders: the page names only a part of its widgets; the rest is found by path / position.
        self._Override('_Image', self._RecordImage)
        self._Override('_Text', self._RecordText)
        self.back = ui.Window()          # the page's FIRST child: everything in it lies under the content
        self.back.SetParent(page)
        self.back.AddFlag('not_pick')
        self.back.SetPosition(0, 0)
        self.back.SetSize(page.GetWidth(), page.GetHeight())
        self.back.Show()
        self._BuildBackdrop()

    # ------------------------------------------------------------------ helpers
    def _Override(self, name, function):
        page = self.page
        setattr(page, name, function)
        self.undo.append(lambda: page.__dict__.pop(name, None))

    def _Original(self, name):
        cls = self.cls
        page = self.page

        def call(*args):
            return getattr(cls, name)(page, *args)
        return call

    def _RecordImage(self, parent, position, path):
        image = self._Original('_Image')(parent, position, path)
        self.images.append((path, image))
        return image

    def _RecordText(self, parent, position, text, color=0xffd9d2c8, align='left'):
        line = self._Original('_Text')(parent, position, text, color, align)
        if parent is self.real:
            self.texts[tuple(position)] = line
        return line

    def _Own(self, widget):
        self.widgets.append(widget)
        return widget

    def _HideKeep(self, widget):
        """Hides an original widget for good (the page keeps calling Show on some of them)."""
        shown = widget.IsShow()
        widget.Hide()
        widget.Show = lambda *args: None
        self.undo.append(lambda: (widget.__dict__.pop('Show', None), widget.Show() if shown else None))

    def _Restyle(self, line, role, dy=TEXT_DY, color=None, text=None):
        font, old_text = line.font if hasattr(line, 'font') else None, line.GetText()
        x, y = line.GetLocalPosition()
        old_font = getattr(line, '_r1_font', None)
        uir1.SetFont(line, self.kit.font(role), old_text if text is None else text)
        line.SetPosition(x, y + dy)
        if color is not None:
            line.SetPackedFontColor(color)

        def restore():
            line.SetPosition(x, y)
            uir1.SetFont(line, old_font or font or 'Tahoma:12', old_text)
        self.undo.append(restore)

    # ------------------------------------------------------------------ backdrop (before the page content)
    def _BuildBackdrop(self):
        back, kit = self.back, self.kit
        for x, y, w, h in COLUMNS:
            self._Own(uir1.Frame(back, x, y, w, h, 'panel'))
            self._Own(uir1.Divider(back, x + 6, y + HEADING_RULE, w - 12))
        # Top-aligned lines centred by position in the heading band (the engine clips a vertically centred line
        # as if it ran down from its y: uir1.CellTop / RowText).
        font = kit.font('text_sb')
        self.headings = [self._Own(uir1.Text(back, '', x + 10, y + uir1.CellTop(HEADING_RULE, font), font, T.IVORY,
                                             valign='top'))
                         for x, y, w, h in COLUMNS]
        self.bands = [uir1.Band(back, LIST_X, LIST_Y + i * 57, ROW_W, ROW_H)
                      for i in range(6)]
        for y in INFO_ROWS:
            self._Own(uir1.Divider(back, INFO_X, y + ROW_LINE_DY, INFO_W))
        for y in STAT_ROWS:
            self._Own(uir1.Divider(back, STAT_X, y + ROW_LINE_DY, STAT_W))
        self._Own(uir1.Frame(back, TICKET[0], TICKET[1], TICKET[2], TICKET[3], 'panel'))
        self._Own(uir1.Divider(back, STAT_X, RANK_RULE_Y, STAT_W))

    # ------------------------------------------------------------------ dressing (after the page content)
    def Dress(self):
        page, kit = self.page, self.kit
        for name in ('_Image', '_Text'):
            page.__dict__.pop(name, None)
        # Original decoration.
        for path, image in self.images:
            if any(path.startswith(prefix) for prefix in HIDDEN_IMAGES):
                self._HideKeep(image)
        for index, position in enumerate(HEADING_POS):
            line = self.texts.get(position)
            if line is not None:
                self.headings[index].SetText(Sentence(line.GetText()))
                self._HideKeep(line)
        # Texts in Noto Sans; the value colours stay as the page sets them.
        for position, line in self.texts.items():
            if position in HEADING_POS or line is page.ticketCount:
                continue
            if position in ((584, 65), (584, 190)):
                self._Restyle(line, 'text_sb', color=T.INK_DIM, text=Sentence(line.GetText()))
            elif line is page.ticketName:
                self._Restyle(line, 'text_sb')
            else:
                self._Restyle(line, 'text_s')
        self._Restyle(page.bossName, 'text_b')
        self._Restyle(page.autoTicketText, 'text_s', dy=-1)
        self.stat_labels = [(self.texts[position], self.texts[position].GetText(), getattr(page, value))
                            for position, value in STAT_LABELS
                            if position in self.texts and getattr(page, value, None) is not None]
        self._DressRows()
        self._DressScroll()
        self._DressChecks()
        self._DressButtons()
        self._DressRanks()
        for name, after in (('_RefreshCatalogue', self.SyncCatalogue), ('_RefreshDetails', self.SyncDetails),
                            ('_RefreshRank', self.SyncRank)):
            self._Wrap(name, after)
        self.real = None
        self.SyncCatalogue()
        self.SyncDetails()
        self.SyncRank()

    def _Wrap(self, name, after):
        original = self._Original(name)

        def run(*args):
            result = original(*args)
            after()
            return result
        self._Override(name, run)

    def _DressRows(self):
        page, kit = self.page, self.kit
        lift = ui.Window()               # a parent for a moment: back to the row = the end of its children
        for row in page.rows.values():
            body = row.body
            hit = RowHit(self, row)
            hit.SetParent(row)
            hit.SetPosition(0, 0)
            hit.SetSize(row.GetWidth(), row.GetHeight())
            hit.SAFE_SetEvent(page._SelectDungeon, row.mobIdx)
            hit.OnMouseWheel = ui.__mem_func__(row.OnMouseWheel)
            hit.Show()
            row.r1Hit = hit
            self.undo.append(lambda row=row: row.__dict__.pop('r1Hit', None) and None)
            self.undo.append(hit.Hide)
            self._HideKeep(body)
            body.SetToolTipText = hit.SetToolTipText
            self.undo.append(lambda body=body: body.__dict__.pop('SetToolTipText', None))
            # The row controls go back above the click area (a new parent appends; the old one again = the end).
            for control in (row.upButton, row.downButton, row.hideButton):
                shown = control.IsShow()
                control.SetParent(lift)
                control.SetParent(row)
                control.Show() if shown else control.Hide()
            name = row.nameText.GetText()
            self._Restyle(row.nameText, 'text_sb', dy=NAME_Y - row.nameText.GetLocalPosition()[1])
            uir1.Fit(row.nameText, name, row.NAME_WIDTH, ELLIPSIS)
            self._Restyle(row.statusText, 'text_s', dy=STATUS_Y - row.statusText.GetLocalPosition()[1])
            row.Refresh()

    def _DressScroll(self):
        page = self.page
        self._HideKeep(page.scrollThumb)
        bar = uir1.ScrollBar(self.kit)
        bar.SetParent(self.real)
        bar.SetPosition(SCROLL_X, SCROLL_Y)
        bar.SetScrollBarSize(SCROLL_H)
        bar.SetScrollEvent(self.OnScroll)
        bar.OnMouseWheel = lambda length: self.page.OnMouseWheel(length)
        bar.Hide()
        self.scroll = self._Own(bar)

    def _DressChecks(self):
        page = self.page
        events = {'showLockedButton': lambda: self.page._ToggleShowLocked(),
                  'showHiddenButton': lambda: self.page._ToggleShowHidden(),
                  'autoTicketCheck': self._ToggleAutoTicket}
        checks = dict(CHECKS)
        # "Skryté (N)" with its check right of the "Zobrazit i zamčené" label in the kit font (Noto Sans 16a is
        # wider than the original Tahoma: the label ran under the second check box).
        locked, hidden = getattr(page, 'showLockedText', None), getattr(page, 'hiddenCountText', None)
        if locked is not None and hidden is not None:
            x, y = checks['showHiddenButton']
            lx = locked.GetLocalPosition()[0]
            moved = max(x, lx + uir1.TextWidth(locked) + CHECK_GAP)
            checks['showHiddenButton'] = (moved, y)
            hx, hy = hidden.GetLocalPosition()
            hidden.SetPosition(hx + moved - x, hy)          # undone with the restyle of the line (its old place)
        for name, (x, y) in checks.items():
            legacy = getattr(page, name)
            box = uir1.CheckBox(self.real, self.kit, x, y, event=events[name])
            self.controls[name] = self._Own(box)
            self._HideKeep(legacy)
            self._Proxy(legacy, box)

    def _DressButtons(self):
        import localeInfo
        page = self.page
        tips = {'alarmButton': self.module._AtlasLocale('DUNGEON_TRACK_ALARM', 'Notify when cooldown ends'),
                'dropButton': getattr(localeInfo, 'DUNGEON_DROP_BUTTON', '')}
        for name, (x, y, w, small, primary, icon) in BUTTONS.items():
            legacy = getattr(page, name)
            button = TipButton(self.real, self.kit, x, y, w, legacy.GetText() if hasattr(legacy, 'GetText') else '',
                               primary=primary, small=small, event=self._Click(name))
            button.SetTip(tips.get(name))
            button.base_primary = primary
            if icon:
                image = ui.ExpandedImageBox()
                image.SetParent(button)
                image.AddFlag('not_pick')
                image.LoadImage(IMG + icon)
                image.SetPosition((w - 20) // 2, (button.h - 20) // 2)
                image.Show()
                button.icon = image
            shown = legacy.IsShow()
            self.controls[name] = self._Own(button)
            self._HideKeep(legacy)
            self._Proxy(legacy, button)
            button.Show() if shown else button.Hide()

    def _DressRanks(self):
        page = self.page
        import app
        czech = app.GetLocalePath().replace('\\', '/').rsplit('/', 1)[-1].lower() == 'cz'
        labels = (u'Počet', u'Čas', u'Poškození') if czech else ('Count', 'Time', 'Damage')
        x, y, w = RANK_SEGMENT
        segment = uir1.Segment(self.real, self.kit, list(enumerate(labels)),
                               event=lambda value: self.page._SelectRank(value), width=w, font=self.kit.font('text_s'))
        segment.SetPosition(x, y)
        self.rank = self._Own(segment)
        for button in page.rankButtons:
            self._HideKeep(button)

    def _Proxy(self, legacy, control):
        """The page keeps calling the original (hidden) control; its state goes to the R1 control. Call it after
        _HideKeep: Show / Hide then reach the R1 control, the original stays hidden."""
        def set_text(text, *args):
            control.SetText(text)
        names = {'Show': lambda *args: control.Show(), 'Hide': lambda *args: control.Hide(),
                 'Enable': lambda *args: control.Enable(), 'Disable': lambda *args: control.Disable()}
        if hasattr(control, 'SetText'):
            names['SetText'] = set_text
        for name, function in names.items():
            setattr(legacy, name, function)

        def restore():
            shown = control.IsShow()
            for name in names:
                legacy.__dict__.pop(name, None)
            legacy.Show() if shown else legacy.Hide()
        self.undo.append(restore)

    def _Click(self, name):
        page = self.page

        def click():
            {'shopButton': page._OpenTicketShop, 'alarmButton': page._ToggleAlarm, 'guideButton': page._OpenGuide,
             'dropButton': page._ToggleDrop, 'enterButton': page._EnterDungeon}[name]()
        return click

    def _ToggleAutoTicket(self):
        self.page._ToggleAutoTicket()
        self.SyncDetails()

    # ------------------------------------------------------------------ sync from the page
    def Hover(self, mobIdx):
        self.hover = mobIdx
        self.SyncBands()

    def SyncBands(self):
        data = self.module.dungeonData
        for index, band in enumerate(self.bands):
            mobIdx = self.slots[index] if index < len(self.slots) else None
            if mobIdx is None or mobIdx not in data:
                band.SetState('normal')
            elif data[mobIdx]['selected']:
                band.SetState('selected')
            else:
                band.SetState('hover' if mobIdx == self.hover else 'normal')

    def SyncCatalogue(self):
        page = self.page
        visible = list(page.visibleMobIndexes)
        self.slots = visible[page.scrollOffset:page.scrollOffset + page.VISIBLE_ROWS]
        self.SyncBands()
        self.controls['showLockedButton'].SetOn(page.showLocked)
        self.controls['showHiddenButton'].SetOn(page.showHidden)
        maximum = max(0, len(visible) - page.VISIBLE_ROWS)
        if maximum:
            self.scroll.SetMiddleBarSize(float(page.VISIBLE_ROWS) / len(visible))
            if not self.dragging:
                self.scroll.SetPos(float(page.scrollOffset) / maximum, False)
            self.scroll.Show()
        else:
            self.scroll.Hide()

    def SyncDetails(self):
        import player
        page = self.page
        self.FitStatLabels()
        mobIdx = page.GetCurrentSelectedDungeon()
        info = self.module.dungeonData.get(mobIdx)
        alarm = bool(info and info['alarm'])
        button = self.controls['alarmButton']
        if button.primary != alarm:
            button.primary = alarm
            button.paint()
        try:
            vip = bool(player.IsVipActive())
        except Exception:
            vip = False
        self.controls['autoTicketCheck'].SetOn(bool(info and info['autoTicket']) and vip)

    def FitStatLabels(self):
        """Every statistics label ends STAT_GAP px before its right-aligned value (shortened only when needed)."""
        for label, text, value in getattr(self, 'stat_labels', ()):
            value_left = value.GetLocalPosition()[0] - uir1.TextWidth(value)
            room = value_left - STAT_GAP - label.GetLocalPosition()[0]
            if label.GetText() != text or uir1.TextWidth(label) > room:
                uir1.Fit(label, text, room, ELLIPSIS)

    def SyncRank(self):
        self.rank.SetValue(self.page.activeRank)

    def OnScroll(self):
        page = self.page
        maximum = max(0, len(page.visibleMobIndexes) - page.VISIBLE_ROWS)
        if not maximum:
            return
        offset = int(round(self.scroll.GetPos() * maximum))
        if offset != page.scrollOffset:
            page.scrollOffset = offset
            self.dragging = True
            try:
                page._RefreshCatalogue()
            finally:
                self.dragging = False

    # ------------------------------------------------------------------ failure
    def Abort(self):
        """Back to the original page: every change is undone, the R1 widgets are hidden."""
        for step in reversed(self.undo):
            try:
                step()
            except Exception:
                pass
        self.undo = []
        for widget in self.widgets:
            try:
                widget.Hide()
            except Exception:
                pass
        for band in getattr(self, 'bands', []):
            band.Hide()
        try:
            self.back.Hide()
        except Exception:
            pass
        self.widgets = []
