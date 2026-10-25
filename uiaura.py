# -*- coding: utf-8 -*-
import app
import snd
import chat
import item
import net
import player
import wndMgr
import ui
import uiCommon
import localeInfo
import mouseModule
import osfInfo
import auraprogression

USE_AURA_WINDOW_LIMIT_RANGE = 1000

def _NeedYang(amount):
	"""The yang an aura upgrade needs: the one R1 yang price of the client ("1.000.000 Yang", root/uir1price.py,
	); "Starý vzhled" keeps localeInfo.AURA_TOOLTIP_NEED_YANG ("1000000 Yangů")."""
	try:
		import uir1price
		return uir1price.Text(amount, lambda: localeInfo.AURA_TOOLTIP_NEED_YANG % (amount))
	except Exception:
		return localeInfo.AURA_TOOLTIP_NEED_YANG % (amount)

if app.WJ_ENABLE_TRADABLE_ICON:
	INVENTORY_PAGE_SIZE = player.INVENTORY_PAGE_SIZE
	if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
		SPECIAL_INVENTORY_PAGE_SIZE = player.SPECIAL_INVENTORY_PAGE_SIZE

class AuraWindow(ui.ScriptWindow):
	def __init__(self):
		if not app.ENABLE_AURA_SYSTEM:
			import exception
			exception.Abort("What do you do?")
			return

		ui.ScriptWindow.__init__(self)
		import uiconfirm
		uiconfirm.Bind(self, 'AcceptButton', child=True)
		self.Initialize()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.ClearDictionary()

		if self.questionDialog:
			self.questionDialog.Close()
		self.Initialize()

	def Initialize(self):
		self.auraRefineWindowType = player.AURA_WINDOW_TYPE_MAX
		self.isLoaded = 0
		self.toolTipItem = None
		self.questionDialog = None
		self.xAuraWindowStart = 0
		self.yAuraWindowStart = 0
		
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = False		
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.interface = None
			self.inven = None
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				self.invenSpecial = None

			self.ItemListIdx = []

	def __LoadWindow(self, type):
		if type == player.AURA_WINDOW_TYPE_GROWTH:
			return

		pyScriptFileNames = {
			player.AURA_WINDOW_TYPE_ABSORB	: "UIScript/aura_absorbwindow.py",
			player.AURA_WINDOW_TYPE_GROWTH	: "UIScript/aura_levelupwindow.py",
			player.AURA_WINDOW_TYPE_EVOLVE	: "UIScript/aura_levelupwindow.py"
		}

		titleNames = {
			player.AURA_WINDOW_TYPE_ABSORB	: localeInfo.AURA_TITLE_ABSORB,
			player.AURA_WINDOW_TYPE_GROWTH	: localeInfo.AURA_TITLE_GROWTH,
			player.AURA_WINDOW_TYPE_EVOLVE	: localeInfo.AURA_TITLE_EVOLUTION
		}

		if type in pyScriptFileNames:
			try:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, pyScriptFileNames[type])
			except:
				import exception
				exception.Abort("AuraWindow.__LoadWindow.LoadScript")
		else:
			import exception
			exception.Abort("AuraWindow.__LoadWindow.InvalidWindow[%d]" % (type))
			return

		try:
			wndItem = self.GetChild("AuraSlot")
			self.GetChild("CancelButton").SetEvent(ui.__mem_func__(self.Cancel))
			self.GetChild("AcceptButton").SetEvent(ui.__mem_func__(self.Accept))
			self.GetChild("TitleBar").SetCloseEvent(ui.__mem_func__(self.Cancel))
			self.GetChild("TitleName").SetText(titleNames[type])
		except:
			import exception
			exception.Abort("AuraWindow.__LoadWindow.LoadBindGenerals")

		self.AuraToolTip1 = self.GetChild2("AuraToolTip1")
		self.AuraToolTip2 = self.GetChild2("AuraToolTip2")
		self.AuraToolTip3 = self.GetChild2("AuraToolTip3")
		self.AuraToolTip4 = self.GetChild2("AuraToolTip4")
		self.AuraToolTip5 = self.GetChild2("AuraToolTip5")
		self.AuraToolTip6 = self.GetChild2("AuraToolTip6")

		wndItem.SetOverInItemEvent(ui.__mem_func__(self.OverInItem))
		wndItem.SetOverOutItemEvent(ui.__mem_func__(self.OverOutItem))
		wndItem.SetUnselectItemSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetUseSlotEvent(ui.__mem_func__(self.UseItemSlot))
		wndItem.SetSelectEmptySlotEvent(ui.__mem_func__(self.SelectEmptySlot))
		wndItem.SetSelectItemSlotEvent(ui.__mem_func__(self.SelectItemSlot))
		wndItem.Show()
		self.wndItem = wndItem

		# R1 look (root/uir1theowahdan.py, inside the shared R1 frame of root/uir1frame.py); "Starý vzhled" or a
		# failure keeps the original window
		try:
			import uir1theowahdan
			uir1theowahdan.Dress(self, "aura_absorb" if type == player.AURA_WINDOW_TYPE_ABSORB else "aura_levelup")
		except Exception:
			pass

	def ClearAuraLevelUpWindowToolTip(self):
		if self.auraRefineWindowType == player.AURA_WINDOW_TYPE_GROWTH or self.auraRefineWindowType == player.AURA_WINDOW_TYPE_EVOLVE:
			self.AuraToolTip1.SetText("")
			self.AuraToolTip2.SetText("")
			self.AuraToolTip3.SetText("")
			self.AuraToolTip4.SetText("")
			self.AuraToolTip5.SetText("")
			self.AuraToolTip6.SetText("")

	def CloseWindow(self):
		wndMgr.OnceIgnoreMouseLeftButtonUpEvent()

		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
		if self.questionDialog:
			self.questionDialog.Close()

		self.ClearAuraLevelUpWindowToolTip()
		osfInfo.AURA_ATTACHED_LIST_SLOT = {}
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = None
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()
		if app.ENABLE_ANIMATED_WINDOW:
			if self.bClosed == False:
				ui.ScriptWindow.Hide(self)
		else:
			ui.ScriptWindow.Hide(self)	
			
		if app.ENABLE_ANIMATED_WINDOW:
			self.bClosed = True			
			
		self.isLoaded = 0

	def Open(self, type):
		if self.isLoaded == 0:
			self.isLoaded = 1
			self.__LoadWindow(type)
			self.auraRefineWindowType = type
			self.SetCenterPosition()
			self.SetTop()
			osfInfo.AURA_ATTACHED_LIST_SLOT = {}
			ui.ScriptWindow.Show(self)		
			
			if app.WJ_ENABLE_TRADABLE_ICON:
				self.ItemListIdx = []
				if self.interface:
					if type == player.AURA_WINDOW_TYPE_GROWTH:
						self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_REFINE)
					elif type == player.AURA_WINDOW_TYPE_EVOLVE:
						self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_EVOLVE)
					else:
						self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_ABSORB)
						
					self.interface.RefreshMarkInventoryBag()
	
			if app.ENABLE_ANIMATED_WINDOW: 	
				self.bClosed = False	
	
			(self.xAuraWindowStart, self.yAuraWindowStart, z) = player.GetMainCharacterPosition()

	def Accept(self):
		if player.IsAuraRefineWindowEmpty():
			chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_ITEM_NEED_REGISTER)
			return

		net.SendAuraRefineAccept(self.auraRefineWindowType)

	def Cancel(self):
		if app.WJ_ENABLE_TRADABLE_ICON:
			if self.interface:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_NONE)
				self.interface.RefreshMarkInventoryBag()

			self.ItemListIdx = None
		net.SendAuraRefineCancel()

	def SetItemToolTip(self, itemTooltip):
		self.toolTipItem = itemTooltip

	def __ShowToolTip(self, slotIndex):
		if self.toolTipItem:
			self.toolTipItem.SetAuraWindowItem(slotIndex)

	def OverInItem(self, slotIndex):
		self.wndItem.SetUsableItem(False)
		self.__ShowToolTip(slotIndex)

	def OverOutItem(self):
		self.wndItem.SetUsableItem(False)
		if self.toolTipItem:
			self.toolTipItem.HideToolTip()
			
	def AddFastItem(self, itemSlotIndex):
		selectedItemVNum = player.GetItemIndex(itemSlotIndex)
		itemCount = player.GetItemCount(itemSlotIndex)
		
		item.SelectItem(selectedItemVNum)
		itemType = item.GetItemType()
		itemSubType = item.GetItemSubType()	

		if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_AURA:
			if player.GetAuraItemID(0) == 0:
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, itemCount)
				self.SelectEmptySlot(0)
		else:
			if player.GetAuraItemID(1) == 0:
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_INVENTORY, itemSlotIndex, selectedItemVNum, itemCount)
				self.SelectEmptySlot(1)

	def SelectEmptySlot(self, selectedSlotPos):
		if selectedSlotPos == (player.AURA_SLOT_MAX - 1):
			return

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
			attachedSlotWindow = player.SlotTypeToInvenType(attachedSlotType)

			itemVnum = player.GetItemIndex(attachedSlotWindow, attachedSlotPos)
			if app.ENABLE_EXTEND_INVEN_SYSTEM:
				itemType = player.GetItemTypeBySlot(attachedSlotWindow, attachedSlotPos)
				itemSubType = player.GetItemSubTypeBySlot(attachedSlotWindow, attachedSlotPos)
				if attachedSlotWindow == player.EQUIPMENT:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EQUIPITEM)
					return
			else:
				item.SelectItem(itemVnum)
				itemType = item.GetItemType()
				itemSubType = item.GetItemSubType()
				if attachedSlotPos >= player.EQUIPMENT_SLOT_START:
					chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EQUIPITEM)
					return

			if player.SLOT_TYPE_AURA != attachedSlotType:
				if player.RESERVED_WINDOW == attachedSlotWindow:
					return

				possablecheckin = False
				if player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_ABSORB:
					if selectedSlotPos == player.AURA_SLOT_MAIN:
						if itemType == item.ITEM_TYPE_COSTUME:
							if itemSubType == item.COSTUME_TYPE_AURA:
								if player.GetItemMetinSocket(attachedSlotWindow, attachedSlotPos, player.ITEM_SOCKET_AURA_DRAIN_ITEM_VNUM) == 0:
									possablecheckin = True
								else:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
									return
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
								return
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
							return

					elif selectedSlotPos == player.AURA_SLOT_SUB:
						if item.IsWeddingItem(itemVnum) == 1:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
							return

						if itemType == item.ITEM_TYPE_ARMOR:
							if itemSubType in [item.ARMOR_SHIELD, item.ARMOR_WRIST, item.ARMOR_NECK, item.ARMOR_EAR]:
								if player.FindUsingAuraSlot(player.AURA_SLOT_MAIN) != player.NPOS():
									possablecheckin = True
								else:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
									return
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_REFINEITEM)
								return
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_ABSORBITEM)
							return

				elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_GROWTH:
					if selectedSlotPos == player.AURA_SLOT_MAIN:
						if itemType == item.ITEM_TYPE_COSTUME:
							if itemSubType == item.COSTUME_TYPE_AURA:
								socketLevelValue = player.GetItemMetinSocket(attachedSlotWindow, attachedSlotPos, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
								curLevel = (socketLevelValue // 100000) - 1000
								curExp = socketLevelValue % 100000;
								if curLevel >= player.AURA_MAX_LEVEL:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_MAX_LEVEL)
									return

								if curExp >= player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_NEED_EXP):
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_GROWTHITEM)
									return

								possablecheckin = True
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
								return
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
							return

					elif selectedSlotPos == player.AURA_SLOT_SUB:
						if player.FindUsingAuraSlot(player.AURA_SLOT_MAIN) != player.NPOS():
							if itemType == item.ITEM_TYPE_RESOURCE:
								if itemSubType == item.RESOURCE_AURA:
									possablecheckin = True
								else:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURARESOURCE)
									return
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURARESOURCE)
								return
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
							return

				elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_EVOLVE:
					if selectedSlotPos == player.AURA_SLOT_MAIN:
						if itemType == item.ITEM_TYPE_COSTUME:
							if itemSubType == item.COSTUME_TYPE_AURA:
								socketLevelValue = player.GetItemMetinSocket(attachedSlotWindow, attachedSlotPos, player.ITEM_SOCKET_AURA_CURRENT_LEVEL)
								if auraprogression.Grade(itemVnum) == 6:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_MAX_LEVEL)
									return

								if not auraprogression.IsReadyToEvolve(itemVnum, socketLevelValue):
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEM)
									return

								possablecheckin = True
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
								return
						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_AURAITEM)
							return

					elif selectedSlotPos == player.AURA_SLOT_SUB:
						Cell = player.FindUsingAuraSlot(player.AURA_SLOT_MAIN)
						if Cell != player.NPOS():
							auraVnum = player.GetItemIndex(Cell[0], Cell[1])
							gradeLevel = auraprogression.GradeLevel(auraVnum)
							if itemVnum == player.GetAuraRefineInfo(gradeLevel, player.AURA_REFINE_INFO_MATERIAL_VNUM):
								if player.GetItemCount(attachedSlotWindow, attachedSlotPos) >= player.GetAuraRefineInfo(gradeLevel, player.AURA_REFINE_INFO_MATERIAL_COUNT):
									possablecheckin = True
								else:
									chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEMCOUNT)
									return
							else:
								chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_EVOLUTION_ITEM)
								return

						else:
							chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_POSSIBLE_REGISTER_AURAITEM)
							return

				if possablecheckin:
					if app.ENABLE_SOUL_BIND_SYSTEM and player.GetItemSealDate(attachedSlotWindow, attachedSlotPos):
						chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.AURA_IMPOSSIBLE_SEALITEM)
						return

					if player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_ABSORB:
						if selectedSlotPos == player.AURA_SLOT_SUB:
							questionDialog = uiCommon.QuestionDialog()
							questionDialog.SetText(localeInfo.AURA_NOTICE_DEL_ABSORDITEM)
							questionDialog.SetAcceptEvent(ui.__mem_func__(self.OnAuraAcceptEvent))
							questionDialog.SetCancelEvent(self.OnAuraCloseEvent)
							questionDialog.Open()
							questionDialog.attachedSlotWindow = attachedSlotWindow
							questionDialog.attachedSlotPos = attachedSlotPos
							questionDialog.selectedSlotPos = selectedSlotPos
							self.questionDialog = questionDialog
						else:
							osfInfo.AURA_ATTACHED_LIST_SLOT[selectedSlotPos] = attachedSlotPos
							net.SendAuraRefineCheckIn(attachedSlotWindow, attachedSlotPos, player.AURA_REFINE, selectedSlotPos, self.auraRefineWindowType)

					elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_GROWTH:
						osfInfo.AURA_ATTACHED_LIST_SLOT[selectedSlotPos] = attachedSlotPos
						net.SendAuraRefineCheckIn(attachedSlotWindow, attachedSlotPos, player.AURA_REFINE, selectedSlotPos, self.auraRefineWindowType)

					elif player.GetAuraRefineWindowType() == player.AURA_WINDOW_TYPE_EVOLVE:
						osfInfo.AURA_ATTACHED_LIST_SLOT[selectedSlotPos] = attachedSlotPos
						net.SendAuraRefineCheckIn(attachedSlotWindow, attachedSlotPos, player.AURA_REFINE, selectedSlotPos, self.auraRefineWindowType)

					snd.PlaySound("sound/ui/drop.wav")

			mouseModule.mouseController.DeattachObject()

	def OnAuraAcceptEvent(self):
		osfInfo.AURA_ATTACHED_LIST_SLOT[self.questionDialog.selectedSlotPos] = self.questionDialog.attachedSlotPos
		net.SendAuraRefineCheckIn(self.questionDialog.attachedSlotWindow, self.questionDialog.attachedSlotPos, player.AURA_REFINE, self.questionDialog.selectedSlotPos, self.auraRefineWindowType)
		self.questionDialog.Close()
		self.questionDialog = None

	def OnAuraCloseEvent(self):
		self.questionDialog.Close()
		self.questionDialog = None

	def UseItemSlot(self, selectedSlotPos):
		if selectedSlotPos == (player.AURA_SLOT_MAX - 1):
			return

		mouseModule.mouseController.DeattachObject()
		osfInfo.AURA_ATTACHED_LIST_SLOT.pop(selectedSlotPos, None)
		net.SendAuraRefineCheckOut(selectedSlotPos, self.auraRefineWindowType)

	def SelectItemSlot(self, selectedSlotPos):
		if selectedSlotPos == (player.AURA_SLOT_MAX - 1):
			return

		if mouseModule.mouseController.isAttached():
			attachedSlotType = mouseModule.mouseController.GetAttachedType()
			if app.ENABLE_EXTEND_INVEN_SYSTEM:
				validSlotTypes = [player.SLOT_TYPE_INVENTORY, player.SLOT_TYPE_DRAGON_SOUL_INVENTORY, player.SLOT_TYPE_BELT_INVENTORY]
				if attachedSlotType in validSlotTypes:
					snd.PlaySound("sound/ui/drop.wav")
			else:
				if player.SLOT_TYPE_INVENTORY == attachedSlotType:
					attachedSlotPos = mouseModule.mouseController.GetAttachedSlotNumber()
					snd.PlaySound("sound/ui/drop.wav")

			mouseModule.mouseController.DeattachObject()

		else:
			curCursorNum = app.GetCursor()
			if app.SELL == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SAFEBOX_SELL_DISABLE_SAFEITEM)
			elif app.BUY == curCursorNum:
				chat.AppendChat(chat.CHAT_TYPE_INFO, localeInfo.SHOP_BUY_INFO)
			else:
				selectedItemID = player.GetAuraItemID(selectedSlotPos)
				mouseModule.mouseController.AttachObject(self, player.SLOT_TYPE_AURA, player.AURA_REFINE, selectedSlotPos, selectedItemID)
				snd.PlaySound("sound/ui/pick.wav")

	def RefreshAuraWindow(self):
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.ItemListIdx = []
			
		getAuraItem = player.GetAuraItemID
		getAuraCount = player.GetAuraItemCount
		setAuraItem = self.wndItem.SetItemSlot
		AuraItemSize = player.GetAuraCurrentItemSlotCount()
		self.ClearAuraLevelUpWindowToolTip()
		[self.wndItem.ClearSlot(i) for i in range(player.AURA_SLOT_MAX)]
		
		if app.WJ_ENABLE_TRADABLE_ICON:
			if AuraItemSize < 1:
				osfInfo.AURA_ATTACHED_LIST_SLOT = {}
				self.inven.RefreshBagSlotWindow()
				self.invenSpecial.RefreshBagSlotWindow()
		
		for i in range(AuraItemSize):
			itemCount = getAuraCount(i)
			if 1 == itemCount:
				itemCount = 0
			setAuraItem(i, getAuraItem(i), itemCount)
			
			if app.WJ_ENABLE_TRADABLE_ICON:
				if i < 2:
					if getAuraItem(i) != 0:
						attachedInvSlot = osfInfo.AURA_ATTACHED_LIST_SLOT.get(i)
						if attachedInvSlot is not None:
							self.ItemListIdx.append(attachedInvSlot)
					else:
						osfInfo.AURA_ATTACHED_LIST_SLOT.pop(i, None)

			if self.auraRefineWindowType == player.AURA_WINDOW_TYPE_GROWTH:
				if i == player.AURA_SLOT_MAIN:
					if getAuraItem(i) != 0:
						curLevel = player.GetAuraRefineInfoLevel(player.AURA_REFINE_INFO_SLOT_CURRENT)
						curStep = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_STEP)
						curDrainPct = 1.0 * curLevel / 10.
						curExpPct = player.GetAuraRefineInfoExpPer(player.AURA_REFINE_INFO_SLOT_CURRENT)

						self.AuraToolTip1.SetText(localeInfo.AURA_TOOLTIP_NOW)
						self.AuraToolTip2.SetText(localeInfo.AURA_TOOLTIP_LEVEL % (curLevel, curStep, curDrainPct))
						self.AuraToolTip3.SetText(localeInfo.AURA_TOOLTIP_EXP % (curExpPct))

				if i == player.AURA_SLOT_SUB:
					if getAuraItem(i) != 0:
						nextLevel = player.GetAuraRefineInfoLevel(player.AURA_REFINE_INFO_SLOT_NEXT)
						nextStep = player.GetAuraRefineInfo(nextLevel, player.AURA_REFINE_INFO_STEP)
						nextDrainPct = auraprogression.AbsorptionPercentForGrade(nextStep)
						nextExpPct = player.GetAuraRefineInfoExpPer(player.AURA_REFINE_INFO_SLOT_NEXT)

						self.AuraToolTip4.SetText(localeInfo.AURA_TOOLTIP_NEXT)
						self.AuraToolTip5.SetText(localeInfo.AURA_TOOLTIP_LEVEL % (nextLevel, curStep, nextDrainPct))
						self.AuraToolTip6.SetText(localeInfo.AURA_TOOLTIP_EXP % (nextExpPct))

			if self.auraRefineWindowType == player.AURA_WINDOW_TYPE_EVOLVE:
				if i == player.AURA_SLOT_MAIN:
					if getAuraItem(i) != 0:
						curLevel = player.GetAuraRefineInfoLevel(player.AURA_REFINE_INFO_SLOT_CURRENT)
						needMaterialVnum = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_MATERIAL_VNUM)
						needMaterialCount = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_MATERIAL_COUNT)
						needGold = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_NEED_GOLD)
						evolPer = player.GetAuraRefineInfo(curLevel, player.AURA_REFINE_INFO_EVOLVE_PCT)

						nextLevel = player.GetAuraRefineInfoLevel(player.AURA_REFINE_INFO_SLOT_EVOLVED)
						nextStep = player.GetAuraRefineInfo(nextLevel, player.AURA_REFINE_INFO_STEP)
						nextDrainPct = auraprogression.AbsorptionPercentForGrade(nextStep)

						self.AuraToolTip1.SetText(localeInfo.AURA_TOOLTIP_NEXT)
						self.AuraToolTip2.SetText(localeInfo.AURA_TOOLTIP_LEVEL % (nextLevel, nextStep, nextDrainPct))
						self.AuraToolTip3.SetText(localeInfo.AURA_TOOLTIP_EVOLUTION_PER % (evolPer))

						self.AuraToolTip4.SetText(localeInfo.AURA_TOOLTIP_RESOURCE)
						# "Name  12 / 25", the count green / red (root/ownedcount.py)
						import ownedcount
						self.AuraToolTip5.SetText("%s  %s" % (item.GetItemNameByVnum(needMaterialVnum),
							ownedcount.Tagged(ownedcount.Owned(needMaterialVnum), needMaterialCount)))
						self.AuraToolTip6.SetText(_NeedYang(needGold))

		self.wndItem.RefreshSlot()

	def OnUpdate(self):
		(x, y, z) = player.GetMainCharacterPosition()
		if abs(x - self.xAuraWindowStart) > USE_AURA_WINDOW_LIMIT_RANGE or abs(y - self.yAuraWindowStart) > USE_AURA_WINDOW_LIMIT_RANGE:
			if app.ENABLE_ANIMATED_WINDOW:
				if (self.bClosed != True):
					self.Cancel()
				else:
					self.Cancel()
			
		if app.WJ_ENABLE_TRADABLE_ICON:
			self.AuraItemMouseEvent()

	def OnPressEscapeKey(self):
		self.Cancel()
		return True
		
	if app.WJ_ENABLE_TRADABLE_ICON:
		def BindInterface(self, interface):
			from _weakref import proxy
			self.interface = proxy(interface)

		def SetInven(self, inven):
			self.inven = inven

		if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
			def SetSpecialInven(self, invenSpecial):
				self.invenSpecial = invenSpecial

		def CantTradableItem(self, slotIndex):
			itemIndex = player.GetItemIndex(slotIndex)

			if itemIndex:
				if app.ENABLE_SOUL_BIND_SYSTEM:
					if player.GetItemSealDate(player.INVENTORY, slotIndex) == -1 or player.GetItemSealDate(player.INVENTORY, slotIndex) > 0: #봉인아이템 걸러냄.
						return True

				if not item.IsPossibleChangeLook(itemIndex):
					return True

			return False
			
		def CantUseItem(self, slotIndex):
			#return True = cannot use this item
			#return False = you can use it
			itemVnum = player.GetItemIndex(slotIndex)
			
			item.SelectItem(itemVnum)
			itemType = item.GetItemType()
			itemSubType = item.GetItemSubType()
			
			if itemType == item.ITEM_TYPE_COSTUME and itemSubType == item.COSTUME_TYPE_AURA:
				return False
			
			if self.auraRefineWindowType == player.AURA_WINDOW_TYPE_GROWTH:
				if itemVnum in [49995]:
					return False
				
			elif self.auraRefineWindowType == player.AURA_WINDOW_TYPE_EVOLVE:
				evolveListVnum = [49996, 49997, 49998, 49999, 50000] #Edit here vnums needed for evolve aura
				
				if itemVnum in evolveListVnum:
					return False
				
			else: #absorb
			
				#check limit 120lv
				for i in range(item.LIMIT_MAX_NUM):
					(limitType, limitValue) = item.GetLimit(i)

					if item.LIMIT_LEVEL == limitType:
						if limitValue == 120:
							return True
				#check limit 120lv
				
				allowedAbsorbList = [item.ARMOR_SHIELD, item.ARMOR_EAR, item.ARMOR_NECK, item.ARMOR_WRIST]
				if itemType == item.ITEM_TYPE_ARMOR and itemSubType in allowedAbsorbList:
					return False
					
			return True

		def OnTop(self):
			# self.tooltipitem.SetTop()
			if not self.interface:
				return

			if self.auraRefineWindowType == player.AURA_WINDOW_TYPE_GROWTH:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_REFINE)
			elif self.auraRefineWindowType == player.AURA_WINDOW_TYPE_EVOLVE:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_EVOLVE)
			else:
				self.interface.SetOnTopWindow(player.ON_TOP_WND_AURA_ABSORB)

			self.interface.RefreshMarkInventoryBag()

		def AuraItemMouseEvent(self):
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				if not self.inven or not self.invenSpecial:
					return
			else:
				if not self.inven:
					return

			if not self.ItemListIdx:
				return

			page = self.inven.GetInventoryPageIndex() # range 0 ~ 1
			if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
				special_page = self.invenSpecial.GetInventoryPageIndex()

			if self.ItemListIdx:
				for i in self.ItemListIdx:
					if (page * INVENTORY_PAGE_SIZE) <= i < ((page + 1) * INVENTORY_PAGE_SIZE): # range 0 ~ 44, 45 ~ 89
						lock_idx = i - (page * INVENTORY_PAGE_SIZE)
						self.inven.wndItem.SetCantMouseEventSlot(lock_idx)

					if app.ENABLE_SPECIAL_INVENTORY_SYSTEM:
						if self.invenSpecial.GetInventoryType() == 0:
							if (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SKILL_BOOK_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SKILL_BOOK_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 1:
							if (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.UPGRADE_ITEMS_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 2:
							if (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.STONE_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.STONE_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 3:
							if (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.GIFT_BOX_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.GIFT_BOX_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 4:
							if (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.SWITCH_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.SWITCH_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)

						if self.invenSpecial.GetInventoryType() == 5:
							if (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE)) <= i < (item.COSTUME_INVENTORY_SLOT_START + (((special_page + 1) * SPECIAL_INVENTORY_PAGE_SIZE))):
								lock_idx = i - (item.COSTUME_INVENTORY_SLOT_START + (special_page * SPECIAL_INVENTORY_PAGE_SIZE))
								self.invenSpecial.wndItem.SetCantMouseEventSlot(lock_idx)
