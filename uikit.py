# -*- coding: utf-8 -*-
"""Althea UI kit runtime: frames, generic title bar, 3-slice buttons, toggle, segment, slider, dropdown list,
confirmation dialog, icons and text helpers; settings v5 adds the scrollbar, key cap, chip, edit field and section;
the owner's choices of 2026-10-06 add ONE button family (Button roles primary / secondary, ButtonGroup B1 / B3,
the chip as a segment cell), the key caps K1-K4 (KEYCAP_STYLE) and the check box.

Settings window c9 v4 and v5, 2026-10-05; design and decisions in docs/SETTINGS_KIT_LOOK.md.
Textures come from the ui pack (d:/ymir work/ui/public/althea_kit/, tools/build_althea_ui_kit.py), the
geometry from uikitlayout (shared with the offline preview) and the tokens from the generated uikittokens.

Any window can use it::

    kit = uikit.Kit(uikit.Profile(), uikit.FontSet())                # profile by screen height, Spectral (B)
    self.frame = uikit.Frame(self, kit, 'window', 0, 0, w, h, bg=True)
    self.bar = uikit.TitleBar(self, kit, 5, 5, w - 10, T('Nastavení', 'Settings'), on_close=self.Close)
    self.ok = uikit.Button(self, kit, x, y, 160, T('Zavřít', 'Close'), role='close', event=self.Close)

Ornaments are always drawn at their native size; only plain tiles repeat (SetRenderingRect, like ui.Board)
and only plain fills stretch (SetScale). Widgets paint their own state from Python mouse events, as
uiguildv2widgets does. Text is never baked except the decorative window titles (uikittokens.TITLES).
"""
import grp
import ui
import wndMgr

import uikitlayout as L
import uikittokens as T
import uiwheel

ROOT = T.KIT_ROOT
R1_ROOT = 'd:/ymir work/ui/public/althea_r1/'   # the R1 kit (uir1): header vein, plain X, row band line

# --------------------------------------------------------------------------- skins (R1 look of the kit)
# The team (7. 10. 2026, proposal 2 variant B) kept the layout and UX of the kit windows (Settings, its dialogs, the
# stone queue editor, the ESC menu) and moved their style, header, frame and font / icon colours into R1. The R1 skin
# swaps the texture root (tools/build_althea_r1_nastaveni.py: every gold texture in R1 at the same path and size,
# uir1nastavenitokens), the colours and fonts of uikittokens and draws the title bar as the R1 header. "Starý vzhled"
# (settingslook 'legacy') never builds a kit window; a skin that fails to build falls back to the gold kit for the
# rest of the session (SkinFailed).
SKIN = 'gold'
_GOLD_TOKENS = None
_SKIN_FAILED = [False]


def _SkinTokens():
    import uir1nastavenitokens
    return uir1nastavenitokens


def UseR1Skin():
    """The R1 skin unless Settings -> "Starý vzhled" chose the original windows or the R1 skin failed this session."""
    if _SKIN_FAILED[0]:
        return False
    try:
        import settingslook
        return settingslook.Get('look') != 'legacy'
    except Exception:
        return True


def SetSkin(name):
    """'r1' or 'gold': the texture root, the colours and the font sets of uikittokens (read at call time by every
    kit window). Returns the skin in use; an R1 skin whose tokens cannot be read stays gold."""
    global SKIN, _GOLD_TOKENS
    name = 'r1' if name == 'r1' else 'gold'
    if name == SKIN:
        return SKIN
    if name == 'r1':
        try:
            tokens = _SkinTokens()
        except Exception:
            TraceSkin('R1 skin tokens')
            _SKIN_FAILED[0] = True
            return SKIN
        if _GOLD_TOKENS is None:
            _GOLD_TOKENS = dict((key, getattr(T, key)) for key in list(tokens.COLORS) + ['FONT_SETS'])
        for key, value in tokens.COLORS.items():
            setattr(T, key, value)
        T.FONT_SETS = tokens.FONT_SETS
    elif _GOLD_TOKENS is not None:
        for key, value in _GOLD_TOKENS.items():
            setattr(T, key, value)
    SKIN = name
    return SKIN


def SyncSkin():
    return SetSkin('r1' if UseR1Skin() else 'gold')


def R1():
    return SKIN == 'r1'


def TraceSkin(what):
    try:
        import dbg
        import traceback
        dbg.TraceError('%s: %s' % (what, traceback.format_exc()))
    except Exception:
        pass


def SkinFailed(what):
    """A kit window could not be built in the R1 skin: traced, the gold kit for the rest of the session (the window
    is built again by its owner). True when the R1 skin was in use (a retry in gold makes sense)."""
    TraceSkin('%s (R1 skin)' % what)
    was = SKIN == 'r1'
    _SKIN_FAILED[0] = True
    SetSkin('gold')
    return was


def Path(rel):
    """Full path of a kit texture (relative to the kit root) in the skin in use; an absolute path stays."""
    if rel.startswith('d:/'):
        return rel
    if SKIN == 'r1':
        tokens = _SkinTokens()
        if not rel.startswith(tokens.KEEP_GOLD):
            return tokens.ROOT + rel
    return ROOT + rel


def _Size(path):
    """Native size of a kit path or of an R1 kit path (R1_ROOT + ...)."""
    if path.startswith(R1_ROOT):
        import uir1tokens
        return tuple(uir1tokens.SIZES[path[len(R1_ROOT):]])
    return L.size(path)


def Tr_(czech, english):
    """Kit texts in the client language (settingslocale when present, Czech otherwise)."""
    try:
        from settingslocale import Text
    except ImportError:
        return czech
    return Text(czech, english)


def Profile(screen_height=None):
    """'1080' (window 1160 x 780) for screens at least 900 px high, otherwise '768' (840 x 620)."""
    if screen_height is None:
        try:
            screen_height = wndMgr.GetScreenHeight()
        except Exception:
            screen_height = 768
    return '1080' if int(screen_height) >= 900 else '768'


def FontCell(descriptor):
    """Cell height of a client font descriptor "Family:12[b][i][a]" (GDI cell, not em)."""
    size = descriptor.rpartition(':')[2]
    digits = ''.join(ch for ch in size if ch.isdigit())
    return int(digits or 12)


_SERIF = None
SERIF_PROBE = ('Althea Book:21a', 'Tahoma:21a', 'Žluťoučký kůň úpěl ďábelské ódy')


def FontSet():
    """Font set of the kit windows: 'B' = Spectral "Althea Book" whenever the client renders it, 'A' = Tahoma with an
    older EXE that ignores registered font families (it would draw the B sizes as an oversized Tahoma). Measured once:
    such an EXE renders 'Althea Book:21a' exactly as wide as 'Tahoma:21a'. A failed measurement keeps 'B'."""
    global _SERIF
    if _SERIF is None:
        try:
            widths = []
            for font in SERIF_PROBE[:2]:
                probe = ui.TextLine()
                probe.SetFontName(font)
                probe.SetText(SERIF_PROBE[2])
                widths.append(int(probe.GetTextSize()[0]))
            _SERIF = widths[0] != widths[1]
        except Exception:
            _SERIF = True
    return 'B' if _SERIF else 'A'


class Kit(object):
    """Profile and font set of one window. Font sizes: L (headings), M (rows), Mb, S (notes), Sb."""

    def __init__(self, prof, font_set='A'):
        SyncSkin()
        self.prof = prof if prof in T.PROFILES else '1080'
        self.font_set = font_set if font_set in ('A', 'B') else 'A'
        self.P = T.PROFILES[self.prof]
        self.skin = SKIN

    def p(self, key):
        return self.P[key]

    def font(self, size):
        return T.FONT_SETS[self.prof][self.font_set][size]

    def cell(self, size):
        return FontCell(self.font(size))

    def group_font(self):
        # A: Tahoma bold (variant 3 of the sidebar study); B: upper case of the same family, semibold (variant 4).
        # R1 skin: Cinzel ('G'), as the button labels and window titles of R1.
        fonts = T.FONT_SETS[self.prof][self.font_set]
        if 'G' in fonts:
            return fonts['G']
        return T.GROUP_FONT_A[self.prof] if self.font_set == 'A' else self.font('Sb')

    def button_font(self, primary=False):
        """The label font of a kit button: the row font (semibold on the primary); Cinzel ('Btn') in the R1 skin."""
        fonts = T.FONT_SETS[self.prof][self.font_set]
        return fonts['Btn'] if 'Btn' in fonts else self.font('Mb' if primary else 'M')

    def group_text(self, text):
        return Upper(text) if self.font_set == 'B' else text

    def rel(self, path):
        return self.prof + '/' + path

    def size(self, path):
        return L.size(self.rel(path))

    def bar(self, kind='window'):
        return L.bar_height(self.prof, kind)


def Color(packed):
    return ((packed >> 16) & 255) / 255.0, ((packed >> 8) & 255) / 255.0, (packed & 255) / 255.0


def GenerateColor(packed, alpha=1.0):
    r, g, b = Color(packed)
    return grp.GenerateColor(r, g, b, alpha)


def _linear(widget):
    setter = getattr(widget, 'SetLinearFiltering', None)
    if setter:
        setter(True)


def _apply(widget, op, dx=0, dy=0):
    kind, path, x, y, w, h = op
    widget.LoadImage(Path(path))
    widget.SetPosition(x + dx, y + dy)
    if kind == 'tile':
        tw, th = _Size(path)
        widget.SetRenderingRect(0.0, 0.0, float(w) / tw - 1.0, float(h) / th - 1.0)
    elif kind == 'stretch':
        tw, th = _Size(path)
        widget.SetScale(float(w) / tw, float(h) / th)
        _linear(widget)
    if w > 0 and h > 0:
        widget.Show()
    else:
        widget.Hide()


class Ops(object):
    """Images of one op list (uikitlayout) under a parent. Apply() re-skins in place: the same op order reuses
    the same widgets, so a state change never re-creates windows."""

    def __init__(self, parent, ops=None, dx=0, dy=0):
        self.parent = parent
        self.items = []
        self.dx, self.dy = dx, dy
        if ops:
            self.Apply(ops)

    def Apply(self, ops):
        for index, op in enumerate(ops):
            image = op[0] == 'image'
            if index < len(self.items) and self.items[index][0] != image:
                self.items[index][1].Hide()
                self.items[index] = None
            if index >= len(self.items) or self.items[index] is None:
                widget = ui.ImageBox() if image else ui.ExpandedImageBox()
                widget.SetParent(self.parent)
                widget.AddFlag('not_pick')
                if index >= len(self.items):
                    self.items.append((image, widget))
                else:
                    self.items[index] = (image, widget)
            _apply(self.items[index][1], op, self.dx, self.dy)
        for unused, widget in self.items[len(ops):]:
            widget.Hide()

    def Show(self):
        for unused, widget in self.items:
            widget.Show()

    def Hide(self):
        for unused, widget in self.items:
            widget.Hide()

    def Destroy(self):
        self.Hide()
        self.items = []
        self.parent = None


