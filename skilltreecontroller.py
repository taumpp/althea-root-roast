# -*- coding: utf-8 -*-

try:
	_INTEGER_TYPES = (int, long)
except NameError:
	_INTEGER_TYPES = (int,)


class SkillTreeUpgradeController(object):

	def __init__(self, model, sender, clock, refreshSender,
		retrySeconds=5.0, maximumRetries=2):
		if model is None or not callable(getattr(model, "BeginUpgrade", None)):
			raise TypeError("model must provide BeginUpgrade")
		if not callable(sender) or not callable(clock) or not callable(refreshSender):
			raise TypeError("sender, clock and refreshSender must be callable")
		if isinstance(retrySeconds, bool) or retrySeconds <= 0:
			raise ValueError("retrySeconds must be positive")
		if isinstance(maximumRetries, bool) or not isinstance(maximumRetries, _INTEGER_TYPES):
			raise TypeError("maximumRetries must be an integer")
		if maximumRetries < 0 or maximumRetries > 5:
			raise ValueError("maximumRetries must be between zero and five")

		self.model = model
		self.sender = sender
		self.clock = clock
		self.refreshSender = refreshSender
		self.retrySeconds = float(retrySeconds)
		self.maximumRetries = int(maximumRetries)
		self.trackedIdentity = None
		self.retryDeadline = None
		self.retryCount = 0
		self.refreshPending = False

	def Reset(self):
		self.trackedIdentity = None
		self.retryDeadline = None
		self.retryCount = 0
		self.refreshPending = False

	def RequestUpgrade(self, nodeId):
		request = self.model.BeginUpgrade(nodeId)
		if request is None:
			return False
		try:
			self.sender(*request)
		except Exception:
			self.model.CancelPending(request[1], request[2])
			self.Reset()
			return False
		self.__Track(request)
		return True

	def Sync(self):
		pending = self.model.GetPendingRequest()
		if pending is None or pending.get("kind") == "dismantle":
			self.Reset()
			return False
		request = self.__PendingTuple(pending)
		identity = self.__Identity(request)
		if identity != self.trackedIdentity:
			self.__Track(request)
		return True

	def Update(self):
		self.Sync()
		if self.model.GetPendingRequest() is None or self.retryDeadline is None:
			return False
		if self.clock() < self.retryDeadline:
			return False
		if self.retryCount >= self.maximumRetries:
			try:
				refreshed = self.refreshSender()
			except Exception:
				refreshed = False
			if refreshed is False:
				self.retryDeadline = self.clock() + self.retrySeconds
				return False
			self.refreshPending = True
			self.retryDeadline = None
			return True

		pending = self.model.GetPendingRequest()
		if pending is None:
			self.Reset()
			return False
		request = self.__PendingTuple(pending)
		self.retryCount += 1
		self.retryDeadline = self.clock() + self.retrySeconds
		try:
			self.sender(*request)
		except Exception:
			return False
		return True

	def ResolveFromAuthoritativeSnapshot(self):
		if not self.refreshPending:
			return False
		pending = self.model.GetPendingRequest()
		if pending is None:
			self.Reset()
			return True
		if not self.model.CancelPending(
			pending["session_nonce"], pending["request_sequence"],
		):
			return False
		self.Reset()
		return True

	def __Track(self, request):
		self.trackedIdentity = self.__Identity(request)
		self.retryDeadline = self.clock() + self.retrySeconds
		self.retryCount = 0

	def __Identity(self, request):
		return (request[0], request[1], request[2], request[3])

	def __PendingTuple(self, pending):
		return (
			pending["node_id"],
			pending["session_nonce"],
			pending["request_sequence"],
			pending["expected_revision"],
		)
