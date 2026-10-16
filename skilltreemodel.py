# -*- coding: utf-8 -*-

import skilltreecatalog

try:
	import skilltreeapplytypes
except ImportError:
	skilltreeapplytypes = None

try:
	import skilltreelocale
except ImportError:
	skilltreelocale = None

TREE_VERSION = skilltreecatalog.TREE_VERSION
EXPECTED_CATALOG_HASH = skilltreecatalog.CATALOG_HASH
EXPECTED_NODE_IDS = skilltreecatalog.NODE_IDS
ROOT_NODE_ID = 2000
ROOT_POSITION = (0, 0)
PATH_COUNT = max(pair[0] for pair in skilltreecatalog.POSITION_BY_ID.values())
RANKS_PER_PATH = max(pair[1] for pair in skilltreecatalog.POSITION_BY_ID.values())
FAMILY_POSITIONS = frozenset(skilltreecatalog.POSITION_BY_ID.values()) - frozenset((ROOT_POSITION,))
CLIENT_SEQUENCE_FIRST = 0x8000000000000001
UINT16_MAX = 0xFFFF
UINT32_MAX = 0xFFFFFFFF
UINT64_MAX = 0xFFFFFFFFFFFFFFFF
INT32_MIN = -0x80000000
INT32_MAX = 0x7FFFFFFF
MAX_RANK = 5
MAX_REQUIRED_LEVEL = 120
MAX_COST_ITEMS = 8
MAX_RENEW_COST_ITEMS = 64
MAX_ACTIVATION_SECONDS = 86400
MAX_ABSOLUTE_RANK_VALUE = 1000000
MAX_ITEM_COUNT = 2000000000
MAX_YANG = 1999999999
ALLOWED_APPLY_TYPES = (
	skilltreeapplytypes.ALLOWED_APPLY_TYPES
	if skilltreeapplytypes is not None
	else frozenset()
)
_DEFAULT_LOCALE_MODULE = object()
_LOCALIZATION_ERROR = {
	"cz": u"Texty stromu dovedností se nepodařilo načíst. Vylepšování je dočasně vypnuté.",
	"en": u"Skill tree texts could not be loaded. Upgrades are temporarily disabled.",
}

try:
	_INTEGER_TYPES = (int, long)
except NameError:
	_INTEGER_TYPES = (int,)

try:
	_STRING_TYPES = (basestring,)
except NameError:
	_STRING_TYPES = (str,)


def _IsInteger(value, minimum, maximum):
	return (
		not isinstance(value, bool)
		and isinstance(value, _INTEGER_TYPES)
		and minimum <= value <= maximum
	)


def _IsFlag(value):
	return type(value) is bool or _IsInteger(value, 0, 1)


def _CopyItems(items):
	return [dict(item) for item in items]


def _CopyCost(cost):
	return {
		"points": cost["points"],
		"yang": cost["yang"],
		"items": _CopyItems(cost["items"]),
	}


def _CopyParents(parents):
	return [dict(parent) for parent in parents]


def _CopyNode(node):
	copy = dict(node)
	copy["parents"] = _CopyParents(node["parents"])
	copy["next_rank_cost"] = _CopyCost(node["next_rank_cost"])
	return copy


