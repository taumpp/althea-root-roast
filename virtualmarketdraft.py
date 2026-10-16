from collections import namedtuple


MAX_PRICE = 10000000000
GRID_COLUMNS = 15
GRID_ROWS = 11
GRID_SLOT_COUNT = GRID_COLUMNS * GRID_ROWS
MAX_ITEM_HEIGHT = 3

STATE_EDITING = "editing"
STATE_CREATING_SHOP = "creating_shop"
STATE_SUBMITTING_LISTING = "submitting_listing"
STATE_COMPLETED = "completed"
STATE_COMPLETED_WITH_ERRORS = "completed_with_errors"
STATE_FAILED = "failed"
STATE_CLEARED = "cleared"

ENTRY_EDITING = "editing"
ENTRY_QUEUED = "queued"
ENTRY_SUBMITTING = "submitting"
ENTRY_RETRYABLE = "retryable"
ENTRY_FAILED = "failed"


DraftRecord = namedtuple("DraftRecord", (
	"source_window", "source_cell", "vnum", "count", "display_slot",
	"height", "total_price", "state", "error"))


def scale_price(previous_total, previous_count, new_count):
	try:
		previous_total = int(previous_total)
		previous_count = int(previous_count)
		new_count = int(new_count)
	except (TypeError, ValueError, OverflowError):
		return None
	if previous_total <= 0 or previous_total > MAX_PRICE:
		return None
	if previous_count <= 0 or new_count <= 0:
		return None
	numerator = previous_total * new_count
	result = (numerator + previous_count - 1) // previous_count
	return result if 0 < result <= MAX_PRICE else None


