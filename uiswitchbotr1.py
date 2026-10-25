# -*- coding: utf-8 -*-
"""The switchbot window in the R1 look ("Krvavá žíla", docs/ALTHEA_R1_KIT.md), drawn INTO uiswitchbot.SwitchbotWindow.

The window keeps its 400 x 430 size and every function; nothing of the original window is re-created:

* frame and header (title, vein, X) over the BoardWithTitleBar;
* five slot cards built like the card of the production window: the number of the slot on an R1 button (small,
  slightly rounded) on top, the three item slots under it (the original 1 x 3 grid, 32 px cells, with the R1 item
  slot C as their slot base: uir1.SLOT_CELL, team choice 2026-10-07) and the whole card tinted by the state with the
  native whole-card tint geometry with the existing P2 hues (running orange, finished green, stopped red) - no state words, no frames in
  the state colour; the selected card has a light ivory 2 px frame instead of the blinking white box (no red
  underline); the button selects the slot through the original select button's handler, a locked VIP slot has the
  button dimmed and a click on it still shows the original lock message;
* Varianta 1 / 2 as an R1 segment calling SelectAlternative;
* the bonus rows as R1 fields (the original row board's own images re-skinned, so the well lies under the row's
  controls): the bonus name, the magnifier and the clear X (the original row events), the value field with a
  chevron for the value picker (the original editable number line stays); an empty row shows only the magnifier,
  the hint and a grey "-"; the wheel over the bonus / value field steps it through its picker's list (the original
  row's own handlers, uiswitchbot.SwitchbotAttribute.WheelType / WheelValue, on the boards this skin keeps);
* Uložit / Spustit (primary) / Zastavit as R1 buttons; the original start / stop / save buttons are replaced on the
  window by adapters with the same calls, so __RefreshButtons and __BindEvents run unchanged;
* "Předmět změny" (the scroll picker) as one R1 card with the icon, the name and the count, the chevron opening the
  original picker, and Instaswitchbot as an R1 button.

The attribute search list (root/uiswitchbotsearchr1.py), the saved configurations (root/uiswitchbotpresetsr1.py) and
the Instaswitchbot (root/uiswitchbotinstantr1.py, built from the rows, fields and adapters of this module) have their
own R1 skins.
Settings -> "Starý vzhled" keeps the original window; a failure while building traces to syserr and keeps it too.
"""
import localeInfo
import ui

import uir1
import uir1layout as L
import uir1tokens as T

ORIGINAL_SLOT_BASE = 'd:/ymir work/ui/public/slot_base.sub'
STATE_COLORS = {'stopped': 0xFFD30D0E, 'running': 0xFFF28C28, 'finished': 0xFF2A8C55}
STATE_TINT_ALPHA = 0.2  # Keep the whole-card tint, with the existing distinguishable P2 hues.
CARD_BUTTON_W, CARD_BUTTON_Y = 49, 4      # the R1 number button of a card (small, 22 px): 49 px wide like the original one
SELECTED_FRAME = 0xFFD6CDBF     # the selected card: a light ivory frame, the outer px strong, the inner one fainter
SELECTED_FRAME_ALPHA = (0.95, 0.55)
FIELD_GAP = 4               # bonus field -> value field
VALUE_W = 68                # the value field (the original is 50 px): five digits in the bonus name's font, a gap
VALUE_X = 8                 # and the chevron; the bonus field is narrower by the same amount, the row keeps its width
CHEVRON_W = 14
ORIGINAL_EDIT_FONT = 'Tahoma:12'    # the number line of the original row, where the line has no SetDefaultFontName
ROW_INSET = 6               # the bonus rows inside the main panel's frame
P = T.PROFILE_WINDOW        # the layout profile of this window (docs/ALTHEA_R1_KIT.md chap. 0)
# The panels of the original window keep 8 px from the frame (uiswitchbot.BORDER_SPACE); in R1 they keep P['pad'] (12)
# on the left, the right and at the bottom. The five cards then share 376 px: 72 px each with a 4 px gap (5 x 72 +
# 4 x 4 = 376), the item slots and the number button centred in them as before.
CARD_GAP = 4                # hardcode-ok: 5 cards x 72 + 4 gaps x 4 = 376 px between the 12 px pads
BUTTON_GAP = 8
SAVE_W, START_W = 120, 128
INSTANT_W = 140
CARD_TEXT_X = 44


