# -*- coding: utf-8 -*-
"""Uložení lokace / Vlastní porty (uicustomports.CustomPortsWindow) in the Althea R1 look "Krvavá žíla"
(docs/ALTHEA_R1_KIT.md).

The window keeps its width (500), its flags (movable, float), its state machine (loading / unavailable / error /
pending rows), the ten rows of a page with their four actions (Uložit, Upravit, Smazat with the original 16 px icons
and the hover hint, Teleport with its icon and label), the five pages I - V and the common dialogs (uiCommon, which
have their own R1 look). Instead of the crimson controls the window gets R1 controls with the same interface the
window drives (SetText on the texts, Enable / Disable on the actions, Down / SetUp on the pages):

* the R1 frame and header (title, vein, plain X) drawn into the window's own board (uir1.BoardSkin);
* the status sentence ("Ulož si pozici a teleportuj se.") centred under the header, the rows and the pages lower
  with room around them; the window grows from 380 to HEIGHT px for it
  and is centred again;
* rows as quiet R1 lines: the slot number, the name and the coordinates as top-aligned row texts (an empty slot
  muted), dividers between the rows; the actions as small dark R1 buttons with the original icons;
* the pages as an R1 segment (the current page is the dark well with the red line).

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building the R1 look
removes what was built, restores the board (traced to syserr) and the original look is built; the R1 look is not
tried again in this session.
"""
import ui

import uir1
import uir1tokens as T

WINDOW = u'Uložení lokace'
ROWS = 10                              # rows of a page (uicustomports.ROWS_PER_PAGE)
ROW_X, ROW_Y, ROW_PITCH, ROW_W, ROW_H = 10, 70, 27, 480, 25
SLOT_X, NAME_X, COORDS_X = 8, 30, 163
NAME_W, COORDS_W = 128, 110
ACTION_X = (282, 311, 340, 376)
ICON_W, TELEPORT_W = 26, 92
ICON, ICON_GAP = 16, 5                 # the original action icons (16 px) and the gap to the label
STATUS_Y = 38                          # the status sentence, centred: 11 px under the header, 16 px above row 1
PAGE_GAP, BOTTOM = 20, 16              # last row -> the pages; the pages -> the bottom edge
PAGE_CELL = 64


def PageY(rows=ROWS):
    """y of the page segment: under the last row with PAGE_GAP between them."""
    return ROW_Y + (rows - 1) * ROW_PITCH + ROW_H + PAGE_GAP


def Height(rows=ROWS):
    """The R1 window height: the pages and BOTTOM px under them (398 for ten rows; the original window has 380)."""
    return PageY(rows) + T.SEG_H + BOTTOM


PAGE_Y, HEIGHT = PageY(), Height()

_failed = set()


def _Destroy(widgets):
    """Hides (and destroys) R1 widgets of a failed or destroyed build."""
    for widget in widgets:
        if widget is None:
            continue
        try:
            widget.Hide()
            if hasattr(widget, 'Destroy'):
                widget.Destroy()
        except Exception:
            pass


def UseR1():
    return WINDOW not in _failed and uir1.UseR1()


