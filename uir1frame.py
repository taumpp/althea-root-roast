# -*- coding: utf-8 -*-
"""The shared R1 window frame ("Krvavá žíla", docs/ALTHEA_R1_KIT.md) for original windows that keep their layout and
need only the R1 frame: the graphite frame with the bronze hairline, the R1 header (the title in Cinzel, the red vein,
the plain X) and the R1 background, drawn INTO the window's own board by uir1.BoardSkin. Nothing of the window's
content is re-created, moved or re-parented, so every control and event keeps working.

REGISTRY lists the windows by (module, class), not by uiscript file: one uiscript can be loaded by several classes
(questiondialog2.py by uicommon, which has its own R1 look in uir1dialog). Two ways in:

* ui.PythonScriptLoader.LoadScriptFile calls Loaded(window) after it loaded a uiscript (guarded: an exception inside
  the loader aborts the client). Every other window costs one dict lookup.
* a window built in code (a ui.BoardWithTitleBar subclass) calls Dress(self) at the end of its setup.

The adapters work for windows that wire their events and texts AFTER the uiscript was loaded:

* the R1 X calls the original close button (its event is read at click time);
* the R1 title follows the original title text (its SetText is wrapped on the instance, so SetTitleName and
  GetChild("TitleName").SetText both reach it) and is shortened to the room beside the X (uir1.Fit);
* the frame follows a later board.SetSize (the refine and attach-stone boards are 0 wide in their uiscript);
* the original title bar stays shown as the invisible drag handle, every title bar of the board (a uiscript TitleBar
  next to the board's own one included) is hidden; ``keep`` keeps chosen title bar children (help, minimize) visible
  and clickable above the R1 header;
* the original buttons of the uiscript (middle_button, xlarge_button, ...) get the R1 plates of the same native size:
  the loader opens uicrimsoncontrols' R1 plate scope while such a window loads (UsesPlates); the label keeps its font.

Settings -> "Starý vzhled" (settingslook 'legacy') keeps the original window untouched. Any exception: traced
(uir1.TraceFailure), the original look comes back and that class is not tried again in this session.
"""
import weakref

