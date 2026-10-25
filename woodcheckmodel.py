# -*- coding: utf-8 -*-
"""Model of the woodcutting rhythm bar (Dřevorubectví, concept D "rytmický pruh", version 2: a direction per
strike): the server lines, the strike schedule and its directions, which strike a press belongs to, the results of
one cut, the bonus, a clean cut ("čistá seč"), the look of a result over time, the texts and the mode the player
chose ("Minihra sekání": Vypnuto | Zapnuto).

Pure Python (no engine module), so it can be tested on its own. Protocol (chat commands, no new EXE):

    game -> server   /wcheck mode <0|1>                             after entering the game and on every change
                     /wcheck hit <id> <strike> <elapsed_ms> <dir>   at most once per strike; elapsed_ms = time since
                                                                    the WoodCheckV2 line arrived (the frame the player
                                                                    saw), dir = the direction of the pressed key 0-3
    server -> game   WoodCheckV2 <id> <cycles> <cycle_ms> <hit1_ms> <hit2_ms> <hit3_ms> <great_ms> <good_ms> <lead_ms>
                                 <dirs>
                         sent at the moment the cut starts (with the woodcut motion); client time 0 = its arrival.
                         Strike k (0 .. 3 * cycles - 1) is due at (k // 3) * cycle_ms + hit[k % 3]; dirs is one digit
                         per strike (3 * cycles): 0 left (← / A), 1 up (↑ / W), 2 right (→ / D), 3 down (↓ / S).
                         great / good / lead depend on the Dřevorubec level (server side); a mark travels lead_ms
                         along the bar before its strike.
                     WoodCheckV3 <id> <great_ms> <good_ms> <marks>
                         irregular marks (owner 13. 10.: random gaps, more marks, a speed per mark): marks is
                         "<step>.<lead>.<dir>,..." in 10 ms units, step = due minus the previous mark's due (the
                         first: minus 0), lead = how long that mark travels along the bar, dir as in WoodCheckV2.
                     WoodCheckResultV1 <id> <strike> <result> <bonus_pct>   result 0 miss, 1 good, 2 great;
                         bonus_pct = the wood bonus of this cut so far (%)
                     WoodCheckEndV1 <id>                      the cut was cancelled (moved, attacked): hide quietly
                     WoodCheckModeV1 <0|1>                    the minigame is off / on for this character
                     CraftWoodCheckV1 <great> <good> <miss> <perfect>   a line of "/craft state" (craftbookmodel)

The SERVER decides every result (its own clock, a ping tolerance, the direction: a wrong key is a miss) and answers
only strikes the player pressed; a press goes to the nearest open strike whatever key it was. A
strike nobody pressed stays without an answer and counts as a miss, so the bar greys it locally once its window
has passed (Lapsed). A clean cut = every strike of the cut answered VÝBORNĚ.
"""
import json
import os

import miningcheckmodel as MC

try:
	import builtins
except ImportError:
	import __builtin__ as builtins

MODE_OFF, MODE_ON = 0, 1
MODES = (MODE_OFF, MODE_ON)
DEFAULT_MODE = MODE_ON       # the server's default is on as well
MISS, GOOD, GREAT = 0, 1, 2
RESULTS = (MISS, GOOD, GREAT)

RESULT, END, MODE = 'WoodCheckResultV1', 'WoodCheckEndV1', 'WoodCheckModeV1'
CHECK_V2 = 'WoodCheckV2'
CHECK_V3 = 'WoodCheckV3'
COMMANDS = (CHECK_V3, CHECK_V2, RESULT, END, MODE)
MAX_MARKS = 99               # irregular marks of one cut (WoodCheckV3)
CRAFT_CHECK_FIELDS = ('great', 'good', 'miss', 'perfect')

STRIKES = 3                  # strikes per cycle (one chop motion)
MAX_ID = 2 ** 32 - 1
MAX_MS = 60000               # a cycle, a window or a lead longer than a minute is not a rhythm bar
MAX_CYCLES = 100             # the server takes a strike index up to 1000
MAX_TOTAL_MS = 600000        # a cut longer than 10 minutes is a broken line
PICK_SLACK_MS = 120          # a press belongs to a strike due within good_ms + this (else it is ignored)

