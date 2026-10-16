# -*- coding: utf-8 -*-


class SkillTreeActivationController(object):

	def __init__(self, model, setSender, renewSender, clock, refreshSender,
		timeoutSeconds=8.0):
		if model is None:
			raise TypeError("model is required")
		for methodName in (
			"BeginSetActivation", "BeginRenewActivation", "CancelActivationPending",
			"GetActivationState", "GetPendingActivationRequest",
		):
			if not callable(getattr(model, methodName, None)):
				raise TypeError("model does not provide %s" % methodName)
		if (
			not callable(setSender) or not callable(renewSender)
			or not callable(clock) or not callable(refreshSender)
		):
			raise TypeError("senders, clock and refreshSender must be callable")
		if isinstance(timeoutSeconds, bool) or timeoutSeconds <= 0:
			raise ValueError("timeoutSeconds must be positive")

		self.model = model
		self.setSender = setSender
		self.renewSender = renewSender
		self.clock = clock
		self.refreshSender = refreshSender
		self.timeoutSeconds = float(timeoutSeconds)
		self.Reset()

	def Reset(self):
		self.authoritativeState = None
		self.stateFingerprint = None
		self.receivedAt = None
		self.trackedRequest = None
		self.timeoutAt = None
		self.lastPresentationKey = None
		self.refreshPending = False
		self.refreshRequest = None

	def Sync(self):
		changed = False
		state = self.model.GetActivationState()
		fingerprint = self.__StateFingerprint(state)
		if fingerprint != self.stateFingerprint:
			self.stateFingerprint = fingerprint
			self.authoritativeState = self.__CopyState(state)
			self.receivedAt = self.clock() if state is not None else None
			self.lastPresentationKey = self.__PresentationKey()
			changed = True

		pending = self.model.GetPendingActivationRequest()
		identity = self.__PendingIdentity(pending)
		if identity != self.trackedRequest:
			if self.refreshPending and identity != self.refreshRequest:
				self.refreshPending = False
				self.refreshRequest = None
			self.trackedRequest = identity
			self.timeoutAt = (
				self.clock() + self.timeoutSeconds
				if identity is not None
				else None
			)
			changed = True
		return changed

	def IsPending(self):
		return self.model.GetPendingActivationRequest() is not None

	def RequestSetActivation(self, desiredEnabled):
		request = self.model.BeginSetActivation(desiredEnabled)
		if request is None:
			return False
		try:
			self.setSender(*request)
		except Exception:
			self.model.CancelActivationPending(request[1], request[2])
			self.Sync()
			return False
		self.__TrackRequest(request[1], request[2])
		return True

	def RequestRenew(self):
		state = self.GetPresentationState()
		if state is None or state["remaining_seconds"] > state["max_seconds"] - 28800:
			return False
		request = self.model.BeginRenewActivation()
		if request is None:
			return False
		try:
			self.renewSender(*request)
		except Exception:
			self.model.CancelActivationPending(request[0], request[1])
			self.Sync()
			return False
		self.__TrackRequest(request[0], request[1])
		return True

	def Update(self):
		changed = self.Sync()
		pending = self.model.GetPendingActivationRequest()
		if pending is not None and self.timeoutAt is not None and self.clock() >= self.timeoutAt:
			try:
				refreshed = self.refreshSender()
			except Exception:
				refreshed = False
			if refreshed is False:
				self.timeoutAt = self.clock() + self.timeoutSeconds
			else:
				self.refreshPending = True
				self.refreshRequest = self.__PendingIdentity(pending)
				self.timeoutAt = None
			changed = True

		presentationKey = self.__PresentationKey()
		if presentationKey != self.lastPresentationKey:
			self.lastPresentationKey = presentationKey
			changed = True
		return changed

	def ResolveFromAuthoritativeState(self):
		if not self.refreshPending:
			return False
		pending = self.model.GetPendingActivationRequest()
		if pending is not None and self.__PendingIdentity(pending) != self.refreshRequest:
			self.refreshPending = False
			self.refreshRequest = None
			return False
		if pending is not None and not self.model.CancelActivationPending(
			pending["session_nonce"], pending["request_sequence"],
		):
			return False
		self.trackedRequest = None
		self.timeoutAt = None
		self.refreshPending = False
		self.refreshRequest = None
		self.Sync()
		return True

	def GetPresentationState(self, includePending=True):
		if self.authoritativeState is None:
			return None
		state = self.__CopyState(self.authoritativeState)
		remaining = state["remaining_seconds"]
		if state["enabled"] and self.receivedAt is not None:
			elapsed = max(0, int(self.clock() - self.receivedAt))
			remaining = max(0, remaining - elapsed)
		state["remaining_seconds"] = remaining
		state["enabled"] = bool(state["enabled"] and remaining > 0)
		pending = self.model.GetPendingActivationRequest()
		if (
			includePending and pending is not None
			and pending["kind"] == "set"
			and pending["session_nonce"] == state["session_nonce"]
			and pending["expected_revision"] == state["activation_revision"]
		):
			state["enabled"] = bool(pending["desired_enabled"] and remaining > 0)
		state["request_pending"] = self.IsPending()
		return state

	def __TrackRequest(self, sessionNonce, requestSequence):
		self.trackedRequest = (sessionNonce, requestSequence)
		self.refreshPending = False
		self.refreshRequest = None
		self.timeoutAt = self.clock() + self.timeoutSeconds
		self.lastPresentationKey = self.__PresentationKey()

	def __PendingIdentity(self, pending):
		if pending is None:
			return None
		return (pending["session_nonce"], pending["request_sequence"])

	def __StateFingerprint(self, state):
		if state is None:
			return None
		return (
			state["tree_version"], state["activation_revision"],
			state["session_nonce"], state["remaining_seconds"],
			state["max_seconds"], state["enabled"],
			state["renew_cost"]["yang"],
			tuple(
				(item["vnum"], item["count"])
				for item in state["renew_cost"]["items"]
			),
		)

	def __CopyState(self, state):
		if state is None:
			return None
		copy = dict(state)
		copy["renew_cost"] = {
			"yang": state["renew_cost"]["yang"],
			"items": [dict(item) for item in state["renew_cost"]["items"]],
		}
		return copy

	def __PresentationKey(self):
		state = self.GetPresentationState()
		if state is None:
			return None
		return (
			state["activation_revision"], state["enabled"],
			state["remaining_seconds"], state["request_pending"],
		)
