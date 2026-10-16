import app
import ime
import grp
import snd
import wndMgr
import item
import skill
import localeInfo
import dbg
# MARK_BUG_FIX
import guild
# END_OF_MARK_BUG_FIX
import math

from _weakref import proxy

if app.ENABLE_WINDOW_RESIZE:
	from resizeexpr import Expr

import os
import osfInfo
import fontconfig
import uicrimsoncontrols

if app.ENABLE_WIKI:
	import WikiRenderTarget

from operator import truediv

BACKGROUND_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
DARK_COLOR = grp.GenerateColor(0.2, 0.2, 0.2, 1.0)
BRIGHT_COLOR = grp.GenerateColor(0.7, 0.7, 0.7, 1.0)

if localeInfo.IsCANADA():
	SELECT_COLOR = grp.GenerateColor(0.9, 0.03, 0.01, 0.4)
else:
	# SELECT_COLOR = grp.GenerateColor(0.0, 0.0, 0.5, 0.3)
	SELECT_COLOR = grp.GenerateColor(0.2, 0.0, 0.5, 0.8)

WHITE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 0.5)
HALF_WHITE_COLOR = grp.GenerateColor(1.0, 1.0, 1.0, 0.2)
CRIMSON_CONTROL_LABEL_COLOR = grp.GenerateColor(228 / 255.0, 218 / 255.0, 203 / 255.0, 1.0)
TOOLTIP_CORNER_PREFIX = "d:/ymir work/ui/game/tooltip/Tooltip_Corner_"
TOOLTIP_LINE_PREFIX = "d:/ymir work/ui/game/tooltip/Tooltip_Line_"
TOOLTIP_BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 179 / 255.0)


def SetCrimsonGameControlsEnabled(enabled):
	uicrimsoncontrols.SetGameControlsEnabled(enabled)

V31_CONTROL_ROOT = "d:/ymir work/ui/public/crimson/controls/"
V31_ACTION_ROOT = V31_CONTROL_ROOT + "actions/"
V31_ACTION_BUTTON_VISUALS = {
	"small_button_01.sub": V31_ACTION_ROOT + "small_normal.png",
	"small_button_02.sub": V31_ACTION_ROOT + "small_hover.png",
	"small_button_03.sub": V31_ACTION_ROOT + "small_pressed.png",
	"middle_button_01.sub": V31_ACTION_ROOT + "middle_normal.png",
	"middle_button_02.sub": V31_ACTION_ROOT + "middle_hover.png",
	"middle_button_03.sub": V31_ACTION_ROOT + "middle_pressed.png",
	"large_button_01.sub": V31_ACTION_ROOT + "large_normal.png",
	"large_button_02.sub": V31_ACTION_ROOT + "large_hover.png",
	"large_button_03.sub": V31_ACTION_ROOT + "large_pressed.png",
	"xlarge_button_01.sub": V31_ACTION_ROOT + "xlarge_normal.png",
	"xlarge_button_02.sub": V31_ACTION_ROOT + "xlarge_hover.png",
	"xlarge_button_03.sub": V31_ACTION_ROOT + "xlarge_pressed.png",
	"xlarge_thin_button_01.sub": V31_ACTION_ROOT + "xlarge_thin_normal.png",
	"xlarge_thin_button_02.sub": V31_ACTION_ROOT + "xlarge_thin_hover.png",
	"xlarge_thin_button_03.sub": V31_ACTION_ROOT + "xlarge_thin_pressed.png",
}
V31_ACTION_DISABLED_VISUALS = {
	"small_button_01.sub": V31_ACTION_ROOT + "small_disabled.png",
	"small_button_02.sub": V31_ACTION_ROOT + "small_disabled.png",
	"small_button_03.sub": V31_ACTION_ROOT + "small_disabled.png",
	"middle_button_01.sub": V31_ACTION_ROOT + "middle_disabled.png",
	"middle_button_02.sub": V31_ACTION_ROOT + "middle_disabled.png",
	"middle_button_03.sub": V31_ACTION_ROOT + "middle_disabled.png",
	"large_button_01.sub": V31_ACTION_ROOT + "large_disabled.png",
	"large_button_02.sub": V31_ACTION_ROOT + "large_disabled.png",
	"large_button_03.sub": V31_ACTION_ROOT + "large_disabled.png",
	"xlarge_button_01.sub": V31_ACTION_ROOT + "xlarge_disabled.png",
	"xlarge_button_02.sub": V31_ACTION_ROOT + "xlarge_disabled.png",
	"xlarge_button_03.sub": V31_ACTION_ROOT + "xlarge_disabled.png",
	"xlarge_thin_button_01.sub": V31_ACTION_ROOT + "xlarge_thin_disabled.png",
	"xlarge_thin_button_02.sub": V31_ACTION_ROOT + "xlarge_thin_disabled.png",
	"xlarge_thin_button_03.sub": V31_ACTION_ROOT + "xlarge_thin_disabled.png",
}
V31_CHOICE_BUTTON_VISUALS = {
	"small_button_01.sub": V31_CONTROL_ROOT + "buttons/small_01.tga",
	"small_button_02.sub": V31_CONTROL_ROOT + "buttons/small_02.tga",
	"small_button_03.sub": V31_CONTROL_ROOT + "buttons/small_03.tga",
	"middle_button_01.sub": V31_CONTROL_ROOT + "buttons/middle_01.tga",
	"middle_button_02.sub": V31_CONTROL_ROOT + "buttons/middle_02.tga",
	"middle_button_03.sub": V31_CONTROL_ROOT + "buttons/middle_03.tga",
	"large_button_01.sub": V31_CONTROL_ROOT + "buttons/large_01.tga",
	"large_button_02.sub": V31_CONTROL_ROOT + "buttons/large_02.tga",
	"large_button_03.sub": V31_CONTROL_ROOT + "buttons/large_03.tga",
	"xlarge_button_01.sub": V31_CONTROL_ROOT + "buttons/xlarge_01.tga",
	"xlarge_button_02.sub": V31_CONTROL_ROOT + "buttons/xlarge_02.tga",
	"xlarge_button_03.sub": V31_CONTROL_ROOT + "buttons/xlarge_03.tga",
	"tab_button_small_01.sub": V31_CONTROL_ROOT + "tabs/small_01.tga",
	"tab_button_small_02.sub": V31_CONTROL_ROOT + "tabs/small_02.tga",
	"tab_button_small_03.sub": V31_CONTROL_ROOT + "tabs/small_03.tga",
	"tab_button_large_01.sub": V31_CONTROL_ROOT + "tabs/large_01.tga",
	"tab_button_large_02.sub": V31_CONTROL_ROOT + "tabs/large_02.tga",
	"tab_button_large_03.sub": V31_CONTROL_ROOT + "tabs/large_03.tga",
	"xlarge_thin_button_01.sub": V31_CONTROL_ROOT + "buttons/xlarge_thin_01.tga",
	"xlarge_thin_button_02.sub": V31_CONTROL_ROOT + "buttons/xlarge_thin_02.tga",
	"xlarge_thin_button_03.sub": V31_CONTROL_ROOT + "buttons/xlarge_thin_03.tga",
	"small_thin_button_01.sub": V31_CONTROL_ROOT + "legacy/small_thin_01.tga",
	"small_thin_button_02.sub": V31_CONTROL_ROOT + "legacy/small_thin_02.tga",
	"small_thin_button_03.sub": V31_CONTROL_ROOT + "legacy/small_thin_03.tga",
	"long_button_01.sub": V31_CONTROL_ROOT + "legacy/long_01.tga",
	"long_button_02.sub": V31_CONTROL_ROOT + "legacy/long_02.tga",
	"long_button_03.sub": V31_CONTROL_ROOT + "legacy/long_03.tga",
	"largeb_button_01.tga": V31_CONTROL_ROOT + "legacy/largeb_01.tga",
	"largeb_button_02.tga": V31_CONTROL_ROOT + "legacy/largeb_02.tga",
	"largeb_button_03.tga": V31_CONTROL_ROOT + "legacy/largeb_03.tga",
	"tab_button_middle_01.sub": V31_CONTROL_ROOT + "tabs/middle_01.tga",
	"tab_button_middle_02.sub": V31_CONTROL_ROOT + "tabs/middle_02.tga",
	"tab_button_middle_03.sub": V31_CONTROL_ROOT + "tabs/middle_03.tga",
	"close_button_01.sub": V31_CONTROL_ROOT + "legacy/close_01.tga",
	"close_button_02.sub": V31_CONTROL_ROOT + "legacy/close_02.tga",
	"close_button_03.sub": V31_CONTROL_ROOT + "legacy/close_03.tga",
	"minimize_button_01.sub": V31_CONTROL_ROOT + "legacy/minimize_01.tga",
	"minimize_button_02.sub": V31_CONTROL_ROOT + "legacy/minimize_02.tga",
	"minimize_button_03.sub": V31_CONTROL_ROOT + "legacy/minimize_03.tga",
	"btn_plus_up.sub": V31_CONTROL_ROOT + "legacy/plus_01.tga",
	"btn_plus_over.sub": V31_CONTROL_ROOT + "legacy/plus_02.tga",
	"btn_plus_down.sub": V31_CONTROL_ROOT + "legacy/plus_03.tga",
	"btn_bigplus_up.sub": V31_CONTROL_ROOT + "legacy/bigplus_01.tga",
	"btn_bigplus_over.sub": V31_CONTROL_ROOT + "legacy/bigplus_02.tga",
	"btn_bigplus_down.sub": V31_CONTROL_ROOT + "legacy/bigplus_03.tga",
	"next_btn_01.sub": V31_CONTROL_ROOT + "legacy/next_01.tga",
	"next_btn_02.sub": V31_CONTROL_ROOT + "legacy/next_02.tga",
	"next_btn_03.sub": V31_CONTROL_ROOT + "legacy/next_03.tga",
	"prev_btn_01.sub": V31_CONTROL_ROOT + "legacy/prev_01.tga",
	"prev_btn_02.sub": V31_CONTROL_ROOT + "legacy/prev_02.tga",
	"prev_btn_03.sub": V31_CONTROL_ROOT + "legacy/prev_03.tga",
	"toggle_unselected.tga": V31_CONTROL_ROOT + "toggle/off.tga",
	"toggle_selected.tga": V31_CONTROL_ROOT + "toggle/on.tga",
}
V31_IMAGE_VISUALS = {
	"parameter_slot_00.sub": V31_CONTROL_ROOT + "inputs/parameter_00.tga",
	"parameter_slot_01.sub": V31_CONTROL_ROOT + "inputs/parameter_01.tga",
	"parameter_slot_02.sub": V31_CONTROL_ROOT + "inputs/parameter_02.tga",
	"parameter_slot_03.sub": V31_CONTROL_ROOT + "inputs/parameter_03.tga",
	"parameter_slot_04.sub": V31_CONTROL_ROOT + "inputs/parameter_04.tga",
	"parameter_slot_05.sub": V31_CONTROL_ROOT + "inputs/parameter_05.tga",
	"parameter_slot_06.sub": V31_CONTROL_ROOT + "inputs/parameter_06.tga",
	"parameter_slot_07.sub": V31_CONTROL_ROOT + "inputs/parameter_07.tga",
	"parameter_slot_100x18.sub": V31_CONTROL_ROOT + "inputs/parameter_100x18.tga",
	"slot_base.sub": V31_CONTROL_ROOT + "slot/slot_base.tga",
	"radio_unselected.tga": V31_CONTROL_ROOT + "radio/off.tga",
	"radio_selected.tga": V31_CONTROL_ROOT + "radio/on.tga",
	"option_title.tga": V31_CONTROL_ROOT + "sections/option_title.tga",
	"checkbox.tga": V31_CONTROL_ROOT + "checkbox/off_01.tga",
}

def _V31VisualBasename(filename):
	if not isinstance(filename, str):
		return ""
	return filename.replace("\\", "/").rsplit("/", 1)[-1].lower()

def ResolveV31ActionVisual(filename):
	basename = _V31VisualBasename(filename)
	return V31_ACTION_BUTTON_VISUALS.get(
		basename,
		V31_CHOICE_BUTTON_VISUALS.get(basename, filename),
	)

def ResolveV31DisabledActionVisual(filename):
	basename = _V31VisualBasename(filename)
	return V31_ACTION_DISABLED_VISUALS.get(
		basename,
		V31_CHOICE_BUTTON_VISUALS.get(basename, filename),
	)

def ResolveV31ChoiceVisual(filename):
	return V31_CHOICE_BUTTON_VISUALS.get(_V31VisualBasename(filename), filename)

def ResolveV31ImageVisual(filename):
	return V31_IMAGE_VISUALS.get(_V31VisualBasename(filename), filename)

createToolTipWindowDict = {}
_focused_edit_lines = set()


def IsEditLineFocused():
	return bool(_focused_edit_lines)


def RegisterCandidateWindowClass(codePage, candidateWindowClass):
	EditLine.candidateWindowClassDict[codePage] = candidateWindowClass
def RegisterToolTipWindow(type, createToolTipWindow):
	createToolTipWindowDict[type] = createToolTipWindow

if app.ENABLE_ITEMSHOP:
	def calculateRect(curValue, maxValue):
		try:
			return -1.0 + float(curValue) / float(maxValue)
		except:
			return 0.0

fonttype = 0
if app.ENABLE_FONT_OPTION and os.path.exists("UserData/font/fontoption.cfg"):
	fd = old_open("UserData/font/fontoption.cfg", "r")
	fonttype = fd.readline()
	fd.close()

fontconfig.ConfigureLevel(fonttype)
app.SetDefaultFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))

## Window Manager Event List##
##############################
## "OnMouseLeftButtonDown"
## "OnMouseLeftButtonUp"
## "OnMouseLeftButtonDoubleClick"
## "OnMouseRightButtonDown"
## "OnMouseRightButtonUp"
## "OnMouseRightButtonDoubleClick"
## "OnMouseDrag"
## "OnSetFocus"
## "OnKillFocus"
## "OnMouseOverIn"
## "OnMouseOverOut"
## "OnRender"
## "OnUpdate"
## "OnKeyDown"
## "OnKeyUp"
## "OnTop"
## "OnIMEUpdate" ## IME Only
## "OnIMETab"	## IME Only
## "OnIMEReturn" ## IME Only
##############################
## Window Manager Event List##


class __mem_func__:
	class __noarg_call__:
		def __init__(self, cls, obj, func):
			self.cls=cls
			self.obj=proxy(obj)
			self.func=proxy(func)

		def __call__(self, *arg):
			return self.func(self.obj)

	class __arg_call__:
		def __init__(self, cls, obj, func):
			self.cls=cls
			self.obj=proxy(obj)
			self.func=proxy(func)

		def __call__(self, *arg):
			return self.func(self.obj, *arg)

	def __init__(self, mfunc):
		if mfunc.__func__.__code__.co_argcount>1:
			self.call=__mem_func__.__arg_call__(mfunc.__self__.__class__, mfunc.__self__, mfunc.__func__)
		else:
			self.call=__mem_func__.__noarg_call__(mfunc.__self__.__class__, mfunc.__self__, mfunc.__func__)

	def __call__(self, *arg):
		return self.call(*arg)


