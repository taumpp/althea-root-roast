# -*- coding: utf-8 -*-
"""Settings (R1 look): the colour of the damage numbers in an R1 dialog (9. 10. 2026).

Opened by the "Barva normálních / kritických zásahů" rows of Rozhraní › Jména a ukazatele (uisettingsc9rows). It
replaces the old uicolorpicker.ColorPickerDialog (dark red board, old title bar and buttons, an empty strip above the
gradient) in the R1 settings; "Starý vzhled" keeps the old dialog. Dialog standard C with a header:

  header        the R1 window header (Cinzel title in upper case, the red vein, the plain X) like POSTAVA
  gradient      the original picker texture (ui/skillcolor/color_picker_background.tga, 225 x 225) cropped to its
                colour area (rows 31-191) with SetRenderingRect, at its native size: no empty strip. The colour is
                read from the screen under the mouse (wndMgr.GetColorAtPosition), as the old picker did: hue left to
                right, light (top) to dark (bottom); any other colour through the hex field.
  hex row       swatch, the hex field (#RRGGBB, Enter = Použít, Esc = Zrušit) and "Výchozí" (sets the default colour)
  preview       a damage number in the chosen colour with the current font, outline, size and thousands grouping
                (uidamagesettings.refresh, the same code as "Náhled zásahů" of the old page); hovering the gradient
                previews the colour under the mouse
  buttons       Použít (primary, left) / Zrušit (right), 96 x 26, gap 10

Text, field and button labels in Tahoma 12 (owner 9. 10. 2026). Values go through the settings window's change() like
before (settingsbackend / damageappearance); Esc, the X and Zrušit close without a change. Built once per settings
window and reused; nothing is created per frame. The settings window falls back to the old dialog (traced) when this
one cannot be built.
"""
import ui
import wndMgr

import uir1
import uir1tokens as T
from settingslocale import Text as Tr

PICKER_IMAGE = 'd:/ymir work/ui/skillcolor/color_picker_background.tga'
PICKER_DOT = 'd:/ymir work/ui/skillcolor/color_picker_dot.tga'
PICKER_TEXTURE = (225, 225)       # native size of the picker texture
PICKER_AREA = (0, 31, 225, 161)   # its colour area (x, y, w, h): the rows above and below are an empty dark strip
DOT = 15                          # the selection ring (native size)

W = 260                           # standard C: 16 px side margin around the 225 px gradient (+ rounding)
PAD_TOP = 8                       # header -> gradient
GAP = 10                          # between the blocks and between the buttons
PAD_BOTTOM = 12
SWATCH = T.FIELD_H                # the colour square, as high as the field
HEX_W = 84
PREVIEW_H = 48
PREVIEW_NUMBERS = {'damage_normal_color': 1016, 'damage_critical_color': 8888}   # as "Náhled zásahů"
GLYPHS = 13                       # the longest preview text ("4 294 967 295")

TITLES = {'damage_normal_color': ('Barva normálních zásahů', 'Normal hit color'),
          'damage_critical_color': ('Barva kritických zásahů', 'Critical hit color')}


def HexText(value):
    return '#%06X' % (int(value) & 0xFFFFFF)


def ParseHex(text):
    """'#RRGGBB' or 'RRGGBB' -> int, None while the text is not a whole colour."""
    text = (text or '').strip()
    if text.startswith('#'):
        text = text[1:]
    if len(text) != 6:
        return None
    try:
        return int(text, 16)
    except ValueError:
        return None


def _Rgb(value):
    return tuple(((int(value) >> shift) & 255) / 255.0 for shift in (16, 8, 0))


