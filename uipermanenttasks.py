import fontconfig
import localeInfo
import nonplayer
import ui
import WikiRenderTarget


WINDOW_SIZE = (410, 264)
TAB_POSITIONS = (12, 208)
TAB_ICON_X = 14
TAB_ICON_Y = 9
TAB_TEXT_CENTER_X = 95
TAB_TEXT_CENTER_Y = 17
CATEGORY_HEADING_COLOR = 0xffffd36b
HUNT_TARGET_LIMIT = 4
HUNT_PROGRESS_TOP = 28
HUNT_PROGRESS_PITCH = 28
COLLECTOR_STATE_ACTIVE = 0
COLLECTOR_STATE_UNCONFIGURED = 1
COLLECTOR_STATUS_UNAVAILABLE = 1
COLLECTOR_STATUS_LOADING = 2
COLLECTOR_STATUS_RESYNC_REQUIRED = 3
ASSET_ROOT = "d:/ymir work/ui/game/crimson_ember/permanent_tasks/"
MARKET_ROOT = "d:/ymir work/ui/game/crimson_ember/virtual_market/"
CATEGORY_LABELS = {
    "bossologie": localeInfo.PERMANENT_TASKS_BOSS_LABEL,
    "kamenologie": localeInfo.PERMANENT_TASKS_STONE_LABEL,
}
HUNT_CATEGORY_KEYS = {2: "kamenologie", 3: "bossologie"}


def _SafeInt(value, default=-1):
	try:
		return int(value)
	except (TypeError, ValueError, OverflowError):
		return default


def _NormalizeCollectorReward(reward):
	if isinstance(reward, dict):
		vnum = _SafeInt(reward.get("vnum"))
		amount = _SafeInt(reward.get("amount"))
	elif isinstance(reward, (tuple, list)) and len(reward) == 2:
		vnum = _SafeInt(reward[0])
		amount = _SafeInt(reward[1])
	else:
		return None
	if vnum <= 0 or amount <= 0 or amount > 9999:
		return None
	return {"vnum": vnum, "amount": amount}


def _NormalizeCollectorRow(row):
	if not isinstance(row, dict):
		return None
	normalized = {
		"generation": _SafeInt(row.get("generation")),
		"state": _SafeInt(row.get("state")),
		"stage": _SafeInt(row.get("stage")),
		"target_vnum": _SafeInt(row.get("target_vnum")),
		"current": _SafeInt(row.get("current")),
		"required": _SafeInt(row.get("required")),
		"revision": _SafeInt(row.get("revision")),
	}
	if normalized["generation"] <= 0 or normalized["stage"] <= 0 or \
			normalized["revision"] <= 0:
		return None
	rewards = row.get("rewards", ())
	if not isinstance(rewards, (tuple, list)) or len(rewards) > 5:
		return None
	normalizedRewards = []
	for reward in rewards:
		reward = _NormalizeCollectorReward(reward)
		if reward is None:
			return None
		normalizedRewards.append(reward)
	normalized["rewards"] = tuple(normalizedRewards)
	if normalized["state"] == COLLECTOR_STATE_UNCONFIGURED:
		if normalized["target_vnum"] != 0 or normalized["current"] != 0 or \
				normalized["required"] != 0 or normalizedRewards:
			return None
		return normalized
	if normalized["state"] != COLLECTOR_STATE_ACTIVE or \
			normalized["target_vnum"] <= 0 or normalized["required"] <= 0 or \
			normalized["current"] < 0 or \
			normalized["current"] > normalized["required"] or \
			not normalizedRewards:
		return None
	return normalized


def _NormalizeHuntTarget(target):
    if not isinstance(target, dict):
        return None
    accepted = target.get("accepted_vnums", ())
    if not isinstance(accepted, (tuple, list)) or not 1 <= len(accepted) <= 4:
        return None
    accepted = tuple(_SafeInt(vnum) for vnum in accepted)
    current = _SafeInt(target.get("current"))
    required = _SafeInt(target.get("required"))
    if any(vnum <= 0 for vnum in accepted) or len(set(accepted)) != len(accepted) or \
            required <= 0 or current < 0 or current > required:
        return None
    return {"accepted_vnums": accepted, "current": current,
        "required": required}