class Window(object):
	def NoneMethod(cls):
		pass

	NoneMethod = classmethod(NoneMethod)

	def __init__(self, layer = "UI"):
		self.hWnd = None
		self.parentWindow = 0
		self.onMouseLeftButtonUpEvent = None
		if app.ENABLE_WINDOW_RESIZE:
			self.resizeDic = {}
		self.onRunMouseWheelEvent = None
		self.RegisterWindow(layer)
		self.Hide()

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.mouseLeftButtonDownEvent = None
			self.mouseLeftButtonDownArgs = None

		if app.ENABLE_ITEMSHOP:
			self.exPos = (0,0)

		if app.ENABLE_QUEST_RENEWAL:
			self.propertyList = {}

		if app.ENABLE_OFFLINE_SHOP:
			self.overInEvent = None
			self.overInArgs = None
			self.overOutEvent = None
			self.overOutArgs = None

		if app.ENABLE_EVENT_MANAGER:
			self.mouseLeftButtonDoubleClickEvent = None
			self.SetWindowName("NONAME_Window")

	def __del__(self):
		hWnd = getattr(self, "hWnd", None)
		if hWnd is not None:
			self.hWnd = None
			wndMgr.Destroy(hWnd)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.Register(self, layer)

	def Destroy(self):
		pass

	def GetWindowHandle(self):
		return self.hWnd

	def AddFlag(self, style):
		wndMgr.AddFlag(self.hWnd, style)

	def IsRTL(self):
		return wndMgr.IsRTL(self.hWnd)

	def SetWindowName(self, Name):
		wndMgr.SetName(self.hWnd, Name)

	def GetWindowName(self):
		return wndMgr.GetName(self.hWnd)

	def SetParent(self, parent):
		wndMgr.SetParent(self.hWnd, parent.hWnd)

	def SetParentProxy(self, parent):
		self.parentWindow=proxy(parent)
		wndMgr.SetParent(self.hWnd, parent.hWnd)

	def GetParentProxy(self):
		return self.parentWindow

	def SetPickAlways(self):
		wndMgr.SetPickAlways(self.hWnd)

	def SetWindowHorizontalAlignLeft(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_LEFT)

	def SetWindowHorizontalAlignCenter(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_CENTER)

	def SetWindowHorizontalAlignRight(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_RIGHT)

	def SetWindowVerticalAlignTop(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_TOP)

	def SetWindowVerticalAlignCenter(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_CENTER)

	def SetWindowVerticalAlignBottom(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_BOTTOM)

	def SetTop(self):
		wndMgr.SetTop(self.hWnd)

	def Show(self):
		wndMgr.Show(self.hWnd)

	def Hide(self):
		wndMgr.Hide(self.hWnd)

	def Lock(self):
		wndMgr.Lock(self.hWnd)

	def Unlock(self):
		wndMgr.Unlock(self.hWnd)

	def IsShow(self):
		return wndMgr.IsShow(self.hWnd)

	def UpdateRect(self):
		wndMgr.UpdateRect(self.hWnd)

	def SetSize(self, width, height):
		wndMgr.SetWindowSize(self.hWnd, width, height)

	def GetWidth(self):
		return wndMgr.GetWindowWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetWindowHeight(self.hWnd)

	if app.ENABLE_MULTIPLE_SELECT:
		def IsLeftMouseClicked(self):
			return wndMgr.IsLeftMouseClicked(self.hWnd)
			
		def IsRightMouseClicked(self):
			return wndMgr.IsRightMouseClicked(self.hWnd)

	if app.ENABLE_SHOP_SEARCH:
		def GetLocalPosition(self, parent = None):
			if parent:
				(my_x, my_y) = self.GetGlobalPosition()
				(parent_x, parent_y) = parent.GetGlobalPosition()
	
				return (my_x - parent_x, my_y - parent_y)
			else:
				return wndMgr.GetWindowLocalPosition(self.hWnd)
	else:
		def GetLocalPosition(self):
			return wndMgr.GetWindowLocalPosition(self.hWnd)

	if app.ENABLE_SEND_TARGET_INFO:
		def GetLeft(self):
			x, y = self.GetLocalPosition()
			return x

		def GetRight(self):
			return self.GetLeft() + self.GetWidth()

		def GetTop(self):
			x, y = self.GetLocalPosition()
			return y

		def GetBottom(self):
			return self.GetTop() + self.GetHeight()

	def GetGlobalPosition(self):
		return wndMgr.GetWindowGlobalPosition(self.hWnd)

	def GetMouseLocalPosition(self):
		return wndMgr.GetMouseLocalPosition(self.hWnd)

	def GetRect(self):
		return wndMgr.GetWindowRect(self.hWnd)

	if app.ENABLE_ITEMSHOP:
		def SetPosition(self, x, y, flag = False):
			if flag == True:
				self.exPos = (x,y)
			wndMgr.SetWindowPosition(self.hWnd, x, y)
	else:
		def SetPosition(self, x, y):
			wndMgr.SetWindowPosition(self.hWnd, x, y)

	def SetCenterPosition(self, x = 0, y = 0):
		self.SetPosition((wndMgr.GetScreenWidth() - self.GetWidth()) // 2 + x, (wndMgr.GetScreenHeight() - self.GetHeight()) // 2 + y)
		if app.ENABLE_WINDOW_RESIZE:
			self.SetResizeDic({"position": ((Expr("SCREEN_WIDTH") - self.GetWidth()) // 2 + x, (Expr("SCREEN_HEIGHT") - self.GetHeight()) // 2 + y)})

	def IsFocus(self):
		return wndMgr.IsFocus(self.hWnd)

	def SetFocus(self):
		wndMgr.SetFocus(self.hWnd)

	def KillFocus(self):
		wndMgr.KillFocus(self.hWnd)

	def GetChildCount(self):
		return wndMgr.GetChildCount(self.hWnd)

	if app.ENABLE_OFFLINE_SHOP:
		def IsIn(self, checkChilds = False):
			return wndMgr.IsIn(self.hWnd, checkChilds)
		
		def GetRenderBox(self):
			return wndMgr.GetRenderBox(self.hWnd)
		
		def SetInsideRender(self, val):
			wndMgr.SetInsideRender(self.hWnd, val)
		
		def IsInPosition(self):
			xMouse, yMouse = wndMgr.GetMousePosition()
			x, y = self.GetGlobalPosition()
			return xMouse >= x and xMouse < x + self.GetWidth() and yMouse >= y and yMouse < y + self.GetHeight()

		def SAFE_SetOverInEvent(self, func, *args):
			self.overInEvent = __mem_func__(func)
			self.overInArgs = args
		
		def SAFE_SetOverOutEvent(self, func, *args):
			self.overOutEvent = __mem_func__(func)
			self.overOutArgs = args
		
		def OnMouseOverIn(self):
			if self.overInEvent:
				self.overInEvent(*self.overInArgs)
		
		def OnMouseOverOut(self):
			if self.overOutEvent:
				self.overOutEvent(*self.overOutArgs)
		
		def AdjustSize(self):
			x, y = self.GetTextSize()
			wndMgr.SetWindowSize(self.hWnd, x, y)
	else:
		def IsIn(self):
			return wndMgr.IsIn(self.hWnd)

	if app.ENABLE_RENDER_TARGET_PREVIEW:
		def SetMouseLeftButtonDownEvent(self, event, *args):
			self.mouseLeftButtonDownEvent = event
			self.mouseLeftButtonDownArgs = args

		def OnMouseLeftButtonDown(self):
			if self.mouseLeftButtonDownEvent:
				self.mouseLeftButtonDownEvent(*self.mouseLeftButtonDownArgs)

		def SetOverEvent(self, func, *args):
			self.overFunc = func
			self.overArgs = args

		def SetOverOutEvent(self, func, *args):
			self.overOutFunc = func
			self.overOutArgs = args

	def SetOnMouseLeftButtonUpEvent(self, event):
		self.onMouseLeftButtonUpEvent = event

	def OnMouseLeftButtonUp(self):
		if self.onMouseLeftButtonUpEvent:
			self.onMouseLeftButtonUpEvent()

	def EnableScissorRect(self):
		wndMgr.EnableScissorRect(self.hWnd)

	def DisableScissorRect(self):
		wndMgr.DisableScissorRect(self.hWnd)

	def IsScissorRectEnabled(self):
		return wndMgr.IsScissorRectEnabled(self.hWnd)

	if app.ENABLE_WINDOW_RESIZE:
		def SetResizeDic(self, dic):
			self.resizeDic.update(dic)

		def OnResize(self):
			if self.resizeDic:
				for k, v in self.resizeDic.items():
					if k == "position":
						self.SetPosition(int(v[0]), int(v[1]))
					elif k == "size":
						self.SetSize(int(v[0]), int(v[1]))
					elif k == "scale":
						wndMgr.SetScale(self.hWnd, float(v[0]), float(v[1]))
					elif k == "rect":
						wndMgr.SetRenderingRect(self.hWnd, float(v[0]), float(v[1]), float(v[2]), float(v[3]))

	if app.ENABLE_QUEST_RENEWAL:
		def SetProperty(self, propName, propValue):
			self.propertyList[propName] = propValue

		def GetProperty(self, propName):
			if propName in self.propertyList:
				return self.propertyList[propName]

			return None

	def SetOnRunMouseWheelEvent(self, event):
		self.onRunMouseWheelEvent = event

	def OnRunMouseWheel(self, nLen):
		if self.onRunMouseWheelEvent:
			self.onRunMouseWheelEvent(*(bool(nLen < 0), ))
			return True

		return False

	def SetVisible(self, is_show):
		if is_show:
			self.Show()
		else:
			self.Hide()

	def SetMouseLeftButtonDoubleClickEvent(self, event):
		self.mouseLeftButtonDoubleClickEvent = event

	def OnMouseLeftButtonDoubleClick(self):
		if self.mouseLeftButtonDoubleClickEvent:
			self.mouseLeftButtonDoubleClickEvent()

	def SetClippingMaskWindow(self, clipping_mask_window):
		wndMgr.SetClippingMaskWindow(self.hWnd, clipping_mask_window.hWnd)

class WikiWindow(object):
	def NoneMethod(cls):
		pass

	NoneMethod = classmethod(NoneMethod)

	def __init__(self, layer = "UI"):
		self.hWnd = None
		self.parentWindow = 0
		self.onMouseLeftButtonUpEvent = None
		if app.ENABLE_WINDOW_RESIZE:
			self.resizeDic = {}

		self.onMouseWheelEvent=None
		self.mouseLeftButtonDownEvent = None
		self.mouseLeftButtonDownArgs = None

		self.eventDict={}
		self.eventFunc = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
		self.eventArgs = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}

		self.RegisterWindow(layer)

		if app.ENABLE_WIKI:
			self.exPos = (0,0)
			self.itsRendered = False
			self.itsNeedDoubleRender = False
			self.sortIndex = 0

		self.moveWindowEvent = None
		self.mouseLeftButtonUpEvent = None
		self.mouseLeftButtonUpArgs = None
		self.mouseLeftButtonDoubleClickEvent = None
		self.mouseRightButtonUpEvent = None
		self.mouseRightButtonUpArgs = None
		self.mouseRightButtonDownEvent = None
		self.mouseRightbuttonDownArgs = None
		self.renderEvent = None
		self.renderArgs = None

		self.mouseOverInEvent = None
		self.mouseOverInArgs = None

		self.mouseOverOutEvent = None
		self.mouseOverOutArgs = None

		if app.ENABLE_QUEST_RENEWAL:
			self.propertyList = {}

		self.overInEvent = None
		self.overInArgs = None
		self.overOutEvent = None
		self.overOutArgs = None
		self.baseX = 0
		self.baseY = 0
		self.SetWindowName("NONAME_Window")

		self.Hide()

	def __del__(self):
		hWnd = getattr(self, "hWnd", None)
		if hWnd is not None:
			self.hWnd = None
			wndMgr.Destroy(hWnd)
		self.eventFunc = None
		self.eventArgs = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.Register(self, layer)

	def Destroy(self):
		pass

	def GetWindowHandle(self):
		return self.hWnd

	def AddFlag(self, style):
		wndMgr.AddFlag(self.hWnd, style)

	def IsRTL(self):
		return wndMgr.IsRTL(self.hWnd)

	def SetWindowName(self, Name):
		wndMgr.SetName(self.hWnd, Name)

	def SetMouseRightButtonUpEvent(self, event, *args):
		self.mouseRightButtonUpEvent = event
		self.mouseRightButtonUpArgs = args

	def OnMouseRightButtonUp(self):
		if self.mouseRightButtonUpEvent:
			self.mouseRightButtonUpEvent(*self.mouseRightButtonUpArgs)

	def GetWindowName(self):
		return wndMgr.GetName(self.hWnd)

	def SetParent(self, parent):
		if parent:
			wndMgr.SetParent(self.hWnd, parent.hWnd)
		else:
			wndMgr.SetParent(self.hWnd, 0)

	def SetAttachParent(self, parent):
		wndMgr.SetAttachParent(self.hWnd, parent.hWnd)

	def SetParentProxy(self, parent):
		self.parentWindow=proxy(parent)
		wndMgr.SetParent(self.hWnd, parent.hWnd)


	def SAFE_SetStringEvent(self, event, func, *args):
		self.eventDict[event] =__mem_func__(func)
		self.eventArgs[event] = args

	def GetParentProxy(self):
		return self.parentWindow

	def SetPickAlways(self):
		wndMgr.SetPickAlways(self.hWnd)

	def SetWindowHorizontalAlignLeft(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_LEFT)

	def SetWindowHorizontalAlignCenter(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_CENTER)

	def SetWindowHorizontalAlignRight(self):
		wndMgr.SetWindowHorizontalAlign(self.hWnd, wndMgr.HORIZONTAL_ALIGN_RIGHT)

	def SetWindowVerticalAlignTop(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_TOP)

	def SetWindowVerticalAlignCenter(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_CENTER)

	def SetWindowVerticalAlignBottom(self):
		wndMgr.SetWindowVerticalAlign(self.hWnd, wndMgr.VERTICAL_ALIGN_BOTTOM)

	def SetTop(self):
		wndMgr.SetTop(self.hWnd)

	def Show(self):
		wndMgr.Show(self.hWnd)

	def Hide(self):
		wndMgr.Hide(self.hWnd)

	def Lock(self):
		wndMgr.Lock(self.hWnd)

	def Unlock(self):
		wndMgr.Unlock(self.hWnd)

	def IsShow(self):
		return wndMgr.IsShow(self.hWnd)

	def SetVisible(self, is_show):
		if is_show:
			self.Show()
		else:
			self.Hide()

	if app.ENABLE_QUEST_RENEWAL:
		def SetProperty(self, propName, propValue):
			self.propertyList[propName] = propValue

		def GetProperty(self, propName):
			if propName in self.propertyList:
				return self.propertyList[propName]

			return None

	def SetLeft(self, x):
		wndMgr.SetWindowPosition(self.hWnd, x, self.GetTop())

	def SetMoveWindowEvent(self, event):
		self.moveWindowEvent = event

	def OnMoveWindow(self, x, y):
		if self.moveWindowEvent:
			self.moveWindowEvent(x, y)

	def SAFE_SetOverInEvent(self, func, *args):
		self.overInEvent = __mem_func__(func)
		self.overInArgs = args

	def SetOverInEvent(self, func, *args):
		self.overInEvent = func
		self.overInArgs = args

	def SAFE_SetOverOutEvent(self, func, *args):
		self.overOutEvent = __mem_func__(func)
		self.overOutArgs = args

	def SetOverOutEvent(self, func, *args):
		self.overOutEvent = func
		self.overOutArgs = args

	def OnMouseOverIn(self):
		if self.overInEvent:
			self.overInEvent(*self.overInArgs)

	def OnMouseOverOut(self):
		if self.overOutEvent:
			self.overOutEvent(*self.overOutArgs)

	def SAFE_SetRenderEvent(self, event, *args):
		self.renderEvent = __mem_func__(event)
		self.renderArgs = args

	def ClearRenderEvent(self):
		self.renderEvent = None
		self.renderArgs = None

	def OnRender(self):
		if self.renderEvent:
			self.renderEvent(*self.renderArgs)

	def SetMouseLeftButtonDoubleClickEvent(self, event):
		self.mouseLeftButtonDoubleClickEvent = event

	def OnMouseLeftButtonDoubleClick(self):
		if self.mouseLeftButtonDoubleClickEvent:
			self.mouseLeftButtonDoubleClickEvent()

	def SetMouseRightButtonDownEvent(self, event, *args):
		self.mouseRightButtonDownEvent = event
		self.mouseRightButtonDownArgs = args

	def OnMouseRightButtonDown(self):
		if self.mouseRightButtonDownEvent:
			self.mouseRightButtonDownEvent(*self.mouseRightButtonDownArgs)

	def UpdateRect(self):
		wndMgr.UpdateRect(self.hWnd)

	def SetSize(self, width, height):
		wndMgr.SetWindowSize(self.hWnd, width, height)

	def GetWidth(self):
		return wndMgr.GetWindowWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetWindowHeight(self.hWnd)

	def GetLocalPosition(self):
		return wndMgr.GetWindowLocalPosition(self.hWnd)

	def GetGlobalPosition(self):
		return wndMgr.GetWindowGlobalPosition(self.hWnd)

	def GetMouseLocalPosition(self):
		return wndMgr.GetMouseLocalPosition(self.hWnd)

	def GetRect(self):
		return wndMgr.GetWindowRect(self.hWnd)

	def GetLeft(self):
		x, y = self.GetLocalPosition()
		return x

	def GetGlobalLeft(self):
		x, y = self.GetGlobalPosition()
		return x

	def GetGlobalTop(self):
		x, y = self.GetGlobalPosition()
		return y

	def GetRight(self):
		return self.GetLeft() + self.GetWidth()

	def GetTop(self):
		x, y = self.GetLocalPosition()
		return y

	def GetBottom(self):
		return self.GetTop() + self.GetHeight()

	if app.ENABLE_WIKI:
		def SetPosition(self, x, y, flag = False):
			if flag == True:
				self.exPos = (x,y)
			wndMgr.SetWindowPosition(self.hWnd, x, y)
	else:
		def SetPosition(self, x, y):
			wndMgr.SetWindowPosition(self.hWnd, x, y)

	def SetCenterPosition(self, x = 0, y = 0):
		self.SetPosition((wndMgr.GetScreenWidth() - self.GetWidth()) // 2 + x, (wndMgr.GetScreenHeight() - self.GetHeight()) // 2 + y)

	def SavePosition(self):
		self.baseX = self.GetLeft()
		self.baseY = self.GetTop()

	def UpdatePositionByScale(self, scale):
		self.SetPosition(self.baseX * scale, self.baseY * scale)

	def SetMouseLeftButtonDownEvent(self, event, *args):
		self.mouseLeftButtonDownEvent = event
		self.mouseLeftButtonDownArgs = args

	def OnMouseLeftButtonDown(self):
		if self.mouseLeftButtonDownEvent:
			self.mouseLeftButtonDownEvent(*self.mouseLeftButtonDownArgs)

	def IsFocus(self):
		return wndMgr.IsFocus(self.hWnd)

	def SetFocus(self):
		wndMgr.SetFocus(self.hWnd)

	def KillFocus(self):
		wndMgr.KillFocus(self.hWnd)

	def GetChildCount(self):
		return wndMgr.GetChildCount(self.hWnd)

	if app.ENABLE_WIKI:
		def IsIn(self, checkChilds = False):
			return wndMgr.IsIn(self.hWnd, checkChilds)
		def GetRenderBox(self):
			return wndMgr.GetRenderBox(self.hWnd)
		def SetInsideRender(self, val):
			wndMgr.SetInsideRender(self.hWnd, val)
		def IsInPosition(self):
			xMouse, yMouse = wndMgr.GetMousePosition()
			x, y = self.GetGlobalPosition()
			return xMouse >= x and xMouse < x + self.GetWidth() and yMouse >= y and yMouse < y + self.GetHeight()
	else:
		def IsIn(self):
			return wndMgr.IsIn(self.hWnd)

	if app.ENABLE_WINDOW_RESIZE:
		def SetResizeDic(self, dic):
			self.resizeDic.update(dic)

		def OnResize(self):
			if self.resizeDic:
				for k, v in self.resizeDic.items():
					if k == "position":
						self.SetPosition(int(v[0]), int(v[1]))
					elif k == "size":
						self.SetSize(int(v[0]), int(v[1]))
					elif k == "scale":
						wndMgr.SetScale(self.hWnd, float(v[0]), float(v[1]))
					elif k == "rect":
						wndMgr.SetRenderingRect(self.hWnd, float(v[0]), float(v[1]), float(v[2]), float(v[3]))

	def SetMouseLeftButtonUpEvent(self, event, *args):
		self.mouseLeftButtonUpEvent = event
		self.mouseLeftButtonUpArgs = args

	def SetOnMouseLeftButtonUpEvent(self, event):
		self.mouseLeftButtonUpEvent = event

	def SetMouseOverInEvent(self, event, *args):
		self.mouseOverInEvent = event
		self.mouseOverInArgs = args

	def SetMouseOverOutEvent(self, event, *args):
		self.mouseOverOutEvent = event
		self.mouseOverOutArgs = args


	def OnMouseLeftButtonUp(self):
		if self.mouseLeftButtonUpEvent:
			self.mouseLeftButtonUpEvent()

	def SetMouseWheelEvent(self, event):
		self.onMouseWheelEvent = event

	def OnMouseWheel(self, delta):
		# print("OnMouseWheel delta %d" % delta)
		if self.onMouseWheelEvent:
			return self.onMouseWheelEvent(delta)
		return False

	def SetAlpha(self, alpha):
		wndMgr.SetDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)

	def SetClippingMaskWindow(self, clipping_mask_window):
		wndMgr.SetClippingMaskWindow(self.hWnd, clipping_mask_window.hWnd)

class ListBoxEx(Window):
	class Item(Window):
		def __init__(self):
			Window.__init__(self)

		def __del__(self):
			Window.__del__(self)

		def SetParent(self, parent):
			Window.SetParent(self, parent)
			self.parent=proxy(parent)

		def OnMouseLeftButtonDown(self):
			self.parent.SelectItem(self)

		def OnRender(self):
			if self.parent.GetSelectedItem()==self:
				self.OnSelectedRender()

		def OnSelectedRender(self):
			x, y = self.GetGlobalPosition()
			grp.SetColor(grp.GenerateColor(0.0, 0.0, 0.7, 0.7))
			grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())

	def __init__(self):
		Window.__init__(self)

		self.viewItemCount = 10
		self.basePos = 0
		self.itemHeight = 16
		self.itemStep = 20
		self.selItem = 0
		self.itemList=[]
		self.onSelectItemEvent = lambda *arg: None

		if localeInfo.IsARABIC():
			self.itemWidth = 130
		else:
			self.itemWidth = 100

		self.scrollBar = None
		self.__UpdateSize()

	def __del__(self):
		Window.__del__(self)

	def __UpdateSize(self):
		height = self.itemStep * self.__GetViewItemCount()

		self.SetSize(self.itemWidth, height)

	def IsEmpty(self):
		if len(self.itemList) == 0:
			return 1
		return 0

	def SetItemStep(self, itemStep):
		self.itemStep = itemStep
		self.__UpdateSize()

	def SetItemSize(self, itemWidth, itemHeight):
		self.itemWidth = itemWidth
		self.itemHeight = itemHeight
		self.__UpdateSize()

	def SetViewItemCount(self, viewItemCount):
		self.viewItemCount = viewItemCount

	def SetSelectEvent(self, event):
		self.onSelectItemEvent = event

	def SetBasePos(self, basePos):
		for oldItem in self.itemList[self.basePos:self.basePos + self.viewItemCount]:
			oldItem.Hide()

		self.basePos = basePos

		pos = basePos
		for newItem in self.itemList[self.basePos : self.basePos + self.viewItemCount]:
			(x, y) = self.GetItemViewCoord(pos, newItem.GetWidth())
			newItem.SetPosition(x, y)
			newItem.Show()
			pos += 1

	def GetItemIndex(self, argItem):
		return self.itemList.index(argItem)

	def GetSelectedItem(self):
		return self.selItem

	def SelectIndex(self, index):
		if index >= len(self.itemList) or index < 0:
			self.selItem = None
			return

		try:
			self.selItem = self.itemList[index]
		except:
			pass

	def SelectItem(self, selItem):
		self.selItem = selItem
		self.onSelectItemEvent(selItem)

	def RemoveAllItems(self):
		self.selItem = None
		self.itemList = []

		if self.scrollBar:
			self.scrollBar.SetPos(0)

	if app.ENABLE_SWITCHBOT_SYSTEM:
		def GetItems(self):
			return self.itemList

	def RemoveItem(self, delItem):
		if delItem == self.selItem:
			self.selItem = None

		self.itemList.remove(delItem)

	def AppendItem(self, newItem):
		newItem.SetParent(self)
		newItem.SetSize(self.itemWidth, self.itemHeight)

		pos = len(self.itemList)
		if self.__IsInViewRange(pos):
			(x, y) = self.GetItemViewCoord(pos, newItem.GetWidth())
			newItem.SetPosition(x, y)
			newItem.Show()
		else:
			newItem.Hide()

		self.itemList.append(newItem)

	def SetScrollBar(self, scrollBar):
		scrollBar.SetScrollEvent(__mem_func__(self.__OnScroll))
		self.scrollBar = scrollBar

	def __OnScroll(self):
		self.SetBasePos(int(self.scrollBar.GetPos() * self.__GetScrollLen()))

	def __GetScrollLen(self):
		scrollLen = self.__GetItemCount() - self.__GetViewItemCount()
		if scrollLen < 0:
			return 0

		return scrollLen

	def __GetViewItemCount(self):
		return self.viewItemCount

	def __GetItemCount(self):
		return len(self.itemList)

	if app.ENABLE_OFFLINE_SHOP:
		def GetItemCount(self):
			return len(self.itemList)

	def GetItemViewCoord(self, pos, itemWidth):
		if localeInfo.IsARABIC():
			return (self.GetWidth() - itemWidth - 10, (pos-self.basePos) * self.itemStep)
		else:
			return (0, (pos - self.basePos) * self.itemStep)

	def __IsInViewRange(self, pos):
		if pos < self.basePos:
			return 0

		if pos >= self.basePos + self.viewItemCount:
			return 0

		return 1

class CandidateListBox(ListBoxEx):

	HORIZONTAL_MODE = 0
	VERTICAL_MODE = 1

	class Item(ListBoxEx.Item):
		def __init__(self, text):
			ListBoxEx.Item.__init__(self)

			self.textBox=TextLine()
			self.textBox.SetParent(self)
			self.textBox.SetText(text)
			self.textBox.Show()

		def __del__(self):
			ListBoxEx.Item.__del__(self)

	def __init__(self, mode = HORIZONTAL_MODE):
		ListBoxEx.__init__(self)
		self.itemWidth=32
		self.itemHeight=32
		self.mode = mode

	def __del__(self):
		ListBoxEx.__del__(self)

	def SetMode(self, mode):
		self.mode = mode

	def AppendItem(self, newItem):
		ListBoxEx.AppendItem(self, newItem)

	def GetItemViewCoord(self, pos):
		if self.mode == self.HORIZONTAL_MODE:
			return ((pos-self.basePos)*self.itemStep, 0)
		elif self.mode == self.VERTICAL_MODE:
			return (0, (pos-self.basePos)*self.itemStep)

class TextLine(Window):
	def __init__(self):
		Window.__init__(self)
		self.max = 0
		self.SetFontName(localeInfo.UI_DEF_FONT)

	def __del__(self):
		Window.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterTextLine(self, layer)

	if app.ENABLE_OFFLINE_SHOP:
		def GetRenderPos(self):
			return wndMgr.GetRenderPos(self.hWnd)

		def SetFixedRenderPos(self, startPos, endPos):
			wndMgr.SetFixedRenderPos(self.hWnd, startPos, endPos)

	def SetMax(self, max):
		wndMgr.SetMax(self.hWnd, max)

	def SetLimitWidth(self, width):
		wndMgr.SetLimitWidth(self.hWnd, width)

	def SetMultiLine(self):
		wndMgr.SetMultiLine(self.hWnd, True)

	def SetHorizontalAlignArabic(self):
		wndMgr.SetHorizontalAlign(self.hWnd, wndMgr.TEXT_HORIZONTAL_ALIGN_ARABIC)

	def SetHorizontalAlignLeft(self):
		wndMgr.SetHorizontalAlign(self.hWnd, wndMgr.TEXT_HORIZONTAL_ALIGN_LEFT)

	def SetHorizontalAlignRight(self):
		wndMgr.SetHorizontalAlign(self.hWnd, wndMgr.TEXT_HORIZONTAL_ALIGN_RIGHT)

	def SetHorizontalAlignCenter(self):
		wndMgr.SetHorizontalAlign(self.hWnd, wndMgr.TEXT_HORIZONTAL_ALIGN_CENTER)

	def SetVerticalAlignTop(self):
		wndMgr.SetVerticalAlign(self.hWnd, wndMgr.TEXT_VERTICAL_ALIGN_TOP)

	def SetVerticalAlignBottom(self):
		wndMgr.SetVerticalAlign(self.hWnd, wndMgr.TEXT_VERTICAL_ALIGN_BOTTOM)

	def SetVerticalAlignCenter(self):
		wndMgr.SetVerticalAlign(self.hWnd, wndMgr.TEXT_VERTICAL_ALIGN_CENTER)

	def SetSecret(self, Value=True):
		wndMgr.SetSecret(self.hWnd, Value)

	def SetOutline(self, Value=True):
		wndMgr.SetOutline(self.hWnd, Value)

	def SetFeather(self, value=True):
		wndMgr.SetFeather(self.hWnd, value)

	def SetFontName(self, fontName):
		wndMgr.SetFontName(self.hWnd, fontName)

	def SetDefaultFontName(self):
		wndMgr.SetFontName(self.hWnd, localeInfo.UI_DEF_FONT)

	def SetFontColor(self, red, green, blue):
		wndMgr.SetFontColor(self.hWnd, red, green, blue)

	def SetTextColor(self, color):
		self.SetPackedFontColor(color)

	def SetPackedFontColor(self, color):
		wndMgr.SetFontColor(self.hWnd, color)

	def SetText(self, text):
		wndMgr.SetText(self.hWnd, text)

	def GetTextLineCount(self):
		return wndMgr.GetTextLineCount(self.hWnd)

	def DisableEnterToken(self):
		wndMgr.DisableEnterToken(self.hWnd)

	def SetLineHeight(self, Height):
		wndMgr.SetLineHeight(self.hWnd, Height)

	def GetLineHeight(self):
		return wndMgr.GetLineHeight(self.hWnd)

	def GetText(self):
		return wndMgr.GetText(self.hWnd)

	def GetTextSize(self):
		return wndMgr.GetTextSize(self.hWnd)

	def GetTextWidth(self):
		w, h = self.GetTextSize()
		return w

	def GetTextHeight(self):
		w, h = self.GetTextSize()
		return h

	def SetAllAlign(self):
		self.SetHorizontalAlignCenter()
		self.SetVerticalAlignCenter()
		self.SetWindowHorizontalAlignCenter()
		self.SetWindowVerticalAlignCenter()

	if app.ENABLE_OFFLINE_SHOP:
		def GetSpecificTextWidth(self, text):
			return wndMgr.GetSpecificTextWidth(self.hWnd, text)

class EmptyCandidateWindow(Window):
	def __init__(self):
		Window.__init__(self)

	def __del__(self):
		Window.__del__(self)

	def Load(self):
		pass

	def SetCandidatePosition(self, x, y, textCount):
		pass

	def Clear(self):
		pass

	def Append(self, text):
		pass

	def Refresh(self):
		pass

	def Select(self):
		pass

class EditLine(TextLine):
	candidateWindowClassDict = {}

	def __init__(self):
		TextLine.__init__(self)

		if app.WJ_MULTI_TEXTLINE:
			self.DisableEnterToken()
		self.eventReturn = Window.NoneMethod
		self.eventEscape = Window.NoneMethod
		self.eventTab = None
		self.numberMode = False
		self.UseCodePage = True #MT-679 개인 상점 타이틀의 CodePage 이슈
		self.useIME = True
		self.infoMsg = ""
		self.backText=None
		self.isNeedEmpty=True
		self.bCodePage = False

		self.candidateWindowClass = None
		self.candidateWindow = None
		self.SetCodePage(app.GetDefaultCodePage())

		if app.ENABLE_OFFLINE_SHOP:
			self.eventUpdate = None
			self.overLay = TextLine()
			self.overLay.SetParent(self)
			self.overLay.SetPosition(0, 0)
			self.overLay.SetPackedFontColor(WHITE_COLOR)
			self.overLay.Hide()

		self.onSetFocusEvent = None
		self.onKillFocusEvent = None
		self.eventUpArrow = None
		self.eventDownArrow = None

		self.readingWnd = ReadingWnd()
		self.readingWnd.Hide()

	def __del__(self):
		_focused_edit_lines.discard(self.hWnd)
		TextLine.__del__(self)

		self.eventReturn = Window.NoneMethod
		self.eventEscape = Window.NoneMethod
		self.eventTab = None

	def SetCodePage(self, codePage):
		candidateWindowClass=EditLine.candidateWindowClassDict.get(codePage, EmptyCandidateWindow)
		self.__SetCandidateClass(candidateWindowClass)

	def SetInfoMessage(self, msg):
		self.infoMsg = msg
		if self.backText == None:
			self.backText = TextLine()
			self.backText.SetParent(self)
			self.backText.SetPosition(0,0)
			self.backText.SetFontColor(128,128,128)

		self.backText.SetText(msg)
		self._RefreshBackTextVisible()

	def _RefreshBackTextVisible(self):
		if self.backText == None:
			return
		if self.isNeedEmpty:
			if len(self.GetText()) > 0:
				self.backText.Hide()
			else:
				self.backText.Show()
		else:
			self.backText.Show()

	def __SetCandidateClass(self, candidateWindowClass):
		if self.candidateWindowClass==candidateWindowClass:
			return

		self.candidateWindowClass = candidateWindowClass
		self.candidateWindow = self.candidateWindowClass()
		self.candidateWindow.Load()
		self.candidateWindow.Hide()

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterTextLine(self, layer)

	def SAFE_SetReturnEvent(self, event):
		self.eventReturn = __mem_func__(event)

	def SetReturnEvent(self, event):
		self.eventReturn = event

	def SetEscapeEvent(self, event):
		self.eventEscape = event

	def SetTabEvent(self, event):
		self.eventTab = event

	if app.ENABLE_OFFLINE_SHOP:
		def SetOverlayText(self, text):
			self.overLay.SetText(text)
			self.__RefreshOverlay()
		
		def GetOverlayText(self):
			return self.overLay.GetText()
		
		def SetUpdateEvent(self, event):
			self.eventUpdate = event
		
		def GetDisplayText(self):
			if len(self.GetText()):
				return self.GetText()
			else:
				return self.overLay.GetText()
		
		def __RefreshOverlay(self):
			if len(self.GetText()):
				self.overLay.Hide()
			else:
				self.overLay.Show()

		def HideOverLay(self):
			if self.overLay:
				self.overLay.Hide()

		def IsShowCursor(self):
			return wndMgr.IsShowCursor(self.hWnd)

	def SetMax(self, max):
		self.max = max
		wndMgr.SetMax(self.hWnd, self.max)
		ime.SetMax(self.max)
		self.SetUserMax(self.max)

	def SetUserMax(self, max):
		self.userMax = max
		ime.SetUserMax(self.userMax)

	def CanEdit(self, flag):
		self.CanClick = flag

	def SetNumberMode(self):
		self.numberMode = True

	def SetOnFocusEvent(self, event):
		self.onSetFocusEvent = event
	
	def SetKillFocusEvent(self, event):
		self.onKillFocusEvent = event

	def SetUpArrowEvent(self, event):
		self.eventUpArrow = event

	def SetDownArrowEvent(self, event):
		self.eventDownArrow = event

	#MT-679 개인 상점 타이틀의 CodePage 이슈
	def SetUseCodePage(self, bUse = True):
		self.UseCodePage = bUse

	#def AddExceptKey(self, key):
	#	ime.AddExceptKey(key)

	#def ClearExceptKey(self):
	#	ime.ClearExceptKey()

	def SetIMEFlag(self, flag):
		self.useIME = flag

	def SetText(self, text):
		wndMgr.SetText(self.hWnd, text)

		if self.IsFocus():
			ime.SetText(text)

		if app.ENABLE_OFFLINE_SHOP:
			self.__RefreshOverlay()

		self._RefreshBackTextVisible()

	def Enable(self):
		wndMgr.ShowCursor(self.hWnd)

	def Disable(self):
		wndMgr.HideCursor(self.hWnd)

	def SetEndPosition(self):
		ime.MoveEnd()

	def OnSetFocus(self):
		_focused_edit_lines.add(self.hWnd)
		Text = self.GetText()
		ime.SetText(Text)
		ime.SetMax(self.max)
		ime.SetUserMax(self.userMax)
		ime.SetCursorPosition(-1)
		if self.numberMode:
			ime.SetNumberMode()
		else:
			ime.SetStringMode()
		ime.EnableCaptureInput()
		if self.useIME:
			ime.EnableIME()
		else:
			ime.DisableIME()

		if self.onSetFocusEvent:
			self.onSetFocusEvent()

		wndMgr.ShowCursor(self.hWnd, True)
		self._RefreshBackTextVisible()
		self.__RefreshOverlay()

	def OnKillFocus(self):
		_focused_edit_lines.discard(self.hWnd)
		self.SetText(ime.GetText(self.bCodePage))
		self.OnIMECloseCandidateList()
		self.OnIMECloseReadingWnd()
		ime.DisableIME()
		ime.DisableCaptureInput()
		wndMgr.HideCursor(self.hWnd)
		self.__RefreshOverlay()

		if self.onKillFocusEvent:
			self.onKillFocusEvent()

	def OnIMEChangeCodePage(self):
		self.SetCodePage(ime.GetCodePage())

	def OnIMEOpenCandidateList(self):
		self.candidateWindow.Show()
		self.candidateWindow.Clear()
		self.candidateWindow.Refresh()

		gx, gy = self.GetGlobalPosition()
		self.candidateWindow.SetCandidatePosition(gx, gy, len(self.GetText()))

		return True

	def OnIMECloseCandidateList(self):
		self.candidateWindow.Hide()
		return True

	def OnIMEOpenReadingWnd(self):
		gx, gy = self.GetGlobalPosition()
		textlen = len(self.GetText())-2
		reading = ime.GetReading()
		readinglen = len(reading)
		self.readingWnd.SetReadingPosition( gx + textlen*6-24-readinglen*6, gy )
		self.readingWnd.SetText(reading)
		if ime.GetReadingError() == 0:
			self.readingWnd.SetTextColor(0xffffffff)
		else:
			self.readingWnd.SetTextColor(0xffff0000)
		self.readingWnd.SetSize(readinglen * 6 + 4, 19)
		self.readingWnd.Show()
		return True

	def OnIMECloseReadingWnd(self):
		self.readingWnd.Hide()
		return True

	def IsNumber(self, text) :
		try :
			int(text)
			return True
		except ValueError :
			return False

	def IsIncludeCodePage(self, text) :
		textLen = len(text)
		idx = 0

		while(idx < textLen) :
			n = text.find("@", idx)

			if n == -1 :
				break
			elif n+4 < textLen and self.IsNumber(text[n+1:n+4]) == True:
				return True
			else:
				idx = n + 1

		return False

	def OnIMEUpdate(self):
		# MT-679 개인 상점 타이틀의 CodePage 이슈
		if self.UseCodePage == False and self.IsIncludeCodePage(ime.GetText(self.bCodePage)) == True :
			ime.SetText("")

		snd.PlaySound("sound/ui/type.wav")
		TextLine.SetText(self, ime.GetText(self.bCodePage))

		self._RefreshBackTextVisible()

		if app.ENABLE_OFFLINE_SHOP:
			self.__RefreshOverlay()
			if self.eventUpdate:
				self.eventUpdate()

	def OnIMETab(self):
		if self.eventTab:
			self.eventTab()
			return True

		return False

	def OnIMEReturn(self):
		snd.PlaySound("sound/ui/click.wav")
		self.eventReturn()

		return True

	def OnPressEscapeKey(self):
		self.eventEscape()
		return True

	def OnKeyDown(self, key):
		if app.DIK_F1 == key:
			return False
		if app.DIK_F2 == key:
			return False
		if app.DIK_F3 == key:
			return False
		if app.DIK_F4 == key:
			return False
		if app.DIK_LALT == key:
			return False
		if app.DIK_SYSRQ == key:
			return False
		if app.DIK_LCONTROL == key:
			return False

		return True

	def OnKeyUp(self, key):
		if app.DIK_F1 == key:
			return False
		if app.DIK_F2 == key:
			return False
		if app.DIK_F3 == key:
			return False
		if app.DIK_F4 == key:
			return False
		if app.DIK_LALT == key:
			return False
		if app.DIK_SYSRQ == key:
			return False
		if app.DIK_LCONTROL == key:
			return False

		return True

	def OnIMEKeyDown(self, key):
		# Left
		if app.VK_LEFT == key:
			ime.MoveLeft()
			return True
		# Right
		if app.VK_RIGHT == key:
			ime.MoveRight()
			return True

		# Home
		if app.VK_HOME == key:
			ime.MoveHome()
			return True
		# End
		if app.VK_END == key:
			ime.MoveEnd()
			return True

		# Delete
		if app.VK_DELETE == key:
			ime.Delete()
			TextLine.SetText(self, ime.GetText(self.bCodePage))
			return True

		if app.VK_UP == key:
			if self.eventUpArrow:
				self.eventUpArrow()
				return True
		# Down
		if app.VK_DOWN == key:
			if self.eventDownArrow:
				self.eventDownArrow()
				return True

		return True

	# def OnMouseLeftButtonDown(self):
		# self.SetFocus()

	def OnMouseLeftButtonDown(self):
		if False == self.IsIn():
			return False

		self.SetFocus()
		PixelPosition = wndMgr.GetCursorPosition(self.hWnd)
		ime.SetCursorPosition(PixelPosition)

	if app.WJ_MULTI_TEXTLINE:
		def DisableEnterToken(self):
			wndMgr.DisableEnterToken(self.hWnd)

class MarkBox(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

	def __del__(self):
		Window.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterMarkBox(self, layer)

	def Load(self):
		wndMgr.MarkBox_Load(self.hWnd)

	def SetScale(self, scale):
		wndMgr.MarkBox_SetScale(self.hWnd, scale)

	def SetIndex(self, guildID):
		MarkID = guild.GuildIDToMarkID(guildID)
		wndMgr.MarkBox_SetImageFilename(self.hWnd, guild.GetMarkImageFilenameByMarkID(MarkID))
		wndMgr.MarkBox_SetIndex(self.hWnd, guild.GetMarkIndexByMarkID(MarkID))

	def SetAlpha(self, alpha):
		wndMgr.MarkBox_SetDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)

class ImageBox(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		self.eventDict={}
		if app.ENABLE_EVENT_MANAGER:
			self.argDict={}
		self.eventFunc = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
		self.eventArgs = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}

		self.mouseRightButtonDownEvent = None
		self.mouseRightButtonUpEvent = None
		self.mouseLeftButtonUpEvent = None

	def __del__(self):
		Window.__del__(self)
		self.eventFunc = None
		self.eventArgs = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterImageBox(self, layer)

	def LoadImage(self, imageName):
		imageName = ResolveV31ImageVisual(imageName)
		self.name=imageName
		wndMgr.LoadImage(self.hWnd, imageName)

		if len(self.eventDict)!=0:
			print("LOAD IMAGE", self, self.eventDict)

	if app.ENABLE_OFFLINE_SHOP:
		def UnloadImage(self):
			wndMgr.UnloadImage(self.hWnd)

	def LoadImageFromFile(self, imageName):
		self.name=imageName
		wndMgr.LoadImageFromFile(self.hWnd, imageName)

		if len(self.eventDict)!=0:
			print("LOAD IMAGE", self, self.eventDict)

	def SetAlpha(self, alpha):
		wndMgr.SetDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)

	def GetWidth(self):
		return wndMgr.GetWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetHeight(self.hWnd)

	def OnMouseRightButtonDown(self):
		if self.mouseRightButtonDownEvent:
			self.mouseRightButtonDownEvent()
			
	def OnMouseRightButtonUp(self):
		if self.mouseRightButtonUpEvent:
			self.mouseRightButtonUpEvent()
			
	def OnMouseLeftButtonUp(self):
		if self.mouseLeftButtonUpEvent:
			self.mouseLeftButtonUpEvent()
			
	def SetMouseRightButtonDownEvent(self, event):
		self.mouseRightButtonDownEvent = event
		
	def SetMouseRightButtonUpEvent(self, event):
		self.mouseRightButtonUpEvent = event
		
	def SetMouseLeftButtonUpEvent(self, event):
		self.mouseLeftButtonUpEvent = event	

	if app.ENABLE_OFFLINE_SHOP:
		def __OnMouseOverIn(self):
			try:
				self.eventDict["MOUSE_OVER_IN"](*self.argDict["MOUSE_OVER_IN"])
			except KeyError:
				pass
		
		def __OnMouseOverOut(self):
			try:
				self.eventDict["MOUSE_OVER_OUT"](*self.argDict["MOUSE_OVER_OUT"])
			except KeyError:
				pass
		
		def OnMouseLeftButtonDown(self):
			if ("MOUSE_LEFT_DOWN" in self.eventDict):
				self.eventDict["MOUSE_LEFT_DOWN"](*self.argDict["MOUSE_LEFT_DOWN"])
	else:
		def OnMouseOverIn(self):
			try:
				self.eventDict["MOUSE_OVER_IN"]()
			except KeyError:
				pass

		def OnMouseOverOut(self):
			try:
				self.eventDict["MOUSE_OVER_OUT"]()
			except KeyError:
				pass

	def SAFE_SetStringEvent(self, event, func, *args):
		self.eventDict[event]=__mem_func__(func)
		self.eventArgs[event]=args

	def SetEvent(self, func, *args):
		result = (args[0] in self.eventFunc)
		if result:
			self.eventFunc[args[0]] = func
			self.eventArgs[args[0]] = args
		else:
			print("[ERROR] ui.py SetEvent, Can`t Find has_key : %s" % args[0])

	def OnMouseLeftButtonUp(self) :
		if self.eventFunc["mouse_click"] :
			self.eventFunc["mouse_click"](*self.eventArgs["mouse_click"])
		else:
			try:
				self.eventDict["MOUSE_LEFT_UP"](*self.argDict["MOUSE_LEFT_UP"])
			except KeyError:
				pass

	def OnMouseOverIn(self):
		if self.eventFunc["mouse_over_in"]:
			self.eventFunc["mouse_over_in"](*self.eventArgs["mouse_over_in"])

		if ("MOUSE_OVER_IN" in self.eventDict):
			if self.eventArgs["MOUSE_OVER_IN"]:
				self.eventDict["MOUSE_OVER_IN"](*self.eventArgs["MOUSE_OVER_IN"])
			else:
				self.eventDict["MOUSE_OVER_IN"]()

	def OnMouseOverOut(self):
		if self.eventFunc["mouse_over_out"]:
			self.eventFunc["mouse_over_out"](*self.eventArgs["mouse_over_out"])

		if ("MOUSE_OVER_OUT" in self.eventDict):
			if self.eventArgs["MOUSE_OVER_OUT"]:
				self.eventDict["MOUSE_OVER_OUT"](*self.eventArgs["MOUSE_OVER_OUT"])
			else:
				self.eventDict["MOUSE_OVER_OUT"]()

	def LeftRightReverse(self):
		wndMgr.LeftRightReverseImageBox(self.hWnd)

	def SetCoolTime(self, time):
		wndMgr.SetCoolTimeImageBox(self.hWnd, time)

	def SetStartCoolTime(self, time):
		wndMgr.SetStartCoolTimeImageBox(self.hWnd, time)

	if app.ENABLE_ITEMSHOP:
		def SetDiffuseColor(self, r, g, b, a):
			wndMgr.SetDiffuseColor(self.hWnd, r, g, b, a)

	if app.ENABLE_EVENT_MANAGER:
		def EventCalendarSetStringEvent(self, event, func, *args):
			self.eventDict[event]=func
			self.argDict[event]=args

		def SetMouseLeftButtonDoubleClickEvent(self, event):
			self.mouseLeftButtonDoubleClickEvent = event

		def OnMouseLeftButtonDoubleClick(self):
			if self.mouseLeftButtonDoubleClickEvent:
				self.mouseLeftButtonDoubleClickEvent()

	if app.ENABLE_FISHING_GAME:
		def SetDiffuseColor(self, r, g, b, alpha = 1.0):
			wndMgr.SetDiffuseColor(self.hWnd, r, g, b, alpha)

	def SetScale(self, xScale, yScale):
		wndMgr.SetScale(self.hWnd, xScale, yScale)

class ExpandedImageBox(ImageBox):
	def __init__(self, layer = "UI"):
		ImageBox.__init__(self, layer)

	def __del__(self):
		ImageBox.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterExpandedImageBox(self, layer)

	def SetScale(self, xScale, yScale):
		wndMgr.SetScale(self.hWnd, xScale, yScale)

	def SetLinearFiltering(self, enabled):
		setter = getattr(wndMgr, "SetImageLinearFiltering", None)
		if setter:
			setter(self.hWnd, bool(enabled))

	def SetOrigin(self, x, y):
		wndMgr.SetOrigin(self.hWnd, x, y)

	def SetRotation(self, rotation):
		wndMgr.SetRotation(self.hWnd, rotation)

	def SetRenderingMode(self, mode):
		wndMgr.SetRenderingMode(self.hWnd, mode)

	# [0.0, 1.0] 사이의 값만큼 퍼센트로 그리지 않는다.
	def SetRenderingRect(self, left, top, right, bottom):
		wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

	if app.ENABLE_IMAGE_CLIP_RECT:
		def SetClipRect(self, left, top, right, bottom, isVertical = False):
			wndMgr.SetClipRect(self.hWnd, left, top, right, bottom, isVertical)

	def SetPercentage(self, curValue, maxValue):
		if maxValue:
			self.SetRenderingRect(0.0, 0.0, -1.0 + float(curValue) / float(maxValue), 0.0)
		else:
			self.SetRenderingRect(0.0, 0.0, 0.0, 0.0)

	def GetWidth(self):
		return wndMgr.GetWindowWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetWindowHeight(self.hWnd)

class ImageBoxWiki(WikiWindow):
	def __init__(self, layer = "UI"):
		WikiWindow.__init__(self, layer)

		self.eventDict={}
		self.eventFunc = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
		self.eventArgs = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
		self.ToolTipText = None

		if app.ENABLE_DETAILS_UI:
			self.overFunc = None
			self.overArgs = None
			self.overOutFunc = None
			self.overOutArgs = None

		self.showtooltipevent = None
		self.showtooltiparg = None
		self.hidetooltipevent = None
		self.hidetooltiparg = None

	def __del__(self):
		WikiWindow.__del__(self)
		self.eventFunc = None
		self.eventArgs = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterImageBox(self, layer)

	def LoadImage(self, imageName):
		self.name=imageName
		wndMgr.LoadImage(self.hWnd, imageName)

		if len(self.eventDict)!=0:
			print("LOAD IMAGE", self, self.eventDict)

	def SetAlpha(self, alpha):
		wndMgr.SetDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)

	def GetWidth(self):
		return wndMgr.GetWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetHeight(self.hWnd)

	def SetDiffuseColor(self, r, g, b, a):
		wndMgr.SetDiffuseColor(self.hWnd, r, g, b, a)

	def SAFE_SetStringEvent(self, event, func, *args):
		self.eventDict[event] =__mem_func__(func)
		self.eventArgs[event] = args

	def SetMouseOverInEvent(self, func, *args):
		self.eventDict["MOUSE_OVER_IN"] = func
		self.eventArgs["MOUSE_OVER_IN"] = args

	def SetOnMouseLeftButtonUpEvent(self, event, *args):
		self.eventFunc["MOUSE_LEFT_BUTTON_UP"] = event
		self.eventArgs["MOUSE_LEFT_BUTTON_UP"] = args

	def SetMouseOverOutEvent(self, func, *args):
		self.eventDict["MOUSE_OVER_OUT"] = func
		self.eventArgs["MOUSE_OVER_OUT"] = args

	def SetEvent(self, func, *args) :
		result = (args[0] in self.eventFunc)
		if result :
			self.eventFunc[args[0]] = func
			self.eventArgs[args[0]] = args
		else :
			print("[ERROR] ui.py SetEvent, Can`t Find has_key : %s" % args[0])

	def OnMouseLeftButtonUp(self) :
		if self.eventFunc["mouse_click"]:
			self.eventFunc["mouse_click"](*self.eventArgs["mouse_click"])
		WikiWindow.OnMouseLeftButtonUp(self)

	def OnMouseOverIn(self):
		if self.eventFunc["mouse_over_in"]:
			self.eventFunc["mouse_over_in"](*self.eventArgs["mouse_over_in"])

		if ("MOUSE_OVER_IN" in self.eventDict):
			if self.eventArgs["MOUSE_OVER_IN"]:
				self.eventDict["MOUSE_OVER_IN"](*self.eventArgs["MOUSE_OVER_IN"])
			else:
				self.eventDict["MOUSE_OVER_IN"]()

	def OnMouseOverOut(self):
		if self.eventFunc["mouse_over_out"]:
			self.eventFunc["mouse_over_out"](*self.eventArgs["mouse_over_out"])

		if ("MOUSE_OVER_OUT" in self.eventDict):
			if self.eventArgs["MOUSE_OVER_OUT"]:
				self.eventDict["MOUSE_OVER_OUT"](*self.eventArgs["MOUSE_OVER_OUT"])
			else:
				self.eventDict["MOUSE_OVER_OUT"]()

	def SetFormToolTipText(self, type, text, x, y):
		if not self.ToolTipText:
			toolTip = createToolTipWindowDict[type]()
			toolTip.SetParent(self)
			toolTip.SetSize(0, 0)
			toolTip.SetHorizontalAlignCenter()
			if app.WJ_MULTI_TEXTLINE:
				toolTip.DisableEnterToken()
			toolTip.SetOutline()
			toolTip.Hide()
			toolTip.SetPosition(x + self.GetWidth() // 2, y)
			self.ToolTipText = toolTip

		self.ToolTipText.SetText(text)

	def SetToolTipWindow(self, toolTip):
		self.ToolTipText=toolTip
		self.ToolTipText.SetParentProxy(self)

	def SetToolTipText(self, text, x=0, y = -19):
		self.SetFormToolTipText("TEXT", text, x, y)

	def ShowToolTip(self):
		if self.ToolTipText:
			self.ToolTipText.Show()

	def HideToolTip(self):
		if self.ToolTipText:
			self.ToolTipText.Hide()

	def SetShowToolTipEvent(self, func, *args):
		self.showtooltipevent = func
		self.showtooltiparg = args

	def SetHideToolTipEvent(self, func, *args):
		self.hidetooltipevent = func
		self.hidetooltiparg = args

class ExpandedImageBoxWiki(ImageBoxWiki):
	def __init__(self, layer = "UI"):
		ImageBoxWiki.__init__(self, layer)

	def __del__(self):
		ImageBoxWiki.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterExpandedImageBox(self, layer)

	def SetScale(self, xScale, yScale):
		wndMgr.SetScale(self.hWnd, xScale, yScale)

	def SetOrigin(self, x, y):
		wndMgr.SetOrigin(self.hWnd, x, y)

	def SetRotation(self, rotation):
		wndMgr.SetRotation(self.hWnd, rotation)

	def SetRenderingMode(self, mode):
		wndMgr.SetRenderingMode(self.hWnd, mode)

	def SetRenderingRect(self, left, top, right, bottom):
		wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

	def SetPercentage(self, curValue, maxValue):
		if maxValue:
			self.SetRenderingRect(0.0, 0.0, -1.0 + float(curValue) / float(maxValue), 0.0)
		else:
			self.SetRenderingRect(0.0, 0.0, 0.0, 0.0)

	def GetWidth(self):
		return wndMgr.GetWindowWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetWindowHeight(self.hWnd)

	def SetDiffuseColor(self, r, g, b, a):
		wndMgr.SetDiffuseColor(self.hWnd, r, g, b, a)

	def SetCoolTime(self, time):
		wndMgr.SetCoolTimeImageBox(self.hWnd, time)

	def SetStartCoolTime(self, time):
		wndMgr.SetStartCoolTimeImageBox(self.hWnd, time)

class AniImageBox(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.end_frame_event = None
		if app.ENABLE_MINI_GAME_CATCH_KING:
			self.end_frame_args = None
		self.key_frame_event = None

	def __del__(self):
		Window.__del__(self)
		self.end_frame_event = None
		if app.ENABLE_MINI_GAME_CATCH_KING:
			self.end_frame_args = None
		self.key_frame_event = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterAniImageBox(self, layer)

	def SetDelay(self, delay):
		wndMgr.SetDelay(self.hWnd, delay)

	def AppendImage(self, filename):
		wndMgr.AppendImage(self.hWnd, filename)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def AppendImageScale(self, filename, scale_x, scale_y):
			wndMgr.AppendImageScale(self.hWnd, filename, scale_x, scale_y)

	def SetPercentage(self, curValue, maxValue):
		wndMgr.SetRenderingRect(self.hWnd, 0.0, 0.0, -1.0 + float(curValue) / float(maxValue), 0.0)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def OnEndFrame(self):
			if self.end_frame_event:
				self.end_frame_event(*self.end_frame_args)
	else:
		def OnEndFrame(self):
			if self.end_frame_event:
				self.end_frame_event()

	def SetScale(self, xScale, yScale):
		wndMgr.SetAniImgScale(self.hWnd, xScale, yScale)

	if app.ENABLE_MINI_GAME_CATCH_KING:
		def SetEndFrameEvent(self, event, *args):
			self.end_frame_event = event
			self.end_frame_args = args
	else:
		def SetEndFrameEvent(self, event):
			self.end_frame_event = event

	def ResetFrame(self):
		wndMgr.ResetFrame(self.hWnd)

	def OnKeyFrame(self, cur_frame):
		if self.key_frame_event:
			self.key_frame_event(cur_frame)

	def SetKeyFrameEvent(self, event):
		self.key_frame_event = event

	if app.ENABLE_FISHING_GAME:
		def SetRotation(self, rotation):
			wndMgr.SetRotation(self.hWnd, rotation)

class MoveImageBox(ImageBox):
	def __init__(self, layer = "UI"):
		ImageBox.__init__(self, layer)
		self.end_move_event = None

	def __del__(self):
		ImageBox.__del__(self)
		self.end_move_event = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterMoveImageBox(self, layer)

	def MoveStart(self):
		wndMgr.MoveStart(self.hWnd)
	def MoveStop(self):
		wndMgr.MoveStop(self.hWnd)
	def GetMove(self):
		return wndMgr.GetMove(self.hWnd)

	def SetMovePosition(self, dst_x, dst_y):
		wndMgr.SetMovePosition(self.hWnd, dst_x, dst_y)

	def SetMoveSpeed(self, speed):
		wndMgr.SetMoveSpeed(self.hWnd, speed)

	def OnEndMove(self):
		if self.end_move_event:
			self.end_move_event()

	def SetEndMoveEvent(self, event):
		self.end_move_event = event

class Button(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		self.eventFunc = None
		self.eventArgs = None

		self.ButtonText = None
		self.fontName = fontconfig.FontForRole(fontconfig.ROLE_CONTROL)
		self.usesUnifiedCrimson = False
		self.usesExplicitTextLayout = False
		self.ToolTipText = None

		self.TextChild = []

		if app.ENABLE_DETAILS_UI:
			self.overFunc = None
			self.overArgs = None
			self.overOutFunc = None
			self.overOutArgs = None

		self.showtooltipevent = None
		self.showtooltiparg = None
		self.hidetooltipevent = None
		self.hidetooltiparg = None

		self.eventFuncDict = {}
		self.eventArgsDict = {}

	def SetFontName(self, fontName):
		self.fontName = fontName
		if self.ButtonText:
			self.ButtonText.SetFontName(fontName)
			self._ApplyUnifiedCrimsonTextStyle()

	def __del__(self):
		Window.__del__(self)

		self.eventFunc = None
		self.eventArgs = None

		if app.ENABLE_DETAILS_UI:
			self.overFunc = None
			self.overArgs = None
			self.overOutFunc = None
			self.overOutArgs = None

	if app.ENABLE_EXCHANGE_LOG:
		def SetRenderingRect(self, left, top, right, bottom):
			wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterButton(self, layer)

	def SetUpVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "normal")
		self._SetUnifiedCrimsonVisual(resolved)
		if not self.usesUnifiedCrimson:
			resolved = ResolveV31ActionVisual(filename)
		wndMgr.SetUpVisual(self.hWnd, resolved)
		if self.usesUnifiedCrimson:
			wndMgr.SetDisableVisual(self.hWnd, uicrimsoncontrols.Visual(self._UnifiedCrimsonFamily(resolved), "disabled"))
			return
		disabledVisual = V31_ACTION_DISABLED_VISUALS.get(_V31VisualBasename(filename))
		if disabledVisual:
			wndMgr.SetDisableVisual(self.hWnd, disabledVisual)

	def SetOverVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "hover")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetOverVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ActionVisual(filename))

	def SetDownVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "pressed")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDownVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ActionVisual(filename))

	def SetDisableVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "disabled")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDisableVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31DisabledActionVisual(filename))

	def _UnifiedCrimsonFamily(self, filename):
		basename = filename.replace("\\", "/").rsplit("/", 1)[-1]
		return basename[len("button_"):].rsplit("_", 1)[0]

	def _SetUnifiedCrimsonVisual(self, filename):
		self.usesUnifiedCrimson = uicrimsoncontrols.IsUnifiedVisual(filename)
		self._ApplyUnifiedCrimsonTextStyle()

	def _ApplyUnifiedCrimsonTextStyle(self):
		if not self.usesUnifiedCrimson or self.usesExplicitTextLayout or not self.ButtonText:
			return
		self.ButtonText.SetPackedFontColor(CRIMSON_CONTROL_LABEL_COLOR)
		self.ButtonText.SetOutline()

	def GetUpVisualFileName(self):
		return wndMgr.GetUpVisualFileName(self.hWnd)

	def GetOverVisualFileName(self):
		return wndMgr.GetOverVisualFileName(self.hWnd)

	def GetDownVisualFileName(self):
		return wndMgr.GetDownVisualFileName(self.hWnd)

	def Flash(self):
		wndMgr.Flash(self.hWnd)

	def EnableFlash(self):
		wndMgr.EnableFlash(self.hWnd)

	def DisableFlash(self):
		wndMgr.DisableFlash(self.hWnd)

	def Enable(self):
		wndMgr.Enable(self.hWnd)

	def Disable(self):
		wndMgr.Disable(self.hWnd)

	def Down(self):
		wndMgr.Down(self.hWnd)

	def FlashEx(self):
		wndMgr.FlashEx(self.hWnd)

	def SetUp(self):
		wndMgr.SetUp(self.hWnd)

	def SAFE_SetEvent(self, func, *args):
		self.eventFunc = __mem_func__(func)
		self.eventArgs = args

	def SetEvent(self, func, *args):
		self.eventFunc = func
		self.eventArgs = args

	def Over(self):
		wndMgr.Over(self.hWnd)

	def LeftRightReverse(self) :
		wndMgr.LeftRightReverse(self.hWnd)

	def SetTextColor(self, color):
		if not self.ButtonText:
			return
		self.ButtonText.SetPackedFontColor(color)

	if app.ENABLE_TELEPORT_WINDOW:
		def SetOutline(self, Value=True):
			if not self.ButtonText:
				return
			self.ButtonText.SetOutline(Value)

	def SetAlpha(self, alpha):
		setButtonDiffuseColor = getattr(wndMgr, "SetButtonDiffuseColor", None)
		if setButtonDiffuseColor:
			setButtonDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)

	def GetText(self):
		if self.ButtonText:
			return self.ButtonText.GetText()
		else:
			return ""

	def IsDisable(self):
		return wndMgr.IsDisable(self.hWnd)

	def SetText(self, text, height = 4):
		self.usesExplicitTextLayout = False
		if not self.ButtonText:
			textLine = TextLine()
			textLine.SetFontName(self.fontName)
			textLine.SetParent(self)
			textLine.SetPosition(self.GetWidth()//2, self.GetHeight()//2)
			textLine.SetVerticalAlignCenter()
			textLine.SetHorizontalAlignCenter()
			textLine.Show()
			self.ButtonText = textLine

		self.ButtonText.SetText(text)
		self._ApplyUnifiedCrimsonTextStyle()

	def AppendTextLineAllClear(self):
		self.TextChild = []

	def SetAppendTextChangeText(self, idx, text):
		if not len(self.TextChild):
			return

		self.TextChild[idx].SetText(text)

	def SetAppendTextColor(self, idx, color):
		if not len(self.TextChild):
			return

		self.TextChild[idx].SetPackedFontColor(color)

	def AppendTextLine(self, text
		, font_size = None
		, font_color = grp.GenerateColor(0.7607, 0.7607, 0.7607, 1.0)
		, text_sort = "center"
		, pos_x = None
		, pos_y = None) :
		if font_size is None:
			font_size = self.fontName
		textLine = TextLine()
		textLine.SetParent(self)
		textLine.SetFontName(font_size)
		textLine.SetPackedFontColor(font_color)
		textLine.SetText(text)
		textLine.Show()

		if not pos_x and not pos_y :
			textLine.SetPosition(self.GetWidth()//2, self.GetHeight()//2)
		else :
			textLine.SetPosition(pos_x, pos_y)

		textLine.SetVerticalAlignCenter()
		if "center" == text_sort:
			textLine.SetHorizontalAlignCenter()
		elif "right" == text_sort:
			textLine.SetHorizontalAlignRight()
		elif "left" == text_sort:
			textLine.SetHorizontalAlignLeft()

		self.TextChild.append(textLine)

	def SetFormToolTipText(self, type, text, x, y):
		if not self.ToolTipText:
			toolTip = createToolTipWindowDict[type]()
			if app.ENABLE_DUNGEON_INFO:
				toolTip.SetWindowName("not_render_tooltip")
			toolTip.SetParent(self)
			toolTip.SetSize(0, 0)
			toolTip.SetHorizontalAlignCenter()
			if app.WJ_MULTI_TEXTLINE:
				toolTip.DisableEnterToken()
			toolTip.SetOutline()
			toolTip.Hide()
			toolTip.SetPosition(x + self.GetWidth() // 2, y)
			self.ToolTipText = toolTip

		self.ToolTipText.SetText(text)

	def SetToolTipWindow(self, toolTip):
		self.ToolTipText=toolTip
		self.ToolTipText.SetParentProxy(self)

	def SetToolTipText(self, text, x=0, y = -19):
		self.SetFormToolTipText("TEXT", text, x, y)

	def CallEvent(self):
		snd.PlaySound("sound/ui/click.wav")

		if self.eventFunc:
			self.eventFunc(*self.eventArgs)

	def ShowToolTip(self):
		if self.ToolTipText:
			self.ToolTipText.Show()

		if self.showtooltipevent:
			self.showtooltipevent(*self.showtooltiparg)

	def HideToolTip(self):
		if self.ToolTipText:
			self.ToolTipText.Hide()

		if self.hidetooltipevent:
			self.hidetooltipevent(*self.hidetooltiparg)

	def SetShowToolTipEvent(self, func, *args):
		self.showtooltipevent = func
		self.showtooltiparg = args

	def SetHideToolTipEvent(self, func, *args):
		self.hidetooltipevent = func
		self.hidetooltiparg = args

	def IsDown(self):
		return wndMgr.IsDown(self.hWnd)

	if app.ENABLE_DETAILS_UI:
		def OnMouseOverIn(self):
			if self.overFunc:
				self.overFunc(*self.overArgs)

		def OnMouseOverOut(self):
			if self.overOutFunc:
				self.overOutFunc(*self.overOutArgs)

		def SetOverEvent(self, func, *args):
			self.overFunc = func
			self.overArgs = args

		def SetOverOutEvent(self, func, *args):
			self.overOutFunc = func
			self.overOutArgs = args

	if app.ENABLE_QUEST_RENEWAL or app.ENABLE_SKILL_COLOR_SYSTEM:
		def GetText(self):
			if not self.ButtonText:
				return ""

			return self.ButtonText.GetText()

		def SetTextAlignLeft(self, text, x = 27, height = 4):
			self.usesExplicitTextLayout = True
			if not self.ButtonText:
				textLine = TextLine()
				textLine.SetFontName(self.fontName)
				textLine.SetParent(self)
				textLine.SetPosition(x, self.GetHeight()//2)
				textLine.SetVerticalAlignCenter()
				textLine.SetHorizontalAlignLeft()
				textLine.Show()
				self.ButtonText = textLine

			#퀘스트 리스트 UI에 맞춰 위치 잡음
			self.ButtonText.SetText(text)
			self.ButtonText.SetPosition(x, self.GetHeight()//2)
			self.ButtonText.SetVerticalAlignCenter()
			self.ButtonText.SetHorizontalAlignLeft()

		def SetTextAlignRight(self, text, x = 27, y = 0):
			self.usesExplicitTextLayout = True
			if not self.ButtonText:
				textLine = TextLine()
				textLine.SetFontName(self.fontName)
				textLine.SetParent(self)
				textLine.SetPosition(x, y)
				textLine.SetVerticalAlignCenter()
				textLine.Show()
				self.ButtonText = textLine

			#퀘스트 리스트 UI에 맞춰 위치 잡음
			self.ButtonText.SetText(text)
			self.ButtonText.SetPosition(x, y)
			self.ButtonText.SetVerticalAlignCenter()

	if app.ENABLE_SKILL_COLOR_SYSTEM or app.ENABLE_NEW_GAMEOPTION:
		def SetListText(self, text, x = 8):
			self.usesExplicitTextLayout = True
			if not self.ButtonText:
				textLine = TextLine()
				textLine.SetFontName(self.fontName)
				textLine.SetParent(self)
				textLine.SetPosition(x, self.GetHeight()//2)
				textLine.SetVerticalAlignCenter()
				textLine.SetHorizontalAlignLeft()
				textLine.Show()
				self.ButtonText = textLine

			self.ButtonText.SetText(text)

	def SetTextAddPos(self, text, x_add = 0, y_add = 0, height = 4):
		self.usesExplicitTextLayout = True
		if not self.ButtonText:
			textLine = TextLine()
			textLine.SetFontName(self.fontName)
			textLine.SetParent(self)
			textLine.SetPosition(self.GetWidth() // 2 + x_add, self.GetHeight() // 2 + y_add)
			textLine.SetVerticalAlignCenter()
			textLine.SetHorizontalAlignCenter()
			textLine.Show()
			self.ButtonText = textLine
		self.ButtonText.SetText(text)

	def OnMouseRightButtonUp(self):
		if ("MOUSE_RIGHT_BUTTON_UP" in self.eventFuncDict):
			if ("MOUSE_RIGHT_BUTTON_UP" in self.eventArgsDict):
				self.eventFuncDict["MOUSE_RIGHT_BUTTON_UP"](*self.eventArgsDict["MOUSE_RIGHT_BUTTON_UP"])
			else:
				self.eventFuncDict["MOUSE_RIGHT_BUTTON_UP"]()

	def SAFE_SetStringEvent(self, event, func, *args):
		self.eventFuncDict[event] = __mem_func__(func)
		self.eventArgsDict[event] = args

class RadioButton(Button):
	def __init__(self):
		Button.__init__(self)

	def __del__(self):
		Button.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRadioButton(self, layer)

	def SetUpVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "normal")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetUpVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetOverVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "hover")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetOverVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetDownVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "pressed")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDownVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetDisableVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "disabled")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDisableVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	if app.ENABLE_TELEPORT_WINDOW:
		def SetFontColor(self, color):
			if not self.ButtonText:
				return
			self.ButtonText.SetPackedFontColor(color)
		def SetOutline(self, Value=True):
			if not self.ButtonText:
				return
			self.ButtonText.SetOutline(Value)
		def SetFontName(self, fontName):
			Button.SetFontName(self, fontName)

class RadioButtonGroup:
	def __init__(self):
		self.buttonGroup = []
		self.selectedBtnIdx = -1

	def __del__(self):
		self.buttonGroup = []
		self.selectedBtnIdx = -1

	def Show(self):
		for (button, selectEvent, unselectEvent) in self.buttonGroup:
			button.Show()

	def Hide(self):
		for (button, selectEvent, unselectEvent) in self.buttonGroup:
			button.Hide()

	def SetText(self, idx, text):
		if idx >= len(self.buttonGroup):
			return
		(button, selectEvent, unselectEvent) = self.buttonGroup[idx]
		button.SetText(text)

	def OnClick(self, btnIdx):
		if btnIdx == self.selectedBtnIdx:
			return
		(button, selectEvent, unselectEvent) = self.buttonGroup[self.selectedBtnIdx]
		if unselectEvent:
			unselectEvent(self.selectedBtnIdx)
		button.SetUp()

		self.selectedBtnIdx = btnIdx
		(button, selectEvent, unselectEvent) = self.buttonGroup[btnIdx]
		if selectEvent:
			selectEvent(btnIdx)

		button.Down()

	def AddButton(self, button, selectEvent, unselectEvent):
		i = len(self.buttonGroup)
		button.SetEvent(__mem_func__(self.OnClick),i)
		self.buttonGroup.append([button, selectEvent, unselectEvent])
		button.SetUp()

	def Create(rawButtonGroup):
		radioGroup = RadioButtonGroup()
		for (button, selectEvent, unselectEvent) in rawButtonGroup:
			radioGroup.AddButton(button, selectEvent, unselectEvent)

		radioGroup.OnClick(0)

		return radioGroup

	Create=staticmethod(Create)

class RadioButtonShopEx:
	def __init__(self):
		self.buttonGroup = []
		self.selectedBtnIdx = -1

	def __del__(self):
		for button, ue, de in self.buttonGroup:
			button.__del__()

	def Show(self):
		for (button, selectEvent, unselectEvent) in self.buttonGroup:
			button.Show()

	def Hide(self):
		for (button, selectEvent, unselectEvent) in self.buttonGroup:
			button.Hide()

	def SetText(self, idx, text):
		if idx >= len(self.buttonGroup):
			return
		(button, selectEvent, unselectEvent) = self.buttonGroup[idx]
		button.SetText(text)

	def OnClick(self, btnIdx):
		if btnIdx == self.selectedBtnIdx:
			return
		(button, selectEvent, unselectEvent) = self.buttonGroup[self.selectedBtnIdx]
		if unselectEvent:
			unselectEvent()
		button.SetUp()

		self.selectedBtnIdx = btnIdx
		(button, selectEvent, unselectEvent) = self.buttonGroup[btnIdx]
		if selectEvent:
			selectEvent()

		button.Down()

	def AddButton(self, button, selectEvent, unselectEvent):
		i = len(self.buttonGroup)
		button.SetEvent(lambda : self.OnClick(i))
		self.buttonGroup.append([button, selectEvent, unselectEvent])
		button.SetUp()

	def Create(rawButtonGroup):
		radioGroup = RadioButtonShopEx()
		for (button, selectEvent, unselectEvent) in rawButtonGroup:
			radioGroup.AddButton(button, selectEvent, unselectEvent)

		radioGroup.OnClick(0)

		return radioGroup

	Create=staticmethod(Create)

class ToggleButton(Button):
	def __init__(self):
		Button.__init__(self)

		self.eventUp = None
		self.eventDown = None

		self.eventUpArgs = None
		self.eventDownArgs = None

	def __del__(self):
		Button.__del__(self)

		self.eventUp = None
		self.eventDown = None

	def SetToggleUpEvent(self, event, *args):
		self.eventUp = event
		self.eventUpArgs = args

	def SetToggleDownEvent(self, event, *args):
		self.eventDown = event
		self.eventDownArgs = args

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterToggleButton(self, layer)

	def SetUpVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "normal")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetUpVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetOverVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "hover")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetOverVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetDownVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "pressed")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDownVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def SetDisableVisual(self, filename):
		resolved = uicrimsoncontrols.ResolveVisual(filename, "disabled")
		self._SetUnifiedCrimsonVisual(resolved)
		wndMgr.SetDisableVisual(self.hWnd, resolved if self.usesUnifiedCrimson else ResolveV31ChoiceVisual(filename))

	def OnToggleUp(self):
		if self.eventUp:
			if self.eventUpArgs:
				self.eventUp(*self.eventUpArgs)
			else:
				self.eventUp()

	def OnToggleDown(self):
		if self.eventDown:
			if self.eventDownArgs:
				self.eventDown(*self.eventDownArgs)
			else:
				self.eventDown()

