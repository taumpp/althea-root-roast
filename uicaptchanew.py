import app
import fontconfig
import grp
import net
import ui
import wndMgr


SCENE_WIDTH = 320
SCENE_HEIGHT = 180
SCENE_BYTES = 768 + SCENE_WIDTH * SCENE_HEIGHT
SCENE_SCALE = 1.5


class CaptchaReadyPulse(ui.Window):
	"""Brief decoration over the public bag; never an input or answer target."""
	DURATION = 0.65

	def __init__(self, canvas):
		ui.Window.__init__(self)
		self.SetParent(canvas)
		self.SetSize(int(SCENE_WIDTH * SCENE_SCALE), int(SCENE_HEIGHT * SCENE_SCALE))
		self.AddFlag("not_pick")
		self.endsAt = 0.0
		self.Hide()

	def Flash(self):
		self.endsAt = app.GetTime() + self.DURATION
		self.Show()

	def Stop(self):
		self.endsAt = 0.0
		self.Hide()

	def OnRender(self):
		remaining = self.endsAt - app.GetTime()
		if remaining <= 0:
			self.Stop()
			return
		x, y = self.GetGlobalPosition()
		for inset in (1, 2):
			grp.SetColor(grp.GenerateColor(0.96, 0.16, 0.13,
				0.55 * remaining / self.DURATION / inset))
			grp.RenderBox(int(x + 252 * SCENE_SCALE) - inset,
				int(y + 66 * SCENE_SCALE) - inset,
				int(60 * SCENE_SCALE) + 2 * inset, int(66 * SCENE_SCALE) + 2 * inset)


class CaptchaPointer(ui.Window):
	def __init__(self, canvas):
		ui.Window.__init__(self)
		self.canvas = canvas
		self.SetParent(canvas)
		self.SetSize(int(SCENE_WIDTH * SCENE_SCALE), int(SCENE_HEIGHT * SCENE_SCALE))
		self.AddFlag("not_pick")
		self.Show()

	def OnRender(self):
		canvas = self.canvas
		if not canvas:
			return
		point = canvas.press or canvas.selection
		if point is None:
			return
		x, y = self.GetGlobalPosition()
		grp.SetColor(grp.GenerateColor(0.90, 0.73, 0.35, 0.95))
		grp.RenderBox(int(x + point[0] * SCENE_SCALE - 8),
			int(y + point[1] * SCENE_SCALE - 8), 16, 16)
		if canvas.press:
			current = canvas.Point()
			if current:
				grp.RenderBox(int(x + current[0] * SCENE_SCALE - 10),
					int(y + current[1] * SCENE_SCALE - 10), 20, 20)


class CaptchaCanvas(ui.ExpandedImageBox):
	"""Displays a flattened image. It has no item IDs, hitboxes or answer map."""
	def __init__(self, owner):
		ui.ExpandedImageBox.__init__(self)
		self.owner = owner
		self.press = None
		self.selection = None
		self.SetParent(owner)
		self.SetPosition(26, 112)
		self.SetSize(int(SCENE_WIDTH * SCENE_SCALE), int(SCENE_HEIGHT * SCENE_SCALE))
		self.pointer = CaptchaPointer(self)

	def SetRaster(self, pixels):
		if not isinstance(pixels, bytes) or len(pixels) != SCENE_BYTES:
			raise ValueError("Invalid CAPTCHA raster")
		wndMgr.LoadCaptchaRaster(self.hWnd, pixels)
		self.SetScale(SCENE_SCALE, SCENE_SCALE)
		self.SetSize(int(SCENE_WIDTH * SCENE_SCALE), int(SCENE_HEIGHT * SCENE_SCALE))
		self.SetLinearFiltering(True)
		self.CancelSelection()
		self.Show()

	def Point(self):
		x, y = self.GetMouseLocalPosition()
		if 0 <= x < SCENE_WIDTH * SCENE_SCALE and 0 <= y < SCENE_HEIGHT * SCENE_SCALE:
			return (int(x / SCENE_SCALE), int(y / SCENE_SCALE))
		return None

	def CancelSelection(self):
		self.press = None
		self.selection = None

	def OnMouseLeftButtonDown(self):
		if self.owner and self.owner.CanInteract():
			self.press = self.Point()
		return True

	def OnMouseLeftButtonUp(self):
		start, self.press = self.press, None
		if not start or not self.owner or not self.owner.CanInteract():
			return True
		end = self.Point()
		if end is None:
			self.CancelSelection()
			return True
		if self.selection is not None:
			selected, self.selection = self.selection, None
			if abs(end[0] - selected[0]) + abs(end[1] - selected[1]) >= 4:
				self.owner.SubmitMove(selected, end)
		elif abs(end[0] - start[0]) + abs(end[1] - start[1]) >= 4:
			self.owner.SubmitMove(start, end)
		else:
			self.selection = start
		return True

	def OnMouseRightButtonDown(self):
		self.CancelSelection()
		return True

	def Destroy(self):
		self.CancelSelection()
		self.Hide()
		self.pointer.canvas = None
		self.pointer.Hide()
		self.pointer = None
		self.owner = None


