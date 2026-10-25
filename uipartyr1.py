# -*- coding: utf-8 -*-
"""Skupina (uiparty) in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md). Visual only.

uiparty keeps its windows, sizes, positions and every action (target / exchange on click, expel, the EXP distribution
mode, Rozpustit / Opustit, the map tooltip); this module re-skins them in place with uir1skin.Recorder, so a failed
build puts every original back:

* a member row (PartyMemberInfoBoard): the name is plain text in Noto Sans 14 (ivory while the member is online,
  muted when offline) on the row's original name bar, exactly as in "Starý vzhled" (owner 8. 10. 2026: no R1 plate behind
  the name), shortened with "…" only when it is longer than the bar (the full name stays in GetCharacterName); the HP
  gauge under it keeps the game's own colour (the original gauge tile, green while poisoned) in an R1 track without
  the bronze caps (the flat bright red bar was wrong). The role / state button, the party bonus icons and the expel
  button keep their art (they are pictograms of the game);
* the button that opens the menu under the last row (Party_Menu_Open / Close, a dark noisy bar with a faint arrow):
  an R1 plate of its place with a chevron (down = closed, up = open);
* the party menu (PartyMenu): the R1 frame instead of the ThinBoard, the heading in Noto Sans, the two EXP
  distribution modes as R1 plates of their native size (the selected one = the plate with the red line) with a label
  that fits the plate (a smaller size, "…" only for a longer one), the Rozpustit / Opustit icon buttons unchanged.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original rows and menu. A failure is traced
(uir1.TraceFailure), the original look comes back and that part is not dressed again in this session.
"""
import weakref

import ui

import uir1
import uir1tokens as T
import uir1hud
import uir1skin

MEMBER = u'the party member row'
MENU = u'the party menu'
OPENER = u'the party menu button'

NAME_PANEL = (22, 0, 84, 17)        # the uiscript's NameSlot bar (partymemberinfoboard.py), which stays
NAME_FONT = 'text_xs'               # Noto Sans 14: "ThaynostNinjaD" (14 letters) is 77 px, the bar has 79
NAME_X = 2                          # text start inside the bar
NAME_W = 79                         # text width: the bar (84) less 2 px left and 3 px right
ELLIPSIS = u'\u2026'
LINK_COLOR = T.IVORY
UNLINK_COLOR = T.MUTED
MENU_TITLE_COLOR = T.INK_DIM
MENU_TEXT_W = 92                    # the heading inside the 106 px menu
MODE_FAMILY = '100x21'              # the widest R1 plate that fits the 106 px menu (the original 88x21 is too narrow)
MODE_TEXT_W = 96                    # label width inside the plate (2 px on both sides next to the outline)
MODE_MIN_SIZE = 11                  # hardcode-ok: Tahoma 11 = fontconfig ROLE_DENSE, the floor of dense captions
PLATE_STATES = (('normal', 'SetUpVisual'), ('hover', 'SetOverVisual'), ('selected', 'SetDownVisual'))
ORIGINAL_MODE = ('d:/ymir work/ui/public/large_button_01.sub', 'd:/ymir work/ui/public/large_button_02.sub',
                 'd:/ymir work/ui/public/large_button_03.sub')
OPENER_FAMILY = '100x21'            # R1 plate of the opener (its original art is 111 x 20, 5 px wider than the rows)
OPENER_SETTERS = (('SetUpVisual', 'normal'), ('SetOverVisual', 'hover'), ('SetDownVisual', 'pressed'))
OPENER_ORIGINAL = 'd:/ymir work/ui/game/windows/Party_Menu_%s_0%d.sub'


def _Ellipsis(text):
    """The ellipsis for ``text``: "…" for a unicode text (Python 3), three dots for a byte string (Python 2 keeps the
    cp1250 names as bytes and cannot add a unicode character to them)."""
    return ELLIPSIS if isinstance(text, type(u'')) else '...'