# (module, class) -> options. The module name is lower case: the client imports some modules in mixed case
# (uiExchange, uiPickMoney, uiSafebox).
#   board:  the board's name in the window's uiscript (ElementDictionary); None = the window is the board itself (a
#           ui.BoardWithTitleBar built in code that calls Dress(self))
#   header: False = the frame only, no header and no X (a window without a title bar)
#   close:  False = the header without the X (a window that must stay open: the CAPTCHA)
#   keep:   names of title bar children that stay visible and clickable above the R1 header (help "?", minimize)
#   panels: names of inner thin boards drawn as R1 panels (a dark well with a thin outline)
#   frame:  False = no frame, only the R1 plates for the original buttons (a full-screen overlay: the help window)
#   plates: False = the original buttons keep the crimson families
#   slots:  {name: original slot base} of the item slot windows (a uiscript child, else an attribute of a window built
#           in code) that get the R1 item slot C as their slot base image (uir1.SLOT_CELL) when the frame is drawn; a
#           slot base the window sets in code later goes through SetSlotBase(window, slot, original)
#   plate_paths: {explicit button path prefix: R1 plate family} - buttons the uiscript names by an explicit path
#           (unified crimson families, own art) that get the R1 plate of that family too (the families are listed in
#           uicrimsoncontrols.R1_EXTRA_PLATE_SIZES unless ALIAS_GROUPS has them)
#   texts:  {name: (role, colour token, smaller roles)} - uiscript text lines without "fontname" drawn in the R1 font
#           (uir1.Kit role) and colour (a uir1tokens name); while the text is wider than the board minus 2 * PAD the
#           line steps down through the smaller roles (checked again on every SetText; 'tahoma' = the original size)
#   move:   {name: (x, y)} uiscript children placed elsewhere while the frame is drawn (a child aligned in the
#           uiscript keeps its alignment: x / y are relative to it, as in the uiscript)
#   hide:   names of uiscript children hidden while the frame is drawn (an inner board the R1 frame replaces)
#   bare:   names of inner boards (thin boards holding controls) drawn without their own frame and fill
#   native: {name: image} of uiscript images drawn from their own texture while the frame is drawn, the way a button
#           with the same image is drawn: ui.ImageBox.LoadImage puts the old crimson art of ui.V31_IMAGE_VISUALS in
#           place of some public images (parameter_slot_* -> crimson/controls/inputs, a dark well with a red-brown
#           rim), ui.Button does not. Same native size; Undo loads the image through ImageBox.LoadImage again
SLOT_BASE = 'd:/ymir work/ui/public/Slot_Base.sub'
EXCHANGE_SLOT_BASE = 'd:/ymir work/ui/game/exchange/original/slot_base.sub'
UNIFIED = 'd:/ymir work/ui/public/crimson/controls/unified/'
SELECT_SKILL = 'd:/ymir work/ui/game/select_skill/'
SKILL_JOB = 'd:/ymir work/ui/skill_slot_job_%d.tga'
YANG_FIELD = 'd:/ymir work/ui/public/parameter_slot_04.sub'
REGISTRY = {
    # the client loads exchangedialog_new.py (ENABLE_NEW_EXCHANGE_WINDOW); its Refresh sets the slot bases again.
    # The yang fields: the own one is a button (Owner_Money, opens the amount dialog), the trade partner's one an
    # image (Target_Money) - drawn from the same parameter_slot_04.sub like the button, not from the crimson V31 well
    ('uiexchange', 'ExchangeDialog'): dict(board='board', panels=('ExchangeLogs',),
                                           slots={'Owner_Slot': EXCHANGE_SLOT_BASE, 'Target_Slot': EXCHANGE_SLOT_BASE},
                                           native={'Target_Money': YANG_FIELD}),
    ('uirefine', 'RefineDialogNew'): dict(board='Board', slots={'CurrentItemSlot': SLOT_BASE,
                                                                'ResultItemSlot': SLOT_BASE}),
    ('uipickmoney', 'PickMoneyDialog'): dict(board='board'),
    ('uipicketc', 'PickETCDialog'): dict(board='board'),
    ('uisplititem', 'SplitItemDialog'): dict(board='board'),
    ('uiattachmetin', 'AttachMetinDialog'): dict(board='Board'),
    ('uirestart', 'RestartDialog'): dict(board='board', header=False),
    ('uisafebox', 'PasswordDialog'): dict(board='board'),
    ('uisafebox', 'ChangePasswordDialog'): dict(board='board'),
    ('uichestdrop', 'ChestDropWindow'): dict(board='board', panels=('CurrentPageBack',)),
    ('uiequipmentdialog', 'EquipmentDialog'): dict(board='Board'),
    ('uirarity', 'RarityDialog'): dict(board='Board', slots={'CurrentItemSlot': SLOT_BASE,
                                                             'ResultItemSlot': SLOT_BASE}),
    ('uiselectitem', 'SelectItemWindow'): dict(board='board', slots={'ItemSlot': SLOT_BASE}),
    # "Okno vylepšení dovedností" / "Čtení knih": the six skill slots (the octagon Slot_Base.sub of the engine) and
    # the item cells the window makes in code (SetCellImage: book / soul stone, the reading items, the Zen bean)
    # become the R1 item slot C
    ('uiskillupgrade', 'SkillUpgradeWindow'): dict(board='board', panels=('ThinBoardSkill',),
                                                   slots={'SkillSlots': SLOT_BASE}),
    # "Vylepšování buffy" (uibuffupgrade.SupportUpgrade): the same window for the Buffi skills (skillupgrade.py)
    ('uibuffupgrade', 'SupportUpgrade'): dict(board='board', panels=('ThinBoardSkill',),
                                              slots={'SkillSlots': SLOT_BASE}),
    ('uimountfeed', 'MountFeedWindow'): dict(board=None, slots={'grid': SLOT_BASE}),
    ('uicontracthandin', 'ContractHandInWindow'): dict(board=None, hide=('body',), slots={'grid': SLOT_BASE},
        texts={'nameText': ('text', 'INK', ('text_s',)), 'hintText': ('text_xs', 'MUTED', ()),
               'piecesText': ('text', 'INK', ('text_s',)), 'statusText': ('text_xs', 'MUTED', ())}),   # okno odevzdání zakázky (bez záznamu zůstával starý vzhled)
    ('uiskilltreedismantle', 'SkillTreeDismantleWindow'): dict(board=None, slots={'grid': SLOT_BASE}),
    ('uihelp', 'HelpWindow'): dict(board=None, frame=False),
    # "Kořist - <dungeon>" (uidungeondrop, the boss loot opened from Dungeony): the frame here, the slot C cells,
    # the texts and the R1 scroll bar in the companion uir1dungeondrop (the window is built in code)
    ('uidungeondrop', 'DungeonDropWindow'): dict(board=None),
    # "Zahodit předmět" (uicommon.QuestionDropDialog) is not here: its compact R1 dialog with a header is
    # root/uir1dropdialog.py (owner 8. 10. 2026, DEV 74)
    # "Nákup více kusů" (uicommon.BuyMultipleDialog) is not here either: root/uir1dropdialog.py (BuyDialogSkin)
    # "Zlepšení svitkem" (uiinventory: a scroll on an item, weapon enhancement): the item tooltip inside stays as is
    ('uirefine', 'RefineDialog'): dict(board='Board'),
    # "Výběr specializace" (level 5): the face box would sit under the header vein - hidden, the name line centred;
    # the skill rows' backs (skill_slot_job_1/2.tga, missing in the client: nothing was drawn) become the item slot C
    # under every skill icon; the select buttons (own 262x23 art) R1 plates
    # Theowahdan's item windows: Kombinování / Bonus absorpce (šerpy, pečetě),
    # Kostým s aurou: Přenos hodnot / Evoluce, Proměna. The frame here; the slots, captions, price and buttons in the
    # companion root/uir1theowahdan.py (each window calls its Dress after wiring the uiscript)
    ('uiacce', 'CombineWindow'): dict(board='board'),
    ('uiacce', 'AbsorbWindow'): dict(board='board'),
    ('uiaura', 'AuraWindow'): dict(board='board'),
    ('uichangelook', 'ChangeLookWindow'): dict(board='board'),
    ('uiselectskill', 'SkillSelectWindow'): dict(board='Board', hide=('RaceImage', 'RaceSlot'),
                                                 move={'InfoTextSlot': (85, 34), 'FirstSkillSlotBack': (19, 69),
                                                       'SecondSkillSlotBack': (19, 154)},
                                                 plate_paths={SELECT_SKILL + 'btn_select_': '262x23'},
                                                 slots={'FirstSkillSlotBack': SKILL_JOB % 1,
                                                        'SecondSkillSlotBack': SKILL_JOB % 2}),
}

