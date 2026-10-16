"""Click-through capture count shared by the pet rail and album entry."""
import math
import app
import ui
import petalbumstate

WindowDestroy = getattr(ui, "WindowDestroy", lambda method: method)


class AlbumCaptureBadge(ui.Window):
	def __init__(self, parent, x, y, role="rail"):
		ui.Window.__init__(self)
		self.count = None
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.size = 16 if role == "rail" else 14
		self.fontSize = 11 if role == "rail" else 10
		self.SetSize(self.size, self.size)
		self.AddFlag("not_pick")
		self.background = ui.ExpandedImageBox()
		self.background.SetParent(self)
		asset = "capture-badge-ruby-16.png" if role == "rail" else "capture-badge-charcoal-14.png"
		self.background.LoadImage("d:/ymir work/ui/pet/album_c/" + asset)
		self.background.AddFlag("not_pick")
		self.label = ui.TextLine()
		self.label.SetParent(self)
		self.label.SetPosition(self.size // 2, self.size // 2)
		self.label.SetVerticalAlignCenter()
		self.label.SetHorizontalAlignCenter()
		self.label.SetFontName("Tahoma:%db" % self.fontSize)
		self.label.SetPackedFontColor(-730468)
		self.label.AddFlag("not_pick")
		self.Refresh()
		# Keep the update owner shown even when the decorative children hide.
		self.Show()

	def __del__(self):
		ui.Window.__del__(self)

	def Refresh(self):
		state = petalbumstate.GetState()
		count = state.unreadCaptures if state.available else 0
		if count == self.count:
			return
		self.count = count
		if count:
			self.label.SetFontName("Tahoma:%db" % (self.fontSize - (1 if count > 9 else 0)))
			self.label.SetText(str(count))
			self.background.Show()
			self.label.Show()
		else:
			self.background.Hide()
			self.label.Hide()

	def OnUpdate(self):
		if self.background is None:
			return
		self.Refresh()
		if self.count:
			# One shared clock keeps both entries in phase; never blink to invisible.
			alpha = 0.70 + 0.30 * (0.5 - 0.5 * math.cos(2.0 * math.pi * app.GetTime() / 2.4))
			self.background.SetAlpha(alpha)
			color = (int(alpha * 255) << 24) | 0xF4DA9C
			self.label.SetPackedFontColor(color - 0x100000000)

	@WindowDestroy
	def Destroy(self):
		self.Hide()
		if self.background:
			self.background.Hide()
		if self.label:
			self.label.Hide()
		self.background = None
		self.label = None
		self.count = None
