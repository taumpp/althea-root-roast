import grp
import ui
import wndMgr
import app

class PhaseCurtain(ui.Bar):
	def __init__(self):
		#print "NEW CURTAIN -----------------------------------------------------------------------------"
		ui.Bar.__init__(self, "CURTAIN")
		if getattr(wndMgr, "IME_RETURN_PRIORITY", 0) == 1:
			self.AddFlag("ime_return_priority")
		self.speed = 0.1
		self.curAlpha = 0.0
		self.event = 0
		self.args = -1
		self.FadeInFlag = False
		# A positive duration makes FadeIn wall-clock based instead of
		# frame based, so a slow or background frame rate cannot stretch it.
		self.fadeInDuration = 0.0
		self.fadeInStartTime = 0.0
		self.fadeInStartAlpha = 0.0
		self.SetWindowName("PhaseCurtain")
		self.AddFlag("float")

	def OnIMEReturn(self):
		return True

	def __del__(self):
		#print "---------------------------------------------------------------------------- DELETE CURTAIN"
		ui.Bar.__del__(self)

	def SAFE_FadeOut(self, event, args = -1):
		self.FadeOut(ui.__mem_func__(event), args)

	def FadeOut(self, event, args = -1):
		self.fadeInDuration = 0.0
		self.curAlpha = 0.0
		self.SetAlpha(self.curAlpha)
		#self.SetTop()
		self.Show()
		self.event = event
		self.args = args

	def FadeIn(self, duration = 0.0):
		self.event = 0
		self.FadeInFlag = True
		self.fadeInDuration = max(0.0, float(duration))
		if self.fadeInDuration > 0.0:
			self.fadeInStartTime = app.GetTime()
			self.fadeInStartAlpha = self.curAlpha

	def CoverInstantly(self):
		self.event = 0
		self.args = -1
		self.FadeInFlag = False
		self.fadeInDuration = 0.0
		self.curAlpha = 1.0
		self.SetAlpha(self.curAlpha)
		self.Show()

	def HideInstantly(self):
		self.event = 0
		self.args = -1
		self.FadeInFlag = False
		self.fadeInDuration = 0.0
		self.curAlpha = 0.0
		self.SetAlpha(self.curAlpha)
		self.Hide()

	def SetAlpha(self, alpha):
		self.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())

		color = grp.GenerateColor(0.0, 0.0, 0.0, alpha)
		self.SetColor(color)

	def OnUpdate(self):
		if 0 != self.event:
			self.curAlpha += self.speed
			if self.curAlpha >= 1.0:
				self.curAlpha = 1.0

				# 이벤트 중간에 멈출경우를 대비해 미리 제거
				event=self.event
				self.event = 0

				#print "페이드 아웃 완료 이벤트 실행"

				if -1 != self.args:
					event(self.args)
				else:
					event()

		elif True == self.FadeInFlag:
			if self.fadeInDuration > 0.0:
				elapsed = max(0.0, app.GetTime() - self.fadeInStartTime)
				progress = min(1.0, elapsed / self.fadeInDuration)
				self.curAlpha = self.fadeInStartAlpha * (1.0 - progress)
			else:
				self.curAlpha -= self.speed
			if self.curAlpha <= 0.0:
				self.curAlpha = 0.0
				self.eventFadeIn = 0
				self.FadeInFlag = False
				self.fadeInDuration = 0.0
				self.Hide()

		self.SetAlpha(self.curAlpha)
