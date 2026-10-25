"""B library: native Althea components, persistent preview, independent layers."""
import grp
import nonplayer
import ui
import wndMgr
import fontconfig
import uicrimsoncontrols as crimson
from uicrimsonember import SettingsScrollBar
from uicolorpicker import UnpackRgb
import uimetinqueueappearance as appearance
import metinqueuelibrary as design
from uimetinqueuelibrarycontroller import DesignController

WIDTH, HEIGHT = 760, 552
LEFT, RIGHT, PANEL_WIDTH = 24, 380, 332
GOLD = 0xFFE5B95F
MUTED = 0xFFB5ADA1


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


class MetinQueueDesignEditor(ui.BoardWithTitleBar):
    def __init__(self, backend=None, onClose=None):
        ui.BoardWithTitleBar.__init__(self)
        self.backend = design.AdaptBackend(backend)
        self.closeEvent = onClose
        self.controller = None
        self.children, self.panes, self.rows, self.tabs = [], [], [], []
        self.widgets, self.sliders = {}, {}
        self.libraryButtons, self.libraryEntries = [], []
        self.activePane, self.libraryLayer = 0, 0
        self.catalogOffsets, self.searches = [0, 0], ["", ""]
        self.syncingLibrary = False
        self.syncedPreset = None
        self.AddFlag("movable")
        self.AddFlag("float")
        self.SetSize(WIDTH, HEIGHT)
        self.SetTitleName(u"Vzhled fronty meteorů")
        self.SetCloseEvent(self.Close)
        self._Build()
        self.controller = DesignController(self, self.backend)

    def _Keep(self, widget, parent, x, y, name=None):
        widget.SetParent(parent)
        widget.SetPosition(int(x), int(y))
        self.children.append(widget)
        if name:
            self.widgets[name] = widget
        widget.Show()
        return widget

    def _Text(self, parent, x, y, text, width=None, name=None, role=fontconfig.ROLE_BODY):
        widget = self._Keep(ui.TextLine(), parent, x, y, name)
        widget.AddFlag("not_pick")
        widget.SetFontName(fontconfig.FontForRole(role))
        if width:
            widget.SetLimitWidth(width)
        widget.SetText(text)
        return widget

    def _Button(self, parent, x, y, text, event, family="100x21", name=None):
        button = self._Keep(ui.Button(), parent, x, y, name)
        crimson.ApplyVisuals(button, family)
        button.SetText(text)
        button.SetEvent(event)
        return button

    def _Toggle(self, parent, x, y, text, field, name):
        button = self._Keep(ui.ToggleButton(), parent, x, y, name)
        button.SetUpVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_unselected.tga")
        button.SetOverVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_hover.tga")
        button.SetDownVisual("d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_selected.tga")
        callback = lambda: self.controller.SetValue(field, int(button.IsDown()))
        button.SetToggleUpEvent(callback)
        button.SetToggleDownEvent(callback)
        self._Text(parent, x + 22, y, text, 150)
        return button

    def _Row(self, pane, field, height):
        row = self._Keep(ui.Window(), self.panes[pane], 0, 0)
        row.SetSize(PANEL_WIDTH, height)
        self.rows.append((pane, field, row, height))
        return row

    def _Slider(self, pane, field, label):
        row = self._Row(pane, field, 44)
        self._Text(row, 0, 0, label, 245)
        value = self._Text(row, PANEL_WIDTH, 0, "")
        value.SetHorizontalAlignRight()
        slider = self._Keep(ui.SliderBar(), row, 0, 22)
        # Exact game-options DragButton + track family, at its original dimensions.
        if hasattr(slider, "SetButtonVisual"):
            slider.SetButtonVisual(appearance.IMG_DIR + "slider/", "small_thumb_01.tga",
                                   "small_thumb_02.tga", "small_thumb_03.tga")
            slider.SetBackgroundVisual(appearance.IMG_DIR + "slider/small_track.tga")
        slider.SetEvent(lambda: self.controller._SampleSliders())
        self.sliders[field] = (pane, row, slider, value)

    def _Choice(self, pane, field, label, choices, name):
        row = self._Row(pane, field, 54)
        self._Text(row, 0, 0, label, PANEL_WIDTH)
        self._Button(row, 0, 22, "", lambda: self.controller.Cycle(field, choices), "199x27", name)

    def _Build(self):
        self._Text(self, LEFT, 42, u"Vyber si styl", 500, role=fontconfig.ROLE_LARGE_BOLD)
        for index, label in enumerate((u"Efekty", u"Barva a jas", u"Pohyb", u"Doladění")):
            self.tabs.append(self._Button(self, LEFT + index * 106, 76, label,
                             lambda pane=index: self._SetPane(pane)))
            pane = self._Keep(ui.Window(), self, LEFT, 154)
            pane.SetSize(PANEL_WIDTH, 310)
            self.panes.append(pane)
        self._Toggle(self, LEFT, 125, u"Obal", design.BODY_ENABLED, "BodyToggle")
        self._Toggle(self, 205, 125, u"Prstenec", design.RING_ENABLED, "RingToggle")

        for index, label in enumerate((u"OBAL", u"PRSTENEC")):
            self._Button(self.panes[0], index * 106, 0, label,
                         lambda layer=index: self.SetLibraryLayer(layer), name="Layer%d" % index)
        searchBox = self._Keep(ui.SlotBar(), self.panes[0], 0, 32)
        searchBox.SetSize(PANEL_WIDTH, 26)
        self.search = self._Keep(LibrarySearch(self), searchBox, 8, 5)
        self.search.SetSize(PANEL_WIDTH - 45, 18)
        self.search.SetMax(60)
        self.search.SetLimitWidth(PANEL_WIDTH - 45)
        if hasattr(self.search, "SetBackText"):
            self.search.SetBackText(u"Hledat efekt...")
        self._Button(self.panes[0], PANEL_WIDTH - 32, 36, "x", self.ClearSearch, "32x16")
        self.catalogViewport = self._Keep(ui.Window(), self.panes[0], 0, 68)
        self.catalogViewport.SetSize(310, 216)
        self.catalogViewport.OnMouseWheel = ui.__mem_func__(self._CatalogWheel)
        for index in range(9):
            button = self._Button(self.catalogViewport, 0, index * 24, "",
                                 lambda row=index: self._SelectRow(row), "306x18")
            button.OnMouseWheel = ui.__mem_func__(self._CatalogWheel)
            self.libraryButtons.append(button)
        self.scroll = self._Keep(SettingsScrollBar(), self.panes[0], PANEL_WIDTH - 12, 68)
        self.scroll.SetScrollBarSize(216)
        self.scroll.SetScrollEvent(ui.__mem_func__(self._ScrollCatalog))
        self.scroll.OnMouseWheel = ui.__mem_func__(self._CatalogWheel)
        self._Text(self.panes[0], 0, 291, "", PANEL_WIDTH, "CatalogueCount", fontconfig.ROLE_DENSE)

        color = self._Row(1, design.PRIMARY, 76)
        self._Text(color, 0, 0, u"Barva obalu a prstence", PANEL_WIDTH)
        colors = (0xE5B95F, 0xFF405F, 0x69BEFF, 0xB290FF, 0x69DF9D, 0xF1E8D6)
        for index, rgb in enumerate(colors):
            swatch = self._Keep(ui.Bar(), color, index * 32, 24, "Color%d" % index)
            swatch.SetSize(24, 21)
            red, green, blue = UnpackRgb(rgb)
            swatch.SetColor(grp.GenerateColor(red / 255., green / 255., blue / 255., 1))
            swatch.SetMouseLeftButtonDownEvent(lambda value=rgb: self.controller.SetValue(design.PRIMARY, value))
        self._Button(color, 218, 23, u"Vlastní...", lambda: self.controller.OpenColor(design.PRIMARY))
        self._Text(color, 0, 53, "", PANEL_WIDTH, "ColorValue")
        for field, label in ((design.BRIGHTNESS, u"Jas kresby"), (design.GLOW, u"Záře kolem efektu")):
            self._Slider(1, field, label)
        hint = self._Row(1, None, 40)
        self._Text(hint, 0, 0, u"Jas zesvětlí kresbu. Záře přidá světelný lem.", PANEL_WIDTH, role=fontconfig.ROLE_DENSE)
        self._Text(hint, 0, 17, u"Jiskry nastavíš v záložce Doladění.", PANEL_WIDTH, role=fontconfig.ROLE_DENSE)

        self._Slider(2, design.TEMPO, u"Rychlost obalu")
        self._Slider(2, design.RING_TEMPO, u"Rychlost prstence")
        self._Choice(2, design.PULSE, u"Pulzování jasu", design.PULSE_CHOICES, "PulseButton")
        self._Choice(2, design.FOCUS, u"Ostatní meteory ve frontě", design.FOCUS_CHOICES, "FocusButton")
        motionHint = self._Row(2, None, 40)
        self._Text(motionHint, 0, 0, "", PANEL_WIDTH, "MotionHint", fontconfig.ROLE_DENSE)
        self._Text(motionHint, 0, 17, u"Každá vrstva má vlastní nastavení pohybu.", PANEL_WIDTH, role=fontconfig.ROLE_DENSE)

        for field, label in ((design.SIZE, u"Velikost obalu"), (design.RING_SIZE, u"Velikost prstence"), (design.RING_WIDTH, u"Tloušťka tahu"),
                             (design.MARKER_SCALE, u"Velikost horní značky"),
                             (design.CLEARANCE, u"Odstup horní značky"),
                             (design.SPARKS, u"Množství jisker")):
            self._Slider(3, field, label)
        sizeHint = self._Row(3, None, 38)
        self._Text(sizeHint, 0, 0, u"100% zachovává základní velikost návrhu.", PANEL_WIDTH, role=fontconfig.ROLE_DENSE)

        frame = self._Keep(ui.Bar(), self, RIGHT, 120, "PreviewFrame")
        frame.SetSize(356, 266)
        frame.SetColor(grp.GenerateColor(.055, .058, .043, 1))
        preview = self._Keep(ui.WikiRenderTargetUi(), frame, 2, 2, "Preview")
        preview.SetSize(352, 262)
        preview.SetClippingMaskWindow(self)
        preview.Hide()
        control = self._Keep(ui.Window(), frame, 2, 2, "PreviewInput")
        control.SetSize(352, 262)
        self._Text(self, RIGHT + 10, 128, "", 330, "SelectedName", fontconfig.ROLE_DENSE)
        self._Text(self, RIGHT, 393, u"Levé: posun. Pravé: otočení. Kolečko: přiblížení.", 356,
                   role=fontconfig.ROLE_DENSE)
        self._Button(self, RIGHT, 415, "", self._CycleModel, "176x21", "ModelButton")
        self._Button(self, 675, 415, u"Kamera", self._ResetCamera, "61x21")
        self._Text(self, RIGHT, 446, "", 250, "SelectedRing")
        self._Button(self, 675, 443, u"Vybrat", lambda: self.SetLibraryLayer(1), "61x21")
        self._Text(self, LEFT, 477, "", WIDTH - 48, "Status", fontconfig.ROLE_DENSE)
        divider = self._Keep(ui.Bar(), self, LEFT, 496)
        divider.SetSize(WIDTH - 48, 1)
        divider.SetColor(grp.GenerateColor(.28, .23, .16, 1))
        divider.AddFlag("not_pick")
        self._Button(self, LEFT, 510, u"Reset vzhledu", lambda: self.controller.RestoreDefaults(), "100x21", "ResetButton")
        self.widgets["ResetButton"].SetToolTipText(u"Výchozí hodnoty pro vybraný obal a prstenec. Typy zůstanou vybrané.")
        self._Button(self, 136, 510, u"Výchozí sestava", lambda: self.controller.RestoreAllDefaults(), "148x23", "DefaultButton")
        self.widgets["DefaultButton"].SetToolTipText(u"Pulzující obal + Klasický vír, zlatá, základní velikost a jas.")
        self._Button(self, 298, 512, u"Zpět", lambda: self.controller.UndoReset(), "61x21", "UndoButton")
        self._Button(self, 462, 508, u"Uložit", self._Ok, "170x24", "SaveButton")
        self._Button(self, 644, 510, u"Zrušit", self.Close, "100x21")
        self._SetPane(0, False)

    def _SetPane(self, index, sample=True):
        if self.controller and sample:
            self.controller._SampleSliders()
        if index != 0:
            self.search.KillFocus()
        self.activePane = index
        for number, pane in enumerate(self.panes):
            pane.Show() if number == index else pane.Hide()
            self.tabs[number].SetUpVisual(crimson.Visual("100x21", "selected" if number == index else "normal"))

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

    def _CatalogWheel(self, delta):
        self.catalogOffsets[self.libraryLayer] += -1 if delta > 0 else 1
        self._RefreshCatalogue()
        return True

    def _ScrollCatalog(self):
        if self.syncingLibrary:
            return
        maximum = max(0, len(self.libraryEntries) - len(self.libraryButtons))
        self.catalogOffsets[self.libraryLayer] = int(round(self.scroll.GetPos() * maximum))
        self._RefreshCatalogue()

    def _RefreshCatalogue(self):
        if not self.controller or self.controller.draft is None:
            return
        draft = self.controller.draft
        raw = design.APPROVED_RINGS if self.libraryLayer else tuple((row[0], row[2]) for row in design.APPROVED_CATALOG)
        query = design.SearchKey(self.search.GetText().strip())
        entries = [row for row in raw if not query or query in design.SearchKey(row[1]) or query == str(row[0])]
        self.libraryEntries = entries
        allowed = dict(design.RingChoices(draft[0])) if self.libraryLayer else design.BY_NUMBER
        # Keep immediately usable choices first in this private UI candidate.
        entries.sort(key=lambda row: row[0] not in allowed)
        self.libraryEntries = entries
        selected = draft[design.RING_STYLE] if self.libraryLayer else draft[0]
        maximum = max(0, len(entries) - len(self.libraryButtons))
        offset = max(0, min(maximum, self.catalogOffsets[self.libraryLayer]))
        self.catalogOffsets[self.libraryLayer] = offset
        self.syncingLibrary = True
        try:
            for index, button in enumerate(self.libraryButtons):
                if offset + index >= len(entries):
                    button.Hide()
                    continue
                number, label = entries[offset + index]
                button.SetText(label)
                available = number in allowed
                button.SetUpVisual(crimson.Visual("306x18", "selected" if selected == number else "normal"))
                button.SetToolTipText(label if available else label + u" · čeká na převedení do testu")
                button.Enable() if available else button.Disable()
                button.Show()
            if maximum:
                self.scroll.SetMiddleBarSize(float(len(self.libraryButtons)) / len(entries))
                self.scroll.SetScrollBarSize(216)
                self.scroll.SetScrollStep(1.0 / maximum)
                self.scroll.SetPos(float(offset) / maximum)
                self.scroll.Show()
            else:
                self.scroll.Hide()
            for layer in (0, 1):
                self.widgets["Layer%d" % layer].SetUpVisual(crimson.Visual("100x21", "selected" if layer == self.libraryLayer else "normal"))
            kind = u"prstenců" if self.libraryLayer else u"obalů"
            ready = sum(1 for number, _ in raw if number in allowed)
            self.widgets["CatalogueCount"].SetText(u"%d %s ve výběru · %d dostupných v testu" % (len(raw), kind, ready))
        finally:
            self.syncingLibrary = False

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
        for field, name in ((design.BODY_ENABLED, "BodyToggle"), (design.RING_ENABLED, "RingToggle")):
            self.widgets[name].Down() if draft[field] else self.widgets[name].SetUp()
        self.widgets["ColorValue"].SetText(u"Zlatá | #E5B95F" if draft[design.PRIMARY] == design.GOLD else "#%06X" % draft[design.PRIMARY])
        for name, field, choices in (("PulseButton", design.PULSE, design.PULSE_CHOICES),
                                     ("FocusButton", design.FOCUS, design.FOCUS_CHOICES)):
            self.widgets[name].SetText(dict(choices)[draft[field]])
        self.widgets["SelectedName"].SetText(u"Náhled | " + design.BY_NUMBER[draft[0]][2])
        self.widgets["SelectedRing"].SetText(u"Prstenec: " + (design.RING_NAMES[draft[design.RING_STYLE]] if draft[design.RING_ENABLED] else u"vypnutý"))
        self.widgets["MotionHint"].SetText(u"100% = výchozí tempo efektu." if design.Supports(draft[0], design.TEMPO, draft)
                                          else u"Tento obal má vlastní původní pohyb.")
        self.widgets["UndoButton"].Show() if self.controller.undoReset is not None else self.widgets["UndoButton"].Hide()
        self._RefreshCatalogue()
        self.SyncModel()
        self.RefreshStatus()

    def SyncModel(self):
        vnum = self.controller.previewVnum
        self.widgets["ModelButton"].SetText(nonplayer.GetMonsterName(vnum) or u"Meteor %d" % vnum)

    def RefreshStatus(self):
        if not self.controller or self.controller.draft is None:
            return
        changed = (self.controller.draft[0] != self.controller.original[0] or
                   self.controller.draftNearbyFill != self.controller.originalNearbyFill or
                   any(tuple(value) != self.controller.originalProfiles[key] for key, value in self.controller.profiles.items()))
        self.SetStatus(u"Neuložené změny. Uložit potvrdí celý rozepsaný vzhled." if changed else
                       u"Vyber styl. Náhled reaguje ihned, nastavení potvrdíš tlačítkem Uložit.")

    def SetStatus(self, text):
        self.widgets["Status"].SetText(text)

    def _CycleModel(self):
        index = design.MODEL_VNUMS.index(self.controller.previewVnum)
        self.controller.SetModel(design.MODEL_VNUMS[(index + 1) % len(design.MODEL_VNUMS)])

    def _ResetCamera(self):
        self.controller.SetModel(self.controller.previewVnum)

    def _Ok(self):
        if self.controller.Apply():
            self.Close()

    def Open(self, draft=None, nearby=None):
        self.backend = design.AdaptBackend(self.backend)
        if not self.controller.BeginSession(draft, nearby):
            return
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Close(self):
        self.search.KillFocus()
        if self.controller:
            self.controller.Discard()
        self.KillFocus()
        self.Hide()
        if self.closeEvent:
            self.closeEvent()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self):
        if self.controller and self.IsShow():
            # Existing camera gestures keep working outside the viewport during a drag.
            self.controller.OnUpdate()

    def Destroy(self):
        self.Close()
        if self.controller:
            self.controller.Destroy()
        self.scroll.Destroy()
        self.controller, self.closeEvent = None, None
        self.search.owner = None
        self.children, self.rows, self.panes, self.tabs = [], [], [], []
        self.widgets, self.sliders, self.libraryButtons = {}, {}, []