class DragButton(Button):
	def __init__(self):
		Button.__init__(self)
		self.AddFlag("movable")

		self.callbackEnable = True
		self.eventMove = lambda: None

	def __del__(self):
		Button.__del__(self)

		self.eventMove = lambda: None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterDragButton(self, layer)

	def SetMoveEvent(self, event):
		self.eventMove = event

	def SetRestrictMovementArea(self, x, y, width, height):
		wndMgr.SetRestrictMovementArea(self.hWnd, x, y, width, height)

	def TurnOnCallBack(self):
		self.callbackEnable = True

	def TurnOffCallBack(self):
		self.callbackEnable = False

	def OnMove(self):
		if self.callbackEnable:
			self.eventMove()

class NumberLine(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

	def __del__(self):
		Window.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterNumberLine(self, layer)

	def SetHorizontalAlignCenter(self):
		wndMgr.SetNumberHorizontalAlignCenter(self.hWnd)

	def SetHorizontalAlignRight(self):
		wndMgr.SetNumberHorizontalAlignRight(self.hWnd)

	def SetPath(self, path):
		wndMgr.SetPath(self.hWnd, path)

	def SetNumber(self, number):
		wndMgr.SetNumber(self.hWnd, number)

###################################################################################################
## PythonScript Element
###################################################################################################

class Box(Window):

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterBox(self, layer)

	def SetColor(self, color):
		wndMgr.SetColor(self.hWnd, color)

class Bar(Window):

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterBar(self, layer)

	def SetColor(self, color):
		wndMgr.SetColor(self.hWnd, color)

class Line(Window):

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterLine(self, layer)

	def SetColor(self, color):
		wndMgr.SetColor(self.hWnd, color)

class SlotBar(Window):

	def __init__(self):
		Window.__init__(self)

	def __del__(self):
		Window.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterBar3D(self, layer)

## Same with SlotBar
class Bar3D(Window):
	def __init__(self):
		Window.__init__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterBar3D(self, layer)

	def SetColor(self, left, right, center):
		wndMgr.SetColor(self.hWnd, left, right, center)

class SlotWindow(Window):
	def __init__(self):
		Window.__init__(self)

		self.StartIndex = 0
		self._slotLocalPositions = {}

		self.eventSelectEmptySlot = None
		self.eventSelectItemSlot = None
		self.eventUnselectEmptySlot = None
		self.eventUnselectItemSlot = None
		self.eventUseSlot = None
		self.eventOverInItem = None
		self.eventOverOutItem = None
		self.eventPressedSlotButton = None

		self.eventSelectItemSlotArgs = None
		self.eventOverInItemArgs = None

		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.eventOverIn = None
			self.eventOverOut = None
			self.eventOverInArgs = None

	def __del__(self):
		Window.__del__(self)

		self.eventSelectEmptySlot = None
		self.eventSelectItemSlot = None
		self.eventUnselectEmptySlot = None
		self.eventUnselectItemSlot = None
		self.eventUseSlot = None
		self.eventOverInItem = None
		self.eventOverOutItem = None
		self.eventPressedSlotButton = None

		self.eventSelectItemSlotArgs = None
		self.eventOverInItemArgs = None

		if app.ENABLE_SLOT_TOOLTIP_INFO:
			self.eventOverIn = None
			self.eventOverOut = None
			self.eventOverInArgs = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterSlotWindow(self, layer)

	def SetSlotStyle(self, style):
		wndMgr.SetSlotStyle(self.hWnd, style)

	def HasSlot(self, slotIndex):
		return wndMgr.HasSlot(self.hWnd, slotIndex)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def SetSlotScale(self, xScale, yScale):
			wndMgr.SetSlotScale(self.hWnd, xScale, yScale)

	def SetSlotBaseImage(self, imageFileName, r, g, b, a):
		wndMgr.SetSlotBaseImage(self.hWnd, imageFileName, r, g, b, a)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def SetSlotBaseImageScale(self, imageFileName, r, g, b, a, sx, sy):
			wndMgr.SetSlotBaseImageScale(self.hWnd, imageFileName, r, g, b, a, sx, sy)

	def SetBaseImageScale(self, xScale, yScale):
		wndMgr.SetBaseImageScale(self.hWnd, xScale, yScale)

	def SetCoverButton(self,\
						slotIndex,\
						upName="d:/ymir work/ui/public/slot_cover_button_01.sub",\
						overName="d:/ymir work/ui/public/slot_cover_button_02.sub",\
						downName="d:/ymir work/ui/public/slot_cover_button_03.sub",\
						disableName="d:/ymir work/ui/public/slot_cover_button_04.sub",\
						LeftButtonEnable = False,\
						RightButtonEnable = True):
		wndMgr.SetCoverButton(self.hWnd, slotIndex, upName, overName, downName, disableName, LeftButtonEnable, RightButtonEnable)

	def SetCorverButtonScale(self, slotIndex, xScale, yScale):
		wndMgr.SetCorverButtonScale(self.hWnd, slotIndex, xScale, yScale)

	def EnableCoverButton(self, slotIndex):
		wndMgr.EnableCoverButton(self.hWnd, slotIndex)

	def DisableCoverButton(self, slotIndex):
		wndMgr.DisableCoverButton(self.hWnd, slotIndex)

	def SetAlwaysRenderCoverButton(self, slotIndex, bAlwaysRender = True):
		wndMgr.SetAlwaysRenderCoverButton(self.hWnd, slotIndex, bAlwaysRender)

	def AppendSlotButton(self, upName, overName, downName):
		wndMgr.AppendSlotButton(self.hWnd, upName, overName, downName)

	def ShowSlotButton(self, slotNumber):
		wndMgr.ShowSlotButton(self.hWnd, slotNumber)

	def HideAllSlotButton(self):
		wndMgr.HideAllSlotButton(self.hWnd)

	def AppendRequirementSignImage(self, filename):
		wndMgr.AppendRequirementSignImage(self.hWnd, filename)

	def ShowRequirementSign(self, slotNumber):
		wndMgr.ShowRequirementSign(self.hWnd, slotNumber)

	def HideRequirementSign(self, slotNumber):
		wndMgr.HideRequirementSign(self.hWnd, slotNumber)

	def ActivateSlotOld(self, slotNumber):
		wndMgr.ActivateSlotOld(self.hWnd, slotNumber)

	def ActivateSlot(self, slotNumber):
		wndMgr.ActivateSlot(self.hWnd, slotNumber)

	def DeactivateSlot(self, slotNumber):
		wndMgr.DeactivateSlot(self.hWnd, slotNumber)

	if app.WJ_ENABLE_PICKUP_ITEM_EFFECT:
		def SetSlotDiffuseColor(self, slotindex, colortype):
			wndMgr.SetSlotDiffuseColor(self.hWnd, slotindex, colortype)

		def SetSlotFlashEffect(self, slotindex, active):
			wndMgr.SetSlotFlashEffect(self.hWnd, slotindex, active)

	def SetSlotHighlightedGreeen(self, slotNumber):
		wndMgr.SetSlotHighlightedGreeen(self.hWnd, slotNumber)

	def DisableSlotHighlightedGreen(self, slotNumber):
		wndMgr.DisableSlotHighlightedGreen(self.hWnd, slotNumber)

	def ShowSlotBaseImage(self, slotNumber):
		wndMgr.ShowSlotBaseImage(self.hWnd, slotNumber)

	def HideSlotBaseImage(self, slotNumber):
		wndMgr.HideSlotBaseImage(self.hWnd, slotNumber)

	def SAFE_SetButtonEvent(self, button, state, event):
		if "LEFT"==button:
			if "EMPTY"==state:
				self.eventSelectEmptySlot=__mem_func__(event)
			elif "EXIST"==state:
				self.eventSelectItemSlot=__mem_func__(event)
			elif "ALWAYS"==state:
				self.eventSelectEmptySlot=__mem_func__(event)
				self.eventSelectItemSlot=__mem_func__(event)
		elif "RIGHT"==button:
			if "EMPTY"==state:
				self.eventUnselectEmptySlot=__mem_func__(event)
			elif "EXIST"==state:
				self.eventUnselectItemSlot=__mem_func__(event)
			elif "ALWAYS"==state:
				self.eventUnselectEmptySlot=__mem_func__(event)
				self.eventUnselectItemSlot=__mem_func__(event)

	def SetSelectEmptySlotEvent(self, empty):
		self.eventSelectEmptySlot = empty

	def SetSelectItemSlotEvent(self, item, *args):
		self.eventSelectItemSlot = item
		self.eventSelectItemSlotArgs = args

	def SetUnselectEmptySlotEvent(self, empty):
		self.eventUnselectEmptySlot = empty

	def SetUnselectItemSlotEvent(self, item):
		self.eventUnselectItemSlot = item

	def SetUseSlotEvent(self, use):
		self.eventUseSlot = use

	def SetOverInItemEvent(self, event, *args):
		self.eventOverInItem = event
		self.eventOverInItemArgs = args

	def SetOverOutItemEvent(self, event):
		self.eventOverOutItem = event

	if app.ENABLE_SLOT_TOOLTIP_INFO:
		def SetOverInEvent(self, event, *args):
			self.eventOverIn = event
			self.eventOverInArgs = args

		def SetOverOutEvent(self, event):
			self.eventOverOut = event

	def SetPressedSlotButtonEvent(self, event):
		self.eventPressedSlotButton = event

	def GetSlotCount(self):
		return wndMgr.GetSlotCount(self.hWnd)

	def SetUseMode(self, flag):
		"True일때만 ItemToItem 이 가능한지 보여준다"
		wndMgr.SetUseMode(self.hWnd, flag)

	def SetUsableItem(self, flag):
		"True면 현재 가리킨 아이템이 ItemToItem 적용 가능하다"
		wndMgr.SetUsableItem(self.hWnd, flag)

	## Slot
	def IsActivatedSlot(self, slotNumber):
		return wndMgr.IsActivatedSlot(self.hWnd, slotNumber)

	def GetSlotCoolTime(self, slotIndex):
		return wndMgr.GetSlotCoolTime(self.hWnd, slotIndex)

	def SetSlotCoolTime(self, slotIndex, coolTime, elapsedTime = 0.0):
		wndMgr.SetSlotCoolTime(self.hWnd, slotIndex, coolTime, elapsedTime)

	def SetSlotCoolTimeColor(self, slotIndex, r, g, b, a):
		wndMgr.SetSlotCoolTimeColor(self.hWnd, slotIndex, r, g, b, a)

	def StoreSlotCoolTime(self, key, slotIndex, coolTime, elapsedTime = 0.0):
		wndMgr.StoreSlotCoolTime(self.hWnd, key, slotIndex, coolTime, elapsedTime)

	def RestoreSlotCoolTime(self, key):
		wndMgr.RestoreSlotCoolTime(self.hWnd, key)

	if app.WJ_ENABLE_TRADABLE_ICON:
		def SetCanMouseEventSlot(self, slotIndex):
			wndMgr.SetCanMouseEventSlot(self.hWnd, slotIndex)

		def SetCantMouseEventSlot(self, slotIndex):
			wndMgr.SetCantMouseEventSlot(self.hWnd, slotIndex)

		def SetUnusableSlotOnTopWnd(self, slotIndex):
			wndMgr.SetUnusableSlotOnTopWnd(self.hWnd, slotIndex)

		def SetUsableSlotOnTopWnd(self, slotIndex):
			wndMgr.SetUsableSlotOnTopWnd(self.hWnd, slotIndex)

	def DisableSlot(self, slotIndex):
		wndMgr.DisableSlot(self.hWnd, slotIndex)

	def EnableSlot(self, slotIndex):
		wndMgr.EnableSlot(self.hWnd, slotIndex)

	def LockSlot(self, slotIndex):
		wndMgr.LockSlot(self.hWnd, slotIndex)

	def UnlockSlot(self, slotIndex):
		wndMgr.UnlockSlot(self.hWnd, slotIndex)

	def RefreshSlot(self):
		wndMgr.RefreshSlot(self.hWnd)

	def ClearSlot(self, slotNumber):
		wndMgr.ClearSlot(self.hWnd, slotNumber)

	def ClearAllSlot(self):
		wndMgr.ClearAllSlot(self.hWnd)

	def AppendSlot(self, index, x, y, width, height):
		self._slotLocalPositions[index] = (x, y)
		wndMgr.AppendSlot(self.hWnd, index, x, y, width, height)

	def SetSlot(self, slotIndex, itemIndex, width, height, icon, diffuseColor = (1.0, 1.0, 1.0, 1.0)):
		wndMgr.SetSlot(self.hWnd, slotIndex, itemIndex, width, height, icon, diffuseColor)

	def SetSlotCount(self, slotNumber, count):
		wndMgr.SetSlotCount(self.hWnd, slotNumber, count)

	def SetRealSlotNumber(self, slotNumber, realSlotNumber):
		wndMgr.SetSlotRealNumber(self.hWnd, slotNumber, realSlotNumber)

	def SetSlotCountNew(self, slotNumber, grade, count):
		wndMgr.SetSlotCountNew(self.hWnd, slotNumber, grade, count)

	if app.ENABLE_MINI_GAME_OKEY:
		def SetCardSlot(self, renderingSlotNumber, CardIndex, cardIcon, diffuseColor = (1.0, 1.0, 1.0, 1.0)):
			if 0 == CardIndex or None == CardIndex:
				wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
				return

			item.SelectItem(CardIndex)
			(width, height) = item.GetItemSize()

			wndMgr.SetCardSlot(self.hWnd, renderingSlotNumber, CardIndex, width, height, cardIcon, diffuseColor)

	def SetItemSlot(self, renderingSlotNumber, ItemIndex, ItemCount = 0, diffuseColor = (1.0, 1.0, 1.0, 1.0)):
		if 0 == ItemIndex or None == ItemIndex:
			wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
			return

		item.SelectItem(ItemIndex)
		itemIcon = item.GetIconImage()

		item.SelectItem(ItemIndex)
		(width, height) = item.GetItemSize()

		wndMgr.SetSlot(self.hWnd, renderingSlotNumber, ItemIndex, width, height, itemIcon, diffuseColor)
		wndMgr.SetSlotCount(self.hWnd, renderingSlotNumber, ItemCount)

	def SetSlotRarityColor(self, slotNumber, color):
		setter = getattr(wndMgr, "SetSlotRarityColor", None)
		if setter is not None:
			setter(self.hWnd, slotNumber, *color)

	def SetSkillSlot(self, renderingSlotNumber, skillIndex, skillLevel):
		skillIcon = skill.GetIconImage(skillIndex)

		if 0 == skillIcon:
			wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
			return

		wndMgr.SetSlot(self.hWnd, renderingSlotNumber, skillIndex, 1, 1, skillIcon)
		wndMgr.SetSlotCount(self.hWnd, renderingSlotNumber, skillLevel)

	def SetSkillSlotNew(self, renderingSlotNumber, skillIndex, skillGrade, skillLevel):

		skillIcon = skill.GetIconImageNew(skillIndex, skillGrade)

		if 0 == skillIcon:
			wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
			return

		wndMgr.SetSlot(self.hWnd, renderingSlotNumber, skillIndex, 1, 1, skillIcon)

	def SetEmotionSlot(self, renderingSlotNumber, emotionIndex):
		import player
		icon = player.GetEmotionIconImage(emotionIndex)

		if 0 == icon:
			wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
			return

		wndMgr.SetSlot(self.hWnd, renderingSlotNumber, emotionIndex, 1, 1, icon)

	## Event
	def OnSelectEmptySlot(self, slotNumber):
		if self.eventSelectEmptySlot:
			self.eventSelectEmptySlot(slotNumber)

	def OnSelectItemSlot(self, slotNumber):
		if self.eventSelectItemSlot:
			if self.eventSelectItemSlotArgs:
				self.eventSelectItemSlot(*self.eventSelectItemSlotArgs)
			else:
				self.eventSelectItemSlot(slotNumber)

	def OnUnselectEmptySlot(self, slotNumber):
		if self.eventUnselectEmptySlot:
			self.eventUnselectEmptySlot(slotNumber)

	def OnUnselectItemSlot(self, slotNumber):
		if self.eventUnselectItemSlot:
			self.eventUnselectItemSlot(slotNumber)

	def OnUseSlot(self, slotNumber):
		if self.eventUseSlot:
			self.eventUseSlot(slotNumber)

	def OnOverInItem(self, slotNumber):
		if self.eventOverInItem:
			if self.eventOverInItemArgs:
				self.eventOverInItem(*self.eventOverInItemArgs)
			else:
				self.eventOverInItem(slotNumber)

	def OnOverOutItem(self):
		if self.eventOverOutItem:
			self.eventOverOutItem()

	if app.ENABLE_SLOT_TOOLTIP_INFO:
		def OnOverIn(self,slotNumber):
			if self.eventOverIn:
				if self.eventOverInArgs:
					self.eventOverIn(*self.eventOverInArgs)
				else:
					self.eventOverIn(slotNumber)

		def OnOverOut(self):
			if self.eventOverOut:
				self.eventOverOut()

	def OnPressedSlotButton(self, slotNumber):
		if self.eventPressedSlotButton:
			self.eventPressedSlotButton(slotNumber)

	def GetStartIndex(self):
		return 0

	def GetSlotGlobalPosition(self, index):
		return wndMgr.GetSlotGlobalPosition(self.hWnd, index)

	def GetSlotLocalPosition(self, index):
		return self._slotLocalPositions.get(index)

	if app.ENABLE_SLOT_COVER_IMAGE_SYSTEM:
		def SetSlotCoverImage(self, slotindex, filename):
			wndMgr.SetSlotCoverImage(self.hWnd, slotindex, filename)

		def EnableSlotCoverImage(self, slotindex, onoff):
			wndMgr.EnableSlotCoverImage(self.hWnd, slotindex, onoff)

	def SetSlotType(self, flag):
		wndMgr.SetSlotType(self.hWnd, flag)

	if app.ENABLE_HIGH_LIGHT_IMAGE:
		def AppendHighLightImage(self, index, fileName, alphaSpeed = 0.0, rotationSpeed = 0.0, curAlpha = 1.0, diffuse = 0xFFFFFFFF):
			wndMgr.AppendHighLightImage(self.hWnd, index, fileName, alphaSpeed, rotationSpeed, curAlpha, diffuse)

		def EnableHighLightImage(self, slotIndex):
			wndMgr.EnableHighLightImage(self.hWnd, slotIndex)

		def DisableHighLightImage(self, slotIndex):
			wndMgr.DisableHighLightImage(self.hWnd, slotIndex)

	if app.ENABLE_GROWTH_PET_SYSTEM:
		def SetSlotCoolTimeInverse(self, slotIndex, coolTime, elapsedTime = 0.0):
			wndMgr.SetSlotCoolTimeInverse(self.hWnd, slotIndex, coolTime, elapsedTime)

		def SetPetSkillSlotNew(self, renderingSlotNumber, petSkillIndex):
		
			petSkillIcon = skill.GetPetSkillIconImage(petSkillIndex)

			if 0 == petSkillIcon:
				wndMgr.ClearSlot(self.hWnd, renderingSlotNumber)
				return

			wndMgr.SetSlot(self.hWnd, renderingSlotNumber, petSkillIndex, 1, 1, petSkillIcon)

	if app.ENABLE_DSS_ACTIVE_EFFECT:
		def SetRenderSlot(self, renderingSlotNumber, diffuseColor = (1.0, 1.0, 1.0, 1.0)):
			wndMgr.SetSlot(self.hWnd, renderingSlotNumber, 1, 1, 1, 0, diffuseColor)
			wndMgr.SetSlotCount(self.hWnd, renderingSlotNumber, 0)


class GridSlotWindow(SlotWindow):

	def __init__(self):
		SlotWindow.__init__(self)

		self.startIndex = 0

	def __del__(self):
		SlotWindow.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterGridSlotWindow(self, layer)

	def ArrangeSlot(self, StartIndex, xCount, yCount, xSize, ySize, xBlank, yBlank):

		self.startIndex = StartIndex
		self._slotLocalPositions = {}
		for y in range(yCount):
			for x in range(xCount):
				index = StartIndex + x + y * xCount
				self._slotLocalPositions[index] = (
					x * (xSize + xBlank),
					y * (ySize + yBlank),
				)

		wndMgr.ArrangeSlot(self.hWnd, StartIndex, xCount, yCount, xSize, ySize, xBlank, yBlank)
		self.startIndex = StartIndex

	def GetStartIndex(self):
		return self.startIndex

class TitleBar(Window):

	BLOCK_WIDTH = 32
	BLOCK_HEIGHT = 23

	def __init__(self):
		Window.__init__(self)
		self.AddFlag("attach")

	def __del__(self):
		Window.__del__(self)

	def MakeTitleBar(self, width, color):

		## 현재 Color는 사용하고 있지 않음

		width = max(64, width)

		imgLeft = ImageBox()
		imgCenter = ExpandedImageBox()
		imgRight = ImageBox()
		imgLeft.AddFlag("not_pick")
		imgCenter.AddFlag("not_pick")
		imgRight.AddFlag("not_pick")
		imgLeft.SetParent(self)
		imgCenter.SetParent(self)
		imgRight.SetParent(self)

		imgLeft.LoadImage("d:/ymir work/ui/pattern/titlebar_left.tga")
		imgCenter.LoadImage("d:/ymir work/ui/pattern/titlebar_center.tga")
		imgRight.LoadImage("d:/ymir work/ui/pattern/titlebar_right.tga")

		imgLeft.Show()
		imgCenter.Show()
		imgRight.Show()

		btnClose = Button()
		btnClose.SetParent(self)
		btnClose.SetUpVisual("d:/ymir work/ui/public/crimson_close_01.tga")
		btnClose.SetOverVisual("d:/ymir work/ui/public/crimson_close_02.tga")
		btnClose.SetDownVisual("d:/ymir work/ui/public/crimson_close_03.tga")
		btnClose.SetToolTipText(localeInfo.UI_CLOSE, 0, -23)
		btnClose.Show()

		self.imgLeft = imgLeft
		self.imgCenter = imgCenter
		self.imgRight = imgRight
		self.btnClose = btnClose

		self.SetWidth(width)

	def SetWidth(self, width):
		self.imgCenter.SetRenderingRect(0.0, 0.0, float((width - self.BLOCK_WIDTH*2) - self.BLOCK_WIDTH) / self.BLOCK_WIDTH, 0.0)
		self.imgCenter.SetPosition(self.BLOCK_WIDTH, 0)
		self.imgRight.SetPosition(width - self.BLOCK_WIDTH, 0)

		if localeInfo.IsARABIC():
			self.btnClose.SetPosition(3, 3)
		else:
			self.btnClose.SetPosition(width - self.btnClose.GetWidth() - 3, 3)

		self.SetSize(width, self.BLOCK_HEIGHT)

	def SetCloseEvent(self, event):
		self.btnClose.SetEvent(event)

	def SetVisuals(self, left, center, right, closeUp, closeOver, closeDown):
		self.imgLeft.LoadImage(left)
		self.imgCenter.LoadImage(center)
		self.imgRight.LoadImage(right)
		self.btnClose.SetUpVisual(closeUp)
		self.btnClose.SetOverVisual(closeOver)
		self.btnClose.SetDownVisual(closeDown)

	if app.ENABLE_DETAILS_UI:
		def CloseButtonHide(self):
			if localeInfo.IsARABIC():
				self.imgLeft.LoadImage("d:/ymir work/ui/pattern/titlebar_right_02.tga")
				self.imgLeft.LeftRightReverse()
				self.btnClose.Hide()
			else:
				self.imgRight.LoadImage("d:/ymir work/ui/pattern/titlebar_right_02.tga")
				self.btnClose.Hide()

if app.ENABLE_QUEST_RENEWAL:
	class SubTitleBar(Button):
		def __init__(self):
			Button.__init__(self)
			self.tabColor = None

		def __del__(self):
			self.tabColor = None
			Button.__del__(self)

		def MakeSubTitleBar(self, width):
			width = max(64, width)
			self.SetWidth(width)
			self.SetUpVisual("d:/ymir work/ui/quest_re/quest_tab_01.tga")
			self.SetOverVisual("d:/ymir work/ui/quest_re/quest_tab_01.tga")
			self.SetDownVisual("d:/ymir work/ui/quest_re/quest_tab_01.tga")
			self.Show()

			scrollImage = ImageBox()
			scrollImage.SetParent(self)
			scrollImage.LoadImage("d:/ymir work/ui/quest_re/quest_down.tga")
			scrollImage.SetPosition(5, 2.5)
			scrollImage.AddFlag("not_pick")
			scrollImage.Show()
			self.scrollImage = scrollImage

			tabColor = ImageBox()
			tabColor.SetParent(self)
			tabColor.AddFlag("not_pick")
			tabColor.SetPosition(188, 12)
			tabColor.Hide()
			self.tabColor = tabColor

		def OpenCategory(self, qcount = 0):
			if qcount > 0:
				self.scrollImage.LoadImage("d:/ymir work/ui/quest_re/quest_up.tga")
			else:
				self.scrollImage.LoadImage("d:/ymir work/ui/quest_re/quest_down.tga")

		def CloseCategory(self, qcount = 0):
			self.scrollImage.LoadImage("d:/ymir work/ui/quest_re/quest_down.tga")

		def SetQuestLabel(self, filename, qcount):
			self.tabColor.LoadImage(filename)
			if qcount > 0:
				self.tabColor.Show()
			else:
				self.tabColor.Hide()

		def SetWidth(self, width):
			self.SetPosition(32, 0)
			self.SetSize(width, 23)

	class ListBar(Button):
		def __init__(self):
			Button.__init__(self)

		def __del__(self):
			Button.__del__(self)

		def MakeListBar(self, width, color):
			width = max(64, width)
			self.SetWidth(width)
			self.Show()

			checkbox = ImageBox()
			checkbox.SetParent(self)
			checkbox.LoadImage("d:/ymir work/ui/quest_re/quest_new.tga")
			checkbox.SetPosition(10, 7)
			checkbox.AddFlag("not_pick")
			checkbox.Show()
			self.checkbox = checkbox
			self.isChecked = False

		def SetWidth(self, width):
			self.SetPosition(32, 0)
			self.SetSize(width, 23)

		def CallEvent(self):
			self.OnClickEvent()
			super(ListBar, self).CallEvent()

		def OnClickEvent(self):
			self.checkbox.Hide()
			self.isChecked = True

		def SetSlot(self, slotIndex, itemIndex, width, height, icon, diffuseColor = (1.0, 1.0, 1.0, 1.0)):
			wndMgr.SetSlot(self.hWnd, slotIndex, itemIndex, width, height, icon, diffuseColor)

class HorizontalBar(Window):
	BLOCK_WIDTH = 32
	BLOCK_HEIGHT = 17

	def __init__(self):
		Window.__init__(self)
		self.AddFlag("attach")

	def __del__(self):
		Window.__del__(self)

	def Create(self, width):

		width = max(96, width)

		imgLeft = ImageBox()
		imgLeft.SetParent(self)
		imgLeft.AddFlag("not_pick")
		imgLeft.LoadImage("d:/ymir work/ui/pattern/horizontalbar_left.tga")
		imgLeft.Show()

		imgCenter = ExpandedImageBox()
		imgCenter.SetParent(self)
		imgCenter.AddFlag("not_pick")
		imgCenter.LoadImage("d:/ymir work/ui/pattern/horizontalbar_center.tga")
		imgCenter.Show()

		imgRight = ImageBox()
		imgRight.SetParent(self)
		imgRight.AddFlag("not_pick")
		imgRight.LoadImage("d:/ymir work/ui/pattern/horizontalbar_right.tga")
		imgRight.Show()

		self.imgLeft = imgLeft
		self.imgCenter = imgCenter
		self.imgRight = imgRight
		self.SetWidth(width)

	def SetWidth(self, width):
		self.imgCenter.SetRenderingRect(0.0, 0.0, float((width - self.BLOCK_WIDTH*2) - self.BLOCK_WIDTH) / self.BLOCK_WIDTH, 0.0)
		self.imgCenter.SetPosition(self.BLOCK_WIDTH, 0)
		self.imgRight.SetPosition(width - self.BLOCK_WIDTH, 0)
		self.SetSize(width, self.BLOCK_HEIGHT)

class Gauge(Window):
	SLOT_WIDTH = 16
	SLOT_HEIGHT = 7

	GAUGE_TEMPORARY_PLACE = 12
	GAUGE_WIDTH = 16

	def __init__(self):
		Window.__init__(self)
		self.width = 0
		if app.ENABLE_POISON_GAUGE_EFFECT:
			self.minValue = 0
			self.curValue = 0
			self.preVaule = 0
			self.targetID = 0
	def __del__(self):
		Window.__del__(self)

	def MakeGauge(self, width, color):
		self.width = max(48, width)

		imgSlotLeft = ImageBox()
		imgSlotLeft.SetParent(self)
		imgSlotLeft.LoadImage("d:/ymir work/ui/pattern/gauge_slot_left.tga")
		imgSlotLeft.Show()

		imgSlotRight = ImageBox()
		imgSlotRight.SetParent(self)
		imgSlotRight.LoadImage("d:/ymir work/ui/pattern/gauge_slot_right.tga")
		imgSlotRight.Show()
		imgSlotRight.SetPosition(width - self.SLOT_WIDTH, 0)

		imgSlotCenter = ExpandedImageBox()
		imgSlotCenter.SetParent(self)
		imgSlotCenter.LoadImage("d:/ymir work/ui/pattern/gauge_slot_center.tga")
		imgSlotCenter.Show()
		imgSlotCenter.SetRenderingRect(0.0, 0.0, float((width - self.SLOT_WIDTH*2) - self.SLOT_WIDTH) / self.SLOT_WIDTH, 0.0)
		imgSlotCenter.SetPosition(self.SLOT_WIDTH, 0)

		if osfInfo.PAST_HEALTH_ON_TARGET:
			imgGaugeBack = ExpandedImageBox()
			imgGaugeBack.SetParent(self)
			imgGaugeBack.LoadImage("d:/ymir work/ui/pattern/gauge_yellow.tga")
			imgGaugeBack.Hide()
			imgGaugeBack.SetRenderingRect(0.0, 0.0, 0.0, 0.0)
			imgGaugeBack.SetPosition(self.GAUGE_TEMPORARY_PLACE, 0)

		imgGauge = ExpandedImageBox()
		imgGauge.SetParent(self)
		imgGauge.LoadImage("d:/ymir work/ui/pattern/gauge_" + color + ".tga")
		imgGauge.Show()
		imgGauge.SetRenderingRect(0.0, 0.0, 0.0, 0.0)
		imgGauge.SetPosition(self.GAUGE_TEMPORARY_PLACE, 0)

		if app.ENABLE_POISON_GAUGE_EFFECT:
			aniGauge = Bar()
			aniGauge.SetParent(self)
			aniGauge.SetPosition(self.GAUGE_TEMPORARY_PLACE, 0)
			aniGauge.Hide()

		imgSlotLeft.AddFlag("attach")
		imgSlotCenter.AddFlag("attach")
		imgSlotRight.AddFlag("attach")

		if app.WJ_SHOW_PARTY_ON_MINIMAP:
			imgSlotLeft.AddFlag("not_pick")
			imgSlotCenter.AddFlag("not_pick")
			imgSlotRight.AddFlag("not_pick")
			imgGauge.AddFlag("not_pick")

		self.imgLeft = imgSlotLeft
		self.imgCenter = imgSlotCenter
		self.imgRight = imgSlotRight
		self.imgGauge = imgGauge
		if osfInfo.PAST_HEALTH_ON_TARGET:
			self.imgGaugeBack = imgGaugeBack
		if app.ENABLE_POISON_GAUGE_EFFECT:
			self.aniGauge = aniGauge
		self.SetSize(width, self.SLOT_HEIGHT)

	if app.WJ_SHOW_PARTY_ON_MINIMAP:
		def GaugeImgBoxAddFlag(self, flag):
			self.imgLeft.AddFlag(flag)
			self.imgCenter.AddFlag(flag)
			self.imgRight.AddFlag(flag)
			self.imgGauge.AddFlag(flag)

	def SetPercentage(self, curValue, maxValue):
		# PERCENTAGE_MAX_VALUE_ZERO_DIVISION_ERROR
		if maxValue > 0.0:
			percentage = min(1.0, float(curValue)/float(maxValue))
		else:
			percentage = 0.0
		# END_OF_PERCENTAGE_MAX_VALUE_ZERO_DIVISION_ERROR

		if osfInfo.PAST_HEALTH_ON_TARGET:
			self.lastCurValue = curValue
			self.lastMaxValue = maxValue

		gaugeSize = -1.0 + float(self.width - self.GAUGE_TEMPORARY_PLACE*2) * percentage / self.GAUGE_WIDTH
		self.imgGauge.SetRenderingRect(0.0, 0.0, gaugeSize, 0.0)

	if app.ENABLE_POISON_GAUGE_EFFECT:
		def SetGaugeColor(self, color):
			if self.imgGauge:
				self.imgGauge.LoadImage("d:/ymir work/ui/pattern/gauge_" + color + ".tga")
				
		def SetDMGPercentage(self, targetID, minValue, curValue, maxValue, color=0x55ff0000):
			if self.curValue < self.minValue:
				self.curValue = self.minValue

			if not self.targetID or self.targetID != targetID:
				self.targetID = targetID
				self.aniGauge.Hide()
				return

			percentage = (float(minValue)*float(maxValue-self.GAUGE_TEMPORARY_PLACE*2))/100
			percentage2 = (float(curValue)*float(maxValue-self.GAUGE_TEMPORARY_PLACE*2))/100
			gaugeSize = percentage+(percentage2-percentage)
			self.minValue = percentage
			self.curValue = gaugeSize

			self.aniGauge.SetColor(color)
			self.aniGauge.SetSize(gaugeSize, 7)
			self.aniGauge.Show()
			
			if gaugeSize <= 0:
				self.aniGauge.Hide()
				
		def OnUpdate(self):
			if self.curValue and self.aniGauge.IsShow():
				if self.curValue > self.minValue:
					if self.curValue > self.minValue*2:
						self.curValue = self.curValue - 1.5
					else:
						self.curValue = self.curValue - 0.3
					self.aniGauge.SetSize(self.curValue, 7)
					
		def GetPrevalue(self):
			return self.preVaule

	if osfInfo.PAST_HEALTH_ON_TARGET:
		def SetPercentageBack(self, curValue, maxValue):
			if not self.imgGaugeBack.IsShow():
				self.imgGaugeBack.Show()

			if maxValue > 0.0:
				percentage = min(1.0, float(curValue)/float(maxValue))
			else:
				percentage = 0.0

			gaugeSize = -1.0 + float(self.width - self.GAUGE_TEMPORARY_PLACE*2) * percentage / self.GAUGE_WIDTH
			if app.ENABLE_POISON_GAUGE_EFFECT:
				self.preVaule = curValue
			self.imgGaugeBack.SetRenderingRect(0.0, 0.0, gaugeSize, 0.0)

class Board(Window):
	CORNER_WIDTH = 32
	CORNER_HEIGHT = 32
	LINE_WIDTH = 128
	LINE_HEIGHT = 128

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self):
		Window.__init__(self)
		if app.ENABLE_IMAGE_CLIP_RECT:
			self.skipMaxCheck = False

		self.MakeBoard("d:/ymir work/ui/pattern/Board_Corner_", "d:/ymir work/ui/pattern/Board_Line_")
		self.MakeBase()

	def MakeBoard(self, cornerPath, linePath):

		CornerFileNames = [ cornerPath+dir+".tga" for dir in ("LeftTop", "LeftBottom", "RightTop", "RightBottom", ) ]
		LineFileNames = [ linePath+dir+".tga" for dir in ("Left", "Right", "Top", "Bottom", ) ]
		"""
		CornerFileNames = (
							"d:/ymir work/ui/pattern/Board_Corner_LeftTop.tga",
							"d:/ymir work/ui/pattern/Board_Corner_LeftBottom.tga",
							"d:/ymir work/ui/pattern/Board_Corner_RightTop.tga",
							"d:/ymir work/ui/pattern/Board_Corner_RightBottom.tga",
							)
		LineFileNames = (
							"d:/ymir work/ui/pattern/Board_Line_Left.tga",
							"d:/ymir work/ui/pattern/Board_Line_Right.tga",
							"d:/ymir work/ui/pattern/Board_Line_Top.tga",
							"d:/ymir work/ui/pattern/Board_Line_Bottom.tga",
							)
		"""

		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ExpandedImageBox()
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)

		self.Lines = []
		for fileName in LineFileNames:
			Line = ExpandedImageBox()
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)

		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)

	def MakeBase(self):
		self.Base = ExpandedImageBox()
		self.Base.AddFlag("not_pick")
		self.Base.LoadImage("d:/ymir work/ui/pattern/Board_Base.tga")
		self.Base.SetParent(self)
		self.Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Base.Show()

	def LoadVisuals(self, cornerPath, linePath, basePath):
		directions = ("LeftTop", "LeftBottom", "RightTop", "RightBottom")
		for image, direction in zip(self.Corners, directions):
			image.LoadImage(cornerPath + direction + ".tga")

		directions = ("Left", "Right", "Top", "Bottom")
		for image, direction in zip(self.Lines, directions):
			image.LoadImage(linePath + direction + ".tga")

		self.Base.LoadImage(basePath)

	def __del__(self):
		Window.__del__(self)

	def SetSize(self, width, height):
		if app.ENABLE_IMAGE_CLIP_RECT:
			if not self.skipMaxCheck:
				width = max(self.CORNER_WIDTH * 2, width)
				height = max(self.CORNER_HEIGHT * 2, height)
		else:
			width = max(self.CORNER_WIDTH * 2, width)
			height = max(self.CORNER_HEIGHT * 2, height)
		Window.SetSize(self, width, height)

		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)

		if self.Base:
			self.Base.SetRenderingRect(0, 0, horizontalShowingPercentage, verticalShowingPercentage)

