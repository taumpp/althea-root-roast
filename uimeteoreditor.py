# -*- coding: utf-8 -*-
"""Editor "Vzhled fronty meteorů" v5 (2026-10-05): the queue marker editor in the Althea UI kit.

Same functions as uimetinqueuedesigneditor.MetinQueueDesignEditor (kept unchanged for the old settings look),
same draft controller and library model, new face:

  v5 kit: window frame + title bar (Spectral / Althea Caps), light separators, the one
  button family of the kit (2026-10-06): secondary buttons, one primary (Uložit), chips for Obal / Prstenec
  left:  segment tabs Efekty | Barva a jas | Pohyb | Doladění
         Efekty: Obal / Prstenec chips, catalogue segment Obaly | Prstence, search in a kit edit field, effect
                 rows with the kit scroll bar, count;  Barva a jas: swatches + Vlastní…, Jas kresby, Záře;  Pohyb: tempo of both
                 layers, Pulzování jasu, Ostatní meteory;  Doladění: sizes, stroke, upper marker, sparks
  right: the dominant live preview (uimeteorpreview: framed stone, studio backdrop, character silhouette),
         meteor choice, Kamera (reset view)
  foot:  status / hover help, Reset vzhledu, Výchozí sestava, Zpět, Zrušit, Uložit

Drafts are never written before Uložit (DesignController); Zrušit and ESC discard them.

Fit to the game window: a game window of half a 1920 x 1080 screen (960 x 1080) cut the
1100 px editor off on the left and right. The window is clamped to the screen minus SCREEN_MARGIN: the preview
shrinks first (and the window gets lower so the preview keeps a sane aspect), below SideMinWidth() the preview
goes above the option list (stacked). The footer and the stone row wrap to two lines when they do not fit.
A resolution change rebuilds the layout once (OnChangeResolution, polled cheaply in OnUpdate) and centres it.
"""
import ui
import wndMgr

import metinqueuelibrary as design
import uimetinqueueappearance as appearance
import uikit
import uikittokens as T
from settingslocale import Text as Tr
from uimeteorpreview import MeteorPreviewController, MeteorPreviewView, RecordName, ColorName, StoneScale
from uisettingsmeteorpage import PRIMARY

SIZES = {'1080': (1100, 720), '768': (860, 600)}
SCREEN_MARGIN = 16                       # free screen edge around the editor
MIN_PREVIEW_W = {'1080': 420, '768': 320}  # narrowest side-by-side preview; below it the preview goes on top
MIN_PREVIEW_H = 150
SIDE_ASPECT = 1.2                        # a narrowed side preview keeps at least this width / height (H allowing)
STACK_ASPECT = 1.6
COLORS = (0xE5B95F, 0xFF405F, 0x69BEFF, 0xB290FF, 0x69DF9D, 0xF1E8D6)
TABS = ((0, Tr('Efekty', 'Effects')), (1, Tr('Barva a jas', 'Colour and light')), (2, Tr('Pohyb', 'Motion')),
        (3, Tr('Doladění', 'Fine tuning')))


def ScreenSize():
    try:
        return int(wndMgr.GetScreenWidth()), int(wndMgr.GetScreenHeight())
    except Exception:
        return 1024, 768


def Metrics(prof):
    """(outer margin, left column width, column gap) of a profile."""
    return (24, 420, 28) if prof == '1080' else (16, 330, 20)


def SideMinWidth(prof):
    """Narrowest window with the option list and the preview side by side."""
    m, lw, gap = Metrics(prof)
    return m + lw + gap + MIN_PREVIEW_W[prof] + m


def FitWidth(prof, screen_width):
    """('side' | 'stack', window width) for a screen width: the full size when it fits, then a narrower preview,
    below SideMinWidth() the stacked layout as wide as the screen allows."""
    avail = int(screen_width) - 2 * SCREEN_MARGIN
    base = SIZES[prof][0]
    if avail >= base:
        return 'side', base
    if avail >= SideMinWidth(prof):
        return 'side', avail
    return 'stack', max(300, avail)


def NewLookEnabled():
    """The new settings look (default) uses this editor; "Starý vzhled" keeps the old one."""
    try:
        import settingslook
        return settingslook.Get('look') != 'legacy'
    except Exception:
        return False


def CreateEditor(backend=None, onClose=None):
    """Entry for the other callers (uimetinqueueeditor factory, offline queue viewer, uimetinqueuespirits):
    the v5 editor with the new settings look, None with the old look (the caller keeps the old editor)."""
    if not NewLookEnabled():
        return None
    return MeteorDesignEditor(backend, onClose)


class LibrarySearch(ui.EditLine):
    def __init__(self, owner):
        ui.EditLine.__init__(self)
        self.owner = owner
        self.SetEscapeEvent(owner.Close)
        self.SetReturnEvent(owner.FocusLibrary)

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        self.owner.SearchChanged()

    def OnPressEscapeKey(self):
        self.owner.Close()
        return True