class CaptchaWindow(ui.BoardWithTitleBar):
	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("float")
		self.AddFlag("movable")
		self.SetSize(532, 446)
		self.SetTitleName("Ověření přítomnosti")
		self.SetCloseEvent(ui.__mem_func__(self.Nothing))
		self.titleBar.btnClose.Hide()
		self.widgets = []
		self.sessionId = 0
		self.generation = 0
		self.deadlineAt = 0
		self.retryAt = 0
		self.status = 0
		self.submissionPending = False
		self.heading = self.Text("Rozhrň kořist", 266, 38, True)
		self.instruction = self.Text("Odlož vrchní předměty a nakonec zlatou truhlu do rámečku.", 266, 65)
		self.timer = self.Text("", 266, 88)
		self.canvas = CaptchaCanvas(self)
		self.feedback = self.Text("", 266, 392)
		self.help = self.Text("Přetáhni předmět, nebo klikni na předmět a potom na cíl.", 266, 416)
		self.Hide()

	def Text(self, value, x, y, heading=False):
		text = ui.TextLine()
		text.SetParent(self)
		text.SetFontName(fontconfig.FontForRole(
			fontconfig.ROLE_SECTION if heading else fontconfig.ROLE_BODY))
		text.SetPosition(x, y)
		text.SetHorizontalAlignCenter()
		text.SetText(value)
		if heading:
			text.SetFontColor(0.90, 0.73, 0.35)
		text.AddFlag("not_pick")
		text.Show()
		self.widgets.append(text)
		return text

	def Nothing(self):
		return True

	def CanInteract(self):
		return (self.IsShow() and self.status in (
			app.CAPTCHA_STATUS_PENDING, app.CAPTCHA_STATUS_WRONG) and
			not self.submissionPending and self.deadlineAt > app.GetGlobalTimeStamp())

	def OpenChallenge(self, status, attemptsRemaining, sessionId, generation,
		deadlineAt, retryAt, pixels):
		self.status = int(status)
		self.sessionId = int(sessionId)
		self.generation = int(generation)
		self.deadlineAt = int(deadlineAt)
		self.retryAt = int(retryAt)
		self.submissionPending = False
		self.canvas.CancelSelection()
		if status == app.CAPTCHA_STATUS_SOLVED:
			self.Hide()
			return
		self.canvas.Hide()
		if status in (app.CAPTCHA_STATUS_PENDING, app.CAPTCHA_STATUS_WRONG):
			try:
				self.canvas.SetRaster(pixels)
			except (ValueError, RuntimeError):
				self.status = app.CAPTCHA_STATUS_ERROR
				self.feedback.SetText("Obrázek nelze zobrazit. Zkus se znovu přihlásit.")
			else:
				self.feedback.SetText(
					"Zkus to znovu. Zbývající pokusy: %d" % attemptsRemaining
					if status == app.CAPTCHA_STATUS_WRONG else "")
		elif status == app.CAPTCHA_STATUS_COOLDOWN:
			self.feedback.SetText("Další pokus bude dostupný po odpočtu.")
		else:
			self.feedback.SetText("Ověření není dostupné. Zkus se znovu přihlásit.")
		if not self.IsShow():
			self.SetCenterPosition()
		self.SetTop()
		self.SetFocus()
		ui.BoardWithTitleBar.Show(self)
		self.OnUpdate()

	def SubmitMove(self, start, end):
		if not self.CanInteract():
			return
		self.submissionPending = True
		self.canvas.CancelSelection()
		try:
			sent = net.SendCaptchaV3(self.sessionId, self.generation,
				start[0], start[1], end[0], end[1])
		except (TypeError, ValueError, RuntimeError):
			sent = False
		if not sent:
			self.submissionPending = False
			self.feedback.SetText("Tah se nepodařilo odeslat. Zkus to znovu.")

	def OnUpdate(self):
		if not self.IsShow():
			return
		now = app.GetGlobalTimeStamp()
		if self.status == app.CAPTCHA_STATUS_ERROR:
			self.timer.SetText("")
		elif self.status == app.CAPTCHA_STATUS_COOLDOWN:
			minutes, seconds = divmod(max(0, self.retryAt - now), 60)
			self.timer.SetText("Další pokus za %02d:%02d" % (minutes, seconds))
		elif self.submissionPending or now >= self.deadlineAt:
			self.timer.SetText("Ověřování...")
		else:
			minutes, seconds = divmod(max(0, self.deadlineAt - now), 60)
			self.timer.SetText("Čas na dokončení: %02d:%02d" % (minutes, seconds))

	def OnPressEscapeKey(self):
		self.canvas.CancelSelection()
		return True

	def Hide(self):
		if getattr(self, "canvas", None):
			self.canvas.CancelSelection()
		self.KillFocus()
		ui.BoardWithTitleBar.Hide(self)

	def Destroy(self):
		self.Hide()
		if self.canvas:
			self.canvas.Destroy()
			self.canvas = None
		self.widgets = []
		self.heading = self.instruction = self.timer = self.feedback = self.help = None


