# dungeon return refusals the player can wait out.
#
# The dungeon_rejoin quest answers an ACCEPT with one of:
#   DungeonRejoinResult <code> <channel>   JOINED, or a final refusal
#                                           (EXPIRED, INVALID, UNAVAILABLE);
#                                           WRONG_CHANNEL keeps the offer.
#   DungeonRejoinRetry <reason> <seconds>  a temporary refusal (trade, shop,
#                                           storage or refine cooldown, an open
#                                           window, a map transfer in progress).
#                                           The server keeps the receipt.
# Old servers never send DungeonRejoinRetry; old clients ignore it because it
# is an unknown server command. No engine imports: this module is unit tested.

import math

# No answer to an ACCEPT within this time re-enables the button.
PENDING_TIMEOUT = 10
# A refusal without a known wait still debounces the button briefly.
MIN_RETRY_DELAY = 2
MAX_RETRY_DELAY = 60

REASON_COOLDOWN = "COOLDOWN"
REASON_BUSY = "BUSY"
RETRY_REASONS = (REASON_COOLDOWN, REASON_BUSY)

LINE_REMAINING = "REMAINING"
LINE_WAITING = "WAITING"
LINE_RETRY_COOLDOWN = "RETRY_COOLDOWN"
LINE_RETRY_BUSY = "RETRY_BUSY"


def ParseRetry(reason, seconds):
	reason = str(reason or "").upper()
	if reason not in RETRY_REASONS:
		reason = REASON_BUSY
	try:
		seconds = int(seconds)
	except (TypeError, ValueError):
		seconds = 0
	return reason, max(0, min(MAX_RETRY_DELAY, seconds))


class RetryState(object):
	def __init__(self):
		self.Reset()

	def Reset(self):
		self.pendingUntil = 0
		self.retryAt = 0
		self.reason = ""

	def Begin(self, now):
		self.pendingUntil = now + PENDING_TIMEOUT
		self.retryAt = 0
		self.reason = ""

	def Refuse(self, reason, seconds, now):
		reason, seconds = ParseRetry(reason, seconds)
		self.pendingUntil = 0
		self.reason = reason
		self.retryAt = now + max(MIN_RETRY_DELAY, seconds)

	def IsPending(self, now):
		return self.pendingUntil > now

	def RetryLeft(self, now):
		if self.retryAt <= now:
			return 0
		return int(math.ceil(self.retryAt - now))

	def CanAccept(self, now):
		return not self.IsPending(now) and self.RetryLeft(now) == 0

	def StatusLine(self, now, offerLeft):
		"""(line kind, value) for the second dialog line."""
		if self.IsPending(now):
			return LINE_WAITING, 0
		left = self.RetryLeft(now)
		if left > 0:
			if self.reason == REASON_COOLDOWN:
				return LINE_RETRY_COOLDOWN, left
			return LINE_RETRY_BUSY, left
		return LINE_REMAINING, max(0, int(offerLeft))
