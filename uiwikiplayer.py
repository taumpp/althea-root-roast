"""Native player wiki, backed exclusively by a catalogue of the connected game."""
from _weakref import proxy
import app
import dbg
import item
import localeInfo
import net
import nonplayer
import player
import skill
import ui
import random
import uiwheel
import wndMgr
import uiToolTip
import uir1 as R
import uir1tokens as T
import uikit
import WikiRenderTarget
from uicrimsonember import SettingsScrollBar
import uicraftingcontrols as controls
import wikicatalog as M
import wikientry
import ownedcount
import wikitabs as Tabs
import wikiequipment as E
import wikiarticles as A
import wikiitemdetails as D
import wikiworld as W
import wikidungeons as DG
import wikihome as H
import wikiguides as G
import uir1layout as RL
from wikilocale import Text as L, BonusName, GUIDES
WindowDestroy = getattr(ui, 'WindowDestroy', lambda function: function)

TOP = H.ARTICLE_Y
PAGE_SIZE = 12
WHEEL_PIXELS = 32  # Fixed visual distance, independent of article length.
SEARCH_DELAY = 0.15  # Coalesce IME repeats without blocking editing/rendering.
# A LiveCatalogV1 notice reaches every player in the same pulse and every
# request is a full rebuild on the core: refetch only when the player next
# uses the data, spread over this many seconds.
STALE_REFRESH_SPREAD = 20.0
BUSY_RETRY_DELAY = (2.0, 5.0)
BUSY_RETRIES = 12
# Server build expiry; idle transfer timeout stays 20s after begin.
BUILD_WAIT_SECONDS = 60.0
QUEUE_WAIT_SECONDS = 16 * BUILD_WAIT_SECONDS


def TabScope():
    # Read the actual TAB lists when requesting, after interface modules load.
    # Do not copy their IDs or use the old server-wide teleport catalogue.
    import teleportmapdata
    import uidungeontrack
    return M.tab_scope(teleportmapdata.DESTINATIONS, uidungeontrack.dungeonData)


def Decoration(parent, path, x, y, size=None):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.LoadImage(path)
    if size:
        scale = min(float(size)/max(1, image.GetWidth()), float(size)/max(1, image.GetHeight()))
        image.SetScale(scale, scale)
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


def EquippedItems():
    slots = set()
    for source, start_name, count_name in (
            (player, 'EQUIPMENT_SLOT_START', 'EQUIPMENT_PAGE_COUNT'),
            (player, 'NEW_EQUIPMENT_SLOT_START', 'NEW_EQUIPMENT_SLOT_COUNT'),
            (item, 'COSTUME_SLOT_START', 'COSTUME_SLOT_COUNT')):
        start, count = getattr(source, start_name, None), getattr(source, count_name, None)
        if start is not None and count is not None:
            slots.update(range(start, start+count))
    equipment = [(slot, player.GetItemIndex(slot)) for slot in sorted(slots)]
    return [(slot, vnum) for slot, vnum in equipment if vnum]


def ItemName(vnum):
    if item.SelectItemWiki(int(vnum)):
        return item.GetItemName()
    return L('unknown_item')+' '+str(vnum)


def MobName(vnum):
    return nonplayer.GetMonsterName(int(vnum))


def BonusValue(label):
    # Captions select an existing native apply identity, never a balance value.
    from wikilocale import BonusApply
    kind = BonusApply(label)
    mapper = getattr(item, 'GetApplyPoint', None)
    point = mapper(kind) if mapper and kind is not None else None
    return player.GetStatus(point) if point else '-'


def Amount(value):
    return E.amount(value)


class WikiScrollBar(SettingsScrollBar):
    """Keep fractional article position when the thumb rounds to native pixels.

    Dragging still uses the shared bar's OnMove. Wheel/programmatic positioning
    must not lose a small article step on a very long page.
    """
    def SetPos(self,pos,moveEvent=True):
        pos=max(0.0,min(1.0,float(pos)))
        SettingsScrollBar.SetPos(self,pos,False)
        self.curPos=pos
        if moveEvent and not self.lockFlag and self.eventScroll:
            uikit.DispatchScroll(self,lambda:self.eventScroll(*self.eventArgs))


class Search(ui.EditLine):
    def __init__(self, changed):
        ui.EditLine.__init__(self)
        self.changed = changed

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        self.changed()


class RowButton(ui.Window):
    def __init__(self, kit, width, text, callback, selected=False, arrow=None, icon=None):
        ui.Window.__init__(self)
        self.SetSize(width, 26)
        self.callback = callback
        self.selected = selected
        self.hovered = False
        self.pressed = False
        self.band = R.Band(self, 0, 0, width, 25)
        self.icon = Decoration(self, H.ART+'glyph-'+icon+'.png', 5, 0) if icon else None
        inset = 30 if icon else 7
        self.label = R.RowText(self, text, inset, 26, kit.font('text_s'), T.INK)
        R.Fit(self.label, text, width-inset-(21 if arrow is not None else 5))
        self.chevron = None
        if arrow is not None:
            path = R.ChevronPath('down' if arrow else 'right', 'active' if selected else 'normal')
            self.chevron = R.Ops(self, [('image', path, width-17, 9, 9, 9)])
        self.Paint()

    def Paint(self):
        self.band.SetState('selected' if self.selected or self.pressed else ('hover' if self.hovered else 'normal'))
        self.label.SetPackedFontColor(T.IVORY if self.selected or self.hovered else T.INK)

    def OnMouseOverIn(self):
        self.hovered = True
        self.Paint()

    def OnMouseOverOut(self):
        self.hovered = False
        self.pressed = False
        self.Paint()

    def OnMouseLeftButtonDown(self):
        self.pressed = True
        self.Paint()
        return True

    def OnMouseLeftButtonUp(self):
        self.pressed = False
        self.Paint()
        if self.callback:
            self.callback()
        return True


