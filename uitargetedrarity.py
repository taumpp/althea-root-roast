# -*- coding: utf-8 -*-
"""One explicitly selected rarity slot; native/server authority owns the roll."""
import chat
import item
import localeInfo
import net
import player
import ui
import uiToolTip
import uiRarity

VNUM = 79632
MODE = 2
EMPTY_EXTRA = (0, 0)


def Text(key, fallback):
    return getattr(localeInfo, key, fallback)


def UnsentRequestText():
    # A refused send while the system is available means another rarity
    # request is still pending, not that rarity is disabled.
    if not getattr(net, "IsRarityV2Available", lambda: False)():
        return localeInfo.RARITY_RESULT_DISABLED
    return localeInfo.RARITY_REQUEST_FAILED


class TargetedRarityDialog(ui.BoardWithTitleBar):
    pendingSince = 0.0

    def __init__(self):
        ui.BoardWithTitleBar.__init__(self)
        self.SetSize(390, 285)
        self.AddFlag("float")
        self.SetTitleName(Text("RARITY_TARGETED_TITLE", u"C\u00edlen\u00e1 prom\u011bna rarity"))
        self.SetCloseEvent(ui.__mem_func__(self.Close))
        self.targetSlot = -1
        self.selectedSlot = 2
        self.previewRequestId = 0
        self.pendingPreview = False
        self.pendingCommit = False
        self.labels = []
        self.buttons = []
        self.children = []
        self.tip = uiToolTip.ItemToolTip()
        self.hint = self._Label(18, 39, Text("RARITY_TARGETED_HINT", u"Vyber bonus, kter\u00fd chce\u0161 p\u0159eto\u010dit."))
        self.itemName = self._Label(18, 62, "")
        for slot in range(3):
            button = ui.RadioButton()
            button.SetParent(self)
            button.SetPosition(18, 90 + 35 * slot)
            button.SetUpVisual("d:/ymir work/ui/public/small_button_01.sub")
            button.SetOverVisual("d:/ymir work/ui/public/small_button_02.sub")
            button.SetDownVisual("d:/ymir work/ui/public/small_button_03.sub")
            button.SetText(str(slot + 6))
            button.SetEvent(ui.__mem_func__(self.SelectSlot), slot)
            button.Show()
            self.buttons.append(button)
            self.labels.append(self._Label(67, 93 + 35 * slot, ""))
        self.cost = self._Label(18, 199, Text("RARITY_TARGETED_COST", u"Cena: 1\u00d7 C\u00edlen\u00e1 prom\u011bna rarity"))
        self.status = self._Label(18, 218, "")
        self.accept = ui.Button()
        self.accept.SetParent(self)
        self.accept.SetPosition(134, 247)
        self.accept.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
        self.accept.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
        self.accept.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
        self.accept.SetText(Text("RARITY_TARGETED_ACTION", u"P\u0159eto\u010dit"))
        self.accept.SetEvent(ui.__mem_func__(self.Confirm))
        self.accept.Show()
        self.Hide()

    def _Label(self, x, y, text):
        label = ui.TextLine()
        label.SetParent(self)
        label.SetPosition(x, y)
        label.SetText(text)
        label.Show()
        self.children.append(label)
        return label

    def _Grade(self):
        return int(net.GetRarityGrade(1, player.INVENTORY, self.targetSlot, 0, 0))

    def _Attributes(self):
        first = [player.GetItemAttribute(player.INVENTORY, self.targetSlot, slot) for slot in (5, 6)]
        try:
            extra = net.GetRarityExtra(1, player.INVENTORY, self.targetSlot, 0, 0)
        except (TypeError, ValueError, RuntimeError, SystemError):
            extra = EMPTY_EXTRA
        first.append(extra or EMPTY_EXTRA)
        return first

    def IsBusy(self):
        self.ExpireStalePending()
        return bool(self.pendingPreview or self.pendingCommit)

    def ExpireStalePending(self):
        if not (self.pendingPreview or self.pendingCommit):
            return False
        if uiRarity.Now() - self.pendingSince < uiRarity.RESPONSE_TIMEOUT_SECONDS:
            return False
        self.pendingPreview = False
        self.pendingCommit = False
        self.previewRequestId = 0
        if self.IsShow():
            self.status.SetText(uiRarity.TimeoutText())
            self.Refresh()
        else:
            chat.AppendChat(chat.CHAT_TYPE_INFO, uiRarity.TimeoutText())
        return True

    def OnUpdate(self):
        self.ExpireStalePending()

    def Open(self, targetSlot):
        if self.IsBusy():
            return False
        if not getattr(net, "IsRarityV2Available", lambda: False)():
            chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_RESULT_DISABLED)
            return False
        if targetSlot < 0 or player.IsEquipmentSlot(targetSlot):
            chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_UNEQUIP_FIRST)
            return False
        vnum = player.GetItemIndex(player.INVENTORY, targetSlot)
        if not vnum:
            return False
        self.targetSlot = int(targetSlot)
        grade = self._Grade()
        if grade < 1 or grade > 6:
            chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.RARITY_RESULT_INVALID_TARGET)
            return False
        item.SelectItem(vnum)
        self.itemName.SetText(item.GetItemName())
        self.selectedSlot = min(grade, 3) - 1
        self.previewRequestId = 0
        self.status.SetText("")
        self.SetCenterPosition()
        self.SetTop()
        self.Show()
        self.Refresh()
        return self.RequestPreview()

    def Refresh(self):
        if self.targetSlot < 0:
            return
        count = min(self._Grade(), 3)
        for slot, attribute in enumerate(self._Attributes()):
            button = self.buttons[slot]
            button.SetUp()
            if slot == self.selectedSlot:
                button.Down()
            if slot < count and not self.pendingPreview and not self.pendingCommit:
                button.Enable()
            else:
                button.Disable()
            if slot >= count:
                description = Text("RARITY_TARGETED_LOCKED", u"Odemkne vy\u0161\u0161\u00ed rarita")
            elif int(attribute[0]):
                formatter = uiToolTip.ItemToolTip.AFFECT_DICT.get(int(attribute[0]))
                description = formatter(int(attribute[1])) if callable(formatter) else str(attribute[1])
            else:
                description = Text("RARITY_TARGETED_EMPTY", u"Pr\u00e1zdn\u00fd bonus")
            self.labels[slot].SetText(description)
            self.labels[slot].SetFontColor(*((245 / 255.0, 217 / 255.0, 139 / 255.0) if slot == self.selectedSlot else (0.6, 0.6, 0.6)))
        self.accept.Disable()
        if self.previewRequestId and not self.pendingPreview and not self.pendingCommit:
            self.accept.Enable()

    def SelectSlot(self, slot):
        if self.pendingPreview or self.pendingCommit or slot >= min(self._Grade(), 3):
            return
        self.selectedSlot = slot
        self.previewRequestId = 0
        self.RequestPreview()

    def RequestPreview(self):
        if self.pendingPreview or self.pendingCommit:
            return False
        self.previewRequestId = 0
        self.pendingPreview = bool(net.RequestRarityRerollPreview(player.INVENTORY, self.targetSlot, self.selectedSlot))
        self.pendingSince = uiRarity.Now()
        self.status.SetText(localeInfo.RARITY_WAITING if self.pendingPreview else UnsentRequestText())
        self.Refresh()
        return self.pendingPreview

    def OnPreviewResult(self, requestId, mode, result, *unused):
        if int(mode) != MODE or not self.pendingPreview:
            return
        self.pendingPreview = False
        if not self.IsShow():
            return
        if int(result) == getattr(net, "RARITY_RESULT_OK", 0):
            self.previewRequestId = int(requestId)
            self.status.SetText(Text("RARITY_TARGETED_PRESERVED", u"Ostatn\u00ed bonusy z\u016fstanou zachovan\u00e9."))
        else:
            self.previewRequestId = 0
            self.status.SetText(uiRarity.ResultText(result))
        self.Refresh()

    def Confirm(self):
        if not self.previewRequestId or self.pendingPreview or self.pendingCommit:
            return
        self.pendingCommit = bool(net.ConfirmRarityReroll(player.INVENTORY, self.targetSlot, self.previewRequestId, self.selectedSlot))
        self.pendingSince = uiRarity.Now()
        self.status.SetText(localeInfo.RARITY_WAITING if self.pendingCommit else UnsentRequestText())
        self.Refresh()

    def OnCommitResult(self, requestId, mode, result, succeeded, grade):
        if int(mode) != MODE or not self.pendingCommit:
            return
        self.pendingCommit = False
        self.previewRequestId = 0
        if not self.IsShow():
            return
        self.status.SetText(Text("RARITY_TARGETED_SUCCESS", u"Bonus byl zm\u011bn\u011bn.") if int(result) == 0 else uiRarity.ResultText(result))
        self.Refresh()
        if int(result) == getattr(net, "RARITY_RESULT_OK", 0):
            self.RequestPreview()

    def Close(self):
        self.previewRequestId = 0
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Close()
        self.tip.HideToolTip()
        self.tip = None
        self.buttons = []
        self.labels = []
        self.children = []
