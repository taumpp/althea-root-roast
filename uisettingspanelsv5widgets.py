# -*- coding: utf-8 -*-
"""Components of Settings v5 -> Panely tlačítek (2026-10-05, design v4.1).

Built on the Althea UI kit runtime (uikit) and kept in this module so the shared kit stays untouched:

  Tile         one function / free place (catalogue, preview): hover, press, drag, right click; any scale
  MiniBadge    dot or number of a scaled tile (the full ButtonDecor draws only on 1:1 tiles)
  InfoDot      the small "i" next to a setting label (opens the help bubble)
  InfoZone     the hover rectangle of a setting group (not a window: polled, never takes a click)
  Outline      a thin gold rectangle (focus of the preview, drop target areas, tour highlights)
  Well         sunken area of a catalogue section (dark fill + bronze line)
  Tip          floating tooltip (kit panel, title + text)
  ContextMenu  right-click menu: title, badge/state switches, actions (closes on any outside click)
  Bubble       help bubble of an "i": title, text, optional small preview drawn by a callback
  ResetDialog  "Obnovit stránku" confirmation: exact text of what returns, choice tab / whole page
  Ghost        the dragged icon following the mouse
  TourBox      the 4-step guide: dimmed window with highlighted holes, a step bubble, Přeskočit / Další

Every popup is a top-level float window; ``Destroy`` releases it.
"""
import ui
import wndMgr

import uikit
import uikittokens as T

KIT = T.KIT_ROOT
# Small texts drawn on the game art (marks, VIP, badge digits): the family of the page (the window's kit:
# Spectral, or Tahoma when the kit fell back for an EXE without registered font families). ``SetFamily``.
SMALL_FONT = 'Althea Book SemiBold:%da'


def SmallFont(size):
    if SMALL_FONT.startswith('Noto Sans'):
        return SMALL_FONT % max(10, int(round(size * 0.86)))   # the width of the Spectral size (Noto is wider)
    return SMALL_FONT % (size if SMALL_FONT.startswith('Althea') else max(9, size - 3))


def SetFamily(kit):
    """Small texts follow the kit's family (called by the page when it builds): Spectral, Noto Sans in the R1 skin,
    Tahoma for an EXE without registered font families."""
    global SMALL_FONT
    medium = kit.font('Mb') if kit is not None else 'Althea Book SemiBold:21a'
    if medium.startswith('Tahoma'):
        SMALL_FONT = 'Tahoma:%db'
    elif medium.startswith('Noto Sans'):
        SMALL_FONT = 'Noto Sans:%da'
    else:
        SMALL_FONT = 'Althea Book SemiBold:%da'
V5 = 'd:/ymir work/ui/public/althea_kit_v5panels/'
BADGE_ART = 'd:/ymir work/ui/game/crimson_ember/button_panel_badges/'
OUTLINE_GOLD = 0xFFDCB46E
DIM_ALPHA = 0.35


def R1Medallions():
    """The previews of the R1 look (R1 kit skin, not "Starý vzhled"): every place is a round minimap A2 button
    (``minimappanelicons``) - the rail places too, and a free place is the empty R1 medallion - when the R1
    minimap art is packed. False keeps today's art (square rail carriers, the gold dotted free circle)."""
    if getattr(uikit, 'SKIN', None) != 'r1':
        return False
    try:
        import minimappanelicons as icons
        return icons.Visual(None, 'normal').startswith(icons.R1_MINIMAPA)
    except Exception:
        return False


def FreeVisual(state='normal'):
    """The free place: the empty R1 medallion in the R1 look, else the gold dotted circle (28 px both)."""
    if R1Medallions():
        import minimappanelicons as icons
        return icons.Visual(None, state)
    return V5 + 'free_slot_28_%s.png' % state


def FreeLegend(parent, x, y, scale=1.0):
    """The free place of the legends (20 px): the dotted circle, or the empty R1 medallion drawn 20 px wide."""
    if R1Medallions():
        return Image.Make(parent, FreeVisual(), x, y, scale * 20.0 / 28.0)
    return Image.Make(parent, V5 + 'free_slot_20_normal.png', x, y, scale)


def SelectedRing():
    """The ring around the selected place (36 px at -4, -4): the brighter R1 inner ring of minimap A2 in R1."""
    if R1Medallions():
        import minimappanelicons as icons
        ring = icons.R1Art('ring_active.png')
        if ring:
            return ring
    return BADGE_ART + 'ring_medallion.png'


