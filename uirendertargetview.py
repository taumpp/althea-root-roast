import ui 
import wndMgr
import player
import renderTarget
import osfInfo
import item
import dbg
import iscostumevoucher

RENDER_TARGET_INDEX = 2

TYPE_ITEM_WEAPON 	= 1
TYPE_ITEM_ARMOR 	= 2
TYPE_ITEM_HAIR 		= 3
TYPE_ITEM_ACCE 		= 4
TYPE_ITEM_SHINING_WEAPON = 5
TYPE_ITEM_SHINING_ARMOR = 6
TYPE_ITEM_MAX		= 7

TYPE_MONTER		= 20

RACE_WARRIOR_M	= 0
RACE_ASSASSIN_W	= 1
RACE_SURA_M		= 2
RACE_SHAMAN_W	= 3
RACE_WARRIOR_W	= 4
RACE_ASSASSIN_M	= 5
RACE_SURA_W		= 6
RACE_SHAMAN_M 	= 7
RACE_WOLFMAN_M 	= 8
RACE_MAX_NUM 	= 9

class RenderTargetWindow(ui.ScriptWindow):

	def __init__(self): 
		self.isLoaded = 0
		self.r1Skin = None
		
		self.board = None
		self.renderBoard = None
		self.currentVnum = 0
		self.currentType = 0
		self.currentRace = 0
		self.currentSex = 0
		self.isCharAvailable = [0 for x in range(4)]
		self.isSexAvailable = [0 for x in range(2)]
		self.hairIndex = 0
		self.isLeftClicked = False
		self.lastMousePos = [0 for x in range(2)]
		
		self.savedItem = [0 for x in range(TYPE_ITEM_MAX)]
		
		ui.ScriptWindow.__init__(self)
		self.__LoadWindow()

	def __LoadWindow(self):
		if self.isLoaded == 1:
			return

		self.isLoaded = 1

		try:
			import uir1
			if uir1.UseR1():
				import uirendertargetr1
				self.r1Skin = uirendertargetr1.Skin(self)
		except Exception:
			uir1.TraceFailure("RenderTargetWindow")

		try:
			if self.r1Skin is None:
				pyScrLoader = ui.PythonScriptLoader()
				pyScrLoader.LoadScriptFile(self, "UIScript/rendertargetPreview.py")
		except:
			import exception
			exception.Abort("RenderTargetWindow.__LoadWindow error")
			
		try:
			self.board = self.GetChild("board")
			self.renderBoard = self.GetChild("RenderBoard")
			self.renderBoard.SetMouseLeftButtonDownEvent(self.MouseLeftButtonDown)
			self.renderBoard.SetMouseLeftButtonUpEvent(self.MouseLeftButtonUp)
			
			self.buttonMale = self.GetChild("MaleButton")
			self.buttonMale.SetEvent(lambda arg=0: self.ChangeSex(arg))
			self.buttonFemale = self.GetChild("FemaleButton")
			self.buttonFemale.SetEvent(lambda arg=1: self.ChangeSex(arg))
			self.buttonMale.Disable()
			self.buttonFemale.Disable()
			
			self.buttonWarrior = self.GetChild("WarriorButton")
			self.buttonWarrior.SetEvent(lambda arg=0: self.ChangeChar(arg))
			self.buttonNinja = self.GetChild("NinjaButton")
			self.buttonNinja.SetEvent(lambda arg=1: self.ChangeChar(arg))
			self.buttonSura = self.GetChild("SuraButton")
			self.buttonSura.SetEvent(lambda arg=2: self.ChangeChar(arg))
			self.buttonShaman = self.GetChild("ShamanButton")
			self.buttonShaman.SetEvent(lambda arg=3: self.ChangeChar(arg))
			self.buttonWarrior.Disable()
			self.buttonNinja.Disable()
			self.buttonSura.Disable()
			self.buttonShaman.Disable()
			
			if self.r1Skin is None:
				self.board.SetCloseEvent(self.Close)
			
		except:
			import exception
			exception.Abort("RenderTargetWindow.LoadWindow.BindObject")
			
		self.SetCenterPosition()
		
	def MouseLeftButtonDown(self):
		(mouseX, mouseY) = self.GetMouseLocalPosition()
		self.lastMousePos[0] = mouseX
		self.lastMousePos[1] = mouseY
		
		self.isLeftClicked = True
		
	def MouseLeftButtonUp(self):
		self.isLeftClicked = False
		
	def OnMouseWheel(self, nLen):
		if nLen >= 0:
			renderTarget.ZoomPlus(RENDER_TARGET_INDEX)
		else:
			renderTarget.ZoomMinus(RENDER_TARGET_INDEX)
			
		return True
		
	def ZoomTest(self, isLeft):
		import chat

		if isLeft:
			
			osfInfo.RENDER_TARGET_ITEM_VNUM = 2493
			osfInfo.RENDER_TARGET_ITEM_TYPE = 5
			self.Reset()

		else:
			osfInfo.RENDER_TARGET_ITEM_VNUM = 2591
			osfInfo.RENDER_TARGET_ITEM_TYPE = 5
			self.Reset()
		
			
	def CanBeSubItem(self, vnum, iType):
		if self.currentType >= TYPE_ITEM_MAX or iType >= TYPE_ITEM_MAX:
			return False
	
		item.SelectItem(vnum)

		if item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR):
			if self.currentRace == RACE_WARRIOR_M or self.currentRace == RACE_WARRIOR_W:
				return False
			
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN):
			if self.currentRace == RACE_ASSASSIN_M or self.currentRace == RACE_ASSASSIN_W:
				return False
			
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA):
			if self.currentRace == RACE_SURA_M or self.currentRace == RACE_SURA_W:
				return False
			
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN):
			if self.currentRace == RACE_SHAMAN_W or self.currentRace == RACE_SHAMAN_M:
				return False
			
		#Sex
		#0 = Male
		#1 = Female				
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
			if self.currentSex == 1:
				return False
			
		if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
			if self.currentSex == 0:
				return False
				
		return True
			
		
	def CheckItem(self, bSetRace = True):
		if self.currentType >= TYPE_ITEM_MAX:
			for button in (self.buttonMale, self.buttonFemale, self.buttonWarrior,
					self.buttonNinja, self.buttonSura, self.buttonShaman):
				button.Disable()
			return

		if self.currentVnum > 0:

			item.SelectItem(self.currentVnum)
			self.hairIndex = item.GetValue(3)
			# self.isCharAvailable
			# 0 = Warrior
			# 1 = Ninja
			# 2 = Sura
			# 3 = Shaman
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR):
				self.isCharAvailable[0] = 0
				self.buttonWarrior.Disable()
			else:
				self.isCharAvailable[0] = 1
				self.buttonWarrior.Enable()
				if bSetRace:
					self.currentRace = RACE_WARRIOR_M
				
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN):
				self.isCharAvailable[1] = 0
				self.buttonNinja.Disable()
			else:
				self.isCharAvailable[1] = 1
				self.buttonNinja.Enable()
				if bSetRace:
					self.currentRace = RACE_ASSASSIN_M
				
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA):
				self.isCharAvailable[2] = 0
				self.buttonSura.Disable()
			else:
				self.isCharAvailable[2] = 1
				self.buttonSura.Enable()
				if bSetRace:
					self.currentRace = RACE_SURA_M
				
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN):
				self.isCharAvailable[3] = 0
				self.buttonShaman.Disable()
			else:
				self.isCharAvailable[3] = 1
				self.buttonShaman.Enable()
				if bSetRace:
					self.currentRace = RACE_SHAMAN_M
				
			#Sex
			#0 = Male
			#1 = Female				
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
				self.isSexAvailable[1] = 0
				self.buttonFemale.Disable()
				if bSetRace:
					self.currentSex = 0
			else:
				self.isSexAvailable[1] = 1
				self.buttonFemale.Enable()
				if bSetRace:
					self.currentSex = 1
				
			if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
				self.isSexAvailable[0] = 0
				self.buttonMale.Disable()
				if bSetRace:
					self.currentSex = 1
			else:
				self.isSexAvailable[0] = 1
				self.buttonMale.Enable()
				if bSetRace:
					self.currentSex = 0
					
			## CHECK FOR MULTIPLE ITEMS:
			if bSetRace == False:
				for x in range(len(self.savedItem)):
					if self.savedItem[x] > 0:
					
						item.SelectItem(self.savedItem[x])

						if item.IsAntiFlag(item.ITEM_ANTIFLAG_WARRIOR):
							self.isCharAvailable[0] = 0
							self.buttonWarrior.Disable()
							
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_ASSASSIN):
							self.isCharAvailable[1] = 0
							self.buttonNinja.Disable()
							
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_SURA):
							self.isCharAvailable[2] = 0
							self.buttonSura.Disable()
							
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_SHAMAN):
							self.isCharAvailable[3] = 0
							self.buttonShaman.Disable()
							
						#Sex		
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_FEMALE):
							self.isSexAvailable[1] = 0
							self.buttonFemale.Disable()
							
						if item.IsAntiFlag(item.ITEM_ANTIFLAG_MALE):
							self.isSexAvailable[0] = 0
							self.buttonMale.Disable()
					
			if bSetRace and self.currentType < TYPE_ITEM_MAX:
				self.PreferPlayerRace()

				
		
	#RENDER_TARGET_ITEM_TYPE
	# 1 = Weapon
	# 2 = Armor
	# 3 = Hair
	# 4 = Sash
	# 5 = Other model (pet, mount, etc.)
	#RENDER_TARGET_ITEM_TYPE
		
	def Show(self):
		if self.renderBoard:
			self.currentVnum = osfInfo.RENDER_TARGET_ITEM_VNUM
			self.currentType = osfInfo.RENDER_TARGET_ITEM_TYPE
			
			if self.currentVnum > 0 and self.currentType > 0:
				self.CheckItem()
				renderTarget.SetBackground(RENDER_TARGET_INDEX, "d:/ymir work/ui/render_target/render_target_bg.dds")
				renderTarget.SetVisibility(RENDER_TARGET_INDEX, True)

				self.SetUpModel()
			
		ui.ScriptWindow.Show(self)
		
	def Reset(self, noCheck = False):
		if self.renderBoard:
			if not noCheck:
				self.CheckItem()
			renderTarget.SetVisibility(RENDER_TARGET_INDEX, False)
			renderTarget.SetBackground(RENDER_TARGET_INDEX, "d:/ymir work/ui/render_target/render_target_bg.dds")
			renderTarget.SetVisibility(RENDER_TARGET_INDEX, True)
			self.SetUpModel()
				
	def SetUpModel(self):
		if self.currentType >= TYPE_ITEM_MAX: #Pet/Mount
			renderTarget.SelectModel(RENDER_TARGET_INDEX, self.currentVnum)
			import vipelfvisual
			armor = vipelfvisual.PreviewArmor(self.currentVnum)
			if armor:
				renderTarget.ChangeArmor(RENDER_TARGET_INDEX, armor)
		else:
			race = self.currentRace
			if self.currentSex == 1:
				race = self.MaleToFemale(race)
			
			renderTarget.SelectModel(RENDER_TARGET_INDEX, race)

			if self.currentType != TYPE_ITEM_HAIR and not self.savedItem[TYPE_ITEM_HAIR]:
				defaultHair = self.DefaultHairIndex(race)
				if defaultHair:
					renderTarget.ChangeHair(RENDER_TARGET_INDEX, defaultHair)
		
			if self.currentType == TYPE_ITEM_HAIR:
				item.SelectItem(self.currentVnum)
				self.hairIndex = item.GetValue(3)
				self.savedItem[self.currentType] = self.hairIndex
			else:
				self.savedItem[self.currentType] = self.currentVnum		
			
			if self.savedItem[TYPE_ITEM_WEAPON]:
				renderTarget.ChangeWeapon(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_WEAPON])
				
			if self.savedItem[TYPE_ITEM_ARMOR]:
				renderTarget.ChangeArmor(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_ARMOR])
				
			if self.savedItem[TYPE_ITEM_HAIR]:
				renderTarget.ChangeHair(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_HAIR])
				
			if self.savedItem[TYPE_ITEM_ACCE]:
				renderTarget.ChangeAcce(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_ACCE])
				
			curWeaponShining = 0
			curArmorShining = 0

			if self.savedItem[TYPE_ITEM_SHINING_WEAPON]:
				curWeaponShining = self.savedItem[TYPE_ITEM_SHINING_WEAPON]
				if self.savedItem[TYPE_ITEM_SHINING_ARMOR]:
					renderTarget.ChangeWeaponShining(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_SHINING_WEAPON], self.savedItem[TYPE_ITEM_SHINING_ARMOR])
				else:
					renderTarget.ChangeWeaponShining(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_SHINING_WEAPON], 0)
				
			if self.savedItem[TYPE_ITEM_SHINING_ARMOR]:
				curArmorShining = self.savedItem[TYPE_ITEM_SHINING_ARMOR]
				if self.savedItem[TYPE_ITEM_SHINING_WEAPON]:
					renderTarget.ChangeArmorShining(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_SHINING_ARMOR], self.savedItem[TYPE_ITEM_SHINING_WEAPON])
				else:
					renderTarget.ChangeArmorShining(RENDER_TARGET_INDEX, self.savedItem[TYPE_ITEM_SHINING_ARMOR], 0)
					
		
			if self.currentType == TYPE_ITEM_WEAPON:
				renderTarget.ChangeWeapon(RENDER_TARGET_INDEX, self.currentVnum)
			elif self.currentType == TYPE_ITEM_ARMOR:
				renderTarget.ChangeArmor(RENDER_TARGET_INDEX, self.currentVnum)
			elif self.currentType == TYPE_ITEM_HAIR:
				renderTarget.ChangeHair(RENDER_TARGET_INDEX, self.hairIndex)
			elif self.currentType == TYPE_ITEM_ACCE:
				renderTarget.ChangeAcce(RENDER_TARGET_INDEX, self.currentVnum)
			elif self.currentType == TYPE_ITEM_SHINING_WEAPON:
				if not self.savedItem[TYPE_ITEM_WEAPON]:
					if self.currentRace == RACE_WARRIOR_M or self.currentRace == RACE_WARRIOR_W:
						weapon = 19
					elif self.currentRace == RACE_ASSASSIN_M or self.currentRace == RACE_ASSASSIN_W:
						weapon = 1009
					elif self.currentRace == RACE_SURA_M or self.currentRace == RACE_SURA_W:
						weapon = 19
					elif self.currentRace == RACE_SHAMAN_M or self.currentRace == RACE_SHAMAN_W:
						weapon = 5009
					elif self.currentRace == RACE_WOLFMAN_M:
						weapon = 6009
					else:
						weapon = player.GetWeapon()
						if weapon == 0:
							weapon = 19
					renderTarget.ChangeWeapon(RENDER_TARGET_INDEX, weapon)
					
				renderTarget.ChangeWeaponShining(RENDER_TARGET_INDEX, self.currentVnum, curArmorShining)
				
			elif self.currentType == TYPE_ITEM_SHINING_ARMOR:
				renderTarget.ChangeArmorShining(RENDER_TARGET_INDEX, self.currentVnum, curWeaponShining)	

	def SetRace(self, race):
		self.currentRace = race

	def DefaultHairIndex(self, race):
		# Previewed costumes keep the viewer's worn hair costume on their own
		# race (ALTHEA-595); otherwise the new actor keeps hair part 0, the
		# race's default hairstyle.
		try:
			playerRace = player.GetRace()
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return 0
		return iscostumevoucher.PreviewHairIndex(
			race, playerRace, iscostumevoucher.WornHairIndex(player, item))

	def PreferPlayerRace(self):
		# Open on the viewer's own class and sex when the item allows them
		# (ALTHEA-595); otherwise keep the sex on an allowed class. Without a
		# usable character race the item's legacy default model stays.
		jobs = [job for job in range(len(self.isCharAvailable)) if self.isCharAvailable[job]]
		try:
			playerRace = player.GetRace()
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return
		race = iscostumevoucher.PreviewRace(
			playerRace, jobs, bool(self.isSexAvailable[0]), bool(self.isSexAvailable[1]))
		if race is None:
			return
		self.currentRace = race
		self.currentSex = 1 if iscostumevoucher.IsFemaleRace(race) else 0
		
	def OnUpdate(self):
		if not self.renderBoard:
			return
			
		if self.isLeftClicked:
			
			(mouseX, mouseY) = self.GetMouseLocalPosition()
			xDif = self.lastMousePos[0] - mouseX
			if xDif:
				if hasattr(renderTarget, "Rotate"):
					renderTarget.Rotate(RENDER_TARGET_INDEX, float(-xDif) * 0.45)
				elif xDif > 0:
					renderTarget.RotateLeft(RENDER_TARGET_INDEX)
				else:
					renderTarget.RotateRight(RENDER_TARGET_INDEX)
			self.lastMousePos[0] = mouseX
			self.lastMousePos[1] = mouseY
			
		if osfInfo.RENDER_TARGET_ITEM_VNUM != 0 and osfInfo.RENDER_TARGET_ITEM_VNUM != self.currentVnum:
			if osfInfo.RENDER_TARGET_ITEM_TYPE != 0:

				if self.IsShow():
					# Handle here multiple items

					if self.CanBeSubItem(osfInfo.RENDER_TARGET_ITEM_VNUM, osfInfo.RENDER_TARGET_ITEM_TYPE):
						
						self.currentVnum = osfInfo.RENDER_TARGET_ITEM_VNUM
						self.currentType = osfInfo.RENDER_TARGET_ITEM_TYPE
						
						self.SetUpModel()
						self.CheckItem(False)

					else:
						self.ClearSavedItems()

						self.currentVnum = osfInfo.RENDER_TARGET_ITEM_VNUM
						self.currentType = osfInfo.RENDER_TARGET_ITEM_TYPE
						self.Reset()

				else:
					self.ClearSavedItems()
					self.currentVnum = osfInfo.RENDER_TARGET_ITEM_VNUM
					self.currentType = osfInfo.RENDER_TARGET_ITEM_TYPE
					self.Reset()
					
	def ClearSavedItems(self):
		if self.renderBoard:
			renderTarget.ResetCamera(RENDER_TARGET_INDEX)
		self.savedItem = [0 for x in range(TYPE_ITEM_MAX)]
		
	def Close(self):
		self.isLeftClicked = False
		self.ClearSavedItems()
		
		if self.renderBoard:
			renderTarget.SetVisibility(RENDER_TARGET_INDEX, False)
			
		self.Hide()
		
	def Destroy(self):
		self.Close()
		if self.r1Skin:
			self.r1Skin.Destroy()
			self.r1Skin = None
		self.ClearDictionary()
		self.board = None
		self.renderBoard = None
		self.currentVnum = 0
		self.currentType = 0
		self.currentRace = 0
		self.currentSex = 0
		self.isCharAvailable = [0 for x in range(4)]
		self.isSexAvailable = [0 for x in range(2)]
		self.hairIndex = 0
		
	def OnPressEscapeKey(self):
		self.Close()
		return True
		
	def MaleToFemale(self, race):
		if race == RACE_WARRIOR_M:
			return RACE_WARRIOR_W
		elif race == RACE_SURA_M:
			return RACE_SURA_W
		elif race == RACE_ASSASSIN_M:
			return RACE_ASSASSIN_W
		elif race == RACE_SHAMAN_M:
			return RACE_SHAMAN_W
		else:
			return race
			
	def FemaleToMale(self, race):
		if race == RACE_ASSASSIN_W:
			return RACE_ASSASSIN_M
		elif race == RACE_SHAMAN_W:
			return RACE_SHAMAN_M
		elif race == RACE_WARRIOR_W:
			return RACE_WARRIOR_M
		elif race == RACE_SURA_W:
			return RACE_SURA_M
		else:
			return race
		
	def ChangeSex(self, sex):
		newRace = -1
		if sex == 0 and self.currentSex != 0: #change to MALE
			newRace = self.FemaleToMale(self.currentRace)
			self.currentSex = 0
		elif sex == 1 and self.currentSex != 1: #change to FEMALE
			newRace = self.MaleToFemale(self.currentRace)
			self.currentSex = 1
			
		if newRace != -1:
			self.currentRace = newRace
			self.Reset(True)
		
	def ChangeChar(self, race):
		# 0 = Warrior
		# 1 = Ninja
		# 2 = Sura
		# 3 = Shaman
		if self.isCharAvailable[race]:
			if race == 0: #warrior
				if self.currentSex == 1:
					self.currentRace = self.MaleToFemale(RACE_WARRIOR_M)
				else:
					self.currentRace = RACE_WARRIOR_M
			elif race == 1: #ninja
				if self.currentSex == 1:
					self.currentRace = self.MaleToFemale(RACE_ASSASSIN_M)
				else:
					self.currentRace = RACE_ASSASSIN_M
			elif race == 2: #Sura
				if self.currentSex == 1:
					self.currentRace = self.MaleToFemale(RACE_SURA_M)
				else:
					self.currentRace = RACE_SURA_M
			elif race == 3: #Shaman
				if self.currentSex == 1:
					self.currentRace = self.MaleToFemale(RACE_SHAMAN_M)
				else:
					self.currentRace = RACE_SHAMAN_M
			
			self.Reset(True)

	def __del__(self): 
		ui.ScriptWindow.__del__(self) 
