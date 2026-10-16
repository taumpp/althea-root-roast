class LoadingProgressModel(object):
	FALLBACK_MIN = 12
	FALLBACK_MAX = 88

	def __init__(self):
		self.Reset()

	def Reset(self):
		self.display = 0
		self.target = 0

	def Step(self, nativeValue, now):
		if nativeValue is None:
			width = self.FALLBACK_MAX - self.FALLBACK_MIN
			phase = int(max(0.0, float(now)) * 32.0) % (width * 2)
			offset = phase if phase <= width else width * 2 - phase
			return self.FALLBACK_MIN + offset

		try:
			value = max(0, min(100, int(nativeValue)))
		except (TypeError, ValueError, OverflowError):
			return self.Step(None, now)
		self.target = max(self.target, value)
		delta = self.target - self.display
		if delta > 0:
			self.display += max(1, (delta + 4) // 5)
			self.display = min(self.display, self.target)
		return self.display