COMMAND_MODE = '/wcheck mode %d'
COMMAND_HIT_V2 = '/wcheck hit %d %d %d %d'

LEFT, UP, RIGHT, DOWN = 0, 1, 2, 3
DIRECTIONS = (LEFT, UP, RIGHT, DOWN)
ARROWS = {LEFT: u'\u2190', UP: u'\u2191', RIGHT: u'\u2192', DOWN: u'\u2193'}    # ← ↑ → ↓ on the marks
# the keys of a direction by their app.DIK_<name>: the arrows and W/A/S/D (the movement keys while no bar is up)
KEY_DIRECTIONS = (('LEFT', LEFT), ('A', LEFT), ('UP', UP), ('W', UP), ('RIGHT', RIGHT), ('D', RIGHT),
				  ('DOWN', DOWN), ('S', DOWN))

STORE_VERSION = 1
_REAL_OPEN = getattr(builtins, 'old_open', builtins.open)

# (Czech, English) fallbacks; the locale table may override them (localeInfo WOOD_CHECK_<key>).
TEXTS = {
	'MODE_OFF': ('Vypnuto', 'Off'),
	'MODE_ON': ('Zapnuto', 'On'),
	'GREAT': ('VÝBORNĚ', 'GREAT'),
	'GOOD': ('DOBŘE', 'GOOD'),
	'MISS': ('VEDLE', 'MISSED'),
	'PERFECT': ('ČISTÁ SEČ', 'CLEAN CUT'),
	'BONUS': ('+%d %% dřeva', '+%d %% wood'),
	'HINT_DIRS': ('Šipky nebo WASD, když značka projede čárou', 'Arrows or WASD when a mark crosses the line'),
}


def Tr(key):
	"""Player text: the locale table (localeInfo WOOD_CHECK_<key>) or the Czech / English fallback."""
	czech, english = TEXTS[key]
	try:
		import localeInfo
		value = getattr(localeInfo, 'WOOD_CHECK_' + key, None)
		if isinstance(value, str) and value:
			return value
	except Exception:
		pass
	try:
		import app
		return czech if app.GetLocalePath().replace('\\', '/').lower().endswith('/cz') else english
	except Exception:
		return czech


_number = MC._number
_numbers = MC._numbers