def _Plate(state, family=MODE_FAMILY):
    import uicrimsoncontrols
    return uicrimsoncontrols.R1PlateVisual(family, state)


def _SmallerFont(font, step):
    """The same family and flags, ``step`` sizes down (not below MODE_MIN_SIZE). The kit has no smaller role than
    text_xs, so only the size of the kit's own font changes (never a hard-coded family: an old EXE has Tahoma)."""
    family, unused, size = font.rpartition(':')
    digits = ''.join(ch for ch in size if ch.isdigit())
    flags = size[len(digits):]
    return '%s:%d%s' % (family, max(MODE_MIN_SIZE, int(digits or MODE_MIN_SIZE) - step), flags)


def _TextWidth(font, text):
    probe = ui.TextLine()
    probe.SetFontName(font)
    probe.SetText(text)
    return uir1.TextWidth(probe)


class MemberSkin(object):
    """R1 look of one PartyMemberInfoBoard (after its uiscript was loaded and bound)."""

    def __init__(self, board):
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.gauge = None
        self.line = None
        self.fullName = u''
        self.nameWrap = None
        try:
            self._Build(board)
        except Exception:
            self.Undo(board)
            raise

    def _Build(self, board):
        rec, kit = self.rec, uir1.Kit()
        slot = board.GetChild('NameSlot')
        name = board.nameTextLine
        x, y, w, h = NAME_PANEL
        font = kit.font(NAME_FONT)
        # the name moves out of the (original, translucent) bar into the row: drawn over it, never clipped by it
        rec.Parent(name, board, x + NAME_X, y + uir1.CellTop(h, font), slot)
        rec.Font(name, font, uir1hud.Signed(LINK_COLOR), None, uir1hud.Signed(board.LINK_COLOR))
        ref = weakref.ref(board)            # the row holds its skin: no strong way back to the row

        def colours():
            row = ref()
            row.LINK_COLOR = uir1hud.Signed(LINK_COLOR)
            row.UNLINK_COLOR = uir1hud.Signed(UNLINK_COLOR)

        def original_colours():
            row = ref()
            for attr in ('LINK_COLOR', 'UNLINK_COLOR'):
                if row is not None and attr in row.__dict__:
                    delattr(row, attr)
        rec.Call(colours, original_colours)
        self._FitName(board, name)
        self.gauge = uir1hud.GaugeSkin(board.gauge, MEMBER, textured=True)
        rec.Call(lambda: None, self.gauge.Restore)

    def _FitName(self, board, line):
        """The name fits the bar; a longer one ends with "…". The row sets the name through SetCharacterName and
        reads it through GetCharacterName: both keep the full name (the text line shows the fitted one)."""
        self.line = line
        self.fullName = line.GetText()
        me = weakref.ref(self)
        row = weakref.ref(board)            # the row holds its skin: no strong way back to the row

        def after(text, *unused):
            skin = me()
            if skin is not None:
                skin._SetName(text)

        def full_name():
            skin = me()
            return skin.fullName if skin is not None else u''

        def undo():
            if self.nameWrap is not None:
                uir1hud.Unwrap(self.nameWrap)
                self.nameWrap = None
            target = row()
            if target is not None and 'GetCharacterName' in target.__dict__:
                delattr(target, 'GetCharacterName')
            self.line.SetText(self.fullName)
        self.rec.Call(lambda: None, undo)           # registered first: a failure half way is undone too
        self._Fit()
        self.nameWrap = uir1hud.Wrap(board, 'SetCharacterName', after)
        board.GetCharacterName = full_name

    def _SetName(self, text):
        self.fullName = text
        try:
            self._Fit()
        except Exception:
            uir1hud.Fail(MEMBER)
            self.line.SetText(self.fullName)

    def _Fit(self):
        uir1.Fit(self.line, self.fullName, NAME_W, _Ellipsis(self.fullName))

    def Undo(self, board):
        self.rec.Undo()
        uir1skin.Destroy(self.widgets)
        self.widgets = []
        if board.__dict__.get('r1') is self:
            board.r1 = None


