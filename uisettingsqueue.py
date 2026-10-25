"""A6 adapter: the existing queue draft/controller inside one settings page."""
import ui
import grp
import WikiRenderTarget
import metinqueuelibrary as design
import uimetinqueueappearance as appearance
from uimetinqueuelibrarycontroller import DesignController
from settingslocale import Text as T

IMG = 'd:/ymir work/ui/game/crimson_ember/gameoption/'
INK, DIM = (.88,.85,.78), (.48,.45,.42)


class InlineDesignController(DesignController):
    def _CreatePreview(self):
        if self.page.active:
            DesignController._CreatePreview(self)

    def _UpdatePreview(self, reframe=False):
        if self.page.active:
            DesignController._UpdatePreview(self,reframe)


class InlineQueuePage:
    def __init__(self, owner, backend=None):
        self.owner = owner
        self.backend = design.AdaptBackend(backend)
        self.controller = None
        self.active = False
        self.syncing = False
        self.activePane = 0
        self.syncedPreset = None
        self.widgets, self.sliders, self.rgb = {}, {}, {}
        self.choices = []
        self.status = ''
        self.preview_visible = None

    def Build(self):
        v = self.owner
        self.active = True
        self.widgets, self.sliders, self.rgb = {}, {}, {}
        self.choices = []
        v.section(T('Označení kamenů','Stone markers'),0)
        self._Choice(design.BODY_ENABLED,1,T('Obal','Body'),0,42,toggle=True)
        self._Choice(design.RING_ENABLED,1,T('Prstenec','Ring'),0,80,toggle=True)
        preview = v._keep(ui.WikiRenderTargetUi(),180,36)
        preview.SetSize(168,132)
        preview.AddFlag('not_pick')
        preview.Hide()
        control = v._keep(ui.Window(),180,36)
        control.SetSize(168,132)
        self.widgets.update(Preview=preview,PreviewInput=control)
        self.widgets['ModelName'] = v.text('',264,173,small=True,center=True,width=168)
        v.slider('stone_size',T('Velikost kamenů ve světě','World stone size'),206,compact=True)
        v.section(T('Velikost a pohyb označení','Marker size and motion'),250)
        for field,label,y in ((design.SIZE,T('Velikost obalu','Body size'),294),
                              (design.TEMPO,T('Rychlost obalu','Body speed'),331),
                              (design.RING_SIZE,T('Velikost prstence','Ring size'),368),
                              (design.RING_TEMPO,T('Rychlost prstence','Ring speed'),405)):
            self._Slider(field,label,y)
        self.widgets['MotionHint'] = v.text('',0,437,small=True,width=348)
        v.section(T('Barva označení','Marker color'),479)
        self.widgets['Swatch'] = v._bar(0,515,25,22,(.9,.7,.4,1))
        self.widgets['ColorValue'] = v.text('',39,519)
        for channel,label,y in ((16,T('Červená','Red'),567),(8,T('Zelená','Green'),605),(0,T('Modrá','Blue'),643)):
            slider,text = self._RawSlider(label,y)
            slider.SetEvent(self._ReadRgb)
            self.rgb[channel]=(slider,text)
        v.section(T('Světlo a podrobnosti','Light and details'),690)
        for field,label,y in ((design.BRIGHTNESS,T('Jas kresby','Artwork brightness'),734),
                              (design.GLOW,T('Záře kolem efektu','Effect glow'),773),
                              (design.SPARKS,T('Množství jisker','Spark density'),812)):
            self._Slider(field,label,y)
        v.text(T('Pulzování jasu','Brightness pulse'),0,856)
        for index,(value,label) in enumerate(design.PULSE_CHOICES):
            self._Choice(design.PULSE,value,label,(index%2)*174,889+(index//2)*28)
        for field,label,y in ((design.RING_WIDTH,T('Tloušťka tahu','Stroke width'),971),
                              (design.MARKER_SCALE,T('Velikost horní značky','Upper marker size'),1010),
                              (design.CLEARANCE,T('Odstup horní značky','Upper marker clearance'),1049)):
            self._Slider(field,label,y)
        v.section(T('Obal','Body'),1100)
        for index,row in enumerate(design.APPROVED_CATALOG):
            self._Choice(design.PRESET,row[0],row[2].replace(' | Althea',''),
                         (index%2)*174,1138+(index//2)*40)
        v.section(T('Prstenec','Ring'),1642)
        for index,(value,label) in enumerate(design.APPROVED_RINGS):
            self._Choice(design.RING_STYLE,value,label,(index%2)*174,1680+(index//2)*40)
        # Camera/model controls are actions in place, never another editor page.
        v.section(T('Model náhledu','Preview model'),2068)
        import nonplayer
        for index,vnum in enumerate(design.MODEL_VNUMS):
            self._Choice('model',vnum,nonplayer.GetMonsterName(vnum) or T('Meteor %d','Stone %d')%vnum,
                         (index%2)*174,2106+(index//2)*40)
        bottom = 2120+((len(design.MODEL_VNUMS)+1)//2)*40
        v.action('reset_camera',T('Obnovit kameru náhledu','Reset preview camera'),bottom,
                 lambda:self.controller.SetModel(self.controller.previewVnum),left=True)
        self.widgets['Status'] = v.text('',0,bottom+35,small=True,width=348)
        if self.controller is None:
            self.controller = InlineDesignController(self,self.backend)
            self.controller.BeginSession()
        else:
            self.controller._BindPreview()
            self.controller._SyncUi()
            self.controller._CreatePreview()
        self.SyncModel()
        self.preview_visible = None
        return bottom+65

    def _RawSlider(self,label,y):
        v = self.owner
        title = v.text(label,0,y+2,width=180)
        slider = v._keep(ui.SliderBar(),184,y+8)
        slider.SetButtonVisual(IMG+'slider/','small_thumb_01.tga','small_thumb_02.tga','small_thumb_03.tga')
        slider.SetBackgroundVisual(IMG+'slider/small_track.tga')
        text = v.text('',348,y+3,small=True,color=(.84,.71,.47))
        text.SetHorizontalAlignRight()
        slider.a6_label = title
        return slider,text

    def _Slider(self,field,label,y):
        slider,text = self._RawSlider(label,y)
        slider.SetEvent(self._ReadSliders)
        self.sliders[field]=(0,slider,slider,text)

    def _Choice(self,field,value,label,x,y,toggle=False):
        v = self.owner
        button = v._keep(ui.Button(),x,y)
        button.SetDownVisual(IMG+'checkbox_selected.tga')
        button.SetToolTipText(label)
        button.SetEvent(lambda:self._Choose(field,value,toggle))
        # Measure at the native font and wrap complete catalogue names in two rows.
        line = v.text(label,x+22,y-1,small=True)
        lines=[line]
        if line.GetTextSize()[0]>146:
            words=label.split()
            split=len(words)-1
            while split>1:
                line.SetText(' '.join(words[:split]))
                if line.GetTextSize()[0]<=146:
                    break
                split-=1
            line.SetText(' '.join(words[:split]))
            lines.append(v.text(' '.join(words[split:]),x+22,y+13,small=True,width=146))
        self.choices.append((field,value,button,lines,toggle))

    def _Choose(self,field,value,toggle):
        c=self.controller
        if c is None or c.draft is None:
            return
        if field=='model':
            c.SetModel(value)
        elif field==design.PRESET:
            c.Select(value)
        else:
            c.SetValue(field,int(not c.draft[field]) if toggle else value)
        self.Sync()
        self.Scrolled(max(0,-self.owner.content.GetLocalPosition()[1]),self.owner.VIEW_HEIGHT)

    def _ReadSliders(self):
        if self.controller and not self.syncing:
            self.controller._SampleSliders()

    def _ReadRgb(self):
        if not self.active or not self.rgb or not self.controller or self.controller.draft is None or self.syncing:
            return
        value=0
        for shift,(slider,text) in self.rgb.items():
            channel=max(0,min(255,int(round(slider.GetSliderPos()*255))))
            value |= channel<<shift
        if value != self.controller.draft[design.PRIMARY]:
            self.controller.SetValue(design.PRIMARY,value)

    def Sync(self):
        if not self.active or not self.controller or self.controller.draft is None:
            return
        self.syncing=True
        try:
            draft=self.controller.draft
            for field,(_,row,slider,text) in self.sliders.items():
                low,high=design.Ranges(draft[0])[field]
                slider.SetSliderPos(appearance.PercentToSlider(draft[field],low,high))
                enabled=design.Supports(draft[0],field,draft)
                slider.Enable() if enabled else slider.Disable()
                slider.a6_label.SetFontColor(*(INK if enabled else DIM))
                text.SetText(design.DisplayValue(field,draft[field]) if enabled else '-')
            for field,value,button,lines,toggle in self.choices:
                selected = self.controller.previewVnum==value if field=='model' else draft[field]==value
                enabled = field in ('model',design.PRESET) or design.Supports(draft[0],field,draft)
                button.SetUpVisual(IMG+'checkbox_'+('selected' if selected else 'unselected')+'.tga')
                button.SetOverVisual(IMG+'checkbox_'+('selected' if selected else 'hover')+'.tga')
                button.SetSize(170,35 if len(lines)>1 else 23)
                button.Enable() if enabled else button.Disable()
                for line in lines:
                    line.SetFontColor(*(INK if enabled else DIM))
            color=draft[design.PRIMARY]
            self.widgets['ColorValue'].SetText('#%06X'%color)
            rgb=tuple((color>>shift)&255 for shift in (16,8,0))
            self.widgets['Swatch'].SetColor(grp.GenerateColor(*(tuple(c/255. for c in rgb)+(1.,))))
            for shift,(slider,text) in self.rgb.items():
                channel=(color>>shift)&255
                slider.SetSliderPos(channel/255.)
                text.SetText(str(channel))
            self.widgets['MotionHint'].SetText('' if design.Supports(draft[0],design.TEMPO,draft) else
                T('Tento obal má pevně danou rychlost.','This body has a fixed animation speed.'))
        finally:
            self.syncing=False

    def SyncModel(self):
        if self.active and self.controller:
            import nonplayer
            vnum=self.controller.previewVnum
            self.widgets['ModelName'].SetText(nonplayer.GetMonsterName(vnum) or T('Meteor %d','Stone %d')%vnum)

    def RefreshStatus(self):
        # The main Apply button owns saving; no extra instructional status prose.
        self.SetStatus('')

    def SetStatus(self,text):
        self.status=text
        if self.active and 'Status' in self.widgets:
            self.widgets['Status'].SetText(text)

    def Scrolled(self,offset,height):
        if not self.active or not self.controller:
            return
        # Scissor owns clipping; suspend rendering only when the preview is offscreen.
        visible=offset<168 and offset+height>36
        if self.controller.previewIndex is not None and visible!=self.preview_visible:
            WikiRenderTarget.SetVisibility(self.controller.previewIndex,visible)
            self.preview_visible=visible
        if not visible:
            self.controller._StopPreviewDrag()

    def Anchor(self,key):
        return dict(queue_color=479,queue_body=1100,queue_ring=1642,stone_size=194).get(key,0)

    def OnUpdate(self):
        if self.active and self.controller:
            self._ReadRgb()
            self.controller.OnUpdate()

    def Detach(self):
        if not self.active:
            return
        self._ReadSliders()
        self._ReadRgb()
        self.active=False
        if self.controller:
            self.controller._RemovePreview()
            design.ClearPreview()
        self.widgets,self.sliders,self.rgb,self.choices={},{},{},[]

    def Apply(self):
        if not self.controller:
            return True
        self._ReadSliders()
        self._ReadRgb()
        c=self.controller
        if c.draft is None:
            return False
        changed=(c.draft[0]!=c.original[0] or c.draftNearbyFill!=c.originalNearbyFill or
                 any(tuple(values)!=c.originalProfiles[key] for key,values in c.profiles.items()))
        # Visiting this page must not activate/rewrite a profile when the player
        # only applies an unrelated preference elsewhere in Settings.
        return c.Apply() if changed else True

    def Reset(self):
        if self.controller:
            self.controller.RestoreAllDefaults()

    def Destroy(self):
        self.Detach()
        if self.controller:
            self.controller.Destroy()
        self.controller=None
        self.owner=None
