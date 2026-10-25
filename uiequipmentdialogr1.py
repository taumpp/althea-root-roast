# -*- coding: utf-8 -*-
"""Výzbroj (the equipment of another player, uiequipmentdialog.EquipmentDialog) in the R1 look (owner
11. 10. 2026, round 4b): the SAME boards, slot places and Výbava / Kostýmy tabs as the own inventory
(root/uiinventoryr1.py), without the costume eyes, under a player card.

uir1frame dresses the board (R1 frame, header, X); this skin, built by the dialog unless Settings -> "Starý vzhled"
chose the original look, adds:

* the title "Výzbroj" and the player card under it: the face in the R1 portrait frame of the character window and
  three separate lines - the name / "Lv." + the level | the job / "Cech" + the guild. The level shows only when the
  client knows it: the server sends it right after the equipment (game command ViewEquipInfoV1); without it the line holds the job only. The job comes from that command or from the character's race,
  the guild from the character's guild id (a guild the client has no name for leaves its line out);
* the boards of the inventory (althea_r1_postava/inventory/panel_equipment.png, panel_costume.png: the lit R1 panel
  with the R1 item slot C at each slot) at the inventory's places: Equipment_Base 10, EquipmentSlot 2, 1;
  Costume_Base 8, CostumeSlot 7, 3 (the dialog's own uiscript had the costume slots 4 px further left);
* the inventory's Výbava / Kostýmy tab row (mode_inactive / mode_active, the row frame, the texts, the vein under the
  selected tab) instead of the old icon tabs;
* the type outline of every empty slot (hint_<eq|co>_<slot>.png), hidden under an item;
* the ring (inventory: ring 1 at 2, 106 - the view packet sends it as index 18; its index 25 is the pendant, which
  the inventory board does not show) and the special items 3 and 4 (ability cells 1, 2: not in the view packet, the
  vnums come with ViewEquipInfoV1).

Every change of an original control is recorded (uir1skin.Recorder); a failed build undoes everything and the
dialog keeps the original look.
"""
import ui
from _weakref import proxy

import uir1
import uir1skin
import uir1tokens as T

ART = 'd:/ymir work/ui/public/althea_r1_postava/inventory/'
PORTRAIT = 'd:/ymir work/ui/public/althea_r1_postava/character/portrait_frame.png'
ORIGINAL_EQUIPMENT = 'd:/ymir work/ui/game/inventory/equipment_inventory.png'
ORIGINAL_COSTUME = 'd:/ymir work/ui/game/inventory/costume_inventory.png'

WIDTH = 176
PAD = 10
CARD_GAP = 6            # header -> card
PORTRAIT_SIZE = 53
FACE_INSET = 5          # the 43 px face inside the 53 px frame
TEXT_X = PAD + PORTRAIT_SIZE + 9
LINE_STEP = 17
SEPARATOR_GAP = 8       # level -> separator -> job
SEPARATOR_COLOR = 0xFF5C5652    # the graphite hairline between the level and the job (1 px)
DIVIDER_GAP = 7         # card -> divider
TAB_GAP = 9             # divider -> tab row
TAB_CELL, TAB_H = 78, 20
TAB_VEIN = (6, 66)
TAB_TEXT_X = (39, 117)
BOARD_GAP = 5           # tab row -> boards
BOARD_H = 187
BOTTOM = 10
EQUIPMENT_X, COSTUME_X = 10, 8
EQUIPMENT_SLOT = (2, 1)
COSTUME_SLOT = (7, 3)

# packet index -> hint of the empty slot ((side, key), x, y in the slot window); the inventory's places
EQUIPMENT_HINTS = {
    0: ('armor', 39, 37), 1: ('head', 39, 2), 2: ('shoes', 39, 145), 3: ('wrist', 75, 67), 4: ('weapon', 3, 3),
    5: ('neck', 114, 67), 6: ('ear', 114, 35), 7: ('unique1', 2, 145), 8: ('unique2', 75, 145),
    10: ('shield', 75, 35), 14: ('sash', 74, 3), 20: ('belt', 39, 106), 21: ('glove', 75, 106),
    25: ('ring', 2, 106),
}
COSTUME_HINTS = {
    11: ('body', 55, 72), 12: ('hair', 57, 29), 13: ('mount', 106, 92), 15: ('weapon', 10, 15), 16: ('aura', 106, 50),
    17: ('pet', 59, 147), 22: ('sash_skin', 106, 8), 23: ('glow_weapon', 18, 144), 24: ('glow_armor', 97, 144),
}
# the view packet's ring 1 (index 18) is drawn in the slot window's cell 25 (2, 106 - the inventory's ring 1 place);
# the packet's 25 (the pendant) has no cell on the inventory board
RING_PACKET, RING_CELL, PENDANT_PACKET = 18, 25, 25
# special items 3 and 4 (the inventory's ability cells 1, 2): cells added to the equipment slot window
SPECIAL_CELLS = ((100, 'unique3', 114, 106), (101, 'unique4', 114, 145))

