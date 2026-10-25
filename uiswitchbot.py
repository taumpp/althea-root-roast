import dbg
import constInfo
import app
import ime
import item
import grp
import net
import ui
from uiToolTip import ItemToolTip, GET_AFFECT_STRING
import player
import mouseModule
import localeInfo
import uiScriptLocale
import wndMgr
import presetstorage
import switchbot
import chat
import mountcorebonus
from marketfilters import folded
import switchbotelements
import switchbottransfer
import bonuscatalog
import switchbotrefusals
from switchbotoptions import options as selectedOptions, instantOptions, RecommendedScroll, SameKind, HeldScroll, memory as attributeMemory
import uiswitchbotcontrols as controls
import uir1
import uiwheel
from uicrimsonember import SettingsScrollBar

COLOR_INACTIVE = grp.GenerateColor(1.0, 0.0, 0.0, 0.2)
COLOR_ACTIVE   = grp.GenerateColor(1.0, 0.6, 0.1, 0.2)
COLOR_FINISHED = grp.GenerateColor(0.0, 1.0, 0.0, 0.2)
COLOR_SELECTED = grp.GenerateColor(1.0, 1.0, 1.0, 1.0)

BOARD_WIDTH = 400
INPUT_HEIGHT = 27

BORDER_SPACE = 8
BORDER_SPACE_TOP = 30

ITEM_TAB_NAME_BOX_HEIGHT = 20
ITEM_TAB_SPACE = 2
ITEM_TAB_WIDTH = (BOARD_WIDTH - BORDER_SPACE * 2) // switchbot.SLOT_COUNT + 1 - ITEM_TAB_SPACE
	
TOP_PANEL_HEIGHT = (BORDER_SPACE * 2) + (3 * 32) + ITEM_TAB_NAME_BOX_HEIGHT
TOP_PANEL_WIDTH = BOARD_WIDTH - (BORDER_SPACE * 2)

MAIN_PANEL_WIDTH = BOARD_WIDTH - BORDER_SPACE * 2
MAIN_PANEL_HEIGHT = INPUT_HEIGHT * 6 #1 AlternativeRow 5 Attribute

BOT_PANEL_HEIGHT = 40
BOT_PANEL_WIDTH = BOARD_WIDTH - BORDER_SPACE * 2

ATTR_SLOT_COUNT = 5
INSTANT_SIDE_GAP = 10	# the Instaswitchbot opens beside the switchbot (R1 preview 9. 10. 2026)

BOARD_HEIGHT = BORDER_SPACE_TOP + TOP_PANEL_HEIGHT + MAIN_PANEL_HEIGHT + BOT_PANEL_HEIGHT + BORDER_SPACE + 58

def ShowSlotLockedMessage():
	# Unknown catalog data is loading, not confirmation of a VIP lock.
	if bonuscatalog.IsReady():
		chat.AppendChat(chat.CHAT_TYPE_INFO, uiScriptLocale.SWITCHBOT_VIP_SLOT_LOCKED)
	else:
		code = {'waiting': 'CATALOG_WAITING', 'error': 'CATALOG_ERROR'}.get(
			bonuscatalog.receiver.state, 'CATALOG_LOADING')
		chat.AppendChat(chat.CHAT_TYPE_INFO, switchbotrefusals.LocalMessage(code))
		bonuscatalog.receiver.Retry()

def ShowEmptyOptionsMessage(catalog):
	if catalog and catalog['item_id'] and not catalog['values'] and not catalog.get('emptyExplained'):
		chat.AppendChat(chat.CHAT_TYPE_INFO, switchbotrefusals.LocalMessage('OPTIONS_EMPTY'))
		catalog['emptyExplained'] = True

def FormatFee(fee):
	"""Instant fee from the server catalog, grouped by thousands ("-" if unknown)."""
	if not fee:
		return '-'
	return '{:,}'.format(int(fee)).replace(',', ' ')

def GetAffectString(affectType, affectValue):
	if not affectType:
		return None
	if mountcorebonus.IsScopedApply(affectType):
		return mountcorebonus.FormatAffect(affectType, affectValue, app.GetLocalePath().endswith("/cz"))
	return GET_AFFECT_STRING(affectType, affectValue)

def ElementLimitNote(allowance):
	text = getattr(localeInfo, "SWITCHBOT_ELEMENT_LIMIT", "max. %d elements")
	try:
		return text % allowance
	except (TypeError, ValueError):
		return text

def AttributeChoices(catalog, selectedTypes, otherSelectedTypes):
	# The entries of the bonus picker in its order: (kind, name, keywords, enabled, note).
	# One item may carry every element its slot offers (ALTHEA-591). An element
	# beyond that allowance stays visible but greyed out with the reason.
	catalogTypes = [kind for kind, value in catalog]
	allowance = switchbotelements.Allowance(catalogTypes)
	choices = []
	for (kind, value) in switchbotelements.Ordered(list(catalog)):
		if kind in selectedTypes:
			continue
		affectString = GetAffectString(kind, value)
		if not affectString:
			continue
		enabled = not switchbotelements.Blocked(kind, otherSelectedTypes, catalogTypes)
		choices.append((kind, affectString, switchbotelements.SearchKeywords(kind),
			enabled, "" if enabled else ElementLimitNote(allowance)))
	return choices

def AppendAttributeChoices(wnd, catalog, selectedTypes, otherSelectedTypes):
	for choice in AttributeChoices(catalog, selectedTypes, otherSelectedTypes):
		wnd.AppendItem(*choice)

def WheelChoices(catalog, selectedTypes, index):
	# The bonus types the wheel steps through in row ``index``: the picker's list of that
	# row in its order (the bonuses of the variant's other rows left out, an element over
	# the limit skipped: it cannot be picked), the row's own bonus at its place in it.
	current = selectedTypes[index]
	other = [kind for position, kind in enumerate(selectedTypes) if position != index]
	return [(kind, name) for (kind, name, keywords, enabled, note) in AttributeChoices(catalog, other, other)
		if enabled or (current and kind == current)]

def StepChoice(entries, current, delta):
	# One wheel notch through a list in its order: up (delta > 0) = the entry above, down =
	# the one below; None at the end of the list (clamped) or for no notch. Nothing chosen
	# yet stands above the first entry.
	if not delta or not entries:
		return None
	if current in entries:
		position = entries.index(current) + (-1 if delta > 0 else 1)
		return entries[position] if 0 <= position < len(entries) else None
	return None if delta > 0 else entries[0]

def StepValue(values, current, delta):
	# One wheel notch through the allowed values (the value picker's): up = the next higher
	# value, down = the next lower one (numeric order);
	# a typed value between two allowed ones steps to its neighbour; None at max / min (clamped).
	values = sorted(set(values))
	if not delta or not values:
		return None
	if delta > 0:
		higher = [value for value in values if value > current]
		return higher[0] if higher else None
	lower = [value for value in values if value < current]
	return lower[-1] if lower else None


def PresetAttributes(config, alternative):
	# A saved preset ("Uložené předvolby") is one variant's bonuses. Since 9. 10. 2026
	# Uložit stores the shown variant in the preset's first row (the other rows empty); an older
	# preset keeps every variant: its row of the same variant when that one is set, otherwise its
	# first set row (a preset saved from Varianta 1 loads into Varianta 2 as well).
	rows = config.get("alternatives") or []
	def configured(row):
		return any(pair[0] for pair in row)
	if 0 <= alternative < len(rows) and configured(rows[alternative]):
		return rows[alternative]
	for row in rows:
		if configured(row):
			return row
	return rows[0] if rows else []