ORIGINAL_FONT = 'Tahoma:12'  # a text line without SetDefaultFontName (the client's default font, localeInfo.UI_DEF_FONT)
TITLE_MARGIN = 10       # px between the title and the frame side (uir1layout.header)
KEEP_GAP = 4            # px between the title and a kept title bar control

_FAILED = set()         # classes whose R1 frame failed in this session: the original look, never tried again


def Key(window):
    cls = window.__class__
    return (str(getattr(cls, '__module__', '') or '').lower(), cls.__name__)


def Loaded(window):
    """A uiscript was loaded into ``window`` (ui.PythonScriptLoader.LoadScriptFile): the R1 frame when its class is in
    REGISTRY. One dict lookup for every other window."""
    if Key(window) not in REGISTRY:
        return None
    return Dress(window)


def SetSlotBase(window, slot, original, r=1.0, g=1.0, b=1.0, a=1.0):
    """A window of REGISTRY sets the slot base image of one of its item slot windows in code: the R1 item slot C
    (with the same tint) while the R1 frame dresses the window - Undo puts ``original`` back -, ``original`` in the
    original look and after a frame failure."""
    skin = None
    try:
        skin = window.__dict__.get('r1frame')
    except Exception:
        skin = None
    if skin is not None:
        try:
            skin.SetSlot(slot, original, (r, g, b, a))
            return
        except Exception:
            pass
    slot.SetSlotBaseImage(original, r, g, b, a)


