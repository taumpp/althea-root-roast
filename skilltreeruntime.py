# -*- coding: utf-8 -*-

import dbg
import skilltreeactivationcontroller
import skilltreecontroller
import skilltreemodel


class SkillTreeRuntime(object):

	def __init__(self, window, netModule, clock):
		if window is None or netModule is None or not callable(clock):
			raise TypeError("window, network module and clock are required")
		wireNodeIds = getattr(getattr(window, "layout", None), "WIRE_NODE_IDS", None)
		if wireNodeIds is None:
			raise TypeError("window layout must provide WIRE_NODE_IDS")

		self.window = window
		self.net = netModule
		self.clock = clock
		self.destroyed = False
		self.presentationObserver = None
		self.initialSyncUntil = None
		self.nextInitialSync = None
		self.dismantleRequest = None
		self.dismantleRetryAt = None
		self.model = skilltreemodel.SkillTreeModel(
			wireNodeIds, rankValues=window.layout.RANK_VALUES,
		)
		self.upgrades = skilltreecontroller.SkillTreeUpgradeController(
			self.model, netModule.SendSkillTreeUpgrade, clock, self.Open,
		)
		self.activation = skilltreeactivationcontroller.SkillTreeActivationController(
			self.model,
			netModule.SendSkillTreeSetActivation,
			netModule.SendSkillTreeRenewActivation,
			clock,
			self.Open,
		)
		if not self.window.SetModel(self.model):
			raise TypeError("window rejected Skill Tree model")
		self.window.SetInteractionHandlers(
			self.upgrades.RequestUpgrade,
			self.RequestActivation,
			self.RequestRenew,
		)
		self.window.SetOpenHandler(self.Open)
		self.window.SetDismantleHandler(self.RequestDismantle)
		self.__RefreshPresentation()

	def SetPresentationObserver(self, observer):
		self.presentationObserver = observer
		self.__RefreshPresentation()

	def Start(self):
		self.initialSyncUntil = self.clock() + 60.0
		self.nextInitialSync = self.clock() + 1.0

	def Open(self):
		if self.destroyed:
			return False
		try:
			self.net.SendSkillTreeOpen()
		except Exception:
			return False
		return True

	def RequestActivation(self, desiredEnabled, activationRevision=None):
		if self.destroyed:
			return False
		state = self.model.GetActivationState()
		if state is None:
			return False
		if (
			activationRevision is not None
			and activationRevision != state["activation_revision"]
		):
			return False
		accepted = self.activation.RequestSetActivation(bool(desiredEnabled))
		self.activation.Sync()
		self.__RefreshPresentation()
		return bool(accepted)

	def RequestRenew(self, activationRevision=None):
		if self.destroyed:
			return False
		state = self.model.GetActivationState()
		if state is None:
			return False
		if (
			activationRevision is not None
			and activationRevision != state["activation_revision"]
		):
			return False
		accepted = self.activation.RequestRenew()
		self.activation.Sync()
		self.__RefreshPresentation()
		return bool(accepted)

	def RequestDismantle(self, slots):
		if self.destroyed:
			return False
		request = self.model.BeginDismantle(slots)
		if request is None:
			dbg.TraceError("SkillTree dismantle not queued: ready=%s refresh=%s pending=%s activation_pending=%s" % (
				self.model.IsReady(), self.model.NeedsRefresh(),
				self.model.GetPendingRequest() is not None,
				self.model.pendingActivationRequest is not None))
			if self.model.NeedsRefresh():
				self.Open()
			return False
		try:
			self.net.SendSkillTreeDismantle(*request)
		except Exception as error:
			dbg.TraceError("SkillTree dismantle send failed: %s" % error)
			self.model.CancelPending(request[1], request[2])
			return False
		self.dismantleRequest = request
		self.dismantleRetryAt = self.clock() + 5.0
		self.__RefreshPresentation()
		return True

	def Update(self):
		if self.destroyed:
			return False
		if self.nextInitialSync is not None:
			if self.model.IsReady() or self.clock() >= self.initialSyncUntil:
				self.nextInitialSync = None
			elif self.clock() >= self.nextInitialSync:
				self.nextInitialSync = self.clock() + 5.0
				self.Open()
		upgradeChanged = self.upgrades.Update()
		activationChanged = self.activation.Update()
		if self.dismantleRequest and self.clock() >= self.dismantleRetryAt:
			pending = self.model.GetPendingRequest()
			if pending and pending.get("kind") == "dismantle":
				try:
					self.net.SendSkillTreeDismantle(*self.dismantleRequest)
				except Exception:
					pass
				self.dismantleRetryAt = self.clock() + 5.0
			else:
				self.dismantleRequest = None
				self.dismantleRetryAt = None
		if upgradeChanged or activationChanged:
			self.__RefreshPresentation()
		return bool(upgradeChanged or activationChanged)

	def Destroy(self):
		if self.destroyed:
			return False
		if self.presentationObserver:
			self.presentationObserver(None, {})
		self.presentationObserver = None
		self.destroyed = True
		self.window.SetOpenHandler(None)
		self.window.SetInteractionHandlers(None, None, None)
		self.window.SetDismantleHandler(None)
		self.model.Destroy()
		self.window.model = None
		self.upgrades.Reset()
		self.activation.Reset()
		return True

	def OnCatalog(self, *packet):
		return self.__Apply(self.model.ApplyCatalog, packet)

	def OnSnapshot(self, *packet):
		accepted = self.__Apply(self.model.ApplySnapshot, packet)
		if accepted and self.upgrades.ResolveFromAuthoritativeSnapshot():
			self.__RefreshPresentation()
		return accepted

	def OnUpgradeResult(self, *packet):
		accepted = self.__Apply(self.model.ApplyUpgradeResult, packet)
		if accepted and self.model.NeedsRefresh():
			self.Open()
		return accepted

	def OnDismantleResult(self, *packet):
		accepted = self.__Apply(self.model.ApplyDismantleResult, packet)
		if accepted:
			if packet[0] != 0:
				dbg.TraceError("SkillTree dismantle rejected by server: result=%s" % packet[0])
			self.dismantleRequest = None
			self.dismantleRetryAt = None
			self.window.OnDismantleResult(packet[0] == 0)
			if self.model.NeedsRefresh():
				self.Open()
		return accepted

	def OnError(self, *packet):
		return self.__Apply(self.model.ApplyError, packet)

	def OnActivationState(self, *packet):
		accepted = self.__Apply(self.model.ApplyActivationState, packet)
		if accepted and self.activation.ResolveFromAuthoritativeState():
			self.__RefreshPresentation()
		return accepted

	def OnActivationResult(self, *packet):
		return self.__Apply(self.model.ApplyActivationResult, packet)

	def __Apply(self, receiver, packet):
		if self.destroyed or not receiver(*packet):
			return False
		self.upgrades.Sync()
		self.activation.Sync()
		self.__RefreshPresentation()
		return True

	def __RefreshPresentation(self):
		if self.destroyed:
			return False
		state = self.activation.GetPresentationState()
		if self.presentationObserver:
			self.presentationObserver(
				self.activation.GetPresentationState(False) if self.model.IsReady() else None,
				self.model.GetNodePresenters(),
			)
		if state is None:
			self.window.SetActivationLoadingState()
			self.window.ApplyModel(False)
			return False

		self.window.SetActivationState(
			state["enabled"],
			state["remaining_seconds"],
			state["max_seconds"],
			state["activation_revision"],
		)
		self.window.SetActivationPending(state["request_pending"])
		self.window.SetRenewCostPayload(state["renew_cost"])
		return bool(self.window.ApplyModel(state["enabled"]))
