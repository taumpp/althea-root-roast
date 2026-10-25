# -*- coding: utf-8 -*-
"""State machine of the server-driven warp curtain (seamless warp v1).

The source server announces a transfer (WarpBegin), the EXE reconnects
without Python phase windows while the game window survives, and the
destination answers the arrival (WarpEnd). The curtain fades in, holds until
the destination is ready, waits until the new world renders smoothly for this
machine (frame times relative to its own in-game baseline before the warp,
see TUNING) and fades out. Pure Python and time-injected so ci/tests can run
it headless; root/uiwarpcurtain.py draws it. See docs/FEATURE_INVARIANTS.md
("Seamless warp curtain").
"""

# Every curtain tunable lives here and nowhere else: the model reads only
# this dict and ci/tests pin the defaults. Times are seconds, frame
# times milliseconds.
TUNING = {
	"world_ready_seconds": 0.05,
	"ready_fade_out_seconds": 0.05,
	# Opening fade (ease-out).
	"fade_in_seconds": 0.3,
	# GC_WARP arrived while fading in: the old world disappears on the next
	# handshake, so the remaining fade is compressed to this.
	"hurry_seconds": 0.08,
	# Closing fade (smoothstep). 0.25 -> 0.15 (owner decision 2026-10-05):
	# the world is already ready when it starts, so it is pure waiting.
	"fade_out_seconds": 0.15,
	# After ENTERGAME the destination's WarpEnd normally follows within one
	# round trip; a missing one (old core, pause flag toggled mid-warp)
	# reveals anyway.
	"hold_timeout_seconds": 8.0,
	# WarpBegin without GC_WARP and without a cancel: the server never
	# finished the transfer; give the unchanged world back to the player.
	"departure_timeout_seconds": 10.0,
	# Settle: reveal after this many consecutive frames with the main actor
	# present and a frame time of at most
	#   clamp(settle_baseline_factor x baseline median,
	#         settle_floor_ms, settle_ceiling_ms),
	# where the baseline is this machine's own in-game frame time before the
	# warp. A fast machine (median <= floor / factor, about 13 ms) keeps the
	# 20 ms floor; a 30 FPS machine gets about 50 ms instead of the cap.
	# 5 -> 3 frames (owner decision 2026-10-05): the dev WARP_TIMELINE showed
	# game_phase -> reveal_start at 366-551 ms; three stable frames still
	# reject a single hitch, any slower frame restarts the streak.
	"settle_frames": 3,
	"settle_floor_ms": 20.0,
	"settle_ceiling_ms": 50.0,
	"settle_baseline_factor": 1.5,
	# Hard cap of the settle wait: the curtain must never be the bottleneck.
	"settle_cap_seconds": 1.2,
	# Native world readiness (EXE background.IsWorldReady) counts rendered
	# terrain patches, so a map with "TerrainVisible 0" (every dungeon built
	# from dungeon blocks) never reports ready. With the main actor present
	# the curtain therefore lifts this long after the settle began even
	# without the native signal. Without a main actor it never lifts.
	"strict_ready_cap_seconds": 3.0,
	# Rolling in-game frame-time window (frames) sampled while no curtain is
	# active; fewer samples than the minimum fall back to the floor. Single
	# frames longer than the sample limit (loading hitch, window drag) are
	# not a frame rate and are skipped.
	"baseline_window_frames": 120,
	"baseline_min_samples": 30,
	"baseline_sample_max_ms": 250.0,
}

IDLE = "idle"
FADE_IN = "fade_in"
COVERED = "covered"
SETTLE = "settle"
FADE_OUT = "fade_out"

ARRIVED = 0
CANCELLED = 1

EVENT_REVEAL_START = "reveal_start"
EVENT_REVEAL_DONE = "reveal_done"


def _ease_out(progress):
	inverse = 1.0 - progress
	return 1.0 - inverse * inverse * inverse


def _smooth(progress):
	return progress * progress * (3.0 - 2.0 * progress)


def _clamp01(value):
	return 0.0 if value < 0.0 else (1.0 if value > 1.0 else value)


