import app
import cfg
import localeInfo
import osfInfo
import ui
import uiScriptLocale
import wndMgr


CONFIG_MODE_KEY = "costume_inventory_separate"
CONFIG_POSITION_X_KEY = "costume_inventory_x"
CONFIG_POSITION_Y_KEY = "costume_inventory_y"
POSITION_SAVE_INTERVAL = 0.5
VISIBILITY_IMAGE_PATH = "d:/ymir work/ui/game/crimson_ember/inventory/"


def _GetConfigInteger(key, defaultValue):
	try:
		return int(cfg.Get(cfg.SAVE_OPTION, key, str(defaultValue)))
	except (TypeError, ValueError):
		return defaultValue


def IsSeparateModeEnabled():
	return bool(_GetConfigInteger(CONFIG_MODE_KEY, 0))


def SetSeparateModeEnabled(enabled):
	cfg.Set(cfg.SAVE_OPTION, CONFIG_MODE_KEY, "1" if enabled else "0")


class CostumeInventoryWindow(ui.ScriptWindow):
	VISIBILITY_SPECS = (
		("BodyToolTipButton", 1, "HIDDEN_BODY_COSTUME"),
		("HairToolTipButton", 2, "HIDDEN_HAIR_COSTUME"),
		("WeaponToolTipButton", 3, "HIDDEN_WEAPON_COSTUME"),
		("AcceSkinToolTipButton", 4, "HIDDEN_ACCE_SKIN"),
		("AuraToolTipButton", 6, "HIDDEN_AURA_COSTUME"),
		("ShiningWeaponToolTipButton", 7, "HIDDEN_SHINING_WEAPON"),
		("ShiningArmorToolTipButton", 8, "HIDDEN_SHINING_ARMOR"),
		# no eye on the mount slot, hiding the mount did nothing.
	)

	def __init__(self, inventoryWindow):
		# Window.__init__ calls the virtual Hide() method after registering the
		# native window.  Keep Hide() safe during that base-class construction:
		# the authoritative inventory proxy must only become visible afterwards.
		self.inventoryWindow = None
		self.isLoaded = False
		self.wndCostume = None
		self.visibilityButtons = {}
		self.lastPositionSaveTime = 0.0
		ui.ScriptWindow.__init__(self)
		from _weakref import proxy
		self.inventoryWindow = proxy(inventoryWindow)
		self.__LoadWindow()
		self.Hide()

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def __LoadWindow(self):
		if self.isLoaded:
			return

		loader = ui.PythonScriptLoader()
		try:
			loader.LoadScriptFile(
				self,
				uiScriptLocale.LOCALE_UISCRIPT_PATH +
				"CostumeInventoryWindow.py",
			)
		except:
			import exception
			exception.Abort(
				"CostumeInventoryWindow.LoadWindow.LoadObject")

		try:
			self.GetChild("TitleBar").SetCloseEvent(
				ui.__mem_func__(self.Close))
			self.wndCostume = self.GetChild("CostumeSlot")
		except:
			import exception
			exception.Abort(
				"CostumeInventoryWindow.LoadWindow.BindObject")

		self.wndCostume.SetSelectEmptySlotEvent(
			ui.__mem_func__(self.__SelectEmptySlot))
		self.wndCostume.SetSelectItemSlotEvent(
			ui.__mem_func__(self.__SelectItemSlot))
		self.wndCostume.SetUnselectItemSlotEvent(
			ui.__mem_func__(self.__UseItemSlot))
		self.wndCostume.SetUseSlotEvent(
			ui.__mem_func__(self.__UseItemSlot))
		self.wndCostume.SetOverInItemEvent(
			ui.__mem_func__(self.__OverInItem))
		self.wndCostume.SetOverOutItemEvent(
			ui.__mem_func__(self.__OverOutItem))
		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.wndCostume.SetOverInEvent(
				ui.__mem_func__(self.__OverInItem))
			self.wndCostume.SetOverOutEvent(
				ui.__mem_func__(self.__OverOutItem))

		if app.ENABLE_HIDE_COSTUME_SYSTEM:
			for name, part, stateName in self.VISIBILITY_SPECS:
				button = self.GetChild2(name)
				if not button:
					continue
				button.SetToggleUpEvent(
					ui.__mem_func__(self.__SetCostumeVisibility),
					part, 0)
				button.SetToggleDownEvent(
					ui.__mem_func__(self.__SetCostumeVisibility),
					part, 1)
				self.visibilityButtons[stateName] = button

		self.isLoaded = True
		self.__RestorePersistentPosition()

	def Destroy(self):
		self.__SavePosition(True)
		self.__OverOutItem()
		self.ClearDictionary()
		self.visibilityButtons = {}
		self.wndCostume = None
		self.inventoryWindow = None
		self.isLoaded = False

	def __SelectEmptySlot(self, slotIndex):
		if self.inventoryWindow:
			self.inventoryWindow.SelectEmptySlot(slotIndex)

	def __SelectItemSlot(self, slotIndex):
		if self.inventoryWindow:
			self.inventoryWindow.SelectItemSlot(slotIndex)

	def __UseItemSlot(self, slotIndex):
		if self.inventoryWindow:
			self.inventoryWindow.UseItemSlot(slotIndex)

	def __OverInItem(self, slotIndex):
		if self.inventoryWindow:
			self.inventoryWindow.OverInItem(slotIndex)

	def __OverOutItem(self):
		inventoryWindow = getattr(self, "inventoryWindow", None)
		if inventoryWindow:
			inventoryWindow.OverOutItem()

	def __SetCostumeVisibility(self, part, hidden):
		if self.inventoryWindow:
			self.inventoryWindow.VisibleCostume(part, hidden)

	def __ApplyVisibilityButton(self, button, hidden):
		if hidden:
			button.SetToolTipText(getattr(
				localeInfo, "SHOW_COSTUME", "Show costume"))
			button.SetUpVisual(
				VISIBILITY_IMAGE_PATH + "visibility_selected.png")
			button.SetOverVisual(
				VISIBILITY_IMAGE_PATH + "visibility_selected.png")
			button.SetDownVisual(
				VISIBILITY_IMAGE_PATH + "visibility_selected.png")
		else:
			button.SetToolTipText(getattr(
				localeInfo, "HIDE_COSTUME", "Hide costume"))
			button.SetUpVisual(
				VISIBILITY_IMAGE_PATH + "visibility_normal.png")
			button.SetOverVisual(
				VISIBILITY_IMAGE_PATH + "visibility_hover.png")
			button.SetDownVisual(
				VISIBILITY_IMAGE_PATH + "visibility_pressed.png")

	def RefreshVisibleCostume(self):
		if not app.ENABLE_HIDE_COSTUME_SYSTEM:
			return
		for stateName, button in self.visibilityButtons.items():
			self.__ApplyVisibilityButton(
				button, bool(getattr(osfInfo, stateName, False)))

	def RefreshItemSlot(self):
		if self.inventoryWindow and self.wndCostume:
			self.inventoryWindow.RefreshCostumeSlotWindow(
				self.wndCostume)

	def Refresh(self):
		self.RefreshItemSlot()
		self.RefreshVisibleCostume()

	def Open(self):
		self.Show()

	def Show(self):
		self.__LoadWindow()
		self.Refresh()
		ui.ScriptWindow.Show(self)
		self.SetTop()

	def Toggle(self):
		if self.IsShow():
			self.Close()
		else:
			self.Open()

	def Hide(self):
		self.__OverOutItem()
		self.__SavePosition(True)
		wndMgr.Hide(self.hWnd)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def __ClampPosition(self, x, y):
		screenWidth = max(0, int(wndMgr.GetScreenWidth()))
		screenHeight = max(0, int(wndMgr.GetScreenHeight()))
		maxX = max(0, screenWidth - int(self.GetWidth()))
		maxY = max(0, screenHeight - int(self.GetHeight()))
		return (
			max(0, min(int(x), maxX)),
			max(0, min(int(y), maxY)),
		)

	def __RestorePersistentPosition(self):
		x = _GetConfigInteger(CONFIG_POSITION_X_KEY, -1)
		y = _GetConfigInteger(CONFIG_POSITION_Y_KEY, -1)
		if x < 0 or y < 0:
			x, y = self.GetGlobalPosition()
		x, y = self.__ClampPosition(x, y)
		self.SetPosition(x, y)

	def __SavePosition(self, force=False):
		if not getattr(self, "isLoaded", False) or not getattr(
				self, "hWnd", None):
			return
		now = app.GetTime()
		if not force and now - self.lastPositionSaveTime < \
				POSITION_SAVE_INTERVAL:
			return
		x, y = self.GetGlobalPosition()
		x, y = self.__ClampPosition(x, y)
		cfg.Set(cfg.SAVE_OPTION, CONFIG_POSITION_X_KEY, str(x))
		cfg.Set(cfg.SAVE_OPTION, CONFIG_POSITION_Y_KEY, str(y))
		self.lastPositionSaveTime = now

	def OnMoveWindow(self, x, y):
		self.__SavePosition()

	if app.ENABLE_WINDOW_RESIZE:
		def OnResize(self):
			x, y = self.GetGlobalPosition()
			x, y = self.__ClampPosition(x, y)
			self.SetPosition(x, y)
			self.__SavePosition(True)