def Tr(czech, english):
    return uir1.Tr_(czech, english)


def _Signed(color):
    """A packed 0xAARRGGBB colour as the signed int the x64 binding takes (it ignores values >= 0x80000000)."""
    return color - 0x100000000 if color >= 0x80000000 else color


def TabState(tab):
    """running / finished / stopped / empty / locked of one SwitchbotItemTab (its own state calls)."""
    if tab.locked:
        return 'locked'
    if tab.IsEmpty():
        return 'empty'
    if tab.IsActive():
        return 'running'
    return 'finished' if tab.IsFinished() else 'stopped'


class _Hidden(object):
    """Stands in for the blinking selection box of a card: never shown in R1."""

    def Show(self):
        pass

    def Hide(self):
        pass

    def IsShow(self):
        return False

    def SetColor(self, color):
        pass


Glyph = uir1.Glyph          # with the hover hint of the original button it replaces (SetToolTipText)


class Chevron(Glyph):
    """The R1 chevron as a small clickable glyph (the chevron textures have 'active' for the pressed state)."""

    def paint(self):
        state = {'pressed': 'active'}.get(self.state(), self.state())
        self.image.LoadImage(uir1.ROOT + self.pattern % state)


class ButtonAdapter(object):
    """Stands in for an original ui.Button / RadioButton of the window (Enable / Disable / Down / SetUp / SetEvent /
    Show / Hide): the calls drive the R1 button; Down / SetUp only remember the state (the R1 look shows the main
    action as the primary button instead of a pressed radio button)."""

    def __init__(self, button):
        self.button = button
        self.down = False

    def SetEvent(self, event, *args):
        self.button.SetEvent((lambda: event(*args)) if args else event)

    def Enable(self):
        self.button.Enable()

    def Disable(self):
        self.button.Disable()

    def IsEnabled(self):
        return self.button.IsEnabled()

    def Down(self):
        self.down = True

    def SetUp(self):
        self.down = False

    def IsDown(self):
        return self.down

    def Show(self):
        self.button.Show()

    def Hide(self):
        self.button.Hide()

    def IsShow(self):
        return self.button.IsShow()

    def SetToolTipText(self, text, *unused):
        self.button.SetToolTipText(text)

    def GetWidth(self):
        return self.button.GetWidth()


class Clear(object):
    """A ThinBoard(Circle) drawn as nothing: its corner, line and base images hidden (restored later)."""

    def __init__(self, board):
        self.board = board
        self.hidden = [w for w in list(getattr(board, 'Corners', ()) or ()) + list(getattr(board, 'Lines', ()) or ())
                       + [getattr(board, 'Base', None)] if w is not None and w.IsShow()]
        for widget in self.hidden:
            widget.Hide()

    def Restore(self):
        for widget in self.hidden:
            widget.Show()
        self.hidden = []


class FieldSkin(object):
    """An R1 field (the 24 px well) drawn with the original ThinBoardCircle's OWN corner and line images (made before
    the board's children, so the well lies under them); the black base bar is hidden."""

    def __init__(self, board, w):
        self.board = board
        self.images = list(board.Corners) + list(board.Lines)
        self.saved = [(image, getattr(image, 'name', None) or getattr(image, 'image_path', None),
                       image.GetLocalPosition()) for image in self.images]
        self.base = getattr(board, 'Base', None)
        if self.base is not None:
            self.base.Hide()
        self.ops = uir1.Ops(board)
        self.ops.items = list(self.images)
        self.Apply(w)

    def Apply(self, w, state='normal'):
        self.w = int(w)
        self.ops.Apply(L.field(state, self.w))

    def Restore(self):
        for image, path, pos in self.saved:
            if path:
                image.LoadImage(path)
            image.SetPosition(*pos)
            image.Show()
        if self.base is not None:
            self.base.Show()
        self.board.SetSize(self.board.GetWidth(), self.board.GetHeight())


