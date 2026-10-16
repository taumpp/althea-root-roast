"""Native-size K1 presentation; no server state or item mutation authority."""
import ui
import uitooltip
import uicrimsoncontrols
from uimountwidgets import ASSET_ROOT, CreateImage, MountSoulOrb, _OwnChild

K1_ROOT = ASSET_ROOT + "k1/"
TEXT = 0xffe4dacb
MUTED = 0xffa59c90
GOLD = 0xffe5c17b
GREEN = 0xff8fcb7c
BLUE = 0xff68b9e7
ELEMENT_KEYS = ("fire", "ice", "lightning", "wind", "earth", "dark")


def SetColor(line, color):
	# The native packed-color overload takes a signed int, not 0xffRRGGBB.
	line.SetFontColor(
		((color >> 16) & 0xff) / 255.0,
		((color >> 8) & 0xff) / 255.0,
		(color & 0xff) / 255.0,
	)


def Text(parent, x, baseline, text=u"", size=12, color=TEXT, align="left", bold=False):
	line = ui.TextLine()
	line.SetParent(parent)
	# Opt into the shipped grayscale coverage path: binary legacy coverage
	# turns faint edge pixels solid and makes small glyphs look clogged.
	line.SetFontName("Tahoma:%d%sa" % (size, "b" if bold else ""))
	line.SetPosition(x, baseline + 2)
	line.SetVerticalAlignBottom()
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	line.AddFlag("not_pick")
	line.SetText(text)
	SetColor(line, color)
	line.Show()
	return _OwnChild(parent, line)


def Image(parent, x, y, filename):
	return CreateImage(parent, x, y, "k1/" + filename)


def Surface(parent, x, y, width, height):
	return Image(parent, x, y, "surface_%dx%d.png" % (width, height))


