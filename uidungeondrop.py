"""Read-only compact dungeon rewards; owned by DungeonTeleportPage."""
import weakref
import chestpreview

import app
import item
import net
import localeInfo
import osfInfo
import ui
import wndMgr

import dungeondropmodel as model
from dungeondroptable import ICON_OFFSETS

ASSETS = "d:/ymir work/ui/game/crimson_ember/dungeon_teleport/"


class DropCell(ui.Window):
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.vnum = 0
        self.SetSize(32, 32)
        self.background = ui.ImageBox()
        self.background.SetParent(self)
        self.background.AddFlag("not_pick")
        self.background.LoadImage("d:/ymir work/ui/slot.png")
        self.background.Show()
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag("not_pick")
        self.count = ui.TextLine()
        self.count.SetParent(self)
        self.count.AddFlag("not_pick")
        self.count.SetFontName("Tahoma:11")
        self.count.SetHorizontalAlignRight()
        self.count.SetPosition(31, 20)

    def SetEntry(self, entry):
        self.vnum = 0
        self.Hide()
        self.icon.Hide()
        self.count.Hide()
        if entry is None:
            return
        vnum, count = entry
        try:
            item.SelectItem(vnum)
            self.icon.SetScale(1.0, 1.0)
            self.icon.LoadImage(item.GetIconImageFileName())
            scale, x, y = model.icon_layout(
                self.icon.GetWidth(), self.icon.GetHeight(), ICON_OFFSETS.get(vnum, (0, 0)))
            self.icon.SetScale(scale, scale)
            self.icon.SetPosition(x, y)
        except (RuntimeError, TypeError):
            return
        self.vnum = vnum
        self.icon.Show()
        if count > 1:
            self.count.SetText(str(count))
            self.count.Show()
        self.Show()

    def OnMouseOverIn(self):
        if self.vnum:
            self.owner.OverIn(self.vnum, self)

    def OnMouseOverOut(self):
        self.owner.LeaveCell()

    def OnMouseWheel(self, length):
        return self.owner.OnMouseWheel(length)

    def Destroy(self):
        self.Hide()
        self.vnum = 0
        self.icon = None
        self.count = None
        self.background = None
        self.owner = None


