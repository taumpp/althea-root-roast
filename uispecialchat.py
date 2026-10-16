import app
import grp
import ui
import wndMgr
import chat
import localeInfo

class SpecialChat(ui.ThinBoard):
	def __init__(self, parent, x = 0, y = 0):
		ui.ThinBoard.__init__(self)
		self.texts = {}
		self.parent = parent
		self.SpaceBet = 14
		self.maxY = 0
		self.x = x
		self.y = y
		self.ColorValue = grp.GenerateColor(1.0, 1.0, 1.0, 0.8)
		self.over_in = False
		self.IsYang = False
		self.lastlinetime = 0
		self.SetTop()
		self.SetSize(150, 215)
		self.SetPosition(wndMgr.GetScreenWidth()//2 - 451, wndMgr.GetScreenHeight() - 60)

	def __del__(self):
		ui.ThinBoard.__del__(self)

	def AddSpecialChatLine(self, text, arg = 0, Yang = False):
		for i in range(len(self.texts)):
			if len(self.texts) == 12 and i == 0:
				self.texts[i].Hide()
			x, y = self.texts[i].GetLocalPosition()
			self.texts[i].SetPosition(x, y+self.SpaceBet)

		i = 0
		if len(self.texts) == 12:
			for i in range(len(self.texts)-1):
				self.texts[i] = self.texts[i+1]
			i = 11
		else:
			i = len(self.texts)

		self.texts[i] = ui.TextLine()
		self.texts[i].SetParent(self)
		self.texts[i].SetPosition(self.GetWidth()//2, 5)
		self.texts[i].SetPackedFontColor(self.ColorValue)
		self.texts[i].SetHorizontalAlignCenter()
		self.texts[i].SetVerticalAlignTop()
		self.texts[i].SetOutline(TRUE)

		max_len = 28-5
		if Yang:
			max_len = 38-5
		if len(text) > max_len:
			text = text[:max_len-3] + "..."

		if not Yang:
			self.texts[i].SetText(text + "|Ikey/item|i")
		else:
			self.texts[i].SetText(text + "|Ikey/money|i")

		self.texts[i].Show()
		self.Show()
		self.lastlinetime = app.GetTime()
		self.IsYang = Yang

	def ClearAll(self):
		self.Hide()
		self.texts = {}
		self.IsYang = False

	def OnMouseOverIn(self):
		self.over_in = True

	def OnMouseOverOut(self):
		self.over_in = False

	def OnUpdate(self):
		if self.over_in == True:
			(x, y) = self.GetGlobalPosition()
			w, h = self.texts[0].GetTextSize()
			height = (h+2)*len(self.texts)+42
			if y > wndMgr.GetScreenHeight() - height:
				self.SetPosition(wndMgr.GetScreenWidth()//2 - 451, max(self.GetHeight(), y - 4))
		else:
			(x, y) = self.GetGlobalPosition()
			if y < wndMgr.GetScreenHeight() - self.GetHeight()//2+50:
				self.SetPosition(wndMgr.GetScreenWidth()//2 - 451, max(self.GetHeight(), y + 4))
