"""Quick equipment presets. The server owns item identities and all mutations."""

import chat
import item
import mouseModule
import net
import player
import ui
import uiCommon
import uiToolTip
import uiScriptLocale
import quickequipstyle as style
from _weakref import proxy

MAX_SETS = 8
VISIBLE_SETS = 4
EMPTY_SET_NAME = "Prázdná sada"
# Slot keys are server wear positions (server-src game/src/quick_equip.cpp
# kWearSlots). The glove wear position comes from the EXE: EQUIPMENT_GLOVE is
# the global equipment cell, so WEAR_GLOVE = 33. Wear 38 is WEAR_BUFFI_SASH.
GLOVE_WEAR = item.EQUIPMENT_GLOVE - player.EQUIPMENT_SLOT_START
EQUIPMENT_SLOTS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 22, 29, 31, GLOVE_WEAR)
COSTUME_SLOTS = (19, 20, 21, 27, 23, 24, 25, 26, 28)
EDIT_ICON = "d:/ymir work/ui/game/crimson_ember/custom_ports/icon_edit_16.png"


def _text(parent, x, y, value, color=0xffe1d4c4, font=style.BODY_FONT):
    line = ui.TextLine()
    line.SetParent(parent)
    line.SetPosition(x, y)
    line.SetFontName(font)
    line.SetPackedFontColor(style.argb(color))
    line.SetText(value)
    line.Show()
    return line


class _SetRow(ui.Window):
    def __init__(self, owner, row):
        ui.Window.__init__(self)
        self.owner = proxy(owner)
        self.row = row
        self.index = 0
        self.SetParent(owner)
        self.SetPosition(18, 74 + row * 41)
        self.SetSize(159, 36)
        self.background = ui.Bar()
        self.background.SetParent(self)
        self.background.SetPosition(0, 0)
        self.background.SetSize(159, 36)
        self.background.AddFlag("not_pick")
        self.background.Show()
        self.accent = ui.Bar()
        self.accent.SetParent(self)
        self.accent.SetPosition(0, 0)
        self.accent.SetSize(3, 36)
        self.accent.SetColor(style.argb(0xffbe4e5d))
        self.accent.AddFlag("not_pick")
        self.topEdge = ui.Bar()
        self.topEdge.SetParent(self)
        self.topEdge.SetPosition(0, 0)
        self.topEdge.SetSize(159, 1)
        self.topEdge.AddFlag("not_pick")
        self.topEdge.Show()
        self.number = _text(self, 11, 10, "", 0xffc29783, style.DENSE_FONT)
        self.number.AddFlag("not_pick")
        self.name = _text(self, 34, 9, "")
        self.name.AddFlag("not_pick")
        self.selectedArrow = _text(self, 148, 10, "\u203a", 0xffe2a1a4, style.ARROW_FONT)
        self.selectedArrow.AddFlag("not_pick")
        self.selectedArrow.Hide()
        self.selected = False
        self.edit = ui.Button()
        self.edit.SetParent(self)
        self.edit.SetPosition(136, 10)
        self.edit.SetUpVisual(EDIT_ICON)
        self.edit.SetOverVisual(EDIT_ICON)
        self.edit.SetDownVisual(EDIT_ICON)
        self.edit.SetEvent(ui.__mem_func__(self._Rename))

    def SetData(self, index, name, selected):
        self.index = index
        self.selected = selected
        if index is None:
            self.Hide()
            return
        # Page zero is the permanent, usable first storage page.
        self.number.SetText("%02d" % (index + 1))
        self.name.SetFontName(style.BOLD_FONT if selected else style.BODY_FONT)
        self.name.SetText(name)
        # Fit real Czech names by pixel width instead of clipping mid-glyph.
        limit = 98 if index else 114
        shortened = name
        while shortened and self.name.GetTextSize()[0] > limit:
            shortened = shortened[:-1]
            self.name.SetText(shortened + "...")
        self.name.SetPackedFontColor(style.argb(0xffe1d4c4))
        self.background.SetColor(style.argb(0xff4c252c if selected else 0xff191415))
        self.topEdge.SetColor(style.argb(0xff79604e if selected else 0xff403531))
        if selected:
            self.accent.Show()
        else:
            self.accent.Hide()
        self.selectedArrow.Show() if selected and not index else self.selectedArrow.Hide()
        if index:
            self.edit.Show()
        else:
            self.edit.Hide()
        self.Show()

    def OnMouseOverIn(self):
        if not self.selected:
            self.background.SetColor(style.argb(0xff302125))

    def OnMouseOverOut(self):
        self.background.SetColor(style.argb(0xff4c252c if self.selected else 0xff191415))

    def _Rename(self):
        if self.index:
            self.owner.OpenNameDialog(self.index)

    def OnMouseLeftButtonDown(self):
        if self.index is not None:
            self.owner.SelectSet(self.index)

    def OnMouseRightButtonDown(self):
        if self.index:
            self.owner.AskDelete(self.index)