class BoardWithTitleBar(Board):
	def __init__(self):
		Board.__init__(self)

		titleBar = TitleBar()
		titleBar.SetParent(self)
		titleBar.MakeTitleBar(0, "red")
		titleBar.SetPosition(-4, 0)
		titleBar.Show()

		titleName = TextLine()
		titleName.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_WINDOW_TITLE))
		titleName.SetParent(titleBar)
		titleName.SetPosition(0, 4)
		titleName.SetWindowHorizontalAlignCenter()
		titleName.SetHorizontalAlignCenter()
		titleName.Show()

		self.titleBar = titleBar
		self.titleName = titleName

		self.SetCloseEvent(self.Hide)

	def __del__(self):
		Board.__del__(self)
		self.titleBar = None
		self.titleName = None

	def SetSize(self, width, height):
		self.titleBar.SetWidth(width + 8)
		#self.pickRestrictWindow.SetSize(width, height - 30)
		Board.SetSize(self, width, height)
		self.titleName.UpdateRect()

	def SetTitleColor(self, color):
		self.titleName.SetPackedFontColor(color)

	def SetTitleName(self, name):
		self.titleName.SetText(name)

	def SetCloseEvent(self, event):
		self.titleBar.SetCloseEvent(event)

class ThinBoard(Window):
	CORNER_WIDTH = 16
	CORNER_HEIGHT = 16
	LINE_WIDTH = 16
	LINE_HEIGHT = 16
	BOARD_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.69)

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self, layer = "UI", cornerPrefix = None, linePrefix = None, baseColor = None):
		Window.__init__(self, layer)

		if cornerPrefix is None:
			cornerPrefix = "d:/ymir work/ui/pattern/ThinBoard_Corner_"
		if linePrefix is None:
			linePrefix = "d:/ymir work/ui/pattern/ThinBoard_Line_"
		CornerFileNames = [ cornerPrefix+dir+".tga" for dir in ["LeftTop","LeftBottom","RightTop","RightBottom"] ]
		LineFileNames = [ linePrefix+dir+".tga" for dir in ["Left","Right","Top","Bottom"] ]

		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ExpandedImageBox()
			Corner.AddFlag("attach")
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)

		self.Lines = []
		for fileName in LineFileNames:
			Line = ExpandedImageBox()
			Line.AddFlag("attach")
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)

		self.usesColorBase = baseColor is not None
		self.baseColor = baseColor
		Base = Bar() if self.usesColorBase else ExpandedImageBox()
		Base.SetParent(self)
		Base.AddFlag("attach")
		Base.AddFlag("not_pick")
		if self.usesColorBase:
			Base.SetColor(baseColor)
		else:
			Base.LoadImage("d:/ymir work/ui/pattern/Board_Base.tga")
		Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		Base.Show()
		self.Base = Base

		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)

	def LoadVisuals(self, cornerPath, linePath, basePath):
		directions = ("LeftTop", "LeftBottom", "RightTop", "RightBottom")
		for image, direction in zip(self.Corners, directions):
			image.LoadImage(cornerPath + direction + ".tga")

		directions = ("Left", "Right", "Top", "Bottom")
		for image, direction in zip(self.Lines, directions):
			image.LoadImage(linePath + direction + ".tga")

		if not self.usesColorBase:
			self.Base.LoadImage(basePath)

	def __del__(self):
		Window.__del__(self)

	if app.ENABLE_SEND_TARGET_INFO:
		def ShowCorner(self, corner):
			self.Corners[corner].Show()
			self.SetSize(self.GetWidth(), self.GetHeight())

		def HideCorners(self, corner):
			self.Corners[corner].Hide()
			self.SetSize(self.GetWidth(), self.GetHeight())

		def ShowLine(self, line):
			self.Lines[line].Show()
			self.SetSize(self.GetWidth(), self.GetHeight())

		def HideLine(self, line):
			self.Lines[line].Hide()
			self.SetSize(self.GetWidth(), self.GetHeight())

	def SetSize(self, width, height):
		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		Window.SetSize(self, width, height)

		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		if self.usesColorBase:
			self.Base.SetSize(width - self.CORNER_WIDTH*2, height - self.CORNER_HEIGHT*2)
		else:
			self.Base.SetRenderingRect(
				0,
				0,
				float((width - self.CORNER_WIDTH*2) - self.Base.GetWidth()) / self.Base.GetWidth(),
				float((height - self.CORNER_HEIGHT*2) - self.Base.GetHeight()) / self.Base.GetHeight(),
			)

	def ShowInternal(self):
		self.Base.Show()
		for wnd in self.Lines:
			wnd.Show()
		for wnd in self.Corners:
			wnd.Show()

	def HideInternal(self):
		self.Base.Hide()
		for wnd in self.Lines:
			wnd.Hide()
		for wnd in self.Corners:
			wnd.Hide()

	if app.ENABLE_NEW_TIPMESSAGE:
		def SetAlpha(self, alpha):
			if self.usesColorBase:
				baseAlpha = (self.baseColor >> 24) & 0xff
				self.Base.SetColor((self.baseColor & 0x00ffffff) | (int(baseAlpha * alpha) << 24))
			else:
				self.Base.SetAlpha(alpha)
			for wnd in self.Lines:
				wnd.SetAlpha(alpha)
			for wnd in self.Corners:
				wnd.SetAlpha(alpha)

class ThinBoardGold(Window):
	CORNER_WIDTH = 16
	CORNER_HEIGHT = 16
	LINE_WIDTH = 16
	LINE_HEIGHT = 16

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		CornerFileNames = [ "d:/ymir work/ui/pattern/thinboardgold/ThinBoard_Corner_"+dir+"_Gold.tga" for dir in ["LeftTop","LeftBottom","RightTop","RightBottom"] ]
		LineFileNames = [ "d:/ymir work/ui/pattern/thinboardgold/ThinBoard_Line_"+dir+"_Gold.tga" for dir in ["Left","Right","Top","Bottom"] ]

		self.MakeBase()

		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ExpandedImageBox()
			Corner.AddFlag("attach")
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)

		self.Lines = []
		for fileName in LineFileNames:
			Line = ExpandedImageBox()
			Line.AddFlag("attach")
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)

		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)

	def __del__(self):
		Window.__del__(self)

	def SetSize(self, width, height):

		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		Window.SetSize(self, width, height)

		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH

		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)

		#self.Base.GetWidth()
		#self.Base.GetHeight()
		"""
			Defalt Width : 128, Height : 128 
			0.0 > 128, 1.0 > 256 
		"""
		if self.Base:
			self.Base.SetRenderingRect(0, 0, (float(width)-32)/float(self.Base.GetWidth()) - 1.0, (float(height)-32)/float(self.Base.GetHeight()) - 1.0)

	def MakeBase(self):
		self.Base = ExpandedImageBox()
		self.Base.AddFlag("not_pick")
		self.Base.LoadImage("d:/ymir work/ui/pattern/Board_Base.tga")
		self.Base.SetParent(self)
		self.Base.SetPosition(16, 16)
		self.Base.SetAlpha(0.8)
		self.Base.Show()

	def ShowInternal(self):
		self.Base.Show()
		for wnd in self.Lines:
			wnd.Show()
		for wnd in self.Corners:
			wnd.Show()

	def HideInternal(self):
		self.Base.Hide()
		for wnd in self.Lines:
			wnd.Hide()
		for wnd in self.Corners:
			wnd.Hide()

class ThinBoardCircle(Window):
	CORNER_WIDTH = 4
	CORNER_HEIGHT = 4
	LINE_WIDTH = 4
	LINE_HEIGHT = 4
	BOARD_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		CornerFileNames = [ "d:/ymir work/ui/pattern/thinboardcircle/ThinBoard_Corner_"+dir+"_Circle.tga" for dir in ["LeftTop","LeftBottom","RightTop","RightBottom"] ]
		LineFileNames = [ "d:/ymir work/ui/pattern/thinboardcircle/ThinBoard_Line_"+dir+"_Circle.tga" for dir in ["Left","Right","Top","Bottom"] ]

		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ExpandedImageBox()
			Corner.AddFlag("attach")
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)

		self.Lines = []
		for fileName in LineFileNames:
			Line = ExpandedImageBox()
			Line.AddFlag("attach")
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)

		Base = Bar()
		Base.SetParent(self)
		Base.AddFlag("attach")
		Base.AddFlag("not_pick")
		Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		Base.SetColor(self.BOARD_COLOR)
		Base.Show()
		self.Base = Base

		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)

	def __del__(self):
		Window.__del__(self)

	def SetSize(self, width, height):

		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		Window.SetSize(self, width, height)

		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Base.SetSize(width - self.CORNER_WIDTH*2, height - self.CORNER_HEIGHT*2)

	def ShowInternal(self):
		self.Base.Show()
		for wnd in self.Lines:
			wnd.Show()
		for wnd in self.Corners:
			wnd.Show()

	def HideInternal(self):
		self.Base.Hide()
		for wnd in self.Lines:
			wnd.Hide()
		for wnd in self.Corners:
			wnd.Hide()

if app.ENABLE_BATTLE_PASS:
	class BorderA(ThinBoardCircle):
		def __init__(self, layer = "UI"):
			ThinBoardCircle.__init__(self)

		def __del__(self):
			ThinBoardCircle.__del__(self)

		def SetSize(self, width, height):
			ThinBoardCircle.SetSize(self, width, height)

	class WikiScrollBar(Window):
		BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 1.0)
		CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3411, 0.3411, 0.3411, 1.0)

		BAR_NUMB = 9 #This is static value! Please dont touch in him.

		class MiddleBar(DragButton):
			MIDDLE_BAR_COLOR = grp.GenerateColor(0.6470, 0.6470, 0.6470, 1.0)

			def __init__(self, horizontal_scroll):
				DragButton.__init__(self)
				self.AddFlag("movable")

				self.horizontal_scroll = horizontal_scroll

				self.middle = Bar()
				self.middle.SetParent(self)
				self.middle.AddFlag("attach")
				self.middle.AddFlag("not_pick")
				self.middle.SetColor(self.MIDDLE_BAR_COLOR)
				self.middle.SetSize(1, 1)
				self.middle.Show()

			def SetStaticScale(self, size):
				(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())

				if not self.horizontal_scroll:
					DragButton.SetSize(self, base_width, size)
					self.middle.SetSize(base_width, size)
				else:
					DragButton.SetSize(self, size, base_height)
					self.middle.SetSize(size, base_height)

			def SetSize(self, selfSize, fullSize):
				(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())

				if not self.horizontal_scroll:
					DragButton.SetSize(self, base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
					self.middle.SetSize(base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
				else:
					DragButton.SetSize(self, truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
					self.middle.SetSize(truediv(int(selfSize), int(fullSize)) * selfSize, base_height)

			def SetStaticSize(self, size):
				size = max(2, size)

				if not self.horizontal_scroll:
					DragButton.SetSize(self, size, self.middle.GetHeight())
					self.middle.SetSize(size, self.middle.GetHeight())
				else:
					DragButton.SetSize(self, self.middle.GetWidth(), size)
					self.middle.SetSize(self.middle.GetWidth(), size)

		def __init__(self, horizontal_scroll = False):
			Window.__init__(self)

			self.horizontal_scroll = horizontal_scroll

			self.scrollEvent = None
			self.scrollSpeed = 1
			self.sizeScale = 1.0

			self.bars = []
			for i in range(self.BAR_NUMB):
				br = Bar()
				br.SetParent(self)
				br.AddFlag("attach")
				br.AddFlag("not_pick")
				br.SetColor([self.CORNERS_AND_LINES_COLOR, self.BASE_COLOR][i == (self.BAR_NUMB-1)])
				if not (i % 2 == 0): br.SetSize(1, 1)
				br.Show()

				self.bars.append(br)

			self.middleBar = self.MiddleBar(self.horizontal_scroll)
			self.middleBar.SetParent(self)
			self.middleBar.SetMoveEvent(__mem_func__(self.OnScrollMove))
			self.middleBar.Show()

		def OnScrollMove(self):
			if not self.scrollEvent:
				return

			arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else\
					float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())

			self.scrollEvent(arg)

		def SetScrollEvent(self, func):
			self.scrollEvent = __mem_func__(func)

		def SetScrollSpeed(self, speed):
			self.scrollSpeed = speed

		def OnMouseWheel(self, length):
			if self.IsInPosition():
				if not self.horizontal_scroll:
					val = min(max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale), self.GetHeight() - self.middleBar.GetHeight() - 1)
					self.middleBar.SetPosition(1, val)
				else:
					val = min(max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) *  self.scrollSpeed * self.sizeScale), self.GetWidth() - self.middleBar.GetWidth() - 1)
					self.middleBar.SetPosition(val, 1)

				self.OnScrollMove()
				return True

			return False

		def OnMouseLeftButtonDown(self):
			(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()

			if not self.horizontal_scroll:
				if xMouseLocalPosition == 0 or xMouseLocalPosition == self.GetWidth():
					return

				y_pos = (yMouseLocalPosition - self.middleBar.GetHeight() // 2)
				self.middleBar.SetPosition(1, y_pos)
			else:
				if yMouseLocalPosition == 0 or yMouseLocalPosition == self.GetHeight():
					return

				x_pos = (xMouseLocalPosition - self.middleBar.GetWidth() // 2)
				self.middleBar.SetPosition(x_pos, 1)

			self.OnScrollMove()

		def SetSize(self, w, h):
			(width, height) = (max(3, w), max(3, h))

			Window.SetSize(self, width, height)

			self.bars[0].SetSize(1, (height - 2))
			self.bars[0].SetPosition(0, 1)
			self.bars[2].SetSize((width - 2), 1)
			self.bars[2].SetPosition(1, 0)
			self.bars[4].SetSize(1, (height - 2))
			self.bars[4].SetPosition((width - 1), 1)
			self.bars[6].SetSize((width - 2), 1)
			self.bars[6].SetPosition(1, (height - 1))
			self.bars[8].SetSize((width - 2), (height - 2))
			self.bars[8].SetPosition(1, 1)

			self.bars[1].SetPosition(0, 0)
			self.bars[3].SetPosition((width - 1), 0)
			self.bars[5].SetPosition((width - 1), (height - 1))
			self.bars[7].SetPosition(0, (height - 1))

			if not self.horizontal_scroll:
				self.middleBar.SetStaticSize(width - 2)
				self.middleBar.SetSize(12, self.GetHeight())
			else:
				self.middleBar.SetStaticSize(height - 2)
				self.middleBar.SetSize(12, self.GetWidth())

			self.middleBar.SetRestrictMovementArea(1, 1, width - 2, height - 2)

		def SetScale(self, selfSize, fullSize):
			self.sizeScale = float(selfSize/fullSize)
			self.middleBar.SetSize(selfSize, fullSize)

		def SetStaticScale(self, r_size):
			self.middleBar.SetStaticScale(r_size)

		def SetPosScale(self, fScale):
			pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else\
					(math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)

			self.SetPos(pos)

		def SetPos(self, pos):
			wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
			self.middleBar.SetPosition(*wPos)

if "ScrollbarDyn" not in globals():
	try:
		ScrollbarDyn = WikiScrollBar
	except NameError:
		class ScrollbarDyn(Window):
			BASE_COLOR = grp.GenerateColor(0.0, 0.0, 0.0, 0.0)
			CORNERS_AND_LINES_COLOR = grp.GenerateColor(0.3961, 0.3804, 0.3647, 1.0)
			BAR_NUMB = 9

			class MiddleBar(DragButton):
				MIDDLE_BAR_COLOR = grp.GenerateColor(0.3, 0.3, 0.3, 1.0)

				def __init__(self, horizontal_scroll):
					DragButton.__init__(self)
					self.AddFlag("movable")

					self.horizontal_scroll = horizontal_scroll

					self.middle = Bar()
					self.middle.SetParent(self)
					self.middle.AddFlag("attach")
					self.middle.AddFlag("not_pick")
					self.middle.SetColor(self.MIDDLE_BAR_COLOR)
					self.middle.SetSize(1, 1)
					self.middle.Show()

				def SetStaticScale(self, size):
					(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())

					if not self.horizontal_scroll:
						DragButton.SetSize(self, base_width, size)
						self.middle.SetSize(base_width, size)
					else:
						DragButton.SetSize(self, size, base_height)
						self.middle.SetSize(size, base_height)

				def SetSize(self, selfSize, fullSize):
					(base_width, base_height) = (self.middle.GetWidth(), self.middle.GetHeight())

					if not self.horizontal_scroll:
						DragButton.SetSize(self, base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
						self.middle.SetSize(base_width, truediv(int(selfSize), int(fullSize)) * selfSize)
					else:
						DragButton.SetSize(self, truediv(int(selfSize), int(fullSize)) * selfSize, base_height)
						self.middle.SetSize(truediv(int(selfSize), int(fullSize)) * selfSize, base_height)

				def SetStaticSize(self, size):
					size = max(2, size)

					if not self.horizontal_scroll:
						DragButton.SetSize(self, size, self.middle.GetHeight())
						self.middle.SetSize(size, self.middle.GetHeight())
					else:
						DragButton.SetSize(self, self.middle.GetWidth(), size)
						self.middle.SetSize(self.middle.GetWidth(), size)

			def __init__(self, horizontal_scroll=False):
				Window.__init__(self)

				self.horizontal_scroll = horizontal_scroll

				self.scrollEvent = None
				self.scrollSpeed = 1
				self.sizeScale = 1.0

				self.is_scrollable = True

				self.bars = []
				for i in range(self.BAR_NUMB):
					br = Bar()
					br.SetParent(self)
					br.AddFlag("attach")
					br.AddFlag("not_pick")
					br.SetColor([self.CORNERS_AND_LINES_COLOR, self.BASE_COLOR][i == (self.BAR_NUMB-1)])
					if not (i % 2 == 0):
						br.SetSize(1, 1)
					br.Show()

					self.bars.append(br)

				self.middleBar = self.MiddleBar(self.horizontal_scroll)
				self.middleBar.SetParent(self)
				self.middleBar.SetMoveEvent(__mem_func__(self.OnScrollMove))
				self.middleBar.Show()

			def OnScrollMove(self):
				if not self.scrollEvent:
					return

				arg = float(self.middleBar.GetLocalPosition()[1] - 1) / float(self.GetHeight() - 2 - self.middleBar.GetHeight()) if not self.horizontal_scroll else \
					float(self.middleBar.GetLocalPosition()[0] - 1) / float(self.GetWidth() - 2 - self.middleBar.GetWidth())

				self.scrollEvent(arg)

			def SetScrollEvent(self, func):
				self.scrollEvent = __mem_func__(func)

			def SetScrollSpeed(self, speed):
				self.scrollSpeed = speed

			def OnMouseWheel(self, length):
				if self.IsInPosition():
					if not self.horizontal_scroll:
						val = min(
							max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale),
							self.GetHeight() - self.middleBar.GetHeight() - 1
						)
						self.middleBar.SetPosition(1, val)
					else:
						val = min(
							max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) * self.scrollSpeed * self.sizeScale),
							self.GetWidth() - self.middleBar.GetWidth() - 1
						)
						self.middleBar.SetPosition(val, 1)

					self.OnScrollMove()
					return True

				return False

			def OnHorizontalWheelEvent(self, length):
				if not self.horizontal_scroll:
					val = min(
						max(1, self.middleBar.GetLocalPosition()[1] - (length * 0.01) * self.scrollSpeed * self.sizeScale),
						self.GetHeight() - self.middleBar.GetHeight() - 1
					)
					self.middleBar.SetPosition(1, val)
				else:
					val = min(
						max(1, self.middleBar.GetLocalPosition()[0] - (length * 0.01) * self.scrollSpeed * self.sizeScale),
						self.GetWidth() - self.middleBar.GetWidth() - 1
					)
					self.middleBar.SetPosition(val, 1)

				self.OnScrollMove()
				return True

			def OnMouseLeftButtonDown(self):
				(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()

				if not self.horizontal_scroll:
					if xMouseLocalPosition == 0 or xMouseLocalPosition == self.GetWidth():
						return

					y_pos = (yMouseLocalPosition - self.middleBar.GetHeight() // 2)
					self.middleBar.SetPosition(1, y_pos)
				else:
					if yMouseLocalPosition == 0 or yMouseLocalPosition == self.GetHeight():
						return

					x_pos = (xMouseLocalPosition - self.middleBar.GetWidth() // 2)
					self.middleBar.SetPosition(x_pos, 1)

				self.OnScrollMove()

			def SetSize(self, w, h):
				(width, height) = (max(3, w), max(3, h))

				Window.SetSize(self, width, height)

				self.bars[0].SetSize(1, (height - 2))
				self.bars[0].SetPosition(0, 1)
				self.bars[2].SetSize((width - 2), 1)
				self.bars[2].SetPosition(1, 0)
				self.bars[4].SetSize(1, (height - 2))
				self.bars[4].SetPosition((width - 1), 1)
				self.bars[6].SetSize((width - 2), 1)
				self.bars[6].SetPosition(1, (height - 1))
				self.bars[8].SetSize((width - 2), (height - 2))
				self.bars[8].SetPosition(1, 1)

				self.bars[1].SetPosition(0, 0)
				self.bars[3].SetPosition((width - 1), 0)
				self.bars[5].SetPosition((width - 1), (height - 1))
				self.bars[7].SetPosition(0, (height - 1))

				if not self.horizontal_scroll:
					self.middleBar.SetStaticSize(width - 2)
					self.middleBar.SetSize(12, self.GetHeight())
				else:
					self.middleBar.SetStaticSize(height - 2)
					self.middleBar.SetSize(12, self.GetWidth())

				self.middleBar.SetRestrictMovementArea(1, 1, width - 2, height - 2)

			def SetScale(self, selfSize, fullSize):
				self.sizeScale = float(selfSize / fullSize)
				self.middleBar.SetSize(selfSize, fullSize)

			def SetStaticScale(self, r_size):
				self.middleBar.SetStaticScale(r_size)

			def SetPosScale(self, fScale):
				pos = (math.ceil((self.GetHeight() - 2 - self.middleBar.GetHeight()) * fScale) + 1) if not self.horizontal_scroll else \
					(math.ceil((self.GetWidth() - 2 - self.middleBar.GetWidth()) * fScale) + 1)

				self.SetPos(pos)

			def SetPos(self, pos):
				wPos = (1, pos) if not self.horizontal_scroll else (pos, 1)
				self.middleBar.SetPosition(*wPos)

class ScrollBar(Window):
	SCROLLBAR_WIDTH = 17
	SCROLLBAR_MIDDLE_HEIGHT = 9
	SCROLLBAR_BUTTON_WIDTH = 17
	SCROLLBAR_BUTTON_HEIGHT = 17
	MIDDLE_BAR_POS = 5
	MIDDLE_BAR_UPPER_PLACE = 3
	MIDDLE_BAR_DOWNER_PLACE = 4
	TEMP_SPACE = MIDDLE_BAR_UPPER_PLACE + MIDDLE_BAR_DOWNER_PLACE

	class MiddleBar(DragButton):
		def __init__(self):
			DragButton.__init__(self)
			self.AddFlag("movable")
			#self.AddFlag("restrict_x")

		def MakeImage(self):
			top = ImageBox()
			top.SetParent(self)
			top.LoadImage("d:/ymir work/ui/pattern/ScrollBar_Top.tga")
			top.SetPosition(0, 0)
			top.AddFlag("not_pick")
			top.Show()
			bottom = ImageBox()
			bottom.SetParent(self)
			bottom.LoadImage("d:/ymir work/ui/pattern/ScrollBar_Bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()

			middle = ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage("d:/ymir work/ui/pattern/ScrollBar_Middle.tga")
			middle.SetPosition(0, 4)
			middle.AddFlag("not_pick")
			middle.Show()

			self.top = top
			self.bottom = bottom
			self.middle = middle

		def SetSize(self, height):
			height = max(12, height)
			DragButton.SetSize(self, 10, height)
			self.bottom.SetPosition(0, height-4)

			height -= 4*3
			self.middle.SetRenderingRect(0, 0, 0, float(height)/4.0)

	def __init__(self):
		Window.__init__(self)

		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = lambda *arg: None
		self.lockFlag = False
		self.scrollStep = 0.20

		self.UpScrollButtonEvent = lambda *arg: None
		self.DownScrollButtonEvent = lambda *arg: None

		self.eventFuncCall = True

		self.CreateScrollBar()

	def __del__(self):
		Window.__del__(self)

	def CreateScrollBar(self):
		barSlot = Bar3D()
		barSlot.SetParent(self)
		barSlot.AddFlag("not_pick")
		barSlot.Show()

		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.MakeImage()
		middleBar.SetSize(12)

		upButton = Button()
		upButton.SetParent(self)
		upButton.SetEvent(__mem_func__(self.OnUp))
		upButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/up_01.tga")
		upButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/up_02.tga")
		upButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/up_03.tga")
		upButton.Show()

		downButton = Button()
		downButton.SetParent(self)
		downButton.SetEvent(__mem_func__(self.OnDown))
		downButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/down_01.tga")
		downButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/down_02.tga")
		downButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/scrollbar/down_03.tga")
		downButton.Show()

		self.upButton = upButton
		self.downButton = downButton
		self.middleBar = middleBar
		self.barSlot = barSlot

		self.SCROLLBAR_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()
		self.SCROLLBAR_BUTTON_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_HEIGHT = self.upButton.GetHeight()

	def OnMouseWheel(self, delta):
		if delta > 0:
			self.SetPos(self.curPos - (self.scrollStep/4))
			return True
		elif delta < 0:
			self.SetPos(self.curPos + (self.scrollStep/4))
			return True
		return False

	def OnMouseWheel2(self, delta):
		if delta > 0:
			self.SetPos(self.curPos - (self.scrollStep))
			return True
		elif delta < 0:
			self.SetPos(self.curPos + (self.scrollStep))
			return True
		return False

	def Destroy(self):
		self.middleBar = None
		self.upButton = None
		self.downButton = None
		self.eventScroll = lambda *arg: None

		self.UpScrollButtonEvent = lambda *arg: None
		self.DownScrollButtonEvent = lambda *arg: None

		self.eventFuncCall = True

	def SetUpScrollButtonEvent(self, event):
		self.UpScrollButtonEvent = event

	def SetDownScrollButtonEvent(self, event):
		self.DownScrollButtonEvent = event

	def SetEvnetFuncCall(self, callable):
		self.eventFuncCall = callable

	def SetScrollEvent(self, event):
		self.eventScroll = event

	def SetMiddleBarSize(self, pageScale):
		realHeight = self.GetHeight() - self.SCROLLBAR_BUTTON_HEIGHT*2
		self.SCROLLBAR_MIDDLE_HEIGHT = int(pageScale * float(realHeight))
		self.middleBar.SetSize(self.SCROLLBAR_MIDDLE_HEIGHT)
		self.pageSize = (self.GetHeight() - self.SCROLLBAR_BUTTON_HEIGHT*2) - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)

	def SetScrollBarSize(self, height):
		self.pageSize = (height - self.SCROLLBAR_BUTTON_HEIGHT*2) - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.upButton.SetPosition(0, 0)
		self.downButton.SetPosition(0, height - self.SCROLLBAR_BUTTON_HEIGHT)
		self.middleBar.SetRestrictMovementArea(self.MIDDLE_BAR_POS, self.SCROLLBAR_BUTTON_HEIGHT + self.MIDDLE_BAR_UPPER_PLACE, self.MIDDLE_BAR_POS+2, height - self.SCROLLBAR_BUTTON_HEIGHT*2 - self.TEMP_SPACE)
		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, 0)

		self.UpdateBarSlot()

	def UpdateBarSlot(self):
		self.barSlot.SetPosition(0, self.SCROLLBAR_BUTTON_HEIGHT)
		self.barSlot.SetSize(self.GetWidth() - 2, self.GetHeight() - self.SCROLLBAR_BUTTON_HEIGHT*2 - 2)

	def GetPos(self):
		return self.curPos

	def SetPos(self, pos, event_callable = True):
		pos = max(0.0, pos)
		pos = min(1.0, pos)

		newPos = float(self.pageSize) * pos
		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, int(newPos) + self.SCROLLBAR_BUTTON_HEIGHT + self.MIDDLE_BAR_UPPER_PLACE)

		self.OnMove(event_callable)

	def SetScrollStep(self, step):
		self.scrollStep = step

	def GetScrollStep(self):
		return self.scrollStep

	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep, self.eventFuncCall)
		self.UpScrollButtonEvent()

	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep, self.eventFuncCall)
		self.DownScrollButtonEvent()

	def OnMove(self, event_callable = True):
		if self.lockFlag:
			return

		if 0 == self.pageSize:
			return

		(xLocal, yLocal) = self.middleBar.GetLocalPosition()
		self.curPos = float(yLocal - self.SCROLLBAR_BUTTON_HEIGHT - self.MIDDLE_BAR_UPPER_PLACE) / float(self.pageSize)

		if event_callable:
			self.eventScroll()

	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		pickedPos = yMouseLocalPosition - self.SCROLLBAR_BUTTON_HEIGHT - self.SCROLLBAR_MIDDLE_HEIGHT//2
		newPos = float(pickedPos) / float(self.pageSize)
		self.SetPos(newPos)

	def LockScroll(self):
		self.lockFlag = True

	def UnlockScroll(self):
		self.lockFlag = False

	def SetUpButtonSizeRefresh(self):
		self.SCROLLBAR_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_HEIGHT = self.upButton.GetHeight()

	def SetUpButtonUpVisual(self, img_path):
		if self.upButton:
			self.upButton.SetUpVisual(img_path)

	def SetUpButtonOverVisual(self, img_path):
		if self.upButton:
			self.upButton.SetOverVisual(img_path)

	def SetUpButtonDownVisual(self, img_path):
		if self.upButton:
			self.upButton.SetDownVisual(img_path)

	def SetDownButtonUpVisual(self, img_path):
		if self.downButton:
			self.downButton.SetUpVisual(img_path)

	def SetDownButtonOverVisual(self, img_path):
		if self.downButton:
			self.downButton.SetOverVisual(img_path)

	def SetDownButtonDownVisual(self, img_path):
		if self.downButton:
			self.downButton.SetDownVisual(img_path)

