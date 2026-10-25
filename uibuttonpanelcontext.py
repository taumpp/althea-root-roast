# -*- coding: utf-8 -*-
"""Small context menu of the configurable button panels (right click / Shift+click).

A float window with one Crimson button per entry; a transparent full-screen
layer behind it closes the menu on any outside click. Entries are
``(label, callback)`` pairs, so the menu is shared by every panel.

In the R1 look (not Settings -> "Starý vzhled") the same window draws the R1
frame with lightly rounded rows (``uir1menu.MenuPanel``); a failure there is
traced and this original menu is used for the rest of the session.
"""
import ui
import wndMgr
import uicrimsoncontrols as crimson
import fontconfig

ROW = 25
WIDTH = 184


class _Dismiss(ui.Window):
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = owner

    def OnMouseLeftButtonDown(self):
        if self.owner:
            self.owner.Close()
        return True

    def OnMouseRightButtonDown(self):
        return self.OnMouseLeftButtonDown()


class ContextMenu(ui.Window):
    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.dismiss = _Dismiss(self)
        self.dismiss.AddFlag('float')
        self.background = ui.Bar()
        self.background.SetParent(self)
        self.background.SetPosition(0, 0)
        self.background.AddFlag('not_pick')
        # Signed 32-bit ARGB, as wndMgr expects (see uicraftingcontrols.packed_color).
        self.background.SetColor(0xf0171410 - 0x100000000)
        self.background.Show()
        self.buttons = []
        self.r1 = None

    def Destroy(self):
        self.Close()
        self.dismiss.owner = None
        self.buttons = []
        if self.r1 is not None:
            self.r1.Destroy()
            self.r1 = None

    def _R1Layout(self, entries):
        """Height of the R1 menu laid out for ``entries``, or None for the original look (Starý vzhled, failure)."""
        try:
            import uir1menu
        except Exception:
            return None
        try:
            if not uir1menu.UseR1():
                if self.r1 is not None:
                    self.r1.Hide()
                return None
            if self.r1 is None:
                self.r1 = uir1menu.MenuPanel(self)
            return self.r1.Layout(entries, WIDTH, self._Run)
        except Exception:
            uir1menu.Failed()
            if self.r1 is not None:
                self.r1.Hide()
            return None

    def Open(self, entries, position):
        entries = list(entries)
        for button in self.buttons:
            button.Hide()
        height = self._R1Layout(entries)
        if height is not None:
            self.background.Hide()
            self._Place(height, position)
            return
        self.background.Show()
        while len(self.buttons) < len(entries):
            button = ui.Button()
            button.SetParent(self)
            crimson.ApplyVisuals(button, '176x21')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
            self.buttons.append(button)
        for index, (label, callback) in enumerate(entries):
            button = self.buttons[index]
            button.SetPosition(4, 4 + index * ROW)
            button.SetText(label)
            button.SetEvent(lambda chosen=callback: self._Run(chosen))
            button.Show()
        height = 8 + len(entries) * ROW - 4
        self.background.SetSize(WIDTH, height)
        self._Place(height, position)

    def _Place(self, height, position):
        self.SetSize(WIDTH, height)
        screen_w, screen_h = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        x = max(0, min(int(position[0]), screen_w - WIDTH))
        y = max(0, min(int(position[1]), screen_h - height))
        self.dismiss.SetPosition(0, 0)
        self.dismiss.SetSize(screen_w, screen_h)
        self.dismiss.Show()
        self.dismiss.SetTop()
        self.SetPosition(x, y)
        self.Show()
        self.SetTop()

    def Close(self):
        self.dismiss.Hide()
        self.Hide()
        return True

    def OnPressEscapeKey(self):
        return self.Close()

    def _Run(self, callback):
        self.Close()
        if callback:
            callback()