class _NameDialog(ui.ScriptWindow):
    def __init__(self, owner):
        ui.ScriptWindow.__init__(self)
        self.owner = proxy(owner)
        self.index = 0
        self.__Load()

    def __Load(self):
        loader = ui.PythonScriptLoader()
        loader.LoadScriptFile(self, "uiscript/quickequipnamedialog.py")
        self.board = self.GetChild("Board")
        self.input = self.GetChild("NameInput")
        self.GetChild("SaveButton").SetEvent(ui.__mem_func__(self.Accept))
        self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Close))
        self.board.SetCloseEvent(ui.__mem_func__(self.Close))
        self.input.SetReturnEvent(ui.__mem_func__(self.Accept))
        self.input.SetEscapeEvent(ui.__mem_func__(self.Close))
        self.Hide()

    def Open(self, index, previous=""):
        self.index = index
        self.board.SetTitleName("Přejmenovat sadu" if previous else "Nová sada výbavy")
        self.input.SetText(previous)
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.input.SetFocus()

    def Accept(self):
        name = self.input.GetText().strip()
        encoded = name.encode("utf-8")
        if not name or len(encoded) > 48 or any(ord(ch) < 32 for ch in name):
            chat.AppendChat(chat.CHAT_TYPE_INFO, "Zadej název sady (maximálně 48 bajtů).")
            return
        self.owner.SaveName(self.index, encoded.hex())
        self.Close()

    def Close(self):
        self.Hide()
        self.input.KillFocus()