class CaptchaDragCanvas(ui.ExpandedImageBox):
	"""Only the server-authorized held tile follows the pointer locally."""
	def __init__(self, owner):
		ui.ExpandedImageBox.__init__(self)
		self.owner = owner
		self.SetParent(owner)
		self.SetPosition(26, 112)
		self.heldImage = ui.ExpandedImageBox()
		self.heldImage.SetParent(self)
		self.heldImage.AddFlag("not_pick")
		self.original = None
		self.lastPickAt = -1.0
		self.ClearPointer()

	def ClearPointer(self):
		self.start = None
		self.down = False
		self.held = False
		self.awaiting = False
		self.cancelling = False
		self.released = False
		self.releasePoint = None
		self.origin = None
		self.requestAt = 0.0
		self.heldImage.Hide()

	def CancelSelection(self):
		self.ClearPointer()

	def Point(self):
		x, y = self.GetMouseLocalPosition()
		if 0 <= x < SCENE_WIDTH * SCENE_SCALE and 0 <= y < SCENE_HEIGHT * SCENE_SCALE:
			return int(x / SCENE_SCALE), int(y / SCENE_SCALE)
		return None

	def Paint(self, pixels):
		if not isinstance(pixels, bytes) or len(pixels) != SCENE_BYTES:
			raise ValueError("Invalid CAPTCHA raster")
		wndMgr.LoadCaptchaRaster(self.hWnd, pixels)
		self.SetScale(SCENE_SCALE, SCENE_SCALE)
		self.SetSize(int(SCENE_WIDTH * SCENE_SCALE), int(SCENE_HEIGHT * SCENE_SCALE))
		self.SetLinearFiltering(False)
		self.Show()

	def SetRaster(self, pixels):
		self.Paint(pixels)
		self.original = pixels
		self.ClearPointer()

	def SetHeld(self, pixels, originX, originY, heldPixels):
		if self.cancelling:
			return
		if not self.awaiting or self.start is None:
			self.Cancel()
			return
		if (not isinstance(heldPixels, bytes) or len(heldPixels) != 64 * 64 or
			not 0 <= originX <= SCENE_WIDTH - 64 or not 0 <= originY <= SCENE_HEIGHT - 64):
			raise ValueError("Invalid CAPTCHA held tile")
		self.Paint(pixels)
		wndMgr.LoadCaptchaDragRaster(self.heldImage.hWnd, pixels[:768] + heldPixels)
		self.heldImage.SetScale(SCENE_SCALE, SCENE_SCALE)
		self.heldImage.SetSize(int(64 * SCENE_SCALE), int(64 * SCENE_SCALE))
		self.heldImage.SetLinearFiltering(False)
		self.origin = originX, originY
		self.awaiting = False
		self.held = True
		self.owner.submissionPending = False
		self.heldImage.Show()
		self.FollowPointer()
		if self.released:
			self.FinishRelease(self.releasePoint)

	def OnMouseLeftButtonDown(self):
		if not self.owner or not self.owner.CanInteract():
			return True
		point = self.Point()
		if point is None:
			return True
		if self.owner.IsClickKind():
			# one click is the whole answer; only the server judges it.
			now = app.GetTime()
			if now - self.lastPickAt < 0.30:
				return True
			self.lastPickAt = now
			self.requestAt = now
			self.owner.SendClick(point)
			return True
		self.down = True
		if self.held:
			return True  # Second click places the already selected tile.
		now = app.GetTime()
		if now - self.lastPickAt < 0.30:
			self.down = False
			return True
		self.lastPickAt = now
		self.start = point
		self.awaiting = True
		self.requestAt = now
		if not self.owner.SendPointer(3, point):
			self.ClearPointer()
		return True

	def OnMouseLeftButtonUp(self):
		if not self.down or self.start is None:
			return True
		self.down = False
		point = self.Point()
		if self.awaiting:
			self.released = True
			self.releasePoint = point
		else:
			self.FinishRelease(point)
		return True

	def FinishRelease(self, point):
		self.released = False
		if point is None:
			self.Cancel()
		elif self.held and abs(point[0] - self.start[0]) + abs(point[1] - self.start[1]) >= 4:
			self.FollowPointer(point)
			self.owner.SendPointer(2, self.start, point)
		else:
			# A short click leaves the tile selected for the next destination click.
			self.FollowPointer()

	def FollowPointer(self, point=None):
		if not self.held or not self.origin or self.owner.submissionPending:
			return
		x, y = self.GetMouseLocalPosition() if point is None else (
			point[0] * SCENE_SCALE, point[1] * SCENE_SCALE)
		x += (self.origin[0] - self.start[0]) * SCENE_SCALE
		y += (self.origin[1] - self.start[1]) * SCENE_SCALE
		self.heldImage.SetPosition(int(x), int(y))

	def Cancel(self):
		if not self.owner or self.cancelling:
			return
		active = self.start is not None or self.held or self.awaiting
		self.ClearPointer()
		if self.original and self.owner.CanShowScene():
			self.Paint(self.original)
		if active:
			self.cancelling = True
			self.requestAt = app.GetTime()
			self.owner.SendPointer(4)

	def OnMouseRightButtonDown(self):
		self.Cancel()
		return True

	def OnUpdate(self):
		self.FollowPointer()
		if self.awaiting and app.GetTime() - self.requestAt > 2.0:
			self.Cancel()
		elif (self.owner and self.owner.IsClickKind() and self.owner.submissionPending and
			app.GetTime() - self.requestAt > 2.0):
			self.owner.submissionPending = False  # no reply: the same image can be clicked again

	def Destroy(self):
		self.ClearPointer()
		self.original = None
		self.Hide()
		self.heldImage.Hide()
		self.owner = None