def Section(parent, x, y, width, caption):
	section = Image(parent, x, y, "header_%dx28.png" % width)
	section.label = Text(section, width // 2, 18, caption, color=GOLD, align="center", bold=True)
	return section


class Progress(ui.Window):
	def __init__(self, parent, x, y, width):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.SetSize(width, 7)
		self.AddFlag("not_pick")
		self.gauge = ui.Gauge()
		self.gauge.SetParent(self)
		self.gauge.MakeGauge(width, "red")
		self.gauge.AddFlag("not_pick")
		for name in ("imgLeft", "imgCenter", "imgRight", "imgGauge", "imgGaugeBack", "aniGauge"):
			child = getattr(self.gauge, name, None)
			if child:
				child.AddFlag("not_pick")
		self.gauge.Show()
		self.SetValue(0, 1)
		self.Show()

	def SetValue(self, value, maximum):
		maximum = max(1, int(maximum))
		value = max(0, min(maximum, int(value)))
		self.gauge.SetPercentage(value, maximum)
		if value:
			self.gauge.imgGauge.Show()
		else:
			self.gauge.imgGauge.Hide()
		for name in ("imgGaugeBack", "aniGauge"):
			child = getattr(self.gauge, name, None)
			if child:
				child.Hide()


class SoulOrb(MountSoulOrb):
	def __init__(self, parent, x, y, index):
		MountSoulOrb.__init__(self, parent, x, y, index)
		self.AddFlag("not_pick")
		self.empty.LoadImage(K1_ROOT + "soul_orb_empty_%02d_19x19.png" % int(index))

	def SetValue(self, ratio):
		try:
			ratio = float(ratio)
		except (TypeError, ValueError):
			ratio = 0.0
		MountSoulOrb.SetValue(self, ratio)
		# The full sprite already has clean antialiased alpha; do not double its rim.
		if float(ratio) >= 1.0:
			self.empty.Hide()
		else:
			self.empty.Show()


class SideTab(ui.RadioButton):
	def __init__(self, parent, glyph, event):
		ui.RadioButton.__init__(self)
		self.SetParent(parent)
		self.SetSize(36, 36)
		self.glyph = Image(self, 8, 8, glyph)
		self.SetEvent(event)
		self.SetSelected(False)
		self.Show()

	def SetSelected(self, selected):
		self.SetUpVisual(K1_ROOT + "switch_36x36_%s.png" % ("selected" if selected else "normal"))
		self.SetOverVisual(K1_ROOT + "switch_36x36_%s.png" % ("selected" if selected else "hover"))
		self.SetDownVisual(K1_ROOT + "switch_36x36_%s.png" % ("selected" if selected else "pressed"))
		self.SetDisableVisual(K1_ROOT + "switch_36x36_disabled.png")
		if selected:
			self.Down()
		else:
			self.SetUp()


class ElementRow(ui.Window):
	WIDTH = 218
	HEIGHT = 55

	def __init__(self, parent, event):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.button = ui.Button()
		self.button.SetParent(self)
		self.button.SetSize(self.WIDTH, self.HEIGHT)
		self.button.SetEvent(event)
		self.button.Show()
		self.icon = CreateImage(self, 12, 15, "element_fire_24.png")
		self.name = Text(self, 48, 21, size=12, bold=True)
		self.value = Text(self, 48, 41, size=11, color=MUTED)
		self.glyph = CreateImage(self, 196, 20, "glyph_right_8.png")
		self.Show()

	def SetData(self, row):
		key = ELEMENT_KEYS[row["element_id"]]
		selected = bool(row.get("opened"))
		state = "selected" if selected else "disabled" if row["state"] == "locked" else "normal"
		self.button.SetUpVisual(K1_ROOT + "row_%s_%s.png" % (key, state))
		self.button.SetOverVisual(K1_ROOT + "row_%s_%s.png" % (key, "selected" if selected else "hover"))
		self.button.SetDownVisual(K1_ROOT + "row_%s_%s.png" % (key, "selected" if selected else "pressed"))
		self.button.SetDisableVisual(K1_ROOT + "row_%s_disabled.png" % key)
		self.icon.LoadImage(ASSET_ROOT + row["icon"])
		self.name.SetText(row["name"])
		SetColor(self.name, GOLD if selected else MUTED if state == "disabled" else TEXT)
		self.value.SetText(row["bonus_text"].lstrip("+"))
		SetColor(self.value, GREEN if row["state"] == "completed" else MUTED)
		glyph = "check" if row["state"] == "completed" else "lock" if row["state"] == "locked" else "right"
		self.glyph.LoadImage(ASSET_ROOT + "glyph_%s_8.png" % glyph)
		if selected or row["state"] in ("completed", "locked"):
			self.glyph.Show()
		else:
			self.glyph.Hide()


def WrappedLines(text, width, measure):
	"""Keep every character, including long unbroken localized item names."""
	result = []
	for paragraph in text.splitlines() or [u""]:
		current = u""
		for word in paragraph.split():
			candidate = (current + u" " + word) if current else word
			if measure(candidate) <= width:
				current = candidate
				continue
			if current:
				result.append(current)
			current = u""
			for char in word:
				if current and measure(current + char) > width:
					result.append(current)
					current = u""
				current += char
		result.append(current)
	return result or [u""]


class TaskRow(ui.Window):
	WIDTH = 210
	HEIGHT = 78

	def __init__(self, parent, submitEvent):
		ui.Window.__init__(self)
		self.SetParent(parent)
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.submitEvent = submitEvent
		self.canSubmit = False
		self.enabled = False
		self.tooltip = None
		self.tooltipLines = []
		self.SAFE_SetOverInEvent(self.__ShowToolTip)
		self.SAFE_SetOverOutEvent(self.HideToolTip)
		self.number = Text(self, 0, 16, size=11, color=GOLD)
		self.measure = Text(self, 27, 16)
		self.measure.Hide()
		self.lines = []
		self.counter = Text(self, self.WIDTH, 37, size=11, color=MUTED, align="right")
		self.progress = Progress(self, 27, 45, 183)
		self.submit = ui.Button()
		self.submit.SetParent(self)
		uicrimsoncontrols.ApplyVisuals(self.submit, "80x24")
		self.submit.SetText(u"Odevzdat")
		self.submit.SetEvent(ui.__mem_func__(self.__Submit))
		self.submit.Hide()
		self.divider = Image(self, 0, 77, "divider_210x1.png")
		self.Show()

	def __Measure(self, text):
		self.measure.SetText(text)
		return self.measure.GetTextSize()[0]

	def SetData(self, row, name, number):
		self.number.SetText(u"%02d" % number)
		for line in self.lines:
			line.Hide()
		self.lines = []
		wrapped = WrappedLines(name, 183, self.__Measure)
		self.tooltipLines = wrapped + [row["reward_text"]]
		for index, text in enumerate(wrapped):
			self.lines.append(Text(self, 27, 16 + index * 14, text))
		extra = (len(wrapped) - 1) * 14
		self.HEIGHT = 78 + extra
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.counter.SetPosition(self.WIDTH, 39 + extra)
		self.counter.SetText(row["progress_text"])
		SetColor(self.counter, GREEN if row["complete"] else MUTED)
		self.progress.SetPosition(27, 45 + extra)
		self.progress.SetValue(row["progress"], row["target"])
		self.submit.SetPosition(130, 48 + extra)
		self.submit.SetToolTipText(name + u" · " + row["reward_text"])
		self.divider.SetPosition(0, self.HEIGHT - 1)
		self.canSubmit = row["event_kind"] == 3 and not row["complete"]
		if self.canSubmit:
			self.progress.Hide()
			self.submit.Show()
		else:
			self.progress.Show()
			self.submit.Hide()
		self.SetEnabled(self.enabled)

	def SetEnabled(self, enabled):
		self.enabled = bool(enabled)
		if self.enabled and self.canSubmit:
			self.submit.Enable()
		else:
			self.submit.Disable()

	def __Submit(self):
		if self.enabled and self.canSubmit:
			self.submitEvent()

	def __ShowToolTip(self):
		if self.tooltip is None:
			self.tooltip = uitooltip.ToolTip(240)
		self.tooltip.ClearToolTip()
		for line in self.tooltipLines:
			self.tooltip.AppendTextLine(line)
		self.tooltip.ShowToolTip()

	def HideToolTip(self):
		self.submit.HideToolTip()
		if self.tooltip:
			self.tooltip.HideToolTip()
