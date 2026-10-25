# -*- coding: utf-8 -*-
"""Model of the mining skill check (Řemesla krok 2): the server lines, the needle and the zones, the result texts and
the mode the player chose ("Minihra těžby": Vypnuto | A - nápřah | B - další těžba).

Pure Python (no engine module), so it can be tested on its own. Protocol (chat commands, no new EXE):

    game -> server   /mcheck mode <0|1|2|3>          0 off, 1 = A, 2 = B, 3 = C; after entering the game and on
                                                     every change
                     /mcheck hit <id> <elapsed_ms>   the click; elapsed_ms = time since the ring was shown
    server -> game   MiningCheckModeV1 <mode>
                     MiningCheckV1 <id> <period_ms> <zone_center_deg> <good_deg> <great_deg> <timeout_ms> <mode>
                     MiningCheckResultV1 <id> <result> <value>     result 0 miss, 1 good, 2 great, 3 timeout;
                         value: A / B the swings saved (B: the credit added), C the chance bonus of this mining
                         in percentage points so far (after the cap)
                     CraftCheckV1 <great> <good> <miss>   a line of the "/craft state" snapshot (craftbookmodel)

Variant C "Během kopání": while the mining runs the server sends a ring at the interval configured on the server; a hit
raises this session's success chance and yield according to the server catalog.

The needle starts at the top (0 degrees) when the ring is shown and turns clockwise, 360 degrees per period_ms.
good_deg / great_deg are the whole widths of the zones centred on zone_center_deg. The SERVER decides the result
(its own clock, a ping tolerance); Zone() is only the local feedback while the needle turns.
"""
import json
import math
import os
import re

try:
	import builtins
except ImportError:
	import __builtin__ as builtins

MODE_OFF, MODE_A, MODE_B, MODE_C = 0, 1, 2, 3
MODES = (MODE_OFF, MODE_A, MODE_B, MODE_C)
DEFAULT_MODE = MODE_C        # owner 8. 10.: on unless the player switched it off (an explicit Off is stored)
MISS, GOOD, GREAT, TIMEOUT = 0, 1, 2, 3
RESULTS = (MISS, GOOD, GREAT, TIMEOUT)

CHECK, RESULT, MODE, CRAFT_CHECK = 'MiningCheckV1', 'MiningCheckResultV1', 'MiningCheckModeV1', 'CraftCheckV1'
CRAFT_CHECK_FIELDS = ('great', 'good', 'miss')

MAX_ID = 2 ** 32 - 1
MAX_MS = 60000               # a period or a timeout longer than a minute is not a skill check
MAX_VALUE = 2 ** 63 - 1

COMMAND_MODE = '/mcheck mode %d'
COMMAND_HIT = '/mcheck hit %d %d'

STORE_VERSION = 1
_REAL_OPEN = getattr(builtins, 'old_open', builtins.open)

# (Czech, English) fallbacks; the locale table may override them (localeInfo MINING_CHECK_<key>).
TEXTS = {
	'MODE_OFF': ('Vypnuto', 'Off'),
	'MODE_A': ('A - nápřah', 'A - swing'),
	'MODE_B': ('B - další těžba', 'B - next mining'),
	'MODE_C': ('C - během kopání', 'C - while mining'),
	'MODE_ON': ('Zapnuto', 'On'),
	'GREAT': ('VÝBORNĚ', 'GREAT'),
	'GOOD': ('DOBŘE', 'GOOD'),
	'MISS': ('VEDLE', 'MISSED'),
	'TIMEOUT': ('VYPRŠELO', 'TOO LATE'),
	'SWINGS_1': ('-%d úder', '-%d swing'),
	'SWINGS_2': ('-%d údery', '-%d swings'),
	'SWINGS_5': ('-%d úderů', '-%d swings'),
	'NEXT': ('%s při další těžbě', '%s on the next mining'),
	'FULL': ('plný počet úderů', 'full number of swings'),
	'BONUS': ('+%d %% šance (celkem +%d %%)', '+%d %% chance (total +%d %%)'),
	'TOTAL': ('šance celkem +%d %%', 'chance in total +%d %%'),
	'HINT_CLICK': ('Klikni, když je ručička v zóně', 'Click when the needle is in the zone'),
	'HINT_KEY': ('Klikni nebo stiskni %s', 'Click or press %s'),
	'SPACE': ('Mezerník', 'Space'),
}