class MenuSkin(object):
    """R1 look of the PartyMenu (a ThinBoard built in code)."""

    def __init__(self, menu):
        self.rec = uir1skin.Recorder()
        self.skin = None
        self.menuRef = weakref.ref(menu)
        try:
            self._Build(menu)
        except Exception:
            self.Undo(menu)
            raise

    def _Build(self, menu):
        rec, kit = self.rec, uir1.Kit()
        import uir1frame
        holder = uir1frame._BoardSkin(uir1, menu, kit, kind='window')     # weak board, restorable half way
        self.skin = holder.skin
        rec.Call(lambda: None, holder.Restore)
        rec.Font(menu.modeTitle, kit.font('text_s'), uir1hud.Signed(MENU_TITLE_COLOR))
        self._Shorten(menu.modeTitle, MENU_TEXT_W)
        buttons = list(menu.modeButtonList.values())
        for button in buttons:
            rec.Visuals(button, [_Plate(state) for state, unused in PLATE_STATES], ORIGINAL_MODE)
        self._Labels(buttons, kit.font(NAME_FONT))

    def _Shorten(self, line, width):
        """``line`` ends with "…" when it is wider than ``width`` (the original text comes back on Undo)."""
        text = line.GetText()
        uir1.Fit(line, text, width, _Ellipsis(text))

        def undo():
            line.SetText(text)
        self.rec.Call(lambda: None, undo)

    def _Labels(self, buttons, font):
        """The labels of the two modes in one size that fits the plate: "Rovnoměrné rozložení" is 109 px in the
        original font, 100 px in Tahoma 12 and 91 px in Tahoma 11 (GDI), the plate has 96. Steps down to MODE_MIN_SIZE,
        then "…"."""
        rec = self.rec
        buttons = [button for button in buttons if getattr(button, 'ButtonText', None) is not None]
        if not buttons:
            return
        texts = [button.ButtonText.GetText() for button in buttons]
        chosen = font
        for step in range(8):
            chosen = _SmallerFont(font, step)
            if max(_TextWidth(chosen, text) for text in texts) <= MODE_TEXT_W:
                break
            if _SmallerFont(font, step + 1) == chosen:      # MODE_MIN_SIZE reached
                break
        plate_w = T.SIZES['plate/button_%s_normal.png' % MODE_FAMILY][0]
        for button, text in zip(buttons, texts):
            line = button.ButtonText
            ox, oy = line.GetLocalPosition()
            original_font = getattr(button, 'fontName', None)
            uir1.SetFont(line, chosen)
            line.SetPosition(plate_w // 2, oy)               # the caption was centred in the 88 px art at SetText
            uir1.Fit(line, text, MODE_TEXT_W, _Ellipsis(text))

            def undo(line=line, text=text, ox=ox, oy=oy, original_font=original_font):
                line.SetText('')
                if original_font is None:
                    line.SetDefaultFontName()
                else:
                    line.SetFontName(original_font)
                line.SetText(text)
                line.SetPosition(ox, oy)
            rec.Call(lambda: None, undo)

    def Resize(self, w, h):
        if self.skin is None:
            return
        try:
            self.skin.Resize(w, h)
        except Exception:
            uir1hud.Fail(MENU)
            menu = self.menuRef()
            if menu is not None:
                self.Undo(menu)

    def Undo(self, menu):
        self.rec.Undo()
        self.skin = None
        if menu.__dict__.get('r1') is self:
            menu.r1 = None


class OpenerSkin(object):
    """R1 look of the button that opens / closes the party menu (PartyWindow.partyMenuButton).

    The window sets its Party_Menu_Open_0x / Party_Menu_Close_0x visuals itself on every toggle: the three setters of
    the button are wrapped, a visual of that art becomes the R1 plate of the same state and the chevron follows
    (down = closed, up = open). The button keeps its place, its event and its hit box (the plate is 100 x 21 instead
    of the 111 x 20 art, centred in the same place)."""

    def __init__(self, window):
        self.rec = uir1skin.Recorder()
        self.chevron = None
        self.direction = None
        self.originals = {}                 # setter -> the original art the window asked for last
        self.button = window.partyMenuButton
        self.windowRef = weakref.ref(window)
        try:
            self._Build(window)
        except Exception:
            self.Undo(window)
            raise

    def _Build(self, window):
        rec, button = self.rec, self.button
        plate_w, plate_h = T.SIZES['plate/button_%s_normal.png' % OPENER_FAMILY]
        chevron = T.CHEVRON
        self.chevron = uir1.Image(button, uir1.ChevronPath('down'), (plate_w - chevron) // 2,
                                  (plate_h - chevron) // 2)
        self.direction = 'down'
        me = weakref.ref(self)
        records = []

        def hook(setter, state):
            def after(filename, *unused):
                skin = me()
                if skin is not None:
                    skin._Visual(setter, state, filename)
            return after

        def undo():
            for record in reversed(records):
                uir1hud.Unwrap(record)
            del records[:]
            for index, (setter, state) in enumerate(OPENER_SETTERS):
                original = self.originals.get(setter) or OPENER_ORIGINAL % ('Open', index + 1)
                getattr(button.__class__, setter)(button, original)
        rec.Call(lambda: None, undo)                # registered first: a failure half way is undone too
        for setter, state in OPENER_SETTERS:
            records.append(uir1hud.Wrap(button, setter, hook(setter, state)))
        menu = window.partyMenu
        self._Sync(menu is not None and menu.IsShow())

    def _Sync(self, opened):
        """The current art of the window's state: the R1 plates and the chevron."""
        for index, (setter, state) in enumerate(OPENER_SETTERS):
            self._Visual(setter, state, OPENER_ORIGINAL % ('Close' if opened else 'Open', index + 1))

    def _Visual(self, setter, state, filename):
        name = str(filename).replace('\\', '/').rsplit('/', 1)[-1].lower()
        if not (name.startswith('party_menu_open_') or name.startswith('party_menu_close_')):
            return
        self.originals[setter] = filename
        try:
            getattr(self.button.__class__, setter)(self.button, _Plate(state, OPENER_FAMILY))
            direction = 'up' if name.startswith('party_menu_close_') else 'down'
            if direction != self.direction and self.chevron is not None:
                self.direction = direction
                self.chevron.LoadImage(uir1.ROOT + uir1.ChevronPath(direction))
        except Exception:
            uir1hud.Fail(OPENER)
            window = self.windowRef()
            if window is not None:
                self.Undo(window)

    def Undo(self, window):
        self.rec.Undo()
        if self.chevron is not None:
            try:
                self.chevron.Hide()
            except Exception:
                pass
        self.chevron = None
        if window.__dict__.get('r1Opener') is self:
            window.r1Opener = None


def DressMember(board):
    """The R1 look of a party member row, or None (original look / failure: traced, the original row)."""
    if not uir1hud.UseR1(MEMBER):
        return None
    try:
        skin = MemberSkin(board)
        board.r1 = skin
        return skin
    except Exception:
        uir1hud.Fail(MEMBER)
        return None


def DressMenu(menu):
    """The R1 look of the party menu, or None (original look / failure: traced, the original menu)."""
    if not uir1hud.UseR1(MENU):
        return None
    try:
        skin = MenuSkin(menu)
        menu.r1 = skin
        return skin
    except Exception:
        uir1hud.Fail(MENU)
        return None


def DressOpener(window):
    """The R1 look of the party menu button (window = PartyWindow), or None (original look / failure: traced)."""
    if not uir1hud.UseR1(OPENER):
        return None
    try:
        skin = OpenerSkin(window)
        if skin.chevron is None:            # failed (and undone) while it was built
            return None
        window.r1Opener = skin
        return skin
    except Exception:
        uir1hud.Fail(OPENER)
        return None