def AccentRole(kind='ruby'):
    """The primary role of the kit's one button family (v6, 2026-10-06); 'close' on an older kit."""
    return 'primary' if 'primary' in getattr(uikit, 'RUBY_ROLES', ()) else 'close'


def Rgb(packed):
    return uikit.Color(packed)


def Bar(parent, packed, alpha=1.0, pick=False):
    """A plain colour bar (not pickable unless ``pick``)."""
    bar = ui.Bar()
    bar.SetParent(parent)
    if not pick:
        bar.AddFlag('not_pick')
    bar.SetColor(uikit.GenerateColor(packed, alpha))
    bar.Show()
    return bar


def FitText(line, text, width):
    """Set ``text`` on a TextLine, shortened with "…" (whole words) when it is wider than ``width``. Returns
    True when the whole text fits."""
    line.SetText(text)
    if uikit.TextWidth(line) <= width:
        return True
    words = text.split()
    while words:
        words.pop()
        line.SetText(' '.join(words) + ' ...' if words else '...')
        if uikit.TextWidth(line) <= width:
            break
    return False


def ScreenSize():
    try:
        return wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
    except Exception:
        return 1920, 1080


def Mouse():
    try:
        return tuple(wndMgr.GetMousePosition())
    except Exception:
        return 0, 0


def GlobalRect(widget):
    x, y = widget.GetGlobalPosition()
    return x, y, widget.GetWidth(), widget.GetHeight()


def Inside(rect, point):
    x, y, w, h = rect
    return x <= point[0] < x + w and y <= point[1] < y + h


class Image(object):
    """An ExpandedImageBox at a scale (native art drawn smaller / larger); alpha for dimmed previews."""

    @staticmethod
    def Make(parent, path, x, y, scale=1.0, alpha=1.0):
        image = ui.ExpandedImageBox()
        image.SetParent(parent)
        image.AddFlag('not_pick')
        Image.Set(image, path, x, y, scale, alpha)
        return image

    @staticmethod
    def Set(image, path, x, y, scale=1.0, alpha=1.0):
        if path and getattr(image, '_v5path', None) != path:
            image.LoadImage(path)
            image._v5path = path
            # LoadImage makes a new engine image instance (CExpandedImageBox::OnCreateInstance): scale and alpha are
            # back to 1.0, so they are applied again (hover swaps the path - the icons shrank on hover).
            image._v5scale = image._v5alpha = 1.0
        image.SetPosition(int(round(x)), int(round(y)))
        if getattr(image, '_v5scale', 1.0) != scale:
            image.SetScale(float(scale), float(scale))
            image._v5scale = scale
            if scale != 1.0 and hasattr(image, 'SetLinearFiltering'):
                image.SetLinearFiltering(True)
        if getattr(image, '_v5alpha', 1.0) != alpha:
            image.SetAlpha(float(alpha))
            image._v5alpha = alpha
        image.Show()
        return image


# --------------------------------------------------------------------------- tiles
class MiniBadge(object):
    """Dot or number of a scaled tile (``buttonpanelbadges.Decor``); placed at the tile's top-right corner."""

    def __init__(self, parent):
        self.parent = parent
        self.image = Image.Make(parent, BADGE_ART + 'dot_action.png', 0, 0)
        self.image.Hide()
        self.text = uikit.Text(parent, '', 0, 0, SmallFont(13), 0xFFF4DA9C, align='center')
        self.text.Hide()
        self.key = None

    def Set(self, decor, size):
        key = (decor.badge, decor.count, size) if decor is not None else None
        if key == self.key:
            return
        self.key = key
        if decor is None or not decor.badge:
            self.image.Hide()
            self.text.Hide()
            return
        import buttonpanelbadges as badges
        if decor.count:
            Image.Set(self.image, BADGE_ART + 'count_action_18.png', size - 13, -5)
            self.text.SetText(badges.BadgeText(decor.count))
            self.text.SetPosition(size - 4, 4)
            self.text.Show()
        else:
            dot = 'dot_action.png' if decor.badge == badges.BADGE_ACTION else 'dot_info.png'
            Image.Set(self.image, BADGE_ART + dot, size - 9, -2)
            self.text.Hide()