def SetCellImage(window, image, original):
    """A window of REGISTRY loads the background of a single item cell (an ImageBox under an item icon, made in code
    or by its uiscript): the R1 item slot C while the R1 frame dresses the window - Undo loads ``original`` again -,
    ``original`` in the original look and after a frame failure."""
    skin = None
    try:
        skin = window.__dict__.get('r1frame')
    except Exception:
        skin = None
    if skin is not None:
        try:
            skin.SetCell(image, original)
            return
        except Exception:
            pass
    image.LoadImage(original)


def UsesPlates(window):
    """True when the uiscript of ``window`` is to be loaded with the R1 plates for its original buttons
    (ui.PythonScriptLoader.LoadScriptFile opens uicrimsoncontrols' plate scope around its children)."""
    key = Key(window)
    opts = REGISTRY.get(key)
    if opts is None or key in _FAILED or not opts.get('plates', True):
        return False
    import uir1
    return bool(uir1.UseR1())


def PlatePaths(window):
    """{explicit button path prefix: R1 plate family} of ``window`` (REGISTRY option ``plate_paths``) for the R1 plate
    scope of its load; {} for every other window."""
    opts = REGISTRY.get(Key(window))
    return dict((opts or {}).get('plate_paths') or {})


PLATE_SETTERS = (('normal', 'SetUpVisual'), ('hover', 'SetOverVisual'), ('pressed', 'SetDownVisual'),
                 ('disabled', 'SetDisableVisual'))


def _Widgets(window):
    """The uiscript widgets of a window: its ElementDictionary and every Children list, once each."""
    seen, out = set(), []
    stack = list((getattr(window, 'ElementDictionary', None) or {}).values()) + list(getattr(window, 'Children', None) or ())
    while stack:
        widget = stack.pop()
        if id(widget) in seen or not hasattr(widget, '__dict__'):
            continue
        seen.add(id(widget))
        out.append(widget)
        stack.extend(getattr(widget, 'Children', None) or ())
    return out


def RestorePlates(window):
    """The original visuals again on every button that got an R1 plate while the window loaded (ui.Button records the
    original names in r1PlateSources); set outside the plate scope they resolve as before."""
    for widget in _Widgets(window):
        sources = widget.__dict__.pop('r1PlateSources', None)
        if not sources:
            continue
        for state, setter in PLATE_SETTERS:
            if state in sources:
                getattr(widget, setter)(sources[state])
        if 'normal' in sources and 'disabled' not in sources:    # the plate's disabled visual came with the normal one
            widget.SetDisableVisual(_UnifiedDisabled(sources['normal']) or sources['normal'])


def _UnifiedDisabled(path):
    """The disabled visual of an explicit unified crimson family (ui.Button.SetUpVisual sets it with the normal one),
    None for every other path."""
    try:
        import uicrimsoncontrols
        if uicrimsoncontrols.IsUnifiedVisual(path) and not uicrimsoncontrols.IsR1PlateVisual(path):
            return uicrimsoncontrols.StateVisual(path, 'disabled')
    except Exception:
        pass
    return None