class QuickEquipWindow(ui.ScriptWindow):
    def __init__(self):
        ui.ScriptWindow.__init__(self)
        self.sets = {}
        self.emptyItems = {}
        self.selected = 0
        self.scroll = 0
        self.ready = False
        self.unavailable = False
        self.tooltip = uiToolTip.ItemToolTip()
        self.deleteDialog = None
        self.closeEvent = None
        self.__Load()

    def SetCloseEvent(self, event):
        self.closeEvent = event

    def __Load(self):
        loader = ui.PythonScriptLoader()
        loader.LoadScriptFile(self, "uiscript/quickequipwindow.py")
        titleBar = self.GetChild("TitleBar")
        titleBar.SetCloseEvent(ui.__mem_func__(self.Close))
        titleBar.btnClose.SetPosition(titleBar.GetWidth() - titleBar.btnClose.GetWidth() - 3, 2)
        self.equipment = self.GetChild("EquipmentSlots")
        self.costume = self.GetChild("CostumeSlots")
        for slots in (self.equipment, self.costume):
            slots.SetSelectEmptySlotEvent(ui.__mem_func__(self._PutItem))
            slots.SetSelectItemSlotEvent(ui.__mem_func__(self._PutItem))
            slots.SetUnselectItemSlotEvent(ui.__mem_func__(self._ClearItem))
            slots.SetOverInItemEvent(ui.__mem_func__(self._OverItem))
            slots.SetOverOutItemEvent(ui.__mem_func__(self._OutItem))
        self.newButton = self.GetChild("NewSetButton")
        self.newButton.SetEvent(ui.__mem_func__(self._NewSet))
        self.applyButton = self.GetChild("ApplyButton")
        self.applyButton.SetEvent(ui.__mem_func__(self._Apply))
        for button, text in ((self.newButton, uiScriptLocale.QUICK_EQUIP_NEW_SET),
                             (self.applyButton, uiScriptLocale.QUICK_EQUIP_APPLY)):
            # Select the font before the first text builds native glyphs.
            button.SetFontName(style.BUTTON_FONT)
            button.SetText(text)
            button.SetTextColor(style.argb(0xffe1d4c4))
        self.selectedLabel = self.GetChild("SelectedSetName")
        self.selectedHint = self.GetChild("SelectedSetHint")
        self.setsCount = self.GetChild("SetsCount")
        self.rows = [_SetRow(self, i) for i in range(VISIBLE_SETS)]
        self.nameDialog = _NameDialog(self)
        self.Refresh()
        self.Hide()

    def Open(self):
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.ready = False
        self.unavailable = False
        self.Refresh()
        net.SendChatPacket("/quick_equip list")

    def Toggle(self):
        if self.IsShow():
            self.Close()
        else:
            self.Open()

    def Close(self):
        self.nameDialog.Close()
        if self.deleteDialog:
            self.deleteDialog.Close()
            self.deleteDialog = None
        self.tooltip.HideToolTip()
        self.Hide()
        if self.closeEvent:
            self.closeEvent()

    def Destroy(self):
        self.closeEvent = None
        self.Close()
        self.ClearDictionary()
        self.rows = []
        self.nameDialog = None
        self.tooltip = None

    def Reset(self):
        self.sets = {}
        self.emptyItems = {}
        self.ready = False
        self.unavailable = False

    def ReceiveSet(self, indexText, nameHex):
        try:
            index = int(indexText)
            name = bytes.fromhex(nameHex).decode("utf-8")
        except (ValueError, UnicodeDecodeError):
            return
        if 1 <= index <= MAX_SETS and 0 < len(name.encode("utf-8")) <= 48:
            self.sets[index] = {"name": name, "items": {}}

    def ReceiveItem(self, indexText, wearText, vnumText):
        try:
            index, wear, vnum = int(indexText), int(wearText), int(vnumText)
        except ValueError:
            return
        if wear in EQUIPMENT_SLOTS + COSTUME_SLOTS and 0 <= vnum <= 999999999:
            if index == 0:
                self.emptyItems[wear] = vnum
            elif index in self.sets:
                self.sets[index]["items"][wear] = vnum

    def Ready(self):
        self.ready = True
        self.unavailable = False
        if self.selected not in self.sets:
            self.selected = 0
        self.Refresh()

    def Status(self, code):
        if code in ("MIGRATION_PENDING", "DB_ERROR"):
            self.ready = False
            self.unavailable = True
            self.Refresh()
        messages = {
            "OK": "Výbava byla přepnuta.",
            "DB_ERROR": "Sady výbavy nyní nejsou dostupné.",
            "MIGRATION_PENDING": "Rychlá výměna se připravuje. Zkus to později.",
            "RECOVERY_WAITING": "Některé předměty čekají na volné místo v inventáři. Uvolni místo a otevři sady znovu.",
            "BUSY": "Výbavu teď nelze měnit.",
            "BAD_NAME": "Neplatný název sady.",
            "MISSING_ITEM": "Některý uložený předmět už nemáš u sebe.",
            "MOVE_MANUALLY": "Předmět je nasazen v jiném slotu; nejprve jej přesuň.",
            "NO_SPACE": "V inventáři není místo pro výměnu.",
            # Belt cells are retired; an older server may still refuse the swap.
            "BELT_NOT_EMPTY": "Opasek nelze přepnout sadou; vyměň ho ručně.",
            "CANNOT_EQUIP": "Některý předmět nyní nelze nasadit.",
            "LINKED_COSTUME": "Nejprve sundej navázaný kostým nebo efekt.",
            "DISMOUNT_FIRST": "Před výměnou mounta sesedni.",
            "PARTIAL": "Výměna se nepodařila úplně. Zkontroluj výbavu.",
            "FAILED": "Výměna selhala; původní výbava byla obnovena.",
            "INVALID_ITEM": "Tento předmět do vybraného slotu nepatří.",
            "NOT_EMPTY": "Nejdříve vyprázdni sloty této sady.",
        }
        if code in messages:
            chat.AppendChat(chat.CHAT_TYPE_INFO, messages[code])

    def Refresh(self):
        indices = [0] + sorted(self.sets)
        if self.scroll > max(0, len(indices) - VISIBLE_SETS):
            self.scroll = max(0, len(indices) - VISIBLE_SETS)
        visible = indices[self.scroll:self.scroll + VISIBLE_SETS]
        for row, index in zip(self.rows, visible + [None] * (VISIBLE_SETS - len(visible))):
            row.SetData(index, self.sets[index]["name"] if index else EMPTY_SET_NAME, index == self.selected)
        self.setsCount.SetText("%d/%d" % (len(self.sets) + 1, MAX_SETS + 1))
        self.newButton.Show() if len(self.sets) < MAX_SETS else self.newButton.Hide()
        self.newButton.Enable() if self.ready else self.newButton.Disable()
        self.selectedHint.SetText(uiScriptLocale.QUICK_EQUIP_SELECTED)
        if self.selected in self.sets:
            self.selectedLabel.SetText("%02d  %s" % (self.selected + 1, self.sets[self.selected]["name"][:20]))
            self.applyButton.Enable() if self.ready else self.applyButton.Disable()
        else:
            self.selectedLabel.SetText("01  " + EMPTY_SET_NAME)
            self.applyButton.Enable() if self.ready else self.applyButton.Disable()
        if self.unavailable:
            self.selectedLabel.SetText(uiScriptLocale.QUICK_EQUIP_UNAVAILABLE)
            self.selectedHint.SetText(uiScriptLocale.QUICK_EQUIP_TRY_LATER)
        items = self.emptyItems if self.selected == 0 else self.sets.get(self.selected, {}).get("items", {})
        for slotWindow, allowed in ((self.equipment, EQUIPMENT_SLOTS), (self.costume, COSTUME_SLOTS)):
            for wear in allowed:
                cell = self.selected * player.QUICK_EQUIP_PAGE_SIZE + wear
                vnum = player.GetItemIndex(player.QUICK_EQUIP, cell) if hasattr(player, "QUICK_EQUIP") else items.get(wear, 0)
                if vnum:
                    slotWindow.SetItemSlot(wear, vnum, 0)
                else:
                    slotWindow.ClearSlot(wear)
            slotWindow.RefreshSlot()

    def OnRunMouseWheel(self, delta):
        self.scroll = max(0, min(max(0, len(self.sets) + 1 - VISIBLE_SETS),
                                  self.scroll - (1 if delta > 0 else -1)))
        self.Refresh()
        return True

    def SelectSet(self, index):
        if index == 0 or index in self.sets:
            self.selected = index
            self.Refresh()

    def _NewSet(self):
        if not self.ready or len(self.sets) >= MAX_SETS:
            return
        index = next((i for i in range(1, MAX_SETS + 1) if i not in self.sets), 0)
        if index:
            self.OpenNameDialog(index)

    def OpenNameDialog(self, index):
        if not self.ready:
            return
        previous = self.sets.get(index, {}).get("name", "")
        self.nameDialog.Open(index, previous)

    def SaveName(self, index, nameHex):
        operation = "rename" if index in self.sets else "create"
        net.SendChatPacket("/quick_equip %s %d %s" % (operation, index, nameHex))
        if operation == "create":
            self.selected = index

    def AskDelete(self, index):
        if not self.ready or index not in self.sets:
            return
        if self.deleteDialog:
            self.deleteDialog.Close()
        self.deleteDialog = uiCommon.QuestionDialog()
        self.deleteDialog.SetText("Smazat sadu %s?" % self.sets[index]["name"][:16])
        self.deleteDialog.SetAcceptEvent(lambda i=index, owner=proxy(self): owner._Delete(i))
        self.deleteDialog.SetCancelEvent(ui.__mem_func__(self._CancelDelete))
        self.deleteDialog.Open()

    def _Delete(self, index):
        self._CancelDelete()
        net.SendChatPacket("/quick_equip delete %d" % index)

    def _CancelDelete(self):
        if self.deleteDialog:
            self.deleteDialog.Close()
            self.deleteDialog = None

    def _Apply(self):
        if self.ready and (self.selected == 0 or self.selected in self.sets):
            net.SendChatPacket("/quick_equip apply %d" % self.selected)

    def _PutItem(self, wear):
        if not self.ready or (self.selected != 0 and self.selected not in self.sets):
            return
        mouse = mouseModule.mouseController
        cell = self.selected * player.QUICK_EQUIP_PAGE_SIZE + wear
        if not mouse.isAttached():
            vnum = player.GetItemIndex(player.QUICK_EQUIP, cell)
            if vnum:
                mouse.AttachObject(self, player.SLOT_TYPE_QUICK_EQUIP, cell, vnum,
                                   player.GetItemCount(player.QUICK_EQUIP, cell))
            return
        if mouse.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
            return
        source = mouse.GetAttachedSlotNumber()
        if source < 0:
            return
        net.SendItemMovePacket(player.INVENTORY, source, player.QUICK_EQUIP, cell, 1)
        mouse.DeattachObject()

    def _ClearItem(self, wear):
        if self.ready and (self.selected == 0 or self.selected in self.sets):
            net.SendChatPacket("/quick_equip clear %d %d" % (self.selected, wear))

    def _OverItem(self, wear):
        cell = self.selected * player.QUICK_EQUIP_PAGE_SIZE + wear
        vnum = player.GetItemIndex(player.QUICK_EQUIP, cell)
        if vnum:
            self.tooltip.SetInventoryItem(cell, player.QUICK_EQUIP)

    def _OutItem(self):
        self.tooltip.HideToolTip()
