# -*- coding: utf-8 -*-
import app
import chat
import constInfo
import uiCommon
import item
import localeInfo
import mouseModule
import net
import player
import skill
import ui
import uiToolTip
import uir1
import uir1chat


# The shared prototype discriminator and operation enum are protocol fields.
SERVICE_PROTO_TAG = 0x5349


def _Text(key):
    # locale_game.txt of the client language; the key itself if a pack lacks it.
    return getattr(localeInfo, key, key)

SINGLE_TARGET_KINDS = (4, 5)
_pendingApply = None


def SingleTargetKind(vnum):
    if not vnum:
        return 0
    item.SelectItem(vnum)
    kind = item.GetValue(0) if item.GetValue(5) == SERVICE_PROTO_TAG else 0
    return kind if kind in SINGLE_TARGET_KINDS else 0


def CanApplyCertificate(sourceCell, targetCell):
    source = player.GetItemIndex(sourceCell)
    if sourceCell == targetCell or player.IsEquipmentSlot(targetCell):
        return False
    target = player.GetItemIndex(targetCell)
    if not target:
        return False
    item.SelectItem(target)
    allowed = item.GetItemType() == item.ITEM_TYPE_COSTUME and item.GetItemSubType() == item.COSTUME_TYPE_ACCE
    item.SelectItem(source)
    return allowed


def ItemImage(cell):
    return (player.GetItemIndex(cell), player.GetItemCount(cell),
            tuple(player.GetItemMetinSocket(cell, i) for i in range(player.METIN_SOCKET_MAX_NUM)),
            tuple(player.GetItemAttribute(cell, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)))


def QueueCertificate(sourceCell, targetCell):
    global _pendingApply
    kind = SingleTargetKind(player.GetItemIndex(sourceCell))
    if not kind:
        return False
    if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() or not CanApplyCertificate(sourceCell, targetCell):
        chat.AppendChat(chat.CHAT_TYPE_INFO, _Text("SERVICE_ITEM_CERT_DRAG"))
        return True
    _pendingApply = (kind, sourceCell, targetCell, ItemImage(sourceCell), ItemImage(targetCell))
    # Opens the server-owned operation; the actual request follows only after confirmation.
    net.SendItemUsePacket(sourceCell)
    return True


class SkillChoice(uir1chat.DropDown):
    def __init__(self, parent, kit, y, changed):
        uir1chat.DropDown.__init__(self, parent, kit, 40, y, 340, [(0, "")], 0, changed)
        self.tooltip = _Text("SERVICE_ITEM_SKILL_PICK")
        self.Hide()

    def ClearItem(self):
        self.CloseMenu()
        self.options = []
        self.value = None

    def InsertItem(self, value, text):
        self.options.append((value, text))

    def SetCurrentItem(self, text):
        self.value = next((key for key, label in self.options if label == text), None)
        self.SetText(text)

    def CloseListBox(self):
        self.CloseMenu()

    def Toggle(self):
        if self.menu:
            self.CloseMenu()
            return
        import uir1layout
        step, pad = uir1layout.button_height(True) + 2, 4
        self.menu = ui.Window("TOP_MOST")
        self.menu.SetSize(self.GetWidth(), len(self.options) * step + 2 * pad - 2)
        self.menu.fill = uir1.Frame(self.menu, 0, 0, self.menu.GetWidth(), self.menu.GetHeight(),
                                   "tooltip", fill_alpha=uir1.MENU_FILL_ALPHA)
        self.menu.options = []
        for index, (value, label) in enumerate(self.options):
            button = uir1chat.TextButton(self.menu, self.kit, pad, pad + index * step,
                self.GetWidth() - 2 * pad, label, _Text("SERVICE_ITEM_SKILL_AFTER_CONFIRM"),
                lambda value=value: self.Select(value))
            button.SetSelected(value == self.value)
            self.menu.options.append(button)
        x, y = self.GetGlobalPosition()
        self.menu.SetPosition(x, y + self.GetHeight())
        self.OnUpdate()
        self.menu.Show()
        self.menu.SetTop()


