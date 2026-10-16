import ui
import nonplayer
import uiOfflineShop
import wndMgr
import renderTarget
import uiScriptLocale
import osfInfo
import app
import localeInfo

class MyShopDecorationWindow(ui.ScriptWindow):
	SHOP_NPCS = (30000, 30001, 30002, 30003, 30004, 30005, 30006, 30007, 30008)
	ADVERTISMENT_BOARDS = {
			"default": uiScriptLocale.OFFLINE_SHOP_DECORATION_1,
			"fire": uiScriptLocale.OFFLINE_SHOP_DECORATION_2,
			"ice": uiScriptLocale.OFFLINE_SHOP_DECORATION_3,
			"paper": uiScriptLocale.OFFLINE_SHOP_DECORATION_4,
			"ribon": uiScriptLocale.OFFLINE_SHOP_DECORATION_5,
			"wing": uiScriptLocale.OFFLINE_SHOP_DECORATION_6
		}
		
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		
		self.__selectedNpc = 0
		self.__selectedAdvertismentBoard = 0
		
		self.__selectedSkinID = 0
		self.__selectedBannerID = 0
		
		ui.PythonScriptLoader().LoadScriptFile(self, "uiscript/myshopdecorationwindow.py")
		
		self.__leftBoard = self.GetChild("LeftBoard")
		self.__scrollBar = self.GetChild("ScrollBar")
		
		self.__modelName = self.GetChild("ModelName")
		self.__boardName = self.GetChild("BoardName")
		self.__renderTarget = self.GetChild("RenderTarget")
		
		self.__nextButton = self.GetChild("NextButton")
		self.__cancelButton = self.GetChild("CancelButton")
		self.__prevButton = self.GetChild("PrevButton")
		self.__completeButton = self.GetChild("CompleteButton")
		
		self.__advertismentBoard = uiOfflineShop.AdvertismentBoard("default")
		self.__advertismentBoard.SetWidth(170)
		self.__advertismentBoard.SetParent(self.__renderTarget)
		self.__advertismentBoard.SetWindowHorizontalAlignCenter()
		self.__advertismentBoard.SetPosition(0, 10)
		self.__advertismentBoard.Hide()
				
		self.__modelButtons = []
		self.__bannerButtons = []
		
		self.__modelInfoButtons = []
		self.__bannerInfoButtons = []
		
		self.__page = 0
		
		self.lastShopSkinDeco = osfInfo.SHOP_SKIN_VALUE
		self.lastShopBannerDeco = osfInfo.SHOP_BANNER_VALUE
		
		shopNpcs = []
		i=0
		for race in self.SHOP_NPCS:
			name = nonplayer.GetMonsterName(race)
			
			button = ui.RadioButton()
			button.SetParent(self.__leftBoard)
			if i == 0 or osfInfo.SHOP_SKIN_UNLOCKED[i-1] == True:
				button.SetUpVisual("d:/ymir work/ui/game/myshop_deco/select_btn_01.sub")
				button.SetOverVisual("d:/ymir work/ui/game/myshop_deco/select_btn_02.sub")
				button.SetDownVisual("d:/ymir work/ui/game/myshop_deco/select_btn_03.sub")
				button.SetText(name)
			else:
				button.SetUpVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_01.tga")
				button.SetOverVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
				button.SetDownVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
				button.SetText("")
				
			button.SetWindowHorizontalAlignCenter()
			button.SetPosition(0, 6 + len(shopNpcs) * 26)
			button.Show()
			
			shopNpcs.append((button, lambda x=race, x2=i-1: self.__SelectShopNPC(x, x2), None))
			self.__modelButtons.append(button)
			i=i+1
					
		advertismentBoards = []
		i=0
		for type, name in self.ADVERTISMENT_BOARDS.items():
		
			button = ui.RadioButton()
			button.SetParent(self.__leftBoard)
			
			if i == 0 or osfInfo.SHOP_BANNER_UNLOCKED[i-1] == True:
				button.SetUpVisual("d:/ymir work/ui/game/myshop_deco/select_btn_01.sub")
				button.SetOverVisual("d:/ymir work/ui/game/myshop_deco/select_btn_02.sub")
				button.SetDownVisual("d:/ymir work/ui/game/myshop_deco/select_btn_03.sub")
				button.SetText(name)
			else:
				button.SetUpVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_01.tga")
				button.SetOverVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
				button.SetDownVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
				button.SetText("")
			
			button.SetWindowHorizontalAlignCenter()
			button.SetPosition(0, 6 + len(advertismentBoards) * 26)
			button.Show()
			
			advertismentBoards.append((button, lambda x=type, x2=i-1: self.__SelectAdvertismentBoard(x, x2), None))
			self.__bannerButtons.append(button)
			i=i+1
			
		##
		for i in range(len(self.__modelButtons)-1):
			timeButton = ui.Button()
			timeButton.SetParent(self.__leftBoard)
			timeButton.SetUpVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetOverVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetDownVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetPosition(142, 36 + i * 26)
			timeButton.SetText("")
			timeButton.SetToolTipText("This shit will expire in xxxxx", -70, -12)
			timeButton.Show()
			self.__modelInfoButtons.append(timeButton)
		##
		
		##
		for i in range(len(self.__bannerButtons)-1):
			timeButton = ui.Button()
			timeButton.SetParent(self.__leftBoard)
			timeButton.SetUpVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetOverVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetDownVisual("d:/ymir work/ui/game/offline_shop/shop_btn_q_mark_1.png")
			timeButton.SetPosition(142, 36 + i * 26)
			timeButton.SetText("")
			timeButton.SetToolTipText("This shit will expire in xxxxx", -70, -12)
			timeButton.Show()
			self.__bannerInfoButtons.append(timeButton)
		##
		
		self.__npcSelection = ui.RadioButtonGroup.Create(shopNpcs)
		self.__advertismentBoardSelection = ui.RadioButtonGroup.Create(advertismentBoards)
		
		self.__scrollBar.Hide()
		
		self.__cancelButton.SetEvent(self.Hide)
		self.GetChild("MyShopDecoBoard").SetCloseEvent(self.Hide)
		self.__nextButton.SetEvent(lambda: self.__SetPage(1))
		self.__prevButton.SetEvent(lambda: self.__SetPage(0))
		
		# self.__nextButton.Enable()
		# self.__completeButton.Enable()
		
		self.__SetPage(0)
	
	def __del__(self):
		ui.ScriptWindow.__del__(self)
	
	def __SetPage(self, page):
		self.__page = page
		if page == 0:
			self.__nextButton.Show()
			self.__cancelButton.Show()
			self.__prevButton.Hide()
			self.__completeButton.Hide()
			
			self.__modelName.Show()
			self.__boardName.Hide()
			
			self.__npcSelection.Show()
			self.__advertismentBoardSelection.Hide()
			self.__advertismentBoard.Hide()
			
			self.RefreshUnlockedTime()
			
			for i in range(len(self.__bannerInfoButtons)):
				self.__bannerInfoButtons[i].Hide()

		else:
			self.__nextButton.Hide()
			self.__cancelButton.Hide()
			self.__prevButton.Show()
			self.__completeButton.Show()
			
			self.__modelName.Hide()
			self.__boardName.Show()
			
			self.__npcSelection.Hide()
			self.__advertismentBoardSelection.Show()
			self.__advertismentBoard.Show()
			
			self.RefreshUnlockedTime()
			
			for i in range(len(self.__modelInfoButtons)):
				self.__modelInfoButtons[i].Hide()
	
	def __SelectShopNPC(self, race, skinID):
		race = 30000 + race
		self.__selectedNpc = race
		
		self.__selectedSkinID = skinID
		
		RENDER_TARGET_INDEX = 3
		renderTarget.SetBackground(RENDER_TARGET_INDEX, "d:/ymir work/ui/game/myshop_deco/background.tga")
		renderTarget.SetVisibility(RENDER_TARGET_INDEX, True)
		renderTarget.SelectModel(RENDER_TARGET_INDEX, race)
		self.__modelName.SetText(nonplayer.GetMonsterName(race))
	
	def __SelectAdvertismentBoard(self, type, bannerID):		
		keys = list(self.ADVERTISMENT_BOARDS.items())

		TYPES = ["default", "ice", "wing", "fire", "paper", "ribon"]
		
		self.__selectedAdvertismentBoard = type
		self.__selectedBannerID = bannerID

		self.__advertismentBoard.SetType(TYPES[type])
		self.__boardName.SetText(keys[type][1])
	
	def Hide(self):
		ui.ScriptWindow.Hide(self)
		game = uiOfflineShop.GetOfflineShopManager().GetGameWindowInstance()
		if game != None:
			game.CheckFocus()
	
	def SetCompleteEvent(self, event):
		self.__completeButton.SetEvent(event)
	
	def GetSelectedSkinID(self):
		return self.__selectedSkinID
		
	def GetSelectedBannerID(self):
		return self.__selectedBannerID
	
	def GetSelectedNpcRace(self):
		return self.__selectedNpc
	
	def GetSelectedAdvertismentBoard(self):
		return self.__selectedAdvertismentBoard
		
	def RefreshUnlockedTime(self):
		if self.__page == 0:
			for i in range(len(self.__modelInfoButtons)):
			
				if osfInfo.SHOP_SKIN_TIME[i] == 111: #permanent
					self.__modelInfoButtons[i].Show()
					self.__modelInfoButtons[i].SetToolTipText(localeInfo.SHOP_SKIN_UNLOCKED_PERMANENTLY, -70, -12)
				else:
					expireIn = osfInfo.SHOP_SKIN_TIME[i] - app.GetGlobalTimeStamp()
					if expireIn > 0:
						self.__modelInfoButtons[i].SetToolTipText(localeInfo.SHOP_SKIN_UNLOCKED_FOR + " : " + localeInfo.SecondToDHM(expireIn), -70, -12)
						self.__modelInfoButtons[i].Show()
					else:
						self.__modelInfoButtons[i].Hide()
		else:
			for i in range(len(self.__bannerInfoButtons)):
			
				if osfInfo.SHOP_BANNER_TIME[i] == 111: #permanent
					self.__bannerInfoButtons[i].Show()
					self.__bannerInfoButtons[i].SetToolTipText(localeInfo.SHOP_SKIN_UNLOCKED_PERMANENTLY, -70, -12)
				else:
					expireIn = osfInfo.SHOP_BANNER_TIME[i] - app.GetGlobalTimeStamp()
					if expireIn > 0:
						self.__bannerInfoButtons[i].SetToolTipText(localeInfo.SHOP_SKIN_UNLOCKED_FOR + " : " + localeInfo.SecondToDHM(expireIn), -70, -12)
						self.__bannerInfoButtons[i].Show()
					else:
						self.__bannerInfoButtons[i].Hide()
	
	def OnUpdate(self):
		if self.IsShow():
			
			self.RefreshUnlockedTime()
		
			if self.lastShopSkinDeco != osfInfo.SHOP_SKIN_VALUE:
				#Update skin buttons
				self.lastShopSkinDeco = osfInfo.SHOP_SKIN_VALUE
				i = 0
				for race in self.SHOP_NPCS:
					name = nonplayer.GetMonsterName(race)
					if i == 0 or osfInfo.SHOP_SKIN_UNLOCKED[i-1] == True:
						self.__modelButtons[i].SetText(name)
						self.__modelButtons[i].SetUpVisual("d:/ymir work/ui/game/myshop_deco/select_btn_01.sub")
						self.__modelButtons[i].SetOverVisual("d:/ymir work/ui/game/myshop_deco/select_btn_02.sub")
						self.__modelButtons[i].SetDownVisual("d:/ymir work/ui/game/myshop_deco/select_btn_03.sub")
					else:
						self.__modelButtons[i].SetText("")
						self.__modelButtons[i].SetUpVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_01.tga")
						self.__modelButtons[i].SetOverVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
						self.__modelButtons[i].SetDownVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
					self.__modelButtons[i].SetWindowHorizontalAlignCenter()
					i=i+1
				
			if self.lastShopBannerDeco != osfInfo.SHOP_BANNER_VALUE:
				#Update banner buttons
				self.lastShopBannerDeco = osfInfo.SHOP_BANNER_VALUE
				i=0
				for type, name in self.ADVERTISMENT_BOARDS.items():
					if i == 0 or osfInfo.SHOP_BANNER_UNLOCKED[i-1] == True:
						self.__bannerButtons[i].SetUpVisual("d:/ymir work/ui/game/myshop_deco/select_btn_01.sub")
						self.__bannerButtons[i].SetOverVisual("d:/ymir work/ui/game/myshop_deco/select_btn_02.sub")
						self.__bannerButtons[i].SetDownVisual("d:/ymir work/ui/game/myshop_deco/select_btn_03.sub")
						self.__bannerButtons[i].SetText(name)
					else:
						self.__bannerButtons[i].SetUpVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_01.tga")
						self.__bannerButtons[i].SetOverVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
						self.__bannerButtons[i].SetDownVisual("d:/ymir work/ui/game/myshop_deco/locked_button_btn_02.tga")
						self.__bannerButtons[i].SetText("")
					self.__bannerButtons[i].SetWindowHorizontalAlignCenter()
					i=i+1
					
			if self.GetLeft() < 0:
				self.SetPosition(0, self.GetTop())
			elif self.GetRight() > wndMgr.GetScreenWidth():
				self.SetPosition(wndMgr.GetScreenWidth() - self.GetWidth(), self.GetTop())
			
			if self.GetTop() < 0:
				self.SetPosition(self.GetLeft(), 0)
			elif self.GetBottom() > wndMgr.GetScreenHeight():
				self.SetPosition(self.GetLeft(), wndMgr.GetScreenHeight() - self.GetHeight())

	def OnPressEscapeKey(self):
		self.Hide()
