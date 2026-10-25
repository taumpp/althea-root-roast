"""Read-only chest contents attached exclusively to a dungeon reward cell."""
import weakref

import app
import item
import localeInfo
import osfInfo
import ui
import uiToolTip
import wndMgr
import stonecrafting
import dungeondropmodel as model


def contains(window, x, y):
    wx, wy = window.GetGlobalPosition()
    return wx <= x < wx + window.GetWidth() and wy <= y < wy + window.GetHeight()


def position(anchor, width, height, screenWidth, screenHeight):
    x, y, cellWidth = anchor
    # Touch the source cell: even a small gap would expose an adjacent boss
    # reward and trigger its hover before the pointer reaches this panel.
    right = x + cellWidth
    left = x - width
    px = right if right + width <= screenWidth - 4 else left
    return (max(4, min(px, screenWidth - width - 4)),
            max(4, min(y, screenHeight - height - 4)))


class DungeonChestPreview(uiToolTip.ToolTip):
    WIDTH = 248
    TOP = 60

    def __init__(self, owner):
        uiToolTip.ToolTip.__init__(self, self.WIDTH, True)
        self.owner = weakref.proxy(owner)
        self.SetFollow(False)
        self.cells = []
        self.entries = ()
        self.grades = {}
        self.cache = {}
        self.vnum = 0
        self.anchor = None
        self.offset = 0
        self.outsideSince = None
        self.deadline = 0
        self.loaded = False
        self.itemTooltip = uiToolTip.ItemToolTip()
        self.r1Header = None
        self.top = self.TOP
        self.r1Vein = self._R1Vein()          # made before the labels: its glow lies under the name
        self.title = self._Label(16, 12, "")
        self.subtitle = self._Label(16, 33, localeInfo.DUNGEON_CHEST_CONTENTS)
        self._R1Header()
        self.status = self._Label(16, self.top + 4, "")
        self.scrollHint = self._Label(16, self.top + model.VISIBLE_ROWS * model.CELL_STEP + 3,
                                      localeInfo.DUNGEON_CHEST_SCROLL)
        # Import only after the boss-drop module has finished defining its cells.
        from uiDungeonDrop import DropCell
        for index in range(model.COLUMNS * model.VISIBLE_ROWS):
            cell = DropCell(self)
            cell.SetParent(self)
            cell.SetPosition(16 + index % model.COLUMNS * model.CELL_STEP,
                             self.top + index // model.COLUMNS * model.CELL_STEP)
            self.cells.append(cell)
        self.Hide()

    def _Label(self, x, y, text):
        label = ui.TextLine()
        label.SetParent(self)
        label.AddFlag("not_pick")
        label.SetFontName("Tahoma:11")
        label.SetPosition(x, y)
        label.SetText(text)
        label.Show()
        return label

    def _R1Vein(self):
        if getattr(self, "r1Frame", None) is None:
            return None
        try:
            import uir1
            return uir1.Vein(self, 0, 0, uir1.HINT_VEIN_MIN)
        except Exception:
            return None

    def _R1Header(self):
        """R1 look (the tooltip has the R1 frame): the header of the one R1 hint (uir1.HintFace) -
        the chest's name centred in ivory with the vein under it, "Možný obsah" dimmer under it, the
        item cells as the body. The original look keeps the two left-aligned labels."""
        if self.r1Vein is None:
            return
        try:
            import uir1
            import uir1tokens
            font = uir1.HintFont()
            cell = uir1.FontCell(font)
            row = uir1.HINT_PAD_TOP + cell + uir1.HINT_VEIN_GAP
            for label, y, color in ((self.title, uir1.HINT_PAD_TOP, uir1tokens.IVORY),
                                    (self.subtitle, row + uir1.HINT_BODY_GAP, uir1tokens.INK_DIM)):
                uir1.SetFont(label, font)               # the line already has its text: laid out again in the font
                label.SetPackedFontColor(color)
                label.SetHorizontalAlignCenter()
                label.SetOutline()
                label.SetPosition(self.WIDTH // 2, y)
        except Exception:
            self.r1Vein.Hide()
            return
        self.r1Header = (self.r1Vein, row)
        self.top = row + uir1.HINT_BODY_GAP + cell + 8

    def _R1LayoutHeader(self):
        """The name, the subtitle and the vein centred on the current width (the vein: the name + the overhang)."""
        if self.r1Header is None:
            return
        import uir1
        vein, row = self.r1Header
        width = self.toolTipWidth
        self.title.SetPosition(width // 2, self.title.GetLocalPosition()[1])
        self.subtitle.SetPosition(width // 2, self.subtitle.GetLocalPosition()[1])
        vein_width = min(width - 8, self.title.GetTextSize()[0] + 2 * uir1.HINT_VEIN_OVERHANG)
        vein.SetPosition((width - vein_width) // 2, row - uir1.T.VEIN_ROW)
        vein.SetWidth(vein_width)

    def Open(self, vnum, anchor):
        self.Close()
        self.vnum = vnum
        self.anchor = weakref.proxy(anchor)
        self.offset = 0
        self.entries = ()
        self.grades = {}
        self.loaded = False
        self.deadline = app.GetTime() + 5.0
        item.SelectItem(vnum)
        self.title.SetText(item.GetItemName())
        # Long localized names expand the native tooltip, never clip the title.
        self.toolTipWidth = max(self.WIDTH, self.title.GetTextSize()[0] + 32)
        self._R1LayoutHeader()
        self.status.SetText(localeInfo.DUNGEON_CHEST_LOADING)
        self._Refresh()
        self.Show()
        self.SetTop()
        if vnum in self.cache:
            self.OnContents(vnum, self.cache[vnum])
            return
        interface = osfInfo.GetInterfaceInstance()
        if not interface or not interface.RequestChestPreview(
                vnum, "dungeon", ui.__mem_func__(self.OnContents)):
            self.OnContents(vnum, {})

    def OnContents(self, vnum, pages):
        if vnum != self.vnum or not self.IsShow() or not self.owner.IsShow():
            return
        self.cache[vnum] = pages
        self.loaded = True
        grouped, ranges = stonecrafting.GroupChestPreview(vnum, pages)
        self.entries = []
        self.grades = {}
        for page in sorted(grouped):
            for slot in sorted(grouped[page]):
                self.grades[len(self.entries)] = ranges.get((page, slot))
                self.entries.append(tuple(grouped[page][slot]))
        self.entries = tuple(self.entries)
        self.status.SetText(localeInfo.DUNGEON_CHEST_UNAVAILABLE)
        self._Refresh()

    def _Refresh(self):
        self.itemTooltip.HideToolTip()
        self.offset = model.clamp_offset(self.offset, len(self.entries))
        visible = model.visible_entries(self.entries, self.offset)
        for index, cell in enumerate(self.cells):
            cell.SetEntry(visible[index] if index < len(visible) else None)
        rows = min(model.VISIBLE_ROWS, (len(self.entries) + model.COLUMNS - 1) // model.COLUMNS)
        height = self.top + max(1, rows) * model.CELL_STEP + 8
        if model.max_offset(len(self.entries)):
            height += 19
            self.scrollHint.Show()
        else:
            self.scrollHint.Hide()
        if self.entries:
            self.status.Hide()
        else:
            self.status.Show()
        self.toolTipHeight = height
        self.ResizeToolTip()
        self._Position()
        # Pooled cell identities do not change on scroll, so the native mouse
        # dispatcher will not send another hover-in for the new reward.
        if self.IsShow():
            x, y = wndMgr.GetMousePosition()
            for cell in self.cells:
                if cell.vnum and cell.IsShow() and contains(cell, x, y):
                    self.OverIn(cell.vnum, cell)
                    break

    def _Position(self):
        if self.anchor:
            x, y = self.anchor.GetGlobalPosition()
            self.SetPosition(*position((x, y, self.anchor.GetWidth()),
                self.GetWidth(), self.GetHeight(), wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()))

    def OverIn(self, vnum, cell=None):
        grade = None
        if cell in self.cells:
            grade = self.grades.get(self.offset * model.COLUMNS + self.cells.index(cell))
        if grade:
            item.SelectItem(vnum)
            self.itemTooltip.ClearToolTip()
            self.itemTooltip.itemVnum = vnum
            self.itemTooltip.SetTitle(item.GetItemName().rsplit("+", 1)[0].rstrip())
            self.itemTooltip.AppendTextLine(localeInfo.CHEST_DROP_GRADE_RANGE % grade)
            self.itemTooltip.ShowToolTip()
        else:
            # Contents are read-only; do not advertise inventory shortcuts or
            # recursively create another chest preview from a nested reward.
            self.itemTooltip.SetItemToolTip(vnum, False)

    def LeaveCell(self):
        self.itemTooltip.HideToolTip()

    def OnMouseWheel(self, length):
        if length:
            self.offset += -1 if length > 0 else 1
            self._Refresh()
        return True

    def OnUpdate(self):
        if not self.vnum or not self.owner.IsShow() or not self.anchor or not self.anchor.IsShow():
            self.Close()
            return
        self._Position()
        now = app.GetTime()
        x, y = wndMgr.GetMousePosition()
        if contains(self, x, y) or contains(self.anchor, x, y):
            self.outsideSince = None
        elif self.outsideSince is None:
            self.outsideSince = now
        elif now - self.outsideSince >= 0.2:
            self.Close()
            return
        if not self.loaded and now >= self.deadline:
            self.loaded = True
            self.status.SetText(localeInfo.DUNGEON_CHEST_UNAVAILABLE)

    def Close(self):
        interface = osfInfo.GetInterfaceInstance()
        if interface:
            interface.CancelChestPreview("dungeon")
        if self.itemTooltip:
            self.itemTooltip.HideToolTip()
        self.vnum = 0
        self.anchor = None
        self.outsideSince = None
        self.Hide()

    def ResetScope(self):
        self.Close()
        self.cache.clear()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.ResetScope()
        for cell in self.cells:
            cell.Destroy()
        self.cells = []
        self.entries = ()
        self.grades = {}
        self.itemTooltip = None
        self.title = None
        self.subtitle = None
        self.status = None
        self.scrollHint = None
        self.owner = None
