import time
import dbg


class Timer:
	def __init__(self, phase):
		self.phase = phase
		self.started = self.previous = time.perf_counter()

	def Mark(self, stage):
		now = time.perf_counter()
		elapsed = (now - self.previous) * 1000.0
		if elapsed >= 10.0:
			dbg.TraceError("CLIENT_INIT_UI phase=%s stage=%s ms=%.3f" %
				(self.phase, stage, elapsed))
		self.previous = time.perf_counter()

	def Finish(self):
		dbg.TraceError("CLIENT_INIT_UI phase=%s stage=total ms=%.3f" %
			(self.phase, (time.perf_counter() - self.started) * 1000.0))