class DesignOptionsEntry(object):
    """Preserve the existing game-settings entry point and native preview owner."""
    def __init__(self, page, closeOwner, backend=None):
        self.page, self.closeOwner = page, closeOwner
        self.backend = design.AdaptBackend(backend)
        self.editor, self.children = None, []
        title = page.GetChild("TitleImage")
        for child in getattr(page, "Children", ()):
            if child is not title:
                child.Hide()
        for y, text in ((48, u"Vzhled fronty meteorů"), (78, ""),
                        (108, u"Obal a prstenec vybíráš nezávisle."),
                        (127, u"Barva, pohyb a náhled v jednom editoru.")):
            label = ui.TextLine()
            label.SetParent(page)
            label.SetPosition(14, y)
            label.SetLimitWidth(337)
            label.SetText(text)
            label.Show()
            self.children.append(label)
            if y == 78:
                self.summary = label
        button = ui.Button()
        button.SetParent(page)
        button.SetPosition(14, 165)
        crimson.ApplyVisuals(button, "199x27")
        button.SetText(u"Otevřít editor efektů")
        button.SetEvent(self.OpenEditor)
        button.Show()
        self.children.append(button)

    def BeginSession(self):
        self.summary.SetText(design.BY_NUMBER[self.backend.Read()[0]][2])

    def OpenEditor(self):
        if self.closeOwner:
            self.closeOwner()
        if self.editor is None:
            self.editor = MetinQueueDesignEditor(self.backend)
        self.editor.Open()

    def Discard(self):
        pass

    def Destroy(self):
        if self.editor:
            self.editor.Destroy()
        for child in self.children:
            child.Hide()
        self.editor, self.page, self.closeOwner = None, None, None
        self.children = []
