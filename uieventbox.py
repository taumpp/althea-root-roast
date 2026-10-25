# -*- coding: utf-8 -*-
"""Moonlight Box event, compact R1 presentation of EventBoxV1 (ordered reward preview)."""
import app
import item
import localeInfo
import net
import player
import ui
import wndMgr
import weakref
import pvmhudposition
import uir1
import uir1tokens as T
import eventboxmodel as model

COLS, PER_PAGE, CELL_W, CELL_H = 8, 32, 96, 80
PAD = T.PAD
INNER_W = COLS * CELL_W
WIDTH, HEIGHT = INNER_W + PAD * 2, 600
HEADER_H = 72
GRID_Y = 33 + HEADER_H + 40
_window = None


def _BoxIcon(image, vnum, scale=1.0):
    """Icon of the server-provided box_vnum; nothing hardcoded on the client.
    LoadImage creates a new image instance, so the scale is applied after it."""
    if not vnum or getattr(image, 'eventBoxVnum', None) == vnum:
        return
    item.SelectItem(vnum)
    path = item.GetIconImageFileName()
    if path:
        image.LoadImage(path)
        if scale != 1.0:
            image.SetScale(scale, scale)
        image.eventBoxVnum = vnum


def _FitIcon(image, path, x, y, w, h):
    """Local copy of the R1 icon fit (the public release branch has no uir1.FitIcon)."""
    image.LoadImage(path)
    iw, ih = max(1, image.GetWidth()), max(1, image.GetHeight())
    scale = min(1.0, float(w) / iw, float(h) / ih)
    if scale < 1.0:
        image.SetScale(scale, scale)
    sw, sh = int(iw * scale), int(ih * scale)
    image.SetPosition(int(x) + (int(w) - sw) // 2, int(y) + (int(h) - sh) // 2)


def _T(key):
    return getattr(localeInfo, key, key)


def _Prague(epoch):
    local = model.time.gmtime(epoch + model.PragueOffset(epoch))
    return _T('EVENT_BOX_DATE') % (
        _T('EVENT_BOX_WEEKDAYS').split(',')[local.tm_wday],
        local.tm_mday, local.tm_mon, local.tm_hour, local.tm_min)


def _Duration(seconds):
    hours, rest = divmod(max(0, int(seconds)), 3600)
    return _T('EVENT_BOX_DURATION') % (hours, rest // 60)


class RewardCell(ui.Window):
    def __init__(self, owner, vnum, count, tier):
        ui.Window.__init__(self)
        self.owner, self.vnum = weakref.proxy(owner), vnum
        self.SetParent(owner)
        self.SetSize(CELL_W, CELL_H)
        center = CELL_W // 2
        colors = (0xff514c47, 0xff426246, 0xff405b80, 0xff897344)
        self.border = uir1.Rect(self, center - 17, 0, 34, 34, colors[tier])
        self.slot = uir1.SlotCell(self, center - 16, 1)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        item.SelectItem(vnum)
        _FitIcon(self.icon, item.GetIconImageFileName(), center - 16, 1, 32, 32)
        self.icon.Show()
        self.names = [uir1.Text(self, '', center, 36 + i * 12, owner.kit.font('text_s'),
                      T.IVORY, align='center', valign='top') for i in range(3)]
        name = item.GetItemName()
        limit = CELL_W - 14  # keeps a visible gap between neighbouring names
        # Wrap at word boundaries, splitting only an individually oversized word.
        chunks, current = [], ''
        for word in name.split():
            candidate = (current + ' ' + word).strip()
            self.names[0].SetText(candidate)
            if current and uir1.TextWidth(self.names[0]) > limit:
                chunks.append(current)
                current = ''
            for char in ((' ' if current else '') + word):
                self.names[0].SetText(current + char)
                if current and uir1.TextWidth(self.names[0]) > limit:
                    chunks.append(current)
                    current = char
                else:
                    current += char
        chunks.append(current)
        for i, label in enumerate(self.names):
            label.SetText(chunks[i] if i < len(chunks) else '')
            label.AddFlag('not_pick')
        self.count = uir1.Text(self, _T('EVENT_BOX_QUANTITY') % count if count > 1 else '',
                         center, 36 + min(3, len(chunks)) * 12, owner.kit.font('text_s'), T.MUTED,
                         align='center', valign='top')
        self.count.AddFlag('not_pick')
        self.Show()

    def OnMouseOverIn(self):
        self.owner.ShowItemTooltip(self.vnum)

    def OnMouseOverOut(self):
        self.owner.HideItemTooltip()


class EventBoxWindow(uir1.Window):
    """Compact R1 window: header with term and warning, reward grid, progress, carried boxes.
    Boxes are opened by double-click in the inventory; the window refreshes itself."""
    def __init__(self):
        self.kit = kit = uir1.Kit()
        uir1.Window.__init__(self, kit, WIDTH, HEIGHT, _T('EVENT_BOX_TITLE'))
        self.lastPoll = 0.0
        self.lastSecond = -1
        self.labels = []
        self.headerPanel = uir1.Frame(self, PAD, 33, INNER_W, HEADER_H, 'panel')
        self.headerIcon = ui.ExpandedImageBox()
        self.headerIcon.SetParent(self)
        self.headerIcon.SetPosition(PAD + 10, 33 + (HEADER_H - 32) // 2)
        self.headerIcon.AddFlag('not_pick')
        self.headerIcon.Show()
        self.subtitle = uir1.Text(self, _T('EVENT_BOX_SUBTITLE'), PAD + 52, 40, kit.font('text_b'), T.IVORY, valign='top')
        self.labels.append(self.subtitle)
        self.term = self.Text('', PAD + 52, 60)
        self.expiryLines = [self.Text('', PAD + 52, 0, T.RED_HI) for _ in range(2)]
        self.expiry = self.expiryLines[0]
        self.status = self.Text('', PAD + INNER_W - 10, 40, T.IVORY, align='right')
        self.clock = self.Text('', PAD + INNER_W - 10, 60, align='right')
        self.rewardWidgets = []
        self.rewardKey = None
        self.rewardPage = 0
        self.rewardSection = uir1.Section(self, kit, PAD, GRID_Y - 26, INNER_W, _T('EVENT_BOX_REWARDS'))
        self.rewardNote = self.Text('', PAD, 0, T.MUTED)
        self.previous = uir1.Button(self, kit, WIDTH - PAD - 196, GRID_Y - 32, 96, _T('EVENT_BOX_PREVIOUS'), small=True, event=self.PreviousPage)
        self.next = uir1.Button(self, kit, WIDTH - PAD - 96, GRID_Y - 32, 96, _T('EVENT_BOX_NEXT'), small=True, event=self.NextPage)
        self.hintLines = [self.Text('', PAD, 0, T.RED_HI) for _ in range(4)]
        self.hint = self.hintLines[0]
        self.SetCenterPosition()
        model.RECEIVER.listener = ui.__mem_func__(self.Refresh)
        model.RECEIVER.sender = net.SendChatPacket
        self.Refresh()

    def Text(self, text, x, y, color=T.INK_DIM, align='left', parent=None):
        label = uir1.Text(parent or self, text, x, y, self.kit.font('text_s'), color,
                         align=align, valign='top')
        self.labels.append(label)
        return label

    def Lines(self, labels, texts, x, y, width, pitch=18):
        """Wrap measured native glyphs; no clipping of translated warnings."""
        rows = []
        probe = labels[0]
        for text in texts:
            current = ''
            for word in text.split():
                candidate = (current + ' ' + word).strip()
                probe.SetText(candidate)
                if current and uir1.TextWidth(probe) > width:
                    rows.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                rows.append(current)
        for index, label in enumerate(labels):
            label.SetText(rows[index] if index < len(rows) else '')
            if index < len(rows):
                label.SetPosition(x, y + index * pitch)
                label.Show()
            else:
                label.Hide()
        return y + len(rows) * pitch

    def PreviousPage(self):
        self.Page(-1)

    def NextPage(self):
        self.Page(1)

    def Page(self, delta):
        pages = max(1, (len(model.RECEIVER.loot) + PER_PAGE - 1) // PER_PAGE)
        self.rewardPage = max(0, min(pages - 1, self.rewardPage + delta))
        self.RefreshRewards()

    def HideItemTooltip(self):
        import osfInfo
        interface = osfInfo.GetInterfaceInstance()
        if interface and interface.tooltipItem:
            interface.tooltipItem.HideToolTip()

    def ShowItemTooltip(self, vnum):
        import osfInfo
        interface = osfInfo.GetInterfaceInstance()
        if interface and interface.tooltipItem:
            interface.tooltipItem.SetItemToolTip(vnum)

    def GridBottom(self):
        """Bottom of the reward block (grid + note); GRID_Y - 34 when there are no rewards."""
        rows = model.RECEIVER.loot
        if not rows:
            return GRID_Y - 34
        shown = min(PER_PAGE, len(rows))
        return GRID_Y + (shown + COLS - 1) // COLS * CELL_H + 4 + 18

    def RefreshRewards(self):
        rows = model.RECEIVER.loot
        key = (tuple(rows), self.rewardPage)
        if key == self.rewardKey:
            return
        self.rewardKey = key
        self.HideItemTooltip()
        for widget in self.rewardWidgets:
            widget.Hide()
        self.rewardWidgets = []
        self.rewardPage = min(self.rewardPage, max(0, (len(rows) - 1) // PER_PAGE))
        (self.rewardSection.Show if rows else self.rewardSection.Hide)()
        (self.previous.Show if self.rewardPage > 0 else self.previous.Hide)()
        (self.next.Show if (self.rewardPage + 1) * PER_PAGE < len(rows) else self.next.Hide)()
        self.rewardNote.SetText(_T('EVENT_BOX_REWARD_NOTE') if rows else '')
        self.rewardNote.SetPosition(PAD, self.GridBottom() - 18)
        for index, (vnum, count, tier) in enumerate(rows[self.rewardPage * PER_PAGE:(self.rewardPage + 1) * PER_PAGE]):
            cell = RewardCell(self, vnum, count, tier)
            cell.SetPosition(PAD + index % COLS * CELL_W, GRID_Y + index // COLS * CELL_H)
            self.rewardWidgets.append(cell)

    def Open(self):
        model.RECEIVER.visible = True
        self.Show()
        self.SetTop()
        self.Refresh()
        self.Request()

    def Close(self):
        self.HideItemTooltip()
        model.RECEIVER.Close()
        self.Hide()

    def Destroy(self):
        self.Close()
        model.RECEIVER.listener = None
        model.RECEIVER.sender = None

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Request(self):
        self.lastPoll = app.GetTime()
        model.RECEIVER.Request()

    def OnUpdate(self):
        if not self.IsShow():
            return
        now = app.GetTime()
        if now - self.lastPoll >= model.REFRESH_SECONDS:
            self.Request()
        model.RECEIVER.Pump()
        if int(now) != self.lastSecond:
            self.lastSecond = int(now)
            self.Refresh()

    def EndDate(self, epoch):
        local = model.EndDay(epoch)
        return _T('EVENT_BOX_END_DATE') % (_T('EVENT_BOX_WEEKDAYS').split(',')[local.tm_wday],
                                          local.tm_mday, local.tm_mon)

    def Layout(self, hints):
        y = self.GridBottom() + (6 if hints else 0)
        y = self.Lines(self.hintLines, hints, PAD, y, INNER_W)
        height = y + PAD
        self.SetSize(WIDTH, height)
        self.chrome.frame.Resize(WIDTH, height)

    def Refresh(self):
        if self.IsShow() and not model.RECEIVER.HudVisible():
            self.Close()
            return
        s = model.RECEIVER.state
        self.RefreshRewards()
        if not s.available:
            self.status.SetText(_T('EVENT_BOX_LOADING') if model.RECEIVER.waiting else _T('EVENT_BOX_OFF'))
            for label in self.labels:
                if label not in (self.status, self.subtitle, self.rewardNote):
                    label.SetText('')
            self.Layout([])
            return
        self.subtitle.SetText(_T('EVENT_BOX_SUBTITLE'))
        _BoxIcon(self.headerIcon, s.box_vnum)
        now = s.Now()
        expired = s['phase'] == 2 or now >= s['end']
        before = now < s['start']
        if expired:
            key = 'EVENT_BOX_EXPIRED'
        elif not s['on']:
            key = 'EVENT_BOX_OFF'
        elif before:
            key = 'EVENT_BOX_BEFORE'
        elif s['drop_stop']:
            key = 'EVENT_BOX_DROP_STOP'
        elif s.Capped():
            key = 'EVENT_BOX_CAPPED'
        else:
            key = 'EVENT_BOX_RUNNING'
        self.status.SetText(_T(key))
        self.term.SetText(_T('EVENT_BOX_TERM') % (_Prague(s['start']), self.EndDate(s['end'])))
        self.clock.SetText('' if expired or not s['on'] else
                          _T('EVENT_BOX_START_IN' if before else 'EVENT_BOX_END_IN') %
                          _Duration((s['start'] if before else s['end']) - now))
        hints = []
        if not expired:
            if not s['loot_ok']:
                hints.append(_T('EVENT_BOX_LOOT_OFF'))
            if s['open_stop']:
                hints.append(_T('EVENT_BOX_OPEN_STOP'))
        warning = []
        if not expired:
            day = model.EndDay(s['end'])
            warning.append(_T('EVENT_BOX_DISAPPEAR') % (
                _T('EVENT_BOX_DEADLINE_DAYS').split(',')[day.tm_wday], day.tm_mday, day.tm_mon))
        self.Lines(self.expiryLines, warning, PAD + 52, 80, INNER_W - 52 - 200)
        self.Layout(hints)


HUD_SIZE = 36
HUD_POSITION_DIRECTORY = 'UserData/event_box_hud'


class HudPlate(ui.Window):
    """Click/drag surface of the HUD button (same captured drag as the level104 HUD)."""
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.SetParent(owner)
        self.SetPosition(0, 0)
        self.SetSize(HUD_SIZE, HUD_SIZE)
        self.AddFlag('dragable')
        self.Show()

    def OnMouseLeftButtonDown(self):
        self.owner.BeginDrag()
        return True

    def OnMouseDrag(self, x, y):
        self.owner.Drag()

    def OnMouseLeftButtonUp(self):
        self.owner.EndDrag()
        return True

    def OnMouseOverIn(self):
        self.owner.Hover(True)

    def OnMouseOverOut(self):
        self.owner.Hover(False)


class EventBoxButton(ui.Window):
    """Small square R1 HUD button: only the box icon (name in the hover hint) and the carried
    count. Movable like the other HUD widgets, position saved per character. Never blinks."""
    def __init__(self):
        self.dragOrigin = None   # ui.Window.__init__ calls the virtual Hide()
        self.dragMoved = False
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.kit = uir1.Kit()
        self.SetSize(HUD_SIZE, HUD_SIZE)
        self.border = uir1.Rect(self, 0, 0, HUD_SIZE, HUD_SIZE, T.BORDER)
        self.hover = uir1.Rect(self, 0, 0, HUD_SIZE, HUD_SIZE, T.RED_DK)
        self.hover.Hide()
        self.slot = uir1.SlotCell(self, 2, 2)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.SetPosition(2, 2)
        self.icon.Show()
        self.badgeText = uir1.Text(self, '', HUD_SIZE - 3, HUD_SIZE - 15, self.kit.font('text_s'), T.IVORY,
                                   align='right', valign='top', outline=True)
        self.badgeText.AddFlag('not_pick')
        self.plate = HudPlate(self)
        try:
            self.positionKey = player.GetName()
        except Exception:
            self.positionKey = ''
        self.saved = pvmhudposition.load(self.positionKey, HUD_POSITION_DIRECTORY)
        self.screen = None
        self.nextCount = 0.0
        self.OnUpdate()
        self.Hide()

    def ScreenSize(self):
        return (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

    def DefaultPosition(self, screen):
        # Beside the existing event-calendar mini HUD (screenWidth - 285, y=0), with a gap.
        return (screen[0] - 285 - 8 - HUD_SIZE, 8)

    def Place(self):
        screen = self.ScreenSize()
        if screen == self.screen:
            return
        self.screen = screen
        start = self.saved if self.saved is not None else self.DefaultPosition(screen)
        self.SetPosition(*pvmhudposition.clamp(start, (HUD_SIZE, HUD_SIZE), screen))

    def Hover(self, inside):
        (self.hover.Show if inside else self.hover.Hide)()
        (self.border.Hide if inside else self.border.Show)()
        if inside:
            uir1.ShowHint(self.kit, self, _T('EVENT_BOX_TITLE'))
        else:
            uir1.HideHint(self)

    def BeginDrag(self):
        self.SetTop()
        self.dragOrigin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
        self.dragMoved = False

    def Drag(self):
        if self.dragOrigin is None:
            return
        (mx, my), (x, y) = self.dragOrigin
        nx, ny = wndMgr.GetMousePosition()
        if not self.dragMoved and abs(nx - mx) + abs(ny - my) < 4:
            return
        position = pvmhudposition.clamp((x + nx - mx, y + ny - my), (HUD_SIZE, HUD_SIZE), self.ScreenSize())
        if position != self.GetGlobalPosition():
            self.SetPosition(*position)
            self.saved = position
            self.dragMoved = True

    def EndDrag(self):
        if self.dragOrigin is None:
            return
        self.dragOrigin = None
        if self.dragMoved:
            if self.saved is not None:
                pvmhudposition.save(self.positionKey, self.saved, HUD_POSITION_DIRECTORY)
        else:
            Toggle()
        self.dragMoved = False

    def OnUpdate(self):
        self.Place()
        now = app.GetTime()
        if now < self.nextCount:
            return
        self.nextCount = now + 0.5
        state = model.RECEIVER.state
        _BoxIcon(self.icon, state.box_vnum if state.available else 0)
        count = sum(player.GetItemCount(slot) for slot in self.InventorySlots()
                    if state.box_vnum and player.GetItemIndex(slot) == state.box_vnum)
        self.badgeText.SetText(str(count) if count > 0 else '')

    def InventorySlots(self):
        slots = list(range(player.INVENTORY_PAGE_COUNT * player.INVENTORY_PAGE_SIZE))
        if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
            slots.extend(range(item.GIFT_BOX_INVENTORY_SLOT_START, item.GIFT_BOX_INVENTORY_SLOT_START +
                               player.SPECIAL_INVENTORY_PAGE_COUNT * player.SPECIAL_INVENTORY_PAGE_SIZE))
        return slots


def Toggle():
    global _window
    if not model.RECEIVER.HudVisible():
        # Server switch ui_enabled / ebox_ui is off: no window (code kept for later).
        Close()
        return
    if _window is None:
        try:
            _window = EventBoxWindow()
        except Exception:
            uir1.TraceFailure('eventbox')
            return
    if _window.IsShow():
        _window.Close()
    else:
        _window.Open()


def Close():
    if _window is not None:
        _window.Close()


def Destroy():
    global _window
    if _window is not None:
        _window.Destroy()
    _window = None
    # No state or callback may survive a character/session change.
    model.RECEIVER = model.Receiver()