class ThinScrollBar(ScrollBar):
	def CreateScrollBar(self):
		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.SetUpVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/thumb_01.tga")
		middleBar.SetOverVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/thumb_02.tga")
		middleBar.SetDownVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/thumb_03.tga")

		upButton = Button()
		upButton.SetParent(self)
		upButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/up_01.tga")
		upButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/up_02.tga")
		upButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/up_03.tga")
		upButton.SetEvent(__mem_func__(self.OnUp))
		upButton.Show()

		downButton = Button()
		downButton.SetParent(self)
		downButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/down_01.tga")
		downButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/down_02.tga")
		downButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/thin_scrollbar/down_03.tga")
		downButton.SetEvent(__mem_func__(self.OnDown))
		downButton.Show()

		self.middleBar = middleBar
		self.upButton = upButton
		self.downButton = downButton

		self.SCROLLBAR_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()
		self.SCROLLBAR_BUTTON_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_HEIGHT = self.upButton.GetHeight()
		self.MIDDLE_BAR_POS = 0
		self.MIDDLE_BAR_UPPER_PLACE = 0
		self.MIDDLE_BAR_DOWNER_PLACE = 0
		self.TEMP_SPACE = 0

	def UpdateBarSlot(self):
		pass

class SmallThinScrollBar(ScrollBar):

	def CreateScrollBar(self):
		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.SetUpVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/thumb_01.tga")
		middleBar.SetOverVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/thumb_02.tga")
		middleBar.SetDownVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/thumb_03.tga")

		upButton = Button()
		upButton.SetParent(self)
		upButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/up_01.tga")
		upButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/up_02.tga")
		upButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/up_03.tga")
		upButton.SetEvent(__mem_func__(self.OnUp))
		upButton.Show()

		downButton = Button()
		downButton.SetParent(self)
		downButton.SetUpVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/down_01.tga")
		downButton.SetOverVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/down_02.tga")
		downButton.SetDownVisual("d:/ymir work/ui/public/crimson/controls/small_thin_scrollbar/down_03.tga")
		downButton.SetEvent(__mem_func__(self.OnDown))
		downButton.Show()

		self.middleBar = middleBar
		self.upButton = upButton
		self.downButton = downButton

		self.SCROLLBAR_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()
		self.SCROLLBAR_BUTTON_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_HEIGHT = self.upButton.GetHeight()
		self.MIDDLE_BAR_POS = 0
		self.MIDDLE_BAR_UPPER_PLACE = 0
		self.MIDDLE_BAR_DOWNER_PLACE = 0
		self.TEMP_SPACE = 0

	def UpdateBarSlot(self):
		pass

class ScrollBarFlat(Window):

	SCROLLBAR_WIDTH = 11
	SCROLLBAR_MIDDLE_HEIGHT = 12
	MIDDLE_BAR_POS = 3
	MIDDLE_BAR_UPPER_PLACE = 0
	MIDDLE_BAR_DOWNER_PLACE = 4
	TEMP_SPACE = MIDDLE_BAR_UPPER_PLACE + MIDDLE_BAR_DOWNER_PLACE

	class MiddleBar(DragButton):
		def __init__(self):
			DragButton.__init__(self)
			self.AddFlag("movable")
			#self.AddFlag("restrict_x")

		def MakeScrollBar(self):
			self.scrollbar = Bar()
			self.scrollbar.SetParent(self)
			self.scrollbar.SetColor(0xFF6B655A)
			self.scrollbar.SetPosition(3, 3)
			self.scrollbar.SetSize(5, 10)
			self.scrollbar.AddFlag("not_pick")
			self.scrollbar.Show()

		def SetSize(self, height):
			height = max(12, height)
			self.scrollbar.SetSize(5, height)
			DragButton.SetSize(self, 8, height)

			#height -= 4*3
			#self.middle.SetRenderingRect(0, 0, 0, float(height)/4.0)

	def __init__(self):
		Window.__init__(self)

		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = lambda *arg: None
		self.lockFlag = False
		self.scrollStep1 = 0.20
		self.scrollStep2 = 0.10

		self.CreateScrollBar()

	def __del__(self):
		Window.__del__(self)

	def CreateScrollBar(self):
		self.barSlotOutline = Bar()
		self.barSlotOutline.SetParent(self)
		self.barSlotOutline.SetSize(11, 50)
		self.barSlotOutline.SetPosition(0, 0)
		self.barSlotOutline.SetColor(0xFF000000)
		self.barSlotOutline.AddFlag("not_pick")
		self.barSlotOutline.Show()
		
		self.barSlotEdge = Bar()
		self.barSlotEdge.SetParent(self.barSlotOutline)
		self.barSlotEdge.SetSize(9, 48)
		self.barSlotEdge.SetPosition(1, 1)
		self.barSlotEdge.SetColor(0xFF6B655A)
		self.barSlotEdge.AddFlag("not_pick")
		self.barSlotEdge.Show()
		
		self.barSlotMiddle = Bar()
		self.barSlotMiddle.SetParent(self.barSlotOutline)
		self.barSlotMiddle.SetSize(7, 46)
		self.barSlotMiddle.SetPosition(2, 2)
		self.barSlotMiddle.SetColor(0xFF0C0C0C)
		self.barSlotMiddle.AddFlag("not_pick")
		self.barSlotMiddle.Show()
		
		self.middleBar = self.MiddleBar()
		self.middleBar.SetParent(self)
		self.middleBar.SetMoveEvent(__mem_func__(self.OnMove))
		self.middleBar.MakeScrollBar()
		self.middleBar.SetSize(12)
		self.middleBar.Show()

		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()

	def Destroy(self):
		self.middleBar = None
		#self.upButton = None
		#self.downButton = None
		self.eventScroll = lambda *arg: None

	def SetScrollEvent(self, event):
		self.eventScroll = event

	def SetMiddleBarSize(self, pageScale):
		realHeight = self.GetHeight()
		self.SCROLLBAR_MIDDLE_HEIGHT = int(pageScale * float(realHeight))
		self.middleBar.SetSize(self.SCROLLBAR_MIDDLE_HEIGHT)
		self.pageSize = self.GetHeight() - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)

	def SetScrollBarSize(self, height):
		self.pageSize = height - self.SCROLLBAR_MIDDLE_HEIGHT - self.TEMP_SPACE
		self.SetSize(11, height)
		self.middleBar.SetRestrictMovementArea(self.MIDDLE_BAR_POS, self.MIDDLE_BAR_UPPER_PLACE, self.MIDDLE_BAR_POS, height - self.TEMP_SPACE)
		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, 0)

		self.UpdateBarSlot()

	def UpdateBarSlot(self):
		self.barSlotOutline.SetSize(11, self.GetHeight() + 1)
		self.barSlotEdge.SetSize(9, self.barSlotOutline.GetHeight() - 2 + 1)
		self.barSlotMiddle.SetSize(7, self.barSlotOutline.GetHeight() - 4 + 1)

	def GetPos(self):
		return self.curPos

	def SetPos(self, pos):
		pos = max(0.0, pos)
		pos = min(1.0, pos)

		newPos = float(self.pageSize) * pos
		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, int(newPos) + self.MIDDLE_BAR_UPPER_PLACE)
		self.OnMove()

	def SetScrollStep(self, step):
		self.scrollStep1 = step
	
	def GetScrollStep(self):
		return self.scrollStep1
		
	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep1)

	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep1)

	def OnUp2(self):
		self.SetPos(self.curPos-self.scrollStep2)

	def OnDown2(self):
		self.SetPos(self.curPos+self.scrollStep2)
		
	def OnMove(self):
		if self.lockFlag:
			return

		if 0 == self.pageSize:
			return

		(xLocal, yLocal) = self.middleBar.GetLocalPosition()
		self.curPos = float(yLocal - self.MIDDLE_BAR_UPPER_PLACE) / float(self.pageSize)

		self.eventScroll()

	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		#pickedPos = yMouseLocalPosition
		pickedPos = yMouseLocalPosition
		newPos = float(pickedPos) / float(self.pageSize)
		self.SetPos(newPos)

	def LockScroll(self):
		self.lockFlag = True

	def UnlockScroll(self):
		self.lockFlag = False


class SliderBar(Window):

	def __init__(self):
		Window.__init__(self)

		self.curPos = 1.0
		self.pageSize = 1.0
		self.eventChange = None

		self.__CreateBackGroundImage()
		self.__CreateCursor()

	def __del__(self):
		Window.__del__(self)

	def __CreateBackGroundImage(self):
		if app.ENABLE_NEW_GAMEOPTION:
			img = ExpandedImageBox()
		else:
			img = ImageBox()
		img.SetParent(self)
		img.LoadImage("d:/ymir work/ui/public/crimson/controls/slider/track.tga")
		img.Show()
		self.backGroundImage = img

		##
		self.SetSize(self.backGroundImage.GetWidth(), self.backGroundImage.GetHeight())

	def __CreateCursor(self):
		cursor = DragButton()
		cursor.AddFlag("movable")
		cursor.AddFlag("restrict_y")
		cursor.SetParent(self)
		cursor.SetMoveEvent(__mem_func__(self.__OnMove))
		cursor.SetUpVisual("d:/ymir work/ui/public/crimson/controls/slider/thumb_01.tga")
		cursor.SetOverVisual("d:/ymir work/ui/public/crimson/controls/slider/thumb_02.tga")
		cursor.SetDownVisual("d:/ymir work/ui/public/crimson/controls/slider/thumb_03.tga")
		cursor.Show()
		self.cursor = cursor

		##
		self.cursor.SetRestrictMovementArea(0, 0, self.backGroundImage.GetWidth(), 0)
		self.pageSize = self.backGroundImage.GetWidth() - self.cursor.GetWidth()

	def __OnMove(self):
		(xLocal, yLocal) = self.cursor.GetLocalPosition()
		self.curPos = float(xLocal) / float(self.pageSize)

		if self.eventChange:
			self.eventChange()

	def SetSliderPos(self, pos):
		# A pressed native DragButton also emits OnMove from SetPosition.
		# Refreshing a slider must not recursively announce another user change.
		callbackEnabled = self.cursor.callbackEnable
		self.cursor.TurnOffCallBack()
		try:
			self.curPos = pos
			self.cursor.SetPosition(int(self.pageSize * pos), 0)
		finally:
			if callbackEnabled:
				self.cursor.TurnOnCallBack()
			else:
				self.cursor.TurnOffCallBack()

	def GetSliderPos(self):
		return self.curPos

	def SetEvent(self, event):
		self.eventChange = event

	def Enable(self):
		self.cursor.Show()

	def Disable(self):
		self.cursor.Hide()

	if app.ENABLE_FOV_OPTION:
		def SetBackgroundVisual(self, filename):
			if self.backGroundImage:
				self.backGroundImage.LoadImage(filename)

				self.SetSize(self.backGroundImage.GetWidth(), self.backGroundImage.GetHeight())
				self.pageSize = self.backGroundImage.GetWidth() - self.cursor.GetWidth()

			if self.cursor:
				self.cursor.SetRestrictMovementArea(0, 0, self.backGroundImage.GetWidth(), 0)

		def SetButtonVisual(self, path, up, over, down):
			if self.cursor:
				self.cursor.SetUpVisual(path + up)
				self.cursor.SetOverVisual(path + over)
				self.cursor.SetDownVisual(path + down)

class ListBox(Window):
	def GetSelectedItemText(self):
		return self.textDict.get(self.selectedLine, "")

	TEMPORARY_PLACE = 3

	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.overLine = -1
		self.overTempLine = -1
		self.selectedLine = -1
		self.width = 0
		self.height = 0
		self.stepSize = 17
		self.basePos = 0
		self.showLineCount = 0
		self.itemCenterAlign = True
		self.drawBorder = False
		self.itemList = []
		self.keyDict = {}
		self.textDict = {}
		self.event = lambda *arg: None
		self.doubleClickEvent = lambda * arg: None

		self.lastMousePos = (-1, -1)

		self.SetWindowName("NONAME_ListBox")

	def __del__(self):
		Window.__del__(self)

	def GetStepSize(self):
		return self.stepSize

	def SetWidth(self, width):
		self.SetSize(width, self.height)

	def SetDrawBorder(self, flag):
		self.drawBorder = flag

	def SetSize(self, width, height):
		Window.SetSize(self, width, height)
		self.width = width
		self.height = height

	def SetTextCenterAlign(self, flag):
		self.itemCenterAlign = flag

	def GetBasePos(self):
		return self.basePos

	def SetBasePos(self, pos):
		self.basePos = pos
		self._LocateItem()

	def ClearItem(self):
		self.keyDict = {}
		self.textDict = {}
		self.itemList = []
		self.overLine = -1
		self.overTempLine = -1
		self.selectedLine = -1

	def HasItem(self, number):
		for i in self.keyDict:
			if self.keyDict[i] == number:
				return True

		return False

	def EraseItem(self, number):
		for i in self.keyDict:
			if self.keyDict[i] == number:
				for j in range(number, len(self.itemList) - 1):
					self.keyDict[j] = self.keyDict[j + 1]
					self.textDict[j] = self.textDict[j + 1]

				del self.keyDict[len(self.itemList) - 1]
				del self.textDict[len(self.itemList) - 1]
				del self.itemList[i]

				maxBasePos = max(self.GetItemCount() - self.GetViewItemCount(), 0)
				if self.basePos > maxBasePos:
					self.SetBasePos(maxBasePos)
				else:
					self.LocateItem()

				return True

		return False

	if app.ENABLE_CHANNEL_LIST:
		def InsertItem(self, number, text, textColor = 0x00000000):
			self.keyDict[len(self.itemList)] = number
			self.textDict[len(self.itemList)] = text

			textLine = TextLine()
			textLine.SetParent(self)
			textLine.SetText(text)
			if textColor != 0x00000000:
				textLine.SetPackedFontColor(textColor)
			textLine.Show()

			if self.itemCenterAlign:
				textLine.SetWindowHorizontalAlignCenter()
				textLine.SetHorizontalAlignCenter()

			self.itemList.append(textLine)

			self._LocateItem()
	else:
		def InsertItem(self, number, text):
			self.keyDict[len(self.itemList)] = number
			self.textDict[len(self.itemList)] = text

			textLine = TextLine()
			textLine.SetParent(self)
			textLine.SetText(text)
			textLine.Show()

			if self.itemCenterAlign:
				textLine.SetWindowHorizontalAlignCenter()
				textLine.SetHorizontalAlignCenter()

			self.itemList.append(textLine)

			self._LocateItem()

	def ChangeItem(self, number, text):
		for key, value in self.keyDict.items():
			if value == number:
				self.textDict[key] = text

				if number < len(self.itemList):
					self.itemList[key].SetText(text)

				return

	def LocateItem(self):
		self._LocateItem()

	def _LocateItem(self):
		skipCount = self.basePos
		yPos = 0
		self.showLineCount = 0

		for textLine in self.itemList:
			textLine.Hide()

			if skipCount > 0:
				skipCount -= 1
				continue

			if localeInfo.IsARABIC():
				w, h = textLine.GetTextSize()
				textLine.SetPosition(w + 10, yPos + 3)
			else:
				textLine.SetPosition(0, yPos + 3)

			yPos += self.stepSize

			if yPos <= self.GetHeight():
				self.showLineCount += 1
				textLine.Show()

	def ArrangeItem(self):
		self.SetSize(self.width, len(self.itemList) * self.stepSize)
		self._LocateItem()

	def SetDoubleClickEvent(self, event):
		self.doubleClickEvent = event

	def GetViewItemCount(self):
		return int(self.GetHeight() // self.stepSize)

	def GetItemCount(self):
		return len(self.itemList)

	def SetEvent(self, event):
		self.event = event

	def SelectItem(self, line):
		if not (line in self.keyDict):
			return

		if line == self.selectedLine:
			return

		self.selectedLine = line
		self.event(self.keyDict.get(line, 0), self.textDict.get(line, "None"))

	def GetSelectedItem(self, defaultVal = 0):
		return self.keyDict.get(self.selectedLine, defaultVal)

	def GetSelectedLine(self):
		return self.selectedLine

	def OnMouseLeftButtonDown(self):
		if self.overLine < 0:
			return

	def ResetSelected(self):
		self.selectedLine = -1

	def OnMouseLeftButtonUp(self):
		if self.overLine >= 0:
			self.SelectItem(self.overLine+self.basePos)

	def OnMouseLeftButtonDoubleClick(self):
		if self.overLine < 0:
			return

		if self.doubleClickEvent:
			try:
				self.doubleClickEvent(self.keyDict.get(self.overLine, 0))
			except TypeError:
				self.doubleClickEvent(self.keyDict.get(self.overLine, 0), self.textDict.get(self.overLine, "None"))

	def IsOverLine(self):
		return self.overLine != -1

	def GetOverLineIdx(self):
		if self.overLine == -1:
			return self.overTempLine

		return self.overLine

	def SetOverLineIdx(self, idx):
		self.overLine = -1
		self.overTempLine = idx

	def GetOverLine(self, defaultVal = 0):
		if self.IsOverLine():
			return self.keyDict.get(self.GetOverLineIdx()+self.basePos, defaultVal)

		return defaultVal

	def OnUpdate(self):
		if self.IsIn():
			x, y = self.GetGlobalPosition()
			height = self.GetHeight()
			xMouse, yMouse = wndMgr.GetMousePosition()

			if self.lastMousePos[0] == xMouse and self.lastMousePos[1] == yMouse:
				return
			self.lastMousePos = (xMouse, yMouse)

			self.overLine = -1
			if yMouse - y < height - 1:
				self.overLine = (yMouse - y) // self.stepSize

				if self.overLine < 0:
					self.overLine = -1
				elif self.overLine >= len(self.itemList):
					self.overLine = -1
				else:
					self.overTempLine = -1

		else:
			self.overLine = -1

	def OnRender(self):
		xRender, yRender = self.GetGlobalPosition()
		yRender -= self.TEMPORARY_PLACE
		widthRender = self.width
		heightRender = self.height + self.TEMPORARY_PLACE*2

		overLine = self.GetOverLineIdx()
		if -1 != overLine:
			grp.SetColor(HALF_WHITE_COLOR)
			grp.RenderBar(xRender + 2, yRender + overLine*self.stepSize + 4, self.width - 3, self.stepSize)				

		if -1 != self.selectedLine:
			if self.selectedLine >= self.basePos:
				if self.selectedLine - self.basePos < self.showLineCount:
					grp.SetColor(SELECT_COLOR)
					grp.RenderBar(xRender + 2, yRender + (self.selectedLine-self.basePos)*self.stepSize + 4, self.width - 3, self.stepSize)

class ListBox2(ListBox):
	def __init__(self, *args, **kwargs):
		ListBox.__init__(self, *args, **kwargs)
		self.rowCount = 10
		self.barWidth = 0
		self.colCount = 0

	def SetRowCount(self, rowCount):
		self.rowCount = rowCount

	def SetSize(self, width, height):
		ListBox.SetSize(self, width, height)
		self._RefreshForm()

	def ClearItem(self):
		ListBox.ClearItem(self)
		self._RefreshForm()

	def InsertItem(self, *args, **kwargs):
		ListBox.InsertItem(self, *args, **kwargs)
		self._RefreshForm()

	def OnUpdate(self):
		mpos = wndMgr.GetMousePosition()
		self.overLine = self._CalcPointIndex(mpos)

	def OnRender(self):
		x, y = self.GetGlobalPosition()
		pos = (x + 2, y)

		if -1 != self.overLine:
			grp.SetColor(HALF_WHITE_COLOR)
			self._RenderBar(pos, self.overLine)

		if -1 != self.selectedLine:
			if self.selectedLine >= self.basePos:
				if self.selectedLine - self.basePos < self.showLineCount:
					grp.SetColor(SELECT_COLOR)
					self._RenderBar(pos, self.selectedLine-self.basePos)

	def _CalcPointIndex(self, mpos):
		if self.IsIn():
			px, py = mpos
			gx, gy = self.GetGlobalPosition()
			lx, ly = px - gx, py - gy

			col = lx // self.barWidth
			row = ly // self.stepSize
			idx = col * self.rowCount + row
			if col >= 0 and col < self.colCount:
				if row >= 0 and row < self.rowCount:
					if idx >= 0 and idx < len(self.itemList):
						return idx

		return -1

	def _CalcRenderPos(self, pos, idx):
		x, y = pos
		row = idx % self.rowCount
		col = idx // self.rowCount
		return (x + col * self.barWidth, y + row * self.stepSize)

	def _RenderBar(self, basePos, idx):
		x, y = self._CalcRenderPos(basePos, idx)
		grp.RenderBar(x, y, self.barWidth - 3, self.stepSize)

	def _LocateItem(self):
		pos = (0, self.TEMPORARY_PLACE)

		self.showLineCount = 0
		for textLine in self.itemList:
			x, y = self._CalcRenderPos(pos, self.showLineCount)
			textLine.SetPosition(x, y)
			textLine.Show()

			self.showLineCount += 1

	def _RefreshForm(self):
		if len(self.itemList) % self.rowCount:
			self.colCount = len(self.itemList) // self.rowCount + 1
		else:
			self.colCount = len(self.itemList) // self.rowCount

		if self.colCount:
			self.barWidth = self.width // self.colCount
		else:
			self.barWidth = self.width

class ComboBoxImage(Window):
	class ListBoxWithBoard(ListBox):
		def __init__(self, layer):
			ListBox.__init__(self, layer)

		def OnRender(self):
			xRender, yRender = self.GetGlobalPosition()
			yRender -= self.TEMPORARY_PLACE
			widthRender = self.width
			heightRender = self.height + self.TEMPORARY_PLACE*2
			grp.SetColor(BACKGROUND_COLOR)
			grp.RenderBar(xRender, yRender, widthRender, heightRender)
			grp.SetColor(DARK_COLOR)
			grp.RenderLine(xRender, yRender, widthRender, 0)
			grp.RenderLine(xRender, yRender, 0, heightRender)
			ListBox.OnRender(self)

	def __init__(self, parent, name, x ,y):
		Window.__init__(self)
		self.isSelected = False
		self.isOver = False
		self.isListOpened = False
		self.event = lambda *arg: None
		self.enable = True
		self.imagebox = None

		## imagebox
		image = ImageBox()
		image.SetParent(parent)
		image.LoadImage(name)
		image.SetPosition(x, y)
		image.Show()
		self.imagebox = image

		## BaseSetting
		self.x = x + 1
		self.y = y + 1
		self.width = self.imagebox.GetWidth() - 3
		self.height = self.imagebox.GetHeight() - 3
		self.SetParent(parent)

		## TextLine
		self.textLine = MakeTextLine(self)
		self.textLine.SetText(localeInfo.UI_ITEM)

		## ListBox
		self.listBox = self.ListBoxWithBoard("TOP_MOST")
		self.listBox.SetPickAlways()
		self.listBox.SetParent(self)
		self.listBox.SetEvent(__mem_func__(self.OnSelectItem))
		self.listBox.Hide()

		Window.SetPosition(self, self.x, self.y)
		Window.SetSize(self, self.width, self.height)
		self.textLine.UpdateRect()
		self.__ArrangeListBox()

	def __del__(self):
		Window.__del__(self)

	def Destroy(self):
		self.textLine = None
		self.listBox = None
		self.imagebox = None

	def SetPosition(self, x, y):
		Window.SetPosition(self, x, y)
		self.imagebox.SetPosition(x, y)
		self.x = x
		self.y = y
		self.__ArrangeListBox()

	def SetSize(self, width, height):
		Window.SetSize(self, width, height)
		self.width = width
		self.height = height
		self.textLine.UpdateRect()
		self.__ArrangeListBox()

	def __ArrangeListBox(self):
		self.listBox.SetPosition(0, self.height + 5)
		self.listBox.SetWidth(self.width)

	def Enable(self):
		self.enable = True

	def Disable(self):
		self.enable = False
		self.textLine.SetText("")
		self.CloseListBox()

	def SetEvent(self, event):
		self.event = event

	def ClearItem(self):
		self.CloseListBox()
		self.listBox.ClearItem()

	def InsertItem(self, index, name):
		self.listBox.InsertItem(index, name)
		self.listBox.ArrangeItem()

	def SetCurrentItem(self, text):
		self.textLine.SetText(text)

	def SelectItem(self, key):
		self.listBox.SelectItem(key)

	def OnSelectItem(self, index, name):
		self.CloseListBox()
		self.event(index)

	def CloseListBox(self):
		self.isListOpened = False
		self.listBox.Hide()

	def OnMouseLeftButtonDown(self):
		if not self.enable:
			return

		self.isSelected = True

	def OnMouseLeftButtonUp(self):
		if not self.enable:
			return

		self.isSelected = False

		if self.isListOpened:
			self.CloseListBox()
		else:
			if self.listBox.GetItemCount() > 0:
				self.isListOpened = True
				self.listBox.Show()
				self.__ArrangeListBox()

	def OnUpdate(self):
		if not self.enable:
			return

		if self.IsIn():
			self.isOver = True
		else:
			self.isOver = False

	def OnRender(self):
		self.x, self.y = self.GetGlobalPosition()
		xRender = self.x
		yRender = self.y
		widthRender = self.width
		heightRender = self.height
		if self.isOver:
			grp.SetColor(HALF_WHITE_COLOR)
			grp.RenderBar(xRender + 2, yRender + 3, self.width - 3, heightRender - 5)
			if self.isSelected:
				grp.SetColor(WHITE_COLOR)
				grp.RenderBar(xRender + 2, yRender + 3, self.width - 3, heightRender - 5)

class ComboBox(Window):

	class ListBoxWithBoard(ListBox):

		def __init__(self, layer):
			ListBox.__init__(self, layer)

		def OnRender(self):
			xRender, yRender = self.GetGlobalPosition()
			yRender -= self.TEMPORARY_PLACE
			widthRender = self.width
			heightRender = self.height + self.TEMPORARY_PLACE*2
			grp.SetColor(BACKGROUND_COLOR)
			grp.RenderBar(xRender, yRender, widthRender, heightRender)
			grp.SetColor(DARK_COLOR)
			grp.RenderLine(xRender, yRender, widthRender, 0)
			grp.RenderLine(xRender, yRender, 0, heightRender)
			grp.SetColor(BRIGHT_COLOR)
			grp.RenderLine(xRender, yRender+heightRender, widthRender, 0)
			grp.RenderLine(xRender+widthRender, yRender, 0, heightRender)

			ListBox.OnRender(self)

	def __init__(self):
		Window.__init__(self)
		self.x = 0
		self.y = 0
		self.width = 0
		self.height = 0
		self.isSelected = False
		self.isOver = False
		self.isListOpened = False
		self.event = lambda *arg: None
		self.enable = True

		self.textLine = MakeTextLine(self)
		self.textLine.SetText(localeInfo.UI_ITEM)

		self.listBox = self.ListBoxWithBoard("TOP_MOST")
		self.listBox.SetPickAlways()
		self.listBox.SetParent(self)
		self.listBox.SetEvent(__mem_func__(self.OnSelectItem))
		self.listBox.Hide()

	def __del__(self):
		Window.__del__(self)

	def Destroy(self):
		self.textLine = None
		self.listBox = None

	def SetPosition(self, x, y):
		Window.SetPosition(self, x, y)
		self.x = x
		self.y = y
		self.__ArrangeListBox()

	def SetSize(self, width, height):
		Window.SetSize(self, width, height)
		self.width = width
		self.height = height
		self.textLine.UpdateRect()
		self.__ArrangeListBox()

	def __ArrangeListBox(self):
		self.listBox.SetPosition(0, self.height + 5)
		self.listBox.SetWidth(self.width)

	def Enable(self):
		self.enable = True

	def Disable(self):
		self.enable = False
		self.textLine.SetText("")
		self.CloseListBox()

	def SetEvent(self, event):
		self.event = event

	def ClearItem(self):
		self.CloseListBox()
		self.listBox.ClearItem()

	def InsertItem(self, index, name):
		self.listBox.InsertItem(index, name)
		self.listBox.ArrangeItem()

	def SetCurrentItem(self, text):
		self.textLine.SetText(text)

	def SelectItem(self, key):
		self.listBox.SelectItem(key)

	def OnSelectItem(self, index, name):

		self.CloseListBox()
		self.event(index)

	def CloseListBox(self):
		self.isListOpened = False
		self.listBox.Hide()

	def OnMouseLeftButtonDown(self):
		if not self.enable:
			return

		self.isSelected = True

	def OnMouseLeftButtonUp(self):
		if not self.enable:
			return

		self.isSelected = False

		if self.isListOpened:
			self.CloseListBox()
		else:
			if self.listBox.GetItemCount() > 0:
				self.isListOpened = True
				self.listBox.Show()
				self.__ArrangeListBox()

	def OnUpdate(self):
		if not self.enable:
			return

		if self.IsIn():
			self.isOver = True
		else:
			self.isOver = False

	def OnRender(self):
		self.x, self.y = self.GetGlobalPosition()
		xRender = self.x
		yRender = self.y
		widthRender = self.width
		heightRender = self.height
		grp.SetColor(BACKGROUND_COLOR)
		grp.RenderBar(xRender, yRender, widthRender, heightRender)
		grp.SetColor(DARK_COLOR)
		grp.RenderLine(xRender, yRender, widthRender, 0)
		grp.RenderLine(xRender, yRender, 0, heightRender)
		grp.SetColor(BRIGHT_COLOR)
		grp.RenderLine(xRender, yRender+heightRender, widthRender, 0)
		grp.RenderLine(xRender+widthRender, yRender, 0, heightRender)

		if self.isOver:
			grp.SetColor(HALF_WHITE_COLOR)
			grp.RenderBar(xRender + 2, yRender + 3, self.width - 3, heightRender - 5)

			if self.isSelected:
				grp.SetColor(WHITE_COLOR)
				grp.RenderBar(xRender + 2, yRender + 3, self.width - 3, heightRender - 5)

class BoxedBoard(Window):
	BORDER_TOP = 0
	BORDER_RIGHT = 1
	BORDER_BOTTOM = 2
	BORDER_LEFT = 3

	DEFAULT_BORDER_COLOR = grp.GenerateColor(0.3, 0.3, 0.3, 0.8)
	DEFAULT_BASE_COLOR = grp.GenerateColor(0, 0, 0, 0.5)

	def __init__(self):
		Window.__init__(self)

		self.borderSize = 1

		# Create Borders
		self.borders = [
			Bar(),
			Bar(),
			Bar(),
			Bar()
		]

		for border in self.borders:
			border.SetParent(self)
			border.AddFlag("not_pick")
			border.Show()

		# Create Base
		self.base = Bar()
		self.base.SetParent(self)
		self.base.AddFlag("not_pick")
		self.base.Show()

		# Set Default Colors
		self.SetBorderColor(self.DEFAULT_BORDER_COLOR)
		self.SetBaseColor(self.DEFAULT_BASE_COLOR)

	def __del__(self):
		self.Destroy()
		Window.__del__(self)

	def Destroy(self):
		del self.borders[:]
		self.base = None

		Window.Destroy(self)

	def SetBorderColor(self, color):
		for border in self.borders:
			border.SetColor(color)

	def SetBorderSize(self, borderSize):
		self.borderSize = borderSize
		self.SetSize(self.GetWidth(), self.GetHeight())

	def SetBaseColor(self, color):
		self.base.SetColor(color)

	def SetSize(self, width, height):
		width = max(width, (2 * self.borderSize) + 1)
		height = max(height, (2 * self.borderSize) + 1)

		Window.SetSize(self, width, height)
		self.UpdateBoard()

	def UpdateBoard(self):
		width = self.GetWidth()
		height = self.GetHeight()

		top, right, bottom, left = self.borders

		# Top Border
		top.SetSize(width - self.borderSize, self.borderSize)

		# Right Border
		right.SetSize(self.borderSize, height - self.borderSize)
		right.SetPosition(width - self.borderSize, 0)

		# Bottom Border
		bottom.SetSize(width - self.borderSize, self.borderSize)
		bottom.SetPosition(self.borderSize, height - self.borderSize)

		# Left Border
		left.SetSize(self.borderSize, height - self.borderSize)
		left.SetPosition(0, self.borderSize)

		# Base
		self.base.SetSize(width - (2 * self.borderSize), height - (2 * self.borderSize))
		self.base.SetPosition(self.borderSize, self.borderSize)

if app.ENABLE_BATTLE_PASS:
	class ExpandedImageBoxButton(ImageBox):
		def __init__(self, layer = "UI"):
			ImageBox.__init__(self, layer)
			self.ButtonText = None
			self.fontName = fontconfig.FontForRole(fontconfig.ROLE_CONTROL)

			self.eventDict={}
			self.eventFunc = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
			self.eventArgs = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}

		def __del__(self):
			ImageBox.__del__(self)
			self.eventDict={}
			self.eventFunc = 0
			self.eventArgs = 0

		def RegisterWindow(self, layer):
			self.hWnd = wndMgr.RegisterExpandedImageBox(self, layer)

		def SetScale(self, xScale, yScale):
			wndMgr.SetScale(self.hWnd, xScale, yScale)

		def SetOrigin(self, x, y):
			wndMgr.SetOrigin(self.hWnd, x, y)

		def SetRotation(self, rotation):
			wndMgr.SetRotation(self.hWnd, rotation)

		def SetRenderingMode(self, mode):
			wndMgr.SetRenderingMode(self.hWnd, mode)

		def SetRenderingRect(self, left, top, right, bottom):
			wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

		def SetClipRect(self, left, top, right, bottom, isVertical = False):
			wndMgr.SetClipRect(self.hWnd, left, top, right, bottom, isVertical)

		def SetPercentage(self, curValue, maxValue):
			if maxValue:
				self.SetRenderingRect(0.0, 0.0, -1.0 + float(curValue) / float(maxValue), 0.0)
			else:
				self.SetRenderingRect(0.0, 0.0, 0.0, 0.0)

		def GetWidth(self):
			return wndMgr.GetWindowWidth(self.hWnd)

		def GetHeight(self):
			return wndMgr.GetWindowHeight(self.hWnd)

		def SetEvent(self, func, event="MOUSE_CLICK", *args):
			self.eventFunc[event] = func
			self.eventArgs[event] = args

		def SetUpVisual(self, path):
			self.normal_visual = path
			self.LoadImage(self.normal_visual)

		def SetOverVisual(self, path):
			self.over_visual = path

		def SetDownVisual(self, path):
			self.down_visual = path

		def SetFontName(self, fontName):
			self.fontName = fontName
			if self.ButtonText:
				self.ButtonText.SetFontName(fontName)

		def SetText(self, text, height = 4):
			if not self.ButtonText:
				textLine = TextLine()
				textLine.SetFontName(self.fontName)
				textLine.SetParent(self)
				textLine.SetPosition(self.GetWidth()//2, self.GetHeight()//2)
				textLine.SetVerticalAlignCenter()
				textLine.SetHorizontalAlignCenter()
				textLine.Show()
				self.ButtonText = textLine

			self.ButtonText.SetText(text)

		def OnMouseLeftButtonDown(self):
			self.LoadImage(self.down_visual)

			try:
				if self.eventDict.__contains__("MOUSE_LEFT_DOWN"):
					self.eventDict["MOUSE_LEFT_DOWN"](* self.argDict["MOUSE_LEFT_DOWN"])
			except Exception:
				pass

		def OnMouseLeftButtonUp(self) :
			self.LoadImage(self.normal_visual)

			try:
				if self.eventFunc["MOUSE_CLICK"]:
					self.eventFunc["MOUSE_CLICK"](*self.eventArgs["MOUSE_CLICK"])
				Window.OnMouseLeftButtonUp(self)
			except Exception:
				pass

		def OnMouseOverIn(self):
			self.LoadImage(self.over_visual)

			try:
				if self.eventFunc["MOUSE_OVER_IN"]:
					self.eventFunc["MOUSE_OVER_IN"](*self.eventArgs["MOUSE_OVER_IN"])

				if ("MOUSE_OVER_IN" in self.eventDict):
					if self.eventArgs["MOUSE_OVER_IN"]:
						self.eventDict["MOUSE_OVER_IN"](*self.eventArgs["MOUSE_OVER_IN"])
					else:
						self.eventDict["MOUSE_OVER_IN"]()
			except Exception:
				pass

		def OnMouseOverOut(self):
			self.LoadImage(self.normal_visual)

			try:
				if self.eventFunc["MOUSE_OVER_OUT"]:
					self.eventFunc["MOUSE_OVER_OUT"](*self.eventArgs["MOUSE_OVER_OUT"])

				if ("MOUSE_OVER_OUT" in self.eventDict):
					if self.eventArgs["MOUSE_OVER_OUT"]:
						self.eventDict["MOUSE_OVER_OUT"](*self.eventArgs["MOUSE_OVER_OUT"])
					else:
						self.eventDict["MOUSE_OVER_OUT"]()
			except Exception:
				pass

class DragonBoard(Window):

	CORNER_WIDTH = 32
	CORNER_HEIGHT = 32
	LINE_WIDTH = 128
	LINE_HEIGHT = 128

	BASE_WIDTH = 777
	BASE_HEIGHT = 486

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self):
		Window.__init__(self)
		self.MakeBoard("d:/ymir work/ui/pattern/dragonboard/dragonboard_corner_", "d:/ymir work/ui/pattern/dragonboard/dragonboard_line_")
		self.MakeBase()

	def __del__(self):
		Window.__del__(self)

	def MakeBoard(self, cornerPath, linePath):
		CornerFileNames = [ cornerPath+dir+".tga" for dir in ("LeftTop", "LeftBottom", "RightTop", "RightBottom", ) ]
		LineFileNames = [ linePath+dir+".tga" for dir in ("Left", "Right", "Top", "Bottom", ) ]

		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ExpandedImageBox()
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)

		self.Lines = []
		for fileName in LineFileNames:
			Line = ExpandedImageBox()
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)

		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)

	def MakeBase(self):
		self.Base = ExpandedImageBox()
		self.Base.AddFlag("not_pick")
		self.Base.LoadImage("d:/ymir work/ui/pattern/dragonboard/dragonboard_base.tga")
		self.Base.SetParent(self)
		self.Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Base.Show()

	def HideLine(self, line):
		self.Lines[line].Hide()
		self.SetSize(self.GetWidth(), self.GetHeight())

	def SetSize(self, width, height):

		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		Window.SetSize(self, width, height)

		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)

		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.BASE_HEIGHT) / self.BASE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.BASE_WIDTH) / self.BASE_WIDTH

		self.Base.SetRenderingRect(0, 0, horizontalShowingPercentage, verticalShowingPercentage)