class SwitchbotItemTab(ui.ThinBoardCircle):
	def __init__(self, slot_num):
		ui.ThinBoardCircle.__init__(self)
		
		self.slot_num = slot_num
		
		self.__Initialize()
		self.__LoadItemTab()
		self.__BindEvents()
		
	def __del__(self):
		ui.ThinBoardCircle.__del__(self)
		
	def __Initialize(self):	
		self.tooltipItem = None
		self.onSelectEvent = None
		self.locked = False
		self.hadItem = False
		
		self.statusBar = None
		self.itemSlot = None
		self.selectButton = None
		
		self.lastSelectAlpha = 255
		self.lastSelectAlphaDir = 1
		
	def __LoadItemTab(self):	
		self.SetSize(ITEM_TAB_WIDTH, TOP_PANEL_HEIGHT)
	
		self.statusBar = ui.Bar()
		self.statusBar.SetParent(self)
		self.statusBar.SetSize(ITEM_TAB_WIDTH - 4, TOP_PANEL_HEIGHT - 4)
		self.statusBar.SetPosition(2, 2)
		
		self.selectBox = ui.Box()
		self.selectBox.SetParent(self)
		self.selectBox.SetPosition(1, 1)
		self.selectBox.SetSize(ITEM_TAB_WIDTH - 2, TOP_PANEL_HEIGHT - 2)
		self.selectBox.SetColor(COLOR_SELECTED)
			
		self.selectButton = ui.RadioButton()
		self.selectButton.SetParent(self)
		self.selectButton.SetUpVisual("d:/ymir work/ui/switchbot/btn_small_01.sub")
		self.selectButton.SetOverVisual("d:/ymir work/ui/switchbot/btn_small_02.sub")
		self.selectButton.SetDownVisual("d:/ymir work/ui/switchbot/btn_small_03.sub")
		self.selectButton.SetDisableVisual("d:/ymir work/ui/switchbot/btn_small_01.sub")
		self.selectButton.SetWindowHorizontalAlignCenter()
		self.selectButton.SetPosition(0, 5)
		self.selectButton.SetText(str(self.slot_num+1))
		self.selectButton.Show()
	
		self.itemSlot = ui.GridSlotWindow()
		self.itemSlot.SetParent(self)
		self.itemSlot.ArrangeSlot(0, 1, 3, 32, 32, 0, 0)
		self.itemSlot.SetSlotBaseImage("d:/ymir work/ui/public/slot_base.sub", 1.0, 1.0, 1.0, 1.0)
		self.itemSlot.SetWindowHorizontalAlignCenter()
		self.itemSlot.SetPosition(0, 30)
		self.itemSlot.Show()
	
	def __BindEvents(self):			
		self.itemSlot.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		self.itemSlot.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		self.itemSlot.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		self.itemSlot.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		self.itemSlot.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		self.itemSlot.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))	
		
		self.selectButton.SetEvent(ui.__mem_func__(self.__OnSelectButtonClick))
		
	def Destroy(self):
		self.__Initialize()
		
	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetLocked(self, locked):
		self.locked = bool(locked)
		if self.locked:
			self.selectButton.Disable()
			self.SetUp()
		else:
			self.selectButton.Enable()
		
	def OnPlacedItem(self, slot_num):
		pass
		
	def OverOutItem(self):
		self.itemSlot.SetUsableItem(False)
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()			
			
	def OverInItem(self, overSlotPos):
		self.itemSlot.SetUsableItem(True)

		if self.IsEmpty():
			return

		self.tooltipItem.ClearToolTip()
		self.tooltipItem.SetInventoryItem(self.slot_num, player.SWITCHBOT)
		self.tooltipItem.ShowToolTip()
		
	def SelectEmptySlot(self, selectedSlotPos):
		if self.locked:
			ShowSlotLockedMessage()
			return

		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if mouseModule.mouseController.isAttached():

			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedItemCount = mouseModule.mouseController.GetAttachedItemCount()
			attachedItemIndex = mouseModule.mouseController.GetAttachedItemIndex()

			if player.SLOT_TYPE_INVENTORY == attachedSlotType or player.SLOT_TYPE_SWITCH_INVENTORY == attachedSlotType:
				attachedCount = mouseModule.mouseController.GetAttachedItemCount()
				net.SendItemMovePacket(player.INVENTORY, attachedSlotPos, player.SWITCHBOT, self.slot_num, int(attachedItemCount))
			elif player.SLOT_TYPE_SWITCHBOT == attachedSlotType:
				attachedCount = mouseModule.mouseController.GetAttachedItemCount()
				net.SendItemMovePacket(player.SWITCHBOT, attachedSlotPos, player.SWITCHBOT, self.slot_num, int(attachedItemCount))
				
			mouseModule.mouseController.DeattachObject()

			self.OnPlacedItem(self.slot_num)
		
	def SelectItemSlot(self, itemSlotIndex):
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		if self.locked:
			if mouseModule.mouseController.isAttached():
				ShowSlotLockedMessage()
				return

			if switchbot.IsActive(self.slot_num):
				return

			itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
			itemCount = player.GetItemCount(player.SWITCHBOT, self.slot_num)
			if itemVnum:
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_SWITCHBOT, self.slot_num, itemVnum, itemCount)
			return
			
		if switchbot.IsActive(self.slot_num):
			return
		
		if mouseModule.mouseController.isAttached():
			mouseModule.mouseController.DeattachObject()
		else:

			if app.IsPressed(app.DIK_LALT):
				if app.ENABLE_REFINE_ELEMENT_SYSTEM:
					link = constInfo.GetItemLinkEx(self.slot_num, player.SWITCHBOT)
				else:
					link = player.GetItemLink(player.SWITCHBOT, self.slot_num)
				ime.PasteString(link)
			else:
				itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
				itemCount = player.GetItemCount(player.SWITCHBOT, self.slot_num)
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_SWITCHBOT, self.slot_num, itemVnum, itemCount)
				
	def UseItemSlot(self, slotIndex):
		curCursorNum = app.GetCursor()
		if app.SELL == curCursorNum:
			return

		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return

		net.SendItemUsePacket(player.SWITCHBOT, self.slot_num)
		mouseModule.mouseController.DeattachObject()
		self.OverOutItem()
			
	def RefreshItemSlot(self):	
		if self.IsEmpty():
			switchbot.ClearSlot(self.slot_num)
			if self.hadItem:
				# The item left the slot: its bonuses go with it. An empty slot of a window just built, while the
				# items of a warp are still on their way, keeps what the player set.
				self.hadItem = False
				attributeMemory.Forget(self.slot_num)
			self.itemSlot.ClearSlot(0)
			self.statusBar.Hide()
		else:			
			self.hadItem = True
			itemCount = player.GetItemCount(player.SWITCHBOT, self.slot_num)
			itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)
			if itemCount == 1:
				itemCount = 0
			
			self.itemSlot.SetItemSlot(0, itemVnum, itemCount)
		
			self.statusBar.Show()
			if self.IsActive():
				self.itemSlot.ActivateSlot(0)
				self.statusBar.SetColor(COLOR_ACTIVE)
			else:
				self.itemSlot.DeactivateSlot(0)
				
				if self.IsFinished():
					self.statusBar.SetColor(COLOR_FINISHED)
				else:
					self.statusBar.SetColor(COLOR_INACTIVE)
		
		self.itemSlot.RefreshSlot()
		
	def IsEmpty(self):
		itemVnum = player.GetItemIndex(player.SWITCHBOT, self.slot_num)	
		return not itemVnum
		
	def IsActive(self):
		return switchbot.IsActive(self.slot_num)
		
	def IsFinished(self):
		return switchbot.IsFinished(self.slot_num)
		
	def GetSlotNum(self):
		return self.slot_num
		
	def SetOnSelectEvent(self, event):
		self.onSelectEvent = event
		
	def __OnSelectButtonClick(self):
		if self.locked:
			ShowSlotLockedMessage()
			return

		if self.onSelectEvent:
			self.onSelectEvent(self.slot_num)
			
	def SetUp(self):
		if self.selectButton:
			self.selectButton.SetUp()
			self.selectBox.Hide()
			
	def Down(self):
		if self.selectButton:
			self.selectButton.Down()
			
			self.lastSelectAlpha = 255
			self.selectBox.Show()
			
	def OnUpdate(self):
		if self.selectBox.IsShow():
			rate = 3
			
			self.lastSelectAlpha -= (rate * self.lastSelectAlphaDir)
		
			if self.lastSelectAlpha <= 0:
				self.lastSelectAlpha = 0
				self.lastSelectAlphaDir = -1
			elif self.lastSelectAlpha >= 255:
				self.lastSelectAlpha = 255
				self.lastSelectAlphaDir = 1
				
			self.selectBox.SetColor(grp.GenerateColor(1.0, 1.0, 1.0, float(self.lastSelectAlpha) / 255.0))
			
class ClassicAttributeProvider:
	GetAttribute = staticmethod(switchbot.GetAttribute)
	SetAttribute = staticmethod(attributeMemory.SetAttribute)
	IsActive = staticmethod(switchbot.IsActive)
	Values = staticmethod(selectedOptions.Values)
	Maximum = staticmethod(selectedOptions.Maximum)

classicAttributeProvider = ClassicAttributeProvider()

class SwitchbotAttribute(ui.Window):
	VALUE_WIDTH = 50
	
	typeInput = None
	typeTextLine = None
	searchTypeButton = None
	deleteAttributeButton = None
	valueInput = None
	valueEditLine = None	
	
	def __init__(self):
		ui.Window.__init__(self)	
		self.__Initialize()
		self.provider = classicAttributeProvider
		
	def __del__(self):
		ui.Window.__del__(self)
		
	def __Initialize(self):
		self.selectedSlot = -1
		self.alternative = 0
		self.index = -1
		
		self.attributeType = 0
		self.attributeValue = 0
		
		self.searchEvent = None
		self.wheelChoicesEvent = None
		self.wheelChooseEvent = None
		self.attributeMaxValue = 0	
		self.valueMenuValues = ()
	
		self.typeInput = None
		self.typeTextLine = None
		self.searchTypeButton = None
		self.deleteAttributeButton = None
		self.valueInput = None
		self.valueEditLine = None
		
	def SetProvider(self, provider):
		self.provider = provider

	def Create(self, width, index):
		self.index = index
		self.SetSize(width, INPUT_HEIGHT)
		
		self.typeInput = ui.ThinBoardCircle()
		self.typeInput.SetParent(self)
		self.typeInput.SetSize(width - self.VALUE_WIDTH, INPUT_HEIGHT)
		self.typeInput.SetPosition(0, 0)
		self.typeInput.Show()
		
		self.typeTextLine = ui.TextLine()
		self.typeTextLine.SetParent(self.typeInput)
		self.typeTextLine.SetText(localeInfo.SWITCHBOT_EMPTY_ATTR)
		self.typeTextLine.SetVerticalAlignCenter()
		self.typeTextLine.SetWindowVerticalAlignCenter()
		self.typeTextLine.SetHorizontalAlignCenter()
		self.typeTextLine.SetWindowHorizontalAlignCenter()
		self.typeTextLine.SetPosition(-20, -1)
		self.typeTextLine.Show()
			
		self.searchTypeButton = ui.Button()
		self.searchTypeButton.SetParent(self.typeInput)
		self.searchTypeButton.SetUpVisual("d:/ymir work/ui/switchbot/search_attr_01.sub")
		self.searchTypeButton.SetOverVisual("d:/ymir work/ui/switchbot/search_attr_02.sub")
		self.searchTypeButton.SetDownVisual("d:/ymir work/ui/switchbot/search_attr_03.sub")
		self.searchTypeButton.SetDisableVisual("d:/ymir work/ui/switchbot/search_attr_03.sub")
		self.searchTypeButton.SetWindowHorizontalAlignRight()
		self.searchTypeButton.SetWindowVerticalAlignCenter()
		self.searchTypeButton.SetPosition(24 * 2 + 2, 1)
		self.searchTypeButton.SetEvent(ui.__mem_func__(self.__OnClickSearchButton))
		self.searchTypeButton.Show()
		
		self.deleteAttributeButton = ui.Button()
		self.deleteAttributeButton.SetParent(self.typeInput)
		self.deleteAttributeButton.SetUpVisual("d:/ymir work/ui/switchbot/delete_attr_01.sub")
		self.deleteAttributeButton.SetOverVisual("d:/ymir work/ui/switchbot/delete_attr_02.sub")
		self.deleteAttributeButton.SetDownVisual("d:/ymir work/ui/switchbot/delete_attr_03.sub")
		self.deleteAttributeButton.SetDisableVisual("d:/ymir work/ui/switchbot/delete_attr_03.sub")
		self.deleteAttributeButton.SetWindowHorizontalAlignRight()
		self.deleteAttributeButton.SetWindowVerticalAlignCenter()
		self.deleteAttributeButton.SetPosition(24 + 2, 1)
		self.deleteAttributeButton.SetToolTipText(localeInfo.SWITCHBOT_CLEAR_ATTR)
		self.deleteAttributeButton.SetEvent(ui.__mem_func__(self.__OnClickClearButton))
		self.deleteAttributeButton.Show()		
		
		self.valueInput = ui.ThinBoardCircle()
		self.valueInput.SetParent(self)
		self.valueInput.SetSize(self.VALUE_WIDTH, INPUT_HEIGHT)
		self.valueInput.SetPosition(width - self.VALUE_WIDTH, 0)
		self.valueInput.Show()
		
		self.valueEditLine = ui.EditLine()
		self.valueEditLine.SetParent(self.valueInput)
		self.valueEditLine.SetSize(self.VALUE_WIDTH - 23, 18)
		self.valueEditLine.SetMax(5)
		self.valueEditLine.SetNumberMode()
		self.valueEditLine.SetText("0")
		self.valueEditLine.SetPosition(5, 7)
		self.valueEditLine.Show()
		self.valueEditLine.OnIMEUpdate = self.__OnEditLineIMEUpdate
		self.valueEditLine.SetEscapeEvent(ui.__mem_func__(self.__OnEscapeEvent))
		self.valuePicker = controls.ValuePicker()
		self.valueArrow = controls.Arrow(self.valueInput, self.VALUE_WIDTH - 20, 4, self.OpenValues)
		# The wheel over a field changes it without its picker (both looks: the R1 skin keeps these boards).
		self.typeInput.OnMouseWheel = ui.__mem_func__(self.WheelType)
		self.valueInput.OnMouseWheel = ui.__mem_func__(self.WheelValue)

		
	def Destroy(self):
		self.__Initialize()
		
	def Hide(self):
		ui.Window.Hide(self)
		
		if self.valueEditLine:
			self.valueEditLine.KillFocus()
		if getattr(self, "valuePicker", None):
			self.valuePicker.Close()
			
	def RefreshAttributeRow(self, slot_num, alternative, index, keepValueMenu=False):
		# keepValueMenu: a refresh that is not about this row (the Instaswitchbot redraws on every roll of the
		# switchbot) leaves its open value menu open while the menu still lists the same choices.
		if not (keepValueMenu and self.__ValueMenuStillValid(slot_num, alternative, index)):
			self.valuePicker.Close()
		self.selectedSlot = slot_num
		self.alternative = alternative
		self.index = index	
	
		if self.provider.IsActive(slot_num):
			self.searchTypeButton.Disable()
			self.deleteAttributeButton.Disable()
			self.valueEditLine.Hide()
		else:
			self.searchTypeButton.Enable()
			self.deleteAttributeButton.Enable()	
			self.valueEditLine.Show()
			
		(type, value) = self.provider.GetAttribute(slot_num, alternative, index)
		if not type:
			self.SetAttribute(localeInfo.SWITCHBOT_EMPTY_ATTR, 0)
			return
			
		affectString = GetAffectString(type, value)
		if not affectString:
			return
			
		self.SetAttribute(affectString, value)

	def __ValueMenuStillValid(self, slot_num, alternative, index):
		# The open menu was built for this row's place, bonus and value list; it stays only if all of them are the same.
		if not self.valuePicker.IsShow():
			return False
		if (slot_num, alternative, index) != (self.selectedSlot, self.alternative, self.index):
			return False
		if self.provider.IsActive(slot_num):
			return False
		kind = self.provider.GetAttribute(slot_num, alternative, index)[0]
		return bool(kind) and tuple(sorted(set(self.provider.Values(slot_num, kind)))) == self.valueMenuValues

	def OpenValues(self):
		if self.provider.IsActive(self.selectedSlot):
			return
		kind = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)[0]
		values = self.provider.Values(self.selectedSlot, kind)
		if values:
			self.valueMenuValues = tuple(sorted(set(values)))
			self.valuePicker.Toggle(self.valueInput, values, self.ChooseValue)

	def ChooseValue(self, value):
		if self.provider.IsActive(self.selectedSlot):
			return
		kind = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)[0]
		self.provider.SetAttribute(self.selectedSlot, self.alternative, self.index, kind, value)
		self.SetAttribute(GetAffectString(kind, value), value)
		self.__OnAttributeUpdate()

	def SetWheelEvents(self, choices, choose):
		# choices(index) -> [(kind, name)] in the picker's order; choose(index, kind, name): what picking does.
		self.wheelChoicesEvent = choices
		self.wheelChooseEvent = choose

	def WheelType(self, delta):
		# A notch over the bonus field: the bonus above (up) / below (down) in the picker's list, as if picked
		# there. The field takes every notch; a running slot changes nothing (like its disabled picker).
		if self.index < 0 or self.provider.IsActive(self.selectedSlot) or not self.wheelChoicesEvent:
			return True
		choices = self.wheelChoicesEvent(self.index)
		kind = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)[0]
		target = StepChoice([choice[0] for choice in choices], kind, delta)
		if target is None or not self.wheelChooseEvent:
			return True
		self.valuePicker.Close()
		self.wheelChooseEvent(self.index, target, dict(choices)[target])
		return True

	def WheelValue(self, delta):
		# A notch over the value field: the next higher (up) / lower (down) allowed value, clamped at max / min.
		if self.index < 0 or self.provider.IsActive(self.selectedSlot):
			return True
		(kind, value) = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)
		if not kind:
			return True
		target = StepValue(self.provider.Values(self.selectedSlot, kind), value, delta)
		if target is not None:
			self.valuePicker.Close()
			self.ChooseValue(target)
		return True

	def __OnEditLineIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.valueEditLine)
		
		text = self.valueEditLine.GetText()
		if not text:
			curType = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)[0]
			self.provider.SetAttribute(self.selectedSlot, self.alternative, self.index, curType, 0)
			self.__OnAttributeUpdate()
			return
		if len(text) > 0 and text.isdigit():
			(curType, curValue) = self.provider.GetAttribute(self.selectedSlot, self.alternative, self.index)
			
			maxValue = self.provider.Maximum(self.selectedSlot, curType)
				
			value = int(text)
			
			if value == curValue:
				return
			
			if maxValue != 0 and value > maxValue:
				value = maxValue
				self.valueEditLine.SetText(str(value))
				
			self.provider.SetAttribute(self.selectedSlot, self.alternative, self.index, curType, value)
			self.typeTextLine.SetText(GetAffectString(curType, value))
			self.__OnAttributeUpdate()
		
	def SetSearchEvent(self, event):
		self.searchEvent= event
		
	def __OnClickSearchButton(self):
		if self.searchEvent:
			self.searchEvent(self.index)
		
	def SetAttributeUpdateEvent(self, event):
		self.attributeUpdateEvent = event		
		
	def __OnAttributeUpdate(self):
		if self.attributeUpdateEvent:
			self.attributeUpdateEvent(self.index)
			
	def SetEscapeEvent(self, event):
		self.escapeEvent = event			
			
	def __OnEscapeEvent(self):
		if self.escapeEvent:
			self.escapeEvent()
			
	def __OnClickClearButton(self):
		self.SetAttribute(localeInfo.SWITCHBOT_EMPTY_ATTR, 0)
		self.provider.SetAttribute(self.selectedSlot, self.alternative, self.index, 0, 0)
		self.__OnAttributeUpdate()		
			
	def SetAttribute(self, applyname, maxValue):
		self.typeTextLine.SetText(applyname)
		self.valueEditLine.SetText(str(maxValue))
		
	def GetIndex(self):
		return self.index
					
class SwitchbotWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)

		try:
			self.__Initialize()
			self.__LoadWindow()
			self.__BindEvents()
		except:
			import exception
			exception.Abort("SwitchbotWindow.__init__")
	
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Initialize(self):		
		self.selectedSlot = 0
		self.alternative = 0
		
		self.alternativeButtons = {}
		self.itemTabs = {}
		self.attrDict = {}
		
		self.attributeSearchWindow = None
		self.attrSearchIdx = -1
		
		self.configurationSaveWindow = None
		
		self.topPanel = None
		self.mainPanel = None
		self.botPanel = None
		
		self.startButton = None
		self.stopButton = None
		self.scrollPicker = None
		self.instantWindow = None
		self.rerollDialog = None
		self.rerollSlot = -1
		self.rerollRequest = None
		self.lastItemVnums = {}
		self.pendingPlacedItems = set()
		self.r1 = None
		self.r1Failed = getattr(self, "r1Failed", False)

	def __LoadWindow(self):
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(localeInfo.SWITCHBOT_TITLE)
		
		self.topPanel = ui.ThinBoardCircle()
		self.topPanel.SetParent(self)
		self.topPanel.SetSize(TOP_PANEL_WIDTH, TOP_PANEL_HEIGHT)
		self.topPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.topPanel.Show()
		
		for i in range(switchbot.SLOT_COUNT):	
			itemTab = SwitchbotItemTab(i)
			itemTab.SetParent(self.topPanel)
			itemTab.SetPosition((ITEM_TAB_WIDTH + ITEM_TAB_SPACE) * i, 0)
			itemTab.SetOnSelectEvent(ui.__mem_func__(self.SelectSlot))
			itemTab.OnPlacedItem = self.__OnPlacedItem
			itemTab.Show()
			
			self.itemTabs[i] = itemTab
		
		self.mainPanel = ui.ThinBoardCircle()
		self.mainPanel.SetParent(self)
		self.mainPanel.SetSize(MAIN_PANEL_WIDTH, MAIN_PANEL_HEIGHT)
		self.mainPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + TOP_PANEL_HEIGHT)
		self.mainPanel.Show()
		
		self.alternativePanel = ui.ThinBoardCircle()
		self.alternativePanel.SetParent(self.mainPanel)
		self.alternativePanel.SetSize(MAIN_PANEL_WIDTH, INPUT_HEIGHT)
		self.alternativePanel.SetPosition(0, 0)
		self.alternativePanel.Show()
		
		self.alternativeTextLine = ui.TextLine()
		self.alternativeTextLine.SetParent(self.alternativePanel)
		self.alternativeTextLine.SetPosition(5, -1)
		self.alternativeTextLine.SetVerticalAlignCenter()
		self.alternativeTextLine.SetWindowVerticalAlignCenter()
		self.alternativeTextLine.SetText(localeInfo.SWITCHBOT_ALTERNATIVE)
		self.alternativeTextLine.Show()
		
		for i in range(switchbot.ALTERNATIVE_COUNT):
			alternativeButton = ui.RadioButton()
			alternativeButton.SetParent(self.alternativePanel)
			alternativeButton.SetUpVisual("d:/ymir work/ui/switchbot/btn_small_01.sub")
			alternativeButton.SetOverVisual("d:/ymir work/ui/switchbot/btn_small_02.sub")
			alternativeButton.SetDownVisual("d:/ymir work/ui/switchbot/btn_small_03.sub")
			alternativeButton.SetDisableVisual("d:/ymir work/ui/switchbot/btn_small_03.sub")
			alternativeButton.SetWindowVerticalAlignCenter()
			alternativeButton.SetPosition(80 + alternativeButton.GetWidth() * i, 0)
			alternativeButton.SetText(str(i+1))
			alternativeButton.SetEvent(lambda arg = i : self.SelectAlternative(arg))
			alternativeButton.Show()
			
			self.alternativeButtons[i] = alternativeButton
		
		for i in range(ATTR_SLOT_COUNT):
			attr = SwitchbotAttribute()
			attr.SetParent(self.mainPanel)
			attr.Create(MAIN_PANEL_WIDTH, i)
			attr.SetPosition(0, INPUT_HEIGHT + (INPUT_HEIGHT * i))
			attr.SetSearchEvent(ui.__mem_func__(self.__OnSearchAttribute))
			attr.SetWheelEvents(ui.__mem_func__(self.__AttributeWheelChoices), ui.__mem_func__(self.__ChooseAttribute))
			attr.SetAttributeUpdateEvent(ui.__mem_func__(self.__OnAttributeUpdate))
			attr.SetEscapeEvent(ui.__mem_func__(self.Close))
			attr.Show()
			
			self.attrDict[i] = attr
			
		self.botPanel = ui.ThinBoardCircle()
		self.botPanel.SetParent(self)
		self.botPanel.SetSize(BOT_PANEL_WIDTH, BOT_PANEL_HEIGHT)
		self.botPanel.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + TOP_PANEL_HEIGHT + MAIN_PANEL_HEIGHT)
		self.botPanel.Show()			
		
		self.saveButton = ui.Button()
		self.saveButton.SetParent(self.botPanel)
		self.saveButton.SetUpVisual("d:/ymir work/ui/switchbot/save_attr_01.sub")
		self.saveButton.SetOverVisual("d:/ymir work/ui/switchbot/save_attr_02.sub")
		self.saveButton.SetDownVisual("d:/ymir work/ui/switchbot/save_attr_03.sub")
		self.saveButton.SetDisableVisual("d:/ymir work/ui/switchbot/save_attr_03.sub")
		self.saveButton.SetWindowVerticalAlignCenter()
		self.saveButton.SetPosition(BORDER_SPACE, 0)
		self.saveButton.SetToolTipText(localeInfo.SWITCHBOT_SAVE_BUTTON)
		self.saveButton.Show()			
		
		self.startButton = ui.RadioButton()
		self.startButton.SetParent(self.botPanel)
		self.startButton.SetUpVisual("d:/ymir work/ui/switchbot/btn_big_01.sub")
		self.startButton.SetOverVisual("d:/ymir work/ui/switchbot/btn_big_02.sub")
		self.startButton.SetDownVisual("d:/ymir work/ui/switchbot/btn_big_03.sub")
		self.startButton.SetDisableVisual("d:/ymir work/ui/switchbot/btn_big_03.sub")
		self.startButton.SetWindowVerticalAlignCenter()
		self.startButton.SetWindowHorizontalAlignCenter()
		self.startButton.SetPosition(-self.startButton.GetWidth() // 2, 0)
		self.startButton.SetText(localeInfo.SWITCHBOT_START)
		self.startButton.Show()	
		
		self.stopButton = ui.RadioButton()
		self.stopButton.SetParent(self.botPanel)
		self.stopButton.SetUpVisual("d:/ymir work/ui/switchbot/btn_big_01.sub")
		self.stopButton.SetOverVisual("d:/ymir work/ui/switchbot/btn_big_02.sub")
		self.stopButton.SetDownVisual("d:/ymir work/ui/switchbot/btn_big_03.sub")
		self.stopButton.SetDisableVisual("d:/ymir work/ui/switchbot/btn_big_03.sub")
		self.stopButton.SetWindowVerticalAlignCenter()
		self.stopButton.SetWindowHorizontalAlignCenter()
		self.stopButton.SetPosition(self.stopButton.GetWidth() // 2 + 20, 0)
		self.stopButton.SetText(localeInfo.SWITCHBOT_STOP)
		self.stopButton.Show()		
		
		self.footer = ui.ThinBoardCircle()
		self.footer.SetParent(self)
		self.footer.SetPosition(BORDER_SPACE, BOARD_HEIGHT - BORDER_SPACE - 58)
		self.footer.SetSize(BOT_PANEL_WIDTH, 58)
		self.footer.Show()
		self.scrollPicker = controls.ScrollPicker(self.footer, self.SelectScroll)
		self.scrollPicker.SetPosition(8, 9)
		self.instantButton = controls.Button(self.footer, 228, 18, "Instaswitchbot", self.OpenInstant)
		selectedOptions.changed = self.OptionsChanged
		bonuscatalog.receiver.AddListener(self.BonusCatalogChanged)

		self.SelectSlot(0, notify=False)
			
	def __BindEvents(self):
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		
		self.startButton.SetEvent(lambda arg = True : self.SetActive(arg))
		self.stopButton.SetEvent(lambda arg = False : self.SetActive(arg))
		self.saveButton.SetEvent(ui.__mem_func__(self.OpenSaveConfiguration))
		self.__LoadR1()

	def __LoadR1(self):
		"""The R1 look (root/uiswitchbotr1.py) drawn into this window unless Settings -> "Starý vzhled" chose the
		original look; a failure traces to syserr and keeps the original look (not retried on every opening)."""
		if self.r1 or self.r1Failed or not uir1.UseR1():
			return
		try:
			import uiswitchbotr1
			self.r1 = uiswitchbotr1.SwitchbotSkin(self, localeInfo.SWITCHBOT_TITLE)
		except Exception:
			uir1.TraceFailure("the switchbot")
			self.r1Failed = True
			self.r1 = None

	def __SyncLook(self):
		"""Settings -> "Starý vzhled" / the R1 look take effect on the next opening."""
		wanted = uir1.UseR1() and not self.r1Failed
		if wanted and not self.r1:
			self.__LoadR1()
		elif not wanted and self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def Destroy(self):
		if self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()
		self.Close()
		bonuscatalog.receiver.RemoveListener(self.BonusCatalogChanged)
		if self.scrollPicker:
			self.scrollPicker.Destroy()
		if self.instantWindow:
			self.instantWindow.Destroy()
		self.__OnRerollCancel()
		self.rerollDialog = None
		instantOptions.Reset()
		if selectedOptions.changed == self.OptionsChanged:
			selectedOptions.Reset()
		self.__Initialize()

	def Open(self):
		self.__SyncLook()
		if not bonuscatalog.IsReady():
			ShowSlotLockedMessage()
		self.Show()
		self.SetTop()
		self.SetCenterPosition()
		self.RefreshSwitchbotWindow()
		for slot in range(switchbot.SLOT_COUNT):
			if bonuscatalog.IsSlotAllowed(slot):
				selectedOptions.Request(slot)

	def OnUpdate(self):
		# A request or its reply lost on the way (a warp) must not leave the rows empty until the window is
		# reopened: occupied slots without options are asked for again, the reply refreshes the window.
		selectedOptions.Retry()

	def Close(self):
		self.__OnRerollCancel()
		if self.scrollPicker:
			self.scrollPicker.Close()
		if self.instantWindow:
			self.instantWindow.Close()
		for row in self.attrDict.values():
			row.valuePicker.Close()
			row.valueEditLine.KillFocus()
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()
			
		if self.configurationSaveWindow:
			self.configurationSaveWindow.Close()
			
		self.Hide()
		return True
		
	def __OnPlacedItem(self, slot_num):
		self.pendingPlacedItems.add(slot_num)
		self.SelectSlot(slot_num)
		
	def SelectSlot(self, selectedSlot, notify=True):
		if not bonuscatalog.IsSlotAllowed(selectedSlot):
			if notify:
				ShowSlotLockedMessage()
			return

		if self.scrollPicker:
			self.scrollPicker.Close()
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()
		self.itemTabs[self.selectedSlot].SetUp()	
		self.selectedSlot = selectedSlot
		self.itemTabs[self.selectedSlot].Down()
		
		self.SelectAlternative(0)
		
	def GetSelectedSlot(self):
		return self.selectedSlot

	def GetSelectedAlternative(self):
		return self.alternative
		
	def SelectAlternative(self, alternative):
		self.alternativeButtons[self.alternative].SetUp()	
		self.alternative = alternative
		self.alternativeButtons[self.alternative].Down()
		
		self.RefreshSwitchbotWindow()
		
	def SetActive(self, active):
		if self.selectedSlot >= switchbot.SLOT_COUNT:
			return

		if active and not bonuscatalog.IsSlotAllowed(self.selectedSlot):
			ShowSlotLockedMessage()
			return
			
		if active and self.IsActiveSlot():
			return
			
		if not active and not self.IsActiveSlot():
			return
				
		if active:
			selectedOptions.Start(self.selectedSlot)
		else:
			switchbot.Stop(self.selectedSlot)
			
	def AskReroll(self, slot):
		"""the server refused to start a slot whose item already carries the bonuses (SLOT_MATCHED).
		Ask the player; once he confirmed the start is repeated with the same configuration and rolls anyway.
		Returns False when there is nothing to ask about (the caller then shows the plain refusal)."""
		if not 0 <= slot < switchbot.SLOT_COUNT or switchbot.IsActive(slot) or \
				not player.GetItemIndex(player.SWITCHBOT, slot):
			return False
		request = selectedOptions.BuildRequest(slot, force=True)
		if request is None:
			return False
		import uiCommon
		if not self.rerollDialog:
			dialog = uiCommon.QuestionDialog2()
			dialog.SetText1(uir1.Tr_(u"Předmět už má požadované bonusy.", "The item already has the requested bonuses."))
			dialog.SetText2(uir1.Tr_(u"Opravdu chceš bonusy přetočit?", "Do you really want to reroll them?"))
			dialog.SetAcceptText(uir1.Tr_(u"Přetočit", "Reroll"))
			dialog.SetCancelText(uir1.Tr_(u"Zrušit", "Cancel"))
			dialog.SetAcceptEvent(ui.__mem_func__(self.__OnRerollAccept))
			dialog.SetCancelEvent(ui.__mem_func__(self.__OnRerollCancel))
			self.rerollDialog = dialog
		self.rerollSlot = slot
		self.rerollRequest = request
		self.rerollDialog.Open()
		return True

	def __OnRerollAccept(self):
		self.__CloseRerollDialog()
		slot, self.rerollSlot = self.rerollSlot, -1
		request, self.rerollRequest = self.rerollRequest, None
		if request is not None and 0 <= slot < switchbot.SLOT_COUNT and not switchbot.IsActive(slot):
			selectedOptions.Start(slot, expected=request, force=True)

	def __OnRerollCancel(self):
		self.__CloseRerollDialog()
		self.rerollSlot = -1
		self.rerollRequest = None

	def __CloseRerollDialog(self):
		if self.rerollDialog:
			self.rerollDialog.Close()

	def SelectScroll(self, vnum):
		if switchbot.IsActive(self.selectedSlot):
			return
		if not SameKind(vnum, selectedOptions.Scroll(self.selectedSlot)):
			self.__ClearSlotAttributes(self.selectedSlot)
		selectedOptions.Request(self.selectedSlot, vnum)
		self.RefreshSwitchbotWindow()

	def __ClearSlotAttributes(self, slot):
		for alternative in range(switchbot.ALTERNATIVE_COUNT):
			for index in range(ATTR_SLOT_COUNT):
				attributeMemory.SetAttribute(slot, alternative, index, 0, 0)

	def OptionsChanged(self, slot):
		# The bonuses are trimmed only against the options of the item that is in the slot now; options that have
		# not arrived (or belong to another item) are no reason to throw the player's bonuses away.
		catalog = selectedOptions.Catalog(slot)
		if catalog and not switchbot.IsActive(slot):
			for alternative in range(switchbot.ALTERNATIVE_COUNT):
				for index in range(ATTR_SLOT_COUNT):
					kind, value = switchbot.GetAttribute(slot, alternative, index)
					if not kind:
						continue
					maximum = selectedOptions.Maximum(slot, kind)
					if not maximum or index >= catalog['slots']:
						attributeMemory.SetAttribute(slot, alternative, index, 0, 0)
					elif value > maximum:
						attributeMemory.SetAttribute(slot, alternative, index, kind, maximum)
		if slot == self.selectedSlot:
			self.RefreshSwitchbotWindow()

	def BonusCatalogChanged(self):
		# The server catalog arrived or changed: slots, scrolls and families
		# may differ, so ask again for every usable slot's options.
		self.lastItemVnums = {}
		if self.instantWindow and instantOptions.cell is not None and not instantOptions.running:
			instantOptions.SetTarget(instantOptions.cell)
		if self.IsShow():
			self.RefreshSwitchbotWindow()

	def OpenInstant(self):
		if not self.instantWindow:
			self.instantWindow = InstantSwitchbotWindow(self)
		if self.instantWindow.IsShow():
			self.instantWindow.Close()		# the button that opens a window closes it on a second click
		else:
			self.instantWindow.Open()

	def OpenSaveConfiguration(self):
		if not self.configurationSaveWindow:
			self.configurationSaveWindow = ConfigurationWindow(self)
				
		if self.configurationSaveWindow.IsShow():
			self.configurationSaveWindow.Close()
		else:
			self.configurationSaveWindow.Open()
			
	def SetItemToolTip(self, tooltipItem):
		for i in range(switchbot.SLOT_COUNT):
			self.itemTabs[i].SetItemToolTip(tooltipItem)
			
	def __AnyAttributeConfigured(self):
		for i in range(switchbot.ALTERNATIVE_COUNT):
			for j in range(ATTR_SLOT_COUNT):
				(type, value) = switchbot.GetAttribute(self.selectedSlot, i, j)
				if type and value:
					return True
				
		return False
		
	def RefreshSwitchbotWindow(self):
		for slot in range(switchbot.SLOT_COUNT):
			self.itemTabs[slot].SetLocked(not bonuscatalog.IsSlotAllowed(slot))

		if not bonuscatalog.IsSlotAllowed(self.selectedSlot):
			self.itemTabs[self.selectedSlot].SetUp()
			self.selectedSlot = 0
			self.itemTabs[self.selectedSlot].Down()
			self.alternativeButtons[self.alternative].SetUp()
			self.alternative = 0
			self.alternativeButtons[self.alternative].Down()

		self.__RefreshItemSlots()
		self.__RefreshAlternatives()
		self.__RefreshAttributeRows()	
		self.__RefreshButtons()
		for slot in range(switchbot.SLOT_COUNT):
			vnum = player.GetItemIndex(player.SWITCHBOT, slot)
			if bonuscatalog.IsSlotAllowed(slot):
				self.__RefreshItemOptions(slot, vnum)
		if self.scrollPicker:
			self.scrollPicker.Refresh(self.selectedSlot)
		if self.instantWindow and self.instantWindow.IsShow():
			self.instantWindow.Refresh()
		if self.r1:
			self.r1.Sync()
		
	def RefreshSwitchbotItem(self, slot):
		itemTab = self.itemTabs.get(slot, None)
		if not itemTab:
			return
			
		itemTab.RefreshItemSlot()
		vnum = player.GetItemIndex(player.SWITCHBOT, slot)
		self.__RefreshItemOptions(slot, vnum)
		if self.scrollPicker:
			self.scrollPicker.Refresh(self.selectedSlot)
		if self.instantWindow and self.instantWindow.IsShow():
			self.instantWindow.Refresh()
		if self.r1:
			self.r1.Sync()

	def __RefreshItemOptions(self, slot, vnum):
		if self.lastItemVnums.get(slot) == vnum and not (vnum and slot in self.pendingPlacedItems):
			return
		# Not a new item: the first look of this window at the slot, or after a new catalog or a warp.
		sameItem = slot not in self.lastItemVnums
		self.lastItemVnums[slot] = vnum
		if not vnum:
			selectedOptions.Request(slot)
			return
		self.pendingPlacedItems.discard(slot)
		current = selectedOptions.Scroll(slot)
		if switchbot.IsActive(slot):
			scroll = current
		elif sameItem and bonuscatalog.IsOfferedScroll(current):
			scroll = HeldScroll(current)
		else:
			scroll = selectedOptions.Wanted(slot, vnum)
		if current and not SameKind(scroll, current):
			self.__ClearSlotAttributes(slot)
		selectedOptions.Request(slot, scroll)
		
	def __RefreshItemSlots(self):
		for i in range(switchbot.SLOT_COUNT):
			itemTab = self.itemTabs.get(i, None)
			if not itemTab:
				continue
				
			itemTab.RefreshItemSlot()
			
	def __RefreshAlternatives(self):
		if self.IsEmptySlot():
			self.alternativePanel.Hide()
		else:
			self.alternativePanel.Show()
			
	def __RefreshAttributeRows(self):
		if self.IsShow():
			ShowEmptyOptionsMessage(selectedOptions.Catalog(self.selectedSlot))
		for i in range(ATTR_SLOT_COUNT):
			row = self.attrDict.get(i, None)
			if not row:
				continue
				
			catalog = selectedOptions.Catalog(self.selectedSlot)
			limit = catalog['slots'] if catalog else 0
			if catalog and catalog['values'] and i < limit:
				row.Show()
			else:
				row.Hide()
			
			row.RefreshAttributeRow(self.selectedSlot, self.alternative, i)		
			
	def __RefreshButtons(self):
		if self.IsActiveSlot():
			self.startButton.Disable()
			self.stopButton.Enable()
			return
		if self.IsEmptySlot() or not selectedOptions.Attributes(self.selectedSlot) or not self.__AnyAttributeConfigured():
			self.startButton.Disable()
			self.stopButton.Disable()
			return
			
		self.startButton.Enable()
		self.stopButton.Enable()
		
		if self.IsActiveSlot():
			self.stopButton.SetUp()
			self.startButton.Down()
		else:
			self.stopButton.Down()
			self.startButton.SetUp()
			
	def __ClearAttributes(self):
		
	
		for index, row in self.attrDict.items():
			for alternative in range(switchbot.ALTERNATIVE_COUNT):
				row.RefreshAttributeRow(self.selectedSlot, alternative, index)
		
	def __OnAttributeUpdate(self, attrIdx):
		self.__RefreshButtons()

	def __OnSearchAttribute(self, attrIdx):
		if self.attributeSearchWindow:
			self.attributeSearchWindow.Close()
			del self.attributeSearchWindow
			
		self.attrSearchIdx = attrIdx
			
		wnd = SearchListWindow()
		width = 340
		height = 260
		wnd.MakeWindow(width, height)
		wnd.SetTitleName(localeInfo.SWITCHBOT_SELECT_ATTR)
		wnd.SetAcceptArgsType("KEY_VALUE")

		(mouseX, mouseY) = wndMgr.GetMousePosition()

		if mouseX + width//2 > wndMgr.GetScreenWidth():
			xPos = wndMgr.GetScreenWidth() - width
		elif mouseX - width//2 < 0:
			xPos = 0
		else:
			xPos = mouseX - width//2
			
		if mouseY + height//2 > wndMgr.GetScreenHeight():
			yPos = wndMgr.GetScreenHeight() - height
		elif mouseY - height//2 < 0:
			yPos = 0
		else:
			yPos = mouseY - height//2

		wnd.SetPosition(xPos, yPos)	
				
		attributes = selectedOptions.Attributes(self.selectedSlot)

		selectedAttributes = [switchbot.GetAttribute(self.selectedSlot, self.alternative, attrIndex)[0] for attrIndex in range(ATTR_SLOT_COUNT)]
		otherSelected = [kind for index, kind in enumerate(selectedAttributes) if index != attrIdx]
		AppendAttributeChoices(wnd, attributes, selectedAttributes, otherSelected)
		
		wnd.SetAcceptEvent(ui.__mem_func__(self.__OnAcceptSearch))
		wnd.SetCancelEvent(ui.__mem_func__(self.__OnCancelSearch))
		wnd.SetTop()
		wnd.Open()

		self.attributeSearchWindow = wnd
		
	def __AttributeWheelChoices(self, attrIdx):
		# the list the picker of row attrIdx offers (__OnSearchAttribute), in its order, with the row's own bonus
		attributes = selectedOptions.Attributes(self.selectedSlot)
		selectedAttributes = [switchbot.GetAttribute(self.selectedSlot, self.alternative, attrIndex)[0] for attrIndex in range(ATTR_SLOT_COUNT)]
		return WheelChoices(attributes, selectedAttributes, attrIdx)

	def __ChooseAttribute(self, attrIdx, key, value):
		# the wheel over a bonus field: the same as picking that bonus in the row's picker; an open picker's list
		# no longer matches the rows (its exclusions), so it is closed
		if self.attributeSearchWindow and self.attributeSearchWindow.IsShow():
			self.attributeSearchWindow.Close()
		self.attrSearchIdx = attrIdx
		self.__OnAcceptSearch(key, value)

	def __OnAcceptSearch(self, key, value):
		if self.attrSearchIdx < 0 or self.attrSearchIdx >= ATTR_SLOT_COUNT:
			return
			
		attrRow = self.attrDict.get(self.attrSearchIdx, None)
		if not attrRow:
			return
			
		maxValue = selectedOptions.Maximum(self.selectedSlot, key)
			
		attrRow.SetAttribute(value, maxValue)
		attributeMemory.SetAttribute(self.selectedSlot, self.alternative, self.attrSearchIdx, key, maxValue)
		
		self.__RefreshButtons()
		if self.instantWindow and self.instantWindow.IsShow():
			self.instantWindow.Refresh()
		
	def SetSavedAttribute(self, slot, alternative, attrIndex, attrType, attrValue):
		if attrIndex < 0 or attrIndex >= ATTR_SLOT_COUNT:
			return
			
		attrRow = self.attrDict.get(attrIndex, None)
		if not attrRow:
			return
			
		if slot >= switchbot.SLOT_COUNT:
			return

		if not bonuscatalog.IsSlotAllowed(slot):
			ShowSlotLockedMessage()
			return
			
		if switchbot.IsActive(slot):
			return
			
		catalog = selectedOptions.Catalog(slot)
		maximum = selectedOptions.Maximum(slot, attrType)
		if catalog and (not maximum or attrIndex >= catalog['slots']):
			attributeMemory.SetAttribute(slot, alternative, attrIndex, 0, 0)
		else:
			if maximum:
				attrValue = min(attrValue, maximum)
			attributeMemory.SetAttribute(slot, alternative, attrIndex, attrType, attrValue)

		self.RefreshSwitchbotWindow()
		
	def IsEmptySlot(self):
		slot = self.itemTabs.get(self.selectedSlot, None)
		if not slot:
			return True
			
		return slot.IsEmpty()
		
	def IsActiveSlot(self):
		slot = self.itemTabs.get(self.selectedSlot, None)
		if not slot:
			return False
			
		return slot.IsActive()
		
	def GetSlotAttributeCount(self):
		slot = self.itemTabs.get(self.selectedSlot, None)
		if not slot:
			return 0
			
		return slot.GetAttributeCount()
		
	def OnMoveWindow(self, x, y):
		if self.configurationSaveWindow:
			self.configurationSaveWindow.AdjustPosition()
		
	def __OnCancelSearch(self):
		pass
		
	def OnPressEscapeKey(self):
		self.Close()
		return True

class SearchListWindow(ui.BoardWithTitleBar):
	class SearchListItem(ui.Window):
		LIST_ITEM_HEIGHT = 12
	
		DISABLED_COLOR = 0xff808080

		def __init__(self, key, value, enabled = True, note = ""):
			ui.Window.__init__(self)
			
			self.key = key
			self.value = value
			self.enabled = enabled
			self.isDown = False
			self.onClickEvent = None	

			self.textLine = ui.TextLine()
			self.textLine.AddFlag("not_pick")
			self.textLine.SetParent(self)
			self.textLine.SetVerticalAlignCenter()
			self.textLine.SetWindowVerticalAlignCenter()
			self.textLine.SetPosition(10, -1)
			self.textLine.SetText(str(value) + (" (%s)" % note if note else ""))
			if not enabled:
				self.textLine.SetPackedFontColor(self.DISABLED_COLOR)
			self.textLine.UpdateRect()
			self.textLine.Show()
				
		def __del__(self):
			ui.Window.__del__(self)
			
			self.key = None
			self.value = None
			
			self.onClickEvent = None
			
			self.textLine = 0
			
		def OnMouseLeftButtonUp(self):
			if self.enabled and not self.isDown:
				self.__OnClick()
				self.Down()
				
		def OnRender(self):
			if self.enabled and (self.IsIn() or self.isDown):
				self.RenderHoverOrSelected()
				
		def RenderHoverOrSelected(self):
			x, y = self.GetGlobalPosition()
			grp.SetColor(grp.GenerateColor(0.0, 0.0, 0.7, 0.7))
			grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())
				
		def SetUp(self):
			self.isDown = False
			
		def Down(self):
			self.isDown = True
			
		def IsDown(self):
			return self.isDown
			
		def GetKey(self):
			return self.key
			
		def GetValue(self):
			return self.value
			
		def GetText(self):	
			return self.textLine.GetText()
			
		def IsEnabled(self):
			return self.enabled
			
		def MatchText(self, text):
			return folded(text) in folded(self.GetText())
			
		def SetOnClickEvent(self, event):
			self.onClickEvent = ui.__mem_func__(event)
			
		def __OnClick(self):
			if self.onClickEvent:
				self.onClickEvent(self.key, self.value)
			
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("attach")
		self.AddFlag("movable")
		
		self.__Initialize()
		
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
		self.__Initialize()
		
	def __Initialize(self):
		self.listItems = {}
		self.acceptEvent = None
		self.acceptArgsType = "VALUE"
		self.cancelEvent = None
		self.r1 = None
		
	def SetTitleName(self, name):
		ui.BoardWithTitleBar.SetTitleName(self, name)
		if self.r1:
			self.r1.SetTitle(name)

	def __ApplyR1Look(self):
		"""The R1 look (root/uiswitchbotsearchr1.py) drawn into this window unless Settings -> "Starý vzhled" chose
		the original one; a failure traces to syserr and keeps the original window."""
		if not uir1.UseR1():
			return
		try:
			import uiswitchbotsearchr1
			self.r1 = uiswitchbotsearchr1.Build(self)
		except Exception:
			uir1.TraceFailure("switchbot attribute picker")
			self.r1 = None

	def MakeWindow(self, width, height, maxInput = 50):
		self.SetSize(width, height)
		
		self.searchInput = ui.ThinBoardCircle()
		self.searchInput.SetParent(self)
		self.searchInput.SetSize(width - (BORDER_SPACE*2), INPUT_HEIGHT)
		self.searchInput.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.searchInput.Show()
		
		self.searchEditLine = ui.EditLine()
		self.searchEditLine.SetParent(self.searchInput)
		self.searchEditLine.SetPosition(10, 8)
		self.searchEditLine.SetSize(self.searchInput.GetWidth() - 20, self.searchInput.GetHeight() - 16)
		self.searchEditLine.SetMax(maxInput)
		self.searchEditLine.SetReturnEvent(ui.__mem_func__(self.__OnAccept))
		self.searchEditLine.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.searchEditLine.OnIMEUpdate = self.__OnSearchIMEUpdate
		self.searchEditLine.Show()
		
		containerHeight = height - (BORDER_SPACE_TOP + INPUT_HEIGHT + 30)
		
		self.scrollBar = SettingsScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetPosition(width - BORDER_SPACE - 14, BORDER_SPACE_TOP + INPUT_HEIGHT + 2)
		self.scrollBar.SetScrollBarSize(containerHeight - 4)	
		
		self.container = ui.ThinBoardCircle()
		self.container.SetParent(self)
		self.container.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + INPUT_HEIGHT)
		self.container.SetSize(width - (BORDER_SPACE*2), containerHeight)
		self.container.Show()
		
		listBoxHeight = self.container.GetHeight()
		listBoxWidth = self.container.GetWidth()
		
		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self.container)
		self.listBox.SetPosition(2, 2)
		self.listBox.SetSize(listBoxWidth - 4, listBoxHeight - 4)
		self.listBox.SetItemStep(self.SearchListItem.LIST_ITEM_HEIGHT)
		self.listBox.SetViewItemCount(self.__GetViewItemCount())
		self.listBox.SetItemSize(listBoxWidth - 4, self.SearchListItem.LIST_ITEM_HEIGHT)
		self.listBox.SetScrollBar(self.scrollBar)
		self.listBox.Show()
		
		buttonWidth = width // 2 - 20
		
		self.acceptButton = ui.Button()
		self.acceptButton.SetParent(self)
		self.acceptButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		self.acceptButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		self.acceptButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.acceptButton.SetDisableVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.acceptButton.SetWindowVerticalAlignBottom()
		self.acceptButton.SetWindowHorizontalAlignCenter()
		self.acceptButton.SetPosition(-buttonWidth // 2 - 5, 29)
		self.acceptButton.SetText(localeInfo.UI_ACCEPT)
		self.acceptButton.SetEvent(ui.__mem_func__(self.__OnAccept))
		self.acceptButton.Show()
		
		self.cancelButton = ui.Button()
		self.cancelButton.SetParent(self)
		self.cancelButton.SetUpVisual("d:/ymir work/ui/public/large_button_01.sub")
		self.cancelButton.SetOverVisual("d:/ymir work/ui/public/large_button_02.sub")
		self.cancelButton.SetDownVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.cancelButton.SetDisableVisual("d:/ymir work/ui/public/large_button_03.sub")
		self.cancelButton.SetWindowVerticalAlignBottom()
		self.cancelButton.SetWindowHorizontalAlignCenter()
		self.cancelButton.SetPosition(buttonWidth // 2 - 5, 29)
		self.cancelButton.SetText(localeInfo.UI_CANCEL)
		self.cancelButton.SetEvent(ui.__mem_func__(self.__OnCancel))
		self.cancelButton.Show()
		
		self.__AdjustScrollbar()
		self.__ApplyR1Look()
		
	def __OnSearchIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchEditLine)
		self.__RefreshListBox()
		
	def __GetViewItemCount(self):
		return self.container.GetHeight() // self.SearchListItem.LIST_ITEM_HEIGHT
		
	def __AdjustScrollbar(self):
		if len(self.listItems) > self.__GetViewItemCount():
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2) - 16
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.container.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.SearchListItem.LIST_ITEM_HEIGHT)
			attachmentCount = len(self.listItems)
			scrollBarHeight = min(float(self.__GetViewItemCount()) / float(attachmentCount), 1.0)
			self.scrollBar.SetMiddleBarSize(scrollBarHeight)
			self.scrollBar.SetScrollStep(1.0 / float(attachmentCount - self.__GetViewItemCount()))
			self.scrollBar.Show()
		else:
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2)
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.container.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.SearchListItem.LIST_ITEM_HEIGHT)
			self.scrollBar.Hide()
		if self.r1:
			self.r1.Sync()
		
	def RemoveAllItems(self):
		self.listItems = {}
		self.listBox.RemoveAllItems()		
		
	def AppendItem(self, key, value = "", keywords = "", enabled = True, note = ""):
		if key in self.listItems:
			return
			
		if not value:
			value = key
			
		self.listItems[key] = { "value" : value, "item" : None, "keywords" : keywords,
			"enabled" : enabled, "note" : note, }
		self.__RefreshListBox()
		
	def __RefreshListBox(self):
		self.listBox.RemoveAllItems()
		
		self.__AdjustScrollbar()
		
		query = self.searchEditLine.GetText()
		for key, dict in self.listItems.items():
			listItem = dict["item"]
			if switchbotelements.Matches(query, dict["value"], dict.get("keywords", "")):
				listItem = self.SearchListItem(key, dict["value"], dict.get("enabled", True), dict.get("note", ""))
				listItem.textLine.SetLimitWidth(self.listBox.GetWidth() - 16)
				listItem.SetOnClickEvent(self.__OnClickListItem)
				self.listBox.AppendItem(listItem)
			else:
				del listItem
			
	def GetSelectedItem(self):
		for listItem in self.listBox.GetItems():
			if listItem.IsDown():
				return listItem
				
		return None
		
	def SetCancelEvent(self, event):
		self.cancelEvent = event
		
	def SetAcceptEvent(self, event):
		self.acceptEvent = event
		
	def SetAcceptArgsType(self, type):
		self.acceptArgsType = type
		
	def __OnClickListItem(self, key, value):
		curItem = self.GetSelectedItem()
		if curItem:
			curItem.SetUp()
				
	def __OnCancel(self):
		if self.cancelEvent:
			self.cancelEvent()
			
		self.Close()
			
	def __OnAccept(self):
		selItem = self.GetSelectedItem()
		if not selItem:
			enabledItems = [listItem for listItem in self.listBox.GetItems() if listItem.IsEnabled()]
			if len(enabledItems) == 1:
				selItem = enabledItems[0]
			else:
				return
		if not selItem.IsEnabled():
			return
	
		if self.acceptEvent:
			if self.acceptArgsType == "VALUES":
				self.acceptEvent(selItem.GetValue())
			elif self.acceptArgsType == "KEY":
				self.acceptEvent(selItem.GetKey())
			elif self.acceptArgsType == "KEY_VALUE":
				self.acceptEvent(selItem.GetKey(), selItem.GetValue())
			
		self.Close()
		
	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnMouseWheel(self, length):
		if not self.scrollBar.IsShow():
			return False
		return uiwheel.Scroll(self.scrollBar, length)	# one bonus per notch (the list's row step)
		
	def Open(self):
		self.Show()
		self.searchEditLine.SetFocus()
		
	def Close(self):
		self.searchEditLine.SetText("")
		self.searchEditLine.KillFocus()
		self.Hide()		

