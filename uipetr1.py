# -*- coding: utf-8 -*-
"""The pet window (Mazlíček), its Nakrmit / Evoluce peta window and the pet album's "Výskyt" popup in the R1 look
("Krvavá žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original windows. The album book itself stays as it is.

* Mazlíček (uipetinfo.PetInformationWindow with the compact page of petcompactlayout / uipetcompact, 292 x 520): the
  R1 frame and header (the window title of today, it follows the window's own title text), no decorative "MAZLÍČEK"
  bar (it was only a picture), the 3D preview in a graphite frame right under the header with the pet's name and its
  evolution stage on top, the rows Úroveň (level · age), Zkušenosti and Doba trvání (both as
  a red vein on a dark track with the value in the row, instead of the four orbs and the red gauge) with quiet dividers, the bonus values bright
  green in their own column with the growth range muted next to them, the original skill and seal slots on the R1
  item slot C (uir1.SLOT_CELL), Nakrmit / Vývoj / Oživit and Otevřít album as R1 buttons (the book glyph and the capture badge stay on
  the album button).
* Výskyt (uipetalbumoccurrence.PetAlbumOccurrenceWindow): the R1 frame and header "Výskyt · <jméno>", the place as a
  heading with the channel muted next to it, the same map and hunting ring in a thin graphite frame, the search line
  in Noto Sans and the hunting time as a row "Kdy lovit ... <čas>".
* Nakrmit / Evoluce peta (uipetinfo.PetFeedWindow, 169 x 202, FeedSkin): the R1 frame and header with the window's
  own title, the 3 x 3 feed grid on the R1 item slot C, the hint in muted Noto Sans, "Nakrmit" as the R1 primary
  button.

Nothing of the windows is re-created: the original controls stay (hidden where R1 draws its own), keep receiving
every value and every call, and R1 mirrors them (button enabled states, the window title, level and age) or is fed
by the same calls (the lifetime gauge, the bonus values). The windows keep their sizes. Settings -> "Starý vzhled"
keeps the original windows; a failure while building traces to syserr and keeps the original look.
"""
import ui
import uiScriptLocale

import uir1
import uir1layout as L
import uir1tokens as T

ORIGINAL_SLOT_BASE = 'd:/ymir work/ui/public/Slot_Base.sub'
BONUS_GREEN = 0xFF63E86D       # the bright positive green of the game's mount / pet value texts (uimountwidgets)
PAGE_W = 292
ROW_X, ROW_R = 28, 264          # label column / right edge of the values
BONUS_VALUE_R = 200             # right edge of the bonus value column (the growth range ends at ROW_R)

# R1 positions of the compact page children (x, y); the original ones are read from the window when R1 is built.
LAYOUT = {
    'PetPreviewFill': (18, 38),
    'PetPreviewViewport': (18, 38),
    'PetName': (146, 45),
    'EvolName': (146, 65),
    'UpBringing_Pet_Slot': (28, 78),
    'PetSealLabel': (44, 113),
    'LevelTitle': (ROW_X, 222),
    'ExpTitle': (ROW_X, 246),
    'LifeTitle': (ROW_X, 284),
    'LifeTextValue': (ROW_R, 284),
    'HpTitle': (ROW_X, 324),
    'DefTitle': (ROW_X, 343),
    'SpTitle': (ROW_X, 362),
}
SKILL_SLOT_X, SKILL_SLOT_STEP, SKILL_SLOT_Y, SKILL_SLOT = 34, 48, 396, 32
STATE_GAP = 1                   # "Volný" right under its slot (the cell top 1 px under the slot's bottom edge)
for _index in range(5):
    LAYOUT['PetSkillSlot%d' % _index] = (SKILL_SLOT_X + _index * SKILL_SLOT_STEP, SKILL_SLOT_Y)
    # centre aligned on the slot's centre column, so the label stands centred under its own slot
    LAYOUT['PetSkillState%d' % _index] = (SKILL_SLOT_X + _index * SKILL_SLOT_STEP + SKILL_SLOT // 2,
                                          SKILL_SLOT_Y + SKILL_SLOT + STATE_GAP)