class FrameTimeBaseline(object):
	"""Rolling window of in-game frame times; median on demand.

	Sampling is one list store per frame; the sort runs once per warp
	arrival, never per frame.
	"""

	def __init__(self, capacity, minSamples, sampleMaxMs):
		self.capacity = max(1, int(capacity))
		self.minSamples = max(1, int(minSamples))
		self.sampleMaxMs = float(sampleMaxMs)
		self.samples = []
		self.cursor = 0

	def Add(self, frameMs):
		if frameMs is None or frameMs <= 0.0 or frameMs > self.sampleMaxMs:
			return False
		if len(self.samples) < self.capacity:
			self.samples.append(float(frameMs))
		else:
			self.samples[self.cursor] = float(frameMs)
		self.cursor = (self.cursor + 1) % self.capacity
		return True

	def Median(self):
		"""Median frame time in ms, or None until enough samples exist."""
		count = len(self.samples)
		if count < self.minSamples:
			return None
		ordered = sorted(self.samples)
		middle = count // 2
		if count % 2:
			return ordered[middle]
		return (ordered[middle - 1] + ordered[middle]) / 2.0


def SettleFrameThresholdMs(baselineMs, tuning=None):
	"""Largest frame time that still counts as stable on arrival."""
	tuning = tuning or TUNING
	floor = float(tuning["settle_floor_ms"])
	ceiling = max(floor, float(tuning["settle_ceiling_ms"]))
	if baselineMs is None:
		return floor
	threshold = float(tuning["settle_baseline_factor"]) * float(baselineMs)
	return min(ceiling, max(floor, threshold))