class ConfigurationWindow(ui.BoardWithTitleBar):
	BOARD_WIDTH = 250

	class ConfigurationLine(ui.Window):
		LIST_ITEM_HEIGHT = 26
	
		id = 0
		name = ""
	
		loadEvent = None
		deleteEvent = None
	
		def __init__(self, width):
			ui.Window.__init__(self)
			
			self.SetSize(width, 26)
			
			self.nameTextLine = ui.TextLine()
			self.nameTextLine.SetParent(self)
			self.nameTextLine.SetVerticalAlignCenter()
			self.nameTextLine.SetWindowVerticalAlignCenter()
			self.nameTextLine.SetPosition(5, -1)
			self.nameTextLine.Show()
				
			self.loadButton = ui.Button()
			self.loadButton.SetParent(self)
			self.loadButton.SetUpVisual("d:/ymir work/ui/switchbot/load_attr_01.sub")
			self.loadButton.SetOverVisual("d:/ymir work/ui/switchbot/load_attr_02.sub")
			self.loadButton.SetDownVisual("d:/ymir work/ui/switchbot/load_attr_03.sub")
			self.loadButton.SetDisableVisual("d:/ymir work/ui/switchbot/load_attr_03.sub")
			self.loadButton.SetWindowHorizontalAlignRight()
			self.loadButton.SetWindowVerticalAlignCenter()
			self.loadButton.SetPosition(24 * 2 + 2, 1)
			self.loadButton.SetToolTipText(localeInfo.SWITCHBOT_LOAD_CONFIGURATION)
			self.loadButton.SetEvent(ui.__mem_func__(self.__OnClickLoadButton))
			self.loadButton.Show()
			
			self.deleteButton = ui.Button()
			self.deleteButton.SetParent(self)
			self.deleteButton.SetUpVisual("d:/ymir work/ui/switchbot/delete_attr_01.sub")
			self.deleteButton.SetOverVisual("d:/ymir work/ui/switchbot/delete_attr_02.sub")
			self.deleteButton.SetDownVisual("d:/ymir work/ui/switchbot/delete_attr_03.sub")
			self.deleteButton.SetDisableVisual("d:/ymir work/ui/switchbot/delete_attr_03.sub")
			self.deleteButton.SetWindowHorizontalAlignRight()
			self.deleteButton.SetWindowVerticalAlignCenter()
			self.deleteButton.SetPosition(24 + 2, 1)
			self.deleteButton.SetToolTipText(localeInfo.SWITCHBOT_CLEAR_CONFIGURATION)
			self.deleteButton.SetEvent(ui.__mem_func__(self.__OnClickDeleteButton))
			self.deleteButton.Show()
			
		def __del__(self):
			ui.Window.__del__(self)
			
		def Load(self, id, name):
			self.id = id
			self.name = name
			self.nameTextLine.SetText(name)
			
		def SetLoadEvent(self, event):
			self.loadEvent = event
			
		def SetDeleteEvent(self, event):
			self.deleteEvent = event
			
		def __OnClickLoadButton(self):
			if self.loadEvent:
				self.loadEvent(self.id)
			
		def __OnClickDeleteButton(self):
			if self.deleteEvent:
				self.deleteEvent(self.id)
	
	wndSwitchbot = None
	
	nameInput = None
	valueEditLine = None
	
	dict = {}
	
	listItems = {}
	
	r1 = None
	r1Failed = False

	def __init__(self, wndSwitchbot=None):
		ui.BoardWithTitleBar.__init__(self)
		
		if not wndSwitchbot:
			import exception
			exception.Abort("ConfigurationWindow.__init__ Cannot initialize without binding to Switchbot window.")
			
		self.wndSwitchbot = wndSwitchbot
		
		self.__LoadWindow()
		self.__LoadR1()
		
	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)
		
	def __LoadR1(self):
		"""The R1 look (root/uiswitchbotpresetsr1.py) drawn into this window unless Settings -> "Starý vzhled" chose
		the original look; a failure traces to syserr and keeps the original window (not retried on every opening)."""
		if self.r1 or self.r1Failed or not uir1.UseR1():
			return
		try:
			import uiswitchbotpresetsr1
			self.r1 = uiswitchbotpresetsr1.Build(self)
		except Exception:
			uir1.TraceFailure("the switchbot presets")
			self.r1 = None
		if not self.r1:
			self.r1Failed = True

	def __SyncLook(self):
		"""Settings -> "Starý vzhled" / the R1 look take effect on the next opening."""
		if uir1.UseR1():
			self.__LoadR1()
		elif self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def Destroy(self):
		if self.r1:
			r1, self.r1 = self.r1, None
			r1.Destroy()
		self.saveButton = None
		self.nameInput = None
		self.valueEditLine = None
		self.scrollBar = None
		self.container = None
		self.listBox = None
		
		self.listItems = {}
		
	def __LoadWindow(self):
		self.SetSize(self.BOARD_WIDTH, BOARD_HEIGHT)
		self.SetTitleName(localeInfo.SWITCHBOT_CONFIGURATION_TITLE)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag("attach")
		# self.AddFlag("movable")
	
		self.saveButton = ui.Button()
		self.saveButton.SetParent(self)
		self.saveButton.SetUpVisual("d:/ymir work/ui/switchbot/btn_small_01.sub")
		self.saveButton.SetOverVisual("d:/ymir work/ui/switchbot/btn_small_02.sub")
		self.saveButton.SetDownVisual("d:/ymir work/ui/switchbot/btn_small_03.sub")
		self.saveButton.SetDisableVisual("d:/ymir work/ui/switchbot/btn_small_01.sub")
		self.saveButton.SetWindowHorizontalAlignRight()
		self.saveButton.SetPosition(self.saveButton.GetWidth() + BORDER_SPACE, BORDER_SPACE_TOP + 3)
		self.saveButton.SetText(localeInfo.SWITCHBOT_SAVE)
		self.saveButton.SetEvent(ui.__mem_func__(self.__OnSave))
		self.saveButton.Show()
	
		self.nameInput = ui.ThinBoardCircle()
		self.nameInput.SetParent(self)
		self.nameInput.SetSize(self.BOARD_WIDTH - (BORDER_SPACE * 2) - self.saveButton.GetWidth() - 3, INPUT_HEIGHT)
		self.nameInput.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP)
		self.nameInput.Show()
		
		self.nameEditLine = ui.EditLine()
		self.nameEditLine.SetParent(self.nameInput)
		self.nameEditLine.SetSize(self.nameInput.GetWidth() - 20, 18)
		self.nameEditLine.SetMax(32)
		self.nameEditLine.SetPosition(10, 7)
		self.nameEditLine.Show()
		self.nameEditLine.SetEscapeEvent(ui.__mem_func__(self.__OnEscapeEvent))
		
		height = BOARD_HEIGHT - BORDER_SPACE_TOP - INPUT_HEIGHT - BORDER_SPACE
		
		self.scrollBar = ui.ScrollBar()
		self.scrollBar.SetParent(self)
		self.scrollBar.SetWindowHorizontalAlignRight()
		self.scrollBar.SetPosition(23, BORDER_SPACE_TOP + INPUT_HEIGHT + 2)
		self.scrollBar.SetScrollBarSize(height - 4)	
		
		self.container = ui.ThinBoardCircle()
		self.container.SetParent(self)
		self.container.SetPosition(BORDER_SPACE, BORDER_SPACE_TOP + INPUT_HEIGHT)
		self.container.SetSize(BOARD_WIDTH - (BORDER_SPACE*2), height)
		self.container.Show()
		
		listBoxHeight = self.container.GetHeight()
		listBoxWidth = self.container.GetWidth()
		
		self.listBox = ui.ListBoxEx()
		self.listBox.SetParent(self.container)
		self.listBox.SetPosition(2, 2)
		self.listBox.SetSize(listBoxWidth, listBoxHeight)
		self.listBox.SetItemStep(self.ConfigurationLine.LIST_ITEM_HEIGHT + 1)
		self.listBox.SetViewItemCount(self.__GetViewItemCount())
		self.listBox.SetItemSize(listBoxWidth, self.ConfigurationLine.LIST_ITEM_HEIGHT)
		self.listBox.SetScrollBar(self.scrollBar)
		self.listBox.Show()
		
		self.__AdjustScrollbar()
		
	def LoadConfigurations(self):
		try:
			self.dict = presetstorage.load("switchbot", switchbot.ALTERNATIVE_COUNT, player.ATTRIBUTE_SLOT_MAX_NUM)
		except (OSError, ValueError, RecursionError):
			self.dict = {}	
		
		self.listBox.RemoveAllItems()
			
		lineWidth = self.listBox.GetWidth()
		if len(self.dict) > self.__GetViewItemCount():	
			lineWidth -= 20
			
		self.__AdjustScrollbar()
			
		for key in self.dict.keys():
			config = self.dict.get(key, None)
			if not config:
				continue
				
			line = self.ConfigurationLine(lineWidth)
			line.Load(key, config["name"])
			line.SetLoadEvent(ui.__mem_func__(self.__OnApplyConfiguration))
			line.SetDeleteEvent(ui.__mem_func__(self.__OnDeleteConfiguration))
			self.listBox.AppendItem(line)
			
			self.listItems[key] = line
			
		if self.r1:
			self.r1.Sync()

	def SaveConfigurations(self):
		try:
			presetstorage.save("switchbot", self.dict, switchbot.ALTERNATIVE_COUNT, player.ATTRIBUTE_SLOT_MAX_NUM)
		except (OSError, ValueError):
			chat.AppendChat(chat.CHAT_TYPE_INFO, "Konfiguraci se nepodařilo uložit.")
			
	def __OnApplyConfiguration(self, key):
		config = self.dict.get(key, None)
		if not config:
			return
			
		if not self.wndSwitchbot:
			return
			
		# Načíst fills the variant shown (Varianta 1 | 2) of the selected slot; the other variant stays
		# as it is (it previously went into Varianta 1 and wiped Varianta 2 with the preset's
		# empty second row). SetSavedAttribute is the manual edit path: limits, memory, refresh.
		selectedSlot = self.wndSwitchbot.GetSelectedSlot()
		alternative = self.wndSwitchbot.GetSelectedAlternative()
		attributes = PresetAttributes(config, alternative)
		for attrIdx in range(len(attributes)):
			(attrType, attrValue) = attributes[attrIdx]
			self.wndSwitchbot.SetSavedAttribute(selectedSlot, alternative, attrIdx, attrType, attrValue)
		
	def __OnDeleteConfiguration(self, key):
		config = self.dict.get(key, None)
		if not config:
			return
			
		del self.listItems[key]
		del self.dict[key]
		self.SaveConfigurations()
		self.LoadConfigurations()
			
	def Open(self):
		self.__SyncLook()
		self.Show()
		self.LoadConfigurations()
		self.AdjustPosition()
	
	def Close(self):
		self.Hide()
		
	def OnMouseWheel(self, length):
		if not self.scrollBar or not self.scrollBar.IsShow():
			return False
		return uiwheel.Scroll(self.scrollBar, length)	# one preset per notch (the list's row step)

	def AdjustPosition(self):
		if not self.wndSwitchbot:
			return 
			
		(x, y) = self.wndSwitchbot.GetGlobalPosition()
		self.SetPosition(x - self.GetWidth(), y)
		
	def __GetViewItemCount(self):
		return self.container.GetHeight() // (self.ConfigurationLine.LIST_ITEM_HEIGHT + 1)
		
	def __AdjustScrollbar(self):
		if len(self.dict) > self.__GetViewItemCount():
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2) - 20
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.ConfigurationLine.LIST_ITEM_HEIGHT)
			attachmentCount = len(self.dict)
			scrollBarHeight = min(float(self.__GetViewItemCount()) / float(attachmentCount), 1.0)
			self.scrollBar.SetMiddleBarSize(scrollBarHeight)
			self.scrollBar.Show()
		else:
			listBoxWidth = self.GetWidth() - (BORDER_SPACE*2)
			self.container.SetSize(listBoxWidth, self.container.GetHeight())
			self.listBox.SetSize(listBoxWidth - 4, self.listBox.GetHeight() - 4)
			self.listBox.SetItemSize(listBoxWidth - 4, self.ConfigurationLine.LIST_ITEM_HEIGHT)
			self.scrollBar.Hide()
		
	def __OnEscapeEvent(self):
		self.Close()
		
	def __GetNewKey(self):
		key = 0
		while key in self.dict:
			key += 1
			
		return key
		
	def __BuildDict(self, slot, alternative, name):
		# Uložit stores the variant shown, in the first row (the storage keeps one row per variant;
		# the others stay empty), so Načíst can put it into either variant.
		key = self.__GetNewKey()
		empty = [(0, 0)] * player.ATTRIBUTE_SLOT_MAX_NUM
		alternatives = [[switchbot.GetAttribute(slot, alternative, i) for i in range(player.ATTRIBUTE_SLOT_MAX_NUM)]]
		alternatives += [list(empty) for unused in range(switchbot.ALTERNATIVE_COUNT - 1)]
		
		new_dict = {
			"name" : name,
			"alternatives" : alternatives,
		}
		
		return (key, new_dict)
		
	def __OnSave(self):
		if not self.wndSwitchbot:
			return
			
		selectedSlot = self.wndSwitchbot.GetSelectedSlot()
		name = self.nameEditLine.GetText()
		
		if not name:
			return
		
		(key, new_dict) = self.__BuildDict(selectedSlot, self.wndSwitchbot.GetSelectedAlternative(), name)
		self.dict[key] = new_dict
		
		self.nameEditLine.SetText("")
		
		self.SaveConfigurations()
		self.LoadConfigurations()
		


