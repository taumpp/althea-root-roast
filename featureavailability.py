# Server-owned availability of pausable features (FeatureAvailabilityV1).
#
# The server (althea/server-src common/feature_pause_switch.h) sends
# "FeatureAvailabilityV1 <name> <available 0|1> <refused 0|1>" at EnterGame,
# on every pause/resume (refused 0) and with every refused request of this
# player (refused 1). The client keeps only that state: it never decides on
# its own that a feature is paused, so the owner can switch a feature back on
# without a client release. A feature the server has not mentioned (older
# server) counts as available and keeps its previous behaviour, except the
# features in HIDDEN_UNTIL_ANNOUNCED and LOCKED_UNTIL_ANNOUNCED.

RANKINGS = "rankings"
RANKED_ARENA = "ranked_arena"
GUILD_ARENA = "guild_arena"

# Features whose entry points stay hidden until the server says they are open
# The rated arena launcher stays hidden while the server disables it.
HIDDEN_UNTIL_ANNOUNCED = (RANKED_ARENA,)

# Features that count as closed until the server says they are open, but whose
# entry points stay visible as locked ("Připravujeme"): the guild tab of the
# rated arena window (guild wars, the guild arena queue, Meley). A server
# without the guild arena never announces it and has no /guild_arena.
LOCKED_UNTIL_ANNOUNCED = (GUILD_ARENA,)

_available = {}
_listener = None


def _Flag(value):
	try:
		return int(value) != 0
	except (TypeError, ValueError):
		return None


def Receive(name, available, refused):
	isAvailable = _Flag(available)
	isRefused = _Flag(refused)
	if not name or isAvailable is None or isRefused is None:
		return
	_available[name] = isAvailable
	if _listener:
		_listener(name, isAvailable, isRefused)


class Receiver(object):
	# stringCommander registers only bound methods (it reads __func__ and
	# counts self), so the server command goes through this instance.
	def Receive(self, name, available, refused):
		Receive(name, available, refused)


receiver = Receiver()


def IsAvailable(name):
	return _available.get(name, name not in HIDDEN_UNTIL_ANNOUNCED and name not in LOCKED_UNTIL_ANNOUNCED)


def _MatchmakingOffered():
	# The native matchmaking offer (pvpmatchmakingv1), which only a game core
	# with ENABLE_PVP_MATCHMAKING sends at EnterGame. Without the native module
	# (a build without the arena) there is nothing to show.
	try:
		import pvpmatchmaking
		return bool(pvpmatchmaking.IsAvailable())
	except Exception:
		return False


def IsShown(name):
	# Whether the entry points of a feature (launchers, "More" rows, settings
	# rows) are shown. The rated arena needs both server switches: its
	# ranked_arena_open flag (this module) and the matchmaking offer of the
	# core (CONFIG ENABLE_PVP_MATCHMAKING); either one off hides it.
	if not IsAvailable(name):
		return False
	if name == RANKED_ARENA:
		return _MatchmakingOffered()
	return True


def ShownKey():
	# One value per hidden-until-announced feature; panels compare it every
	# frame and rebuild when it changes (a GM opens or pauses a feature live).
	return tuple(IsShown(name) for name in HIDDEN_UNTIL_ANNOUNCED)


def NotifyRefused(name):
	# A local click on a paused feature: the same answer as a server refusal,
	# without sending a request the server would refuse anyway.
	if _listener:
		_listener(name, False, True)


def SetListener(callback):
	global _listener
	_listener = callback


def ClearListener(callback):
	global _listener
	if _listener is callback:
		_listener = None
