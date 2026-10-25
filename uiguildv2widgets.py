import fontconfig
import ime
import ui
import uicrimsoncontrols
import wndMgr
from uicrimsonember import SettingsScrollBar

# R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md) unless Settings -> "Starý vzhled": the page code of the guild window
# keeps its layout, these primitives draw it with the R1 frame, controls, fonts and palette. Decided once per session
# (as the other windows: the look applies after a restart of the client).
try:
    import uir1
    import uir1tokens as T1
    R1 = bool(uir1.UseR1())
except Exception:
    uir1 = T1 = None
    R1 = False

ART = "d:/ymir work/ui/game/guild_v2/"
CHECKBOX = "d:/ymir work/ui/game/crimson_ember/virtual_market/choice/checkbox_"
if R1:
    INK, DIM, GOLD, GREEN, RED = T1.INK, T1.INK_DIM, T1.IVORY, 0xff8fbf8c, T1.RED_HI
    MUTED = T1.MUTED
else:
    INK, DIM, GOLD, GREEN, RED = 0xffeee5d6, 0xffaea294, 0xffdcc08b, 0xff96c397, 0xffce6170
    MUTED = 0xff82796f
LOCKED_HINT = "Připravujeme"
# The guild window is presented at SCALE of the A1 layout. Page code keeps the
# 1040 x 690 design units; these primitives convert them to pixels. Buttons keep
# their canonical visuals and use the native button scale (as uidungeontrack).
# Text is NOT scaled: it uses the player's normal palette, so body copy matches
# the rest of the game (Tahoma 12), and the A1 hierarchy adds larger roles for
# page titles and resource figures. Tahoma 11 stays the floor for captions: at
# 10 px the Czech diacritics of dense captions run together.
SCALE = 0.78
MIN_FONT_SIZE = 11
ROLE_TITLE = "guild_title"
ROLE_FIGURE = "guild_figure"
ROLE_CAPTION = fontconfig.ROLE_DENSE
# Guild-only roles are derived from the active palette and only ever enlarge it.
_ROLE_STEPS = {"guild_title": ("large_bold", 4), "guild_figure": ("large_bold", 2)}

def px(value):
    return int(round(value * SCALE))

def unit(pixels):
    """The design unit whose px() is exactly ``pixels``: dialogs of the R1 look are laid out in pixels."""
    value = int(round(pixels / SCALE))
    for candidate in (value, value - 1, value + 1, value - 2, value + 2):
        if px(candidate) == pixels:
            return candidate
    return value

def span(start, length):
    """Pixel length of a design span, keeping adjacent spans seamless and lines visible."""
    size = px(start + length) - px(start)
    return max(1, size) if length > 0 else 0

# R1: every guild role is a role of the R1 kit (Noto Sans; Cinzel only for the window title and buttons).
_R1_ROLES = {"guild_title": "text_l", "guild_figure": "text_l", "section": "text_sb", "control": "text",
    "body": "text", "dense": "text_s", "large_bold": "text_b", "window_title": "title"}
_KIT = []

def kit():
    if not _KIT:
        _KIT.append(uir1.Kit())
    return _KIT[0]

def font(role):
    if R1:
        return kit().font(_R1_ROLES.get(role, "text"))
    base, step = _ROLE_STEPS.get(role, (role, 0))
    face, size = fontconfig.FontForRole(base).split(":")
    bold = size.endswith("b")
    return "%s:%d%s" % (face, max(MIN_FONT_SIZE, int(size.rstrip("b")) + step), "b" if bold else "")

def font_height(role):
    return int("".join(ch for ch in font(role).split(":")[1] if ch.isdigit()))

def sliced_button(owner, family, selected, text):
    """The scaled crimson action as a 3-slice button at its exact pixel size, so the
    0.78 window scale no longer blurs the frame. None = keep the old scaled family."""
    sliced = getattr(ui, "CrimsonSlicedButton", None)
    if not sliced:
        return None
    width, height = family.split("x")
    width, height = px(int(width)), px(int(height))
    if not uicrimsoncontrols.HasSlices(height):
        return None
    try:
        button = owner.keep(sliced())
        button.SetParent(owner)
        button.SetSlicedSize(width, height)
        button.SetSelected(selected)
        button.SetFontName(font(fontconfig.ROLE_CONTROL))
        if text is not None:
            button.SetText(text)
        return button
    except Exception:
        return None

def scale_button(button, text=None):
    """Scale visuals and hit area first, so the native label centres on the result."""
    wndMgr.SetScale(button.hWnd, SCALE, SCALE)
    button.SetFontName(font(fontconfig.ROLE_CONTROL))
    if text is not None:
        button.SetText(text)

def native_color(color):
    """Keep ARGB bits while respecting wndMgr's signed 32-bit Python argument."""
    return color - 0x100000000 if color > 0x7fffffff else color

def wrap(line, text, limit):
    """Break at spaces with the native width of the line's own font.

    The engine's multiline text breaks inside words; real LF characters are
    native line breaks, so the words are placed before the text is shown."""
    lines = []
    for paragraph in str(text).split("\n"):
        current = ""
        for word in paragraph.split(" "):
            candidate = word if not current else current + " " + word
            line.SetText(candidate)
            # Keep a small margin: the native break tests glyph boxes, not advances.
            if current and line.GetTextSize()[0] > limit - 3:
                lines.append(current)
                current = word
            else:
                current = candidate
        lines.append(current)
    return "\n".join(lines)

def lines_height(count, role=fontconfig.ROLE_BODY):
    """Design height of ``count`` wrapped lines in ``role`` (the step of Canvas.block)."""
    return int(count * (font_height(role) + 3) / SCALE + 0.5)

