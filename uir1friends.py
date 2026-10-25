# -*- coding: utf-8 -*-
"""The friends list (Přátelé) in the Althea R1 look "Krvavá žíla" (docs/ALTHEA_R1_KIT.md).

uimessenger.MessengerWindow keeps the window (204 x 340; in R1 6 px taller for the 26 px "Zprávy" button; uiscript
MessengerWindow, the crimson list logic) and every
function: the four pages (Přátelé / Cech / GM / Blokovaní), the live search with the clear cross and the search
button, the Online / Offline groups (a click on the heading folds the group), selecting and double clicking a
member, the mouse wheel and the scroll bar over the list, the five actions (add, whisper, remove, block, guild) with
their tooltips and their enabled state, and the bottom button that opens the messenger. This module draws the R1
look INTO that window:

* the R1 frame and header (title, vein, plain X) on the window's board; the crimson board art is hidden;
* the page tabs and the action buttons as dark R1 buttons with the ORIGINAL icons (the selected tab with the vein);
  each R1 button stands in for the original ui.Button (IconButton): it calls the original event, shows the original
  tooltip and follows every Enable / Disable / Show / Hide / Down / SetUp the window does on the original;
* the search as an R1 field (the original edit line inside it) with the small clear cross, the magnifier button;
* group headings in the R1 section style with a chevron, member rows as R1 bands (hover lighter, selected = the dark
  band with the red line), portraits and presence dots unchanged, the R1 scroll bar;
* the bottom button "Zprávy" as a thin 20 px primary button with the unread count as a small dark badge.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window. A failure while building the R1 look
restores the original window (traced to syserr) and the R1 look is not tried again in this session.
"""
from _weakref import ref

import ui

import uir1
import uir1drag
import uir1layout as L
import uir1tokens as T

P = T.PROFILE_WINDOW                # the layout profile of this window (docs/ALTHEA_R1_KIT.md chap. 0)
ORIGINAL_HEIGHT = 340               # uiscript MessengerWindow
# Owner 13. 10. (R1-SADA-ZPRAVY = A): "Zprávy" is an ordinary 26 px button; the window grows by the 6 px it needs so the
# button keeps its 6 px from the action rail and P['pad'] from the bottom edge (the R1 look only).
WIDTH, HEIGHT = 204, ORIGINAL_HEIGHT + 6
TAB = (12, 32, 43, 45)              # x, y, width, pitch of the four page tabs
SEARCH = (12, 62, 150)              # the search field
SEARCH_BUTTON = (166, 63, 26)       # the magnifier button
LIST_X, LIST_W = 14, 172            # the member rows (MessengerWindow START_POSITION 89, 184 px high)
SCROLL = (187, 89, 184)             # the list scroll bar
RAIL = (12, 280, 35, 36)            # x, y, width, pitch of the five action buttons
FOOTER = (P['pad'], HEIGHT - P['pad'] - P['btn'], 180)     # the "Zprávy" button (26 px)
ROW_H, DIVIDER_H = 36, 18           # member row / group heading (crimson geometry, the scroll logic counts them)
BADGE_REFRESH = 1.5                 # seconds between two reads of the unread count while the window is shown
TAB_NAMES = ('FriendsTabIcon', 'GuildTabIcon', 'GMTabIcon', 'BlockTabIcon')
RAIL_NAMES = (('AddFriendButton', 'RosterAddIcon'), ('WhisperButton', 'RosterWhisperIcon'),
              ('RemoveButton', 'RosterDeleteIcon'), ('BlockFriendButton', 'RosterBlockIcon'),
              ('GuildButton', 'RosterGuildIcon'))

_failed = set()          # windows whose R1 look failed in this session (not tried again)


def UseR1(what=u'Přátelé'):
    """The R1 look unless "Starý vzhled" is chosen or the R1 look of this window already failed in this session."""
    return what not in _failed and uir1.UseR1()


def Fail(what):
    _failed.add(what)
    uir1.TraceFailure(what)


def Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