def Tr(key):
	"""Player text: the locale table (localeInfo MINING_CHECK_<key>) or the Czech / English fallback."""
	czech, english = TEXTS[key]
	try:
		import localeInfo
		value = getattr(localeInfo, 'MINING_CHECK_' + key, None)
		if isinstance(value, str) and value:
			return value
	except Exception:
		pass
	try:
		import app
		return czech if app.GetLocalePath().replace('\\', '/').lower().endswith('/cz') else english
	except Exception:
		return czech


def _number(token, maximum=MAX_VALUE):
	"""A whole number 0..maximum from a server token, else None."""
	if isinstance(token, bool):
		return None
	if isinstance(token, int):
		value = token
	else:
		text = str(token).strip()
		if not text.isdigit():
			return None
		value = int(text)
	if value < 0 or value > maximum:
		return None
	return value


def _numbers(args, count, maximum=MAX_VALUE):
	if args is None or len(args) != count:
		return None
	values = [_number(arg, maximum) for arg in args]
	if any(value is None for value in values):
		return None
	return values


class Check(object):
	"""One MiningCheckV1: the ring the player has to hit."""

	def __init__(self, check_id, period_ms, zone_center, good_deg, great_deg, timeout_ms, mode):
		self.id = check_id
		self.period_ms = period_ms
		self.zone_center = zone_center % 360
		self.good_deg = good_deg
		self.great_deg = great_deg
		self.timeout_ms = timeout_ms
		self.mode = mode

	def Angle(self, elapsed_ms):
		return Angle(elapsed_ms, self.period_ms)

	def Zone(self, elapsed_ms):
		return Zone(self.Angle(elapsed_ms), self.zone_center, self.good_deg, self.great_deg)


class Result(object):
	"""One MiningCheckResultV1."""

	def __init__(self, check_id, result, value):
		self.id = check_id
		self.result = result
		self.value = value
		self.swings_saved = value      # A / B: the swings saved; C: the chance bonus of the mining so far


def ParseCheck(args):
	"""MiningCheckV1 fields -> Check, or None for a malformed line (a zero period, degrees over 360, an unknown
	mode, a missing or extra field)."""
	values = _numbers(args, 7)
	if values is None:
		return None
	check_id, period, centre, good, great, timeout, mode = values
	if check_id > MAX_ID or not 0 < period <= MAX_MS or not 0 < timeout <= MAX_MS or centre > 360:
		return None
	if not 0 < good <= 360 or great > good or mode not in MODES:
		return None
	return Check(check_id, period, centre, good, great, timeout, mode)


def ParseResult(args):
	values = _numbers(args, 3)
	if values is None or values[0] > MAX_ID or values[1] not in RESULTS or values[2] > 100:
		return None
	return Result(*values)


def ParseMode(args):
	values = _numbers(args, 1)
	if values is None or values[0] not in MODES:
		return None
	return values[0]


def ParseCraftCheck(args):
	"""CraftCheckV1 <great> <good> <miss> -> the three counters, or None."""
	return _numbers(args, len(CRAFT_CHECK_FIELDS))


# --------------------------------------------------------------------------- needle and zones
def Angle(elapsed_ms, period_ms):
	"""The needle angle in degrees (0 = top, clockwise) ``elapsed_ms`` after the ring was shown."""
	period = float(period_ms)
	if period <= 0:
		return 0.0
	return (max(0.0, float(elapsed_ms)) % period) * 360.0 / period


def Distance(a, b):
	"""Circular distance of two angles in degrees (0..180)."""
	d = abs(float(a) - float(b)) % 360.0
	return 360.0 - d if d > 180.0 else d


def Zone(angle, centre, good_deg, great_deg):
	"""GREAT / GOOD / MISS of a needle angle (local feedback only; the server decides the result)."""
	d = Distance(angle, centre)
	if d <= great_deg / 2.0:
		return GREAT
	if d <= good_deg / 2.0:
		return GOOD
	return MISS


def ElapsedMs(shown_at, now):
	"""Whole milliseconds since the ring was shown (app.GetTime seconds), never negative."""
	return max(0, int(round((float(now) - float(shown_at)) * 1000.0)))