def _NormalizeHuntRows(rows):
    if not isinstance(rows, (tuple, list)) or len(rows) != 2:
        return None
    normalized = {}
    for row in rows:
        if not isinstance(row, dict):
            return None
        category = _SafeInt(row.get("category"))
        key = HUNT_CATEGORY_KEYS.get(category)
        state = _SafeInt(row.get("state"))
        stage = _SafeInt(row.get("stage"))
        stageBonus = _SafeInt(row.get("stage_bonus_percent"))
        completedBonus = _SafeInt(row.get("completed_bonus_percent"))
        revision = _SafeInt(row.get("revision"))
        if not key or key in normalized or stage <= 0 or revision <= 0 or \
                state not in (COLLECTOR_STATE_ACTIVE,
                    COLLECTOR_STATE_UNCONFIGURED) or \
                not 0 <= stageBonus <= 100 or not 0 <= completedBonus <= 100:
            return None
        targets = row.get("targets", ())
        if not isinstance(targets, (tuple, list)) or len(targets) > 4:
            return None
        normalizedTargets = []
        for target in targets:
            target = _NormalizeHuntTarget(target)
            if target is None:
                return None
            normalizedTargets.append(target)
        if state == COLLECTOR_STATE_ACTIVE:
            if not normalizedTargets:
                return None
        elif normalizedTargets or stageBonus != 0:
            return None
        normalized[key] = {
            "category": category, "state": state, "stage": stage,
            "stage_bonus_percent": stageBonus,
            "completed_bonus_percent": completedBonus,
            "revision": revision, "targets": tuple(normalizedTargets),
        }
    return normalized if len(normalized) == 2 else None


def _CreateText(parent, x, y, text=u"", color=0xffeadfc8, align="left",
				fontRole=fontconfig.ROLE_BODY, outline=False,
				verticalAlign=None):
	line = ui.TextLine()
	line.SetParent(parent)
	line.SetPosition(x, y)
	line.SetFontName(fontconfig.FontForRole(fontRole))
	if outline:
		line.SetOutline()
	line.AddFlag("not_pick")
	line.SetPackedFontColor(color)
	if align == "center":
		line.SetHorizontalAlignCenter()
	elif align == "right":
		line.SetHorizontalAlignRight()
	if verticalAlign == "center":
		line.SetVerticalAlignCenter()
	line.SetText(text)
	line.Show()
	return line


def _CreateImage(parent, x, y, filename):
	image = ui.ImageBox()
	image.SetParent(parent)
	image.SetPosition(x, y)
	image.AddFlag("not_pick")
	image.LoadImage(filename)
	image.Show()
	return image


def _BuildR1(window):
	"""The R1 look of the window (uipermanenttasksr1) or None for the original look ("Starý vzhled")."""
	try:
		import uipermanenttasksr1
	except Exception:
		return None
	return uipermanenttasksr1.Build(window)


def _CreateSlot(parent, x, y, slotIndex=0):
	slot = ui.SlotWindow()
	slot.SetParent(parent)
	slot.SetPosition(x, y)
	slot.SetSize(32, 32)
	slot.AppendSlot(slotIndex, 0, 0, 32, 32)
	slot.SetSlotBaseImage("d:/ymir work/ui/public/Slot_Base.sub", 1.0, 1.0, 1.0, 1.0)
	slot.Show()
	return slot