class DraftController(object):
	_LOCKED_ENTRY_STATES = (
		ENTRY_EDITING, ENTRY_QUEUED, ENTRY_SUBMITTING, ENTRY_RETRYABLE)

	def __init__(self, columns=GRID_COLUMNS, rows=GRID_ROWS):
		self.columns = int(columns)
		self.rows = int(rows)
		if self.columns <= 0 or self.rows <= 0:
			raise ValueError("draft grid dimensions must be positive")
		self.slot_count = self.columns * self.rows
		self.state = STATE_EDITING
		self.last_error = ""
		self._records = {}
		self._occupied = {}
		self._queue = []
		self._current_slot = None
		self._had_errors = False

	def _fail(self, error):
		self.last_error = error
		return None

	def _coerce_positive(self, value):
		try:
			value = int(value)
		except (TypeError, ValueError, OverflowError):
			return None
		return value if value > 0 else None

	def _source_key(self, source_window, source_cell):
		try:
			source_window = int(source_window)
			source_cell = int(source_cell)
		except (TypeError, ValueError, OverflowError):
			return None
		if source_window < 0 or source_cell < 0:
			return None
		return source_window, source_cell

	def _footprint(self, display_slot, height):
		try:
			display_slot = int(display_slot)
			height = int(height)
		except (TypeError, ValueError, OverflowError):
			return None
		if display_slot < 0 or display_slot >= self.slot_count:
			return None
		if height <= 0 or height > MAX_ITEM_HEIGHT:
			return None
		row = display_slot // self.columns
		if row + height > self.rows:
			return None
		return tuple(display_slot + offset * self.columns for offset in range(height))

	def add(self, source_window, source_cell, vnum, count,
			display_slot, height, total_price):
		if self.state != STATE_EDITING:
			return self._fail("not_editing")
		source = self._source_key(source_window, source_cell)
		if source is None:
			return self._fail("invalid_source")
		vnum = self._coerce_positive(vnum)
		count = self._coerce_positive(count)
		if vnum is None or count is None:
			return self._fail("invalid_item")
		total_price = self._coerce_positive(total_price)
		if total_price is None or total_price > MAX_PRICE:
			return self._fail("invalid_price")
		footprint = self._footprint(display_slot, height)
		if footprint is None:
			return self._fail("outside_grid")
		if source in self.locked_sources():
			return self._fail("duplicate_source")
		if any(slot in self._occupied for slot in footprint):
			return self._fail("occupied")

		display_slot = int(display_slot)
		record = DraftRecord(
			source[0], source[1], vnum, count, display_slot, int(height),
			total_price, ENTRY_EDITING, "")
		self._records[display_slot] = record
		for slot in footprint:
			self._occupied[slot] = display_slot
		self.last_error = ""
		return record

	def get(self, display_slot):
		try:
			display_slot = int(display_slot)
		except (TypeError, ValueError, OverflowError):
			return None
		base_slot = self._occupied.get(display_slot, display_slot)
		return self._records.get(base_slot)

	def snapshot(self):
		return tuple(self._records[slot] for slot in sorted(self._records))

	def occupied_slots(self):
		return tuple(sorted(self._occupied))

	def locked_sources(self):
		return tuple(sorted(
			(record.source_window, record.source_cell)
			for record in self._records.values()
			if record.state in self._LOCKED_ENTRY_STATES))

	def remove(self, display_slot):
		if self.state != STATE_EDITING:
			return self._fail("not_editing")
		record = self.get(display_slot)
		if record is None:
			return self._fail("not_found")
		self._remove_record(record.display_slot)
		self.last_error = ""
		return record

	def reject(self, display_slot, error=""):
		if self.state != STATE_EDITING:
			return self._fail("not_editing")
		record = self.get(display_slot)
		if record is None:
			return self._fail("not_found")
		self._had_errors = True
		self._release_footprint(record)
		self.last_error = str(error or "rejected")
		self._replace(record.display_slot, state=ENTRY_FAILED,
			error=self.last_error)
		return record

	def clear(self):
		locked = tuple(
			record for record in self.snapshot()
			if record.state in self._LOCKED_ENTRY_STATES)
		self._records.clear()
		self._occupied.clear()
		self._queue = []
		self._current_slot = None
		self.state = STATE_CLEARED
		self.last_error = ""
		return locked

	def start_creation(self):
		if self.state != STATE_EDITING:
			return self._fail("not_editing")
		self.state = STATE_CREATING_SHOP
		self._queue = []
		for slot in sorted(self._records):
			record = self._records[slot]
			if record.state == ENTRY_EDITING:
				self._replace(slot, state=ENTRY_QUEUED, error="")
				self._queue.append(slot)
			elif record.state == ENTRY_FAILED:
				self._had_errors = True
		self._current_slot = None
		self.last_error = ""
		return self.snapshot()

	def mark_shop_result(self, success, error=""):
		if self.state != STATE_CREATING_SHOP:
			return False
		if success:
			self.state = (STATE_SUBMITTING_LISTING
				if self._queue else STATE_COMPLETED)
			self.last_error = ""
			return True

		self.state = STATE_FAILED
		self._had_errors = True
		for slot in tuple(self._records):
			record = self._records[slot]
			if record.state in self._LOCKED_ENTRY_STATES:
				self._replace(slot, state=ENTRY_FAILED, error=str(error or "rejected"))
		self._queue = []
		self._current_slot = None
		self.last_error = str(error or "rejected")
		return True

	def next_submission(self):
		if self.state != STATE_SUBMITTING_LISTING or self._current_slot is not None:
			return None
		while self._queue:
			slot = self._queue.pop(0)
			record = self._records.get(slot)
			if record is None or record.state != ENTRY_QUEUED:
				continue
			self._current_slot = slot
			return self._replace(slot, state=ENTRY_SUBMITTING, error="")
		self._finish_submission()
		return None

	def current_submission(self):
		if self._current_slot is None:
			return None
		return self._records.get(self._current_slot)

	def defer_current(self, error=""):
		if self.state != STATE_SUBMITTING_LISTING or self._current_slot is None:
			return False
		slot = self._current_slot
		record = self._records.get(slot)
		if record is None or record.state != ENTRY_SUBMITTING:
			return False
		self._replace(slot, state=ENTRY_QUEUED, error=str(error or "deferred"))
		self._queue.insert(0, slot)
		self._current_slot = None
		return True

	def mark_result(self, display_slot, success, error="", retryable=False):
		if self.state != STATE_SUBMITTING_LISTING or self._current_slot is None:
			return False
		try:
			display_slot = int(display_slot)
		except (TypeError, ValueError, OverflowError):
			return False
		if display_slot != self._current_slot:
			return False
		record = self._records.get(display_slot)
		if record is None or record.state not in (ENTRY_SUBMITTING, ENTRY_RETRYABLE):
			return False
		if retryable and not success:
			self._replace(display_slot, state=ENTRY_RETRYABLE,
				error=str(error or "retryable"))
			return True

		self._current_slot = None
		if success:
			self._remove_record(display_slot)
		else:
			self._had_errors = True
			self._replace(display_slot, state=ENTRY_FAILED,
				error=str(error or "rejected"))
			self._release_footprint(record)
		if not self._queue:
			self._finish_submission()
		return True

	def _replace(self, display_slot, **changes):
		record = self._records[display_slot]._replace(**changes)
		self._records[display_slot] = record
		return record

	def _release_footprint(self, record):
		for slot in self._footprint(record.display_slot, record.height) or ():
			if self._occupied.get(slot) == record.display_slot:
				del self._occupied[slot]

	def _remove_record(self, display_slot):
		record = self._records.pop(display_slot, None)
		if record is not None:
			self._release_footprint(record)
		return record

	def _finish_submission(self):
		if self._current_slot is not None or self._queue:
			return
		self.state = (STATE_COMPLETED_WITH_ERRORS
			if self._had_errors else STATE_COMPLETED)