# --------------------------------------------------------------------------- server lines
class Check(object):
	"""One WoodCheckV2 (or V1): the strike schedule of one cut and the direction of every strike (``dirs`` None for a
	V1 line: any direction key hits)."""

	def __init__(self, check_id, cycles, cycle_ms, hits, great_ms, good_ms, lead_ms, dirs=None):
		self.id = check_id
		self.cycles = cycles
		self.cycle_ms = cycle_ms
		self.hits = tuple(hits)
		self.great_ms = great_ms
		self.good_ms = good_ms
		self.lead_ms = lead_ms
		self.dirs = None if dirs is None else tuple(dirs)
		self.dues = None             # WoodCheckV3: the due time of every mark (else the chop strikes)
		self.leads = None            # WoodCheckV3: how long every mark travels (else lead_ms)

	def Direction(self, strike):
		"""LEFT / UP / RIGHT / DOWN of strike ``strike``."""
		return self.dirs[strike]

	def Count(self):
		"""The number of strikes of the cut."""
		if self.dues is not None:
			return len(self.dues)
		return self.cycles * STRIKES

	def Due(self, strike):
		"""Milliseconds after the WoodCheck line when strike ``strike`` is due."""
		if self.dues is not None:
			return self.dues[strike]
		return (strike // STRIKES) * self.cycle_ms + self.hits[strike % STRIKES]

	def Lead(self, strike):
		"""How long the mark of ``strike`` travels along the bar before it is due (its own speed on a V3 bar)."""
		if self.leads is not None:
			return self.leads[strike]
		return self.lead_ms

	def Dues(self):
		return [self.Due(strike) for strike in range(self.Count())]

	def LastDue(self):
		return self.Due(self.Count() - 1)

	def End(self):
		"""Milliseconds after which no strike can be hit any more (the last window closed)."""
		return self.LastDue() + self.good_ms

	def Pick(self, elapsed_ms, taken=()):
		"""The strike a press at ``elapsed_ms`` belongs to: the nearest strike not ``taken`` (already sent or
		answered) due within good_ms + PICK_SLACK_MS; the earlier one on a tie. None = the press is ignored."""
		reach = self.good_ms + PICK_SLACK_MS
		best, best_distance = None, None
		for strike in range(self.Count()):
			if strike in taken:
				continue
			distance = abs(self.Due(strike) - float(elapsed_ms))
			if distance <= reach and (best_distance is None or distance < best_distance):
				best, best_distance = strike, distance
		return best

	def Zone(self, strike, elapsed_ms):
		"""GREAT / GOOD / MISS of a press at ``elapsed_ms`` for ``strike`` (local only; the server decides)."""
		distance = abs(self.Due(strike) - float(elapsed_ms))
		if distance <= self.great_ms:
			return GREAT
		if distance <= self.good_ms:
			return GOOD
		return MISS


class Result(object):
	"""One WoodCheckResultV1."""

	def __init__(self, check_id, strike, result, bonus_pct):
		self.id = check_id
		self.strike = strike
		self.result = result
		self.bonus = bonus_pct


def ParseCheck(args):
	"""The first nine WoodCheckV2 fields (the timing) -> Check without directions, or None for a malformed line (a missing or extra field, no cycle, hits out of
	order or after the cycle, great wider than good, a cut longer than MAX_TOTAL_MS)."""
	values = _numbers(args, 9)
	if values is None:
		return None
	check_id, cycles, cycle_ms, hit1, hit2, hit3, great, good, lead = values
	if check_id > MAX_ID or not 1 <= cycles <= MAX_CYCLES or not 0 < cycle_ms <= MAX_MS:
		return None
	if not hit1 <= hit2 <= hit3 <= cycle_ms or not 0 < good <= MAX_MS or great > good or not 0 < lead <= MAX_MS:
		return None
	if cycles * cycle_ms > MAX_TOTAL_MS:
		return None
	return Check(check_id, cycles, cycle_ms, (hit1, hit2, hit3), great, good, lead)


def ParseCheckV2(args):
	"""WoodCheckV2 fields -> Check with the directions, or None for a malformed line (the ParseCheck rules, and
	``dirs`` must be exactly 3 * cycles digits 0-3)."""
	args = tuple(args or ())
	if len(args) != 10:
		return None
	check = ParseCheck(args[:9])
	dirs = args[9]
	if check is None or not isinstance(dirs, str) or len(dirs) != check.Count():
		return None
	if any(digit not in '0123' for digit in dirs):
		return None
	check.dirs = tuple(int(digit) for digit in dirs)
	return check


def ParseCheckV3(args):
	"""WoodCheckV3 fields -> Check with irregular marks, or None for a malformed line (an id, windows great <= good,
	1..MAX_MARKS marks of three numbers each, rising due times, a lead > 0, directions 0-3, a cut shorter than
	MAX_TOTAL_MS)."""
	args = tuple(args or ())
	if len(args) != 4:
		return None
	head = _numbers(args[:3], 3)
	if head is None:
		return None
	check_id, great, good = head
	if check_id > MAX_ID or not 0 < good <= MAX_MS or not 0 <= great <= good:
		return None
	dues, leads, dirs = [], [], []
	due = 0
	marks = args[3].split(',') if isinstance(args[3], str) else ()
	if not 1 <= len(marks) <= MAX_MARKS:
		return None
	for mark in marks:
		parts = mark.split('.')
		if len(parts) != 3 or not all(part.isdigit() for part in parts):
			return None
		step, lead, direction = int(parts[0]) * 10, int(parts[1]) * 10, int(parts[2])
		if (dues and step <= 0) or not 0 < lead <= MAX_MS or direction > 3:
			return None
		due += step
		dues.append(due)
		leads.append(lead)
		dirs.append(direction)
	if due > MAX_TOTAL_MS:
		return None
	check = Check(check_id, 1, max(due, 1), (0, 0, 0), great, good, max(leads), dirs)
	check.dues = tuple(dues)
	check.leads = tuple(leads)
	return check


def HitCommand(check, strike, elapsed_ms, direction=None):
	"""The hit of ``strike``: "/wcheck hit <id> <strike> <elapsed_ms> <dir>" (None without a valid direction: a hit
	always names the pressed key)."""
	if isinstance(direction, bool) or direction not in DIRECTIONS:
		return None
	return COMMAND_HIT_V2 % (check.id, strike, int(elapsed_ms), direction)


def ParseResult(args):
	values = _numbers(args, 4)
	if values is None or values[0] > MAX_ID or values[1] >= MAX_CYCLES * STRIKES or values[2] not in RESULTS:
		return None
	if values[3] > 1000:
		return None
	return Result(*values)


def ParseEnd(args):
	"""WoodCheckEndV1 <id> -> the id, or None."""
	values = _numbers(args, 1, MAX_ID)
	return None if values is None else values[0]


def ParseMode(args):
	values = _numbers(args, 1)
	if values is None or values[0] not in MODES:
		return None
	return values[0]


def ParseCraftCheck(args):
	"""CraftWoodCheckV1 <great> <good> <miss> <perfect> -> the four counters, or None."""
	return _numbers(args, len(CRAFT_CHECK_FIELDS))


# --------------------------------------------------------------------------- one cut
class Session(object):
	"""The bookkeeping of one cut: the strikes sent (at most once each), the server's answers, the bonus."""

	def __init__(self, check):
		self.check = check
		self.sent = {}               # strike -> elapsed_ms sent
		self.pressed = {}            # strike -> the direction sent with it
		self.results = {}            # strike -> MISS / GOOD / GREAT (the server's answer)
		self.bonus = 0
		self.last = None             # the strike answered last

	def Taken(self):
		return set(self.sent) | set(self.results)

	def Hit(self, elapsed_ms, direction=None):
		"""A press of a ``direction`` key: the strike it belongs to (now sent), or None when it belongs to none. The
		nearest open strike takes it whatever the key (a wrong key is the server's miss, not the next strike's)."""
		strike = self.check.Pick(elapsed_ms, self.Taken())
		if strike is None:
			return None
		self.sent[strike] = int(elapsed_ms)
		self.pressed[strike] = direction
		return strike

	def SetResult(self, result):
		"""The server's answer of this cut; False for another id, a strike outside the cut or a second answer."""
		if result.id != self.check.id or not 0 <= result.strike < self.check.Count():
			return False
		if result.strike in self.results:
			return False
		self.results[result.strike] = result.result
		self.bonus = max(0, int(result.bonus))
		self.last = result.strike
		return True

	def Lapsed(self, strike, elapsed_ms):
		"""True when ``strike`` was never pressed and its window has passed (no answer will come: a miss)."""
		return strike not in self.sent and strike not in self.results and \
			float(elapsed_ms) > self.check.Due(strike) + self.check.good_ms + PICK_SLACK_MS

	def State(self, strike, elapsed_ms):
		"""MISS / GOOD / GREAT of a strike for its pip, or None while it is still open or waits for its answer."""
		if strike in self.results:
			return self.results[strike]
		if self.Lapsed(strike, elapsed_ms):
			return MISS
		return None

	def Waiting(self):
		"""Strikes sent without an answer yet."""
		return [strike for strike in self.sent if strike not in self.results]

	def Settled(self, elapsed_ms):
		"""Every strike is answered or lapsed: nothing more can change."""
		return all(self.State(strike, elapsed_ms) is not None for strike in range(self.check.Count()))

	def Complete(self):
		"""Every strike of the cut has the server's answer."""
		return len(self.results) == self.check.Count()

	def Perfect(self):
		"""A clean cut: every strike answered VÝBORNĚ."""
		return self.Complete() and all(result == GREAT for result in self.results.values())

	def Streak(self):
		"""VÝBORNĚ in a row up to the strike answered last (an earlier strike not answered VÝBORNĚ breaks it)."""
		if self.last is None:
			return 0
		count, strike = 0, self.last
		while strike >= 0 and self.results.get(strike) == GREAT:
			count += 1
			strike -= 1
		return count

	def Counts(self, elapsed_ms):
		"""(great, good, miss) so far (a lapsed strike is a miss)."""
		states = [self.State(strike, elapsed_ms) for strike in range(self.check.Count())]
		return states.count(GREAT), states.count(GOOD), states.count(MISS)


# --------------------------------------------------------------------------- the bar geometry
def Speed(travel_px, lead_ms):
	"""Pixels per millisecond: a mark enters ``travel_px`` right of the hit line ``lead_ms`` before it is due."""
	return float(travel_px) / max(1.0, float(lead_ms))


def MarkX(due_ms, elapsed_ms, hit_x, speed):
	"""X of a mark (its centre): on the hit line exactly at its due time, right of it before, left of it after."""
	return float(hit_x) + (float(due_ms) - float(elapsed_ms)) * speed


def Marks(check, elapsed_ms, taken=(), behind_ms=None, margin_ms=0):
	"""[(strike, due - elapsed)] of the marks on the bar now: visible from (due - lead_ms - ``margin_ms``) and not
	past by more than ``behind_ms`` (default good_ms + PICK_SLACK_MS); a strike sent or answered leaves the bar."""
	behind = check.good_ms + PICK_SLACK_MS if behind_ms is None else behind_ms
	out = []
	for strike in range(check.Count()):
		if strike in taken:
			continue
		ahead = check.Due(strike) - float(elapsed_ms)
		if -behind <= ahead <= check.Lead(strike) + margin_ms:
			out.append((strike, ahead))
	return out


HEAD_HEIGHT = MC.HEAD_HEIGHT
OFF_SCREEN = MC.OFF_SCREEN
NAME_GAP = 34                # px between the top of the character and the window (the name tag stays visible)


def Anchor(head, screen, size, gap=NAME_GAP):
	"""The window centre above the woodcutter: centred on the character, its bottom ``gap`` px above the top of
	the character (chr.GetProjectPosition at HEAD_HEIGHT). None when the character is not on the screen."""
	if head is None or tuple(head) == OFF_SCREEN:
		return None
	hx, hy = head
	width, height = screen
	if not (0 <= hx < width and 0 <= hy < height):
		return None
	return (float(hx), float(hy) - gap - size[1] / 2.0)


Follow = MC.Follow
SeenTime = MC.SeenTime
ElapsedMs = MC.ElapsedMs
Clamp01 = MC.Clamp01
EaseOut = MC.EaseOut


# --------------------------------------------------------------------------- feedback over time
APPEAR = 0.15                # s: the bar comes in
LINGER = 1.0                 # s: after the last answer (or the last window) the bar stays, then hides
PERFECT_LINGER = 1.6         # s: a clean cut stays a little longer
RESULT_WAIT = 1.5            # s: a sent strike waits this long for its answer after the last window
FADE = 0.25                  # s: the bar fades out at the end
FLASH = 0.22                 # s: the hit line flashes on an answer


def Appear(t):
	"""Alpha of the bar ``t`` s after it was shown."""
	return EaseOut(t / APPEAR)


def Headline(t):
	"""(alpha, rise px) of the headline ``t`` s after a result: it fades in and rises 8 px into place (as the
	mining ring's headline)."""
	return Clamp01(t / 0.12), int(round(8.0 * (1.0 - EaseOut(t / 0.18))))


GREY_FOR = 0.32              # s: VEDLE greys the bar this long
JERK_PX = 30.0               # px of the vertical jerk per unit of the mining punch (112 % -> 3.6 px up)


class Look(object):
	"""The look of a result ``t`` s after it arrived, taken over from the mining ring (miningcheckmodel.Feedback):

	VÝBORNĚ  a white-hot flare on the hit line, sparks and wood chips out of it, the bar jerks up (the punch to
	         112 % as a vertical jerk), the "výborně" zone flashes white-hot then blood red, a blood red ring flies
	         out of the hit line; the headline in blood red rises into place.
	DOBŘE    softer: a weaker flash and jerk, a faint ring; no flare, sparks or chips.
	VEDLE    the bar jerks sideways +-3 px and greys for GREY_FOR s; no flash, no ring.
	Unlike the ring the bar does not fade after a result: the next strikes follow."""

	def __init__(self, result, t):
		t = max(0.0, float(t))
		feedback = MC.Feedback(result, t)
		self.flash = feedback.flash
		self.flash_hot = t < 0.08                     # the zone flash: white-hot first, then blood red
		self.jerk = -int(round((feedback.scale - 1.0) * JERK_PX))
		self.shake = feedback.shake
		self.grey = feedback.grey if t < GREY_FOR else 1.0
		self.burst_scale, self.burst_alpha = feedback.burst_scale, feedback.burst_alpha
		self.sparks, self.chips, self.flare = feedback.sparks, feedback.chips, feedback.flare
		self.text_alpha, self.text_rise = Headline(t)


Pips = MC.Pips


def Flash(t):
	"""Alpha of the hit line flash ``t`` s after an answer."""
	if t < 0.0 or t >= FLASH:
		return 0.0
	return 1.0 - t / FLASH


def FadeOut(now, until):
	"""Alpha at the end: 1 until FADE s before ``until``, then down to 0."""
	return Clamp01((float(until) - float(now)) / FADE)


def ResultText(result):
	return Tr({GREAT: 'GREAT', GOOD: 'GOOD'}.get(result, 'MISS'))


def BonusText(bonus):
	"""+N % dřeva ('' without a bonus)."""
	bonus = max(0, int(bonus or 0))
	return Tr('BONUS') % bonus if bonus else ''


def ModeLabels():
	"""The craft book switch: Vypnuto | Zapnuto."""
	return [(MODE_OFF, Tr('MODE_OFF')), (MODE_ON, Tr('MODE_ON'))]


# --------------------------------------------------------------------------- the chosen mode, per character
class ModeStore(object):
	"""The mode chosen for one character in UserData/wood_check_<name>.json (like miningcheckmodel.ModeStore); a
	missing or broken file is DEFAULT_MODE (Zapnuto). ``explicit`` is True once the player's own choice is stored
	or loaded: only then does the server's word overwrite the file."""

	def __init__(self, storage_directory='UserData'):
		self.storage_directory = storage_directory
		self.name = ''
		self.path = ''
		self.mode = DEFAULT_MODE
		self.explicit = False

	def SetIdentity(self, name):
		"""Loads the mode of character ``name``; True when the character changed."""
		name = str(name or '')
		path = os.path.join(self.storage_directory, 'wood_check_%s.json' % MC.SafeName(name))
		if path == self.path:
			return False
		self.name, self.path = name, path
		stored = self.Stored()
		self.explicit = stored is not None
		self.mode = DEFAULT_MODE if stored is None else stored
		return True

	def Stored(self):
		"""The stored choice or None for a missing or broken file."""
		try:
			with _REAL_OPEN(self.path, 'rb') as handle:
				payload = json.loads(handle.read().decode('utf-8'))
		except Exception:
			return None
		mode = payload.get('mode') if isinstance(payload, dict) else None
		if isinstance(mode, bool) or mode not in MODES:
			return None
		return mode

	def Load(self):
		stored = self.Stored()
		return DEFAULT_MODE if stored is None else stored

	def Set(self, mode):
		"""Stores the mode at once; False for an unknown mode or when the file cannot be written."""
		if isinstance(mode, bool) or mode not in MODES:
			return False
		self.mode = mode
		self.explicit = True
		if not self.path:
			return False
		temporary = self.path + '.tmp'
		try:
			directory = os.path.dirname(self.path)
			if directory and not os.path.isdir(directory):
				os.makedirs(directory)
			body = json.dumps({'version': STORE_VERSION, 'character': self.name, 'mode': mode},
							  ensure_ascii=False, separators=(',', ':')).encode('utf-8')
			with _REAL_OPEN(temporary, 'wb') as handle:
				handle.write(body)
			replace = getattr(os, 'replace', None)
			if replace is None:              # an os module without replace (Python 2 style): remove, then rename
				if os.path.exists(self.path):
					os.remove(self.path)
				os.rename(temporary, self.path)
			else:
				replace(temporary, self.path)
			return True
		except Exception:              # whatever the file system or an embedded os module does: never raise
			try:
				os.unlink(temporary)
			except Exception:
				pass
			return False