class EffectRow(uikit.Interactive):
    """One catalogue row: diamond bullet, name, note for effects not converted for the test yet."""

    def __init__(self, owner, w, h):
        uikit.Interactive.__init__(self)
        self.owner, self.index, self.selected = owner, 0, False
        kit = owner.kit
        self.SetParent(owner.list)
        self.SetSize(w, h)
        self.band = uikit.Band(self, 0, 0, w, h, 'hover')
        self.band.Hide()
        self.mark = uikit.Band(self, 0, 0, w, h, 'selected')
        self.mark.Hide()
        bw, bh = kit.size('bullet/diamond_normal.png')
        self.bullet = uikit.Image(self, kit.rel('bullet/diamond_normal.png'), 10, (h - bh) // 2)
        self.label = uikit.Text(self, '', 10 + bw + 12, h // 2, kit.font('M'), T.INK_DIM, limit=w - bw - 40)
        self.note = uikit.Text(self, '', w - 10, h // 2, kit.font('S'), T.DISABLED, align='right')
        self.OnMouseWheel = owner._CatalogWheel
        self.Show()

    def Set(self, index, text, selected, available):
        self.index, self.selected = index, selected
        self.label.SetText(text)
        self.note.SetText('' if available else Tr('čeká na převedení', 'not converted yet'))
        self.enabled = available
        self.paint()

    def paint(self):
        self.mark.Show() if self.selected else self.mark.Hide()
        self.band.Show() if self.hovered and not self.selected else self.band.Hide()
        self.bullet.LoadImage(uikit.Path(self.owner.kit.rel('bullet/diamond_%s.png' %
                                                            ('selected' if self.selected else 'normal'))))
        self.label.SetPackedFontColor(T.GOLD_HI if self.selected else (T.DISABLED if not self.enabled else
                                                                       (T.INK if self.hovered else T.INK_DIM)))

    def click(self):
        self.owner._SelectRow(self.index)


class ColorSwatch(uikit.Interactive):
    def __init__(self, parent, x, y, s, rgb, event):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(s, s)
        self.selected = False
        self.ring = []
        for rx, ry, rw, rh in ((0, 0, s, 2), (0, s - 2, s, 2), (0, 0, 2, s), (s - 2, 0, 2, s)):
            bar = ui.Bar()
            bar.SetParent(self)
            bar.AddFlag('not_pick')
            bar.SetPosition(rx, ry)
            bar.SetSize(rw, rh)
            bar.Show()
            self.ring.append(bar)
        self.fill = ui.Bar()
        self.fill.SetParent(self)
        self.fill.AddFlag('not_pick')
        self.fill.SetPosition(4, 4)
        self.fill.SetSize(s - 8, s - 8)
        self.fill.SetColor(uikit.GenerateColor(rgb))
        self.fill.Show()
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        color = T.GOLD_HI if self.selected else (T.BRASS_LINE if self.hovered else T.BRONZE_LINE_DK)
        for bar in self.ring:
            bar.SetColor(uikit.GenerateColor(color))


class MeteorDesignEditor(ui.Window):
    def __init__(self, backend=None, onClose=None):
        ui.Window.__init__(self)
        self.backend = design.AdaptBackend(backend)
        self.closeEvent = onClose
        self.controller = None
        self.children, self.panes, self.rows = [], [], []
        self.widgets, self.sliders, self.choices = {}, {}, {}
        self.libraryRows, self.libraryEntries = [], []
        self.activePane, self.libraryLayer = 0, 0
        self.catalogOffsets, self.searches = [0, 0], ["", ""]
        self.syncedPreset = None
        self.hint_buttons = []
        self.status_text = ''
        self.AddFlag('movable')
        self.AddFlag('float')
        # Close / Hide / OnUpdate stay safe before (or after a failed) _Build.
        self.search, self.view, self.screen, self.mode = None, None, None, 'side'
        self.kit = uikit.Kit(uikit.Profile(), uikit.FontSet())   # Spectral; Tahoma when the EXE cannot draw it
        self.W, self.H = SIZES[self.kit.prof]
        self.SetSize(self.W, self.H)
        self._Build()
        self.controller = MeteorPreviewController(self, self.backend, self.view)

    # ---------------------------------------------------------------- helpers
    def _Keep(self, widget, name=None):
        self.children.append(widget)
        if name:
            self.widgets[name] = widget
        return widget

    def _Text(self, parent, text, x, y, size='M', color=None, name=None, **kw):
        return self._Keep(uikit.Text(parent, text, x, y, self.kit.font(size), T.INK if color is None else color, **kw),
                          name)

    def _Button(self, parent, x, y, w, text, event, name=None, primary=False, icon=None, hint=None, size='content'):
        button = uikit.Button(parent, self.kit, x, y, w, text, role=PRIMARY if primary else 'secondary', icon=icon,
                              event=event, size=size)
        button.FitWidth(w)
        if hint:
            self.hint_buttons.append((button, hint))
        return self._Keep(button, name)

    def _Row(self, pane, field, height):
        row = self._Keep(ui.Window())
        row.SetParent(self.panes[pane])
        row.SetSize(self.lw, height)
        row.Show()
        self.rows.append((pane, field, row, height))
        return row

    def _Slider(self, pane, field, label):
        k = self.kit
        knob = k.size('knob_normal.png')[0]
        h = k.cell('M') + 10 + knob + 14
        row = self._Row(pane, field, h)
        self._Text(row, label, 0, 0, valign='top')
        value = self._Text(row, '', self.lw, 0, 'M', T.INK_DIM, align='right', valign='top')
        slider = self._Keep(uikit.Slider(row, k, self.lw - knob, event=lambda: self.controller._SampleSliders()))
        slider.SetPosition(0, k.cell('M') + 10)
        self.sliders[field] = (pane, row, slider, value)

    def _Choice(self, pane, field, label, choices, name):
        k = self.kit
        h = k.cell('M') + 10 + k.p('seg_h') + 16
        row = self._Row(pane, field, h)
        self._Text(row, label, 0, 0, valign='top')
        segment = self._Keep(uikit.Segment(row, k, choices, event=lambda value: self.controller.SetValue(field, value),
                                           font=k.font('S'), max_width=self.lw, min_cell=60), name)
        segment.SetPosition(0, k.cell('M') + 10)
        self.choices[name] = (field, segment)

    def _Hint(self, pane, lines, name=None):
        k = self.kit
        lh = k.cell('S') + 4
        row = self._Row(pane, None, len(lines) * lh + 6)
        for index, text in enumerate(lines):
            self._Text(row, text, 0, 4 + index * lh, 'S', T.MUTED, valign='top',
                       name=(name if index == 0 else None), limit=self.lw)

    # ---------------------------------------------------------------- build
    def _Build(self):
        k = self.kit
        big = k.prof == '1080'
        m, base_lw, col_gap = Metrics(k.prof)
        self.screen = ScreenSize()
        sw, sh = self.screen
        self.mode, W = FitWidth(k.prof, sw)
        avail_h = max(200, sh - 2 * SCREEN_MARGIN)
        # The frame first (it is the background); its height is set once the rows below are measured.
        self.frame = self._Keep(uikit.Frame(self, k, 'window', 0, 0, W, SIZES[k.prof][1], bg=True))
        self.bar = self._Keep(uikit.TitleBar(self, k, 5, 5, W - 10, Tr('Vzhled fronty meteorů', 'Stone queue look'),
                                             kind='window', on_close=self.Close))
        top = 5 + self.bar.Height() + (14 if big else 10)
        stack = self.mode == 'stack'
        self.lw = W - 2 * m if stack else base_lw
        px = m if stack else m + self.lw + col_gap
        pw = W - m - px
        seg_h = k.p('seg_h')
        tab_gap = 18 if big else 12
        status_h = k.cell('S') + 10
        # Footer buttons (placed below): one row, or two rows when the window is too narrow.
        footer = self._BuildFooter(big, W - 2 * m)
        bar_h = uikit.ButtonHeight(k, 'bar')
        foot_h = (70 if big else 54) if self.footer_rows == 1 else 2 * bar_h + 10 + (24 if big else 16)
        # Stone row under the preview: "Meteor" + stone choice + Kamera on one line, or the camera on a second one.
        under = self._BuildStoneRow(big, pw)
        under_h = (seg_h if self.stone_rows == 1 else 2 * seg_h + 8) + 16
        need = self._PaneNeed()
        if stack:
            rest = top + 12 + under_h + seg_h + tab_gap + need + 10 + status_h + foot_h
            ph = min(int(pw / STACK_ASPECT), 420)
            H = min(rest + ph, avail_h)
            ph = max(MIN_PREVIEW_H, H - rest)
            H = min(rest + ph, avail_h)
        else:
            rest = top + 12 + under_h + status_h + foot_h
            H = SIZES[k.prof][1]
            if W < SIZES[k.prof][0]:
                # Narrower preview: lower window too (the preview keeps SIDE_ASPECT) unless the options need it.
                H = min(H, max(rest + int(pw / SIDE_ASPECT), top + seg_h + tab_gap + need + 10 + status_h + foot_h))
            H = min(H, avail_h)
            ph = H - rest
        self.W, self.H = W, H
        self.SetSize(W, H)
        self.frame.SetSize(W, H)
        self.frame.Apply(uikit.L.frame('window', k.prof, W, H, bg=True))
        foot = H - foot_h
        status_y = foot - status_h
        if stack:
            view_y = top
            tabs_y = top + ph + 12 + under_h
        else:
            view_y = tabs_y = top
        lx = m
        # Left column (stacked: under the preview): tabs (segment), then one pane per tab.
        self.tabs = self._Keep(uikit.Segment(self, k, TABS, event=self._SetPane, max_width=self.lw,
                                             font=k.font('S' if not big else 'M')))
        self.tabs.SetPosition(lx, tabs_y)
        pane_top = tabs_y + seg_h + tab_gap
        self.pane_h = max(0, status_y - 10 - pane_top)
        for index in range(len(TABS)):
            pane = self._Keep(ui.Window())
            pane.SetParent(self)
            pane.SetPosition(lx, pane_top)
            pane.SetSize(self.lw, self.pane_h)
            pane.Show()
            self.panes.append(pane)
        self._BuildEffects()
        self._BuildColour()
        self._BuildMotion()
        self._BuildTuning()
        # The dominant preview (right column, stacked: on top), stone choice and camera reset under it.
        self.view = MeteorPreviewView(self, k, px, view_y, pw, ph, track=self.children.append)
        self.widgets.update(Preview=self.view.target, PreviewInput=self.view.input)
        self._PlaceStoneRow(under, px, view_y + ph + 12, pw)
        # Status line and footer.
        self._Keep(uikit.HLine(self, m, foot - 1, W - 2 * m, T.BRONZE_LINE_DK))
        self._Text(self, '', m, status_y, 'S', T.MUTED, name='Status', valign='top', limit=W - 2 * m)
        self._PlaceFooter(footer, m, foot, foot_h, bar_h)
        self._SetPane(0, False)

    def _BuildFooter(self, big, room):
        bw = 170 if big else 140
        reset = self._Button(self, 0, 0, bw, Tr('Reset vzhledu', 'Reset look'),
                             lambda: self.controller.RestoreDefaults(), 'ResetButton', size='bar',
                             hint=Tr('Výchozí hodnoty pro vybraný obal a prstenec. Typy zůstanou vybrané.',
                                     'Default values of the selected body and ring. The types stay selected.'))
        default = self._Button(self, 0, 0, bw, Tr('Výchozí sestava', 'Default set'),
                               lambda: self.controller.RestoreAllDefaults(), 'DefaultButton', size='bar',
                               hint=Tr('Pulzující obal + Klasický vír, zlatá, základní velikost a jas.',
                                       'Pulsing body + Classic swirl, gold, base size and brightness.'))
        undo = self._Button(self, 0, 0, 90, Tr('Zpět', 'Undo'), lambda: self.controller.UndoReset(), 'UndoButton',
                            size='bar', hint=Tr('Vrátí poslední reset.', 'Undoes the last reset.'))
        save = self._Button(self, 0, 0, 190 if big else 150, Tr('Uložit', 'Save'), self._Ok, 'SaveButton', primary=True,
                            size='bar', hint=Tr('Uloží celý rozepsaný vzhled (všechny upravené obaly) a použije ho ve hře.',
                                    'Saves the whole draft (every edited body) and uses it in the game.'))
        cancel = self._Button(self, 0, 0, bw - 30, Tr('Zrušit', 'Cancel'), self.Close, 'CancelButton', size='bar',
                              hint=Tr('Zavře editor bez uložení.', 'Closes the editor without saving.'))
        left, right = (reset, default, undo), (save, cancel)

        def width(buttons):
            return sum(b.w for b in buttons) + 10 * (len(buttons) - 1)
        if width(left) + 24 + width(right) > room:
            for button in left + right:   # as wide as their labels before wrapping
                button.FitWidth()
        self.footer_rows = 1 if width(left) + 24 + width(right) <= room else 2
        return left, right

    def _PlaceFooter(self, footer, m, foot, foot_h, bar_h):
        left, right = footer
        if self.footer_rows == 1:
            rows = (foot + (foot_h - bar_h) // 2 - 2,) * 2
        else:
            first = foot + (foot_h - 2 * bar_h - 10) // 2
            rows = (first, first + bar_h + 10)
        x = m
        for button in left:
            button.SetPosition(x, rows[0])
            x += button.w + 10
        # confirm left, cancel right (the rule of the whole client): Uložit, Zrušit
        cancel, save = right[1], right[0]
        cancel.SetPosition(self.W - m - cancel.w, rows[1])
        # GetLocalPosition(), never widget.x: only the test fakes have .x - in game this raised AttributeError and
        # "Upravit vzhled…" did nothing (syserr 2026-10-05 23:22, uimeteoreditor.py _Build).
        save.SetPosition(cancel.GetLocalPosition()[0] - 10 - save.w, rows[1])

    def _BuildStoneRow(self, big, pw):
        k = self.kit
        import nonplayer
        models = [(vnum, nonplayer.GetMonsterName(vnum) or u'Meteor %d' % vnum) for vnum in design.MODEL_VNUMS]
        camera_button = self._Button(self, 0, 0, 130 if big else 110, Tr('Kamera', 'Camera'), self._ResetCamera,
                                     'CameraButton', icon='camera',
                                     hint=Tr('Výchozí pohled na kámen (otočení, posun a přiblížení zpět).',
                                             'Default view of the stone (rotation, pan and zoom back).'))
        label = self._Text(self, Tr('Meteor', 'Stone'), 0, 0, 'S', T.MUTED)
        lw = 70 if big else 56
        inline = pw - camera_button.w - 16 - lw
        self.models = self._Keep(uikit.Segment(self, k, models, event=self._SetModel, font=k.font('S'),
                                               max_width=inline, min_cell=60), 'Models')
        self.stone_rows = 1 if self.models.Width() <= inline else 2
        if self.stone_rows == 2:
            self.models.Hide()
            self.children.remove(self.models)
            self.models = self._Keep(uikit.Segment(self, k, models, event=self._SetModel, font=k.font('S'),
                                                   max_width=pw - lw, min_cell=60), 'Models')
        return camera_button, label, lw

    def _PlaceStoneRow(self, under, px, uy, pw):
        camera_button, label, lw = under
        seg_h = self.kit.p('seg_h')
        label.SetPosition(px, uy + seg_h // 2)
        self.models.SetPosition(px + lw, uy)
        cy = uy if self.stone_rows == 1 else uy + seg_h + 8
        camera_button.SetPosition(px + pw - camera_button.w, cy + (seg_h - camera_button.h) // 2)

    def _PaneNeed(self):
        """Height the tallest option pane needs (every row shown; the Efekty list keeps at least four rows)."""
        k = self.kit
        slider = k.cell('M') + 10 + k.size('knob_normal.png')[0] + 14
        choice = k.cell('M') + 10 + k.p('seg_h') + 16
        hint = k.cell('S') + 4

        def hints(lines):
            return lines * hint + 6
        swatch = 34 if k.prof == '1080' else 28
        colour = k.cell('M') + 10 + swatch + 10 + k.cell('S') + 14 + 2 * slider + hints(2)
        motion = 2 * slider + 2 * choice + hints(2)
        tuning = 6 * slider + hints(1)
        chip = uikit.L.button6_height(k.prof, 'c')
        effects = (2 * (k.cell('S') + 8) + chip + 12 + k.p('seg_h') + 14 + k.p('seg_h') + 10 +
                   4 * k.p('sub_pitch') + k.cell('S') + 8)
        return max(colour, motion, tuning, effects)

    def _BuildEffects(self):
        k = self.kit
        pane = self.panes[0]
        # Layers on/off: v5 chips (two independent choices), the catalogue segment picks which list is shown.
        self._Text(pane, Tr('Vrstvy', 'Layers'), 0, 0, 'S', T.MUTED, valign='top')
        y = k.cell('S') + 8
        x = 0
        for field, label, name in ((design.BODY_ENABLED, Tr('Obal', 'Body'), 'BodyToggle'),
                                   (design.RING_ENABLED, Tr('Prstenec', 'Ring'), 'RingToggle')):
            chip = self._Keep(uikit.Chip(pane, k, x, y, label, event=lambda field=field: self._Flip(field)), name)
            x += chip.Width() + 10
        layer = self._Keep(uikit.Segment(pane, k, ((0, Tr('Obaly', 'Bodies')), (1, Tr('Prstence', 'Rings'))),
                                         event=self.SetLibraryLayer, min_cell=96 if k.prof == '1080' else 80),
                           'Layer')
        chip_h = self.widgets['BodyToggle'].h
        lx, ly, top = self.lw - layer.Width(), y + (chip_h - k.p('seg_h')) // 2, 0
        if x - 10 + 24 > lx:  # no room beside the chips: the catalogue goes under them
            top = y + chip_h + 12
            lx, ly = 0, top + k.cell('S') + 8
        layer.SetPosition(lx, ly)
        self._Text(pane, Tr('Katalog', 'Catalogue'), lx, top, 'S', T.MUTED, valign='top')
        y = max(y + chip_h, ly + k.p('seg_h')) + 14
        # Search: v5 edit field (recessed well, brass rim while focused) around the catalogue search line.
        # The kit's one search field (2026-10-06: the placeholder was small and not centred, the ornate "×"
        # too big): placeholder in the row font, centred, a small plain clear cross only while there is text.
        self.search = self._Keep(LibrarySearch(self))
        field = self._Keep(uikit.SearchField(pane, k, 0, y, self.lw, hint=Tr('Hledat efekt...', 'Search effect…'),
                                             edit=self.search, max_len=60, on_clear=self.ClearSearch), 'SearchField')
        self.widgets['ClearSearch'] = field.clear
        y += field.h + 10
        pitch = k.p('sub_pitch')
        count_h = k.cell('S') + 8
        visible = max(4, (self.pane_h - y - count_h) // pitch)
        # v5 kit scroll bar (SettingsScrollBar API) beside the rows.
        self.scroll = self._Keep(uikit.ScrollBar(k))
        self.scroll.SetParent(pane)
        self.scroll.SetScrollBarSize(visible * pitch)
        self.scroll.SetPosition(self.lw - self.scroll.Width(), y)
        self.scroll.SetScrollEvent(lambda: self._ScrollCatalog(self.scroll.GetPos()))
        self.scroll.OnMouseWheel = self._CatalogWheel
        list_w = self.lw - self.scroll.Width() - 4
        self.list = self._Keep(ui.Window())
        self.list.SetParent(pane)
        self.list.SetPosition(0, y)
        self.list.SetSize(list_w, visible * pitch)
        self.list.OnMouseWheel = self._CatalogWheel
        self.list.Show()
        for index in range(visible):
            row = self._Keep(EffectRow(self, list_w, pitch))
            row.SetPosition(0, index * pitch)
            self.libraryRows.append(row)
        self._Text(pane, '', 0, y + visible * pitch + 6, 'S', T.MUTED, name='CatalogueCount', valign='top')

    def _BuildColour(self):
        k = self.kit
        color = self._Row(1, design.PRIMARY, k.cell('M') + 10 + 34 + 10 + k.cell('S') + 14)
        self._Text(color, Tr('Barva obalu a prstence', 'Body and ring colour'), 0, 0, valign='top')
        s = 34 if k.prof == '1080' else 28
        y = k.cell('M') + 10
        for index, rgb in enumerate(COLORS):
            self._Keep(ColorSwatch(color, index * (s + 8), y, s, rgb,
                                   lambda value=rgb: self.controller.SetValue(design.PRIMARY, value)),
                       'Color%d' % index)
        custom = self._Button(color, 0, 0, 120, Tr('Vlastní...', 'Custom…'),
                              lambda: self.controller.OpenColor(design.PRIMARY), 'CustomColor')
        custom.SetPosition(self.lw - custom.w, y + (s - custom.h) // 2)
        self._Text(color, '', 0, y + s + 8, 'S', T.INK_DIM, name='ColorValue', valign='top')
        for field, label in ((design.BRIGHTNESS, Tr('Jas kresby', 'Artwork brightness')),
                             (design.GLOW, Tr('Záře kolem efektu', 'Glow around the effect'))):
            self._Slider(1, field, label)
        self._Hint(1, (Tr('Jas zesvětlí kresbu. Záře přidá světelný lem.',
                          'Brightness lightens the artwork. Glow adds a light rim.'),
                       Tr('Jiskry nastavíš v záložce Doladění.', 'Sparks are in Fine tuning.')))

    def _BuildMotion(self):
        self._Slider(2, design.TEMPO, Tr('Rychlost obalu', 'Body speed'))
        self._Slider(2, design.RING_TEMPO, Tr('Rychlost prstence', 'Ring speed'))
        self._Choice(2, design.PULSE, Tr('Pulzování jasu', 'Brightness pulse'), design.PULSE_CHOICES, 'PulseButton')
        self._Choice(2, design.FOCUS, Tr('Ostatní meteory ve frontě', 'Other stones in the queue'),
                     design.FOCUS_CHOICES, 'FocusButton')
        self._Hint(2, ('', Tr('Každá vrstva má vlastní nastavení pohybu.', 'Each layer has its own motion.')),
                   'MotionHint')

    def _BuildTuning(self):
        for field, label in ((design.SIZE, Tr('Velikost obalu', 'Body size')),
                             (design.RING_SIZE, Tr('Velikost prstence', 'Ring size')),
                             (design.RING_WIDTH, Tr('Tloušťka tahu', 'Stroke width')),
                             (design.MARKER_SCALE, Tr('Velikost horní značky', 'Upper marker size')),
                             (design.CLEARANCE, Tr('Odstup horní značky', 'Upper marker clearance')),
                             (design.SPARKS, Tr('Množství jisker', 'Spark density'))):
            self._Slider(3, field, label)
        self._Hint(3, (Tr('100 % zachovává základní velikost návrhu.', '100 % keeps the base size of the design.'),))

    # ---------------------------------------------------------------- tabs, layers, catalogue
    def _SetPane(self, index, sample=True):
        if self.controller and sample:
            self.controller._SampleSliders()
        if index != 0:
            self.search.KillFocus()
        self.activePane = index
        for number, pane in enumerate(self.panes):
            pane.Show() if number == index else pane.Hide()
        self.tabs.SetValue(index)

    def SetLibraryLayer(self, layer):
        self.searches[self.libraryLayer] = self.search.GetText()
        self.libraryLayer = layer
        self.search.SetText(self.searches[layer])
        self._SetPane(0)
        self._RefreshCatalogue()
        self.FocusLibrary()

    def FocusLibrary(self):
        self.search.KillFocus()
        self.SetFocus()

    def SearchChanged(self):
        self.searches[self.libraryLayer] = self.search.GetText()
        self.catalogOffsets[self.libraryLayer] = 0
        self._RefreshCatalogue()

    def ClearSearch(self):
        self.search.SetText("")
        self.SearchChanged()
        self.search.SetFocus()
        field = self.widgets.get('SearchField')
        if field is not None:
            field.SyncClear()

    def _CatalogWheel(self, delta):
        self.catalogOffsets[self.libraryLayer] += -1 if delta > 0 else 1
        self._RefreshCatalogue()
        return True

    def _ScrollCatalog(self, pos):
        maximum = max(0, len(self.libraryEntries) - len(self.libraryRows))
        self.catalogOffsets[self.libraryLayer] = int(round(pos * maximum))
        self._RefreshCatalogue(scroll=False)

    def _RefreshCatalogue(self, scroll=True):
        if not self.controller or self.controller.draft is None:
            return
        draft = self.controller.draft
        raw = design.APPROVED_RINGS if self.libraryLayer else tuple((row[0], row[2]) for row in design.APPROVED_CATALOG)
        query = design.SearchKey(self.search.GetText().strip())
        entries = [row for row in raw if not query or query in design.SearchKey(row[1]) or query == str(row[0])]
        allowed = dict(design.RingChoices(draft[0])) if self.libraryLayer else design.BY_NUMBER
        entries.sort(key=lambda row: row[0] not in allowed)  # immediately usable choices first
        self.libraryEntries = entries
        selected = draft[design.RING_STYLE] if self.libraryLayer else draft[0]
        maximum = max(0, len(entries) - len(self.libraryRows))
        offset = max(0, min(maximum, self.catalogOffsets[self.libraryLayer]))
        self.catalogOffsets[self.libraryLayer] = offset
        for index, row in enumerate(self.libraryRows):
            if offset + index >= len(entries):
                row.Hide()
                continue
            number, label = entries[offset + index]
            row.Set(index, label, selected == number, number in allowed)
            row.Show()
        if maximum:
            self.scroll.SetMiddleBarSize(float(len(self.libraryRows)) / len(entries))
            self.scroll.SetScrollStep(1.0 / maximum)
            if scroll:
                self.scroll.SetPos(float(offset) / maximum, False)
            self.scroll.Show()
        else:
            self.scroll.Hide()
        self.widgets['Layer'].SetValue(self.libraryLayer)
        kind = Tr('prstenců', 'rings') if self.libraryLayer else Tr('obalů', 'bodies')
        ready = sum(1 for number, _ in raw if number in allowed)
        found = (Tr(' | nalezeno %d', ' · found %d') % len(entries)) if query else ''
        self.widgets['CatalogueCount'].SetText(Tr(u'%d %s ve výběru | %d dostupných v testu', '%d %s · %d available')
                                               % (len(raw), kind, ready) + found)

    def _SelectRow(self, row):
        index = self.catalogOffsets[self.libraryLayer] + row
        if index >= len(self.libraryEntries):
            return
        number = self.libraryEntries[index][0]
        if self.libraryLayer:
            if number in dict(design.RingChoices(self.controller.draft[0])):
                self.controller.SetValue(design.RING_STYLE, number)
        else:
            self.controller.Select(number)

    def _Flip(self, field):
        if self.controller and self.controller.draft is not None:
            self.controller.SetValue(field, int(not self.controller.draft[field]))

    # ---------------------------------------------------------------- controller callbacks
    def Sync(self):
        draft = self.controller.draft
        offsets = [0] * len(self.panes)
        for pane, field, row, height in self.rows:
            if design.Supports(draft[0], field, draft):
                row.SetPosition(0, offsets[pane])
                row.Show()
                offsets[pane] += height
            else:
                row.Hide()
        for field, (_, row, slider, text) in self.sliders.items():
            low, high = design.Ranges(draft[0])[field]
            slider.SetSliderPos(appearance.PercentToSlider(draft[field], low, high))
            text.SetText(design.DisplayValue(field, draft[field]))
        for field, name in ((design.BODY_ENABLED, 'BodyToggle'), (design.RING_ENABLED, 'RingToggle')):
            self.widgets[name].SetOn(bool(draft[field]))
        rgb = draft[design.PRIMARY]
        self.widgets['ColorValue'].SetText(u'%s | #%06X' % (ColorName(rgb), rgb) if rgb == design.GOLD else ColorName(rgb))
        for index, value in enumerate(COLORS):
            swatch = self.widgets['Color%d' % index]
            swatch.selected = value == rgb
            swatch.paint()
        for name, (field, segment) in self.choices.items():
            segment.SetValue(draft[field])
        self.widgets['MotionHint'].SetText(Tr('100 % = výchozí tempo efektu.', '100 % = the default tempo.')
                                           if design.Supports(draft[0], design.TEMPO, draft)
                                           else Tr('Tento obal má vlastní původní pohyb.', 'This body has its own motion.'))
        undo = self.widgets['UndoButton']
        undo.Show() if self.controller.undoReset is not None else undo.Hide()
        self._RefreshCatalogue()
        self.SyncModel()
        self.RefreshStatus()

    def SyncModel(self):
        if not self.controller:
            return
        self.models.SetValue(self.controller.previewVnum)
        if self.controller.draft is not None:
            import nonplayer
            vnum = self.controller.previewVnum
            self.view.SetTitle(RecordName(self.controller.draft),
                               nonplayer.GetMonsterName(vnum) or u'Meteor %d' % vnum)

    def RefreshStatus(self):
        c = self.controller
        if not c or c.draft is None:
            return
        changed = (c.draft[0] != c.original[0] or c.draftNearbyFill != c.originalNearbyFill or
                   any(tuple(value) != c.originalProfiles[key] for key, value in c.profiles.items()))
        self.SetStatus(Tr(u'Neuložené změny | Uložit potvrdí celý rozepsaný vzhled.', 'Unsaved changes.') if changed
                       else Tr(u'Vyber styl. Náhled reaguje ihned, nastavení potvrdíš tlačítkem Uložit.',
                               'Pick a style. The preview reacts at once; Save confirms it.'))

    def SetStatus(self, text):
        self.status_text = text
        self.widgets['Status'].SetText(text)

    # ---------------------------------------------------------------- actions
    def _SetModel(self, vnum):
        self.controller.SetModel(vnum)

    def _ResetCamera(self):
        self.controller.ResetCamera()

    def _Ok(self):
        if self.controller.Apply():
            self.Close()

    def Open(self, draft=None, nearby=None):
        self.backend = design.AdaptBackend(self.backend)
        self.controller.backend = self.backend
        self.controller.viewScale = StoneScale()
        if ScreenSize() != self.screen:
            self._Rebuild()
        if not self.controller.BeginSession(draft, nearby):
            return
        self._PlaceOnScreen()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Close(self):
        if self.search is not None:
            self.search.KillFocus()
        if self.controller:
            self.controller.Discard()
        self.KillFocus()
        self.Hide()
        if self.closeEvent:
            self.closeEvent()

    # ---------------------------------------------------------------- screen fit
    def OnChangeResolution(self):
        """The game window changed size: rebuild the layout for it (once) and put the editor back on screen."""
        if ScreenSize() != self.screen:
            self._Rebuild()
        self._PlaceOnScreen()

    def _PlaceOnScreen(self):
        """Centred on the screen, never past an edge (the window is never larger than the screen minus margins)."""
        sw, sh = self.screen or ScreenSize()
        x = max(0, min((sw - self.W) // 2, sw - self.W))
        y = max(0, min((sh - self.H) // 2, sh - self.H))
        self.SetPosition(x, y)
        update = getattr(self, 'UpdateRect', None)
        if update:
            update()

    def _Rebuild(self):
        """New layout for the current screen: the same draft, tab, catalogue layer and search, a fresh preview target."""
        c = self.controller
        pane, layer = self.activePane, self.libraryLayer
        if self.search is not None:
            self.searches[layer] = self.search.GetText()
            self.search.KillFocus()
            self.search.owner = None
        if c is not None:
            if c.draft is not None:
                c._SampleSliders()
            c._StopPreviewDrag()
            c._RemovePreview()
        if self.view is not None:
            self.view.Destroy()
        for widget in self.children:
            if hasattr(widget, 'Hide'):
                widget.Hide()
        self.children, self.panes, self.rows = [], [], []
        self.widgets, self.sliders, self.choices = {}, {}, {}
        self.libraryRows, self.hint_buttons = [], []
        self.search, self.view = None, None
        self.kit = uikit.Kit(uikit.Profile(), uikit.FontSet())
        self._Build()
        if c is not None:
            c.view = self.view
            self.view.on_silhouette = c._PlaceSilhouette
            self.view.on_camera = c.ResetCamera
            c._BindPreview()
        self.libraryLayer = layer
        self.search.SetText(self.searches[layer])
        self._SetPane(pane, False)
        if c is not None and c.draft is not None:
            c._SyncUi()
            c._CreatePreview()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        if not self.controller or not self.IsShow():
            return
        if ScreenSize() != self.screen:   # two int reads a frame; the rebuild runs once per resolution change
            self.OnChangeResolution()
        # Existing camera gestures keep working outside the viewport during a drag.
        self.controller.OnUpdate()
        hovered = next((hint for button, hint in self.hint_buttons if button.hovered and button.IsShow()), None)
        self.widgets['Status'].SetText(hovered or self.status_text)

    def Destroy(self):
        self.Close()
        if self.controller:
            self.controller.Destroy()
        self.controller, self.closeEvent = None, None
        if self.search is not None:
            self.search.owner = None
        if self.view is not None:
            self.view.Destroy()
        for widget in self.children:
            if hasattr(widget, 'Hide'):
                widget.Hide()
        self.children, self.rows, self.panes = [], [], []
        self.widgets, self.sliders, self.libraryRows, self.choices = {}, {}, [], {}