# R1 look A "Věrná" (): the original layout in the R1 frame, steps by brightness,
# the countdown on the right, attempts as dots. Colours are R1 tokens as floats.
INK = (0.93, 0.90, 0.85)
INK_DIM = (0.75, 0.71, 0.67)
MUTED = (0.57, 0.55, 0.52)
DOT_ON = 0xFFD30D0E
DOT_OFF = 0xFF383434

# Click kinds named by CaptchaV4Stage (kind * 100 + step * 10 + steps): presentation only.
KIND_RECIPE, KIND_COUNT, KIND_ROTATE, KIND_ODD = 5, 6, 7, 8
KIND_ARROW, KIND_LINES, KIND_SHARD, KIND_DICE, KIND_SEAL = 9, 10, 11, 12, 13
KIND_GEARS, KIND_COMPASS, KIND_SHADOWS = 14, 15, 16
KIND_TEXT = {
	KIND_RECIPE: ("Krok %d ze %d", "Klikej na suroviny v pořadí podle receptu nahoře.",
		"Na stole jsou i podobné suroviny. Kliknutí se nedá vrátit."),
	KIND_COUNT: ("Kolo %d ze %d", "Spočítej předmět z rámečku a klikni na správné číslo.",
		"Předměty se překrývají a jsou různě natočené."),
	KIND_ROTATE: ("Kolo %d ze %d", "Otoč runu na kotouči, aby stála jako vzor.",
		"Šipkou otočíš runu o 30°. Pak klikni na tlačítko s fajfkou."),
	KIND_ODD: ("Kolo %d ze %d", "Klikni na předmět, který mezi ostatní nepatří.",
		"Ostatní předměty jsou stejného druhu, jen jinak natočené."),
	KIND_ARROW: ("Kolo %d ze %d", "Na který předmět míří šipka?",
		"Ostatní šipky jsou návnady. Klikni na předmět, na který míří."),
	KIND_LINES: ("Kolo %d ze %d", "Která ryba visí na vlasci s velkým splávkem s bílým kroužkem?",
		"Vlasce mají stejnou barvu a kříží se. Klikni na rybu."),
	KIND_SHARD: ("Kolo %d ze %d", "Který úlomek přesně zapadne do díry ve skále?",
		"Úlomky jsou natočené. Rozhoduje tvar zubaté hrany."),
	KIND_DICE: ("Kolo %d ze %d", "Sečti oka na horních stranách kostek a klikni na součet.",
		"Oka na bocích kostek se nepočítají."),
	KIND_SEAL: ("Kolo %d ze %d", "Kterým prstenem byla otištěna pečeť?",
		"Otisk je zrcadlový. Prsteny i pečeť jsou natočené."),
	KIND_GEARS: ("Kolo %d ze %d", "Kam se točí kolo s bílou tečkou? Klikni na směr.",
		"Rudá šipka ukazuje první kolo. Kolo bez záběru se netočí."),
	KIND_COMPASS: ("Kolo %d ze %d", "Který předmět leží na sever (S) od stanu?",
		"Kompas je pokaždé jinak natočený. Klikni na předmět."),
	KIND_SHADOWS: ("Kolo %d ze %d", "Který předmět vrhá stín špatným směrem?",
		"Stíny míří od pochodně. Klikni na předmět."),
}
# Owner 21. 10.: one round per puzzle (the server sends steps = 1). No "Kolo 1 ze 1": the
# heading is neutral and the recipe asks for one ingredient. Older three-round stages keep
# the round copy above.
SINGLE_HEADING = "Ověření přítomnosti"
SINGLE_INSTRUCTION = {
	KIND_RECIPE: "Klikni na surovinu z receptu nahoře.",
}
# Arrow kind (owner 11. 10.): the stage names the asked colour as (colour + 1) * 10000.
# The word is drawn in the arrow's colour. Owner 21. 10. (colour-blind players): the task
# names the head shape first, the colour only in brackets. Heads as the server draws
# them, in the same order 0 red .. 4 white.
ARROW_COLOURS = (
	("RUDÁ", "FFF0302A", "s hrotem do V"),
	("MODRÁ", "FF8C88FF", "s plným trojúhelníkem"),
	("ZELENÁ", "FF6DB265", "s kosočtvercem"),
	("ZLATÁ", "FFDEC86F", "s dvojitým hrotem"),
	("BÍLÁ", "FFFFFFFF", "s kuličkou"),
)
ARROW_INSTRUCTION = "Kam ukazuje šipka %s (|c%s%s|r)?"
# A one-line hint under the task, only where the picture alone could mislead. Never the answer.
KIND_HINT = {}  # owner 11. 10.: the compass task itself says "na sever (S)"; no hint line now
CHEST_HELP = "Táhni myší, nebo klikni na předmět a potom na cíl."
CHEST_INSTRUCTION = "Odkryj celý čtverec truhly, pak ji vlož do vaku."
# Owner 11. 10.: no image means no task copy. The cooldown shows only neutral text;
# the countdown itself is the timer on the right ("Další pokus za mm:ss").
WAIT_HEADING = "Ověření přítomnosti"
WAIT_INSTRUCTION = "Po odpočtu dostaneš nový obrázek."