class PermanentTasksWindow(ui.BoardWithTitleBar):
	CATEGORY_ORDER = ("bossologie", "kamenologie")

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.children = []
		self.tabs = {}
		self.rewardSlots = []
		self.category = "bossologie"
		self.tooltipItem = None
		self.renderIndex = None
		self.collectorAvailable = False
		self.collectorLoading = False
		self.collectorRow = None
		self.huntRows = {}
		self.huntRewards = {}
		self.snapshotEvent = None
		self.r1 = None
		self.__BuildWindow()

	def __del__(self):
		ui.BoardWithTitleBar.__del__(self)

	def __Keep(self, child):
		self.children.append(child)
		return child

	def __BuildWindow(self):
		self.SetSize(*WINDOW_SIZE)
		self.SetTitleName(u"Trvalé úkoly")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.AddFlag("movable")
		self.AddFlag("float")

		for index, category in enumerate(self.CATEGORY_ORDER):
			self.tabs[category] = self.__CreateCategoryTab(
				category, TAB_POSITIONS[index], 34
			)

		self.previewPanel = ui.Window()
		self.previewPanel.SetParent(self)
		self.previewPanel.SetPosition(12, 78)
		self.previewPanel.SetSize(150, 170)
		self.previewPanel.Show()
		self.__Keep(self.previewPanel)

		self.detailsPanel = ui.Window()
		self.detailsPanel.SetParent(self)
		self.detailsPanel.SetPosition(174, 78)
		self.detailsPanel.SetSize(224, 174)
		self.detailsPanel.Show()
		self.__Keep(self.detailsPanel)

		self.renderView = ui.WikiRenderTargetUi()
		self.renderView.SetParent(self.previewPanel)
		self.renderView.SetPosition(0, 0)
		self.renderView.SetSize(150, 170)
		self.renderView.Hide()
		self.__Keep(self.renderView)

		self.previewFallback = _CreateImage(
			self.previewPanel, 64, 74,
			ASSET_ROOT + "icon_bossologie_22.png",
		)
		self.__Keep(self.previewFallback)

		self.categoryText = _CreateText(
			self.detailsPanel, 0, 1, u"", CATEGORY_HEADING_COLOR, "left",
			fontconfig.ROLE_LARGE_BOLD, True,
		)
		self.__Keep(self.categoryText)
		self.stageText = _CreateText(
			self.detailsPanel, 0, 67, u"", 0xffa89f92, "left",
			fontconfig.ROLE_BODY,
		)
		self.__Keep(self.stageText)
		self.targetIcon = _CreateImage(
			self.detailsPanel, 101, 28,
			ASSET_ROOT + "icon_bossologie_22.png",
		)
		self.__Keep(self.targetIcon)
		self.targetText = _CreateText(
			self.detailsPanel, 112, 34, u"", 0xfff1eee8, "center",
			fontconfig.ROLE_LARGE_BOLD, True,
		)
		self.__Keep(self.targetText)
		self.progressText = _CreateText(
			self.detailsPanel, 112, 58, u"", 0xfff1eee8, "center"
		)
		self.__Keep(self.progressText)
		self.progressGauge = ui.Gauge()
		self.progressGauge.SetParent(self.detailsPanel)
		self.progressGauge.SetPosition(0, 68)
		self.progressGauge.MakeGauge(224, "green")
		self.progressGauge.Show()
		self.__Keep(self.progressGauge)
		self.huntProgressTexts = []
		self.huntCountTexts = []
		self.huntProgressGauges = []
		for index in range(HUNT_TARGET_LIMIT):
			line = _CreateText(
				self.detailsPanel, 0, HUNT_PROGRESS_TOP, u"",
				0xfff1eee8, "left", fontconfig.ROLE_BODY,
			)
			line.Hide()
			self.huntProgressTexts.append(line)
			self.__Keep(line)
			count = _CreateText(
				self.detailsPanel, 224, HUNT_PROGRESS_TOP, u"",
				0xfff1eee8, "right", fontconfig.ROLE_BODY,
			)
			count.Hide()
			self.huntCountTexts.append(count)
			self.__Keep(count)
			gauge = ui.Gauge()
			gauge.SetParent(self.detailsPanel)
			gauge.AddFlag("not_pick")
			gauge.MakeGauge(224, "green")
			gauge.Hide()
			self.huntProgressGauges.append(gauge)
			self.__Keep(gauge)
		self.rewardsText = _CreateText(
			self.detailsPanel, 0, 95, localeInfo.PERMANENT_TASKS_REWARD_TITLE, 0xffc8bba6, "left",
			fontconfig.ROLE_CONTROL,
		)
		self.__Keep(self.rewardsText)
		for index in range(5):
			slot = _CreateSlot(self.detailsPanel, 152, 119, index)
			slot.SetOverInItemEvent(ui.__mem_func__(self.__OverInReward))
			slot.SetOverOutItemEvent(ui.__mem_func__(self.__OverOutItem))
			slot.Hide()
			self.rewardSlots.append(slot)
			self.__Keep(slot)
		self.rewardItemSlot = self.rewardSlots[0]
		self.passiveFrame = _CreateImage(
			self.detailsPanel, 32, 119,
			"d:/ymir work/ui/public/Slot_Base.sub",
		)
		self.__Keep(self.passiveFrame)
		self.passiveButton = ui.Button()
		self.passiveButton.SetParent(self.detailsPanel)
		self.passiveButton.SetPosition(32, 119)
		passiveIcon = ASSET_ROOT + "passive_bossologie_32.png"
		self.passiveButton.SetUpVisual(passiveIcon)
		self.passiveButton.SetOverVisual(passiveIcon)
		self.passiveButton.SetDownVisual(passiveIcon)
		self.passiveButton.Show()
		self.__Keep(self.passiveButton)
		self.rewardBonusText = _CreateText(
			self.detailsPanel, 48, 158, u"", 0xffa6d69b, "center",
			fontconfig.ROLE_CONTROL,
		)
		self.__Keep(self.rewardBonusText)
		self.r1 = _BuildR1(self)

		self.__RefreshTask()
		self.Hide()

	def __CreateCategoryTab(self, category, x, y):
		button = ui.RadioButton()
		button.SetParent(self)
		button.SetPosition(x, y)
		button.SetUpVisual(MARKET_ROOT + "tab/market_normal.png")
		button.SetOverVisual(MARKET_ROOT + "tab/market_hover.png")
		button.SetDownVisual(MARKET_ROOT + "tab/market_selected.png")
		button.SetDisableVisual(MARKET_ROOT + "tab/market_disabled.png")
		button.SetEvent(ui.__mem_func__(self.SelectCategory), category)

		icon = _CreateImage(
			button, TAB_ICON_X, TAB_ICON_Y, ASSET_ROOT + "tab_%s_16.png" % category
		)
		label = _CreateText(
			button, TAB_TEXT_CENTER_X, TAB_TEXT_CENTER_Y,
			CATEGORY_LABELS[category],
			0xffc8bba6, "center", fontconfig.ROLE_CONTROL,
			False, "center",
		)
		button.categoryIcon = icon
		button.categoryLabel = label
		button.Show()
		return button

	def SetItemToolTip(self, tooltipItem):
		self.tooltipItem = tooltipItem

	def SetSnapshotRequestEvent(self, snapshotEvent):
		self.snapshotEvent = snapshotEvent

	def SetCollectorCapability(self, available):
		available = bool(available)
		self.collectorAvailable = available
		self.collectorLoading = bool(available and self.collectorRow is None)
		self.__RefreshTask()

	def SetCollectorLoading(self, loading=True):
		self.collectorLoading = bool(loading)
		self.__RefreshTask()

	def SetCollectorSnapshot(self, row):
		row = _NormalizeCollectorRow(row)
		if row is None:
			return False
		self.collectorAvailable = True
		self.collectorLoading = False
		self.collectorRow = row
		self.__RefreshTask()
		return True

	def SetHuntSnapshots(self, rows):
		rows = _NormalizeHuntRows(rows)
		if rows is None:
			return False
		self.huntRows = rows
		self.__RefreshTask()
		if self.IsShow():
			self.__RefreshRenderTarget()
		return True

	def SetHuntRewards(self, rows):
		if not isinstance(rows, (tuple, list)) or len(rows) != 2:
			return False
		parsed = {}
		for row in rows:
			if not isinstance(row, dict):
				return False
			key = HUNT_CATEGORY_KEYS.get(_SafeInt(row.get("category")))
			stage = _SafeInt(row.get("stage"))
			revision = _SafeInt(row.get("revision"))
			rewards = row.get("rewards", ())
			if not key or key in parsed or stage <= 0 or revision <= 0 or \
					not isinstance(rewards, (tuple, list)) or len(rewards) > 5:
				return False
			rewards = tuple(_NormalizeCollectorReward(reward) for reward in rewards)
			if any(reward is None for reward in rewards):
				return False
			parsed[key] = {"stage": stage, "revision": revision, "rewards": rewards}
		self.huntRewards = parsed
		self.__RefreshTask()
		return True

	def SetCollectorSubmitResult(self, result):
		return _NormalizeCollectorRow(result) is not None

	def SetCollectorStatus(self, statusCode):
		statusCode = _SafeInt(statusCode)
		if statusCode == COLLECTOR_STATUS_UNAVAILABLE:
			self.collectorAvailable = False
			self.collectorLoading = False
		elif statusCode in (
				COLLECTOR_STATUS_LOADING, COLLECTOR_STATUS_RESYNC_REQUIRED):
			self.collectorLoading = True
		self.__RefreshTask()

	def Open(self, category=None):
		if category is None:
			category = self.category
		self.SelectCategory(category)
		self.Show()
		self.SetCenterPosition()
		self.SetTop()
		self.__RefreshRenderTarget()
		return True

	def SelectCategory(self, category):
		if category not in self.CATEGORY_ORDER:
			category = "bossologie"
		self.category = category
		for key, button in self.tabs.items():
			if key == category:
				button.Down()
				button.categoryLabel.SetPackedFontColor(0xffffe9bd)
			else:
				button.SetUp()
				button.categoryLabel.SetPackedFontColor(0xffc8bba6)
		if self.r1:
			self.r1.SelectCategory(category)
		self.__RefreshTask()
		if self.IsShow():
			self.__RefreshRenderTarget()

	def __RefreshTask(self):
		self.passiveButton.HideToolTip()
		self.__RefreshHuntTask()

	def __ShowHuntProgress(self, visible):
		for widget in self.huntProgressTexts + self.huntCountTexts + self.huntProgressGauges:
			widget.Show() if visible else widget.Hide()

	def __MonsterName(self, vnum):
		try:
			name = nonplayer.GetMonsterName(vnum)
			return name or u"Cíl %d" % vnum
		except (AttributeError, RuntimeError, TypeError, ValueError):
			return u"Cíl %d" % vnum

	def __HuntTargetName(self, row, target):
		accepted = target["accepted_vnums"]
		if row["category"] == 2 and len(accepted) > 1:
			return (u"Libovolný meteor z 1. města" if row["stage"] == 1
				else u"Libovolný meteor z 2. města")
		if len(accepted) == 1:
			name = self.__MonsterName(accepted[0])
			return name
		return u"Libovolný z uvedených cílů"

	def __LayoutHunt(self, targetCount):
		count = max(1, min(HUNT_TARGET_LIMIT, targetCount))
		extra = (count - 1) * HUNT_PROGRESS_PITCH
		height = WINDOW_SIZE[1] + (extra - 8 if count > 1 else 0)
		footerExtra = extra - 4 if count > 1 else 0
		self.SetSize(WINDOW_SIZE[0], height)
		self.previewPanel.SetSize(150, height - 94)
		self.renderView.SetSize(150, height - 94)
		self.previewFallback.SetPosition(64, (height - 94 - 22) // 2)
		self.detailsPanel.SetSize(224, height - 90)
		self.stageText.SetPosition(0, 67 + extra)
		self.rewardsText.SetPosition(0, 95 + footerExtra)
		self.passiveFrame.SetPosition(32, 119 + footerExtra)
		self.passiveButton.SetPosition(32, 119 + footerExtra)
		self.rewardItemSlot.SetPosition(152, 119 + footerExtra)
		self.rewardBonusText.SetPosition(48, 158 + footerExtra)
		if self.r1:
			self.r1.Layout(WINDOW_SIZE[0], height)

	def __RefreshHuntTask(self):
		self.__LayoutHunt(1)
		self.categoryText.SetText(CATEGORY_LABELS[self.category])
		self.rewardBonusText.SetText(u"")
		self.stageText.Hide()
		self.targetIcon.LoadImage(ASSET_ROOT + "icon_%s_22.png" % self.category)
		passiveIcon = ASSET_ROOT + "passive_%s_32.png" % self.category
		self.passiveButton.SetUpVisual(passiveIcon)
		self.passiveButton.SetOverVisual(passiveIcon)
		self.passiveButton.SetDownVisual(passiveIcon)
		self.passiveFrame.Show()
		self.passiveButton.Show()
		self.targetIcon.Hide()
		self.targetText.Hide()
		self.progressText.Hide()
		self.progressGauge.Hide()
		self.rewardsText.Show()
		for slot in getattr(self, "rewardSlots", (self.rewardItemSlot,)):
			slot.Hide()
		self.__ShowHuntProgress(False)
		row = self.huntRows.get(self.category)
		if not self.collectorAvailable:
			self.stageText.SetText(u"")
			self.targetText.SetText(u"Lov teď není dostupný")
			self.targetText.Show()
			self.passiveButton.SetToolTipText(u"Trvalý bonus: 0%")
			return
		if self.collectorLoading or row is None:
			self.stageText.SetText(u"")
			self.targetText.SetText(u"Načítání...")
			self.targetText.Show()
			self.passiveButton.SetToolTipText(u"Načítání...")
			return
		self.__LayoutHunt(len(row["targets"]))
		self.categoryText.SetText(localeInfo.PERMANENT_TASKS_STAGE % row["stage"])
		bonus = row["completed_bonus_percent"]
		self.stageText.SetText(localeInfo.PERMANENT_TASKS_COMPLETED_BONUS % bonus)
		self.stageText.Show()
		bonusName = (u"Silný proti meteorům" if row["category"] == 2
			else u"Silný proti bossům")
		self.passiveButton.SetToolTipText(
			u"%s: %d %%" % (bonusName, bonus)
		)
		if row["state"] == COLLECTOR_STATE_UNCONFIGURED:
			self.stageText.SetText(u"Dokončeno")
			self.targetText.SetText(u"Lov dokončen")
			self.targetText.Show()
			return
		self.passiveButton.SetToolTipText(
			u"%s: %d%% | +%d%% za dokončení" % (
				bonusName, bonus, row["stage_bonus_percent"]
			)
		)
		bonusLabel = (localeInfo.PERMANENT_TASKS_STONE_REWARD
			if row["category"] == 2 else localeInfo.PERMANENT_TASKS_BOSS_REWARD)
		self.rewardBonusText.SetText(bonusLabel % row["stage_bonus_percent"])
		entitlement = getattr(self, "huntRewards", {}).get(self.category, {})
		if entitlement.get("stage") == row["stage"] and entitlement.get("revision") == row["revision"]:
			rewards = entitlement["rewards"]
			count = len(rewards)
			y = 119 + (len(row["targets"]) - 1) * HUNT_PROGRESS_PITCH
			if len(row["targets"]) > 1:
				y -= 4
			if count > 2:
				self.passiveFrame.SetPosition(0, y)
				self.passiveButton.SetPosition(0, y)
			for index, reward in enumerate(rewards):
				slot = self.rewardSlots[index]
				x = (152 if count == 1 else 132 + index * 40) if count <= 2 else 56 + index * 34
				slot.SetPosition(x, y)
				slot.SetItemSlot(index, reward["vnum"], reward["amount"])
				slot.RefreshSlot()
				slot.Show()
		for index, target in enumerate(row["targets"]):
			y = HUNT_PROGRESS_TOP + index * HUNT_PROGRESS_PITCH
			self.huntProgressTexts[index].SetPosition(0, y)
			self.huntProgressTexts[index].SetText(self.__HuntTargetName(row, target))
			self.huntProgressTexts[index].Show()
			self.huntCountTexts[index].SetPosition(224, y)
			self.huntCountTexts[index].SetText(u"%d / %d" % (
				target["current"], target["required"]))
			self.huntCountTexts[index].Show()
			gauge = self.huntProgressGauges[index]
			gauge.SetPosition(0, y + 18)
			gauge.SetPercentage(target["current"], target["required"])
			gauge.Show()

	def __OverInReward(self, unusedSlot=0):
		row = self.huntRows.get(self.category)
		entitlement = self.huntRewards.get(self.category, {})
		if not row or not self.tooltipItem or entitlement.get("stage") != row["stage"] or \
				entitlement.get("revision") != row["revision"]:
			return
		index = _SafeInt(unusedSlot)
		if 0 <= index < len(entitlement["rewards"]):
			self.tooltipItem.SetItemToolTip(entitlement["rewards"][index]["vnum"])

	def __OverOutItem(self):
		if self.tooltipItem:
			self.tooltipItem.HideToolTip()

	def __EnsureRenderTarget(self):
		if self.renderIndex is not None:
			return True
		try:
			self.renderIndex = int(WikiRenderTarget.GetFreeIndex(86, 1000000))
			if self.renderIndex < 1:
				raise RuntimeError("no free render target")
			self.renderView.SetRenderTarget(self.renderIndex)
			WikiRenderTarget.SetBackground(
				self.renderIndex,
				"d:/ymir work/ui/render_target/render_target_bg.dds",
			)
			WikiRenderTarget.SetRotation(self.renderIndex, False)
			return True
		except (AttributeError, RuntimeError, TypeError, ValueError):
			self.__RemoveRenderTarget()
			return False

	def __RefreshRenderTarget(self):
		self.__HideRenderTarget()
		row = self.huntRows.get(self.category)
		if not row or row["state"] != COLLECTOR_STATE_ACTIVE:
			self.previewFallback.LoadImage(
				ASSET_ROOT + "icon_%s_22.png" % self.category
			)
			self.previewFallback.Show()
			return
		previewVnum = 0
		for target in row["targets"]:
			if target["current"] < target["required"]:
				previewVnum = target["accepted_vnums"][0]
				break
		if not previewVnum:
			self.previewFallback.Show()
			return
		self.previewFallback.LoadImage(
			ASSET_ROOT + "icon_%s_22.png" % self.category
		)
		if not self.__EnsureRenderTarget():
			self.previewFallback.Show()
			return
		try:
			WikiRenderTarget.SelectModel(
				self.renderIndex, previewVnum
			)
			WikiRenderTarget.SetVisibility(self.renderIndex, True)
			self.renderView.Show()
			self.previewFallback.Hide()
		except (AttributeError, RuntimeError, TypeError, ValueError):
			self.__HideRenderTarget()
			self.previewFallback.Show()

	def __HideRenderTarget(self):
		if self.renderIndex is not None:
			try:
				WikiRenderTarget.SetVisibility(self.renderIndex, False)
			except (AttributeError, RuntimeError):
				pass
		self.renderView.Hide()

	def __RemoveRenderTarget(self):
		index = self.renderIndex
		self.renderIndex = None
		self.renderView.Hide()
		if index is None:
			return
		try:
			WikiRenderTarget.Remove(index)
		except (AttributeError, RuntimeError):
			try:
				WikiRenderTarget.SetVisibility(index, False)
				WikiRenderTarget.ResetModel(index)
			except (AttributeError, RuntimeError):
				pass

	def Close(self):
		self.passiveButton.HideToolTip()
		self.__HideRenderTarget()
		self.Hide()

	def Destroy(self):
		self.Close()
		self.__RemoveRenderTarget()
		if self.r1:
			self.r1.Destroy()
		self.r1 = None
		self.tooltipItem = None
		self.snapshotEvent = None
		self.collectorRow = None
		self.huntRows = {}
		self.huntRewards = {}
		self.children = []
		self.tabs = {}
		self.rewardSlots = []
		self.huntProgressTexts = []
		self.huntCountTexts = []
		self.huntProgressGauges = []
		self.previewPanel = None
		self.detailsPanel = None
		self.renderView = None

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def OnPressExitKey(self):
		return self.OnPressEscapeKey()