class DragonBoardWithTitleBar(DragonBoard):
	def __init__(self):
		DragonBoard.__init__(self)

		titleBar = TitleBar()
		titleBar.SetParent(self)
		titleBar.MakeTitleBar(0, "red")
		titleBar.SetPosition(-4, 0)
		titleBar.Show()

		titleName = TextLine()
		titleName.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_WINDOW_TITLE))
		titleName.SetParent(titleBar)
		titleName.SetPosition(0, 4)
		titleName.SetWindowHorizontalAlignCenter()
		titleName.SetHorizontalAlignCenter()
		titleName.Show()

		self.titleBar = titleBar
		self.titleName = titleName

		self.SetCloseEvent(self.Hide)

	def __del__(self):
		DragonBoard.__del__(self)
		self.titleBar = None
		self.titleName = None

	def SetSize(self, width, height):
		self.titleBar.SetWidth(width + 8)
		#self.pickRestrictWindow.SetSize(width, height - 30)
		DragonBoard.SetSize(self, width, height)
		self.titleName.UpdateRect()

	def SetTitleColor(self, color):
		self.titleName.SetPackedFontColor(color)

	def SetTitleName(self, name):
		self.titleName.SetText(name)

	def SetCloseEvent(self, event):
		self.titleBar.SetCloseEvent(event)

class ImageBoxSaveItem(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		self.eventDict={}	
		self.eventFunc = {
			"MOUSE_LEFT_BUTTON_UP" : None, 
			"MOUSE_LEFT_BUTTON_DOWN" : None, 
			"MOUSE_RIGHT_BUTTON_UP" : None, 
			"MOUSE_RIGHT_BUTTON_DOWN" : None, 
			"MOUSE_OVER_IN" : None, 
			"MOUSE_OVER_OUT" : None
		}
		self.eventArgs = {
			"MOUSE_LEFT_BUTTON_UP" : None, 
			"MOUSE_LEFT_BUTTON_DOWN" : None, 
			"MOUSE_RIGHT_BUTTON_UP" : None, 
			"MOUSE_RIGHT_BUTTON_DOWN" : None, 
			"MOUSE_OVER_IN" : None, 
			"MOUSE_OVER_OUT" : None
		}

	def __del__(self):
		Window.__del__(self)	
		self.eventFunc = None
		self.eventArgs = None

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterImageBox(self, layer)

	def LoadImage(self, imageName):
		self.name=imageName
		wndMgr.LoadImage(self.hWnd, imageName)

	def UnloadImage(self):
		wndMgr.UnloadImage(self.hWnd)

	def SetAlpha(self, alpha):
		wndMgr.SetDiffuseColor(self.hWnd, 1.0, 1.0, 1.0, alpha)
		
	def SetColor(self, r, g, b, a):
		wndMgr.SetDiffuseColor(self.hWnd, r, g, b, a)

	def SetImageSize(self,w,h):
		wndMgr.SetImageSize(self.hWnd,w,h)

	def GetWidth(self):
		return wndMgr.GetWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetHeight(self.hWnd)

	def SetEvent(self, func, *args) :
		result = (args[0] in self.eventFunc)		
		if result :
			self.eventFunc[args[0]] = func
			self.eventArgs[args[0]] = args
		else :
			print("[ERROR] ui.py SetEvent, Can`t Find has_key : %s" % args[0])
			
	def SAFE_SetEvent(self, func, *args):
		result = (args[0] in self.eventFunc)		
		if result :
			self.eventFunc[args[0]] = __mem_func__(func)
			self.eventArgs[args[0]] = args
		else :
			print("[ERROR] ui.py SAFE_SetEvent, Can`t Find has_key : %s" % args[0])

	def OnMouseLeftButtonUp(self):
		if self.eventFunc["MOUSE_LEFT_BUTTON_UP"] :
			self.eventFunc["MOUSE_LEFT_BUTTON_UP"](*self.eventArgs["MOUSE_LEFT_BUTTON_UP"])
			
	def OnMouseLeftButtonDown(self):
		if self.eventFunc["MOUSE_LEFT_BUTTON_DOWN"] :
			self.eventFunc["MOUSE_LEFT_BUTTON_DOWN"](*self.eventArgs["MOUSE_LEFT_BUTTON_DOWN"])

	def OnMouseRightButtonUp(self):
		if self.eventFunc["MOUSE_RIGHT_BUTTON_UP"] :
			self.eventFunc["MOUSE_RIGHT_BUTTON_UP"](*self.eventArgs["MOUSE_RIGHT_BUTTON_UP"])
			
	def OnMouseRightButtonDown(self):
		if self.eventFunc["MOUSE_RIGHT_BUTTON_DOWN"] :
			self.eventFunc["MOUSE_RIGHT_BUTTON_DOWN"](*self.eventArgs["MOUSE_RIGHT_BUTTON_DOWN"])
			
	def OnMouseOverIn(self) :
		if self.eventFunc["MOUSE_OVER_IN"] :
			self.eventFunc["MOUSE_OVER_IN"](*self.eventArgs["MOUSE_OVER_IN"])

	def OnMouseOverOut(self) :
		if self.eventFunc["MOUSE_OVER_OUT"] :
			self.eventFunc["MOUSE_OVER_OUT"](*self.eventArgs["MOUSE_OVER_OUT"])
			
	def SAFE_SetStringEvent(self, event, func,isa=FALSE):
		if not isa:
			self.eventDict[event]=__mem_func__(func)
		else:
			self.eventDict[event]=func

	def SetCoolTime(self, time):
		wndMgr.SetCoolTimeImageBox(self.hWnd, time)

	def SetStartCoolTime(self, time):
		wndMgr.SetStartCoolTimeImageBox(self.hWnd, time)


class ExpandedImageBoxSaveItem(ImageBoxSaveItem):
	def __init__(self, layer = "UI"):
		ImageBoxSaveItem.__init__(self, layer)
		self.xScaleImage = 0
		self.yScaleImage = 0

	def __del__(self):
		ImageBoxSaveItem.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterExpandedImageBox(self, layer)

	def SetScale(self, xScale, yScale, IsTemporary = False):
		if not IsTemporary:
			self.xScaleImage = xScale
			self.yScaleImage = yScale
	
		wndMgr.SetScale(self.hWnd, xScale, yScale)

	def SetOrigin(self, x, y):
		wndMgr.SetOrigin(self.hWnd, x, y)

	def SetRotation(self, rotation):
		wndMgr.SetRotation(self.hWnd, rotation)

	def SetRenderingMode(self, mode):
		wndMgr.SetRenderingMode(self.hWnd, mode)

	def SetRenderingRect(self, left, top, right, bottom):
		wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

	# if app.ENABLE_IMAGE_CLIP_RECT:
	def SetClipRect(self, left, top, right, bottom, isVertical = False):
		wndMgr.SetClipRect(self.hWnd, left, top, right, bottom, isVertical)

	def SetPercentage(self, curValue, maxValue):
		if maxValue:
			self.SetRenderingRect(0.0, 0.0, -1.0 + float(curValue) / float(maxValue), 0.0)
		else:
			self.SetRenderingRect(0.0, 0.0, 0.0, 0.0)

	def GetWidth(self):
		return wndMgr.GetWindowWidth(self.hWnd)

	def GetHeight(self):
		return wndMgr.GetWindowHeight(self.hWnd)

class InputField(Window):

	PATH = "d:/ymir work/ui/pattern/input_%s.tga"

	BORDER_SIZE = 1
	BASE_SIZE = 1

	L = 0
	R = 1
	T = 2
	B = 3

	def __init__(self, basePath = PATH):
		Window.__init__(self)

		self.isButtonStyle = False
		self.isButtonStyleOverOnly = False
		self.isDown = False
		self.renderData = {}

		self.onClickEvent = None
		self.onClickArgs = None

		self.MakeField(basePath)
		self.SetSize(0, 0)

		self.SetWindowName("NONAME_InputField")

	def __del__(self):
		Window.__del__(self)

	def MakeField(self, basePath):
		self.Lines = []
		for i in range(4):
			line = ExpandedImageBox()
			line.AddFlag("attach")
			line.AddFlag("not_pick")
			line.SetParent(self)
			line.LoadImage(basePath % "border")
			line.Show()
			self.Lines.append(line)

		self.Lines[self.T].SetPosition(self.BORDER_SIZE, 0)
		self.Lines[self.B].SetPosition(self.BORDER_SIZE, 0)

		self.Base = ExpandedImageBox()
		self.Base.AddFlag("attach")
		self.Base.AddFlag("not_pick")
		self.Base.SetParent(self)
		self.Base.SetPosition(self.BORDER_SIZE, self.BORDER_SIZE)
		self.Base.LoadImage(basePath % "base")
		self.Base.Show()

	def SetSize(self, width, height):
		minSize = self.BORDER_SIZE * 2 + self.BASE_SIZE
		width = max(minSize, width)
		height = max(minSize, height)
		Window.SetSize(self, width, height)

		scaleH = float(width - self.BORDER_SIZE * 2 - self.BORDER_SIZE) / float(self.BORDER_SIZE)
		scaleV = float(height - self.BORDER_SIZE) / float(self.BORDER_SIZE)
		self.Lines[self.L].SetRenderingRect(0, 0, 0, scaleV)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, scaleV)
		self.Lines[self.T].SetRenderingRect(0, 0, scaleH, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, scaleH, 0)
		self.Lines[self.R].SetPosition(width - self.BORDER_SIZE, self.Lines[self.R].GetTop())
		self.Lines[self.B].SetPosition(self.Lines[self.B].GetLeft(), height - self.BORDER_SIZE)

		scaleH = float(width - self.BORDER_SIZE * 2 - self.BASE_SIZE) / float(self.BASE_SIZE)
		scaleV = float(height - self.BORDER_SIZE * 2 - self.BASE_SIZE) / float(self.BASE_SIZE)
		self.Base.SetRenderingRect(0, 0, scaleH, scaleV)

	def SetAlpha(self, alpha):
		for line in self.Lines:
			line.SetAlpha(alpha)
		self.Base.SetAlpha(alpha)

	def SetEvent(self, event, *args):
		self.onClickEvent = event
		self.onClickArgs = args

	def ClearEvent(self):
		self.onClickEvent = None

	def SetButtonStyle(self, isButtonStyle):
		self.isButtonStyle = isButtonStyle

		if self.isButtonStyle == False and (self.isButtonStyleOverOnly == False or not self.IsIn()):
			self.__ResetRenderData()

	def SetButtonStyleOverOnly(self, isButtonStyleOverOnly):
		self.isButtonStyleOverOnly = isButtonStyleOverOnly

		if self.isButtonStyleOverOnly == False:
			if self.isButtonStyle == False:
				self.__ResetRenderData()

	def __ResetRenderData(self):
		self.renderData = {"render" : False}

	def __SetRenderData(self, key, val):
		self.renderData["render"] = True
		self.renderData[key] = val

	def __GetRenderData(self, key):
		return self.renderData.get(key, False)

	def OnMouseOverIn(self):
		if self.isButtonStyle or self.isButtonStyleOverOnly:
			if self.isButtonStyle == False or self.isDown == False:
				self.__SetRenderData("color", HALF_WHITE_COLOR)
			elif self.isButtonStyle:
				self.__SetRenderData("color", SELECT_COLOR)

	def OnMouseOverOut(self):
		if self.isButtonStyle or self.isButtonStyleOverOnly:
			if self.isButtonStyle == False or self.isDown == False:
				self.__ResetRenderData()

	def OnMouseLeftButtonDown(self):
		Window.OnMouseLeftButtonDown(self)

		self.isDown = True
		if self.isButtonStyle:
			self.__SetRenderData("color", SELECT_COLOR)

	def OnMouseLeftButtonUp(self):
		Window.OnMouseLeftButtonUp(self)

		self.isDown = False
		self.__ResetRenderData()

		if self.IsIn():
			if self.isButtonStyle or self.isButtonStyleOverOnly:
				self.__SetRenderData("color", HALF_WHITE_COLOR)
			if self.onClickEvent:
				self.onClickEvent(*self.onClickArgs)


class CheckBox_N(Window):

	STATE_UNSELECTED = 0
	STATE_SELECTED = 1

	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		self.state = self.STATE_UNSELECTED
		self.eventFunc = None
		self.eventArgs = None

		self.overIn = ""

		self.btnBox = {
			self.STATE_UNSELECTED : self.__init_MakeButton("d:/ymir work/ui/public/crimson/controls/checkbox/off_%s.tga"),
			self.STATE_SELECTED : self.__init_MakeButton("d:/ymir work/ui/public/crimson/controls/checkbox/on_%s.tga", "d:/ymir work/ui/public/crimson/controls/checkbox/on_03.tga"),
		}

		text = TextLine()
		text.SetParent(self)
		text.SetWindowVerticalAlignCenter()
		text.SetVerticalAlignCenter()
		text.Show()
		self.text = text

		self.__Refresh()

		self.SetWindowName("NONAME_CheckBox")

	def __del__(self):
		Window.__del__(self)

	def __ConvertPath(self, path, subStr):
		if path.find("%s") != -1:
			return path % subStr
		else:
			return path

	def __init_MakeButton(self, path, disablePath = None):
		btn = Button()
		btn.SetParent(self)
		btn.SetWindowVerticalAlignCenter()
		btn.SetUpVisual(self.__ConvertPath(path, "01"))
		btn.SetOverVisual(self.__ConvertPath(path, "02"))
		btn.SetDownVisual(self.__ConvertPath(path, "03"))
		if disablePath:
			btn.SetDisableVisual(disablePath)
		else:
			btn.SetDisableVisual(self.__ConvertPath(path, "01"))
		btn.SAFE_SetEvent(self.OnClickButton)
		btn.baseWidth = btn.GetWidth()
		return btn

	def __UpdateRect(self):
		if self.text.GetText():
			width = self.btnBox[self.state].baseWidth + 5 + self.text.GetTextWidth()
		else:
			width = self.btnBox[self.state].baseWidth
		height = max(self.btnBox[self.state].GetHeight(), self.text.GetTextHeight())
		self.SetSize(width, height)

		self.btnBox[self.state].SetSize(width, self.btnBox[self.state].GetHeight())
		self.text.SetPosition(self.btnBox[self.state].baseWidth + 5, 0)

		self.text.UpdateRect()
		self.btnBox[self.state].UpdateRect()
		self.UpdateRect()

	def __Refresh(self):
		self.__UpdateRect()

		self.btnBox[self.STATE_UNSELECTED].SetVisible(self.state == self.STATE_UNSELECTED)
		self.btnBox[self.STATE_SELECTED].SetVisible(self.state == self.STATE_SELECTED)

	def SAFE_SetOverInData(self, data):
		self.btnBox[self.state].SetToolTipText(data)

	def OnClickButton(self):
		if self.state == self.STATE_UNSELECTED:
			self.state = self.STATE_SELECTED
		else:
			self.state = self.STATE_UNSELECTED

		self.__Refresh()

		if self.eventFunc:
			self.eventFunc(*self.eventArgs)

	def SetChecked(self, state):
		self.state = state
		self.__Refresh()

	def IsChecked(self):
		return self.state != self.STATE_UNSELECTED

	def SetText(self, text):
		self.text.SetText(text)
		self.__UpdateRect()

	def SetTextColor(self, color):
		self.text.SetPackedFontColor(color)

	def SetEvent(self, event, *args):
		self.eventFunc = event
		self.eventArgs = args

	def SAFE_SetEvent(self, event, *args):
		self.eventFunc = __mem_func__(event)
		self.eventArgs = args

	def Disable(self):
		self.btnBox[self.STATE_UNSELECTED].Disable()
		self.btnBox[self.STATE_SELECTED].Disable()

	def Enable(self):
		self.btnBox[self.STATE_UNSELECTED].Enable()
		self.btnBox[self.STATE_SELECTED].Enable()

###################################################################################################
## Python Script Loader
###################################################################################################

class ScriptWindow(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.Children = []
		self.ElementDictionary = {}
	def __del__(self):
		Window.__del__(self)

	def ClearDictionary(self):
		self.Children = []
		self.ElementDictionary = {}
	def InsertChild(self, name, child):
		self.ElementDictionary[name] = child

	def IsChild(self, name):
		return (name in self.ElementDictionary)
	def GetChild(self, name):
		return self.ElementDictionary[name]

	def GetChild2(self, name):
		return self.ElementDictionary.get(name, None)

class ScrollBarTemplate(Window):

	MIDDLE_BAR_POS = 5
	MIDDLE_BAR_UPPER_PLACE = 2
	MIDDLE_BAR_DOWNER_PLACE = 2
	TEMP_SPACE = MIDDLE_BAR_UPPER_PLACE + MIDDLE_BAR_DOWNER_PLACE

	class MiddleBar(DragButton):
		def __init__(self):
			self.middle = None
			DragButton.__init__(self)
			self.AddFlag("movable")

		def MakeImage(self, img):
			middle = ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(img)
			middle.SetPosition(0, 0)
			middle.AddFlag("not_pick")
			middle.Show()
			self.middle = middle
			self.SetSize(self.GetHeight())

		def SetSize(self, height):
			height = max(12, height)
			if self.middle:
				DragButton.SetSize(self, self.middle.GetWidth(), height)
				val = 0
				if self.middle.GetHeight() != 0:
					val = float(height)/self.middle.GetHeight()
				self.middle.SetRenderingRect(0, 0, 0, -1.0 + val)
			else:
				DragButton.SetSize(self, self.GetWidth(), height)

	def __init__(self):
		Window.__init__(self)

		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = None
		self.eventArgs = None
		self.lockFlag = False

		self.SCROLLBAR_WIDTH = 0
		self.SCROLLBAR_BUTTON_WIDTH = 0
		self.SCROLLBAR_BUTTON_HEIGHT = 0
		self.SCROLLBAR_MIDDLE_HEIGHT = 0

		self.CreateScrollBar()

		self.scrollStep = 0.20

	def SetUpButton(self, upVisual, overVisual, downVisual):
		self.upButton.SetUpVisual(upVisual)
		self.upButton.SetOverVisual(overVisual)
		self.upButton.SetDownVisual(downVisual)
		self.upButton.Show()
		self.SCROLLBAR_BUTTON_WIDTH = self.upButton.GetWidth()
		self.SCROLLBAR_BUTTON_HEIGHT = self.upButton.GetHeight() + 3

	def SetDownButton(self, upVisual, overVisual, downVisual):
		self.downButton.SetUpVisual(upVisual)
		self.downButton.SetOverVisual(overVisual)
		self.downButton.SetDownVisual(downVisual)
		self.downButton.Show()

	def SetMiddleImage(self, img):
		self.middleBar.MakeImage(img)
		self.SCROLLBAR_MIDDLE_HEIGHT = self.middleBar.GetHeight()
		self.MIDDLE_BAR_POS = (self.SCROLLBAR_WIDTH - self.middleBar.GetWidth()) // 2

	def SetBarPartImages(self, topImg, centerImg, bottomImg):
		self.barTopImage.LoadImage(topImg)
		self.barTopImage.Show()
		self.barCenterImage.LoadImage(centerImg)
		self.barCenterImage.SetPosition(0, self.barTopImage.GetHeight())
		self.barCenterImage.Show()
		self.barBottomImage.LoadImage(bottomImg)
		self.barBottomImage.Show()
		self.SCROLLBAR_WIDTH = max(self.barTopImage.GetWidth(), self.SCROLLBAR_WIDTH)
		self.MIDDLE_BAR_POS = (self.SCROLLBAR_WIDTH - self.middleBar.GetWidth()) // 2

	def SetBarImage(self, img):
		self.barImage.LoadImage(img)
		self.barImage.Show()
		self.SCROLLBAR_WIDTH = max(self.barImage.GetWidth(), self.SCROLLBAR_WIDTH)
		self.MIDDLE_BAR_POS = (self.SCROLLBAR_WIDTH - self.middleBar.GetWidth()) // 2

	def CreateScrollBar(self):
		barImage = ExpandedImageBox()
		barImage.SetParent(self)
		barImage.AddFlag("not_pick")
		barImage.Hide()

		barTopImage = ImageBox()
		barTopImage.SetParent(self)
		barTopImage.AddFlag("not_pick")
		barTopImage.Hide()

		barCenterImage = ExpandedImageBox()
		barCenterImage.SetParent(self)
		barCenterImage.AddFlag("not_pick")
		barCenterImage.Hide()

		barBottomImage = ImageBox()
		barBottomImage.SetParent(self)
		barBottomImage.AddFlag("not_pick")
		barBottomImage.Hide()

		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.SetSize(150)

		upButton = Button()
		upButton.SetParent(self)
		upButton.SetEvent(__mem_func__(self.OnUp))
		upButton.SetWindowHorizontalAlignCenter()
		upButton.Hide()

		downButton = Button()
		downButton.SetParent(self)
		downButton.SetEvent(__mem_func__(self.OnDown))
		downButton.SetWindowHorizontalAlignCenter()
		downButton.Hide()

		self.upButton = upButton
		self.downButton = downButton
		self.middleBar = middleBar
		self.barImage = barImage
		self.barTopImage = barTopImage
		self.barCenterImage = barCenterImage
		self.barBottomImage = barBottomImage

	def Destroy(self):
		self.middleBar = None
		self.upButton = None
		self.downButton = None
		self.barImage = None
		self.barTopImage = None
		self.barCenterImage = None
		self.barBottomImage = None
		self.eventScroll = None
		self.eventArgs = None

	def SetScrollEvent(self, event, *args):
		self.eventScroll = event
		self.eventArgs = args

	# ------------------------------------------------------------------------------------------

	# Important: pageScale must be float! so parse the values to float before you use them.
	# Otherwise it simply won't work or the bar is gonna be very small

	# ------------------------------------------------------------------------------------------

	def SetMiddleBarSize(self, pageScale):
		realHeight = self.GetHeight() - self.SCROLLBAR_BUTTON_HEIGHT*2
		self.SCROLLBAR_MIDDLE_HEIGHT = max(12, int(pageScale * float(realHeight)))
		self.middleBar.SetSize(self.SCROLLBAR_MIDDLE_HEIGHT)
		self.pageSize = (self.GetHeight() - self.SCROLLBAR_BUTTON_HEIGHT*2) - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)

	def SetScrollBarSize(self, height):
		self.pageSize = (height - self.SCROLLBAR_BUTTON_HEIGHT*2) - self.SCROLLBAR_MIDDLE_HEIGHT - (self.TEMP_SPACE)
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.upButton.SetPosition(0, 3)
		self.downButton.SetPosition(0, height - self.SCROLLBAR_BUTTON_HEIGHT)
		self.middleBar.SetRestrictMovementArea(self.MIDDLE_BAR_POS, self.SCROLLBAR_BUTTON_HEIGHT + self.MIDDLE_BAR_UPPER_PLACE, self.middleBar.GetWidth(), height - self.SCROLLBAR_BUTTON_HEIGHT*2 - self.TEMP_SPACE)
		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, 0)

		self.UpdateBarImage()
		self.upButton.UpdateRect()
		self.downButton.UpdateRect()

	def SetScrollStep(self, step):
		self.scrollStep = step

	def GetScrollStep(self):
		return self.scrollStep

	def UpdateBarImage(self):
		if self.barImage.IsShow():
			val = 0

			if self.barImage.GetHeight() != 0:
				val = self.GetHeight() / float(self.barImage.GetHeight())

			self.barImage.SetRenderingRect(0.0, 0.0, 0.0, -1.0 + val)

		if self.barCenterImage.IsShow():
			centerHeight = self.GetHeight() - (self.barTopImage.GetHeight() + self.barBottomImage.GetHeight())

			val = 0

			if self.barCenterImage.GetHeight() != 0:
				val = (centerHeight / float(self.barCenterImage.GetHeight()))

			self.barCenterImage.SetRenderingRect(0.0, 0.0, 0.0, -1.0 + val)

		if self.barBottomImage.IsShow():
			self.barBottomImage.SetPosition(0, self.GetHeight() - self.barBottomImage.GetHeight())

	def GetPos(self):
		return self.curPos

	def OnMouseWheel(self, nLen):
		if nLen > 0:
			self.OnUp()
			return True
		elif nLen < 0:
			self.OnDown()
			return True
		return False

	def SetPos(self, pos):
		pos = max(0.0, pos)
		pos = min(1.0, pos)

		newPos = float(self.pageSize) * pos

		self.middleBar.SetPosition(self.MIDDLE_BAR_POS, int(newPos) + self.SCROLLBAR_BUTTON_HEIGHT + self.MIDDLE_BAR_UPPER_PLACE)
		self.OnMove()

	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep)

	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep)

	def OnMove(self):

		if self.lockFlag:
			return

		if 0 == self.pageSize:
			return

		(xLocal, yLocal) = self.middleBar.GetLocalPosition()

		self.curPos = float(yLocal - self.SCROLLBAR_BUTTON_HEIGHT - self.MIDDLE_BAR_UPPER_PLACE) / float(self.pageSize)

		if self.eventScroll:
			self.eventScroll(*self.eventArgs)

	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()

		pickedPos = yMouseLocalPosition - self.SCROLLBAR_BUTTON_HEIGHT - self.SCROLLBAR_MIDDLE_HEIGHT//2
		newPos = float(pickedPos) / float(self.pageSize)

		self.SetPos(newPos)

	def LockScroll(self):
		self.lockFlag = True

	def UnlockScroll(self):
		self.lockFlag = False

