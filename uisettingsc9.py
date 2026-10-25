# -*- coding: utf-8 -*-
"""Settings window v5 (2026-10-05; c9 v4 reworked after the owner's play test; design and
decisions in docs/SETTINGS_KIT_LOOK.md).

GameOptionWindow() returns a host that keeps ONE of two windows and forwards every call to it:
  C9SettingsWindow      new look (default): one outer frame and the title bar, NO frames inside (the sidebar is one
                        shade different and a hairline separates it), content over the whole width down to the
                        footer, the description of a row as a kit tooltip on hover (v5 fix 2026-10-05: the strip under
                        the content is gone, owner: "nesedí tam, jen tak plave"), Obnovit stránku (confirmation names
                        what returns) / Starý vzhled / Zavřít. Only Panely tlačítek keeps a right column (preview).
                        Spectral only (Tahoma just as the automatic fallback of an old EXE, uikit.FontSet).
  LegacySettingsWindow  the original A7 window plus a "Nový vzhled" button (comparison)
The choice and the option icons live in UserData/settings-look.json (settingslook); switching rebuilds the window.

C9SettingsWindow subclasses the A7 window (uisettings.GameOptionWindow): session, change(), Apply(), the search index,
popups, panels and the stone queue are the A7 code. Window size by screen height: 1160 x 780 from 900 px up,
otherwise 840 x 620. Panely tlačítek and Fronta kamenů keep their A7 look inside the new frame (other workstreams);
Klávesové zkratky has its own renderer (uisettingsc9keys).
"""
import settingsc9pages as c9pages
import settingschat
import settingslook
import settingsmodel
import settingspages as pages
import ui
import wndMgr
import uikit
import uikittokens as T
import uisettings as a7
from settingslocale import Text as Tr
from uisettingsc9reset import C9Reset
from uisettingsc9rows import C9Rows

CHANNEL_BAR_STYLE = 'channel_bar_style'   # settingslook: the R1 channel bar, 'stepper' / 'list' (Vzhled page)


def ChannelBarFollowLook(interface=None):
    """An open channel bar takes the look / style just stored (uichannelbar.StyleChanged); never breaks Settings."""
    try:
        import uichannelbar
        return uichannelbar.StyleChanged(interface)
    except Exception:
        import dbg
        import traceback
        dbg.TraceError('channel bar look: %s' % traceback.format_exc())
        return False


def WindowsFollowLook():
    """Every live window takes the look just stored (uir1.LookChanged: the interface built at the login - tooltips,
    inventory, character, taskbar, minimap, chat ... - in both directions, R1 -> Starý vzhled -> R1); never breaks
    Settings."""
    try:
        import uir1
        return uir1.LookChanged()
    except Exception:
        import dbg
        import traceback
        dbg.TraceError('look switch: %s' % traceback.format_exc())
        return 0


Base = a7.GameOptionWindow
# Pages with their own renderer (settingsc9pages: custom=<id>): id -> (module, class), imported on first use. The
# class is constructed with the window and implements Build(width) -> content height (rows into window.content,
# window.c9_rows for the row tooltip), Clear(), OnUpdate(), Destroy(); optionally ResetText() and RestoreDefaults() (the
# confirmed "Obnovit stránku") or AskReset() (the page asks itself), OnPressEscapeKey() -> True when it closed
# a popup of its own, SearchIndex() -> [(page, key, label)] and FillSide(x, y, w, h) for a page with a right
# column (side=...; a custom page gets the column in both profiles), SideLayout() -> (width, caption) for its own
# column width and a small caption instead of the column heading (Panely tlačítek P1, 2026-10-06: the preview
# over the whole height, no heading). Panely tlačítek and Fronta kamenů hook in here.
CUSTOM_VIEWS = {'keys': ('uisettingsc9keys', 'KeysView'), 'panels': ('uisettingspanelsv5', 'PanelsPage'),
                'queue': ('uisettingsmeteorpage', 'MeteorQueueView')}


class NavItem(uikit.Interactive):
    """Sidebar group or page: hover band, click opens a page."""

    def __init__(self, parent, x, y, w, h, event, selected=False):
        uikit.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetPosition(int(x), int(y))
        self.SetSize(int(w), int(h))
        self.selected = selected
        self.band = uikit.Band(self, 0, 0, w, h, 'hover')
        self.band.Hide()
        self.callback = event
        self.Show()

    def paint(self):
        self.band.Show() if self.hovered and not self.selected else self.band.Hide()


