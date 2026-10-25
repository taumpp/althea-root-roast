"""Settings -> Panely tlačítek: one page, one tab per configurable button panel.

Tabs: "Minimapa" (``uisettingsminimappanel.MinimapPanelPage``) and "Inventář"
(``uisettingsinventorypanel.InventoryPanelPage``). A tab page implements ``Build(top)`` returning
the content height and ``RestoreDefaults()``; it stores its state in its own
section of ``UserData/button-panels.json`` through ``buttonpanelstore``.
A further panel registers its page factory in ``TABS``.
"""
import ui
import uicrimsoncontrols as crimson
import fontconfig
from settingslocale import Text as T

TAB_TOP, TAB_HEIGHT = 0, 31
CONTENT_TOP = 40


def _minimap_page(owner):
    from uisettingsminimappanel import MinimapPanelPage
    return MinimapPanelPage(owner)


def _inventory_page(owner):
    from uisettingsinventorypanel import InventoryPanelPage
    return InventoryPanelPage(owner)


# (key, label, page factory)
TABS = (
    ('minimap', T('Minimapa', 'Minimap'), _minimap_page),
    ('inventory', T('Inventář', 'Inventory'), _inventory_page),
)


class ButtonPanelsPage:
    def __init__(self, owner):
        self.owner = owner
        self.tab = TABS[0][0]
        self.pages = {}
        self.tab_buttons = {}
        self.badge_popup = None

    def Page(self, key=None):
        key = key or self.tab
        if key not in self.pages:
            factory = dict((k, f) for k, unused, f in TABS).get(key)
            self.pages[key] = factory(self.owner) if factory else None
        return self.pages[key]

    @property
    def minimap(self):
        return self.Page('minimap')

    def Build(self):
        v = self.owner
        self.tab_buttons = {}
        for index, (key, label, factory) in enumerate(TABS):
            button = v._keep(ui.Button(), index * 120, TAB_TOP)
            crimson.ApplyVisuals(button, '88x21')
            button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
            button.SetText(label)
            button.SetEvent(lambda selected=key: self.SelectTab(selected))
            self.tab_buttons[key] = button
            if key == self.tab:
                button.Down()
            else:
                button.SetUp()
        # Badges and states (owner 2026-10-04): one button, the switches open in a popup.
        badges_button = v._keep(ui.Button(), 352 - 88, TAB_TOP)
        crimson.ApplyVisuals(badges_button, '88x21')
        badges_button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
        badges_button.SetText(T('Odznaky...', 'Badges…'))
        badges_button.SetEvent(lambda button=badges_button: self.OpenBadgeSettings(button))
        v._bar(0, TAB_TOP + 26, 352, 1, (.25, .195, .17, 1))
        page = self.Page()
        if page is None:
            return v.VIEW_HEIGHT
        height = max(v.VIEW_HEIGHT, page.Build(CONTENT_TOP))
        import buttonpanelstore
        if buttonpanelstore.IsReadOnly() and hasattr(page, 'Status'):
            import buttonpanelsettings
            page.Status(buttonpanelsettings.StoreErrorText(buttonpanelstore.ERROR_NEWER))
        return height

    def OnUpdate(self):
        """Hover tooltips of the active tab (drawn on the settings window, never clipped)."""
        page = self.pages.get(self.tab)
        if page is not None and hasattr(page, 'OnUpdate'):
            page.OnUpdate()

    def OpenBadgeSettings(self, anchor=None):
        import uisettingsbuttonbadges
        import uibuttonpanelbadges
        if self.badge_popup is None:
            self.badge_popup = uisettingsbuttonbadges.BadgeSettingsPopup(on_change=self.BadgesChanged)
        if self.badge_popup.IsShow():
            self.badge_popup.Close()
            return
        (x, y) = anchor.GetGlobalPosition() if anchor is not None else (0, 0)
        self.badge_popup.Open((x + 88 + 6, y))

    def BadgesChanged(self):
        import uibuttonpanelbadges
        uibuttonpanelbadges.Invalidate()
        page = self.pages.get(self.tab)
        if page is not None and hasattr(page, 'Sync'):
            page.Sync()

    def SelectTab(self, key):
        if key == self.tab:
            return
        current = self.pages.get(self.tab)
        if current is not None and hasattr(current, 'Detach'):
            current.Detach()
        self.tab = key
        self.owner._Render()

    def Detach(self):
        for page in self.pages.values():
            if page is not None and hasattr(page, 'Detach'):
                page.Detach()
        if self.badge_popup is not None:
            self.badge_popup.Close()

    def Destroy(self):
        for page in self.pages.values():
            if page is not None and hasattr(page, 'Destroy'):
                page.Destroy()
        self.pages = {}
        if self.badge_popup is not None:
            self.badge_popup.Destroy()
        self.badge_popup = None

    def RestoreDefaults(self):
        page = self.Page()
        if page is not None:
            page.RestoreDefaults()
