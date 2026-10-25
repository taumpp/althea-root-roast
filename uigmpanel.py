import app
import chat
import gmmapcatalog
import gmpanelcatalog
import item
import localeinfo
import net
import nonplayer
import ui
import uiCommon


PUBLIC_PATH = "d:/ymir work/ui/public/"


def _GetMapDisplayName(mapIndex, internalName):
	byIndex = getattr(localeinfo, "MINIMAP_ZONE_NAME_DICT_BY_IDX", {})
	displayName = byIndex.get(mapIndex, "")
	if displayName:
		return displayName

	byName = getattr(localeinfo, "MINIMAP_ZONE_NAME_DICT", {})
	displayName = byName.get(internalName, "")
	if displayName:
		return displayName

	lowerName = internalName.lower()
	for key, value in byName.items():
		if key.lower() == lowerName:
			return value

	return internalName


class GMMapSelectionDialog(ui.BoardWithTitleBar):
	WIDTH = 520
	HEIGHT = 445
	PAGE_SIZE = 18
	MAP_BUTTON_WIDTH = 180
	NAV_BUTTON_WIDTH = 61
	COLUMN_GAP = 36
	SEARCH_GAP = 12
	CONTENT_WIDTH = MAP_BUTTON_WIDTH * 2 + COLUMN_GAP
	CONTENT_LEFT = (WIDTH - CONTENT_WIDTH) // 2
	SEARCH_BOARD_WIDTH = CONTENT_WIDTH - NAV_BUTTON_WIDTH - SEARCH_GAP

	def __init__(self, selectEvent):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName("Vyber runtime mapy")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.selectEvent = selectEvent
		self.children = []
		self.mapButtons = []
		self.filteredMaps = []
		self.page = 0
		self._Build()
		self.Hide()

	def _Keep(self, child):
		self.children.append(child)
		return child

	def _MakeButton(self, x, y, text, event, xlarge=False):
		button = ui.Button()
		button.SetParent(self)
		button.SetPosition(x, y)
		prefix = "xlarge" if xlarge else "middle"
		button.SetUpVisual(PUBLIC_PATH + prefix + "_button_01.sub")
		button.SetOverVisual(PUBLIC_PATH + prefix + "_button_02.sub")
		button.SetDownVisual(PUBLIC_PATH + prefix + "_button_03.sub")
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		return self._Keep(button)

	def _Build(self):
		searchBoard = ui.ThinBoard()
		searchBoard.SetParent(self)
		searchBoard.SetPosition(self.CONTENT_LEFT, 38)
		searchBoard.SetSize(self.SEARCH_BOARD_WIDTH, 28)
		searchBoard.Show()
		self._Keep(searchBoard)

		self.searchEdit = ui.EditLine()
		self.searchEdit.SetParent(searchBoard)
		self.searchEdit.SetPosition(8, 6)
		self.searchEdit.SetSize(self.SEARCH_BOARD_WIDTH - 16, 17)
		self.searchEdit.SetMax(64)
		self.searchEdit.SetReturnEvent(ui.__mem_func__(self.ApplySearch))
		self.searchEdit.Show()
		self._Keep(self.searchEdit)

		self._MakeButton(
			self.CONTENT_LEFT + self.SEARCH_BOARD_WIDTH + self.SEARCH_GAP,
			41,
			"Hledat",
			ui.__mem_func__(self.ApplySearch),
		)

		self.summaryText = ui.TextLine()
		self.summaryText.SetParent(self)
		self.summaryText.SetPosition(self.WIDTH // 2, 74)
		self.summaryText.SetHorizontalAlignCenter()
		self.summaryText.Show()
		self._Keep(self.summaryText)

		for index in range(self.PAGE_SIZE):
			button = self._MakeButton(
				self.CONTENT_LEFT + (index % 2) * (
					self.MAP_BUTTON_WIDTH + self.COLUMN_GAP),
				98 + (index // 2) * 29,
				"",
				lambda: None,
				True,
			)
			button.Hide()
			self.mapButtons.append(button)

		previousInset = (self.MAP_BUTTON_WIDTH - self.NAV_BUTTON_WIDTH) // 2
		nextInset = self.MAP_BUTTON_WIDTH - self.NAV_BUTTON_WIDTH - previousInset
		self.previousButton = self._MakeButton(
			self.CONTENT_LEFT + previousInset,
			374,
			"Predchozi",
			ui.__mem_func__(self.PreviousPage),
		)
		self.nextButton = self._MakeButton(
			self.CONTENT_LEFT + self.MAP_BUTTON_WIDTH + self.COLUMN_GAP + nextInset,
			374,
			"Dalsi",
			ui.__mem_func__(self.NextPage),
		)

		self.pageText = ui.TextLine()
		self.pageText.SetParent(self)
		self.pageText.SetPosition(self.WIDTH // 2, 379)
		self.pageText.SetHorizontalAlignCenter()
		self.pageText.Show()
		self._Keep(self.pageText)

	def Open(self):
		self.searchEdit.SetText("")
		self.ApplySearch()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.searchEdit.SetFocus()

	def Close(self):
		self.searchEdit.KillFocus()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		return self.Close()

	def ApplySearch(self):
		query = self.searchEdit.GetText().strip().lower()
		self.filteredMaps = []
		for mapIndex, internalName in gmmapcatalog.RUNTIME_MAPS:
			displayName = _GetMapDisplayName(mapIndex, internalName)
			searchText = "%d %s %s" % (mapIndex, internalName, displayName)
			if not query or query in searchText.lower():
				self.filteredMaps.append((mapIndex, internalName, displayName))
		self.page = 0
		self._RefreshPage()
		return True

	def _RefreshPage(self):
		total = len(self.filteredMaps)
		pageCount = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
		self.page = max(0, min(self.page, pageCount - 1))
		start = self.page * self.PAGE_SIZE
		visible = self.filteredMaps[start:start + self.PAGE_SIZE]

		for index, button in enumerate(self.mapButtons):
			if index < len(visible):
				mapEntry = visible[index]
				label = "%03d | %s" % (mapEntry[0], mapEntry[2])
				if len(label) > 31:
					label = label[:28] + "..."
				button.SetText(label)
				button.SetEvent(lambda mapEntry=mapEntry: self._SelectMap(mapEntry))
				button.Show()
			else:
				button.Hide()

		self.summaryText.SetText("Nalezeno map: %d z %d" % (
			total, len(gmmapcatalog.RUNTIME_MAPS)))
		self.pageText.SetText("Strana %d / %d" % (self.page + 1, pageCount))
		if self.page > 0:
			self.previousButton.Enable()
		else:
			self.previousButton.Disable()
		if self.page + 1 < pageCount:
			self.nextButton.Enable()
		else:
			self.nextButton.Disable()

	def PreviousPage(self):
		if self.page > 0:
			self.page -= 1
			self._RefreshPage()

	def NextPage(self):
		pageCount = max(1,
			(len(self.filteredMaps) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
		if self.page + 1 < pageCount:
			self.page += 1
			self._RefreshPage()

	def _SelectMap(self, mapEntry):
		self.Close()
		if self.selectEvent:
			self.selectEvent(mapEntry)


class GMEntitySelectionDialog(ui.BoardWithTitleBar):
	WIDTH = 570
	HEIGHT = 445
	PAGE_SIZE = 12
	MAX_RESULTS = 32
	RECENT = {"item": [], "mob": []}

	def __init__(self, selectEvent):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.selectEvent = selectEvent
		self.mode = "item"
		self.children = []
		self.results = []
		self.resultByVnum = {}
		self.page = 0
		self.selectedEntry = None
		self.searchChangedAt = 0.0
		self.lastAppliedQuery = None
		self._Build()
		self.Hide()

	def _Keep(self, child):
		self.children.append(child)
		return child

	def _MakeButton(self, parent, x, y, text, event, xlarge=False):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		prefix = "xlarge" if xlarge else "middle"
		button.SetUpVisual(PUBLIC_PATH + prefix + "_button_01.sub")
		button.SetOverVisual(PUBLIC_PATH + prefix + "_button_02.sub")
		button.SetDownVisual(PUBLIC_PATH + prefix + "_button_03.sub")
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		return self._Keep(button)

	def _MakeText(self, parent, text, x, y):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		return self._Keep(line)

	def _Build(self):
		searchBoard = ui.ThinBoard()
		searchBoard.SetParent(self)
		searchBoard.SetPosition(20, 38)
		searchBoard.SetSize(430, 28)
		searchBoard.Show()
		self._Keep(searchBoard)

		self.searchEdit = ui.EditLine()
		self.searchEdit.SetParent(searchBoard)
		self.searchEdit.SetPosition(8, 6)
		self.searchEdit.SetSize(414, 17)
		self.searchEdit.SetMax(64)
		self.searchEdit.SetInfoMessage("Zadej nazev nebo VNUM")
		self.searchEdit.SetReturnEvent(ui.__mem_func__(self.AcceptOrSearch))
		self.searchEdit.SetEscapeEvent(ui.__mem_func__(self.Close))
		self.searchEdit.SetUpArrowEvent(ui.__mem_func__(self.SelectPrevious))
		self.searchEdit.SetDownArrowEvent(ui.__mem_func__(self.SelectNext))
		self.searchEdit.OnIMEUpdate = self._OnSearchIMEUpdate
		self.searchEdit.Show()
		self._Keep(self.searchEdit)

		self._MakeButton(self, 466, 41, "Hledat",
			ui.__mem_func__(self.ApplySearch))

		self.hintText = self._MakeText(self, "", 20, 73)
		self.resultSummary = self._MakeText(self, "", 550, 73)
		self.resultSummary.SetHorizontalAlignRight()

		resultBoard = ui.ThinBoard()
		resultBoard.SetParent(self)
		resultBoard.SetPosition(20, 92)
		resultBoard.SetSize(530, 222)
		resultBoard.Show()
		self._Keep(resultBoard)

		self.resultList = ui.ListBox()
		self.resultList.SetParent(resultBoard)
		self.resultList.SetPosition(8, 7)
		self.resultList.SetSize(514, 204)
		self.resultList.SetTextCenterAlign(False)
		self.resultList.SetEvent(ui.__mem_func__(self._SelectResult))
		self.resultList.SetDoubleClickEvent(
			ui.__mem_func__(self._DoubleClickResult))
		self.resultList.Show()
		self._Keep(self.resultList)

		self.previousButton = self._MakeButton(
			self, 80, 322, "Predchozi", ui.__mem_func__(self.PreviousPage))
		self.pageText = self._MakeText(self, "Strana 1 / 1", self.WIDTH // 2, 328)
		self.pageText.SetHorizontalAlignCenter()
		self.nextButton = self._MakeButton(
			self, 429, 322, "Dalsi", ui.__mem_func__(self.NextPage))

		previewBoard = ui.ThinBoard()
		previewBoard.SetParent(self)
		previewBoard.SetPosition(20, 356)
		previewBoard.SetSize(530, 58)
		previewBoard.Show()
		self._Keep(previewBoard)

		self.previewIcon = ui.ExpandedImageBox()
		self.previewIcon.SetParent(previewBoard)
		self.previewIcon.SetPosition(12, 13)
		self.previewIcon.Hide()
		self._Keep(self.previewIcon)

		self.previewName = self._MakeText(
			previewBoard, "Nevybrano", 54, 10)
		self.previewDetail = self._MakeText(
			previewBoard, "Vyber zaznam ze seznamu.", 54, 32)
		self.acceptButton = self._MakeButton(
			previewBoard, 430, 15, "Vybrat", ui.__mem_func__(self.Accept))
		self.acceptButton.Disable()

	def Open(self, mode, currentVnum=0):
		self.mode = mode if mode in ("item", "mob") else "item"
		self.SetTitleName(
			"Vyber predmetu" if self.mode == "item" else "Vyber monstra")
		self.hintText.SetText(
			"Predmety: nazev nebo VNUM, sipky + Enter"
			if self.mode == "item" else
			u"Monstra a meteory: název nebo VNUM, šipky + Enter")
		self.searchEdit.SetText(str(currentVnum) if currentVnum > 0 else "")
		self.lastAppliedQuery = None
		self.ApplySearch()
		self.SetCenterPosition()
		self.SetTop()
		self.Show()
		self.searchEdit.SetFocus()

	def Close(self):
		self.searchEdit.KillFocus()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		return self.Close()

	def _OnSearchIMEUpdate(self):
		ui.EditLine.OnIMEUpdate(self.searchEdit)
		self.searchChangedAt = app.GetTime()

	def OnUpdate(self):
		if not self.IsShow():
			return
		query = self.searchEdit.GetText().strip()
		if query == self.lastAppliedQuery:
			return
		if app.GetTime() - self.searchChangedAt < 0.20:
			return
		self.ApplySearch()

	def _ItemEntry(self, vnum):
		try:
			item.SelectItem(int(vnum))
			name = item.GetItemName().strip()
			if not name:
				return None
			return {
				"vnum": int(vnum),
				"name": name,
				"detail": "Predmet | VNUM %d" % int(vnum),
				"icon": item.GetIconImageFileName(),
				"iconScale": 1.0 / max(1, int(item.GetItemSize()[1])),
			}
		except:
			return None

	def _MobEntry(self, vnum):
		try:
			vnum = int(vnum)
			name = nonplayer.GetMonsterName(vnum).strip()
			if not name:
				return None
			level = int(nonplayer.GetMonsterLevel(vnum))
			kind = "Meteor" if nonplayer.IsMonsterStone(vnum) else "Monstrum"
			return {
				"vnum": vnum,
				"name": name,
				"detail": "%s | Level %d | VNUM %d" % (
					kind, level, vnum),
				"icon": "",
				"iconScale": 1.0,
			}
		except:
			return None

	def _BuildEntry(self, vnum):
		if self.mode == "item":
			return self._ItemEntry(vnum)
		return self._MobEntry(vnum)

	def _SearchVnums(self, query):
		if not query:
			return list(self.RECENT[self.mode])
		if query.isdigit():
			return [int(query)] if int(query) > 0 else []
		if len(query) < 2:
			return []

		try:
			if self.mode == "item":
				return list(item.GetItemsByName(query, self.MAX_RESULTS))
			return list(nonplayer.GetMobsByName(query.lower()))[:self.MAX_RESULTS]
		except:
			return []

	def ApplySearch(self):
		query = self.searchEdit.GetText().strip()
		self.lastAppliedQuery = query
		self.searchChangedAt = app.GetTime()
		vnums = self._SearchVnums(query)
		entries = []
		seen = set()
		for vnum in vnums:
			vnum = int(vnum)
			if vnum <= 0 or vnum in seen:
				continue
			seen.add(vnum)
			entry = self._BuildEntry(vnum)
			if entry:
				entries.append(entry)
			if len(entries) >= self.MAX_RESULTS:
				break

		lowerQuery = query.lower()
		entries.sort(key=lambda entry: (
			0 if lowerQuery and entry["name"].lower().startswith(lowerQuery) else 1,
			entry["name"].lower(), entry["vnum"]))
		self.results = entries
		self.resultByVnum = dict(
			(entry["vnum"], entry) for entry in self.results)
		self.page = 0
		self.selectedEntry = None
		self._RefreshPage()
		return True

	def _EntryLabel(self, entry):
		name = entry["name"]
		if len(name) > 42:
			name = name[:39] + "..."
		return "%s  |  VNUM %d" % (name, entry["vnum"])

	def _RefreshPage(self):
		total = len(self.results)
		pageCount = max(1, (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
		self.page = max(0, min(self.page, pageCount - 1))
		start = self.page * self.PAGE_SIZE
		visible = self.results[start:start + self.PAGE_SIZE]

		self.resultList.ClearItem()
		for entry in visible:
			self.resultList.InsertItem(
				entry["vnum"], self._EntryLabel(entry))

		if not self.searchEdit.GetText().strip():
			self.resultSummary.SetText(
				"Posledni: %d" % total if total else "Zadej hledany text")
		else:
			self.resultSummary.SetText("Nalezeno: %d" % total)
		self.pageText.SetText(
			"Strana %d / %d" % (self.page + 1, pageCount))
		self.previousButton.Enable() if self.page > 0 else self.previousButton.Disable()
		self.nextButton.Enable() if self.page + 1 < pageCount else self.nextButton.Disable()
		self._ShowPreview(None)
		if visible:
			self.resultList.SelectItem(0)

	def _ShowPreview(self, entry):
		self.selectedEntry = entry
		self.previewIcon.Hide()
		if not entry:
			self.previewName.SetText("Nevybrano")
			self.previewDetail.SetText("Vyber zaznam ze seznamu.")
			self.acceptButton.Disable()
			return

		self.previewName.SetText(entry["name"])
		self.previewDetail.SetText(entry["detail"])
		if entry["icon"]:
			try:
				self.previewIcon.LoadImage(entry["icon"])
				scale = entry.get("iconScale", 1.0)
				self.previewIcon.SetScale(scale, scale)
				self.previewIcon.Show()
			except:
				self.previewIcon.Hide()
		self.acceptButton.Enable()

	def _SelectResult(self, vnum, unusedText):
		self._ShowPreview(self.resultByVnum.get(int(vnum)))

	def _DoubleClickResult(self, vnum):
		entry = self.resultByVnum.get(int(vnum))
		if entry:
			self._ShowPreview(entry)
			self.Accept()

	def _MoveSelection(self, direction):
		count = self.resultList.GetItemCount()
		if count <= 0:
			return
		current = self.resultList.GetSelectedLine()
		if current < 0:
			current = 0 if direction > 0 else count - 1
		else:
			current = max(0, min(count - 1, current + direction))
		self.resultList.SelectItem(current)

	def SelectPrevious(self):
		self._MoveSelection(-1)

	def SelectNext(self):
		self._MoveSelection(1)

	def PreviousPage(self):
		if self.page > 0:
			self.page -= 1
			self._RefreshPage()

	def NextPage(self):
		pageCount = max(1,
			(len(self.results) + self.PAGE_SIZE - 1) // self.PAGE_SIZE)
		if self.page + 1 < pageCount:
			self.page += 1
			self._RefreshPage()

	def AcceptOrSearch(self):
		if self.searchEdit.GetText().strip() != self.lastAppliedQuery:
			self.ApplySearch()
			return True
		if self.selectedEntry:
			self.Accept()
		else:
			self.ApplySearch()
		return True

	def Accept(self):
		if not self.selectedEntry:
			return
		entry = self.selectedEntry
		recent = self.RECENT[self.mode]
		if entry["vnum"] in recent:
			recent.remove(entry["vnum"])
		recent.insert(0, entry["vnum"])
		del recent[12:]
		self.Close()
		if self.selectEvent:
			self.selectEvent(self.mode, entry)


class GMPanelWindow(ui.BoardWithTitleBar):
	WIDTH = 700
	HEIGHT = 455
	ACTION_PANEL_WIDTH = 318
	FORM_PANEL_WIDTH = 344
	CONTENT_HEIGHT = 330

	def __init__(self):
		ui.BoardWithTitleBar.__init__(self)
		self.AddFlag("movable")
		self.AddFlag("float")
		self.SetSize(self.WIDTH, self.HEIGHT)
		self.SetTitleName("GM panel (F10)")
		self.SetCloseEvent(ui.__mem_func__(self.Close))
		self.SetCenterPosition()

		self.requestID = 0
		self.actionMask = 0
		self.gmLevel = 0
		self.capabilitiesLoaded = False
		self.openAfterQuery = False
		self.selectedAction = None
		self.selectedCategory = None
		self.questionDialog = None
		self.mapDialog = None
		self.entityDialog = None
		self.selectedMapIndex = 0
		self.selectedMapName = ""
		self.selectedEntities = {}
		self.children = []
		self.actionButtons = {}
		self.categoryButtons = {}
		self.fieldRows = {}
		# What the server described of this session's actions; empty until a
		# complete set of rows arrived.
		self.catalogCollector = gmpanelcatalog.Collector()
		self.catalog = self.catalogCollector.catalog

		self._Build()
		self.Hide()

	def Destroy(self):
		self.CloseQuestion()
		self.CloseMapDialog()
		self.CloseEntityDialog()
		self.Hide()
		self.actionButtons = {}
		self.categoryButtons = {}
		self.fieldRows = {}
		self.children = []

	def _MakeText(self, parent, text, x, y):
		line = ui.TextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetText(text)
		line.Show()
		self.children.append(line)
		return line

	def _MakeMultiText(self, parent, text, x, y, width, height):
		line = ui.MultiTextLine()
		line.SetParent(parent)
		line.SetPosition(x, y)
		line.SetSize(width, height)
		line.SetText(text)
		line.Show()
		self.children.append(line)
		return line

	def _MakePanel(self, x, y, width, height):
		panel = ui.ThinBoard()
		panel.SetParent(self)
		panel.SetPosition(x, y)
		panel.SetSize(width, height)
		panel.Show()
		self.children.append(panel)
		return panel

	def _MakeButton(self, parent, x, y, text, event):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual(PUBLIC_PATH + "large_button_01.sub")
		button.SetOverVisual(PUBLIC_PATH + "large_button_02.sub")
		button.SetDownVisual(PUBLIC_PATH + "large_button_03.sub")
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		self.children.append(button)
		return button

	def _MakeTabButton(self, parent, x, y, text, event):
		button = ui.Button()
		button.SetParent(parent)
		button.SetPosition(x, y)
		button.SetUpVisual(PUBLIC_PATH + "middle_button_01.sub")
		button.SetOverVisual(PUBLIC_PATH + "middle_button_02.sub")
		button.SetDownVisual(PUBLIC_PATH + "middle_button_03.sub")
		button.SetText(text)
		button.SetEvent(event)
		button.Show()
		self.children.append(button)
		return button

	def _MakeField(self, parent, name, maximum):
		label = self._MakeText(parent, "", 16, 0)
		board = ui.ThinBoard()
		board.SetParent(parent)
		board.SetPosition(14, 0)
		board.SetSize(312, 27)
		board.Show()
		self.children.append(board)

		edit = ui.EditLine()
		edit.SetParent(board)
		edit.SetPosition(8, 6)
		edit.SetSize(296, 17)
		edit.SetMax(maximum)
		edit.Show()
		self.children.append(edit)
		self.fieldRows[name] = (label, board, edit)

	def _MakeMapField(self, parent):
		self.mapFieldLabel = self._MakeText(parent, "", 16, 0)
		self.mapFieldBoard = ui.ThinBoard()
		self.mapFieldBoard.SetParent(parent)
		self.mapFieldBoard.SetPosition(14, 0)
		self.mapFieldBoard.SetSize(312, 42)
		self.mapFieldBoard.Show()
		self.children.append(self.mapFieldBoard)

		self.mapFieldText = self._MakeText(
			self.mapFieldBoard, "Mapa neni vybrana", 9, 13)
		self.mapSelectButton = self._MakeTabButton(
			self.mapFieldBoard, 211, 9, "Vybrat", ui.__mem_func__(self.OpenMapDialog))

	def _Build(self):
		summaryPanel = self._MakePanel(12, 34, 676, 54)
		self.statusText = self._MakeMultiText(summaryPanel,
			"Pripraveno. Opravneni se nactou pri prvnim otevreni.", 14, 9, 430, 34)
		self.roleText = self._MakeText(summaryPanel, "Opravneni: -", 458, 8)
		self.actionCountText = self._MakeText(summaryPanel, "Dostupne akce: -", 458, 28)

		actionPanel = self._MakePanel(12, 96, self.ACTION_PANEL_WIDTH, self.CONTENT_HEIGHT)
		formPanel = self._MakePanel(338, 96, self.FORM_PANEL_WIDTH, self.CONTENT_HEIGHT)
		self.actionPanel = actionPanel
		self._MakeText(actionPanel, "Kategorie", 14, 10)
		self.categorySummary = self._MakeText(actionPanel, "", 14, 88)

		self.actionTitle = self._MakeText(formPanel, "Vyber akci", 16, 12)
		self.actionMeta = self._MakeText(formPanel, "", 16, 34)
		self.actionDescription = self._MakeMultiText(formPanel, "", 16, 56, 312, 42)

		self._MakeField(formPanel, "target", 24)
		self._MakeField(formPanel, "argument", 127)
		self._MakeField(formPanel, "value", 12)
		self._MakeField(formPanel, "secondary", 12)
		self._MakeField(formPanel, "reason", 95)
		self._MakeMapField(formPanel)
		self.entitySelectButton = self._MakeTabButton(
			self.fieldRows["value"][1], 211, 3, "Vybrat",
			ui.__mem_func__(self.OpenEntityDialog))
		self.entitySelectButton.Hide()

		self.executeButton = self._MakeButton(formPanel, 122, 126, "Spustit akci", ui.__mem_func__(self.ExecuteSelected))
		self.executeButton.Disable()
		self._HideAllFields()

	def _HideAllFields(self):
		for label, board, edit in self.fieldRows.values():
			label.Hide()
			board.Hide()
		self.fieldRows["value"][2].SetSize(296, 17)
		self.entitySelectButton.Hide()
		self.mapFieldLabel.Hide()
		self.mapFieldBoard.Hide()

	def _CanUse(self, action):
		return bool(self.actionMask & (1 << action))

	def _CategoryPosition(self, index):
		return 7 + (index % 3) * 101, 34 + (index // 3) * 25

	def _ActionPosition(self, index, plain):
		# Actions the catalogue does not describe are listed by number on
		# small buttons, so every one a mask can hold stays reachable.
		if plain:
			return 7 + (index % 5) * 61, 112 + (index // 5) * 25
		return 10 + (index % 2) * 151, 112 + (index // 2) * 38

	def _CountAvailableActions(self, category=None):
		return sum(1 for action in self.catalog.Actions(self.actionMask)
			if category is None or self.catalog.Info(action)["category"] == category)

	def _RoleName(self):
		return self.catalog.RoleName(self.gmLevel)

	def _DropButtons(self):
		for button in list(self.categoryButtons.values()) + list(self.actionButtons.values()):
			button.Hide()
			self.children.remove(button)
		self.categoryButtons = {}
		self.actionButtons = {}

	def _CategoryButton(self, category):
		button = self.categoryButtons.get(category)
		if button is None:
			button = self._MakeTabButton(self.actionPanel, 0, 0,
				self.catalog.CategoryLabel(category), lambda category=category: self.SelectCategory(category))
			self.categoryButtons[category] = button
		return button

	def _ActionButton(self, action):
		button = self.actionButtons.get(action)
		if button is None:
			info = self.catalog.Info(action)
			make = self._MakeTabButton if info["plain"] else self._MakeButton
			button = make(self.actionPanel, 0, 0, info["label"],
				lambda action=action: self.SelectAction(action))
			self.actionButtons[action] = button
		return button

	def SetCatalogCollector(self, collector):
		"""Rows that arrived before the panel was built."""
		self.catalogCollector = collector
		self._ApplyCatalog()

	def OnCatalogRow(self, row):
		if self.catalogCollector.Row(row):
			self._ApplyCatalog()

	def _ApplyCatalog(self):
		self.catalog = self.catalogCollector.catalog
		self.CloseQuestion()
		self.CloseEntityDialog()
		self._DropButtons()
		self.selectedAction = None
		self.selectedCategory = None
		if self.capabilitiesLoaded:
			self._RefreshSummary()
			self._RefreshActions()

	def _RefreshSummary(self):
		self.roleText.SetText("Opravneni: %s (%d)" % (self._RoleName(), self.gmLevel))
		self.actionCountText.SetText("Dostupne akce: %d / %d" % (
			self._CountAvailableActions(), self.catalog.Total(self.actionMask)))

	def _NextRequestID(self):
		self.requestID += 1
		if self.requestID > 2147483647:
			self.requestID = 1
		return self.requestID

	def QueryCapabilities(self, openAfter=False):
		self.openAfterQuery = bool(openAfter)
		self._SetStatus("Nacitam opravneni ze serveru...")
		if not net.SendGMPanelAction(self._NextRequestID(), net.GM_PANEL_ACTION_QUERY, 0, 0, "", "", ""):
			self.openAfterQuery = False
			self._SetStatus("Pozadavek se nepodarilo odeslat.")

	def Toggle(self):
		if self.IsShow():
			self.Close()
			return

		if not self.capabilitiesLoaded:
			self.QueryCapabilities(True)
			return

		if self.actionMask:
			self.Open()

	def Open(self):
		if not self.actionMask:
			return
		self.SetCenterPosition()
		self.SetTop()
		self.Show()

	def Close(self):
		self.CloseQuestion()
		self.CloseMapDialog()
		self.CloseEntityDialog()
		self.Hide()
		return True

	def OnPressEscapeKey(self):
		return self.Close()

	def _RefreshActions(self):
		actions = self.catalog.Actions(self.actionMask)
		availableCategories = self.catalog.Categories(self.actionMask)

		for category, button in self.categoryButtons.items():
			if category not in availableCategories:
				button.Hide()
		for index, category in enumerate(availableCategories):
			button = self._CategoryButton(category)
			button.SetPosition(*self._CategoryPosition(index))
			button.Show()

		if self.selectedCategory not in availableCategories:
			self.selectedCategory = availableCategories[0] if availableCategories else None
		for category, button in self.categoryButtons.items():
			if category == self.selectedCategory:
				button.Down()
			else:
				button.SetUp()

		if self.selectedCategory is not None:
			self.categorySummary.SetText("%s | %d dostupnych" % (
				self.catalog.CategoryLabel(self.selectedCategory),
				self._CountAvailableActions(self.selectedCategory)))
		else:
			self.categorySummary.SetText("Zadna dostupna akce")

		firstAction = None
		visibleIndex = 0
		for action, button in self.actionButtons.items():
			if action not in actions:
				button.Hide()
		for action in actions:
			info = self.catalog.Info(action)
			if info["category"] == self.selectedCategory:
				button = self._ActionButton(action)
				button.SetPosition(*self._ActionPosition(visibleIndex, info["plain"]))
				button.Show()
				visibleIndex += 1
				if firstAction is None:
					firstAction = action
			elif action in self.actionButtons:
				self.actionButtons[action].Hide()

		if (self.selectedAction is None or not self._CanUse(self.selectedAction) or
			self.catalog.Info(self.selectedAction)["category"] != self.selectedCategory):
			self.SelectAction(firstAction)

	def SelectCategory(self, category):
		if category == self.selectedCategory:
			return
		self.selectedCategory = category
		self.selectedAction = None
		self._RefreshActions()

	def SelectAction(self, action):
		if action is None or not self._CanUse(action):
			self.selectedAction = None
			self.executeButton.Disable()
			return

		previousAction = self.selectedAction
		if self.selectedAction in self.actionButtons:
			self.actionButtons[self.selectedAction].SetUp()
		self.selectedAction = action
		self.actionButtons[action].Down()

		info = self.catalog.Info(action)
		self.actionTitle.SetText(info["label"])
		self.actionMeta.SetText("Kategorie: %s | Potvrzeni: %s" % (
			self.catalog.CategoryLabel(info["category"]), "ano" if info["confirm"] else "ne"))
		self.actionDescription.SetText(info["description"])
		self._HideAllFields()
		if info["picker"]:
			self.fieldRows["value"][2].SetSize(190, 17)
			self.entitySelectButton.Show()
			if previousAction != action:
				self.fieldRows["value"][2].SetText("")
				self.fieldRows["secondary"][2].SetText("1")

		labels = info["labels"]
		# Without a description every input is offered, packed closer.
		fieldY, fieldStep = (56, 46) if info["plain"] else (104, 56)
		for fieldName in info["fields"]:
			if fieldName == "map":
				self.mapFieldLabel.SetText(labels[fieldName])
				self.mapFieldLabel.SetPosition(16, fieldY)
				self.mapFieldBoard.SetPosition(14, fieldY + 17)
				self.mapFieldLabel.Show()
				self.mapFieldBoard.Show()
				fieldY += 70
				continue
			label, board, edit = self.fieldRows[fieldName]
			label.SetText(labels[fieldName])
			label.SetPosition(16, fieldY)
			board.SetPosition(14, fieldY + 17)
			label.Show()
			board.Show()
			fieldY += fieldStep
		self.executeButton.SetPosition(122, min(fieldY + 8, 294))
		self.executeButton.Enable()

	def _ReadInteger(self, fieldName):
		text = self.fieldRows[fieldName][2].GetText().strip()
		if not text:
			return 0
		return int(text)

	def ExecuteSelected(self):
		if self.selectedAction is None or not self._CanUse(self.selectedAction):
			return

		info = self.catalog.Info(self.selectedAction)
		fields = info["fields"]
		try:
			value = self._ReadInteger("value") if "value" in fields else 0
			secondary = self._ReadInteger("secondary") if "secondary" in fields else 0
		except ValueError:
			self._SetStatus("Ciselna pole musi obsahovat platne cele cislo.")
			return

		target = self.fieldRows["target"][2].GetText().strip() if "target" in fields else ""
		argument = self.fieldRows["argument"][2].GetText().strip() if "argument" in fields else ""
		reason = self.fieldRows["reason"][2].GetText().strip() if "reason" in fields else ""

		if "map" in fields:
			if self.selectedMapIndex <= 0:
				self._SetStatus("Nejprve vyber cilovou mapu.")
				return
			value = self.selectedMapIndex

		# Which inputs an undescribed action needs is for the server to say.
		if "target" in fields and not target and not info["plain"]:
			self._SetStatus("Vypln jmeno hrace.")
			return
		if "argument" in fields and not argument and not info["plain"]:
			self._SetStatus("Vypln argument akce.")
			return
		if info["reason"] and len(reason) < 3:
			self._SetStatus("Vypln duvod alespon o trech znacich.")
			return

		payload = (value, secondary, target, argument, reason)
		if info["confirm"]:
			confirmation = "Opravdu chces provest akci '%s'?" % info["label"]
			if info["picker"] and value > 0:
				entry = self.selectedEntities.get(info["picker"])
				name = entry["name"] if entry and entry["vnum"] == value else "VNUM %d" % value
				confirmation = "Opravdu chces pouzit %s x%d?" % (
					name, secondary)
			self._OpenQuestion(confirmation,
				self.selectedAction, payload)
		else:
			self._SendSelected(self.selectedAction, payload)

	def _OpenQuestion(self, text, action, payload):
		self.CloseQuestion()
		dialog = uiCommon.QuestionDialog()
		dialog.SetText(text)
		dialog.SetAcceptEvent(lambda action=action, payload=payload: self._AcceptQuestion(action, payload))
		dialog.SetCancelEvent(ui.__mem_func__(self.CloseQuestion))
		dialog.Open()
		self.questionDialog = dialog

	def _AcceptQuestion(self, action, payload):
		self.CloseQuestion()
		self._SendSelected(action, payload, True)

	def CloseQuestion(self):
		if self.questionDialog:
			self.questionDialog.Close()
			self.questionDialog = None
		return True

	def OpenMapDialog(self):
		if self.mapDialog is None:
			self.mapDialog = GMMapSelectionDialog(
				ui.__mem_func__(self._SelectMap))
		self.mapDialog.Open()

	def CloseMapDialog(self):
		if self.mapDialog:
			self.mapDialog.Close()
		return True

	def OpenEntityDialog(self):
		if self.selectedAction is None:
			return
		mode = self.catalog.Info(self.selectedAction)["picker"]
		if not mode:
			return
		try:
			currentVnum = self._ReadInteger("value")
		except ValueError:
			currentVnum = 0
		if self.entityDialog is None:
			self.entityDialog = GMEntitySelectionDialog(
				ui.__mem_func__(self._SelectEntity))
		self.entityDialog.Open(mode, currentVnum)

	def CloseEntityDialog(self):
		if self.entityDialog:
			self.entityDialog.Close()
		return True

	def _SelectEntity(self, mode, entry):
		if self.selectedAction is None or \
			self.catalog.Info(self.selectedAction)["picker"] != mode:
			return
		self.selectedEntities[mode] = entry
		self.fieldRows["value"][2].SetText(str(entry["vnum"]))
		if not self.fieldRows["secondary"][2].GetText().strip():
			self.fieldRows["secondary"][2].SetText("1")
		self._SetStatus("Vybrano: %s (VNUM %d)." % (
			entry["name"], entry["vnum"]))

	def _SelectMap(self, mapEntry):
		self.selectedMapIndex = int(mapEntry[0])
		self.selectedMapName = mapEntry[2]
		label = "%03d | %s" % (self.selectedMapIndex, self.selectedMapName)
		if len(label) > 30:
			label = label[:27] + "..."
		self.mapFieldText.SetText(label)
		self._SetStatus("Vybrana mapa: %s" % label)

	def _SendSelected(self, action, payload, confirmed=False):
		value, secondary, target, argument, reason = payload
		if confirmed and self.catalog.Info(action)["mark"]:
			secondary = 1

		if net.SendGMPanelAction(self._NextRequestID(), action, value,
			secondary, target, argument, reason):
			self._SetStatus("Pozadavek byl odeslan serveru...")
		else:
			self._SetStatus("Pozadavek se nepodarilo odeslat.")

	def OnServerResult(self, requestID, action, status, gmLevel, maskLow, maskHigh, message):
		self.gmLevel = gmLevel
		self.actionMask = (maskLow & 0xffffffff) | ((maskHigh & 0xffffffff) << 32)
		self._RefreshSummary()

		if status == net.GM_PANEL_RESULT_CAPABILITIES:
			self.capabilitiesLoaded = True
			self._RefreshActions()
			if self.openAfterQuery and self.actionMask:
				self.Open()
			self.openAfterQuery = False
		elif status == net.GM_PANEL_RESULT_DENIED and action == net.GM_PANEL_ACTION_QUERY:
			self.capabilitiesLoaded = False
			self.actionMask = 0
			self.openAfterQuery = False

		self._SetStatus(message)
		if message:
			chat.AppendChat(chat.CHAT_TYPE_INFO, "[GM panel] %s" % message)

	def _SetStatus(self, message):
		self.statusText.SetText(message or "")


def NewWindow():
	"""The panel the interface builds once the server grants an action: the R1 panel (uigmpanelr1, design B2)
	unless Settings -> "Stary vzhled" chose the original look or R1 failed in this session; a failure while
	building R1 is traced and this original panel is built instead."""
	r1 = None
	try:
		import uigmpanelr1
		r1 = uigmpanelr1
		if r1.UseR1():
			return r1.GMPanelR1Window()
	except Exception:
		if r1 is not None:
			r1.Failed()
		else:
			try:
				import dbg
				dbg.TraceError("R1 look of GM panel could not be loaded, the original look is used.")
			except Exception:
				pass
	return GMPanelWindow()
