# -*- coding: utf-8 -*-
"""The item windows of Theowahdan's menu in the R1 look: Kombinování and Bonus absorpce (uiacce: šerpy and pečetě), Kostým s aurou: Přenos hodnot and
Evoluce (uiaura) and Proměna (uichangelook, also the mount transformation).

The frame, the header (title in Cinzel, the red vein, the plain X) and the background are the shared R1 frame
(uir1frame.REGISTRY, drawn when the uiscript loads). This companion draws the inside after the window wired its
uiscript (Dress):

* the old slot picture (stone, ornaments, the bronze slot frames) is hidden; its slots and captions keep their
  arrangement and are centred in the dialog width of the R1 dialog profile (T.PROFILE_DIALOG['w']); every slot has
  the R1 item slot C of the R1 inventory under it (uir1.SLOT_CELL), a tall slot (weapon / armour, 96 px) as a column
  of those 32 px cells like the inventory grid;
* Evoluce: the "+" between the aura and its material (two R1 hairlines in the muted ink, sizes from the kit tokens);
* an optional quiet motif behind the slots: the kit texture SPECS[...]['backdrop'] centred on the
  slots, drawn only when the kit has it (listed in uir1tokens.SIZES), otherwise nothing;
* the slot captions (Předmět 1, Předmět 2, Výsledek; Kostým s aurou, Materiál) in the R1 font and the dim R1 ink;
* the evolution info (Nové / Úroveň / Šance, Spotřební materiál / count / yang) in an R1 inner panel, a quiet
  divider between its two blocks instead of the old ornament line;
* the price as the one R1 yang price of the client (uir1price.Price: the coin and "100.000 Yang"); a pečeť
  combination shows its chance line there instead (the window's own text, in the R1 font);
* OK / Zrušit as the R1 dialog buttons (uir1price.ConfirmButtons) running the window's own buttons; the help "?" of
  Proměna stays at the left of the header.

Nothing of the window's logic changes: the same slot windows (events, tooltips, drag and drop, the inventory
locks), the same buttons and packets. Settings -> "Starý vzhled" keeps the original windows; a failure while dressing
traces to syserr and the original look comes back (uir1frame FrameSkin.Fail), the class is not dressed again.
"""
import ui

import uir1
import uir1skin
import uir1tokens as T

P = T.PROFILE_DIALOG
CAPTION_GAP = 4                 # px between a slot cell and its caption under it
CAPTION = ('text_s', 'INK_DIM')
INFO = ('text_s', 'INK')
INFO_HEAD = ('text_sb', 'INK_DIM')

# What each window has inside. Names are the uiscript children; captions name uiScriptLocale strings.
#   art:      the old slot picture (hidden); its children (slots, captions) stay arranged as they are
#   cells:    (slot window, slot index, slot height) - the R1 item slot C under every slot
#   captions: (uiScriptLocale key, slot index of ``cells``) - a caption under the slot (when the uiscript has none)
#   cost:     the uiscript text line of the price (shown as the R1 price; SetCost)
#   info:     the text lines of the info panel and the index where its second block starts; rule: the old line
#   help:     a board button that moves to the left of the R1 header
#   plus:     two slot indexes of ``cells`` with a "+" drawn between them
#   backdrop: the motif behind the slots, a texture under the R1 kit root (T.ROOT); drawn centred on the slots only
#             when the kit lists it in T.SIZES (built by tools/build_althea_r1_kit.py), else nothing
BACKDROP = 'theowahdan/backdrop_%s.png'
PLUS_ALPHA = 1.0
SPECS = {
    'combine': dict(art='Acce_Combine', cells=(('AcceSlot', 0, 32), ('AcceSlot', 1, 32), ('AcceSlot', 2, 32)),
                    cost='Cost'),
    'absorb': dict(art='Acce_Combine', cells=(('AcceSlot', 0, 32), ('AcceSlot', 1, 96), ('AcceSlot', 2, 32)),
                   captions=(('ACCE_MAIN', 0), ('ACCE_SERVE', 1), ('ACCE_RESULT', 2))),
    'aura_absorb': dict(art='Aura_Absorb', cells=(('AuraSlot', 0, 32), ('AuraSlot', 1, 96), ('AuraSlot', 2, 32)),
                        captions=(('AURA_MAIN', 0), ('AURA_SUB', 1), ('ACCE_RESULT', 2))),
    'aura_levelup': dict(art='Aura_Levelup', cells=(('AuraSlot', 0, 32), ('AuraSlot', 1, 32)), plus=(0, 1),
                         backdrop=None,                     # Evoluce without a motif
                         info=(('AuraToolTip1', 'AuraToolTip2', 'AuraToolTip3', 'AuraToolTip4', 'AuraToolTip5',
                                'AuraToolTip6'), 3), rule='Aura_ToopTip_Line'),
    'changelook': dict(art='ChangeLook_SlotImg', cells=(('ChangeLookSlot', 0, 96), ('ChangeLookSlot', 1, 96),
                                                        ('ChangeLookSlot_PassYangItem', 0, 32)),
                       cost='Cost', help='ChangeLookToolTIpButton'),
}
for _kind, _spec in SPECS.items():
    _spec.setdefault('backdrop', BACKDROP % _kind)