def _OriginalFont(line):
    """The client's default font and the white of a uiscript text line without "fontname" / colour again (laid out
    again: the engine keeps the glyphs of the old font until the text changes)."""
    text = line.GetText()
    line.SetText('')
    if hasattr(line, 'SetDefaultFontName'):
        line.SetDefaultFontName()
    else:
        line.SetFontName(ORIGINAL_FONT)
    line.SetText(text)
    line.SetPackedFontColor(_Signed(0xFFFFFFFF))
    line.__dict__.pop('_r1frame_font', None)


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def _LoadNative(image_box, image):
    """``image`` into a ui.ImageBox as the engine loads it (wndMgr.LoadImage), without ui.ImageBox.LoadImage's swap
    for the crimson V31 art: the texture a ui.Button with this image shows, in its native size."""
    import wndMgr
    wndMgr.LoadImage(image_box.hWnd, image)
    image_box.name = image


def Dress(window, opts=None):
    """The R1 frame drawn into ``window`` (``opts`` from REGISTRY when not given). Returns the FrameSkin, or None: the
    original look ("Starý vzhled"), a window this module does not know, a class that failed before, a board the
    loaded uiscript does not have. Never raises."""
    key = None
    try:
        key = Key(window)
        if opts is None:
            opts = REGISTRY.get(key)
        old = window.__dict__.get('r1frame')
        if old is not None:                      # another uiscript loaded into the same window
            window.r1frame = None
            old.Undo(plates=False)
        if opts is None or key in _FAILED or not opts.get('frame', True):
            return None
        import uir1
        if not uir1.UseR1():
            return None
        board = _Board(window, opts)
        if board is None:
            RestorePlates(window)                # a uiscript without the board: no R1 at all
            return None
        skin = FrameSkin(window, board, opts, key)
        window.r1frame = skin
        return skin
    except Exception:
        _Failed(key)
        try:
            RestorePlates(window)
        except Exception:
            pass
        return None


def _Failed(key):
    try:
        import uir1
        uir1.TraceFailure('the frame of %s.%s' % (key or ('?', '?')))
    except Exception:
        pass
    _FAILED.add(key)


def _Child(window, name):
    children = getattr(window, 'ElementDictionary', None) or {}
    return children.get(name)


def _Board(window, opts):
    name = opts.get('board')
    return window if name is None else _Child(window, name)


def _ScriptChildren(widget):
    """The uiscript children of a window (ui.PythonScriptLoader.LoadChildren keeps them in ``Children``)."""
    children = getattr(widget, 'Children', None)
    return [child for child in (children or ()) if hasattr(child, 'IsShow')]


def _IsTitleBar(widget):
    return getattr(widget, 'imgCenter', None) is not None and hasattr(widget, 'btnClose')


def _TitleBars(window, board):
    """Every title bar of the board: its own (BoardWithTitleBar.titleBar) and the uiscript TitleBar children of the
    board and of the window (a board with both shows two bars in the original)."""
    bars = []
    for widget in [getattr(board, 'titleBar', None)] + _ScriptChildren(board) + _ScriptChildren(window):
        if widget is not None and _IsTitleBar(widget) and widget not in bars:
            bars.append(widget)
    return bars


def _TitleLine(board, bars):
    line = getattr(board, 'titleName', None)
    if line is not None:
        return line
    for bar in bars:
        for child in _ScriptChildren(bar):
            if hasattr(child, 'GetText') and hasattr(child, 'SetText') and not hasattr(child, 'SetEvent'):
                return child
    return None


def _Wrap(target, name, after):
    """``target.<name>`` (an instance attribute) runs the original method, then ``after()``. Weak references only: a
    wrapper on the window that held the window strongly would make a reference cycle of objects with __del__ (ui.Window),
    which Python 2 never frees. Returns the undo record."""
    own = target.__dict__.get(name)
    ref = weakref.ref(target)
    if own is not None:
        original = own
    else:
        function = getattr(target.__class__, name)

        def original(*args):
            obj = ref()
            return function(obj, *args) if obj is not None else None

    def wrapper(*args):
        result = original(*args)
        after()
        return result
    setattr(target, name, wrapper)
    return (ref, name, own)


def _Unwrap(record):
    ref, name, own = record
    target = ref()
    if target is None:
        return
    if own is not None:
        setattr(target, name, own)
    elif name in target.__dict__:
        delattr(target, name)