# --------------------------------------------------------------------------- undo log of a skin
class Journal(object):
    """Every change the R1 look makes to the original window, so a failure can put the original back."""

    def __init__(self):
        self.steps = []

    def Do(self, undo):
        self.steps.append(undo)

    def Hide(self, widget):
        if widget is not None and widget.IsShow():
            widget.Hide()
            self.steps.append(widget.Show)

    def Own(self, widget):
        def undo():
            widget.Hide()
            destroy = getattr(widget, 'Destroy', None)
            if destroy:
                destroy()
        self.steps.append(undo)
        return widget

    def Reparent(self, widget, old_parent, new_parent, x, y):
        ox, oy = widget.GetLocalPosition()
        widget.SetParent(new_parent)
        widget.SetPosition(int(x), int(y))

        def undo():
            widget.SetParent(old_parent)
            widget.SetPosition(ox, oy)
        self.steps.append(undo)

    def Attr(self, obj, name, value):
        had = name in obj.__dict__
        old = obj.__dict__.get(name)
        setattr(obj, name, value)

        def undo():
            if had:
                setattr(obj, name, old)
            else:
                obj.__dict__.pop(name, None)
        self.steps.append(undo)

    def Undo(self):
        for step in reversed(self.steps):
            try:
                step()
            except Exception:
                pass
        self.steps = []


class Stub(object):
    """Stands in for an original widget the R1 look replaced (the crimson search hint): calls do nothing."""

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return lambda *args, **kwargs: None


def HideBoard(journal, board):
    """Hides the art of a ui.BoardWithTitleBar (corners, lines, base, title bar); the board stays as the first child
    of the window, so the R1 chrome drawn into it lies under everything else of the window."""
    for image in list(getattr(board, 'Corners', [])) + list(getattr(board, 'Lines', [])):
        journal.Hide(image)
    journal.Hide(getattr(board, 'Base', None))
    journal.Hide(getattr(board, 'titleBar', None))