class PythonScriptLoader(object):

	BODY_KEY_LIST = ( "x", "y", "width", "height" )

	#####

	DEFAULT_KEY_LIST = ( "type", "x", "y", )
	WINDOW_KEY_LIST = ( "width", "height", )
	IMAGE_KEY_LIST = ( "image", )
	EXPANDED_IMAGE_KEY_LIST = ( "image", )
	ANI_IMAGE_KEY_LIST = ( "images", )
	SLOT_KEY_LIST = ( "width", "height", "slot", )
	CANDIDATE_LIST_KEY_LIST = ( "item_step", "item_xsize", "item_ysize", )
	GRID_TABLE_KEY_LIST = ( "start_index", "x_count", "y_count", "x_step", "y_step", )
	EDIT_LINE_KEY_LIST = ( "width", "height", "input_limit", )
	COMBO_BOX_KEY_LIST = ( "width", "height", "item", )
	TITLE_BAR_KEY_LIST = ( "width", )
	HORIZONTAL_BAR_KEY_LIST = ( "width", )
	BOARD_KEY_LIST = ( "width", "height", )
	BOARD_WITH_TITLEBAR_KEY_LIST = ( "width", "height", "title", )
	BOX_KEY_LIST = ( "width", "height", )
	BAR_KEY_LIST = ( "width", "height", )
	LINE_KEY_LIST = ( "width", "height", )
	SLOTBAR_KEY_LIST = ( "width", "height", )
	GAUGE_KEY_LIST = ( "width", "color", )
	SCROLLBAR_KEY_LIST = ( "size", )
	LIST_BOX_KEY_LIST = ( "width", "height", )

	# app.ENABLE_MONSTER_CARD or app.ENABLE_MYSHOP_DECO or app.ENABLE_MINI_GAME_YUTNORI
	RENDER_TARGET_KEY_LIST = ( "width", "height", )

	if app.ENABLE_QUEST_RENEWAL:
		SUB_TITLE_BAR_KEY_LIST = ( "width", )
		LIST_BAR_KEY_LIST = ( "width", )

	# app.ENABLE_FISH_EVENT
	SP_GRID_TABLE_KEY_LIST = ( "start_index", "x_count", "y_count", "x_step", "y_step", )

	def __init__(self):
		self.Clear()

	def Clear(self):
		if app.ENABLE_WINDOW_RESIZE:
			self.ScriptDictionary = {
				"SCREEN_WIDTH": Expr("SCREEN_WIDTH"),
				"SCREEN_HEIGHT": Expr("SCREEN_HEIGHT"),
				"int": SandboxInt,
				"float": SandboxFloat,
			}
		else:
			self.ScriptDictionary = { "SCREEN_WIDTH" : wndMgr.GetScreenWidth(), "SCREEN_HEIGHT" : wndMgr.GetScreenHeight() }
		self.InsertFunction = 0

	def LoadScriptFile(self, window, FileName, abortOnError=True):
		import exception
		import os
		import errno
		self.Clear()

		#print "===== Load Script File : %s" % (FileName)

		#ui 코드는 sandbox 내에서 실행되어야한다.(봇이 껴있을 여지가 있기 때문에)
		#import sys
		#from utils import Sandbox
		#sandbox = Sandbox(True, ["uiScriptLocale", "localeInfo", "sys", "item", "app"])

		# chr, player 등은 sandbox 내에서 import가 허용되지 않기 때문에,(봇이 악용할 여지가 매우 큼.)
		#  미리 script dictionary에 필요한 상수를 넣어놓는다.
		import chr
		import player
		import app
		self.ScriptDictionary["PLAYER_NAME_MAX_LEN"] = chr.PLAYER_NAME_MAX_LEN
		if app.ENABLE_DRAGON_SOUL_SYSTEM:
			self.ScriptDictionary["DRAGON_SOUL_EQUIPMENT_SLOT_START"] = player.DRAGON_SOUL_EQUIPMENT_SLOT_START
		self.ScriptDictionary["LOCALE_PATH"] = app.GetLocalePath()

		try:
			#sandbox.execfile(FileName, self.ScriptDictionary)
			execfile(FileName, self.ScriptDictionary)
		except IOError as err:
			import sys
			import dbg
			dbg.TraceError("Failed to load script file : %s" % (FileName))
			dbg.TraceError("error : %s" % (err))
			if abortOnError:
				exception.Abort("LoadScriptFile1")
			return False
		except RuntimeError as err:
			import sys
			import dbg
			dbg.TraceError("Failed to load script file : %s" % (FileName))
			dbg.TraceError("error : %s" % (err))
			if abortOnError:
				exception.Abort("LoadScriptFile2")
			return False
		except:
			import sys
			import dbg
			dbg.TraceError("Failed to load script file : %s" % (FileName))
			if abortOnError:
				exception.Abort("LoadScriptFile!!!!!!!!!!!!!!")
			return False

		#####

		Body = self.ScriptDictionary["window"]
		self.CheckKeyList("window", Body, self.BODY_KEY_LIST)

		window.ClearDictionary()
		self.InsertFunction = window.InsertChild

		window.SetPosition(int(Body["x"]), int(Body["y"]))

		if localeInfo.IsARABIC():
			w = wndMgr.GetScreenWidth()
			h = wndMgr.GetScreenHeight()
			if ("width" in Body):
				w = int(Body["width"])
			if ("height" in Body):
				h = int(Body["height"])

			window.SetSize(w, h)
		else:
			window.SetSize(int(Body["width"]), int(Body["height"]))
			if True == ("style" in Body):
				for StyleList in Body["style"]:
					window.AddFlag(StyleList)

		if app.ENABLE_WINDOW_RESIZE:
			resizeDic = ExtractWindowScaling(Body)
			window.SetResizeDic(resizeDic)

		self.LoadChildren(window, Body)
		return True

	def LoadChildren(self, parent, dicChildren):

		if localeInfo.IsARABIC():
			parent.AddFlag( "rtl" )

		if True == ("style" in dicChildren):
			for style in dicChildren["style"]:
				parent.AddFlag(style)

		if False == ("children" in dicChildren):
			return False

		Index = 0

		ChildrenList = dicChildren["children"]
		parent.Children = list(range(len(ChildrenList)))
		for ElementValue in ChildrenList:
			try:
				Name = ElementValue["name"]
			except KeyError:
				Name = ElementValue["name"] = "NONAME"

			try:
				Type = ElementValue["type"]
			except KeyError:
				Type = ElementValue["type"] = "window"

			if False == self.CheckKeyList(Name, ElementValue, self.DEFAULT_KEY_LIST):
				del parent.Children[Index]
				continue

			if Type == "window":
				parent.Children[Index] = ScriptWindow()
				parent.Children[Index].SetParent(parent)
				self.LoadElementWindow(parent.Children[Index], ElementValue, parent)

			elif Type == "button":
				parent.Children[Index] = Button()
				parent.Children[Index].SetParent(parent)
				self.LoadElementButton(parent.Children[Index], ElementValue, parent)

			elif Type == "outline_window":
				parent.Children[Index] = OutlineWindow()
				parent.Children[Index].SetParent(parent)
				self.LoadOutlineWindow(parent.Children[Index], ElementValue, parent)

			elif Type == "radio_button":
				parent.Children[Index] = RadioButton()
				parent.Children[Index].SetParent(parent)
				self.LoadElementButton(parent.Children[Index], ElementValue, parent)

			elif Type == "toggle_button":
				parent.Children[Index] = ToggleButton()
				parent.Children[Index].SetParent(parent)
				self.LoadElementButton(parent.Children[Index], ElementValue, parent)

			elif Type == "mark":
				parent.Children[Index] = MarkBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementMark(parent.Children[Index], ElementValue, parent)

			elif Type == "image":
				parent.Children[Index] = ImageBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementImage(parent.Children[Index], ElementValue, parent)

			elif Type == "expanded_image":
				parent.Children[Index] = ExpandedImageBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementExpandedImage(parent.Children[Index], ElementValue, parent)

			elif Type == "ani_image":
				parent.Children[Index] = AniImageBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementAniImage(parent.Children[Index], ElementValue, parent)

			elif Type == "slot":
				parent.Children[Index] = SlotWindow()
				parent.Children[Index].SetParent(parent)
				self.LoadElementSlot(parent.Children[Index], ElementValue, parent)

			elif Type == "candidate_list":
				parent.Children[Index] = CandidateListBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementCandidateList(parent.Children[Index], ElementValue, parent)

			elif Type == "grid_table":
				parent.Children[Index] = GridSlotWindow()
				parent.Children[Index].SetParent(parent)
				self.LoadElementGridTable(parent.Children[Index], ElementValue, parent)

			elif Type == "text":
				parent.Children[Index] = TextLine()
				parent.Children[Index].SetParent(parent)
				self.LoadElementText(parent.Children[Index], ElementValue, parent)

			elif Type == "editline":
				parent.Children[Index] = EditLine()
				parent.Children[Index].SetParent(parent)
				self.LoadElementEditLine(parent.Children[Index], ElementValue, parent)

			elif Type == "titlebar":
				parent.Children[Index] = TitleBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementTitleBar(parent.Children[Index], ElementValue, parent)

			elif Type == "horizontalbar":
				parent.Children[Index] = HorizontalBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementHorizontalBar(parent.Children[Index], ElementValue, parent)

			elif Type == "board":
				parent.Children[Index] = Board()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "invisibleboard":
				parent.Children[Index] = InvisibleBoard()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "board_with_titlebar":
				parent.Children[Index] = BoardWithTitleBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoardWithTitleBar(parent.Children[Index], ElementValue, parent)

			elif Type == "thinboard":
				parent.Children[Index] = ThinBoard()
				parent.Children[Index].SetParent(parent)
				self.LoadElementThinBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "thinboard_gold":
				parent.Children[Index] = ThinBoardGold()
				parent.Children[Index].SetParent(parent)
				self.LoadElementThinBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "thinboard_circle":
				parent.Children[Index] = ThinBoardCircle()
				parent.Children[Index].SetParent(parent)
				self.LoadElementThinBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "box":
				parent.Children[Index] = Box()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBox(parent.Children[Index], ElementValue, parent)

			elif Type == "bar":
				parent.Children[Index] = Bar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBar(parent.Children[Index], ElementValue, parent)

			elif Type == "line":
				parent.Children[Index] = Line()
				parent.Children[Index].SetParent(parent)
				self.LoadElementLine(parent.Children[Index], ElementValue, parent)

			elif Type == "slotbar":
				parent.Children[Index] = SlotBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementSlotBar(parent.Children[Index], ElementValue, parent)

			elif Type == "gauge":
				parent.Children[Index] = Gauge()
				parent.Children[Index].SetParent(parent)
				self.LoadElementGauge(parent.Children[Index], ElementValue, parent)

			elif Type == "scrollbar":
				parent.Children[Index] = ScrollBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementScrollBar(parent.Children[Index], ElementValue, parent)

			elif Type == "thin_scrollbar":
				parent.Children[Index] = ThinScrollBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementScrollBar(parent.Children[Index], ElementValue, parent)

			elif Type == "small_thin_scrollbar":
				parent.Children[Index] = SmallThinScrollBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementScrollBar(parent.Children[Index], ElementValue, parent)

			elif Type == "scrollbar_flat":
				parent.Children[Index] = ScrollBarFlat()
				parent.Children[Index].SetParent(parent)
				self.LoadElementScrollBar(parent.Children[Index], ElementValue, parent)

			elif Type == "sliderbar":
				parent.Children[Index] = SliderBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementSliderBar(parent.Children[Index], ElementValue, parent)

			elif Type == "listbox":
				parent.Children[Index] = ListBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementListBox(parent.Children[Index], ElementValue, parent)

			elif Type == "listbox2":
				parent.Children[Index] = ListBox2()
				parent.Children[Index].SetParent(parent)
				self.LoadElementListBox2(parent.Children[Index], ElementValue, parent)

			elif Type == "listboxex":
				parent.Children[Index] = ListBoxEx()
				parent.Children[Index].SetParent(parent)
				self.LoadElementListBoxEx(parent.Children[Index], ElementValue, parent)

			elif Type == "numberline":
				parent.Children[Index] = NumberLine()
				parent.Children[Index].SetParent(parent)
				self.LoadElementNumberLine(parent.Children[Index], ElementValue, parent)

			# app.ENABLE_MONSTER_CARD or app.ENABLE_MYSHOP_DECO or app.ENABLE_MINI_GAME_YUTNORI
			elif Type == "render_target":
				parent.Children[Index] = RenderTarget()
				parent.Children[Index].SetParent(parent)
				self.LoadElementRenderTarget(parent.Children[Index], ElementValue, parent)

			elif Type == "wiki_render_target":
				parent.Children[Index] = WikiRenderTargetUi()
				parent.Children[Index].SetParent(parent)
				self.LoadElementRenderTarget(parent.Children[Index], ElementValue, parent)

			elif Type == "middleboard" and app.ENABLE_LOADING_TIP:
				parent.Children[Index] = ThinBoard()
				parent.Children[Index].SetParent(parent)
				self.LoadElementThinBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "listbox_new" and app.ENABLE_EXCHANGE_LOG:
				parent.Children[Index] = ListBoxNew()
				parent.Children[Index].SetParent(parent)
				self.LoadElementListBox(parent.Children[Index], ElementValue, parent)

			elif Type == "subtitlebar" and app.ENABLE_QUEST_RENEWAL:
				parent.Children[Index] = SubTitleBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementSubTitleBar(parent.Children[Index], ElementValue, parent)

			elif Type == "listbar" and app.ENABLE_QUEST_RENEWAL:
				parent.Children[Index] = ListBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementListBar(parent.Children[Index], ElementValue, parent)

			elif Type == "multi_text" and app.ENABLE_OFFLINE_SHOP:
				parent.Children[Index] = MultiTextLine()
				parent.Children[Index].SetParent(parent)
				self.LoadElementMultiText(parent.Children[Index], ElementValue, parent)

			elif Type == "dragonboard":
				parent.Children[Index] = DragonBoard()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "dragonboard_with_titlebar":
				parent.Children[Index] = DragonBoardWithTitleBar()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoardWithTitleBar(parent.Children[Index], ElementValue, parent)

			elif Type == "border_a" and app.ENABLE_BATTLE_PASS:
				parent.Children[Index] = BorderA()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoard(parent.Children[Index], ElementValue, parent)				

			elif Type == "boxed_board":
				parent.Children[Index] = BoxedBoard()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBoxedBoard(parent.Children[Index], ElementValue, parent)

			elif Type == "line_graph" and app.ENABLE_OFFLINE_SHOP:
				parent.Children[Index] = LineGraph()
				parent.Children[Index].SetParent(parent)
				self.LoadElementLineGraph(parent.Children[Index], ElementValue, parent)

			elif Type == "bar_graph" and app.ENABLE_OFFLINE_SHOP:
				parent.Children[Index] = BarGraph()
				parent.Children[Index].SetParent(parent)
				self.LoadElementBarGraph(parent.Children[Index], ElementValue, parent)

			elif Type == "selectable_text":
				parent.Children[Index] = SelectableTextLine(False)
				parent.Children[Index].SetParent(parent)
				self.LoadElementSelectableText(parent.Children[Index], ElementValue, parent)

			elif Type == "extended_text" and app.ENABLE_OFFLINE_SHOP:
				parent.Children[Index] = ExtendedTextLine()
				parent.Children[Index].SetParent(parent)
				self.LoadElementExtendedText(parent.Children[Index], ElementValue, parent)

			elif Type == "renderbox":
				parent.Children[Index] = RenderBox()
				parent.Children[Index].SetParent(parent)
				self.LoadElementRenderBox(parent.Children[Index], ElementValue, parent)

			else:
				Index += 1
				continue

			parent.Children[Index].SetWindowName(Name)
			if app.ENABLE_WINDOW_RESIZE:
				resizeDic = ExtractWindowScaling(ElementValue)
				parent.Children[Index].SetResizeDic(resizeDic)
			if 0 != self.InsertFunction:
				self.InsertFunction(Name, parent.Children[Index])

			self.LoadChildren(parent.Children[Index], ElementValue)
			Index += 1

	def CheckKeyList(self, name, value, key_list):

		for DataKey in key_list:
			if False == (DataKey in value):
				print("Failed to find data key", "[" + name + "/" + DataKey + "]")
				return False

		return True

	def LoadDefaultData(self, window, value, parentWindow):
		loc_x = int(value["x"])
		loc_y = int(value["y"])
		if ("vertical_align" in value):
			if "center" == value["vertical_align"]:
				window.SetWindowVerticalAlignCenter()
			elif "bottom" == value["vertical_align"]:
				window.SetWindowVerticalAlignBottom()

		if parentWindow.IsRTL():
			loc_x = int(value["x"]) + window.GetWidth()
			if ("horizontal_align" in value):
				if "center" == value["horizontal_align"]:
					window.SetWindowHorizontalAlignCenter()
					loc_x = - int(value["x"])
				elif "right" == value["horizontal_align"]:
					window.SetWindowHorizontalAlignLeft()
					loc_x = int(value["x"]) - window.GetWidth()
					## loc_x = parentWindow.GetWidth() - int(value["x"]) + window.GetWidth()
			else:
				window.SetWindowHorizontalAlignRight()

			if ("all_align" in value):
				window.SetWindowVerticalAlignCenter()
				window.SetWindowHorizontalAlignCenter()
				loc_x = - int(value["x"])
		else:
			if ("horizontal_align" in value):
				if "center" == value["horizontal_align"]:
					window.SetWindowHorizontalAlignCenter()
				elif "right" == value["horizontal_align"]:
					window.SetWindowHorizontalAlignRight()

		window.SetPosition(loc_x, loc_y)
		window.Show()

	## Window
	def LoadElementWindow(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.WINDOW_KEY_LIST):
			return False

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Outline Window
	def LoadOutlineWindow(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.OUTLINE_WINDOW_KEY_LIST):
			return False

		window.MakeOutlineWindow(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Button
	def LoadElementButton(self, window, value, parentWindow):
		if ("width" in value) and ("height" in value):
			window.SetSize(int(value["width"]), int(value["height"]))

		if True == ("default_image" in value):
			window.SetUpVisual(value["default_image"])
		if True == ("over_image" in value):
			window.SetOverVisual(value["over_image"])
		if True == ("down_image" in value):
			window.SetDownVisual(value["down_image"])
		if True == ("disable_image" in value):
			window.SetDisableVisual(value["disable_image"])

		if True == ("text" in value):
			if True == ("fontsize" in value):
				fontSize = value["fontsize"]

				if "LARGE" == fontSize:
					window.AppendTextLine(value["text"], localeInfo.UI_DEF_FONT_LARGE)
				elif "SMALL" == fontSize:
					window.AppendTextLine(value["text"], localeInfo.UI_DEF_FONT_SMALL)
				else:
					window.AppendTextLine(value["text"])
			else:
				if True == ("text_height" in value):
					window.SetText(value["text"], value["text_height"])
				elif TRUE == ("text_x" in value) and app.ENABLE_NEW_GAMEOPTION:
					window.SetListText(value["text"], value["text_x"])
				else:
					window.SetText(value["text"])

			if ("text_color" in value):
				window.SetTextColor(value["text_color"])

			if ("text_outline" in value) and app.ENABLE_TELEPORT_WINDOW:
				if value["text_outline"]:
					window.SetOutline()

		if True == ("tooltip_text" in value):
			if True == ("tooltip_x" in value) and True == ("tooltip_y" in value):
				window.SetToolTipText(value["tooltip_text"], int(value["tooltip_x"]), int(value["tooltip_y"]))
			else:
				window.SetToolTipText(value["tooltip_text"])

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Mark
	def LoadElementMark(self, window, value, parentWindow):

		#if False == self.CheckKeyList(value["name"], value, self.MARK_KEY_LIST):
		#	return False

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Image
	def LoadElementImage(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.IMAGE_KEY_LIST):
			return False

		window.LoadImage(value["image"])

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## AniImage
	def LoadElementAniImage(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.ANI_IMAGE_KEY_LIST):
			return False

		if True == ("delay" in value):
			window.SetDelay(value["delay"])

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if True == ("x_scale" in value) and True == ("y_scale" in value):
				for image in value["images"]:
					window.AppendImageScale(image, float(value["x_scale"]), float(value["y_scale"]))
			else:
				for image in value["images"]:
					window.AppendImage(image)
		else:
			for image in value["images"]:
				window.AppendImage(image)

		if ("width" in value) and ("height" in value):
			window.SetSize(value["width"], value["height"])

		if app.ENABLE_GROWTH_PET_SYSTEM:
			if True == ("x_scale" in value) and True == ("y_scale" in value):
				window.SetScale(float(value["x_scale"]), float(value["y_scale"]))

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Expanded Image
	def LoadElementExpandedImage(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.EXPANDED_IMAGE_KEY_LIST):
			return False

		window.LoadImage(value["image"])

		if True == ("x_origin" in value) and True == ("y_origin" in value):
			window.SetOrigin(float(value["x_origin"]), float(value["y_origin"]))

		if True == ("x_scale" in value) and True == ("y_scale" in value):
			window.SetScale(float(value["x_scale"]), float(value["y_scale"]))

		if True == ("rect" in value):
			RenderingRect = value["rect"]
			window.SetRenderingRect(RenderingRect[0], RenderingRect[1], RenderingRect[2], RenderingRect[3])

		if True == ("mode" in value):
			mode = value["mode"]
			if "MODULATE" == mode:
				window.SetRenderingMode(wndMgr.RENDERING_MODE_MODULATE)

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Slot
	def LoadElementSlot(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.SLOT_KEY_LIST):
			return False

		global_x = int(value["x"])
		global_y = int(value["y"])
		global_width = int(value["width"])
		global_height = int(value["height"])

		window.SetPosition(global_x, global_y)
		window.SetSize(global_width, global_height)
		window.Show()

		r = 1.0
		g = 1.0
		b = 1.0
		a = 1.0

		if True == ("image_r" in value) and \
			True == ("image_g" in value) and \
			True == ("image_b" in value) and \
			True == ("image_a" in value):
			r = float(value["image_r"])
			g = float(value["image_g"])
			b = float(value["image_b"])
			a = float(value["image_a"])

		SLOT_ONE_KEY_LIST = ("index", "x", "y", "width", "height")

		for slot in value["slot"]:
			if True == self.CheckKeyList(value["name"] + " - one", slot, SLOT_ONE_KEY_LIST):
				window.AppendSlot(int(slot["index"]),
								  int(slot["x"]),
								  int(slot["y"]),
								  int(slot["width"]),
								  int(slot["height"]))
		if app.ENABLE_GROWTH_PET_SYSTEM:
			if True == ("x_scale" in value) and True == ("y_scale" in value):
				window.SetSlotScale(float(value["x_scale"]), float(value["y_scale"]))
		if True == ("image" in value):
			wndMgr.SetSlotBaseImage(window.hWnd,
									value["image"],
									r, g, b, a)

		return True

	def LoadElementCandidateList(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.CANDIDATE_LIST_KEY_LIST):
			return False

		window.SetPosition(int(value["x"]), int(value["y"]))
		window.SetItemSize(int(value["item_xsize"]), int(value["item_ysize"]))
		window.SetItemStep(int(value["item_step"]))
		window.Show()

		return True

	## Table
	def LoadElementGridTable(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.GRID_TABLE_KEY_LIST):
			return False

		xBlank = 0
		yBlank = 0
		if True == ("x_blank" in value):
			xBlank = int(value["x_blank"])
		if True == ("y_blank" in value):
			yBlank = int(value["y_blank"])

		if localeInfo.IsARABIC():
			pass
		else:
			window.SetPosition(int(value["x"]), int(value["y"]))

		window.ArrangeSlot(	int(value["start_index"]),
							int(value["x_count"]),
							int(value["y_count"]),
							int(value["x_step"]),
							int(value["y_step"]),
							xBlank,
							yBlank)
		if True == ("image" in value):
			r = 1.0
			g = 1.0
			b = 1.0
			a = 1.0
			if True == ("image_r" in value) and \
				True == ("image_g" in value) and \
				True == ("image_b" in value) and \
				True == ("image_a" in value):
				r = float(value["image_r"])
				g = float(value["image_g"])
				b = float(value["image_b"])
				a = float(value["image_a"])
			wndMgr.SetSlotBaseImage(window.hWnd, value["image"], r, g, b, a)

		if True == ("style" in value):
			if "select" == value["style"]:
				wndMgr.SetSlotStyle(window.hWnd, wndMgr.SLOT_STYLE_SELECT)
		if localeInfo.IsARABIC():
			self.LoadDefaultData(window, value, parentWindow)
		else:
			window.Show()

		return True

	## Text
	def LoadElementText(self, window, value, parentWindow):
		if isinstance(parentWindow, TitleBar):
			value = dict(value)
			value["x"] = 0
			value["horizontal_align"] = "center"
			value["text_horizontal_align"] = "center"

		if ("multi_line" in value):
			if value["multi_line"]:
				window.SetMultiLine()

		if value.get("name") == "TitleName" and parentWindow.GetWindowName() == "TitleBar":
			window.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_WINDOW_TITLE))

		if app.ENABLE_TELEPORT_WINDOW:
			if ("fontsize" in value):
				fontSize = value["fontsize"]
				if "SLARGE" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_SLARGE)
				if "LARGE" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_LARGE)
				if "XLARGE" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_XLARGE)
				if "XXLARGE" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_XXLARGE)
				if "SMALL" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_SMALL)
		else:
			if ("fontsize" in value):
				fontSize = value["fontsize"]

				if "LARGE" == fontSize:
					window.SetFontName(localeInfo.UI_DEF_FONT_LARGE)

		if ("fontname" in value):
			fontName = value["fontname"]
			window.SetFontName(fontName)

		if ("text_horizontal_align" in value):
			if "left" == value["text_horizontal_align"]:
				window.SetHorizontalAlignLeft()
			elif "center" == value["text_horizontal_align"]:
				window.SetHorizontalAlignCenter()
			elif "right" == value["text_horizontal_align"]:
				window.SetHorizontalAlignRight()

		if ("text_vertical_align" in value):
			if "top" == value["text_vertical_align"]:
				window.SetVerticalAlignTop()
			elif "center" == value["text_vertical_align"]:
				window.SetVerticalAlignCenter()
			elif "bottom" == value["text_vertical_align"]:
				window.SetVerticalAlignBottom()

		if ("all_align" in value):
			window.SetHorizontalAlignCenter()
			window.SetVerticalAlignCenter()
			window.SetWindowHorizontalAlignCenter()
			window.SetWindowVerticalAlignCenter()

		if ("r" in value) and ("g" in value) and ("b" in value):
			window.SetFontColor(float(value["r"]), float(value["g"]), float(value["b"]))
		elif ("color" in value):
			window.SetPackedFontColor(value["color"])
		else:
			window.SetFontColor(0.8549, 0.8549, 0.8549)

		if ("outline" in value):
			if value["outline"]:
				window.SetOutline()
		if ("limit_width" in value):
			window.SetLimitWidth(value["limit_width"])
		if True == ("text" in value):
			window.SetText(value["text"])

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## EditLine
	def LoadElementEditLine(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.EDIT_LINE_KEY_LIST):
			return False

		if ("secret_flag" in value):
			window.SetSecret(value["secret_flag"])
		if ("with_codepage" in value):
			if value["with_codepage"]:
				window.bCodePage = True
		if ("only_number" in value):
			if value["only_number"]:
				window.SetNumberMode()
		if ("enable_codepage" in value):
			window.SetIMEFlag(value["enable_codepage"])
		if ("enable_ime" in value):
			window.SetIMEFlag(value["enable_ime"])
		if ("limit_width" in value):
			window.SetLimitWidth(value["limit_width"])
		if ("multi_line" in value):
			if value["multi_line"]:
				window.SetMultiLine()
		if ("overlay" in value):
			window.SetOverlayText(value["overlay"])

		window.SetMax(int(value["input_limit"]))
		window.SetSize(int(value["width"]), int(value["height"]))

		self.LoadElementText(window, value, parentWindow)

		return True

	## TitleBar
	def LoadElementTitleBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.TITLE_BAR_KEY_LIST):
			return False

		# V31 structural chrome: titlebars form the complete top edge of their
		# parent window.  Work on a copy so reused script dictionaries keep their
		# source geometry and RTL handling stays inside LoadDefaultData.
		titleBarValue = dict(value)
		if not titleBarValue.get("v31_keep_inset", False):
			titleBarValue["x"] = -4
			titleBarValue["y"] = 0
			titleBarValue["width"] = parentWindow.GetWidth() + 8

		window.MakeTitleBar(int(titleBarValue["width"]), titleBarValue.get("color", "red"))
		self.LoadDefaultData(window, titleBarValue, parentWindow)

		return True

	## HorizontalBar
	def LoadElementHorizontalBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.HORIZONTAL_BAR_KEY_LIST):
			return False

		window.Create(int(value["width"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Board
	def LoadElementBoard(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.BOARD_KEY_LIST):
			return False

		if app.ENABLE_IMAGE_CLIP_RECT:
			if True == ("size_skip" in value):
				window.skipMaxCheck = True

		assetRoot = value.get("asset_root")
		if assetRoot:
			window.LoadVisuals(
				assetRoot + "board_corner_",
				assetRoot + "board_line_",
				assetRoot + "board_base.tga",
			)

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Board With TitleBar
	def LoadElementBoardWithTitleBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.BOARD_WITH_TITLEBAR_KEY_LIST):
			return False

		window.SetSize(int(value["width"]), int(value["height"]))
		window.SetTitleName(value["title"])
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## BoxedBoard
	def LoadElementBoxedBoard(self, window, value, parentWindow):
		if not self.CheckKeyList(value["name"], value, self.WINDOW_KEY_LIST):
			return False

		window.SetSize(value["width"], value["height"])

		if ("border_color" in value):
			window.SetBorderColor(value["border_color"])

		if ("border_size" in value):
			window.SetBorderSize(value["border_size"])

		if ("base_color" in value):
			window.SetBaseColor(value["base_color"])

		self.LoadDefaultData(window, value, parentWindow)
		return True

	## ThinBoard
	def LoadElementThinBoard(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.BOARD_KEY_LIST):
			return False

		assetRoot = value.get("asset_root")
		if assetRoot:
			window.LoadVisuals(
				assetRoot + "thinboard_corner_",
				assetRoot + "thinboard_line_",
				assetRoot + "board_base.tga",
			)

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	if app.ENABLE_QUEST_RENEWAL:
		## SubTitleBar
		def LoadElementSubTitleBar(self, window, value, parentWindow):
			if False == self.CheckKeyList(value["name"], value, self.SUB_TITLE_BAR_KEY_LIST):
				return False

			window.MakeSubTitleBar(int(value["width"]), value.get("color", "red"))
			self.LoadElementButton(window, value, parentWindow)
			window.Show()
			return True

		## ListBar
		def LoadElementListBar(self, window, value, parentWindow):
			if False == self.CheckKeyList(value["name"], value, self.LIST_BAR_KEY_LIST):
				return False

			window.MakeListBar(int(value["width"]), value.get("color", "red"))
			self.LoadElementButton(window, value, parentWindow)

			return True

	## Box
	def LoadElementBox(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.BOX_KEY_LIST):
			return False

		if True == ("color" in value):
			window.SetColor(value["color"])

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Bar
	def LoadElementBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.BAR_KEY_LIST):
			return False

		if True == ("color" in value):
			window.SetColor(value["color"])

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Line
	def LoadElementLine(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.LINE_KEY_LIST):
			return False

		if True == ("color" in value):
			window.SetColor(value["color"])

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Slot
	def LoadElementSlotBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.SLOTBAR_KEY_LIST):
			return False

		window.SetSize(int(value["width"]), int(value["height"]))
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## Gauge
	def LoadElementGauge(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.GAUGE_KEY_LIST):
			return False

		window.MakeGauge(value["width"], value["color"])
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## ScrollBar
	def LoadElementScrollBar(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.SCROLLBAR_KEY_LIST):
			return False

		window.SetScrollBarSize(value["size"])
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## SliderBar
	def LoadElementSliderBar(self, window, value, parentWindow):

		self.LoadDefaultData(window, value, parentWindow)

		return True

	## ListBox
	def LoadElementListBox(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.LIST_BOX_KEY_LIST):
			return False

		if ("item_align" in value):
			window.SetTextCenterAlign(value["item_align"])

		window.SetSize(value["width"], value["height"])
		self.LoadDefaultData(window, value, parentWindow)

		return True

	## ListBox2
	def LoadElementListBox2(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.LIST_BOX_KEY_LIST):
			return False

		window.SetRowCount(value.get("row_count", 10)) 
		window.SetSize(value["width"], value["height"])
		self.LoadDefaultData(window, value, parentWindow)

		if ("item_align" in value):
			window.SetTextCenterAlign(value["item_align"])

		return True

	def LoadElementListBoxEx(self, window, value, parentWindow):

		if False == self.CheckKeyList(value["name"], value, self.LIST_BOX_KEY_LIST):
			return False

		window.SetSize(value["width"], value["height"])
		self.LoadDefaultData(window, value, parentWindow)

		if ("itemsize_x" in value) and ("itemsize_y" in value):
			window.SetItemSize(int(value["itemsize_x"]), int(value["itemsize_y"]))

		if ("itemstep" in value):
			window.SetItemStep(int(value["itemstep"]))

		if ("viewcount" in value):
			window.SetViewItemCount(int(value["viewcount"]))

		return True

	def LoadElementNumberLine(self, window, value, parentWindow):
		self.LoadDefaultData(window, value, parentWindow)
		return True

	# app.ENABLE_MONSTER_CARD or app.ENABLE_MYSHOP_DECO or app.ENABLE_MINI_GAME_YUTNORI
	def LoadElementRenderTarget(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.RENDER_TARGET_KEY_LIST):
			return False

		window.SetSize(value["width"], value["height"])

		if True == ("style" in value):
			for style in value["style"]:
				window.AddFlag(style)

		self.LoadDefaultData(window, value, parentWindow)

		if ("index" in value):
			window.SetRenderTarget(int(value["index"]))

		return True

	def LoadElementRenderBox(self, window, value, parentWindow):
		if False == self.CheckKeyList(value["name"], value, self.RENDER_BOX_KEY_LIST):
			return False

		window.SetSize(value["width"], value["height"])
		self.LoadDefaultData(window, value, parentWindow)

		if ("color" in value):
			window.SetColor(int(value["color"]))

		return True

	def LoadElementExtendedText(self, window, value, parentWindow):

		if True == ("text" in value):
			window.SetText(value["text"])

		self.LoadDefaultData(window, value, parentWindow)

		return True
	
	def LoadElementGraphDefault(self, window, value, parent):
		if ("width" in value) and ("height" in value):
			window.SetSize(value["width"], value["height"])

		if ("y_axis_limit" in value):
			window.SetYAxisLimitValue(value["y_axis_limit"][0], value["y_axis_limit"][1])

		if ("x_axis_limit" in value):
			window.SetXAxisLimitValue(value["x_axis_limit"][0], value["x_axis_limit"][1])

		if ("color" in value):
			window.SetColor(value["color"])

		return True

	def LoadElementSelectableText(self, window, value, parent):
		# if ("normal_color" in value):
		# 	window.SetNormalBackground(value["normal_color"])

		# if ("over_color" in value):
		# 	window.SetOverBackground(value["over_color"])

		# if ("down_color" in value):
		# 	window.SetDownBackground(value["down_color"])

		if ("text" in value):
			window.SetText(value["text"])

		window.SetSize(int(value["width"]), int(value["height"]))

		self.LoadDefaultData(window, value, parent)

		return True

	def LoadElementBarGraph(self, window, value, parent):
		self.LoadDefaultData(window, value, parent)
		self.LoadElementGraphDefault(window, value, parent)

		if ("bar_space" in value):
			window.SetBarSpace(value["bar_space"])

		return True

	def LoadElementLineGraph(self, window, value, parent):
		self.LoadDefaultData(window, value, parent)
		self.LoadElementGraphDefault(window, value, parent)

		if ("line_thickness" in value):
			window.SetLineThickness(value["line_thickness"])

		return True

	def LoadElementMultiText(self, window, value, parent):

		if ("width" in value) and ("height" in value):
			window.SetSize(value["width"], value["height"])
		elif ("width" in value):
			window.SetWidth(value["width"])

		if ("text_horizontal_align" in value):
			if "center" == value["text_horizontal_align"]:
				window.SetTextHorizontalAlignCenter()

		if ("text_vertical_align" in value):
			if "center" == value["text_vertical_align"]:
				window.SetTextVerticalAlignCenter()

		if ("r" in value) and ("g" in value) and ("b" in value):
			window.SetFontColor(float(value["r"]), float(value["g"]), float(value["b"]))
		elif ("color" in value):
			window.SetPackedFontColor(value["color"])
		elif ("register_color" in value):
			for data in value["register_color"]:
				window.RegisterPackedFontColor(data[0], data[1])
				if len(data) > 2 and data[2] == True:
					window.SetPackedFontColor(data[1])

		if ("text" in value):
			window.SetText(value["text"])

		self.LoadDefaultData(window, value, parent)

		return True

class ReadingWnd(Bar):
	def __init__(self):
		Bar.__init__(self,"TOP_MOST")

		self.__BuildText()
		self.SetSize(80, 19)
		self.Show()

	def __del__(self):
		Bar.__del__(self)

	def __BuildText(self):
		self.text = TextLine()
		self.text.SetParent(self)
		self.text.SetPosition(4, 3)
		self.text.Show()

	def SetText(self, text):
		self.text.SetText(text)

	def SetReadingPosition(self, x, y):
		xPos = x + 2
		yPos = y  - self.GetHeight() - 2
		self.SetPosition(xPos, yPos)

	def SetTextColor(self, color):
		self.text.SetPackedFontColor(color)

class OutlineWindow(Window):
	PATTERN_PATH = "d:/ymir work/ui/pattern/"

	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.__Initialize()

	def __del__(self):
		Window.__del__(self)
		self.__Initialize()

	def __Initialize(self):
		self.pattern_x_count = 0
		self.pattern_y_count = 0
		self.left_top_img = None
		self.right_top_img = None
		self.left_bottom_img = None
		self.right_bottom_img = None
		self.top_center_img = None
		self.left_center_img = None
		self.right_center_img = None
		self.bottom_center_img = None
		self.center_img = None

	def MakeOutlineWindow(self, window_width, window_height):
		self.AddFlag("ltr")
		self.AddFlag("attach")
		self.SetWindowName("outline_window")
		self.SetSize(window_width, window_height)

		self.pattern_x_count = (window_width - 32) // 16
		self.pattern_y_count = (window_height - 32) // 16

		self.left_top_img = ImageBox()
		self.left_top_img.SetParent(self)
		self.left_top_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_left_top.tga")
		self.left_top_img.SetPosition(0, 0)
		self.left_top_img.Show()

		self.right_top_img = ImageBox()
		self.right_top_img.SetParent(self)
		self.right_top_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_right_top.tga")
		self.right_top_img.SetPosition(window_width - 16, 0)
		self.right_top_img.Show()

		self.left_bottom_img = ImageBox()
		self.left_bottom_img.SetParent(self)
		self.left_bottom_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_left_bottom.tga")
		self.left_bottom_img.SetPosition(0, window_height - 16)
		self.left_bottom_img.Show()

		self.right_bottom_img = ImageBox()
		self.right_bottom_img.SetParent(self)
		self.right_bottom_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_right_bottom.tga")
		self.right_bottom_img.SetPosition(window_width - 16, window_height - 16)
		self.right_bottom_img.Show()

		self.top_center_img = ExpandedImageBox()
		self.top_center_img.SetParent(self)
		self.top_center_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_top.tga")
		self.top_center_img.SetPosition(16, 0)
		self.top_center_img.SetRenderingRect(0.0, 0.0, self.pattern_x_count, 0.0)
		self.top_center_img.Show()

		self.left_center_img = ExpandedImageBox()
		self.left_center_img.SetParent(self)
		self.left_center_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_left.tga")
		self.left_center_img.SetPosition(0, 16)
		self.left_center_img.SetRenderingRect(0.0, 0.0, 0.0, self.pattern_y_count)
		self.left_center_img.Show()

		self.right_center_img = ExpandedImageBox()
		self.right_center_img.SetParent(self)
		self.right_center_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_right.tga")
		self.right_center_img.SetPosition(window_width - 16, 16)
		self.right_center_img.SetRenderingRect(0.0, 0.0, 0.0, self.pattern_y_count)
		self.right_center_img.Show()

		self.bottom_center_img = ExpandedImageBox()
		self.bottom_center_img.SetParent(self)
		self.bottom_center_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_bottom.tga")
		self.bottom_center_img.SetPosition(16, window_height - 16)
		self.bottom_center_img.SetRenderingRect(0.0, 0.0, self.pattern_x_count, 0.0)
		self.bottom_center_img.Show()

		self.center_img = ExpandedImageBox()
		self.center_img.SetParent(self)
		self.center_img.LoadImage(OutlineWindow.PATTERN_PATH + "border_A_center.tga")
		self.center_img.SetPosition(16, 16)
		self.center_img.SetRenderingRect(0.0, 0.0, self.pattern_x_count, self.pattern_y_count)
		self.center_img.Show()

if app.ENABLE_AUTO_REFINE or app.ENABLE_SKILL_COLOR_SYSTEM:
	class CheckBox(Window):
		def __init__(self):
			Window.__init__(self)

			self.backgroundImage = None
			self.checkImage = None

			self.eventFunc = { "ON_CHECK" : None, "ON_UNCKECK" : None, }
			self.eventArgs = { "ON_CHECK" : None, "ON_UNCKECK" : None, }
			self.enabled = True

			self.CreateElements()

		def __del__(self):
			Window.__del__(self)

			self.backgroundImage = None
			self.checkImage = None

			self.eventFunc = { "ON_CHECK" : None, "ON_UNCKECK" : None, }
			self.eventArgs = { "ON_CHECK" : None, "ON_UNCKECK" : None, }

		def CreateElements(self):
			self.backgroundImage = ImageBox()
			self.backgroundImage.SetParent(self)
			self.backgroundImage.AddFlag("not_pick")
			self.backgroundImage.LoadImage(V31_CONTROL_ROOT + "checkbox/off_01.tga")
			self.backgroundImage.Show()

			self.checkImage = ImageBox()
			self.checkImage.SetParent(self)
			self.checkImage.AddFlag("not_pick")
			self.checkImage.SetPosition(0, 0)
			self.checkImage.LoadImage(V31_CONTROL_ROOT + "checkbox/on_01.tga")
			self.checkImage.Hide()

			self.textInfo = TextLine()
			self.textInfo.SetParent(self)
			self.textInfo.SetPosition(20, -2)
			self.textInfo.Show()

			self.SetSize(self.backgroundImage.GetWidth() + self.textInfo.GetTextSize()[0], self.backgroundImage.GetHeight() + self.textInfo.GetTextSize()[1])

		def SetTextInfo(self, info):
			if self.textInfo:
				self.textInfo.SetText(info)

			self.SetSize(self.backgroundImage.GetWidth() + self.textInfo.GetTextSize()[0], self.backgroundImage.GetHeight() + self.textInfo.GetTextSize()[1])

		def SetCheckStatus(self, flag):
			if flag:
				self.checkImage.Show()
			else:
				self.checkImage.Hide()

		def GetCheckStatus(self):
			if self.checkImage:
				return self.checkImage.IsShow()

			return False

		def SetEvent(self, func, *args) :
			result = (args[0] in self.eventFunc)
			if result:
				self.eventFunc[args[0]] = func
				self.eventArgs[args[0]] = args
			else:
				print("[ERROR] ui.py SetEvent, Can`t Find has_key : %s" % args[0])

		def Disable(self):
			self.enabled = False

		def Enable(self):
			self.enabled = True

		def OnMouseLeftButtonUp(self):
			if not self.enabled:
				return

			if self.checkImage:
				if self.checkImage.IsShow():
					self.checkImage.Hide()

					if self.eventFunc["ON_UNCKECK"]:
						self.eventFunc["ON_UNCKECK"](*self.eventArgs["ON_UNCKECK"])
				else:
					self.checkImage.Show()

					if self.eventFunc["ON_CHECK"]:
						self.eventFunc["ON_CHECK"](*self.eventArgs["ON_CHECK"])

if app.ENABLE_SEND_TARGET_INFO:
	class CheckBoxTarget(Window):
		def __init__(self):
			Window.__init__(self)

			self.checkbox_image = None
			self.check_image = None
			self.text_line = None
			self.check = False

			self.event_func = { "check" : None, "uncheck" : None, }
			self.event_args = { "check" : None, "uncheck" : None, }

			self.__BuildCheckBox()

		def __del__(self):
			Window.__del__(self)

			self.checkbox_image = None
			self.check_image = None
			self.text_line = None
			self.check = False

			self.event_func = { "check" : None, "uncheck" : None, }
			self.event_args = { "check" : None, "uncheck" : None, }

		def __BuildCheckBox(self):
			checkbox_image = ImageBox()
			checkbox_image.SetParent(self)
			checkbox_image.AddFlag("not_pick")
			checkbox_image.LoadImage(V31_CONTROL_ROOT + "checkbox/off_01.tga")
			checkbox_image.Show()
			self.checkbox_image = checkbox_image

			check_image = ImageBox()
			check_image.SetParent(self)
			check_image.AddFlag("not_pick")
			check_image.SetPosition(0, 0)
			check_image.LoadImage(V31_CONTROL_ROOT + "checkbox/on_01.tga")
			check_image.Hide()
			self.check_image = check_image

			text_line = TextLine()
			text_line.SetParent(self)
			text_line.SetPosition(17, -2)
			text_line.Show()
			self.text_line = text_line

			self.SetSize(self.checkbox_image.GetWidth() + self.text_line.GetTextSize()[0], self.checkbox_image.GetHeight() + self.text_line.GetTextSize()[1])

		def SetText(self, text, color = 0):
			if self.text_line:
				self.text_line.SetText(text)
				if color:
					self.text_line.SetPackedFontColor(color)

			self.SetSize(self.checkbox_image.GetWidth() + self.text_line.GetTextSize()[0], self.checkbox_image.GetHeight() + self.text_line.GetTextSize()[1])

		def SetCheckBox(self, check):
			self.check = check
			if check:
				self.check_image.Show()
			else:
				self.check_image.Hide()

		def IsChecked(self):
			return self.check

		def SetEvent(self, func, *args):
			result = (args[0] in self.event_func)
			if result:
				self.event_func[args[0]] = func
				self.event_args[args[0]] = args
			else:
				print("[ERROR] ui.py SetEvent, Can`t Find has_key : %s" % args[0])

		def OnMouseLeftButtonUp(self):
			if self.check != True:
				self.check = True
				self.check_image.Show()

				if self.event_func["check"]:
					self.event_func["check"](*self.event_args["check"])
			else:
				self.check = False
				self.check_image.Hide()

				if self.event_func["uncheck"]:
					self.event_func["uncheck"](*self.event_args["uncheck"])

def MakeSlotBar(parent, x, y, width, height):
	slotBar = SlotBar()
	slotBar.SetParent(parent)
	slotBar.SetSize(width, height)
	slotBar.SetPosition(x, y)
	slotBar.Show()
	return slotBar

def MakeImageBox(parent, name, x, y):
	image = ImageBox()
	image.SetParent(parent)
	image.LoadImage(name)
	image.SetPosition(x, y)
	image.Show()
	return image

def MakeTextLine(parent):
	textLine = TextLine()
	textLine.SetParent(parent)
	textLine.SetWindowHorizontalAlignCenter()
	textLine.SetWindowVerticalAlignCenter()
	textLine.SetHorizontalAlignCenter()
	textLine.SetVerticalAlignCenter()
	if app.WJ_MULTI_TEXTLINE:
		textLine.DisableEnterToken()
	textLine.Show()
	return textLine

def MakeTextLineNew(parent, x, y, text):
	textLine = TextLine()
	textLine.SetParent(parent)
	textLine.SetPosition(x, y)
	textLine.SetText(text)
	textLine.Show()
	return textLine

def MakeRadioButton(parent, x, y, path, up, over, down):
	button = RadioButton()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(path + up)
	button.SetOverVisual(path + over)
	button.SetDownVisual(path + down)
	button.Show()
	return button

def MakeButton(parent, x, y, tooltipText, path, up, over, down):
	button = Button()
	button.SetParent(parent)
	button.SetPosition(x, y)
	button.SetUpVisual(path + up)
	button.SetOverVisual(path + over)
	button.SetDownVisual(path + down)
	button.SetToolTipText(tooltipText)
	button.Show()
	return button

def RenderRoundBox(x, y, width, height, color):
	grp.SetColor(color)
	grp.RenderLine(x+2, y, width-3, 0)
	grp.RenderLine(x+2, y+height, width-3, 0)
	grp.RenderLine(x, y+2, 0, height-4)
	grp.RenderLine(x+width, y+1, 0, height-3)
	grp.RenderLine(x, y+2, 2, -2)
	grp.RenderLine(x, y+height-2, 2, 2)
	grp.RenderLine(x+width-2, y, 2, 2)
	grp.RenderLine(x+width-2, y+height, 2, -2)

def GenerateColor(r, g, b):
	r = float(r) / 255.0
	g = float(g) / 255.0
	b = float(b) / 255.0
	return grp.GenerateColor(r, g, b, 1.0)

def EnablePaste(flag):
	ime.EnablePaste(flag)

def GetHyperlink():
	return wndMgr.GetHyperlink()

RegisterToolTipWindow("TEXT", TextLine)

class WikiRenderTargetUi(WikiWindow):
	def __init__(self, layer = "UI"):
		WikiWindow.__init__(self, layer)
		self.eventDict={}
		self.eventFunc = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}
		self.eventArgs = {"mouse_click" : None, "mouse_over_in" : None, "mouse_over_out" : None}

		self.children = {}
		self.children["totalPos"] = [0, 0]
		self.children["lastPos"] = [0, 0]
		self.children["isDrag"] = False
		self.SetMouseRightButtonDownEvent(__mem_func__(self.RenderMouseRightDown))
		self.SetMouseRightButtonUpEvent(__mem_func__(self.RenderMouseRightUp))

		if app.WIKI_IMPROVEMENTS:
			self.renderIndex = -1

	def Destroy(self):
		self.eventDict={}
		self.eventFunc = 0
		self.eventArgs = 0
		self.renderIndex = 0
	def __del__(self):
		WikiWindow.__del__(self)

	def GetRenderIndex(self):
		return self.renderIndex

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterWikiRenderTarget(self, layer)

	def SetRenderTarget(self, number):
		wndMgr.SetWikiRenderTarget(self.hWnd, number)
		self.renderIndex = number

	def CanCheckMouse(self):
		renderIndex = self.GetRenderIndex()

		if app.WIKI_IMPROVEMENTS and renderIndex == -1:
			return False
		if WikiRenderTarget.IsShow(self.GetRenderIndex()) != 1:
			return False
		if ("isDrag" in self.children):
			return self.children["isDrag"]

	def SetRenderingRect(self, left, top, right, bottom):
		wndMgr.SetRenderingRect(self.hWnd, left, top, right, bottom)

	def SetEvent(self, func, *args):
		result = (args[0] in self.eventFunc)
		if result:
			self.eventFunc[args[0]] = func
			self.eventArgs[args[0]] = args

	def OnUpdate(self):
		if self.CanCheckMouse():
			[currentMousePos, lastPos] = [app.GetCursorPosition(), self.children["lastPos"]]
			totalPos = self.children["totalPos"] if ("totalPos" in self.children) else [0, 0]
			_x = (currentMousePos[0] - lastPos[0]) + totalPos[0]
			_y = (currentMousePos[1] - lastPos[1]) + totalPos[1]
			fNewPitchVelocity = _y * 0.3
			fNewRotationVelocity = _x * 0.3
			WikiRenderTarget.RotateEyeAroundTarget(self.GetRenderIndex(), fNewPitchVelocity, fNewRotationVelocity)
			self.children["totalPos"] = [_x, _y]
			self.children["lastPos"] = currentMousePos

	def RenderMouseRightUp(self):
		app.SetCursor(app.NORMAL)
		self.children["isDrag"] = False
		return True

	def RenderMouseRightDown(self):
		app.SetCursor(app.CAMERA_ROTATE)
		self.children["isDrag"] = True
		self.children["lastPos"] = app.GetCursorPosition()
		return True

	def OnMouseWheel(self, nLen):
		renderIndex = self.GetRenderIndex()

		if app.WIKI_IMPROVEMENTS and renderIndex == -1:
			return False
		if WikiRenderTarget.IsShow(renderIndex) != 1:
			return False
		WikiRenderTarget.Zoom(renderIndex, app.CAMERA_TO_NEGATIVE if nLen > 0 else app.CAMERA_TO_POSITIVE)
		return True

	def OnMouseLeftButtonUp(self) :
		if self.eventFunc["mouse_click"] :
			self.eventFunc["mouse_click"](*self.eventArgs["mouse_click"])

	def OnMouseOverIn(self):
		try:
			if self.eventFunc["mouse_over_in"]:
				if self.eventArgs:
					self.eventFunc["mouse_over_in"](*self.eventArgs["mouse_over_in"])
				else:
					self.eventFunc["mouse_over_in"]()
		except KeyError:
			pass

	def OnMouseOverOut(self):
		try:
			if self.eventFunc["mouse_over_out"]:
				if self.eventArgs:
					self.eventFunc["mouse_over_out"](*self.eventArgs["mouse_over_out"])
				else:
					self.eventFunc["mouse_over_out"]()
		except KeyError:
			pass