PREVIEW = (17, 37, 257, 174)    # the graphite frame around the preview (1 px outside the fill)
DIVIDERS = (240, 280, 318)
EXP_TRACK_Y = 263               # Zkušenosti and Doba trvání: the same R1 gauge (a red vein on a dark track) under
LIFE_TRACK_Y = 301              # the label row, the value right-aligned in the row (ROW_R)
BONUS_NAMES = ('Hp', 'Def', 'Sp')
# The two button rows at the bottom (docs/ALTHEA_R1_KIT.md): "Otevřít album" the profile's pad above the window's bottom edge,
# Nakrmit / Evoluce / Oživit ROWS_GAP above it, the three of one width with the kit gap between them, the row as
# wide as the content (BUTTON_X .. PAGE_W - BUTTON_X) and centred; placed from the board's height in _Buttons.
P = T.PROFILE_WINDOW            # the layout profile of this window (docs/ALTHEA_R1_KIT.md chap. 0)
BUTTON_X = 18                   # hardcode-ok: the content's left edge of the original page (as before)
BUTTON_W = (PAGE_W - 2 * BUTTON_X - 2 * P['gap']) // 3      # hardcode-ok: three buttons share the row
ALBUM_W = 170                   # hardcode-ok: the album button's width of the original page (as before)
ROWS_GAP = 7                    # hardcode-ok: between the two rows as before (the "Volný" labels under the slots)
GLYPH_GAP = 6                   # the book glyph -> the label on the album button (centred together)
BADGE_MARGIN = 5                # the capture badge: right end of the album button
HIDE = ('PetSection', 'PetSectionText', 'PetPreviewFrame', 'LifeGauge', 'UpBringing_Pet_EXP_Gauge_Board', 'LevelValue', 'AgeValue', 'HpValue',
        'DefValue', 'SpValue', 'FeedMainButton', 'EvolutionMainButton', 'ReviveMainButton', 'AlbumButton')
# label -> (font role, colour) of the R1 look
STYLE = {
    'PetName': ('text_b', T.IVORY), 'EvolName': ('text_s', T.INK_DIM), 'PetSealLabel': ('text_s', T.INK_DIM),
    'LevelTitle': ('text_s', T.INK), 'ExpTitle': ('text_s', T.INK), 'LifeTitle': ('text_s', T.INK),
    'LifeTextValue': ('text_s', T.IVORY), 'HpTitle': ('text_s', T.INK), 'DefTitle': ('text_s', T.INK),
    'SpTitle': ('text_s', T.INK),
}


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def OriginalSpecs():
    """name -> the original uiscript spec of the compact page (font, colour) from petcompactlayout itself."""
    import petcompactlayout
    window = {'children': [{'children': [
        {'name': 'PetInfo_Page', 'children': [{'name': 'DetermineButton'}]},
        {'name': 'PetInfoUIBG'}, {'name': 'PetAttrChange_Page', 'children': []}, {'name': 'TitleBar'}]}]}
    petcompactlayout.Apply(window)
    page = next(child for child in window['children'][0]['children'] if child.get('name') == 'PetInfo_Page')
    return dict((child['name'], child) for child in page['children'])


class GaugeAdapter(object):
    """Stands in for the original lifetime gauge (owner.lifeTimeGauge): the hidden gauge keeps every value, the R1
    vein shows it."""

    def __init__(self, gauge, skin):
        self.gauge = gauge
        self.skin = skin

    def SetPercentage(self, current, maximum):
        self.gauge.SetPercentage(current, maximum)
        self.skin.SetLife(current, maximum)

    def __getattr__(self, name):
        return getattr(self.gauge, name)