class DungeonDropWindow(ui.BoardWithTitleBar):
    WIDTH = 264
    HEIGHT = 208
    TRACK_HEIGHT = 140

    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self._Initialize()
        self.AddFlag("movable")
        self.AddFlag("float")
        self.SetSize(self.WIDTH, self.HEIGHT)
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.heading = self._Text(16, 35, localeInfo.DUNGEON_DROP_SOURCE)
        self.total = self._Text(247, 35, "")
        self.total.SetHorizontalAlignRight()
        self.empty = self._Text(132, 113, localeInfo.DUNGEON_DROP_EMPTY)
        self.empty.SetHorizontalAlignCenter()
        for index in range(model.COLUMNS * model.VISIBLE_ROWS):
            cell = DropCell(self)
            cell.SetParent(self)
            cell.SetPosition(16 + index % model.COLUMNS * model.CELL_STEP,
                             57 + index // model.COLUMNS * model.CELL_STEP)
            self.cells.append(cell)
        self.track = ui.ExpandedImageBox()
        self.track.SetParent(self)
        self.track.SetPosition(238, 57)
        self.track.AddFlag("not_pick")
        self.track.LoadImage(ASSETS + "scrollbar/track_12x373.png")
        self.track.SetRenderingRect(0.0, 0.0, 0.0, float(self.TRACK_HEIGHT) / 373.0 - 1.0)
        self.thumb = ui.DragButton()
        self.thumb.SetParent(self)
        for setter, state in ((self.thumb.SetUpVisual, "normal"),
                              (self.thumb.SetOverVisual, "hover"),
                              (self.thumb.SetDownVisual, "pressed")):
            setter(ASSETS + "scrollbar/thumb_8x93_" + state + ".png")
        self.thumb.SetPosition(240, 57)
        self.thumb.SetSize(8, 93)
        self.thumb.SetRestrictMovementArea(240, 57, 8, self.TRACK_HEIGHT)
        self.thumb.SetMoveEvent(ui.__mem_func__(self._OnDrag))
        self.Hide()
        # R1 look (root/uir1dungeondrop.py); "Starý vzhled" or a failure keeps this window as it is
        try:
            import uir1dungeondrop
            self.r1Drop = uir1dungeondrop.Dress(self)
        except Exception:
            self.r1Drop = None

    def _Initialize(self):
        self.cells = []
        self.entries = ()
        self.offset = 0
        self.bossVnum = 0
        self.requestId = 0
        self.pending = None
        self.tooltipShown = False
        self.chestPreview = None
        self.heading = None
        self.total = None
        self.empty = None
        self.track = None
        self.thumb = None
        self.r1Drop = None

    def _Text(self, x, y, value):
        label = ui.TextLine()
        label.SetParent(self)
        label.SetPosition(x, y)
        label.SetFontName("Tahoma:11")
        label.AddFlag("not_pick")
        label.SetText(value)
        label.Show()
        return label

    def Open(self, bossVnum, name, anchor):
        self.SetDungeon(bossVnum, name)
        x, y = anchor.GetGlobalPosition()
        x += anchor.GetWidth() + 8
        if x + self.WIDTH + 4 > wndMgr.GetScreenWidth():
            x = anchor.GetGlobalPosition()[0] + (anchor.GetWidth() - self.WIDTH) // 2
        self.SetPosition(max(4, min(x, wndMgr.GetScreenWidth() - self.WIDTH - 4)),
                         max(0, min(y, wndMgr.GetScreenHeight() - self.HEIGHT)))
        self.Show()
        self.SetTop()
        self.RequestDrops()

    def SetDungeon(self, bossVnum, name):
        self.SetTitleName(localeInfo.DUNGEON_DROP_TITLE % name)
        if self.bossVnum == bossVnum:
            return
        self.OverOut()
        if self.chestPreview:
            self.chestPreview.ResetScope()
        self.bossVnum = bossVnum
        self.entries = ()
        self.pending = None
        self.offset = 0
        self.total.SetText("...")
        self._Refresh()
        self.empty.Hide()
        if self.IsShow():
            self.RequestDrops()

    def RequestDrops(self):
        self.requestId = self.requestId % 2147483647 + 1
        self.pending = None
        self.entries = ()
        self.offset = 0
        self.total.SetText("...")
        self._Refresh()
        self.empty.Hide()
        net.SendChatPacket("/dungeon_info drops %d %d" % (self.bossVnum, self.requestId))

    def _MatchesResponse(self, bossVnum, requestId):
        try:
            return (self.IsShow() and int(bossVnum) == self.bossVnum and
                    int(requestId) == self.requestId)
        except (TypeError, ValueError):
            return False

    def OnServerBegin(self, bossVnum, requestId):
        if self._MatchesResponse(bossVnum, requestId):
            self.pending = []

    def OnServerItem(self, bossVnum, requestId, itemVnum, count):
        if not self._MatchesResponse(bossVnum, requestId) or self.pending is None:
            return
        try:
            entry = (int(itemVnum), int(count))
        except (TypeError, ValueError):
            return
        if entry[0] > 0 and entry[1] > 0 and entry not in self.pending:
            self.pending.append(entry)

    def OnServerEnd(self, bossVnum, requestId):
        if not self._MatchesResponse(bossVnum, requestId) or self.pending is None:
            return
        self.entries = tuple(self.pending)
        self.pending = None
        self.total.SetText(localeInfo.DUNGEON_DROP_COUNT % len(self.entries))
        self._Refresh()

    def _Refresh(self):
        self.OverOut()
        self.offset = model.clamp_offset(self.offset, len(self.entries))
        visible = model.visible_entries(self.entries, self.offset)
        for index, cell in enumerate(self.cells):
            cell.SetEntry(visible[index] if index < len(visible) else None)
        maximum = model.max_offset(len(self.entries))
        if maximum:
            self.track.Show()
            self.thumb.SetPosition(240, 57 + int(float(self.offset) / maximum * 47))
            self.thumb.Show()
        else:
            self.track.Hide()
            self.thumb.Hide()
        if self.entries:
            self.empty.Hide()
        else:
            self.empty.Show()

    def _OnDrag(self):
        self.offset = int(round(float(self.thumb.GetLocalPosition()[1] - 57) / 47 *
                                model.max_offset(len(self.entries))))
        self._Refresh()

    def OnMouseWheel(self, length):
        if length:
            self.offset += -1 if length > 0 else 1
            self._Refresh()
        return True

    def _ToolTip(self):
        interface = osfInfo.GetInterfaceInstance()
        if interface:
            return interface.tooltipItem
        return None

    def OverIn(self, vnum, cell=None):
        self.OverOut()
        if cell and getattr(app, "ENABLE_SHOW_CHEST_DROP", False):
            item.SelectItem(vnum)
            if chestpreview.CanPreview(vnum) and item.GetItemType() in (item.ITEM_TYPE_GIFTBOX, item.ITEM_TYPE_GACHA,
                                      item.ITEM_TYPE_TREASURE_BOX):
                if self.chestPreview is None:
                    import uidungeonchestpreview
                    self.chestPreview = uidungeonchestpreview.DungeonChestPreview(self)
                self.chestPreview.Open(vnum, cell)
                return
        tooltip = self._ToolTip()
        if tooltip:
            tooltip.SetItemToolTip(vnum)
            self.tooltipShown = True

    def LeaveCell(self):
        if self.chestPreview and self.chestPreview.IsShow():
            return
        self.OverOut()

    def OverOut(self):
        if self.chestPreview:
            self.chestPreview.Close()
        # The item tooltip is shared; hide it only when a drop cell showed it.
        if not self.tooltipShown:
            return
        self.tooltipShown = False
        tooltip = self._ToolTip()
        if tooltip:
            tooltip.HideToolTip()

    def Close(self):
        self.OverOut()
        if self.chestPreview:
            self.chestPreview.ResetScope()
        self.pending = None
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Close()
        if self.chestPreview:
            self.chestPreview.Destroy()
        for cell in self.cells:
            cell.Destroy()
        if self.thumb:
            self.thumb.Hide()
        self._Initialize()
