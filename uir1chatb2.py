# -*- coding: utf-8 -*-
"""Compact chat B2 (owner choice 8. 10. 2026, the chat mockup round "B2"): a layer over the R1 chat
(root/uir1chat.py) of uicompactchat.ChatWindow.

* 540 x 194 (the chat keeps the size the player dragged; only the old default 588 x 230 becomes 540 x 194);
* one strip of text tabs Vše / Okolí / Volání / Skupina / Cech / Systém: a tab is the filter AND the sending channel
  (Vše, Okolí and Systém send to Okolí); a custom tab "Vlastní..." follows when the player has custom tabs;
* unread messages of Skupina and Cech that arrive while their tab is not shown: a dark blood red glow behind the
  label (G2, round 7) and the number as a small pill top right of the label (variant b, round 8); viewing the tab
  clears it. The Zprávy envelope shows the unread private messages the same way;
* the selected tab is a lighter well with ivory text (brightness only, no red underline), the hovered one a dark well;
* the channel is a tag in the channel colour inside the field (a click opens the channel choice), the field has no
  red vein: the focus is a lighter outline; emoticons inside the field, sending is the 24 px primary button;
* the scroll bar shows only while the view is scrolled up, with "N nových" bottom right (a click jumps down);
* the resize grip is three dots in the top right corner; the strip can be minimised to a 30 px bar;
* idle (after sending / Esc, the chat in the background) is the original Metin2 idle chat (owner in game, 8. 10.):
  no box, no frame, no strip, only the recent lines over the world, outlined and fading with their age (the native
  stream). The box, the tabs (with their unread numbers) and the field come back while the chat is active.

Whispers use the existing Messenger flow.
Settings -> "Starý vzhled" keeps the original chat (no R1, no B2). When building B2 or a B2 hook raises, the chat
traces it (syserr), drops the B2 parts and goes on as today's R1 chat (no retry until the next start).
"""
import app
import chat
import player
import ui

import uir1
import uir1layout as L
import uir1tokens as T
import uir1chat
import uir1chatart as A
import uicompactchatcontrols as controls
import compactchatmodel as model

ENABLED = True               # the B2 layer over the R1 chat (ci tests of the plain R1 row switch it off)
FAILED = []                  # a failed B2 build or hook: today's R1 chat until the next start

W, H = 540, 194              # the B2 size; the old default 588 x 230 maps to it
OLD_DEFAULT = (588, 230)
MIN_W = 480                  # the six tabs and the strip icons side by side
STRIP_H = 24
TAB_X, TAB_Y, TAB_H, TAB_GAP = 5, 3, 20, 2
LABEL_X = 7                  # label inset inside a tab (the well is 7 px wider on each side)
ICON = 20                    # strip icon hit box (16 px glyph inside)
ICON_STEP = 22
ROW_H = 24                   # input row: field + send button
ROW_BOTTOM = 5
SEND = 24
FIELD_X = 5
CHIP_X, CHIP_Y, CHIP_H = 3, 3, 18
MIN_H = STRIP_H + 6          # minimised: the strip only
VIEW_X, VIEW_TOP = 9, STRIP_H + 6
PM_POLL = 1.0                # seconds between two reads of the private message history

TABS = (('all', 'Vše'), ('talk', 'Okolí'), ('shout', 'Volání'), ('party', 'Skupina'), ('guild', 'Cech'),
        ('system', 'Systém'))
TAB_CHANNEL = {'all': 0, 'talk': 0, 'shout': 1, 'party': 2, 'guild': 3, 'system': 0}   # uicompactchat.CHANNELS
TIPS = {'all': 'Zobrazit vše. Psaní půjde do Okolí.', 'talk': 'Zobrazit Okolí. Psaní půjde do Okolí.',
        'shout': 'Zobrazit Volání. Psaní půjde do Volání (od úrovně 15).',
        'party': 'Zobrazit Skupinu. Psaní půjde do Skupiny.', 'guild': 'Zobrazit Cech. Psaní půjde do Cechu.',
        'system': 'Zobrazit systémové zprávy. Psaní půjde do Okolí.'}
COUNTED = ('party', 'guild')  # the tabs with an unread number (the mockup: Skupina and Cech)
CHANNEL_COLOR = {'Okolí': T.INK, 'Volání': 0xFFA7FFD4, 'Skupina': 0xFF00FFE4, 'Cech': 0xFFFDFF7C}  # today's chat
PLACEHOLDER = {'Okolí': 'Napiš zprávu...', 'Volání': 'Volání (od úrovně 15)...', 'Skupina': 'Napiš skupině...',
               'Cech': 'Napiš cechu...'}
PREFIX = {'!': 'Volání', '#': 'Skupina', '%': 'Cech'}

TAB_SEL = T.IVORY
TAB_HOVER = 0xFFDED6CC
TAB_DIM = T.INK_DIM
TAB_LIT = 0xFFF6EEE2         # label of a tab with unread messages (ivory, over the glow)
PILL_TEXT = 0xFFF6ECE0
FILL = (12 / 255., 11 / 255., 12 / 255.)
PILL_FONT = {'B': 'Noto Sans:11a', 'A': 'Tahoma:11'}


