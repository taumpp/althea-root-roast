import ui


class CrimsonWindowChrome(ui.Window):
	ASSET_ROOT = "local_target_board/flat_reference_v3/"
	BODY_ROOT = ASSET_ROOT + "body/"
	TARGET_ROOT = ASSET_ROOT + "target-crimson-seam/"
	BODY_FILL_WIDTH = 64
	BODY_FILL_HEIGHT = 64
	BODY_EDGE_WIDTH = 2
	BODY_EDGE_HEIGHT = 2
	BODY_EDGE_SOURCE_LENGTH = 64
	TARGET_CAP_WIDTH = 2
	TARGET_CENTER_WIDTH = 64
	TARGET_HEIGHT = 40
	DIVIDER_WIDTH = 64
	DIVIDER_HEIGHT = 1
	CONTENT_ALPHA = 0.70

	def __init__(self, with_titlebar=False):
		ui.Window.__init__(self)
		self.with_titlebar = bool(with_titlebar)
		self.dividers = []

		self.body_fill = self.__CreateImage(self.BODY_ROOT + "body-fill.png")
		self.body_fill.SetDiffuseColor(1.0, 1.0, 1.0, self.CONTENT_ALPHA)
		self.body_edge_left = self.__CreateImage(self.BODY_ROOT + "edge-left.png")
		self.body_edge_right = self.__CreateImage(self.BODY_ROOT + "edge-right.png")
		self.body_edge_bottom = self.__CreateImage(self.BODY_ROOT + "edge-bottom.png")
		self.body_corner_left = self.__CreateImage(self.BODY_ROOT + "corner-left-bottom.png")
		self.body_corner_right = self.__CreateImage(self.BODY_ROOT + "corner-right-bottom.png")

		self.target_left = None
		self.target_center = None
		self.target_right = None
		if self.with_titlebar:
			self.target_left = self.__CreateImage(self.TARGET_ROOT + "left.png")
			self.target_center = self.__CreateImage(self.TARGET_ROOT + "center.png")
			self.target_center.SetDiffuseColor(1.0, 1.0, 1.0, self.CONTENT_ALPHA)
			self.target_right = self.__CreateImage(self.TARGET_ROOT + "right.png")

	def __CreateImage(self, path):
		image = ui.ExpandedImageBox()
		image.SetParent(self)
		image.AddFlag("not_pick")
		image.LoadImage(path)
		image.Show()
		return image

	def __ScaleImage(self, image, width, height, source_width, source_height):
		image.SetScale(
			float(width) / float(source_width),
			float(height) / float(source_height),
		)

	def __SetBodyVisible(self, visible):
		for image in (
			self.body_fill,
			self.body_edge_left,
			self.body_edge_right,
			self.body_edge_bottom,
			self.body_corner_left,
			self.body_corner_right,
		):
			if visible:
				image.Show()
			else:
				image.Hide()

	def __LayoutBody(self, width, body_y, body_height):
		if body_height < self.BODY_EDGE_HEIGHT:
			self.__SetBodyVisible(False)
			return

		self.__SetBodyVisible(True)
		self.body_fill.SetPosition(0, body_y)
		self.__ScaleImage(
			self.body_fill,
			width, body_height, self.BODY_FILL_WIDTH, self.BODY_FILL_HEIGHT
		)

		edge_height = body_height - self.BODY_EDGE_HEIGHT
		self.body_edge_left.SetPosition(0, body_y)
		self.__ScaleImage(
			self.body_edge_left,
			self.BODY_EDGE_WIDTH, edge_height,
			self.BODY_EDGE_WIDTH, self.BODY_EDGE_SOURCE_LENGTH,
		)
		self.body_edge_right.SetPosition(width - self.BODY_EDGE_WIDTH, body_y)
		self.__ScaleImage(
			self.body_edge_right,
			self.BODY_EDGE_WIDTH, edge_height,
			self.BODY_EDGE_WIDTH, self.BODY_EDGE_SOURCE_LENGTH,
		)

		bottom_y = body_y + body_height - self.BODY_EDGE_HEIGHT
		bottom_width = width - self.BODY_EDGE_WIDTH * 2
		self.body_edge_bottom.SetPosition(self.BODY_EDGE_WIDTH, bottom_y)
		self.__ScaleImage(
			self.body_edge_bottom,
			bottom_width, self.BODY_EDGE_HEIGHT,
			self.BODY_EDGE_SOURCE_LENGTH, self.BODY_EDGE_HEIGHT,
		)
		self.body_corner_left.SetPosition(0, bottom_y)
		self.body_corner_right.SetPosition(width - self.BODY_EDGE_WIDTH, bottom_y)

	def __LayoutTarget(self, width, height):
		middle_width = width - self.TARGET_CAP_WIDTH * 2
		target_scale_x = float(middle_width) / float(self.TARGET_CENTER_WIDTH)
		target_scale_y = float(height) / float(self.TARGET_HEIGHT)
		self.target_left.SetPosition(0, 0)
		self.__ScaleImage(
			self.target_left,
			self.TARGET_CAP_WIDTH, height,
			self.TARGET_CAP_WIDTH, self.TARGET_HEIGHT,
		)
		self.target_center.SetPosition(self.TARGET_CAP_WIDTH, 0)
		self.target_center.SetScale(target_scale_x, target_scale_y)
		self.target_right.SetPosition(width - self.TARGET_CAP_WIDTH, 0)
		self.__ScaleImage(
			self.target_right,
			self.TARGET_CAP_WIDTH, height,
			self.TARGET_CAP_WIDTH, self.TARGET_HEIGHT,
		)
		self.target_left.Show()
		self.target_center.Show()
		self.target_right.Show()

	def CreateDivider(self, width):
		width = max(self.DIVIDER_WIDTH, int(width))
		divider = self.__CreateImage(self.BODY_ROOT + "divider.png")
		self.__ScaleImage(
			divider,
			width, self.DIVIDER_HEIGHT,
			self.DIVIDER_WIDTH, self.DIVIDER_HEIGHT,
		)
		self.dividers.append(divider)
		return divider

	def SetChromeSize(self, width, height):
		width = max(self.TARGET_CAP_WIDTH * 2 + 1, int(width))
		minimum_height = self.TARGET_HEIGHT if self.with_titlebar else self.BODY_EDGE_HEIGHT
		height = max(minimum_height, int(height))
		ui.Window.SetSize(self, width, height)

		if self.with_titlebar:
			self.__SetBodyVisible(False)
			self.__LayoutTarget(width, height)
		else:
			self.__LayoutBody(width, 0, height)

		self.Show()




