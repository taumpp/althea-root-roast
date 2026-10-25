# -*- coding: utf-8 -*-
"""Strom dovedností (uiskilltree.SkillTreeWindow, 780 x 520 or 900 x 600 by the screen) in the R1 look ("Krvavá
žíla", docs/ALTHEA_R1_KIT.md), drawn INTO the original window. The tree itself (preset background, nodes, edges,
sparks, the drag of the canvas, the node tooltips) keeps its art; only the window chrome, the buttons and the labels
become R1:

* the R1 frame and header with the plain X; the original title bar stays as an invisible drag handle (the window
  flags do not change); the point icon and the point balance stay at the right of the header, Noto Sans;
* a quiet line between the tree and the footer; the activation lamp keeps its art;
* "Zapnout / Vypnout", "Rozebrat" and "Obnovit" as 26 px R1 buttons of today's widths standing in for the original
  buttons; the footer row follows the R1 kit (docs/ALTHEA_R1_KIT.md): its buttons the profile's pad (P) above the window's bottom
  edge, the lamp and "Zapnout" the profile's pad from the left edge, "Obnovit" the pad from the right edge, "Rozebrat" the kit's
  button gap (P['gap']) before it (the window's Enable / Disable / SetText reach them through an adapter, the state is never asked from the
  engine); the renew cost tooltip stays anchored on the renew button (its hover area moves onto the R1 button);
* the remaining time and the error text in Noto Sans.

Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps the
original look.
"""
import fontconfig
import ui

import uir1
import uir1skin
import uir1tokens as T
import uir1vybava as V

BUTTON_Y = 12
P = T.PROFILE_WINDOW # the layout profile of this window (docs/ALTHEA_R1_KIT.md chap. 0): pad, button, gap
# window attribute, handler, today's width (uicrimsoncontrols family), renew
BUTTONS = (('activationButton', '_SkillTreeWindow__OnActivationButton', 100, False),
           ('dismantleButton', '_SkillTreeWindow__OpenDismantle', 88, False),
           ('renewButton', '_SkillTreeWindow__OnRenewButton', 176, True))
POINT_ICON = 14


class SkillTreeSkin(object):
    def __init__(self, window):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.rec = rec = uir1skin.Recorder()
        self.skin = self.handle = None
        self.widgets = []
        self.adapters = []
        try:
            board = window.board
            layout = window.layout
            w = layout.WINDOW_WIDTH
            self.skin = uir1.BoardSkin(board, kit, board.titleName.GetText(), on_close=ui.__mem_func__(window.Close))
            self.handle = V.DragHandle(board.titleBar, (board.titleName,))
            self._Points(board, w)
            fx, fy, fw, unused = layout.FOOTER_RECT
            self.row = self.Row(layout)
            # the line between the tree and the footer: the gap above the button row (to the line) is the gap under
            # it (to the window's edge), P['foot_gap'] = P['pad'] (docs/ALTHEA_R1_KIT.md, owner 13. 10.); the divider
            # draws its line on its middle row (uir1.Divider), the gap counts from under that line
            self.widgets.append(uir1.Divider(board, fx, fy + self.row - P['foot_gap'] - (T.RULE_H // 2 + 1), fw))
            self._Lamp(window)
            self._Buttons(window)
            text = kit.font('text')
            line = window.remainingTimeText
            rec.Font(line, text, T.INK)
            x = line.GetLocalPosition()[0]
            rec.Position(line, x, self.row + uir1.CellTop(P['btn'], text))
            rec.Font(window.treeErrorText, text, T.INK)
            getattr(window, '_SkillTreeWindow__RefreshActivationButtons')()
        except Exception:
            self.Restore()
            raise

    def _Points(self, board, w):
        """The point icon and balance from the hidden title bar onto the board, right of the header (left of the X)."""
        window, rec, kit = self.window, self.rec, self.kit
        font = kit.font('text_sb')
        icon_y = (T.HEAD_H - POINT_ICON) // 2 + 1
        rec.Parent(window.pointIcon, board, w - 126, icon_y, board.titleBar)
        rec.Parent(window.pointBalanceText, board, w - 106, uir1.CellTop(T.HEAD_H, font) + 1, board.titleBar)
        rec.Font(window.pointBalanceText, font, T.IVORY, fontconfig.FontForRole(fontconfig.ROLE_BODY))

    @staticmethod
    def Row(layout):
        """y of the R1 button row in the footer board: the buttons' bottom edge the pad above the window's bottom edge."""
        return layout.WINDOW_HEIGHT - P['pad'] - P['btn'] - layout.FOOTER_RECT[1]

    def _Lamp(self, window):
        """The activation lamp the pad from the window's left edge, centred on the button row."""
        lamp = window.activationStatus
        fx = window.layout.FOOTER_RECT[0]
        self.lamp_x = P['pad'] - fx
        self.lamp_dx = self.lamp_x - lamp.GetLocalPosition()[0]        # "Zapnout" keeps its distance to the lamp
        # its centre stays on the centre line of the row (the original lamp was centred on the original 22 px row)
        y = lamp.GetLocalPosition()[1] + self.row - BUTTON_Y + (P['btn'] - T.BTN_H_S) // 2
        self.rec.Position(lamp, self.lamp_x, y)

    def Columns(self, window):
        """x of the three buttons in the footer board: "Zapnout" beside the lamp, "Obnovit" the pad from the window's
        right edge, "Rozebrat" the profile's gap before it."""
        layout = window.layout
        widths = dict((attr, w) for attr, unused, w, unused2 in BUTTONS)
        renew = layout.WINDOW_WIDTH - P['pad'] - layout.FOOTER_RECT[0] - widths['renewButton']
        return {'activationButton': window.activationButton.GetLocalPosition()[0] + self.lamp_dx,
                'dismantleButton': renew - P['gap'] - widths['dismantleButton'],
                'renewButton': renew}

    def _Buttons(self, window):
        kit = self.kit
        footer = window.footerBoard
        columns = self.Columns(window)
        for attr, handler, w, renew in BUTTONS:
            original = getattr(window, attr)
            button = uir1.Button(footer, kit, columns[attr], self.row, w, original.GetText(),
                                 event=ui.__mem_func__(getattr(window, handler)))
            self.widgets.append(button)
            adapter = V.Swap(window, attr, original, button)
            self.adapters.append((attr, adapter))
            if renew:
                self._Renew(window, original, button)

    def _Renew(self, window, original, button):
        """The renew cost tooltip: its hover area (clicks and hover of the renew button) and its anchor move onto the
        R1 button."""
        rec = self.rec
        area = window.renewHoverArea
        if area is not None:
            rec.Parent(area, button, 0, 0, original)
        tooltip = window.renewToolTip
        if tooltip is not None:
            rec.Call(lambda: tooltip.SetAnchorButton(button), lambda: tooltip.SetAnchorButton(original))

    def Restore(self):
        window = self.window
        if window is None:
            return
        for attr, adapter in self.adapters:
            V.Unswap(window, attr, adapter)
        self.adapters = []
        self.rec.Undo()
        V.Fail(self.widgets)
        self.widgets = []
        if self.handle is not None:
            self.handle.Restore()
        if self.skin is not None:
            self.skin.Restore()
            self.skin.Destroy()
        self.skin = self.handle = None
        self.window = None

    Destroy = Restore
