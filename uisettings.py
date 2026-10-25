"""Settings A7, composed from the existing Crimson frame and controls."""
import app
import background
import dbg
import fontconfig
import grp
import ui
from uicrimsonember import SettingsScrollBar
import uicrimsoncontrols as crimson
import settingsbackend
import settingsmodel
import settingspages as pages
import uidamagesettings
from settingslocale import Text as T

IMG = 'd:/ymir work/ui/game/crimson_ember/gameoption/'
INK = (.88, .85, .78)
DIM = (.68, .64, .58)
GOLD = (.84, .71, .47)
blockMode = 0


class Search(ui.EditLine):
    def __init__(self, owner):
        ui.EditLine.__init__(self)
        self.owner = owner
        self.SetReturnEvent(owner.SearchOptions)
        self.SetEscapeEvent(owner.OnPressEscapeKey)

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        self.owner.SearchOptions()


def MenuMusicChoices():
    return [('shuffle', T('Náhodně (střídá skladby)','Shuffle'))] + list(settingsmodel.MENU_MUSIC_TRACKS)


def AltheaTrackChoices():
    """Our tracks (bgm/bgm/althea_*.flac, seamless loops) for 'Hudební doprovod -> Skladba', by their
    names, the ones present in BGM/ only; (file, name)."""
    try:
        present = set(name.lower() for name in app.GetFileList('BGM/*.flac'))
    except Exception:
        present = set()
    return [('althea_%s.flac' % key, name) for key, name in settingsmodel.MENU_MUSIC_TRACKS
            if ('althea_%s.flac' % key) in present]


class PageIndex:
    """Run the same page descriptions without widgets to index actual controls."""
    def __init__(self):
        self.entries = []
        self.page = None
        self.seen = set()

    def value(self, key):
        return settingsmodel.DEFAULTS.get(key, 0)

    def _record(self, key, label, *args, **kwargs):
        if not label and key in ('quality_preset','color_preset'):
            label = T('Kvalita světa','World quality') if key=='quality_preset' else T('Barevný profil','Color profile')
        if label and (self.page, key, label) not in self.seen:
            self.entries.append((self.page, key, label))
            self.seen.add((self.page, key, label))

    slider = toggle = radios = check = number = action = link = _record

    def queue_inline(self):
        for key, label in (('stone_size', T('Velikost kamenů ve světě','World stone size')),
                           ('queue_color', T('Barva označení','Marker color')),
                           ('queue_body', T('Obal','Body')), ('queue_ring', T('Prstenec','Ring'))):
            self._record(key, label)

    def custom_colors(self):
        for key,label in pages.CUSTOM_COLORS:
            self._record(key,label)

    def frame_limit(self,y):
        self._record('fps', T('Limit snímků (FPS)', 'Frame limit (FPS)'))

    def refresh_rate(self,y):
        self._record('refresh_hz', T('Obnovovací frekvence (Hz)', 'Refresh rate (Hz)'))

    def ui_scale(self,y):
        if settingsbackend.ui_scale_info() is None:
            return 0
        self._record('ui_scale', T('Velikost rozhran\u00ed', 'Interface scale'))
        return 118

    def tree_shadow(self,y):
        self._record('tree_shadow', pages.TREE_SHADOW_LABEL)

    def background_fps(self,y):
        if settingsbackend.background_fps_supported():
            self._record('background_fps', pages.BACKGROUND_FPS_LABEL)

    def sky_picker(self,y):
        self._record('sky',T('Obloha','Sky'))

    def damage_controls(self,y):
        for key,label in (('damage_font',T('Písmo zásahů','Damage font')),
                          ('damage_normal_color',T('Barva normálních zásahů','Normal hit color')),
                          ('damage_critical_color',T('Barva kritických zásahů','Critical hit color')),
                          ('damage_outline',T('Černý obrys číslic','Black number outline')),
                          ('damage_height',T('Výška zásahů','Hit height')),
                          ('damage_grouping',T('Oddělování tisíců','Thousands grouping'))):
            self._record(key,label)

    def music_inline(self, y):
        self._record('track', T('Hudební doprovod','Background music'))

    def menu_music(self, y):
        self._record('menu_music', T('Hudba v menu','Menu music'))

    def button_panels_inline(self):
        for key, label in (('minimap_panel', T('Tlačítka u minimapy','Minimap buttons')),
                           ('minimap_panel_order', T('Pořadí tlačítek','Button order')),
                           ('minimap_panel_more', T('Menu Další','More menu')),
                           ('inventory_panel', T('Tlačítka u inventáře','Inventory buttons'))):
            self._record(key, label)

    def __getattr__(self, key):
        return lambda *args, **kwargs: None


def _button(parent, x, y, label, event, family='88x21'):
    button = ui.Button()
    button.SetParent(parent)
    button.SetPosition(x, y)
    crimson.ApplyVisuals(button, family)
    button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
    button.SetText(label)
    button.SetEvent(event)
    button.Show()
    return button


