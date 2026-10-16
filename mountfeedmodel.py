"""Temporary mount crystal selection; never predicts or awards soul EXP."""

CRYSTAL_VNUMS = (79530, 79531, 79532)
PROTEIN_BAR_VNUM = 55001
REGULAR_FEED_VNUMS = CRYSTAL_VNUMS + (PROTEIN_BAR_VNUM,)
SLOT_COUNT = 9


class FeedBasket(object):

	def __init__(self):
		self.slots = [None] * SLOT_COUNT
		self.active = False
		self.inflight = None
		self.accepted_revision = None

	@property
	def busy(self):
		return self.inflight is not None

	def add(self, slot, cell, vnum, count):
		if self.active or self.busy or not 0 <= slot < SLOT_COUNT:
			return False
		if self.slots[slot] or cell < 0 or vnum not in CRYSTAL_VNUMS or count <= 0:
			return False
		if any(row and row[0] == cell for row in self.slots):
			return False
		self.slots[slot] = (cell, vnum, count)
		return True

	def remove(self, slot):
		if self.active or self.busy or not 0 <= slot < SLOT_COUNT or not self.slots[slot]:
			return False
		self.slots[slot] = None
		return True

	def validate(self, inventory):
		return all(not row or inventory(row[0]) == row[1:] for row in self.slots)

	def start(self):
		if self.active or self.busy or not any(self.slots):
			return False
		self.active = True
		return True

	def sent(self, slot, sequence, revision, nonce):
		if not self.active or self.busy or not self.slots[slot]:
			raise ValueError("invalid mount feed dispatch")
		self.inflight = (slot, sequence, revision, nonce)
		self.accepted_revision = None

	def acknowledge(self, sequence, revision, result):
		if not self.inflight or sequence != self.inflight[1]:
			return False
		if result != 0:
			self.stop()
			return True
		if revision <= self.inflight[2]:
			return False
		self.accepted_revision = revision
		return True

	def snapshot(self, revision, nonce):
		if not self.inflight:
			return False
		if nonce != self.inflight[3]:
			self.stop()
			self.clear()
			return False
		if self.accepted_revision is None or revision < self.accepted_revision:
			return False
		self.slots[self.inflight[0]] = None
		self.inflight = None
		self.accepted_revision = None
		self.active = self.active and any(self.slots)
		return True

	def stop(self):
		self.active = False
		self.inflight = None
		self.accepted_revision = None

	def clear(self):
		# Closing cancels only unsent work; the existing request still needs a reply.
		self.active = False
		self.slots = [None] * SLOT_COUNT