def VipTag(parent, x, y):
    """The small "VIP" plate of the VIP channels (catalogue, legend): dark plate, brass line, gold text."""
    widgets = [Bar(parent, 0xFF1A1208, 0.95), Bar(parent, T.BRASS, 0.9),
               uikit.Text(parent, 'VIP', 0, 0, SmallFont(11), T.GOLD_HI, align='center')]
    PlaceVipTag(widgets, x, y)
    return widgets


def PlaceVipTag(widgets, x, y):
    plate, line, text = widgets
    plate.SetPosition(int(x), int(y))
    plate.SetSize(20, 10)
    line.SetPosition(int(x), int(y) + 9)
    line.SetSize(20, 1)
    text.SetPosition(int(x) + 10, int(y) + 5)
    for widget in widgets:
        widget.Show()


class Tile(uikit.Interactive):
    """One function or free place. ``kind`` 'medallion' (28 px minimap/catalogue art) or 'rail' (37 px
    carrier with the 24 px rail icon). The page owns the logic: press / release / right click / hover."""

    def __init__(self, page, parent, kind='medallion'):
        uikit.Interactive.__init__(self)
        self.page = page
        self.kind = kind
        self.SetParent(parent)
        self.action = None       # function id, None = free place
        self.source = None       # page-defined descriptor of the place / catalogue entry
        self.scale = 1.0
        self.alpha = 1.0
        self.static = False      # dimmed thumbnails: no input
        self.selected = False
        self.carrier = Image.Make(self, None, 0, 0) if kind == 'rail' else None
        self.icon = Image.Make(self, None, 0, 0)
        self.mark = uikit.Text(self, '', 0, 0, SmallFont(15), T.INK, align='center')
        self.mark.Hide()
        self.vip = None
        self.off = None
        self.ring = None
        self.mini = None
        self.decor_kind = None
        self.Show()

    def Size(self):
        native = 37 if self.kind == 'rail' else 28
        return int(round(native * self.scale))

    def Set(self, action, source, scale=1.0, alpha=1.0, static=False):
        self.action, self.source, self.scale, self.alpha, self.static = action, source, scale, alpha, static
        size = self.Size()
        self.SetSize(size, size)
        if static:
            self.AddFlag('not_pick')
        self.hovered = self.hovered and not static
        self.paint()
        self.Show()

    def _Visuals(self):
        """(carrier or None, icon path, icon offset (native px), icon scale factor, mark text)."""
        import minimappanelicons
        if self.action is None:
            offset = 4.5 if self.kind == 'rail' else 0
            return None, FreeVisual('hover' if self.hovered else 'normal'), offset, 1.0, ''
        state = 'hover' if self.hovered or self.selected else 'normal'
        if self.kind == 'rail' and R1Medallions():
            # R1: the round minimap A2 button centred on the 37 px place, no square carrier.
            return None, minimappanelicons.Visual(self.action, state), 4.5, 1.0, minimappanelicons.Mark(self.action)
        if self.kind == 'rail':
            import inventoryrailicons
            path, position, mark = inventoryrailicons.Icon(self.action)
            carrier = 'd:/ymir work/ui/game/crimson_ember/inventory/rail_button_%s.png' % state
            return carrier, path, position, 1.0, mark
        return None, minimappanelicons.Visual(self.action, state), 0, 1.0, minimappanelicons.Mark(self.action)

    def paint(self):
        carrier, path, offset, unused, mark = self._Visuals()
        s, a = self.scale, self.alpha
        if isinstance(offset, tuple):
            ox, oy = offset
        else:
            ox = oy = offset
        if self.carrier is not None:
            if carrier:
                Image.Set(self.carrier, carrier, 0, 0, s, a)
            else:
                self.carrier.Hide()
        Image.Set(self.icon, path, ox * s, oy * s, s, a)
        if mark and s >= 0.7:
            self.mark.SetText(mark)
            self.mark.SetPosition(self.Size() // 2, self.Size() // 2)
            self.mark.Show()
        else:
            self.mark.Hide()
        self._Vip()

    def _Vip(self):
        import minimappanel
        vip = self.action is not None and minimappanel.ChannelIndex(self.action) in minimappanel.VIP_CHANNELS
        if vip and self.scale >= 0.7:
            if self.vip is None:
                self.vip = VipTag(self, 0, 0)
            size = self.Size()
            PlaceVipTag(self.vip, size // 2 - 4, size - 8)
        elif self.vip is not None:
            for widget in self.vip:
                widget.Hide()

    def SetBadgeOff(self, off):
        """Crossed grey dot: the player turned this function's badge off (as on the A7 page)."""
        if off and self.action is not None:
            if self.off is None:
                self.off = Image.Make(self, BADGE_ART + 'dot_off.png', 0, 0)
            Image.Set(self.off, BADGE_ART + 'dot_off.png', self.Size() - 9, -1)
        elif self.off is not None:
            self.off.Hide()

    def SetSelected(self, selected):
        self.selected = bool(selected)
        round_place = self.kind != 'rail' or R1Medallions()
        if self.selected and round_place:
            ring = SelectedRing()
            inset = -4 + (4.5 if self.kind == 'rail' else 0)
            if self.ring is None:
                self.ring = Image.Make(self, ring, 0, 0)
            Image.Set(self.ring, ring, inset * self.scale, inset * self.scale, self.scale)
        elif self.ring is not None:
            self.ring.Hide()
        self.paint()

    def SetMini(self, decor):
        if self.mini is None:
            self.mini = MiniBadge(self)
        self.mini.Set(decor, self.Size())

    # input -----------------------------------------------------------------------
    def OnMouseOverIn(self):
        if self.static:
            return
        self.hovered = True
        self.paint()
        if self.page is not None:
            self.page.TileHover(self, True)

    def OnMouseOverOut(self):
        self.hovered = False
        if self.static:
            return
        self.paint()
        if self.page is not None:
            self.page.TileHover(self, False)

    def OnMouseLeftButtonDown(self):
        if not self.static and self.page is not None:
            self.page.TilePress(self)
        return True

    def OnMouseLeftButtonUp(self):
        if not self.static and self.page is not None:
            self.page.TileRelease(self)
        return True

    def OnMouseRightButtonUp(self):
        if not self.static and self.page is not None:
            self.page.TileContext(self)
        return True

    def Destroy(self):
        self.page = None


class InfoZone(object):
    """The hover area of one setting group for its help bubble - NOT a window. Owner play test 2026-10-06
    (screenshot 190): a hover window over "Sloupce / Strany" took every click, because the engine picks the LAST
    added child first (CWindow::PickWindow) and re-parenting the control to the same parent does not move it
    (CWindowManager::SetParent returns early). The page polls the mouse position against these rectangles every
    frame (PanelsInput._InfoTick), so nothing lies over a control."""

    def __init__(self, parent, x, y, w, h, key):
        self.parent, self.info_key = parent, key
        self.x, self.y, self.w, self.h = int(x), int(y), int(w), int(h)

    def IsShow(self):
        try:
            return bool(self.parent.IsShow())
        except Exception:
            return False

    def GetGlobalPosition(self):
        px, py = self.parent.GetGlobalPosition()
        return px + self.x, py + self.y

    def GetLocalPosition(self):
        return self.x, self.y

    def GetWidth(self):
        return self.w

    def GetHeight(self):
        return self.h


class InfoDot(uikit.Interactive):
    """The "i" after a setting label; a click opens the help bubble (kit info icon, 20 px)."""
    SIZE = 20

    def __init__(self, parent, x, y, event):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.SIZE, self.SIZE)
        self.image = Image.Make(self, None, 0, 0)
        self.callback = event
        self.paint()
        self.Show()

    def paint(self):
        state = {'pressed': 'active', 'disabled': 'disabled'}.get(self.state(), self.state())
        Image.Set(self.image, uikit.Path('icons/%d/info_%s.png' % (self.SIZE, state)), 0, 0)


class Outline(object):
    """Thin rectangle of four bars (not pickable)."""

    def __init__(self, parent, packed=OUTLINE_GOLD, alpha=0.85, thickness=1):
        self.bars = [Bar(parent, packed, alpha) for unused in range(4)]
        self.thickness = thickness
        self.Hide()

    def Set(self, x, y, w, h):
        t = self.thickness
        for bar, (bx, by, bw, bh) in zip(self.bars, ((x, y, w, t), (x, y + h - t, w, t), (x, y, t, h),
                                                    (x + w - t, y, t, h))):
            bar.SetPosition(int(bx), int(by))
            bar.SetSize(max(1, int(bw)), max(1, int(bh)))
            bar.Show()

    def Hide(self):
        for bar in self.bars:
            bar.Hide()

    def SetTop(self):
        for bar in self.bars:
            bar.SetTop()

    def Widgets(self):
        return list(self.bars)


class Well(object):
    """Catalogue section area (drop target): a sunken well (dark fill + bronze line), or ``plain`` (P1, owner
    2026-10-06: the icons stand on the page without frames) where only an EMPTY section shows a faint outline as the
    place to drop into."""

    def __init__(self, parent, plain=False):
        self.plain = plain
        self.fill = Bar(parent, 0xFF060505, 0.78)
        self.line = Outline(parent, T.BRONZE_LINE_DK if not plain else T.BRONZE_LINE, 1.0 if not plain else 0.55)

    def Set(self, x, y, w, h, empty=False):
        self.fill.SetPosition(int(x), int(y))
        self.fill.SetSize(int(w), int(h))
        if self.plain and not empty:
            self.fill.Hide()
            self.line.Hide()
            return
        self.fill.SetColor(uikit.GenerateColor(0xFF060505, 0.78 if not self.plain else 0.45))
        self.fill.Show()
        self.line.Set(x, y, w, h)

    def Widgets(self):
        return [self.fill] + self.line.Widgets()


# --------------------------------------------------------------------------- popups
class Panel(ui.Window):
    """Top-level float window with the kit popup frame (uikit.PopupFrame: drop shadow, crisp outline, panel frame,
    one shade lighter fill - v5 fix 2026-10-05, the menu edge was hard to see on the dark window)."""

    def __init__(self, kit):
        ui.Window.__init__(self)
        self.kit = kit
        self.AddFlag('float')
        # The frame is the first child, so everything added later draws above it.
        self.frame = uikit.PopupFrame(self, kit)
        self.items = []

    def _Frame(self, w, h):
        self.frame.Apply(w, h)
        self.SetSize(w, h)

    def _Clear(self):
        for item in self.items:
            item.Hide()
        self.items = []

    def _Text(self, text, x, y, size, color, **kw):
        line = uikit.Text(self, text, x, y, self.kit.font(size), color, valign='top', **kw)
        self.items.append(line)
        return line

    def _Place(self, rect, side):
        """Next to ``rect`` (global x, y, w, h): 'left', 'right', 'above' or 'below', clamped to the screen."""
        x, y, w, h = rect
        pw, ph = self.GetWidth(), self.GetHeight()
        sw, sh = ScreenSize()
        gap = 8
        if side == 'left':
            px, py = x - pw - gap, y + h // 2 - ph // 2
            if px < 0:
                px = x + w + gap
        elif side == 'right':
            px, py = x + w + gap, y + h // 2 - ph // 2
            if px + pw > sw:
                px = x - pw - gap
        elif side == 'below':
            px, py = x + w // 2 - pw // 2, y + h + gap
            if py + ph > sh:
                py = y - ph - gap
        else:
            px, py = x + w // 2 - pw // 2, y - ph - gap
            if py < 0:
                py = y + h + gap
        self.SetPosition(max(0, min(int(px), sw - pw)), max(0, min(int(py), sh - ph)))


class Tip(Panel):
    """Hover tooltip: gold title and a dim line under it (never pickable, never steals the hover)."""

    def __init__(self, kit):
        Panel.__init__(self, kit)
        self.AddFlag('not_pick')
        self.key = None

    def ShowAt(self, rect, title, body='', side='left'):
        key = (tuple(rect), title, body, side)
        if key == self.key and self.IsShow():
            return
        self.key = key
        if self._R1Hint(rect, title, body, side):
            return
        self._Clear()
        k = self.kit
        pad = 12 if k.prof == '1080' else 9
        title_line = self._Text(title, pad, pad - 2, 'Sb', T.GOLD_HI)
        w = uikit.TextWidth(title_line)
        h = pad - 2 + k.cell('Sb')
        if body:
            body_line = self._Text(body, pad, h + 3, 'S', T.INK_DIM)
            w = max(w, uikit.TextWidth(body_line))
            h += 3 + k.cell('S')
        self._Frame(w + 2 * pad, h + pad)
        self._Place(rect, side)
        self.Show()
        self.SetTop()

    def _R1Hint(self, rect, title, body, side):
        """In the R1 look the one R1 hint: above the anchor, or beside it for side 'left' /
        'right'."""
        try:
            import uir1
            if not uir1.UseR1():
                return False
            uir1.ShowHintAt(rect, title, body or None, side if side in ('left', 'right') else 'above', owner=self)
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


class _Dismiss(ui.Window):
    """Transparent full-screen layer under a popup: any click outside closes it."""

    def __init__(self, owner):
        ui.Window.__init__(self)
        self.owner = owner
        self.AddFlag('float')

    def OnMouseLeftButtonDown(self):
        if self.owner is not None:
            self.owner.Close()
        return True

    def OnMouseRightButtonDown(self):
        return self.OnMouseLeftButtonDown()


class Popup(Panel):
    """A panel that closes on any outside click and on Esc."""

    def __init__(self, kit):
        Panel.__init__(self, kit)
        self.dismiss = _Dismiss(self)
        self.on_close = None

    def _Open(self):
        sw, sh = ScreenSize()
        self.dismiss.SetPosition(0, 0)
        self.dismiss.SetSize(sw, sh)
        self.dismiss.Show()
        self.dismiss.SetTop()
        self.Show()
        self.SetTop()

    def Close(self):
        was = self.IsShow()
        self.dismiss.Hide()
        self.Hide()
        if was and self.on_close:
            self.on_close()
        return True

    def OnPressEscapeKey(self):
        return self.Close()

    def Destroy(self):
        self.on_close = None
        self.Close()
        self.dismiss.owner = None


class _MenuRow(uikit.Interactive):
    def __init__(self, menu, w, h, label, callback, enabled=True):
        uikit.Interactive.__init__(self)
        self.menu = menu
        self.SetParent(menu)
        self.SetSize(w, h)
        self.band = uikit.Band(self, 0, 0, w, h, 'hover')
        self.band.Hide()
        self.label = uikit.Text(self, label, 14, h // 2, menu.kit.font('M'), T.INK)
        self.callback = callback
        self.enabled = enabled
        self.paint()
        self.Show()

    def paint(self):
        self.band.Show() if self.hovered and self.enabled else self.band.Hide()
        self.label.SetPackedFontColor(T.DISABLED if not self.enabled else (T.GOLD_HI if self.hovered else T.INK))

    def click(self):
        self.menu.Run(self.callback)


class ContextMenu(Popup):
    """Right click on a function: its name, the badge / state switches, then the actions."""

    def Open(self, title, toggles, actions, rect):
        """``toggles`` [(label, on, enabled, callback)], ``actions`` [(label, callback)]; rect = global anchor."""
        self._Clear()
        k = self.kit
        big = k.prof == '1080'
        rh = 34 if big else 28
        check = getattr(uikit, 'CheckBox', None)
        tw, th = (k.p('check'), k.p('check')) if check is not None else uikit.Toggle.Size(k)
        y = 12
        title_line = self._Text(title, 14, y, 'Mb', T.GOLD_HI)
        w = max(240 if big else 200, uikit.TextWidth(title_line) + 28)
        labels = []
        for label, on, enabled, callback in toggles:
            line = uikit.Text(self, label, 14, 0, k.font('M'), T.INK if enabled else T.DISABLED)
            self.items.append(line)
            labels.append(line)
            w = max(w, uikit.TextWidth(line) + tw + 44)
        for label, callback in actions:
            probe = uikit.Text(self, label, 0, 0, k.font('M'), T.INK)
            w = max(w, uikit.TextWidth(probe) + 40)
            probe.Hide()
        y += k.cell('Mb') + 8
        # Owner play test 2026-10-05: the items were told apart only by the hover band. Now a bronze rule under the
        # title and between the groups, a fine kit separator between neighbouring items.
        self.separators = []
        if toggles or actions:
            self._Separator(10, y - 3, w - 20, group=True)
        self.toggles = []
        for index, (line, (label, on, enabled, callback)) in enumerate(zip(labels, toggles)):
            if index:
                self._Separator(14, y, w - 28)
            if check is not None:
                # v6 (design v5 section 4): a check box before the label instead of a big switch at the right.
                toggle = check(self, k, 14, y + (rh - th) // 2, '', on,
                               event=lambda run=callback: self.Run(run, keep=True))
                line.SetPosition(14 + tw + 10, y + rh // 2)
            else:
                line.SetPosition(14, y + rh // 2)
                toggle = uikit.Toggle(self, k, w - 14 - tw, y + (rh - th) // 2, on,
                                      event=lambda run=callback: self.Run(run, keep=True))
            if not enabled:
                toggle.Disable()
            self.items.append(toggle)
            self.toggles.append(toggle)
            y += rh
        if toggles and actions:
            self._Separator(10, y + 4, w - 20, group=True)
            y += 10
        self.rows = []
        for index, (label, callback) in enumerate(actions):
            if index:
                self._Separator(14, y, w - 28)
            row = _MenuRow(self, w - 8, rh, label, callback)
            row.SetPosition(4, y)
            self.items.append(row)
            self.rows.append(row)
            y += rh
        self._Frame(w, y + 8)
        self._Place(rect, 'left')
        self._Open()

    def _Separator(self, x, y, w, group=False):
        """A rule between groups (bronze) or a fine separator between items (uikit.Separator)."""
        line = uikit.HLine(self, x, y, w, T.BRONZE_LINE_DK) if group else uikit.Separator(self, x, y, w)
        self.items.append(line)
        self.separators.append(line)
        return line

    def Run(self, callback, keep=False):
        if not keep:
            self.Close()
        if callback:
            callback()


class Bubble(Popup):
    """Help of a setting: title, paragraphs and an optional small preview (``figure(parent, x, y, w)`` returns
    the height it drew). ``modal=False`` (the hover help of Panely, 2026-10-06): no dismiss layer and not pickable,
    so it never takes a click or the hover from the page under it."""

    def __init__(self, kit, modal=True):
        Popup.__init__(self, kit)
        self.modal = modal
        if not modal:
            self.AddFlag('not_pick')

    def _Open(self):
        if self.modal:
            Popup._Open(self)
            return
        self.Show()
        self.SetTop()

    def Open(self, title, paragraphs, rect, figure=None, side='right'):
        self._Clear()
        k = self.kit
        w = 320 if k.prof == '1080' else 250
        pad = 14 if k.prof == '1080' else 10
        y = pad
        self._Text(title, pad, y, 'Mb', T.GOLD_HI)
        y += k.cell('Mb') + 8
        for index, paragraph in enumerate(paragraphs):
            lines, y = uikit.Wrap(self, paragraph, pad, y, w - 2 * pad, k.font('S'), T.INK_DIM, k.cell('S') + 4)
            self.items.extend(lines)
            y += 6
        if figure is not None:
            y += 4
            holder = ui.Window()
            holder.SetParent(self)
            holder.AddFlag('not_pick')
            holder.SetPosition(pad, y)
            holder.Show()
            self.items.append(holder)
            fh = figure(holder, w - 2 * pad)
            holder.SetSize(w - 2 * pad, fh)
            y += fh + 6
        self._Frame(w, y + pad - 6)
        self._Place(rect, side)
        self._Open()


class ResetDialog(ui.Window):
    """"Obnovit stránku": dialog title bar, a choice "Tuto záložku / Celou stránku" and the exact text of
    what returns for that choice (``describe(scope)`` -> (question, [lines])); ESC cancels."""

    def __init__(self, kit, title, accept_text, cancel_text, choices):
        ui.Window.__init__(self)
        import uiconfirm
        uiconfirm.Bind(self, 'accept')
        self.kit = kit
        self.AddFlag('float')
        self.AddFlag('movable')
        self.w = 470 if kit.prof == '1080' else 380
        self.frame = uikit.Frame(self, kit, 'window', 0, 0, self.w, 200, bg=True)
        self.bar = uikit.TitleBar(self, kit, 5, 5, self.w - 10, title, kind='dialog', on_close=self.Cancel)
        self.segment = uikit.Segment(self, kit, choices, event=self.Choose, font=kit.font('S'))
        bw = 150 if kit.prof == '1080' else 124
        self.accept = uikit.Button(self, kit, 0, 0, bw, accept_text, role=AccentRole('ruby'), event=self.Accept,
                                   size='bar')
        self.cancel = uikit.Button(self, kit, 0, 0, bw, cancel_text, role='secondary', event=self.Cancel, size='bar')
        self.lines = []
        self.scope = None
        self.describe = None
        self.on_accept = None
        self.owner = None

    def Open(self, describe, on_accept, scope):
        self.describe, self.on_accept = describe, on_accept
        self.Choose(scope)
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Choose(self, scope):
        self.scope = scope
        self.segment.SetValue(scope)
        for line in self.lines:
            line.Hide()
        k = self.kit
        question, details = self.describe(scope)
        y = 5 + self.bar.Height() + 16
        self.segment.SetPosition((self.w - self.segment.Width()) // 2, y)
        y += k.p('seg_h') + 14
        lines, y = uikit.Wrap(self, question, 24, y, self.w - 48, k.font('Mb'), T.INK, k.cell('Mb') + 4)
        self.lines = list(lines)
        y += 4
        for detail in details:
            more, y = uikit.Wrap(self, detail, 24, y, self.w - 48, k.font('S'), T.INK_DIM, k.cell('S') + 4)
            self.lines.extend(more)
        y += 14
        gap = 14
        x = (self.w - self.accept.w - self.cancel.w - gap) // 2
        bh = max(self.accept.h, self.cancel.h)
        self.accept.SetPosition(x, y + (bh - self.accept.h) // 2)
        self.cancel.SetPosition(x + self.accept.w + gap, y + (bh - self.cancel.h) // 2)
        h = y + bh + 18
        self.SetSize(self.w, h)
        self.frame.SetSize(self.w, h)
        self.frame.Apply(uikit.L.frame('window', k.prof, self.w, h, bg=True))

    def Text(self):
        return ' '.join(line.GetText() for line in self.lines)

    def Accept(self):
        scope = self.scope
        self.Close()
        if self.on_accept:
            self.on_accept(scope)

    def Cancel(self):
        self.Close()

    def Close(self):
        self.KillFocus()
        self.Hide()
        owner = self.owner
        if owner is not None and owner.IsShow():
            owner.SetFocus()

    def OnPressEscapeKey(self):
        self.Cancel()
        return True

    def Destroy(self):
        self.Hide()
        self.on_accept = self.describe = self.owner = None


class Ghost(ui.Window):
    """The dragged icon: a not-pickable float window under the cursor."""

    def __init__(self):
        ui.Window.__init__(self)
        self.AddFlag('float')
        self.AddFlag('not_pick')
        self.image = Image.Make(self, None, 0, 0)
        self.SetSize(28, 28)

    def Start(self, path, scale=1.0):
        Image.Set(self.image, path, 0, 0, scale, 0.85)
        size = int(round(28 * scale))
        self.SetSize(size, size)
        self.Show()
        self.SetTop()

    def Move(self, x, y):
        self.SetPosition(int(x) - self.GetWidth() // 2 + 6, int(y) - self.GetHeight() // 2 + 6)


class TourBox(Panel):
    """One step of the guide: "Krok n / 4 · title", text, four diamonds, Přeskočit and Další ›."""

    def __init__(self, kit, on_skip, on_next):
        Panel.__init__(self, kit)
        self.on_skip, self.on_next = on_skip, on_next
        bw = 116 if kit.prof == '1080' else 100
        self.skip = uikit.Button(self, kit, 0, 0, bw, '', role='secondary',
                                 event=lambda: self.on_skip and self.on_skip())
        self.next = uikit.Button(self, kit, 0, 0, bw + 8, '', role=AccentRole('ruby_s'),
                                  event=lambda: self.on_next and self.on_next())
        self.bullets = []

    def ShowStep(self, title, paragraphs, step, count, skip_text, next_text, position):
        self._Clear()
        k = self.kit
        w = 380 if k.prof == '1080' else 300
        pad = 14 if k.prof == '1080' else 10
        y = pad
        self._Text(title, pad, y, 'Mb', T.GOLD_HI)
        y += k.cell('Mb') + 10
        for paragraph in paragraphs:
            lines, y = uikit.Wrap(self, paragraph, pad, y, w - 2 * pad, k.font('S'), T.INK_DIM, k.cell('S') + 4)
            self.items.extend(lines)
            y += 8
        y += 4
        self.skip.SetText(skip_text)
        self.next.SetText(next_text)
        self.skip.SetPosition(pad, y)
        self.next.SetPosition(w - pad - self.next.w, y + (self.skip.h - self.next.h) // 2)
        for bullet in self.bullets:
            bullet.Hide()
        self.bullets = []
        bs = k.size('bullet/diamond_normal.png')
        x0 = w // 2 - (count * 16) // 2
        for index in range(count):
            state = 'selected' if index == step else 'normal'
            self.bullets.append(uikit.Image(self, k.rel('bullet/diamond_%s.png' % state), x0 + index * 16,
                                            y + self.skip.h // 2 - bs[1] // 2))
        h = y + self.skip.h + pad
        self._Frame(w, h)
        sw, sh = ScreenSize()
        self.SetPosition(max(0, min(int(position[0]), sw - w)), max(0, min(int(position[1]), sh - h)))
        self.Show()
        self.SetTop()

    def Destroy(self):
        self.on_skip = self.on_next = None
        self.Hide()