# --------------------------------------------------------------------------- controls
class IconButton(uir1.Button):
    """R1 button standing in for an original ui.Button: the original icon (re-parented onto it), the original event
    (CallEvent), the original tooltip, and the original's Enable / Disable / Show / Hide / Down / SetUp mirrored (the
    window keeps calling them on the original, which stays hidden). selected=True draws the tab look (the vein)."""

    def __init__(self, parent, kit, journal, x, y, w, original, icon=None, primary=False, small=True, text='',
                 font=None):
        self.original = ref(original)
        self.selected = bool(primary)
        uir1.Button.__init__(self, parent, kit, x, y, w, text, primary=primary, small=small, event=self._Click,
                             font=font)
        self.icon = icon
        if icon is not None:
            journal.Reparent(icon, original, self, (w - icon.GetWidth()) // 2, (self.h - icon.GetHeight()) // 2)
            icon.Show()
        tip = getattr(original, 'ToolTipText', None)
        if tip is not None:
            journal.Reparent(tip, original, self, w // 2, tip.GetLocalPosition()[1])
        # The enabled state is never read from the engine (the game's buttons have no IsEnabled / IsDisable); the
        # window's later Enable / Disable calls on the original reach this button through _Mirror.
        visible = original.IsShow()
        journal.Hide(original)
        if not visible:
            self.Hide()
        _Mirror(journal, original, self)

    def _Click(self):
        original = self.original()
        if original is None:
            return
        call = getattr(original, 'CallEvent', None)
        if call:
            call()
        elif getattr(original, 'eventFunc', None):
            original.eventFunc(*(original.eventArgs or ()))

    def SetSelected(self, selected):
        selected = bool(selected)
        if selected != self.selected or selected != self.primary:
            self.selected = self.primary = selected
            self.paint()

    def OnMouseOverIn(self):
        uir1.Button.OnMouseOverIn(self)
        original = self.original()
        if original is not None and hasattr(original, 'ShowToolTip'):
            original.ShowToolTip()

    def OnMouseOverOut(self):
        uir1.Button.OnMouseOverOut(self)
        original = self.original()
        if original is not None and hasattr(original, 'HideToolTip'):
            original.HideToolTip()


def _Mirror(journal, original, proxy):
    """The window keeps driving the original button; its state calls go to the R1 button too."""
    cls = type(original)
    weak_original, weak_proxy = ref(original), ref(proxy)

    def call(name, *proxy_call):
        def method(*args):
            target = weak_original()
            result = getattr(cls, name)(target, *args) if target is not None and name in ('Enable', 'Disable', 'Down',
                                                                                          'SetUp') else None
            stand_in = weak_proxy()
            if stand_in is not None:
                getattr(stand_in, proxy_call[0])(*proxy_call[1:])
            return result
        return method

    for name, proxy_call in (('Enable', ('Enable',)), ('Disable', ('Disable',)), ('Show', ('Show',)),
                             ('Hide', ('Hide',)), ('Down', ('SetSelected', True)), ('SetUp', ('SetSelected', False))):
        if hasattr(cls, name) or name in ('Show', 'Hide'):
            journal.Attr(original, name, call(name, *proxy_call))



class ScrollBar(uir1.ScrollBar):
    """The R1 scroll bar with the API of uicrimsonember.CrimsonScrollBar (SetScale, OnMouseWheel, a size change
    keeps the position)."""

    def __init__(self, kit=None):
        uir1.ScrollBar.__init__(self, kit)
        self.scrollStep = 0.12

    def SetScrollBarSize(self, height):
        pos = self.curPos
        uir1.ScrollBar.SetScrollBarSize(self, height)
        self.SetPos(pos, False)

    def SetScale(self, visible, total):
        visible, total = float(visible or 0), float(total or 0)
        if total <= visible or total <= 0:
            self.SetPos(0.0, False)
            return
        pos = self.curPos
        self.SetMiddleBarSize(visible / total)
        self.SetPos(pos, False)

    def OnMouseWheel(self, delta):
        if delta > 0:
            self.SetPos(self.curPos - self.scrollStep)
            return True
        if delta < 0:
            self.SetPos(self.curPos + self.scrollStep)
            return True
        return False


class CountBadge(ui.Window):
    """Unread count: a small dark plate with a thin red rim and an ivory number; hidden at 0."""

    H = 15

    def __init__(self, parent, kit, right, cy):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.AddFlag('not_pick')
        self.right, self.cy = int(right), int(cy)
        self.fill = uir1.Rect(self, 1, 1, 14, 13, 0x0E0C0C)
        self.rims = [uir1.Rect(self, 0, 0, 1, 1, T.RED_DK) for unused in range(4)]
        # Row text rule (docs/ALTHEA_R1_KIT.md): a top-aligned line at CellTop, its whole cell inside the badge - the
        # badge grows with the font (at least 15 px).
        self.font = kit.font('text_sb')
        self.H = max(CountBadge.H, uir1.FontCell(self.font) + 1)
        self.label = uir1.RowText(self, '', 0, self.H, self.font, T.IVORY, align='center')
        self.count = None
        self.SetCount(0)

    def SetCount(self, count):
        count = max(0, int(count or 0))
        if count == self.count:
            return
        self.count = count
        if not count:
            self.Hide()
            return
        self.label.SetText(str(count) if count < 100 else '99+')
        w = max(16, uir1.TextWidth(self.label) + 10)
        h = self.H
        self.SetPosition(self.right - w, self.cy - h // 2)
        self.SetSize(w, h)
        self.fill.SetSize(w - 2, h - 2)
        for rim, (x, y, rw, rh) in zip(self.rims, ((0, 0, w, 1), (0, h - 1, w, 1), (0, 0, 1, h), (w - 1, 0, 1, h))):
            rim.SetPosition(x, y)
            rim.SetSize(rw, rh)
        self.label.SetPosition(w // 2, uir1.CellTop(h, self.font))
        self.Show()


class SearchField(uir1.Field):
    """R1 field around the original edit line with the small clear cross (only while there is text)."""

    def __init__(self, parent, kit, x, y, w, hint, edit, max_len, on_clear, font=None):
        uir1.Field.__init__(self, parent, kit, x, y, w, hint=hint, edit=edit, max_len=max_len, trail=T.CLEAR + 8,
                            font=font)
        hit = T.CLEAR + 6
        self.clear = uir1.Glyph(self, 'icon/clear_%s.png', self.w - hit - 3, (self.h - hit) // 2, T.CLEAR, on_clear,
                                hit)
        self.clear.Hide()

    def SyncClear(self):
        has_text = bool(self.edit.GetText())
        if has_text != bool(self.clear.IsShow()):
            self.clear.Show() if has_text else self.clear.Hide()

    def OnUpdate(self):
        uir1.Field.OnUpdate(self)
        self.SyncClear()


def _DuelUnread():
    """Duel challenge rows of Messages not seen yet (session only, see duelchallenge)."""
    try:
        import duelchallenge
        return duelchallenge.challenges.UnreadCount()
    except Exception:
        return 0


def UnreadTotal():
    """Unread private messages of the local history (guild lines excluded, like the messenger's own badge); 0 when
    the badge is switched off in the messenger settings or the history is not available."""
    try:
        import messengerHistory
    except Exception:
        return 0
    try:
        if not messengerHistory.GetNotificationPreference('badge'):
            return 0
        lister = getattr(messengerHistory, 'ListConversationSummaries', None) or messengerHistory.ListConversations
        total = 0
        for row in lister():
            if len(row) > 4 and not str(row[0]).startswith('guild:'):
                total += int(row[4] or 0)
        return total + _DuelUnread()
    except Exception:
        return 0


# --------------------------------------------------------------------------- list rows
SELECTED_FILL = (0x2E0A0C, 0.78)        # a selected row: dark blood fill (the band's red line under it)


def PaintBand(band, state):
    """uir1.Band state; a selected list row of these windows gets the dark blood fill instead of the plain dark well
    (the owner's mockup: "vybraný řádek = tmavá krvavá výplň se žílou")."""
    band.SetState(state)
    if state == 'selected':
        band.fill.SetColor(uir1.GenerateColor(*SELECTED_FILL))


class ItemBand(ui.Window):
    """R1 background of one member row; created by the row before its own images, hidden in the original look."""

    def __init__(self, row):
        ui.Window.__init__(self)
        self.SetParent(row)
        self.AddFlag('not_pick')
        self.SetSize(LIST_W, ROW_H)
        self.band = uir1.Band(self, 0, 0, LIST_W, ROW_H - 1)
        self.rule = uir1.Rect(self, 2, ROW_H - 1, LIST_W - 4, 1, T.LINE, 0.6)
        self.Hide()

    def SetState(self, state):
        PaintBand(self.band, state)
        self.rule.Show() if state != 'selected' else self.rule.Hide()
        self.Show()


def NewItemBand(row):
    try:
        return ItemBand(row)
    except Exception:
        return None


# --------------------------------------------------------------------------- the skin
class FriendsSkin(object):
    """The R1 look drawn into an existing, loaded MessengerWindow. Raises on failure after undoing its changes."""

    def __init__(self, window):
        self.window = ref(window)
        self.kit = uir1.Kit()
        self.journal = Journal()
        self.tabs = []
        self.actions = []
        self.lastBadge = -1.0
        try:
            self._Build(window)
        except Exception:
            self.journal.Undo()
            raise

    def _Build(self, win):
        kit, j = self.kit, self.journal
        child = win.GetChild
        board = child('board')
        for widget in (win, board):                     # the R1 window is 6 px taller (HEIGHT)
            ow, oh = widget.GetWidth(), widget.GetHeight()
            widget.SetSize(ow, HEIGHT)
            j.Do(lambda widget=widget, ow=ow, oh=oh: widget.SetSize(ow, oh))
        HideBoard(j, board)
        self.chrome = uir1.Chrome(board, kit, WIDTH, HEIGHT, _Title(), on_close=ui.__mem_func__(win.Close))
        for widget in self.chrome.Widgets():
            j.Own(widget)

        page = child('page_bg')
        j.Hide(page)
        x, y, w, pitch = TAB
        for index, icon_name in enumerate(TAB_NAMES):
            original = child('page_%d_btn' % index)
            tab = IconButton(win, kit, j, x + index * pitch, y, w, original, child(icon_name),
                             primary=index == getattr(win, 'pageIdx', 0))
            self.tabs.append(j.Own(tab))

        j.Hide(child('SearchBG'))
        edit = child('editline')
        j.Hide(child('FriendsSearchHint'))
        j.Attr(win, 'crimsonSearchHint', Stub())
        sx, sy, sw = SEARCH
        old = (edit.GetLocalPosition(), edit.GetWidth(), edit.GetHeight())

        def restore_edit():
            edit.SetParent(child('SearchBG'))
            edit.SetPosition(*old[0])
            edit.SetSize(old[1], old[2])
        j.Do(restore_edit)
        clear = child('clear_btn')
        self.search = j.Own(SearchField(win, kit, sx, sy, sw, Tr(u'Hledat přítele', 'Search friends'), edit, 18,
                                        lambda: clear.CallEvent() if hasattr(clear, 'CallEvent') else None,
                                        font=kit.font('text_s')))
        bx, by, bw = SEARCH_BUTTON
        self.searchButton = j.Own(IconButton(win, kit, j, bx, by, bw, child('search_btn'),
                                             child('FriendsSearchIcon')))

        old_bar = win.scrollBar
        j.Hide(old_bar)
        bar = ScrollBar(kit)
        bar.SetParent(win)
        bar.SetPosition(SCROLL[0], SCROLL[1])
        bar.SetScrollBarSize(SCROLL[2])
        bar.SetScrollEvent(ui.__mem_func__(win._CrimsonFriendsPixelScroll))
        bar.Hide()
        j.Own(bar)
        j.Attr(win, 'scrollBar', bar)
        self.scrollBar = bar

        j.Hide(child('ActionRail'))
        x, y, w, pitch = RAIL
        for index, (name, icon_name) in enumerate(RAIL_NAMES):
            button = IconButton(win, kit, j, x + index * pitch, y, w, child(name), child(icon_name))
            self.actions.append(j.Own(button))

        fx, fy, fw = FOOTER
        launcher = child('UnifiedMessengerButton')
        self.footer = j.Own(IconButton(win, kit, j, fx, fy, fw, launcher, None, primary=True, small=False,
                                       text=Tr(u'Zprávy', 'Messages'), font=kit.font('text_sb')))
        self.badge = CountBadge(self.footer, kit, fw - 6, self.footer.h // 2)
        self.RefreshBadge()
        # The header row drags the window like the hidden title bar did ('attach' -> the movable root); the X stays free.
        self.dragStrip = j.Own(uir1drag.DragStrip(win, WIDTH))

    # ------------------------------------------------------------------ runtime
    def Update(self):
        import app
        try:
            now = app.GetTime()
        except Exception:
            now = 0.0
        if now - self.lastBadge >= BADGE_REFRESH or now < self.lastBadge:
            self.lastBadge = now
            self.RefreshBadge()

    def RefreshBadge(self):
        self.badge.SetCount(UnreadTotal())

    def PaintItem(self, item):
        """A member row in R1: the band instead of the crimson row art, the name in Noto Sans (muted offline)."""
        band = getattr(item, 'r1Band', None)
        if band is None:
            return
        background = getattr(item, 'background', None)
        if background is not None:
            background.Hide()
        state = 'selected' if getattr(item, 'isSelected', False) else ('hover' if getattr(item, 'r1Hover', False)
                                                                        else 'normal')
        band.SetState(state)
        text = getattr(item, 'text', None)
        if text is not None:
            if not getattr(item, 'r1Styled', False):
                # Top-aligned at CellTop (never the engine's vertical centre): the whole cell stays in the row.
                uir1.SetFont(text, self.kit.font('text'))
                text.SetPosition(41, uir1.CellTop(ROW_H, self.kit.font('text')))
                item.r1Styled = True
            online = getattr(item, 'state', None) == getattr(item, 'STATE_ONLINE', object())
            text.SetPackedFontColor(T.IVORY if state == 'selected' else (T.INK if online else T.MUTED))

    def DressDivider(self, divider, collapsed):
        """A group heading (Online (3) / Offline (2)) in the R1 section style; the chevron shows the fold."""
        divider.background.Hide()
        uir1.SetFont(divider.text, self.kit.font('text_sb'))
        divider.text.SetPosition(2, uir1.CellTop(DIVIDER_H, self.kit.font('text_sb')))
        divider.text.SetPackedFontColor(T.INK_DIM)
        divider.arrow.LoadImage(uir1.ROOT + uir1.ChevronPath('right' if collapsed else 'down'))
        divider.arrow.SetPosition(LIST_W - T.CHEVRON - 4, (DIVIDER_H - T.CHEVRON) // 2)
        rx = uir1.TextWidth(divider.text) + 10
        divider.r1Rule = uir1.Ops(divider, L.rule(rx, DIVIDER_H // 2 - T.RULE_H // 2, LIST_W - rx - T.CHEVRON - 12))

    def Destroy(self):
        self.tabs = []
        self.actions = []


def _Title():
    try:
        import uiScriptLocale
        return uiScriptLocale.MESSENGER_TITLE
    except Exception:
        return u'Přátelé'


def Build(window):
    """The R1 look for a freshly loaded MessengerWindow, or None (original look: 'legacy' or a failure)."""
    if not UseR1():
        return None
    try:
        skin = FriendsSkin(window)
        SyncStates(window, (('OnSelectItem', lambda: (getattr(window, 'selectedItem', None),)),
                            ('RefreshUnifiedMessengerButton', tuple)))
        return skin
    except Exception:
        Fail(u'Přátelé')
        return None


def SyncStates(window, calls):
    """The enabled state of the stand-in buttons comes from the window's own state methods run once more after the
    build (their Enable / Disable on the originals reach the stand-ins); it is never read from the engine - the
    game's buttons have no IsEnabled / IsDisable."""
    for name, args in calls:
        method = getattr(window, name, None)
        if method is not None:
            method(*args())