JOBS = {   # race -> (Czech, English)
    0: (u'Válečník', 'Warrior'), 4: (u'Válečnice', 'Warrior'),
    1: (u'Ninja', 'Ninja'), 5: (u'Ninja', 'Ninja'),
    2: (u'Sura', 'Sura'), 6: (u'Sura', 'Sura'),
    3: (u'Šamanka', 'Shaman'), 7: (u'Šaman', 'Shaman'),
    8: (u'Lykan', 'Lycan'),
}
FACES = {0: 'warrior_m', 1: 'assassin_w', 2: 'sura_m', 3: 'shaman_w', 4: 'warrior_w', 5: 'assassin_m',
         6: 'sura_w', 7: 'shaman_m', 8: 'wolfman_m'}


def _Tr(czech, english):
    try:
        from settingslocale import Text
        return Text(czech, english)
    except Exception:
        return czech


def Apply(dialog, drop):
    """The skin of ``dialog`` when the R1 look is on and the shared R1 frame (uir1frame) dressed it, else None (the
    original look: "Starý vzhled", or the frame failed / is not there). ``drop`` (the dialog's own drop of the skin)
    joins the frame's undo, so the frame failing later takes the skin with it. A build failure is traced and
    undone; None."""
    if not uir1.UseR1():
        return None
    frame = dialog.__dict__.get('r1frame')
    if frame is None:
        return None
    try:
        skin = EquipmentSkin(dialog)
    except Exception:
        uir1.TraceFailure('the equipment dialog')
        return None
    frame.undo.append(drop)
    return skin


def Layout():
    """y of the card, the tab row, the boards and the window height (the window keeps its width 176)."""
    card = T.HEAD_H + CARD_GAP
    divider = card + PORTRAIT_SIZE + DIVIDER_GAP
    tabs = divider + T.RULE_H + TAB_GAP
    boards = tabs + TAB_H + BOARD_GAP
    return dict(card=card, divider=divider, tabs=tabs, boards=boards, height=boards + BOARD_H + BOTTOM)


def JobName(race):
    names = JOBS.get(race)
    return _Tr(names[0], names[1]) if names else ''


def GuildName(guild_id):
    if not guild_id:
        return ''
    try:
        import guild
        name = guild.GetGuildName(int(guild_id))
    except Exception:
        return ''
    return '' if not name or name == 'Noname' else name