class CrimsonScrollBar(ui.Window):
	ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/messenger/scrollbar/"
	TRACK_SOURCE_HEIGHT = 340.0
	THUMB_HEIGHT = 72
	WIDTH = 12

	def __init__(self):
		ui.Window.__init__(self)
		self.eventScroll = lambda *args: None
		self.curPos = 0.0
		self.scrollStep = 0.12
		self.barHeight = 100
		self.travel = 1

		self.track = ui.ExpandedImageBox()
		self.track.SetParent(self)
		self.track.LoadImage(self.ASSET_ROOT + "track.png")
		self.track.SetPosition(0, 0)
		self.track.AddFlag("not_pick")
		self.track.Show()

		self.thumb = ui.DragButton()
		self.thumb.SetParent(self)
		self.thumb.SetUpVisual(self.ASSET_ROOT + "thumb_normal.png")
		self.thumb.SetOverVisual(self.ASSET_ROOT + "thumb_hover.png")
		self.thumb.SetDownVisual(self.ASSET_ROOT + "thumb_pressed.png")
		self.thumb.SetMoveEvent(ui.__mem_func__(self.OnMove))
		self.thumb.Show()
		self.SetScrollBarSize(self.barHeight)

	def SetScrollBarSize(self, height):
		self.barHeight = max(self.THUMB_HEIGHT + 2, int(height))
		ui.Window.SetSize(self, self.WIDTH, self.barHeight)
		self.track.SetScale(1.0, float(self.barHeight) / self.TRACK_SOURCE_HEIGHT)
		self.travel = max(1, self.barHeight - self.THUMB_HEIGHT)
		self.thumb.SetRestrictMovementArea(2, 0, 2, self.barHeight)
		self.SetPos(self.curPos, False)

	def SetScrollEvent(self, event):
		self.eventScroll = event if event else (lambda *args: None)

	def SetScrollStep(self, step):
		self.scrollStep = float(step)

	def SetMiddleBarSize(self, pageScale):
		return

	def SetScale(self, visibleSize, fullSize):
		if float(fullSize or 0) <= float(visibleSize or 0):
			self.SetPos(0.0, False)

	def GetPos(self):
		return self.curPos

	def SetPos(self, pos, callEvent=True):
		self.curPos = max(0.0, min(1.0, float(pos)))
		self.thumb.SetPosition(2, int(round(self.travel * self.curPos)))
		if callEvent:
			self.eventScroll()

	def OnMove(self):
		_x, y = self.thumb.GetLocalPosition()
		self.curPos = max(0.0, min(1.0, float(y) / float(self.travel)))
		self.eventScroll()

	def OnMouseWheel(self, delta):
		if delta > 0:
			self.SetPos(self.curPos - self.scrollStep)
			return True
		if delta < 0:
			self.SetPos(self.curPos + self.scrollStep)
			return True
		return False

	def OnMouseLeftButtonDown(self):
		_x, y = self.GetMouseLocalPosition()
		self.SetPos(float(y - self.THUMB_HEIGHT // 2) / float(self.travel))


class SettingsScrollBar(ui.Window):
	ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/gameoption/scrollbar/"
	SCROLLBAR_WIDTH = 12
	SCROLL_BTN_XDIST = 2
	SCROLL_BTN_YDIST = 0
	TEMP_SPACE = 0
	MINIMUM_THUMB_HEIGHT = 20

	class MiddleBar(ui.DragButton):
		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.SetWindowName("scrollbar_middlebar")

		def MakeImage(self):
			top = ui.ExpandedImageBox()
			top.SetParent(self)
			top.LoadImage(SettingsScrollBar.ASSET_ROOT + "scrollbar_top.tga")
			top.AddFlag("not_pick")
			top.Show()
			topScale = ui.ExpandedImageBox()
			topScale.SetParent(self)
			topScale.SetPosition(0, top.GetHeight())
			topScale.LoadImage(SettingsScrollBar.ASSET_ROOT + "scrollbar_scale.tga")
			topScale.AddFlag("not_pick")
			topScale.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(SettingsScrollBar.ASSET_ROOT + "scrollbar_bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()
			bottomScale = ui.ExpandedImageBox()
			bottomScale.SetParent(self)
			bottomScale.LoadImage(SettingsScrollBar.ASSET_ROOT + "scrollbar_scale.tga")
			bottomScale.AddFlag("not_pick")
			bottomScale.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(SettingsScrollBar.ASSET_ROOT + "scrollbar_mid.tga")
			middle.AddFlag("not_pick")
			middle.Show()
			self.top = top
			self.topScale = topScale
			self.bottom = bottom
			self.bottomScale = bottomScale
			self.middle = middle

		def SetSize(self, height):
			minimum = self.top.GetHeight() + self.bottom.GetHeight() + self.middle.GetHeight()
			height = max(minimum, height)
			ui.DragButton.SetSize(self, 8, height)
			scale = (height - minimum) // 2
			extraScale = 1 if (height - minimum) % 2 else 0
			self.topScale.SetRenderingRect(0, 0, 0, scale - 1)
			self.middle.SetPosition(0, self.top.GetHeight() + scale)
			self.bottomScale.SetPosition(0, self.middle.GetBottom())
			self.bottomScale.SetRenderingRect(0, 0, 0, scale - 1 + extraScale)
			self.bottom.SetPosition(0, height - self.bottom.GetHeight())

	def __init__(self):
		ui.Window.__init__(self)
		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = None
		self.eventArgs = None
		self.lockFlag = False
		self.CreateScrollBar()
		self.SetScrollBarSize(0)
		self.scrollStep = 0.4
		self.SetWindowName("NONAME_ScrollBar")

	def __del__(self):
		ui.Window.__del__(self)

	def CreateScrollBar(self):
		self.topImage = ui.ExpandedImageBox()
		self.topImage.SetParent(self)
		self.topImage.AddFlag("not_pick")
		self.topImage.LoadImage(self.ASSET_ROOT + "scroll_top.tga")
		self.topImage.Show()
		self.bottomImage = ui.ExpandedImageBox()
		self.bottomImage.SetParent(self)
		self.bottomImage.AddFlag("not_pick")
		self.bottomImage.LoadImage(self.ASSET_ROOT + "scroll_bottom.tga")
		self.bottomImage.Show()
		self.middleImage = ui.ExpandedImageBox()
		self.middleImage.SetParent(self)
		self.middleImage.AddFlag("not_pick")
		self.middleImage.SetPosition(0, self.topImage.GetHeight())
		self.middleImage.LoadImage(self.ASSET_ROOT + "scroll_mid.tga")
		self.middleImage.Show()
		self.middleBar = self.MiddleBar()
		self.middleBar.SetParent(self)
		self.middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
		self.middleBar.Show()
		self.middleBar.MakeImage()
		self.middleBar.SetSize(12)

	def Destroy(self):
		self.eventScroll = None
		self.eventArgs = None

	def SetScrollEvent(self, event, *args):
		self.eventScroll = event
		self.eventArgs = args

	def SetMiddleBarSize(self, pageScale):
		self.middleBar.SetSize(int(pageScale * float(self.GetHeight() - (self.SCROLL_BTN_YDIST * 2))))
		self.pageSize = self.GetHeight() - (self.SCROLL_BTN_YDIST * 2) - self.middleBar.GetHeight()

	def SetScrollBarSize(self, height):
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.pageSize = height - self.SCROLL_BTN_YDIST * 2 - self.middleBar.GetHeight()
		scale = float((height - self.SCROLL_BTN_YDIST * 2) - self.middleImage.GetHeight()) / float(self.middleImage.GetHeight())
		self.middleImage.SetRenderingRect(0, 0, 0, scale)
		self.bottomImage.SetPosition(0, height - self.bottomImage.GetHeight())
		self.middleBar.SetRestrictMovementArea(
			self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST,
			self.middleBar.GetWidth(), height - self.SCROLL_BTN_YDIST * 2,
		)
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST)

	def SetScrollStep(self, step):
		self.scrollStep = step

	def GetScrollStep(self):
		return self.scrollStep

	def GetPos(self):
		return self.curPos

	def OnUp(self):
		self.SetPos(self.curPos - self.scrollStep)

	def OnDown(self):
		self.SetPos(self.curPos + self.scrollStep)

	def SetPos(self, pos, moveEvent=True):
		pos = max(0.0, min(1.0, pos))
		self.middleBar.SetPosition(
			self.SCROLL_BTN_XDIST,
			int(float(self.pageSize) * pos) + self.SCROLL_BTN_YDIST,
		)
		if moveEvent:
			self.OnMove()

	def OnMove(self):
		if self.lockFlag or self.pageSize == 0:
			return
		_x, y = self.middleBar.GetLocalPosition()
		self.curPos = float(y - self.SCROLL_BTN_YDIST) / float(self.pageSize)
		if self.eventScroll:
			self.eventScroll(*self.eventArgs)

	def OnMouseLeftButtonDown(self):
		_x, y = self.GetMouseLocalPosition()
		self.SetPos(float(y) / float(self.GetHeight()))

	def LockScroll(self):
		self.lockFlag = True

	def UnlockScroll(self):
		self.lockFlag = False
