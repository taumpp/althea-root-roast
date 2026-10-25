# -*- coding: utf-8 -*-
"""Presentation adapter around the authoritative existing pet controller."""
from _weakref import proxy
import item
import localeInfo
import player
import ui
import uiScriptLocale
import WikiRenderTarget
import growthpetpresentation
import uimountk1 as K1
import uipetalbum
import uipetalbumcapturebadge
import uir1

ART = uipetalbum.ASSET_ROOT


class PetCompactPresentation(object):
	def __init__(self, owner):
		self.owner = proxy(owner)
		self.renderIndex = None
		self.race = None
		self.album = None
		self.orbs = []
		self.actionState = None
		self.view = ui.WikiRenderTargetUi()
		parent = owner.GetChild("PetPreviewViewport")
		self.view.SetParent(parent)
		self.view.SetSize(255, 172)
		self.view.SetClippingMaskWindow(parent)
		self.view.AddFlag("not_pick")
		self.view.Hide()
		board = owner.GetChild("UpBringing_Pet_EXP_Gauge_Board")
		for index in range(4):
			self.orbs.append(K1.SoulOrb(board,index*24,0,index+1))
		albumButton = owner.GetChild("AlbumButton")
		albumButton.SetEvent(ui.__mem_func__(self.OpenAlbum))
		# Centre the native caption beside the book, reserving room for the badge.
		if albumButton.ButtonText:
			albumButton.ButtonText.SetPosition(97, 12)
			albumButton.ButtonText.SetVerticalAlignCenter()
		self.captureBadge = uipetalbumcapturebadge.AlbumCaptureBadge(albumButton, 151, 5, role="album")
		owner.GetChild("ReviveMainButton").SetEvent(ui.__mem_func__(owner.OpenPetReviveFromFeed))
		owner.GetChild("DetermineButton").Hide()
		for name in ("Hp", "Def", "Sp"):
			owner.GetChild(name + "Jump").Hide()
		self.r1 = None
		self.r1Failed = False
		self.LoadR1()
		self.Refresh(0, 0)

	def LoadR1(self):
		"""The R1 look (root/uipetr1.py) drawn into the pet window unless Settings -> "Starý vzhled" chose the original
		look; a failure traces to syserr and keeps the original look (not retried on every opening)."""
		if self.r1 or self.r1Failed or not uir1.UseR1():
			return
		try:
			import uipetr1
			self.r1 = uipetr1.PetSkin(self, self.owner)
		except Exception:
			uir1.TraceFailure("the pet window")
			self.r1Failed = True
			self.r1 = None

	def SyncLook(self):
		"""Settings -> "Starý vzhled" / the R1 look take effect on the next opening of the window."""
		wanted = uir1.UseR1() and not self.r1Failed
		if wanted and not self.r1:
			self.LoadR1()
		elif not wanted and self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()

	def OpenAlbum(self):
		if self.album is None:
			self.album = uipetalbum.PetAlbumWindow()
		self.album.Open()

	def SetExperience(self, battle, battleMax, food, foodMax):
		# One visible total; no fifth/item orb or permanent duplicate percent.
		total = max(0, battleMax) + max(0, foodMax)
		value = min(max(0,battle),max(0,battleMax)) + min(max(0,food),max(0,foodMax))
		ratio = float(value) / total if total else 0.0
		self.experience = (value, total)
		for index, orb in enumerate(self.orbs):
			orb.SetValue(max(0.0,min(1.0,ratio*4-index)))
		self.owner.tooltipEXP.SetText("%s: %d / %d" % (uiScriptLocale.PET_INFORMATION_EXP,value,total))
		self.owner.tooltipEXP.SetPosition(28, 284)
		if self.r1:
			self.r1.SetExperience(value, total)

	def Refresh(self, petID, evolution, itemVnum=0, isActive=False,
			isExpired=False, petType=0, statValues=(0.0, 0.0, 0.0)):
		owner = self.owner
		thirdLabel = (getattr(localeInfo, "PET_ALBUM_HUMANS", u"Silný proti pololidem")
			if petType % 2 else getattr(localeInfo, "PET_ALBUM_MONSTERS", u"Silný proti příšerám"))
		owner.GetChild("SpTitle").SetText(thirdLabel if petID else "-")
		for index, name in enumerate(("Hp", "Def", "Sp")):
			low, high = growthpetpresentation.GrowthBounds(index, petID)
			if petID:
				owner.GetChild(name + "Value").SetText(
					growthpetpresentation.StatValueText(statValues[index], low, high))
				if self.r1:
					current = ("%.1f" % float(statValues[index])).replace(".", ",")
					growth = ""
					if low is not None and high is not None:
						growth = ("(%.1f-%.1f %%)" % (low / 10.0, high / 10.0)).replace(".", ",")
					self.r1.SetBonus(index, u"+%s %%" % current, growth)
			elif self.r1:
				self.r1.SetBonus(index, "-", "")
			owner.GetChild(name + "Jump").SetText("")
		actionState = (bool(isActive and not isExpired), bool(isExpired and not isActive))
		if self.actionState != actionState:
			self.actionState = actionState
			for key in ("FeedMainButton", "EvolutionMainButton"):
				button = owner.GetChild(key)
				button.Enable() if actionState[0] else button.Disable()
			revive = owner.GetChild("ReviveMainButton")
			revive.Enable() if actionState[1] else revive.Disable()
		for index in range(5):
			label = owner.GetChild("PetSkillState%d" % index)
			if not isActive:
				label.SetText("")
				owner.skillSlot[index].SetAlwaysRenderCoverButton(0, True)
				continue
			locked, vnum, level, cooldown = player.GetPetSkillSlotState(petID,index)
			label.SetText(uiScriptLocale.PET_ALBUM_FREE if not locked and not vnum else "")
		if self.r1:
			self.r1.Sync()
		if not petID:
			owner.GetChild("PetName").SetText(uiScriptLocale.PET_ALBUM_EMPTY)
			for key in ("LevelValue","AgeValue","LifeTextValue","HpValue","DefValue","SpValue"):
				owner.GetChild(key).SetText("-")
			if self.r1:
				self.r1.Sync()
			self.RemoveTarget()
			return
		if not owner.IsShow() or owner.state != player.PET_WINDOW_INFO:
			self.RemoveTarget()
			return
		item.SelectItem(itemVnum)
		race = item.GetValue(3 if evolution >= 4 else 0)
		if race <= 0:
			self.RemoveTarget()
			return
		try:
			if self.renderIndex is None:
				index = int(WikiRenderTarget.GetFreeIndex(100,255))
				if not 1 <= index <= 255:
					return
				self.renderIndex = index
				self.view.SetRenderTarget(index)
				WikiRenderTarget.SetBackground(index, ART + "preview-fill.png")
				WikiRenderTarget.SetRotation(index,False)
			if self.race != race:
				WikiRenderTarget.SelectModel(self.renderIndex,race)
				self.race = race
			WikiRenderTarget.SetVisibility(self.renderIndex,True)
			self.view.Show()
		except (AttributeError,RuntimeError,TypeError,ValueError):
			self.RemoveTarget()

	def SetState(self, state):
		owner = self.owner
		width,height = (292,520) if state == player.PET_WINDOW_INFO else (352,448)
		owner.SetSize(width,height)
		owner.GetChild("board").SetSize(width,height)
		owner.GetChild("TitleBar").SetWidth(width+8)
		if self.r1:
			self.r1.Resize(width, height)
		if state != player.PET_WINDOW_INFO:
			self.RemoveTarget()

	def SetGrowthPreview(self, petID, *values):
		growthpetpresentation.SetGrowthPreview(petID, *values)

	def RemoveTarget(self):
		index = self.renderIndex
		self.renderIndex, self.race = None, None
		if self.view:
			self.view.Hide()
		if index is not None:
			try:
				WikiRenderTarget.SetVisibility(index,False)
				WikiRenderTarget.Remove(index)
			except (AttributeError,RuntimeError):
				pass

	def Hide(self):
		self.RemoveTarget()

	def AlbumWindows(self):
		if not self.album:
			return ()
		if self.album.occurrenceWindow:
			return (self.album, self.album.occurrenceWindow)
		return (self.album,)

	def CloseAlbumWindows(self):
		if self.album:
			self.album.Close()
			if self.album.occurrenceWindow:
				self.album.occurrenceWindow.Close()

	def Destroy(self):
		if self.r1:
			r1, self.r1 = self.r1, None
			r1.Restore()
		self.Hide()
		if self.captureBadge:
			self.captureBadge.Destroy()
		self.captureBadge = None
		if self.album:
			self.album.Destroy()
		self.album = None
		for orb in self.orbs:
			orb.Hide()
		self.orbs = []
		self.view = None
		self.owner = None
