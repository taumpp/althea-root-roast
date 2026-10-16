# Server-owned availability of pausable features (FeatureAvailabilityV1).
#
# The server (althea/server-src common/feature_pause_switch.h) sends
# "FeatureAvailabilityV1 <name> <available 0|1> <refused 0|1>" at EnterGame,
# on every pause/resume (refused 0) and with every refused request of this
# player (refused 1). The client keeps only that state: it never decides on
# its own that a feature is paused, so the owner can switch a feature back on
# without a client release. A feature the server has not mentioned (older
# server) counts as available and keeps its previous behaviour.

RANKINGS = "rankings"
RANKED_ARENA = "ranked_arena"

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
	return _available.get(name, True)


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
