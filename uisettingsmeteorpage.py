# -*- coding: utf-8 -*-
"""Settings v5 page "Fronta kamenů" (2026-10-05): stone size, big live preview, "Upravit vzhled…".

Replaces the old-look queue page inside the new settings window (owner: "metin tam nejde vidět", red bars,
wooden room). Layout in the content column of the shell, any width 300..800 px, never scrolls:

  Velikost kamenů ve světě  (◆ Výchozí: 100 %)  [kit slider]  150 %   <- row like every v5 row (no icon; the
                                                                      default note only while the size is changed)
  Vzhled označení ─────────────────────────────            <- v5 kit Section, no red bar
  +------------------------------------------------------+
  |  big live preview (uimeteorpreview), postava switch, |
  |  "Výchozí pohled" while rotated / panned / zoomed     |
  +------------------------------------------------------+
  Pulzující obal · Klasický vír                [Upravit vzhled…]   <- secondary button (2026-10-06)
  Barva: Zlatá · ...

The page follows the A7 queue_page protocol the settings window already calls (Build / Detach / Destroy /
OnUpdate / Scrolled / Anchor), registers the slider as a 'c9_slider' control (reset of the page and the
central refresh keep working) and watches the session value: dragging the slider, Obnovit stránku or any
other change of stone_size resizes the stone in the preview live. Viewing never writes a queue profile.
Hook for the v5 shell: uisettingsc9.CUSTOM_VIEWS['queue'] = ('uisettingsmeteorpage',
'MeteorQueueView') and settingsc9pages 'queue': custom='queue', a7='queue'.
"""
import ui

import metinqueuelibrary as design
import uikit
import uikittokens as T
from settingslocale import Text as Tr
from uimeteorpreview import MeteorPreviewController, MeteorPreviewView, RecordName, ColorName, StoneScale

KEY = 'stone_size'


PRIMARY = 'primary'  # the one primary action of a screen (v6 family, 2026-10-06): the editor's Uložit


