# -*- coding: utf-8 -*-
"""Jezdecká zvířata (uimountsystem.MountSystemWindow, 500 x 500) in the R1 look ("Krvavá žíla",
docs/ALTHEA_R1_KIT.md), drawn INTO the original window.

* the R1 frame and header; the title follows the page (Systém mounta / Elementární výpravy) through the window's own
  SetTitleName; the hidden original title bar stays as an invisible drag handle (the window itself is not pickable,
  the title bar is what moves it);
* section headings as R1 sections (Noto Sans, a quiet hairline) instead of the K1 heading images; the code that
  renames a heading (the element detail) keeps working through the heading's ``label``;
* the K1 surfaces, the level badge, the dividers and the side switches in their original shapes, recoloured to
  graphite (tools/build_althea_r1_obchody.py); the selected side switch gets the red vein on its outer edge; the
  equipment slot frames (32 x 32) are the R1 item slot C (uir1.SLOT_CELL), the slot hints stay on them;
* soul orbs, the 3D preview, slot hints, element rows and every value keep today's art and colours;
* "Nakrmit" as the primary R1 button standing in for the original button (Enable / Disable / Show / Hide);
* Úkoly větve (page Živly): the heading as an R1 section, the task rows as R1 rows (root/uimountr1tasks.py: number,
  text, counter, the red vein progress, "Odevzdat" as an R1 button) and the bonus of the branch as the R1 vein; the
  window creates its rows through ``taskRowClass``, which the skin sets while it is applied.

Every original object and handler stays: nothing of the content is re-created or moved. Settings -> "Starý vzhled"
keeps the original window; a failure while building traces to syserr and keeps the original look.
"""
import ui

import uir1
import uir1obchodyart as A
import uir1tokens as T

ASSET_ROOT = 'd:/ymir work/ui/game/crimson_ember/mount_system/'
K1_ROOT = ASSET_ROOT + 'k1/'
# original texture -> R1 recoloured copy
RECOLOURED = dict((ASSET_ROOT + rel, A.ROOT + 'mount/' + rel.rsplit('/', 1)[-1]) for rel in (
    'k1/level_48x64.png', 'k1/divider_172x1.png', 'k1/divider_210x1.png',
    'k1/surface_200x272.png', 'k1/surface_218x57.png', 'k1/surface_242x411.png', 'k1/surface_260x272.png',
    'k1/surface_468x58.png'))
RECOLOURED[ASSET_ROOT + 'slot_item_32x32.png'] = uir1.SLOT_CELL     # the equipment slot frame: the R1 item slot C
SWITCH = A.ROOT + 'mount/switch_36x36_%s.png'
HEADER_PREFIX = K1_ROOT + 'header_'
HEADER_H = 28
FEED_W = 170
VEIN_W = 2
VEIN_INSET = 5
TASKS_SECTION = (258, 180, 210)         # Úkoly větve: the heading above the task list (page Živly)


def _Path(image):
    return getattr(image, 'name', None) or getattr(image, 'image_path', None)


def _Owned(window):
    return list(getattr(window, '_mountOwnedChildren', None) or ())


