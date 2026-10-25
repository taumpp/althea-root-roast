"""Native component views for the approved A3 Crimson notification bell."""
import time
import weakref

import app
import fontconfig
import item
import ui
import uiToolTip
import wndMgr
from countdownmodel import fit_text
from systemnotificationlocale import Text, SwitchbotMessage
from uicrimsonember import SettingsScrollBar

ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/system_notifications/"
HUD_ROOT = "d:/ymir work/ui/game/crimson_ember/countdown_hud/"
GEAR = "d:/ymir work/ui/game/crimson_ember/messenger/icon/settings.png"
BUTTON_ROOT = "d:/ymir work/ui/public/crimson/controls/unified/button_100x21_"
INK = (0.918, 0.886, 0.827)
DIM = (0.686, 0.651, 0.596)
GOLD = (0.89, 0.71, 0.44)
JADE = (0.58, 0.76, 0.67)
CATEGORY_STYLE = {"biolog": ("BIOLOG", 0xFF172820, JADE),
                  "dungeon": ("DUNGEONS", 0xFF2A2117, GOLD),
                  "switchbot": ("SWITCHBOT", 0xFF23201E, INK)}


def _Line(parent, x, y, text="", role=fontconfig.ROLE_BODY, color=INK, align="left"):
    line = ui.TextLine()
    line.SetParent(parent)
    line.AddFlag("not_pick")
    line.SetFontName(fontconfig.FontForRole(role))
    line.SetPosition(x, y)
    if align == "right":
        line.SetHorizontalAlignRight()
    elif align == "center":
        line.SetHorizontalAlignCenter()
    line.SetText(str(text))
    line.SetFontColor(*color)
    line.Show()
    return line


def _Fit(line, text, width):
    def measure(candidate):
        line.SetText(candidate)
        return line.GetTextSize()[0]
    line.SetText(fit_text(str(text), width, measure))