ATTR = 'r1theowahdan'


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    color = int(color) & 0xFFFFFFFF
    return color - 0x100000000 if color > 0x7FFFFFFF else color


def Dress(window, kind):
    """The R1 inside of a window the shared R1 frame dressed (after the window wired its uiscript); returns the skin or
    None (Starý vzhled, no frame, a failure: the original look)."""
    old = window.__dict__.get(ATTR)
    if old is not None:                       # the window loaded its uiscript again (Kostým s aurou)
        window.__dict__[ATTR] = None
        old.Restore()
    frame = window.__dict__.get('r1frame')
    if frame is None or kind not in SPECS:
        return None
    try:
        skin = Skin(window, frame, SPECS[kind])
    except Exception:
        frame.Fail()
        return None
    window.__dict__[ATTR] = skin
    frame.undo.append(skin.Restore)           # a later frame failure gives the original inside back too
    return skin


def SetCost(window, amount=None, text=None):
    """The price of a dressed window (``amount`` Yang) or a line in its place (``text``, e.g. the chance of a pečeť);
    nothing in the original look (the window sets its own line)."""
    skin = window.__dict__.get(ATTR)
    if skin is None:
        return
    try:
        skin.SetCost(amount, text)
    except Exception:
        skin.Fail()


class Skin(object):
    def __init__(self, window, frame, spec):
        self.frame = frame
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.widgets = []
        self.buttons = None
        self.price = None
        self.cost_line = None
        self.cost_y = 0
        self.w = 0
        self.backdrop = None
        try:
            self._Build(window, kit, rec, spec)
        except Exception:
            self.Restore()
            raise

    # build --------------------------------------------------------------------------------------------------------
    def _Build(self, window, kit, rec, spec):
        child = window.GetChild
        board = child('board')
        self.window_w, self.window_h = window.GetWidth(), window.GetHeight()
        w = max(P['w'], board.GetWidth())
        top = self.frame.frame.ContentTop() + P['gap']
        art = child(spec['art'])
        kids = [kid for kid in (getattr(art, 'Children', None) or ()) if hasattr(kid, 'IsShow')]
        # the slot cells and the captions in the coordinates of the old picture
        cells = []
        for name, index, height in spec['cells']:
            slot = child(name)
            sx, sy = slot.GetLocalPosition()
            px, py = slot.GetSlotLocalPosition(index) or (0, 0)
            cells.append((int(sx + px), int(sy + py), int(height)))
        font = kit.font(CAPTION[0])
        cell = uir1.FontCell(font)
        captions = []
        for key, index in spec.get('captions', ()):
            x, y, height = cells[index]
            captions.append((self._Locale(key), x + T.SLOT // 2, y + height + CAPTION_GAP))
        texts = [kid for kid in kids if self._IsText(kid)]
        boxes = [(x, y, x + T.SLOT, y + h) for x, y, h in cells]
        for line in texts:
            x, y = line.GetLocalPosition()
            half = uir1.TextWidth(line) // 2
            boxes.append((x - half, y, x + half, y + cell))
        boxes += [(x - 1, y, x + 1, y + cell) for unused, x, y in captions]
        left, right = min(b[0] for b in boxes), max(b[2] for b in boxes)
        upper, lower = min(b[1] for b in boxes), max(b[3] for b in boxes)
        dx = (w - (right - left)) // 2 - left       # picture coordinates -> board coordinates
        dy = top - upper
        # the motif and the R1 cells first (under the slots), then the picture's children on the board above them
        self.slot_area = (right - left, lower - upper)          # what a motif covers (diagnostics, asset sizes)
        # the motif is symmetric about its middle column: centred on the slots' own box (not the captions), so its
        # axis is the axis between the slot columns / of the result slot (<= 0.5 px off)
        cl, cr = min(x for x, y, h in cells), max(x + T.SLOT for x, y, h in cells)
        ct, cb = min(y for x, y, h in cells), max(y + h for x, y, h in cells)
        self._Backdrop(board, spec, cl + cr + 2 * dx, ct + cb + 2 * dy)
        for x, y, height in cells:
            self.widgets.append(uir1.SlotGrid(board, x + dx, y + dy, 1, max(1, int(height) // T.SLOT)))
        if spec.get('plus'):
            a, b = [cells[index] for index in spec['plus']]
            self._Plus(board, (a[0] + T.SLOT + b[0]) // 2 + dx, (a[1] + b[1] + T.SLOT) // 2 + dy)
        rec.Call(lambda: None, lambda: uir1.Restack(art, kids))
        for kid in kids:
            kx, ky = kid.GetLocalPosition()
            rec.Parent(kid, board, kx + dx, ky + dy, art)
        rec.Hide(art)
        for line in texts:
            rec.Font(line, font, _Signed(getattr(T, CAPTION[1])))
        for text, x, y in captions:
            self.widgets.append(uir1.Text(board, text, x + dx, y + dy, font, getattr(T, CAPTION[1]), align='center',
                                          valign='top'))
        y = top + (lower - upper)
        if spec.get('info'):
            y = self._Info(window, board, kit, rec, spec, w, y + P['gap'])
        if spec.get('cost'):
            self.cost_line = child(spec['cost'])
            rec.Hide(self.cost_line)
            rec.Font(self.cost_line, kit.font(INFO[0]), _Signed(getattr(T, INFO[1])))
            import uir1price
            self.cost_y = y + P['gap']
            self.price = uir1price.Price(board, w // 2, self.cost_y, 'center')
            self.widgets.append(self.price)
            y = self.cost_y + uir1price.ICON_H
        self.w = w
        self._Buttons(window, board, w, y + P['foot_gap'])
        # Slot windows retain their native hit rectangles; keep the header above them.
        uir1.Restack(board, [self.frame.frame.header])
        if spec.get('help'):
            self._Help(child(spec['help']), board, rec)

    def _Backdrop(self, board, spec, cx2, cy2):
        """The optional motif behind the slots, its centre on (cx2 / 2, cy2 / 2); nothing when the kit has no such
        texture."""
        path = spec.get('backdrop')
        if not path or path not in T.SIZES:
            return
        bw, bh = T.SIZES[path]
        self.backdrop = uir1.Image(board, path, (cx2 - bw) // 2, (cy2 - bh) // 2)
        self.widgets.append(self.backdrop)

    def _Plus(self, board, cx, cy):
        """A "+" centred on (cx, cy): two hairlines T.ICON long and T.RULE_H thick in the muted R1 ink."""
        arm, thick = T.ICON, T.RULE_H
        for x, y, w, h in ((cx - arm // 2, cy - thick // 2, arm, thick), (cx - thick // 2, cy - arm // 2, thick, arm)):
            self.widgets.append(uir1.Rect(board, x, y, w, h, T.MUTED, PLUS_ALPHA))

    def _Info(self, window, board, kit, rec, spec, w, y):
        """The info lines in an R1 inner panel (a divider before the second block); returns the panel's bottom."""
        names, split = spec['info']
        lines = [window.GetChild(name) for name in names]
        if spec.get('rule'):
            rec.Hide(window.GetChild(spec['rule']))
        x, inner = P['pad'], w - 2 * P['pad']
        head, body = kit.font(INFO_HEAD[0]), kit.font(INFO[0])
        pitch = max(uir1.FontCell(head), uir1.FontCell(body)) + P['line_gap']
        height = 2 * P['pad'] + pitch * len(lines) + P['gap']
        self.widgets.append(uir1.Frame(board, x, y, inner, height, 'panel'))
        ty = y + P['pad']
        for index, line in enumerate(lines):
            if index == split:
                self.widgets.append(uir1.Divider(board, x + P['pad'], ty + (P['gap'] - T.RULE_H) // 2,
                                                 inner - 2 * P['pad']))
                ty += P['gap']
            role = INFO_HEAD if index in (0, split) else INFO
            rec.Position(line, x + P['pad'], ty)
            rec.Font(line, kit.font(role[0]), _Signed(getattr(T, role[1])))
            ty += pitch
        uir1.Restack(board, lines)               # above the panel made now
        return y + height

    def _Help(self, button, board, rec):
        """The help "?" at the left of the R1 header, above it (made after the header: drawn and picked first)."""
        rec.Position(button, P['pad'], (T.HEAD_H - button.GetHeight()) // 2)
        uir1.Restack(board, [button])

    def _Buttons(self, window, board, w, row_top):
        import uir1price
        accept, cancel = window.GetChild('AcceptButton'), window.GetChild('CancelButton')
        self.buttons = uir1price.ConfirmButtons(board, accept, cancel, self.kit)
        for button, key in zip(self.buttons.Buttons(), ('OK', 'CANCEL')):
            if not button.GetText():          # the image buttons of Proměna (a tick, a cross)
                button.SetText(self._Locale(key))
        h = row_top + self.buttons.Height() + uir1price.BUTTON_BOTTOM
        self.buttons.Place(w, h - uir1price.BUTTON_BOTTOM)
        for widget in (window, board):
            original = (widget.GetWidth(), widget.GetHeight())
            widget.SetSize(w, h)
            # A later native resize belongs to the caller, including a resize that fails the R1 frame.
            def restore_size(widget=widget, original=original):
                if (widget.GetWidth(), widget.GetHeight()) == (w, h):
                    widget.SetSize(*original)
            self.rec.Call(lambda: None, restore_size)

    @staticmethod
    def _IsText(widget):
        return hasattr(widget, 'GetText') and hasattr(widget, 'SetPackedFontColor') and \
            not hasattr(widget, 'SetEvent') and not hasattr(widget, 'SetSlotBaseImage')

    @staticmethod
    def _Locale(key):
        import uiScriptLocale
        return getattr(uiScriptLocale, key, '')

    # used by the window -------------------------------------------------------------------------------------------
    def SetCost(self, amount, text):
        if self.price is None:
            return
        line = self.cost_line
        if text:
            self.price.Clear()
            line.SetText(text)
            line.SetPosition(self.w // 2, self.cost_y)
            line.Show()
            return
        line.Hide()
        if amount is None:
            self.price.Clear()
            return
        import uir1price
        self.price.SetPrice(int(amount), uir1price.CanAfford(int(amount)))

    def Fail(self):
        uir1.TraceFailure('the Theowahdan window inside')
        self.frame.Fail()

    # back to the original look ------------------------------------------------------------------------------------
    def Restore(self):
        if self.buttons is not None:
            self.buttons.Restore()
            self.buttons = None
        uir1skin.Destroy(self.widgets)
        self.widgets = []
        self.price = None
        self.rec.Undo()
        if self.cost_line is not None:
            self.cost_line.Show()
            self.cost_line = None