class PanelHeading(ui.Window):
    """Compact R1 heading of a mount panel (no long hairline after the text, the two columns stay quiet): the label
    in Noto Sans, aligned to its panel, and a short red vein under the label only. STYLE 'left' puts it on the
    panel's left edge, 'center' over the panel's middle. The label is a top-aligned line (uir1.CellTop) so its cell
    stays inside the heading. Not pickable."""

    STYLE = 'center'
    LABEL_H = 20            # the label's row inside the 28 px heading slot; the vein runs under it
    VEIN_PAD = 6            # the vein reaches this far past the label on each side ('center') / to the right ('left')

    def __init__(self, parent, kit, x, y, w, text):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.kit = kit
        self.w = int(w)
        self.SetPosition(int(x), int(y))
        self.SetSize(self.w, HEADER_H)
        font = kit.font('text_sb')
        self.vein = uir1.Vein(self, 0, self.LABEL_H + 1, 24)              # images before the label
        self.label = uir1.Text(self, '', 0, uir1.CellTop(self.LABEL_H, font), font, T.IVORY, valign='top')
        self.SetText(text)
        self.Show()

    def SetText(self, text):
        self.label.SetText(text)
        tw = uir1.TextWidth(self.label)
        vw = min(self.w, tw + 2 * self.VEIN_PAD)
        if self.STYLE == 'center':
            self.label.SetPosition((self.w - tw) // 2, self.label.GetLocalPosition()[1])
            vx = (self.w - vw) // 2
        else:
            self.label.SetPosition(2, self.label.GetLocalPosition()[1])
            vx = 0
        self.vein.SetPosition(vx, self.LABEL_H + 1 - T.VEIN_ROW)
        self.vein.SetWidth(vw)

    def GetText(self):
        return self.label.GetText()

    def Height(self):
        return HEADER_H


class HeadingLabel(object):
    """The ``label`` of a K1 heading while R1 shows it: SetText renames the R1 section and the hidden original."""

    def __init__(self, original, section):
        self.original, self.section = original, section

    def SetText(self, text):
        self.original.SetText(text)
        self.section.SetText(text)

    def GetText(self):
        return self.original.GetText()


class ButtonAdapter(object):
    """Stands in for the original "Nakrmit" button (the window enables / disables / shows it)."""

    def __init__(self, original, button):
        self.original, self.button = original, button

    def Enable(self):
        self.button.Enable()

    def Disable(self):
        self.button.Disable()

    def IsEnabled(self):
        return self.button.IsEnabled()

    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

    def IsShow(self):
        return self.button.IsShow()

    def SetEvent(self, event, *args):
        self.button.SetEvent((lambda: event(*args)) if args else event)

    def SetPosition(self, x, y):
        self.button.SetPosition(x, y)

    def GetLocalPosition(self):
        return self.button.GetLocalPosition()

    def SetText(self, text):
        self.button.SetText(text)

    def GetText(self):
        return self.button.GetText()


class MountSkin(object):
    """R1 into one MountSystemWindow (after its constructor built both pages and the side switches)."""

    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.swapped = []          # (image, original path)
        self.headings = []         # (k1 heading image, original label, R1 section)
        self.tabs = []             # (side switch, vein)
        self.feed = None
        self.tasks = None          # (original heading, original icon, original progress, R1 section, R1 gauge)
        self.title_bar = window.titleBar
        self.skin = uir1.BoardSkin(window, kit, window.titleName.GetText(), on_close=window.Close)
        uir1.Front(window, not_pick=True)     # 'not_pick': the engine never raises it on a click by itself
        try:
            self._DragHandle(True)
            window.body.Hide()
            for root in self._Roots():
                self._Skin(root)
            for tab in (window.mountSwitch, window.elementsSwitch):
                self._Tab(tab)
            self._Feed()
            self._Tasks()
            window.SetTitleName = self.SetTitleName
        except Exception:
            self.Restore()
            raise

    # ------------------------------------------------------------------ build
    def _Roots(self):
        window = self.window
        roots = [window.mountPage, window.elementsPage, getattr(window, 'coreInfo', None)]
        roots += list(getattr(window, 'equipmentSlots', {}).values())
        return [root for root in roots if root is not None]

    def _DragHandle(self, invisible):
        """The original title bar stays shown but draws nothing: the window is not pickable, the title bar's 'attach'
        is what moves it."""
        bar = self.title_bar
        parts = [getattr(bar, name, None) for name in ('imgLeft', 'imgCenter', 'imgRight', 'btnClose')]
        parts.append(self.window.titleName)
        for part in parts:
            if part is not None:
                part.Hide() if invisible else part.Show()
        bar.Show()

    def _Skin(self, root):
        for widget in _Owned(root):
            path = _Path(widget)
            if not path:
                continue
            if path.startswith(HEADER_PREFIX):
                self._Heading(root, widget)
            elif path in RECOLOURED:
                self.swapped.append((widget, path))
                widget.LoadImage(RECOLOURED[path])

    def _Heading(self, parent, image):
        label = getattr(image, 'label', None)
        text = label.GetText() if label is not None else ''
        x, y = image.GetLocalPosition()
        width = int(path_width(_Path(image)))
        section = PanelHeading(parent, self.kit, x, y, width, text)
        image.Hide()
        if label is not None:
            image.label = HeadingLabel(label, section)
        self.headings.append((image, label, section))

    def _Tab(self, tab):
        vein = uir1.Rect(tab, tab.GetWidth() - VEIN_W, VEIN_INSET, VEIN_W, tab.GetHeight() - 2 * VEIN_INSET, T.RED)
        vein.Hide()
        self.tabs.append((tab, vein))
        selected = bool(tab.IsDown()) if hasattr(tab, 'IsDown') else False

        def set_selected(on, tab=tab, vein=vein):
            for setter, state in ((tab.SetUpVisual, 'normal'), (tab.SetOverVisual, 'hover'),
                                  (tab.SetDownVisual, 'pressed')):
                setter(SWITCH % ('selected' if on else state))
            tab.SetDisableVisual(SWITCH % 'disabled')
            tab.Down() if on else tab.SetUp()
            vein.Show() if on else vein.Hide()
        tab.SetSelected = set_selected
        set_selected(selected)

    def _Feed(self):
        window = self.window
        original = window.feedButton
        x, y = original.GetLocalPosition()
        button = uir1.Button(window.mountPage, self.kit, x, y - 1, FEED_W, original.GetText(), primary=True,
                             event=ui.__mem_func__(getattr(window, '_MountSystemWindow__OpenFeed')))
        # the EXE cannot tell a native button's state (no wndMgr.IsDisable): disabled until Open's snapshot request
        # sets it through the adapter (__SetInteractive)
        if not uir1.IsEnabled(original, default=False):
            button.Disable()
        original.Hide()
        self.feed = ButtonAdapter(original, button)
        window.feedButton = self.feed

    def _Tasks(self):
        """Úkoly větve: the R1 section instead of the gold heading and its icon, the R1 vein for the bonus of the branch
        and the R1 task rows. The window shows / hides the detail through these attributes (__ShowElementDetail)."""
        import uimountr1tasks as R1T
        window = self.window
        heading, icon, progress = window.tasksHeading, window.tasksIcon, window.detailProgress
        page = window.elementsPage
        x, y, w = TASKS_SECTION
        section = uir1.Section(page, self.kit, x, y, w, u'Úkoly větve', color=T.INK)
        gx, gy = progress.GetLocalPosition()
        gauge = R1T.Gauge(page, gx, gy + 1, progress.GetWidth())
        shown = heading.IsShow()
        for original in (heading, icon, progress):
            original.Hide()
        for widget in (section, gauge):
            widget.Show() if shown else widget.Hide()
        self.tasks = (heading, icon, progress, section, gauge)
        window.tasksHeading = window.tasksIcon = section
        window.detailProgress = gauge
        window.taskRowClass = R1T.TaskRow

    # ------------------------------------------------------------------ used by the window
    def SetTitleName(self, name):
        type(self.window).SetTitleName(self.window, name)
        self.skin.SetTitle(name)

    # ------------------------------------------------------------------ restore
    def Restore(self):
        window = self.window
        if window is None:
            return
        if self.tasks is not None:
            heading, icon, progress, section, gauge = self.tasks
            shown = section.IsShow()
            for original in (heading, icon, progress):
                original.Show() if shown else original.Hide()
            progress.SetValue(gauge.value, gauge.maximum)
            section.Hide()
            gauge.Hide()
            window.tasksHeading, window.tasksIcon, window.detailProgress = heading, icon, progress
            if 'taskRowClass' in window.__dict__:
                del window.taskRowClass
        if self.feed is not None:
            original = self.feed.original
            original.Enable() if self.feed.IsEnabled() else original.Disable()
            original.Show()
            self.feed.button.callback = None
            self.feed.button.Hide()
            window.feedButton = original
        for tab, vein in self.tabs:
            selected = bool(tab.IsDown()) if hasattr(tab, 'IsDown') else False
            vein.Hide()
            del tab.SetSelected
            tab.SetSelected(selected)
        for image, label, section in self.headings:
            section.Hide()
            if label is not None:
                image.label = label
            image.Show()
        for image, path in self.swapped:
            image.LoadImage(path)
        window.body.Show()
        if 'SetTitleName' in window.__dict__:
            del window.SetTitleName
        self._DragHandle(False)
        self.skin.Restore()
        self.skin.Destroy()
        self.swapped, self.headings, self.tabs, self.feed, self.tasks = [], [], [], None, None
        self.window = None

    Destroy = Restore


def path_width(path):
    """header_<w>x28.png -> w."""
    name = path.rsplit('/', 1)[-1]
    return int(name.split('_')[1].split('x')[0])
