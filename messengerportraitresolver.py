import app
import net
import player


LOOKUP_BY_PID = 1
LOOKUP_BY_EXACT_NAME = 2
STATUS_OK = 0
STATUS_NOT_FOUND = 1
STATUS_RATE_LIMITED = 2
STATUS_UNAVAILABLE = 3
STATUS_INVALID_REQUEST = 4

REQUEST_INTERVAL_SECONDS = 0.15
RATE_LIMIT_BACKOFF_SECONDS = 1.0
SEND_FAILURE_BACKOFF_SECONDS = 1.0
# A response that never arrives must not block every later portrait.
INFLIGHT_TIMEOUT_SECONDS = 5.0
# A temporarily unavailable profile service is asked again only after a pause
# instead of on every list render.
UNAVAILABLE_RETRY_SECONDS = 60.0

PORTRAIT_ROOT = "d:/ymir work/ui/game/crimson_ember/messenger/portrait/"
NEUTRAL_PORTRAIT = PORTRAIT_ROOT + "neutral_player.png"
PORTRAIT_BY_RACE = {
	0: PORTRAIT_ROOT + "war_m.png",
	1: PORTRAIT_ROOT + "ninja_w.png",
	2: PORTRAIT_ROOT + "sura_m.png",
	3: PORTRAIT_ROOT + "sham_w.png",
	4: PORTRAIT_ROOT + "war_f.png",
	5: PORTRAIT_ROOT + "ninja_m.png",
	6: PORTRAIT_ROOT + "sura_w.png",
	7: PORTRAIT_ROOT + "sham_m.png",
}


class PortraitResolver(object):
	def __init__(self, network=net, clock=None):
		self.network = network
		self.clock = clock or app.GetTime
		self.available = False
		self.queue = []
		self.queued = set()
		self.terminalMisses = set()
		self.deferredUntil = {}
		self.inflight = None
		self.inflightSince = 0.0
		self.nextAttemptAt = 0.0

	def SetCapability(self, enabled):
		try:
			advertised = bool(
				self.network.IsUnifiedMessengerPlayerProfileAvailable())
		except (AttributeError, RuntimeError):
			advertised = False
		self.available = bool(enabled and advertised)
		self.nextAttemptAt = 0.0
		self.terminalMisses.clear()
		self.deferredUntil.clear()
		if not self.available:
			self.queue = []
			self.queued.clear()
			self.inflight = None
			return
		self.Pump()

	def Resolve(self, pid=0, name=""):
		pid = int(pid or 0)
		name = str(name or "").strip()
		profile = self.__CachedProfile(pid, name)
		if profile:
			try:
				race = int(profile[2])
			except (IndexError, TypeError, ValueError):
				race = -1
			return PORTRAIT_BY_RACE.get(race, NEUTRAL_PORTRAIT)
		try:
			isLocalPlayer = bool(
				name and str(player.GetName()).strip().lower() == name.lower())
			if isLocalPlayer:
				race = int(player.GetRace())
				return PORTRAIT_BY_RACE.get(race, NEUTRAL_PORTRAIT)
		except (AttributeError, RuntimeError, TypeError, ValueError):
			pass
		if self.available:
			key = self.__RequestKey(pid, name)
			if (key is not None and key not in self.terminalMisses and
					not self.__Deferred(key)):
				self.__Enqueue(pid, name)
				self.Pump()
		return NEUTRAL_PORTRAIT

	def OnResponse(self, token, status, pid, name, race):
		if not self.inflight or int(token) != self.inflight[0]:
			return False
		request = self.inflight[1]
		self.inflight = None
		status = int(status)
		if status in (STATUS_NOT_FOUND, STATUS_INVALID_REQUEST):
			self.terminalMisses.add(request[3])
		elif status == STATUS_UNAVAILABLE:
			self.deferredUntil[request[3]] = self.clock() + UNAVAILABLE_RETRY_SECONDS
		elif status == STATUS_RATE_LIMITED:
			key = request[3]
			if key not in self.queued:
				self.queued.add(key)
				self.queue.insert(0, request)
			self.nextAttemptAt = max(
				self.nextAttemptAt, self.clock() + RATE_LIMIT_BACKOFF_SECONDS)
		self.Pump()
		return (status == STATUS_OK and int(pid) > 0
			and int(race) in PORTRAIT_BY_RACE)

	def Pump(self):
		if not self.available:
			return
		now = self.clock()
		if self.inflight and now - self.inflightSince >= INFLIGHT_TIMEOUT_SECONDS:
			# Unanswered request: retry it later with the normal pacing.
			request = self.inflight[1]
			self.inflight = None
			if request[3] not in self.queued:
				self.queued.add(request[3])
				self.queue.append(request)
		if self.inflight or not self.queue:
			return
		if now < self.nextAttemptAt:
			return
		mode, pid, name, key = self.queue.pop(0)
		self.queued.discard(key)
		try:
			token = self.network.SendUnifiedMessengerPlayerProfile(mode, pid, name)
		except (AttributeError, RuntimeError):
			token = None
		if token is None:
			self.queued.add(key)
			self.queue.append((mode, pid, name, key))
			self.nextAttemptAt = now + SEND_FAILURE_BACKOFF_SECONDS
			return
		self.inflight = (int(token), (mode, pid, name, key))
		self.inflightSince = now
		self.nextAttemptAt = now + REQUEST_INTERVAL_SECONDS

	def __CachedProfile(self, pid, name):
		try:
			if pid > 0:
				profile = self.network.GetUnifiedMessengerPlayerProfileByPid(pid)
				if profile:
					return profile
			if name:
				return self.network.GetUnifiedMessengerPlayerProfileByName(name)
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return None
		return None

	def __Deferred(self, key):
		until = self.deferredUntil.get(key)
		if until is None:
			return False
		if self.clock() >= until:
			del self.deferredUntil[key]
			return False
		return True

	def __RequestKey(self, pid, name):
		if pid > 0:
			return (LOOKUP_BY_PID, pid)
		if name:
			return (LOOKUP_BY_EXACT_NAME, name.lower())
		return None

	def __Enqueue(self, pid, name):
		key = self.__RequestKey(pid, name)
		if key is None or key in self.terminalMisses:
			return
		if pid > 0:
			request = (LOOKUP_BY_PID, pid, "", key)
		else:
			request = (LOOKUP_BY_EXACT_NAME, 0, name, key)
		if key in self.queued or (
				self.inflight and self.inflight[1][3] == key):
			return
		self.queued.add(key)
		self.queue.append(request)


resolver = PortraitResolver()


def ResolvePortrait(pid=0, name=""):
	return resolver.Resolve(pid, name)


def SetCapability(enabled):
	resolver.SetCapability(enabled)


def OnResponse(token, status, pid, name, race):
	return resolver.OnResponse(token, status, pid, name, race)


def Pump():
	resolver.Pump()
