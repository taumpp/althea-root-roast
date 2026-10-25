"""Album-owned occurrence atlas; never registers with the live minimap."""
import json
import grp
import wndMgr
import ui
import uiScriptLocale
import uimountk1 as K1
import petalbumoccurrence as occurrence

WindowDestroy = getattr(ui, 'WindowDestroy', lambda function: function)


def _UseR1():
    """The R1 look (root/uir1.py) unless Settings -> "Starý vzhled" chose the original one."""
    try:
        import uir1
    except Exception:
        return False             # without the R1 kit the original window
    return uir1.UseR1()
RING = 'd:/ymir work/ui/pet/album_c/occurrence-ring.png'


def L(name):
    return getattr(uiScriptLocale, 'PET_ALBUM_' + name)


class OccurrenceOutline(ui.Window):
    """Fixed-pixel contour above the existing fill; dragging uses native bounds."""
    def __init__(self, parent, left, top, width, height, ring):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(left, top)
        self.SetSize(width, height)
        # grp.SetColor accepts a signed native int, not an unsigned Python DWORD.
        self.layers = ((0xff19140e-(1 << 32), occurrence.OutlineRows(ring, width, height, 7)),
                       (0xffffd66b-(1 << 32), occurrence.OutlineRows(ring, width, height, 3)))

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        for color, rows in self.layers:
            grp.SetColor(color)
            for left, top, width, height in rows:
                grp.RenderBar(x+left, y+top, width, height)


