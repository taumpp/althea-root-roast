"""Interface-owned silent delivery; existing systems remain the event owners."""
import re
import weakref

import app
import item
import player
import ui
import wndMgr
import systemnotificationmodel as model
from systemnotificationlocale import Text, SwitchbotMessage
from uisystemnotifications import Bell, MessageWindow, SettingsWindow


def SwitchbotSlot(message):
    # This exact suffix is emitted by new_switchbot.cpp. Other translations
    # retain the complete message but do not select a guessed inventory slot.
    match = re.search(r"\(Slot: ([1-6])\) successfully finished\.$", str(message))
    return int(match.group(1)) - 1 if match else -1


class NotificationManager:
    def __init__(self, interface):
        self.interface = weakref.proxy(interface)
        self.store = model.NotificationStore(str(player.GetName() or ""))
        self.suspended = True
        self.destroyed = False
        self.lastRevision = -1
        self.lastLayout = None
        self.nextTick = 0.0
        self.bell = Bell(ui.__mem_func__(self.ToggleInbox))
        self.inbox = MessageWindow(ui.__mem_func__(self.Activate),
                                   ui.__mem_func__(self.MarkAllRead),
                                   ui.__mem_func__(self.OpenSettings),
                                   ui.__mem_func__(self.Refresh))
        self.settings = SettingsWindow(ui.__mem_func__(self.ApplyPreferences),
                                        ui.__mem_func__(self.OpenInbox))

    def _Screen(self):
        width, height = int(wndMgr.GetScreenWidth()), int(wndMgr.GetScreenHeight())
        usable = height
        taskbar = getattr(self.interface, "wndTaskBar", None)
        if taskbar:
            unused, top = taskbar.GetGlobalPosition()
            if 216 < top < height:
                usable = int(top)
        return width, height, usable

    def Dock(self):
        width, height, usable = self._Screen()
        y = 170 * height // 600
        minimap = getattr(self.interface, "wndMiniMap", None)
        if minimap and minimap.IsShow():
            children = [getattr(minimap, name, None) for name in
                        ("serverInfo", "positionInfo", "observerCount", "statusNotice")]
            if minimap.IsChild("StatusPennant"):
                children.append(minimap.GetChild("StatusPennant"))
            for child in children:
                if child and child.IsShow():
                    unused, top = child.GetGlobalPosition()
                    height = child.GetHeight()
                    if isinstance(child, ui.TextLine):
                        height = max(height, child.GetTextSize()[1])
                    y = max(y, int(top + height) + 12)
        return max(4, width - 74), max(4, min(y, usable - 53))

    def DockReserved(self):
        return not self.suspended and self.store.unread_count() > 0

    def Tick(self):
        if self.destroyed or self.suspended:
            return
        now = app.GetTime()
        if now >= self.nextTick:
            self.nextTick = now + 0.25
            self.Refresh()

    def Refresh(self):
        if self.destroyed:
            return
        unread = self.store.unread_count()
        if self.lastRevision != self.store.revision:
            self.lastRevision = self.store.revision
            self.bell.SetUnread(unread)
            self.inbox.SetEntries(self.store.entries)
        visible = unread > 0 and not self.suspended
        self.bell.Show() if visible else self.bell.Hide()
        layout = self._Screen() + self.Dock() + (visible,)
        if layout != self.lastLayout:
            self.lastLayout = layout
            self.bell.SetPosition(*self.Dock())
            if self.inbox.IsShow():
                x, y = self.inbox.GetLocalPosition()
                # Reflow existing open panel on resize; SetTop is reserved for
                # explicit opening, so a new event cannot steal foreground.
                self.inbox.Reflow(layout[2])
                self.inbox.Clamp(x, y, layout[2])
            if self.settings.IsShow():
                self.settings.Clamp(*self.settings.GetLocalPosition(), usable_height=layout[2])
            self.interface.ArrangeMessageDock()

    def Resume(self):
        self.suspended = False
        self.nextTick = 0.0
        self.Refresh()

    def Suspend(self):
        self.suspended = True
        self.bell.Hide()
        self.inbox.HideHint()
        self.inbox.Hide()
        self.settings.Close()
        self.lastLayout = None

    def IsHUDEnabled(self, category):
        return self.store.hud_enabled(category)

    def ApplyPreferences(self, preferences):
        previous = dict(self.store.preferences)
        if not self.store.apply_preferences(preferences):
            return False
        reveal = any(self.store.preferences[key] and not previous[key]
                     for key in ("biolog_hud", "dungeon_hud"))
        self.interface.RefreshCountdownHUDSelection(reveal)
        self.Refresh()
        return True

    def OpenSettings(self):
        if not self.suspended:
            self.interface.OpenSystemNotificationSettings()

    def ToggleInbox(self):
        if self.inbox.IsShow():
            self.inbox.Close()
        else:
            self.OpenInbox()

    def OpenInbox(self):
        if self.suspended:
            return
        self.Refresh()
        x, y = self.Dock()
        self.inbox.OpenAt(x - self.inbox.WIDTH - 12, y - 4, self._Screen()[2])

    def MarkAllRead(self):
        self.store.mark_all_read()
        self.Refresh()

    def Activate(self, identity):
        entry = self.store.find(identity)
        if not entry or self.suspended:
            return
        self.store.mark_read(identity)
        self.Refresh()
        category = entry["category"]
        if category == "biolog":
            window = getattr(self.interface, "wndBio", None)
            if window:
                window.Show()
                window.SetTop()
        elif category == "dungeon" and getattr(app, "ENABLE_DUNGEON_INFO", False):
            self.interface.OpenDungeonInfo()
            atlas = getattr(self.interface, "wndTeleportAtlas", None)
            page = getattr(atlas, "dungeonPage", None)
            if page:
                page.OpenTrackedDungeon(entry["target"])
        elif category == "switchbot":
            window = getattr(self.interface, "wndSwitchbot", None)
            if window:
                window.Open()
                if entry["target"] >= 0:
                    import bonuscatalog
                    import switchbot
                    if entry["target"] < switchbot.SLOT_COUNT and bonuscatalog.IsSlotAllowed(entry["target"]):
                        window.SelectSlot(entry["target"])

    def _Add(self, category, title, message, icon_vnum, target, key=""):
        accepted = self.store.add(category, title, message, icon_vnum, target,
                                  int(app.GetGlobalTimeStamp()), key)
        self.Refresh()
        return accepted

    def AddBiolog(self, title, message, icon_vnum, signature=None):
        key = ""
        if isinstance(signature, (tuple, list)) and len(signature) == 3:
            key = "biolog:%s:%s" % (signature[1], signature[2])
        if icon_vnum:
            try:
                item.SelectItem(icon_vnum)
                title = item.GetItemName() or title
            except (RuntimeError, OSError):
                pass
        return self._Add("biolog", title, message, icon_vnum, -1, key)

    def AddDungeon(self, title, message, boss_vnum, cooldown_end=None):
        import uiDungeonTrack
        title = uiDungeonTrack.dungeonData.get(boss_vnum, {}).get("name", title)
        key = "dungeon:%s:%s" % (boss_vnum, cooldown_end) if cooldown_end is not None else ""
        return self._Add("dungeon", title, Text("READY_DUNGEON"), 0, boss_vnum, key)

    def AddSwitchbot(self, message):
        slot = SwitchbotSlot(message)
        title = Text("SLOT_FORMAT") % (slot + 1) if slot >= 0 else Text("SWITCHBOT")
        return self._Add("switchbot", title, SwitchbotMessage(message), 71084, slot)

    def Destroy(self):
        self.Suspend()
        self.destroyed = True
        self.store.save()
        self.bell.Destroy()
        self.inbox.Destroy()
        self.settings.Destroy()
        self.bell = self.inbox = self.settings = None
        self.interface = None