class MeteorQueuePage(object):
    def __init__(self, host, backend=None):
        self.host = host
        self.backend_source = backend
        self.backend = None
        self.controller = None
        self.view = None
        self.active = False
        self.activePane = 0
        self.syncedPreset = None
        self.widgets, self.sliders = {}, {}
        self.items = []
        self.shown_value = None
        self.preview_visible = None
        self.preview_y = 0
        self.height = 0

    # ---------------------------------------------------------------- build
    def _track(self, widget):
        self.items.append(widget)
        page_widgets = getattr(self.host, 'page_widgets', None)
        if page_widgets is not None:
            page_widgets.append(widget)
        return widget

    def Build(self, parent=None, width=None, height=None):
        """Lays the page into parent (the shell's scrolled content). Returns the content height."""
        self.Detach()
        host = self.host
        k = host.kit
        parent = parent if parent is not None else host.content
        width = int(width or getattr(host, 'c9_view_w', 0) or host.content.GetWidth())
        view_h = int(height or host.VIEW_HEIGHT)
        self.parent, self.width = parent, width
        self.backend = design.AdaptBackend(self.backend_source)
        self.active = True
        pitch = k.p('pitch')
        compact = width < 440

        # Stone size row: label, kit slider, value (the c9 row rhythm, no icon).
        row = dict(type='control', kind='slider', key=KEY, label=Tr('Velikost kamenů ve světě', 'World stone size'),
                   y=0, h=pitch, hints=[],
                   hint_text=Tr('Velikost meteorů ve světě (100-200 %). Náhled níže ukazuje změnu hned.',
                                'Size of the stones in the world (100–200 %). The preview below shows it at once.'))
        band = self._track(uikit.Band(parent, 0, 0, width, pitch, 'hover'))
        band.Hide()
        hit = self._track(uikit.HitArea(parent, 0, 0, width, pitch))
        row['band'], row['hit'] = band, hit
        show_info = getattr(host, '_C9ShowInfo', None)
        if show_info:
            hit.SetHoverEvent(lambda: show_info(row))
        label = self._track(uikit.Text(parent, row['label'], 0, pitch // 2, k.font('M'), T.INK))
        row['label_line'] = label
        track_w = 210 if k.prof == '1080' else 150
        if compact:
            track_w = max(110, min(track_w, width - uikit.TextWidth(label) - 90))
        value_w = 56
        slider = uikit.Slider(parent, k, track_w)
        x0 = width - value_w - track_w
        slider.SetPosition(x0 - slider.knob_w // 2, (pitch - slider.h) // 2)
        slider.SetEvent(lambda: self._SliderMoved(slider))
        if show_info:
            slider.SetHoverEvent(lambda: show_info(row))
        if hasattr(host, 'OnMouseWheel'):
            slider.SetWheelEvent(host.OnMouseWheel)
            hit.SetWheelEvent(host.OnMouseWheel)
        self._track(slider)
        value = self._track(uikit.Text(parent, '', x0 + track_w + 14, pitch // 2, k.font('M'), T.INK_DIM))
        # v5 rows: "Výchozí: 100 %" with the gold diamond only while the size differs from the default (the shell's
        # marker, refreshed by the shell with every change; v5 fix 2026-10-05 - it used to show always, small).
        marker = getattr(host, 'C9DefaultMarker', None)
        right = x0 - slider.knob_w // 2 - 14
        if marker is not None:
            marker(parent, row, right, pitch // 2, uikit.TextWidth(label) + 24, track=self._track)
        else:  # older shell (c9 v4): the always-shown grey note
            default = self._track(uikit.Text(parent, Tr('Výchozí: 100 %', 'Default: 100 %'), right, pitch // 2,
                                             k.font('S'), T.MUTED, align='right'))
            if right - uikit.TextWidth(default) < uikit.TextWidth(label) + 24:
                default.Hide()
        self._track(uikit.HLine(parent, 0, pitch - 1, width, T.ROW_LINE))
        record = dict(kind='c9_slider', key=KEY, widget=slider, label=label, y=0, row=row, text=value,
                      bounds=(0., 1.))
        row['control'] = record
        controls = getattr(host, 'controls', None)
        if controls is not None:
            controls.append(record)
        rows = getattr(host, 'c9_rows', None)
        if rows is not None:
            rows.append(row)
        self.widgets.update(Slider=slider, SliderValue=value, SliderRow=row)

        # Section heading in the section look of the settings pages (uikitsections.SECTION_STYLE), no red bar.
        import uikitsections
        y = pitch + 14
        style = uikitsections.Style(k)
        section = style.Open(parent, 0, y, width, self._track)
        y += style.Heading(parent, 0, y, width, Tr('Vzhled označení', 'Marker appearance'), self._track) + \
            (4 if k.prof == '1080' else 6)
        y += style.Close(section, y - (4 if k.prof == '1080' else 6))
        # The bottom block: record name + colour (two lines) beside the button.
        button_h = uikit.ButtonHeight(k)
        bottom = max(button_h, k.cell('M') + k.cell('S') + 6) + 14
        preview_h = max(180, min(int(width * 0.85), view_h - y - 12 - bottom - 10))  # the shell adds 8 px
        self.preview_y = y
        self.view = MeteorPreviewView(parent, k, 0, y, width, preview_h, track=self._track, compact=compact,
                                      camera=True)
        if hasattr(host, 'OnMouseWheel'):
            self.view.toggle.SetWheelEvent(host.OnMouseWheel)
        self.view.SetTitle('')
        self.widgets.update(Preview=self.view.target, PreviewInput=self.view.input)
        y += preview_h + 12
        self.widgets['Record'] = self._track(uikit.Text(parent, '', 0, y, k.font('M'), T.INK, valign='top'))
        swatch = self._track(ui.Bar())
        swatch.SetParent(parent)
        swatch.AddFlag('not_pick')
        sw = k.cell('S') - 3
        swatch.SetSize(sw, sw)
        swatch.SetPosition(0, y + k.cell('M') + 8)
        swatch.Show()
        self.widgets['Swatch'] = swatch
        self.widgets['Detail'] = self._track(uikit.Text(parent, '', sw + 8, y + k.cell('M') + 5, k.font('S'),
                                                        T.MUTED, valign='top'))
        bw = 220 if k.prof == '1080' else 170
        # Secondary (2026-10-06): not the main action of the page - Zavřít of the window is.
        edit = uikit.Button(parent, k, width - bw, y + (bottom - 14 - button_h) // 2, bw,
                            Tr('Upravit vzhled...', 'Edit appearance…'), role='secondary', event=self.OpenEditor)
        edit.FitWidth(bw)
        edit.SetPosition(width - edit.w, y + (bottom - 14 - button_h) // 2)
        if hasattr(host, 'OnMouseWheel'):
            edit.SetWheelEvent(host.OnMouseWheel)
        self._track(edit)
        self.widgets['EditButton'] = edit
        limit = width - edit.w - 16
        self.widgets['Record'].SetLimitWidth(limit)
        self.widgets['Detail'].SetLimitWidth(max(40, limit - sw - 8))
        self.height = y + bottom

        self.shown_value = None
        self.controller = MeteorPreviewController(self, self.backend, self.view)
        self.controller.viewScale = 1.0 + self._Value()
        self.controller.BeginSession()
        self._SyncSize()
        self.SyncModel()
        self.preview_visible = None
        return self.height

    # ---------------------------------------------------------------- stone size
    def _Value(self):
        try:
            return max(0.0, min(1.0, float(self.host.value(KEY))))
        except Exception:
            return max(0.0, StoneScale() - 1.0)

    def _SliderMoved(self, slider):
        if not self.active:
            return
        self.host.change(KEY, max(0., min(1., slider.GetSliderPos())), continuous=True)
        self._SyncSize()

    def _SyncSize(self):
        value = self._Value()
        if value == self.shown_value:
            return
        self.shown_value = value
        slider, text = self.widgets.get('Slider'), self.widgets.get('SliderValue')
        if slider and abs(slider.GetSliderPos() - value) > 1e-4:
            slider.SetSliderPos(value)
        if text:
            fmt = getattr(self.host, '_Format', None)
            text.SetText(fmt(KEY, value) if fmt else '%d %%' % round((1 + value) * 100))
        if self.controller:
            self.controller.SetViewScale(1.0 + value)

    # ---------------------------------------------------------------- controller callbacks (read only)
    def Sync(self):
        # No editable appearance fields: viewing settings must never save a profile.
        if not self.active or not self.controller or self.controller.draft is None:
            return
        draft = self.controller.draft
        self.widgets['Record'].SetText(RecordName(draft))
        rgb = draft[design.PRIMARY]
        self.widgets['Swatch'].SetColor(uikit.GenerateColor(rgb))
        self.widgets['Detail'].SetText(Tr('Barva: %s | upravíš v editoru vzhledu', 'Colour: %s · change it in the editor')
                                       % ColorName(rgb))

    def SyncModel(self):
        if self.active and self.controller and self.view:
            import nonplayer
            vnum = self.controller.previewVnum
            self.view.SetTitle('', nonplayer.GetMonsterName(vnum) or Tr('Meteor %d', 'Stone %d') % vnum)

    def RefreshStatus(self):
        self.SetStatus('')

    def SetStatus(self, text):
        if self.active and self.view:
            self.view.SetStatus(text if text and self.controller and self.controller.previewIndex is None else '')

    def Scrolled(self, offset, height):
        if not self.active or not self.controller or not self.view:
            return
        visible = offset < self.preview_y + self.view.h and offset + height > self.preview_y
        if self.controller.previewIndex is not None and visible != self.preview_visible:
            import WikiRenderTarget
            WikiRenderTarget.SetVisibility(self.controller.previewIndex, visible)
            self.preview_visible = visible
        if not visible:
            self.controller._StopPreviewDrag()

    def Anchor(self, key):
        """Scroll offset of a searched key; the stone size row is marked like a highlighted c9 row."""
        row = self.widgets.get('SliderRow')
        if key == KEY and row:
            row['label_line'].SetPackedFontColor(T.GOLD_HI)
            row['band'].Show()
            row['marked'] = True
        return 0 if key == KEY else max(0, self.preview_y - 12)

    def OnUpdate(self):
        if self.active and self.controller:
            self._SyncSize()
            self.controller.OnUpdate()

    # ---------------------------------------------------------------- editor
    def OpenEditor(self):
        """Opens the v5 editor. The page releases its native preview (one library draft at a time) only once the
        editor exists, and comes back whenever the editor does not show: owner play test 2026-10-05 - the editor
        raised while building, after the page had already detached itself, so the page stayed empty."""
        host = self.host
        editor = getattr(host, 'editor', None)
        if editor is not None and editor.IsShow():
            editor.SetTop()
            return
        if hasattr(host, 'Apply') and not host.Apply():
            return
        import uimeteoreditor
        if not isinstance(editor, uimeteoreditor.MeteorDesignEditor):
            if editor is not None:
                editor.Destroy()
            host.editor = None
            try:
                editor = uimeteoreditor.MeteorDesignEditor(onClose=getattr(host, '_QueueEditorClosed', None))
            except Exception:
                self._EditorFailed()
                return
            host.editor = editor
        self.Detach()
        try:
            editor.Open()
        except Exception:
            self._EditorFailed()
        if not editor.IsShow():  # BeginSession failed (the profile could not be read): the page comes back
            self._Rebuild()

    def _EditorFailed(self):
        import dbg
        import traceback
        dbg.TraceError('[MeteorQueuePage] editor: %s' % traceback.format_exc())
        self._Rebuild()
        self.SetStatus(Tr('Editor vzhledu se nepodařilo otevřít.', 'The appearance editor could not be opened.'))

    def _Rebuild(self):
        """The page again after a failed editor (the shell re-renders the page; the old A7 shell too)."""
        host = self.host
        if host is None or self.active:
            return
        render = getattr(host, '_Render', None)
        if render is not None and getattr(host, 'page', None) == 'queue':
            render()

    # ---------------------------------------------------------------- lifecycle
    def Detach(self):
        self.active = False
        if self.controller:
            self.controller.Destroy()
            self.controller = None
        if self.view:
            self.view.Destroy()
            self.view = None
        for widget in self.items:
            widget.Hide()
        self.items = []
        self.widgets = {}
        self.shown_value = None

    def Reset(self):
        pass  # the page's only setting is stone_size: the shell's Obnovit stránku resets it as a c9 control

    def Apply(self):
        return True

    def Destroy(self):
        self.Detach()
        self.host = None


class MeteorQueueView(object):
    """Custom view of the v5 settings shell (uisettingsc9.CUSTOM_VIEWS):

        CUSTOM_VIEWS['queue'] = ('uisettingsmeteorpage', 'MeteorQueueView')
        settingsc9pages 'queue': custom='queue', a7='queue'   (instead of legacy='queue')

    Build(width) lays MeteorQueuePage into window.content as window.queue_page, so the A7 window keeps driving it
    (OnUpdate, Detach on page change, Destroy on close). Obnovit stránku returns only the stone size; the marker
    look has its own reset in the editor."""

    def __init__(self, window):
        self.window = window

    def _Page(self):
        window = self.window
        if not isinstance(window.queue_page, MeteorQueuePage):
            if window.queue_page:
                window.queue_page.Destroy()
            window.queue_page = MeteorQueuePage(window)
        return window.queue_page

    def Build(self, width):
        window = self.window
        view = getattr(window, 'c9_current_view', None) or window.c9_view
        return self._Page().Build(window.content, width, view['h'])

    def Clear(self):
        page = getattr(self.window, 'queue_page', None)
        if isinstance(page, MeteorQueuePage):
            page.Detach()

    def OnUpdate(self):
        pass  # the A7 window already calls queue_page.OnUpdate() on this page (twice would double the drag)

    def ResetText(self):
        return Tr('Vrátit velikost kamenů ve světě na 100 %? Vzhled označení se nezmění - ten vrací editor '
                  '(Výchozí sestava).', 'Reset the world stone size to 100 %? The marker look stays – the editor '
                  'resets it (Default set).')

    def RestoreDefaults(self):
        import settingsmodel
        self.window.change(KEY, settingsmodel.DEFAULTS[KEY])

    def SearchIndex(self):
        return []  # the A7 index already lists stone_size and the marker look under 'queue'

    def Destroy(self):
        self.Clear()
        self.window = None
