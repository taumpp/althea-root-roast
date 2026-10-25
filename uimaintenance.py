import ui
import app
import localeInfo
import wndMgr
import weakref

import pvmhudposition

# The board can be dragged anywhere. Its position is a presentation preference of this client
# installation (not of one character): UserData/maintenance_hud, written when a drag ends.
POSITION_DIRECTORY = "UserData/maintenance_hud"
POSITION_KEY = "maintenance-board"
# Where the board sits until the player moves it: centred at the top of the screen.
DEFAULT_TOP = -13
# The server sends one announcement to a player more than once on older cores (and again when he
# enters the game); a packet that repeats the open announcement must not start it over.
SAME_ANNOUNCEMENT_SECONDS = 2


def LoadPosition():
	try:
		return pvmhudposition.load(POSITION_KEY, POSITION_DIRECTORY)
	except Exception:
		return None


def SavePosition(position):
	try:
		return pvmhudposition.save(POSITION_KEY, position, POSITION_DIRECTORY)
	except Exception:
		return False


class DragSurface(ui.Window):
	"""Transparent plate over the board: a left press starts the drag, the owner moves itself."""

	def __init__(self, owner):
		ui.Window.__init__(self)
		self.owner = weakref.proxy(owner)
		self.SetParent(owner)
		self.SetPosition(0, 0)
		self.AddFlag("dragable")
		self.Show()

	def OnMouseLeftButtonDown(self):
		self.owner.BeginDrag()
		return True

	def OnMouseDrag(self, x, y):
		self.owner.Drag()

	def OnMouseLeftButtonUp(self):
		self.owner.EndDrag()
		return True


