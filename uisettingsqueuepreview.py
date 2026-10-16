"""Read-only current queue appearance inside the compact settings page."""
import ui
import metinqueuelibrary as design
from uimetinqueuelibrarycontroller import DesignController
from settingslocale import Text as T


class QueuePreviewPage:
    def __init__(self, owner, backend=None):
        self.owner = owner
        self.backend_source = backend
        self.backend = None
        self.controller = None
        self.active = False
        self.activePane = 0
        self.syncedPreset = None
        self.widgets, self.sliders = {}, {}

    def Build(self):
        self.Detach()
        # GameBackend caches its profile file: re-open it after another editor saves.
        self.backend = design.AdaptBackend(self.backend_source)
        v = self.owner
        self.active = True
        v.section(T('Fronta kamenů','Stone queue'),0)
        v.slider('stone_size',T('Velikost kamenů ve světě','World stone size'),40,compact=True)
        v.section(T('Vzhled označení','Marker appearance'),80)
        preview = v._keep(ui.WikiRenderTargetUi(),0,116)
        preview.SetSize(352,240)
        preview.AddFlag('not_pick')
        preview.Hide()
        control = v._keep(ui.Window(),0,116)
        control.SetSize(352,240)
        self.widgets = dict(Preview=preview, PreviewInput=control)
        self.widgets['ModelName'] = v.text('',176,363,small=True,center=True,width=348)
        self.widgets['Status'] = v.text('',176,386,small=True,center=True,width=348)
        v.action('queue_editor',T('Otevřít editor','Open editor'),419,
                 v.OpenQueueEditor,left=True,x=88)
        self.controller = DesignController(self,self.backend)
        self.controller.BeginSession()
        self.SyncModel()
        return v.VIEW_HEIGHT

    def Sync(self):
        # No editable appearance fields: viewing settings must never save a profile.
        pass

    def SyncModel(self):
        if self.active and self.controller:
            import nonplayer
            vnum = self.controller.previewVnum
            self.widgets['ModelName'].SetText(nonplayer.GetMonsterName(vnum) or T('Meteor %d','Stone %d') % vnum)

    def RefreshStatus(self):
        self.SetStatus('')

    def SetStatus(self,text):
        if self.active and 'Status' in self.widgets:
            self.widgets['Status'].SetText(text)

    def Scrolled(self,offset,height):
        pass  # This page always fits the fixed viewport.

    def Anchor(self,key):
        return 0

    def OnUpdate(self):
        if self.active and self.controller:
            self.controller.OnUpdate()

    def Detach(self):
        self.active = False
        if self.controller:
            self.controller.Destroy()
            self.controller = None
        for widget in self.widgets.values():
            widget.Hide()
        self.widgets = {}

    def Destroy(self):
        self.Detach()
        self.owner = None
