import ui
import player
import chr
import textTail
import app

if app.ENABLE_POISON_GAUGE_EFFECT:
	import chrmgr

class PlayerGauge(ui.Gauge):

	def __init__(self, parent):
		ui.Gauge.__init__(self)
		self.SetParent(parent)
		self.AddFlag("not_pick")
		# The original bar in every look: it only shows below half HP and the owner wants it as it always was.
		self.MakeGauge(100, "red")

		self.curHP = 0
		self.maxHP = 0

		self.showAlways = FALSE

	def __del__(self):
		ui.Gauge.__del__(self)

	def Hide(self):
		self.SetPosition(-100, -100)
		ui.Gauge.Hide(self)

	def OnUpdate(self):
		playerIndex = player.GetMainCharacterIndex()

		(x, y, z)=textTail.GetPosition(playerIndex)

		if x != x or y != y:
			return

		isChat = textTail.IsChat(playerIndex)
		ui.Gauge.SetPosition(self, int(x - self.GetWidth()//2), int(y + 5) + isChat*17)

	def RefreshGauge(self):

		self.curHP = player.GetStatus(player.HP)
		self.maxHP = player.GetStatus(player.MAX_HP)
		if app.ENABLE_POISON_GAUGE_EFFECT:
			poisoned = chrmgr.HasAffectByVID(player.GetMainCharacterIndex(), chr.AFFECT_POISON)
			if poisoned:
				self.imgGauge.LoadImage("d:/ymir work/ui/pattern/gauge_lime.tga")
			else:
				self.imgGauge.LoadImage("d:/ymir work/ui/pattern/gauge_red.tga")

		self.SetPercentage(self.curHP, self.maxHP)

		if self.showAlways:
			self.Show()

		else:

			if self.IsShow():
				if self.curHP > self.maxHP // 2:
					self.Hide()

			else:
				if self.curHP < self.maxHP // 2:
					self.OnUpdate()
					self.Show()

	def EnableShowAlways(self):
		self.showAlways = TRUE
		self.RefreshGauge()

	def DisableShowAlways(self):
		self.showAlways = FALSE
		self.RefreshGauge()