class SkillTreeModel(object):

	_NODE_FIELDS = frozenset((
		"node_id", "path_id", "path_order", "rank", "max_rank", "eligible",
		"required_level", "apply_type", "next_rank_value", "completion_present",
		"completion_apply_type", "completion_value", "parents", "next_rank_cost",
	))
	_PARENT_FIELDS = frozenset(("node_id", "required_rank"))
	_COST_FIELDS = frozenset(("points", "yang", "items"))
	_ITEM_FIELDS = frozenset(("vnum", "count"))
	_RANK_FIELDS = frozenset(("node_id", "rank"))
	_NODE_STATE_FIELDS = frozenset(("node_id", "rank", "eligible", "next_rank_value"))

	def __init__(self, expectedNodeIds, localeModule=_DEFAULT_LOCALE_MODULE,
		rankValues=None):
		try:
			expected = tuple(expectedNodeIds)
		except TypeError:
			raise TypeError("expectedNodeIds must be iterable")
		if expected != EXPECTED_NODE_IDS:
			raise ValueError("Skill Tree model requires the exact approved node IDs")
		self.expectedNodeIds = expected
		self.expectedNodeIdSet = frozenset(expected)
		self.rankValuesById = self.__ValidateRankValues(rankValues)
		if localeModule is _DEFAULT_LOCALE_MODULE:
			localeModule = skilltreelocale
		self.localeModule = localeModule
		self.localizationReady = bool(
			localeModule is not None
			and callable(getattr(localeModule, "HasCompleteLocale", None))
			and localeModule.HasCompleteLocale("cz", expected)
			and localeModule.HasCompleteLocale("en", expected)
		)
		self.__ResetState()

	def __ValidateRankValues(self, rankValues):
		if rankValues is None:
			return {}
		if not isinstance(rankValues, dict):
			raise TypeError("rankValues must be a dictionary")
		expectedVisible = self.expectedNodeIdSet - frozenset((ROOT_NODE_ID,))
		if frozenset(rankValues) != expectedVisible:
			raise ValueError("rankValues must cover every visible node exactly")
		validated = {}
		for nodeId, values in rankValues.items():
			if not isinstance(values, (list, tuple)) or len(values) != skilltreecatalog.MAX_RANK_BY_ID[nodeId]:
				raise ValueError("rankValues must match each approved node rank count")
			if any(
				not _IsInteger(value, -MAX_ABSOLUTE_RANK_VALUE,
					MAX_ABSOLUTE_RANK_VALUE)
				for value in values
			):
				raise ValueError("rankValues contains an invalid value")
			validated[nodeId] = tuple(values)
		return validated

	def __ResetState(self):
		self.catalogById = {}
		self.ranksById = {}
		self.treeVersion = 0
		self.catalogHash = ""
		self.sessionNonce = 0
		self.progressRevision = 0
		self.pointBalance = 0
		self.pointCap = 0
		self.pointSources = {}
		self.pointSourceOrder = ()
		self.pendingRequest = None
		self.pendingActivationRequest = None
		self.confirmedUpgrade = None
		self.activationState = None
		self.nextRequestSequence = CLIENT_SEQUENCE_FIRST
		self.stagedCatalog = None
		self.ready = False
		self.needsRefresh = False

	def Reset(self):
		self.__ResetState()

	def Destroy(self):
		self.__ResetState()

	def IsReady(self):
		return bool(self.ready)

	def IsLocalizationReady(self):
		return bool(self.localizationReady)

	def GetLocalizationError(self, language):
		if self.localeModule is not None:
			getter = getattr(self.localeModule, "GetErrorText", None)
			if callable(getter):
				return getter(language)
		return _LOCALIZATION_ERROR.get(language, _LOCALIZATION_ERROR["en"])

	def NeedsRefresh(self):
		return bool(self.needsRefresh)

	def GetTreeVersion(self):
		return self.treeVersion

	def GetSessionNonce(self):
		return self.sessionNonce

	def GetProgressRevision(self):
		return self.progressRevision

	def GetPointBalance(self):
		return self.pointBalance if self.IsReady() else None

	def GetPointSources(self):
		return dict(self.pointSources) if self.IsReady() else {}

	def GetPointSourceOrder(self):
		return self.pointSourceOrder if self.IsReady() else ()

	def GetPendingRequest(self):
		if self.pendingRequest is None:
			return None
		return dict(self.pendingRequest)

	def IsActivationReady(self):
		return bool(
			self.IsReady()
			and self.activationState is not None
			and self.activationState["tree_version"] == self.treeVersion
			and self.activationState["session_nonce"] == self.sessionNonce
		)

	def GetActivationState(self):
		if not self.IsActivationReady():
			return None
		state = dict(self.activationState)
		state["renew_cost"] = _CopyCost(self.activationState["renew_cost"])
		state["request_pending"] = self.pendingActivationRequest is not None
		return state

	def GetPendingActivationRequest(self):
		if self.pendingActivationRequest is None:
			return None
		return dict(self.pendingActivationRequest)

	def GetCatalogNode(self, nodeId):
		node = self.catalogById.get(nodeId)
		if node is None:
			return None
		return _CopyNode(node)

	def GetNextRankValue(self, nodeId):
		node = self.catalogById.get(nodeId)
		if node is None:
			return None
		return node["next_rank_value"]

	def GetNextCost(self, nodeId):
		node = self.catalogById.get(nodeId)
		if node is None:
			return None
		return _CopyCost(node["next_rank_cost"])

	def GetRankText(self, nodeId):
		if not self.IsReady() or nodeId not in self.ranksById:
			return u"\u2014"
		return str(self.__DisplayRank(nodeId))

	def GetNodePresenters(self):
		if not self.IsReady():
			return {}
		presenters = {}
		for nodeId in self.expectedNodeIds:
			node = self.catalogById[nodeId]
			rank = self.__DisplayRank(nodeId)
			if rank == 0:
				state = "available" if node["eligible"] else "locked"
			elif rank >= node["max_rank"]:
				state = "maxed"
			else:
				state = "learned"
			presenters[nodeId] = {
				"node_id": nodeId,
				"rank": rank,
				"max_rank": node["max_rank"],
				"state": state,
				"eligible": bool(node["eligible"]),
				"required_level": node["required_level"],
				"apply_type": node["apply_type"],
				"parents": _CopyParents(node["parents"]),
				"next_rank_value": node["next_rank_value"],
				"next_rank_cost": _CopyCost(node["next_rank_cost"]),
				"refresh_pending": bool(
					self.confirmedUpgrade is not None
					and self.confirmedUpgrade["node_id"] == nodeId
				),
				"request_pending": bool(
					self.pendingRequest is not None
					and self.pendingRequest["node_id"] == nodeId
				),
			}
			values = self.rankValuesById.get(nodeId)
			if values is None:
				presenters[nodeId].update({
					"current_total": 0,
					"next_total": None,
					"next_increment": None,
				})
			else:
				currentTotal = values[rank - 1] if rank > 0 else 0
				nextTotal = values[rank] if rank < node["max_rank"] else None
				presenters[nodeId].update({
					"current_total": currentTotal,
					"next_total": nextTotal,
					"next_increment": (
						None if nextTotal is None else nextTotal - currentTotal
					),
				})
		return presenters

	def __DisplayRank(self, nodeId):
		if (
			self.confirmedUpgrade is not None
			and self.confirmedUpgrade["node_id"] == nodeId
		):
			return self.confirmedUpgrade["rank"]
		return self.ranksById[nodeId]

	def CanUpgrade(self, nodeId):
		if (
			not self.IsReady()
			or not self.IsLocalizationReady()
			or self.stagedCatalog is not None
			or self.needsRefresh
			or self.pendingRequest is not None
			or self.pendingActivationRequest is not None
			or nodeId not in self.catalogById
			or self.sessionNonce == 0
			or self.progressRevision == 0
		):
			return False
		node = self.catalogById[nodeId]
		return bool(node["eligible"] and self.ranksById[nodeId] < node["max_rank"])

	def BeginUpgrade(self, nodeId):
		if not self.CanUpgrade(nodeId):
			return None
		sequence = self.__ReserveRequestSequence()
		if sequence is None:
			return None
		self.pendingRequest = {
			"node_id": nodeId,
			"session_nonce": self.sessionNonce,
			"request_sequence": sequence,
			"expected_revision": self.progressRevision,
			"target_rank": self.ranksById[nodeId] + 1,
			"point_cost": self.catalogById[nodeId]["next_rank_cost"]["points"],
		}
		return (nodeId, self.sessionNonce, sequence, self.progressRevision)

	def CanBeginDismantle(self):
		return bool(self.IsReady() and not self.needsRefresh
			and self.stagedCatalog is None and self.pendingRequest is None
			and self.pendingActivationRequest is None
			and self.sessionNonce != 0 and self.progressRevision != 0)

	def BeginDismantle(self, slots):
		if (not self.CanBeginDismantle()
			or not isinstance(slots, (list, tuple)) or not 1 <= len(slots) <= 9):
			return None
		seen = set()
		for slot in slots:
			if (not isinstance(slot, (list, tuple)) or len(slot) != 2
				or not _IsInteger(slot[0], 1, 1)
				or not _IsInteger(slot[1], 0, UINT16_MAX)
				or tuple(slot) in seen):
				return None
			seen.add(tuple(slot))
		sequence = self.__ReserveRequestSequence()
		if sequence is None:
			return None
		self.pendingRequest = {
			"kind": "dismantle", "node_id": None,
			"session_nonce": self.sessionNonce,
			"request_sequence": sequence,
			"expected_revision": self.progressRevision,
			"slots": tuple(tuple(slot) for slot in slots),
		}
		return (self.pendingRequest["slots"], self.sessionNonce,
			sequence, self.progressRevision)

	def CancelPending(self, sessionNonce, requestSequence):
		if not self.__MatchesPending(sessionNonce, requestSequence):
			return False
		self.pendingRequest = None
		return True

	def BeginSetActivation(self, desiredEnabled):
		if type(desiredEnabled) is not bool or not self.__CanMutateActivation():
			return None
		if desiredEnabled == self.activationState["enabled"]:
			return None
		sequence = self.__ReserveRequestSequence()
		if sequence is None:
			return None
		self.pendingActivationRequest = {
			"kind": "set",
			"desired_enabled": desiredEnabled,
			"session_nonce": self.sessionNonce,
			"request_sequence": sequence,
			"expected_revision": self.activationState["activation_revision"],
		}
		return (
			desiredEnabled, self.sessionNonce, sequence,
			self.activationState["activation_revision"],
		)

	def BeginRenewActivation(self):
		if not self.__CanMutateActivation():
			return None
		sequence = self.__ReserveRequestSequence()
		if sequence is None:
			return None
		self.pendingActivationRequest = {
			"kind": "renew",
			"desired_enabled": None,
			"session_nonce": self.sessionNonce,
			"request_sequence": sequence,
			"expected_revision": self.activationState["activation_revision"],
		}
		return (
			self.sessionNonce, sequence,
			self.activationState["activation_revision"],
		)

	def CancelActivationPending(self, sessionNonce, requestSequence):
		if not self.__MatchesActivationPending(sessionNonce, requestSequence):
			return False
		self.pendingActivationRequest = None
		return True

	def __CanMutateActivation(self):
		return bool(
			self.IsActivationReady()
			and self.pendingRequest is None
			and self.pendingActivationRequest is None
			and self.nextRequestSequence <= UINT64_MAX
		)

	def __ReserveRequestSequence(self):
		sequence = self.nextRequestSequence
		if sequence > UINT64_MAX:
			return None
		self.nextRequestSequence = sequence + 1
		return sequence

	def ApplyCatalog(self, treeVersion, catalogHash, pointCap, pointSources, nodes):
		if pointCap != skilltreecatalog.POINT_CAP or not isinstance(pointSources, (list, tuple)):
			return self.__RejectPair()
		validatedSources = {}
		for source in pointSources:
			if (not isinstance(source, dict) or
				frozenset(source) != frozenset(("vnum", "points_per_item")) or
				not _IsInteger(source["vnum"], 1, UINT32_MAX) or
				not _IsInteger(source["points_per_item"], 1, pointCap) or
				source["vnum"] in validatedSources):
				return self.__RejectPair()
			validatedSources[source["vnum"]] = source["points_per_item"]
		if validatedSources != skilltreecatalog.POINT_SOURCE_BY_VNUM:
			return self.__RejectPair()
		validated = self.__ValidateCatalog(treeVersion, catalogHash, nodes)
		if validated is None:
			return self.__RejectPair()
		validated["point_cap"] = pointCap
		validated["point_sources"] = validatedSources
		validated["point_source_order"] = tuple(source["vnum"] for source in pointSources)
		preservePresentation = bool(
			self.ready
			and treeVersion == self.treeVersion
			and catalogHash == self.catalogHash
		)
		self.stagedCatalog = validated
		if not preservePresentation:
			self.ready = False
		return True

	def ApplySnapshot(self, treeVersion, sessionNonce, progressRevision, pointBalance, ranks):
		if self.stagedCatalog is None:
			return False
		if (
			not _IsInteger(treeVersion, 1, UINT32_MAX)
			or treeVersion != self.stagedCatalog["tree_version"]
			or not _IsInteger(sessionNonce, 1, UINT64_MAX)
			or not _IsInteger(progressRevision, 1, UINT64_MAX)
			or not _IsInteger(pointBalance, 0, self.stagedCatalog["point_cap"])
		):
			return self.__RejectPair()
		validatedRanks = self.__ValidateRanks(ranks, self.stagedCatalog["catalog"])
		if validatedRanks is None:
			return self.__RejectPair()
		if self.sessionNonce == sessionNonce:
			if self.confirmedUpgrade is not None:
				confirmed = self.confirmedUpgrade
				targetNode = self.stagedCatalog["catalog"][confirmed["node_id"]]
				expectedRanks = dict(self.ranksById)
				expectedRanks[confirmed["node_id"]] = confirmed["rank"]
				if (
					progressRevision != confirmed["progress_revision"]
					or pointBalance != confirmed["point_balance"]
					or treeVersion != self.treeVersion
					or self.stagedCatalog["catalog_hash"] != self.catalogHash
					or not self.__CatalogMatchesConfirmedUpgrade(
						self.stagedCatalog["catalog"], self.catalogById, confirmed,
					)
					or validatedRanks != expectedRanks
					or targetNode["rank"] != confirmed["rank"]
					or bool(targetNode["eligible"]) != confirmed["eligible"]
					or targetNode["next_rank_value"] != confirmed["next_rank_value"]
					or targetNode["next_rank_cost"] != confirmed["next_rank_cost"]
				):
					return self.__RejectPair()
				self.catalogById = self.stagedCatalog["catalog"]
				self.ranksById = validatedRanks
				self.pointBalance = pointBalance
				self.stagedCatalog = None
				self.confirmedUpgrade = None
				self.needsRefresh = False
				self.ready = True
				return True
			if progressRevision < self.progressRevision:
				return self.__RejectPair()
			if progressRevision == self.progressRevision:
				if (
					treeVersion != self.treeVersion
					or self.stagedCatalog["catalog_hash"] != self.catalogHash
					or not self.__CatalogMatchesExceptEligibility(
						self.stagedCatalog["catalog"], self.catalogById,
					)
					or validatedRanks != self.ranksById
					or pointBalance != self.pointBalance
				):
					return self.__RejectPair()
				self.catalogById = self.stagedCatalog["catalog"]
				self.stagedCatalog = None
				self.needsRefresh = False
				self.ready = True
				return True

		newSession = self.sessionNonce != sessionNonce
		self.catalogById = self.stagedCatalog["catalog"]
		self.ranksById = validatedRanks
		self.treeVersion = treeVersion
		self.catalogHash = self.stagedCatalog["catalog_hash"]
		self.sessionNonce = sessionNonce
		self.progressRevision = progressRevision
		self.pointBalance = pointBalance
		self.pointCap = self.stagedCatalog["point_cap"]
		self.pointSources = self.stagedCatalog["point_sources"]
		self.pointSourceOrder = self.stagedCatalog["point_source_order"]
		self.stagedCatalog = None
		self.pendingRequest = None
		self.confirmedUpgrade = None
		if newSession:
			self.pendingActivationRequest = None
			if (
				self.activationState is not None
				and self.activationState["session_nonce"] != sessionNonce
			):
				self.activationState = None
			self.nextRequestSequence = CLIENT_SEQUENCE_FIRST
		self.needsRefresh = False
		self.ready = True
		return True

	def __RejectPair(self):
		self.stagedCatalog = None
		self.needsRefresh = True
		return False

	def ApplyUpgradeResult(self, resultCode, treeVersion, sessionNonce, progressRevision,
		pointBalance, requestSessionNonce, requestSequence, nodeState, nextCost):
		if (
			not _IsInteger(resultCode, 0, 7)
			or not _IsInteger(treeVersion, 1, UINT32_MAX)
			or not _IsInteger(sessionNonce, 1, UINT64_MAX)
			or not _IsInteger(progressRevision, 1, UINT64_MAX)
			or not _IsInteger(pointBalance, 0, skilltreecatalog.POINT_CAP)
			or not self.IsReady()
			or self.needsRefresh
			or self.pendingRequest is None
			or treeVersion != self.treeVersion
			or sessionNonce != self.sessionNonce
			or not self.__MatchesPending(requestSessionNonce, requestSequence)
		):
			return False
		pending = self.pendingRequest
		if resultCode != 0:
			if progressRevision != self.progressRevision or pointBalance != self.pointBalance:
				return False
			self.pendingRequest = None
			return True
		if progressRevision != pending["expected_revision"] + 1:
			return False
		validatedState = self.__ValidateNodeState(nodeState)
		validatedCost = self.__ValidateCost(nextCost)
		if validatedState is None or validatedCost is None:
			return False
		if (
			validatedState["node_id"] != pending["node_id"]
			or pointBalance != self.pointBalance - pending["point_cost"]
			or validatedState["rank"] != pending["target_rank"]
			or validatedState["rank"] > self.catalogById[pending["node_id"]]["max_rank"]
		):
			return False

		self.confirmedUpgrade = {
			"node_id": pending["node_id"],
			"rank": validatedState["rank"],
			"eligible": validatedState["eligible"],
			"next_rank_value": validatedState["next_rank_value"],
			"next_rank_cost": validatedCost,
			"progress_revision": progressRevision,
			"point_balance": pointBalance,
		}
		self.progressRevision = progressRevision
		self.pointBalance = pointBalance
		self.pendingRequest = None
		self.needsRefresh = True
		return True

	def ApplyDismantleResult(self, resultCode, treeVersion, sessionNonce,
		progressRevision, pointBalance, earnedPoints, requestSessionNonce,
		requestSequence):
		if (not _IsInteger(resultCode, 0, 7)
			or not self.IsReady() or self.needsRefresh
			or self.pendingRequest is None
			or self.pendingRequest.get("kind") != "dismantle"
			or treeVersion != self.treeVersion or sessionNonce != self.sessionNonce
			or not self.__MatchesPending(requestSessionNonce, requestSequence)
			or not _IsInteger(pointBalance, 0, self.pointCap)
			or not _IsInteger(earnedPoints, 0, self.pointCap)):
			return False
		pending = self.pendingRequest
		if resultCode:
			if (progressRevision != self.progressRevision
				or pointBalance != self.pointBalance or earnedPoints != 0):
				return False
			self.pendingRequest = None
			return True
		if (progressRevision != pending["expected_revision"] + 1
			or earnedPoints == 0
			or pointBalance != self.pointBalance + earnedPoints):
			return False
		self.progressRevision = progressRevision
		self.pointBalance = pointBalance
		self.pendingRequest = None
		self.needsRefresh = True
		return True

	def ApplyActivationState(self, treeVersion, activationRevision, sessionNonce,
		remainingSeconds, maxSeconds, enabled, renewCost):
		validated = self.__ValidateActivationState(
			treeVersion, activationRevision, sessionNonce,
			remainingSeconds, maxSeconds, enabled, renewCost,
		)
		if validated is None:
			return False
		if self.activationState is not None:
			current = self.activationState
			if current["session_nonce"] == sessionNonce:
				if activationRevision < current["activation_revision"]:
					return False
				if activationRevision == current["activation_revision"]:
					currentWithoutTime = dict(current)
					validatedWithoutTime = dict(validated)
					del currentWithoutTime["remaining_seconds"]
					del validatedWithoutTime["remaining_seconds"]
					if (
						validatedWithoutTime != currentWithoutTime
						or validated["remaining_seconds"] > current["remaining_seconds"]
					):
						return False
		self.activationState = validated
		if (
			self.pendingActivationRequest is not None
			and self.pendingActivationRequest["session_nonce"] == sessionNonce
			and activationRevision > self.pendingActivationRequest["expected_revision"]
		):
			self.pendingActivationRequest = None
		elif (
			self.pendingActivationRequest is not None
			and self.pendingActivationRequest["session_nonce"] != sessionNonce
		):
			self.pendingActivationRequest = None
		return True

	def ApplyActivationResult(self, resultCode, treeVersion, activationRevision,
		sessionNonce, remainingSeconds, maxSeconds, enabled,
		requestSessionNonce, requestSequence, renewCost):
		if (
			not _IsInteger(resultCode, 0, 7)
			or not self.__MatchesActivationPending(requestSessionNonce, requestSequence)
		):
			return False
		pending = self.pendingActivationRequest
		validated = self.__ValidateActivationState(
			treeVersion, activationRevision, sessionNonce,
			remainingSeconds, maxSeconds, enabled, renewCost,
		)
		if (
			validated is None
			or not self.IsActivationReady()
			or treeVersion != self.treeVersion
			or sessionNonce != self.sessionNonce
			or requestSessionNonce != sessionNonce
		):
			return False
		expectedRevision = pending["expected_revision"] + (1 if resultCode == 0 else 0)
		if activationRevision != expectedRevision:
			return False
		self.activationState = validated
		self.pendingActivationRequest = None
		return True

	def ApplyError(self, resultCode, treeVersion, progressRevision, activationRevision,
		requestSessionNonce, requestSequence):
		if (
			not _IsInteger(resultCode, 1, 7)
			or not _IsInteger(treeVersion, 1, UINT32_MAX)
			or not _IsInteger(progressRevision, 0, UINT64_MAX)
			or not _IsInteger(activationRevision, 0, UINT64_MAX)
			or treeVersion != self.treeVersion
		):
			return False
		if self.__MatchesPending(requestSessionNonce, requestSequence):
			if progressRevision != self.pendingRequest["expected_revision"]:
				return False
			self.pendingRequest = None
			return True
		if self.__MatchesActivationPending(requestSessionNonce, requestSequence):
			if activationRevision != self.pendingActivationRequest["expected_revision"]:
				return False
			self.pendingActivationRequest = None
			return True
		return False

	def __MatchesPending(self, sessionNonce, requestSequence):
		return bool(
			self.pendingRequest is not None
			and _IsInteger(sessionNonce, 1, UINT64_MAX)
			and _IsInteger(requestSequence, CLIENT_SEQUENCE_FIRST, UINT64_MAX)
			and sessionNonce == self.pendingRequest["session_nonce"]
			and requestSequence == self.pendingRequest["request_sequence"]
		)

	def __MatchesActivationPending(self, sessionNonce, requestSequence):
		return bool(
			self.pendingActivationRequest is not None
			and _IsInteger(sessionNonce, 1, UINT64_MAX)
			and _IsInteger(requestSequence, CLIENT_SEQUENCE_FIRST, UINT64_MAX)
			and sessionNonce == self.pendingActivationRequest["session_nonce"]
			and requestSequence == self.pendingActivationRequest["request_sequence"]
		)

	def __ValidateCatalog(self, treeVersion, catalogHash, nodes):
		if treeVersion != TREE_VERSION:
			return None
		if (
			not isinstance(catalogHash, _STRING_TYPES)
			or catalogHash != EXPECTED_CATALOG_HASH
		):
			return None
		if not isinstance(nodes, (list, tuple)) or len(nodes) != len(self.expectedNodeIds):
			return None

		catalog = {}
		pathPairs = set()
		applyCounts = {}
		for record in nodes:
			if not isinstance(record, dict) or frozenset(record) != self._NODE_FIELDS:
				return None
			nodeId = record["node_id"]
			if (
				not _IsInteger(nodeId, 1, UINT16_MAX)
				or nodeId not in self.expectedNodeIdSet
				or nodeId in catalog
				or not _IsInteger(record["path_id"], 0, PATH_COUNT)
				or not _IsInteger(record["path_order"], 0, RANKS_PER_PATH)
				or not _IsInteger(record["max_rank"], 1, MAX_RANK)
				or not _IsInteger(record["rank"], 0, record["max_rank"])
				or not _IsFlag(record["eligible"])
				or record["required_level"] != skilltreecatalog.REQUIRED_LEVEL_BY_ID[nodeId]
				or not _IsInteger(record["apply_type"], 1, UINT16_MAX)
				or record["apply_type"] not in ALLOWED_APPLY_TYPES
				or record["apply_type"] != skilltreecatalog.APPLY_BY_ID[nodeId]
				or not _IsInteger(
					record["next_rank_value"],
					-MAX_ABSOLUTE_RANK_VALUE,
					MAX_ABSOLUTE_RANK_VALUE,
				)
				or not _IsFlag(record["completion_present"])
				or not _IsInteger(record["completion_apply_type"], 0, UINT16_MAX)
				or not _IsInteger(
					record["completion_value"],
					-MAX_ABSOLUTE_RANK_VALUE,
					MAX_ABSOLUTE_RANK_VALUE,
				)
			):
				return None
			if nodeId == ROOT_NODE_ID:
				if (
					(record["path_id"], record["path_order"]) != ROOT_POSITION
					or record["max_rank"] != 1
					or record["rank"] != 1
					or record["next_rank_value"] != 0
				):
					return None
			else:
				if (
					(record["path_id"], record["path_order"]) != skilltreecatalog.POSITION_BY_ID[nodeId]
					or record["max_rank"] != skilltreecatalog.MAX_RANK_BY_ID[nodeId]
				):
					return None
			pair = (record["path_id"], record["path_order"])
			if pair in pathPairs:
				return None
			pathPairs.add(pair)
			applyCounts[record["apply_type"]] = applyCounts.get(record["apply_type"], 0) + 1
			parents = self.__ValidateParents(record["parents"], nodeId)
			cost = self.__ValidateCost(record["next_rank_cost"])
			if parents is None or cost is None:
				return None
			if tuple((p["node_id"], p["required_rank"]) for p in parents) != skilltreecatalog.PARENTS_BY_ID[nodeId]:
				return None
			completionPresent = bool(record["completion_present"])
			if (
				completionPresent
				or record["completion_apply_type"] != 0
				or record["completion_value"] != 0
			):
				return None
			node = dict(record)
			node["eligible"] = bool(record["eligible"])
			node["completion_present"] = completionPresent
			node["parents"] = parents
			node["next_rank_cost"] = cost
			catalog[nodeId] = node

		expectedApplyCounts = {}
		for applyType in skilltreecatalog.APPLY_BY_ID.values():
			expectedApplyCounts[applyType] = expectedApplyCounts.get(applyType, 0) + 1
		if (
			frozenset(catalog) != self.expectedNodeIdSet
			or pathPairs != set(FAMILY_POSITIONS) | set((ROOT_POSITION,))
			or applyCounts != expectedApplyCounts
		):
			return None
		if (
			catalog[ROOT_NODE_ID]["parents"]
			or catalog[ROOT_NODE_ID]["next_rank_cost"] != {"points": 0, "yang": 0, "items": []}
		):
			return None
		if catalog[skilltreecatalog.FIRST_NODE_ID]["parents"] != [{"node_id": ROOT_NODE_ID, "required_rank": 1}]:
			return None
		for nodeId in skilltreecatalog.VISIBLE_NODE_IDS:
			if nodeId == skilltreecatalog.FIRST_NODE_ID:
				continue
			if any(parent["node_id"] == ROOT_NODE_ID for parent in catalog[nodeId]["parents"]):
				return None
		for node in catalog.values():
			for parent in node["parents"]:
				parentNode = catalog.get(parent["node_id"])
				if parentNode is None or parent["required_rank"] != parentNode["max_rank"]:
					return None
		if self.__HasCycle(catalog):
			return None
		return {
			"tree_version": treeVersion,
			"catalog_hash": str(catalogHash),
			"catalog": catalog,
		}

	def __ValidateParents(self, parents, nodeId):
		if not isinstance(parents, (list, tuple)) or len(parents) > MAX_COST_ITEMS:
			return None
		validated = []
		seen = set()
		for parent in parents:
			if not isinstance(parent, dict) or frozenset(parent) != self._PARENT_FIELDS:
				return None
			parentId = parent["node_id"]
			if (
				not _IsInteger(parentId, 1, UINT16_MAX)
				or parentId not in self.expectedNodeIdSet
				or parentId == nodeId
				or parentId in seen
				or not _IsInteger(parent["required_rank"], 1, MAX_RANK)
			):
				return None
			seen.add(parentId)
			validated.append({
				"node_id": parentId,
				"required_rank": parent["required_rank"],
			})
		return validated

	def __ValidateCost(self, cost, maximumItems=MAX_COST_ITEMS):
		if not isinstance(cost, dict) or frozenset(cost) != self._COST_FIELDS:
			return None
		if not _IsInteger(cost["yang"], 0, MAX_YANG):
			return None
		if not _IsInteger(cost["points"], 0, skilltreecatalog.POINT_CAP):
			return None
		items = cost["items"]
		if not isinstance(items, (list, tuple)) or len(items) > maximumItems:
			return None
		validatedItems = []
		seen = set()
		for item in items:
			if not isinstance(item, dict) or frozenset(item) != self._ITEM_FIELDS:
				return None
			if (
				not _IsInteger(item["vnum"], 1, UINT32_MAX)
				or not _IsInteger(item["count"], 1, MAX_ITEM_COUNT)
				or item["vnum"] in seen
			):
				return None
			seen.add(item["vnum"])
			validatedItems.append({"vnum": item["vnum"], "count": item["count"]})
		return {"points": cost["points"], "yang": cost["yang"], "items": validatedItems}

	def __ValidateActivationState(self, treeVersion, activationRevision, sessionNonce,
		remainingSeconds, maxSeconds, enabled, renewCost):
		if (
			treeVersion != TREE_VERSION
			or not _IsInteger(activationRevision, 0, UINT64_MAX)
			or not _IsInteger(sessionNonce, 1, UINT64_MAX)
			or not _IsInteger(maxSeconds, 1, MAX_ACTIVATION_SECONDS)
			or not _IsInteger(remainingSeconds, 0, maxSeconds)
			or not _IsFlag(enabled)
			or (bool(enabled) and remainingSeconds == 0)
		):
			return None
		validatedCost = self.__ValidateCost(renewCost, MAX_RENEW_COST_ITEMS)
		if validatedCost is None:
			return None
		return {
			"tree_version": treeVersion,
			"activation_revision": activationRevision,
			"session_nonce": sessionNonce,
			"remaining_seconds": remainingSeconds,
			"max_seconds": maxSeconds,
			"enabled": bool(enabled),
			"renew_cost": validatedCost,
		}

	def __ValidateRanks(self, ranks, catalog):
		if not isinstance(ranks, (list, tuple)) or len(ranks) != len(self.expectedNodeIds):
			return None
		validated = {}
		for record in ranks:
			if not isinstance(record, dict) or frozenset(record) != self._RANK_FIELDS:
				return None
			nodeId = record["node_id"]
			if (
				not _IsInteger(nodeId, 1, UINT16_MAX)
				or nodeId not in catalog
				or nodeId in validated
				or not _IsInteger(record["rank"], 0, catalog[nodeId]["max_rank"])
				or record["rank"] != catalog[nodeId]["rank"]
			):
				return None
			validated[nodeId] = record["rank"]
		if frozenset(validated) != self.expectedNodeIdSet:
			return None
		return validated

	def __ValidateNodeState(self, nodeState):
		if not isinstance(nodeState, dict) or frozenset(nodeState) != self._NODE_STATE_FIELDS:
			return None
		if (
			not _IsInteger(nodeState["node_id"], 1, UINT16_MAX)
			or nodeState["node_id"] not in self.expectedNodeIdSet
			or not _IsInteger(nodeState["rank"], 0, MAX_RANK)
			or not _IsFlag(nodeState["eligible"])
			or not _IsInteger(
				nodeState["next_rank_value"],
				-MAX_ABSOLUTE_RANK_VALUE,
				MAX_ABSOLUTE_RANK_VALUE,
			)
		):
			return None
		return {
			"node_id": nodeState["node_id"],
			"rank": nodeState["rank"],
			"eligible": bool(nodeState["eligible"]),
			"next_rank_value": nodeState["next_rank_value"],
		}

	def __CatalogMatchesExceptEligibility(self, candidate, active):
		if frozenset(candidate) != frozenset(active):
			return False
		for nodeId in self.expectedNodeIds:
			candidateNode = candidate[nodeId]
			activeNode = active[nodeId]
			for field in self._NODE_FIELDS:
				if field == "eligible":
					continue
				if candidateNode[field] != activeNode[field]:
					return False
		return True

	def __CatalogMatchesConfirmedUpgrade(self, candidate, active, confirmed):
		if frozenset(candidate) != frozenset(active):
			return False
		targetId = confirmed["node_id"]
		for nodeId in self.expectedNodeIds:
			candidateNode = candidate[nodeId]
			activeNode = active[nodeId]
			for field in self._NODE_FIELDS:
				if field == "eligible":
					continue
				if nodeId == targetId and field in (
					"rank", "next_rank_value", "next_rank_cost",
				):
					continue
				if candidateNode[field] != activeNode[field]:
					return False
		return True

	def __HasCycle(self, catalog):
		visiting = set()
		visited = set()

		def Visit(nodeId):
			if nodeId in visited:
				return False
			if nodeId in visiting:
				return True
			visiting.add(nodeId)
			for parent in catalog[nodeId]["parents"]:
				if Visit(parent["node_id"]):
					return True
			visiting.remove(nodeId)
			visited.add(nodeId)
			return False

		for nodeId in self.expectedNodeIds:
			if Visit(nodeId):
				return True
		return False
