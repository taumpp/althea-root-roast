import fontconfig
import ime
import ui
import uicrimsoncontrols
import wndMgr
from uicrimsonember import SettingsScrollBar

ART = "d:/ymir work/ui/game/guild_v2/"
CHECKBOX = "d:/ymir work/ui/game/crimson_ember/virtual_market/choice/checkbox_"
INK, DIM, GOLD, GREEN, RED = 0xffeee5d6, 0xffaea294, 0xffdcc08b, 0xff96c397, 0xffce6170
MUTED = 0xff82796f
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

def span(start, length):
    """Pixel length of a design span, keeping adjacent spans seamless and lines visible."""
    size = px(start + length) - px(start)
    return max(1, size) if length > 0 else 0

def font(role):
    base, step = _ROLE_STEPS.get(role, (role, 0))
    face, size = fontconfig.FontForRole(base).split(":")
    bold = size.endswith("b")
    return "%s:%d%s" % (face, max(MIN_FONT_SIZE, int(size.rstrip("b")) + step), "b" if bold else "")

def font_height(role):
    return int(font(role).split(":")[1].rstrip("b"))

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

def check(button, checked):
    """Show a checkbox button's current state (state is owned by the caller)."""
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

    def __init__(self, parent, x, y, width, height, callback, text="", style="secondary",
                 selected=False, enabled=True, align="center", role=fontconfig.ROLE_CONTROL, accent=False):
        ui.Window.__init__(self)
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
                self.label.SetPosition(width // 2, max(0, (height - font_height(role)) // 2 - 1))
            else:
                self.label.SetPosition(align, max(0, (height - font_height(role)) // 2 - 1))
            self.label.AddFlag("not_pick")
            self.label.SetText(str(text))
            self.label.Show()
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
        elif self.hovered or self.pressed:
            fill, border, text = hover_fill, hover_border, hover_text
        self.fill.SetColor(native_color(fill))
        for edge in self.edges:
            edge.SetColor(native_color(border))
        self.mark.SetSize(2 if self.accent and self.selected and self.enabled else 0, self.GetHeight())
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

    def OnMouseOverOut(self):
        self.hovered = self.pressed = False
        self.paint()

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
        self.callback = self.wheel = None
        self.Hide()

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
            if isinstance(widget, ui.Button):
                widget.SetEvent(None)
            if isinstance(widget, SettingsScrollBar):
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
        return int((line.GetText().count("\n") + 1) * (font_height(role) + 3) / SCALE + 0.5)

    def image(self, name, x, y, width=None, height=None):
        image = self.keep(ui.ExpandedImageBox())
        image.SetParent(self)
        image.AddFlag("not_pick")
        image.LoadImage(ART + name + ".png")
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
        self.pixel_bar(left, top, w, h, 0xff4c3d2d if not selected else 0xffa9604e)
        self.pixel_bar(left + 1, top + 1, w - 2, h - 2, 0xff100e0c if not selected else 0xff281216)

    def rule(self, x, y, width, color=0xff32281e):
        return self.pixel_bar(px(x), px(y), span(x, width), 1, color)

    def header(self, text, x, y, width):
        self.image("header_804", x, y, width, 28)
        self.text(x + 17, y + 7, text, width - 40, GOLD, fontconfig.ROLE_SECTION)

    def table_header(self, x, y, width, height=28):
        self.pixel_bar(px(x), px(y), span(x, width), span(y, height), 0xff1c1612)
        self.pixel_bar(px(x), px(y + height) - 1, span(x, width), 1, 0xff4c3d2d)

    def button(self, text, x, y, event, enabled=True, width=170, selected=False, tooltip=None):
        """Primary crimson action. Use at most one per screen."""
        button = self.keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(px(x), px(y))
        family = "170x24" if width == 170 else "80x24"
        button.SetUpVisual(uicrimsoncontrols.Visual(family, "selected" if selected else "normal"))
        button.SetOverVisual(uicrimsoncontrols.Visual(family, "hover"))
        button.SetDownVisual(uicrimsoncontrols.Visual(family, "pressed"))
        button.SetDisableVisual(uicrimsoncontrols.Visual(family, "disabled"))
        scale_button(button, text)
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

    def action(self, text, x, y, event, enabled=True, width=150, height=26, style="secondary", selected=False, role=fontconfig.ROLE_CONTROL):
        return self.keep(Flat(self, px(x), px(y), span(x, width), span(y, height), event, text, style,
            selected, enabled, "center", role))

    def row(self, x, y, width, height, event, selected=False, style="row", enabled=True, accent=False):
        """Whole-row hit target; draw its content on the canvas afterwards."""
        return self.keep(Flat(self, px(x), px(y), span(x, width), span(y, height), event, "", style,
            selected, enabled, accent=accent))

    def checkbox(self, x, y, checked, event, enabled=True):
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

    def tab(self, text, x, y, event, selected=False):
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
        self.pixel_bar(left - 4, top - 3, w + 8, h + 6, 0xff6e553f)
        self.pixel_bar(left - 3, top - 2, w + 6, h + 4, 0xff110d0b)
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
        self.pixel_bar(left, top, w, h, 0xff5a4634)
        self.pixel_bar(left + 1, top + 1, w - 2, h - 2, 0xff1d1714)
        if required > 0:
            self.pixel_bar(left + 1, top + 1, min(w - 2, max(0, int((w - 2) * min(current, required) // required))), h - 2, color)

    def pips(self, x, y, width, filled, count=5, height=5):
        step = float(width + 6) / count
        for index in range(count):
            self.bar(x + index * step, y, step - 6, height, 0xffbd8551 if index < filled else 0xff2c251e)

    def shell(self, width, height, title, close):
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

class ScrollList(Canvas):
    def __init__(self, parent, x, y, width, height, rows, row_height, draw, offset=0):
        Canvas.__init__(self, parent, x, y, width, height)
        self.rows, self.row_height, self.draw = rows, row_height, draw
        self.visible = max(1, height // row_height)
        self.maximum = max(0, len(rows) - self.visible)
        self.offset = min(self.maximum, max(0, offset))
        self.content = Canvas(self, 0, 0, width - 16, height)
        self.EnableScissorRect()
        self.content.Show()
        self.scroll = SettingsScrollBar()
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
            self.draw(self.content, row, index * self.row_height, self.design_width - 16)

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
        self.scroll = self.keep(SettingsScrollBar())
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
        self.frame = [self.pixel_bar(0, 0, self.GetWidth(), self.GetHeight(), 0xff6e553f),
            self.pixel_bar(1, 1, self.GetWidth() - 2, self.GetHeight() - 2, 0xff110d0b)]
        self.edit = self.keep(ui.EditLine())
        self.edit.SetParent(self)
        self.edit.SetFontName(font(fontconfig.ROLE_BODY))
        self.edit.SetPackedFontColor(native_color(INK))
        self.edit.SetMax(24)
        self.edit.SetEscapeEvent(escape)
        self.edit.SetReturnEvent(ui.__mem_func__(self.edit.KillFocus))
        self.edit.Show()

    def place(self, x, y, width):
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
        self.owner, self.identity = owner, owner.model.identity()
        self.edit_lines = []
        self.shell(width, height, title, ui.__mem_func__(self.Close))
        self.SetCenterPosition()
        self.message = self.text(24, height - 66, "", width - 48, RED)
        self.close_button = self.action("Zavřít", width - 134, height - 36, ui.__mem_func__(self.Close), width=110)
        self.Show()
        self.SetTop()
        # Native Lock routes IME to the dialog itself instead of its focused
        # EditLine. Use the same floating/focus contract as uiCommon.InputDialog.
        self.SetFocus()

    def primary(self, text, event, enabled=True, reason=None):
        """The dialog's single crimson action, bottom right; Zavřít moves left."""
        width, height = self.design_width, self.design_height
        button = self.button(text, width - 194, height - 36, event, enabled and not reason, tooltip=reason)
        self.close_button.SetPosition(px(width - 324), px(height - 35))
        if reason:
            self.message.SetPackedFontColor(native_color(DIM))
            self.message.SetText(reason)
        return button

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
        if self.identity != self.owner.model.identity():
            self.message.SetText("Údaje se změnily. Zavři okno a otevři ho znovu.")
            return False
        return self.owner.request(action, values, title, body, self.identity)

    def Close(self):
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