class CardSkin(object):
    """One slot card (SwitchbotItemTab) built like the card of the production window: the number button on top, the
    three item slots under it, the whole card tinted by the state, in R1 parts."""

    def __init__(self, skin, tab):
        self.skin, self.tab = skin, tab
        self.board = self.box = self.button = self.hit = self.old_button = None
        self.marks = []
        self.state = self.selected = None
        try:
            self._Build()
        except Exception:
            self.Restore()              # a half-built card gives its slot back as it was, then the window falls back
            raise

    def _Build(self):
        skin, tab = self.skin, self.tab
        kit = skin.kit
        w, h = tab.GetWidth(), tab.GetHeight()
        self.board = uir1.BoardSkin(tab, kit, kind='panel')
        self.box, tab.selectBox = tab.selectBox, _Hidden()      # the blinking white box of the original is not drawn
        self.box.Hide()
        self.old_button = tab.selectButton
        self.old_button.Hide()
        tab.itemSlot.SetSlotBaseImage(uir1.SLOT_CELL, 1.0, 1.0, 1.0, 1.0)
        # the whole-card state tint (tab.statusBar) stays and lies under everything made here; above it the light frame
        # of the selected card (2 px), then the R1 number button and, over a locked slot's button, the click area
        self.marks = [self._Box(tab, w, h, inset) for inset in (0, 1)]
        x = (w - CARD_BUTTON_W) // 2
        handler = tab._SwitchbotItemTab__OnSelectButtonClick
        self.button = uir1.Button(tab, kit, x, CARD_BUTTON_Y, CARD_BUTTON_W, str(tab.slot_num + 1), small=True,
                                  event=handler)
        self.hit = uir1.HitArea(tab, x, CARD_BUTTON_Y, CARD_BUTTON_W, self.button.GetHeight())
        self.hit.callback = handler         # a locked slot: the button is dimmed, the click still says why
        self.hit.Hide()
        self.Sync()

    @staticmethod
    def _Box(tab, w, h, inset):
        box = ui.Box()
        box.SetParent(tab)
        box.AddFlag('not_pick')
        box.SetPosition(inset, inset)
        box.SetSize(w - 2 * inset, h - 2 * inset)
        box.Hide()
        return box

    def Sync(self):
        tab = self.tab
        state = TabState(tab)
        if state in STATE_COLORS:
            tab.statusBar.SetColor(uir1.GenerateColor(STATE_COLORS[state], STATE_TINT_ALPHA))
        selected = self.skin.window.selectedSlot == tab.slot_num and state != 'locked'
        if (state, selected) == (self.state, self.selected):
            return
        self.state, self.selected = state, selected
        for box, alpha in zip(self.marks, SELECTED_FRAME_ALPHA):
            if selected:
                box.SetColor(uir1.GenerateColor(SELECTED_FRAME, alpha))
                box.Show()
            else:
                box.Hide()
        locked = state == 'locked'
        if locked == self.button.IsEnabled():
            self.button.Disable() if locked else self.button.Enable()
        self.hit.Show() if locked else self.hit.Hide()

    def Restore(self):
        tab = self.tab
        for widget in self.marks + [self.hit, self.button]:
            if widget is not None:
                widget.Hide()
        if self.hit is not None:
            self.hit.callback = None
        if self.button is not None:
            self.button.callback = None
        if self.box is not None:
            tab.selectBox = self.box
            tab.itemSlot.SetSlotBaseImage(ORIGINAL_SLOT_BASE, 1.0, 1.0, 1.0, 1.0)
        if self.old_button is not None:
            self.old_button.Show()
            if self.box is not None and self.old_button.IsDown():
                self.box.Show()
        if self.board is not None:
            self.board.Restore()
            self.board.Destroy()


