#
# Title: Fishing Game
# Description: Fishing game, catch the fish.
# Author: Owsap
# Last Date: 2022.10.28
#
# Skype: owsap.
# Discord: owsap
#
# Website: https://owsap.dev/
# GitHub: https://github.com/Owsap
# M2Dev: https://metin2.dev/profile/544-owsap/
#

import event
import app
import wndMgr
import dbg
import player
import ui
import uiScriptLocale
import math
import systemSetting
import servergamedata

DEBUG = False
FISH_MOVE_INTERVAL = 1.0 / 60.0
MAX_FISH_MOVE_STEPS = 15 # Avoid a long catch-up jump after a rendering pause.

class FishGame(ui.ScriptWindow):
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.__Initialize()
		self.__Load()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		self.Destroy()

	def __Initialize(self):
		## Objects
		self.backGroundWater = None # ImageBox
		self.goalCircle = None # ui.ImageBox
		self.fishImage = None
		self.hitImage = None
		self.missImage = None
		self.waveImage = None
		self.sharkImage = None
		self.timerGauge = None # ui.ExpandedImageBox
		# Goal count and duration are the server's minigame (fishing catalog).
		self.timerGaugeVal = servergamedata.FISHING_GAME_DURATION
		self.goalTarget = servergamedata.FISHING_GAME_GOALS
		self.hitCount = None
		self.hitCountText = None # ui.TextLine

		## Debug
		self.debugText_fish_pos_Local = None # TextLine
		self.debugText_goal_pos_Local = None # TextLine
		self.debugText_mouse_pos_Local = None # TextLine

		self.hit_image_list = []
		self.miss_image_list = []
		self.wave_image_list = []
		self.navigationArea = None # ui.Box

		self.hit_image_list = [
			"d:/ymir work/ui/game/fishing/fishing_effect_hit.sub"
		]
		self.miss_image_list = [
			"d:/ymir work/ui/game/fishing/fishing_effect_miss.sub"
		]
		self.wave_image_list = [
			"d:/ymir work/ui/game/fishing/wave/fishing_effect_wave_1.sub",
			"d:/ymir work/ui/game/fishing/wave/fishing_effect_wave_2.sub",
			"d:/ymir work/ui/game/fishing/wave/fishing_effect_wave_3.sub",
			"d:/ymir work/ui/game/fishing/wave/fishing_effect_wave_4.sub",
		]
		self.fish_image_list = [
			"d:/ymir work/ui/game/fishing/fish/fishing_fish_1.sub",
			"d:/ymir work/ui/game/fishing/fish/fishing_fish_2.sub",
			"d:/ymir work/ui/game/fishing/fish/fishing_fish_3.sub",
			"d:/ymir work/ui/game/fishing/fish/fishing_fish_4.sub"
		]

		self.fishSpeed = 2
		self.lastFishMoveTime = 0.0
		self.fishMoveRemainder = 0.0
		self.nextCourse = 0
		self.nextHit = 0
		self.fishMoving = False
		self.fishInGoal = False
		self.fishWaitDelay = 0
		self.fishingLimitDelay = 0
		self.fishingHanging = 0

		self.hitImageShowDelay = 0
		self.missImageShowDelay = 0
		self.sharkImageShowDelay = 0

		self.xFishDest = 0
		self.yFishDest = 0

		self.goalCount = 0

	def __Load(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/FishingGameWindow.py")

			self.board = self.GetChild("board") # board_with_titlebar
			self.backGroundWater = self.GetChild("fishing_background_water") # ui.ImageBox

			self.goalCircle = self.GetChild("fishing_goal_circle") # ui.ImageBox
			self.hitCount = self.GetChild("fishing_goal_count") # ui.ExpandedImageBox
			self.fishing_goal_count_text = self.GetChild("fishing_goal_count_text") # ui.ExpandedImageBox

			self.fishing_timer_baseImg = self.GetChild("fishing_timer_baseImg") # ui.ImageBox
			self.timerGauge = self.GetChild("fishing_timer_gauge") # ui.ExpandedImageBox

			#self.fishing_water_navArea = self.GetChild("fishing_water_navArea") # ui.Box

			## Debug
			if DEBUG:
				self.debug_text_circle_pos = self.GetChild("debug_text_circle_pos") # ui.TextLine
				self.debug_text_fish_pos = self.GetChild("debug_text_fish_pos") # ui.TextLine
				self.debug_text_mouse_pos = self.GetChild("debug_text_mouse_pos") # ui.TextLine
		except:
			import exception
			exception.Abort("FishGame.Load.UIScript/FishingGameWindow.py")

		if self.board:
			self.board.SetCloseEvent(ui.__mem_func__(self.Close))
			# The water image already has its own opaque frame.
			for framePart in self.board.Corners + self.board.Lines + [self.board.Base]:
				framePart.Hide()
			self.board.titleBar.SetPosition(0, 0)
			self.board.titleBar.SetWidth(self.board.GetWidth())

		if self.backGroundWater:
			self.backGroundWater.SetEvent(ui.__mem_func__(self.OnMouseLeftButtonDownEvent), "mouse_click")
			self.backGroundWater.OnMouseOverIn = ui.__mem_func__(self.OnMouseOverIn)
			self.backGroundWater.OnMouseOverOut = ui.__mem_func__(self.OnMouseOverOut)

		if DEBUG:
			self.debug_text_circle_pos.SetPosition(50, 50)
			self.debug_text_fish_pos.SetPosition(50, 50 + (12 * 1))
			self.debug_text_mouse_pos.SetPosition(50, 50 + (12 * 2))

		self.CreateFishImage()

	def Destroy(self):
		self.__Initialize()

	def OnUpdate(self):
		hitImageShowTime = max(0, self.hitImageShowDelay - app.GetTime())
		if hitImageShowTime <= 0:

			self.fishingHanging = False

			self.hitCount.SetDiffuseColor(1.0, 1.0, 1.0, 1.0)

		missImageShowTime = max(0, self.missImageShowDelay - app.GetTime())
		if missImageShowTime <= 0:
			self.timerGauge.SetDiffuseColor(1, 1, 1)

		fishingLimitTime = max(0, self.fishingLimitDelay - app.GetTime())
		self.timerGauge.SetPercentage(fishingLimitTime, self.timerGaugeVal)

		if fishingLimitTime <= 0:
			self.Close()
			return

		elif fishingLimitTime <= 5:
			self.timerGauge.SetDiffuseColor(1, 0, 0)

		if hasattr(self, "closeTimer") and self.closeTimer > 0:
			if app.GetTime() >= self.closeTimer:
				self.Close()
				return

		if app.GetTime() >= self.nextCourse:
			self.fishSpeed = app.GetRandom(1, 2)
			self.__OnMoveFish()
			self.nextCourse = app.GetTime() + 0.7

	def OnRender(self):
		if not self.fishImage:
			return

		## Move at the original 60 FPS pace on every refresh rate.
		now = app.GetTime()
		elapsed = max(0.0, now - self.lastFishMoveTime)
		self.lastFishMoveTime = now
		self.fishMoveRemainder = min(self.fishMoveRemainder + elapsed,
			FISH_MOVE_INTERVAL * MAX_FISH_MOVE_STEPS)
		steps = int(self.fishMoveRemainder / FISH_MOVE_INTERVAL)
		self.fishMoveRemainder -= steps * FISH_MOVE_INTERVAL

		(xFish, yFish) = self.fishImage.GetLocalPosition()
		moveX, moveY = 0, 0
		for _ in range(steps):
			stepX, stepY = xFish, yFish
			if self.xFishDest > xFish + self.fishSpeed:
				xFish += self.fishSpeed
			elif self.xFishDest < xFish - self.fishSpeed:
				xFish -= self.fishSpeed
			if self.yFishDest > yFish + self.fishSpeed:
				yFish += self.fishSpeed
			elif self.yFishDest < yFish - self.fishSpeed:
				yFish -= self.fishSpeed
			if xFish != stepX or yFish != stepY:
				moveX, moveY = xFish - stepX, yFish - stepY

		if moveX or moveY:
			angle = math.atan2(float(moveY), float(moveX)) * 180 / math.pi + 90
			self.fishImage.SetRotation(angle)
			self.fishImage.SetPosition(xFish, yFish)

		if DEBUG:
			self.debug_text_fish_pos.SetText("%d, %d" % (xFish, yFish))

		## Miss & Hit Image Effect
		if self.missImage:
			(xMiss, yMiss) = self.missImage.GetLocalPosition()
			missImageShowTime = max(0, self.missImageShowDelay - app.GetTime())
			if missImageShowTime > 0.0:
				self.missImage.SetPosition(xMiss + missImageShowTime + 1.0, yMiss - missImageShowTime - 1.0)
			else:
				self.missImage.Hide()

		if self.hitImage:
			(xHit, yHit) = self.hitImage.GetLocalPosition()
			hitImageShowTime = max(0, self.hitImageShowDelay - app.GetTime())
			if hitImageShowTime > 0.0:
				self.hitImage.SetPosition(xHit + hitImageShowTime, yHit - hitImageShowTime - 0.1)
			else:
				self.hitImage.Hide()

		if self.sharkImage:
			(xShark, yShark) = self.sharkImage.GetLocalPosition()
			sharkImageShowTime = max(0, self.sharkImageShowDelay - app.GetTime())
			if sharkImageShowTime > 0.0:
				self.sharkImage.SetAlpha(sharkImageShowTime)
			else:
				self.sharkImage.Hide()

		## Circle Render
		if self.fishingHanging != True:
			(xCircle, yCircle) = self.goalCircle.GetLocalPosition()
			if DEBUG:
				self.debug_text_circle_pos.SetText("%d, %d" % (xCircle, yCircle))

			xCenterCircle = ((self.goalCircle.GetWidth() // 2) + xCircle) - 14 # 125
			yCenterCircle = ((self.goalCircle.GetHeight() // 2) + yCircle) - 13 # 100
			circleRadius = 65.0

			circleDistance = math.sqrt((xCenterCircle - xFish) ** 2 + (yCenterCircle - yFish) ** 2)
			if circleDistance < circleRadius:
				self.fishInGoal = True
				self.goalCircle.SetDiffuseColor(1.0, 0.7, 0.7, 1.0)
			else:
				self.fishInGoal = False
				self.goalCircle.SetDiffuseColor(1.0, 1.0, 1.0, 1.0)

		## Mouse Position Debug
		if DEBUG:
			(xWater, yWater) = self.backGroundWater.GetGlobalPosition()
			(xMouse, yMouse) = wndMgr.GetMousePosition()
			(xCursor, yCursor) = (xMouse - xWater - 15, yMouse - yWater - 15)
			if DEBUG:
				self.debug_text_mouse_pos.SetText("%d, %d" % (xCursor, yCursor))

	def __OnMoveFish(self):
		self.xFishDest = app.GetRandom(15, 230)
		self.yFishDest = app.GetRandom(15, 180)

	def InitFishing(self):
		now = app.GetTime()
		self.fishingLimitDelay = now + self.timerGaugeVal
		self.lastFishMoveTime = now
		self.fishMoveRemainder = 0.0
		self.goalCount = 0
		self.closeTimer = 0
		self.nextCourse = 0
		self.nextHit = 0
		self.fishingHanging = False
		self.fishInGoal = False

		self.fishing_goal_count_text.SetText("%d / %d" % (self.goalCount, self.goalTarget))
		self.__OnMoveFish()
		self.fishImage.SetPosition(self.xFishDest, self.yFishDest)

	def OnMouseLeftButtonDownEvent(self):
		now = app.GetTime()
		if self.fishingHanging or now < self.nextHit:
			return

		## Clicked position.
		(xWater, yWater) = self.backGroundWater.GetGlobalPosition()
		(xCursor, yCursor) = wndMgr.GetMousePosition()
		(xClick, yClick) = (xCursor - xWater - 15, yCursor - yWater - 15)

		## Fish position.
		(xFish, yFish) = self.fishImage.GetLocalPosition()
		xFishGap = xClick - xFish
		yFishGap = yClick - yFish
		fishGap = 15

		if xFishGap > -fishGap and xFishGap < fishGap and yFishGap > -fishGap and yFishGap < fishGap and self.fishInGoal:
			self.CreateHitEffect(xClick, yClick)

			self.fishingHanging = True

			self.goalCircle.SetDiffuseColor(1.0, 1.0, 1.0)
			self.hitCount.SetDiffuseColor(0.5, 0.5, 0.5)

			self.goalCount += 1
			self.fishing_goal_count_text.SetText("%d / %d" % (self.goalCount, self.goalTarget))

			player.FishingGameGoal(self.goalCount)
		else:
			self.CreateMissEffect(xClick, yClick)
			if self.timerGauge:
				self.timerGauge.SetDiffuseColor(1, 0, 0)

		self.nextHit = now + 1.0
		if self.goalCount >= self.goalTarget:
			self.closeTimer = app.GetTime() + 0.05   # 50ms before closing

	def OnMouseOverIn(self):
		if systemSetting.IsSoftwareCursor():
			app.SetCursor(app.FISH)
		else:
			app.SetCursor(app.PICK)

	def OnMouseOverOut(self):
		app.SetCursor(app.NORMAL)

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Open(self, level):
		# Keep the packet argument for compatibility; all fish use the same pace.
		self.fishSpeed = 2
		self.InitFishing()
		self.Show()

	def QuitFishing(self):
		self.ClearFishing()
		player.FishingGameQuit()

	def Show(self):
		self.SetCenterPosition()
		ui.ScriptWindow.Show(self)

	def Close(self):
		self.QuitFishing()

		app.SetCursor(app.NORMAL)
		self.Hide()

	def ClearFishing(self):
		self.fishSpeed = 0
		self.lastFishMoveTime = 0.0
		self.fishMoveRemainder = 0.0
		self.nextCourse = 0
		self.nextHit = 0
		self.closeTimer = 0
		self.fishMoving = False
		self.fishInGoal = False
		self.fishWaitDelay = 0
		self.fishingLimitDelay = 0
		self.fishingHanging = 0

		self.hitImageShowDelay = 0
		self.missImageShowDelay = 0

		self.xFishDest = 0
		self.yFishDest = 0

	def CreateFishImage(self):
		self.fishImage = ui.AniImageBox()
		self.fishImage.SetParent(self.backGroundWater)
		self.fishImage.SetPosition(215, 160)
		self.fishImage.SetDelay(6.0)
		for fileName in self.fish_image_list:
			self.fishImage.AppendImage(fileName)
		self.fishImage.Show()

	def CreateHitEffect(self, x, y):
		self.hitImage = ui.ExpandedImageBox()
		self.hitImage.SetParent(self.backGroundWater)
		self.hitImage.SetPosition(x, y)
		self.hitImage.SetAlpha(1.0) #6
		for fileName in self.hit_image_list:
			self.hitImage.LoadImage(fileName)
		self.hitImage.Show()

		self.hitImage.AddFlag("not_pick")
		self.hitImage.AddFlag("float")

		self.hitImageShowDelay = app.GetTime() + 0.5

	def CreateMissEffect(self, x, y):
		self.missImage = ui.ExpandedImageBox()
		self.missImage.SetParent(self.backGroundWater)
		self.missImage.SetPosition(x + 10, y - 5)
		self.missImage.SetAlpha(1.0)
		for fileName in self.miss_image_list:
			self.missImage.LoadImage(fileName)
		self.missImage.Show()

		self.missImage.AddFlag("not_pick")
		self.missImage.AddFlag("float")

		self.missImageShowDelay = app.GetTime() + 0.2

	def CreateWaveEffect(self, x, y, delay):
		self.waveImage = ui.AniImageBox()
		self.waveImage.SetParent(self.backGroundWater)
		self.waveImage.SetPosition(x, y)
		self.waveImage.SetDelay(delay)
		self.waveImage.SetEndFrameEvent(ui.__mem_func__(self.__OnEndWaveEffect))
		for fileName in self.wave_image_list:
			self.waveImage.AppendImage(fileName)
		self.waveImage.Show()

		self.waveImage.AddFlag("not_pick")
		self.waveImage.AddFlag("float")

	def __OnEndWaveEffect(self):
		if self.waveImage:
			self.waveImage.Hide()

	def CreateSharkEffect(self):
		(xCircle, yCircle) = self.goalCircle.GetLocalPosition()
		xCenterCircle = ((self.goalCircle.GetWidth() // 2) + xCircle) - 14 # 125
		yCenterCircle = ((self.goalCircle.GetHeight() // 2) + yCircle) - 13 # 100

		self.sharkImage = ui.ExpandedImageBox()
		self.sharkImage.SetParent(self.backGroundWater)
		self.sharkImage.SetPosition(xCircle + 11, yCircle + 11)
		self.sharkImage.SetAlpha(1.0)
		self.sharkImage.LoadImage("d:/ymir work/ui/game/fishing/shark.png")
		self.sharkImage.Show()

		self.sharkImage.AddFlag("not_pick")
		self.sharkImage.AddFlag("float")

		self.sharkImageShowDelay = app.GetTime() + 1.0