class PetAlbumOccurrenceWindow(ui.Window):
    def __init__(self):
        self.Initialize()
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.AddFlag('movable')
        with open('petalbumoccurrencemaps.txt', 'r') as stream:
            self.maps = json.load(stream)
        self.board = ui.BoardWithTitleBar()
        self.board.SetParent(self)
        self.board.AddFlag('not_pick')
        self.board.SetCloseEvent(ui.__mem_func__(self.Close))
        self.board.Show()
        self.r1Failed = False
        self.LoadR1()
        self.Hide()

    def LoadR1(self):
        """The R1 look (root/uipetr1.py) unless Settings -> "Starý vzhled" chose the original one; a failure traces to
        syserr and keeps the original look (not retried on every opening)."""
        if self.r1 or self.r1Failed or not _UseR1():
            return
        try:
            import uipetr1
            self.r1 = uipetr1.OccurrenceSkin(self)
        except Exception:
            import uir1
            uir1.TraceFailure('the pet occurrence window')
            self.r1Failed = True
            self.r1 = None

    def SyncLook(self):
        wanted = _UseR1() and not self.r1Failed
        if wanted and not self.r1:
            self.LoadR1()
        elif not wanted and self.r1:
            r1, self.r1 = self.r1, None
            r1.Restore()

    def __del__(self):
        ui.Window.__del__(self)

    def Initialize(self):
        self.board = self.state = self.atlas = self.ring = self.mask = self.r1 = None
        self.maps, self.owned, self._mountOwnedChildren = {}, [], []
        self.identity, self.petId = None, None

    def Label(self, x, y, value, size, color):
        label = K1.Text(self, x, y, value, size, color, 'center', False)
        label.AddFlag('not_pick')
        return label

    def ClearMap(self):
        for widget in self.owned + self._mountOwnedChildren:
            widget.Hide()
        self.owned, self._mountOwnedChildren = [], []
        self.atlas = self.ring = self.mask = None

    def Open(self, state, petId, petName, days, hours, overnight=False):
        row = state.pets.get(petId)
        if not state.available or not occurrence.Available(row, state.NowUtc()):
            self.Close()
            return False
        definition = self.maps.get(str(row['map']))
        if not definition:
            self.Close()
            return False
        self.SyncLook()
        self.ClearMap()
        atlas = ui.ExpandedImageBox()
        atlas.SetParent(self)
        atlas.AddFlag('not_pick')
        try:
            atlas.LoadImage(definition['atlas'])
            width, height, scale, ring = occurrence.Layout(
                atlas.GetWidth(), atlas.GetHeight(), definition['width'], definition['height'],
                row['x'], row['y'], row['radius'], wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        except (RuntimeError, ValueError, KeyError):
            atlas.Hide()
            self.Close()
            return False
        panelWidth, panelHeight = max(416, width+32), height+144
        self.SetSize(panelWidth, panelHeight)
        self.board.SetSize(panelWidth, panelHeight)
        self.board.SetTitleName(L('OCCURRENCE_TITLE') % petName)
        middle = panelWidth // 2
        route = L('OCCURRENCE_HUB') if row['shared_hub'] else L('OCCURRENCE_CHANNEL') % row['channel']
        location = L('OCCURRENCE_LOCATION') % (row['map_name'], route)
        labels = [self.Label(middle, 51, location, 16, 0xffecd3a6)]
        atlas.SetScale(scale, scale)
        # This engine scales ExpandedImageBox bounds a second time in SetScale.
        atlas.SetSize(width, height)
        left = (panelWidth-width) // 2
        atlas.SetPosition(left, 70)
        atlas.Show()
        mask = ui.Window()
        mask.SetParent(self)
        mask.AddFlag('not_pick')
        mask.SetPosition(left, 70)
        mask.SetSize(width, height)
        mask.Show()
        region = ui.ExpandedImageBox()
        region.SetParent(self)
        region.AddFlag('not_pick')
        region.LoadImage(RING)
        region.SetScale(ring[2]/region.GetWidth(), ring[3]/region.GetHeight())
        region.SetSize(round(ring[2]), round(ring[3]))
        region.SetPosition(left+round(ring[0]), 70+round(ring[1]))
        region.SetClippingMaskWindow(mask)
        region.Show()
        outline = OccurrenceOutline(self, left, 70, width, height, ring)
        outline.Show()
        self.owned.extend((atlas, mask, region, outline))
        self.atlas, self.mask, self.ring = atlas, mask, region
        labels.append(self.Label(middle, height+90, L('OCCURRENCE_SEARCH'), 12, 0xffdbd0bb))
        timing = L('OCCURRENCE_HOURS') % (days, hours)
        probe = self.Label(0, 0, '', 12, 0xffb5aa96)
        probe.Hide()
        def measure(value):
            probe.SetText(value)
            return probe.GetTextSize()[0]
        lines = K1.WrappedLines(timing, panelWidth-32, measure)
        if overnight:
            lines.append(L('OCCURRENCE_OVERNIGHT'))
        for index, line in enumerate(lines):
            labels.append(self.Label(middle, height+114+index*14, line, 12, 0xffb5aa96))
        if len(lines) > 1:
            panelHeight += (len(lines)-1)*14
            self.SetSize(panelWidth, panelHeight)
            self.board.SetSize(panelWidth, panelHeight)
        if self.r1:
            place = row['map_name']
            rest = location[len(place):].strip() if location.startswith(place) else route
            self.r1.Apply(L('OCCURRENCE_TITLE') % petName, place, rest, L('OCCURRENCE_SEARCH'), lines,
                          (left, 70, width, height), labels)
        self.state, self.petId = state, petId
        self.identity = occurrence.Identity(state.context, row)
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        return True

    def Close(self):
        self.state, self.petId, self.identity = None, None, None
        self.Hide()

    def Hide(self):
        ui.Window.Hide(self)

    def Show(self):
        self.OnUpdate()
        if self.state:
            ui.Window.Show(self)

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        if not self.state:
            return
        row = self.state.pets.get(self.petId)
        if (not self.state.available or not occurrence.Available(row, self.state.NowUtc()) or
                occurrence.Identity(self.state.context, row) != self.identity):
            self.Close()

    @WindowDestroy
    def Destroy(self):
        self.Close()
        self.ClearMap()
        if self.r1:
            r1, self.r1 = self.r1, None
            r1.Restore()
        if self.board:
            self.board.SetCloseEvent(None)
            self.board.Hide()
        self.Initialize()