class C9SettingsWindow(C9Rows, C9Reset, Base):
    def __init__(self, host=None):
        # ui.Window.__init__ (inside the A7 constructor) dispatches Hide() and _BuildShell(): set state first.
        self.host = host
        look = settingslook.Load()
        self.kit = uikit.Kit(uikit.Profile(), uikit.FontSet())
        self.c9_icons = bool(look['row_icons'])
        self.WIDTH, self.HEIGHT = self._CanvasWindowSize()
        self.legacy_mode = False
        self.c9_page = c9pages.DEFAULT_PAGE
        self.c9_items, self.c9_rows, self.c9_nav = [], [], []
        self.c9_info_row = None
        self.searching = False
        self.c9_has_custom = self.c9_custom_shown = False
        self.c9_rendering = False
        self.c9_list = self.c9_confirm = self.c9_tip = None
        self.c9_tip_pending = self.c9_tip_owner = None
        self.c9_index = []
        self.c9_side_lines = []
        self.c9_views = {}
        self.c9_view_active = None
        self.c9_chat = settingschat.ChatOptions(self._C9Interface)
        self._C9Geometry()
        Base.__init__(self)
        self._C9BuildIndex()

    def _CanvasWindowSize(self):
        width, height = self.kit.p('window')
        return (min(width, max(800, wndMgr.GetScreenWidth()) - 16),
                min(height, max(600, wndMgr.GetScreenHeight()) - 16))

    def _C9Interface(self):
        backend = getattr(self, 'backend', None)
        return backend.interface() if backend else None

    def _C9CustomView(self, name):
        """The custom view of a page, built once; None (traced) when it cannot be built - the page then shows one
        line pointing to the old look instead of breaking the window."""
        if name not in self.c9_views:
            module, cls = CUSTOM_VIEWS[name]
            try:
                self.c9_views[name] = getattr(__import__(module), cls)(self)
            except Exception:
                import dbg
                import traceback
                dbg.TraceError('settings kit page %s: %s' % (name, traceback.format_exc()))
                self.c9_views[name] = None
        return self.c9_views[name]

    def _C9Unavailable(self, width):
        if c9pages.LegacyToggle():
            note = Tr('Tuto stránku se nepodařilo načíst. Zkus Starý vzhled.', 'This page could not be loaded. Try the '
                      'old look.')
        else:                   # no "Starý vzhled" for players (settingslook.ALLOW_LEGACY_TOGGLE)
            note = Tr('Tuto stránku se nepodařilo načíst.', 'This page could not be loaded.')
        self._C9Text(note, 0, 4, 'M', T.MUTED, valign='top')
        return self.kit.cell('M') + 8

    @property
    def c9_keys(self):
        return self._C9CustomView('keys')

    # ------------------------------------------------------------------ geometry and shell
    def _C9Geometry(self):
        k = self.kit
        W, H = self.WIDTH, self.HEIGHT
        big = k.prof == '1080'
        m = k.p('margin')
        self.c9_bar = k.bar('window')
        bar_bottom = 5 + uikit.TitleBarHeight(k, 'window')   # the R1 header in the R1 skin (27 px)
        top = bar_bottom + (14 if big else 10)
        bot = H - k.p('bottom_h')
        sbw, iw, gap = k.p('sidebar_w'), k.p('info_w'), (20 if big else 14)
        sep = m + sbw
        cx0, cx1 = sep + 1 + gap, W - m
        side_x0 = cx1 - iw
        side_sep = side_x0 - gap
        cell = k.cell('L')
        hy = top + cell // 2
        divider_y = hy + cell // 2 + (8 if big else 6)
        rows_top = divider_y + k.size('divider_center.png')[1] + (14 if big else 10)
        # The content runs down to the footer (no description strip any more): the bottom room the strip took
        # (2 lines + padding) goes to the rows, so pages like Stíny a efekty fit without a scrollbar.
        self.c9 = dict(m=m, top=top, bot=bot, bar_bottom=bar_bottom, sbw=sbw, sep=sep, gap=gap, cx0=cx0, cx1=cx1,
                       iw=iw, side_x0=side_x0, side_sep=side_sep, hy=hy, divider_y=divider_y, rows_top=rows_top,
                       inset=6)
        self.c9_view = self._C9View(cx1)
        self.c9_view_side = self._C9View(side_sep - gap)
        # Panely tlačítek keeps a preview column; its A7 page (352 px + scrollbar) needs the room - when the content
        # beside the column is narrower (profile 768), the page takes the column's place (no preview column).
        self.c9_side_fits = side_sep - gap - cx0 >= 352 + 22
        self.VIEW_TOP, self.VIEW_HEIGHT = self.c9_view['y'], self.c9_view['h']

    def _C9View(self, right):
        g = self.c9
        y = g['rows_top']
        return dict(x=g['cx0'], y=y, w=right - g['cx0'], h=g['bot'] - (10 if self.kit.prof == '1080' else 8) - y)

    def _C9LegacyView(self, view):
        return dict(x=view['x'] + (view['w'] - 352 - 22) // 2, y=view['y'], w=352, h=view['h'])

    def _BuildShell(self):
        for name in ('Corners', 'Lines'):
            for widget in getattr(self, name, None) or ():
                widget.Hide()
        for name in ('Base', 'titleBar'):
            widget = getattr(self, name, None)
            if widget:
                widget.Hide()
        k, g = self.kit, self.c9
        W, H = self.WIDTH, self.HEIGHT
        keep = self.permanent.append
        inset = g['inset']
        keep(uikit.Frame(self, k, 'window', 0, 0, W, H, bg=True))
        # One shade lighter sidebar and a hairline: the only separation inside the window (owner v5: no frames).
        keep(uikit.Rect(self, inset, g['bar_bottom'], g['sep'] - inset, g['bot'] - g['bar_bottom'], T.PANEL_HI, .55))
        keep(uikit.Rect(self, g['sep'], g['bar_bottom'], 1, g['bot'] - g['bar_bottom'], T.BRONZE_LINE_DK, .9))
        self.c9_titlebar = uikit.TitleBar(self, k, 5, 5, W - 10, Tr('Nastavení', 'Settings'), kind='window',
                                          on_close=self.Hide)
        keep(self.c9_titlebar)
        self.heading = uikit.Text(self, '', g['cx0'], g['hy'], k.font('L'), T.GOLD_HI, outline=not uikit.R1())
        keep(self.heading)
        self.c9_divider = uikit.Divider(self, k, g['cx0'], g['divider_y'], self.c9_view['w'])
        keep(self.c9_divider)
        self._C9BuildSide()
        v = self.c9_view
        self.viewport = self._keep(ui.Window(), v['x'], v['y'], permanent=True)
        self.viewport.SetSize(v['w'], v['h'])
        self.viewport.EnableScissorRect()
        self.viewport.OnMouseWheel = self.OnMouseWheel
        self.content = self._keep(ui.Window(), 0, 0, parent=self.viewport, permanent=True)
        self.content.SetSize(v['w'], v['h'])
        self.content.OnMouseWheel = self.OnMouseWheel
        self.c9_view_w = v['w']
        scrollbar = uikit.ScrollBar(k)
        self.scrollbar = self._keep(scrollbar, v['x'] + v['w'] - scrollbar.Width(), v['y'], permanent=True)
        self.scrollbar.SetScrollBarSize(v['h'])
        self.scrollbar.SetScrollEvent(self._OnScroll)
        self.scrollbar.OnMouseWheel = self.OnMouseWheel
        self.scrollbar.middleBar.OnMouseWheel = self.OnMouseWheel
        self.scrollbar.Hide()
        self._C9BuildFooter()
        self._C9BuildSearch()
        self.nav_buttons, self.category_buttons = {}, {}

    def _C9BuildSide(self):
        """Right column of Panely tlačítek ("Náhled ve hře"): hairline, heading and divider; the page fills it."""
        k, g = self.kit, self.c9
        self.c9_side_rule = uikit.Rect(self, g['side_sep'], g['top'] - 4, 1, g['bot'] - g['top'] + 4,
                                       T.BRONZE_LINE_DK, .9)
        self.c9_side_heading = uikit.Text(self, '', g['side_x0'], g['hy'], k.font('L'), T.GOLD_HI,
                                          outline=not uikit.R1())
        self.c9_side_divider = uikit.Divider(self, k, g['side_x0'], g['divider_y'], g['cx1'] - g['side_x0'])
        self.c9_side_box = (g['side_x0'], g['rows_top'], g['cx1'] - g['side_x0'], g['bot'] - 8 - g['rows_top'])
        # Small muted caption of a compact column (SideLayout: Panely tlačítek P1) instead of heading + divider.
        self.c9_side_caption = uikit.Text(self, '', g['side_x0'], g['top'] + 2, k.font('S'), T.MUTED, valign='top')
        for widget in (self.c9_side_rule, self.c9_side_heading, self.c9_side_divider, self.c9_side_caption):
            self.permanent.append(widget)
            widget.Hide()

    def _C9BuildFooter(self):
        k, g = self.kit, self.c9
        W, H, m, bot = self.WIDTH, self.HEIGHT, g['m'], g['bot']
        keep = self.permanent.append
        keep(uikit.HLine(self, g['inset'], bot, W - 2 * g['inset'], T.BRONZE_LINE_DK))
        # One button family (2026-10-06): the three footer buttons are the same height and frame - Zavřít is
        # the one primary action of the window, Obnovit stránku and Starý vzhled are secondary (no spikes, no plate).
        bh = uikit.ButtonHeight(k, 'bar')
        by = bot + (H - bot - bh) // 2
        self.reset_button = uikit.Button(self, k, m + 4, by, 0, Tr('Obnovit stránku', 'Reset page'),
                                         role='secondary', icon='reset', event=self._C9AskReset, size='bar')
        self.reset_button.FitWidth(176 if k.prof == '1080' else 144)
        self.reset_button.SetHoverEvent(self._C9ShowResetInfo)
        cw = k.p('close_btn')[0]
        self.close_button = uikit.Button(self, k, W - m - 4 - cw, by, cw, Tr('Zavřít', 'Close'), role='primary',
                                         event=self.Hide, size='bar')
        for widget in (self.reset_button, self.close_button):
            keep(widget)
        self.c9_footer_old = None
        if not c9pages.LegacyToggle():
            return              # owner 9. 10. 2026 ("zatím"): players have no "Starý vzhled" switch
        # Comparison switch of the trial (kept on the owner's request): the original A7 window.
        old = uikit.Button(self, k, 0, by, 0, Tr('Starý vzhled', 'Old look'), role='secondary',
                           event=lambda: self._C9SetOldLook(True), size='bar')
        old.FitWidth(120 if k.prof == '1080' else 100)
        old.SetPosition(m + 4 + self.reset_button.w + 12, by)
        self.c9_footer_old = old
        keep(old)

    def _C9BuildSearch(self):
        k, g = self.kit, self.c9
        x, y, w = g['m'], g['top'] - 2, g['sbw'] - 12
        self.search = a7.Search(self)
        # The kit's one search field (2026-10-06): placeholder in the row font, centred; a small clear cross.
        field = uikit.SearchField(self, k, x, y, w, hint=Tr('Hledat...', 'Search…'), edit=self.search, max_len=40,
                                  on_clear=self._C9ClearSearch)
        self.search.Show()
        self.c9_search_field = field
        self.permanent.append(field)
        self.c9_nav_top = y + field.h + (12 if k.prof == '1080' else 8)

    def _C9ClearSearch(self):
        self.SearchOptions()        # an empty query renders the current page again
        self.search.SetFocus()

    def _C9BuildIndex(self):
        seen, index = set(), []

        def add(page, key, label):
            if page and label and (page, key, label) not in seen:
                seen.add((page, key, label))
                index.append((page, key, label))
        for page in c9pages.ORDER:
            add(page, None, c9pages.PAGES[page]['label'])
        for page in ('chat',):
            add(page, 'font', c9pages.RELABEL['font'])
        for a7_page, key, label in self.search_index:
            add(c9pages.owner(a7_page, None if key == a7_page else key), None if key == a7_page else key, label)
        for page in c9pages.ORDER:
            for item in c9pages.items(page):
                add(page, item.get('key'), item.get('label'))
        for page, key, label in c9pages.SEARCH_EXTRA:
            add(page, key, label)
        self.c9_index = index

    # ------------------------------------------------------------------ navigation and rendering
    def open_page(self, page):
        target = c9pages.resolve(page)
        if target is None:
            return
        page, highlight = target
        if highlight:
            self.highlight = highlight
        if self.session is None:
            self.session = settingsmodel.Session(self.backend)
        elif not self.Apply():
            return
        self._SaveScroll()
        self.c9_page = page
        self.searching = False
        self.search.KillFocus()
        self._Render()

    def _C9Open(self, page):
        self.open_page(page)

    def _SaveScroll(self):
        if getattr(self, 'rendered_page', None) and not self.searching and hasattr(self, 'content'):
            self.scroll_offsets[self.rendered_page] = max(0, -self.content.GetLocalPosition()[1])

    def _C9Side(self):
        """The right column is shown only on a page that declares one (Panely tlačítek) and when it fits."""
        spec = c9pages.PAGES.get(self.c9_page, {})
        fits = self.c9_side_fits or bool(spec.get('custom'))  # a custom page is laid out for the column width
        return bool(spec.get('side')) and fits and not self.searching

    def _C9SideLayout(self):
        """(width, caption) the custom view of the page asks for (SideLayout), or (None, None) = the shell column."""
        spec = c9pages.PAGES.get(self.c9_page, {})
        view = self._C9CustomView(spec['custom']) if spec.get('custom') else None
        if view is not None and hasattr(view, 'SideLayout'):
            width, caption = view.SideLayout()
            return (int(width) if width else None), caption
        return None, None

    def _C9Columns(self, legacy):
        side = self._C9Side()
        g, k = self.c9, self.kit
        side_w, caption = self._C9SideLayout() if side else (None, None)
        compact = side and caption is not None
        if side and side_w:
            side_x0 = g['cx1'] - side_w
            side_sep = side_x0 - g['gap']
            view = self._C9View(side_sep - g['gap'])
        else:
            side_x0, side_sep = g['side_x0'], g['side_sep']
            view = self.c9_view_side if side else self.c9_view
        self.c9_side_rule.SetPosition(side_sep, g['top'] - 4)
        self.c9_side_rule.Show() if side else self.c9_side_rule.Hide()
        for widget in (self.c9_side_heading, self.c9_side_divider):
            widget.Show() if side and not compact else widget.Hide()
        self.c9_side_heading.SetPosition(side_x0, g['hy'])
        self.c9_side_divider.SetPosition(side_x0, g['divider_y'])
        self.c9_side_divider.Apply(uikit.L.divider(k.prof, g['cx1'] - side_x0))
        self.c9_side_divider.SetSize(g['cx1'] - side_x0, self.c9_side_divider.GetHeight())
        if compact:
            self.c9_side_caption.SetText(caption)
            self.c9_side_caption.SetPosition(side_x0, g['top'] + 2)
            self.c9_side_caption.Show()
            top = g['top'] + 2 + k.cell('S') + 8
        else:
            self.c9_side_caption.Hide()
            top = g['rows_top']
        self.c9_side_box = (side_x0, top, g['cx1'] - side_x0, g['bot'] - 8 - top)
        for line in self.c9_side_lines:
            line.Hide()
        self.c9_side_lines = []
        if side:
            self._C9FillSide()
        self.c9_divider.Apply(uikit.L.divider(self.kit.prof, view['w']))
        self.c9_divider.SetSize(view['w'], self.c9_divider.GetHeight())
        v = self._C9LegacyView(view) if legacy else view
        self.c9_current_view = v
        self.VIEW_TOP, self.VIEW_HEIGHT = v['y'], v['h']
        self.viewport.SetPosition(v['x'], v['y'])
        self.viewport.SetSize(v['w'], v['h'])
        self.c9_view_w = v['w']
        sw = self.scrollbar.Width()
        self.scrollbar.SetPosition(v['x'] + v['w'] + 6 if legacy else v['x'] + v['w'] - sw, v['y'])
        self.scrollbar.SetScrollBarSize(v['h'])
        self.heading.SetPosition(g['cx0'], g['hy'])

    def _C9FillSide(self):
        """The right column: a custom view with FillSide() draws it (the Panely tlačítek preview); otherwise a
        placeholder with the page description and the badge legend."""
        k = self.kit
        spec = c9pages.PAGES[self.c9_page]
        self.c9_side_heading.SetText(spec['side'])
        x, y, w, h = self.c9_side_box
        view = self._C9CustomView(spec['custom']) if spec.get('custom') else None
        if view is not None and hasattr(view, 'FillSide'):
            view.FillSide(x, y, w, h)
            return
        lines, y = uikit.Wrap(self, c9pages.text(self.c9_page), x, y, w, k.font('M'), T.INK_DIM, k.cell('M') + 4)
        self.c9_side_lines.extend(lines)
        if spec.get('legend'):
            y += 12
            self.c9_side_lines.append(uikit.Section(self, k, x, y, w, Tr('Legenda', 'Legend')))
            y += k.cell('Sb') + 14
            for entry in spec['legend']:
                self.c9_side_lines.append(uikit.Text(self, entry, x, y, k.font('S'), T.INK_DIM, valign='top'))
                y += k.cell('S') + 6

    def _Render(self):
        if self.c9_rendering:
            return
        self.c9_rendering = True
        try:
            self._C9Render()
        finally:
            self.c9_rendering = False

    def _C9Render(self):
        spec = c9pages.PAGES[self.c9_page]
        self.page = c9pages.primary(self.c9_page)
        self.children['optionType'], self.children['categoryType'] = pages.PAGES[self.page][:2]
        self._C9RenderNav()
        self.reset_button.Enable()
        if spec.get('legacy'):
            self.legacy_mode = True
            self.searching = False
            self._C9Columns(True)
            Base._Render(self)
            self.rendered_page = self.c9_page
            self.heading.SetText(spec['label'])
            self.c9_info_row = None
            self._C9ShowInfo(None)
            return
        self._ClearPage()
        self.legacy_mode = False
        self.searching = False
        self._C9Columns(False)
        self.rendered_page = self.c9_page
        self.heading.SetText(spec['label'])
        width = self.c9_current_view['w']
        if spec.get('custom'):
            view = self._C9CustomView(spec['custom'])
            self.c9_view_active = view
            build = view.Build if view is not None else self._C9Unavailable
        else:
            items = self._C9Collect(self.c9_page)
            build = lambda w: self._C9Layout(items, w)
        view_h = self.c9_current_view['h']
        height = build(width)
        if height > view_h:
            self._ClearPage()
            if spec.get('custom'):
                self.c9_view_active = view  # _ClearPage() forgets it; the second pass is the same page
            height = build(width - self.scrollbar.Width() - 8)
        # A scrollbar only when the rows really overflow: the 8 px bottom margin is added to an overflowing page
        # only (it used to turn a page 1..8 px shorter than the view into a scrolling one).
        self.content_height = height + 8 if height > view_h else view_h
        self._Refresh()
        offset = self.scroll_offsets.get(self.c9_page, 0)
        info = None
        if self.highlight:
            for row in self.c9_rows:
                if row['key'] == self.highlight:
                    if row.get('label_line'):
                        row['label_line'].SetPackedFontColor(T.GOLD_HI)
                    row['band'].Show()
                    row['marked'] = True
                    offset, info = max(0, row['y'] - 12), row
                    break
            self.highlight = None
        if not self._C9ResetText():
            self.reset_button.Disable()  # e.g. Souboje a soukromí: the server owns PvP mode and request blocks
        self._C9ShowInfo(info)
        self._LayoutScroll(offset)

    def _C9RenderNav(self):
        for widget in self.c9_nav:
            widget.Hide()
        self.c9_nav = []
        k, g = self.kit, self.c9
        x, w = g['m'] + 6, g['sbw'] - 18
        gp, sp, isz = k.p('group_pitch'), k.p('sub_pitch'), k.p('icon_side')
        current = self.c9_page
        active = c9pages.group_of(current)[0]
        yy = self.c9_nav_top
        add = self.c9_nav.append
        for group, label, icon, group_pages in c9pages.GROUPS:
            open_ = group == active
            single = len(group_pages) == 1
            selected = open_ and single
            if selected:
                add(uikit.Band(self, x - 6, yy + 2, w + 6, gp - 4, 'selected'))
            add(NavItem(self, x - 6, yy, w + 6, gp, lambda page=group_pages[0]: self._C9Open(page), selected))
            add(uikit.Icon(self, icon, isz, x + 8, yy + (gp - isz) // 2, 'active' if open_ else 'normal'))
            add(uikit.Text(self, k.group_text(label), x + isz + 22, yy + gp // 2, k.group_font(),
                           T.GOLD_HI if open_ else T.GOLD, outline=not uikit.R1()))
            chevron = k.rel('chevron/%s_%s.png' % ('down' if open_ and not single else 'right',
                                                  'active' if open_ else 'normal'))
            cs = uikit.L.size(chevron)
            add(uikit.Image(self, chevron, x + w - 20, yy + (gp - cs[1]) // 2))
            yy += gp
            if open_ and not single:
                for page in group_pages:
                    sel = page == current
                    if sel:
                        add(uikit.Band(self, x - 6, yy, w + 6, sp, 'selected'))
                    add(NavItem(self, x - 6, yy, w + 6, sp, lambda page=page: self._C9Open(page), sel))
                    bullet = k.rel('bullet/diamond_%s.png' % ('selected' if sel else 'normal'))
                    bs = uikit.L.size(bullet)
                    add(uikit.Image(self, bullet, x + isz + 2, yy + (sp - bs[1]) // 2))
                    add(uikit.Text(self, c9pages.PAGES[page]['label'], x + isz + 22, yy + sp // 2, k.font('M'),
                                   T.INK if sel else T.INK_DIM))
                    yy += sp
                yy += 6
            add(uikit.HLine(self, x + 4, yy, w - 8, T.BRONZE_LINE_DK, .7))
            yy += 3
        self.c9_nav_bottom = yy

    def _ClearPage(self):
        Base._ClearPage(self)
        if self.c9_list:
            self.c9_list.Close()
        for view in [v for v in self.c9_views.values() if v is not None]:
            view.Clear()
        self.c9_view_active = None
        self.c9_rows = []
        self.c9_info_row = None
        self._C9HideTip()

    def _LayoutScroll(self, offset=0):
        self.content_height = max(self.VIEW_HEIGHT, self.content_height)
        self.content.SetSize(self.c9_view_w, self.content_height)
        overflow = self.content_height - self.VIEW_HEIGHT
        self.scroll_syncing = True
        try:
            self.scrollbar.SetMiddleBarSize(float(self.VIEW_HEIGHT) / self.content_height)
            self.scrollbar.SetScrollStep(min(1., 40. / max(1, overflow)))
            offset = max(0, min(int(offset), overflow))
            self.scrollbar.SetPos(float(offset) / max(1, overflow))
            self.content.SetPosition(0, -offset)
            self.scrollbar.Show() if overflow else self.scrollbar.Hide()
        finally:
            self.scroll_syncing = False
        if self.queue_page and self.page == 'queue' and not self.searching:
            self.queue_page.Scrolled(offset, self.VIEW_HEIGHT)

    def _Refresh(self):
        Base._Refresh(self)
        if not self.legacy_mode:
            self._C9RefreshControls()

    def _RefreshCustomColors(self):
        if self.legacy_mode:
            return Base._RefreshCustomColors(self)
        visible = self.custom_expanded or self.highlight in dict(pages.CUSTOM_COLORS)
        self.custom_expanded = visible
        if self.c9_has_custom and visible != self.c9_custom_shown and not self.c9_rendering and not self.searching:
            offset = max(0, -self.content.GetLocalPosition()[1])
            self._Render()
            self._LayoutScroll(offset)

    def value(self, key):
        # Look switches and chat options are not session values; the A7 refresh asks every control.
        if key == 'row_icons':
            return int(self.c9_icons)
        if key in ('look_old', 'reset_all', 'name_actions'):
            return 0
        if key == CHANNEL_BAR_STYLE:
            return settingslook.Get(key)
        if settingschat.owns(key):
            return self.c9_chat.get(key)
        return Base.value(self, key)

    def change(self, key, value, continuous=False):
        if key == CHANNEL_BAR_STYLE:
            self._C9SetChannelBarStyle(value)
            return
        if settingschat.owns(key):
            self.c9_chat.set(key, value)
            self._Refresh()
            return
        Base.change(self, key, value, continuous)

    def _C9SetChannelBarStyle(self, value):
        """Lišta kanálů: stored at once (settingslook) and an open channel bar is rebuilt in the new style."""
        if value not in settingslook.CHOICES[CHANNEL_BAR_STYLE]:
            return
        settingslook.Set(CHANNEL_BAR_STYLE, value)
        ChannelBarFollowLook(self._C9Interface())
        self._Refresh()

    def OnMouseWheel(self, delta):
        if self.scrollbar.IsShow() and delta:
            self.scrollbar.OnUp() if delta > 0 else self.scrollbar.OnDown()
            return True
        return False

    def Apply(self):
        saved = Base.Apply(self)
        if saved:
            self.c9_resize_blocked = False
        return saved

    def OnUpdate(self):
        # Rebuild outside native resize traversal, retaining the autosave session
        # on failure. Existing kit profiles keep text and controls at native size.
        if self.host and self.IsShow() and not getattr(self, 'c9_resize_blocked', False) and (self.kit.prof != uikit.Profile() or
                (self.WIDTH, self.HEIGHT) != self._CanvasWindowSize()):
            if self.Apply():
                self.host.Rebuild(self.c9_page)
                return
            self.c9_resize_blocked = True
        Base.OnUpdate(self)
        import app
        import settingsbackend
        for control in self.controls:
            if control['kind'] == 'c9_ui_scale' and app.GetTime() >= control['refresh_at']:
                control['refresh_at'] = app.GetTime() + .25
                self._RefreshUIScaleStatus(control, settingsbackend.ui_scale_info())
        for view in [v for v in self.c9_views.values() if v is not None]:
            view.OnUpdate()
        self._C9TipTick()

    # ------------------------------------------------------------------ search
    def SearchOptions(self):
        if not self.session:
            return
        query = settingsmodel.search_text(self.search.GetText().strip())
        self._SaveScroll()
        if not query:
            self._Render()
            return
        self._ClearPage()
        self.legacy_mode = False
        self.searching = True
        self._C9Columns(False)
        self.search.SetFocus()
        self.heading.SetText(Tr('Výsledky hledání', 'Search results'))
        index = list(self.c9_index)
        for name in CUSTOM_VIEWS:
            view = self._C9CustomView(name)
            if hasattr(view, 'SearchIndex'):
                index.extend(view.SearchIndex())
        results = [row for row in index if query in settingsmodel.search_text(row[2])]
        k = self.kit
        width, pitch = self.c9_current_view['w'], k.p('pitch')
        self._C9Text(Tr('Nalezeno: %d', 'Found: %d') % len(results), 0, 4, 'S', T.MUTED, valign='top')
        y = k.cell('S') + 14
        for page, key, label in results:
            group = c9pages.group_of(page)
            path = '%s › %s' % (group[1], c9pages.PAGES[page]['label'])
            hit = self._C9Track(uikit.HitArea(self.content, 0, y, width, pitch))
            hit.SetEvent(lambda page=page, key=key: self._C9OpenResult(page, key))
            self._C9Text(label, 0, y + pitch // 2 - k.cell('S') // 2 - 1, 'M', T.INK)
            self._C9Text(path, 0, y + pitch // 2 + k.cell('M') // 2 + 1, 'S', T.MUTED)
            chevron = k.rel('chevron/right_normal.png')
            cs = uikit.L.size(chevron)
            self._C9Track(uikit.Image(self.content, chevron, width - cs[0] - 4, y + (pitch - cs[1]) // 2), wheel=False)
            self._C9Track(uikit.HLine(self.content, 0, y + pitch - 1, width, T.ROW_LINE), wheel=False)
            y += pitch
        self.content_height = y + 8
        self._C9ShowInfo(None)
        self._LayoutScroll(0)

    def _C9OpenResult(self, page, key):
        self.highlight = key
        self.searching = False
        self.open_page(page)

    # ------------------------------------------------------------------ look switches
    def _C9SetIcons(self, on):
        on = bool(on)
        if on == self.c9_icons:
            return
        settingslook.Set('row_icons', on)
        self.c9_icons = on
        offset = max(0, -self.content.GetLocalPosition()[1])
        self._Render()
        self._LayoutScroll(offset)

    def _C9SetOldLook(self, on):
        if not on or not c9pages.LegacyToggle():
            return
        settingslook.Set('look', 'legacy')
        ChannelBarFollowLook()
        WindowsFollowLook()
        self._C9Rebuild(c9pages.primary(self.c9_page))

    def _C9Rebuild(self, page=None):
        if self.host:
            self.host.Rebuild(page or self.c9_page)

    # ------------------------------------------------------------------ lifecycle
    def _C9ClosePopups(self):
        self._C9HideTip()
        if getattr(self, 'c9_list', None):
            self.c9_list.Close()
        for name in ('c9_confirm', 'c9_confirm_wide'):
            dialog = getattr(self, name, None)
            if dialog and dialog.IsShow():
                dialog.Close()

    def Hide(self):
        self._C9ClosePopups()
        Base.Hide(self)

    def OnPressEscapeKey(self):
        view = self.c9_view_active
        if view is not None and hasattr(view, 'OnPressEscapeKey') and view.OnPressEscapeKey():
            return True  # a popup of the custom page (e.g. the panels picker) closes first
        for name in ('c9_confirm', 'c9_confirm_wide'):
            dialog = getattr(self, name, None)
            if dialog and dialog.IsShow():
                dialog.Cancel()
                return True
        if self.c9_list and self.c9_list.IsShow():
            self.c9_list.Close()
            return True
        colour = self.damage_color_dialog
        if colour is not None and hasattr(colour, 'IsOpen') and colour.IsOpen():
            colour.Cancel()      # the R1 damage colour dialog (uisettingsc9color) closes first
            return True
        return Base.OnPressEscapeKey(self)

    def Destroy(self):
        self._C9ClosePopups()
        Base.Destroy(self)
        for widget in self.c9_nav + self.c9_side_lines:
            widget.Hide()
        self.c9_nav, self.c9_rows, self.c9_side_lines = [], [], []
        for view in [v for v in self.c9_views.values() if v is not None]:
            view.Destroy()
        self.c9_views, self.c9_view_active = {}, None
        for name in ('c9_list', 'c9_confirm', 'c9_confirm_wide', 'c9_tip'):
            widget = getattr(self, name, None)
            if widget:
                widget.Hide()
            setattr(self, name, None)
        self.c9_titlebar = self.c9_footer_old = self.c9_search_field = None
        self.host = None


class LegacySettingsWindow(Base):
    """The original A7 window with a "Nový vzhled" button back to the c9 window."""

    def __init__(self, host=None):
        self.host = host
        self.c9_button = None
        Base.__init__(self)

    def _BuildShell(self):
        Base._BuildShell(self)
        self.c9_button = a7._button(self, 240, 565, Tr('Nový vzhled', 'New look'), self._SwitchToC9, '88x21')
        self.c9_button.SetToolTipText(Tr('Zpět na nový vzhled Nastavení.', 'Back to the new settings look.'))
        self.permanent.append(self.c9_button)

    def _SwitchToC9(self):
        settingslook.Set('look', 'c9')
        ChannelBarFollowLook()
        WindowsFollowLook()
        if self.host:
            self.host.Rebuild(self.page)

    def Destroy(self):
        Base.Destroy(self)
        self.c9_button = None
        self.host = None


class SettingsWindowHost(object):
    """Holds the settings window of the chosen look; every other attribute goes to that window, so the
    system menu, warp restore, compact chat and OpenPage() callers keep working unchanged."""

    def __init__(self):
        self._window = None
        self._window = self._Create()

    def _Create(self):
        if settingslook.Get('look') == 'legacy':
            return LegacySettingsWindow(host=self)
        try:
            return C9SettingsWindow(host=self)
        except Exception:
            # Fail safe: a kit window that cannot be built (missing texture, older EXE API) never leaves the player
            # without settings. The R1 skin failed: the gold kit window for the rest of the session (traced);
            # otherwise the original window opens instead and the cause goes to syserr.
            if uikit.SkinFailed('settings kit look'):
                try:
                    return C9SettingsWindow(host=self)
                except Exception:
                    pass
            import dbg
            import traceback
            dbg.TraceError('settings kit look: %s' % traceback.format_exc())
            return LegacySettingsWindow(host=self)

    def __getattr__(self, name):
        window = self.__dict__.get('_window')
        if window is None:
            raise AttributeError(name)
        return getattr(window, name)

    @property
    def window(self):
        return self._window

    def Rebuild(self, page=None):
        old = self._window
        if not old.Apply():
            return old
        shown = old.IsShow()
        old.Hide()
        offsets = dict(old.scroll_offsets)
        query = old.search.GetText()
        old.Destroy()
        self._window = self._Create()
        self._window.scroll_offsets.update(offsets)
        if shown:
            self._window.Open()
            if page:
                self._window.open_page(page)
            if query:
                self._window.search.SetText(query)
                self._window.SearchOptions()
        return self._window

    def Destroy(self):
        if self._window is not None:
            self._window.Destroy()


def GameOptionWindow():
    return SettingsWindowHost()