def UseB2():
    """B2 over the R1 chat unless Settings -> "Starý vzhled" or B2 / R1 failed in this session."""
    return ENABLED and not FAILED and uir1chat.UseR1()


def Signed(color):
    """A packed colour for SetPackedFontColor: the x64 binding ignores values >= 0x80000000 silently."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color >= 0x80000000 else color


def Art(name):
    return A.ROOT + name


def Plural(count):
    """"1 nová", "3 nové", "5 nových" (messages under the view)."""
    if count == 1:
        return '1 nová'
    if 2 <= count <= 4:
        return '%d nové' % count
    return '%d nových' % count


def _DuelUnread():
    """Duel challenge rows of Messages not seen yet (session only, see duelchallenge)."""
    try:
        import duelchallenge
        return duelchallenge.challenges.UnreadCount()
    except Exception:
        return 0


def UnreadPrivate():
    """Unread private messages of the local history (guild lines excluded, like uir1friends.UnreadTotal and the
    messenger's own badge); 0 when the badge is off in the messenger settings or the history is not available."""
    try:
        import messengerHistory
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


# --------------------------------------------------------------------------- images of the B2 art
def _image(parent):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    return image


class Strip(object):
    """Caps + repeated middle of one art family ('tab/sel_' -> tab/sel_l.png, tab/sel_m.png, tab/sel_r.png) under a
    parent. LoadImage makes a new image instance, so the tile rect, the window size and the alpha are set again after
    every LoadImage; the middle gets the window size of the area it draws (uir1._put)."""

    def __init__(self, parent, stem, cap):
        self.parent = parent
        self.cap = cap
        self.stem = None
        self.alpha = 1.0
        self.rect = None
        self.images = [_image(parent) for unused in range(3)]       # l, m, r
        self.SetStem(stem)

    def SetStem(self, stem):
        if stem == self.stem:
            return
        self.stem = stem
        for image, part in zip(self.images, ('l', 'm', 'r')):
            image.LoadImage(Art(stem + part + '.png'))
        rect, self.rect = self.rect, None
        if rect:
            self.Place(*rect)

    def Place(self, x, y, w):
        x, y, w = int(x), int(y), int(w)
        self.rect = (x, y, w)
        l, m, r = self.images
        cap = self.cap
        h = A.SIZES[self.stem + 'm.png'][1]
        mid = max(0, w - 2 * cap)
        l.SetPosition(x, y)
        r.SetPosition(x + max(cap, w - cap), y)
        m.SetPosition(x + cap, y)
        if mid:
            m.SetRenderingRect(0.0, 0.0, float(mid) / A.SIZES[self.stem + 'm.png'][0] - 1.0, 0.0)
            m.SetSize(mid, h)
        for image in self.images:
            image.SetAlpha(self.alpha)
        self.mid = mid

    def SetAlpha(self, alpha):
        if alpha != self.alpha:
            self.alpha = alpha
            for image in self.images:
                image.SetAlpha(alpha)

    def Show(self):
        self.images[0].Show()
        self.images[2].Show()
        if getattr(self, 'mid', 0):
            self.images[1].Show()
        else:
            self.images[1].Hide()

    def Hide(self):
        for image in self.images:
            image.Hide()

    def Destroy(self):
        self.Hide()
        self.images = []
        self.parent = None


def Picture(parent, name, x=0, y=0):
    image = _image(parent)
    image.LoadImage(Art(name))
    image.SetPosition(int(x), int(y))
    image.Show()
    return image


class Pill(object):
    """The unread number "b": a 10 px dark blood red pill with the ivory number, its left edge at x, top at y."""

    def __init__(self, parent, kit):
        self.strip = Strip(parent, 'pill/', A.CAPS['pill'])
        self.font = PILL_FONT.get(kit.font_set, PILL_FONT['B'])
        self.text = uir1.Text(parent, '', 0, 0, self.font, Signed(PILL_TEXT), align='center', valign='top')
        self.count = 0
        self.Hide()

    def Width(self):
        return uir1.TextWidth(self.text) + 6 if self.count else 0

    def SetCount(self, count):
        self.count = int(count)
        self.text.SetText(('99+' if self.count > 99 else str(self.count)) if self.count else '')

    def Place(self, x, y):
        w = self.Width()
        self.strip.Place(x, y, w)
        self.text.SetPosition(int(x) + w // 2, int(y) + uir1.CellTop(A.SIZES['pill/m.png'][1], self.font))

    def SetAlpha(self, alpha):
        self.strip.SetAlpha(alpha)

    def Show(self):
        if self.count:
            self.strip.Show()
            self.text.Show()
        else:
            self.Hide()

    def Hide(self):
        self.strip.Hide()
        self.text.Hide()

    def Destroy(self):
        self.strip.Destroy()
        self.text = None


# --------------------------------------------------------------------------- strip controls
class Tab(uir1chat._Tip, uir1.Interactive):
    """A text tab of the strip: label (text_s), the well of the selected / hovered tab, the G2 glow and the number
    pill of unread messages."""

    def __init__(self, parent, kit, key, label, tooltip, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.key = key
        self.kit = kit
        self.tooltip = tooltip
        self.callback = event
        self.selected = False
        self.count = 0
        self.font = kit.font('text_s')
        self.full_label = label
        self.maximum_width = None
        self.glow = Strip(self, 'glow/', A.CAPS['glow'])                   # images before the texts
        self.well = Strip(self, 'tab/sel_', A.CAPS['tab'])
        self.label = uir1.RowText(self, label, LABEL_X, TAB_H, self.font, Signed(TAB_DIM))
        self.pill = Pill(self, kit)
        self.SetSize(self.Width(), TAB_H)
        self.paint()
        self.Show()

    def LabelWidth(self):
        return uir1.TextWidth(self.label)

    def Unread(self):
        return self.count if not self.selected else 0

    def Width(self):
        extra = (self.pill.Width() + 1) if self.Unread() else 0
        return self.LabelWidth() + 2 * LABEL_X + extra

    def SetLabel(self, text):
        self.full_label = text
        self.Relayout()

    def SetMaximumWidth(self, width):
        self.maximum_width = width
        self.Relayout()

    def MinimumWidth(self):
        previous = self.label.GetText()
        self.label.SetText(self.full_label[:1] + '...')
        minimum = self.Width()
        self.label.SetText(previous)
        return min(minimum, self.Width())

    def SetSelected(self, value):
        self.selected = bool(value)
        self.Relayout()

    def SetCount(self, count):
        self.count = int(count)
        self.pill.SetCount(self.count)
        self.Relayout()

    def Relayout(self):
        self.label.SetText(self.full_label)
        if self.maximum_width is not None:
            extra = self.pill.Width() + 1 if self.Unread() else 0
            uir1.Fit(self.label, self.full_label, self.maximum_width - 2 * LABEL_X - extra)
        self.SetSize(self.Width(), TAB_H)
        self.paint()

    def paint(self):
        if getattr(self, 'pill', None) is None:          # native Hide / mouse event during __init__
            return
        w, lw = self.Width(), self.LabelWidth()
        unread = bool(self.Unread())
        if self.selected:
            self.well.SetStem('tab/sel_')
            self.well.Place(0, 0, w)
            self.well.Show()
        elif self.hovered:
            self.well.SetStem('tab/hover_')
            self.well.Place(0, 0, w)
            self.well.Show()
        else:
            self.well.Hide()
        if unread:
            self.glow.Place(LABEL_X - 17, -9, lw + 34)
            self.glow.Show()
            self.pill.Place(LABEL_X + lw + 1, 0)
            self.pill.Show()
        else:
            self.glow.Hide()
            self.pill.Hide()
        if unread:
            color = TAB_LIT
        elif self.selected:
            color = TAB_SEL
        elif self.hovered:
            color = TAB_HOVER
        else:
            color = TAB_DIM
        self.label.SetPackedFontColor(Signed(color))

    def Destroy(self):
        uir1chat._Tip.Destroy(self)
        self.glow.Destroy()
        self.well.Destroy()
        self.pill.Destroy()
        self.pill = None


class StripIcon(uir1chat._Tip, uir1.Interactive):
    """16 px ivory icon in a 20 px hit box: normal = dim, hover / on = ivory; count > 0 = the G2 glow behind it and
    the number pill (the Zprávy envelope). on = a running repeated shout."""

    def __init__(self, parent, kit, key, tooltip, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.SetSize(ICON, ICON)
        self.key = key
        self.tooltip = tooltip
        self.callback = event
        self.on = False
        self.running = False                 # API of the original repeat IconControl (ChatWindow.OnUpdate)
        self.count = 0
        self.glow = Picture(self, 'glow/icon.png', -6, -6)
        self.icon = _image(self)
        self.icon_name = None
        self.pill = Pill(self, kit)
        self.paint()
        self.Show()

    def SetKey(self, key, tooltip=None):
        self.key = key
        if tooltip:
            self.tooltip = tooltip
            self.tip = None
        self.paint()

    def SetCount(self, count):
        if int(count) != self.count:
            self.count = int(count)
            self.pill.SetCount(self.count)
            self.paint()

    def paint(self):
        if getattr(self, 'pill', None) is None:
            return
        lit = self.hovered or self.on or self.running or self.count
        if self.key == 'expand':
            name, x = uir1.ROOT + uir1.ChevronPath('up', 'hover' if self.hovered else 'normal'), 5
        else:
            name, x = Art('icon/%s_%s.png' % (self.key, 'hover' if lit else 'normal')), 2
        if name != self.icon_name:
            self.icon_name = name
            self.icon.LoadImage(name)
            self.icon.SetPosition(x, x)
        self.icon.Show()
        if self.count:
            self.glow.Show()
            self.pill.Place(12, 0)           # top right of the envelope, its number cell inside the 20 px box
            self.pill.Show()
        else:
            self.glow.Hide()
            self.pill.Hide()

    def Destroy(self):
        uir1chat._Tip.Destroy(self)
        self.pill.Destroy()
        self.pill = None
        self.glow = self.icon = None


class ChannelChip(uir1chat._Tip, uir1.Interactive):
    """The sending channel as a tag inside the field: a dark 18 px well, the channel name in its chat colour and a
    down chevron; a click opens the channel choice. API of the original CompactInput.mode (text, SetText)."""

    def __init__(self, parent, kit, name, tooltip, event, changed):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.tooltip = tooltip
        self.callback = event
        self.changed = changed
        self.font = kit.font('text_s')
        self.well = Strip(self, 'chip/normal_', A.CAPS['chip'])
        self.text = uir1.RowText(self, '', 6, CHIP_H, self.font, Signed(T.INK))
        self.chevron = _image(self)
        self.name = None
        self.SetText(name)
        self.Show()

    def Width(self):
        return uir1.TextWidth(self.text) + 8 + 14

    def SetText(self, value):
        self.name = value
        self.text.SetText(value)
        self.text.SetPackedFontColor(Signed(CHANNEL_COLOR.get(value, T.INK)))
        self.SetSize(self.Width(), CHIP_H)
        self.paint()
        if self.changed:
            self.changed()

    def paint(self):
        if getattr(self, 'chevron', None) is None:
            return
        w = self.Width()
        self.well.SetStem('chip/%s_' % ('hover' if self.hovered or self.pressed else 'normal'))
        self.well.Place(0, 0, w)
        self.well.Show()
        state = 'hover' if self.hovered else 'normal'
        self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath('down', state))
        self.chevron.SetPosition(w - 14, (CHIP_H - T.CHEVRON) // 2)
        self.chevron.Show()

    def Destroy(self):
        uir1chat._Tip.Destroy(self)
        self.well.Destroy()
        self.changed = None
        self.chevron = None


class PlateButton(uir1chat._Tip, uir1.Interactive):
    """A small square button of the input row: the emoji glyph inside the field (no plate) or the 24 px primary
    send plate with the ivory send arrow."""

    def __init__(self, parent, key, tooltip, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.key = key
        self.tooltip = tooltip
        self.callback = event
        self.text = self.check = None
        size = SEND if key == 'send' else ICON
        self.SetSize(size, size)
        self.plate = _image(self) if key == 'send' else None
        self.icon = _image(self)
        self.paint()
        self.Show()

    def paint(self):
        if getattr(self, 'icon', None) is None:
            return
        state = self.state()
        down = 1 if self.pressed else 0
        if self.plate is not None:
            self.plate.LoadImage(Art('send/%s.png' % ('pressed' if state == 'pressed' else
                                                      ('hover' if state == 'hover' else 'normal'))))
            self.plate.SetPosition(0, 0)
            self.plate.Show()
            self.icon.LoadImage(Art('icon/send_normal.png'))
            self.icon.SetPosition(2, 2 + down)
        else:
            self.icon.LoadImage(Art('icon/emoji_%s.png' % ('hover' if state in ('hover', 'pressed') else 'normal')))
            self.icon.SetPosition(0, down)
        self.icon.Show()

    def Destroy(self):
        uir1chat._Tip.Destroy(self)
        self.plate = self.icon = None


class JumpButton(uir1chat._Tip, uir1.Interactive):
    """"N nových" bottom right of the scrolled view: a 20 px R1 secondary plate, a down chevron and the count; a click
    returns the view to the newest messages."""

    def __init__(self, parent, kit, event):
        uir1.Interactive.__init__(self)
        self.SetParent(parent)
        self.tooltip = 'Zpět na nejnovější zprávy.'
        self.callback = event
        self.font = kit.font('text_s')
        self.h = L.button_height('xs')
        self.SetSize(64, self.h)
        self.plate = uir1.Ops(self, L.button(False, 'xs', 'normal', 64))       # the plate before the texts
        self.chevron = uir1.Image(self, uir1.ChevronPath('down'), 8, (self.h - T.CHEVRON) // 2)
        self.label = uir1.RowText(self, '', 22, self.h, self.font, Signed(T.INK))
        self.SetLabel(Plural(1))

    def SetLabel(self, text):
        if text != self.label.GetText():
            self.label.SetText(text)
        self.SetSize(22 + uir1.TextWidth(self.label) + 9, self.h)
        self.paint()

    def paint(self):
        if getattr(self, 'label', None) is None:
            return
        self.plate.Apply(L.button(False, 'xs', self.state(), self.GetWidth()))

    def Destroy(self):
        uir1chat._Tip.Destroy(self)
        self.plate.Destroy()
        self.label = None


# --------------------------------------------------------------------------- the B2 skin of one chat window
class CompactSkin(object):
    """The B2 parts of one ChatWindow that already wears the R1 skin (window.r1). Build raises after undoing itself,
    so the owner keeps today's R1 chat."""

    def __init__(self, window):
        if not getattr(window, 'r1', None):
            raise RuntimeError('B2 needs the R1 chat')
        self.window = window
        self.r1 = window.r1
        self.kit = self.r1.kit
        self.minimised = False
        self.full = (W, H)
        self.tabs = {}
        self.icons = {}
        self.unread = dict((key, 0) for key in COUNTED)
        self.pm_count = 0
        self.pm_due = 0.
        self.revision = None
        self.last_seq = None
        self.legacy_mode = None
        self.legacy_buttons = None
        self.chip = self.field = self.placeholder = None
        self.frame = self.divider = None
        self.jump = self.fade = self.grip_dots = None
        self.move_tip = None
        self.buttons = []
        self.focused = None
        try:
            self._Build()
        except Exception:
            self.Undress()
            raise

    def _Build(self):
        window = self.window
        inp = window.chatInputSet
        self.frame = uir1.Frame(window, 0, 0, W, H, 'window', bg=None)
        self.divider = uir1.Layer(window, 0, 0, W, T.RULE_H, L.divider(0, 0, W - 10))
        # The input row: the field and the channel tag inside the input set, the chat line moved after them (a window
        # joins the END of its new parent's children) so the engine draws it above the field.
        self.legacy_mode = inp.mode
        self.legacy_mode.Hide()
        self.field = Strip(inp, 'field/normal_', A.CAPS['field'])
        self.chip = ChannelChip(inp, self.kit, self.legacy_mode.text.GetText() or 'Okolí',
                                'Vybrat kanál odesílání. Záložka zůstane.', ui.__mem_func__(window.OpenChannels),
                                ui.__mem_func__(self.LayoutInput))
        self.placeholder = uir1.Text(inp, '', 0, 0, 'Tahoma:12', Signed(T.MUTED), valign='top')
        self.measure = uir1.Text(inp, '', 0, 0, 'Tahoma:12', Signed(T.MUTED), valign='top')
        self.measure.Hide()
        line = inp.chatLine
        line.SetParent(window)
        line.SetParent(inp)
        back = getattr(line, 'backText', None)
        if back is not None:
            back.SetPackedFontColor(Signed(T.MUTED))
        inp.mode = self.chip
        inp.r1 = self
        events = dict((b.key, b.callback) for b in window.buttons if getattr(b, 'key', None))
        tips = dict((b.key, b.tooltip) for b in window.buttons if getattr(b, 'key', None))
        self.legacy_buttons = list(window.buttons)
        for button in self.legacy_buttons:
            button.Hide()
        self.events = events
        self.buttons = [PlateButton(window, 'emoji', tips.get('emoji', ''), events['emoji']),
                        PlateButton(window, 'send', tips.get('send', ''), events['send'])]
        window.buttons = list(self.buttons)
        # "N nových": the last row fades into the chat fill under the button (nothing is cut mid-word)
        self.fade = _image(window)
        self.fade.LoadImage(Art('fade.png'))
        self.fade.Hide()
        self.jump = JumpButton(window, self.kit, ui.__mem_func__(self.JumpLatest))
        self.jump.Hide()
        view = window.view
        view.on_drawn = ui.__mem_func__(self.ViewDrawn)
        # the resize grip: three dots; the move grip: the strip behind the tabs (drawn by nothing)
        window.resize_grip.OnRender = _Nothing
        window.move_grip.OnRender = _Nothing
        # the move grip lies invisible behind the whole tab strip, so its hint "Tažením přesunout chat..."
        # flashed above the chat in every gap between the tabs and icons (a "shadow" hint nobody can aim at); B2 has
        # no visible move control to name - the drag itself stays
        self.move_tip = window.move_grip.tooltip
        window.move_grip.tooltip = ''
        self.grip_dots = Picture(window.resize_grip, 'grip_normal.png', 5, 4)
        # idle = the original Metin2 chat: the outlined lines only, no box behind them ("Pozadí při hraní" unused)
        window.passive.draw_background = False
        self.last_seq = self._MaxSeq()
        self.revision = chat.GetMessageRevision()

    # ------------------------------------------------------------------ geometry
    def Size(self, width, height):
        """The chat size of B2: the old default becomes 540 x 194, the strip needs at least MIN_W."""
        if (width, height) == OLD_DEFAULT:
            width, height = W, H
        return max(MIN_W, width), height

    def VisibleHeight(self, height, visible):
        return MIN_H if self.minimised else visible

    def Layout(self, width, height):
        """After uicompactchat.Refresh and the R1 layout: the strip, the message view, the input row."""
        window = self.window
        self.full = (width, height)
        self.frame.SetPosition(0, 0)
        self.frame.Resize(width, MIN_H if self.minimised else height)
        self.divider.SetPosition(5, STRIP_H + 1)
        self.divider.SetSize(width - 10, T.RULE_H)
        self.divider.Apply(L.divider(0, 0, width - 10))
        self.LayoutStrip()
        window.resize_grip.SetPosition(width - 16, 0)
        window.resize_grip.SetSize(16, 16)
        window.move_grip.SetPosition(0, 0)
        window.move_grip.SetSize(width - 16, STRIP_H + 2)
        mh = height - VIEW_TOP - ROW_H - ROW_BOTTOM - 5
        window.view.SetPosition(VIEW_X, VIEW_TOP)
        window.view.Resize(width - VIEW_X - 6, mh)
        window.view.scroll.SetPosition(window.view.GetWidth() - window.view.scroll_inset, 0)
        row_y = height - ROW_H - ROW_BOTTOM
        field_w = width - 2 * FIELD_X - SEND - 4
        inp = window.chatInputSet
        inp.SetPosition(FIELD_X, row_y)
        inp.SetSize(field_w, ROW_H)
        self.field_w = field_w
        if self.r1.well is not None:
            self.r1.well.Hide()                        # the R1 layout re-applied the vein field
        self.focused = None
        self.LayoutInput()
        self.buttons[0].SetPosition(FIELD_X + field_w - ICON - 3, row_y + (ROW_H - ICON) // 2)
        self.buttons[1].SetPosition(width - FIELD_X - SEND, row_y)
        self.fade.SetPosition(3, VIEW_TOP + mh - 24)
        self.fade.SetRenderingRect(0.0, 0.0, float(width - 20) / A.SIZES['fade.png'][0] - 1.0, 0.0)
        self.fade.SetSize(width - 20, 24)
        self.ViewDrawn(window.view)

    def LayoutInput(self):
        inp = self.window.chatInputSet
        if inp is None or self.chip is None or not hasattr(self, 'field_w'):
            return
        self.chip.SetPosition(CHIP_X, CHIP_Y)
        line = inp.chatLine
        x = CHIP_X + self.chip.Width() + 7
        line.SetPosition(x, (ROW_H - 17) // 2 + 1)
        line.SetSize(max(20, self.field_w - x - ICON - 6), 17)
        line.x, line.y, line.width, line.height = line.GetRect()
        self.line_x = x
        self.placeholder.SetText('')                   # placed again by SyncInput
        self.focused = None
        self.SyncInput()

    def LayoutStrip(self):
        window = self.window
        width = self.full[0]
        rx = width - 14
        for key in ('minimise', 'settings', 'history', 'pm', 'add', 'repeat'):
            icon = self.icons.get(key)
            rx -= ICON_STEP
            if icon is not None:
                icon.SetPosition(rx, TAB_Y)
        # Reserve the complete toolbar before shortening labels. The original
        # names/filters and unread counts remain intact; hover explains a tab.
        tabs = [control for control in window.header if isinstance(control, Tab)]
        for tab in tabs:
            tab.SetMaximumWidth(None)
        widths = [tab.GetWidth() for tab in tabs]
        minimums = [tab.MinimumWidth() for tab in tabs]
        available = rx - TAB_X - TAB_GAP * len(tabs)
        while sum(widths) > available:
            candidates = [i for i, w in enumerate(widths) if w > minimums[i]]
            if not candidates:
                break
            index = max(candidates, key=lambda i: widths[i])
            widths[index] -= 1
        x = TAB_X
        for tab, limit in zip(tabs, widths):
            tab.SetMaximumWidth(limit)
            tab.SetPosition(x, TAB_Y)
            x += tab.GetWidth() + TAB_GAP

    # ------------------------------------------------------------------ the strip
    def BuildHeader(self):
        """The strip controls (ChatWindow.header): the tabs, the custom tab, the icons. Sets window.repeat_button."""
        window = self.window
        header = []
        self.tabs = {}
        for key, label in TABS:
            tab = Tab(window, self.kit, key, label, TIPS[key], _Bind(self.SelectTab, key))
            self.tabs[key] = tab
            header.append(tab)
        if len(window.prefs['tabs']) > 1:
            custom = window.selected == 'custom'
            name = window.prefs['tabs'][window.tab_index]['name'] if custom else 'Vlastní...'
            tab = Tab(window, self.kit, 'custom', name,
                      'Vybrat vlastní záložku nebo oddělené okno: ' + name, ui.__mem_func__(window.OpenCustomTabs))
            self.tabs['custom'] = tab
            header.append(tab)
        icons = (('repeat', 'Opakované volání: stav, uložená zpráva, spuštění a pozastavení.', window.OpenRepeat),
                 ('add', 'Vytvořit vlastní záložku s názvem a filtry.', window.OpenAddTab),
                 ('pm', 'Otevřít stávající Messenger.', window.OpenMessenger),
                 ('history', 'Otevřít historii veřejného chatu.', window.OpenHistory),
                 ('settings', 'Nastavení chatu: Obsah, Vzhled, Upozornění.', window.OpenSettings),
                 ('minimise', 'Sbalit chat na pás se záložkami.', self.ToggleMinimise))
        self.icons = {}
        for key, tooltip, callback in icons:
            icon = StripIcon(window, self.kit, key, tooltip, ui.__mem_func__(callback))
            self.icons[key] = icon
            header.append(icon)
        self.icons['repeat'].running = window.repeat.running
        window.repeat_button = self.icons['repeat']
        self.PaintStrip(header)
        return header

    def PaintStrip(self, header=None):
        window = self.window
        selected = window.selected
        for key, tab in self.tabs.items():
            tab.SetSelected(key == selected)
            tab.SetCount(self.unread.get(key, 0))
        self.icons['pm'].SetCount(self.pm_count)
        self.icons['minimise'].SetKey('expand' if self.minimised else 'minimise',
                                      'Rozbalit chat.' if self.minimised else 'Sbalit chat na pás se záložkami.')
        if header is None:
            self.LayoutStrip()

    def SelectTab(self, key):
        """A tab is the filter and the sending channel; viewing it clears its unread number."""
        window = self.window
        if key in self.unread:
            self.unread[key] = 0
        self.minimised = False
        window.SelectHeader(key)
        window.chatInputSet.SelectChannel(TAB_CHANNEL.get(key, 0))     # opens the chat (and the strip)

    def ToggleMinimise(self):
        window = self.window
        if self.minimised:
            self.minimised = False
            window.OpenChat()
        else:
            self.minimised = True
            window.CloseChat()
        self.PaintStrip()

    def Expand(self):
        """Opening the chat (Enter, a tab, sending) brings the minimised chat back."""
        if self.minimised:
            self.minimised = False
            self.PaintStrip()

    # ------------------------------------------------------------------ visibility
    def RefreshVisibility(self):
        """After uicompactchat.RefreshEditorVisibility: box, strip and field only while the chat is active (open or
        minimised to its strip); idle shows only the passive lines of the original chat."""
        window = self.window
        strip = window.edit_mode or self.minimised
        for control in window.header:
            control.Show() if strip else control.Hide()
        for part in (self.frame, self.divider):
            part.Show() if strip else part.Hide()
        if self.minimised:
            self.divider.Hide()
            for control in [window.view, window.chatInputSet, window.resize_grip] + window.buttons:
                control.Hide()
            window.move_grip.Show()
            window.passive.Hide()
        if not window.edit_mode or self.minimised:
            self.jump.Hide()
            self.fade.Hide()
        window.passive.suppressed = self.minimised

    # ------------------------------------------------------------------ rendering, input row, view
    def Render(self):
        """ChatWindow.OnRender: the chat fill (prefs 'opacity') while active; nothing idle. True = drawn."""
        window = self.window
        x, y = window.GetGlobalPosition()
        width, height = self.full
        if self.minimised:
            controls.bar(x, y, width, MIN_H, FILL, window.prefs['opacity'] / 100.)
        elif window.edit_mode:
            controls.bar(x, y, width, height, FILL, window.prefs['opacity'] / 100.)
        return True

    def SyncInput(self):
        """Every frame (CompactInput.OnUpdate): the focus outline of the field, the placeholder of the channel."""
        inp = self.window.chatInputSet
        try:
            focused = bool(inp.chatLine.IsFocus())
        except Exception:
            focused = False
        if focused != self.focused:
            self.focused = focused
            self.field.SetStem('field/%s_' % ('focus' if focused else 'normal'))
            self.field.Place(0, 0, getattr(self, 'field_w', 64))
            self.field.Show()
        value = inp.chatLine.GetText()
        name = PREFIX.get(value[:1], 'Okolí')
        hint = PLACEHOLDER.get(name, '') if value in ('', '!', '#', '%') else ''
        if hint and value:
            if self.placeholder.GetText() != hint:
                self.placeholder.SetText(hint)
                # after the channel mark the chat line keeps in front of the text ("#", "%", "!")
                self.measure.SetText(value[:1])
                self.placeholder.SetPosition(getattr(self, 'line_x', 0) + uir1.TextWidth(self.measure) + 4,
                                             (ROW_H - 17) // 2 + 3)
            self.placeholder.Show()
        else:
            self.placeholder.Hide()
        back = getattr(inp.chatLine, 'backText', None)
        if back is not None and not value and back.GetText() != PLACEHOLDER['Okolí']:
            back.SetText(PLACEHOLDER['Okolí'])

    def ViewDrawn(self, view):
        """MessageView.DrawRows: the scroll bar only while scrolled up, "N nových" bottom right with the fade."""
        window = self.window
        if window is None or self.jump is None:
            return
        scrolled = bool(view.offset) and window.edit_mode and not self.minimised
        if not scrolled:
            if view.scroll.IsShow():
                view.scroll.Hide()
            self.jump.Hide()
            self.fade.Hide()
            return
        below = len(set(row[0] for row in view.lines[len(view.lines) - view.offset:]))
        self.jump.SetLabel(Plural(max(1, below)))
        width = self.full[0]
        mh = view.GetHeight()
        self.jump.SetPosition(width - 24 - self.jump.GetWidth(), VIEW_TOP + mh - 22)
        self.fade.Show()
        self.jump.Show()
        view.scroll.Show()

    def JumpLatest(self):
        self.window.view.Latest()

    # ------------------------------------------------------------------ unread counting
    def _MaxSeq(self):
        rows = chat.GetRecentMessages()
        return max([row[0] for row in rows]) if rows else None

    def CountNew(self):
        """Counts the Skupina / Cech messages that arrived since the last frame while their tab is not shown (the
        player's own lines excluded). The native snapshot numbers messages in arrival order (row[0])."""
        revision = chat.GetMessageRevision()
        if revision == self.revision:
            return False
        self.revision = revision
        rows = chat.GetRecentMessages()
        if not rows:
            return False
        kinds = {chat.CHAT_TYPE_PARTY: 'party', chat.CHAT_TYPE_GUILD: 'guild'}
        own = (player.GetName() or '').lower()
        last, changed = self.last_seq, False
        for row in rows:
            seq = row[0]
            if last is not None and seq <= last:
                continue
            key = kinds.get(row[1])
            if key is None or key == self.window.selected:
                continue
            match = model.SENDER.match(row[2]) if row[4] else None
            if match and match.group(1).lower() == own:
                continue
            self.unread[key] += 1
            changed = True
        self.last_seq = max(last, max(row[0] for row in rows)) if last is not None else max(row[0] for row in rows)
        return changed

    def Update(self):
        """ChatWindow.OnUpdate: unread numbers, the Zprávy count, the grip under the mouse."""
        changed = self.CountNew()
        now = app.GetTime()
        if now >= self.pm_due:
            self.pm_due = now + PM_POLL
            count = UnreadPrivate()
            if count != self.pm_count:
                self.pm_count = count
                changed = True
        if changed:
            self.PaintStrip()
        repeat = self.icons.get('repeat')
        if repeat is not None and repeat.running != getattr(repeat, 'shown_running', None):
            repeat.shown_running = repeat.running            # ChatWindow.OnUpdate sets it every frame
            repeat.paint()
        grip = self.window.resize_grip
        name = Art('grip_%s.png' % ('hover' if getattr(grip, 'hover', False) else 'normal'))
        if getattr(self, 'grip_name', None) != name:
            self.grip_name = name
            self.grip_dots.LoadImage(name)
            self.grip_dots.SetPosition(5, 4)

    # ------------------------------------------------------------------ undo
    def Undress(self):
        """Back to today's R1 chat (a failed build or a failing hook)."""
        window = self.window
        if window is None:
            return
        inp = getattr(window, 'chatInputSet', None)
        if inp is not None:
            if self.legacy_mode is not None:
                inp.mode = self.legacy_mode
                inp.mode.Show()
            if getattr(inp, 'r1', None) is self:
                inp.r1 = self.r1
            for part in (self.chip, self.field):
                if part is not None:
                    part.Destroy()
            if self.placeholder is not None:
                self.placeholder.Hide()
        if self.legacy_buttons is not None:
            for button in self.buttons:
                button.Destroy()
            window.buttons = self.legacy_buttons
            for button in window.buttons:
                button.Show() if window.edit_mode else button.Hide()
        for part in (self.frame, self.divider, self.jump):
            if part is not None:
                part.Hide()
                part.Destroy()
        if self.fade is not None:
            self.fade.Hide()
        if self.grip_dots is not None:
            self.grip_dots.Hide()
        move_grip = getattr(window, 'move_grip', None)
        if move_grip is not None and self.move_tip is not None:
            move_grip.tooltip = self.move_tip
        self.move_tip = None
        for grip in (getattr(window, 'resize_grip', None), move_grip):
            if grip is not None and 'OnRender' in grip.__dict__:
                del grip.OnRender
        view = getattr(window, 'view', None)
        if view is not None and 'on_drawn' in view.__dict__:
            view.on_drawn = None
        passive = getattr(window, 'passive', None)
        if passive is not None:
            passive.draw_background = True
            passive.suppressed = False
        if self.r1 is not None and self.r1.well is not None and window.edit_mode:
            self.r1.well.Show()
        self.buttons, self.tabs, self.icons = [], {}, {}
        if getattr(self, 'measure', None) is not None:
            self.measure.Hide()
        self.chip = self.field = self.placeholder = self.measure = self.frame = self.divider = None
        self.jump = self.fade = self.grip_dots = None
        self.legacy_mode = self.legacy_buttons = None
        self.minimised = False

    def Destroy(self):
        """ChatWindow.Destroy: the window already destroyed its buttons (B2's) and the input set's mode (the tag)."""
        for button in self.legacy_buttons or ():
            button.Destroy()
        if self.legacy_mode is not None:
            self.legacy_mode.Destroy()
        for part in (self.frame, self.divider, self.jump, self.field):
            if part is not None:
                part.Destroy()
        self.buttons, self.tabs, self.icons = [], {}, {}
        self.legacy_buttons = self.legacy_mode = None
        self.frame = self.divider = self.jump = self.chip = self.field = None
        self.window = self.r1 = None


def _Nothing():
    pass


def _Bind(method, *args):
    callback = ui.__mem_func__(method)
    return lambda: callback(*args)