class _BoardSkin(object):
    """uir1.BoardSkin that can be restored also when its constructor raised half way, holding its board weakly."""

    def __init__(self, uir1, board, kit, **kwargs):
        skin = uir1.BoardSkin.__new__(uir1.BoardSkin)
        skin.board, skin.hidden, skin.frame, skin.header, skin.base = board, [], None, None, None
        self.skin = skin
        try:
            uir1.BoardSkin.__init__(skin, board, kit, **kwargs)
        except Exception:
            skin.board = weakref.proxy(board)
            self.Restore()                           # what was hidden before the failure comes back
            raise
        skin.board = weakref.proxy(board)            # the window holds its skin: no strong way back to it

    def Restore(self):
        skin = self.skin
        if skin.frame is None and skin.header is None and not skin.hidden:
            return
        if skin.frame is None:                       # failed before the frame: no base to bring back
            for widget in skin.hidden:
                widget.Show()
            skin.hidden = []
            return
        skin.Restore()


class FrameSkin(object):
    """The R1 frame of one window (see the module doc). Undo() brings the original look back."""

    def __init__(self, window, board, opts, key):
        import uir1
        import uir1layout
        self.R, self.L = uir1, uir1layout
        self.key = key
        self.window = weakref.proxy(window)
        self.wrapped = []           # undo records of _Wrap
        self.kept = []              # (widget ref, bar ref, local position in the bar)
        self.skins = []             # _BoardSkin of the frame, then of the panels
        self.bars = []              # weak refs of the original title bars (the X calls their close button)
        self.title_line = None
        self.slots = {}             # id(slot window) -> (its weak ref, original slot base, tint): Undo restores them
        self.cells = {}             # id(image) -> (its weak ref, original image): the item cells of SetCellImage
        self.undo = []              # undo functions of the options hide / bare / move / texts (newest last)
        self.texts = []             # (weak ref of a re-fonted line, role, colour, smaller role)
        self.frame = None           # the uir1.BoardSkin of the window frame
        try:
            self._Build(window, board, opts)
        except Exception:
            self.Undo()
            raise

    # build -----------------------------------------------------------------------------------------------------
    def _Build(self, window, board, opts):
        R = self.R
        kit = R.Kit()
        header = opts.get('header', True)
        bars = _TitleBars(window, board) if header else []
        keep = [w for w in (_Child(window, name) for name in opts.get('keep', ())) if w is not None]
        me = weakref.ref(self)

        def close():
            skin = me()
            if skin is not None:
                skin.Close()
        closable = header and opts.get('close', True)
        frame = _BoardSkin(R, board, kit, title='' if header else None, on_close=close if closable else None,
                            hide=[bar for bar in bars if bar is not getattr(board, 'titleBar', None)])
        self.skins.append(frame)
        self.frame = frame.skin
        self.bars = [weakref.ref(bar) for bar in bars]
        for widget in keep:
            self._Keep(board, bars, widget)
        for name in opts.get('panels', ()):
            panel = _Child(window, name)
            if panel is not None:
                self.skins.append(_BoardSkin(R, panel, kit, kind='panel'))
                self._Follow(panel, len(self.skins) - 1)
        for name, original in sorted((opts.get('slots') or {}).items()):
            slot = _Child(window, name)
            if slot is None:
                slot = window.__dict__.get(name)
            if slot is not None and hasattr(slot, 'SetSlotBaseImage'):
                self.SetSlot(slot, original)
        self._Options(window, opts, kit)
        self._Follow(board, 0)
        if header:
            line = _TitleLine(board, bars)
            if line is not None:
                self.title_line = weakref.ref(line)

                def changed():
                    skin = me()
                    if skin is not None:
                        skin._Changed()
                self.wrapped.append(_Wrap(line, 'SetText', changed))
            self.Title()

    def _Options(self, window, opts, kit):
        """hide / bare / move / native / texts (see REGISTRY), each change recorded for Undo."""
        for name in opts.get('hide', ()):
            widget = _Child(window, name)
            if widget is not None and widget.IsShow():
                widget.Hide()
                self.undo.append(widget.Show)
        for name in opts.get('bare', ()):
            board = _Child(window, name)
            if board is None:
                continue
            for widget in list(getattr(board, 'Corners', None) or ()) + list(getattr(board, 'Lines', None) or ()) + \
                    [getattr(board, 'Base', None)]:
                if widget is not None and widget.IsShow():
                    widget.Hide()
                    self.undo.append(widget.Show)
        for name, (x, y) in sorted((opts.get('move') or {}).items()):
            widget = _Child(window, name)
            if widget is None:
                continue
            ox, oy = widget.GetLocalPosition()
            widget.SetPosition(int(x), int(y))
            self.undo.append(lambda widget=widget, ox=ox, oy=oy: widget.SetPosition(ox, oy))
        for name, image in sorted((opts.get('native') or {}).items()):
            widget = _Child(window, name)
            if widget is None or not hasattr(widget, 'LoadImage'):
                continue
            self.undo.append(lambda widget=widget, image=image: widget.LoadImage(image))
            _LoadNative(widget, image)
        me = weakref.ref(self)
        for name, (role, color, smaller) in sorted((opts.get('texts') or {}).items()):
            line = _Child(window, name)
            if line is None:
                continue
            self.undo.append(lambda line=line: _OriginalFont(line))
            self.texts.append((weakref.ref(line), role, getattr(self.R.T, color), smaller))
            if smaller:
                def changed():
                    skin = me()
                    if skin is not None:
                        skin._Changed()
                self.wrapped.append(_Wrap(line, 'SetText', changed))
        self.kit = kit
        self.Texts()

    def Texts(self):
        """The R1 font of the ``texts`` lines; a line wider than the board minus 2 * PAD steps down to its smaller
        role."""
        if not self.texts or self.__dict__.get('fitting'):
            return
        self.fitting = True                  # uir1.SetFont empties the text: its SetText must not fit again
        try:
            self._Fit()
        finally:
            self.fitting = False

    def _Fit(self):
        room = self.frame.board.GetWidth() - 2 * self.R.T.PAD
        for ref, role, color, smaller in self.texts:
            line = ref()
            if line is None:
                continue
            font = self.kit.font(role)
            if getattr(line, '_r1frame_font', None) != font:
                self.R.SetFont(line, font)
                line._r1frame_font = font
            for step in smaller or ():
                if self.R.TextWidth(line) <= room:
                    break
                font = self.kit.font(step)
                self.R.SetFont(line, font)
                line._r1frame_font = font
            line.SetPackedFontColor(_Signed(color))

    def _Keep(self, board, bars, widget):
        """A title bar child that stays (help "?", minimize): shown again and moved onto the board after the R1
        header, so it draws above the vein and takes its clicks before the header's grip (the drag handle over the
        whole row). Only uiscript children of a title bar can be kept (the engine keeps no Python parent)."""
        owner = None
        for bar in bars:
            if any(child is widget for child in _ScriptChildren(bar)):
                owner = bar
        if owner is None:
            return
        skin = self.frame
        skin.hidden = [hidden for hidden in skin.hidden if hidden is not widget]
        at = widget.GetLocalPosition()
        bx, by = owner.GetLocalPosition()
        widget.SetParent(board)
        widget.SetPosition(bx + at[0], by + at[1])
        widget.Show()
        self.kept.append((weakref.ref(widget), weakref.ref(owner), at))

    def _Follow(self, board, index):
        me = weakref.ref(self)

        def resized():
            skin = me()
            if skin is not None:
                skin._Resized(index)
        self.wrapped.append(_Wrap(board, 'SetSize', resized))

    # adapters --------------------------------------------------------------------------------------------------
    def SetSlot(self, slot, original, tint=(1.0, 1.0, 1.0, 1.0)):
        """The R1 item slot C as the slot base of an item slot window of the window (the engine grid unchanged)."""
        slot.SetSlotBaseImage(self.R.SLOT_CELL, *tint)
        self.slots[id(slot)] = (weakref.ref(slot), original, tuple(tint))

    def SetCell(self, image, original):
        """The R1 item slot C (32 x 32, the size of the original cell) as the background image of one item cell."""
        image.LoadImage(self.R.SLOT_CELL)
        self.cells[id(image)] = (weakref.ref(image), original)

    def Close(self):
        """The R1 X: the original close button's event as the window wired it (after loading its uiscript)."""
        buttons = [getattr(ref(), 'btnClose', None) for ref in self.bars if ref() is not None]
        buttons = [button for button in buttons if button is not None]
        for button in buttons:
            if getattr(button, 'eventFunc', None) or getattr(button, 'event', None):
                button.CallEvent()
                return
        if buttons:
            buttons[0].CallEvent()

    def _Changed(self):
        try:
            self.Texts()
            self.Title()
        except Exception:
            self.Fail()

    def _Resized(self, index):
        try:
            holder = self.skins[index]
            skin = holder.skin
            board = skin.board
            skin.Resize(board.GetWidth(), board.GetHeight())
            if index == 0:
                self.Title()
        except Exception:
            self.Fail()

    def Room(self):
        """Width the title may take: centred, clear of the X and of the kept title bar controls."""
        header = self.frame.header
        w = header.GetWidth()
        layout = self.L.header(w, 0, header.close is not None)
        right = layout['close'][0] - 4 if layout['close'] else w - TITLE_MARGIN
        room = right - TITLE_MARGIN
        centre = w // 2
        for ref, bar, at in self.kept:
            widget = ref()
            if widget is None or not widget.IsShow():
                continue
            x = widget.GetLocalPosition()[0]
            if x + widget.GetWidth() <= centre:
                room = min(room, 2 * (centre - (x + widget.GetWidth()) - KEEP_GAP))
            else:
                room = min(room, 2 * (x - centre - KEEP_GAP))
        return max(0, room)

    def Title(self):
        header = self.frame.header
        if header is None:
            return
        line = self.title_line() if self.title_line else None
        text = (line.GetText() if line is not None else '') or ''
        shown = self.R.Fit(header.title, self.R.Upper(text), self.Room())
        header.SetTitle(shown)

    # teardown --------------------------------------------------------------------------------------------------
    def Fail(self):
        """An adapter raised after the frame was built: traced, the original look back, not tried again."""
        _Failed(self.key)
        self.Undo()

    def Undo(self, plates=True):
        """The original look: the wrappers removed, kept controls back on their title bar, the boards restored, the
        original button visuals back (not when the window just loaded another uiscript: its buttons are new)."""
        wrapped, self.wrapped = self.wrapped, []
        for record in reversed(wrapped):
            try:
                _Unwrap(record)
            except Exception:
                pass
        undo, self.undo, self.texts = self.undo, [], []
        for function in reversed(undo):
            try:
                function()
            except Exception:
                pass
        kept, self.kept = self.kept, []
        for ref, bar, at in kept:
            widget, owner = ref(), bar() if bar is not None else None
            try:
                if widget is not None and owner is not None:
                    widget.SetParent(owner)
                    widget.SetPosition(*at)
            except Exception:
                pass
        skins, self.skins = self.skins, []
        for skin in reversed(skins):
            try:
                skin.Restore()
            except Exception:
                pass
        slots, self.slots = self.slots, {}
        for ref, original, tint in slots.values():
            slot = ref()
            try:
                if slot is not None:
                    slot.SetSlotBaseImage(original, *tint)
            except Exception:
                pass
        cells, self.cells = self.cells, {}
        for ref, original in cells.values():
            image = ref()
            try:
                if image is not None:
                    image.LoadImage(original)
            except Exception:
                pass
        try:
            if plates:
                RestorePlates(self.window)
        except Exception:
            pass
        try:
            if self.window.__dict__.get('r1frame') is self:
                self.window.r1frame = None
        except Exception:
            pass