class DamageColorDialog(ui.Window):
    def __init__(self, owner=None):
        # ui.Window.__init__ may dispatch Hide / Close: every attribute they read exists first
        self.owner = owner
        self.key = None
        self.selected = 0
        self.shown_value = None
        self.values = {}
        self.on_confirm = self.on_default = None
        self.updating_hex = False
        self.preview_state = None
        self.built = False
        ui.Window.__init__(self)
        import uiconfirm
        uiconfirm.Bind(self, 'accept')
        self.AddFlag('float')
        self.AddFlag('movable')
        self._Build()

    # ------------------------------------------------------------------ build (once)
    def _Build(self):
        kit = self.kit = uir1.Kit()
        font = kit.font('tahoma')
        self.chrome = uir1.Chrome(self, kit, W, 100, Tr(*TITLES['damage_normal_color']), on_close=ui.__mem_func__(self.Cancel))
        y = self.chrome.ContentTop() + PAD_TOP
        ax, ay, aw, ah = PICKER_AREA
        tw, th = PICKER_TEXTURE
        self.area = (int((W - aw) // 2), y, aw, ah)
        x0 = self.area[0]
        # the texture keeps its pixels where they are; the rendering rect only cuts the strips off
        self.gradient = ui.ExpandedImageBox()
        self.gradient.SetParent(self)
        self.gradient.AddFlag('not_pick')
        self.gradient.LoadImage(PICKER_IMAGE)
        self.gradient.SetPosition(x0 - ax, y - ay)
        self.gradient.SetRenderingRect(-float(ax) / tw, -float(ay) / th, float(ax + aw) / tw - 1.0,
                                       float(ay + ah) / th - 1.0)
        self.gradient.Show()
        self.dot = ui.ImageBox()
        self.dot.SetParent(self)
        self.dot.AddFlag('not_pick')
        self.dot.LoadImage(PICKER_DOT)
        self.dot.Hide()
        self.pick = uir1.HitArea(self, x0, y, aw, ah)
        self.pick.SetEvent(ui.__mem_func__(self.SelectHovered))
        y += ah + GAP
        row_h = T.BTN_H
        line = uir1.Rect(self, x0, y + (row_h - SWATCH) // 2, SWATCH, SWATCH, T.LINE)
        line.AddFlag('not_pick')
        self.swatch = uir1.Rect(self, x0 + 1, y + (row_h - SWATCH) // 2 + 1, SWATCH - 2, SWATCH - 2, 0xFFFFFF00)
        self.field = uir1.Field(self, kit, x0 + SWATCH + 8, y + (row_h - T.FIELD_H) // 2, HEX_W, max_len=7,
                                font=font)
        edit = self.field.edit
        edit.OnIMEUpdate = ui.__mem_func__(self._OnHexInput)
        edit.SetReturnEvent(ui.__mem_func__(self.Confirm))
        edit.SetEscapeEvent(ui.__mem_func__(self.Cancel))
        self.default = uir1.Button(self, kit, x0 + aw - T.BTN_W, y, T.BTN_W, Tr('Výchozí', 'Default'),
                                   event=ui.__mem_func__(self.UseDefault), font=font)
        y += row_h + GAP
        self.preview_frame = uir1.Frame(self, x0, y, aw, PREVIEW_H, 'panel')
        self.preview_box = (x0, y, aw, PREVIEW_H)
        self.glyphs = []
        for unused in range(GLYPHS):
            image = ui.ExpandedImageBox()
            image.SetParent(self)
            image.AddFlag('not_pick')
            image.Hide()
            self.glyphs.append(image)
        y += PREVIEW_H + GAP + 2
        bx = (W - 2 * T.BTN_W - GAP) // 2
        # confirm left (primary, the red vein), cancel right
        self.accept = uir1.Button(self, kit, bx, y, T.BTN_W, Tr('Použít', 'Apply'), primary=True,
                                  event=ui.__mem_func__(self.Confirm), font=font)
        self.cancel = uir1.Button(self, kit, bx + T.BTN_W + GAP, y, T.BTN_W, Tr('Zrušit', 'Cancel'),
                                  event=ui.__mem_func__(self.Cancel), font=font)
        self.h = y + T.BTN_H + PAD_BOTTOM
        self.SetSize(W, self.h)
        self.chrome.frame.Resize(W, self.h)
        self.built = True

    # ------------------------------------------------------------------ open / close
    def Open(self, key, value, values, on_confirm, on_default):
        """key: damage_normal_color / damage_critical_color; values: the current damage settings (font, outline,
        size, grouping) for the preview; on_confirm(value) / on_default() as the old ColorPickerDialog."""
        import damageappearance as damage
        self.key = key if key in TITLES else 'damage_normal_color'
        self.values = dict(values or {})
        self.selected = int(value) & 0xFFFFFF
        self.on_confirm, self.on_default = on_confirm, on_default
        self.chrome.SetTitle(Tr(*TITLES[self.key]))
        default = damage.DEFAULTS.get(self.key, 0)
        self.default.SetToolTipText(Tr('Vrátí výchozí barvu %s.' % HexText(default),
                                       'Restores the default colour %s.' % HexText(default)))
        self.dot.Hide()
        self.preview_state = None
        self._ShowColor(self.selected, hex_text=True)
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def IsOpen(self):
        return self.built and self.IsShow()

    def _Finish(self):
        self.on_confirm = self.on_default = None
        if not self.built:
            return
        self.field.edit.KillFocus()
        uir1.HideHint(self.default)
        self.KillFocus()
        self.Hide()
        owner = self.owner
        try:
            if owner is not None and owner.IsShow():
                owner.SetFocus()
        except ReferenceError:
            self.owner = None

    def Confirm(self):
        callback, value = self.on_confirm, self.selected
        self._Finish()
        if callback:
            callback(value)
        return True

    def UseDefault(self):
        callback = self.on_default
        self._Finish()
        if callback:
            callback()
        return True

    def Cancel(self):
        self._Finish()
        return True

    def Close(self):
        return self.Cancel()

    def ClearDictionary(self):
        """The settings window's Destroy (the old dialog's API): drops the callbacks and the owner."""
        self._Finish()
        self.owner = None

    def OnPressEscapeKey(self):
        return self.Cancel()

    # ------------------------------------------------------------------ colour
    def _ShowColor(self, value, hex_text=False):
        """Swatch and preview in ``value`` (the selection or the colour under the mouse); the hex text only when
        asked (typing keeps what the player writes)."""
        value = int(value) & 0xFFFFFF
        r, g, b = _Rgb(value)
        self.swatch.SetColor(uir1.GenerateColor(value | 0xFF000000))
        if hex_text:
            self.updating_hex = True
            try:
                self.field.edit.SetText(HexText(value))
            finally:
                self.updating_hex = False
        self._Preview(value)
        self.shown_value = value

    def _OnHexInput(self):
        ui.EditLine.OnIMEUpdate(self.field.edit)
        if self.updating_hex:
            return
        value = ParseHex(self.field.edit.GetText())
        if value is None:
            return
        self.selected = value
        self.dot.Hide()
        self._ShowColor(value)

    def _ColorUnderMouse(self):
        try:
            x, y = wndMgr.GetRealMousePosition()
            red, green, blue = wndMgr.GetColorAtPosition(x, y)
        except Exception:
            return None
        return ((int(red) & 255) << 16) | ((int(green) & 255) << 8) | (int(blue) & 255)

    def SelectHovered(self):
        value = self._ColorUnderMouse()
        if value is None:
            return
        self.selected = value
        ax, ay, aw, ah = self.area
        gx, gy = self.GetGlobalPosition()
        mx, my = wndMgr.GetMousePosition()
        lx = max(0, min(aw - 1, mx - gx - ax))
        ly = max(0, min(ah - 1, my - gy - ay))
        self.dot.SetPosition(ax + lx - DOT // 2, ay + ly - DOT // 2)
        self.dot.Show()
        self._ShowColor(value, hex_text=True)

    def OnUpdate(self):
        if not self.built or not self.IsShow():
            return
        value = self.selected
        if self.pick.hovered:
            under = self._ColorUnderMouse()
            if under is not None:
                value = under
        if value != self.shown_value:
            self._ShowColor(value)

    # ------------------------------------------------------------------ preview
    def _Preview(self, value):
        """The number of "Náhled zásahů" in the dialog: laid out again (textures, scale, centring) only when the
        font, outline, size or grouping or the original-digits case changes; otherwise only recoloured."""
        import damageappearance as damage
        values = self.values
        font = int(values.get('damage_font', damage.DEFAULTS['damage_font']))
        outline = int(values.get('damage_outline', damage.DEFAULTS['damage_outline']))
        legacy = self.key == 'damage_normal_color' and font == 0 and outline and \
            value == damage.DEFAULTS['damage_normal_color']
        state = (self.key, font, outline, values.get('damage_size', 0.), values.get('damage_grouping', 0), legacy)
        if state != self.preview_state:
            self.preview_state = state
            self._LayoutPreview(value)
            return
        color = _Rgb(value)
        for image, glyph in zip(self.glyphs, self.glyph_text):
            if image.IsShow():
                old = legacy and glyph != '.'
                image.SetDiffuseColor(*(color if not old or self.key == 'damage_critical_color' else (1., 1., 1.))
                                      + (1.,))

    def _LayoutPreview(self, value):
        import uidamagesettings
        import damageappearance as damage
        bx, by, bw, bh = self.preview_box
        values = dict(damage.DEFAULTS)
        values.update(damage_size=0., damage_height=0.)
        values.update(self.values)
        values['damage_height'] = 0.              # the height above the target does not belong to the preview
        values[self.key] = value
        number = PREVIEW_NUMBERS.get(self.key, 1016)
        control = dict(kind='damage_preview', key=self.key, images=self.glyphs, x=0, y=0, number=number)
        uidamagesettings.refresh(control, values)
        self.glyph_text = damage.format_number(number, values['damage_grouping'])
        shown = [image for image in self.glyphs if image.IsShow()]
        if not shown:
            return
        # the engine's ExpandedImageBox.SetScale resizes the window too (CExpandedImageBox::SetScale): the sizes are
        # the drawn glyph sizes
        left = min(image.GetLocalPosition()[0] for image in shown)
        top = min(image.GetLocalPosition()[1] for image in shown)
        right = max(image.GetLocalPosition()[0] + image.GetWidth() for image in shown)
        bottom = max(image.GetLocalPosition()[1] + image.GetHeight() for image in shown)
        dx = bx + (bw - (right - left)) // 2 - left
        dy = by + (bh - (bottom - top)) // 2 - top
        for image in shown:
            x, y = image.GetLocalPosition()
            image.SetPosition(x + dx, y + dy)


def DamageValues(window):
    """The damage settings of the settings window for the preview (its current, unsaved values)."""
    import damageappearance as damage
    values = {}
    for key in damage.KEYS + ('damage_size',):
        try:
            values[key] = window.value(key)
        except Exception:
            pass
    return values