class GameOptionWindow(ui.BoardWithTitleBar):
    WIDTH, HEIGHT = 616, 600
    VIEW_TOP, VIEW_HEIGHT = 82, 456

    def __init__(self):
        # ui.Window.__init__ dispatches self.Hide() before returning here.
        # All state used by that callback must exist before the base constructor.
        self.session = None
        self.family_name_state = None
        self.permanent, self.page_widgets, self.controls = [], [], []
        self.popup_widgets, self.edit_lines = [], []
        self.popup = self.key_window = self.key_page = self.editor = self.music_dialog = None
        self.message_dialog = None
        self.damage_color_dialog = None
        self.queue_page = None
        self.panels_page = None
        self.save_deadline = None
        self.closing = False
        self.custom_widgets = []
        self.custom_expanded = False
        self.scroll_offsets = {}
        self.content_height = self.VIEW_HEIGHT
        self.scroll_syncing = False
        self.rendered_page = None
        self.searching = False
        self.children = dict(optionType=0, categoryType=0)
        self.page = 'game'
        self.search_offset = 0
        self.highlight = None
        ui.BoardWithTitleBar.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetTitleName(T('Nastavení','Settings'))
        self.SetCloseEvent(self.Hide)
        self.SetCenterPosition()
        self._BuildShell()
        index = PageIndex()
        for page in pages.PAGES:
            index.page = page
            index._record(page, pages.PAGES[page][2])
            pages.compose(index, page)
        self.search_index = index.entries
        self.backend = settingsbackend.GameBackend(lambda: blockMode)

    def _keep(self, widget, x, y, parent=None, permanent=False):
        widget.SetParent(parent if parent is not None else self if permanent else self.content)
        widget.SetPosition(int(x), int(y))
        (self.permanent if permanent else self.page_widgets).append(widget)
        if not permanent:
            widget.OnMouseWheel = self.OnMouseWheel
        widget.Show()
        return widget

    def text(self, label, x, y, small=False, bold=False, center=False, width=None, color=INK, permanent=False):
        line = self._keep(ui.TextLine(), x, y, permanent=permanent)
        role = fontconfig.ROLE_DENSE if small else fontconfig.ROLE_SECTION if bold else fontconfig.ROLE_BODY
        line.SetFontName(fontconfig.FontForRole(role))
        line.SetFontColor(*color)
        line.AddFlag('not_pick')
        if center:
            line.SetHorizontalAlignCenter()
        if width:
            line.SetLimitWidth(int(width))
        line.SetText(label)
        return line

    def _bar(self, x, y, w, h, color, permanent=False):
        bar = self._keep(ui.Bar(), x, y, permanent=permanent)
        bar.SetSize(w, h)
        bar.SetColor(grp.GenerateColor(*color))
        bar.AddFlag('not_pick')
        return bar

    def _BuildShell(self):
        self._bar(10,36,207,510,(.025,.02,.025,1),True)
        for x,y,w,h in ((10,36,207,1),(10,36,1,510),(217,36,1,510),(10,545,207,1),(19,550,581,1)):
            self._bar(x,y,w,h,(.25,.195,.17,1),True)
        bg=self._keep(ui.ImageBox(),14,43,permanent=True)
        bg.LoadImage(IMG+'search_bg.tga')
        self.search=self._keep(Search(self),22,47,permanent=True)
        self.search.SetSize(154,18)
        self.search.SetMax(40)
        self.search.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        self.search.SetInfoMessage(T('Hledat...','Search…'))
        button=self._keep(ui.Button(),183,46,permanent=True)
        for method, state in (('SetUpVisual',0),('SetOverVisual',1),('SetDownVisual',2)):
            getattr(button,method)(IMG+'search_btn_%d.tga'%state)
        button.SetEvent(self.SearchOptions)
        self.nav_buttons={}
        for group,stem,label,y in ((0,'first',T('Hra','Game'),76),(1,'middle',T('Obraz','Image'),313),(2,'end',T('Zvuk','Sound'),442)):
            button=self._keep(ui.RadioButton(),14,y,permanent=True)
            for method,state in (('SetUpVisual',0),('SetOverVisual',1),('SetDownVisual',2)):
                getattr(button,method)(IMG+'%s_title_%d.tga'%(stem,state))
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
            button.SetListText(label,58)
            button.SetEvent(lambda selected=group:self.SetOptionType(selected))
            self.nav_buttons[group]=button
        self.category_buttons={}
        # Seven Game pages; the Sound row ends at 507, above the ESC hint at 519.
        positions=(114,141,168,195,222,249,276,351,378,405,480)
        for page,y in zip(pages.NAV,positions):
            button=self._keep(ui.RadioButton(),14,y,permanent=True)
            for method,state in (('SetUpVisual',0),('SetOverVisual',1),('SetDownVisual',2)):
                getattr(button,method)(IMG+'category_%d.tga'%state)
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_CONTROL))
            button.SetListText(pages.PAGES[page][2],38)
            button.SetEvent(lambda selected=page:self.open_page(selected))
            self.category_buttons[page]=button
        self.text(T('ESC  Zavřít nastavení','ESC  Close settings'),22,519,small=True,color=DIM,permanent=True)
        self.reset_button=_button(self,23,562,T('Obnovit tuto stránku','Reset this page'),self.ResetPage,'199x27')
        self.close_button=_button(self,469,559,T('Zavřít','Close'),self.Hide,'137x31')
        self.permanent.extend((self.reset_button,self.close_button))
        self.heading = self.text('',230,43,bold=True,width=352,permanent=True)
        self.viewport = self._keep(ui.Window(),230,self.VIEW_TOP,permanent=True)
        self.viewport.SetSize(352,self.VIEW_HEIGHT)
        # One inherited scissor tree; child masks would detach nested positions.
        self.viewport.EnableScissorRect()
        self.viewport.OnMouseWheel = self.OnMouseWheel
        self.content = self._keep(ui.Window(),0,0,parent=self.viewport,permanent=True)
        self.content.SetSize(352,self.VIEW_HEIGHT)
        self.content.OnMouseWheel = self.OnMouseWheel
        self.scrollbar = self._keep(SettingsScrollBar(),592,self.VIEW_TOP,permanent=True)
        self.scrollbar.SetScrollBarSize(self.VIEW_HEIGHT)
        self.scrollbar.SetScrollEvent(self._OnScroll)
        self.scrollbar.OnMouseWheel = self.OnMouseWheel
        self.scrollbar.Hide()

    def Open(self):
        if not self.IsShow():
            self.session=settingsmodel.Session(self.backend)
            self.custom_expanded = self.session.color_preset == 4
            if self.key_page:
                self.key_page.BeginSession()
            self._Render()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Hide(self):
        if self.session and not self.closing and not self.Apply():
            return
        self.closing = True
        self._SaveScroll()
        self._ClosePopup()
        if self.panels_page:
            self.panels_page.Detach()
        if self.queue_page:
            self.queue_page.Destroy()
            self.queue_page = None
        if self.session:
            self.session.discard()
        if getattr(self,'search',None):
            self.search.KillFocus()
        for edit in self.edit_lines:
            edit.KillFocus()
        if self.key_page:
            self.key_page.Discard()
        if self.editor and self.editor.IsShow():
            self.editor.Close()
        if self.music_dialog and self.music_dialog.IsShow():
            self.music_dialog.Close()
        if self.damage_color_dialog:
            self.damage_color_dialog.Close()
        if self.message_dialog:
            self.message_dialog.Close()
        if getattr(self,'hWnd',None):
            self.KillFocus()
        ui.BoardWithTitleBar.Hide(self)
        self.closing = False

    def Destroy(self):
        self.Apply()
        self.closing = True
        self.Hide()
        if self.key_page:
            self.key_page.Destroy()
        if self.panels_page:
            self.panels_page.Destroy()
        if self.editor:
            self.editor.Destroy()
        if self.key_window:
            self.key_window.ClearDictionary()
        self.scrollbar.Destroy()
        self.search.owner=None
        self.nav_buttons,self.category_buttons={},{}
        self.reset_button=self.close_button=None
        self.session=None
        self.family_name_state=None
        self.key_page=self.key_window=self.editor=self.music_dialog=self.message_dialog=None
        if self.damage_color_dialog:
            self.damage_color_dialog.Close()
            self.damage_color_dialog.ClearDictionary()
        self.damage_color_dialog=None
        self.panels_page=None
        self.permanent,self.page_widgets,self.controls,self.edit_lines=[],[],[],[]
        self.children={}

    def OnPressEscapeKey(self):
        if self.popup:
            self._ClosePopup()
        else:
            self.Hide()
        return True

    def SetOptionType(self, option):
        self.open_page(('game','image','sound')[max(0,min(2,int(option)))])

    def SetCategoryTypeForOption(self, option, category):
        legacy = {0: ('game','queue','interface','notifications'),
                  1: ('image','world','image'), 2: ('sound',)}
        choices = legacy.get(option, ('game',))
        self.open_page(choices[max(0,min(len(choices)-1,int(category)))])

    def OnBlockMode(self, mode):
        global blockMode
        blockMode=int(mode)&127
        displayed = self.backend.confirm_block(blockMode) if hasattr(self,'backend') else blockMode
        if self.session and self.session.values['block']==self.session.before['values']['block']:
            self.session.values['block']=displayed
            self.session.before['values']['block']=displayed
            self._Refresh()

    def OnChangePKMode(self):
        import player
        if self.session:
            value=player.GetPKMode()
            self.session.values['pvp']=value
            self.session.before['values']['pvp']=value
            self._Refresh()

    def open_page(self, page):
        if page in pages.ALIASES:
            page, self.highlight = pages.ALIASES[page]
        if page not in pages.PAGES:
            return
        if self.session is None:
            self.session=settingsmodel.Session(self.backend)
        elif not self.Apply():
            return
        self._SaveScroll()
        self.page=page
        self.children['optionType'],self.children['categoryType']=pages.PAGES[page][:2]
        self.search.KillFocus()
        self._Render()

    def OpenPage(self, page):
        self.Open()
        self.open_page(page)

    def _ClearPage(self):
        if self.damage_color_dialog:
            self.damage_color_dialog.Close()
        if self.editor and self.editor.IsShow():
            self.closing = True
            try:
                self.editor.Close()
            finally:
                self.closing = False
        self._ClosePopup()
        if self.queue_page:
            self.queue_page.Detach()
        if self.panels_page:
            self.panels_page.Detach()
        self.scrollbar.Hide()
        for edit in self.edit_lines:
            edit.KillFocus()
        for widget in self.page_widgets:
            widget.Hide()
        if self.key_window:
            self.key_window.Hide()
        self.page_widgets,self.controls,self.edit_lines=[],[],[]
        self.custom_widgets=[]

    def _SaveScroll(self):
        if self.rendered_page and not self.searching and hasattr(self,'content'):
            self.scroll_offsets[self.rendered_page] = max(0,-self.content.GetLocalPosition()[1])

    def _Render(self):
        self._ClearPage()
        self.searching = False
        self.rendered_page = self.page
        group, category, title, _ = pages.PAGES[self.page]
        self.heading.SetText(title)
        self.content_height = pages.HEIGHTS[self.page]
        for index,button in self.nav_buttons.items():
            button.Down() if index==group else button.SetUp()
        for page,button in self.category_buttons.items():
            button.Down() if page==self.page else button.SetUp()
        pages.compose(self,self.page)
        self._Refresh()
        offset = self.scroll_offsets.get(self.page,0)
        if self.highlight:
            for record in self.controls:
                if record['key']==self.highlight:
                    if record.get('label'):
                        record['label'].SetFontColor(*GOLD)
                    offset = max(0,record.get('y',0)-12)
                    break
            if self.page=='queue' and self.queue_page:
                offset = self.queue_page.Anchor(self.highlight)
            self.highlight=None
        self._LayoutScroll(offset)

    def _LayoutScroll(self, offset=0):
        self.content_height = max(self.VIEW_HEIGHT,self.content_height)
        self.content.SetSize(352,self.content_height)
        overflow = self.content_height-self.VIEW_HEIGHT
        self.scroll_syncing = True
        try:
            self.scrollbar.SetMiddleBarSize(max(20.0/self.VIEW_HEIGHT,
                float(self.VIEW_HEIGHT)/self.content_height))
            self.scrollbar.SetScrollStep(min(1.,40./max(1,overflow)))
            offset = max(0,min(int(offset),overflow))
            self.scrollbar.SetPos(float(offset)/max(1,overflow))
            self.content.SetPosition(0,-offset)
            self.scrollbar.Show() if overflow else self.scrollbar.Hide()
        finally:
            self.scroll_syncing = False
        if self.queue_page and self.page=='queue' and not self.searching:
            self.queue_page.Scrolled(offset,self.VIEW_HEIGHT)

    def _OnScroll(self):
        if self.scroll_syncing:
            return
        offset = int(max(0,self.content_height-self.VIEW_HEIGHT)*self.scrollbar.GetPos())
        self.content.SetPosition(0,-offset)
        self._SaveScroll()
        if self.queue_page and self.page=='queue' and not self.searching:
            self.queue_page.Scrolled(offset,self.VIEW_HEIGHT)

    def value(self,key):
        if key in ('color_preset','quality_preset'):
            return getattr(self.session,key)
        if key in settingsmodel.COLOR_BOUNDS:
            return self.session.colors[key]
        if key == 'dps_meter':
            # one switch with the target form's chip: the live state, not this session's copy
            getter = getattr(settingsbackend,'dps_meter_enabled',None)
            if getter is not None:
                try:
                    return int(getter())
                except Exception:
                    pass
        return self.session.values[key]

    def change(self,key,value,continuous=False):
        if key == 'dps_meter' and callable(getattr(settingsbackend,'set_dps_meter',None)):
            # saved and applied at once (live: an open DPS section collapses); the session follows
            if self.Apply():
                value = settingsbackend.set_dps_meter(value)
                self.session.values[key] = value
                before = getattr(self.session,'before',None)
                if isinstance(before,dict) and isinstance(before.get('values'),dict):
                    before['values'][key] = value
                self._Refresh()
            return
        if key == 'family_names':
            if self.Apply():
                settingsbackend.request_family_names(value)
                self._Refresh()
            return
        if not continuous and not self.Apply():
            return
        previous = self.session.snapshot()
        if key=='color_preset':
            self.session.select_colors(value)
            self.custom_expanded = value == 4
        elif key=='quality_preset':
            self.session.select_quality(value)
        else:
            self.session.set(key,value)
        if self.session.snapshot() == previous:
            self._Refresh()
            return
        if continuous:
            try:
                self.backend.preview(self.session.snapshot(), previous)
            except (OSError,ValueError,TypeError,RuntimeError) as error:
                dbg.TraceError('[Settings A7] Preview: %s' % error)
            self.save_deadline = app.GetTime() + .3
        else:
            self.Apply()
        self._Refresh()

    def custom_colors(self):
        start = len(self.page_widgets)
        for index,(key,label) in enumerate(pages.CUSTOM_COLORS):
            self.slider(key,label,476+index*36,compact=True)
        self.custom_widgets = self.page_widgets[start:]

    def _RefreshCustomColors(self):
        if not self.custom_widgets:
            return
        # Never rebuild a dragged slider. Search can reveal custom controls
        # without changing the active color profile merely by navigating to it.
        visible = self.custom_expanded or self.highlight in dict(pages.CUSTOM_COLORS)
        self.custom_expanded = visible
        for widget in self.custom_widgets:
            widget.Show() if visible else widget.Hide()
        height = 650 if visible else self.VIEW_HEIGHT
        if self.content_height != height:
            self.content_height = height
            self._LayoutScroll(max(0,-self.content.GetLocalPosition()[1]))

    def damage_controls(self,y):
        uidamagesettings.build(self,y)

    def _Refresh(self):
        # A server acknowledgement owns this character's checkbox state.
        value = settingsbackend.family_names_value()
        self.family_name_state = (settingsbackend.family_names_supported(), value)
        self.session.values['family_names'] = value
        self.session.before['values']['family_names'] = value
        self._RefreshCustomColors()
        for control in self.controls:
            value=self.value(control['key'])
            if control['key']=='track' and not value:
                import musicInfo
                value=musicInfo.METIN2THEMA
            kind=control['kind']
            if kind.startswith('damage_'):
                uidamagesettings.refresh(control,self.session.values)
            elif kind=='check':
                checked=bool(value&control['mask']) if control.get('mask') else bool(value)
                name='selected' if checked else 'unselected'
                button=control['widget']
                button.SetUpVisual(IMG+'checkbox_'+name+'.tga')
                button.SetOverVisual(IMG+'checkbox_'+('selected' if checked else 'hover')+'.tga')
                button.SetDownVisual(IMG+'checkbox_selected.tga')
                button.SetSize(control['width'],21)
                if control['key'] == 'family_names':
                    button.Enable() if self.family_name_state[0] else button.Disable()
                if control.get('status'):
                    control['status'].SetText(T('Zapnuto','On') if checked else T('Vypnuto','Off'))
            elif kind=='fps_cycle':
                control['widget'].SetText('%d >'%value)
            elif kind=='ui_scale':
                control['widget'].SetText('%d %% >' % value)
                self._RefreshUIScaleStatus(control, settingsbackend.ui_scale_info())
            elif kind=='tree_shadow':
                button=control['widget']
                if settingsbackend.tree_shadow_supported():
                    button.Enable()
                    button.SetText(('%d m >'%value) if value else T('Bez omezení >','Unlimited >'))
                    button.SetToolTipText(T('Stromy dál od postavy nevrhají stín. Menší dosah = více FPS v lese.',
                                            'Trees farther from your character cast no shadow. Shorter distance = more FPS in forests.'))
                else:
                    button.SetText('-')
                    button.Disable()
                    button.SetToolTipText(T('Dostupné po aktualizaci hry.','Available after updating the client.'))
            elif kind=='refresh':
                info=settingsbackend.refresh_rate_info()
                button=control['widget']
                if info is None:
                    button.SetText('-')
                    button.Disable()
                    control['status'].SetText(T('Dostupné po aktualizaci hry.','Available after updating the client.'))
                elif info[2]:
                    button.SetText('%d Hz'%info[1] if info[1] else '-')
                    button.Disable()
                    control['status'].SetText(T('V okně se používá nastavení Windows.','Windowed mode uses Windows display settings.'))
                else:
                    button.Enable()
                    button.SetText('%d Hz >'%value if value else T('Auto >','Auto >'))
                    control['status'].SetText(T('Teď %d Hz | změna po restartu.','Now %d Hz · change after restart.')%info[1])
            elif kind=='radio':
                for selected,button,width in control['widgets']:
                    button.SetUpVisual(IMG+'checkbox_'+('selected' if value==selected else 'unselected')+'.tga')
                    button.SetOverVisual(IMG+'checkbox_'+('selected' if value==selected else 'hover')+'.tga')
                    button.SetSize(width,23)
            elif kind=='sky':
                if control.get('current'):
                    control['value']=value
                    path='d:/ymir work/ui/game/graphic/jtx_skybox/sky%d.dds'%(value+1)
                    for method in ('SetUpVisual','SetOverVisual','SetDownVisual'):
                        getattr(control['widget'],method)(path)
                for border in control['borders']:
                    border.Show() if value==control['value'] else border.Hide()
            elif kind=='slider':
                low,high=control['bounds']
                control['widget'].SetSliderPos((float(value)-low)/(high-low))
                control['text'].SetText(self._Format(control['key'],value))
            elif kind=='number':
                if not control['widget'].IsFocus():
                    control['widget'].SetText(str(value))

    def _Format(self,key,value):
        if key=='damage_height':
            return '+%d %%'%round(value*100)
        if key=='fov':
            return '%d°'%round(value)
        if key=='grass_radius':
            return '%.1fx'%(value/100.)
        if key in ('damage_size','stone_size'):
            return '%d %%'%round((1+value)*100)
        if key in ('contrast','saturation'):
            return '%+d %%'%round((value-1)*100)
        if key in ('exposure','temperature','shadows'):
            return '%+d'%round(value*100)
        return '%d %%'%round(value*100)

    def section(self,label,y):
        carrier=self._keep(ui.ExpandedImageBox(),0,y)
        carrier.LoadImage(IMG+'option_title.tga')
        carrier.SetScale(2.,1.)
        carrier.AddFlag('not_pick')
        self.text(label,15,y+6,bold=True,width=311)

    def _row_label(self,label,y,hint='',compact=False):
        line=self.text(label,0,y+2,width=263)
        if hint:
            self.text(hint,0,y+23,small=True,color=DIM,width=348)
        if not compact:
            self._bar(0,y+44,348,1,(.145,.12,.11,1))
        return line

    def check(self,key,label,x,y,width=170,mask=None,status=None,hint=''):
        button=self._keep(ui.Button(),x,y)
        button.SetSize(width,21)
        button.SetEvent(lambda:self.change(key,self.value(key)^mask if mask else int(not self.value(key))))
        if label:
            button.SetToolTipText(hint or label)
        line=self.text(label,x+22,y-1,small=True,width=max(0,width-24)) if label else None
        self.controls.append(dict(kind='check',key=key,label=line,widget=button,mask=mask,status=status,width=width,y=y))
        return button

    def toggle(self,key,label,y,hint='',compact=False):
        line=self._row_label(label,y,hint,compact)
        line.SetLimitWidth(262)
        status=self.text('',287,y+4,width=65,small=True)
        self.check(key,'',265,y+7,width=83,status=status)
        self.controls[-1]['label']=line

    def radios(self,key,label,y,choices,vertical=False,columns=None,gap=None,pitch=None):
        choices = list(choices)
        current = self.value(key)
        if key=='track' and not current:
            import musicInfo
            current=musicInfo.METIN2THEMA
        if key in ('fps','track') and current not in dict(choices):
            # Preserve imported FPS limits / custom music instead of showing no selection.
            choices.append((current, str(current)+' FPS' if key=='fps' else str(current)))
        line=self.text(label,0,y+1,width=348) if label else None
        columns = 1 if vertical else columns or len(choices)
        if key=='fps' and len(choices)>6:
            columns=4
        width = 348//columns
        widgets=[]
        for index,(value,title) in enumerate(choices):
            x=(index%columns)*width
            row=y+((14 if vertical and not label else 29) if gap is None else gap)+(index//columns)*(pitch or (32 if vertical else 27))
            button=self._keep(ui.Button(),x,row)
            button.SetDownVisual(IMG+'checkbox_selected.tga')
            button.SetEvent(lambda chosen=value:self.change(key,chosen))
            button.SetToolTipText(title)
            self.text(title,x+22,row-1,small=True,width=width-24)
            widgets.append((value,button,width))
        self.controls.append(dict(kind='radio',key=key,label=line,widgets=widgets,y=y))

    def frame_limit(self,y):
        label=self.text(T('Limit snímků (FPS)','Frame limit (FPS)'),0,y,width=220,small=True)
        button=_button(self.content,238,y-2,'',self._CycleFrameLimit,'88x21')
        button.SetToolTipText(T('Kliknutím vybereš další limit FPS.','Click to select the next FPS limit.'))
        self.page_widgets.append(button)
        self.controls.append(dict(kind='fps_cycle',key='fps',label=label,widget=button,y=y))

    def tree_shadow(self,y):
        label=self.text(pages.TREE_SHADOW_LABEL,0,y,width=220,small=True)
        button=_button(self.content,238,y-2,'',self._CycleTreeShadow,'88x21')
        self.page_widgets.append(button)
        self.controls.append(dict(kind='tree_shadow',key='tree_shadow',label=label,widget=button,y=y))

    def background_fps(self,y):
        # The fixed A7 image page has no free line; the option lives in the R1 look (the A7 look is a fallback).
        return None

    def _CycleTreeShadow(self):
        choices=settingsmodel.TREE_SHADOW_CHOICES
        current=self.value('tree_shadow')
        index=choices.index(current) if current in choices else -1
        self.change('tree_shadow',choices[(index+1)%len(choices)])

    def _CycleFrameLimit(self):
        current=self.value('fps')
        choices=sorted(set((60,120,144,165,180,240,current)))
        self.change('fps',choices[(choices.index(current)+1)%len(choices)])

    def refresh_rate(self,y):
        label=self.text(T('Obnovovací frekvence (Hz)','Refresh rate (Hz)'),0,y,width=220,small=True)
        button=_button(self.content,238,y-2,'',self._CycleRefreshRate,'88x21')
        button.SetToolTipText(T('Kliknutím vybereš další podporovanou frekvenci.','Click to select the next supported refresh rate.'))
        self.page_widgets.append(button)
        status=self.text('',0,y+23,small=True,color=DIM,width=348)
        self.controls.append(dict(kind='refresh',key='refresh_hz',label=label,widget=button,status=status,y=y))

    def _CycleRefreshRate(self):
        info=settingsbackend.refresh_rate_info()
        if info is None or info[2]:
            return
        choices=(0,)+info[3]
        current=self.value('refresh_hz')
        next_index=(choices.index(current)+1)%len(choices) if current in choices else 0
        self.change('refresh_hz',choices[next_index])

    def ui_scale(self,y):
        if settingsbackend.ui_scale_info() is None:
            return 0
        self.section(T('Velikost rozhran\u00ed', 'Interface scale'), y)
        label=self.text(T('Cel\u00e9 rozhran\u00ed a HUD', 'Entire interface and HUD'),
                        0,y+36,width=220,small=True)
        button=_button(self.content,238,y+34,'',ui.__mem_func__(self._CycleUIScale),'88x21')
        button.SetToolTipText(T('Kliknut\u00edm vybere\u0161 dal\u0161\u00ed velikost.', 'Click to select the next scale.'))
        self.page_widgets.append(button)
        status=self.text('',0,y+63,small=True,color=DIM,width=348)
        self.hint(T('50\u2013150 % po 5 %. Zm\u011bna plat\u00ed ihned.', '50\u2013150% in 5% steps. Changes apply immediately.'), y+87)
        self.controls.append(dict(kind='ui_scale',key='ui_scale',label=label,
                                  widget=button,status=status,y=y+36,refresh_at=0.))
        self.content_height += 118
        return 118

    def _RefreshUIScaleStatus(self, control, info):
        if info == control.get('info'):
            return
        control['info'] = info
        if info is not None:
            control['status'].SetText(T('Aktivn\u00ed: %g %% | Maximum: %g %%',
                'Active: %g %% | Maximum: %g %%') % (info[1], info[2]))

    def _CycleUIScale(self):
        if settingsbackend.ui_scale_info() is None:
            return
        choices=settingsmodel.UI_SCALE_CHOICES
        current=self.value('ui_scale')
        self.change('ui_scale', choices[(choices.index(current)+1)%len(choices)])

    def hint(self,label,y):
        self.text(label,0,y,small=True,color=DIM,width=348)

    def slider(self,key,label,y,hint='',compact=False):
        line=self._row_label(label,y,hint,compact)
        line.SetLimitWidth(181)
        slider=self._keep(ui.SliderBar(),184,y+8)
        slider.SetButtonVisual(IMG+'slider/','small_thumb_01.tga','small_thumb_02.tga','small_thumb_03.tga')
        slider.SetBackgroundVisual(IMG+'slider/small_track.tga')
        bounds=settingsmodel.COLOR_BOUNDS.get(key,settingsmodel.BOUNDS.get(key))
        if key=='fov':
            bounds=(float(app.MIN_CAMERA_PERSPECTIVE),float(app.MAX_CAMERA_PERSPECTIVE))
        low,high=bounds
        def moved():
            value=low+max(0.,min(1.,slider.GetSliderPos()))*(high-low)
            if key=='grass_radius':
                value=int(round(value/10.))*10
            self.change(key,value,continuous=True)
        slider.SetEvent(moved)
        text=self.text('',348,y+3,color=GOLD,small=True)
        text.SetHorizontalAlignRight()
        self.controls.append(dict(kind='slider',key=key,label=line,widget=slider,text=text,bounds=bounds,y=y))

    def number(self,key,label,x,y):
        line=self.text(label,x,y+2)
        bg=_button(self.content,x+29,y,'',lambda:None,'88x21')
        self.page_widgets.append(bg)
        edit=self._keep(ui.EditLine(),x+36,y+3)
        edit.SetSize(70,16)
        edit.SetMax(3)
        edit.SetNumberMode()
        edit.SetText(str(self.value(key)))
        edit.SetUpdateEvent(lambda:self._NumberChanged(key,edit))
        edit.SetEscapeEvent(self.OnPressEscapeKey)
        self.edit_lines.append(edit)
        self.controls.append(dict(kind='number',key=key,label=line,widget=edit,y=y))

    def _NumberChanged(self,key,edit):
        if edit.GetText().isdigit():
            self.change(key,int(edit.GetText()),continuous=True)

    def link(self,key,label,y,hint='',event=None):
        self.section(label,y-4)
        # The existing section artwork owns paint; a Window owns its hit area.
        hit=self._keep(ui.Window(),0,y-4)
        hit.SetSize(348,28)
        hit.OnMouseLeftButtonUp=event or (lambda:self.open_page(key))
        self.text('›',330,y+1,color=GOLD)
        if hint:
            self.text(hint,15,y+27,small=True,color=DIM,width=327)

    def action(self,key,label,y,event,hint='',left=False,x=0,family='176x21'):
        if left:
            button=_button(self.content,x,y,label,event,family)
        else:
            self._row_label(label,y,hint)
            button=_button(self.content,260,y,T('Otevřít','Open'),event,'88x21')
        self.page_widgets.append(button)
        return button

    def tint(self,x,y,w,h,index):
        self._bar(x,y,w,h,((.06,.1,.08,.9),(.13,.09,.055,.9),(.075,.06,.075,.9))[index])

    def sky_thumbnail(self,x,y,index,event):
        button=self._keep(ui.Button(),x,y)
        path='d:/ymir work/ui/game/graphic/jtx_skybox/sky%d.dds'%(index+1)
        button.SetUpVisual(path)
        button.SetOverVisual(path)
        button.SetDownVisual(path)
        button.SetEvent(event)
        borders=[]
        for xx,yy,w,h in ((x,y,85,1),(x,y+50,85,1),(x,y,1,51),(x+84,y,1,51)):
            borders.append(self._bar(xx,yy,w,h,(*GOLD,1)))
        self.controls.append(dict(kind='sky',key='sky',widget=button,value=index,borders=borders,y=y))

    def sky_picker(self,y):
        self.sky_thumbnail(0,y,self.value('sky'),self.OpenSkyPicker)
        self.controls[-1]['current'] = True
        self.text(T('Obloha','Sky'),98,y+1)
        self.action('sky',T('Vybrat oblohu','Choose sky'),y+26,self.OpenSkyPicker,left=True,x=98)

    def OpenSkyPicker(self):
        self._ClosePopup()
        popup = ui.BoardWithTitleBar()
        self.popup = popup
        popup.AddFlag('float')
        popup.AddFlag('movable')
        popup.SetSize(388,320)
        popup.SetTitleName(T('Vybrat oblohu','Choose sky'))
        popup.SetCloseEvent(self._ClosePopup)
        popup.OnPressEscapeKey = self._ClosePopup
        popup.SetCenterPosition()
        for index,label in enumerate(pages.SKIES):
            x,y=20+(index%4)*89,43+(index//4)*84
            button=ui.Button()
            button.SetParent(popup)
            button.SetPosition(x,y)
            path='d:/ymir work/ui/game/graphic/jtx_skybox/sky%d.dds'%(index+1)
            button.SetUpVisual(path)
            button.SetOverVisual(path)
            button.SetDownVisual(path)
            button.SetEvent(lambda selected=index:self._SelectSky(selected))
            button.SetToolTipText(label)
            button.Show()
            text=ui.TextLine()
            text.SetParent(popup)
            text.SetPosition(x+42,y+55)
            text.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
            text.SetHorizontalAlignCenter()
            text.SetText(label)
            text.Show()
            self.popup_widgets.extend((button,text))
        popup.Show()
        popup.SetTop()
        popup.SetFocus()

    def _SelectSky(self,index):
        self.change('sky',index)
        self._ClosePopup()

    def _ClosePopup(self):
        if self.popup:
            self.popup.KillFocus()
            self.popup.Hide()
        self.popup=None
        self.popup_widgets=[]
        return True

    def recommended(self):
        if not self.Apply():
            return
        level=max(0,min(3,int(background.GetWorldGraphicsRecommendedLevel())))
        self.session.set('world_level',level)
        if level>0:
            for key in ('grass','lights','reflections','postprocess','rain_fx'):
                self.session.set(key,1)
            self.session.set('grass_radius',100)
        self.Apply()
        self._Refresh()

    def ResetPage(self):
        if not self.session:
            return
        if self.page=='keys' and self.key_page:
            self.key_page.RestoreDefaults()
            return
        if self.page=='panels' and self.panels_page:
            self.panels_page.RestoreDefaults()
            return
        keys={control['key'] for control in self.controls}
        # Reset only the current page, not unrelated renderer/color/camera state.
        if 'quality_preset' in keys:
            self.session.select_quality(2)
        if 'track' in keys:
            import musicInfo
            self.session.set('track',musicInfo.METIN2THEMA)
        reset_keys = keys-{'color_preset','quality_preset','block','pvp','track','family_names'}
        refresh_info = settingsbackend.refresh_rate_info()
        if refresh_info is None or refresh_info[2]:
            reset_keys.discard('refresh_hz')
        if 'quality_preset' in keys:
            reset_keys -= set(settingsmodel.QUALITY_KEYS)
        for key in reset_keys:
            self.session.set(key,settingsmodel.COLOR_DEFAULTS[key] if key in settingsmodel.COLOR_DEFAULTS else settingsmodel.DEFAULTS[key])
        if 'color_preset' in keys:
            self.session.select_colors(1)
            self.custom_expanded = False
        self.Apply()
        self._Refresh()

    def _Message(self,text):
        import uiCommon
        if self.message_dialog is None:
            self.message_dialog=uiCommon.PopupDialog()
        self.message_dialog.SetText(text)
        self.message_dialog.Open()

    def Apply(self):
        """Compatibility/flush entry; ordinary controls invoke this themselves."""
        self.save_deadline = None
        if not self.session:
            return True
        try:
            if self.key_page and getattr(self.key_page,'dirty',False) and not self.key_page.Save():
                return False
            self.session.apply()
        except settingsbackend.SettingsValidationError as error:
            self.session.discard()
            self._Refresh()
            self._Message(str(error))
            return False
        except (OSError,ValueError,TypeError,RuntimeError) as error:
            dbg.TraceError('[Settings A7] Save: %s'%error)
            self._Message(T('Nastavení se nepodařilo uložit. Okno zůstává otevřené a při zavření se uloží znovu.',
                            'Could not save settings. The window stays open; closing retries the save.'))
            return False
        return True

    def keybindings(self):
        if not self.key_window:
            import uikeybindings
            self.key_window=ui.ScriptWindow()
            ui.PythonScriptLoader().LoadScriptFile(self.key_window,'UIScript/game_option_0_2.py')
            self.key_window.SetParent(self)
            self.key_window.SetPosition(230,self.VIEW_TOP)
            self.key_window.SetSize(374,self.VIEW_HEIGHT)
            self.key_window.GetChild('BindingList').SetSize(352,self.VIEW_HEIGHT)
            self.key_window.GetChild('BindingScrollBar').SetScrollBarSize(self.VIEW_HEIGHT)
            self.key_page=uikeybindings.KeybindingsPage(auto_save=True)
            self.key_page.Bind(self.key_window)
            self.key_page.BeginSession()
            self.key_window.GetChild('SaveButton').Hide()
            self.key_window.GetChild('RestoreDefaultsButton').Hide()
            self.key_window.GetChild('BindingScrollBar').SetPosition(362,0)
        self.key_window.Show()

    def queue_inline(self):
        if self.queue_page is None:
            from uisettingsqueuepreview import QueuePreviewPage
            self.queue_page = QueuePreviewPage(self)
        self.content_height = self.queue_page.Build()

    def button_panels_inline(self):
        if self.panels_page is None:
            from uisettingsbuttonpanels import ButtonPanelsPage
            self.panels_page = ButtonPanelsPage(self)
        self.content_height = self.panels_page.Build()

    @property
    def minimap_page(self):
        return self.panels_page.minimap if self.panels_page else None

    def OpenQueueEditor(self):
        if self.editor and self.editor.IsShow():
            self.editor.SetTop()
            return
        if not self.Apply():
            return
        if self.queue_page:
            self.queue_page.Detach()
        if self.editor is None:
            from uimetinqueuedesigneditor import MetinQueueDesignEditor
            self.editor = MetinQueueDesignEditor(onClose=self._QueueEditorClosed)
        self.editor.Open()

    def _QueueEditorClosed(self):
        if not self.closing and self.IsShow() and self.page=='queue' and not self.searching:
            self._Render()

    def menu_music(self,y):
        """Hudba v menu: the select / creation music - shuffle or one track (pregame-hall.cfg music=)."""
        self.radios('menu_music','',y,MenuMusicChoices(),vertical=True)

    def music_inline(self,y):
        import musicInfo
        default = musicInfo.METIN2THEMA
        choices = [(default,T('Výchozí podle mapy','Map default'))]
        ours = AltheaTrackChoices()
        choices.extend(ours)
        names = set(app.GetFileList('BGM/*.mp3'))
        current = self.value('track')
        if current and current!=default and current not in dict(ours):
            names.add(current)
        choices.extend((name,name) for name in sorted(names,key=lambda name:name.lower()) if name!=default)
        self.radios('track','',y,choices,vertical=True)
        self.content_height = max(self.VIEW_HEIGHT,y+14+len(choices)*32+12)

    def OnUpdate(self):
        if self.session:
            state = (settingsbackend.family_names_supported(), settingsbackend.family_names_value())
            if state != self.family_name_state:
                self._Refresh()
        if self.session and self.page=='interface' and not self.searching and self.IsShow():
            for control in self.controls:
                if control['kind']=='ui_scale' and app.GetTime() >= control['refresh_at']:
                    control['refresh_at'] = app.GetTime() + .25
                    self._RefreshUIScaleStatus(control, settingsbackend.ui_scale_info())
        if self.save_deadline is not None and app.GetTime() >= self.save_deadline:
            self.Apply()
        if self.queue_page and self.page=='queue' and not self.searching and self.IsShow():
            self.queue_page.OnUpdate()
        if self.panels_page and self.page=='panels' and not self.searching and self.IsShow():
            self.panels_page.OnUpdate()

    def history(self):
        interface=self.backend.interface()
        if interface and getattr(interface,'systemNotifications',None):
            interface.systemNotifications.OpenInbox()

    def edit_loot(self):
        if not self.Apply():
            return
        interface=self.backend.interface()
        if interface and interface.BeginDropTrackerPlacementEdit():
            self.Hide()

    def reset_loot(self):
        interface=self.backend.interface()
        if interface:
            interface.ResetDropTrackerFloatingPlacement()

    def SearchOptions(self):
        if not self.session:
            return
        query=settingsmodel.search_text(self.search.GetText().strip())
        self._SaveScroll()
        if not query:
            self._Render()
            return
        self._ClearPage()
        self.searching = True
        self.search.SetFocus()
        self.heading.SetText(T('Výsledky hledání','Search results'))
        results=[row for row in self.search_index if query in settingsmodel.search_text(row[2])]
        self.hint(T('Nalezeno: %d','Found: %d')%len(results),0)
        for index,(page,key,label) in enumerate(results):
            def open_result(target=page,selected=key):
                self.highlight=selected
                self.open_page(target)
            self.link(key,label,35+index*62,pages.PAGES[page][2],event=open_result)
        self.content_height = 35+len(results)*62
        self._LayoutScroll(0)

    def OnMouseWheel(self,delta):
        if self.page=='keys' and self.key_page and not self.searching:
            return self.key_page.OnMouseWheel(delta)
        if self.scrollbar.IsShow() and delta:
            self.scrollbar.OnUp() if delta>0 else self.scrollbar.OnDown()
            return True
        return False
