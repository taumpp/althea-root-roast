# -*- coding: utf-8 -*-
"""Settings window v5: "Obnovit stránku" and "Obnovit všechna nastavení" (2026-10-05).

Obnovit stránku (footer) asks first and names what returns ("Vrátit 9 voleb stránky Svět a počasí na výchozí
hodnoty?"); a page with nothing to reset (Souboje a soukromí: the server owns PvP and request blocks) disables the
button and its tooltip says why. A custom page (key bindings) resets through its view without a second question,
the A7-look pages (panels, queue) keep their A7 reset. Obnovit všechna nastavení (Rychlé nastavení › Obnovení) is
the destructive one: a wide confirmation lists what returns and what stays (keybindings and the panel layout have
their own reset, the stone queue look its editor, PvP and blocks belong to the server).
"""
import settingsc9pages as c9pages
import settingschat
import settingsmodel
import uikit
import uisettings as a7
from settingslocale import Text as Tr
from uisettingsc9rows import Plural

Base = a7.GameOptionWindow


class C9Reset(object):
    """Mixin of the settings window: reset of the page and of everything, both with confirmation."""

    def _C9Confirm(self, wide=False):
        attr = 'c9_confirm_wide' if wide else 'c9_confirm'
        dialog = getattr(self, attr, None)
        if dialog is None:
            dialog = uikit.Confirm(self.kit, Tr('Potvrzení', 'Confirm'), Tr('Obnovit', 'Reset'), Tr('Zrušit', 'Cancel'),
                                   wide=wide)
            dialog.owner = self
            setattr(self, attr, dialog)
        return dialog

    def _C9ResetKeys(self):
        """Keys of the shown page that "Obnovit stránku" returns (the A7 ResetPage rules: no server-owned PvP /
        block / family name, the refresh rate only in full screen, chat options only with the live chat)."""
        keys = []
        for control in self.controls:
            key = control['key']
            if not key or key in keys or key in ('block', 'pvp', 'family_names', 'look_old', 'reset_all'):
                continue
            if key == 'refresh_hz':
                import settingsbackend
                info = settingsbackend.refresh_rate_info()
                if info is None or info[2]:
                    continue
            if settingschat.owns(key) and not self.c9_chat.available(key):
                continue
            keys.append(key)
        return keys

    def _C9ResetText(self):
        label = c9pages.PAGES[self.c9_page]['label']
        view = self.c9_view_active
        if view is not None and hasattr(view, 'ResetText'):
            return view.ResetText()
        if self.legacy_mode or view is not None:
            return Tr('Vrátit nastavení stránky „%s“ na výchozí hodnoty?',
                      'Reset the settings of the page "%s" to their defaults?') % label
        count = len(self._C9ResetKeys())
        if not count:
            return ''
        return Tr('Vrátit %s stránky %s na výchozí hodnoty?', 'Reset %s of the page %s to the defaults?') % (
            Plural(count, 'volba'), label)

    def _C9ShowResetInfo(self):
        """Hover of "Obnovit stránku": a kit tooltip above the button says what returns, or why nothing does."""
        text = self._C9ResetText() if self.session else ''
        if not text:
            text = Tr('Na této stránce není co obnovit: režim boje a blokování žádostí řídí server.',
                      'Nothing to reset here: the server owns the combat mode and the request blocks.')
        self._C9ShowInfo(None)
        self._C9ShowTip(self.reset_button, Tr('Obnovit stránku', 'Reset page'), text, side='above')

    def _C9AskReset(self):
        if not self.session or self.searching:
            return
        view = self.c9_view_active
        if view is not None and hasattr(view, 'AskReset'):
            view.AskReset()  # the page has its own confirmation (it names what returns itself)
            return
        text = self._C9ResetText()
        if not text:
            return
        self._C9Confirm().Open(text, self.ResetPage)

    def ResetPage(self):
        if not self.session or self.searching:
            return
        view = self.c9_view_active
        if view is not None and hasattr(view, 'RestoreDefaults'):
            view.RestoreDefaults()
            return
        if self.legacy_mode:
            Base.ResetPage(self)
            return
        chat_keys = [c['key'] for c in self.controls if settingschat.owns(c['key'])]
        if self.c9_page == 'look':
            if self.value('channel_bar_style') != 'stepper':
                self.change('channel_bar_style', 'stepper')
            if self.c9_icons:
                self._C9SetIcons(False)
                return
        controls = self.controls
        self.controls = [c for c in controls if c['key'] and not settingschat.owns(c['key'])
                         and c['key'] not in ('row_icons', 'look_old', 'reset_all', 'channel_bar_style')]
        try:
            Base.ResetPage(self)
        finally:
            self.controls = controls
        self.c9_chat.reset(chat_keys)
        # A reset of single world controls that brings back the High preset values is the High preset again.
        values = self.session.values
        if self.session.quality_preset == 4 and all(values[key] == settingsmodel.QUALITY_PRESETS[2][key]
                                                    for key in settingsmodel.QUALITY_KEYS):
            self.session.select_quality(2)
            self.Apply()
        self._Refresh()

    # Everything "Obnovit všechna nastavení" returns and what it leaves (the confirmation lists both).
    RESET_ALL_LIST = (Tr('Grafika: kvalita Vysoká, barvy Althea, stíny a efekty, doprovody, FPS, počasí a obloha',
                         'Graphics: quality High, colors Althea, shadows and effects, companions, FPS, weather, sky'),
                      Tr('Ovládání: zorné pole a oddálení kamery', 'Controls: field of view and camera distance'),
                      Tr('Rozhraní: písmo, chat, jména a ukazatele, kořist a inventář, upozornění',
                         'Interface: font, chat, names and indicators, loot and inventory, notifications'),
                      Tr('Hra: automatický sběr a velikost kamenů', 'Game: automatic pickup and stone size'),
                      Tr('Zvuk: hlasitost a hudba', 'Sound: volume and music'))
    RESET_ALL_KEEP = Tr('Nezmění se: klávesové zkratky a rozložení Panelů tlačítek (mají vlastní „Obnovit stránku“), '
                        'vzhled fronty kamenů (editor), vzhled tohoto okna a režim boje a blokování žádostí '
                        '(řídí server).', 'Unchanged: keybindings and the button panel layout (their own "Reset '
                        'page"), the stone queue look (editor), the look of this window, the combat mode and request '
                        'blocks (server).')

    def _C9AskResetAll(self):
        if not self.session:
            return
        self._C9Confirm(wide=True).Open(Tr('Vrátit všechna nastavení na výchozí hodnoty?',
                                           'Reset all settings to their defaults?'), self.ResetAll,
                                        bullets=self.RESET_ALL_LIST, note=self.RESET_ALL_KEEP,
                                        accept_text=Tr('Obnovit vše', 'Reset all'))

    def ResetAll(self):
        """Every session option back to its default (the A7 defaults, quality High, colors Althea, default track)
        and the chat options; keybindings, panel layout, queue look and the server-owned PvP / blocks stay."""
        if not self.session or not self.Apply():
            return
        import musicInfo
        import settingsbackend
        session = self.session
        # Not here: server-owned PvP / blocks / family name, the track (below), quality keys (the preset) and the
        # shop visibility that no settings page shows (it is toggled in game).
        skip = set(('block', 'pvp', 'family_names', 'track', 'shop')) | set(settingsmodel.QUALITY_KEYS)
        info = settingsbackend.refresh_rate_info()
        if info is None or info[2]:
            skip.add('refresh_hz')
        for key in settingsmodel.BOUNDS:
            if key not in skip:
                session.set(key, settingsmodel.DEFAULTS[key])
        for key in ('exposure', 'sharpness'):
            session.set(key, settingsmodel.COLOR_DEFAULTS[key])
        session.select_colors(1)
        session.select_quality(2)
        session.set('track', musicInfo.METIN2THEMA)
        self.custom_expanded = False
        self.Apply()
        self.c9_chat.reset(settingschat.KEYS)
        self._Render()