class InstantSwitchbotWindow(ui.BoardWithTitleBar):
	"""Inventory based instant reroller with its own target and bonus choices."""
	# an item picked up from the slot is not dropped / given away on the ground or on a character
	# (game.OnMouseLeftButtonUp), like an item picked up from a switchbot slot.
	KEEPS_ITEM_ON_GROUND_DROP = True

	def __init__(self, owner):
		ui.BoardWithTitleBar.__init__(self)
		self.owner = owner
		self.AddFlag('movable')
		self.AddFlag('float')		# a click brings it above the switchbot and the other windows
		self.SetSize(374, 266)
		self.SetTitleName('Instaswitchbot')
		self.SetCloseEvent(self.Close)
		self.r1 = None
		self.r1Failed = False
		# The R1 panels are drawn into this layer: made first, so they lie under the slot, the rows and the footer.
		self.backdrop = ui.Window()
		self.backdrop.SetParent(self)
		self.backdrop.AddFlag('not_pick')
		self.backdrop.SetSize(374, 266)
		self.backdrop.Show()
		self.rows = []
		self.displayedVnum = 0
		self.transfer = switchbottransfer.Transfer()
		self.searchWindow = None
		instantOptions.changed = ui.__mem_func__(self.OptionsChanged)
		self.itemSlot = ui.GridSlotWindow()
		self.itemSlot.SetParent(self)
		self.itemSlot.SetPosition(9, 34)
		self.itemSlot.ArrangeSlot(0, 1, 3, 32, 32, 0, 0)
		self.itemSlot.SetSlotBaseImage('d:/ymir work/ui/public/slot_base.sub', 1, 1, 1, 1)
		self.itemSlot.SetSelectEmptySlotEvent(self.AttachItem)
		self.itemSlot.SetSelectItemSlotEvent(self.ClickItem)
		self.itemSlot.SetUnselectItemSlotEvent(self.UseItem)
		self.itemSlot.SetOverInItemEvent(self.OverItem)
		self.itemSlot.SetOverOutItemEvent(self.OutItem)
		self.itemSlot.Show()
		for index in range(5):
			row = SwitchbotAttribute()
			row.SetProvider(instantOptions)
			row.SetParent(self)
			row.Create(318, index)
			row.SetPosition(48, 34 + index * INPUT_HEIGHT)
			row.SetSearchEvent(self.Search)
			row.SetWheelEvents(self.WheelChoices, self.WheelChoose)
			row.SetAttributeUpdateEvent(self.Changed)
			row.SetEscapeEvent(self.Close)
			row.Show()
			self.rows.append(row)
		self.picker = controls.ScrollPicker(self, self.SelectScroll, instantOptions)
		self.picker.SetPosition(10, 178)
		self.yangIcon = ui.ImageBox()
		self.yangIcon.SetParent(self)
		self.yangIcon.LoadImage('d:/ymir work/ui/game/crimson_ember/inventory/icon_yang.png')
		self.yangIcon.SetPosition(11, 236)
		self.yangIcon.Show()
		self.fee = controls.Text(self, 32, 237, FormatFee(bonuscatalog.InstantFee()))
		self.start = controls.Button(self, 216, 232, 'Točit okamžitě', self.Start)
		self.__LoadR1()

	def __LoadR1(self):
		"""The R1 look (root/uiswitchbotinstantr1.py, variant A) drawn into this window unless Settings -> "Starý
		vzhled" chose the original look; a failure traces to syserr and keeps the original look (not retried)."""
		if self.r1 or self.r1Failed or not uir1.UseR1():
			return
		try:
			import uiswitchbotinstantr1
			self.r1 = uiswitchbotinstantr1.InstantSkin(self)
		except Exception:
			uir1.TraceFailure("the Instaswitchbot")
			self.r1Failed = True
			self.r1 = None

	def __SyncLook(self):
		"""Settings -> "Starý vzhled" / the R1 look take effect on the next opening."""
		wanted = uir1.UseR1() and not self.r1Failed
		if wanted and not self.r1:
			self.__LoadR1()
		elif not wanted and self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def Hide(self):
		# ui.Window.__init__ already calls Hide(): nothing set in __init__ may be needed here
		r1 = getattr(self, 'r1', None)
		if r1:
			r1.HideHint()
		ui.BoardWithTitleBar.Hide(self)

	def AdjustPosition(self):
		"""Beside the switchbot, never over it (like the saved configurations beside it): right of it, left of it
		when the screen has no room on the right, the top edges level."""
		owner = self.owner
		if not owner:
			self.SetCenterPosition()
			return
		x, y = owner.GetGlobalPosition()
		width, height = self.GetWidth(), self.GetHeight()
		screenWidth, screenHeight = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
		right = x + owner.GetWidth() + INSTANT_SIDE_GAP
		if right + width <= screenWidth:
			newX = right
		elif x - INSTANT_SIDE_GAP - width >= 0:
			newX = x - INSTANT_SIDE_GAP - width
		else:
			newX = max(0, screenWidth - width)
		self.SetPosition(newX, max(0, min(y, screenHeight - height)))

	def AttachItem(self, unused):
		if not mouseModule.mouseController.isAttached() or instantOptions.running or self.transfer.pending is not None:
			return
		if mouseModule.mouseController.GetAttachedType() == player.SLOT_TYPE_SWITCHBOT:
			if self.transfer.Begin(mouseModule.mouseController.GetAttachedSlotNumber()):
				instantOptions.SetTarget(None)
				mouseModule.mouseController.DeattachObject()
			return
		if mouseModule.mouseController.GetAttachedType() != player.SLOT_TYPE_INVENTORY:
			return
		cell = mouseModule.mouseController.GetAttachedSlotNumber()
		mouseModule.mouseController.DeattachObject()
		if cell == instantOptions.cell:
			return		# put back where it was picked up: the target and its bonuses stay
		if cell >= 0 and player.GetItemIndex(player.INVENTORY, cell):
			instantOptions.SetTarget(cell)

	def ClickItem(self, unused):
		"""the left click as on a switchbot slot (SwitchbotItemTab.SelectItemSlot): the item on the cursor
		(an inventory item: it can be dragged back into the switchbot, the inventory, ...); Alt pastes its link."""
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return
		if mouseModule.mouseController.isAttached():
			self.AttachItem(0)
			return
		if instantOptions.running:
			return
		cell = instantOptions.cell
		itemVnum = player.GetItemIndex(player.INVENTORY, cell) if cell is not None else 0
		if not itemVnum:
			return
		if app.IsPressed(app.DIK_LALT):
			if app.ENABLE_REFINE_ELEMENT_SYSTEM:
				link = constInfo.GetItemLinkEx(cell, player.INVENTORY)
			else:
				link = player.GetItemLink(player.INVENTORY, cell)
			ime.PasteString(link)
		else:
			itemCount = player.GetItemCount(player.INVENTORY, cell)
			mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, cell, itemVnum, itemCount)

	def UseItem(self, unused):
		"""the right click as on a switchbot slot (SwitchbotItemTab.UseItemSlot): the item back to the
		inventory. It already lies there, so the slot just lets it go (the target is cleared)."""
		if app.SELL == app.GetCursor():
			return
		if constInfo.GET_ITEM_QUESTION_DIALOG_STATUS() == 1:
			return
		if not instantOptions.running:
			self.transfer.Cancel()
			instantOptions.SetTarget(None)
		mouseModule.mouseController.DeattachObject()
		self.OutItem()

	def OverItem(self, unused):
		if instantOptions.cell is not None and player.GetItemIndex(player.INVENTORY, instantOptions.cell):
			tooltip = self.owner.itemTabs[self.owner.GetSelectedSlot()].tooltipItem
			if tooltip:
				tooltip.SetInventoryItem(instantOptions.cell, player.INVENTORY)
				tooltip.ShowToolTip()

	def OutItem(self):
		tooltip = self.owner.itemTabs[self.owner.GetSelectedSlot()].tooltipItem
		if tooltip:
			tooltip.HideToolTip()

	def Open(self):
		self.__SyncLook()
		self.Refresh()
		self.AdjustPosition()
		self.SetTop()
		self.Show()

	def OnUpdate(self):
		transferred = self.transfer.Poll()
		if transferred is not None:
			instantOptions.SetTarget(transferred)
		cell = instantOptions.cell
		vnum = player.GetItemIndex(player.INVENTORY, cell) if cell is not None else 0
		if cell is not None and vnum != self.displayedVnum and self.displayedVnum and not instantOptions.running:
			# the item left its cell (picked up and moved to the switchbot / elsewhere): the slot is empty,
			# like a switchbot slot, and does not show what else comes into that cell later
			instantOptions.SetTarget(None)
			cell, vnum = None, 0
		if vnum != self.displayedVnum:
			self.Refresh()

	def Search(self, index):
		if instantOptions.running or not instantOptions.Catalog():
			return
		if self.searchWindow:
			self.searchWindow.Close()
		self.searchIndex = index
		wnd = SearchListWindow()
		wnd.MakeWindow(340, 260)
		wnd.SetTitleName(localeInfo.SWITCHBOT_SELECT_ATTR)
		wnd.SetAcceptArgsType('KEY_VALUE')
		mouseX, mouseY = wndMgr.GetMousePosition()
		wnd.SetPosition(max(0, min(mouseX - 170, wndMgr.GetScreenWidth() - 340)),
			max(0, min(mouseY - 130, wndMgr.GetScreenHeight() - 260)))
		selected = [kind for kind, value in instantOptions.attrs]
		otherSelected = [kind for position, (kind, value) in enumerate(instantOptions.attrs) if position != index]
		AppendAttributeChoices(wnd, instantOptions.Attributes(), selected, otherSelected)
		wnd.SetAcceptEvent(self.ChooseAttribute)
		wnd.SetTop()
		wnd.Open()
		self.searchWindow = wnd

	def WheelChoices(self, index):
		if not instantOptions.Catalog():
			return []
		return WheelChoices(instantOptions.Attributes(), [kind for kind, value in instantOptions.attrs], index)

	def WheelChoose(self, index, kind, name):
		# the wheel over a bonus field: the same as picking it in the row's picker (an open picker is stale)
		if self.searchWindow:
			self.searchWindow.Close()
		self.searchIndex = index
		self.ChooseAttribute(kind, name)

	def ChooseAttribute(self, kind, name):
		value = instantOptions.Maximum(None, kind)
		instantOptions.SetAttribute(None, 0, self.searchIndex, kind, value)
		self.rows[self.searchIndex].SetAttribute(name, value)

	def Changed(self, unused):
		self.Refresh()

	def OptionsChanged(self):
		self.Refresh()

	def SelectScroll(self, vnum):
		instantOptions.scroll = vnum
		instantOptions.attrs = [(0, 0) for _ in range(5)]
		instantOptions.Request()

	def Refresh(self):
		cell = instantOptions.cell
		vnum = player.GetItemIndex(player.INVENTORY, cell) if cell is not None else 0
		self.displayedVnum = vnum
		if vnum:
			self.itemSlot.SetItemSlot(0, vnum, 0)
		else:
			self.itemSlot.ClearSlot(0)
		self.itemSlot.RefreshSlot()
		self.picker.Refresh(None)
		catalog = instantOptions.Catalog()
		if self.IsShow():
			ShowEmptyOptionsMessage(catalog)
		for index, row in enumerate(self.rows):
			row.RefreshAttributeRow(0, 0, index, keepValueMenu=True)
			if catalog and catalog['values'] and index < catalog['slots']:
				row.Show()
			else:
				row.Hide()
		self.fee.SetText(FormatFee(bonuscatalog.InstantFee()))
		if instantOptions.BuildRequest():
			self.start.Enable()
		else:
			self.start.Disable()
		if self.r1:
			self.r1.Sync()

	def Start(self):
		request = instantOptions.BuildRequest()
		if request:
			instantOptions.Start(request)

	def Close(self):
		self.transfer.Cancel()
		if self.searchWindow:
			self.searchWindow.Close()
			self.searchWindow = None
		self.picker.Close()
		for row in self.rows:
			row.Hide()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		if self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()
		self.Close()
		self.picker.Destroy()
		instantOptions.changed = None
		self.rows = []
		self.owner = None