class EquipmentSkin(object):
    """R1 look of one EquipmentDialog. Build failures undo every change and re-raise (the dialog traces them)."""

    def __init__(self, dialog):
        self.dialog = dialog
        self.kit = uir1.Kit()
        self.rec = uir1skin.Recorder()
        self.widgets = []
        self.hints = {}             # packet index -> hint image
        self.special = {}           # cell -> (vnum)
        self.tab_texts = []
        self.tabs = []
        self.tab_vein = None
        self.level = None
        self.race = None
        self.vid = None
        try:
            self._Build()
        except Exception:
            self.Undo()
            raise

    # ------------------------------------------------------------------ build
    def _Build(self):
        d, rec = self.dialog, self.rec
        lay = Layout()
        board = d.board
        for widget in (d, board):
            self._Size(widget, WIDTH, lay['height'])
        # the boards and the slots at the inventory's places
        rec.Image(d.maskEquipment, ART + 'panel_equipment.png', ORIGINAL_EQUIPMENT)
        rec.Position(d.maskEquipment, EQUIPMENT_X, lay['boards'])
        rec.Position(d.slotWindow, EQUIPMENT_SLOT[0], EQUIPMENT_SLOT[1])
        rec.Image(d.maskCostume, ART + 'panel_costume.png', ORIGINAL_COSTUME)
        rec.Position(d.maskCostume, COSTUME_X, lay['boards'])
        rec.Position(d.costumeSlotWindow, COSTUME_SLOT[0], COSTUME_SLOT[1])
        self._BuildHints()
        self._BuildCard(lay)
        self._BuildTabs(lay)
        # last (cannot be undone - a later failure would leave them, empty, in the original look)
        for cell, key, x, y in SPECIAL_CELLS:
            d.slotWindow.AppendSlot(cell, x, y, 32, 32)

    def _Size(self, widget, w, h):
        """SetSize with its undo - which leaves a size the window set later alone (only ours goes back)."""
        ow, oh = widget.GetWidth(), widget.GetHeight()
        widget.SetSize(w, h)

        def back():
            if (widget.GetWidth(), widget.GetHeight()) == (w, h):
                widget.SetSize(ow, oh)
        self.rec.Call(lambda: None, back)

    def _Hint(self, parent, side, key, x, y):
        image = ui.ImageBox()
        image.SetParent(parent)
        image.AddFlag('not_pick')
        image.LoadImage(ART + 'hint_%s_%s.png' % (side, key))
        image.SetPosition(int(x), int(y))
        image.Show()
        self.widgets.append(image)
        return image

    def _BuildHints(self):
        d = self.dialog
        ex, ey = EQUIPMENT_SLOT
        for index, (key, x, y) in EQUIPMENT_HINTS.items():
            self.hints[index] = self._Hint(d.maskEquipment, 'eq', key, ex + x, ey + y)
        for cell, key, x, y in SPECIAL_CELLS:
            self.hints[cell] = self._Hint(d.maskEquipment, 'eq', key, ex + x, ey + y)
        cx, cy = COSTUME_SLOT
        for index, (key, x, y) in COSTUME_HINTS.items():
            self.hints[index] = self._Hint(d.maskCostume, 'co', key, cx + x, cy + y)

    def _BuildTabs(self, lay):
        """The inventory's Výbava / Kostýmy row: own radio buttons with the inventory's mode plates over the original
        ones (hidden - they have no art of their own to go back to, they lay over the old icon strip), the row
        frame, the texts and the vein under the selected tab. A click selects the page as the original tab does."""
        d, rec, kit = self.dialog, self.rec, self.kit
        control = d.GetChild('EquipmentTabControl')
        rec.Position(control, PAD, lay['tabs'])
        for image in d.imageTab:
            rec.Hide(image)
        for index, tab in enumerate(d.equipmentTab):
            rec.Hide(tab)
            button = ui.RadioButton()
            button.SetParent(control)
            button.SetPosition(index * TAB_CELL, 0)
            button.SetUpVisual(ART + 'mode_inactive.png')
            button.SetOverVisual(ART + 'mode_inactive.png')
            button.SetDownVisual(ART + 'mode_active.png')
            button.SetEvent(lambda page=index, owner=proxy(self): owner.dialog.SetEquipmentPage(page))
            button.Show()
            self.tabs.append(button)
            self.widgets.append(button)
        frame = ui.ImageBox()
        frame.SetParent(control)
        frame.AddFlag('not_pick')
        frame.LoadImage(ART + 'mode_frame.png')
        frame.SetPosition(0, 0)
        frame.Show()
        self.widgets.append(frame)
        font = kit.font('text_s')
        top = max(0, (TAB_H - kit.cell('text_s')) // 2)
        for x, text in zip(TAB_TEXT_X, (_Tr(u'Výbava', 'Equipment'), _Tr(u'Kostýmy', 'Costumes'))):
            line = uir1.Text(control, text, x, top, font, T.INK_DIM, align='center', valign='top')
            self.tab_texts.append(line)
            self.widgets.append(line)
        self.tab_vein = uir1.Vein(control, TAB_VEIN[0], TAB_H - 1, TAB_VEIN[1])
        self.widgets.append(self.tab_vein)

    def _BuildCard(self, lay):
        d, kit = self.dialog, self.kit
        board, y = d.board, lay['card']
        self.face = ui.ImageBox()
        self.face.SetParent(board)
        self.face.AddFlag('not_pick')
        self.face.SetPosition(PAD + FACE_INSET, y + FACE_INSET)
        self.widgets.append(self.face)
        frame = ui.ImageBox()
        frame.SetParent(board)
        frame.AddFlag('not_pick')
        frame.LoadImage(PORTRAIT)
        frame.SetPosition(PAD, y)
        frame.Show()
        self.widgets.append(frame)
        text, bold = kit.font('text_s'), kit.font('text_sb')
        self.name = uir1.Text(board, '', TEXT_X, y + 3, bold, T.IVORY, valign='top')
        line2 = y + 3 + LINE_STEP
        self.level_label = uir1.Text(board, 'Lv.', TEXT_X, line2, text, T.MUTED, valign='top')
        self.level_value = uir1.Text(board, '', TEXT_X, line2, text, T.IVORY, valign='top')
        self.separator = ui.Bar()
        self.separator.SetParent(board)
        self.separator.AddFlag('not_pick')
        self.separator.SetSize(1, kit.cell('text_s') - 2)
        self.separator.SetColor(SEPARATOR_COLOR)
        self.job = uir1.Text(board, '', TEXT_X, line2, text, T.INK, valign='top')
        line3 = line2 + LINE_STEP
        self.guild_label = uir1.Text(board, _Tr(u'Cech', 'Guild'), TEXT_X, line3, text, T.MUTED, valign='top')
        self.guild_value = uir1.Text(board, '', TEXT_X, line3, text, T.INK, valign='top')
        self.widgets += [self.name, self.level_label, self.level_value, self.separator, self.job, self.guild_label,
                         self.guild_value]
        self.divider = uir1.Divider(board, PAD, lay['divider'], WIDTH - 2 * PAD)
        self.widgets.append(self.divider)

    # ------------------------------------------------------------------ state
    def Open(self, vid):
        """The dialog opened for ``vid``: the R1 title, the card from what the client knows, every slot empty."""
        self.vid = vid
        self.level = None
        self.race = None
        self.special = {}
        try:
            import chr
            name = chr.GetNameByVID(vid)
            race = chr.GetVirtualNumber(vid)
            guild_id = chr.GetGuildID(vid)
        except Exception:
            name, race, guild_id = '', None, 0
        self.dialog.board.SetTitleName(_Tr(u'Výzbroj', 'Equipment'))
        self.name.SetText(name if name and name != 'None' else '')
        if race in JOBS:
            self.race = race
        self.guild = GuildName(guild_id)
        self._Card()
        for image in self.hints.values():
            image.Show()
        for cell, unused, unused2, unused3 in SPECIAL_CELLS:
            self.dialog.slotWindow.ClearSlot(cell)

    def SetInfo(self, level, race, specials):
        """ViewEquipInfoV1 of the server: the level, the race and the vnums of the special items 3 and 4."""
        self.level = int(level) if int(level) > 0 else None
        if int(race) in JOBS:
            self.race = int(race)
        self._Card()
        for (cell, unused, unused2, unused3), vnum in zip(SPECIAL_CELLS, specials):
            vnum = int(vnum)
            if vnum:
                self.special[cell] = vnum
                self.dialog.slotWindow.SetItemSlot(cell, vnum, 0)
                self.Filled(cell)
        self.dialog.slotWindow.RefreshSlot()

    def SetInfoSafe(self, level, race, specials):
        """SetInfo() for the dialog: a failure is traced and never breaks the dialog."""
        try:
            self.SetInfo(level, race, specials)
        except Exception:
            uir1.TraceFailure('the equipment dialog (info)')

    def _Card(self):
        if self.race is not None:
            self.face.LoadImage('icon/face/%s.tga' % FACES[self.race])
            self.face.Show()
        else:
            self.face.Hide()
        job = JobName(self.race) if self.race is not None else ''
        x = TEXT_X
        if self.level:
            self.level_label.Show()
            self.level_value.SetText(str(self.level))
            x += uir1.TextWidth(self.level_label) + 4
            self.level_value.SetPosition(x, self.level_value.GetLocalPosition()[1])
            self.level_value.Show()
            x += uir1.TextWidth(self.level_value) + SEPARATOR_GAP
            if job:
                self.separator.SetPosition(x, self.level_value.GetLocalPosition()[1] + 2)
                self.separator.Show()
                x += 1 + SEPARATOR_GAP
            else:
                self.separator.Hide()
        else:
            self.level_label.Hide()
            self.level_value.Hide()
            self.separator.Hide()
        self.job.SetText(job)
        self.job.SetPosition(x, self.job.GetLocalPosition()[1])
        if self.guild:
            self.guild_label.Show()
            self.guild_value.SetText(self.guild)
            self.guild_value.SetPosition(TEXT_X + uir1.TextWidth(self.guild_label) + 6,
                                         self.guild_value.GetLocalPosition()[1])
            self.guild_value.Show()
        else:
            self.guild_label.Hide()
            self.guild_value.Hide()

    def Filled(self, cell):
        """An item came into ``cell``: its type outline hides."""
        image = self.hints.get(cell)
        if image is not None:
            image.Hide()

    def SpecialItem(self, cell):
        return self.special.get(cell, 0)

    def SyncPage(self, page):
        """The vein and the bright text under the selected tab."""
        kit = self.kit
        for index, line in enumerate(self.tab_texts):
            selected = index == page
            uir1.SetFont(line, kit.font('text_sb' if selected else 'text_s'))
            line.SetPackedFontColor(T.IVORY if selected else T.INK_DIM)
        self.tab_vein.SetPosition(page * TAB_CELL + TAB_VEIN[0], TAB_H - 1 - T.VEIN_ROW)
        for index, button in enumerate(self.tabs):
            if index == page:
                button.Down()
            else:
                button.SetUp()

    # ------------------------------------------------------------------ teardown
    def Undo(self):
        self.rec.Undo()
        self.Destroy()

    def Destroy(self):
        for widget in self.widgets:
            try:
                widget.Hide()
            except Exception:
                pass
        uir1skin.Destroy([w for w in self.widgets if hasattr(w, 'ops')])
        self.widgets = []
        self.hints = {}
        self.tab_texts = []
        self.tab_vein = None
        self.dialog = None