def Wedges(centre, width, step):
	"""Centres (degrees) of the ``step`` degree wedges that draw a zone of ``width`` degrees around ``centre``: the
	fewest wedges with a spacing <= step (a wedge texture is drawn a little wider than its step, no seam shows)."""
	width = max(0.0, min(360.0, float(width)))
	if width <= 0:
		return []
	count = max(1, int(-(-width // float(step))))
	spacing = width / count
	return [(centre - width / 2.0 + spacing * (index + 0.5)) % 360.0 for index in range(count)]


# --------------------------------------------------------------------------- the moment the player saw (low FPS)
MAX_FRAME = 0.1              # s: a longer frame is a hitch, not the frame rate


def SeenTime(now, prev_draw, last_draw):
	"""When the needle the player saw at the hit was drawn (seconds of the same clock as the draws).

	The ring draws its needle every rendered frame (OnRender) at the time of that frame. The game handles a hit late
	by up to a frame: the mouse button in the message pump after the frame (and its frame-limiter wait) ended, the
	key in the next frame (DirectInput is polled after the timer advanced) - while the screen still showed the frame
	before. Taking the time of the hit as it is (or app.GetTime, the start of the frame) measured the click one to two
	frames late: at 30 FPS 10 to 20 degrees of a 1.1 s turn, more than the whole "výborně" zone, so low frame rates
	lost VÝBORNĚ. A press during one frame interval is equally likely at any moment of it, so the frame on the screen
	at the press was drawn on average one frame interval before the hit was handled: now - (last_draw - prev_draw),
	kept between the last two draws. Without two draws it is the last draw (or now)."""
	now = float(now)
	if last_draw is None:
		return now
	last_draw = float(last_draw)
	if prev_draw is None:
		return min(now, last_draw)
	prev_draw = float(prev_draw)
	frame = max(0.0, min(MAX_FRAME, last_draw - prev_draw))
	return max(prev_draw, min(last_draw, now - frame))


# --------------------------------------------------------------------------- where the ring stands
HEAD_HEIGHT = 180            # world units above the feet: the top of the miner (chr.GetProjectPosition)
OFF_SCREEN = (-100, -100)    # chr.GetProjectPosition of a character that is not drawn


def Anchor(head, feet, screen):
	"""The ring centre beside the miner's shoulder: right of the character by about 0.4 of its height on the screen
	plus the ring's radius (100..190 px; the ring is 1.5x bigger since the owner's game test), a fifth of its height
	below the top. None when the character is not on the screen."""
	if head is None or feet is None or tuple(head) == OFF_SCREEN or tuple(feet) == OFF_SCREEN:
		return None
	(hx, hy), (fx, fy) = head, feet
	width, height = screen
	if not (0 <= hx < width and 0 <= hy < height):
		return None
	tall = max(0.0, float(fy) - float(hy))
	return (float(hx) + max(100.0, min(190.0, 0.4 * tall + 76.0)), float(hy) + 0.22 * tall)


def Follow(current, target, dt, rate=14.0, snap=400.0):
	"""Smooth following of the anchor (the projection jumps a little while the camera turns): an exponential step
	towards ``target``; a jump longer than ``snap`` px (a warp, a turned camera) is taken at once."""
	if current is None:
		return target
	dx, dy = target[0] - current[0], target[1] - current[1]
	if math.hypot(dx, dy) > snap:
		return target
	k = 1.0 - math.exp(-rate * max(0.0, min(0.1, float(dt))))
	return (current[0] + dx * k, current[1] + dy * k)


# --------------------------------------------------------------------------- feedback over time
APPEAR = 0.15                # s: the ring comes in (115 % -> 100 %, transparent -> opaque)
PRESS = 0.12                 # s: the ring gives a little under the hit (local, before the server answers)
RESULT_SECONDS = 1.4         # s: the result shows, then the window hides
RING_FADE = (0.6, 0.9)       # s after the result: the ring fades out, the text stays
TEXT_FADE = 0.3              # s: the text fades out at the end


def Clamp01(t):
	return max(0.0, min(1.0, float(t)))


def EaseOut(t):
	t = Clamp01(t)
	return 1.0 - (1.0 - t) ** 3


def Appear(t):
	"""(scale, alpha) of the ring ``t`` s after it was first drawn."""
	k = EaseOut(t / APPEAR)
	return 1.0 + 0.15 * (1.0 - k), k


def Press(t):
	"""Scale factor of the ring ``t`` s after the hit (a 3 % give, back by PRESS)."""
	if not 0.0 <= t < PRESS:
		return 1.0
	return 1.0 - 0.03 * math.sin(math.pi * t / PRESS)


SPARK_LIFE = 0.2             # s: steel sparks are fast
CHIP_LIFE = 0.38             # s: stone chips fly, fall and fade
FLARE_LIFE = 0.14            # s: the white-hot star where the pickaxe strikes


def Punch(t, peak, rise=0.05, settle=0.25):
	"""Scale of a punch: up to 1 + ``peak`` in ``rise`` s, then back to 1.0 by ``settle`` s with a damped small
	undershoot (about a fifth of the punch)."""
	if t < 0.0 or t >= settle:
		return 1.0
	if t < rise:
		return 1.0 + peak * EaseOut(t / rise)
	k = (t - rise) / (settle - rise)
	return 1.0 + peak * (1.0 - k) ** 2 * math.cos(1.5 * math.pi * k)


class Feedback(object):
	"""The look of a result ``t`` s after it arrived (krok2-vzhled 06-zpetna-vazba-cas.png, owner round 2: "jako
	úder krumpáče do kamene"):

	VÝBORNĚ  0-0.14 s a white-hot four-point flare where the needle struck, popping 60 -> 130 %; 0-0.2 s steel
	         sparks shoot out of it; 0-0.38 s stone chips fly out, fall and fade; the ring punches to 112 % and
	         settles; 0-0.25 s the zone flashes white-hot then blood red; 0.03-0.40 s a blood red ring flies out to
	         145 %; the headline rises 8 px into place.
	DOBŘE    softer: a weaker flash, a 4 % punch, a faint ring to 125 %; no flare, no sparks, no chips.
	VEDLE    the ring jerks +-3 px for 0.24 s and turns grey (60 %); no flash, no burst.
	Then the ring fades out (RING_FADE) and the text at the end (TEXT_FADE)."""

	def __init__(self, result, t):
		t = max(0.0, float(t))
		great, good = result == GREAT, result == GOOD
		hit = great or good
		self.flash = (1.0 if great else 0.6) * (1.0 - Clamp01(t / 0.25)) if hit else 0.0
		self.scale = Punch(t, 0.12 if great else 0.04) if hit else 1.0
		b = Clamp01((t - 0.03) / 0.37)
		if hit and 0.0 < b < 1.0:
			self.burst_scale = 1.0 + (0.45 if great else 0.25) * EaseOut(b)
			self.burst_alpha = (0.9 if great else 0.45) * (1.0 - b)
		else:
			self.burst_scale, self.burst_alpha = 1.0, 0.0
		self.sparks = Clamp01(t / SPARK_LIFE) if great and t < SPARK_LIFE else None
		self.chips = Clamp01(t / CHIP_LIFE) if great and t < CHIP_LIFE else None
		if great and t < FLARE_LIFE:
			k = t / FLARE_LIFE
			self.flare = (0.6 + 0.7 * math.sin(0.5 * math.pi * min(1.0, 1.3 * k)), 1.0 - Clamp01((k - 0.4) / 0.6))
		else:
			self.flare = None
		self.shake = int(round(3.0 * math.sin(2.0 * math.pi * t / 0.08) * (1.0 - t / 0.24))) \
			if result == MISS and t < 0.24 else 0
		self.grey = 0.6 if result == MISS else 1.0
		f0, f1 = RING_FADE
		self.ring_alpha = 1.0 - Clamp01((t - f0) / (f1 - f0))
		self.text_rise = int(round(8.0 * (1.0 - EaseOut(t / 0.18))))
		self.text_alpha = Clamp01(t / 0.12) * (1.0 - Clamp01((t - (RESULT_SECONDS - TEXT_FADE)) / TEXT_FADE))


def Polar(cx, cy, r, degrees):
	"""(x, y) of radius ``r`` at an angle clockwise from the top (screen coordinates, y down)."""
	a = math.radians(degrees)
	return cx + r * math.sin(a), cy - r * math.cos(a)


def _seed(check_id, index):
	return (int(check_id) * 7919 + index * 104729) % 1000 / 1000.0


def Sparks(check_id, angle, count=8):
	"""(angle, travel px, length factor) of the steel sparks of a VÝBORNĚ: a cone of +-35 degrees around the angle
	the needle struck, a little different for every check (deterministic)."""
	out = []
	for index in range(count):
		seed = _seed(check_id, index)
		spread = -35.0 + 70.0 * (index + 0.5) / count + (seed - 0.5) * 8.0
		out.append(((angle + spread) % 360.0, 10.0 + 10.0 * seed, 0.8 + 0.4 * ((seed * 3.0) % 1.0)))
	return out


GRAVITY = 380.0              # px/s^2 on the screen


def Chips(check_id, angle, count=6):
	"""(vx, vy, spin deg/s, start turn, size, texture 1..3) of the stone chips of a VÝBORNĚ: out of the struck point
	within +-60 degrees, kicked up a little, then falling (GRAVITY)."""
	out = []
	for index in range(count):
		seed = _seed(check_id, index + 17)
		a = math.radians(angle - 60.0 + 120.0 * (index + 0.5) / count + (seed - 0.5) * 10.0)
		speed = 90.0 + 60.0 * seed
		vx, vy = math.sin(a) * speed, -math.cos(a) * speed - (40.0 + 40.0 * ((seed * 7.0) % 1.0))
		spin = (-1.0 if index % 2 else 1.0) * (300.0 + 400.0 * seed)
		out.append((vx, vy, spin, 360.0 * ((seed * 13.0) % 1.0), 0.8 + 0.4 * ((seed * 5.0) % 1.0), 1 + index % 3))
	return out


def ChipAt(chip, t):
	"""(dx, dy, turn) of a chip ``t`` s after the hit."""
	vx, vy, spin, turn, unused, unused2 = chip
	return vx * t, vy * t + 0.5 * GRAVITY * t * t, turn + spin * t


def Pips(streak):
	"""Diamonds under the text for VÝBORNĚ in a row: none below 3, at most 5."""
	return 0 if streak < 3 else min(5, int(streak))


# --------------------------------------------------------------------------- texts
def Swings(count):
	"""-1 úder, -2 údery, -5 úderů (Czech plural)."""
	count = int(count)
	if count == 1:
		key = 'SWINGS_1'
	elif 2 <= count <= 4:
		key = 'SWINGS_2'
	else:
		key = 'SWINGS_5'
	return Tr(key) % count


def ResultTexts(result, swings_saved, mode):
	"""(headline, detail) of a server result: VÝBORNĚ / DOBŘE / MINUL / VYPRŠELO and "-N úder(y)" (mode B: "... při
	další těžbě"); a miss or a timeout of mode A: "plný počet úderů", of mode B no detail. Mode C: ``swings_saved`` is
	the value field = the chance bonus of this mining so far: "+6 % šance (celkem +12 %)" (the gain of this hit is
	its nominal bonus, at most the total), a miss "šance celkem +12 %" (nothing without a bonus)."""
	headline = Tr({GREAT: 'GREAT', GOOD: 'GOOD', MISS: 'MISS', TIMEOUT: 'TIMEOUT'}.get(result, 'MISS'))
	if mode == MODE_C:
		total = max(0, int(swings_saved))
		return headline, (Tr('TOTAL') % total if total else '')
	if swings_saved > 0 and result in (GOOD, GREAT):
		detail = Swings(swings_saved)
		if mode == MODE_B:
			detail = Tr('NEXT') % detail
	elif mode == MODE_A:
		detail = Tr('FULL')
	else:
		detail = ''
	return headline, detail


def ModeLabels():
	"""The player's switch: Vypnuto | Zapnuto (owner after the game test 7. 10.: C is clearly the best, A and B
	are dropped from the switch; the server still accepts them)."""
	return [(MODE_OFF, Tr('MODE_OFF')), (MODE_C, Tr('MODE_ON'))]


def Migrate(mode):
	"""A stored A or B (the trial switch of krok 2) becomes C."""
	return MODE_C if mode in (MODE_A, MODE_B) else mode


# --------------------------------------------------------------------------- the chosen mode, per character
def SafeName(name):
	value = re.sub(r'[^A-Za-z0-9_.-]+', '_', str(name or 'character'))
	value = value.strip('._')
	return value[:64] or 'character'


class ModeStore(object):
	"""The mode chosen for one character in UserData/mining_check_<name>.json (like the quick buffs); a missing or
	broken file is DEFAULT_MODE (Zapnuto). ``explicit`` is True once the player's own choice is stored or loaded:
	only then does the server's word overwrite the file, so a server that refuses C does not freeze the default
	at Vypnuto."""

	def __init__(self, storage_directory='UserData'):
		self.storage_directory = storage_directory
		self.name = ''
		self.path = ''
		self.mode = DEFAULT_MODE
		self.explicit = False

	def SetIdentity(self, name):
		"""Loads the mode of character ``name``; True when the character changed."""
		name = str(name or '')
		path = os.path.join(self.storage_directory, 'mining_check_%s.json' % SafeName(name))
		if path == self.path:
			return False
		self.name, self.path = name, path
		stored = self.Stored()
		self.explicit = stored is not None
		self.mode = DEFAULT_MODE if stored is None else stored
		return True

	def Stored(self):
		"""The stored choice (A/B migrated to C) or None for a missing or broken file."""
		try:
			with _REAL_OPEN(self.path, 'rb') as handle:
				payload = json.loads(handle.read().decode('utf-8'))
		except Exception:
			return None
		mode = payload.get('mode') if isinstance(payload, dict) else None
		if isinstance(mode, bool) or mode not in MODES:
			return None
		return Migrate(mode)

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