class GradeButton(RowButton):
    def __init__(self, owner, width, label, vnum):
        self.owner = proxy(owner)
        self.vnum = vnum
        RowButton.__init__(self, owner.kit, width, '', lambda v=vnum,r=self.owner:r.OpenItem(v))
        self.label.Hide()
        self.SetSize(width, 22)
        self.band.Resize(0, 0, width, 21)
        owner.ExactText(self, width//2, 4, label, color=T.IVORY, align='center', width=width-4)

    def OnMouseOverIn(self):
        RowButton.OnMouseOverIn(self)
        self.owner.ShowItem(self.vnum)

    def OnMouseOverOut(self):
        RowButton.OnMouseOverOut(self)
        self.owner.HideTooltip()


class HomeLink(RowButton):
    """Exact approved state rasters, with separate native text and hit area."""
    def __init__(self, width, height, title, callback, family, selected=False,
                 icon=None, hint=None, arrow=None):
        ui.Window.__init__(self)
        self.SetSize(width, height)
        self.callback, self.selected = callback, selected
        self.hovered = self.pressed = False
        self.family, self.arrow = family, arrow
        self.image = Decoration(self, H.ART+family+'-normal.png', 0, 0)
        self.state = None
        self.chevron = R.Ops(self) if arrow is not None or hint is not None else None
        self.icon = Decoration(self, H.ART+'glyph-'+icon+'.png', 8, 5) if icon else None
        self.label = R.Text(self, title, 18 if hint is not None else 44,
                            height//2-21 if hint is not None else 11,
                            'Althea Caps:20a' if hint is not None else 'Noto Sans:16a',
                            T.IVORY, valign='top')
        R.Fit(self.label, title, width-50 if hint is not None else width-66)
        self.hint = None
        if hint is not None:
            self.hint = R.Text(self, hint, 18, height//2+5, 'Noto Sans:15a', T.INK_DIM, valign='top')
            R.Fit(self.hint, hint, width-50)
        self.Paint()

    def Paint(self):
        state = 'pressed' if self.pressed else ('selected' if self.selected else ('hover' if self.hovered else 'normal'))
        if state != self.state:
            self.image.LoadImage(H.ART+self.family+'-'+state+'.png')
            self.state = state
        if self.chevron:
            direction = 'down' if self.arrow else 'right'
            x = self.GetWidth()-(25 if self.hint else 20)
            self.chevron.Apply([('image', R.ChevronPath(direction, 'active' if state != 'normal' else 'normal'),
                                  x, self.GetHeight()//2-5, 10, 10)])


class HistoryArrow(RowButton):
    def __init__(self, direction, callback):
        ui.Window.__init__(self)
        self.SetSize(28, 24)
        self.callback, self.direction = callback, direction
        self.selected = self.hovered = self.pressed = False
        self.chevron = R.Ops(self)
        self.Paint()

    def Paint(self):
        self.chevron.Apply([('image', R.ChevronPath(self.direction, 'active' if self.hovered or self.pressed else 'normal'),
                              9, 7, 10, 10)])


class ItemIcon(ui.Window):
    def __init__(self, owner, vnum, count=0, size=32, height=None):
        ui.Window.__init__(self)
        self.owner = proxy(owner)
        self.vnum = int(vnum)
        self.variants = None
        self.extraLines = []
        self.recommendation = None
        self.inventorySlot = None
        height = size if height is None else height
        self.SetSize(size, height)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        try:
            # SelectItem alone silently selects a fallback icon on missing data.
            if not item.SelectItemWiki(self.vnum):
                raise RuntimeError('missing native item')
            self.icon.LoadImage(item.GetIconImageFileName())
            w, h = self.icon.GetWidth(), self.icon.GetHeight()
            scale = min(float(size) / max(1, w), float(height) / max(1, h), 1.0)
            self.icon.SetScale(scale, scale)
            self.icon.SetPosition(int((size-w*scale)//2), int((height-h*scale)//2))
            self.icon.Show()
        except RuntimeError:
            pass
        self.count = None
        if count and str(count).isdigit():
            # The same native digit sprites and inset as target-info drop slots.
            self.count = ui.NumberLine()
            self.count.SetParent(self)
            self.count.AddFlag('not_pick')
            self.count.SetHorizontalAlignRight()
            self.count.SetNumber(str(count))
            self.count.SetPosition(size-4, height-10)
            self.count.Show()
        elif count:
            # Native digits omit punctuation: retain grouped drop ranges verbatim.
            self.count = R.Text(self, str(count), size-1, height-13, 'Tahoma:12ba', T.IVORY, align='right', valign='top')
            self.count.SetOutline()
            self.count.AddFlag('not_pick')
        self.Show()

    def OnMouseOverIn(self):
        if self.inventorySlot is not None:
            self.owner.ShowInventoryItem(self.inventorySlot)
        else:
            self.owner.ShowItem(self.vnum, self.variants, self.extraLines, self.recommendation)

    def OnMouseOverOut(self):
        self.owner.HideTooltip()

    def OnMouseLeftButtonUp(self):
        self.owner.OpenItem(self.vnum)
        return True


class PortraitButton(RowButton):
    def __init__(self, kit, width, text, image, callback, selected=False):
        RowButton.__init__(self, kit, width, '', callback, selected)
        self.SetSize(width, 49)
        self.band = R.Band(self, 0, 0, width, 49)
        self.portrait = Decoration(self, image, 2, 2)
        self.label = R.Text(self, text, 49, 16, 'Noto Sans:14a', T.INK_DIM, valign='top')
        R.Fit(self.label, text, width-51)
        self.Paint()


class CategoryCard(RowButton):
    def __init__(self, kit, width, title, count, vnum, callback):
        RowButton.__init__(self, kit, width, '', callback)
        self.SetSize(width, 72)
        self.band.Resize(0, 0, width, 72)
        self.label.SetText(title)
        self.label.SetPosition(51, 16)
        R.Fit(self.label, title, width-57)
        self.countLabel = R.Text(self, L('count') % count, 51, 37,
                                 kit.font('text_s'), T.INK_DIM, valign='top')
        self.itemImage = None
        if item.SelectItemWiki(vnum):
            self.itemImage = Decoration(self, item.GetIconImageFileName(), 2, 8, 36)
        self.Paint()


class MoneyCell(ui.Window):
    def __init__(self, kit, width, value):
        ui.Window.__init__(self)
        self.kit, self.value = kit, M.number(value)
        self.SetSize(width,21)
        self.label = R.Text(self, Amount(value), width//2,4,'Noto Sans:13a',T.INK,align='center',valign='top')
        R.Fit(self.label,Amount(value),width-4)

    def OnMouseOverIn(self):
        R.ShowHint(self.kit,self,format(self.value,',').replace(',',' ')+' Yang',watch=True)

    def OnMouseOverOut(self):
        R.HideHint(self)


class SourceButton(RowButton):
    def __init__(self,kit,width,title,hint,event):
        RowButton.__init__(self,kit,width,title,event)
        self.kit,self.sourceTitle,self.sourceHint=kit,title,hint

    def OnMouseOverIn(self):
        RowButton.OnMouseOverIn(self)
        R.ShowHint(self.kit,self,self.sourceTitle,self.sourceHint,watch=True)

    def OnMouseOverOut(self):
        RowButton.OnMouseOverOut(self)
        R.HideHint(self)


class EncyclopediaofGame(ui.Window):
    def _Measure(self):
        width, height = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        self.compact, self.windowWidth, self.windowHeight = H.Measure(width, height)
        self.sideWidth = H.SIDE
        self.pageWidth = self.windowWidth-H.ARTICLE_X-12
        self.viewHeight = self.windowHeight-TOP-12
        self.sideViewHeight = self.windowHeight-H.NAV_Y-12

    def __init__(self):
        # ui.Window.__init__ calls our Hide before creating any child windows.
        self.Initialize()
        ui.Window.__init__(self)
        self.receiver = M.Receiver(ui.__mem_func__(self.Send), TabScope, deferred=True,
                                   name_provider=ItemName, catalog_setup=ui.__mem_func__(self.LocalizeCatalog))
        M.BindDungeonReceiver(self.receiver)
        # Data ownership is independent of the hidden presentation. The first
        # Open builds the unchanged window; login/refresh builds no widgets.

    def Initialize(self):
        self._Measure()
        self.widgets = []
        self.breadcrumb = None
        self.content = []
        self.sidebar = []
        self.receiver = None
        self.toolTip = None
        self.skillToolTip = None
        self.kit = None
        self.chrome = None
        self.board = None
        self.viewport = None
        self.body = None
        self.scroll = None
        self.sideview = None
        self.sidebody = None
        self.sidescroll = None
        self.search = None
        self.status = None
        self.refreshButton = None
        self.navGroup = None
        self.mode = 'overview'
        self.category = None
        self.equipmentSubtype = None
        self.selectedJob = None
        self.itemVnum = None
        self.itemSourcesOnly = False
        self.recipeSelected = None
        self.detailPane, self.detailKind, self.detailOption = 'bonuses', None, 0
        self.alchemyChoice = (None, None, None)
        self.alchemyOverview = False
        self.detailLists = []
        self.dungeonStatusWidgets = []
        self.dungeonAnchors = {}
        self.sectionTabs = []
        self.dungeonStatus = {}
        self.dungeonStatusAt = {}
        self.dungeonPending = None
        self.dungeonRequestAt = -100
        self.dungeonPaintAt = -100
        self.dungeonLootPage = 0
        self.dungeonLootBoss = None
        self.sourceExpanded = None
        self.restoreScroll = None
        self.guide = None
        self.location = None
        self.opened = None
        self.extraSources = False
        self.lootGroup = None
        self.page = 0
        self.searchDue = None
        self.bodyHeight = self.viewHeight
        self.sideHeight = 1
        self.seenRevision = 0
        self.requestAt = 0
        self.requestStarted = 0
        self.catalogRequested = False
        self.catalogDemand = False
        self.gameReady = False
        self.loadingLabel = None
        self.loadingTrack = None
        self.loadingFill = None
        self.loadingPercent = -1
        self.staleDue = 0
        self.retryAt = 0
        self.retryKeep = False
        self.busyRetries = 0
        self.lastPersonal = 0
        self.history = []
        self.historyIndex = -1
        self.look = None
        self.renderIndex = None
        self.modelPreviews = []
        self.drawRevision = 0
        self.queueNoticed = False
        self.buildStarted = None
        self.worldKind = 'boss'
        self.worldMob = None
        self.worldChoosingMap = False
        self.worldDropPages, self.worldMapPages = {}, {}
        self.pendingItem = None
        self.pendingBoss = None
        self.dewFamily = None
        self.meteorVnum = None
        self.destroyed = False

    def _Keep(self, widget, parent, x, y, collection=None):
        widget.SetParent(parent)
        widget.SetPosition(int(x), int(y))
        (self.widgets if collection is None else collection).append(widget)
        widget.Show()
        return widget

    def _Build(self):
        if self.toolTip is None:
            self.toolTip = uiToolTip.ItemToolTip()
            self.toolTip.Hide()
        if self.skillToolTip is None:
            self.skillToolTip = uiToolTip.SkillToolTip()
            self.skillToolTip.Hide()
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(self.windowWidth, self.windowHeight)
        self.SetPosition((wndMgr.GetScreenWidth()-self.windowWidth)//2,
                         max(8, (wndMgr.GetScreenHeight()-96-self.windowHeight)//2))
        self.kit = R.Kit()
        self.look = R.UseR1()
        if self.look:
            self.chrome = R.Chrome(self, self.kit, self.windowWidth, self.windowHeight, L('title'), on_close=ui.__mem_func__(self.Close))
        else:
            self.board = self._Keep(ui.BoardWithTitleBar(), self, 0, 0)
            self.board.SetSize(self.windowWidth, self.windowHeight)
            self.board.SetTitleName(L('title'))
            self.board.SetCloseEvent(ui.__mem_func__(self.Close))
        self._Rect(self, 4, 34, self.sideWidth-4, self.windowHeight-38, T.SIDE, self.widgets)
        self._Rect(self, self.sideWidth, 34, 1, self.windowHeight-46, T.LINE, self.widgets)
        self.search = Search(ui.__mem_func__(self.Filter))
        field = R.Field(self, self.kit, 12, 40, H.NAV_WIDTH, L('search_short'), edit=self.search,
                        max_len=60, lead=16, font='Noto Sans:14a')
        self.widgets.append(field)
        field.searchIcon = R.Ops(field, [('image', 'icon/search_normal.png', 8, 7, 10, 10)])
        self.search.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
        self._Keep(HistoryArrow('left', ui.__mem_func__(self.Back)), self, 12, 73)
        self._Keep(HistoryArrow('right', ui.__mem_func__(self.Next)), self, 44, 73)
        self.breadcrumb = R.Text(self, L('overview'), 89, 75, 'Noto Sans:15a', T.IVORY, valign='top')
        self.widgets.append(self.breadcrumb)
        self.sideview = self._Keep(ui.Window(), self, 12, H.NAV_Y)
        self.sideview.SetSize(H.NAV_WIDTH, self.sideViewHeight)
        self.sideview.EnableScissorRect()
        self.sidebody = self._Keep(ui.Window(), self.sideview, 0, 0)
        self.sidebody.SetSize(H.NAV_WIDTH, self.sideViewHeight)
        self.sidescroll = self._Keep(WikiScrollBar(), self, self.sideWidth-7, H.NAV_Y)
        self.sidescroll.SetScrollBarSize(self.sideViewHeight)
        self.sidescroll.SetScrollEvent(ui.__mem_func__(self.ScrollSide))
        uiwheel.Bind(self.sidescroll, self.sideview, ui.__mem_func__(self.SideWheelStep))
        self.viewport = self._Keep(ui.Window(), self, H.ARTICLE_X, TOP)
        self.viewport.SetSize(self.pageWidth, self.viewHeight)
        self.viewport.EnableScissorRect()
        self.body = self._Keep(ui.Window(), self.viewport, 0, 0)
        self.body.SetSize(self.pageWidth, self.viewHeight)
        self.scroll = self._Keep(WikiScrollBar(), self, self.windowWidth-10, TOP)
        self.scroll.SetScrollBarSize(self.viewHeight)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.Scroll))
        uiwheel.Bind(self.scroll, self.viewport, ui.__mem_func__(self.BodyWheelStep))
        self.status = self._Text(self, H.ARTICLE_X, self.windowHeight-27, '', T.INK_DIM, self.widgets,
                                 small=True, width=self.pageWidth-106)
        self.refreshButton = self._Button(self, self.windowWidth-100, self.windowHeight-32, 84,
                                         L('refresh'), self.Refresh, self.widgets)
        self.UpdateBreadcrumb()
        # Open draws once after Show so model visibility is correct.

    def PageName(self, state=None):
        if state is None and self.mode == 'item' and self.itemVnum:
            return M.family_name(ItemName(self.itemVnum))
        mode, category, guide, location = state or (self.mode, self.category, self.guide, self.location)
        if category:
            return L(category) if mode == 'chests' else category
        if guide:
            return next((g[2] for g in GUIDES if g[0] == guide), L(mode))
        if location and self.receiver and self.receiver.catalog:
            return self.receiver.catalog.MapName(location)
        return L(mode)

    def UpdateBreadcrumb(self):
        if self.breadcrumb:
            R.Fit(self.breadcrumb, self.PageName(), H.NAV_WIDTH-77)

    def _Clear(self, collection):
        for widget in collection:
            widget.Hide()
        del collection[:]

    def _Rect(self, parent, x, y, w, h, color, collection=None):
        bar = self._Keep(ui.Bar(), parent, x, y, self.content if collection is None else collection)
        bar.SetSize(w, h)
        bar.SetColor(controls.packed_color(color))
        bar.AddFlag('not_pick')
        return bar

    def _Text(self, parent, x, y, text, color=T.INK, collection=None, small=False, title=False, width=None, hero=False):
        font = self.kit.font('title' if title or hero else ('text_s' if small else 'text'))
        if hero:
            family, unused, spec = font.rpartition(':')
            suffix = ''.join(c for c in spec if not c.isdigit())
            font = family+':'+str(uikit.FontCell(font)+(4 if self.compact else 8))+suffix
        text = R.WordGap(str(text), font)
        line = R.Text(parent, str(text), int(x), int(y), font, R.SignedColor(color), valign='top')
        (self.content if collection is None else collection).append(line)
        if width is not None:
            R.Fit(line, str(text), int(width))
        return line

    def _Button(self, parent, x, y, width, text, event, collection=None, selected=False, arrow=None, icon=None):
        callback = ui.__mem_func__(event) if hasattr(event, '__self__') else event
        button = self._Keep(RowButton(self.kit, width, text, callback, selected, arrow, icon),
                            parent, x, y, self.content if collection is None else collection)
        return button

    def _Icon(self, parent, x, y, vnum, count=0, size=32, height=None):
        return self._Keep(ItemIcon(self, vnum, count, size, height), parent, x, y, self.content)

    def _Rule(self, y):
        self._Rect(self.body, 0, y, self.pageWidth-10, 1, T.LINE)
        return y+(9 if self.compact else 13)

    def _Heading(self, y, text):
        self._Text(self.body, 0, y, text, T.IVORY, title=True, width=self.pageWidth-10)
        return y+31

    def _Flow(self, y, text, width=None, x=0, color=T.INK_DIM):
        width = self.pageWidth-20 if width is None else width
        line, words = '', str(text).split()
        probe = ui.TextLine()
        probe.SetFontName(self.kit.font('text_s'))
        for word in words:
            candidate = (line+' '+word).strip()
            probe.SetText(candidate)
            if line and probe.GetTextSize()[0] > width:
                self._Text(self.body, x, y, line, color, small=True)
                y += 19
                line = word
            else:
                line = candidate
        if line:
            self._Text(self.body, x, y, line, color, small=True)
            y += 19
        return y+7

    def _PageTitle(self, y, title, eyebrow):
        self._Text(self.body, 0, y+5, eyebrow, T.INK_DIM, small=True)
        self._Text(self.body, 0, y+(20 if self.compact else 25), title, T.IVORY, hero=True, width=self.pageWidth-12)
        return self._Rule(y+(49 if self.compact else 61))

    def _Steps(self, y, steps):
        columns = 3 if self.pageWidth >= 680 else 2
        cell = (self.pageWidth-20)//columns
        for start in range(0, len(steps), columns):
            bottom = y
            for col, step in enumerate(steps[start:start+columns]):
                x = col*cell
                self._Text(self.body, x, y, '%02d' % (start+col+1), T.IVORY, hero=True)
                self._Rect(self.body, x, y+33, cell-18, 1, T.LINE)
                bottom = max(bottom, self._Flow(y+44, step, width=cell-24, x=x))
            y = bottom+18
        return y

    def _TableColumns(self):
        return (8, int(self.pageWidth*.46), int(self.pageWidth*.64), int(self.pageWidth*.81))

    def _PersonalRow(self, y, label, have, need, ready=None, label_x=8):
        columns = self._TableColumns()
        values = (label, str(have), str(need), L('neutral') if ready is None else L('ready' if ready else 'missing'))
        for index, (x, value) in enumerate(zip(columns, values)):
            end = columns[index+1] if index < 3 else self.pageWidth
            color = T.INK
            if index in (1, 3):
                # the green / red of every item price (root/ownedcount.py)
                color = T.INK_DIM if ready is None else (ownedcount.GREEN if ready else ownedcount.SHORT)
            if index == 0:
                x = label_x
            self._Text(self.body, x, y, value, color, small=index == 3, width=end-x-8)
        return y+27

    def _TableHeader(self, y, first='readiness'):
        self._Rect(self.body, 0, y-4, self.pageWidth-10, 27, 0xff242120)
        for x, key in zip(self._TableColumns(), (first, 'have', 'need', 'status')):
            self._Text(self.body, x, y, L(key), T.IVORY, small=True)
        return y+30

    def Send(self, command):
        if not self.destroyed:
            net.SendChatPacket(command)

    def Feed(self, action, *args):
        if self.destroyed or not self.receiver or not self.catalogRequested:
            return
        if not args or M.number(args[0]) != self.receiver.nonce:
            return
        if action == 'queued':
            if (len(args) == 2 and self.buildStarted is None and 1 <= M.number(args[1]) <= 16 and self.receiver.requested and
                    self.receiver.pending is None and not self.receiver.error and
                    0 <= app.GetTime()-self.requestStarted <= QUEUE_WAIT_SECONDS):
                self.queueNoticed = True
                self.requestAt = app.GetTime()
            return
        if action == 'building':
            if (getattr(self, 'queueNoticed', False) and self.buildStarted is None and len(args) == 1 and
                    self.receiver.requested and self.receiver.pending is None and not self.receiver.error and
                    0 <= app.GetTime()-self.requestStarted <= QUEUE_WAIT_SECONDS):
                self.buildStarted = app.GetTime()
            # Only an active matching pre-begin request may extend this deadline.
            # Background refresh keeps the installed catalogue visible as before.
            if (len(args) == 1 and self.receiver.requested and
                    self.receiver.pending is None and not self.receiver.error and
                    0 <= app.GetTime()-(self.buildStarted if self.buildStarted is not None else self.requestStarted) <= BUILD_WAIT_SECONDS):
                self.requestAt = app.GetTime()
            return
        if action.startswith('prep_'):
            DG.feed(self, action, args)
            return
        before = len(self.receiver.pending['parts']) if self.receiver.pending else -1
        previousError = self.receiver.error
        background = self.receiver.background
        self.receiver.Feed(action, *args)
        after = len(self.receiver.pending['parts']) if self.receiver.pending else -1
        if after > before:
            self.requestAt = app.GetTime()
            percent = after*100//self.receiver.pending['count']
            self.LoadingProgress(percent)
        if self.receiver.revision != self.seenRevision:
            self.CatalogReady(background)
        if self.receiver.error and self.receiver.error != previousError:
            dbg.TraceError('WIKI_CATALOG_V1 failed reason='+self.receiver.error)
            if self.receiver.error == 'busy' and self.busyRetries < BUSY_RETRIES:
                # The core is serving its 16 transfers; ask again shortly.
                self.busyRetries += 1
                self.receiver.error = ''
                self.retryAt = app.GetTime()+random.uniform(*BUSY_RETRY_DELAY)
                self.requestAt = 0
            self.UpdateStatus()
            self.Draw()

    def LocalizeCatalog(self, catalog):
        wikientry.LocalizeCatalog(catalog)

    def CatalogReady(self, background):
        self.seenRevision = self.receiver.revision
        drawn = self.drawRevision
        self.busyRetries = 0
        self.UpdateStatus()
        if self.IsShow() and self.pendingItem is not None:
            vnum, self.pendingItem = self.pendingItem, None
            self.OpenItem(vnum)
        elif self.IsShow() and self.pendingBoss is not None:
            boss, self.pendingBoss = self.pendingBoss, None
            self.OpenDungeon(boss)
        self.UpdateBreadcrumb()
        if self.IsShow() and drawn == self.drawRevision:
            self.DrawSidebar()
            if background:
                # The reader stays where he was; only the data are new.
                self.restoreScroll = self.scroll.GetPos()
            self.Draw()
        dbg.TraceError('WIKI_CLIENT_WORK_V1 max_step_us=%d pumps=%d steps=%d step_limited=%d' % (
            self.receiver.max_work_us, self.receiver.work_pumps,
            self.receiver.work_steps, self.receiver.step_limited_pumps))
        for phase in ('decode', 'json', 'graph', 'names'):
            if phase in self.receiver.phase_seconds:
                dbg.TraceError('WIKI_CLIENT_PHASE_V1 phase=%s seconds=%.3f' % (
                    phase, self.receiver.phase_seconds[phase]))
        dbg.TraceError('WIKI_CATALOG_V1 ready maps=%d items=%d seconds=%.2f shown=%d' % (
            len(self.receiver.catalog.maps), len(self.receiver.catalog.items),
            app.GetTime()-self.requestStarted, bool(self.IsShow())))

    def LoadingProgress(self, percent):
        if percent == self.loadingPercent:
            return
        self.loadingPercent = percent
        text = ''
        self.UpdateStatus()
        if self.loadingLabel:
            self.loadingLabel.SetText(text)
        if self.loadingFill:
            self.loadingFill.SetSize(max(1, (self.pageWidth-24)*percent//100), 3)

    def Refresh(self):
        self.busyRetries = 0
        self.retryKeep = bool(self.receiver and self.receiver.catalog)
        self._Request(self.retryKeep)

    def _Request(self, keep):
        if self.destroyed or not self.gameReady or not self.NetworkReady():
            return
        self.catalogRequested = True
        self.staleDue = self.retryAt = 0
        self.retryKeep = keep
        self.receiver.Request(keep)
        if not self.receiver.background:
            self.HideTooltip()
        self.dungeonStatus.clear()
        self.dungeonStatusAt.clear()
        self.dungeonPending = None
        self.dungeonRequestAt = -100
        self.requestAt = self.requestStarted = app.GetTime()
        self.queueNoticed = False
        self.buildStarted = None
        self.loadingPercent = -1
        dbg.TraceError('WIKI_CATALOG_V1 request')
        self.UpdateStatus()
        if self.receiver.background:
            return  # The pages keep the installed catalogue until the new one is complete.
        self.DrawSidebar()
        self.Draw()

    def Prefetch(self):
        self.catalogDemand = True
        if self.gameReady and not self.catalogRequested:
            self.Refresh()

    def NetworkReady(self):
        # Loading.__RecvPlayerPoints also dispatches RefreshStatus. Only the
        # native predicate proves SendChatPacket will accept this request.
        ready = getattr(net, 'IsGamePhase', None)
        return bool(ready and ready())

    def OnGameReady(self):
        if not self.NetworkReady():
            return
        self.gameReady = True
        if self.catalogDemand:
            self.Prefetch()

    def UpdateStatus(self):
        if not self.status:
            return
        text = ''
        if self.mode == 'overview' and not (self.search and self.search.GetText()) and not self.receiver.error:
            self.status.SetText('')
            return
        if self.receiver and self.receiver.error:
            text = L('unavailable')
        elif self.StaleShown():
            text = L('stale_refreshing') if self.StaleRefreshing() else L('stale')
        self.status.SetText(text)

    def StaleShown(self):
        # The pages on screen were built before the server changed its data.
        return bool(self.receiver and self.receiver.stale and self.receiver.catalog)

    def StaleRefreshing(self):
        return bool(self.staleDue or self.retryAt or (self.receiver and self.receiver.background))

    def OnLiveCatalog(self, *args):
        """LiveCatalogV1 <schema> <catalog id> <generation>: only a mark. A
        request here would come from every player at once."""
        if self.destroyed or not self.receiver or len(args) < 3:
            return
        schema, catalog, generation = (M.number(value) for value in args[:3])
        if schema != 1 or catalog <= 0 or generation <= 0:
            return
        shown = self.StaleShown()
        self.receiver.MarkStale()
        if self.StaleShown() and not shown and self.IsShow():
            # Same pages at the same place, now with the status line and the refresh button.
            self.restoreScroll = self.scroll.GetPos()
            self.Draw()
        else:
            self.UpdateStatus()

    def UseCatalog(self):
        """The player opened a window that reads the catalogue (wiki, teleport).
        A stale catalogue is refetched once, after a random delay, and stays
        readable until its replacement is complete."""
        if self.destroyed or not self.receiver:
            return
        self.Prefetch()
        if not self.receiver.stale:
            return
        if self.staleDue or self.retryAt or self.receiver.requested:
            return
        self.busyRetries = 0
        self.staleDue = app.GetTime()+random.uniform(0.0, STALE_REFRESH_SPREAD)
        self.UpdateStatus()

    def InvalidateCatalog(self):
        self.Close()
        self.receiver.catalog = None
        self.receiver.pending = None
        self.receiver.CancelWork()
        self.receiver.error = ''
        self.receiver.requested = self.receiver.background = self.receiver.stale = False
        self.staleDue = self.retryAt = 0
        self.retryKeep = False
        self.busyRetries = 0
        # Preserve nonce monotonicity so delayed old-session frames cannot win.
        self.catalogRequested = False
        self.catalogDemand = False
        self.gameReady = False
        self.requestAt = 0
        self.loadingPercent = -1
        self.pendingItem = self.pendingBoss = None
        self.UpdateStatus()

    def GuideGroup(self, guide):
        if guide[1] == L('equipment'):
            return 'equipment'
        if guide[1] == L('companions'):
            return 'companions'
        if guide[1] == L('crafting'):
            return 'crafting'
        if guide[1] == L('world'):
            return 'maps'
        return 'progression'

    def SelectGroup(self, group):
        expanded = self.navGroup != group
        self.navGroup = group if expanded else None
        if group == 'chests':
            self.Navigate('chests', category='boss_chests', expand=False)
        elif group in ('equipment', 'dungeons', 'maps'):
            self.Navigate(group, expand=False)
        else:
            self.Navigate('systems', expand=False)

    def DrawSidebar(self):
        if not self.sidebody:
            return
        offset = max(0, -self.sidebody.GetLocalPosition()[1])
        self._Clear(self.sidebar)
        owner = proxy(self)
        self._Keep(HomeLink(H.NAV_WIDTH, H.NAV_HEIGHT, L('overview'),
                            lambda r=owner: r.Navigate('overview'), 'nav-188x38',
                            selected=self.mode == 'overview', icon='overview'),
                   self.sidebody, 0, 0, self.sidebar)
        y = H.GROUP_Y-H.NAV_Y
        catalog = self.receiver.catalog if self.receiver else None
        for group, label, icon in H.GROUPS:
            opened = self.navGroup == group
            active = (self.mode == group or
                      (group == 'chests' and self.mode == 'equipment' and self.category == L('chests')) or
                      (self.mode == 'systems' and self.navGroup == group))
            if group == 'equipment' and self.category == L('chests'):
                active = False
            self._Keep(HomeLink(H.NAV_WIDTH, H.NAV_HEIGHT, L(label),
                                lambda g=group, r=owner: r.SelectGroup(g), 'nav-188x38',
                                selected=active, icon=icon, arrow=opened), self.sidebody, 0, y, self.sidebar)
            y += H.NAV_HEIGHT+H.NAV_GAP
            if not opened:
                continue
            if group == 'equipment' and catalog:
                categories = [L(g) for g in E.categories(catalog)]
                for category in categories:
                    self._Button(self.sidebody, 8, y, H.NAV_WIDTH-12, category,
                                 lambda c=category, r=owner: r.Navigate('equipment', category=c), self.sidebar,
                                 selected=self.category == category)
                    y += 27
            if group == 'dungeons' and catalog:
                for map_id, row in sorted(catalog.maps.items(), key=lambda r: M.number(r[1]['level'])):
                    if not M.number(row.get('boss')):
                        continue
                    self._Button(self.sidebody, 8, y, H.NAV_WIDTH-12, row['name'],
                                 lambda m=map_id, r=owner: r.Navigate('dungeons', location=m), self.sidebar,
                                 selected=self.mode == 'dungeons' and self.location == map_id)
                    y += 27
            if group == 'chests':
                for category in A.chest_categories(catalog):
                    self._Button(self.sidebody, 8, y, H.NAV_WIDTH-12, L(category),
                                 lambda c=category, r=owner: r.Navigate('chests', category=c), self.sidebar,
                                 selected=self.mode == 'chests' and self.category == category)
                    y += 27
            if group == 'maps':
                for kind in ('boss', 'metin'):
                    self._Button(self.sidebody, 8, y, H.NAV_WIDTH-12, L('detail_'+kind),
                                 lambda k=kind, r=owner: r.OpenWorld(k), self.sidebar,
                                 selected=self.mode == 'maps' and self.worldKind == kind)
                    y += 27
            for guide in GUIDES:
                if self.GuideGroup(guide) == group:
                    self._Button(self.sidebody, 8, y, H.NAV_WIDTH-12, guide[2],
                                 lambda g=guide[0], r=owner: r.Navigate('systems', guide=g), self.sidebar,
                                 selected=self.guide == guide[0])
                    y += 27
        self.sideHeight = max(self.sideViewHeight, y)
        self.sidebody.SetSize(H.NAV_WIDTH, self.sideHeight)
        self._LayoutScroll(self.sidescroll, self.sideHeight, self.sideViewHeight)
        self.sidescroll.SetPos(min(1.0,float(offset)/max(1,self.sideHeight-self.sideViewHeight)))
        self.ScrollSide()

    def CategoryName(self, category):
        kind, sub = category
        if kind == item.ITEM_TYPE_WEAPON:
            for symbol, label in (('SWORD', 'sword'), ('DAGGER', 'dagger'), ('BOW', 'bow'), ('TWO_HANDED', 'twohand'),
                                  ('BELL', 'bell'), ('FAN', 'fan'), ('MOUNT_SPEAR', 'mount_weapon'),
                                  ('ARROW','arrows'), ('QUIVER','quivers')):
                if sub == getattr(item, 'WEAPON_'+symbol, -1):
                    return L(label)
            return L('weapon')
        if kind == item.ITEM_TYPE_ARMOR:
            for symbol, label in (('BODY', 'body_armor'), ('HEAD', 'helmet'), ('SHIELD', 'shield'), ('WRIST', 'bracelet'),
                                  ('FOOTS', 'shoes'), ('NECK', 'necklace'), ('EAR', 'earring'), ('PENDANT', 'talisman'),
                                  ('TALISMAN_HEART', 'talisman_heart'), ('GLOVE', 'glove')):
                if sub == getattr(item, 'ARMOR_'+symbol, -1):
                    return L(label)
        if kind == getattr(item,'ITEM_TYPE_MOUNT_EQUIPMENT',None):
            for symbol,label in (('SADDLE','mount_saddle'),('HORSESHOES','mount_horseshoes'),
                                  ('BRIDLE','mount_bridle'),('ARMOR','mount_armor'),('PRISMATIC_CORE','mount_core')):
                if sub == getattr(item,'MOUNT_EQUIPMENT_'+symbol,None):
                    return L(label)
            return L('mount_equipment')
        if kind == getattr(item, 'ITEM_TYPE_BELT', -1):
            return L('belt')
        if kind == getattr(item, 'ITEM_TYPE_COSTUME', -1):
            for symbol,label in (('BODY','costume_body'),('HAIR','costume_hair'),('MOUNT','costume_mount'),
                                  ('ACCE','costume_sash'),('WEAPON','costume_weapon'),('AURA','costume_aura'),
                                  ('PET','costume_pet'),('EFFECT_WEAPON','costume_weapon_effect'),
                                  ('EFFECT_ARMOR','costume_armor_effect'),('ACCE_SKIN','costume_sash_skin')):
                if sub == getattr(item,'COSTUME_TYPE_'+symbol,None):
                    return L(label)
            return L('costume')
        for symbols, label in (
                (('GIFTBOX', 'TREASURE_BOX', 'GACHA'), 'chests'),
                (('MATERIAL', 'RESOURCE'), 'materials'),
                (('METIN',), 'spirit_stones'),
                (('SKILLBOOK', 'SKILLFORGET'), 'books'),
                (('DS', 'SPECIAL_DS'), 'dragon_stones'),
                (('BLEND',), 'dews'),
                (('USE', 'AUTOUSE'), 'consumables'),
                (('ROD', 'PICK'), 'tools'),
                (('FISH',), 'fish'),
                (('PET',), 'companions'),
                (('RING', 'UNIQUE'), 'rings')):
            if any(kind == getattr(item, 'ITEM_TYPE_'+symbol, -1) for symbol in symbols):
                return L(label)
        return L('other')

    def State(self):
        return dict(mode=self.mode, category=self.category, guide=self.guide, location=self.location, page=self.page,
                    job=self.selectedJob, subtype=self.equipmentSubtype, item=self.itemVnum,
                    sources_only=self.itemSourcesOnly, recipe=self.recipeSelected,
                    detail=(self.detailPane,self.detailKind,self.detailOption),
                    alchemy=self.alchemyChoice, alchemy_overview=self.alchemyOverview,
                    world=(self.worldKind,self.worldMob,self.worldChoosingMap,dict(self.worldDropPages),dict(self.worldMapPages)),
                    scroll=self.scroll.GetPos() if self.scroll else 0,
                    side_scroll=self.sidescroll.GetPos() if self.sidescroll else 0,
                    query=self.search.GetText() if self.search else '')

    def SaveHistory(self):
        if 0 <= self.historyIndex < len(self.history):
            self.history[self.historyIndex] = self.State()

    def EquipmentGroup(self):
        return next((g for g in E.GROUPS if L(g) == self.category), None)

    def Navigate(self, mode, category=None, guide=None, location=None, record=True, expand=True,
                 targetItem=None, restore=None):
        self.HideTooltip()
        if record:
            self.SaveHistory()
        subtype = None
        catalog = self.receiver.catalog if self.receiver else None
        if (mode == 'equipment' and category and catalog and category != L('chests')
                and category not in [L(g) for g in E.GROUPS]):
            for key in catalog.families:
                group = E.group(key[1:])
                if group and category == self.CategoryName(key[1:]) and category != L(group):
                    category, subtype = L(group), key[1:]
                    break
        if (not restore and mode != 'item' and self.historyIndex >= 0 and not (self.search and self.search.GetText()) and
                (self.mode,self.category,self.guide,self.location,self.itemVnum)==(mode,category,guide,location,targetItem) and
                (subtype is None or subtype==self.equipmentSubtype)):
            self.DrawSidebar()
            self.Draw()
            self.SaveHistory()
            return
        self.restoreScroll = 0
        self.mode, self.category, self.guide, self.location = mode, category, guide, location
        self.equipmentSubtype, self.itemVnum = subtype, targetItem
        self.itemSourcesOnly, self.recipeSelected = False, None
        self.detailPane, self.detailKind, self.detailOption = 'bonuses', None, 0
        self.worldMob, self.worldChoosingMap = None, False
        self.worldDropPages, self.worldMapPages = {}, {}
        if mode == 'maps' and location is not None and catalog:
            if not W.entries(catalog, self.worldKind, location):
                other = 'metin' if self.worldKind == 'boss' else 'boss'
                if W.entries(catalog, other, location):
                    self.worldKind = other
        if mode == 'overview':
            self.navGroup = None
        elif expand:
            if mode == 'equipment':
                self.navGroup = 'chests' if category == L('chests') else 'equipment'
            elif mode in ('dungeons', 'maps', 'chests'):
                self.navGroup = mode
            elif guide:
                article = next((row for row in GUIDES if row[0] == guide), None)
                self.navGroup = self.GuideGroup(article) if article else 'progression'
            else:
                self.navGroup = 'progression'
        self.opened = None
        self.extraSources = False
        self.lootGroup = None
        self.page = 0
        if self.search:
            self.search.SetText('')
        if restore:
            self.page = restore.get('page',0)
            self.selectedJob, self.equipmentSubtype, self.itemVnum = restore['job'], restore['subtype'], restore['item']
            self.itemSourcesOnly, self.recipeSelected = restore['sources_only'], restore['recipe']
            self.detailPane,self.detailKind,self.detailOption = restore.get('detail',('bonuses',None,0))
            self.alchemyChoice = restore.get('alchemy', self.alchemyChoice)
            self.alchemyOverview = restore.get('alchemy_overview', False)
            world = restore.get('world', ('boss',None,False,{},{}))
            self.worldKind,self.worldMob,self.worldChoosingMap = world[:3]
            self.worldDropPages,self.worldMapPages = dict(world[3]),dict(world[4])
            self.restoreScroll = restore['scroll']
            self.search.SetText(restore['query'])
        self.UpdateBreadcrumb()
        self.DrawSidebar()
        self.Draw()
        if restore:
            self.sidescroll.SetPos(restore['side_scroll'])
            self.ScrollSide()
        if record:
            self.history = self.history[:self.historyIndex+1] + [self.State()]
            self.historyIndex = len(self.history)-1

    def OpenWorld(self, kind):
        if self.mode != 'maps':
            self.Navigate('maps')
        W.select_kind(self, kind)

    def RestoreHistory(self):
        state = self.history[self.historyIndex]
        self.Navigate(state['mode'], state['category'], state['guide'], state['location'],
                      record=False, restore=state)

    def Back(self):
        if self.historyIndex > 0:
            self.SaveHistory()
            self.historyIndex -= 1
            self.RestoreHistory()

    def Next(self):
        if self.historyIndex+1 < len(self.history):
            self.SaveHistory()
            self.historyIndex += 1
            self.RestoreHistory()

    def LoadGuidePage(self, *unused):
        self.Navigate('overview')

    def RunHistoryArgument(self, argument):
        # Existing chat/item hyperlink compatibility. Unknown legacy article
        # IDs lead to the overview, never to a packaged gameplay table.
        parts = str(argument).replace('#', ':').split(':')
        vnum = M.number(parts[1] if len(parts) > 2 and parts[0] == 'NEW' else parts[-1])
        # Interface opens the shared window after resolving a chat hyperlink.
        # Preserve its target until the fresh connected catalogue arrives.
        self.pendingItem = vnum if vnum else None
        if vnum and self.receiver.catalog and vnum in self.receiver.catalog.items:
            self.pendingItem = None
            self.OpenItem(vnum)
        elif not vnum:
            self.LoadGuidePage()

    def ShowItemInfo(self, vnum, unused=0, isHistory=False):
        if self.receiver.catalog:
            self.OpenItem(int(vnum))
        else:
            self.pendingItem = int(vnum)

    def FocusSearchItem(self):
        if self.search:
            self.search.SetFocus()

    def OpenDungeon(self, boss):
        if not self.receiver.catalog:
            self.pendingBoss = int(boss)
            return
        for map_index, location in self.receiver.catalog.maps.items():
            if M.number(location.get('boss')) == int(boss):
                self.Navigate('dungeons', location=map_index)
                return
        self.Navigate('dungeons')

    def Filter(self):
        # IME can notify repeatedly for one edit. Keep typing immediate, and
        # rebuild native widgets once after the last edit, including deletion.
        self.searchDue = app.GetTime()+SEARCH_DELAY

    def OpenItem(self, vnum):
        catalog = self.receiver.catalog
        if not catalog:
            return
        if vnum in catalog.alchemy:
            stone = catalog.alchemy[vnum]
            self.alchemyChoice = tuple(M.number(stone[k]) for k in ('kind', 'grade', 'purity'))
            self.alchemyOverview = False
            self.Navigate('equipment', category=L('dragon_stones'))
            return
        for key, variants in catalog.families.items():
            if vnum in variants:
                group = E.group(key[1:])
                self.Navigate('item',category=L(group) if group else None,targetItem=vnum,expand=False)
                return
        # Recipe ingredients can have gathering/shop provenance without being
        # independently listed as obtainable equipment.
        if vnum in catalog.items:
            self.Navigate('item',targetItem=vnum,expand=False)

    def Toggle(self, key):
        self.opened = None if self.opened == key else key
        self.extraSources = False
        self.Draw()

    def MoreSources(self):
        self.extraSources = not self.extraSources
        self.Draw()

    def TurnPage(self, delta):
        self.restoreScroll = 0
        self.page = max(0, self.page+delta)
        self.opened = None
        self.Draw()

    def Draw(self):
        self.searchDue = None
        if not self.body or self.destroyed:
            return
        self.drawRevision += 1
        query = self.search.GetText() if self.search else ''
        offset = max(0,-self.body.GetLocalPosition()[1]) if query==getattr(self,'drawQuery','') else 0
        self.drawQuery = query
        self.HideTooltip()
        self.DropModel()
        self.sectionTabs = []
        self._Clear(self.content)
        self.recipeListFamilies = None
        self.drawnCraftRecipes = set()
        self.detailLists = []
        self.dungeonStatusWidgets = []
        self.loadingLabel = self.loadingTrack = self.loadingFill = None
        home = self.mode == 'overview' and not query
        equipment = self.mode == 'equipment' and self.EquipmentGroup() is not None and not query
        clean = not query and (home or equipment or self.mode in ('item', 'chests', 'maps', 'dungeons') or (self.mode == 'systems' and self.guide in G.SUPPORTED))
        if self.receiver and self.receiver.error:
            clean = False  # First-use errors must expose Refresh, including item links from home.
        if clean and not home and self.StaleShown():
            clean = False  # Say that the data changed and offer the refresh.
        self.viewHeight = self.windowHeight-TOP-(14 if clean else 44)
        self.viewport.SetPosition(H.ARTICLE_X, TOP)
        self.scroll.SetPosition(self.windowWidth-18, TOP)
        self.viewport.SetSize(self.pageWidth, self.viewHeight)
        self.scroll.SetScrollBarSize(self.viewHeight)
        self.refreshButton.Hide() if clean else self.refreshButton.Show()
        self.status.Hide() if clean else self.status.Show()
        self.UpdateStatus()
        catalog = self.receiver.catalog if self.receiver else None
        y = 0
        query = self.search.GetText() if self.search else ''
        if not catalog and self.mode == 'overview' and not query:
            y = self.DrawOverview(y)
        elif not catalog and self.mode == 'systems' and not query:
            y = self.DrawGuide(y)
        elif not catalog:
            y = self._PageTitle(y, self.PageName(), L('atlas'))
            if self.receiver and self.receiver.error:
                y = self._Flow(y, L('unavailable'))
            if self.receiver and self.receiver.error:
                self._Button(self.body, 0, y+8, 160, L('retry'), self.Refresh)
                y += 48
        elif query:
            y = self.DrawSearch(y, query)
        elif equipment and self.EquipmentGroup() == 'dragon_stones':
            y = A.draw_alchemy(self, query)
        elif equipment:
            y = self.DrawEquipment(query)
        elif self.mode == 'chests' or (self.mode == 'equipment' and self.category == L('chests')):
            y = A.draw_chests(self, query)
        elif self.mode == 'item':
            y = self.DrawItemDetail()
        elif self.mode == 'maps':
            y = W.draw(self, query)
        elif self.mode == 'dungeons':
            y = DG.draw(self, query)
        elif self.mode == 'equipment':
            y = self.DrawItems(self._PageTitle(y, self.category, L('atlas')), self.Families()) if self.category else self.DrawCategories(y)
        elif self.mode == 'systems':
            y = self.DrawGuide(y)
        else:
            y = self.DrawOverview(y)
        padding = 0 if self.mode in ('item', 'maps') or (equipment and self.EquipmentGroup() == 'dragon_stones') else 10
        self.bodyHeight = max(self.viewHeight, y+padding)
        self.body.SetSize(self.pageWidth, self.bodyHeight)
        self._LayoutScroll(self.scroll, self.bodyHeight, self.viewHeight)
        if self.restoreScroll is not None:
            self.scroll.SetPos(self.restoreScroll)
            self.restoreScroll = None
        else:
            self.scroll.SetPos(min(1.0,float(offset)/max(1,self.bodyHeight-self.viewHeight)))
        self.Scroll()

        self.SyncModels()

    def Families(self):
        group = self.EquipmentGroup()
        if group:
            mount = group == 'mount_equipment'
            return E.families(self.receiver.catalog,group,None if mount else self.equipmentSubtype,None if mount else self.selectedJob,
                              self.search.GetText() if self.search else '')
        return [row for row in self.receiver.catalog.Families()
                if self.category is None or self.CategoryName(row[0][1:]) == self.category]

    def ExactText(self, parent, x, y, text, font='Noto Sans:14a', color=T.INK_DIM,
                  align='left', width=None):
        line = R.Text(parent, str(text), x, y, font, R.SignedColor(color), align=align, valign='top')
        self.content.append(line)
        if width is not None:
            R.Fit(line,str(text),width)
        return line

    def SetJob(self, job):
        self.selectedJob = None if self.selectedJob == job else job
        self.equipmentSubtype = None
        self.page = 0
        self.Draw()
        self.SaveHistory()

    def SetEquipmentSubtype(self, subtype):
        self.equipmentSubtype = subtype
        self.page = 0
        self.Draw()
        self.SaveHistory()

    def DrawEquipment(self, query=''):
        owner, catalog = proxy(self), self.receiver.catalog
        group = self.EquipmentGroup()
        mount = group == 'mount_equipment'
        width = self.pageWidth-8
        options = [] if mount else E.subtypes(catalog,group)
        valid = [cat for cat in options if E.families(catalog,group,cat,self.selectedJob)]
        if self.equipmentSubtype not in valid:
            self.equipmentSubtype = E.preferred_subtype(catalog,group,valid,self.selectedJob)
        families = E.families(catalog,group,self.equipmentSubtype,None if mount else self.selectedJob,query)
        self.recipeListFamilies = families
        x = H.ARTICLE_X
        self.ExactText(self,x,42,L('equipment')+'  /  '+self.category)
        self.ExactText(self,x,65,self.category.upper(),'Althea Caps:23a',T.IVORY)
        job_label = next((L(label) for job,label,unused in E.JOBS if job == self.selectedJob),L('all_jobs'))
        count=len(families);word=L('family_one') if count==1 else L('family_few') if 2<=count<=4 else L('family_many')
        if not mount:
            self.ExactText(self,self.windowWidth-24,71,job_label+' · '+'%d '%count+word,align='right')
        if mount:
            makers = {M.number(r['npc']) for key, variants in families for v in variants for r in catalog.recipe_index.get(v, [])}
            if len(makers) == 1:
                self.ExactText(self, self.windowWidth-24, 78, L('craft_by')+nonplayer.GetMonsterName(next(iter(makers))), color=A.GOLD, align='right')
        if not mount:
            all_button = Tabs.create(self,self,x,102,52,[(None,L('all'))],
                                     None if self.selectedJob is None else 'inactive',
                                     lambda unused,r=owner:r.SetJob(None),font='Noto Sans:15a')
            card=(width-52-24)//4
            for n,(job,label,face) in enumerate(E.JOBS):
                button=PortraitButton(self.kit,card,L(label),'icon/face/'+face+'.tga',
                                      lambda j=job,r=owner:r.SetJob(j),self.selectedJob==job)
                self._Keep(button,self,x+58+n*(card+6),94,self.content)
        if valid:
            Tabs.create(self,self,x,150,width,[(cat,self.CategoryName(cat)) for cat in valid],
                        self.equipmentSubtype,ui.__mem_func__(self.SetEquipmentSubtype))
        first_steps=E.forge(catalog,families[0][1]) if families else []
        article_y = 100 if mount else 211
        if first_steps:
            if mount:
                article_y += 23
            self.ExactText(self,x,article_y-23,L('forge')+' '+self.GradeRange(families[0][1]),'Noto Sans:15a',T.IVORY)
            self.ExactText(self,self.windowWidth-28,article_y-22,L('one_attempt'),'Noto Sans:13a',align='right')
        self.viewHeight=self.windowHeight-article_y-14
        self.viewport.SetPosition(x,article_y)
        self.viewport.SetSize(self.pageWidth,self.viewHeight)
        self.scroll.SetPosition(self.windowWidth-18,article_y)
        self.scroll.SetScrollBarSize(self.viewHeight)
        y=0
        if not families:
            return self._Flow(8,L('empty'))
        pages=max(1,(len(families)+PAGE_SIZE-1)//PAGE_SIZE)
        self.page=min(self.page,pages-1)
        y=self.DrawPager(y,pages)
        for key,variants in families[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE]:
            y=self.DrawMatrix(y,key,variants)+(0 if mount else 12)
        if not mount:y-=12
        return self.DrawPager(y+8,pages) if pages>1 else y

    def DrawPager(self,y,pages):
        if pages<=1:return y
        owner=proxy(self)
        previous=self._Button(self.body,0,y,52,'<',lambda r=owner:r.TurnPage(-1))
        self.ExactText(self.body,65,y+5,'%d / %d'%(self.page+1,pages))
        following=self._Button(self.body,135,y,52,'>',lambda r=owner:r.TurnPage(1))
        if self.page==0:previous.callback=None
        if self.page+1==pages:following.callback=None
        return y+36

    def SetAlchemy(self, kind=None, grade=None, purity=None, overview=False):
        old = self.alchemyChoice
        self.alchemyChoice = (old[0] if kind is None else kind,
                              old[1] if grade is None else grade,
                              old[2] if purity is None else purity)
        self.alchemyOverview = overview
        self.scroll.SetPos(0)
        self.Draw()
        self.SaveHistory()

    def GradeRange(self, variants):
        grades=[E.grade(ItemName(v)) for v in variants]
        grades=[g for g in grades if g is not None]
        return '+%d až +%d'%(min(grades),max(grades)) if grades else ''

    def DrawMatrix(self, y, key, variants, heading=None):
        catalog, owner = self.receiver.catalog, proxy(self)
        forge=E.forge(catalog,variants)
        if not forge and E.creations(catalog,variants):
            return self.DrawTransformUses(A.draw_craft(self,y,key,variants),key,variants)
        icon=next((v for v in variants if v in catalog.available),variants[0])
        width=self.pageWidth-8;left=84 if width<600 else 96
        chunks=[forge[i:i+9] for i in range(0,len(forge),9)] or [[]]
        for steps in chunks:
            cell=(width-left-8)//len(steps) if steps else 0
            grid_width=width
            body_height=max(80,max([len(M.rows(s.get('materials')))*36 for s in steps] or [0]))
            height=29+22+body_height+(42 if steps else 0)
            frame=R.Frame(self.body,0,y,grid_width,height,'panel',bg='panel_dark')
            self.content.append(frame)
            self._Rect(self.body,2,y+2,grid_width-4,26,0xff211d1d)
            header=self._Button(self.body,0,y,grid_width,'',lambda v=icon,r=owner:r.OpenItem(v),arrow=False)
            header.label.Hide()
            self.ExactText(header,10,6,heading or key[0],'Althea Caps:18a',T.IVORY,width=grid_width-145)
            levels=[M.number(catalog.items[v].get('level')) for v in variants if v in catalog.available]
            caption=L('single_attempt') if heading else L('level')+' %d+'%min(levels) if levels and min(levels)>0 else ''
            self.ExactText(header,grid_width-26,8,caption,
                           align='right')
            grade_y=y+29
            first=M.number(steps[0]['from']) if steps else icon
            base=E.grade(ItemName(first))
            if steps:
                self._Keep(GradeButton(self,left,'+'+str(base) if base is not None else L('base'),first),self.body,0,grade_y,self.content)
                self._Rect(self.body,1,grade_y+22,grid_width-2,1,T.LINE)
            self._Keep(ItemIcon(self,first,size=32,height=80),self.body,(left-32)//2,
                       grade_y+22+(body_height-80)//2,self.content)
            for index,step in enumerate(steps):
                xx=left+index*cell
                self._Rect(self.body,xx,grade_y,1,height-29,T.LINE)
                target=M.number(step['to']);grade=E.grade(ItemName(target))
                self._Keep(GradeButton(self,cell,'+'+str(grade) if grade is not None else L('next'),target),self.body,xx,grade_y,self.content)
                for row,material in enumerate(M.rows(step.get('materials'))):
                    self._Icon(self.body,xx+(cell-32)//2,grade_y+24+row*36,
                               M.number(material['vnum']),M.number(material['count']))
                bottom=grade_y+22+body_height
                self._Keep(MoneyCell(self.kit,cell,step['gold']),self.body,xx,bottom,self.content)
                self.ExactText(self.body,xx+cell//2,bottom+24,str(M.number(step['chance']))+' %',
                               'Noto Sans:13a',align='center')
            if steps:
                bottom=grade_y+22+body_height
                self._Rect(self.body,1,bottom,grid_width-2,1,T.LINE)
                self.ExactText(self.body,8,bottom+4,L('yang_short'),'Noto Sans:13a')
                self.ExactText(self.body,8,bottom+24,L('chance_short'),'Noto Sans:13a')
            else:
                proto=catalog.items[icon]
                yy=grade_y+25
                for apply in M.rows(proto.get('applies')):
                    label=self.ApplyText(M.number(apply['type']),M.number(apply['value']))
                    if label:
                        self.ExactText(self.body,left+6,yy,label,'Noto Sans:14a',A.FixedColor(M.number(apply['value'])),width=grid_width-left-16)
                        yy+=20
            y+=height+12
        return self.DrawTransformUses(y-12,key,variants)

    def DrawTransformUses(self,y,key,variants):
        catalog=self.receiver.catalog
        targets=[r for r in E.uses(catalog,variants) if r['sources'].intersection(variants) or
                 any(E.group((M.number(catalog.items[t]['type']),M.number(catalog.items[t]['subtype'])))==E.group(key[1:]) for t in r['targets'])]
        for row in targets:
            # Show every loaded transformation here, including its exact source
            # grade and materials, without requiring a detail-page detour.
            recipes=E.creations(catalog,row['variants'])
            recipes=[recipe for recipe in recipes if any(
                M.number(material['vnum']) in variants for material in M.rows(recipe.get('materials')))]
            if self.recipeListFamilies is not None:
                recipes=[recipe for recipe in recipes
                         if E.recipe_card_owner(catalog,recipe,self.recipeListFamilies)==key]
            y=A.draw_craft(self,y,row['key'],row['variants'],recipes=recipes)
        return y

    def DetailFamily(self):
        catalog=self.receiver.catalog
        return next(((key,vs) for key,vs in catalog.families.items() if self.itemVnum in vs),
                    ((M.family_name(ItemName(self.itemVnum)),M.number(catalog.items[self.itemVnum]['type']),
                      M.number(catalog.items[self.itemVnum]['subtype'])),[self.itemVnum]))

    def DetailColumn(self,x,y,width,height,title):
        self.ExactText(self.body,x,y,title.upper(),'Althea Caps:18a',T.IVORY,width=width-12)
        view=self._Keep(ui.Window(),self.body,x,y+33,self.content)
        view.SetSize(width-14,height);view.EnableScissorRect()
        body=self._Keep(ui.Window(),view,0,0,self.content)
        scroll=self._Keep(WikiScrollBar(),self.body,x+width-12,y+33,self.content)
        scroll.SetScrollBarSize(height)
        index=len(self.detailLists)
        self.detailLists.append([body,scroll,height,height])
        owner=proxy(self)
        scroll.SetScrollEvent(lambda i=index,r=owner:r.ScrollDetail(i))
        uiwheel.Bind(scroll,view,lambda i=index,r=owner:float(WHEEL_PIXELS)/max(1,r.detailLists[i][3]-r.detailLists[i][2]))
        return body,index

    def FinishColumn(self,index,content,width):
        body,scroll,visible,unused=self.detailLists[index]
        content=max(visible,content)
        self.detailLists[index][3]=content
        body.SetSize(width-14,content)
        scroll.SetMiddleBarSize(min(1.0,float(visible)/content))
        scroll.SetPos(0)
        scroll.Show() if content>visible else scroll.Hide()

    def ScrollDetail(self,index):
        body,scroll,visible,content=self.detailLists[index]
        body.SetPosition(0,-int(max(0,content-visible)*scroll.GetPos()))

    def ToggleSource(self,identity):
        self.sourceExpanded=None if self.sourceExpanded==identity else identity
        self.Draw()

    def DrawSourceRows(self,parent,width,variants):
        catalog,owner=self.receiver.catalog,proxy(self)
        y=0
        for mission in catalog.missions:
            book=M.number(mission['book'])
            if M.number(mission['chest']) in variants and book in catalog.available:
                self._Icon(parent,3,y+1,book,size=24)
                self._Button(parent,31,y,width-47,ItemName(book),lambda v=book,r=owner:r.OpenItem(v),arrow=False)
                y+=29
        for index,source in enumerate(E.sources(catalog,variants)):
            maps=sorted(source['maps']);chests=source['chests'];inset=42 if chests else 7
            if chests:self._Icon(parent,3,y+6,chests[-1],size=30)
            title=ItemName(chests[-1]) if chests else MobName(source['mob'])
            identity=(source['mob'],source['chests'],tuple(maps))
            if len(maps)==1:
                loc=maps[0];mode='dungeons' if M.number(catalog.maps[loc].get('boss')) else 'maps'
                event=lambda m=mode,loc=loc,r=owner:r.Navigate(m,location=loc)
            else:event=lambda k=identity,r=owner:r.ToggleSource(k)
            if chests:event=lambda v=chests[-1],r=owner:r.OpenItem(v)
            hint=catalog.MapName(maps[0]) if len(maps)==1 else L('location_count')%len(maps)
            if source['min_level']:hint+=' · '+L('level')+' '+str(source['min_level'])+'+'
            if source['gloves']:hint+=' · '+L('gloves')
            self._Keep(SourceButton(self.kit,width-inset-16,title,hint,event),parent,inset,y,self.content)
            self.ExactText(parent,inset+7,y+27,hint,'Noto Sans:13a',width=width-inset-24)
            y+=52
            if self.sourceExpanded==identity:
                for loc in maps:
                    mode='dungeons' if M.number(catalog.maps[loc].get('boss')) else 'maps'
                    self._Button(parent,12,y,width-28,catalog.MapName(loc),
                                 lambda m=mode,loc=loc,r=owner:r.Navigate(m,location=loc))
                    y+=29
        for index,recipe in enumerate([r for v in variants for r in catalog.recipe_index.get(v,[])]):
            npc=M.number(recipe['npc'])
            self._Button(parent,0,y,width-16,L('recipes')+' · '+MobName(npc),
                         lambda i=index,r=owner:r.OpenItemRecipe(i))
            y+=29
        if not y:self.ExactText(parent,7,0,L('no_source'),'Noto Sans:14a',width=width-20);y=30
        return y

    def DrawItemDetail(self):
        return D.draw(self)

    def OpenItemForge(self, vnum):
        self.OpenItem(vnum)
        if self.mode == 'item':
            self.detailPane = 'forge'
            self.Draw()

    def OpenItemSources(self):
        # Preserve the detail's identity; switch to the compact source pane.
        self.itemSourcesOnly=True
        self.detailPane='sources'
        self.Draw()

    def OpenItemRecipe(self,index):
        self.recipeSelected=index
        self.Draw()

    def DrawOverview(self, y):
        width, height = H.HeaderSize(self.compact)
        image = Decoration(self.body, H.ART+'header-%dx%d.png' % (width, height), 0, 0)
        self.content.append(image)
        frame = R.Frame(self.body, 0, 0, width, height, 'panel', bg=None)
        self.content.append(frame)
        for text, text_y, font, color in (
                ('ALTHEA', 10 if self.compact else 14, 'Althea Caps:14a', T.INK_DIM),
                ('WIKIPEDIE', 30 if self.compact else 35, 'Althea Caps:28a', T.IVORY)):
            self.content.append(R.Text(self.body, text, width//2, text_y, font, color, align='center', valign='top'))
        owner = proxy(self)
        width, height = H.CardSize(self.compact)
        for index, (mode, title, hint) in enumerate(H.CARDS):
            family = {'equipment': 'equipment', 'dungeons': 'dungeon', 'systems': 'systems'}[mode]
            family += '-%dx%d' % (width, height)
            link = HomeLink(width, height, L(title), lambda m=mode, r=owner: r.Navigate(m), family, hint=L(hint))
            y = H.CardY(self.compact, index)-H.ARTICLE_Y
            self._Keep(link, self.body, 0, y, self.content)
        return y+height

    def DrawCategories(self, y):
        y = self._PageTitle(y, L('equipment'), L('atlas'))
        y = self._Flow(y, L('choose'))
        categories = {}
        for key, variants in self.receiver.catalog.Families():
            group = E.group(key[1:])
            if group:
                categories.setdefault(L(group), []).append((key, variants))
        owner = proxy(self)
        columns = 3 if self.pageWidth >= 680 else 2
        cell = self.pageWidth//columns
        for index, (category, families) in enumerate(sorted(categories.items(),key=lambda row:(min(self.receiver.catalog.FamilyKey(vs) for unused,vs in row[1]),row[0]))):
            x, row_y = (index%columns)*cell, y+(index//columns)*84
            subtypes = E.subtypes(self.receiver.catalog, E.group(families[0][0][1:]))
            key, variants = min(families, key=lambda row: subtypes.index(row[0][1:]))
            vnum = next(v for v in variants if v in self.receiver.catalog.available)
            card = CategoryCard(self.kit, cell-14, category, len(families), vnum,
                                lambda c=category, r=owner: r.Navigate('equipment', category=c))
            self._Keep(card, self.body, x, row_y, self.content)
            self._Rect(self.body, x, row_y+72, cell-14, 1, T.LINE)
        return y+((len(categories)+columns-1)//columns)*84

    def DrawSearch(self, y, query):
        y = self._PageTitle(y, L('results'), query)
        needle = M.folded(query)
        owner = proxy(self)
        for guide in GUIDES:
            if needle in M.folded(guide[2]):
                self._Button(self.body, 0, y, self.pageWidth-16, guide[2], lambda g=guide[0], r=owner: r.Navigate('systems', guide=g))
                y += 31
        for map_index, location in sorted(self.receiver.catalog.maps.items(), key=lambda row: self.receiver.catalog.MapKey(row[0])):
            if needle in M.folded(location['name']):
                mode = 'dungeons' if M.number(location.get('boss')) else 'maps'
                self._Button(self.body, 0, y, self.pageWidth-16, location['name'], lambda m=mode, loc=map_index, r=owner: r.Navigate(m, location=loc))
                y += 31
        return self.DrawItems(y, self.receiver.catalog.Families(query=query), compact=True)

    def DrawItems(self, y, families, compact=False):
        owner = proxy(self)
        if not compact:
            self.recipeListFamilies = families
        self._Text(self.body, 0, y, L('count') % len(families), T.INK_DIM, small=True)
        y += 30
        total = (len(families)+PAGE_SIZE-1)//PAGE_SIZE
        self.page = min(self.page, max(0, total-1))
        if total > 1:
            self._Button(self.body, 300, y-30, 80, '<', lambda r=owner: r.TurnPage(-1))
            self._Text(self.body, 390, y-25, '%d / %d' % (self.page+1, total), small=True)
            self._Button(self.body, 460, y-30, 70, '>', lambda r=owner: r.TurnPage(1))
        if not families:
            return self._Flow(y, L('empty'))
        for key, variants in families[self.page*PAGE_SIZE:(self.page+1)*PAGE_SIZE]:
            if not compact and E.group(key[1:]):
                y=self.DrawMatrix(y,key,variants)+12
                continue
            icon = next(v for v in variants if v in self.receiver.catalog.available)
            self._Icon(self.body, 2, y+3, icon)
            self._Button(self.body, 43, y+2, self.pageWidth-58, key[0], lambda v=icon, r=owner: r.OpenItem(v),arrow=False)
            y += 40 if self.compact else 47
            y = self._Rule(y)
        return self.DrawPager(y+8,total) if total>1 else y

    def DrawItem(self, y, key, variants):
        catalog = self.receiver.catalog
        available = [v for v in variants if v in catalog.available]
        levels = [M.number(catalog.items[v].get('level')) for v in available]
        if any(levels):
            self._Text(self.body, 8, y, L('level')+' '+str(min(levels))+'+', T.INK_DIM, small=True)
            y += 25
        forge = catalog.Forge(variants)
        if forge:
            y = self.DrawForge(y, forge)
        recipes = [r for v in available for r in catalog.recipe_index.get(v, [])]
        if recipes:
            y = self._Heading(y+9, L('recipes'))
            for recipe in recipes:
                y = self.DrawRecipe(y, recipe)
        routes = catalog.Routes(variants)
        if routes:
            y = self._Heading(y+10, L('sources'))
            y = self.DrawRoutes(y, routes)
        if any(v in catalog.chests for v in available):
            loot = [row for v in available for row in catalog.chests.get(v, [])]
            y = self.DrawLoot(y+8, loot)
        return y

    def DrawForge(self, y, forge):
        y = self._Heading(y, L('forge'))
        # Table width is bounded at native size. More than nine authored
        # transitions continue in another table, without separate item rows.
        for start in range(0, len(forge), 9):
            steps = forge[start:start+9]
            label_w, cell = 135, (self.pageWidth-145)//max(1, len(steps))
            self._Rect(self.body, 0, y-4, self.pageWidth-10, 27, 0xff242120)
            self._Text(self.body, 6, y, L('material'), T.IVORY, small=True)
            for index, step in enumerate(steps):
                name = ItemName(M.number(step['to']))
                grade = name.rpartition('+')[-1]
                self._Text(self.body, label_w+index*cell+2, y, '+'+grade if grade.isdigit() else str(start+index+1), T.IVORY, small=True, width=cell-3)
            y += 29
            materials = sorted({M.number(m['vnum']) for step in steps for m in M.rows(step.get('materials'))})
            for row_index, vnum in enumerate(materials):
                if row_index % 2 == 0:
                    self._Rect(self.body, 0, y-3, self.pageWidth-10, 27, 0xff171615)
                self._Icon(self.body, 4, y-2, vnum, size=22)
                self._Text(self.body, 31, y, ItemName(vnum), small=True, width=label_w-36)
                for index, step in enumerate(steps):
                    count = sum(M.number(m['count']) for m in M.rows(step.get('materials')) if M.number(m['vnum']) == vnum)
                    self._Text(self.body, label_w+index*cell+3, y, str(count) if count else '-', small=True)
                y += 28
            for key, label in (('gold', 'yang'), ('chance', 'chance')):
                self._Text(self.body, 6, y, L(label), T.INK_DIM, small=True)
                for index, step in enumerate(steps):
                    value = Amount(step[key]) if key == 'gold' else str(M.number(step[key]))+' %'
                    self._Text(self.body, label_w+index*cell+2, y, value, small=True, width=cell-3)
                y += 27
        return self._Flow(y+3, L('forge_hint'))

    def DrawRecipe(self, y, recipe, show_result=True):
        npc = M.number(recipe['npc'])
        portable = M.number(self.receiver.catalog.systems.get('dew', {}).get('catalogue'))
        if show_result:
            self._Icon(self.body, 3, y, M.number(recipe['vnum']), M.number(recipe['count']))
        label_x = 46 if show_result else 8
        maker = L('forge') if recipe.get('method') == 'forge' else L('reforge') if recipe.get('method') == 'refine' else L('scroll_craft') if recipe.get('method') == 'scroll' else L('portable') if npc == portable else MobName(npc)
        self._Text(self.body, label_x, y+2, L('recipes')+' · '+maker, T.IVORY, width=self.pageWidth-label_x-12)
        # Price belongs to the requirements row below, not a duplicate caption.
        self._Text(self.body, label_x, y+22, L('recipe_result') % (M.number(recipe['count']), M.number(recipe['chance'])), T.INK_DIM, small=True)
        y += 48
        y = self._TableHeader(y, 'recipe_materials')
        for material in M.rows(recipe.get('materials')):
            vnum, count = M.number(material['vnum']), M.number(material['count'])
            have = ownedcount.Owned(vnum)     # the server's count (root/ownedcount.py)
            self._Icon(self.body, 6, y-2, vnum, size=22)
            y = self._PersonalRow(y, ItemName(vnum), have, count, have >= count, label_x=35)
        gold = M.number(recipe.get('gold'))
        if gold:
            y = self._PersonalRow(y, 'Yang', Amount(player.GetElk()), Amount(gold), player.GetElk() >= gold)
        gem = M.number(recipe.get('gem'))
        if gem:
            y = self._PersonalRow(y, 'Gaya', Amount(player.GetGem()), Amount(gem), player.GetGem() >= gem)
        if M.number(recipe.get('level')):
            have = player.GetStatus(player.LEVEL)
            y = self._PersonalRow(y, L('level'), have, recipe['level'], have >= M.number(recipe['level']))
        if M.truth(recipe.get('mount_required')):
            y = self._Flow(y, L('mount_required'))
        if M.number(recipe.get('retained')):
            self._Icon(self.body, 6, y, M.number(recipe['retained']))
            y = self._Flow(y, L('retained'), width=self.pageWidth-56, x=46)
        return y+12

    def DrawRoutes(self, y, routes):
        for map_index, mob, chests, drop in routes if self.extraSources else routes[:3]:
            self._Text(self.body, 7, y, self.receiver.catalog.MapName(map_index), T.IVORY, small=True, width=self.pageWidth-15)
            self._Text(self.body, 7, y+19, MobName(mob), T.INK_DIM, small=True, width=260)
            x = 275
            for chest in chests:
                self._Icon(self.body, x, y, chest, size=30)
                x += 37
            if M.number(drop.get('min_level')):
                self._Text(self.body, x, y+19, L('level')+' '+str(drop['min_level'])+'+', T.INK_DIM, small=True)
            if M.truth(drop.get('gloves')):
                self._Text(self.body, x, y, L('gloves'), T.INK_DIM, small=True)
            y += 47
        if len(routes) > 3:
            self._Button(self.body, 0, y, self.pageWidth-15, L('all_sources')+' ('+str(len(routes))+')', self.MoreSources, arrow=self.extraSources)
            y += 36
        return y

    def DrawLocations(self, y):
        owner = proxy(self)
        y = self._PageTitle(y, L(self.mode), L('world'))
        for map_index, location in sorted(self.receiver.catalog.maps.items(), key=lambda row: self.receiver.catalog.MapKey(row[0])):
            if bool(M.number(location.get('boss'))) != (self.mode == 'dungeons'):
                continue
            label = location['name']+' | '+L('level')+' '+str(location['level'])+'+'
            self._Button(self.body, 0, y, self.pageWidth-15, label, lambda loc=map_index, r=owner: r.Navigate(r.mode, location=loc))
            y += 37
        return y

    def DrawLocation(self, y):
        catalog = self.receiver.catalog
        location = catalog.maps.get(self.location)
        if not location:
            return self._Flow(y, L('empty'))
        boss = M.number(location.get('boss'))
        y = self._PageTitle(y, location['name'], L(self.mode))
        if boss:
            self.DrawModel(0, y, boss)
            preview = self.pageWidth >= 680
            facts_width = self.pageWidth-185-(174 if preview else 0)
            self._Text(self.body, 171, y+8, MobName(boss), T.IVORY, width=facts_width)
            self._Text(self.body, 171, y+38, L('level')+' '+str(location['level'])+'+', T.INK_DIM)
            self._Text(self.body, 171, y+64, L('cooldown')+' '+str(M.number(location['cooldown'])//60)+' min', T.INK_DIM, small=True)
            self._Icon(self.body, 171, y+93, M.number(location['ticket']), M.number(location['ticket_count']))
            self._Text(self.body, 212, y+101, ItemName(M.number(location['ticket'])), width=facts_width-41, small=True)
            if preview:
                x = self.pageWidth-168
                self._Text(self.body, x, y+8, L('loot'), T.IVORY, title=True)
                drops = {}
                for mob in catalog.mobs:
                    if M.number(mob['vnum']) != boss or M.number(mob['map']) != self.location:
                        continue
                    for drop in M.rows(mob.get('drops')):
                        vnum = M.number(drop['vnum'])
                        drops.setdefault(M.family_name(ItemName(vnum)), {})[vnum] = M.number(drop['count'])
                for index, variants in enumerate(list(drops.values())[:8]):
                    vnum = min(variants)
                    icon = self._Icon(self.body, x+(index%4)*40, y+37+(index//4)*42, vnum, variants[vnum])
                    icon.variants = variants
            y += 166
        else:
            self._Text(self.body, 0, y, L('level')+' '+str(location['level'])+'+', T.INK_DIM)
            y += 32
        if boss:
            mob = next((m for m in catalog.mobs if M.number(m['vnum']) == boss and M.number(m['map']) == self.location), {})
            y = self._TableHeader(y)
            level = player.GetStatus(player.LEVEL)
            y = self._PersonalRow(y, L('level'), level, location['level'], level >= M.number(location['level']))
            ticket, need = M.number(location['ticket']), M.number(location['ticket_count'])
            have = ownedcount.Owned(ticket)
            self._Icon(self.body, 6, y-2, ticket, size=24)
            y = self._PersonalRow(y, '      '+ItemName(ticket), have, need, have >= need)
            self._Text(self.body, 8, y, L('cooldown')+'   '+str(M.number(location['cooldown'])//60)+' min', T.INK_DIM, small=True)
            y += 32
            y = self._Flow(y, L('minimum_unknown'))
            y = self._Heading(y+9, L('bonuses'))
            # These are the actual character values, without fabricated thresholds.
            y = self._TableHeader(y)
            for symbol, apply in (('MAX_HP', item.APPLY_MAX_HP), ('DEF_GRADE', item.APPLY_DEF_GRADE_BONUS), ('ATT_SPEED', item.APPLY_ATT_SPEED)):
                point = getattr(player, symbol, None)
                if point is not None:
                    y = self._PersonalRow(y, BonusName(apply), player.GetStatus(point), '-', None)
            for bonus in M.rows(mob.get('bonuses')):
                y = self._PersonalRow(y, L(bonus['label']), BonusValue(bonus['label']), '-', None)
            y = self._Heading(y+10, L('spells'))
            y = self._Flow(y, L('spell_hint'))
            spells = []
            for slot in range(player.SKILL_SLOT_COUNT):
                index = player.GetSkillIndex(slot)
                if not index or skill.GetSkillType(index) != skill.SKILL_TYPE_ACTIVE:
                    continue
                spells.append((slot, index))
            columns = 3 if self.pageWidth >= 680 else 2
            cell = self.pageWidth//columns
            for number, (slot, index) in enumerate(spells):
                x, row_y = (number%columns)*cell, y+(number//columns)*53
                icon = self._Keep(ui.SlotWindow(), self.body, x+4, row_y, self.content)
                icon.SetSize(32, 32)
                icon.AppendSlot(0, 0, 0, 32, 32)
                icon.SetSkillSlotNew(0, index, player.GetSkillGrade(slot), player.GetSkillLevel(slot))
                owner = proxy(self)
                icon.SetOverInItemEvent(lambda unused, s=slot, r=owner: r.ShowSkill(s))
                icon.SetOverOutItemEvent(ui.__mem_func__(self.HideTooltip))
                self._Text(self.body, x+46, row_y, skill.GetSkillName(index), width=cell-54, small=True)
                self._Text(self.body, x+46, row_y+20, '%s / %s' % (player.GetSkillGrade(slot), player.GetSkillLevel(slot)), T.INK_DIM, small=True)
            y += ((len(spells)+columns-1)//columns)*53
            y = self._Heading(y+10, L('gear'))
            equipment = EquippedItems()
            columns = max(1, (self.pageWidth-16)//43)
            start = getattr(item, 'COSTUME_SLOT_START', 0)
            end = start+getattr(item, 'COSTUME_SLOT_COUNT', 0)
            for costume, caption in ((False, 'equipment'), (True, 'costume')):
                entries = [(slot, vnum) for slot, vnum in equipment if (start <= slot < end) == costume]
                if not entries:
                    continue
                self._Text(self.body, 8, y, L(caption), T.INK_DIM, small=True)
                y += 24
                for index, (slot, vnum) in enumerate(entries):
                    icon = self._Icon(self.body, 8+(index%columns)*43, y+(index//columns)*43, vnum)
                    icon.inventorySlot = slot
                y += ((len(entries)+columns-1)//columns)*43+12
            if not equipment:
                y = self._Flow(y, L('no_gear'))
            mob = next((m for m in catalog.mobs if M.number(m['vnum']) == boss and M.number(m['map']) == self.location), {})
            if M.number(mob.get('minimum_players')):
                y = self._Heading(y+10, L('mechanics'))
                for key, label, unit in (('minimum_players', 'players', ''), ('spell_period_ms', 'spell_period', ' s'),
                                         ('recovery_ms', 'recovery', ' s'), ('enrage_ms', 'enrage', ' s')):
                    value = M.number(mob.get(key))
                    if value:
                        self._Text(self.body, 8, y, L(label), width=360)
                        self._Text(self.body, 380, y, str(value//1000 if unit else value)+unit, T.IVORY)
                        y += 26
                y = self._Flow(y, L('mechanic_hint'))
                y = self._Flow(y, L('position_hint'))
        loot = [drop for mob in catalog.mobs if M.number(mob['map']) == self.location and
                (not boss or M.number(mob['vnum']) == boss) for drop in M.rows(mob.get('drops'))]
        return self.DrawLoot(y+15, loot)

    def LootCategory(self, vnum):
        proto = self.receiver.catalog.items.get(vnum, {})
        kind = M.number(proto.get('type'))
        if kind in (item.ITEM_TYPE_WEAPON, item.ITEM_TYPE_ARMOR, getattr(item, 'ITEM_TYPE_BELT', -1)):
            return L('equipment')
        if vnum in self.receiver.catalog.chests:
            return L('chest')
        return L('gather')

    def DrawLoot(self, y, loot, caption=True):
        if not loot:
            return y
        if caption:
            y = self._Heading(y, L('loot'))
            y = self._Flow(y, L('loot_hint'))
        # One icon per item family, retaining the actual grades/counts in the
        # tooltip of the representative item; no caption wall under the icons.
        grouped = {}
        for row in loot:
            vnum = M.number(row['vnum'])
            if not vnum:
                continue
            name = M.family_name(ItemName(vnum))
            key = (self.LootCategory(vnum), name)
            grouped.setdefault(key, {})[vnum] = M.number(row.get('count'))
        for category in sorted({key[0] for key in grouped}):
            self._Text(self.body, 4, y+7, category, T.INK_DIM, small=True, width=120)
            entries = [(key, values) for key, values in grouped.items() if key[0] == category]
            entries.sort(key=lambda row: self.receiver.catalog.FamilyKey(row[1]))
            columns = max(1, (self.pageWidth-140)//39)
            for index, (key, values) in enumerate(entries):
                vnum = min(values)
                icon = self._Icon(self.body, 130+(index%columns)*39, y+(index//columns)*41, vnum, values[vnum])
                icon.variants = values
            y += max(1, (len(entries)+columns-1)//columns)*41+14
        return y

    def DrawGuide(self, y):
        if self.guide in G.SUPPORTED:
            return G.draw(self, self.guide)
        owner = proxy(self)
        guide = next((g for g in GUIDES if g[0] == self.guide), None)
        if not guide:
            y = self._PageTitle(y, L('systems'), L('guide'))
            group = None
            for row in GUIDES:
                if group != row[1]:
                    group = row[1]
                    y = self._Heading(y+14, group)
                self._Button(self.body, 0, y, self.pageWidth-15, row[2], lambda g=row[0], r=owner: r.Navigate('systems', guide=g))
                y += 32
            return y
        y = self._PageTitle(y, guide[2], guide[1])
        y = self._Flow(y, guide[3], color=T.IVORY)
        y = self._Steps(y+12, guide[4])
        if not self.receiver.catalog:
            return y
        if guide[0] == 'ponds':
            ponds = self.receiver.catalog.systems.get('ponds') or {}
            if ponds:
                y = self._Heading(y+12, L('current'))
                for key, label in (('active', 'active_ponds'), ('visible_seconds', 'pond_time')):
                    # Semantic captions are selected explicitly; no balance literals.
                    if key in ponds:
                        self._Text(self.body, 8, y, L(label)+'   '+str(ponds[key]) + (' s' if key == 'visible_seconds' else ''))
                        y += 27
        if guide[0] == 'dews':
            families = [(key, variants) for key, variants in self.receiver.catalog.Families()
                        if any('dew_family' in self.receiver.catalog.items[v] for v in variants)]
            y = self.DrawItems(y+14, families)
        if guide[0] == 'meteors':
            tiers = M.rows(self.receiver.catalog.systems.get('meteors'))
            for tier in tiers:
                vnum = M.number(tier['vnum'])
                self._Button(self.body, 0, y, self.pageWidth-15, MobName(vnum),
                             lambda v=vnum, r=owner: r.SelectMeteor(v), selected=self.meteorVnum == vnum)
                y += 31
            selected = self.meteorVnum or (M.number(tiers[0]['vnum']) if tiers else None)
            loot = [drop for mob in self.receiver.catalog.mobs if M.number(mob['vnum']) == selected
                    for drop in M.rows(mob.get('drops'))]
            y = self.DrawLoot(y+12, loot)
        return y

    def SelectMeteor(self, vnum):
        self.meteorVnum = vnum
        self.Draw()

    def _LayoutScroll(self, scroll, content, visible):
        scroll.SetPos(0)
        if content > visible:
            scroll.SetMiddleBarSize(float(visible)/content)
            scroll.Show()
        else:
            scroll.Hide()
        if scroll is self.scroll:
            self.body.SetPosition(0, 0)
        else:
            self.sidebody.SetPosition(0, 0)

    def BodyWheelStep(self):
        return float(WHEEL_PIXELS)/max(1,self.bodyHeight-self.viewHeight)

    def SideWheelStep(self):
        return float(WHEEL_PIXELS)/max(1,self.sideHeight-self.sideViewHeight)

    def Scroll(self):
        self.body.SetPosition(0, -int(max(0, self.bodyHeight-self.viewHeight)*self.scroll.GetPos()))
        Tabs.update(self)
        self.SyncModels()

    def ScrollSide(self):
        self.sidebody.SetPosition(0, -int(max(0, self.sideHeight-self.sideViewHeight)*self.sidescroll.GetPos()))

    def ShowItem(self, vnum, variants=None, extraLines=None, recommendation=None):
        if self.toolTip:
            self.toolTip.ClearToolTip()
            if recommendation is not None:
                sockets,attrs=recommendation
                sockets=list(sockets[:player.METIN_SOCKET_MAX_NUM])+[0]*max(0,player.METIN_SOCKET_MAX_NUM-len(sockets))
                attrs=list(attrs[:player.ATTRIBUTE_SLOT_MAX_NUM])+[(0,0)]*max(0,player.ATTRIBUTE_SLOT_MAX_NUM-len(attrs))
                self.toolTip.AddItemData(vnum,sockets,attrs,slotIndex=-1,show_character_totals=False)
                for extra in extraLines or []:
                    label, color = extra if isinstance(extra, tuple) else (extra, T.INK_DIM)
                    self.toolTip.AppendTextLine(label, R.SignedColor(color))
                self.AppendWikiVnum(vnum, native=True)
                self.toolTip.ShowToolTip()
                return
            self.toolTip.SetItemToolTip(vnum, showChestHint=False)
            if variants and (len(variants) > 1 or any(isinstance(v, (tuple, list)) for v in variants.values())):
                self.toolTip.AppendSpace(5)
                for variant, count in sorted(variants.items()):
                    quantities = ' / '.join(str(n)+'×' for n in count) if isinstance(count, (tuple, list)) else str(count)+'×'
                    self.toolTip.AppendTextLine(ItemName(variant)+'   '+quantities)
            for extra in extraLines or []:
                label, color = extra if isinstance(extra, tuple) else (extra, T.INK_DIM)
                self.toolTip.AppendTextLine(label, R.SignedColor(color))
            self.AppendWikiVnum(vnum, native=True)
            self.toolTip.ShowToolTip()

    def AppendWikiVnum(self, vnum, native=False):
        # Authority is the native main-character GM flag, never a name or UI toggle.
        try:
            import chr
            if not chr.IsGameMaster(player.GetMainCharacterIndex()):
                return
        except (ImportError, AttributeError, RuntimeError, TypeError):
            return
        if native:
            import osfInfo
            if getattr(osfInfo, "SHOW_ITEM_VNUM_TOOTIP", False):
                return  # Native inventory tooltip already included the GM-only line.
        self.toolTip.AppendSpace(5)
        self.toolTip.AppendTextLine("VNUM: %d" % int(vnum), R.SignedColor(A.GOLD))

    def ApplyText(self, kind, value):
        if kind not in uiToolTip.ItemToolTip.AFFECT_DICT:
            return ''
        return uiToolTip.GET_AFFECT_STRING(kind, value) or ''

    def ShowInventoryItem(self, slot):
        if self.toolTip:
            self.toolTip.SetInventoryItem(slot)
            self.AppendWikiVnum(player.GetItemIndex(slot), native=True)
            self.toolTip.ShowToolTip()

    def ShowSkill(self, slot):
        if self.skillToolTip:
            self.skillToolTip.SetSkillNew(slot, player.GetSkillIndex(slot), player.GetSkillGrade(slot), player.GetSkillLevel(slot))

    def DrawModel(self, x, y, vnum):
        model = W.LiveModel(self.body, x, y, 150, 150, int(vnum))
        self.modelPreviews.append(model)
        self.content.append(model.view)

    def SyncModels(self):
        if not self.body or not self.scroll:
            return
        offset = int(max(0, self.bodyHeight-self.viewHeight)*self.scroll.GetPos())
        for model in self.modelPreviews:
            # Native render targets must not paint over the header or window edge.
            if self.IsShow() and model.top >= offset and model.top+model.height <= offset+self.viewHeight:
                model.Open()
            else:
                model.Close()

    def DropModel(self):
        models, self.modelPreviews = self.modelPreviews, []
        for model in models:
            model.Close()
        self.renderIndex = None

    def HideTooltip(self):
        if self.toolTip:
            self.toolTip.HideToolTip()
        if self.skillToolTip:
            self.skillToolTip.HideToolTip()

    def Open(self):
        if self.destroyed:
            return
        geometry = (self.windowWidth, self.windowHeight, self.sideWidth)
        self._Measure()
        if self.look != R.UseR1() or geometry != (self.windowWidth, self.windowHeight, self.sideWidth):
            self._Clear(self.content)
            self._Clear(self.sidebar)
            self._Clear(self.widgets)
            if self.chrome:
                self.chrome.Destroy()
            self.chrome = self.board = None
            self._Build()
        self.Show()
        self.SetTop()
        self.Prefetch()
        self.UseCatalog()
        drawn = self.drawRevision
        self.OnUpdate()
        if self.receiver.catalog and (self.pendingItem is not None or self.pendingBoss is not None):
            self.CatalogReady(False)
        if drawn == self.drawRevision:
            self.DrawSidebar()
            self.Draw()

    def Close(self):
        self.HideTooltip()
        if self.search:
            self.search.KillFocus()
        self.DropModel()
        self.Hide()

    def Hide(self):
        # Interface.HideAllWindows also calls Hide directly during a warp.
        self.searchDue = None
        self.HideTooltip()
        self.DropModel()
        ui.Window.Hide(self)

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def OnUpdate(self, pump=False):
        if self.destroyed:
            return
        # Only GameWindow -> Interface owns the preparation budget. The native
        # window callback also runs while visible and must not pump a second time.
        if pump and self.receiver and self.receiver.work is not None:
            background = self.receiver.background
            previousError = self.receiver.error
            self.receiver.Pump()
            if self.receiver.revision != self.seenRevision:
                self.CatalogReady(background)
            elif self.receiver.error and self.receiver.error != previousError:
                self.UpdateStatus()
                if self.IsShow():
                    self.Draw()
        if self.IsShow() and self.searchDue is not None and app.GetTime() >= self.searchDue:
            self.page = 0
            self.opened = None
            self.restoreScroll = 0
            self.Draw()
        if self.IsShow() and self.mode == 'dungeons' and self.location:
            now = app.GetTime()
            if now-self.dungeonRequestAt >= 3:
                DG.request(self)
            if now-self.dungeonPaintAt >= 1:
                DG.update(self)
                self.dungeonPaintAt = now
        # Only a deadline while a response is pending. Inventory/skills are read
        # on drawing; no network or catalogue rebuild on every frame.
        if not self.gameReady and self.NetworkReady():
            self.OnGameReady()
        if self.retryAt and app.GetTime() >= self.retryAt:
            self._Request(self.retryKeep)
        elif self.staleDue and app.GetTime() >= self.staleDue:
            self._Request(True)
        if self.requestAt and self.receiver and self.receiver.requested and not self.receiver.error and self.receiver.work is None:
            if app.GetTime()-self.requestAt > 20:
                self.receiver.Fail('timeout')
                self.requestAt = 0
                dbg.TraceError('WIKI_CATALOG_V1 failed reason=timeout progress=%d' % self.loadingPercent)
                self.UpdateStatus()
                self.Draw()

    @WindowDestroy
    def Destroy(self):
        self.Close()
        if self.receiver:
            M.UnbindDungeonReceiver(self.receiver)
            self.receiver.Reset()
        if self.chrome:
            self.chrome.Destroy()
        self.Initialize()
        self.destroyed = True

    def __del__(self):
        ui.Window.__del__(self)