def _Image(parent, path, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag("not_pick")
    image.LoadImage(path)
    image.SetPosition(x, y)
    image.Show()
    return image


def _Bar(parent, x, y, width, height, color):
    bar = ui.Bar()
    bar.SetParent(parent)
    bar.AddFlag("not_pick")
    bar.SetPosition(x, y)
    bar.SetSize(width, height)
    bar.SetColor(color)
    bar.Show()
    return bar


def DisplayEntry(entry):
    """The entry as a row shows it. Old stored Switchbot results share the same typed category: a display copy is
    translated so history and its navigation target stay intact."""
    if entry["category"] == "switchbot":
        entry = dict(entry)
        entry["message"] = SwitchbotMessage(entry["message"])
    return entry


def IconPath(entry):
    """The icon file of a row (item icon, dungeon portrait, Switchbot item) or "" for no icon."""
    path = ""
    if entry["category"] == "switchbot":
        path = "icon/item/71084.tga"
    elif entry["category"] == "dungeon":
        path = HUD_ROOT + "portrait/%d_41x32.png" % entry["target"]
        if not app.IsExistFile(path):
            path = HUD_ROOT + "dungeon_normal.png"
    elif entry["icon_vnum"]:
        try:
            item.SelectItem(entry["icon_vnum"])
            path = item.GetIconImageFileName()
        except (RuntimeError, OSError):
            pass
    return path


def _BuildR1(window):
    """The R1 look of the message window (uisystemnotificationsr1) or None for the original look ("Starý vzhled",
    or R1 failed: then the original look is already back)."""
    try:
        import uisystemnotificationsr1
    except Exception:
        return None
    return uisystemnotificationsr1.Build(window)


def _Button(parent, x, y, caption, callback):
    button = ui.Button()
    button.SetParent(parent)
    for setter, state in ((button.SetUpVisual, "normal"), (button.SetOverVisual, "hover"),
                          (button.SetDownVisual, "pressed"), (button.SetDisableVisual, "disabled")):
        setter(BUTTON_ROOT + state + ".png")
    button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
    button.SetText(caption)
    button.SetPosition(x, y)
    button.SetEvent(callback)
    button.Show()
    return button


class SettingsLink(ui.Window):
    """Native-size gear and optional caption; the tight hit box has visible states."""
    def __init__(self, parent, callback, caption=True):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.callback = callback
        self.pressed = False
        self.SetSize(118 if caption else 20, 21)
        self.icon = _Image(self, GEAR, 0, 0)
        self.label = _Line(self, 26, 3, Text("SETTINGS"), color=DIM) if caption else None
        self._State(0.85, DIM)
        self.Show()

    def _State(self, factor, color):
        self.icon.SetDiffuseColor(factor, factor, factor, 1.0)
        if self.label:
            self.label.SetFontColor(*color)

    def OnMouseOverIn(self):
        self._State(1.0, GOLD)

    def OnMouseOverOut(self):
        self.pressed = False
        self._State(0.85, DIM)

    def OnMouseLeftButtonDown(self):
        self.pressed = True
        self._State(0.75, DIM)
        return True

    def OnMouseLeftButtonUp(self):
        pressed = self.pressed
        self.pressed = False
        self._State(1.0, GOLD)
        if pressed and self.callback:
            self.callback()
        return True

    def Destroy(self):
        self.Hide()
        self.callback = None
        self.icon = None
        self.label = None


class Bell(ui.Window):
    def __init__(self, callback):
        # Like classic PMs, keep the entire icon and badge above normal windows.
        ui.Window.__init__(self, "TOP_MOST")
        self.AddFlag("float")
        self.AddFlag("not_pick")
        self.SetSize(49, 40)
        self.button = ui.Button()
        self.button.SetParent(self)
        for setter, state in ((self.button.SetUpVisual, "normal"),
                              (self.button.SetOverVisual, "hover"),
                              (self.button.SetDownVisual, "pressed"),
                              (self.button.SetDisableVisual, "disabled")):
            setter(ASSET_ROOT + "bell_" + state + ".png")
        self.button.SetEvent(callback)
        # Same native blink as unread PMs; the manager owns unread visibility.
        self.button.Flash()
        self.button.Show()
        self.badge = _Image(self, ASSET_ROOT + "unread_17x17.png", 32, 0)
        # The badge is authored for this fixed native font, independent of the
        # player's body-text preference; it is never a scaled bitmap number.
        self.count = _Line(self, 40, 1, role=fontconfig.ROLE_DENSE, align="center")
        self.count.SetFontName("Tahoma:11")
        self.SetUnread(0)
        self.Hide()

    def SetUnread(self, count):
        count = max(0, min(50, int(count)))
        self.count.SetText(str(count))
        self.count.SetFontColor(*INK)
        for child in (self.badge, self.count):
            child.Show() if count else child.Hide()
        self.button.SetToolTipText(Text("BELL_HINT") % count)

    def Destroy(self):
        self.Hide()
        self.button.SetEvent(None)
        self.button.HideToolTip()
        self.button = self.badge = self.count = None


class _Frame(ui.Window):
    """Board and titlebar retain their fixed native corners and one outer width."""
    INSET = 4  # the R1 look draws its frame over the whole width (uisystemnotificationsr1)

    def __init__(self, width, height, title):
        ui.Window.__init__(self)
        self.AddFlag("movable")
        self.AddFlag("float")
        self.board = ui.Board()
        self.board.SetParent(self)
        self.board.SetPosition(self.INSET, 0)
        self.board.AddFlag("not_pick")
        self.board.Show()
        self.titleBar = ui.TitleBar()
        self.titleBar.SetParent(self)
        self.titleBar.MakeTitleBar(width, "red")
        self.titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        self.titleBar.Show()
        self.titleName = _Line(self.titleBar, width // 2, 3, title,
                               fontconfig.ROLE_WINDOW_TITLE, align="center")
        self.SetSize(width, height)

    def SetSize(self, width, height):
        ui.Window.SetSize(self, width, height)
        self.board.SetPosition(self.INSET, 0)
        self.board.SetSize(width - 2 * self.INSET, height)
        self.titleBar.SetWidth(width)
        self.titleName.SetPosition(width // 2, 3)
        r1 = self.__dict__.get("r1")
        if r1:
            r1.Layout(width, height)

    def Clamp(self, x, y, usable_height):
        self.SetPosition(max(4, min(int(x), wndMgr.GetScreenWidth() - self.GetWidth() - 4)),
                         max(4, min(int(y), usable_height - self.GetHeight() - 4)))

    def OnPressEscapeKey(self):
        self.Close()
        return True


class _MessageRow(ui.Window):
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = weakref.proxy(owner)
        self.SetParent(owner)
        self.identity = None
        self.entry = None
        self.pressed = False
        self.band = _Bar(self, 0, 0, 304, 23, 0xFF23201E)
        self.category = _Line(self, 11, 3, role=fontconfig.ROLE_SECTION)
        self.stamp = _Line(self, 293, 3, color=DIM, align="right")
        self.icon = ui.ImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag("not_pick")
        self.name = _Line(self, 54, 31, role=fontconfig.ROLE_CONTROL)
        self.message = _Line(self, 54, 51, color=DIM)
        self.openLabel = _Line(self, 293, 31, Text("OPEN"), color=GOLD, align="right")

    def SetEntry(self, entry, width):
        entry = DisplayEntry(entry)
        self.entry = entry
        self.identity = entry["id"]
        self.SetSize(width, 76)
        category, color, ink = CATEGORY_STYLE[entry["category"]]
        self.band.SetSize(width, 23)
        self.band.SetColor(color)
        self.category.SetText(Text(category))
        self.category.SetFontColor(*ink)
        self.stamp.SetPosition(width - 11, 3)
        self.stamp.SetText(time.strftime("%H:%M", time.localtime(entry["created"])))
        self.stamp.SetFontColor(*DIM)
        self.openLabel.SetPosition(width - 11, 31)
        self.openLabel.SetFontColor(*(GOLD if not entry["read"] else DIM))
        open_width = self.openLabel.GetTextSize()[0]
        _Fit(self.category, Text(category), width - self.stamp.GetTextSize()[0] - 32)
        _Fit(self.name, entry["title"], width - 54 - open_width - 23)
        self.name.SetFontColor(*(INK if not entry["read"] else DIM))
        _Fit(self.message, entry["message"], width - 65)
        self.icon.Hide()
        path = IconPath(entry)
        if path:
            try:
                self.icon.LoadImage(path)
                self.icon.SetPosition(4 + (41 - self.icon.GetWidth()) // 2,
                                      32 + (32 - self.icon.GetHeight()) // 2)
                self.icon.Show()
            except (RuntimeError, OSError):
                pass
        self.Show()

    def OnMouseOverIn(self):
        self.openLabel.SetFontColor(*GOLD)
        if self.entry:
            self.owner.ShowHint(self.entry["title"] + "\n" + self.entry["message"])

    def OnMouseOverOut(self):
        self.pressed = False
        self.owner.HideHint()
        if self.entry:
            self.openLabel.SetFontColor(*(DIM if self.entry["read"] else GOLD))

    def OnMouseLeftButtonDown(self):
        self.pressed = True
        self.openLabel.SetFontColor(*DIM)
        return True

    def OnMouseLeftButtonUp(self):
        pressed = self.pressed
        self.pressed = False
        self.owner.HideHint()
        if pressed and self.identity is not None:
            self.owner.Activate(self.identity)
        return True

    def OnMouseWheel(self, delta):
        return self.owner.OnMouseWheel(delta)

    def Destroy(self):
        self.Hide()
        self.owner = self.entry = None
        self.band = self.category = self.stamp = self.icon = None
        self.name = self.message = self.openLabel = None


class MessageWindow(_Frame):
    WIDTH = 332
    ROW_HEIGHT = 80
    LIST_TOP = 34
    FOOTER = 42
    # The rest of the geometry. The R1 look (uisystemnotificationsr1) sets its own values on the instance and
    # deletes them again when it falls back to the original look.
    ROW_X = 14
    ROW_WIDTH = 304
    ROW_WIDTH_SCROLL = 288
    SCROLL_X = 306
    FOOTER_Y = 30  # distance of the footer controls from the bottom edge
    SETTINGS_X = 20
    READ_X = 218

    def __init__(self, activate_callback, read_all_callback, settings_callback, close_callback):
        _Frame.__init__(self, self.WIDTH, 316, Text("TITLE"))
        self.activate_callback = activate_callback
        self.close_callback = close_callback
        self.read_all_callback = read_all_callback
        self.settings_callback = settings_callback
        self.entries = []
        self.offset = 0
        self.capacity = 3
        self.rows = [_MessageRow(self) for unused in range(3)]
        self.scroll = SettingsScrollBar()
        self.scroll.SetParent(self)
        self.scroll.SetScrollEvent(ui.__mem_func__(self._Scroll))
        self.scroll.Hide()
        self.settings = SettingsLink(self, settings_callback)
        self.readAll = _Button(self, 218, 286, Text("MARK_ALL_READ"), read_all_callback)
        self.empty = _Line(self, self.WIDTH // 2, 69, Text("EMPTY"), color=DIM, align="center")
        self.tooltip = uiToolTip.ToolTip()
        self.tooltip.SetDefaultFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        self.measure = _Line(self, 0, 0)
        self.measure.Hide()
        self.r1 = _BuildR1(self)
        self.Hide()

    def SetEntries(self, entries):
        self.HideHint()
        self.entries = [dict(entry) for entry in entries]
        self.offset = min(self.offset, max(0, len(self.entries) - self.capacity))
        self._LayoutRows()

    def _LayoutRows(self):
        overflow = max(0, len(self.entries) - self.capacity)
        width = self.ROW_WIDTH_SCROLL if overflow else self.ROW_WIDTH
        for index, row in enumerate(self.rows):
            position = self.offset + index
            if index < self.capacity and position < len(self.entries):
                row.SetPosition(self.ROW_X, self.LIST_TOP + index * self.ROW_HEIGHT)
                row.SetEntry(self.entries[position], width)
            else:
                row.Hide()
        self.empty.Hide() if self.entries else self.empty.Show()
        if overflow:
            self.scroll.SetPosition(self.SCROLL_X, self.LIST_TOP)
            self.scroll.SetScrollBarSize(self.capacity * self.ROW_HEIGHT - 4)
            self.scroll.SetMiddleBarSize(float(self.capacity) / len(self.entries))
            self.scroll.SetScrollStep(1.0 / overflow)
            self.scroll.SetPos(float(self.offset) / overflow, False)
            self.scroll.Show()
        else:
            self.scroll.Hide()
        y = self.GetHeight() - self.FOOTER_Y
        self.settings.SetPosition(self.SETTINGS_X, y)
        self.readAll.SetPosition(self.READ_X, y)

    def _Scroll(self):
        self.HideHint()
        overflow = max(0, len(self.entries) - self.capacity)
        self.offset = int(round(self.scroll.GetPos() * overflow))
        # The layout repositions the thumb. While the thumb is dragged the client
        # reports that as another move even for SetPos(..., False); the scroll
        # bar keeps this handler from running nested (uicrimsonember).
        self._LayoutRows()

    def OnMouseWheel(self, delta):
        if not self.IsShow() or not self.IsIn() or not self.scroll.IsShow():
            return False
        maximum = max(0, len(self.entries) - self.capacity)
        self.offset = max(0, min(maximum, self.offset + (-1 if delta > 0 else 1)))
        self.HideHint()
        self._LayoutRows()
        return True

    def Reflow(self, usable_height):
        self.capacity = max(1, min(3, (usable_height - 8 - self.LIST_TOP - self.FOOTER) // self.ROW_HEIGHT))
        self.SetSize(self.WIDTH, self.LIST_TOP + self.capacity * self.ROW_HEIGHT + self.FOOTER)
        self.offset = min(self.offset, max(0, len(self.entries) - self.capacity))
        self._LayoutRows()

    def OpenAt(self, x, y, usable_height):
        self.Reflow(usable_height)
        self.Clamp(x, y, usable_height)
        self.Show()
        self.SetTop()

    def Activate(self, identity):
        if self.activate_callback:
            self.activate_callback(identity)

    def ShowHint(self, text):
        self.tooltip.ClearToolTip()
        self.tooltip.SetThinBoardSize(uiToolTip.ToolTip.TOOL_TIP_WIDTH)
        width = min(340, max(80, wndMgr.GetScreenWidth() - 56))
        for line in text.split("\n"):
            remaining = line
            while remaining:
                length = 0
                for end in range(1, len(remaining) + 1):
                    self.measure.SetText(remaining[:end])
                    if self.measure.GetTextSize()[0] > width:
                        break
                    length = end
                length = max(1, length)
                if length < len(remaining):
                    space = remaining.rfind(" ", 0, length + 1)
                    if space > 0:
                        length = space
                native = self.tooltip.AutoAppendTextLine(remaining[:length])
                native.SetFontColor(*INK)
                remaining = remaining[length:].lstrip()
        self.tooltip.AlignHorizonalCenter()
        self.tooltip.ShowToolTip()

    def HideHint(self):
        if getattr(self, "tooltip", None):
            self.tooltip.HideToolTip()

    def Close(self):
        self.HideHint()
        self.Hide()
        if self.close_callback:
            self.close_callback()

    def Destroy(self):
        self.HideHint()
        self.Hide()
        self.titleBar.SetCloseEvent(None)
        self.activate_callback = self.close_callback = None
        self.read_all_callback = self.settings_callback = None
        self.readAll.SetEvent(None)
        self.settings.Destroy()
        self.scroll.Destroy()
        for row in self.rows:
            row.Destroy()
        self.rows = []
        self.entries = []
        r1 = self.__dict__.get("r1")
        if r1:
            r1.Destroy()
        self.r1 = None
        self.tooltip = self.measure = self.readAll = self.settings = self.scroll = self.empty = None


class SettingsWindow(_Frame):
    def __init__(self, apply_callback, history_callback):
        _Frame.__init__(self, 516, 354, Text("SETTINGS_TITLE"))
        self.apply_callback = apply_callback
        self.draft = {}
        self.children = []
        self.checks = {}
        self._Own(_Line(self, 20, 43, Text("WAY"), fontconfig.ROLE_SECTION))
        self._Own(_Line(self, 20, 86, Text("SYSTEM"), color=DIM))
        self._Own(_Line(self, 291, 86, Text("HUD_COLUMN"), color=DIM, align="center"))
        self._Own(_Line(self, 427, 86, Text("MESSAGE_COLUMN"), color=DIM, align="center"))
        for index, (category, hint, glyph) in enumerate((
                ("biolog", "BIO_HINT", HUD_ROOT + "bio_normal.png"),
                ("dungeon", "DUNGEON_HINT", HUD_ROOT + "dungeon_normal.png"),
                ("switchbot", "SWITCHBOT_HINT", "icon/item/71084.tga"))):
            y = 112 + index * 48
            name, unused, color = CATEGORY_STYLE[category]
            self._Own(_Bar(self, 16, y, 484, 44, 0xFF141312))
            rgb = tuple(int(component * 255) for component in color)
            self._Own(_Bar(self, 16, y + 4, 2, 36,
                          0xFF000000 | rgb[0] << 16 | rgb[1] << 8 | rgb[2]))
            icon = self._Own(_Image(self, glyph, 0, 0))
            icon.SetPosition(37 - icon.GetWidth() // 2, y + (44 - icon.GetHeight()) // 2)
            self._Own(_Line(self, 60, y + 5, Text(name), fontconfig.ROLE_CONTROL, color))
            self._Own(_Line(self, 60, y + 24, Text(hint), color=DIM))
            for column, x in (("hud", 291), ("messages", 427)):
                if category == "switchbot" and column == "hud":
                    self._Own(_Line(self, x, y + 14, "-", color=DIM, align="center"))
                    continue
                key = category + "_" + column
                checkbox = self._Own(ui.ToggleButton())
                checkbox.SetParent(self)
                folder = "d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_"
                checkbox.SetUpVisual(folder + "unselected.tga")
                checkbox.SetOverVisual(folder + "hover.tga")
                checkbox.SetDownVisual(folder + "selected.tga")
                checkbox.SetPosition(x - checkbox.GetWidth() // 2, y + (44 - checkbox.GetHeight()) // 2)
                checkbox.SetToggleUpEvent(ui.__mem_func__(self._Toggle), key, False)
                checkbox.SetToggleDownEvent(ui.__mem_func__(self._Toggle), key, True)
                checkbox.Show()
                self.checks[key] = checkbox
        hint = self._Own(_Line(self, 20, 270, Text("ALARM_HINT"), color=DIM))
        _Fit(hint, Text("ALARM_HINT"), 476)
        self.error = self._Own(_Line(self, 20, 292, "", color=GOLD))
        self.history = self._Own(_Button(self, 20, 314, Text("HISTORY"), history_callback))
        self.apply = self._Own(_Button(self, 286, 314, Text("APPLY"), ui.__mem_func__(self.Apply)))
        self.cancel = self._Own(_Button(self, 394, 314, Text("CANCEL"), ui.__mem_func__(self.Close)))
        self.Hide()

    def _Own(self, child):
        self.children.append(child)
        return child

    def _Toggle(self, key, enabled):
        self.draft[key] = bool(enabled)

    def Open(self, preferences):
        self.draft = dict(preferences)
        for key, checkbox in self.checks.items():
            checkbox.Down() if self.draft[key] else checkbox.SetUp()
        self.error.SetText("")
        self.Clamp((wndMgr.GetScreenWidth() - self.GetWidth()) // 2,
                   (wndMgr.GetScreenHeight() - self.GetHeight()) // 2, wndMgr.GetScreenHeight() - 48)
        self.Show()
        self.SetTop()

    def Apply(self):
        if self.apply_callback and self.apply_callback(dict(self.draft)):
            self.Close()
        else:
            self.error.SetText(Text("SAVE_FAILED"))
            self.error.SetFontColor(*GOLD)

    def Close(self):
        self.draft = {}
        self.Hide()

    def Destroy(self):
        self.Close()
        self.titleBar.SetCloseEvent(None)
        self.apply_callback = None
        for button in (self.history, self.cancel, self.apply):
            button.SetEvent(None)
        for checkbox in self.checks.values():
            checkbox.SetToggleUpEvent(None)
            checkbox.SetToggleDownEvent(None)
        self.checks = {}
        self.children = []
        self.history = self.cancel = self.apply = self.error = None