def Image(parent, path, x, y, pick=False):
    """Native-size kit image (path relative to the kit root)."""
    image = ui.ImageBox()
    image.SetParent(parent)
    if not pick:
        image.AddFlag('not_pick')
    image.LoadImage(Path(path))
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


def IconPath(name, size, state='normal'):
    if name not in T.ICONS or size not in T.ICON_SIZES:
        return None
    return 'icons/%d/%s_%s.png' % (size, name, state)


def Icon(parent, name, size, x, y, state='normal'):
    path = IconPath(name, size, state)
    return Image(parent, path, x, y) if path else None


def Text(parent, text, x, y, font, color=None, align='left', valign='center', outline=False, limit=None):
    line = ui.TextLine()
    line.SetParent(parent)
    line.AddFlag('not_pick')
    line.SetFontName(font)
    line.SetPackedFontColor(T.INK if color is None else color)
    if align == 'center':
        line.SetHorizontalAlignCenter()
    elif align == 'right':
        line.SetHorizontalAlignRight()
    if valign == 'center':
        line.SetVerticalAlignCenter()
    if outline:
        line.SetOutline()
    if limit:
        line.SetLimitWidth(int(limit))
    line.SetPosition(int(x), int(y))
    line.SetText(text)
    line.Show()
    return line


def Upper(text, encoding='cp1250'):
    """``text`` in upper case with every Czech diacritic (č -> Č, ě -> Ě, ů -> Ů, ď ť ň ř š ž ...): the R1 titles,
    headers and group headings. A Python 3 str (the client decodes the locale text, system.__DecodePackText__) is
    upper-cased directly. A byte string (a Python 2 client's cp1250 locale text) is decoded with ``encoding``, upper-
    cased and encoded back: str.upper on the bytes changes only ASCII in the C locale ("KOřIST - SVATYNě ORKů"). A text
    not valid in the code page, or whose capitals are not in it, falls back to the plain upper()."""
    if not text:
        return text
    if isinstance(text, bytes):
        try:
            return text.decode(encoding).upper().encode(encoding)
        except (UnicodeError, LookupError):
            return text.upper()
    return text.upper()


def SetFont(line, font, text=None):
    """Font change of a text line that may already show text. The engine's SetFontName only swaps the font pointer
    (CTextLine::SetFontName -> CGraphicTextInstance::SetTextPointer, no new layout) and SetText with the same string
    returns early (CGraphicTextInstance::SetValue), so glyphs laid out in the old font would be drawn from the new
    font's atlas - garbage letters (2026-10-06, screenshots 189 / 191: "ứửk ẻé ẞ" for "Najít funkci…"). The
    line is emptied first, so the text is laid out again in the new font."""
    if text is None:
        text = line.GetText()
    line.SetText('')
    line.SetFontName(font)
    line.SetText(text or '')


def TextWidth(line):
    try:
        return int(line.GetTextSize()[0])
    except Exception:
        return len(line.GetText()) * 7


def WordGap(text, font):
    """``text`` with every single space between two words doubled when ``font`` is Cinzel ("Althea Caps"), otherwise
    ``text`` itself. The space of Cinzel is only 0.25 em: at the 15 - 17 px of a button label that is 3 px, as much as
    the gaps between its letters, so the words of a two-word label ran together ("AKTIVOVATBUFFY", "ZRUŠITMISI",
    "OTEVŘÍTALBUM"); two spaces are 6 px. Idempotent (a double space stays double)."""
    if not text or ' ' not in text or not str(font).lower().startswith('althea caps'):
        return text
    out = []
    last = len(text) - 1
    for index, ch in enumerate(text):
        single = ch == ' ' and 0 < index < last and text[index - 1] != ' ' and text[index + 1] != ' '
        out.append('  ' if single else ch)
    return ''.join(out)


def Wrap(parent, text, x, y, width, font, color, line_height):
    """Word-wrapped lines (the client has no automatic wrap); returns (lines, next y)."""
    probe = ui.TextLine()
    probe.SetFontName(font)
    lines, current = [], ''
    for word in (text or '').split():
        candidate = (current + ' ' + word).strip()
        probe.SetText(candidate)
        if not current or TextWidth(probe) <= width:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    widgets = []
    for line in lines:
        widgets.append(Text(parent, line, x, y, font, color, valign='top'))
        y += line_height
    return widgets, y


def HLine(parent, x, y, w, packed, alpha=1.0):
    bar = ui.Bar()
    bar.SetParent(parent)
    bar.AddFlag('not_pick')
    bar.SetPosition(int(x), int(y))
    bar.SetSize(int(w), 1)
    bar.SetColor(GenerateColor(packed, alpha))
    bar.Show()
    return bar


def Rect(parent, x, y, w, h, packed, alpha=1.0):
    """Plain filled rectangle (ui.Bar): column shades and hairlines of the v5 shell (no frames inside a window)."""
    bar = HLine(parent, x, y, w, packed, alpha)
    bar.SetSize(int(w), int(h))
    return bar


class Layer(ui.Window):
    """Not-pickable container that draws an op list (frames, dividers). Keep a reference to it."""

    def __init__(self, parent, x, y, w, h, ops):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.ops = Ops(self, ops)
        self.Show()

    def Apply(self, ops):
        self.ops.Apply(ops)

    def Destroy(self):
        self.ops.Destroy()


def Frame(parent, kit, kind, x, y, w, h, bg=False, vignette=False):
    """9-slice frame ('window' or 'panel') of any size >= 2 x corner."""
    return Layer(parent, x, y, w, h, L.frame(kind, kit.prof, w, h, bg=bg, vignette=vignette))


def Divider(parent, kit, x, y, w):
    h = L.size(kit.rel('divider_center.png'))[1]
    return Layer(parent, x, y, w, h, L.divider(kit.prof, w))


class R1Band(ui.Window):
    """The R1 row state of the skin (uir1.Band): hover = a lighter fill, selected = the dark fill with the red line
    under the row and a 2 px red mark on its left edge (proposal 2 B). Not pickable; Show / Hide like the band."""

    def __init__(self, parent, x, y, w, h, state):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        import uir1tokens as R1T
        self.state = state
        self.line = self.mark = None
        if state == 'hover':
            self.fill = Rect(self, 0, 0, w, h, R1T.BAND_HOVER, R1T.BAND_ALPHA['hover'])
        else:
            self.fill = Rect(self, 0, 0, w, h, R1T.BAND_SELECTED, R1T.BAND_ALPHA['selected'])
            self.line = Ops(self, self._LineOps(w, h))
            self.mark = Rect(self, 0, 0, 2, int(h) - 1, R1T.RED)
        self.Show()

    @staticmethod
    def _LineOps(w, h):
        import uir1layout as RL
        return [(kind, R1_ROOT + path, ox, oy, ow, oh) for kind, path, ox, oy, ow, oh in RL.band_line(0, int(h), int(w))]

    def Resize(self, w, h):
        w, h = int(w), int(h)
        self.SetSize(w, h)
        self.fill.SetSize(w, h)
        if self.line is not None:
            self.line.Apply(self._LineOps(w, h))
            self.mark.SetSize(2, h - 1)

    def SetScale(self, sx, sy):
        """The gold band is a stretched 128 x 28 texture (callers resize it with SetScale): the same size here."""
        w, h = L.size('select/band_%s.png' % self.state)
        self.Resize(int(round(w * sx)), int(round(h * sy)))


def Band(parent, x, y, w, h, state='selected'):
    """Stretched selection / hover band of the sidebar and rows (the R1 row band in the R1 skin)."""
    if SKIN == 'r1':
        return R1Band(parent, x, y, w, h, state)
    band = ui.ExpandedImageBox()
    band.SetParent(parent)
    band.AddFlag('not_pick')
    _apply(band, ('stretch', 'select/band_%s.png' % state, int(x), int(y), int(w), int(h)))
    return band


# --------------------------------------------------------------------------- interactive base
class Interactive(ui.Window):
    """Python-painted control: hover, pressed and disabled states from the native mouse callbacks."""

    def __init__(self):
        ui.Window.__init__(self)
        self.enabled = True
        self.hovered = self.pressed = False
        self.callback = None
        self.on_hover = None

    def SetEvent(self, callback):
        self.callback = callback

    def SetHoverEvent(self, callback):
        self.on_hover = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback

    def Enable(self):
        self.enabled = True
        self.paint()

    def Disable(self):
        self.enabled = False
        self.hovered = self.pressed = False
        self.paint()

    def IsEnabled(self):
        return self.enabled

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.pressed:
            return 'pressed'
        return 'hover' if self.hovered else 'normal'

    def OnMouseOverIn(self):
        self.hovered = True
        self.paint()
        if self.on_hover:
            self.on_hover()

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
        if activate and self.enabled:
            self.click()
        return True

    def click(self):
        if self.callback:
            self.callback()

    def paint(self):
        pass


class HitArea(Interactive):
    """Invisible pickable area (a settings row): hover callback, optional click."""

    def __init__(self, parent, x, y, w, h):
        Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.Show()


class ImageButton(Interactive):
    """Four-state image button; pattern is a path with '%s' for the state (e.g. the close cross)."""

    def __init__(self, parent, pattern, x, y, w, h, event=None, inset=0):
        Interactive.__init__(self)
        self.pattern = pattern
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.image = ui.ImageBox()
        self.image.SetParent(self)
        self.image.AddFlag('not_pick')
        self.image.SetPosition(int(inset), int(inset))   # a glyph smaller than its hit box (the R1 X)
        self.image.Show()
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        self.image.LoadImage(Path(self.pattern % self.state()))


# One control family (2026-10-06, "ty čudlíky jsou hrozné, každý vypadá jinak"): three roles only - primary
# (ruby, at most one per screen), secondary (dark) and the on/off chip - with the same thin frame, corners, outline
# and one height in the content ('content') and one in a window footer ('bar'). The old role names of the c9 / v4.1
# kit map onto it, so every caller (settings, panels, stone queue, editor, ESC menu, dialogs) gets the same button.
ROLES = {'primary': 'primary', 'secondary': 'secondary', 'reset': 'secondary', 'ruby': 'primary',
         'ruby_s': 'primary', 'close': 'primary'}