class AlbumButton(uir1.Button):
    """Otevřít album: the R1 button with the original book glyph (reparented into it); the glyph and the label are
    centred TOGETHER on the plate (uir1.Button.paint centres the label alone, the glyph hung left of it). The label
    keeps the y the button gives it (top-aligned at CellTop, 1 px lower while pressed); the glyph is centred by y."""

    glyph = None

    def SetGlyph(self, glyph):
        self.glyph = glyph
        self.paint()

    def paint(self):
        uir1.Button.paint(self)
        glyph = self.glyph
        if glyph is None:
            return
        gw, gh = glyph.GetWidth(), glyph.GetHeight()
        dy = 1 if self.pressed else 0
        gy = (self.h - gh) // 2 + dy
        if not self.label.GetText():
            glyph.SetPosition((self.w - gw) // 2, gy)
            return
        text_w = uir1.TextWidth(self.label)
        group = gw + GLYPH_GAP + text_w
        gx = max(0, (self.w - group) // 2)
        glyph.SetPosition(gx, gy)
        # the label is centre aligned: the engine draws it from x - width // 2 (CGraphicTextInstance)
        self.label.SetPosition(gx + gw + GLYPH_GAP + text_w // 2, self.label.GetLocalPosition()[1])


class PetSkin(object):
    """R1 into one PetInformationWindow (owner) through its compact presentation (after uipetcompact built it)."""

    def __init__(self, compact, owner):
        self.compact = compact
        self.owner = owner
        self.kit = kit = uir1.Kit()
        self.page = owner.GetChild('PetInfo_Page')
        self.board = owner.GetChild('board')
        self.moved, self.styled, self.hidden, self.widgets = {}, [], [], []
        self.title = self._Title()
        # The window is not pickable (uipetinfo AddFlag 'not_pick'): the uiscript title bar ('attach') is its only
        # drag handle, so it stays shown and only stops drawing; the R1 header (made later, its X picks first) is on it.
        self.title_bar = owner.GetChild('TitleBar')
        self.skin = uir1.BoardSkin(self.board, kit, self.title, on_close=owner.Close)
        uir1.Front(owner, not_pick=True)      # 'not_pick': the engine never raises it on a click by itself
        self.gauge = None
        self._DragHandle(True)
        self.reparented = []
        self.flashing = []
        try:
            self._Build()
        except Exception:
            self.Restore()
            raise

    def _DragHandle(self, invisible):
        bar = self.title_bar
        parts = [getattr(bar, name, None) for name in ('imgLeft', 'imgCenter', 'imgRight', 'btnClose')]
        if self.owner.IsChild('TitleName'):
            parts.append(self.owner.GetChild('TitleName'))
        for part in parts:
            if part is not None:
                part.Hide() if invisible else part.Show()
        bar.Show()

    def _Title(self):
        title = getattr(self.owner, 'windowTitle', None)
        text = title.GetText() if title is not None else ''
        return text or uiScriptLocale.PET_INFORMATION_TITLE

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def _Build(self):
        owner, page, kit = self.owner, self.page, self.kit
        specs = OriginalSpecs()
        self.specs = specs
        background = getattr(owner, 'petInfoBackground', None)
        for name in HIDE + (('PetInfoUIBG',) if background is None else ()):
            if owner.IsChild(name):
                widget = owner.GetChild(name)
                self.hidden.append((widget, widget.IsShow()))
                widget.Hide()
        if background is not None:
            background.Hide()
        for name, position in LAYOUT.items():
            widget = owner.GetChild(name)
            self.moved[name] = widget.GetLocalPosition()
            widget.SetPosition(*position)
        for name, (role, colour) in STYLE.items():
            line = owner.GetChild(name)
            uir1.SetFont(line, kit.font(role), line.GetText())
            line.SetPackedFontColor(colour)
            self.styled.append(name)
        for index in range(5):
            name = 'PetSkillState%d' % index
            line = owner.GetChild(name)
            uir1.SetFont(line, kit.font('text_s'), line.GetText())
            line.SetPackedFontColor(T.INK_DIM)
            self.styled.append(name)
        for name in ['UpBringing_Pet_Slot'] + ['PetSkillSlot%d' % index for index in range(5)]:
            owner.GetChild(name).SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
        x, y, w, h = PREVIEW
        self.preview = self._Keep(uir1.Frame(page, x, y, w, h, 'panel', bg=None))
        for dy in DIVIDERS:
            self._Keep(uir1.Divider(page, ROW_X - 4, dy, ROW_R - ROW_X + 8))
        self.level = self._Keep(uir1.Text(page, '', ROW_R, LAYOUT['LevelTitle'][1], kit.font('text_s'), T.IVORY,
                                          align='right', valign='top'))
        track_w = ROW_R - ROW_X
        self.track = self._Keep(uir1.Layer(page, ROW_X, LIFE_TRACK_Y, track_w, T.SLIDER_H,
                                           L.slider_track(0, 0, track_w)))
        self.fill = self._Keep(uir1.Layer(page, ROW_X, LIFE_TRACK_Y, track_w, T.SLIDER_H, []))
        self.track_w = track_w
        # Zkušenosti: one R1 gauge with "value / total" in the row instead of the four small orbs and the hover line
        self.exp_track = self._Keep(uir1.Layer(page, ROW_X, EXP_TRACK_Y, track_w, T.SLIDER_H,
                                               L.slider_track(0, 0, track_w)))
        self.exp_fill = self._Keep(uir1.Layer(page, ROW_X, EXP_TRACK_Y, track_w, T.SLIDER_H, []))
        self.exp_value = self._Keep(uir1.Text(page, '', ROW_R, LAYOUT['ExpTitle'][1], kit.font('text_s'), T.IVORY,
                                              align='right', valign='top'))
        self.exp = None
        self.SetExperience(*getattr(self.compact, 'experience', (0, 0)))
        self.life = None
        self.values, self.ranges = [], []
        for name in BONUS_NAMES:
            y = LAYOUT[name + 'Title'][1]
            self.values.append(self._Keep(uir1.Text(page, '-', BONUS_VALUE_R, y, kit.font('text_sb'), BONUS_GREEN,
                                                    align='right', valign='top')))
            self.ranges.append(self._Keep(uir1.Text(page, '', ROW_R, y, kit.font('text_s'), T.INK_DIM, align='right',
                                                    valign='top')))
        compact = self.compact
        self.buttons = []
        album_y = self.board.GetHeight() - P['pad'] - P['btn']
        row_y = album_y - ROWS_GAP - P['btn']
        row_x = (PAGE_W - 3 * BUTTON_W - 2 * P['gap']) // 2
        for index, (name, event) in enumerate((('FeedMainButton', owner.OpenFeedMenu),
                                               ('EvolutionMainButton', owner.OpenEvolutionFeed),
                                               ('ReviveMainButton', owner.OpenPetReviveFromFeed))):
            original = owner.GetChild(name)
            button = self._Keep(uir1.Button(page, kit, row_x + index * (BUTTON_W + P['gap']), row_y, BUTTON_W,
                                            original.GetText(), event=event))
            self.buttons.append((button, original))
            if index < 2:
                self._MirrorFlash(button, original)
        album = owner.GetChild('AlbumButton')
        ax, ay, aw = (PAGE_W - ALBUM_W) // 2, album_y, ALBUM_W
        self.album = self._Keep(AlbumButton(page, kit, ax, ay, aw, album.GetText(), event=compact.OpenAlbum))
        self.buttons.append((self.album, album))
        # The EXE cannot tell a native button's state (no wndMgr.IsDisable): the originals' own Enable / Disable calls
        # (uipetcompact.Refresh on an action state change) are tracked and mirrored; the start is the known state.
        state = compact.actionState
        for index, (button, original) in enumerate(self.buttons):
            enabled = True if state is None or index == 3 else bool(state[0] if index < 2 else state[1])
            uir1.TrackEnabled(original, enabled, lambda on, button=button: button.Enable() if on else button.Disable())
            button.Enable() if enabled else button.Disable()
        glyph = owner.GetChild('AlbumGlyph')
        self._Reparent(glyph, self.album, 0, 0)
        self.album.SetGlyph(glyph)
        badge = getattr(compact, 'captureBadge', None)
        if badge is not None:
            self._Reparent(badge, self.album, aw - BADGE_MARGIN - badge.GetWidth(), (T.BTN_H - badge.GetHeight()) // 2)
        gauge = getattr(owner, 'lifeTimeGauge', None)
        if gauge is not None and not isinstance(gauge, GaugeAdapter):
            self.gauge = gauge
            owner.lifeTimeGauge = GaugeAdapter(gauge, self)
        self.SetLife(0, 0)
        self.Sync()

    def _MirrorFlash(self, button, original):
        """The original feed / evolution button flashes when the pet can be fed or evolved (EnableFlash /
        DisableFlash from uipetinfo); the hidden original keeps doing so and the R1 button shows it as the primary
        one (the red vein)."""
        enable, disable = original.EnableFlash, original.DisableFlash

        def on():
            enable()
            button.SetPrimary(True)

        def off():
            disable()
            button.SetPrimary(False)
        original.EnableFlash, original.DisableFlash = on, off
        self.flashing.append(original)

    def _Reparent(self, widget, parent, x, y):
        self.reparented.append((widget, widget.parent if hasattr(widget, 'parent') else None,
                                widget.GetLocalPosition()))
        widget.SetParent(parent)
        widget.SetPosition(int(x), int(y))

    # ------------------------------------------------------------------ fed by uipetcompact / uipetinfo
    def SetExperience(self, value, total):
        """The pet's experience (uipetcompact.SetExperience: battle + food into one total) as the R1 gauge."""
        ratio = max(0.0, min(1.0, float(value) / total)) if total else 0.0
        if ratio != self.exp:
            self.exp = ratio
            self.exp_fill.Apply(L.slider_fill(0, 0, int(round(ratio * self.track_w))) if ratio > 0 else [])
        text = '%d / %d' % (value, total) if total else '-'
        if self.exp_value.GetText() != text:
            self.exp_value.SetText(text)

    def SetLife(self, current, maximum):
        ratio = max(0.0, min(1.0, float(current) / maximum)) if maximum else 0.0
        if ratio != self.life:
            self.life = ratio
            self.fill.Apply(L.slider_fill(0, 0, int(round(ratio * self.track_w))) if ratio > 0 else [])

    def SetBonus(self, index, value, growth):
        """value '+4,2 %' (or '-' without a pet), growth '(1,0-6,0 %)' (or '')."""
        if self.values[index].GetText() != value:
            self.values[index].SetText(value)
        if self.ranges[index].GetText() != growth:
            self.ranges[index].SetText(growth)

    def Sync(self):
        """Mirrors the hidden originals: the title and level · age (the buttons follow their tracked Enable /
        Disable); keeps the dark page bar of the original look hidden."""
        owner = self.owner
        title = self._Title()
        if title != self.title:
            self.title = title
            self.skin.SetTitle(title)
        level, age = owner.GetChild('LevelValue').GetText(), owner.GetChild('AgeValue').GetText()
        text = ' | '.join(part for part in (level, age) if part and part != '-') or (level or '-')
        if self.level.GetText() != text:
            self.level.SetText(text)
        background = getattr(owner, 'petInfoBackground', None)
        if background is not None and background.IsShow():
            background.Hide()

    def Resize(self, w, h):
        self.skin.Resize(w, h)

    # ------------------------------------------------------------------ back to the original look
    def Restore(self):
        owner = self.owner
        if owner is None:
            return
        specs = getattr(self, 'specs', {})
        for widget in self.widgets:
            widget.Hide()
            if hasattr(widget, 'callback'):
                widget.callback = None
        if getattr(self, 'album', None) is not None:
            self.album.glyph = None
        for widget, parent, position in reversed(self.reparented):
            if parent is not None:
                widget.SetParent(parent)
            widget.SetPosition(*position)
        for name, position in self.moved.items():
            owner.GetChild(name).SetPosition(*position)
        for name in self.styled:
            line, spec = owner.GetChild(name), specs.get(name, {})
            uir1.SetFont(line, spec.get('fontname', 'Tahoma:12a'), line.GetText())
            if 'color' in spec:
                line.SetPackedFontColor(spec['color'])
        if self.styled:
            for name in ['UpBringing_Pet_Slot'] + ['PetSkillSlot%d' % index for index in range(5)]:
                owner.GetChild(name).SetSlotBaseImage(ORIGINAL_SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
        for widget, shown in self.hidden:
            if shown:
                widget.Show()
        background = getattr(owner, 'petInfoBackground', None)
        if background is not None:
            background.Show()
        if self.gauge is not None:
            owner.lifeTimeGauge = self.gauge
        for button, original in getattr(self, 'buttons', []):
            uir1.UntrackEnabled(original)
        for original in getattr(self, 'flashing', []):
            for name in ('EnableFlash', 'DisableFlash'):
                if name in original.__dict__:
                    delattr(original, name)
        self.flashing = []
        self._DragHandle(False)
        self.skin.Restore()
        self.skin.Destroy()
        self.widgets, self.buttons, self.reparented = [], [], []
        self.owner = self.compact = None

    Destroy = Restore


# --------------------------------------------------------------------------- Výskyt
HEADING_Y = 51
SEARCH_GAP = 90          # the search line: map bottom + 90 - 70 (as the original window)
ROW_GAP = 114            # the hunting time row: map bottom + 114 - 70
LINE_H = 14
FRAME_MARGIN = 2


class OccurrenceSkin(object):
    """R1 into one PetAlbumOccurrenceWindow (its BoardWithTitleBar); Apply() after every Open()."""

    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        board = window.board
        self.skin = uir1.BoardSkin(board, kit, '', on_close=window.Close)
        self.widgets = []
        self.applied = []
        try:
            self.place = self._Keep(uir1.Text(window, '', 0, HEADING_Y, kit.font('text_b'), T.IVORY, valign='top'))
            self.route = self._Keep(uir1.Text(window, '', 0, HEADING_Y, kit.font('text'), T.INK_DIM, valign='top'))
            self.search = self._Keep(uir1.Text(window, '', 0, 0, kit.font('text'), T.INK, align='center',
                                               valign='top'))
            self.when = self._Keep(uir1.Text(window, Tr('Kdy lovit', 'When to hunt'), 0, 0, kit.font('text_s'),
                                             T.INK_DIM, valign='top'))
            self.times = []
            self.map_frame = None
            self.divider = None
            for widget in self.widgets:
                widget.Hide()
        except Exception:
            self.Restore()
            raise

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def Apply(self, title, place, route, search, timing, map_rect, labels):
        """title, the place and route of the heading, the search line, the hunting time lines, the map rectangle
        (x, y, w, h) and the original labels the R1 texts replace (hidden)."""
        window, kit = self.window, self.kit
        w, h = window.GetWidth(), window.GetHeight()
        self.skin.Resize(w, h)
        self.skin.SetTitle(title)
        for label in labels:
            label.Hide()
        self.place.SetText(place)
        self.route.SetText(route)
        pw, rw = uir1.TextWidth(self.place), uir1.TextWidth(self.route)
        gap = 5 if route else 0
        left = (w - pw - gap - rw) // 2
        self.place.SetPosition(left, HEADING_Y)
        self.route.SetPosition(left + pw + gap, HEADING_Y + (kit.cell('text_b') - kit.cell('text')) // 2)
        x, y, mw, mh = map_rect
        # 2 px outside the map: the map of a later opening is made after the frame and must not cover its lines.
        m = FRAME_MARGIN
        if self.map_frame is None:
            self.map_frame = self._Keep(uir1.Frame(window, x - m, y - m, mw + 2 * m, mh + 2 * m, 'panel', bg=None))
        else:
            self.map_frame.SetPosition(x - m, y - m)
            self.map_frame.Resize(mw + 2 * m, mh + 2 * m)
        bottom = y + mh
        self.search.SetText(search)
        self.search.SetPosition(w // 2, bottom + SEARCH_GAP - 70 - 4)
        row_y = bottom + ROW_GAP - 70 - 2
        if self.divider is None:
            self.divider = self._Keep(uir1.Divider(window, T.PAD, row_y - 6, w - 2 * T.PAD))
        else:
            self.divider.SetPosition(T.PAD, row_y - 6)
        self.when.SetPosition(T.PAD + 4, row_y)
        for line in self.times:
            line.Hide()
        for index, text in enumerate(timing):
            if index >= len(self.times):
                self.times.append(self._Keep(uir1.Text(window, '', 0, 0, kit.font('text_sb'), T.IVORY,
                                                       align='right', valign='top')))
            line = self.times[index]
            room = w - 2 * T.PAD - 8 - uir1.TextWidth(self.when) - 12
            uir1.SetFont(line, kit.font('text_sb'), text)
            if uir1.TextWidth(line) > room:          # a long time text: the smaller font, then shortened
                uir1.SetFont(line, kit.font('text_s'), text)
                uir1.Fit(line, text, room)
            line.SetPosition(w - T.PAD - 4, row_y + index * LINE_H)
            line.Show()
        for widget in (self.place, self.route, self.search, self.when, self.map_frame, self.divider):
            widget.Show()
        if not route:
            self.route.Hide()

    def Restore(self):
        if self.window is None:
            return
        for widget in self.widgets:
            widget.Hide()
        self.skin.Restore()
        self.skin.Destroy()
        self.widgets, self.times = [], []
        self.window = None

    Destroy = Restore


# --------------------------------------------------------------------------- Nakrmit / Evoluce peta
FEED_HINT_COLOUR = -0x325ba5                     # the hint's colour of uiscript/petfeedwindow.py (0xffcda45b, signed)
FEED_HINT_TOP = T.HEAD_H + T.VEIN_H // 2 + 1     # the hint row: under the header vein, above the slot grid
FEED_GRID_Y = 59                                 # the 3 x 3 grid stays where it is (pitch 32, x 36)
FEED_BUTTON_W = 3 * T.SLOT + 1                   # the primary button as wide as the grid, centred under it
FEED_BUTTON_BOTTOM = T.PAD                       # px from the window's bottom edge to the button
FEED_HIDE = ('PetFeedBody',)                     # the near-black body bar of the original look


def _Signed(color):
    """A packed colour for SetPackedFontColor: the x64 binding ignores values >= 0x80000000 (PRAVIDLA-UI, Kód)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color & 0x80000000 else color


class FeedSkin(object):
    """R1 into one uipetinfo.PetFeedWindow (Nakrmit and, with the same window, Evoluce peta; 169 x 202):

    * the R1 frame and header (the window's own title: SetFeedMode's SetTitleName reaches the header too, the plain X
      closes through the window's Close); the original title bar stays as the invisible drag handle;
    * no near-black body bar: the content lies on the R1 panel; the hint ("Krystaly nebo tyčinka" / "Vlož příslušnou
      knihu") in Noto Sans, muted ink instead of the old gold, centred in its row under the header vein;
    * the 3 x 3 feed grid on the R1 item slot C (uir1.SLOT_CELL, the same cell as the R1 inventory), same place and
      pitch, so drag and drop, the item icons, the tooltips and the slot events stay those of the original grid;
    * "Nakrmit" as the R1 primary button calling the window's own ClickPetFeedButton (the original button is hidden).

    Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps the
    original look (PetFeedWindow.LoadR1)."""

    def __init__(self, window):
        import uir1skin                              # only the feed window needs it (not loaded with the pet window)
        self.window = window
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = None
        self.widgets = []
        try:
            board = window.board
            w, h = window.GetWidth(), window.GetHeight()
            self.skin = uir1.BoardSkin(board, kit, board.titleName.GetText(), on_close=ui.__mem_func__(window.Close))
            for name in FEED_HIDE:
                if window.IsChild(name):
                    rec.Hide(window.GetChild(name))
            hint = window.GetChild('FeedHint')
            font = kit.font('text_s')
            rec.Font(hint, font, _Signed(T.INK_DIM), None, FEED_HINT_COLOUR)
            rec.Position(hint, w // 2, FEED_HINT_TOP + uir1.CellTop(FEED_GRID_Y - FEED_HINT_TOP, font))
            grid = window.GetChild('FeedItemSlot')
            rec.SlotBase(grid, uir1.SLOT_CELL, ORIGINAL_SLOT_BASE)
            original = window.GetChild('FeedButton')
            rec.Hide(original)
            self.button = self._Keep(uir1.Button(board, kit, (w - FEED_BUTTON_W) // 2,
                                                 h - FEED_BUTTON_BOTTOM - T.BTN_H, FEED_BUTTON_W,
                                                 original.GetText(), primary=True,
                                                 event=ui.__mem_func__(window.ClickPetFeedButton)))
            self.set_title = board.SetTitleName
            rec.Call(lambda: setattr(board, 'SetTitleName', self.SetTitleName),
                     lambda: board.__dict__.pop('SetTitleName', None))
        except Exception:
            self.Restore()
            raise

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def SetTitleName(self, name):
        """board.SetTitleName of the original window (SetFeedMode): the hidden title text and the R1 header."""
        self.set_title(name)
        if self.skin is not None:
            self.skin.SetTitle(name)

    def Restore(self):
        if self.window is None:
            return
        for widget in self.widgets:
            widget.Hide()
            if hasattr(widget, 'callback'):
                widget.callback = None
        self.rec.Undo()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = None
        self.widgets = []
        self.window = None

    Destroy = Restore


# --------------------------------------------------------------------------- Inkubátor / Změnit jméno
# The two small pet windows of uipetinfo (PetHatchingWindow, PetNameChangeWindow) share one layout (176 x 184,
# uiscript pethatchingwindow.py / petnamechangewindow.py): a ui.Board with its own uiscript title bar, the pet's slot
# on a picture (SlotBG), the name label and the edit line on a picture (PetNamingBG), the price line and the button.
INCUBATOR_PARTS = {
    'hatching': dict(title_bar='PetHatching_TitleBar', money_window='HatchingMoneyWindow', money='HatchingMoney',
                     button='HatchingButton', event='ClickHatchingButton'),
    'name_change': dict(title_bar='PetNameChangeTitleBar', money_window='NameChangeMoneyWindow',
                        money='NameChangeMoney', button='NameChangeButton', event='ClickNameChangeButton'),
}
INCUBATOR_SLOT = (72, 38)                # the R1 slot C under the pet slot (the slot window itself stays at 72, 38)
INCUBATOR_LABEL_Y = 72                   # "Jméno mazlíka": its row (the label cell centred in INCUBATOR_ROW_H)
INCUBATOR_ROW_H = 22
INCUBATOR_FIELD = (16, 96, 144)          # x, y, w of the R1 field around the same edit line
INCUBATOR_MONEY_Y = 122                  # the price row (the R1 yang price)
INCUBATOR_BUTTON_W = 120
INCUBATOR_EDIT = (11, 28, 129, 16, 20)   # the edit line in PetNamingBG: x, y, w, h and its input limit (uiscript)
INCUBATOR_ORIGINAL_SLOT_BG = 'd:/ymir work/ui/pet/Pet_Incu_slot_001.tga'


class IncubatorSkin(object):
    """R1 into one uipetinfo.PetHatchingWindow (Inkubátor) or PetNameChangeWindow (Změnit jméno); kind is
    'hatching' or 'name_change':

    * the R1 frame and header with the window's title (the plain X closes through the window's Close); the uiscript
      title bar stays as the invisible drag handle;
    * the pet's slot on the R1 item slot C (the SlotBG picture shows the cell; the slot window and its item stay);
    * "Jméno mazlíka" in muted Noto Sans, the SAME edit line (window.petNameEdit, its return / escape / click events
      and its focus) in the R1 field instead of the parchment strip;
    * the price as the one R1 yang price of the client (root/uir1price.py, : the
      coin, "100.000 Yang" in Tahoma 12, red when the player has less) centred in the price row; the window keeps
      writing its own line ("Cena: 100.000", localeInfo.PET_HATCHING_MONEY, hidden), the price follows its amount;
    * "Vylíhnout" / "Změnit" as the R1 primary button calling the window's own handler (the original is hidden).

    Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps the
    original look (uipetinfo._PetR1Look)."""

    def __init__(self, window, kind):
        import uir1skin                              # only the small pet windows need it (not the pet window)
        parts = INCUBATOR_PARTS[kind]
        self.window = window
        self.kind = kind
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = self.field = None
        self.widgets = []
        child = window.GetChild
        try:
            board = child('board')
            w, h = window.GetWidth(), window.GetHeight()
            bar = child(parts['title_bar'])
            title = child('TitleName').GetText()
            self.skin = uir1.BoardSkin(board, kit, title, on_close=ui.__mem_func__(window.Close), hide=(bar,))
            slot_bg = child('SlotBG')
            rec.Image(slot_bg, uir1.SLOT_CELL, INCUBATOR_ORIGINAL_SLOT_BG)
            rec.Position(slot_bg, *INCUBATOR_SLOT)
            small = kit.font('text_s')
            # the label and the price: centred texts in their own uiscript windows (all_align), the windows are
            # centred in their R1 rows (the size stays, so the engine's alignment of the text stays)
            for name, line, row_y, colour in (('PetNamingTitleWindow', 'PetNamingTitle', INCUBATOR_LABEL_Y, T.INK_DIM),):
                holder = child(name)
                rec.Position(holder, (w - holder.GetWidth()) // 2,
                             row_y + (INCUBATOR_ROW_H - holder.GetHeight()) // 2)
                rec.Font(child(line), small, _Signed(colour), None, _Signed(0xFFFFFFFF))
            self._Price(board, w, child(parts['money']))
            self._Field(child('PetNamingBG'), window.petNameEdit)
            original = child(parts['button'])
            rec.Hide(original)
            self.button = self._Keep(uir1.Button(board, kit, (w - INCUBATOR_BUTTON_W) // 2, h - T.PAD - T.BTN_H,
                                                 INCUBATOR_BUTTON_W, original.GetText(), primary=True,
                                                 event=ui.__mem_func__(getattr(window, parts['event']))))
            import uiconfirm
            rec.Call(lambda: None, uiconfirm.Visual(original, self.button))
        except Exception:
            self.Restore()
            raise

    def _Price(self, board, w, line):
        """The R1 yang price in the price row; the window's own line stays its source (hidden): every SetText of the
        window reaches the price too (the amount is the number in the line). Restore gives the line back."""
        import uir1price
        rec = self.rec
        self.price = self._Keep(uir1price.Price(board, w // 2,
                                                INCUBATOR_MONEY_Y + (INCUBATOR_ROW_H - uir1price.ICON_H) // 2,
                                                'center'))
        import weakref
        me = weakref.ref(self)
        method = type(line).SetText

        def set_text(text):
            method(line, text)
            skin = me()
            if skin is not None:
                skin.SyncPrice(text)

        def back():
            line.__dict__.pop('SetText', None)
        rec.Call(lambda: setattr(line, 'SetText', set_text), back)
        rec.Hide(line)
        self.SyncPrice(line.GetText())

    def SyncPrice(self, text):
        import uir1price
        price = getattr(self, 'price', None)
        if price is None or self.window is None:
            return
        amount = uir1price.ParseAmount(text)
        price.SetPrice(amount, uir1price.CanAfford(amount))

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def _Field(self, strip, edit):
        """The edit line moves from the parchment strip (hidden) into the R1 field; back on Restore."""
        rec = self.rec
        rec.Hide(strip)

        def back():
            ex, ey, ew, eh, limit = INCUBATOR_EDIT
            edit.SetParent(strip)
            edit.SetPosition(ex, ey)
            edit.SetSize(ew, eh)
            edit.SetMax(limit)
            text = edit.GetText()
            edit.SetText('')
            edit.SetDefaultFontName()
            edit.SetText(text)
        rec.Call(lambda: None, back)                 # recorded first: a failure below still brings the line back
        x, y, w = INCUBATOR_FIELD
        self.field = uir1.Field(self.window.GetChild('board'), self.kit, x, y, w, edit=edit,
                                max_len=INCUBATOR_EDIT[4])
        self._Keep(self.field)
        if edit.IsFocus():
            self.field.SetFocused(True)

    def Restore(self):
        if self.window is None:
            return
        for widget in self.widgets + ([self.field] if self.field is not None else []):
            widget.Hide()
            if hasattr(widget, 'callback'):
                widget.callback = None
        self.rec.Undo()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = self.field = None
        self.widgets = []
        self.window = None

    Destroy = Restore