class MaintenanceBoard(ui.ScriptWindow):

	def __init__(self):
		ui.ScriptWindow.__init__(self, "UI_BOTTOM")

		self.timeEnd = 0
		self.duration = 0
		self.savedPosition = LoadPosition()
		self.dragOrigin = None
		self.dragMoved = False
		self.screenSize = None

		self.LoadWindow()

		# Created after the script's children: it lies over the board and the text.
		self.dragSurface = DragSurface(self)

	def __del__(self):
		ui.ScriptWindow.__del__(self)

	def Destroy(self):
		self.EndDrag()
		self.Close()

	def LoadWindow(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/MaintenanceWindow.py")
		except:
			import exception
			exception.Abort("MaintenanceBoard.LoadDialog.LoadScript")

		try:
			GetObject=self.GetChild
			self.board = GetObject("board")
			self.desc = GetObject("desc")

		except:
			import exception
			exception.Abort("MaintenanceBoard.LoadDialog.BindObject")

	def Open(self, timeLeft, duration):
		timeEnd = app.GetTime() + timeLeft
		if self.IsShow() and duration == self.duration and abs(timeEnd - self.timeEnd) <= SAME_ANNOUNCEMENT_SECONDS:
			return

		self.timeEnd = timeEnd
		self.duration = duration
		self.Refresh(True)
		self.Show()

	def Close(self):
		self.EndDrag()
		self.duration = 0
		self.Hide()

	def GetScreenSize(self):
		return (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

	def GetPlace(self):
		if self.savedPosition is None:
			return ((wndMgr.GetScreenWidth() - self.GetWidth()) // 2, DEFAULT_TOP)
		return pvmhudposition.clamp(self.savedPosition, (self.GetWidth(), self.GetHeight()), self.GetScreenSize())

	def Place(self):
		x, y = self.GetPlace()
		self.SetPosition(x, y)
		self.screenSize = self.GetScreenSize()

	def Refresh(self, new_size = False):
		self.desc.SetText(localeInfo.MAINTENANCE_DESCRIPTION % (localeInfo.MaintenanceSecondToDHMS(max(0, int(self.timeEnd - app.GetTime()))), localeInfo.MaintenanceSecondToDHMS(self.duration)))

		if new_size == True or self.desc.GetWidth() + 30 > self.GetWidth():
			self.SetSize(self.desc.GetWidth() + 30, self.GetHeight())
			self.board.SetSize(self.GetWidth(), self.GetHeight())
			self.dragSurface.SetSize(self.GetWidth(), self.GetHeight())
			self.Place()
			self.desc.UpdateRect()
			self.Show()
		elif self.dragOrigin is None and self.screenSize != self.GetScreenSize():
			# A new resolution: a kept position may now lie outside the screen.
			self.Place()

	def OnUpdate(self):
		self.Refresh()

	def BeginDrag(self):
		self.SetTop()
		self.dragOrigin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
		self.dragMoved = False

	def Drag(self):
		if self.dragOrigin is None:
			return
		(mouseX, mouseY), (x, y) = self.dragOrigin
		nowX, nowY = wndMgr.GetMousePosition()
		if (nowX, nowY) != (mouseX, mouseY) or self.dragMoved:
			self.dragMoved = True
			self.savedPosition = pvmhudposition.clamp((x + nowX - mouseX, y + nowY - mouseY),
				(self.GetWidth(), self.GetHeight()), self.GetScreenSize())
			self.Place()

	def EndDrag(self):
		if self.dragOrigin is None:
			return
		self.dragOrigin = None
		if self.dragMoved and self.savedPosition is not None:
			SavePosition(self.savedPosition)
		self.dragMoved = False


# The last minute: a label the player hid comes back (without the X) and cannot be hidden again.
LAST_MINUTE = 60


class MaintenanceIndicator(ui.Window):
	"""What the interface holds for an announced maintenance: the R1 label (uimaintenancer1) in the R1
	look, today's table (MaintenanceBoard, draggable) with Settings -> "Stary vzhled" (old look) or when the R1 label fails
	(traced, the table takes over with the same announcement and R1 is not tried again).

	It keeps the announcement itself, so the two looks always agree: a packet that repeats the open one (the server
	sends it more than once) changes nothing - a label the player hid stays hidden; another start or duration, or a
	new announcement after a cancel, starts over and shows it again. Hiding is only in this client (nothing goes to the
	server or to the disk): the chat and the big notices go on. This window is an invisible 1 x 1 ticker (OnUpdate)
	while an announcement is open; it keeps the label's time, brings a hidden label back in the last minute and follows
	a change of the look."""

	def __init__(self):
		ui.Window.__init__(self)
		self.AddFlag("not_pick")
		self.SetSize(1, 1)

		self.legacy = MaintenanceBoard()
		self.label = None
		self.look = None
		self.r1Failed = False
		self.announced = False
		self.timeEnd = 0.0
		self.duration = 0
		self.total = 1
		self.reason = 0
		self.hidden = False
		self.tickKey = None
		self.shower = None
		self.party = None

	def __del__(self):
		ui.Window.__del__(self)

	def Destroy(self):
		self.__DropLabel()
		self.legacy.Destroy()
		self.announced = False
		self.look = None
		ui.Window.Hide(self)

	def SetNeighbours(self, shower, party):
		"""The affect icons and the party panel: the default place of the R1 label is beside / over them."""
		self.shower, self.party = shower, party
		if self.label:
			self.label.SetNeighbours(shower, party)

	def SetReason(self, reason):
		"""The id of the reason preset of this announcement (maintenance_reason <id>; 0 = none)."""
		try:
			self.reason = int(reason)
		except (TypeError, ValueError):
			self.reason = 0
		self.Tick(True)

	def Open(self, timeLeft, duration):
		timeEnd = app.GetTime() + timeLeft
		if self.announced and duration == self.duration and abs(timeEnd - self.timeEnd) <= SAME_ANNOUNCEMENT_SECONDS:
			return

		self.announced = True
		self.timeEnd = timeEnd
		self.duration = duration
		self.total = max(1, int(timeLeft))
		self.hidden = False
		if self.look == "legacy":
			self.legacy.Open(timeLeft, duration)
		ui.Window.Show(self)
		self.Tick(True)

	def Close(self):
		self.announced = False
		self.hidden = False
		self.reason = 0
		self.duration = 0
		self.tickKey = None
		self.legacy.Close()
		self.__DropLabel()
		self.look = None
		ui.Window.Hide(self)

	def Hide(self):
		# ui.Window.__init__ already calls Hide(), before __init__ made the parts: nothing to close yet.
		if "legacy" not in self.__dict__:
			ui.Window.Hide(self)
			return
		self.Close()

	def OnUpdate(self):
		self.Tick()

	def HideByPlayer(self):
		"""The X of the label: hidden until the last minute (the announcement and the chat go on)."""
		self.hidden = True
		if self.label:
			self.label.Hide()

	def Remaining(self):
		return max(0, int(self.timeEnd - app.GetTime()))

	def Tick(self, force = False):
		"""Once a second (or when told): the time left, the hidden label's return, the look."""
		if not self.announced:
			return
		remaining = self.Remaining()
		if not force and self.tickKey == (remaining, self.hidden):
			return
		self.tickKey = (remaining, self.hidden)
		if self.hidden and remaining <= LAST_MINUTE:
			self.hidden = False
		wanted = self.__WantedLook()
		if wanted != self.look:
			self.__Switch(wanted, remaining)
		if self.look == "r1":
			self.__TickLabel(remaining)

	def __WantedLook(self):
		if self.r1Failed:
			return "legacy"
		try:
			import uimaintenancer1
			return "r1" if uimaintenancer1.UseR1() else "legacy"
		except Exception:
			self.__FailR1()
			return "legacy"

	def __Switch(self, wanted, remaining):
		if self.look == "legacy":
			self.legacy.Close()
		elif self.label:
			self.label.Hide()
		self.look = wanted
		if wanted == "legacy":
			self.legacy.Open(remaining, self.duration)

	def __TickLabel(self, remaining):
		try:
			if self.label is None:
				import uimaintenancer1
				self.label = uimaintenancer1.Label(self.HideByPlayer)
				self.label.SetNeighbours(self.shower, self.party)
			if self.hidden:
				if self.label.IsShow():
					self.label.Hide()
				return
			self.label.SetState(remaining, self.duration, self.reason, self.total, remaining > LAST_MINUTE)
			if not self.label.IsShow():
				self.label.Show()
			self.label.Place()
		except Exception:
			self.__FailR1()
			if self.announced:
				self.__Switch("legacy", remaining)

	def __FailR1(self):
		self.r1Failed = True
		self.__DropLabel()
		try:
			import uimaintenancer1
			uimaintenancer1.Fail()
		except Exception:
			try:
				import dbg
				dbg.TraceError("R1 look of the maintenance label failed, the original table is used.")
			except Exception:
				pass

	def __DropLabel(self):
		label, self.label = self.label, None
		if label:
			try:
				label.Destroy()
			except Exception:
				pass