RUBY_ROLES = ('primary', 'close', 'ruby', 'ruby_s')
# B1 = separate small buttons with a gap (owner's choice); 'b3' = adjacent secondary buttons joined into one block
# (segment-like cells, design v5 section 3 B3, still in play with the team). ButtonGroup reads it.
BUTTON_GROUPS = 'b1'


def ButtonRole(role):
    return ROLES.get(role, 'secondary')


def ButtonHeight(kit, size='content'):
    return L.button6_height(kit.prof, 'b' if size == 'bar' else 'c')


class Button(Interactive):
    """Button of the v6 family: role 'primary' (ruby) or 'secondary' (dark; the old 'reset'); size 'content' (rows,
    popups, panels) or 'bar' (window footer); pos 'single' or first / mid / last inside a joined B3 block. Optional
    kit icon before the label. One font for every button (the row font; semibold on the primary)."""

    def __init__(self, parent, kit, x, y, w, text='', role='secondary', icon=None, event=None, font=None,
                 align='center', size='content', pos='single'):
        Interactive.__init__(self)
        self.kit, self.align = kit, align
        self.role = ButtonRole(role)
        self.size = 'b' if size == 'bar' else 'c'
        self.pos = pos
        self.w = int(w)
        self.h = L.button6_height(kit.prof, self.size)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, self.h)
        # Plate images first: children draw in creation order, the icon and label must stay above them.
        self.ops = Ops(self, L.button6(kit.prof, self.role, self.size, pos, 'normal', self.w))
        self.icon_name = icon
        # One icon size for every button of the family (2026-10-06, ESC: the 24 px arrow of "Zpět do hry" was
        # too big next to its text): 20 px, in the footer as in the content.
        self.icon_size = 20
        # 1 px (1080) / 0 (768): measured on the owner's ESC screenshot 196 (6. 10.) the old 2 px lift left the label
        # cap/x-height block ~1.5 px above the plate centre.
        self.nudge = (1 if kit.prof == '1080' else 0) if kit.font_set == 'B' else 0
        self.icon = None
        if icon and IconPath(icon, self.icon_size):
            self.icon = Image(self, IconPath(icon, self.icon_size), 0, (self.h - self.icon_size) // 2)
        primary = self.role == 'primary'
        font = kit.button_font(primary)
        self.given_text = text
        self.label = Text(self, WordGap(text, font), 0, self.h // 2, font, T.GOLD_HI if primary else T.BUTTON_TEXT)
        self.callback = event
        self.paint()
        self.Show()

    def Pad(self):
        return 14 if self.kit.prof == '1080' else 10

    def FitWidth(self, minimum=0):
        """As wide as the label (+ icon) and the padding, at least ``minimum``."""
        icon = self.icon_size + 6 if self.icon else 0
        self.SetWidth(max(int(minimum), TextWidth(self.label) + icon + 2 * self.Pad() + 4))
        return self.w

    def SetText(self, text):
        self.given_text = text
        self.label.SetText(WordGap(text, self.kit.button_font(self.role == 'primary')))
        self._place()

    def GetText(self):
        """The text as given (the label shows it with the word gaps of WordGap)."""
        shown = self.label.GetText()
        font = self.kit.button_font(self.role == 'primary')
        return self.given_text if shown == WordGap(self.given_text, font) else shown

    def SetWidth(self, w):
        self.w = int(w)
        self.SetSize(self.w, self.h)
        self.paint()

    def _place(self):
        dy = 1 if self.pressed else 0
        tw = TextWidth(self.label)
        if self.align == 'left':
            x = self.Pad()
        else:
            total = tw + (self.icon_size + 6 if self.icon else 0)
            x = (self.w - total) // 2
        if self.icon:
            self.icon.SetPosition(x, (self.h - self.icon_size) // 2 + dy)
            x += self.icon_size + 6
        # Centred like the row texts: the Spectral lower-case body (not the font cell) on the button centre.
        self.label.SetPosition(x, self.h // 2 + dy - self.nudge)

    def paint(self):
        self.ops.Apply(L.button6(self.kit.prof, self.role, self.size, self.pos, self.state(), self.w))
        if self.icon and self.icon_name:
            state = {'disabled': 'disabled', 'hover': 'hover', 'pressed': 'active'}.get(self.state(), 'normal')
            self.icon.LoadImage(Path(IconPath(self.icon_name, self.icon_size, state)))
        self.label.SetPackedFontColor(T.DISABLED if not self.enabled else
                                      (T.GOLD_HI if self.role == 'primary' else T.BUTTON_TEXT))
        self._place()


class ButtonGroup(ui.Window):
    """Adjacent secondary actions (e.g. Vysunout / Vyrovnat): separate buttons with a gap (B1) or one joined block of
    segment-like cells (B3) - BUTTON_GROUPS picks it for the whole client. items = [(text, event)]; buttons[i] are
    ordinary Buttons (SetText / Enable / Disable). Width() is known after construction; the caller places it."""

    def __init__(self, parent, kit, items, size='content', min_w=0, gap=None, style=None):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit = kit
        self.style = style or BUTTON_GROUPS
        joined = self.style == 'b3' and len(items) > 1
        self.gap = 0 if joined else (gap if gap is not None else (8 if kit.prof == '1080' else 6))
        self.buttons = []
        n = len(items)
        for index, (text, event) in enumerate(items):
            pos = 'single' if not joined else ('first' if index == 0 else ('last' if index == n - 1 else 'mid'))
            self.buttons.append(Button(self, kit, 0, 0, 40, text, role='secondary', event=event, size=size, pos=pos))
        self.min_w = int(min_w)
        self.Layout()
        self.Show()

    def Layout(self):
        widths = [button.FitWidth(self.min_w) for button in self.buttons]
        if self.style == 'b3' and len(widths) > 1:
            widths = [max(widths)] * len(widths)   # one block: equal cells, like a segment
        x = 0
        for button, w in zip(self.buttons, widths):
            button.SetWidth(w)
            button.SetPosition(x, 0)
            x += w + self.gap
        self.width = max(0, x - self.gap)
        self.h = self.buttons[0].h if self.buttons else ButtonHeight(self.kit)
        self.SetSize(self.width, self.h)

    def Width(self):
        return self.width

    def SetHoverEvent(self, callback):
        for button in self.buttons:
            button.SetHoverEvent(callback)

    def SetWheelEvent(self, callback):
        for button in self.buttons:
            button.SetWheelEvent(callback)


# The on/off control of the settings (2026-10-06: "nevím, jestli se mi líbí" - variants for the vote; the
# code keeps today's look until the vote): 'v5' today's ruby track with the brass knob, 'flat' a flat smaller
# switch, 'check' the kit check box, 'segment' two cells Zap | Vyp, 'chip' one chip Zapnuto / Vypnuto. One constant for
# every Toggle of the client (settings rows, Panely, dialogs); the API (SetOn, Enable, Size, the callback) is the same.
TOGGLE_STYLE = 'v5'
TOGGLE_STYLES = ('v5', 'flat', 'check', 'segment', 'chip')


def _ToggleLabels(style):
    if style == 'chip':
        return Tr_('Zapnuto', 'On'), Tr_('Vypnuto', 'Off')
    return Tr_('Zap', 'On'), Tr_('Vyp', 'Off')


class Toggle(Interactive):
    """On/off control in the style TOGGLE_STYLE (default: the c9 switch, brass knob on a ruby track). The callback
    flips the value; the segment style switches only when the other cell is clicked."""

    def __init__(self, parent, kit, x, y, on=False, event=None, style=None):
        Interactive.__init__(self)
        self.kit = kit
        self.style = style if style in TOGGLE_STYLES else TOGGLE_STYLE
        self.on = bool(on)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        w, h = Toggle.Size(kit, self.style)
        self.SetSize(w, h)
        self.image = self.ops = self.bullet = None
        self.labels = []
        if self.style in ('v5', 'flat', 'check'):
            self.image = ui.ImageBox()
            self.image.SetParent(self)
            self.image.AddFlag('not_pick')
            self.image.Show()
        else:
            # The cell images are created NOW, before the texts: children draw in creation order and an Ops filled
            # later would cover the labels (offline render 2026-10-06: an empty "Zap | Vyp").
            if self.style == 'chip':
                first = L.button6(kit.prof, 'chip_off', 'c', 'single', 'normal', w)
            else:
                first = (L.segment_cell(kit.prof, 'first', 'normal', w // 2) +
                         [(kind, path, ox + w // 2, oy, ow, oh) for kind, path, ox, oy, ow, oh in
                          L.segment_cell(kit.prof, 'last', 'normal', w - w // 2)])
            self.ops = Ops(self, first)
            if self.style == 'chip':
                bw, bh = kit.size('bullet/diamond_normal.png')
                pad = 12 if kit.prof == '1080' else 9
                self.bullet = Image(self, kit.rel('bullet/diamond_normal.png'), pad, (h - bh) // 2)
                self.labels = [Text(self, '', pad + bw + 8, h // 2, kit.font('M'), T.INK_DIM)]
            else:
                self.labels = [Text(self, text, 0, h // 2, kit.font('S' if kit.prof == '768' else 'M'), T.INK_DIM,
                                    align='center') for text in _ToggleLabels('segment')]
        self.callback = event
        self.paint()
        self.Show()

    @staticmethod
    def Size(kit, style=None):
        style = style if style in TOGGLE_STYLES else TOGGLE_STYLE
        if style == 'v5':
            return (max(kit.size('toggle/on_normal.png')[0], kit.size('toggle/off_normal.png')[0]),
                    kit.size('toggle/on_normal.png')[1])
        if style == 'flat':
            return tuple(kit.size('toggle_flat/on_normal.png'))
        if style == 'check':
            return kit.p('check'), kit.p('check')
        probe = ui.TextLine()
        if style == 'segment':
            probe.SetFontName(kit.font('S' if kit.prof == '768' else 'M'))
            widths = []
            for text in _ToggleLabels('segment'):
                probe.SetText(text)
                widths.append(TextWidth(probe) + 2 * Segment.PAD)
            return 2 * max(widths + [44 if kit.prof == '1080' else 36]), kit.p('seg_h')
        probe.SetFontName(kit.font('M'))
        bw = kit.size('bullet/diamond_normal.png')[0]
        pad = 12 if kit.prof == '1080' else 9
        widest = 0
        for text in _ToggleLabels('chip'):
            probe.SetText(text)
            widest = max(widest, TextWidth(probe))
        return pad + bw + 8 + widest + pad + 2, L.button6_height(kit.prof, 'c')

    def SetOn(self, on):
        on = bool(on)
        if on != self.on:
            self.on = on
            self.paint()

    def click(self):
        if self.style == 'segment':
            try:
                mx = wndMgr.GetMousePosition()[0] - self.GetGlobalPosition()[0]
            except Exception:
                mx = None
            if mx is not None and (mx < self.GetWidth() // 2) == self.on:
                return                                              # the cell that is already selected
        Interactive.click(self)

    def paint(self):
        st = self.state()
        w, h = self.GetWidth(), self.GetHeight()
        if self.style in ('v5', 'flat'):
            folder = 'toggle' if self.style == 'v5' else 'toggle_flat'
            path = '%s/%s_%s.png' % (folder, 'on' if self.on else 'off', st)
            self.image.LoadImage(Path(self.kit.rel(path)))
            # Right-aligned: the on and off textures differ by a few pixels.
            self.image.SetPosition(w - self.kit.size(path)[0], 0)
        elif self.style == 'check':
            self.image.LoadImage(Path(L.check(self.kit.prof, self.on, {'pressed': 'hover'}.get(st, st))))
            self.image.SetPosition(0, 0)
        elif self.style == 'chip':
            self.ops.Apply(L.button6(self.kit.prof, 'chip_on' if self.on else 'chip_off', 'c', 'single', st, w))
            self.bullet.LoadImage(Path(self.kit.rel('bullet/diamond_%s.png' % ('selected' if self.on else 'normal'))))
            self.labels[0].SetText(_ToggleLabels('chip')[0 if self.on else 1])
            self.labels[0].SetPackedFontColor(T.DISABLED if st == 'disabled' else (T.GOLD_HI if self.on else T.INK_DIM))
        else:
            half = w // 2
            ops = []
            for index, (pos, selected) in enumerate((('first', self.on), ('last', not self.on))):
                cell = 'disabled' if st == 'disabled' else ('selected' if selected else
                                                            ('hover' if st == 'hover' else 'normal'))
                ops += [(kind, path, ox + index * half, oy, ow, oh) for kind, path, ox, oy, ow, oh in
                        L.segment_cell(self.kit.prof, pos, cell, half if index == 0 else w - half)]
                self.labels[index].SetPosition(index * half + (half if index == 0 else w - half) // 2, h // 2)
                self.labels[index].SetPackedFontColor(T.DISABLED if st == 'disabled' else
                                                      (T.GOLD_HI if selected else T.INK_DIM))
            self.ops.Apply(ops)


class SegmentCell(Interactive):
    def __init__(self, segment, index, pos, text):
        Interactive.__init__(self)
        self.segment, self.index, self.pos = segment, index, pos
        self.selected = False
        self.SetParent(segment)
        self.ops = Ops(self, L.segment_cell(segment.kit.prof, pos, 'normal', 16))  # images before the label
        self.label = Text(self, text, 0, 0, segment.font, T.INK_DIM, align='center')
        self.w = 0
        self.Show()

    def Place(self, x, w, h):
        self.w = int(w)
        self.SetPosition(int(x), 0)
        self.SetSize(self.w, h)
        self.label.SetPosition(self.w // 2, h // 2)
        self.paint()

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.selected:
            return 'selected'
        return 'hover' if self.hovered else 'normal'

    def paint(self):
        if not self.w:
            return
        self.ops.Apply(L.segment_cell(self.segment.kit.prof, self.pos, self.state(), self.w))
        self.label.SetPackedFontColor(T.GOLD_HI if self.selected else (T.DISABLED if not self.enabled else
                                                                       (T.INK if self.hovered else T.INK_DIM)))

    def click(self):
        self.segment.Select(self.index)

    def OnMouseOverIn(self):
        Interactive.OnMouseOverIn(self)
        if self.segment.on_hover:
            self.segment.on_hover()


class Segment(ui.Window):
    """One-of-N switch (c9 segment). Cells share one width when it fits max_width, otherwise each cell is as
    wide as its label. Width() is known after construction, so the caller places it afterwards."""
    PAD = 12

    def __init__(self, parent, kit, options, event=None, font=None, max_width=None, min_cell=None):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.options = list(options)
        self.values = [value for value, unused in self.options]
        self.callback = event
        self.on_hover = None
        self.font = font or kit.font('S' if kit.prof == '768' else 'M')
        n = len(self.options)
        self.cells = [SegmentCell(self, i, 'single' if n == 1 else
                                  ('first' if i == 0 else ('last' if i == n - 1 else 'mid')), label)
                      for i, (unused, label) in enumerate(self.options)]
        h = kit.p('seg_h')
        min_cell = min_cell or (68 if kit.prof == '1080' else 52)
        texts = [TextWidth(cell.label) for cell in self.cells]
        uniform = max([max(min_cell, w + 2 * self.PAD) for w in texts] or [0])
        if not max_width or uniform * n <= max_width:
            widths = [uniform] * n
        else:  # as wide as each label, the spare room shared out evenly
            widths = [max(min_cell // 2, w + 2 * self.PAD) for w in texts]
            spare = max(0, int(max_width) - sum(widths)) // max(1, n)
            widths = [w + min(spare, max(0, uniform - w)) for w in widths]
        x = 0
        for cell, w in zip(self.cells, widths):
            cell.Place(x, w, h)
            x += w
        self.width = x
        self.SetSize(x, h)
        self.Show()

    def Width(self):
        return self.width

    def SetHoverEvent(self, callback):
        self.on_hover = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback
        for cell in self.cells:
            cell.OnMouseWheel = callback

    def SetValue(self, value):
        for cell, v in zip(self.cells, self.values):
            selected = v == value
            if selected != cell.selected:
                cell.selected = selected
                cell.paint()

    def Select(self, index):
        if self.callback:
            self.callback(self.values[index])

    def Enable(self):
        for cell in self.cells:
            cell.Enable()

    def Disable(self):
        for cell in self.cells:
            cell.Disable()


class Slider(ui.Window):
    """c9 slider: bronze track (3-slice), ruby fill to the knob centre, brass diamond knob (ui.DragButton).
    Width() = track + knob; SetSliderPos/GetSliderPos like ui.SliderBar, and a programmatic position never
    re-announces a change (the knob callback is switched off meanwhile)."""

    def __init__(self, parent, kit, track_w, event=None):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.track_w = int(track_w)
        self.knob_w, self.knob_h = kit.size('knob_normal.png')
        sh = kit.p('slider_h')
        self.h = max(self.knob_h, sh)
        self.SetSize(self.track_w + self.knob_w, self.h)
        self.track_x, self.track_y = self.knob_w // 2, (self.h - sh) // 2
        self.track = Ops(self, L.slider_track(kit.prof, self.track_x, self.track_y, self.track_w))
        self.pos = 0.
        self.fill = Ops(self, L.slider_fill(kit.prof, self.track_x, self.track_y, 0))  # under the knob
        self.hit = HitArea(self, 0, 0, self.track_w + self.knob_w, self.h)
        self.hit.OnMouseLeftButtonDown = self._Jump
        self.knob = ui.DragButton()
        self.knob.SetParent(self)
        self.knob.SetUpVisual(Path(kit.rel('knob_normal.png')))
        self.knob.SetOverVisual(Path(kit.rel('knob_hover.png')))
        self.knob.SetDownVisual(Path(kit.rel('knob_pressed.png')))
        self.knob.SetSize(self.knob_w, self.knob_h)
        self.knob_y = (self.h - self.knob_h) // 2
        self.knob.SetRestrictMovementArea(0, self.knob_y, self.track_w + self.knob_w, self.knob_h)
        self.knob.SetPosition(0, self.knob_y)
        self.knob.SetMoveEvent(ui.__mem_func__(self._OnMove))
        self.knob.Show()
        self.callback = event
        self._Fill()
        self.Show()

    def Width(self):
        return self.track_w + self.knob_w

    def Enable(self):
        """Back to a draggable knob over the whole track."""
        self.hit.Enable()
        self.knob.Enable()
        self.knob.SetUpVisual(Path(self.kit.rel('knob_normal.png')))
        self.knob.SetRestrictMovementArea(0, self.knob_y, self.track_w + self.knob_w, self.knob_h)

    def Disable(self):
        """Grey knob locked in place (e.g. a chat option without the new chat)."""
        self.hit.Disable()
        self.knob.Disable()
        self.knob.SetUpVisual(Path(self.kit.rel('knob_disabled.png')))
        x = self.knob.GetLocalPosition()[0]
        self.knob.SetRestrictMovementArea(x, self.knob_y, self.knob_w, self.knob_h)

    def SetEvent(self, callback):
        self.callback = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback
        self.knob.OnMouseWheel = callback
        self.hit.OnMouseWheel = callback

    def SetHoverEvent(self, callback):
        self.hit.SetHoverEvent(callback)

    def _Fill(self):
        self.fill.Apply(L.slider_fill(self.kit.prof, self.track_x, self.track_y, int(round(self.pos * self.track_w))))

    def _OnMove(self):
        x = self.knob.GetLocalPosition()[0]
        self.pos = max(0., min(1., float(x) / max(1, self.track_w)))
        self._Fill()
        if self.callback:
            self.callback()

    def _Jump(self):
        try:
            mx = wndMgr.GetMousePosition()[0] - self.GetGlobalPosition()[0]
        except Exception:
            return True
        self.knob.SetPosition(max(0, min(self.track_w, int(mx - self.knob_w // 2))), self.knob_y)
        self._OnMove()
        return True

    def SetSliderPos(self, pos):
        enabled = getattr(self.knob, 'callbackEnable', True)
        self.knob.TurnOffCallBack()
        try:
            self.pos = max(0., min(1., float(pos)))
            self.knob.SetPosition(int(round(self.pos * self.track_w)), self.knob_y)
        finally:
            if enabled:
                self.knob.TurnOnCallBack()
        self._Fill()

    def GetSliderPos(self):
        return self.pos


def _ReturnFocus(popup):
    """A popup that took the keyboard focus gives it back to its owner window (ESC keeps working there)."""
    owner = getattr(popup, 'owner', None)
    if owner is not None and owner.IsShow():
        owner.SetFocus()


class ListRow(Interactive):
    def __init__(self, popup, w, h):
        Interactive.__init__(self)
        self.popup = popup
        self.value = None
        self.selected = False
        self.SetParent(popup)
        self.SetSize(w, h)
        self.band = Band(self, 0, 0, w, h, 'hover')
        self.band.Hide()
        self.label = Text(self, '', 14, h // 2, popup.kit.font('M'), T.INK_DIM, limit=w - 28)
        self.OnMouseWheel = popup.OnMouseWheel

    def Set(self, value, text, selected):
        self.value, self.selected = value, selected
        self.label.SetText(text)
        self.paint()

    def paint(self):
        self.band.Show() if self.hovered else self.band.Hide()
        self.label.SetPackedFontColor(T.GOLD_HI if self.selected else (T.INK if self.hovered else T.INK_DIM))

    def click(self):
        self.popup.Choose(self.value)


class ListPopup(ui.Window):
    """Floating choice list under an anchor (the dropdown of the settings window). Mouse wheel scrolls."""

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.kit = kit
        self.AddFlag('float')
        self.choices, self.offset, self.current = [], 0, None
        self.callback = None
        self.rows, self.frame = [], None
        self.row_h = kit.p('sub_pitch')
        self.visible = 9

    def Open(self, anchor, choices, current, callback, width):
        self.choices, self.current, self.callback = list(choices), current, callback
        n = min(self.visible, len(self.choices))
        w, h = int(width), n * self.row_h + 12
        self.SetSize(w, h)
        if self.frame:
            self.frame.Apply(L.frame('panel', self.kit.prof, w, h, bg=True))
            self.frame.SetSize(w, h)
        else:
            self.frame = Layer(self, 0, 0, w, h, L.frame('panel', self.kit.prof, w, h, bg=True))
        while len(self.rows) < n:
            self.rows.append(ListRow(self, w - 8, self.row_h))
        for index, row in enumerate(self.rows):
            row.SetSize(w - 8, self.row_h)
            row.SetPosition(4, 6 + index * self.row_h)
            row.Show() if index < n else row.Hide()
        values = [value for value, unused in self.choices]
        index = values.index(current) if current in values else 0
        self.offset = max(0, min(index - n // 2, len(self.choices) - n))
        self._Fill()
        x, y = anchor.GetGlobalPosition()
        y += anchor.GetHeight() + 2
        try:
            if y + h > wndMgr.GetScreenHeight():
                y = anchor.GetGlobalPosition()[1] - h - 2
        except Exception:
            pass
        self.SetPosition(x + anchor.GetWidth() - w, y)
        self.Show()
        self.SetTop()
        self.SetFocus()

    def _Fill(self):
        for index, row in enumerate(self.rows[:min(self.visible, len(self.choices))]):
            value, text = self.choices[self.offset + index]
            row.Set(value, text, value == self.current)

    def OnMouseWheel(self, delta):
        n = min(self.visible, len(self.choices))
        offset = max(0, min(len(self.choices) - n, self.offset + (-1 if delta > 0 else 1)))
        if offset != self.offset:
            self.offset = offset
            self._Fill()
        return True

    def Choose(self, value):
        self.Close()
        if self.callback:
            self.callback(value)

    def Close(self):
        self.KillFocus()
        self.Hide()
        _ReturnFocus(self)

    def OnPressEscapeKey(self):
        self.Close()
        return True


def TitleBarHeight(kit, kind='window'):
    """Height of a kit title bar of this kind under its 5 px inset (the R1 header in the R1 skin)."""
    if SKIN == 'r1':
        return _SkinTokens().BAR_H
    return T.BARS[str(kit.bar(kind))]['height']


class TitleBar(ui.Window):
    """Generic c9 title bar for any window width (>= both end caps, tested 260..1600 px).

    kind 'window' or 'dialog' picks the bar height of the profile (uikittokens.BAR_FOR). The title is a baked
    texture when the kit has one for this text (uikittokens.TITLES, tools/build_althea_ui_kit.py) - the largest
    size that fits - and engine text otherwise (font set B: Cinzel 'Althea Caps' when the EXE knows it, else
    Tahoma bold). The bar itself is not pickable, so dragging it moves a movable parent."""

    def __init__(self, parent, kit, x, y, width, title, kind='window', on_close=None, mode='auto'):
        ui.Window.__init__(self)
        self.kit, self.kind, self.mode = kit, kind, mode
        self.bar = kit.bar(kind)
        # R1 skin: the R1 header (Cinzel title, the vein on row HEAD_H, the plain X) across the whole frame - the bar
        # is placed BAR_INSET px inside the window by every caller, the header starts at the frame edge.
        self.r1 = SKIN == 'r1'
        self.inset = _SkinTokens().BAR_INSET if self.r1 else 0
        self.r1_width = int(width) + 2 * self.inset
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.SetPosition(int(x) - self.inset, int(y) - self.inset)
        self.ops = Ops(self)
        self.title_image = None
        self.title_text = None
        self.close = None
        self.has_close = on_close is not None
        self.title = ''
        self.SetTitle(title, width)
        if on_close:  # created after the bar images, so it is drawn and picked above them
            cx, cy, cw, ch = self.layout['close']
            if self.r1:
                import uir1tokens as R1T
                self.close = ImageButton(self, R1_ROOT + 'close/x_%s.png', cx, cy, cw, ch, on_close,
                                         inset=(cw - R1T.X_SIZE) // 2)
            else:
                self.close = ImageButton(self, 'bar/%d/close_%%s.png' % self.bar, cx, cy, cw, ch, on_close)
        self.Show()

    def Height(self):
        """Height under the bar's own top (callers place the content at 5 + Height())."""
        if self.r1:
            return _SkinTokens().BAR_H
        return T.BARS[str(self.bar)]['height']

    def _TitleSize(self, width):
        text = Upper(self.title)
        path, size = (None, (0, 0))
        if self.mode != 'text':
            path, size = L.pick_title(text, self.bar, width, self.has_close)
        if path:
            return path, size
        probe = ui.TextLine()           # measured off the bar: the drawn title is made after the bar images
        probe.SetFontName(self._TitleFont())
        probe.SetText(text)
        return None, (TextWidth(probe), FontCell(self._TitleFont()))

    def _TitleFont(self):
        fonts = T.FONT_SETS[self.kit.prof][self.kit.font_set]
        if self.r1 and 'title' in fonts:
            return fonts['title']
        if self.kit.font_set == 'B':
            return T.BARS[str(self.bar)]['title_font']
        return 'Tahoma:%db' % {52: 18, 40: 15, 32: 13}.get(self.bar, 15)

    def _SetTitleR1(self, width):
        """The R1 header (uir1layout.header): the title centred (left of the X when it would touch it), the vein 6 px
        from both frame sides on row HEAD_H, the X with its 20 px hit box. No baked title texture."""
        import uir1layout as RL
        import uir1tokens as R1T
        text = Upper(self.title)
        font = self._TitleFont()
        probe = ui.TextLine()
        probe.SetFontName(font)
        probe.SetText(text)
        tw, th = TextWidth(probe), FontCell(font)
        lay = RL.header(width, tw, self.has_close)
        self.SetSize(width, R1T.HEAD_H)
        fresh = self._ApplyBar([(kind, R1_ROOT + path, ox, oy, ow, oh) for kind, path, ox, oy, ow, oh in lay['vein']])
        if self.title_text is None or fresh:
            if self.title_text is not None:
                self.title_text.Hide()
            self.title_text = Text(self, '', 0, 0, font, T.GOLD_HI)
        tx, ty = lay['title']
        self.title_text.SetText(text)
        self.title_text.SetPosition(tx, ty)
        self.title_text.Show()
        if self.close:
            cx, cy, unused_cw, unused_ch = lay['close']
            self.close.SetPosition(cx, cy)
        self.layout = dict(ops=lay['vein'], width=width, height=R1T.HEAD_H, title=(tx, ty - th // 2, tw, th),
                           close=lay['close'], flourish=0, fits=tx >= 10)
        return self.layout

    def SetTitle(self, title, width=None):
        self.title = title or ''
        if self.r1:
            return self._SetTitleR1(self.r1_width)
        width = int(width or self.GetWidth())
        path, size = self._TitleSize(width)
        layout = L.titlebar(width, self.bar, size, self.has_close)
        self.SetSize(layout['width'], layout['height'])
        fresh = self._ApplyBar(layout['ops'])
        tx, ty, tw, th = layout['title']
        if path:
            if self.title_image is None or fresh:
                if self.title_image is not None:
                    self.title_image.Hide()
                self.title_image = ui.ImageBox()
                self.title_image.SetParent(self)
                self.title_image.AddFlag('not_pick')
            self.title_image.LoadImage(Path(path))
            self.title_image.SetPosition(tx, ty)
            self.title_image.Show()
            if self.title_text:
                self.title_text.Hide()
        else:
            if self.title_image:
                self.title_image.Hide()
            if self.title_text is None or fresh:
                if self.title_text is not None:
                    self.title_text.Hide()
                self.title_text = Text(self, '', 0, 0, self._TitleFont(), T.GOLD_HI, valign='top', outline=True)
            self.title_text.SetText(Upper(self.title))
            self.title_text.SetPosition(tx, ty)
            self.title_text.Show()
        if self.close:
            cx, cy, cw, ch = layout['close']
            self.close.SetPosition(cx, cy)
        self.layout = layout
        return layout

    def _ApplyBar(self, ops):
        """Applies the bar images; True when a NEW image window was made. The engine draws the children in the order
        they were added and a SetParent to the same parent does not move a window (CWindowManager::SetParent), so a
        title made before such an image would lie under it - the caller makes the title again."""
        before = set(id(widget) for unused, widget in self.ops.items)
        self.ops.Apply(ops)
        return any(id(widget) not in before for unused, widget in self.ops.items)


class Confirm(ui.Window):
    """Small c9 dialog: dialog title bar, wrapped message, optional bullet list and note, accept (ruby) and cancel
    buttons. ESC cancels. wide=True for a dialog that lists what an action changes."""

    def __init__(self, kit, title, accept_text, cancel_text, wide=False):
        ui.Window.__init__(self)
        import uiconfirm
        uiconfirm.Bind(self, 'accept')
        self.kit = kit
        self.AddFlag('float')
        self.AddFlag('movable')
        w = (420 if kit.prof == '1080' else 360) if not wide else (600 if kit.prof == '1080' else 480)
        self.w = w
        self.on_accept = self.on_cancel = None
        self.accept_text = accept_text
        self.frame = Frame(self, kit, 'window', 0, 0, w, 200, bg=True)
        self.bar = TitleBar(self, kit, 5, 5, w - 10, title, kind='dialog', on_close=self.Cancel)
        self.lines = []
        bw = 150 if kit.prof == '1080' else 128
        self.accept = Button(self, kit, 0, 0, bw, accept_text, role='primary', event=self.Accept, size='bar')
        self.cancel = Button(self, kit, 0, 0, bw, cancel_text, role='secondary', event=self.Cancel, size='bar')

    def Open(self, text, on_accept, on_cancel=None, bullets=(), note='', accept_text=None):
        self.on_accept, self.on_cancel = on_accept, on_cancel
        self.accept.SetText(accept_text or self.accept_text)
        self.accept.FitWidth(150 if self.kit.prof == '1080' else 128)
        for line in self.lines:
            line.Hide()
        top = 5 + self.bar.Height() + 18
        lh = self.kit.cell('M') + 6
        self.lines, y = Wrap(self, text, 24, top, self.w - 48, self.kit.font('M'), T.INK, lh)
        if bullets:
            y += 6
            bw, bh = self.kit.size('bullet/diamond_normal.png')
            for bullet in bullets:
                self.lines.append(Image(self, self.kit.rel('bullet/diamond_normal.png'), 30,
                                        y + (self.kit.cell('M') - bh) // 2 + 1))
                more, y = Wrap(self, bullet, 30 + bw + 10, y, self.w - 54 - bw - 10, self.kit.font('M'), T.INK_DIM, lh)
                self.lines.extend(more)
        if note:
            more, y = Wrap(self, note, 24, y + 8, self.w - 48, self.kit.font('S'), T.MUTED, self.kit.cell('S') + 4)
            self.lines.extend(more)
        y += 14
        bh = max(self.accept.h, self.cancel.h)
        gap = 14
        total = self.accept.w + self.cancel.w + gap
        x = (self.w - total) // 2
        self.accept.SetPosition(x, y + (bh - self.accept.h) // 2)
        self.cancel.SetPosition(x + self.accept.w + gap, y + (bh - self.cancel.h) // 2)
        h = y + bh + 18
        self.SetSize(self.w, h)
        self.frame.SetSize(self.w, h)
        self.frame.Apply(L.frame('window', self.kit.prof, self.w, h, bg=True))
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Accept(self):
        self.Close()
        if self.on_accept:
            self.on_accept()

    def Cancel(self):
        self.Close()
        if self.on_cancel:
            self.on_cancel()

    def Close(self):
        self.KillFocus()
        self.Hide()
        _ReturnFocus(self)

    def OnPressEscapeKey(self):
        self.Cancel()
        return True


class OptionRow(Interactive):
    def __init__(self, owner, index, text, w, h):
        Interactive.__init__(self)
        self.owner, self.index = owner, index
        self.selected = False
        self.SetParent(owner)
        self.SetSize(w, h)
        kit = owner.kit
        self.band = Band(self, 0, 0, w, h, 'hover')
        self.band.Hide()
        bw, bh = kit.size('bullet/diamond_normal.png')
        self.bullet = Image(self, kit.rel('bullet/diamond_normal.png'), 6, (h - bh) // 2)
        self.label = Text(self, text, 6 + bw + 10, h // 2, owner.font, T.INK_DIM, limit=w - bw - 22)
        self.Show()

    def paint(self):
        self.band.Show() if self.hovered and not self.selected else self.band.Hide()
        self.bullet.LoadImage(Path(self.owner.kit.rel('bullet/diamond_%s.png' % ('selected' if self.selected else 'normal'))))
        self.label.SetPackedFontColor(T.GOLD_HI if self.selected else (T.DISABLED if not self.enabled else
                                                                       (T.INK if self.hovered else T.INK_DIM)))

    def click(self):
        self.owner.Select(self.index)

    def OnMouseOverIn(self):
        Interactive.OnMouseOverIn(self)
        if self.owner.on_hover:
            self.owner.on_hover()


class OptionList(ui.Window):
    """Vertical one-of-N list (diamond bullet + label) for choices too long for a segment."""

    def __init__(self, parent, kit, options, w, event=None, font=None):
        ui.Window.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.font = font or kit.font('M')
        self.values = [value for value, unused in options]
        self.callback = event
        self.on_hover = None
        h = kit.p('sub_pitch')
        self.rows = []
        for index, (value, text) in enumerate(options):
            row = OptionRow(self, index, text, int(w), h)
            row.SetPosition(0, index * h)
            row.paint()
            self.rows.append(row)
        self.SetSize(int(w), h * len(self.rows))
        self.Show()

    def Height(self):
        return self.GetHeight()

    def SetHoverEvent(self, callback):
        self.on_hover = callback

    def SetWheelEvent(self, callback):
        self.OnMouseWheel = callback
        for row in self.rows:
            row.OnMouseWheel = callback

    def SetValue(self, value):
        for row, v in zip(self.rows, self.values):
            selected = v == value
            if selected != row.selected:
                row.selected = selected
                row.paint()

    def Select(self, index):
        if self.callback:
            self.callback(self.values[index])

    def Enable(self):
        for row in self.rows:
            row.Enable()

    def Disable(self):
        for row in self.rows:
            row.Disable()


# --------------------------------------------------------------------------- settings v5 components
class ScrollThumb(ui.DragButton):
    """Brass thumb of ScrollBar: vertical 3-slice and a grip, hover from the native mouse callbacks."""

    def __init__(self, kit, inset):
        ui.DragButton.__init__(self)
        self.AddFlag('movable')
        self.kit, self.inset = kit, inset
        self.state = 'normal'
        # Plate images before the grip (creation order = draw order; the same trap as the track above).
        self.ops = Ops(self, L.vscroll(kit.prof, 'thumb', 'normal', inset, 0, kit.p('scroll_min')))
        self.grip = Image(self, kit.rel('scroll/grip_normal.png'), inset, 0)
        self.h = 0

    def SetHeight(self, h):
        self.h = int(h)
        ui.DragButton.SetSize(self, self.kit.p('scroll_w') + 2 * self.inset, self.h)
        self.paint()

    def paint(self):
        self.ops.Apply(L.vscroll(self.kit.prof, 'thumb', self.state, self.inset, 0, self.h))
        grip = self.kit.rel('scroll/grip_%s.png' % ('hover' if self.state == 'hover' else 'normal'))
        gh = L.size(grip)[1]
        self.grip.LoadImage(Path(grip))
        self.grip.SetPosition(self.inset, (self.h - gh) // 2)
        self.grip.Show() if self.h >= gh + 2 * L.size(self.kit.rel('scroll/thumb_t_normal.png'))[1] else self.grip.Hide()

    def OnMouseOverIn(self):
        self.state = 'hover'
        self.paint()

    def OnMouseOverOut(self):
        self.state = 'normal'
        self.paint()


# A pressed drag button reports OnMove from C++ for every SetPosition (CDragButton::OnChangePosition): a scroll
# handler that lays the bar out again (SetPos(..., False), SetScrollBarSize, a crimson SetScale) while the thumb is
# dragged re-entered itself until the client's stack overflowed (DEV ui.DispatchScrollEvent, report D-20261005-3VJE8R).
# The kit / R1 bars run their handler the same way: never nested; a move made during the handler only updates
# curPos and, when the position ended up different, the handler runs again afterwards (bounded).
SCROLL_EVENT_MAX_PASSES = 3


def DispatchScroll(bar, call):
    if getattr(bar, 'scrollEventActive', False):
        bar.scrollEventPending = True
        return
    bar.scrollEventActive = True
    try:
        for unused in range(SCROLL_EVENT_MAX_PASSES):
            bar.scrollEventPending = False
            position = bar.curPos
            call()
            if not bar.scrollEventPending or bar.curPos == position:
                break
    finally:
        bar.scrollEventActive = False
        bar.scrollEventPending = False


class ScrollBar(ui.Window):
    """Settings v5 scrollbar: a recessed track over the whole content height and a brass thumb with a grip, wider
    than the v4 bar (14 / 12 px, the pick area 4 px more on each side). Same API as uicrimsonember.SettingsScrollBar
    (SetScrollBarSize, SetMiddleBarSize, SetScrollStep, SetPos / GetPos, OnUp / OnDown, SetScrollEvent), so it is a
    drop-in; a click into the track jumps there. The window it is placed in scrolls it with the mouse wheel, one step
    per notch (uiwheel; an owner that also forwards the wheel keeps working)."""
    INSET = 4

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.kit = kit
        self.w = kit.p('scroll_w') + 2 * self.INSET
        self.pageSize = 1
        self.curPos = 0.0
        self.scrollStep = 0.4
        self.eventScroll = None
        self.lockFlag = False
        # Track images FIRST: children draw in creation order, and a track created after the thumb (it used to get
        # its images only in SetScrollBarSize) covered the thumb - in game the bar was a "column" without a thumb
        # (owner play test 2026-10-05). Later Apply() calls re-use these images, so the order stays.
        self.track = Ops(self, L.vscroll(kit.prof, 'track', 'normal', self.INSET, 0, kit.p('scroll_min') * 2))
        self.middleBar = ScrollThumb(kit, self.INSET)
        self.middleBar.SetParent(self)
        self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
        self.middleBar.SetHeight(kit.p('scroll_min'))
        self.middleBar.Show()
        self.SetScrollBarSize(kit.p('scroll_min') * 2)

    def Width(self):
        return self.w

    def SetParent(self, parent):
        ui.Window.SetParent(self, parent)
        uiwheel.Follow(self, parent)

    def SetScrollEvent(self, event):
        self.eventScroll = event

    def SetScrollBarSize(self, height):
        height = max(int(height), self.kit.p('scroll_min'))
        self.SetSize(self.w, height)
        self.track.Apply(L.vscroll(self.kit.prof, 'track', 'normal', self.INSET, 0, height))
        self.pageSize = max(0, height - self.middleBar.h)
        self.middleBar.SetRestrictMovementArea(0, 0, self.w, height)
        self.middleBar.SetPosition(0, 0)
        self.curPos = 0.0

    def SetMiddleBarSize(self, pageScale):
        height = self.GetHeight()
        self.middleBar.SetHeight(max(self.kit.p('scroll_min'), min(height, int(float(pageScale) * height))))
        self.pageSize = max(0, height - self.middleBar.h)
        self.middleBar.SetRestrictMovementArea(0, 0, self.w, height)

    def SetScrollStep(self, step):
        self.scrollStep = step

    def GetScrollStep(self):
        return self.scrollStep

    def GetPos(self):
        return self.curPos

    def SetPos(self, pos, moveEvent=True):
        pos = max(0.0, min(1.0, float(pos)))
        self.middleBar.SetPosition(0, int(round(self.pageSize * pos)))
        self.curPos = pos
        if moveEvent:
            self.OnMove()

    def OnUp(self):
        self.SetPos(self.curPos - self.scrollStep)

    def OnDown(self):
        self.SetPos(self.curPos + self.scrollStep)

    def OnMove(self):
        if self.lockFlag or not self.pageSize:
            return
        self.curPos = max(0.0, min(1.0, float(self.middleBar.GetLocalPosition()[1]) / self.pageSize))
        if self.eventScroll:
            DispatchScroll(self, self.eventScroll)

    def OnMouseLeftButtonDown(self):
        try:
            y = wndMgr.GetMousePosition()[1] - self.GetGlobalPosition()[1]
        except Exception:
            return True
        if self.pageSize:
            self.SetPos(float(y - self.middleBar.h // 2) / self.pageSize)
        return True

    def Destroy(self):
        self.eventScroll = None


# Key cap style of the key bindings page (2026-10-06: K4 chosen, K1-K3 liked too): 'k1' flat, 'k2' light key,
# 'k3' muted outline, 'k4' dark cap with a soft shadow (design v5 section 2), or 'v5' = the old variable-width cap.
# One constant for the whole client; every style has its textures in the kit (tools/build_althea_ui_kit.py).
KEYCAP_STYLE = 'k4'
def KeycapColors():
    """Label colour per key cap style and state (design mock.css .k1-.k4), from the tokens of the skin in use."""
    return {
        'k1': dict(normal=T.INK, hover=T.GOLD_HI, active=0xFFFFFFFF, empty=T.DISABLED, disabled=T.DISABLED),
        'k2': dict(normal=0xFF20160F, hover=0xFF20160F, active=0xFFFFFFFF, empty=T.DISABLED, disabled=0xFF3A3532),
        'k3': dict(normal=T.INK, hover=T.GOLD_HI, active=T.RUBY_HI, empty=T.DISABLED, disabled=T.DISABLED),
        'k4': dict(normal=T.INK, hover=T.GOLD_HI, active=0xFFFFFFFF, empty=T.DISABLED, disabled=T.DISABLED),
        'v5': dict(normal=T.BUTTON_TEXT, hover=T.GOLD_HI, active=T.GOLD_HI, empty=T.MUTED, disabled=T.DISABLED),
    }


KEYCAP_COLORS = KeycapColors()   # the gold kit's table (kept for callers); paint() asks KeycapColors()


class KeyCap(Interactive):
    """Key cap of the key bindings page, the key text by the engine. Styles K1-K4: a FIXED width (keycap_w, wider only
    for a text that does not fit) so the caps stand in one column at the right edge (align='right' keeps the right
    edge); an unbound action shows "–" and a muted "nepřiřazeno" left of the cap, a capturing cap is ruby with the
    hint beside it. Style 'v5' = the old cap (width by the text, "Nepřiřazeno" inside). States normal / hover /
    active (capturing) / empty (unbound) / disabled."""

    def __init__(self, parent, kit, x, y, text='', min_w=None, event=None, align='right', style=None):
        Interactive.__init__(self)
        self.kit = kit
        self.style = style or KEYCAP_STYLE
        self.SetParent(parent)
        self.right = int(x)
        self.top = int(y)
        self.align = align
        v5 = self.style == 'v5'
        self.min_w = min_w or (kit.p('keycap_w') if not v5 else (56 if kit.prof == '1080' else 46))
        self.h = L.size(kit.rel('keycap/l_normal.png'))[1] if v5 else kit.p('keycap6_h')
        self.lip = (4 if kit.prof == '1080' else 3) if v5 else 0
        self.empty = self.active = False
        self.text = ''
        self.ops = Ops(self, self._Ops('normal', self.min_w))
        cy = (self.h - self.lip) // 2 + (1 if v5 else 0)
        self.label = Text(self, '', 0, cy, kit.font('Sb'), T.BUTTON_TEXT, align='center')
        # The note left of the cap ("nepřiřazeno" / the capture hint): a not-pickable child drawn outside the cap.
        self.note = Text(self, '', -12, self.h // 2, kit.font('S'), T.MUTED, align='right')
        self.note.Hide()
        self.hint = ''
        self.callback = event
        self.w = self.min_w
        self.SetText(text)
        self.Show()

    def _Ops(self, state, w):
        if self.style == 'v5':
            return L.keycap(self.kit.prof, state, w)
        return L.keycap6(self.kit.prof, self.style, state, w)

    def Width(self):
        return self.w

    def SetHint(self, hint):
        """Text beside a capturing cap (e.g. "stiskni novou klávesu · Esc zruší")."""
        self.hint = hint or ''
        self.paint()

    def SetText(self, text, empty=False):
        self.empty = bool(empty)
        self.text = text
        shown = '-' if self.empty and self.style != 'v5' else text
        self.label.SetText(shown)
        pad = (28 if self.kit.prof == '1080' else 22) if self.style == 'v5' else (16 if self.kit.prof == '1080' else 12)
        self.w = max(self.min_w, TextWidth(self.label) + pad)
        x = self.right - self.w if self.align == 'right' else self.right
        self.SetPosition(x, self.top)
        self.SetSize(self.w, self.h)
        self.paint()

    def GetText(self):
        return self.text

    def SetActive(self, active):
        self.active = bool(active)
        self.paint()

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.active or self.pressed:
            return 'active'
        if self.hovered:
            return 'hover'
        return 'empty' if self.empty else 'normal'

    def paint(self):
        st = self.state()
        self.ops.Apply(self._Ops(st, self.w))
        v5 = self.style == 'v5'
        if not v5:
            font = self.kit.font('S' if self.empty and st != 'active' else 'Sb')
            text = '...' if st == 'active' else ('-' if self.empty else self.text)
            if getattr(self, '_font', None) != font:
                self._font = font
                SetFont(self.label, font, text)      # never a font swap under unchanged text (stale glyphs)
            else:
                self.label.SetText(text)
        self.label.SetPosition(self.w // 2, (self.h - self.lip) // 2 + (1 if v5 else 0) +
                               (1 if st == 'active' and v5 else 0) - (0 if v5 else self._Nudge()))
        colors = KeycapColors()
        self.label.SetPackedFontColor(colors.get(self.style, colors['k4'])[st])
        note = ''
        if not v5:
            if st == 'active':
                note = self.hint
            elif self.empty and st != 'disabled':
                note = Tr_('nepřiřazeno', 'unbound')
        if note:
            self.note.SetText(note)
            self.note.SetPackedFontColor(T.MUTED if st == 'active' else T.DISABLED)
            self.note.Show()
        else:
            self.note.Hide()

    def _Nudge(self):
        return 1 if self.kit.font_set == 'B' else 0


class Chip(Interactive):
    """On/off chip of the v6 family (2026-10-06): a single segment cell - the same frame as the buttons and
    segments, ruby with the brass inner line while on (= a selected segment cell), dark while off - with the state
    diamond and a label. Width() is known after construction (text + padding), so the caller lays chips out."""

    def __init__(self, parent, kit, x, y, text, on=False, event=None, font=None):
        Interactive.__init__(self)
        self.kit = kit
        self.on = bool(on)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.h = L.button6_height(kit.prof, 'c')
        self.ops = Ops(self, L.button6(kit.prof, 'chip_on' if self.on else 'chip_off', 'c', 'single', 'normal', 64))
        bw, bh = kit.size('bullet/diamond_normal.png')
        pad = 12 if kit.prof == '1080' else 9
        self.bullet = Image(self, kit.rel('bullet/diamond_normal.png'), pad, (self.h - bh) // 2)
        self.label = Text(self, text, pad + bw + 8, self.h // 2, kit.font('M'), T.INK_DIM)
        self.w = pad + bw + 8 + TextWidth(self.label) + pad + 2
        self.SetSize(self.w, self.h)
        self.callback = event
        self.paint()
        self.Show()

    def Width(self):
        return self.w

    def SetOn(self, on):
        on = bool(on)
        if on != self.on:
            self.on = on
            self.paint()

    def paint(self):
        st = self.state()
        self.ops.Apply(L.button6(self.kit.prof, 'chip_on' if self.on else 'chip_off', 'c', 'single', st, self.w))
        self.bullet.LoadImage(Path(self.kit.rel('bullet/diamond_%s.png' % ('selected' if self.on else 'normal'))))
        self.label.SetPackedFontColor(T.DISABLED if st == 'disabled' else
                                      (T.GOLD_HI if self.on else (T.INK if st == 'hover' else T.INK_DIM)))


class CheckBox(Interactive):
    """Check box of the v6 family (table O1, context menu): 16 / 14 px box, optional label right of it; the whole
    box + label is the hit area. SetOn() / Enable() / Disable() like a Toggle."""

    def __init__(self, parent, kit, x, y, text='', on=False, event=None, font=None, color=None):
        Interactive.__init__(self)
        self.kit = kit
        self.on = bool(on)
        self.color = T.INK if color is None else color
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        s = kit.p('check')
        self.box_size = s
        self.box = ui.ImageBox()
        self.box.SetParent(self)
        self.box.AddFlag('not_pick')
        self.box.Show()
        self.label = None
        w, h = s, s
        if text:
            cell = FontCell(font or kit.font('M'))
            h = max(s, cell)
            self.label = Text(self, text, s + 8, h // 2, font or kit.font('M'), self.color)
            w = s + 8 + TextWidth(self.label)
        self.box.SetPosition(0, (h - s) // 2)
        self.w, self.h = w, h
        self.SetSize(w, h)
        self.callback = event
        self.paint()
        self.Show()

    def Width(self):
        return self.w

    def SetOn(self, on):
        on = bool(on)
        if on != self.on:
            self.on = on
            self.paint()

    def paint(self):
        st = {'pressed': 'hover'}.get(self.state(), self.state())
        self.box.LoadImage(Path(L.check(self.kit.prof, self.on, st)))
        if self.label is not None:
            self.label.SetPackedFontColor(T.DISABLED if st == 'disabled' else
                                          (T.GOLD_HI if st == 'hover' else self.color))


class EditField(Interactive):
    """Edit field: recessed 3-slice well and a native ui.EditLine inside (self.edit); the rim turns brass while the
    line has the keyboard focus. A click anywhere in the well focuses the line. The placeholder (SetHint) is drawn
    in the field's own font and colour where the typed text starts - the engine's EditLine draws it in its small
    default font at the top (2026-10-06: "drobný, není svisle vystředěný")."""

    def __init__(self, parent, kit, x, y, w, font=None, max_len=40, number=False, hint='', edit=None, lead=0,
                 trail=0):
        Interactive.__init__(self)
        self.kit = kit
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.w = int(w)
        self.h = L.size(kit.rel('field/l_normal.png'))[1]
        self.SetSize(self.w, self.h)
        self.ops = Ops(self, L.field(kit.prof, 'normal', self.w))
        font = font or kit.font('M')
        self.font = font
        self.pad = 10 if kit.prof == '1080' else 8
        self.edit = edit if edit is not None else ui.EditLine()  # lead / trail = room for icons left / right
        self.edit.SetParent(self)
        self.edit.SetPosition(self.pad + lead, (self.h - FontCell(font)) // 2 - self.TextNudge())
        self.edit.SetSize(self.w - 2 * self.pad - lead - trail, FontCell(font) + 2)
        self.edit.SetMax(max_len)
        self.edit.SetFontName(font)
        if number:
            self.edit.SetNumberMode()
        if hint:
            self.SetHint(hint)
        self.edit.Show()
        self.callback = self.Focus
        self.focused = False
        self.paint()
        self.Show()

    def TextNudge(self):
        """Pixels the text moves up inside the well. 0: measured in the game (owner screenshot 195, 6. 10.) the old
        2 px lift put the Spectral cap/x-height block ~2.5 px above the well centre; with no lift it is centred."""
        return 0

    def SetHint(self, text):
        self.edit.SetInfoMessage(text)
        self._StyleHint()

    def _StyleHint(self):
        """The EditLine's placeholder (ui.EditLine.SetInfoMessage: a child TextLine laid out in the DEFAULT font)
        in the field font: emptied, font swapped, text set again - a bare SetFontName would draw the default-font
        layout from the Spectral atlas (garbage letters in the game, screenshots 189 / 191)."""
        back = getattr(self.edit, 'backText', None)
        message = getattr(self.edit, 'infoMsg', '') or ''
        if back is None or getattr(back, '_kit_hint', None) == (self.font, message):
            return
        SetFont(back, self.font, message)
        back.SetPackedFontColor(T.MUTED)
        back._kit_hint = (self.font, message)

    def Focus(self):
        self.edit.SetFocus()
        self.SetFocused(True)

    def SetFocused(self, focused):
        if bool(focused) != self.focused:
            self.focused = bool(focused)
            self.paint()

    def state(self):
        if not self.enabled:
            return 'disabled'
        if self.focused:
            return 'focus'
        return 'hover' if self.hovered else 'normal'

    def paint(self):
        self.ops.Apply(L.field(self.kit.prof, self.state(), self.w))

    def OnUpdate(self):
        self._StyleHint()          # a caller may set the placeholder on the line itself (SetInfoMessage)
        try:
            focused = bool(self.edit.IsFocus())
        except Exception:
            return
        if focused != self.focused:
            self.SetFocused(focused)


class SearchField(EditField):
    """The one search field of the kit (settings sidebar, Panely catalogue, the stone queue editor; owner
    2026-10-06): search icon, text and placeholder in the row-label font centred in the well, and a small plain
    clear cross only while there is something to clear. on_clear() runs after the text was emptied."""

    def __init__(self, parent, kit, x, y, w, hint='', edit=None, max_len=40, on_clear=None):
        isz = kit.p('icon_side')
        cs = L.size(kit.rel('field/clear_normal.png'))[0]
        EditField.__init__(self, parent, kit, x, y, w, font=kit.font('M'), max_len=max_len, hint=hint, edit=edit,
                           lead=isz + 8, trail=cs + 10)
        self.icon = Icon(self, 'search', isz, self.pad - 2, (self.h - isz) // 2)
        self.on_clear = on_clear
        self.clear = ImageButton(self, kit.rel('field/clear_%s.png'), self.w - self.pad - cs + 2, (self.h - cs) // 2,
                                 cs, cs, self.Clear)
        self.clear.Hide()

    def Clear(self):
        self.edit.SetText('')
        self.clear.Hide()
        if self.on_clear:
            self.on_clear()

    def SyncClear(self):
        has_text = bool(self.edit.GetText())
        if has_text != bool(self.clear.IsShow()):
            self.clear.Show() if has_text else self.clear.Hide()

    def OnUpdate(self):
        EditField.OnUpdate(self)
        self.SyncClear()


class Section(ui.Window):
    """Section heading of the v5 pages: semibold small text in muted gold and a thin bronze rule after it that
    fades out (the same on every page; no ribbons, no ornaments). Not pickable."""

    def __init__(self, parent, kit, x, y, w, text):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit = kit
        cell = kit.cell('Sb')
        self.h = cell + 6
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), self.h)
        self.label = Text(self, text, 0, self.h // 2, kit.font('Sb'), T.GOLD, valign='center')
        rx = TextWidth(self.label) + 12
        rh = L.size(kit.rel('section/rule_m.png'))[1]
        self.rule = Ops(self, L.section_rule(kit.prof, rx, self.h // 2 - rh // 2, int(w) - rx))
        self.Show()

    def Height(self):
        return self.h


# --------------------------------------------------------------------------- settings v5 fix: popups
def Separator(parent, x, y, w, alpha=0.9):
    """A fine 1 px divider between the items of a popup (context menu, list): visible without a hover band."""
    return HLine(parent, x, y, w, T.LINE, alpha)


class PopupFrame(object):
    """Frame of a floating popup (context menu, tooltip): a soft drop shadow and a crisp dark outline, the kit panel
    frame and one shade lighter fill, so the popup reads as one object above the dark window behind it (owner play
    test 2026-10-05: the menu edge was hard to see). Create it FIRST in the popup - children draw in creation
    order. Apply(w, h) resizes; the shadow lies outside the popup rect and is never pickable."""
    SHADOW = ((2, .30), (3, .22), (4, .14), (5, .08))

    def __init__(self, parent, kit):
        self.parent, self.kit = parent, kit
        self.shadow = [Rect(parent, 0, 0, 1, 1, 0x000000, alpha) for unused, alpha in self.SHADOW]
        self.outline = [Rect(parent, 0, 0, 1, 1, 0x000000, .75) for unused in range(4)]
        self.bg = Layer(parent, 0, 0, 1, 1, [])
        self.tint = Rect(parent, 0, 0, 1, 1, T.PANEL_HI, .7)
        self.edges = Layer(parent, 0, 0, 1, 1, [])
        self.w = self.h = 0

    def Apply(self, w, h):
        w, h = int(w), int(h)
        self.w, self.h = w, h
        for bar, (offset, unused) in zip(self.shadow, self.SHADOW):
            bar.SetPosition(offset, offset)
            bar.SetSize(w, h)
        for bar, (bx, by, bw, bh) in zip(self.outline, ((-1, -1, w + 2, 1), (-1, h, w + 2, 1), (-1, 0, 1, h),
                                                        (w, 0, 1, h))):
            bar.SetPosition(bx, by)
            bar.SetSize(bw, bh)
        ops = L.frame('panel', self.kit.prof, w, h, bg=True)
        self.bg.SetSize(w, h)
        self.bg.Apply(ops[:1])
        inset = 3
        self.tint.SetPosition(inset, inset)
        self.tint.SetSize(max(1, w - 2 * inset), max(1, h - 2 * inset))
        self.edges.SetSize(w, h)
        self.edges.Apply(ops[1:])

    def Widgets(self):
        return self.shadow + self.outline + [self.bg, self.tint, self.edges]


class Tooltip(ui.Window):
    """Kit hover tooltip (settings v5 fix 2026-10-05, replaces the description strip under the content): popup frame,
    gold title, the description wrapped to a readable width and an optional muted note. Floating and never
    pickable, so it never steals the hover of what it describes. ShowAt(rect) places it under the anchor rect
    (global x, y, w, h) - above it when the screen has no room below, or side='above' - clamped to the screen."""

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.kit = kit
        self.AddFlag('float')
        self.AddFlag('not_pick')
        self.frame = PopupFrame(self, kit)
        self.lines = []
        self.key = None

    def MaxWidth(self):
        return 440 if self.kit.prof == '1080' else 340

    def ShowAt(self, rect, title, body='', note='', max_w=None, side='below'):
        key = (tuple(int(v) for v in rect), title, body, note, side)
        if key == self.key and self.IsShow():
            return
        self.key = key
        if self._R1Hint(rect, title, body, note):
            return
        for line in self.lines:
            line.Hide()
        self.lines = []
        k = self.kit
        pad = 12 if k.prof == '1080' else 9
        max_w = int(max_w or self.MaxWidth())
        y, w = pad - 2, 0
        if title:
            line = Text(self, title, pad, y, k.font('Sb'), T.GOLD_HI, valign='top')
            self.lines.append(line)
            w = TextWidth(line)
            y += k.cell('Sb') + 4
        if body:
            wrapped, y = Wrap(self, body, pad, y, max_w, k.font('S'), T.INK_DIM, k.cell('S') + 3)
            self.lines.extend(wrapped)
            w = max([w] + [TextWidth(line) for line in wrapped])
        if note:
            line = Text(self, note, pad, y + 2, k.font('S'), T.MUTED, valign='top')
            self.lines.append(line)
            w = max(w, TextWidth(line))
            y += k.cell('S') + 5
        width, height = w + 2 * pad, y + pad - 2
        self.SetSize(width, height)
        self.frame.Apply(width, height)
        x, ry, unused, rh = rect
        gap = 4
        try:
            sw, sh = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        except Exception:
            sw, sh = 1920, 1080
        above, below = ry - height - gap, ry + rh + gap
        top = above if side == 'above' and above >= 0 else below
        if top + height > sh:
            top = above
        self.SetPosition(max(0, min(int(x), sw - width)), max(0, int(top)))
        self.Show()
        self.SetTop()

    def _R1Hint(self, rect, title, body, note):
        """In the R1 look the one R1 hint shows the tooltip (every hover box has one style, the ESC
        menu and the settings too): the title above the vein, the description and the note under it."""
        try:
            import uir1
            if not uir1.UseR1():
                return False
            import uir1tokens
            lines = []
            if body:
                lines.append((body, uir1tokens.INK_DIM))
            if note:
                lines.append((note, uir1tokens.MUTED))
            uir1.ShowHintAt(rect, title, lines, owner=self)
        except Exception:
            return False
        ui.Window.Hide(self)
        return True

    def IsShow(self):
        if ui.Window.IsShow(self):
            return True
        try:
            import uir1
            return uir1.HintShownFor(self)
        except Exception:
            return False

    def Hide(self):
        self.key = None
        try:
            import uir1
            uir1.HideHint(self)
        except Exception:
            pass
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.lines = []