class WarpCurtainModel(object):
	def __init__(self, tuning=None):
		self.tuning = dict(TUNING)
		if tuning:
			self.tuning.update(tuning)
		# The baseline outlives every warp of this client run.
		self.baseline = FrameTimeBaseline(self.tuning["baseline_window_frames"],
			self.tuning["baseline_min_samples"], self.tuning["baseline_sample_max_ms"])
		self.lastSettleThresholdMs = None
		self.Reset()

	def Reset(self):
		self.state = IDLE
		self.alpha = 0.0
		self.mapIndex = 0
		self.kind = 0
		self.reconnecting = False
		self.beganAt = 0.0
		self.arrivedAt = None
		self.endResult = None
		self.fadeStart = 0.0
		self.fadeFrom = 0.0
		self.fadeDuration = self.tuning["fade_in_seconds"]
		self.settleStart = 0.0
		self.settleThresholdMs = self.tuning["settle_floor_ms"]
		self.stableFrames = 0
		self.readySince = None
		self.strictReady = False
		self.revealReason = ""
		self.revealStarted = False
		# Why the last curtain lifted (arrived, cancelled, hold_timeout,
		# departure_timeout); kept after Reset for diagnostics.
		self.lastRevealReason = getattr(self, "lastRevealReason", "")

	# Queries -----------------------------------------------------------------
	def IsActive(self):
		return self.state != IDLE

	def IsInputLocked(self):
		return self.state in (FADE_IN, COVERED, SETTLE)

	def IsReconnecting(self):
		return self.reconnecting

	def IsCovering(self):
		"""Fully opaque: nothing behind the curtain is visible."""
		return self.state == COVERED or (self.state == SETTLE and self.alpha >= 1.0)

	# Frame baseline ----------------------------------------------------------
	def SampleGameFrame(self, frameMs):
		"""One in-game frame time before any warp; ignored under a curtain."""
		if self.state != IDLE:
			return False
		return self.baseline.Add(frameMs)

	# Network events ----------------------------------------------------------
	def Begin(self, now, mapIndex, kind=0):
		self.mapIndex = int(mapIndex)
		self.kind = int(kind)
		if self.state in (FADE_IN, COVERED, SETTLE):
			# A repeated WarpBegin of the same transfer keeps the curtain.
			return False
		self.state = FADE_IN
		self.fadeFrom = self.alpha
		self.fadeStart = now
		self.fadeDuration = self.tuning["fade_in_seconds"]
		self.beganAt = now
		self.arrivedAt = None
		self.endResult = None
		self.reconnecting = False
		self.revealReason = ""
		return True

	def Leave(self, now):
		"""GC_WARP on the seamless path: the reconnect starts now."""
		self.reconnecting = True
		self.endResult = None
		if self.state in (IDLE, FADE_OUT):
			# The EXE takes the seamless path only with an active curtain;
			# never let the old world vanish uncovered.
			self.state = COVERED
			self.alpha = 1.0
			return
		if self.state == FADE_IN:
			remaining = self.fadeDuration - (now - self.fadeStart)
			hurry = self.tuning["hurry_seconds"]
			if remaining > hurry:
				self.fadeFrom = self.alpha
				self.fadeStart = now
				self.fadeDuration = hurry

	def Arrive(self, now):
		"""ENTERGAME was sent on the destination (seamless path)."""
		self.reconnecting = False
		self.arrivedAt = now

	def End(self, now, result):
		if self.state == IDLE:
			return False
		if result != ARRIVED and self.reconnecting:
			# A source cancel cannot follow GC_WARP; ignore a stale one.
			return False
		self.endResult = ARRIVED if result == ARRIVED else CANCELLED
		if self.endResult == CANCELLED and self.state in (FADE_IN, COVERED, SETTLE):
			self.__StartFadeOut(now, "cancelled")
		return True

	def Abort(self):
		"""Another presentation took over (legacy warp, login screen)."""
		wasActive = self.IsActive()
		self.Reset()
		return wasActive

	# Frame update ------------------------------------------------------------
	def Update(self, now, frameMs, worldReady, strictReady=False, actorReady=None):
		self.strictReady = bool(strictReady)
		events = []
		if self.state == FADE_IN:
			progress = _clamp01((now - self.fadeStart) / max(self.fadeDuration, 0.001))
			self.alpha = self.fadeFrom + (1.0 - self.fadeFrom) * _ease_out(progress)
			if progress >= 1.0:
				self.alpha = 1.0
				self.state = COVERED

		if self.state == COVERED:
			if self.reconnecting:
				pass
			elif self.endResult == ARRIVED:
				self.__StartSettle(now, "arrived")
			elif self.endResult == CANCELLED:
				self.__StartFadeOut(now, "cancelled")
			elif self.arrivedAt is not None:
				if now - self.arrivedAt >= self.tuning["hold_timeout_seconds"]:
					self.__StartSettle(now, "hold_timeout")
			elif now - self.beganAt >= self.tuning["departure_timeout_seconds"]:
				self.__StartFadeOut(now, "departure_timeout")

		if self.state == SETTLE and now > self.settleStart:
			# Frames are counted from the first update after settling began.
			if worldReady and frameMs is not None and frameMs <= self.settleThresholdMs:
				self.stableFrames += 1
			else:
				self.stableFrames = 0
			if self.strictReady:
				if not worldReady:
					self.readySince = None
					# The native signal can be unreachable for a map (see
					# TUNING); a present main actor must not hold the curtain
					# forever. A missing actor still holds it.
					if actorReady and now - self.settleStart >= self.tuning["strict_ready_cap_seconds"]:
						self.__StartFadeOut(now, "ready_cap")
				elif self.readySince is None:
					self.readySince = now
				elif now - self.readySince >= self.tuning["world_ready_seconds"]:
					self.__StartFadeOut(now, self.revealReason)
			elif self.stableFrames >= self.tuning["settle_frames"] or \
					now - self.settleStart >= self.tuning["settle_cap_seconds"]:
				self.__StartFadeOut(now, self.revealReason)

		if self.state == FADE_OUT:
			if not self.revealStarted:
				self.revealStarted = True
				events.append(EVENT_REVEAL_START)
			progress = _clamp01((now - self.fadeStart) / max(self.fadeDuration, 0.001))
			self.alpha = self.fadeFrom * (1.0 - _smooth(progress))
			if progress >= 1.0:
				self.lastRevealReason = self.revealReason
				self.Reset()
				events.append(EVENT_REVEAL_DONE)
		return events

	def __StartSettle(self, now, reason):
		self.state = SETTLE
		self.settleStart = now
		self.stableFrames = 0
		self.readySince = None
		self.revealReason = reason
		# Frozen for this arrival: frames after the warp never feed it.
		self.settleThresholdMs = SettleFrameThresholdMs(self.baseline.Median(), self.tuning)
		self.lastSettleThresholdMs = self.settleThresholdMs

	def __StartFadeOut(self, now, reason):
		self.state = FADE_OUT
		self.fadeFrom = self.alpha
		self.fadeStart = now
		self.fadeDuration = self.tuning["ready_fade_out_seconds"] if self.strictReady and reason in ("arrived", "hold_timeout") else self.tuning["fade_out_seconds"]
		self.revealStarted = False
		if reason:
			self.revealReason = reason