class CaptchaUncoverWindow(CaptchaWindow):
	def __init__(self):
		CaptchaWindow.__init__(self)
		self.canvas.Destroy()
		self.canvas = CaptchaDragCanvas(self)
		self.SetSize(532, 402)
		self.kind = None
		self.heading.SetHorizontalAlignLeft()
		self.heading.SetPosition(26, 39)
		self.heading.SetText("1  Odkryj truhlu")
		self.stepTwo = self.Text("2  Vlož ji do vaku", 136, 39, True)
		self.stepTwo.SetHorizontalAlignLeft()
		self.timer.SetHorizontalAlignRight()
		self.timer.SetPosition(506, 39)
		self.timer.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_SECTION))
		self.timer.SetFontColor(*INK)
		self.instruction.SetPosition(266, 61)
		self.instruction.SetText(CHEST_INSTRUCTION)
		self.hint = self.Text("", 266, 68)
		self.hint.SetFontColor(*INK_DIM)
		self.hint.Hide()
		self.instruction.SetFontColor(*INK)
		self.canvas.SetPosition(26, 82)
		self.feedback.SetPosition(266, 358)
		self.feedback.SetFontColor(0.96, 0.16, 0.13)
		self.help.SetHorizontalAlignLeft()
		self.help.SetPosition(26, 378)
		self.help.SetText(CHEST_HELP)
		self.help.SetFontColor(*MUTED)
		self.attemptsLabel = self.Text("Pokusy", 450, 378)
		self.attemptsLabel.SetHorizontalAlignRight()
		self.attemptsLabel.SetFontColor(*MUTED)
		self.attemptDots = []
		for index in range(3):
			dot = ui.Bar()
			dot.SetParent(self)
			dot.SetPosition(462 + index * 14, 383)
			dot.SetSize(7, 7)
			dot.SetColor(DOT_ON)
			dot.AddFlag("not_pick")
			dot.Show()
			self.attemptDots.append(dot)
		self.stage = None
		self.readyPulse = CaptchaReadyPulse(self.canvas)
		self.bagLabels = []
		for text, y in (("Sem patří", 142), ("truhla", 153)):
			label = self.Text(text, 0, 0)
			label.SetParent(self.canvas)
			label.SetPosition(int(282 * SCENE_SCALE), int(y * SCENE_SCALE))
			label.SetFontColor(0.70, 0.68, 0.63)
			self.bagLabels.append(label)
		# No overlay labels for click kinds: every scene places its parts differently,
		# so the raster carries everything (the rune's confirm button has a check mark).
		self.kindLabels = []
		self.ShowChestCopy()
		self.r1frame = None
		try:
			import uir1frame
			self.r1frame = uir1frame.Dress(self, dict(board=None, close=False))
		except Exception:
			self.r1frame = None

	def IsClickKind(self):
		return self.kind in KIND_TEXT

	def ShowChestCopy(self, stage=None):
		self.kind = None
		self.heading.SetText("1  Odkryj truhlu")
		self.heading.SetFontColor(*(INK if stage != 2 else MUTED))
		self.stepTwo.SetFontColor(*(INK if stage == 2 else MUTED))
		self.stepTwo.Show()
		self.help.SetText(CHEST_HELP)
		self.instruction.SetPosition(266, 61)
		self.hint.Hide()
		for label in self.bagLabels:
			label.Show()
		for label in self.kindLabels:
			label.Hide()

	def ShowWaitCopy(self):
		"""Cooldown or error: no scene is shown, so no chest or click-kind copy either."""
		self.kind = None
		self.stage = None
		self.readyPulse.Stop()
		self.heading.SetText(WAIT_HEADING)
		self.heading.SetFontColor(*INK)
		self.stepTwo.Hide()
		self.instruction.SetPosition(266, 61)
		self.instruction.SetText(WAIT_INSTRUCTION
			if self.status == app.CAPTCHA_STATUS_COOLDOWN else "")
		self.hint.Hide()
		self.help.SetText("")
		for label in self.bagLabels:
			label.Hide()
		for label in self.kindLabels:
			label.Hide()

	def ShowKindCopy(self, kind, step, steps, colour=0):
		heading, instruction, help = KIND_TEXT[kind]
		if steps <= 1:
			heading = SINGLE_HEADING
			instruction = SINGLE_INSTRUCTION.get(kind, instruction)
		if kind == KIND_ARROW and 1 <= colour <= len(ARROW_COLOURS):
			word, tint, shape = ARROW_COLOURS[colour - 1]
			instruction = ARROW_INSTRUCTION % (shape, tint, word)
		self.kind = kind
		self.readyPulse.Stop()
		self.heading.SetText(heading % (step, steps) if "%" in heading else heading)
		self.heading.SetFontColor(*INK)
		self.stepTwo.Hide()
		self.instruction.SetText(instruction)
		self.help.SetText(help)
		hint = KIND_HINT.get(kind, "")
		self.hint.SetText(hint)
		if hint:
			self.instruction.SetPosition(266, 54)  # the hint takes the line above the scene
			self.hint.Show()
		else:
			self.instruction.SetPosition(266, 61)
			self.hint.Hide()
		for label in self.bagLabels:
			label.Hide()
		for label in self.kindLabels:
			label.Hide()

	def SetAttempts(self, remaining):
		for index, dot in enumerate(self.attemptDots):
			dot.SetColor(DOT_ON if index < remaining else DOT_OFF)

	def SetStage(self, sessionId, generation, stage):
		"""The server repeats only the public visual step after its snapshot."""
		try:
			sessionId, generation, stage = int(sessionId), int(generation), int(stage)
		except (TypeError, ValueError, OverflowError):
			return
		colour, base = stage // 10000, stage % 10000
		kind, step, steps = base // 100, base // 10 % 10, base % 10
		click = (kind in KIND_TEXT and 1 <= step <= steps <= 3 and (colour == 0 or
			(kind == KIND_ARROW and colour <= len(ARROW_COLOURS))))
		if ((stage not in (1, 2) and not click) or not sessionId or not generation or
			(sessionId, generation) != (self.sessionId, self.generation) or
			not self.IsShow() or not self.canvas or not self.canvas.IsShow() or
			self.status not in (app.CAPTCHA_STATUS_PENDING, app.CAPTCHA_STATUS_WRONG,
				app.CAPTCHA_STATUS_HELD) or self.deadlineAt <= app.GetGlobalTimeStamp()):
			return
		if click:
			self.stage = stage
			self.ShowKindCopy(kind, step, steps, colour)
			return
		if self.IsClickKind():
			return  # a chest hint never reaches a click-kind puzzle of this session
		if stage == 2:
			self.instruction.SetText("Přesuň truhlu do vaku.")
			if self.stage != 2:
				self.readyPulse.Flash()
		else:
			self.instruction.SetText("Odkryj celý čtverec truhly.")
			self.readyPulse.Stop()
		self.stage = stage
		self.ShowChestCopy(stage)
		for label in self.bagLabels:
			label.SetFontColor(*(INK if stage == 2 else (0.70, 0.68, 0.63)))

	def OnUpdate(self):
		if not self.IsShow():
			return
		now = app.GetGlobalTimeStamp()
		if self.status == app.CAPTCHA_STATUS_ERROR:
			text = ""
		elif self.status == app.CAPTCHA_STATUS_COOLDOWN:
			text = "Další pokus za %02d:%02d" % divmod(max(0, self.retryAt - now), 60)
		elif now >= self.deadlineAt:
			text = "Načítání..."
			self.readyPulse.Stop()
		else:
			# Keep time visible during PICK/MOVE round trips instead of flickering
			# between the countdown and a pending-operation label on every drag.
			text = "Zbývá %02d:%02d" % divmod(self.deadlineAt - now, 60)
		self.timer.SetText(text)

	def Hide(self):
		if getattr(self, "readyPulse", None):
			self.readyPulse.Stop()
		CaptchaWindow.Hide(self)

	def Destroy(self):
		CaptchaWindow.Destroy(self)
		self.readyPulse = None
		self.bagLabels = []
		self.kindLabels = []
		self.attemptDots = []
		self.attemptsLabel = self.stepTwo = self.hint = None
		self.r1frame = None

	def CanShowScene(self):
		"""Only a live puzzle repaints its last scene; never a cooldown or an error."""
		return self.status in (app.CAPTCHA_STATUS_PENDING, app.CAPTCHA_STATUS_WRONG,
			app.CAPTCHA_STATUS_HELD)

	def CanInteract(self):
		return (self.IsShow() and self.status in (app.CAPTCHA_STATUS_PENDING,
			app.CAPTCHA_STATUS_WRONG, app.CAPTCHA_STATUS_HELD) and
			not self.submissionPending and self.deadlineAt > app.GetGlobalTimeStamp())

	def OpenChallenge(self, status, attemptsRemaining, sessionId, generation,
		deadlineAt, retryAt, pixels, originX=0, originY=0, heldPixels=b""):
		if status != app.CAPTCHA_STATUS_HELD:
			if sessionId != self.sessionId:
				self.stage = None
				self.kind = None
			self.readyPulse.Stop()
			image = status in (app.CAPTCHA_STATUS_PENDING, app.CAPTCHA_STATUS_WRONG)
			if not image:
				# The previous scene no longer exists on the server: forget it, so no
				# Esc/right-click/failed send can paint it back during the cooldown.
				self.canvas.ClearPointer()
				self.canvas.original = None
			elif not self.IsClickKind():
				self.instruction.SetText(CHEST_INSTRUCTION)
				self.ShowChestCopy()
				for label in self.bagLabels:
					label.SetFontColor(0.70, 0.68, 0.63)
			self.SetAttempts(attemptsRemaining)
			CaptchaWindow.OpenChallenge(self, status, attemptsRemaining, sessionId,
				generation, deadlineAt, retryAt, pixels)
			if not image or self.status == app.CAPTCHA_STATUS_ERROR:
				self.ShowWaitCopy()
			return
		if (sessionId, generation) != (self.sessionId, self.generation):
			return
		self.status = status
		try:
			self.canvas.SetHeld(pixels, originX, originY, heldPixels)
		except (ValueError, RuntimeError):
			self.status = app.CAPTCHA_STATUS_ERROR
			self.readyPulse.Stop()
			self.canvas.Hide()
			self.canvas.ClearPointer()
			self.feedback.SetText("Obrázek nelze zobrazit. Zkus se znovu přihlásit.")

	def SendClick(self, point):
		"""A click-kind answer: PICK at the clicked raster point, nothing else."""
		if self.SendPointer(3, point):
			self.canvas.ClearPointer()

	def SendPointer(self, action, start=(0, 0), end=(0, 0)):
		self.submissionPending = True
		try:
			sent = net.SendCaptchaV4(action, self.sessionId, self.generation,
				start[0], start[1], end[0], end[1])
		except (TypeError, ValueError, RuntimeError):
			sent = False
		if not sent:
			self.submissionPending = False
			self.canvas.ClearPointer()
			if self.canvas.original and self.CanShowScene():
				self.canvas.Paint(self.canvas.original)
			self.feedback.SetText("Tah se nepodařilo odeslat. Zkus to znovu.")
		return sent

	def OnPressEscapeKey(self):
		self.canvas.Cancel()
		return True