def block_height(text, width, role=fontconfig.ROLE_BODY):
    """Design height Canvas.block() will give ``text`` at ``width``, measured before any window exists: a dialog
    sized to its content (the guild glossary) lays the bottom row out below the last paragraph."""
    probe = ui.TextLine()
    probe.SetFontName(font(role))
    probe.DisableEnterToken()
    return lines_height(wrap(probe, text, px(width)).count("\n") + 1, role)

def check(button, checked):
    """Show a checkbox button's current state (state is owned by the caller)."""
    if hasattr(button, "SetOn"):
        button.SetOn(checked)
        return
    button.SetUpVisual(CHECKBOX + ("selected" if checked else "normal") + ".png")
    button.SetOverVisual(CHECKBOX + ("selected" if checked else "hover") + ".png")
    button.SetDownVisual(CHECKBOX + "pressed.png")
    button.SetDisableVisual(CHECKBOX + "disabled.png")

def _bar(parent, x, y, width, height, color):
    bar = ui.Bar()
    bar.SetParent(parent)
    bar.SetPosition(x, y)
    bar.SetSize(max(0, width), max(0, height))
    bar.SetColor(native_color(color))
    bar.AddFlag("not_pick")
    bar.Show()
    return bar

class Flat(ui.Window):
    """Outlined A1 control drawn from native bars: secondary action, clickable
    row, navigation item or segmented choice. Only a crimson button is primary."""
    STYLES = {
        # fill, border, hover fill, hover border, text, hover text
        "secondary": (0xff15100e, 0xff8a6a4c, 0xff221915, 0xffc49a6c, INK, GOLD),
        "danger": (0xff170d0d, 0xff84403f, 0xff261212, 0xffc0605c, 0xffe7a3a0, 0xfff5c3bf),
        "row": (0xff100e0c, 0xff4c3d2d, 0xff18130f, 0xff8c724c, INK, GOLD),
        "plain": (0x00000000, 0x00000000, 0xff1b1512, 0xff3d3025, INK, GOLD),
        "link": (0x00000000, 0x00000000, 0x00000000, 0x00000000, GOLD, INK),
    }
    SELECTED = (0xff34131a, 0xffa9604e)
    DISABLED = (0xff0e0c0b, 0xff39322a, MUTED)
    if R1:
        STYLES = {
            "secondary": (0xff121011, T1.LINE, 0xff1d1a1b, 0xff5a5252, T1.BUTTON_TEXT, T1.IVORY),
            "danger": (0xff150d0e, 0xff5e1a1b, 0xff201011, 0xff9a2224, T1.BUTTON_TEXT, T1.IVORY),
            "row": (0xff0f0d0e, 0xff2a2627, 0xff1a1718, 0xff4a4344, T1.INK, T1.IVORY),
            "plain": (0x00000000, 0x00000000, T1.BAND_HOVER, 0x00000000, T1.INK, T1.IVORY),
            "link": (0x00000000, 0x00000000, 0x00000000, 0x00000000, T1.IVORY, T1.INK),
            "tab": (0xff121011, T1.LINE, 0xff1d1a1b, 0xff5a5252, T1.INK_DIM, T1.INK),
        }
        SELECTED = (T1.BAND_SELECTED, T1.LINE)
        DISABLED = (0xff0e0c0d, 0xff242021, T1.DISABLED)

    def __init__(self, parent, x, y, width, height, callback, text="", style="secondary",
                 selected=False, enabled=True, align="center", role=fontconfig.ROLE_CONTROL, accent=False,
                 hint=None, locked=False):
        ui.Window.__init__(self)
        self.hint, self.locked = hint, locked
        self.SetParent(parent)
        self.SetPosition(x, y)
        self.SetSize(width, height)
        self.callback, self.style, self.selected, self.enabled = callback, style, selected, bool(enabled)
        self.disabled = not self.enabled
        self.accent, self.hovered, self.pressed = accent, False, False
        self.wheel = getattr(parent, "on_wheel", None)
        self.fill = _bar(self, 0, 0, width, height, 0)
        self.edges = [_bar(self, 0, 0, width, 1, 0), _bar(self, 0, height - 1, width, 1, 0),
            _bar(self, 0, 0, 1, height, 0), _bar(self, width - 1, 0, 1, height, 0)]
        self.mark = _bar(self, 0, 0, 2 if accent else 0, height, 0xffa94751)
        self.label = None
        if text:
            self.label = ui.TextLine()
            self.label.SetParent(self)
            self.label.SetFontName(font(role))
            self.label.DisableEnterToken()
            if align == "center":
                self.label.SetHorizontalAlignCenter()
                # a locked control keeps room for its padlock on the right
                self.label.SetPosition((width - (16 if locked else 0)) // 2, max(0, (height - font_height(role)) // 2 - 1))
            else:
                self.label.SetPosition(align, max(0, (height - font_height(role)) // 2 - 1))
            self.label.AddFlag("not_pick")
            self.label.SetText(str(text))
            self.label.Show()
        self.lock = None
        if locked:
            # A feature that comes after the start: dimmed, a padlock and the hint "Připravujeme".
            self.lock = lock_image(self, width - 17, (height - 14) // 2)
        self.paint()
        self.Show()

    def paint(self):
        fill, border, hover_fill, hover_border, text, hover_text = self.STYLES[self.style]
        if not self.enabled:
            fill, border, text = self.DISABLED if self.style not in ("plain", "link") else (0, 0, MUTED)
        elif self.selected and self.style == "link":
            text = INK
        elif self.selected:
            fill, border = self.SELECTED
            text = INK if self.style == "plain" else GOLD
            if R1:
                text = T1.IVORY
                if self.style == "plain":
                    border = 0x00000000
        elif self.hovered or self.pressed:
            fill, border, text = hover_fill, hover_border, hover_text
        self.fill.SetColor(native_color(fill))
        for edge in self.edges:
            edge.SetColor(native_color(border))
        if R1:
            # R1 selection: a dark well with the red line under it, never a red plate.
            on = self.selected and self.enabled and (self.accent or self.style in ("tab", "plain", "row"))
            self.mark.SetPosition(0, self.GetHeight() - 2)
            self.mark.SetSize(self.GetWidth() if on else 0, 2)
            self.mark.SetColor(native_color(T1.RED))
        else:
            self.mark.SetSize(2 if self.accent and self.selected and self.enabled else 0, self.GetHeight())
        if self.lock is not None:
            self.lock.LoadImage(LOCK + ("lock_hover.png" if self.hovered else "lock_normal.png"))
        if self.label:
            self.label.SetPackedFontColor(native_color(text))

    def SetSelected(self, selected):
        self.selected = selected
        self.paint()

    def SetEnabled(self, enabled):
        self.enabled = bool(enabled)
        self.disabled = not self.enabled
        self.paint()

    def Enable(self):
        self.SetEnabled(True)

    def Disable(self):
        self.SetEnabled(False)

    def click(self):
        if self.enabled and self.callback:
            self.callback()
            return True
        return False

    def OnMouseOverIn(self):
        self.hovered = True
        self.paint()
        if self.hint and R1:
            uir1.ShowHint(kit(), self, self.hint)

    def OnMouseOverOut(self):
        self.hovered = self.pressed = False
        self.paint()
        if self.hint and R1:
            uir1.HideHint()

    def OnMouseLeftButtonDown(self):
        self.pressed = bool(self.enabled)
        self.paint()
        return True

    def OnMouseLeftButtonUp(self):
        activate, self.pressed = self.pressed, False
        self.paint()
        if activate:
            self.click()
        return True

    def OnRunMouseWheel(self, length):
        return bool(self.wheel and self.wheel(length < 0))

    def Destroy(self):
        if self.hint and R1 and self.hovered:
            uir1.HideHint()
        self.callback = self.wheel = None
        self.Hide()

LOCK = "d:/ymir work/ui/public/althea_r1_cech/"

def lock_image(parent, x, y):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag("not_pick")
    image.LoadImage(LOCK + "lock_normal.png")
    image.SetPosition(int(x), int(y))
    image.Show()
    return image

def button_font():
    """The label of the guild's R1 buttons: Noto Sans in sentence case, as the approved R1 market."""
    return kit().font("text_s")

def scrollbar():
    return uir1.ScrollBar(kit()) if R1 else SettingsScrollBar()

if R1:
    class R1Action(uir1.Button):
        """A secondary action on the R1 button plate (never an outlined box, never a red plate). The Flat API the
        page code uses: SetSelected (a chosen toggle shows the vein), SetEnabled, enabled/disabled; ``locked`` adds
        the padlock and the hint "Připravujeme"; ``danger`` is kept for the page code and changes nothing: the R1
        rules allow no pale or pink red, so a dangerous action is an ordinary secondary button (the dark red stays
        the vein of the primary one)."""

        def __init__(self, parent, x, y, w, h, callback, text, selected=False, enabled=True, danger=False,
                     locked=False):
            small = True if h >= 19 else "xs"      # one height (22 px) for the actions of pages and dialogs
            uir1.Button.__init__(self, parent, kit(), x, y + max(0, (h - uir1.L.button_height(small)) // 2), w,
                                 text, primary=bool(selected), small=small, event=callback, font=button_font())
            self.danger, self.locked, self.wheel = danger, locked, getattr(parent, "on_wheel", None)
            self.lock = None
            if locked:
                self.label.SetPosition((self.w - 14) // 2, self.label.GetLocalPosition()[1])
                self.lock = lock_image(self, self.w - 18, (self.h - 14) // 2)
                self.SetToolTipText(LOCKED_HINT)
            if not enabled or locked:
                self.Disable()
            self.paint()

        @property
        def selected(self):
            return self.primary

        @property
        def disabled(self):
            return not self.enabled

        def SetSelected(self, selected):
            self.SetPrimary(selected)

        def SetEnabled(self, enabled):
            self.Enable() if enabled and not self.locked else self.Disable()

        def paint(self):
            uir1.Button.paint(self)
            if getattr(self, "lock", None) is not None:
                self.label.SetPosition((self.w - 14) // 2, self.label.GetLocalPosition()[1])

        def OnRunMouseWheel(self, length):
            return bool(self.wheel and self.wheel(length < 0))

class Canvas(ui.Window):
    def __init__(self, parent=None, x=0, y=0, width=0, height=0):
        ui.Window.__init__(self)
        self.widgets = []
        self.on_wheel = None
        if parent:
            self.SetParent(parent)
        # Layout code reads design units; GetWidth/GetHeight remain pixels.
        self.design_width, self.design_height = width, height
        self.SetPosition(px(x), px(y))
        self.SetSize(span(x, width), span(y, height))

    def keep(self, widget):
        self.widgets.append(widget)
        return widget

    def clear(self):
        for widget in self.widgets:
            widget.Hide()
            if isinstance(widget, getattr(ui, "Button", ())):
                widget.SetEvent(None)
            if isinstance(widget, SettingsScrollBar) or (R1 and isinstance(widget, uir1.ScrollBar)):
                widget.SetScrollEvent(None)
            widget.Destroy()
        self.widgets = []

    def Destroy(self):
        self.clear()
        self.on_wheel = None
        self.Hide()

    def text(self, x, y, text, width=0, color=INK, role=fontconfig.ROLE_BODY, align="left", multiline=False):
        line = self.keep(ui.TextLine())
        line.SetParent(self)
        line.SetPosition(px(x), px(y))
        line.SetFontName(font(role))
        line.DisableEnterToken()
        line.SetPackedFontColor(native_color(color))
        if align == "right":
            line.SetHorizontalAlignRight()
        elif align == "center":
            line.SetHorizontalAlignCenter()
        value = str(text)
        if multiline and width:
            # Measure on the plain line before the native limit/wrap is applied.
            value = wrap(line, value, px(width))
        if width:
            line.SetLimitWidth(px(width))
        if multiline:
            line.SetMultiLine()
        line.AddFlag("not_pick")
        line.SetText(value)
        line.Show()
        return line

    def block(self, x, y, text, width, color=INK, role=fontconfig.ROLE_BODY):
        """Word-wrapped paragraph; returns the design height it occupies."""
        line = self.text(x, y, text, width, color, role, multiline=True)
        return lines_height(line.GetText().count("\n") + 1, role)

    def image(self, name, x, y, width=None, height=None):
        image = self.keep(ui.ExpandedImageBox())
        image.SetParent(self)
        image.AddFlag("not_pick")
        # a guild_v2 art name, or a whole pack path of another window's art ("d:/...png": the yang coin)
        image.LoadImage(name if name.startswith("d:/") else ART + name + ".png")
        if width is not None and height is not None:
            image.SetScale(float(span(x, width)) / max(1, image.GetWidth()), float(span(y, height)) / max(1, image.GetHeight()))
        else:
            image.SetScale(SCALE, SCALE)
        image.SetPosition(px(x), px(y))
        image.Show()
        return image

    def picture(self, path, x, y):
        """Unscaled shared asset (for example a read-only checkbox state)."""
        image = self.keep(ui.ExpandedImageBox())
        image.SetParent(self)
        image.AddFlag("not_pick")
        image.LoadImage(path)
        image.SetPosition(px(x), px(y))
        image.Show()
        return image

    def bar(self, x, y, width, height, color=0xff4c3d2d):
        return self.pixel_bar(px(x), px(y), span(x, max(0, int(width))), span(y, max(0, int(height))), color)

    def pixel_bar(self, x, y, width, height, color):
        return self.keep(_bar(self, x, y, width, height, color))

    def panel(self, x, y, width, height, selected=False):
        # The one-pixel border stays one pixel at every scale.
        left, top, w, h = px(x), px(y), span(x, width), span(y, height)
        if R1:
            frame = self.keep(uir1.Frame(self, left, top, w, h, "panel"))
            if selected:
                self.pixel_bar(left + 2, top + h - 3, w - 4, 2, T1.RED)
            return frame
        self.pixel_bar(left, top, w, h, 0xff4c3d2d if not selected else 0xffa9604e)
        self.pixel_bar(left + 1, top + 1, w - 2, h - 2, 0xff100e0c if not selected else 0xff281216)

    def rule(self, x, y, width, color=0xff32281e):
        return self.pixel_bar(px(x), px(y), span(x, width), 1, T1.LINE if R1 else color)

    def header(self, text, x, y, width):
        if R1:
            # R1 section: the heading and a hairline fading out to the right (no plate).
            section = self.keep(uir1.Section(self, kit(), px(x), px(y) + 2, span(x, width), text.capitalize()
                if text.isupper() else text))
            return section
        self.image("header_804", x, y, width, 28)
        self.text(x + 17, y + 7, text, width - 40, GOLD, fontconfig.ROLE_SECTION)

    def table_header(self, x, y, width, height=28):
        self.pixel_bar(px(x), px(y), span(x, width), span(y, height), 0xff141213 if R1 else 0xff1c1612)
        self.pixel_bar(px(x), px(y + height) - 1, span(x, width), 1, T1.LINE if R1 else 0xff4c3d2d)

    def button(self, text, x, y, event, enabled=True, width=170, selected=False, tooltip=None):
        """Primary crimson action. Use at most one per screen."""
        if R1:
            # The R1 primary button (dark, the red vein along its bottom edge) at the action's pixel size.
            button = self.keep(uir1.Button(self, kit(), px(x), px(y), span(x, width), text, primary=True,
                small=True, event=event if enabled else None, font=button_font()))
            if tooltip:
                button.SetToolTipText(tooltip)
            if not enabled:
                button.Disable()
            return button
        family = "170x24" if width == 170 else "80x24"
        button = sliced_button(self, family, selected, text)
        if button is None:
            button = self.keep(ui.Button())
            button.SetParent(self)
            button.SetUpVisual(uicrimsoncontrols.Visual(family, "selected" if selected else "normal"))
            button.SetOverVisual(uicrimsoncontrols.Visual(family, "hover"))
            button.SetDownVisual(uicrimsoncontrols.Visual(family, "pressed"))
            button.SetDisableVisual(uicrimsoncontrols.Visual(family, "disabled"))
            scale_button(button, text)
        button.SetPosition(px(x), px(y))
        button.SetEvent(event if enabled else None)
        if tooltip:
            button.SetToolTipText(tooltip)
        if not enabled:
            button.Disable()
        button.Show()
        return button

    def primary(self, text, x, y, event, reason=None, width=170, place="above"):
        """Crimson action; an unavailable one states why (above, left or right)."""
        button = self.button(text, x, y, event, not reason, width, tooltip=reason)
        if reason:
            if place == "right":
                self.text(x + width + 14, y + 5, reason, 330, GOLD, ROLE_CAPTION)
            elif place == "left":
                self.text(x - 14, y + 5, reason, max(60, x - 14), GOLD, ROLE_CAPTION, "right")
            else:
                self.text(x + width, y - 19, reason, 360, GOLD, ROLE_CAPTION, "right")
        return button

    def action(self, text, x, y, event, enabled=True, width=150, height=26, style="secondary", selected=False,
               role=fontconfig.ROLE_CONTROL, locked=False):
        """Secondary action; ``locked`` = a feature after the start (dimmed, padlock, hint "Připravujeme")."""
        if locked:
            enabled = False
        if R1 and style in ("secondary", "danger"):
            return self.keep(R1Action(self, px(x), px(y), span(x, width), span(y, height), event, text, selected,
                enabled, style == "danger", locked))
        return self.keep(Flat(self, px(x), px(y), span(x, width), span(y, height), event, text, style,
            selected, enabled, "center", role, hint=LOCKED_HINT if locked else None, locked=locked))

    def locked_panel(self, x, y, width, height, title, text="Tahle část cechu přijde s první větší aktualizací."):
        """A block of the page that comes after the start: the frame, its title, a padlock and "Připravujeme"."""
        self.panel(x, y, width, height)
        self.text(x + 16, y + 12, title, width - 60, MUTED, fontconfig.ROLE_SECTION)
        image = self.keep(lock_image(self, px(x + width - 30), px(y + 14)))
        self.text(x + 16, y + 42, LOCKED_HINT, width - 32, DIM, fontconfig.ROLE_CONTROL)
        if height >= 90:
            self.text(x + 16, y + 68, text, width - 32, MUTED, ROLE_CAPTION, multiline=True)
        return image

    def row(self, x, y, width, height, event, selected=False, style="row", enabled=True, accent=False, hint=None):
        """Whole-row hit target; draw its content on the canvas afterwards."""
        return self.keep(Flat(self, px(x), px(y), span(x, width), span(y, height), event, "", style,
            selected, enabled, accent=accent, hint=hint))

    def checkbox(self, x, y, checked, event, enabled=True):
        if R1:
            box = self.keep(uir1.CheckBox(self, kit(), px(x), px(y), "", on=checked, event=event))
            if not enabled:
                box.Disable()
            return box
        if not enabled:
            return self.picture(CHECKBOX + ("selected" if checked else "disabled") + ".png", x, y)
        button = self.keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(px(x), px(y))
        check(button, checked)
        button.SetEvent(event)
        button.Show()
        return button

    def icon_button(self, name, x, y, event, tooltip):
        if R1:
            # A plain R1 hit area (hover fill, hint) around the guild icon at the window scale.
            size = span(x, 30)
            button = self.keep(Flat(self, px(x) - 2, px(y) - 2, size, size, event, "", "plain", hint=tooltip))
            image = ui.ExpandedImageBox()
            image.SetParent(button)
            image.AddFlag("not_pick")
            image.LoadImage(ART + name + ".png")
            image.SetScale(SCALE, SCALE)
            image.SetPosition(2, 2)
            image.Show()
            button.icon = image
            return button
        button = self.keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(px(x), px(y))
        for setter in (button.SetUpVisual, button.SetOverVisual, button.SetDownVisual, button.SetDisableVisual):
            setter(ART + name + ".png")
        scale_button(button)
        button.SetEvent(event)
        button.SetToolTipText(tooltip)
        button.Show()
        return button

    def tab(self, text, x, y, event, selected=False, locked=False):
        if R1 or locked:
            # R1 tab: a dark cell with the red line under the selected one (the native tab size 132 x 30).
            return self.keep(Flat(self, px(x), px(y), span(x, 132), span(y, 30), event, text, "tab" if R1 else "secondary",
                selected, not locked, "center", ROLE_CAPTION if locked else fontconfig.ROLE_CONTROL, accent=True,
                hint=LOCKED_HINT if locked else None, locked=locked))
        button = self.keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(px(x), px(y))
        button.SetUpVisual(ART + ("tab_selected.png" if selected else "tab_normal.png"))
        button.SetOverVisual(ART + "tab_hover.png")
        button.SetDownVisual(ART + "tab_pressed.png")
        button.SetDisableVisual(ART + "tab_disabled.png")
        scale_button(button, text)
        button.SetEvent(event)
        button.Show()
        return button

    def edit(self, x, y, width, maximum, value="", numeric=False, height=20):
        left, top, w, h = px(x), px(y), span(x, width), span(y, height)
        self.pixel_bar(left - 4, top - 3, w + 8, h + 6, 0xff4a4445 if R1 else 0xff6e553f)
        self.pixel_bar(left - 3, top - 2, w + 6, h + 4, 0xff0a090a if R1 else 0xff110d0b)
        if height > 20:
            block = self.keep(TextViewport(self, x, y, width, height, str(value), maximum))
            return block.line
        edit = self.keep(ui.EditLine())
        edit.SetParent(self)
        edit.SetPosition(left, top)
        edit.SetSize(w, h)
        edit.SetFontName(font(fontconfig.ROLE_BODY))
        edit.SetPackedFontColor(native_color(INK))
        edit.SetMax(maximum)
        edit.SetLimitWidth(w)
        if numeric:
            edit.SetNumberMode()
        edit.SetText(str(value))
        edit.Show()
        return edit

    def paragraph(self, x, y, width, height, value):
        return self.keep(TextViewport(self, x, y, width, height, value))

    def gauge(self, x, y, width, current, required, height=8, color=0xffa8323a):
        left, top, w, h = px(x), px(y), span(x, width), span(y, height)
        if R1:
            color = T1.RED
        self.pixel_bar(left, top, w, h, T1.LINE if R1 else 0xff5a4634)
        self.pixel_bar(left + 1, top + 1, w - 2, h - 2, 0xff0c0b0c if R1 else 0xff1d1714)
        if required > 0:
            self.pixel_bar(left + 1, top + 1, min(w - 2, max(0, int((w - 2) * min(current, required) // required))), h - 2, color)

    def pips(self, x, y, width, filled, count=5, height=5):
        """The rank marks I..V. R1: the reached ranks in the brand blood red, the others in the kit's line colour (owner
        16. 10. 2026: tokens of the kit only, no bronze, no pale red), the same as the R1 gauge."""
        step = float(width + 6) / count
        on, off = (T1.RED, T1.LINE) if R1 else (0xffbd8551, 0xff2c251e)
        for index in range(count):
            self.bar(x + index * step, y, step - 6, height, on if index < filled else off)

    def shell(self, width, height, title, close):
        if R1:
            # The R1 chrome: frame with the background, Cinzel title with the vein, the plain X; the whole header
            # row drags the window.
            self.chrome = uir1.Chrome(self, kit(), self.GetWidth(), self.GetHeight(), title, close)
            self.title_line = ChromeTitle(self.chrome)
            return
        self.bar(4, 23, width - 8, height - 23, 0xff0c0b0a)
        self.image("body-fill", 4, 23, width - 8, height - 23)
        self.image("edge-left", 4, 23, 2, height - 25)
        self.image("edge-right", width - 6, 23, 2, height - 25)
        self.image("edge-bottom", 6, height - 2, width - 12, 2)
        self.image("title_left", 0, 0)
        self.image("title_center", 32, 0, width - 64, 23)
        self.image("title_right", width - 32, 0)
        self.title_line = self.text(width // 2, 4, title, width - 90, align="center")
        button = self.keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(px(width - 22), px(3))
        button.SetUpVisual(ART + "close_normal.png")
        button.SetOverVisual(ART + "close_hover.png")
        button.SetDownVisual(ART + "close_pressed.png")
        scale_button(button)
        button.SetEvent(close)
        button.Show()

class ChromeTitle(object):
    """The title_line of the R1 chrome (page code sets the window title through it)."""
    def __init__(self, chrome):
        self.chrome, self.text = chrome, ""

    def SetText(self, text):
        self.text = text
        self.chrome.SetTitle(text)

    def GetText(self):
        return self.text

class ScrollList(Canvas):
    @staticmethod
    def gutter_for(count, height, row_height):
        """Width the scroll bar takes from the rows; a page lines its column headers up with it. R1: the rows run
        to the panel edge unless the scroll bar is needed."""
        return 16 if (count > max(1, height // row_height) or not R1) else 0

    def __init__(self, parent, x, y, width, height, rows, row_height, draw, offset=0):
        Canvas.__init__(self, parent, x, y, width, height)
        self.rows, self.row_height, self.draw = rows, row_height, draw
        self.visible = max(1, height // row_height)
        self.maximum = max(0, len(rows) - self.visible)
        self.offset = min(self.maximum, max(0, offset))
        self.gutter = ScrollList.gutter_for(len(rows), height, row_height)
        self.content = Canvas(self, 0, 0, width - self.gutter, height)
        self.EnableScissorRect()
        self.content.Show()
        self.scroll = scrollbar()
        self.scroll.SetParent(self)
        self.scroll.SetPosition(self.GetWidth() - 10, 0)
        self.scroll.SetScrollBarSize(self.GetHeight())
        self.scroll.SetMiddleBarSize(min(1.0, float(self.visible) / max(1, len(rows))))
        self.scroll.SetScrollStep(1.0 / max(1, self.maximum))
        self.scroll.SetPos(float(self.offset) / max(1, self.maximum))
        self.scroll.SetScrollEvent(ui.__mem_func__(self.on_scroll))
        self.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel))
        self.content.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel))
        # Clickable rows forward the wheel, so hovering a row still scrolls.
        self.content.on_wheel = ui.__mem_func__(self.wheel)
        if self.maximum:
            self.scroll.Show()
        self.render()
        self.Show()

    def render(self):
        self.content.clear()
        for index, row in enumerate(self.rows[self.offset:self.offset + self.visible]):
            self.draw(self.content, row, index * self.row_height, self.design_width - self.gutter)

    def on_scroll(self):
        self.offset = int(self.maximum * self.scroll.GetPos() + 0.5)
        self.render()

    def wheel(self, down):
        if not self.maximum:
            return False
        self.scroll.OnDown() if down else self.scroll.OnUp()
        return True

    def Destroy(self):
        self.draw = None
        self.SetOnRunMouseWheelEvent(None)
        self.content.SetOnRunMouseWheelEvent(None)
        self.content.Destroy()
        self.scroll.SetScrollEvent(None)
        self.scroll.Destroy()
        self.scroll.Hide()
        Canvas.Destroy(self)

class TextViewport(Canvas):
    """Clipped native multiline text with a scrollbar, including editable fields."""
    def __init__(self, parent, x, y, width, height, value, maximum=0):
        Canvas.__init__(self, parent, x, y, width, height)
        width, height = self.GetWidth(), self.GetHeight()
        self.EnableScissorRect()
        self.editable = bool(maximum)
        self.offset = self.maximum = 0
        self.line = self.keep(ui.EditLine() if maximum else ui.TextLine())
        self.line.SetParent(self)
        self.line.SetFontName(font(fontconfig.ROLE_BODY))
        self.line.SetPackedFontColor(native_color(INK))
        self.line.DisableEnterToken()
        if not maximum:
            # Read-only text is laid out per word; typed text keeps native flow.
            value = wrap(self.line, value, width - 18)
        self.last_text = value
        self.line.SetMultiLine()
        self.line.SetLimitWidth(width - 18)
        self.line.SetSize(width - 18, height)
        if maximum:
            self.line.SetMax(maximum)
            self.line.SetReturnEvent(lambda: ime.PasteString("\n"))
        else:
            self.line.AddFlag("not_pick")
        self.line.SetText(value)
        self.line.Show()
        self.scroll = self.keep(scrollbar())
        self.scroll.SetParent(self)
        self.scroll.SetPosition(width - 10, 0)
        self.scroll.SetScrollBarSize(height)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.on_scroll))
        self.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel))
        self.line.SetOnRunMouseWheelEvent(ui.__mem_func__(self.wheel))
        self.Show()

    def OnUpdate(self):
        text_height = max(14, self.line.GetTextSize()[1])
        total = max(1, self.line.GetTextLineCount()) * text_height + 4
        new_maximum = max(0, total - self.GetHeight())
        text = self.line.GetText()
        follow_end = self.editable and text != self.last_text and self.offset >= self.maximum
        self.last_text = text
        if new_maximum != self.maximum:
            self.maximum = new_maximum
            self.offset = new_maximum if follow_end else min(self.offset, new_maximum)
            self.scroll.SetMiddleBarSize(min(1.0, float(self.GetHeight()) / total))
            self.scroll.SetScrollStep(float(text_height * 3) / max(1, new_maximum))
            self.scroll.SetPos(float(self.offset) / max(1, new_maximum))
        self.scroll.Show() if self.maximum else self.scroll.Hide()
        self.line.SetPosition(0, -self.offset)
        self.line.SetSize(self.GetWidth() - 18, max(self.GetHeight(), total))

    def on_scroll(self):
        self.offset = int(self.maximum * self.scroll.GetPos() + 0.5)
        self.line.SetPosition(0, -self.offset)

    def wheel(self, down):
        if not self.maximum:
            return False
        self.scroll.OnDown() if down else self.scroll.OnUp()
        return True

    def Destroy(self):
        self.SetOnRunMouseWheelEvent(None)
        self.line.SetOnRunMouseWheelEvent(None)
        if self.editable:
            self.line.SetReturnEvent(None)
        Canvas.Destroy(self)

class SearchField(Canvas):
    """One persistent search line. It survives page re-rendering, so a periodic
    snapshot never steals the player's typing focus or text."""
    def __init__(self, parent, escape):
        Canvas.__init__(self, parent, 0, 0, 260, 22)
        self.field = None
        if R1:
            self.frame = []
            self.field = uir1.SearchField(self, kit(), 0, 0, self.GetWidth(), "Hledat", max_len=24)
            self.edit = self.field.edit
            self.edit.SetEscapeEvent(escape)
            self.edit.SetReturnEvent(ui.__mem_func__(self.edit.KillFocus))
            return
        self.frame = [self.pixel_bar(0, 0, self.GetWidth(), self.GetHeight(), 0xff4a4445 if R1 else 0xff6e553f),
            self.pixel_bar(1, 1, self.GetWidth() - 2, self.GetHeight() - 2, 0xff0a090a if R1 else 0xff110d0b)]
        self.edit = self.keep(ui.EditLine())
        self.edit.SetParent(self)
        self.edit.SetFontName(font(fontconfig.ROLE_BODY))
        self.edit.SetPackedFontColor(native_color(INK))
        self.edit.SetMax(24)
        self.edit.SetEscapeEvent(escape)
        self.edit.SetReturnEvent(ui.__mem_func__(self.edit.KillFocus))
        self.edit.Show()

    def place(self, x, y, width):
        if self.field is not None:
            self.SetPosition(px(x), px(y))
            self.SetSize(span(x, width), uir1.T.FIELD_H)
            self.field.SetWidth(span(x, width))
            self.Show()
            self.SetTop()
            return
        left, top, w, h = px(x), px(y), span(x, width), span(y, 22)
        self.SetPosition(left, top)
        self.SetSize(w, h)
        self.frame[0].SetSize(w, h)
        self.frame[1].SetSize(w - 2, h - 2)
        self.edit.SetPosition(6, max(0, (h - font_height(fontconfig.ROLE_BODY)) // 2 - 1))
        self.edit.SetSize(w - 12, h - 2)
        self.edit.SetLimitWidth(w - 12)
        self.Show()
        self.SetTop()

    def value(self):
        return self.edit.GetText()

    def reset(self, text=""):
        self.edit.KillFocus()
        self.edit.SetText(text)

    def Destroy(self):
        self.edit.KillFocus()
        self.edit.SetEscapeEvent(None)
        self.edit.SetReturnEvent(None)
        Canvas.Destroy(self)

class Dialog(Canvas):
    def __init__(self, owner, title, height=340, width=560):
        Canvas.__init__(self, None, 0, 0, width, height)
        self.AddFlag("float")
        if R1:
            self.AddFlag("movable")     # the R1 header row drags it
        self.owner, self.identity = owner, owner.model.identity()
        self.edit_lines = []
        self.ticks = []             # called every frame (OnUpdate): what follows the text of a field
        self.message_fit = self.message_shown = self.message_probe = None
        self.shell(width, height, title, ui.__mem_func__(self.Close))
        self.SetCenterPosition()
        self.message = self.text(24, height - 66, "", width - 48, RED)
        self.close_button = self.action("Zavřít", width - 134, height - 36, ui.__mem_func__(self.Close), width=110)
        self.Show()
        self.SetTop()
        # Native Lock routes IME to the dialog itself instead of its focused
        # EditLine. Use the same floating/focus contract as uiCommon.InputDialog.
        self.SetFocus()

    def text(self, x, y, text, width=0, color=INK, role=fontconfig.ROLE_BODY, align="left", multiline=False):
        # R1: the window header already names the dialog; its big first heading would repeat it.
        if R1 and role == ROLE_TITLE and y < 60:
            line = Canvas.text(self, x, y, "", width, color, role, align)
            line.Hide()
            return line
        return Canvas.text(self, x, y, text, width, color, role, align, multiline)

    def primary(self, text, event, enabled=True, reason=None, equal=None):
        """The dialog's single crimson action, bottom, LEFT of Zavřít (confirm left, cancel right: the rule of the whole
        client); Zavřít keeps the bottom right corner. R1 ``equal`` = (x of Zavřít, y, width of each, x of the crimson
        action) in design units: the two actions are equal buttons across the content instead (the crimson one on the
        left)."""
        width, height = self.design_width, self.design_height
        if R1 and equal:
            left, top, each, right = equal
            button = self.button(text, right, top, event, enabled and not reason, each, tooltip=reason)
            self.close_button.SetPosition(px(left), px(top))
            self.close_button.SetWidth(span(left, each))
        else:
            button = self.button(text, width - 324, height - 36, event, enabled and not reason, tooltip=reason)
            self.close_button.SetPosition(px(width - 134), px(height - 35))
        if reason:
            self.message.SetPackedFontColor(native_color(DIM))
            self.message.SetText(reason)
        self.confirm_button = button
        import uiconfirm
        uiconfirm.Bind(self, "confirm_button")
        return button

    def place_beside(self, window):
        """Puts the dialog next to ``window`` instead of the screen centre: right of it, else left of it, top edges
        aligned, clamped to the screen (owner 16. 10. 2026: the guild passive detail covered the guild window and its
        rows). The gap and the screen margin are the kit's dialog profile (uir1tokens.PROFILE_DIALOG gap / pad)."""
        gap, margin = (T1.PROFILE_DIALOG["gap"], T1.PROFILE_DIALOG["pad"]) if R1 else (10, 12)
        screen_w, screen_h = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        wx, wy = window.GetGlobalPosition()
        w, h = self.GetWidth(), self.GetHeight()
        x = wx + window.GetWidth() + gap
        if x + w > screen_w - margin:
            left = wx - gap - w
            x = left if left >= margin else max(margin, min(screen_w - margin - w, x))
        self.SetPosition(int(x), int(max(margin, min(screen_h - margin - h, wy))))

    def place_message(self, x, y, width, role=ROLE_CAPTION):
        """Moves the message line (errors, "Čeká se na potvrzení...") to design (x, y), ``width`` wide, in ``role``: a
        compact dialog has no free row at the bottom, the message takes the place of its note. fit_message() keeps a
        long message inside the width."""
        self.message.SetPosition(px(x), px(y))
        self.message.SetLimitWidth(px(width))
        self.message_fit = (px(width), role)
        if R1:
            uir1.SetFont(self.message, font(role))

    def fit_message(self):
        """R1: the message in its role while it fits the width of place_message(), else in the next smaller size (the
        status texts of the server run up to 290 px)."""
        if not R1 or not self.message_fit:
            return
        text = self.message.GetText()
        if text == self.message_shown:
            return
        self.message_shown = text
        limit, role = self.message_fit
        if self.message_probe is None:
            self.message_probe = ui.TextLine()
        self.message_probe.SetFontName(font(role))
        self.message_probe.SetText(text)
        fits = uir1.TextWidth(self.message_probe) <= limit
        uir1.SetFont(self.message, font(role) if fits else kit().font("text_xs"))

    def OnUpdate(self):
        for tick in self.ticks:
            tick()

    def edit(self, *args, **kwargs):
        line = Canvas.edit(self, *args, **kwargs)
        self.edit_lines.append(line)
        line.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
        line.SetTabEvent(ui.__mem_func__(self.focus_next))
        if len(self.edit_lines) == 1:
            line.SetFocus()
        return line

    def focus_next(self):
        for index, line in enumerate(self.edit_lines):
            if line.IsFocus():
                self.edit_lines[(index + 1) % len(self.edit_lines)].SetFocus()
                return True
        return False

    def submit(self, action, values=(), title="", body=""):
        # A deposit, an invitation or a notice does not depend on the data shown when the dialog opened: member awards
        # change the revision every few seconds, so it goes with the current one (player report 21. 10., batch 7 add-on).
        identity = self.owner.model.command_identity(action, self.identity)
        if identity is None:
            self.message.SetText("Údaje se změnily. Zavři okno a otevři ho znovu.")
            return False
        return self.owner.request(action, values, title, body, identity)

    def Close(self):
        self.ticks = []
        for line in self.edit_lines:
            line.KillFocus()
            line.SetReturnEvent(None)
            line.SetEscapeEvent(None)
            line.SetTabEvent(None)
        self.edit_lines = []
        self.KillFocus()
        self.Hide()
        if self.owner and self.owner.dialog is self:
            self.owner.dialog = None
        self.owner = None
        self.clear()

    def OnPressEscapeKey(self):
        self.Close()
        return True


def whole_text(canvas, x, y, text, width, color=INK, role=fontconfig.ROLE_BODY, align="left"):
    """A short table label drawn whole: measured in its font and drawn without the native line limit when it fits,
    limited to ``width`` design units only when it is wider. Owner 21. 10. 2026 (VPS): the native limit showed
    "Duše…" in the 356 px wide Materiál column of a passive, the other materials were whole."""
    line = canvas.text(x, y, text, 0, color, role, align)
    size = line.GetTextSize() if hasattr(line, "GetTextSize") else (0, 0)
    if width and size and size[0] > px(width):
        line.Hide()
        return canvas.text(x, y, text, width, color, role, align)
    return line