class RenderTarget(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)

		self.number = -1

		if app.ENABLE_RENDER_TARGET_PREVIEW:
			self.mouseRightButtonDownEvent = None
			self.mouseRightButtonUpEvent = None
			self.mouseLeftButtonUpEvent = None

	def __del__(self):
		Window.__del__(self)

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.RegisterRenderTarget(self, layer)

	def SetRenderTarget(self, number):
		self.number = number
		wndMgr.SetRenderTarget(self.hWnd, self.number)

	if app.ENABLE_RENDER_TARGET_PREVIEW:
		def OnMouseRightButtonDown(self):
			if self.mouseRightButtonDownEvent:
				self.mouseRightButtonDownEvent()
				
		def OnMouseRightButtonUp(self):
			if self.mouseRightButtonUpEvent:
				self.mouseRightButtonUpEvent()
				
		def OnMouseLeftButtonUp(self):
			if self.mouseLeftButtonUpEvent:
				self.mouseLeftButtonUpEvent()
				
		def SetMouseRightButtonDownEvent(self, event):
			self.mouseRightButtonDownEvent = event
			
		def SetMouseRightButtonUpEvent(self, event):
			self.mouseRightButtonUpEvent = event
			
		def SetMouseLeftButtonUpEvent(self, event):
			self.mouseLeftButtonUpEvent = event

class ExtendedTextLine(Window):

	OBJECT_TYPE_IMAGE = 0
	OBJECT_TYPE_TEXT = 1
	OBJECT_TYPE_HEIGHT = 2
	OBJECT_TYPE_WIDTH = 3

	OBJECT_TAGS = {
		OBJECT_TYPE_IMAGE : "IMAGE",
		OBJECT_TYPE_TEXT : "TEXT",
		OBJECT_TYPE_HEIGHT : "HEIGHT",
		OBJECT_TYPE_WIDTH : "WIDTH",
	}

	def __init__(self):
		Window.__init__(self)

		self.inputText = ""
		self.childrenList = []

		self.limitWidth = 0
		self.x = 0
		self.maxHeight = 0
		self.extraHeight = 0

		self.renderingRect = { "left" : 0, "right" : 0, "top" : 0, "bottom" : 0 }

		self.SetWindowName("NONAME_ExtendedTextLine")

	def __del__(self):
		Window.__del__(self)

	def SetLimitWidth(self, width):
		self.limitWidth = width
		if self.inputText != "":
			self.SetText(self.inputText)

	def IsText(self, text):
		return self.inputText == text

	def SetText(self, text):
		self.childrenList = []
		self.x = 0
		self.maxHeight = 0
		self.extraHeight = 0

		charIndex = 0
		currentWord = ""

		textLine = None

		while charIndex < len(text):
			c = text[charIndex:charIndex+1] 

			# tags
			if c == "<":
				if textLine:
					self.childrenList.append(textLine)
					self.x += textLine.GetTextWidth()
					self.maxHeight = max(self.maxHeight, textLine.GetTextHeight() + 2)
					textLine = None

				tagStart = charIndex
				tagEnd = text[tagStart:].find(">")
				if tagEnd == -1:
					tagEnd = len(text)
				else:
					tagEnd += tagStart

				tagNameStart = charIndex + 1
				tagNameEnd = text[tagNameStart:].find(" ")
				if tagNameEnd == -1 or tagNameEnd > tagEnd:
					tagNameEnd = tagEnd
				else:
					tagNameEnd += tagNameStart
				tag = text[tagNameStart:tagNameEnd]

				content = {}
				tagContentPos = tagNameEnd + 1
				while tagContentPos < tagEnd:
					tagContentStart = -1
					for i in range(tagContentPos, tagEnd):
						if text[i:i+1] != " " and text[i:i+1] != "\t":
							tagContentStart = i
							break
					if tagContentStart == -1:
						break

					tagContentPos = text[tagContentStart:].find("=") + tagContentStart
					tagKey = text[tagContentStart:tagContentPos]

					tagContentPos += 1

					tagContentEnd = -1
					isBreakAtSpace = True
					for i in range(tagContentPos, tagEnd+1):
						if isBreakAtSpace == True and (text[i:i+1] == " " or text[i:i+1] == "\t" or text[i:i+1] == ">"):
							tagContentEnd = i
							break
						elif text[i:i+1] == "\"":
							if isBreakAtSpace == True:
								isBreakAtSpace = False
								tagContentPos = i + 1
							else:
								tagContentEnd = i
								break
					if tagContentEnd == -1:
						break

					tagValue = text[tagContentPos:tagContentEnd]
					content[tagKey] = tagValue

					tagContentPos = text[tagContentEnd:].find(" ")
					if tagContentPos == -1:
						tagContentPos = tagContentEnd
					else:
						tagContentPos += tagContentEnd

				bRet = True
				for key in self.OBJECT_TAGS:
					if self.OBJECT_TAGS[key] == tag.upper():
						bRet = self.__ComputeTag(key, content)
						break

				if bRet == False:
					break

				charIndex = tagEnd + 1
				continue

			# text
			if not textLine:
				textLine = TextLine()
				textLine.SetParent(self)
				textLine.SetPosition(self.x, 0)
				textLine.SetWindowVerticalAlignCenter()
				textLine.SetVerticalAlignCenter()
				textLine.Show()
			subtext = textLine.GetText()
			textLine.SetText(subtext + c)
			if textLine.GetTextWidth() + self.x >= self.limitWidth and self.limitWidth != 0:
				if subtext != "":
					textLine.SetText(subtext)
					self.childrenList.append(textLine)
					self.x += textLine.GetTextWidth()
					self.maxHeight = max(self.maxHeight, textLine.GetTextHeight() + 2)
					textLine = None
				else:
					textLine = None
				break

			# increase char index
			charIndex += 1

		if textLine:
			self.childrenList.append(textLine)
			self.x += textLine.GetTextWidth()
			self.maxHeight = max(self.maxHeight, textLine.GetTextHeight() + 2)
			textLine = None

		self.inputText = text[:charIndex]
		self.SetSize(self.x, self.maxHeight + self.extraHeight)
		self.UpdateRect()

		return charIndex

	def __ComputeTag(self, index, content):
		# tag <IMAGE []>
		if index == self.OBJECT_TYPE_IMAGE:
			if not ("path" in content):
				import dbg
				dbg.TraceError("Cannot read image tag : no path given")
				return False

			image = ImageBox()
			image.SetParent(self)
			image.SetPosition(self.x, 0)
			image.SetWindowVerticalAlignCenter()
			image.LoadImage(content["path"])
			image.Show()

			if ("y" in content):
				image.SetPosition(image.GetLeft(), int(content["y"]))

			if ("align" in content) and content["align"].lower() == "center":
				image.SetPosition(self.limitWidth // 2 - image.GetWidth() // 2, 0)
			else:
				if self.x + image.GetWidth() >= self.limitWidth and self.limitWidth != 0:
					return False
				self.x += image.GetWidth()

			self.childrenList.append(image)
			self.maxHeight = max(self.maxHeight, image.GetHeight())

			return True

		# tag <TEXT []>
		elif index == self.OBJECT_TYPE_TEXT:
			if not ("text" in content):
				import dbg
				dbg.TraceError("Cannot read text tag : no text given")
				return False

			textLine = TextLine()
			textLine.SetParent(self)
			textLine.SetPosition(self.x, 0)
			textLine.SetWindowVerticalAlignCenter()
			textLine.SetVerticalAlignCenter()
			if ("r" in content) and ("g" in content) and ("b" in content):
				textLine.SetFontColor(int(content["r"]) / 255.0, int(content["g"]) / 255.0, int(content["b"]) / 255.0)
			elif ("color" in content):
				textLine.SetPackedFontColor(int(content["color"], 0))
			isLarge = False
			if ("font_size" in content):
				if content["font_size"].lower() == "large":
					isLarge = True
					textLine.SetFontName(localeInfo.UI_DEF_FONT_LARGE)
			if ("bold" in content):
				if content["bold"] == "1" or content["bold"].lower() == "true":
					if isLarge:
						textLine.SetFontName(localeInfo.UI_DEF_FONT_LARGE_BOLD)
					else:
						textLine.SetFontName(localeInfo.UI_DEF_FONT_BOLD)
			if ("outline" in content) and content["outline"] == "1":
				textLine.SetOutline()
			textLine.SetText(content["text"])
			textLine.Show()

			if self.x + textLine.GetTextWidth() >= self.limitWidth and self.limitWidth != 0:
				return False

			self.childrenList.append(textLine)
			self.x += textLine.GetTextWidth()
			self.maxHeight = max(self.maxHeight, textLine.GetTextHeight() + 2)

			return True

		# tag <HEIGHT []>
		elif index == self.OBJECT_TYPE_HEIGHT:
			if not ("size" in content):
				import dbg
				dbg.TraceError("Cannot read height tag : no size given")
				return False

			self.extraHeight += int(content["size"])

			return True

		# tag <WIDTH []>
		elif index == self.OBJECT_TYPE_WIDTH:
			if not ("size" in content):
				import dbg
				dbg.TraceError("Cannot read width tag : no size given")
				return False

			self.x += int(content["size"])

			return True

		return False

	def SetRenderingRect(self, left, top, right, bottom):
		self.renderingRect = {
			"left" : max(0, min(self.GetWidth(), int(-left * self.GetWidth()))),
			"top" : max(0, min(self.GetHeight(), int(-top * self.GetHeight()))),
			"right" : max(0, min(self.GetWidth(), int(-right * self.GetWidth()))),
			"bottom" : max(0, min(self.GetHeight(), int(-bottom * self.GetHeight()))),
		}

		self.__ApplyRenderingRect()

	def __ApplyRenderingRect(self):
		for child in self.childrenList:
			(x, y) = child.GetLocalPosition()
			childHeight = child.GetHeight()
			if isinstance(child, TextLine):
				childHeight = child.GetTextHeight()
			yEnd = y + childHeight

			renderTop = max(0, self.renderingRect["top"] - y)
			renderBottom = max(0, self.renderingRect["bottom"] - (self.GetHeight() - yEnd))

			child.SetRenderingRect(0, -float(renderTop) / childHeight, 0, -float(renderBottom) / childHeight)
	
	def GetTextHeight(self):
		for child in self.childrenList:
			if isinstance(child, TextLine):
				return child.GetTextHeight()
		
		return 0

	def GetTextWidth(self):
		for child in self.childrenList:
			if isinstance(child, TextLine):
				return child.GetTextWidth()
		
		return 0

class Graph(Window):

	def __init__(self):
		Window.__init__(self)

		self.yMinValue = 0.0
		self.yMaxValue = 100.0
		self.xMinValue = 0.0
		self.xMaxValue = 10.0

		self.renderColor = grp.GenerateColor(1.0, 0.0, 0.0, 1.0)

		self.keyList = []
		self.valueList = []

	def SetYAxisLimitValue(self, minValue, maxValue):
		self.yMinValue = float(minValue)
		self.yMaxValue = float(maxValue)

	def SetXAxisLimitValue(self, minValue, maxValue):
		self.xMinValue = float(minValue)
		self.xMaxValue = float(maxValue)

	def Clear(self):
		self.keyList = []
		self.valueList = []

	def AddValue(self, xAxisPosition, yAxisValue):
		xAxisPosition = float(xAxisPosition)
		yAxisValue = float(yAxisValue)

		if xAxisPosition in self.keyList:
			import dbg
			dbg.TraceError("Cannot add value to bar graph : already existing xAxisPosition (" + str(xAxisPosition) + ", " + str(yAxisValue) + ")")
			return

		self.keyList.append(xAxisPosition)
		self.valueList.append({ "x" : xAxisPosition, "y" : yAxisValue })

	def Refresh(self):
		self.valueList = sorted(self.valueList, key = lambda val: val["x"])

	def SetColor(self, color):
		self.renderColor = color

	def OnRender(self):
		grp.SetColor(self.renderColor)

class LineGraph(Graph):

	def __init__(self):
		Graph.__init__(self)

		self.lineThickness = 1

		self.lastOverPos = -1
		self.overEvent = None
		self.outEvent = None

	def SetLineThickness(self, thickness):
		self.lineThickness = thickness

	def SetOverLineEvent(self, event):
		self.overEvent = event

	def SetOutLineEvent(self, event):
		self.outEvent = event

	def __GetYPosition(self, xPosition):
		if xPosition < 0 or xPosition >= self.GetWidth():
			return -1

		width = float(self.GetWidth())
		height = float(self.GetHeight())
		valueXRange = self.xMaxValue - self.xMinValue
		valueYRange = self.yMaxValue - self.yMinValue

		lastPos = (0, 0)
		for data in self.valueList:
			renderX = int((data["x"] - self.xMinValue) / valueXRange * width)
			renderY = int((data["y"] - self.yMinValue) / valueYRange * height)

			if xPosition >= lastPos[0] and xPosition <= renderX:
				factor = 1.0
				if renderX - lastPos[0] > 0:
					factor = (xPosition - lastPos[0]) / float(renderX - lastPos[0])

				mouseRenderY = int(factor * (renderY - lastPos[1]) + lastPos[1])
				return self.GetHeight() - mouseRenderY

			lastPos = (renderX, renderY)

		return -1

	def __GetValueByXPos(self, xPosition):
		if xPosition < 0 or xPosition >= self.GetWidth():
			return -1

		width = float(self.GetWidth())
		height = float(self.GetHeight())
		valueXRange = self.xMaxValue - self.xMinValue
		valueYRange = self.yMaxValue - self.yMinValue

		lastPos = (0, 0, 0)
		for data in self.valueList:
			renderX = int((data["x"] - self.xMinValue) / valueXRange * width)
			renderY = int((data["y"] - self.yMinValue) / valueYRange * height)

			if xPosition >= lastPos[0] and xPosition <= renderX:
				factor = 1.0
				if renderX - lastPos[0] > 0:
					factor = (xPosition - lastPos[0]) / float(renderX - lastPos[0])

				return self.yMinValue + ((lastPos[2] - self.yMinValue) * (1.0 - factor) + (data["y"] - self.yMinValue) * factor)

			lastPos = (renderX, renderY, data["y"])

		return -1

	def __RenderElem(self, data, lastXPos, lastYPos):
		(x, y) = self.GetGlobalPosition()

		width = float(self.GetWidth())
		height = float(self.GetHeight())
		valueXRange = self.xMaxValue - self.xMinValue
		valueYRange = self.yMaxValue - self.yMinValue

		renderX = lastXPos
		renderY = lastYPos
		renderEndX = int((data["x"] - self.xMinValue) / valueXRange * width)
		renderEndY = int((data["y"] - self.yMinValue) / valueYRange * height)

		if renderX < renderEndX:
			renderWidth = renderEndX - renderX
			renderHeight = renderEndY - renderY

			for i in range(self.lineThickness):
				change = (i + 1) // 2
				if i % 2 == 0:
					grp.RenderLine(x + renderX, y + height - renderY - change, renderWidth, -renderHeight)
				else:
					grp.RenderLine(x + renderX, y + height - renderY + change, renderWidth, -renderHeight)

		return (renderEndX, renderEndY)

	def OnRender(self):
		Graph.OnRender(self)

		lastPos = (0, 0)
		for data in self.valueList:
			lastPos = self.__RenderElem(data, lastPos[0], lastPos[1])

	def OnUpdate(self):
		if self.IsIn():
			(xMouse, yMouse) = self.GetMouseLocalPosition()
			for i in range(4 + 3 * self.lineThickness):
				xAdjust = (i + 1) // 2
				if i % 2 == 0:
					xAdjust = -xAdjust

				y = self.__GetYPosition(xMouse + xAdjust)
				if abs(yMouse - y) < 10:
					if xMouse != self.lastOverPos:
						self.lastOverPos = xMouse
						if self.overEvent:
							self.overEvent(xMouse, y, self.__GetValueByXPos(xMouse))
					return

		if self.lastOverPos != -1:
			self.lastOverPos = -1
			if self.outEvent:
				self.outEvent()

class BarGraph(Graph):

	def __init__(self):
		Graph.__init__(self)

		self.barSpace = 1

	def SetBarSpace(self, space):
		self.barSpace = int(space)

	def __RenderElem(self, data, endXValue, addSpace = True):
		(x, y) = self.GetGlobalPosition()

		width = self.GetWidth()
		height = self.GetHeight()
		valueXRange = self.xMaxValue - self.xMinValue
		valueYRange = self.yMaxValue - self.yMinValue

		renderX = int((data["x"] - self.xMinValue) / valueXRange * width)
		renderY = 0
		renderWidth = int((endXValue - data["x"]) / valueXRange * width)
		renderHeight = int((data["y"] - self.yMinValue) / valueYRange * height)

		if addSpace:
			renderWidth -= self.barSpace

		if renderWidth > 0.0 and renderHeight > 0.0:
			grp.RenderBar(x + renderX, y + renderY + height - renderHeight, renderWidth, renderHeight)

	def OnRender(self):
		Graph.OnRender(self)

		lastPair = { "x" : self.xMinValue, "y" : self.yMinValue }
		for data in self.valueList:
			self.__RenderElem(lastPair, data["x"])
			lastPair = data

		self.__RenderElem(lastPair, self.xMaxValue, False)


class MultiTextLine(Window):

	RETURN_STRING = "[ENTER]"
	LINE_HEIGHT = 15

	def __init__(self):
		Window.__init__(self)

		self.isSetFontColor = False
		self.r = 0.0
		self.g = 0.0
		self.b = 0.0
		self.packedFontColor = -1
		self.textColorDict = {}

		self.lines = []
		self.hAlignCenter = False
		self.vAlignCenter = False
		self.windowVAlignCenter = False
		self.isOutline = False
		self.text = ""
		self.basePos = 0
		self.maxTextWidth = 0
		self.realX = 0
		self.realY = 0

		self.SetWindowName("NONAME_MultiTextLine")

	def __del__(self):
		Window.__del__(self)

	def SetWidth(self, width):
		self.SetSize(width, self.GetHeight())
		self.SetText(self.GetText())

	def SetHeight(self, height):
		self.SetSize(self.GetWidth(), height)
		self.SetText(self.GetText())

	def RegisterPackedFontColor(self, name, color):
		self.textColorDict[name] = color

	def SetRegisteredColor(self, name):
		if (name in self.textColorDict):
			self.SetPackedFontColor(self.textColorDict[name])

	def SetAlpha(self, alpha):
		for line in self.lines:
			line.SetAlpha(alpha)

	def NewTextLine(self):
		line = TextLine()
		line.xRect = 0.0
		line.SetParent(self)
		if self.hAlignCenter == True:
			line.SetWindowHorizontalAlignCenter()
			line.SetHorizontalAlignCenter()
		if self.vAlignCenter == True:
			line.SetVerticalAlignCenter()
		if self.isSetFontColor == True:
			if self.packedFontColor != -1:
				line.SetPackedFontColor(self.packedFontColor)
			else:
				line.SetFontColor(self.r, self.g, self.b)
		if self.isOutline == True:
			line.SetOutline()
		line.Show()
		self.lines.append(line)

		return self.lines[len(self.lines) - 1]

	def Clear(self):
		self.text = ""
		self.lines = []

	def SetTextHorizontalAlignCenter(self):
		self.hAlignCenter = True
		self.SetText(self.GetText())

	def SetTextVerticalAlignCenter(self):
		self.vAlignCenter = True
		self.SetText(self.GetText())

	def SetOutline(self):
		self.isOutline = True
		self.SetText(self.GetText())

	def SetFontColor(self, r, g, b):
		self.isSetFontColor = True
		self.r = r
		self.g = g
		self.b = b

	def SetPackedFontColor(self, color, lineIdx=-1):
		if lineIdx == -1:
			self.isSetFontColor = True
			self.packedFontColor = color
			for line in self.lines:
				line.SetPackedFontColor(color)
		else:
			self.lines[lineIdx].SetPackedFontColor(color)

	def SetText(self, text):
		self.Clear()

		self.text = text
		self.maxTextWidth = 0

		line = self.NewTextLine()
		pos = 0
		newStartPos = 0
		while pos < len(text):
			curTextWidth = line.GetSpecificTextWidth(text[:pos+1])
			#line.SetText(text[:pos+1])

			newLine = False
			if len(text) >= pos + len(self.RETURN_STRING):
				if text[pos:pos+len(self.RETURN_STRING)] == self.RETURN_STRING:
					newLine = True
					newStartPos = pos+len(self.RETURN_STRING)
			if newLine == False and pos > 0:
				if curTextWidth > self.GetWidth() and self.GetWidth() > 0:
					newLine = True

					curText = text[:pos+1]
					breakPos = curText.rfind(" ")
					if breakPos == -1:
						if curText.find("|Hlink:") != -1:
							newLine = False
						else:
							breakPos = curText.rfind(".")
							if breakPos == -1:
								breakPos = curText.rfind(",")
								if breakPos == -1:
									breakPos = curText.rfind(";")
									if breakPos == -1:
										breakPos = curText.rfind(":")
							if breakPos != -1:
								breakPos += 1
					if breakPos != -1:
						pos = breakPos
						newStartPos = pos
					else:
						newStartPos = pos

			if newLine == True:
				line.SetText(text[:pos])
				curTextWidth = line.GetTextWidth()
#				if line.GetTextWidth() > self.GetWidth() and self.GetWidth() > 0:
#					line.ShowPercentage(0.0, 1.0 - (line.GetTextWidth() - self.GetWidth()) / float(line.GetTextWidth()))
#					line.xRect = -(line.GetTextWidth() - self.GetWidth()) / float(line.GetTextWidth())

				line = self.NewTextLine()
				text = text[newStartPos:]
				if text[:1] == " ":
					text = text[1:]
				pos = 0
			else:
				pos += 1
				if pos >= len(text):
					pass
#					if line.GetTextWidth() > self.GetWidth() and self.GetWidth() > 0:
#						line.ShowPercentage(0.0, 1.0 - (line.GetTextWidth() - self.GetWidth()) / float(line.GetTextWidth()))
#						line.xRect = -(line.GetTextWidth() - self.GetWidth()) / float(line.GetTextWidth())

			self.maxTextWidth = max(self.maxTextWidth, curTextWidth)
			if self.GetWidth() > 0 and self.maxTextWidth > self.GetWidth():
				self.maxTextWidth = self.GetWidth()

		line.SetText(text)

		self.ShowBetween(self.GetLineCount() - self.GetViewLineCount(), self.GetLineCount() - 1)
		#self.SetSize(self.GetWidth(), len(self.lines) * self.LINE_HEIGHT)

		self.SetPosition(self.realX, self.realY)

	def GetMaxTextWidth(self):
		return self.maxTextWidth

	def GetLine(self, index):
		if index < 0 or index >= len(self.lines):
			return None
		return self.lines[index]

	def GetLastLine(self):
		return self.GetLine(len(self.lines) - 1)

	def GetLineCount(self):
		return len(self.lines)

	def GetViewLineCount(self):
		if self.GetHeight() == 0:
			return self.GetLineCount()
		return self.GetHeight() // self.LINE_HEIGHT

	def SetBasePos(self, basePos):
		self.basePos = basePos

		self.ShowBetween(self.basePos, self.basePos + self.GetViewLineCount() - 1)

	def GetBasePos(self):
		return self.basePos

	def ShowBetween(self, start, end):
		start = max(0, start)
		end = min(self.GetLineCount() - 1, end)

		height = self.GetHeight()
		if height == 0:
			height = self.GetLineCount() * self.LINE_HEIGHT

		for i in range(len(self.lines)):
			if i < start or i > end:
				self.lines[i].Hide()
			else:
				self.lines[i].SetPosition(0, (i - start) * self.LINE_HEIGHT)
				self.lines[i].Show()

	def GetRealHeight(self):
		if self.GetHeight() > 0:
			return self.GetHeight()

		return self.GetLineCount() * self.LINE_HEIGHT

	def SetWindowVerticalAlignCenter(self):
		Window.SetWindowVerticalAlignCenter(self)
		self.windowVAlignCenter = True

		if self.GetHeight() == 0:
			self.SetPosition(self.realX, self.realY)

	def SetPosition(self, x, y):
		self.realX = x
		self.realY = y
		if self.windowVAlignCenter and self.GetHeight() == 0:
			Window.SetPosition(self, x, y - self.GetRealHeight() // 2)
		else:
			Window.SetPosition(self, x, y)

	def GetBottom(self):
		return self.GetTop() + self.GetRealHeight()

	def GetText(self):
		return self.text

	def SetYRenderingRect(self, sy, ey):
		sy = max(0, sy)
		ey = min(self.GetRealHeight(), ey)

		for i in range(len(self.lines)):
			line = self.lines[i]
			if sy >= line.GetBottom() or ey <= line.GetTop() or ey <= sy:
				line.SetRenderingRect(0.0, 0.0, line.xRect, -1.0)
			elif line.GetTextHeight() > 0:
				line.SetRenderingRect(0.0, -min(1.0, float(max(0, sy - line.GetTop())) / line.GetTextHeight()), line.xRect, max(-1.0, float(min(0, ey - line.GetTop() - line.GetTextHeight())) / line.GetTextHeight()))

class SelectableTextLine(TextLine):

	STATE_NONE = 0
	STATE_OVER = 1
	STATE_DOWN = 2

	def __init__(self, autoResize = True):
		TextLine.__init__(self)

		self.autoResize = autoResize
		self.state = self.STATE_NONE
		self.clickEvent = lambda: None

		self.SetOverBackground(HALF_WHITE_COLOR)
		self.SetDownBackground(WHITE_COLOR)

	def SetEvent(self, event):
		self.clickEvent = event

	def SetOverBackground(self, color):
		self.overBackground = color

	def SetDownBackground(self, color):
		self.downBackground = color

	def SetText(self, text):
		TextLine.SetText(self, text)

		if self.autoResize:
			self.SetSize(self.GetTextWidth(), self.GetTextHeight())

	def OnMouseOverIn(self):
		self.state = self.STATE_OVER

	def OnMouseOverOut(self):
		self.state = self.STATE_NONE

	def OnMouseLeftButtonDown(self):
		self.state = self.STATE_DOWN

	def OnMouseLeftButtonUp(self):
		if self.state == self.STATE_DOWN:
			self.clickEvent()

		if self.IsIn():
			self.state = self.STATE_OVER
		else:
			self.state = self.STATE_NONE

	def OnRender(self):
		if self.state == self.STATE_NONE:
			return

		if self.state == self.STATE_OVER:
			grp.SetColor(self.overBackground)
		elif self.state == self.STATE_DOWN:
			grp.SetColor(self.downBackground)

		(x, y) = self.GetGlobalPosition()
		grp.RenderBar(x, y, self.GetWidth(), self.GetHeight())

class RenderBox(Window):
	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.color = 0xFF000000

	def __del__(self):
		Window.__del__(self)
		self.color = 0xFF000000

	def RegisterWindow(self, layer):
		self.hWnd = wndMgr.Register(self, layer)

	def SetColor(self, color):
		self.color = color

	def OnRender(self):
		(x, y, width, height) = self.GetRect()
		grp.SetColor(self.color)
		grp.RenderBar(x, y, width, height)

if app.ENABLE_BATTLE_PASS:
	def AddTextLine(parent, x, y, text):
		textLine = TextLine()
		textLine.SetParent(parent)
		textLine.SetPosition(x, y)
		textLine.SetText(text)
		textLine.DisableEnterToken()
		textLine.Show()
		return textLine

	def MakeNewTextLine(parent, horizontalAlign = True, verticalAlgin = True, x = 0, y = 0):
		textLine = TextLine()
		textLine.SetParent(parent)

		if horizontalAlign == True:
			textLine.SetWindowHorizontalAlignCenter()

		if verticalAlgin == True:
			textLine.SetWindowVerticalAlignCenter()

		textLine.SetHorizontalAlignCenter()
		textLine.SetVerticalAlignCenter()
		textLine.DisableEnterToken()

		if x != 0 and y != 0:
			textLine.SetPosition(x, y)

		textLine.Show()
		return textLine

	def MakeExpandedImageBox(parent, name, x, y, flag = ""):
		image = ExpandedImageBox()
		image.SetParent(parent)
		image.LoadImage(name)
		image.SetPosition(x, y)

		if flag != "":
			image.AddFlag(flag)

		image.Show()

		return image

	def MakeThinBoardCircle(parent, x, y, width, heigh, text, bnsId = 0):
		thin = ThinBoardCircle()
		thin.SetParent(parent)
		thin.SetSize(width, heigh)
		thin.SetPosition(x, y)
		thin.Show()
		return thin

if app.ENABLE_EXCHANGE_LOG:
	class ListBoxNew(Window):
		def __del__(self):
			Window.__del__(self)
		def Destroy(self):
			for item in self.itemList:
				item.Destroy()
			self.itemList=[]
			self.scrollBar=None
			self.basePos=0
			self.scrollLen=0
			self.scrollLenExtra=0
			self.isHorizontal= 0
		def __init__(self, isHorizontal = False):
			Window.__init__(self)
			self.itemList=[]
			self.Destroy()
			self.isHorizontal= isHorizontal
		def RemoveAllItems(self):
			for item in self.itemList:
				item.Destroy()
			self.itemList=[]
			if self.scrollBar:
				self.scrollBar.SetPos(0)
			self.RefreshAll()
		def SetExtraScrollLen(self, extraLen):
			self.scrollLenExtra=extraLen
		def GetItems(self):
			return self.itemList
		def AppendItem(self, newItem):
			self.itemList.append(newItem)
			self.RefreshAll()
		def SetScrollBar(self, scrollBar):
			scrollBar.SetScrollEvent(__mem_func__(self.__OnScroll))
			self.scrollBar=scrollBar
		def OnMouseWheel(self, nLen):
			if self.scrollBar:
				if self.scrollBar.IsShow():
					if nLen > 0:
						self.scrollBar.OnUp()
					else:
						self.scrollBar.OnDown()
					return True
			return False
		def __OnScroll(self):
			self.SetBasePos(int(self.scrollBar.GetPos()*self.scrollLen))
		def RefreshAll(self):
			windowHeight = self.GetHeight()
			scrollBar = self.scrollBar
			screenSize = 0
			for child in self.itemList:
				if child.exPos[1]+child.GetHeight() > screenSize:
					screenSize = child.exPos[1]+child.GetHeight()
			if screenSize > windowHeight:
				scrollLen = screenSize-windowHeight
				if scrollLen != 0:
					scrollLen += self.scrollLenExtra
				self.scrollLen = scrollLen
				scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(screenSize))
			else:
				scrollBar.SetMiddleBarSize(1.0)
		def Render(self,basePos):
			for item in self.itemList:
				(ex,ey) = item.exPos
				if self.isHorizontal:
					item.SetPosition(ex-(basePos), ey)
				else:
					item.SetPosition(ex, ey-(basePos))
				item.OnRender()
		def SetBasePos(self, basePos):
			if self.basePos == basePos:
				return
			self.Render(basePos)
			self.basePos=basePos

class InvisibleBoard(Window):
	CORNER_WIDTH = 32
	CORNER_HEIGHT = 32
	LINE_WIDTH = 128
	LINE_HEIGHT = 128

	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3


	def __init__(self, layer = "UI"):
		Window.__init__(self, layer)
		self.skipMaxCheck = False

		self.MakeBoard()
		
	def MakeBoard(self):
		self.Corners = []
		self.Lines = []
		self.Base = None

	def __del__(self):
		Window.__del__(self)

	def SetSize(self, width, height):
		if not self.skipMaxCheck:
			width = max(self.CORNER_WIDTH*2, width)
			height = max(self.CORNER_HEIGHT*2, height)
			
		Window.SetSize(self, width, height)

class MouseReflector(Window):
	def __init__(self, parent):
		Window.__init__(self)
		self.SetParent(parent)
		self.AddFlag("not_pick")
		self.width = self.height = 0
		self.isDown = False
		
	def __del__(self):
		Window.__del__(self)
		
	def Down(self):
		self.isDown = True
		
	def Up(self):
		self.isDown = False
		
	def OnRender(self):
		if self.isDown:
			grp.SetColor(WHITE_COLOR)
		else:
			grp.SetColor(HALF_WHITE_COLOR)
		x, y = self.GetGlobalPosition()
		grp.RenderBar(x + 2, y + 2, self.GetWidth() - 4, self.GetHeight() - 4)

class CheckBoxNew(ImageBox):
	def __init__(self, parent, x, y, event, filename = V31_CONTROL_ROOT + "checkbox/wide_off_01.tga"):
		ImageBox.__init__(self)
		self.SetParent(parent)
		self.SetPosition(x, y)
		self.LoadImage(filename)
		self.mouseReflector = MouseReflector(self)
		self.mouseReflector.SetSize(self.GetWidth(), self.GetHeight())
		image = MakeImageBox(self, V31_CONTROL_ROOT + "checkbox/wide_on_01.tga", 0, 0)
		image.AddFlag("not_pick")
		image.SetWindowHorizontalAlignCenter()
		image.SetWindowVerticalAlignCenter()
		image.Hide()
		self.check = False
		self.enable = True
		self.image = image
		self.event = event
		self.Show()
		self.mouseReflector.UpdateRect()
		
	def __del__(self):
		ImageBox.__del__(self)
		
	def GetCheck(self):
		return self.check
		
	def SetCheck(self, flag):
		if flag:
			self.check = True
			self.image.Show()
		else:
			self.check = False
			self.image.Hide()
			
	def Disable(self):
		self.enable = False
		
	def OnMouseOverIn(self):
		if not self.enable:
			return
		self.mouseReflector.Show()
		
	def OnMouseOverOut(self):
		if not self.enable:
			return
		self.mouseReflector.Hide()
		
	def OnMouseLeftButtonDown(self):
		if not self.enable:
			return
		self.mouseReflector.Down()
		
	def OnMouseLeftButtonUp(self):
		if not self.enable:
			return
		self.mouseReflector.Up()
		self.event()

if app.ENABLE_AUTO_FARM_METIN:
	class MultiTextLine2(Window):
		def __del__(self):
			Window.__del__(self)
		def Destroy(self):
			self.textRules = {}
		def __init__(self):
			Window.__init__(self)
			self.Destroy()
			self.AddFlag("not_pick")
			self.textRules["textRange"] = 15
			self.textRules["text"] = ""
			self.textRules["textType"] = ""
			self.textRules["fontName"] = ""
			self.textRules["hexColor"] = 0
			self.textRules["fontColor"] = 0
			self.textRules["outline"] = 0
		def SetTextType(self, textType):
			self.textRules["textType"] = textType
			self.Refresh()
		def SetTextRange(self, textRange):
			self.textRules["textRange"] = textRange
			self.Refresh()
		def SetOutline(self, outline):
			self.textRules["outline"] = outline
			self.Refresh()
		def SetPackedFontColor(self, hexColor):
			self.textRules["hexColor"] = hexColor
			self.Refresh()
		def SetFontColor(self, r, g, b):
			self.textRules["fontColor"] =[r, g, b]
			self.Refresh()
		def SetFontName(self, fontName):
			self.textRules["fontName"] = fontName
			self.Refresh()
		def SetText(self, newText):
			self.textRules["text"] = newText
			self.Refresh()
		def Refresh(self):
			textRules = self.textRules
			if textRules["text"] == "":
				return
			self.children=[]
			outline = textRules["outline"]
			fontColor = textRules["fontColor"]
			hexColor = textRules["hexColor"]
			yRange = textRules["textRange"]
			fontName = textRules["fontName"]
			textTypeList = textRules["textType"].split("?")
			#textType = textRules["textType"].split("#")
			totalTextList = textRules["text"].split("#")

			(xPosition, yPosition) = (0, 0)
			width = 0
			for text in totalTextList:
				childText = TextLine()
				childText.SetParent(self)
				childText.AddFlag("not_pick")
				childText.SetPosition(xPosition, yPosition)
				if fontName != "":
					childText.SetFontName(fontName)
				if hexColor != 0:
					childText.SetPackedFontColor(hexColor)
				if fontColor != 0:
					childText.SetFontColor(*fontColor)
				if outline:
					childText.SetOutline()
				for textType in textTypeList:
					self.AddTextType(childText, textType.split("#"))
				childText.SetText(str(text))
				if childText.GetTextSize()[0] > width:
					width = childText.GetTextSize()[0]
				childText.Show()
				self.children.append(childText)
				yPosition+=yRange

		def AddTextType(self, text,  typeArg):
			if len(typeArg) != 2:
				return
			_typeDict = {
				"vertical": {
					"top":text.SetVerticalAlignTop,
					"bottom":text.SetVerticalAlignBottom,
					"center":text.SetVerticalAlignCenter,
				},
				"horizontal": {
					"left":text.SetHorizontalAlignLeft,
					"right":text.SetHorizontalAlignRight,
					"center":text.SetHorizontalAlignCenter,
				},
				"all_align": {
					"1" : [text.SetHorizontalAlignCenter,text.SetVerticalAlignCenter,text.SetWindowHorizontalAlignCenter,text.SetWindowVerticalAlignCenter],
				},
			}
			(firstToken, secondToken) = tuple(typeArg)
			if (firstToken in _typeDict):
				textType = _typeDict[firstToken][secondToken] if (secondToken in _typeDict[firstToken]) else None
				if textType != None:
					if isinstance(textType, list):
						for rule in textType:
							rule()
					else:
						textType()

if app.ENABLE_WINDOW_RESIZE:
	def IsDependOnScreen(expr):
		if not isinstance(expr, Expr):
			return False

		if expr.name in ("SCREEN_WIDTH", "SCREEN_HEIGHT"):
			return True

		return (IsDependOnScreen(expr.left) or IsDependOnScreen(expr.right))

	def ScanValue(value):
		if isinstance(value, Expr):
			return IsDependOnScreen(value)
		elif isinstance(value, (tuple, list)):
			for v in value:
				if ScanValue(v):
					return True
		return False

	def CheckPair(dic, x, y):
		x = dic.get(x)
		y = dic.get(y)

		if x is None or y is None:
			return None

		if (ScanValue(x) or ScanValue(y)):
			return (x, y)

		return None

	def ExtractWindowScaling(dic):
		scaling = {}

		position = CheckPair(dic, "x", "y")
		if position:
			scaling["position"] = position

		size = CheckPair(dic, "width", "height")
		if size:
			scaling["size"] = size

		scale = CheckPair(dic, "x_scale", "y_scale")
		if scale:
			scaling["scale"] = scale

		rect = dic.get("rect")
		if rect and ScanValue(rect):
			scaling["rect"] = rect

		return scaling

	def SandboxInt(x):
		if isinstance(x, Expr):
			return Expr(op="int", left=x)
		return int(x)

	def SandboxFloat(x):
		if isinstance(x, Expr):
			return Expr(op="float", left=x)
		return float(x)

def MakeText(parent, textlineText, x, y, color):
	textline = TextLine()
	if parent:
		textline.SetParent(parent)
	textline.SetPosition(x, y)
	if color:
		textline.SetFontColor(color[0], color[1], color[2])
	textline.SetText(textlineText)
	textline.Show()
	return textline