class ServiceItemWindow(ui.BoardWithTitleBar):
    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self.children = []
        self.cells = [None, None]
        self.kind = 0
        self.confirmDialog = None
        self.confirmPreimages = None
        self.scrollCell = None
        self.scrollVnum = 0
        self.tooltip = uiToolTip.ItemToolTip()
        self.SetSize(420, 280)
        self.AddFlag("movable")
        self.AddFlag("float")
        self.SetCloseEvent(self.Close)
        self.heading = self.Text(24, 43, "")
        self.nameLabel = self.Text(24, 70, _Text("SERVICE_ITEM_FAMILY_NEW"))
        self.nameLabel.SetPackedFontColor(0xffffd58a)
        self.nameField = ui.SlotBar()
        self.nameField.SetParent(self)
        self.nameField.SetPosition(24, 91)
        self.nameField.SetSize(372, 28)
        self.children.append(self.nameField)
        self.nameHelp = self.Text(24, 128, _Text("SERVICE_ITEM_FAMILY_RULE"))
        self.nameWarning = self.Text(24, 147, _Text("SERVICE_ITEM_FAMILY_HINT"))
        self.nameInput = ui.EditLine()
        self.nameInput.SetParent(self.nameField)
        self.nameInput.SetPosition(10, 7)
        self.nameInput.SetSize(350, 18)
        self.nameInput.SetMax(16)
        self.nameInput.SetReturnEvent(self.Accept)
        self.nameInput.SetEscapeEvent(self.Close)
        self.children.append(self.nameInput)
        self.slotSets = {}
        self.slotBacks = {}
        for height in (32, 96):
            slots, backs = [], []
            for index, x in enumerate((100, 288)):
                back = ui.SlotBar()
                back.SetParent(self)
                back.SetPosition(x, 95)
                back.SetSize(32, height)
                back.AddFlag("not_pick")
                back.Hide()
                slot = ui.SlotWindow()
                slot.SetParent(self)
                slot.SetPosition(x, 95)
                slot.SetSize(32, height)
                slot.AppendSlot(0, 0, 0, 32, height)
                slot.SetSelectEmptySlotEvent(lambda unused, index=index: self.Select(index))
                slot.SetSelectItemSlotEvent(lambda unused, index=index: self.Select(index))
                slot.SetUnselectItemSlotEvent(lambda unused, index=index: self.Clear(index))
                slot.SetOverInItemEvent(lambda unused, index=index: self.OverIn(index))
                slot.SetOverOutItemEvent(self.tooltip.HideToolTip)
                slot.Hide()
                slots.append(slot)
                backs.append(back)
                self.children.extend((back, slot))
            self.slotSets[height], self.slotBacks[height] = slots, backs
        self.slots = self.slotSets[32]
        self.sourceLabel = self.Text(45, 65, "Zdroj")
        self.targetLabel = self.Text(265, 65, _Text("SERVICE_ITEM_TARGET_NO_BONUS"))
        self.notice = self.Text(25, 205, _Text("SERVICE_ITEM_RELOG_AFTER"))
        self.action = ui.Button()
        self.action.SetParent(self)
        self.action.SetPosition(135, 240)
        self.action.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
        self.action.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
        self.action.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
        self.action.SetText("Potvrdit")
        self.action.SetEvent(self.Accept)
        self.action.Show()
        self.children.append(self.action)
        self.cancelButton = ui.Button()
        self.cancelButton.SetParent(self)
        self.cancelButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
        self.cancelButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
        self.cancelButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
        self.cancelButton.SetText(_Text("SERVICE_ITEM_CANCEL"))
        self.cancelButton.SetEvent(self.Close)
        self.cancelButton.Show()
        self.children.append(self.cancelButton)
        self.slotHint = self.Text(24, 194, _Text("SERVICE_ITEM_DRAG_ITEMS"))
        self.slotHint.Hide()
        self.skillChoices = [0, 0]
        self.skillNames = [{}, {}]
        self.skillBoxes = []
        for index, y in enumerate((100, 155)):
            box = ui.ComboBox()
            box.SetParent(self)
            box.SetPosition(40, y)
            box.SetSize(340, 24)
            box.SetEvent(lambda value, index=index: self.SelectSkill(index, value))
            box.Hide()
            self.skillBoxes.append(box)
            self.children.append(box)
        try:
            self.DressR1()
        except Exception:
            uir1.TraceFailure("service item window")
        self.Hide()

    def DressR1(self):
        import uir1
        import uir1frame
        import uir1dialog
        self.ElementDictionary = {
            "heading": self.heading, "nameLabel": self.nameLabel,
            "nameHelp": self.nameHelp, "nameWarning": self.nameWarning,
            "sourceLabel": self.sourceLabel, "targetLabel": self.targetLabel,
            "notice": self.notice, "slotHint": self.slotHint,
        }
        options = {"board": None, "texts": {
            name: ("text_xs", "INK_DIM", ()) for name in self.ElementDictionary}}
        options["texts"]["nameLabel"] = ("text_b", "INK", ())
        frame = uir1frame.Dress(self, options)
        if frame is None:
            return
        try:
            kit = uir1.Kit()
            for height, slots in self.slotSets.items():
                for slot in slots:
                    slot.SetSlotBaseImage(uir1.SlotBase(height), 1.0, 1.0, 1.0, 1.0)
                    frame.undo.append(lambda slot=slot: slot.SetSlotBaseImage(
                        "d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0))
            for attr, primary in (("action", True), ("cancelButton", False)):
                native = getattr(self, attr)
                button = uir1dialog.DialogButton(self, kit, native, primary, False)
                button.SetWidth(136)
                self.children.append(button)
                native.Hide()
                setattr(self, attr, button)
                def restore(attr=attr, native=native, button=button):
                    button.Hide()
                    setattr(self, attr, native)
                    native.Show()
                frame.undo.append(restore)
            nativeField = self.nameField
            def restoreField():
                self.nameField.Hide()
                self.nameInput.SetParent(nativeField)
                self.nameInput.SetPosition(10, 7)
                self.nameInput.SetSize(350, 18)
                self.nameInput.SetDefaultFontName()
                self.nameField = nativeField
                nativeField.Hide()
            frame.undo.append(restoreField)
            field = uir1.Field(self, kit, 24, 91, 372, edit=self.nameInput,
                              hint=_Text("SERVICE_ITEM_FAMILY_NEW"), max_len=16)
            nativeField.Hide()
            self.nameField = field
            self.children.append(field)
            field.Hide()
            nativeBoxes = self.skillBoxes[:]
            self.skillBoxes = []
            def restoreBoxes():
                for box in self.skillBoxes:
                    box.Hide()
                self.skillBoxes = nativeBoxes
            frame.undo.append(restoreBoxes)
            for index, y in enumerate((100, 155)):
                box = SkillChoice(self, kit, y, lambda value, index=index: self.SelectSkill(index, value))
                self.skillBoxes.append(box)
                self.children.append(box)
                nativeBoxes[index].Hide()
        except Exception:
            frame.Fail()

    def Text(self, x, y, text):
        line = ui.TextLine()
        line.SetParent(self)
        line.SetPosition(x, y)
        line.SetText(text)
        line.Show()
        self.children.append(line)
        return line

    def Open(self, kind, scrollCell, active="0", sub="0"):
        global _pendingApply
        pending, _pendingApply = _pendingApply, None
        self.Close()
        self.kind = int(kind)
        self.scrollCell = int(scrollCell)
        self.scrollVnum = player.GetItemIndex(self.scrollCell)
        if not self.scrollVnum:
            return
        if self.kind in SINGLE_TARGET_KINDS:
            if (not pending or pending[:2] != (self.kind, self.scrollCell) or
                    pending[3] != ItemImage(self.scrollCell) or
                    pending[4] != ItemImage(pending[2]) or
                    not CanApplyCertificate(self.scrollCell, pending[2])):
                chat.AppendChat(chat.CHAT_TYPE_INFO, _Text("SERVICE_ITEM_CERT_DRAG"))
                return
            self.cells = [pending[2], None]
            self.confirmPreimages = (pending[3], pending[4])
            self.OpenCertificateConfirmation()
            return
        item.SelectItem(self.scrollVnum)
        self.SetTitleName(item.GetItemName())
        self.cells = [None, None]
        self.SetSize(420, 280)
        self.nameWarning.SetText(_Text("SERVICE_ITEM_FAMILY_HINT"))
        self.nameWarning.SetPackedFontColor(uir1.SignedColor(0xffcccccc))
        self.heading.SetText("")
        self.notice.SetPosition(24, 205)
        self.action.SetPosition((420 - self.action.GetWidth()) // 2, 240)
        self.action.SetText("Potvrdit")
        for control in (self.nameLabel, self.nameField, self.nameHelp, self.nameWarning):
            control.Hide()
        self.nameInput.SetText("")
        self.nameInput.Hide()
        self.sourceLabel.SetHorizontalAlignLeft()
        self.targetLabel.SetHorizontalAlignLeft()
        self.sourceLabel.SetPosition(45, 65)
        self.targetLabel.SetPosition(265, 65)
        for slots in self.slotSets.values():
            for slot in slots:
                slot.Hide()
        for backs in self.slotBacks.values():
            for back in backs:
                back.Hide()
        self.slots = self.slotSets[96 if self.kind == 1 else 32]
        self.slotHint.Hide()
        self.sourceLabel.Hide()
        self.targetLabel.Hide()
        for box in self.skillBoxes:
            box.Hide()
        if self.kind == 7:
            for index, text in enumerate((active, sub)):
                box = self.skillBoxes[index]
                box.ClearItem()
                values = [int(value) for value in text.split(",") if value.isdigit()]
                self.skillNames[index] = {}
                for value in values:
                    name = skill.GetSkillName(value) if value else _Text("SERVICE_ITEM_SKILL_UNSPENT")
                    self.skillNames[index][value] = name
                    box.InsertItem(value, name)
                self.skillChoices[index] = values[0] if len(values) == 1 else None
                box.SetCurrentItem(self.skillNames[index][values[0]] if len(values) == 1 else _Text("SERVICE_ITEM_SKILL_CHOOSE"))
                box.Show()
            self.sourceLabel.SetText(_Text("SERVICE_ITEM_SKILL_ACTIVE"))
            self.sourceLabel.SetPosition(40, 78)
            self.sourceLabel.Show()
            self.targetLabel.SetText(_Text("SERVICE_ITEM_SKILL_SUB"))
            self.targetLabel.SetPosition(40, 133)
            self.targetLabel.Show()
        elif self.kind == 3:
            self.SetSize(420, 238)
            self.heading.SetText(_Text("SERVICE_ITEM_FAMILY_DESC"))
            for control in (self.nameLabel, self.nameField, self.nameHelp, self.nameWarning):
                control.Show()
            self.notice.SetPosition(24, 174)
            self.action.SetPosition((420 - self.action.GetWidth()) // 2, 204)
            self.action.SetText(_Text("SERVICE_ITEM_FAMILY_BUTTON"))
            self.nameInput.Show()
            self.nameInput.SetFocus()
        elif self.kind in (1, 2, 4, 5):
            height = 96 if self.kind == 1 else 32
            count = 2 if self.kind in (1, 2) else 1
            for index in range(count):
                self.slotBacks[height][index].Show()
                self.slots[index].Show()
            self.sourceLabel.SetPosition(116, 72)
            self.sourceLabel.SetHorizontalAlignCenter()
            self.targetLabel.SetPosition(304, 72)
            self.targetLabel.SetHorizontalAlignCenter()
            if self.kind == 1:
                self.SetSize(420, 306)
                self.slotHint.SetPosition(24, 208)
                self.notice.SetPosition(24, 232)
                self.action.SetPosition(0, 268)
            else:
                self.SetSize(420, 242)
                self.slotHint.SetPosition(24, 144)
                self.notice.SetPosition(24, 168)
                self.action.SetPosition(0, 204)
            if count == 1:
                self.slots[0].SetPosition(194, 95)
                self.slotBacks[height][0].SetPosition(194, 95)
                self.sourceLabel.SetPosition(210, 72)
            else:
                self.slots[0].SetPosition(100, 95)
                self.slotBacks[height][0].SetPosition(100, 95)
            self.slotHint.Show()
            self.sourceLabel.Show()
            if self.kind in (1, 2):
                self.targetLabel.Show()
                self.targetLabel.SetText(_Text("SERVICE_ITEM_TARGET_MOUNT") if self.kind == 2 else _Text("SERVICE_ITEM_TARGET_NO_BONUS"))
            self.sourceLabel.SetText(_Text("SERVICE_ITEM_SASH") if self.kind in (4, 5) else _Text("SERVICE_ITEM_SOURCE_MOUNT") if self.kind == 2 else _Text("SERVICE_ITEM_SOURCE_BONUS"))
        else:
            self.notice.SetText(_Text("SERVICE_ITEM_NOT_READY"))
            self.action.Hide()
            self.SetCenterPosition()
            self.Show()
            return
        self.notice.SetText(_Text("SERVICE_ITEM_LOGOUT_AFTER") if self.kind == 3 else
                            _Text("SERVICE_ITEM_LEVEL_EFFECT") if self.kind == 7 else
                            _Text("SERVICE_ITEM_SASH_CLEAR_WARN") if self.kind == 4 else
                            _Text("SERVICE_ITEM_COSTUME_CONSUMED") if self.kind == 1 else
                            _Text("SERVICE_ITEM_SEAL_CONSUMED") if self.kind == 2 else
                            _Text("SERVICE_ITEM_RELOG_AFTER"))
        self.action.Show()
        self.cancelButton.Show()
        y = self.action.GetLocalPosition()[1]
        gap = 10
        total = self.action.GetWidth() + gap + self.cancelButton.GetWidth()
        x = (self.GetWidth() - total) // 2
        self.action.SetPosition(x, y)
        self.cancelButton.SetPosition(x + self.action.GetWidth() + gap, y)
        self.RefreshSlots()
        self.SetCenterPosition()
        self.Show()
        self.SetTop()

    def OpenCertificateConfirmation(self):
        item.SelectItem(player.GetItemIndex(self.cells[0]))
        name = item.GetItemName()
        dialog = uiCommon.QuestionDialog2()
        dialog.SetWidth(440)
        dialog.SetText1((_Text("SERVICE_ITEM_CLEAR_QUESTION") if self.kind == 4 else _Text("SERVICE_ITEM_RETURN_QUESTION")) % name)
        dialog.SetText2(_Text("SERVICE_ITEM_CLEAR_NO_RETURN") if self.kind == 4 else
                        _Text("SERVICE_ITEM_RETURN_DESC"))
        dialog.SetAcceptText(_Text("SERVICE_ITEM_CLEAR_BUTTON") if self.kind == 4 else _Text("SERVICE_ITEM_RETURN_BUTTON"))
        dialog.SetCancelText(_Text("SERVICE_ITEM_CANCEL"))
        dialog.SetAcceptEvent(self.Accept)
        dialog.SetCancelEvent(self.Close)
        self.confirmDialog = dialog
        constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(1)
        dialog.Open()

    def SelectSkill(self, index, value):
        self.skillChoices[index] = value
        self.skillBoxes[index].SetCurrentItem(self.skillNames[index][value])

    def Select(self, index):
        if index not in (0, 1) or (index == 1 and self.kind not in (1, 2)):
            return
        controller = mouseModule.mouseController
        if not controller.isAttached() or controller.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
            return
        cell = controller.GetAttachedSlotNumber()
        if isinstance(cell, tuple):
            cell = cell[-1]
        cell = int(cell)
        controller.DeattachObject()
        if cell == self.scrollCell or cell in self.cells:
            return
        if not player.GetItemIndex(cell):
            return
        self.cells[index] = cell
        self.RefreshSlots()

    def Clear(self, index):
        if index in (0, 1):
            self.cells[index] = None
            self.RefreshSlots()

    def RefreshSlots(self):
        for index, cell in enumerate(self.cells):
            self.slots[index].ClearSlot(0)
            if cell is not None:
                vnum = player.GetItemIndex(cell)
                if vnum:
                    self.slots[index].SetItemSlot(0, vnum, 1)
            self.slots[index].RefreshSlot()

    def OverIn(self, index):
        if index in (0, 1) and self.cells[index] is not None:
            self.tooltip.SetInventoryItem(self.cells[index])

    def Accept(self):
        if self.confirmPreimages is not None and (
                self.confirmPreimages[0] != ItemImage(self.scrollCell) or
                self.confirmPreimages[1] != ItemImage(self.cells[0])):
            self.Refused()
            self.Close()
            return
        if self.scrollCell is None or player.GetItemIndex(self.scrollCell) != self.scrollVnum:
            self.Refused()
            return
        if self.kind in (1, 2) and any(cell is None for cell in self.cells):
            self.Refused()
            return
        if self.kind in (4, 5) and self.cells[0] is None:
            self.Refused()
            return
        name = self.nameInput.GetText().strip() if self.kind == 3 else "-"
        if self.kind == 3 and not (3 <= len(name) <= 16 and name.isascii() and
                name[0].isalpha() and all(c.isalnum() or c == "_" for c in name)):
            self.nameWarning.SetText(_Text("SERVICE_ITEM_NAME_RULE"))
            self.nameWarning.SetPackedFontColor(uir1.SignedColor(0xffff8888))
            self.nameInput.SetFocus()
            return
        if self.kind == 7:
            if any(value is None for value in self.skillChoices):
                self.Refused()
                return
            name = "%d,%d" % tuple(self.skillChoices)
        source, target = [65535 if cell is None else cell for cell in self.cells]
        net.SendChatPacket("/service_item %d %d %d %s" % (self.scrollCell, source, target, name))
        self.Close()

    def Refused(self):
        chat.AppendChat(chat.CHAT_TYPE_INFO, _Text("SERVICE_ITEM_REFUSED"))

    def Result(self, code, reason="0", retrySeconds="0"):
        messages = {
            0: _Text("SERVICE_ITEM_RESULT_RELAUNCH"),
            1: _Text("SERVICE_ITEM_RESULT_REFUSED_RELOG"),
            2: _Text("SERVICE_ITEM_RESULT_UNCERTAIN"),
            3: _Text("SERVICE_ITEM_RESULT_ONLINE"),
            4: _Text("SERVICE_ITEM_RESULT_REFUSED"),
        }
        if int(code) == 4:
            reasons = {
                2: _Text("SERVICE_ITEM_FAMILY_TAKEN"),
                3: _Text("SERVICE_ITEM_FAMILY_SAME"),
                4: _Text("SERVICE_ITEM_FAMILY_DISABLED"),
                5: _Text("SERVICE_ITEM_FAMILY_SETUP_FIRST"),
            }
            if int(reason) == 1:
                minutes = (max(0, int(retrySeconds)) + 59) // 60
                days, hours, minutes = minutes // 1440, (minutes // 60) % 24, minutes % 60
                messages[4] = _Text("SERVICE_ITEM_COOLDOWN") % (days, hours, minutes)
            else:
                messages[4] = reasons.get(int(reason), messages[4])
        chat.AppendChat(chat.CHAT_TYPE_INFO, messages.get(int(code), messages[2]))
        self.Close()

    def Close(self):
        global _pendingApply
        _pendingApply = None
        if self.confirmDialog is not None:
            self.confirmDialog.Close()
            self.confirmDialog = None
            constInfo.SET_ITEM_QUESTION_DIALOG_STATUS(0)
        self.confirmPreimages = None
        self.scrollCell = None
        self.scrollVnum = 0
        if self.tooltip is not None:
            self.tooltip.HideToolTip()
        for box in self.skillBoxes:
            box.CloseListBox()
        if self.nameInput is not None:
            self.nameInput.KillFocus()
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Close()
        frame = getattr(self, "r1frame", None)
        if frame is not None:
            frame.Undo()
            self.r1frame = None
        self.ElementDictionary = {}
        self.tooltip = None
        self.children = []
        self.nameInput = None
        self.nameField = None
        self.slots = None
        self.slotSets = {}
        self.slotBacks = {}
        self.skillBoxes = []
        self.action = None
        self.cancelButton = None