class ActionButton(uir1.Button):
    """Small R1 button with an original 16 px icon (left of the label, or centred without one). Enable / Disable /
    Show / Hide come from the window's Refresh like on the original ui.Button; the icon dims when disabled."""

    def __init__(self, parent, kit, x, y, w, icon_path, text='', tooltip=''):
        self.icon = None
        uir1.Button.__init__(self, parent, kit, x, y, w, text, small=True, font=kit.font('text_s'))
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(icon_path)
        self.icon.Show()
        if tooltip:
            self.SetToolTipText(tooltip)
        self.paint()

    def paint(self):
        """uir1.Button.paint places the label (top-aligned at CellTop, 1 px lower while pressed, centred by x); with
        an icon the icon and the label are centred TOGETHER: the label keeps the y the button gave it and moves right
        by half the icon and the gap. The original crimson button put the label at the middle of the plate with its
        own vertical centre, which an R1 label (top-aligned) must not copy: "Teleport" sat 11 px low, over the edge."""
        uir1.Button.paint(self)
        icon = getattr(self, 'icon', None)
        if icon is None:
            return
        dy = 1 if self.pressed else 0
        iy = (self.h - ICON) // 2 + dy
        if self.label.GetText():
            group = ICON + ICON_GAP + uir1.TextWidth(self.label)
            gx = max(0, (self.w - group) // 2)
            icon.SetPosition(gx, iy)
            self.label.SetPosition(gx + ICON + ICON_GAP + (group - ICON - ICON_GAP + 1) // 2,
                                   self.label.GetLocalPosition()[1])
        else:
            icon.SetPosition((self.w - ICON) // 2, iy)
        icon.SetAlpha(1.0 if self.enabled else 0.35)

    def Disable(self):
        uir1.Button.Disable(self)
        if getattr(self, 'tooltip', None):
            uir1.HideHint()

    def SetEvent(self, event, *args):
        self.callback = (lambda: event(*args)) if event else None


class PageButton(object):
    """One page of the R1 segment with the Down / SetUp of the original page button (the window's Refresh)."""

    def __init__(self, segment, index):
        self.segment, self.index = segment, index

    def Down(self):
        self.segment.SetValue(self.index)

    def SetUp(self):
        if self.segment.value == self.index:
            self.segment.SetValue(None)

    def Show(self):
        self.segment.Show()

    def Hide(self):
        self.segment.Hide()


class Skin(object):
    def __init__(self, window):
        self.window = window
        self.widgets = []
        self.board = None
        self.pages = None
        self.size = None                # the original size, restored when the R1 build fails

    def Build(self, icons, page_labels, rows, locale):
        window = self.window
        self.kit = kit = uir1.Kit()
        self.add_text = locale('CUSTOM_PORTS_ADD', '+Add+')
        title = locale('CUSTOM_PORTS_TITLE', 'Saved locations')
        # The taller R1 window: resized before the board skin (it reads the board's size), centred again.
        self.size = (window.GetWidth(), window.GetHeight())
        window.SetSize(self.size[0], Height(rows))
        window.SetCenterPosition()
        self.board = uir1.BoardSkin(window, kit, title, on_close=window.Close)
        small = kit.font('text_s')
        width = window.GetWidth()

        status = uir1.Text(window, '', width // 2, STATUS_Y, small, T.INK_DIM, align='center', valign='top',
                           limit=width - 2 * T.PAD)
        self.widgets.append(status)
        window.instructionText = status

        save = locale('CUSTOM_PORTS_SAVE_HERE', 'Save')
        edit = locale('CUSTOM_PORTS_RENAME', 'Edit')
        delete = locale('CUSTOM_PORTS_DELETE', 'Delete')
        teleport = locale('CUSTOM_PORTS_TELEPORT', 'Teleport')
        for index in range(rows):
            y = ROW_Y + index * ROW_PITCH
            if index:
                self.widgets.append(uir1.Divider(window, ROW_X, y - 3, ROW_W))
            panel = ui.Window()
            panel.SetParent(window)
            panel.AddFlag('not_pick')          # the empty part of a row drags the window; the buttons take clicks
            panel.SetPosition(ROW_X, y)
            panel.SetSize(ROW_W, ROW_H)
            panel.Show()
            self.widgets.append(panel)
            slot = uir1.RowText(panel, '', SLOT_X, ROW_H, small, T.MUTED)
            name = uir1.RowText(panel, '', NAME_X, ROW_H, small, T.INK)
            name.SetLimitWidth(NAME_W)
            coords = uir1.RowText(panel, '', COORDS_X, ROW_H, small, T.INK_DIM)
            coords.SetLimitWidth(COORDS_W)
            by = (ROW_H - T.BTN_H_S) // 2
            buttons = {
                'save': ActionButton(panel, kit, ACTION_X[0], by, ICON_W, icons['save'], tooltip=save),
                'edit': ActionButton(panel, kit, ACTION_X[1], by, ICON_W, icons['edit'], tooltip=edit),
                'delete': ActionButton(panel, kit, ACTION_X[2], by, ICON_W, icons['delete'], tooltip=delete),
                'teleport': ActionButton(panel, kit, ACTION_X[3], by, TELEPORT_W, icons['teleport'], teleport),
            }
            buttons['save'].SetEvent(window._Save, index)
            buttons['edit'].SetEvent(window._OpenRenameDialog, index)
            buttons['delete'].SetEvent(window._OpenDeleteDialog, index)
            buttons['teleport'].SetEvent(window._Teleport, index)
            window.children.extend([panel, slot, name, coords] + list(buttons.values()))
            window.rows.append({'panel': panel, 'slot': slot, 'name': name, 'coords': coords, 'buttons': buttons})

        self.pages = uir1.Segment(window, kit, list(enumerate(page_labels)), event=window.SetPage,
                                  width=PAGE_CELL * len(page_labels))
        self.pages.value = None
        self.pages.SetPosition((width - self.pages.Width()) // 2, PageY(rows))
        self.widgets.append(self.pages)
        base_set = self.pages.SetValue

        def set_value(value):
            self.pages.value = value
            base_set(value)
        self.pages.SetValue = set_value
        window.pageButtons.extend(PageButton(self.pages, index) for index in range(len(page_labels)))

    def Sync(self):
        """Colours that follow the state the window's Refresh wrote: an empty slot muted, an error in red."""
        window = self.window
        failed = bool(window.unavailable or window.error)
        window.instructionText.SetPackedFontColor(T.RED_HI if failed else T.INK_DIM)
        for row in window.rows:
            empty = row['name'].GetText() == self.add_text
            row['name'].SetPackedFontColor(T.MUTED if empty else T.INK)
            row['coords'].SetPackedFontColor(T.MUTED if empty else T.INK_DIM)

    def Destroy(self):
        _Destroy(self.widgets)
        self.widgets = []
        if self.board is not None:
            self.board.Destroy()
        self.board = None
        self.window = None


def Build(window, icons, page_labels, rows, locale):
    """The R1 look of the window, or None (the original look: "Starý vzhled", or the R1 look failed - traced)."""
    if not UseR1():
        return None
    skin = Skin(window)
    try:
        skin.Build(icons, page_labels, rows, locale)
        return skin
    except Exception:
        _failed.add(WINDOW)
        uir1.TraceFailure(WINDOW)
        _Undo(window, skin)
        return None


def _Undo(window, skin):
    """Removes a half-built R1 look: the R1 widgets hidden, the board's original art back, the lists emptied."""
    widgets = []
    for row in window.rows:
        widgets.append(row.get('panel'))
    widgets.append(getattr(window, 'instructionText', None))
    _Destroy([w for w in widgets if w is not None])
    for page in window.pageButtons:
        try:
            page.Hide()
        except Exception:
            pass
    window.rows[:] = []
    window.pageButtons[:] = []
    window.children[:] = []
    _Destroy(skin.widgets)
    if skin.size is not None and (window.GetWidth(), window.GetHeight()) != skin.size:
        window.SetSize(*skin.size)          # the original 500 x 380, centred again
        window.SetCenterPosition()
    if skin.board is not None:
        skin.board.Restore()
        skin.board.Destroy()
    skin.board = skin.window = None
