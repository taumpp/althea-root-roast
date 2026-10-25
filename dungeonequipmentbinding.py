"""Presentation of server-owned physical-item dungeon bindings."""
import math
import time

import app
import localeInfo
import net
import player

LOCK_IMAGE = "d:/ymir work/ui/game/crimson_ember/mount_system/glyph_lock_8.png"


def _integer(value, maximum):
    value = int(value)
    if value < 0 or value > maximum:
        raise ValueError("binding value out of range")
    return value


def _window(window):
    return player.INVENTORY if window == player.EQUIPMENT else window


class Receiver(object):
    def __init__(self):
        self.owner = None
        self.Reset()

    def BeginSession(self, owner):
        self.owner = owner
        self.Reset()

    def Owns(self, owner):
        return owner is not None and self.owner is owner

    def EndSession(self, owner):
        if self.Owns(owner):
            self.Reset()
            self.owner = None

    def Reset(self):
        self.available = False
        self.known = True
        self.rows = {}
        self.staging = None
        self.serverTime = 0
        self.receivedAt = 0.0
        self.nextExpiry = 0

    def Offer(self):
        self.Reset()
        self.available = True
        net.SendChatPacket("/dungeon_equipment_ui 1")

    def Begin(self, serial, known, serverTime):
        try:
            serial = _integer(serial, 0x7fffffff)
            known = _integer(known, 1)
            serverTime = _integer(serverTime, 0x7fffffffffffffff)
            if not serial or not serverTime:
                raise ValueError("missing snapshot identity")
            self.staging = [serial, bool(known), serverTime, {}]
        except (TypeError, ValueError, OverflowError):
            self.staging = None

    def Slot(self, serial, window, cell, vnum, pending, until):
        try:
            serial = _integer(serial, 0x7fffffff)
            window = _window(_integer(window, 255))
            cell = _integer(cell, 65535)
            vnum = _integer(vnum, 0xffffffff)
            pending = _integer(pending, 1)
            until = _integer(until, 0x7fffffffffffffff)
            if self.staging is None or self.staging[0] != serial:
                return
            rows = self.staging[3]
            if not self.staging[1] or not vnum or (window, cell) in rows or len(rows) >= 2048:
                raise ValueError("invalid binding snapshot row")
            rows[window, cell] = (vnum, bool(pending), until)
        except (TypeError, ValueError, OverflowError):
            self.staging = None

    def End(self, serial):
        try:
            serial = _integer(serial, 0x7fffffff)
        except (TypeError, ValueError, OverflowError):
            return False
        if self.staging is None or self.staging[0] != serial:
            return False
        unused, self.known, self.serverTime, self.rows = self.staging
        self.receivedAt = app.GetTime()
        self.staging = None
        self._NextExpiry()
        return True

    def Now(self):
        return self.serverTime + max(0.0, app.GetTime() - self.receivedAt)

    def Get(self, window, cell, vnum):
        if not self.available:
            return None
        if not self.known:
            return (2, 0)
        row = self.rows.get((_window(window), cell))
        if row is None or row[0] != vnum:
            return None
        if row[1]:
            return (1, row[2])
        return (0, row[2]) if row[2] > self.Now() else None

    def _NextExpiry(self):
        deadlines = [row[2] for row in self.rows.values() if not row[1]]
        self.nextExpiry = min(deadlines) if deadlines else 0

    def Expire(self):
        if not self.nextExpiry or self.nextExpiry > self.Now():
            return False
        expired = [key for key, row in self.rows.items() if not row[1] and row[2] <= self.Now()]
        for key in expired:
            del self.rows[key]
        self._NextExpiry()
        return bool(expired)


receiver = Receiver()



def _equipmentTypes(item):
    return tuple(getattr(item, name, -1) for name in (
        "ITEM_TYPE_WEAPON", "ITEM_TYPE_ARMOR", "ITEM_TYPE_COSTUME", "ITEM_TYPE_UNIQUE",
        "ITEM_TYPE_ROD", "ITEM_TYPE_PICK", "ITEM_TYPE_DS", "ITEM_TYPE_SPECIAL_DS",
        "ITEM_TYPE_RING", "ITEM_TYPE_BELT", "ITEM_TYPE_MOUNT_EQUIPMENT", "ITEM_TYPE_SHAMAN"))

def HideWindow(overlays, slotWindow):
    for key, overlay in overlays.items():
        if key[0] == id(slotWindow):
            overlay.Hide()


def Clear(overlays):
    for overlay in overlays.values():
        overlay.Hide()
    overlays.clear()


def SetOverlay(overlays, slotWindow, visibleSlot, sourceSlot, vnum, window=None):
    import ui
    import item
    key = (id(slotWindow), visibleSlot)
    overlay = overlays.get(key)
    if overlay:
        overlay.Hide()
    if not vnum or receiver.Get(player.INVENTORY if window is None else window, sourceSlot, vnum) is None:
        return
    item.SelectItem(vnum)
    if not receiver.known and item.GetItemType() not in _equipmentTypes(item):
        return
    position = slotWindow.GetSlotLocalPosition(visibleSlot)
    if position is None:
        return
    if not overlay:
        overlay = ui.ImageBox()
        overlay.SetParent(slotWindow)
        overlay.AddFlag("not_pick")
        overlay.LoadImage(LOCK_IMAGE)
        overlays[key] = overlay
    overlay.SetPosition(int(position[0]) + 2, int(position[1]) + 2)
    overlay.Show()


def AppendTooltip(tooltip, window, cell, vnum):
    state = receiver.Get(window, cell, vnum)
    if state is None:
        return
    if state[0] == 2:
        import item
        item.SelectItem(vnum)
        if item.GetItemType() not in _equipmentTypes(item):
            return
    tooltip.AppendSpace(5)
    tooltip.AutoAppendNewTextLineResize(localeInfo.DUNGEON_EQUIPMENT_LOCK_TITLE, tooltip.NEGATIVE_COLOR)
    if state[0] == 2:
        tooltip.AutoAppendNewTextLineResize(localeInfo.DUNGEON_EQUIPMENT_LOCK_UNAVAILABLE, tooltip.NEGATIVE_COLOR)
    elif state[0] == 1:
        tooltip.AutoAppendNewTextLineResize(localeInfo.DUNGEON_EQUIPMENT_LOCK_PENDING, tooltip.NEGATIVE_COLOR)
    else:
        absolute = time.strftime("%d.%m.%Y %H:%M:%S", time.localtime(state[1]))
        tooltip.AutoAppendNewTextLineResize(localeInfo.DUNGEON_EQUIPMENT_LOCK_UNTIL % absolute, tooltip.NORMAL_COLOR)
        line = tooltip.AutoAppendNewTextLineResize("", tooltip.NEGATIVE_COLOR)
        tooltip.dungeonBindingCountdown = (state[1], line, None)
        UpdateTooltip(tooltip)
    tooltip.ResizeToolTip()


def UpdateTooltip(tooltip):
    countdown = getattr(tooltip, "dungeonBindingCountdown", None)
    if not countdown:
        return
    until, line, previous = countdown
    remaining = max(0, int(math.ceil(until - receiver.Now())))
    if remaining == previous:
        return
    hours, rest = divmod(remaining, 3600)
    minutes, seconds = divmod(rest, 60)
    line.SetText(localeInfo.DUNGEON_EQUIPMENT_LOCK_REMAINING % (hours, minutes, seconds))
    tooltip.dungeonBindingCountdown = (until, line, remaining)
