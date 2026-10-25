import ui, player, item, net, app, localeInfo
from uiToolTip import ItemToolTip, GET_AFFECT_STRING

import osfInfo
import characterbonuses
import textcase

IMG_DIR = "d:/ymir work/ui/game/characterdetails/"
# Categories define presentation order; native APPLY mapping owns point identities. Every bonus of a group belongs
# in its category (the element resistances beside each other in Obranne); Ostatni keeps the stats, HP / SP, the
# shop, dungeon and skill tree bonuses. A name this EXE does not know is skipped (getattr), no row is invented.
def _Apply(name):
	return getattr(item, "APPLY_" + name, None)

bonus_list = [
	[localeInfo.BONUS_TABLE_TITLE_1,
		[
			_Apply("ATTBONUS_MONSTER"),
			_Apply("ATTBONUS_ORDINARY_MONSTER"),
			_Apply("ATTBONUS_METIN"),
			_Apply("ATTBONUS_BOSS"),
			_Apply("ATTBONUS_UNDEAD"),
			_Apply("ATTBONUS_DEVIL"),
			_Apply("ATTBONUS_ORC"),
			_Apply("ATTBONUS_ANIMAL"),
			_Apply("ATTBONUS_MILGYO"),
			_Apply("ATTBONUS_INSECT"),
			_Apply("ATTBONUS_DESERT"),
			_Apply("ATTBONUS_CZ"),
			_Apply("PVM_ATTBONUS"),
			_Apply("RESIST_MONSTER"),
			_Apply("RESIST_BOSS"),
			_Apply("STEAL_HP"),
			_Apply("STEAL_SP"),
			_Apply("HP_REGEN"),
			_Apply("EXP_DOUBLE_BONUS"),
			_Apply("GOLD_DOUBLE_BONUS"),
			_Apply("ITEM_DROP_BONUS"),
			_Apply("ENCHANT_ELECT"),
			_Apply("ENCHANT_ELEC"),
			_Apply("ENCHANT_FIRE"),
			_Apply("ENCHANT_ICE"),
			_Apply("ENCHANT_WIND"),
			_Apply("ENCHANT_EARTH"),
			_Apply("ENCHANT_DARK"),
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_2,
		[
			_Apply("ATTBONUS_HUMAN"),
			_Apply("ATTBONUS_WARRIOR"),
			_Apply("ATTBONUS_ASSASSIN"),
			_Apply("ATTBONUS_SURA"),
			_Apply("ATTBONUS_SHAMAN"),
			_Apply("ATTBONUS_WOLFMAN"),
			_Apply("RESIST_WARRIOR"),
			_Apply("RESIST_ASSASSIN"),
			_Apply("RESIST_SURA"),
			_Apply("RESIST_SHAMAN"),
			_Apply("RESIST_WOLFMAN"),
			_Apply("RESIST_HUMAN"),
			_Apply("RESIST_SWORD"),
			_Apply("RESIST_TWOHAND"),
			_Apply("RESIST_DAGGER"),
			_Apply("RESIST_BELL"),
			_Apply("RESIST_FAN"),
			_Apply("RESIST_BOW"),
			_Apply("RESIST_CLAW"),
			_Apply("RESIST_MAGIC"),
			_Apply("RESIST_SWORD_REDUCTION"),
			_Apply("RESIST_TWOHAND_REDUCTION"),
			_Apply("RESIST_DAGGER_REDUCTION"),
			_Apply("RESIST_BELL_REDUCTION"),
			_Apply("RESIST_FAN_REDUCTION"),
			_Apply("RESIST_BOW_REDUCTION"),
			_Apply("RESIST_CLAW_REDUCTION"),
			_Apply("RESIST_MAGIC_REDUCTION"),
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_3,
		[
			_Apply("SKILL_DAMAGE_BONUS"),
			_Apply("NORMAL_HIT_DAMAGE_BONUS"),
			_Apply("CRITICAL_PCT"),
			_Apply("PENETRATE_PCT"),
			_Apply("BLOCK_PENETRATION"),
			_Apply("DEFENSE_BREAKTHROUGH"),
			_Apply("POISON_PCT"),
			_Apply("BLEEDING_PCT"),
			_Apply("SLOW_PCT"),
			_Apply("STUN_PCT"),
			_Apply("MANA_BURN_PCT"),
			_Apply("CAST_SPEED"),
			_Apply("ATT_SPEED"),
			_Apply("ATT_GRADE_BONUS"),
			_Apply("MAGIC_ATT_GRADE"),
			_Apply("MAGIC_ATTBONUS_PER"),
			_Apply("MELEE_MAGIC_ATTBONUS_PER"),
		]
	],
	[localeInfo.BONUS_TABLE_TITLE_4,
		[
			_Apply("SKILL_DEFEND_BONUS"),
			_Apply("NORMAL_HIT_DEFEND_BONUS"),
			_Apply("ANTI_CRITICAL_PCT"),
			_Apply("ANTI_PENETRATE_PCT"),
			_Apply("BLOCK"),
			_Apply("REFLECT_MELEE"),
			_Apply("REFLECT_CURSE"),
			_Apply("DODGE"),
			_Apply("POISON_REDUCE"),
			_Apply("BLEEDING_REDUCE"),
			_Apply("IMMUNE_STUN"),
			_Apply("IMMUNE_SLOW"),
			_Apply("IMMUNE_FALL"),
			_Apply("RESIST_FIRE"),
			_Apply("RESIST_ELEC"),
			_Apply("RESIST_WIND"),
			_Apply("RESIST_ICE"),
			_Apply("RESIST_EARTH"),
			_Apply("RESIST_DARK"),
			_Apply("MAGIC_DEF_GRADE"),
			_Apply("DEF_GRADE_BONUS"),
		]
	],
]

# Fill the existing categories and append all remaining registered bonus kinds.
bonus_list = characterbonuses.Catalog(item, ItemToolTip.AFFECT_DICT,
    GET_AFFECT_STRING, bonus_list, app.GetLocalePath().split("/")[-1])

def GetBonusName(bonus):
    return bonus[2]

def GetBonusValue(bonus, now=None):
    # POINT addresses survive historical APPLY numbering differences. An
    # unmapped, localized APPLY uses the authoritative server APPLY alias.
    return characterbonuses.Value(bonus)

stat_list = [
 [localeInfo.BONUS_TABLE_4, player.KILL_ALLPLAYER],
 [localeInfo.BONUS_TABLE_5, player.KILL_DUELWON],
 [localeInfo.BONUS_TABLE_6, player.KILL_DUELLOST],
 [localeInfo.BONUS_TABLE_7, player.KILL_MONSTER],
 [localeInfo.BONUS_TABLE_8, player.KILL_BOSSES ],
 [localeInfo.BONUS_TABLE_9, player.KILL_METINSTONE]
]

def BonusLabel(bonus):
	"""The R1 name of a bonus row: the catalogue label (characterbonuses.Catalog, the tooltip affect string
	without its value), its spaces collapsed, a trailing ':' dropped and its first letter upper case (the
	value-first strings: "%d%% šance odrazit přímý tělesný útok")."""
	return textcase.CapitalFirst(" ".join(GetBonusName(bonus).split()).rstrip(":").strip())

def _UseKitLook():
	"""The Althea UI kit panel (uicharacterdetailskit) unless Settings -> "Starý vzhled" chose the original look;
	an import problem keeps the original panel."""
	try:
		import uicharacterdetailskit
	except Exception:
		import dbg
		import traceback
		dbg.TraceError("character details kit: %s" % traceback.format_exc())
		return False
	return uicharacterdetailskit.UseKitLook()


def _SourceStore():
	"""Rozpad zdrojů ze serveru (bonussources.server), None když modul chybí."""
	try:
		import bonussources
		return bonussources.server
	except Exception:
		return None

class CharacterDetailsUI(ui.ScriptWindow):
	def __del__(self):
		ui.ScriptWindow.__del__(self)
	def Destroy(self):
		self.__DestroyKitPanel()
		self.ClearDictionary()
		self.btnIndex = 0
		self.isPacketLoaded = False
	def Show(self):
		self.__SyncLook()
		ui.ScriptWindow.Show(self)
		self.SetTop()
		if self.btnIndex == 0:
			characterbonuses.totals.Request()
		self.Refresh()
	def Close(self):
		self.Hide()
	def OnPressEscapeKey(self):
		self.Close()
		return True
	def AdjustPosition(self, x, y):
		# Beside the character window: the offset is the uiscript board width, also when the R1 panel is wider.
		self.SetPosition(x + getattr(self, "layoutWidth", self.GetWidth()), y)
	def __ClickRadioButton(self, buttonList, buttonIndex):
		try:
			radioBtn = buttonList[buttonIndex]
		except IndexError:
			return
		for eachButton in buttonList:
			eachButton.SetUp()
		radioBtn.Down()
	def __init__(self):
		ui.ScriptWindow.__init__(self)
		self.kitPanel = None
		self.loadedLook = None
		self.kitFailed = False
		self.Destroy()
		self.__LoadScript()

	def __DestroyKitPanel(self):
		kitPanel = getattr(self, "kitPanel", None)
		self.kitPanel = None
		if kitPanel is not None:
			kitPanel.Destroy()

	def __LoadKitPanel(self):
		"""The kit look drawn into this window over the hidden original board; False (traced) when the original
		look is chosen or the kit panel cannot be built - the original panel is built instead."""
		if self.kitFailed or not _UseKitLook():
			return False
		try:
			import uicharacterdetailskit
			spec = {
				"tabs" : (localeInfo.CHARACTER_DETAILS_BONUS_TAB, localeInfo.CHARACTER_DETAILS_STATS_TAB),
				"sections" : [(title, [(BonusLabel(bonus), bonus) for bonus in rows]) for title, rows in bonus_list],
				"stats" : [(label, kind) for label, kind in stat_list],
				"value" : GetBonusValue,
				"visible" : characterbonuses.Visible,
				"stat" : lambda kind: localeInfo.DottedNumber(player.GetKillLOG(kind)),
				"close" : ui.__mem_func__(self.Close),
				"row_in" : ui.__mem_func__(self.OverInBonus),
				"row_out" : ui.__mem_func__(self.OverOutBonus),
				"sources" : ui.__mem_func__(self.SourcesBreakdown),
				"item_in" : ui.__mem_func__(self.OverInSourceItem),
				"item_out" : ui.__mem_func__(self.OverOutBonus),
			}
			# One rectangle for both tabs: PANEL_W x the uiscript height (the character window height).
			self.SetSize(max(self.layoutWidth, uicharacterdetailskit.PANEL_W), self.GetHeight())
			self.kitPanel = uicharacterdetailskit.BonusPanel(self, spec)
			self.GetChild("MainBoard").Hide()
		except Exception:
			import dbg
			import traceback
			dbg.TraceError("character details kit: %s" % traceback.format_exc())
			self.kitFailed = True
			self.__DestroyKitPanel()
			self.SetSize(self.layoutWidth, self.GetHeight())
			if self.IsChild("MainBoard"):
				self.GetChild("MainBoard").Show()
			return False
		self.loadedLook = "kit"
		self.SetCategory(0)
		return True

	def __SyncLook(self):
		"""Settings -> "Starý vzhled" / "Nový vzhled" switches this panel too: rebuilt on the next opening."""
		if self.loadedLook is None:
			return
		wanted = "kit" if (not self.kitFailed and _UseKitLook()) else "legacy"
		if wanted == self.loadedLook:
			return
		self.__DestroyKitPanel()
		for child in getattr(self, "Children", ()) or ():
			if hasattr(child, "Hide"):
				child.Hide()   # the old board must not linger until it is collected
		self.Destroy()
		self.__LoadScript()
	def __LoadScript(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/CharacterDetailsWindow.py")
			# The board width of the uiscript (once: a later reload may find the window still at the R1 width).
			if not getattr(self, "layoutWidth", 0):
				self.layoutWidth = self.GetWidth()
			self.SetSize(self.layoutWidth, self.GetHeight())

			self.GetChild("bonus_button").SAFE_SetEvent(self.SetCategory,0)
			self.GetChild("stat_button").SAFE_SetEvent(self.SetCategory,1)
			
		except:
			import exception
			exception.Abort("CharacterDetailsUI.__LoadScript")

		if self.__LoadKitPanel():
			return
		self.loadedLook = "legacy"

		#self.ScrollBar = self.GetChild("ScrollBar")
		#self.ScrollBar.SetScrollEvent(ui.__mem_func__(self.OnScroll))

		elementList = self.ElementDictionary
		statWindow = self.GetChild("stat_window")
		for i in range(len(stat_list)):
			statName = ui.TextLine()
			statName.SetParent(statWindow)
			statName.AddFlag("not_pick")
			statName.SetPosition(70,15+(i*40))
			statName.SetFontName("Tahoma:13")
			statName.SetHorizontalAlignCenter()
			statName.SetText(stat_list[i][0])
			statName.Show()
			elementList["%d_stat_name"%i] = statName

			statValue = ui.TextLine()
			statValue.AddFlag("not_pick")
			statValue.SetParent(statWindow)
			statValue.SetPosition(180,15+(i*40))
			statValue.SetFontName("Tahoma:13")
			statValue.SetHorizontalAlignCenter()
			statValue.Show()
			elementList["%d_stat"%i] = statValue

		bonusWindow = self.GetChild("bonus_window")

		searchBoard = SearchSlotBoard()
		searchBoard.SetParent(bonusWindow)
		searchBoard.SetPosition((bonusWindow.GetWidth()//2)-(129//2),11)
		searchBoard.SetSize(129,23)
		searchBoard.Show()
		elementList["searchBoard"] = searchBoard

		itemSearch = ui.EditLine()
		itemSearch.SetParent(searchBoard)
		itemSearch.SetMax(40)
		itemSearch.SetPosition(5,5)
		itemSearch.SetSize(searchBoard.GetWidth(), searchBoard.GetHeight())
		itemSearch.OnIMEUpdate = ui.__mem_func__(self.__OnValueUpdate)
		itemSearch.SetEscapeEvent(ui.__mem_func__(self.Close))
		itemSearch.Show()
		elementList["itemSearch"] = itemSearch

		searchBtn = ui.Button()
		searchBtn.SetParent(searchBoard)
		searchBtn.SetUpVisual(IMG_DIR+"search_btn_0.tga")
		searchBtn.SetOverVisual(IMG_DIR+"search_btn_1.tga")
		searchBtn.SetDownVisual(IMG_DIR+"search_btn_2.tga")
		searchBtn.SetEvent(self.__OnValueUpdate)
		searchBtn.SetPosition(itemSearch.GetWidth()-searchBtn.GetWidth(),2)
		searchBtn.Show()
		elementList["searchBtn"] = searchBtn

		#bonusWindow.OnMouseWheel = ui.__mem_func__(self.OnMouseWheel)

		scrollBar = ScrollBarNew()
		scrollBar.SetParent(bonusWindow)
		scrollBar.SetPosition((bonusWindow.GetWidth()-scrollBar.GetWidth())-3,43)
		scrollBar.SetScrollBarSize((bonusWindow.GetHeight()-46)-5)
		scrollBar.SetScrollEvent(ui.__mem_func__(self.Refresh))
		scrollBar.Show()
		elementList["scrollBar"] = scrollBar

		for i in range(len(bonus_list)):
			bonus_data = bonus_list[i][1]

			category = ui.ExpandedImageBox()
			category.SetParent(bonusWindow)
			category.LoadImage(IMG_DIR+"category_item.tga")
			category.buttonStatus = 0
			category.SetEvent(ui.__mem_func__(self.SetBonusCategory),"mouse_click", i)
			category.Show()
			elementList["%d_category"%i] = category

			categoryText = ui.TextLine()
			categoryText.SetParent(category)
			categoryText.SetHorizontalAlignLeft()
			categoryText.SetPosition(8,3)
			categoryText.SetText("|Ikey/plus|i "+bonus_list[i][0])
			categoryText.Show()
			elementList["%d_categoryText"%i] = categoryText

			for j in range(len(bonus_data)):
				bonusImage = ui.ExpandedImageBox()
				#bonusImage.AddFlag("not_pick")
				bonusImage.SetParent(bonusWindow)
				bonusImage.LoadImage(IMG_DIR+"bonus_item.tga")
				bonusImage.Show()
				elementList["%d_%d_image"%(i,j)] = bonusImage

				bonusText = BonusLabel(bonus_data[j])
				bonusImage.SAFE_SetStringEvent("MOUSE_OVER_IN",self.OverInBonus, bonusText)
				bonusImage.SAFE_SetStringEvent("MOUSE_OVER_OUT",self.OverOutBonus)
				
				#bonusText = bonusText.replace(":","")
				#index = bonusText.find("+")
				#if index == -1:
				#	index = bonusText.find("%")
				#	if index == -1:
				#		index =0
				#if not index  <= 0:
				#	bonusText = bonusText[:index]

				bonusName = ui.TextLine()
				bonusName.AddFlag("not_pick")
				bonusName.SetParent(bonusImage)
				bonusName.SetHorizontalAlignCenter()
				bonusName.SetPosition(72,3)
				bonusName.SetFontName("Tahoma:13")
				bonusName.SetText(bonusText)

				newText = ""
				if bonusName.GetTextSize()[0] > 134:
					for o in range(100):
						if bonusName.GetTextSize()[0] > 134:
							newText = bonusName.GetText()[:len(bonusName.GetText())-2]+"..."
							bonusName.SetText(bonusName.GetText()[:len(bonusName.GetText())-2])
						else:
							break
				
				if newText != "":
					bonusName.SetText(newText)

				bonusName.Show()
				elementList["%d_%d_name"%(i,j)] = bonusName

				bonusValue = ui.TextLine()
				bonusValue.AddFlag("not_pick")
				bonusValue.SetParent(bonusImage)
				bonusValue.SetHorizontalAlignCenter()
				bonusValue.SetPosition(170,3)
				bonusValue.SetFontName("Tahoma:13")
				bonusValue.SetText("0")
				bonusValue.Show()
				elementList["%d_%d_value"%(i,j)] = bonusValue

		self.SetCategory(0)
	
	def SourcesBreakdown(self, bonus, request=True):
		"""Odkud bonus mám: rozpad řádku (bonussources) se serverovou hodnotou řádku; chyba = jen zbytek."""
		import bonussources
		members = characterbonuses.Members(bonus)
		sources = _SourceStore()
		if request and sources is not None:
			sources.RequestRows([characterbonuses.Key(part) for part in members])
		if len(members) > 1:
			combined = bonussources.Breakdown(BonusLabel(bonus), False)
			combined.components = [self.SourcesBreakdown(part, False) for part in members]
			return combined
		if members[0] is not bonus:
			return self.SourcesBreakdown(members[0], False)
		key = characterbonuses.Key(bonus)
		total = bonussources.FromScaled(characterbonuses.totals.GetExact(key))
		# Krok 2: přesný rozpad ze serveru, dokud nepřijde (nebo starý server), platí odhad klienta.
		entries = None
		if sources is not None:
			entries = sources.Get(key)
		try:
			return bonussources.Build(bonus, total, title=BonusLabel(bonus), server_entries=entries)
		except Exception:
			import dbg
			import traceback
			dbg.TraceError("bonus sources: %s" % traceback.format_exc())
			return bonussources.Breakdown(BonusLabel(bonus), bonus[3])

	def OverInSourceItem(self, cell):
		"""Najetí na předmět v rozpadu: tooltip toho předmětu ze slotu výbavy, jako v inventáři. Jiný zdroj
		(bonussources.Entry) ukáže tooltip své ikony z lišty efektů, jinak celý název a poznámku."""
		import uir1
		uir1.HideHint(self)
		if not isinstance(cell, int):
			self.__OverInSource(cell)
			return
		interface = osfInfo.GetInterfaceInstance()
		tooltip = getattr(interface, "tooltipItem", None) if interface else None
		if tooltip is None:
			return
		# Stejný předmět pod myší: tooltip (i otáčející se náhled modelu) nestavět znovu.
		if getattr(self, "sourceTooltipCell", None) == cell:
			return
		self.sourceTooltipCell = cell
		try:
			tooltip.SetInventoryItem(cell)
		except Exception:
			import dbg
			import traceback
			dbg.TraceError("bonus sources: %s" % traceback.format_exc())

	def __OverInSource(self, entry):
		"""Tooltip zdroje: efekt z předmětu (lektvar, rosa) tooltip toho předmětu jako v inventáři, stejnou cestou jako
		Výbava; jinak tooltip ikony z lišty efektů; jinak celý název a poznámka. Volá se i při každé obnově rozpadu,
		když je řádek pod myší: stejný předmět se nestaví znovu, ikona a text dostanou aktuální čas."""
		import bonussources
		slot, vnum = bonussources.AffectItemSource(entry)
		if slot is not None:
			self.__HideSourceHover()
			self.OverInSourceItem(slot)
			return
		self.sourceTooltipCell = None
		interface = osfInfo.GetInterfaceInstance()
		tooltip = getattr(interface, "tooltipItem", None) if interface else None
		if vnum and tooltip is not None:
			if getattr(self, "sourceTooltipVnum", None) == vnum:
				return
			self.__HideSourceHover()
			try:
				tooltip.SetItemToolTip(vnum)
				self.sourceTooltipVnum = vnum
				return
			except Exception:
				import dbg
				import traceback
				dbg.TraceError("bonus sources: %s" % traceback.format_exc())
		self.sourceTooltipVnum = None
		image = bonussources.AffectHoverImage(entry)
		if image is not None:
			try:
				if getattr(self, "sourceHoverImage", None) is image and getattr(self, "sourceHoverHide", None):
					tick = getattr(image, "TickHover", None)
					if tick is not None:
						tick()
					return
				self.__HideSourceHover()
				self.sourceHoverHide = image.ShowHover()
				self.sourceHoverImage = image
				return
			except Exception:
				import dbg
				import traceback
				dbg.TraceError("bonus sources: %s" % traceback.format_exc())
		self.__HideSourceHover()
		if tooltip is None:
			return
		tooltip.ClearToolTip()
		for text in (entry.name, entry.detail):
			if text:
				tooltip.AppendTextLine(text)
		tooltip.ShowToolTip()

	def __HideSourceHover(self):
		hide = getattr(self, "sourceHoverHide", None)
		self.sourceHoverHide = None
		self.sourceHoverImage = None
		if callable(hide):
			try:
				hide()
			except Exception:
				pass

	def OverOutBonus(self):
		self.__HideSourceHover()
		self.sourceTooltipCell = None
		self.sourceTooltipVnum = None
		if getattr(self, "kitPanel", None) is not None:
			import uir1
			uir1.HideHint(self)
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.HideToolTip()
	def OverInBonus(self, bonusName):
		if getattr(self, "kitPanel", None) is not None:
			# The R1 panel: the bonus name as the one R1 hint above the mouse cursor (the item tooltip board
			# of the original panel was a bigger box with another padding).
			import uir1
			if uir1.TextTooltipShow(self, bonusName):
				return
		interface = osfInfo.GetInterfaceInstance()
		if interface:
			if interface.tooltipItem:
				interface.tooltipItem.ClearToolTip()
				interface.tooltipItem.AppendTextLine(bonusName)
				interface.tooltipItem.ShowToolTip()

	def OnMouseWheel(self, nLen):
		if getattr(self, "kitPanel", None) is not None:
			return self.kitPanel.OnMouseWheel(nLen)
		if self.btnIndex == 0:
			if "scrollBar" in self.ElementDictionary:
				scrollBar = self.ElementDictionary["scrollBar"]
				if scrollBar.IsShow():
					if nLen > 0:
						scrollBar.OnUp()
					else:
						scrollBar.OnDown()
					return True
		return False

	def __OnValueUpdate(self):
		elementList = self.ElementDictionary
		itemSearch = elementList["itemSearch"]
		ui.EditLine.OnIMEUpdate(itemSearch)
		bonusWindow = self.GetChild("bonus_window")
		searchText = itemSearch.GetText()
		board = elementList["searchBoard"]
		totalWidth = 129
		if len(searchText) > 0:
			self.ElementDictionary["scrollBar"].SetPos(0, True)
			totalWidth-=25
			windowHeight = bonusWindow.GetWidth()-15
			textSize = itemSearch.GetTextSize()[0]
			if textSize >= totalWidth:
				if textSize >= windowHeight:
					totalWidth = windowHeight
				else:
					totalWidth = textSize
			totalWidth+=25
			if totalWidth >= windowHeight:
				totalWidth = windowHeight
		board.SetSize(totalWidth,23)
		itemSearch.SetSize(totalWidth,23)
		board.SetPosition((bonusWindow.GetWidth()//2)-(board.GetWidth()//2),11)
		searchBtn = elementList["searchBtn"]
		searchBtn.SetPosition(itemSearch.GetWidth()-searchBtn.GetWidth(),2)
		self.Refresh()

	def SetBonusCategory(self, emptyArg, categoryIndex):
		category = self.ElementDictionary["%d_category"%categoryIndex]
		category.buttonStatus = not category.buttonStatus
		if category.buttonStatus == 0:
			self.ElementDictionary["%d_categoryText"%categoryIndex].SetText("|Ikey/plus|i "+bonus_list[categoryIndex][0])
		else:
			self.ElementDictionary["%d_categoryText"%categoryIndex].SetText("|Ikey/negative|i "+bonus_list[categoryIndex][0])
		self.Refresh()

	def Refresh(self):
		if getattr(self, "kitPanel", None) is not None:
			self.kitPanel.Refresh()
			return
		elementList = self.ElementDictionary
		now = app.GetTime()
		(X_POS,Y_POS) = (3,43)
		CATEGORY_Y_RANGE = 25
		CATEGORY_Y_FIRST_BONUS_RANGE = 29
		BONUS_X = 13

		if self.btnIndex == 0:
			bonusWindow = self.GetChild("bonus_window")
			scrollBar = self.GetChild("scrollBar")
			(basePos,windowHeight) = (0,bonusWindow.GetHeight()-46)

			searchText = textcase.SearchKey(elementList["itemSearch"].GetText())  # no case, no Czech accents

			# Conditional rows stay allocated but vanish when their active value expires.
			for i, (_, rows) in enumerate(bonus_list):
				for j, row in enumerate(rows):
					if not characterbonuses.Visible(row):
						elementList["%d_%d_image" % (i, j)].Hide()
			maxHeight = 0
			if len(searchText) > 0:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					for j in range(len(bonus_data)):
						if not characterbonuses.Visible(bonus_data[j]):
							continue
						text = textcase.SearchKey(GetBonusName(bonus_data[j]))
						if text.find(searchText) != -1:
						#if len(text) >= len(searchText):
						#	if text[:len(searchText)] == searchText:
							maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE
			else:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						categoryBtn = elementList["%d_category"%i]
						if categoryBtn.buttonStatus == 0:
							maxHeight += CATEGORY_Y_RANGE
						else:
							maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE
							for j in range(len(bonus_data)):
								if not characterbonuses.Visible(bonus_data[j]):
									continue
								maxHeight += CATEGORY_Y_FIRST_BONUS_RANGE

			if maxHeight > windowHeight:
				scrollLen = maxHeight-windowHeight
				basePos = int(scrollBar.GetPos()*scrollLen)
				stepSize = 1.0 / (scrollLen/100.0)
				scrollBar.SetScrollStep(stepSize)
				scrollBar.SetMiddleBarSize(float(windowHeight-5)/float(maxHeight))
				scrollBar.Show()
			else:
				scrollBar.Hide()

			textLines = []
			images = []
			_wy = bonusWindow.GetGlobalPosition()[1]+43

			if len(searchText) > 0:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						elementList["%d_category"%i].Hide()
						for j in range(len(bonus_data)):
							if not characterbonuses.Visible(bonus_data[j]):
								continue
							text = textcase.SearchKey(GetBonusName(bonus_data[j]))
							if text.find(searchText) != -1:
								elementList["%d_%d_image"%(i,j)].Show()
								elementList["%d_%d_image"%(i,j)].SetPosition(BONUS_X, Y_POS - basePos, True)
								elementList["%d_%d_value"%(i,j)].SetText(GetBonusValue(bonus_data[j], now))
								Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE
								images.append(elementList["%d_%d_image"%(i,j)])
								textLines.append(elementList["%d_%d_name"%(i,j)])
								textLines.append(elementList["%d_%d_value"%(i,j)])
							else:
								elementList["%d_%d_image"%(i,j)].Hide()
			else:
				for i in range(len(bonus_list)):
					bonus_data = bonus_list[i][1]
					if ("%d_category"%i) in elementList:
						categoryBtn = elementList["%d_category"%i]
						categoryBtn.SetPosition(X_POS, Y_POS - basePos, True)
						categoryBtn.Show()

						images.append(categoryBtn)
						textLines.append(elementList["%d_categoryText"%i])

						if categoryBtn.buttonStatus == 0:
							Y_POS += CATEGORY_Y_RANGE
							for j in range(len(bonus_data)):
								if not characterbonuses.Visible(bonus_data[j]):
									continue
								elementList["%d_%d_image"%(i,j)].Hide()
						else:
							Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE
							for j in range(len(bonus_data)):
								if not characterbonuses.Visible(bonus_data[j]):
									continue
								elementList["%d_%d_image"%(i,j)].Show()
								elementList["%d_%d_image"%(i,j)].SetPosition(BONUS_X, Y_POS - basePos, True)
								elementList["%d_%d_value"%(i,j)].SetText(GetBonusValue(bonus_data[j], now))
								Y_POS += CATEGORY_Y_FIRST_BONUS_RANGE

								images.append(elementList["%d_%d_image"%(i,j)])
								textLines.append(elementList["%d_%d_name"%(i,j)])
								textLines.append(elementList["%d_%d_value"%(i,j)])

			for childItem in textLines:
				(_x,_y) = childItem.GetGlobalPosition()
				if _y < _wy:
					if childItem.IsShow():
						childItem.Hide()
				elif _y > (_wy+windowHeight-20):
					if childItem.IsShow():
						childItem.Hide()
				else:
					if not childItem.IsShow():
						childItem.Show()

			for childItem in images:
				childHeight = childItem.GetHeight()
				(_x,_y) = childItem.GetGlobalPosition()
				if _y < _wy:
					childItem.SetRenderingRect(0,ui.calculateRect(childHeight-abs(_y-_wy),childHeight),0,0)
					childItem.Hide()
				elif _y+childHeight > (_wy+windowHeight-4):
					calculate = (_wy+windowHeight-4) - (_y+childHeight)
					if calculate == 0:
						return
					f = ui.calculateRect(childHeight-abs(calculate),childHeight)
					childItem.SetRenderingRect(0,0,0,f)
					childItem.Hide()
				else:
					childItem.SetRenderingRect(0,0,0,0)
					childItem.Show()

		elif self.btnIndex == 1:
			for i in range(len(stat_list)):
				if ("%d_stat"%i) in elementList:
					elementList["%d_stat"%i].SetText(localeInfo.DottedNumber(player.GetKillLOG(stat_list[i][1])))

	def OnUpdate(self):
		if not self.IsShow():
			return
		if self.btnIndex == 1:
			# Kill counters are client values; redraw the open tab whenever one changes.
			kills = tuple(player.GetKillLOG(kind) for _, kind in stat_list)
			if kills != getattr(self, "statVersion", None):
				self.statVersion = kills
				self.Refresh()
			return
		if self.btnIndex != 0:
			return
		characterbonuses.totals.Request()
		sources = _SourceStore()
		kitPanel = getattr(self, "kitPanel", None)
		if sources is not None:
			if kitPanel is not None and getattr(kitPanel, "cascade_row", None) is not None:
				sources.Poll()
			else:
				sources.Stop()
		version = characterbonuses.totals.Version()
		if sources is not None:
			version = (version, sources.Version())
		if version == getattr(self, "bonusVersion", None):
			return
		self.bonusVersion = version
		# One full refresh for every snapshot change (both looks): values, conditional row
		# visibility and the scroll range follow the server state without a user action.
		self.Refresh()

	def SetCategory(self, categoryIndex):
		self.btnIndex = categoryIndex
		if getattr(self, "kitPanel", None) is not None:
			self.kitPanel.SetTab(categoryIndex)
			return
		self.__ClickRadioButton([self.GetChild("bonus_button"),self.GetChild("stat_button")],categoryIndex)
		self.ElementDictionary["itemSearch"].KillFocus()
		if self.btnIndex == 0:
			self.GetChild("bonus_window").Show()
			self.GetChild("stat_window").Hide()
		elif self.btnIndex == 1:
			self.GetChild("bonus_window").Hide()
			self.GetChild("stat_window").Show()

		self.Refresh()

	def OnScroll(self):
		pass


class ScrollBarNew(ui.Window):
	SCROLLBAR_WIDTH = 7
	SCROLL_BTN_XDIST = 0
	SCROLL_BTN_YDIST = 0
	class MiddleBar(ui.DragButton):
		def __init__(self):
			ui.DragButton.__init__(self)
			self.AddFlag("movable")
			self.SetWindowName("scrollbar_middlebar")
		def MakeImage(self):
			top = ui.ExpandedImageBox()
			top.SetParent(self)
			top.LoadImage(IMG_DIR+"scrollbar/scrollbar_top.tga")
			top.AddFlag("not_pick")
			top.Show()
			topScale = ui.ExpandedImageBox()
			topScale.SetParent(self)
			topScale.SetPosition(0, top.GetHeight())
			topScale.LoadImage(IMG_DIR+"scrollbar/scrollbar_scale.tga")
			topScale.AddFlag("not_pick")
			topScale.Show()
			bottom = ui.ExpandedImageBox()
			bottom.SetParent(self)
			bottom.LoadImage(IMG_DIR+"scrollbar/scrollbar_bottom.tga")
			bottom.AddFlag("not_pick")
			bottom.Show()
			bottomScale = ui.ExpandedImageBox()
			bottomScale.SetParent(self)
			bottomScale.LoadImage(IMG_DIR+"scrollbar/scrollbar_scale.tga")
			bottomScale.AddFlag("not_pick")
			bottomScale.Show()
			middle = ui.ExpandedImageBox()
			middle.SetParent(self)
			middle.LoadImage(IMG_DIR+"scrollbar/scrollbar_mid.tga")
			middle.AddFlag("not_pick")
			middle.Show()
			self.top = top
			self.topScale = topScale
			self.bottom = bottom
			self.bottomScale = bottomScale
			self.middle = middle
		def SetSize(self, height):
			minHeight = self.top.GetHeight() + self.bottom.GetHeight() + self.middle.GetHeight()
			height = max(minHeight, height)
			ui.DragButton.SetSize(self, 10, height)
			scale = (height - minHeight) // 2
			extraScale = 0
			if (height - minHeight) % 2 == 1:
				extraScale = 1
			self.topScale.SetRenderingRect(0, 0, 0, scale - 1)
			self.middle.SetPosition(0, self.top.GetHeight() + scale)
			self.bottomScale.SetPosition(0, self.middle.GetBottom())
			self.bottomScale.SetRenderingRect(0, 0, 0, scale - 1 + extraScale)
			self.bottom.SetPosition(0, height - self.bottom.GetHeight())
	def __init__(self):
		ui.Window.__init__(self)
		self.pageSize = 1
		self.curPos = 0.0
		self.eventScroll = None
		self.eventArgs = None
		self.lockFlag = False
		self.CreateScrollBar()
		self.SetScrollBarSize(0)
		self.scrollStep = 0.4
		self.SetWindowName("NONAME_ScrollBar")
	def __del__(self):
		ui.Window.__del__(self)
	def CreateScrollBar(self):
		topImage = ui.ExpandedImageBox()
		topImage.SetParent(self)
		topImage.AddFlag("not_pick")
		topImage.LoadImage(IMG_DIR+"scrollbar/scroll_top.tga")
		topImage.Show()
		bottomImage = ui.ExpandedImageBox()
		bottomImage.SetParent(self)
		bottomImage.AddFlag("not_pick")
		bottomImage.LoadImage(IMG_DIR+"scrollbar/scroll_bottom.tga")
		bottomImage.Show()
		middleImage = ui.ExpandedImageBox()
		middleImage.SetParent(self)
		middleImage.AddFlag("not_pick")
		middleImage.SetPosition(0, topImage.GetHeight())
		middleImage.LoadImage(IMG_DIR+"scrollbar/scroll_mid.tga")
		middleImage.Show()
		self.topImage = topImage
		self.bottomImage = bottomImage
		self.middleImage = middleImage
		middleBar = self.MiddleBar()
		middleBar.SetParent(self)
		middleBar.SetMoveEvent(ui.__mem_func__(self.OnMove))
		middleBar.Show()
		middleBar.MakeImage()
		middleBar.SetSize(12)
		self.middleBar = middleBar
	def Destroy(self):
		self.eventScroll = None
		self.eventArgs = None
	def SetScrollEvent(self, event, *args):
		self.eventScroll = event
		self.eventArgs = args
	def SetMiddleBarSize(self, pageScale):
		self.middleBar.SetSize(int(pageScale * float(self.GetHeight() - (self.SCROLL_BTN_YDIST*2))))
		realHeight = self.GetHeight() - (self.SCROLL_BTN_YDIST*2) - self.middleBar.GetHeight()
		self.pageSize = realHeight

	def SetScrollBarSize(self, height):
		self.SetSize(self.SCROLLBAR_WIDTH, height)
		self.pageSize = height - self.SCROLL_BTN_YDIST*2 - self.middleBar.GetHeight()
		middleImageScale = float((height - self.SCROLL_BTN_YDIST*2) - self.middleImage.GetHeight()) / float(self.middleImage.GetHeight())
		self.middleImage.SetRenderingRect(0, 0, 0, middleImageScale)
		self.bottomImage.SetPosition(0, height - self.bottomImage.GetHeight())
		self.middleBar.SetRestrictMovementArea(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST, \
			self.middleBar.GetWidth(), height - self.SCROLL_BTN_YDIST * 2)
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, self.SCROLL_BTN_YDIST)
	def SetScrollStep(self, step):
		self.scrollStep = step
	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep)
	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep)
	def GetScrollStep(self):
		return self.scrollStep
	def GetPos(self):
		return self.curPos
	def OnUp(self):
		self.SetPos(self.curPos-self.scrollStep)
	def OnDown(self):
		self.SetPos(self.curPos+self.scrollStep)
	def SetPos(self, pos, moveEvent = True):
		pos = max(0.0, pos)
		pos = min(1.0, pos)
		newPos = float(self.pageSize) * pos
		self.middleBar.SetPosition(self.SCROLL_BTN_XDIST, int(newPos) + self.SCROLL_BTN_YDIST)
		if moveEvent == True:
			self.OnMove()
	def OnMove(self):
		if self.lockFlag:
			return
		if 0 == self.pageSize:
			return
		(xLocal, yLocal) = self.middleBar.GetLocalPosition()
		self.curPos = float(yLocal - self.SCROLL_BTN_YDIST) / float(self.pageSize)
		if self.eventScroll:
			self.eventScroll(*self.eventArgs)
	def OnMouseLeftButtonDown(self):
		(xMouseLocalPosition, yMouseLocalPosition) = self.GetMouseLocalPosition()
		newPos = float(yMouseLocalPosition) / float(self.GetHeight())
		self.SetPos(newPos)
	def LockScroll(self):
		self.lockFlag = True
	def UnlockScroll(self):
		self.lockFlag = False

class SearchSlotBoard(ui.Window):
	CORNER_WIDTH = 7
	CORNER_HEIGHT = 7
	LINE_WIDTH = 7
	LINE_HEIGHT = 7
	LT = 0
	LB = 1
	RT = 2
	RB = 3
	L = 0
	R = 1
	T = 2
	B = 3
	def __init__(self):
		ui.Window.__init__(self)
		self.MakeBoard()
		self.MakeBase()
	def MakeBoard(self):
		cornerPath = IMG_DIR+"board/corner_"
		linePath = IMG_DIR+"board/"
		CornerFileNames = [ cornerPath+dir+".tga" for dir in ("left_top", "left_bottom", "right_top", "right_bottom") ]
		LineFileNames = [ linePath+dir+".tga" for dir in ("left", "right", "top", "bottom") ]
		self.Corners = []
		for fileName in CornerFileNames:
			Corner = ui.ExpandedImageBox()
			Corner.AddFlag("not_pick")
			Corner.LoadImage(fileName)
			Corner.SetParent(self)
			Corner.SetPosition(0, 0)
			Corner.Show()
			self.Corners.append(Corner)
		self.Lines = []
		for fileName in LineFileNames:
			Line = ui.ExpandedImageBox()
			Line.AddFlag("not_pick")
			Line.LoadImage(fileName)
			Line.SetParent(self)
			Line.SetPosition(0, 0)
			Line.Show()
			self.Lines.append(Line)
		self.Lines[self.L].SetPosition(0, self.CORNER_HEIGHT)
		self.Lines[self.T].SetPosition(self.CORNER_WIDTH, 0)
	def MakeBase(self):
		self.Base = ui.ExpandedImageBox()
		self.Base.AddFlag("not_pick")
		self.Base.LoadImage(IMG_DIR+"board/base.tga")
		self.Base.SetParent(self)
		self.Base.SetPosition(self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Base.Show()
	def __del__(self):
		ui.Window.__del__(self)
	def Destroy(self):
		self.Base=0
		self.Corners=0
		self.Lines=0
		self.CORNER_WIDTH = 0
		self.CORNER_HEIGHT = 0
		self.LINE_WIDTH = 0
		self.LINE_HEIGHT = 0
		self.LT = 0
		self.LB = 0
		self.RT = 0
		self.RB = 0
		self.L = 0
		self.R = 0
		self.T = 0
		self.B = 0
	def SetSize(self, width, height):
		width = max(self.CORNER_WIDTH*2, width)
		height = max(self.CORNER_HEIGHT*2, height)
		ui.Window.SetSize(self, width, height)
		self.Corners[self.LB].SetPosition(0, height - self.CORNER_HEIGHT)
		self.Corners[self.RT].SetPosition(width - self.CORNER_WIDTH, 0)
		self.Corners[self.RB].SetPosition(width - self.CORNER_WIDTH, height - self.CORNER_HEIGHT)
		self.Lines[self.R].SetPosition(width - self.CORNER_WIDTH, self.CORNER_HEIGHT)
		self.Lines[self.B].SetPosition(self.CORNER_HEIGHT, height - self.CORNER_HEIGHT)
		verticalShowingPercentage = float((height - self.CORNER_HEIGHT*2) - self.LINE_HEIGHT) / self.LINE_HEIGHT
		horizontalShowingPercentage = float((width - self.CORNER_WIDTH*2) - self.LINE_WIDTH) / self.LINE_WIDTH
		self.Lines[self.L].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.R].SetRenderingRect(0, 0, 0, verticalShowingPercentage)
		self.Lines[self.T].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		self.Lines[self.B].SetRenderingRect(0, 0, horizontalShowingPercentage, 0)
		if self.Base:
			self.Base.SetRenderingRect(0, 0, horizontalShowingPercentage, verticalShowingPercentage)