class RowSkin(object):
    """One bonus row (SwitchbotAttribute)."""

    def __init__(self, skin, row, width):
        self.skin, self.row = skin, row
        kit = skin.kit
        self.pos = row.GetLocalPosition()
        self.size = (row.GetWidth(), row.GetHeight())
        self.type_size = (row.typeInput.GetWidth(), row.typeInput.GetHeight())
        self.value_pos = row.valueInput.GetLocalPosition()
        self.value_size = (row.valueInput.GetWidth(), row.valueInput.GetHeight())
        vw = max(self.value_size[0], VALUE_W)
        tw = width - vw - FIELD_GAP
        row.SetPosition(ROW_INSET, self.pos[1])
        row.SetSize(width, self.size[1])
        row.typeInput.SetSize(tw, self.type_size[1])
        row.valueInput.SetSize(vw, self.value_size[1])
        row.valueInput.SetPosition(tw + FIELD_GAP, 0)
        self.type_field = FieldSkin(row.typeInput, tw)
        self.value_field = FieldSkin(row.valueInput, vw)
        cy = T.FIELD_H // 2
        self.hidden = [row.typeTextLine, row.searchTypeButton, row.deleteAttributeButton, row.valueArrow]
        for widget in self.hidden:
            widget.Hide()
        self.text = uir1.RowText(row.typeInput, '', 8, T.FIELD_H, kit.font('text'), T.INK)
        clear_hit = T.CLEAR + 6
        self.clear_x = tw - 4 - clear_hit
        self.search_x = self.clear_x - 2 - (T.ICON + 4)
        self.search = Glyph(row.typeInput, 'icon/search_%s.png', self.search_x, cy - (T.ICON + 4) // 2, T.ICON,
                                 row._SwitchbotAttribute__OnClickSearchButton, T.ICON + 4)
        self.clear = Glyph(row.typeInput, 'icon/clear_%s.png', self.clear_x, cy - clear_hit // 2, T.CLEAR,
                           row._SwitchbotAttribute__OnClickClearButton, clear_hit)
        self.clear.SetToolTipText(localeInfo.SWITCHBOT_CLEAR_ATTR)
        # the value in the font of the bonus name; the original number line (Tahoma 12 by default) too, in the room
        # left of the chevron
        font = kit.font('text')
        self.value_text = uir1.RowText(row.valueInput, '-', VALUE_X, T.FIELD_H, font, T.MUTED)
        chevron_x = vw - 6 - CHEVRON_W
        self.chevron = Chevron(row.valueInput, 'chevron/down_%s.png', chevron_x, cy - 7, T.CHEVRON,
                               row.OpenValues, CHEVRON_W)
        edit = row.valueEditLine
        self.edit_saved = (edit.GetLocalPosition(), (edit.GetWidth(), edit.GetHeight()))
        uir1.SetFont(edit, font)
        edit.SetPackedFontColor(_Signed(T.INK))
        edit.SetPosition(VALUE_X, (T.FIELD_H - uir1.FontCell(font)) // 2)
        edit.SetSize(chevron_x - 2 - VALUE_X, uir1.FontCell(font) + 2)
        self.key = None
        self.Sync()

    def Sync(self):
        row = self.row
        provider = row.provider
        active = bool(provider.IsActive(row.selectedSlot))
        kind, value = provider.GetAttribute(row.selectedSlot, row.alternative, row.index) if row.index >= 0 else (0, 0)
        # The original row shows its number line again on every RefreshAttributeRow (an inactive row), which the key
        # below does not see: it is put right every time, or the "0" of an empty row stood beside R1's grey "-".
        editable = bool(kind) and not active
        if editable != bool(row.valueEditLine.IsShow()):
            row.valueEditLine.Show() if editable else row.valueEditLine.Hide()
        name = row.typeTextLine.GetText()
        key = (active, kind, value, name)
        if key == self.key:
            return
        self.key = key
        limit = self.search_x - 8 - 4
        if kind:
            uir1.Fit(self.text, name, limit)
            self.text.SetPackedFontColor(T.INK)
        else:
            uir1.Fit(self.text, Tr('Vyber bonus...', 'Choose a bonus...'), limit)
            self.text.SetPackedFontColor(T.MUTED)
        for glyph in (self.search, self.clear, self.chevron):
            glyph.Disable() if active else glyph.Enable()
        if kind:
            self.search.SetPosition(self.search_x, self.search.GetLocalPosition()[1])
            self.clear.Show()
        else:
            self.search.SetPosition(self.clear_x - 2, self.search.GetLocalPosition()[1])
            self.clear.Hide()
        if editable:
            self.value_text.Hide()
            self.chevron.Show()
        else:
            self.value_text.SetText(str(value) if kind and value else '-')
            self.value_text.Show()
            self.chevron.Hide()

    def Restore(self):
        row = self.row
        for widget in (self.text, self.search, self.clear, self.value_text, self.chevron):
            widget.Hide()
        self.search.callback = self.clear.callback = self.chevron.callback = None
        self.type_field.Restore()
        self.value_field.Restore()
        row.SetPosition(*self.pos)
        row.SetSize(*self.size)
        row.typeInput.SetSize(*self.type_size)
        row.valueInput.SetSize(*self.value_size)
        row.valueInput.SetPosition(*self.value_pos)
        edit = row.valueEditLine
        position, size = self.edit_saved
        text = edit.GetText()
        edit.SetText('')
        if hasattr(edit, 'SetDefaultFontName'):
            edit.SetDefaultFontName()
        else:
            edit.SetFontName(ORIGINAL_EDIT_FONT)
        edit.SetText(text)
        edit.SetPackedFontColor(-1)
        edit.SetPosition(*position)
        edit.SetSize(*size)
        for widget in self.hidden:
            widget.Show()
        if row.provider.IsActive(row.selectedSlot):
            row.valueEditLine.Hide()
        else:
            row.valueEditLine.Show()


class SwitchbotSkin(object):
    """R1 into one uiswitchbot.SwitchbotWindow (after its __LoadWindow and __BindEvents)."""

    def __init__(self, window, title):
        self.window = window
        self.kit = kit = uir1.Kit()
        self.cards, self.rows, self.clears = [], [], []
        self.moved = []                 # (original control, position, size) moved for the R1 layout
        self.board = uir1.BoardSkin(window, kit, title, on_close=window.Close)
        uir1.Front(window)             # the original had no 'float': a click never brought it to the front
        self.originals = (window.startButton, window.stopButton, window.saveButton)
        try:
            self._Build()
        except Exception:
            self.Restore()
            raise

    def _Place(self, widget, x=None, y=None, w=None, h=None):
        """Move / resize an original control for the R1 layout; Restore() puts it back."""
        ox, oy = widget.GetLocalPosition()
        ow, oh = widget.GetWidth(), widget.GetHeight()
        self.moved.append((widget, (ox, oy), (ow, oh)))
        if w is not None or h is not None:
            widget.SetSize(ow if w is None else int(w), oh if h is None else int(h))
        if x is not None or y is not None:
            widget.SetPosition(ox if x is None else int(x), oy if y is None else int(y))

    def _Relayout(self, window):
        """The panels P['pad'] from the frame (left, right, bottom), the cards in the narrower top panel."""
        W, H = window.GetWidth(), window.GetHeight()
        pad = P['pad']
        inner = W - 2 * pad
        for panel in (window.topPanel, window.mainPanel, window.botPanel):
            self._Place(panel, x=pad, w=inner)
        self._Place(window.alternativePanel, w=inner)
        footer = window.footer
        fy = footer.GetLocalPosition()[1]
        self._Place(footer, x=pad, w=inner, h=H - pad - fy)
        picker = window.scrollPicker
        self._Place(picker, y=(footer.GetHeight() - picker.GetHeight()) // 2)
        tabs = [window.itemTabs[slot] for slot in sorted(window.itemTabs)]
        count = len(tabs)
        card_w = (inner - (count - 1) * CARD_GAP) // count
        x0 = (inner - count * card_w - (count - 1) * CARD_GAP) // 2
        for index, tab in enumerate(tabs):
            h = tab.GetHeight()
            self._Place(tab, x=x0 + index * (card_w + CARD_GAP), w=card_w)
            self._Place(tab.statusBar, w=card_w - 4)
            self._Place(tab.selectBox, w=card_w - 2)
            for centred in (tab.itemSlot, tab.selectButton):      # centred children follow the new width
                self._Place(centred, x=centred.GetLocalPosition()[0])

    def _Build(self):
        window, kit = self.window, self.kit
        self._Relayout(window)
        for panel in (window.topPanel, window.alternativePanel, window.botPanel):
            self.clears.append(Clear(panel))
        self.main = uir1.BoardSkin(window.mainPanel, kit, kind='panel')
        self.footer = uir1.BoardSkin(window.footer, kit, kind='panel')
        for slot in sorted(window.itemTabs):
            self.cards.append(CardSkin(self, window.itemTabs[slot]))

        # Varianta 1 / 2
        alt = window.alternativePanel
        self.alt_label_hidden = [window.alternativeTextLine] + list(window.alternativeButtons.values())
        for widget in self.alt_label_hidden:
            widget.Hide()
        label = (window.alternativeTextLine.GetText() or '').rstrip(': ')
        self.alt_label = uir1.RowText(alt, label, ROW_INSET + 8, alt.GetHeight(), kit.font('text_s'), T.INK_DIM)
        options = [(index, str(index + 1)) for index in sorted(window.alternativeButtons)]
        self.segment = uir1.Segment(alt, kit, options, event=window.SelectAlternative, width=40 * len(options))
        self.segment.SetPosition(80, (alt.GetHeight() - T.SEG_H) // 2)

        width = window.mainPanel.GetWidth() - 2 * ROW_INSET
        for index in sorted(window.attrDict):
            self.rows.append(RowSkin(self, window.attrDict[index], width))

        # Uložit / Spustit / Zastavit
        bot = window.botPanel
        y = (bot.GetHeight() - T.BTN_H) // 2
        stop_w = bot.GetWidth() - SAVE_W - START_W - 2 * BUTTON_GAP
        self.save = uir1.Button(bot, kit, 0, y, SAVE_W, localeInfo.SWITCHBOT_SAVE, event=window.OpenSaveConfiguration)
        self.save.SetToolTipText(localeInfo.SWITCHBOT_SAVE_BUTTON)
        self.start = uir1.Button(bot, kit, SAVE_W + BUTTON_GAP, y, START_W, window.startButton.GetText(), primary=True)
        self.stop = uir1.Button(bot, kit, SAVE_W + START_W + 2 * BUTTON_GAP, y, stop_w, window.stopButton.GetText())
        for original in self.originals:
            original.Hide()
        window.startButton, window.stopButton = ButtonAdapter(self.start), ButtonAdapter(self.stop)
        window.saveButton = ButtonAdapter(self.save)
        window.startButton.SetEvent(lambda: window.SetActive(True))
        window.stopButton.SetEvent(lambda: window.SetActive(False))
        for adapter, original in zip((window.startButton, window.stopButton), self.originals):
            # the EXE cannot tell a native button's state; Open -> __RefreshButtons sets it through the adapters
            adapter.Enable() if uir1.IsEnabled(original, default=False) else adapter.Disable()

        # Předmět změny + Instaswitchbot
        picker = window.scrollPicker
        choice = picker.choice
        self.clears.append(Clear(choice))
        self.picker_hidden = [choice.name, choice.count, picker.arrow, window.instantButton]
        for widget in self.picker_hidden:
            widget.Hide()
        self.card_name = uir1.Text(choice, '', CARD_TEXT_X, 4, kit.font('text_sb'), T.IVORY, valign='top')
        self.card_count = uir1.Text(choice, '', CARD_TEXT_X, 22, kit.font('text_s'), T.INK_DIM, valign='top')
        self.card_chevron = Chevron(choice, 'chevron/down_%s.png', choice.GetWidth() - 6 - 14,
                                    (choice.GetHeight() - 14) // 2, T.CHEVRON, picker.Toggle, 14)
        footer = window.footer
        self.instant = uir1.Button(footer, kit, footer.GetWidth() - T.PAD - INSTANT_W,
                                   (footer.GetHeight() - T.BTN_H) // 2, INSTANT_W, window.instantButton.GetText(),
                                   event=window.OpenInstant)

        # every frame: the state of the cards, the rows and the card texts follow the original controls
        self.ticker = ui.Window()
        self.ticker.SetParent(window)
        self.ticker.AddFlag('not_pick')
        self.ticker.SetSize(0, 0)
        self.ticker.OnUpdate = self.Sync
        self.ticker.Show()
        self.Sync()

    # ------------------------------------------------------------------ state
    def Sync(self):
        window = self.window
        if window is None:
            return
        for card in self.cards:
            card.Sync()
        for row in self.rows:
            row.Sync()
        self.segment.SetValue(window.alternative)
        choice = window.scrollPicker.choice
        name, count = choice.name.GetText(), choice.count.GetText()
        if (name, count) != getattr(self, '_card', None):
            self._card = (name, count)
            uir1.Fit(self.card_name, name, choice.GetWidth() - CARD_TEXT_X - 26)
            self.card_count.SetText(count)
        enabled = bool(window.scrollPicker.enabled)
        if enabled != self.card_chevron.IsEnabled():
            self.card_chevron.Enable() if enabled else self.card_chevron.Disable()

    # ------------------------------------------------------------------ restore
    def Restore(self):
        window = self.window
        if window is None:
            return
        self.window = None
        ticker = getattr(self, 'ticker', None)
        if ticker is not None:
            ticker.OnUpdate = lambda: None
            ticker.Hide()
        for row in self.rows:
            row.Restore()
        for card in self.cards:
            card.Restore()
        adapters = (window.startButton, window.stopButton)
        if isinstance(window.startButton, ButtonAdapter):
            states = [(adapter.IsEnabled(), adapter.IsDown()) for adapter in adapters]
            for original, (enabled, down) in zip(self.originals, states):
                original.Enable() if enabled else original.Disable()
                original.Down() if down else original.SetUp()
        window.startButton, window.stopButton, window.saveButton = self.originals
        for original in self.originals:
            original.Show()
        for name in ('save', 'start', 'stop', 'instant', 'card_name', 'card_count', 'card_chevron', 'alt_label',
                     'segment'):
            widget = getattr(self, name, None)
            if widget is not None:
                widget.Hide()
                if hasattr(widget, 'callback'):
                    widget.callback = None
        for widget in list(getattr(self, 'alt_label_hidden', [])) + list(getattr(self, 'picker_hidden', [])):
            widget.Show()
        for clear in self.clears:
            clear.Restore()
        for skin in (getattr(self, 'main', None), getattr(self, 'footer', None), self.board):
            if skin is not None:
                skin.Restore()
                skin.Destroy()
        for widget, pos, size in reversed(getattr(self, 'moved', [])):
            widget.SetSize(*size)
            widget.SetPosition(*pos)
        self.moved = []

    Destroy = Restore
