"""State for refining one player-selected Dragon Soul stone."""


class StrengthAutoRefineSession(object):
	TARGET_STRENGTH = 6
	INVALID_POSITION = (-1, -1)

	def __init__(self):
		self.pending = False
		self.Stop()

	def Stop(self):
		self.active = False
		self.materialPosition = self.INVALID_POSITION
		self.materialVnum = 0
		self.stonePosition = self.INVALID_POSITION
		self.stoneFamily = None

	def Start(self, materialPosition, materialVnum, stonePosition, stoneInfo):
		if self.pending:
			return False
		self.Stop()
		if materialPosition == self.INVALID_POSITION:
			return False
		if stonePosition == self.INVALID_POSITION or materialVnum <= 0:
			return False
		if not isinstance(stoneInfo, (tuple, list)) or len(stoneInfo) != 4:
			return False
		if stoneInfo[3] >= self.TARGET_STRENGTH:
			return False

		self.active = True
		self.materialPosition = tuple(materialPosition)
		self.materialVnum = materialVnum
		self.stonePosition = tuple(stonePosition)
		self.stoneFamily = tuple(stoneInfo[:3])
		return True

	def CanSend(self, materialPosition, materialVnum, stonePosition, stoneInfo):
		if not self.active or self.pending:
			return False
		if tuple(materialPosition) != self.materialPosition:
			return False
		if materialVnum != self.materialVnum:
			return False
		if tuple(stonePosition) != self.stonePosition:
			return False
		if not isinstance(stoneInfo, (tuple, list)) or len(stoneInfo) != 4:
			return False
		if tuple(stoneInfo[:3]) != self.stoneFamily:
			return False
		return stoneInfo[3] < self.TARGET_STRENGTH

	def MarkRequestSent(self):
		if not self.active or self.pending:
			return False
		self.pending = True
		return True

	def AcceptResult(self, stonePosition, stoneInfo):
		if not self.pending:
			self.Stop()
			return False
		self.pending = False
		if not self.active:
			self.Stop()
			return False
		if stonePosition == self.INVALID_POSITION:
			self.Stop()
			return False
		if not isinstance(stoneInfo, (tuple, list)) or len(stoneInfo) != 4:
			self.Stop()
			return False
		if tuple(stoneInfo[:3]) != self.stoneFamily:
			self.Stop()
			return False
		if stoneInfo[3] >= self.TARGET_STRENGTH:
			self.Stop()
			return False

		self.stonePosition = tuple(stonePosition)
		return True
