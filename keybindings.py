import os

try:
	import builtins
except ImportError:
	import __builtin__ as builtins

import keybindingcore

try:
	import app
except ImportError:
	app = None

try:
	import ui
except ImportError:
	ui = None


def _load_uisystem():
	try:
		return __import__("uiSystem")
	except ImportError as error:
		if getattr(error, "name", "uiSystem") != "uiSystem":
			raise

	try:
		return __import__("uisystem")
	except ImportError as error:
		if getattr(error, "name", "uisystem") != "uisystem":
			raise
		return None


CONFIG_VERSION = 2
CONFIG_RELATIVE_PATH = os.path.join("UserData", "keybindings.cfg")
_REAL_OPEN = getattr(builtins, "old_open", builtins.open)

CATEGORY_CHANNELS = "KEYBIND_CATEGORY_CHANNELS"
CATEGORY_INVENTORIES = "KEYBIND_CATEGORY_INVENTORIES"
CATEGORY_CHARACTER_COMMUNITY = "KEYBIND_CATEGORY_CHARACTER_COMMUNITY"
CATEGORY_MAPS_INFORMATION = "KEYBIND_CATEGORY_MAPS_INFORMATION"
CATEGORY_SYSTEMS = "KEYBIND_CATEGORY_SYSTEMS"


class ActionDefinition(object):
	def __init__(
		self,
		action_id,
		locale_key,
		category_key,
		order,
		default,
		callback,
	):
		self.action_id = action_id
		self.locale_key = locale_key
		self.category_key = category_key
		self.order = order
		self.default = keybindingcore.Shortcut.parse(default)
		self.callback = callback


# Switched off by the owner on 2026-10-05: no panel button, "More" entry or
# assignable shortcut. The windows stay in the client and the server refuses
# their requests while the matching event flag is unset (althea/server-src
# common/feature_gate_policy.h); bringing one back needs both sides.
RETIRED_ACTION_IDS = frozenset((
	"system.exchange_log",
	"system.destroyed_items",
	"system.reward",
	"system.battle_pass",
))


def _feature_enabled(name):
	return bool(app and getattr(app, name, False))


def _append_action(
	actions,
	interface,
	action_id,
	locale_key,
	category_key,
	order,
	default,
	callback_name,
	feature_name=None,
):
	if action_id in RETIRED_ACTION_IDS:
		return
	if feature_name and not _feature_enabled(feature_name):
		return
	callback = getattr(interface, callback_name, None)
	if not callable(callback):
		return
	actions.append(
		ActionDefinition(
			action_id,
			locale_key,
			category_key,
			order,
			default,
			callback,
		)
	)


def build_actions(interface, channel_count, request_channel_change=None,
	request_adjacent_channel_change=None):
	actions = []
	if callable(request_adjacent_channel_change) and int(channel_count) > 1:
		for action_id, locale_key, order, step in (
			("channel.next", "KEYBIND_ACTION_CHANNEL_NEXT", -2, 1),
			("channel.previous", "KEYBIND_ACTION_CHANNEL_PREVIOUS", -1, -1),
		):
			actions.append(ActionDefinition(
				action_id, locale_key, CATEGORY_CHANNELS, order, "",
				lambda direction=step: request_adjacent_channel_change(direction),
			))
	if callable(request_channel_change):
		for channel_index in range(1, max(0, int(channel_count)) + 1):
			actions.append(
				ActionDefinition(
					"channel.%d" % channel_index,
					"KEYBIND_ACTION_CHANNEL_%d" % channel_index,
					CATEGORY_CHANNELS,
					channel_index,
					"",
					lambda index=channel_index: request_channel_change(index),
				)
			)

	_append_action(actions, interface, "inventory.normal", "KEYBIND_ACTION_INVENTORY_NORMAL", CATEGORY_INVENTORIES, 10, "I", "ToggleInventoryWindow")
	_append_action(actions, interface, "inventory.special", "KEYBIND_ACTION_INVENTORY_SPECIAL", CATEGORY_INVENTORIES, 20, "U", "ToggleSpecialInventoryWindow", "ENABLE_SPECIAL_INVENTORY_SYSTEM")
	_append_action(actions, interface, "inventory.dragon_soul", "KEYBIND_ACTION_INVENTORY_DRAGON_SOUL", CATEGORY_INVENTORIES, 30, "O", "ToggleDragonSoulWindowWithNoInfo", "ENABLE_DRAGON_SOUL_SYSTEM")

	character_actions = (
		("character.status", "KEYBIND_ACTION_CHARACTER_STATUS", 10, "C", "STATUS"),
		("character.skills", "KEYBIND_ACTION_CHARACTER_SKILLS", 20, "V", "SKILL"),
		("character.quests", "KEYBIND_ACTION_CHARACTER_QUESTS", 30, "N", "QUEST"),
		("character.emotes", "KEYBIND_ACTION_CHARACTER_EMOTES", 40, "B", "EMOTICON"),
	)
	toggle_character = getattr(interface, "ToggleCharacterWindow", None)
	if callable(toggle_character):
		for action_id, locale_key, order, default, state in character_actions:
			actions.append(
				ActionDefinition(
					action_id,
					locale_key,
					CATEGORY_CHARACTER_COMMUNITY,
					order,
					default,
					lambda page=state: toggle_character(page),
				)
			)

	_append_action(actions, interface, "community.messenger", "KEYBIND_ACTION_COMMUNITY_MESSENGER", CATEGORY_CHARACTER_COMMUNITY, 50, "ALT+M", "ToggleMessenger")
	_append_action(actions, interface, "community.guild", "KEYBIND_ACTION_COMMUNITY_GUILD", CATEGORY_CHARACTER_COMMUNITY, 60, "ALT+G", "ToggleGuildWindow")

	_append_action(actions, interface, "information.atlas", "KEYBIND_ACTION_INFORMATION_ATLAS", CATEGORY_MAPS_INFORMATION, 10, "M", "ToggleAtlasWindow")
	_append_action(actions, interface, "information.minimap", "KEYBIND_ACTION_INFORMATION_MINIMAP", CATEGORY_MAPS_INFORMATION, 20, "SHIFT+M", "ToggleMiniMapVisibility")
	_append_action(actions, interface, "information.wiki", "KEYBIND_ACTION_INFORMATION_WIKI", CATEGORY_MAPS_INFORMATION, 30, "H", "OpenWikiWindow", "ENABLE_WIKI")
	_append_action(actions, interface, "information.skill_tree", "KEYBIND_ACTION_INFORMATION_SKILL_TREE", CATEGORY_MAPS_INFORMATION, 40, "F5", "ToggleSkillTreeWindow")
	_append_action(actions, interface, "information.event_calendar", "KEYBIND_ACTION_INFORMATION_EVENT_CALENDAR", CATEGORY_MAPS_INFORMATION, 50, "", "OpenEventCalendar", "ENABLE_EVENT_MANAGER")
	_append_action(actions, interface, "information.ranking", "KEYBIND_ACTION_INFORMATION_RANKING", CATEGORY_MAPS_INFORMATION, 60, "", "ShowRankGlobal", "ENABLE_PLAYER_RANKING")
	_append_action(actions, interface, "information.dungeon", "KEYBIND_ACTION_INFORMATION_DUNGEON", CATEGORY_MAPS_INFORMATION, 70, "F7", "ToggleDungeonInfo", "ENABLE_DUNGEON_INFO")
	_append_action(actions, interface, "information.countdowns", "KEYBIND_ACTION_INFORMATION_COUNTDOWNS", CATEGORY_MAPS_INFORMATION, 75, "", "ToggleCountdownHUD")
	# Hides / restores every letter on the left (quest letters, Trvalé / Denní úkoly).
	_append_action(actions, interface, "information.quest_letters", "KEYBIND_ACTION_INFORMATION_QUEST_LETTERS", CATEGORY_MAPS_INFORMATION, 77, "CTRL+Q", "ToggleQuestLetters")

	_append_action(actions, interface, "system.teleport", "KEYBIND_ACTION_SYSTEM_TELEPORT", CATEGORY_SYSTEMS, 10, "TAB", "ToggleTeleportAtlas", "ENABLE_TELEPORT_WINDOW")
	_append_action(actions, interface, "system.custom_ports", "KEYBIND_ACTION_SYSTEM_CUSTOM_PORTS", CATEGORY_SYSTEMS, 15, "CTRL+X", "ToggleCustomPortsWindow", "ENABLE_CUSTOM_PORTS")
	_append_action(actions, interface, "system.drop_tracker", "KEYBIND_ACTION_SYSTEM_DROP_TRACKER", CATEGORY_SYSTEMS, 17, "F9", "ToggleDropTrackerWindow", "ENABLE_DROP_TRACKER")
	_append_action(actions, interface, "system.quick_buffs", "KEYBIND_ACTION_QUICK_BUFFS", CATEGORY_SYSTEMS, 18, "", "ActivateQuickBuffs")
	_append_action(actions, interface, "system.mount", "KEYBIND_ACTION_SYSTEM_MOUNT", CATEGORY_SYSTEMS, 19, "K", "ToggleMountSystemWindow")
	_append_action(actions, interface, "system.pet", "KEYBIND_ACTION_SYSTEM_PET", CATEGORY_SYSTEMS, 20, "P", "TogglePetInformationWindow", "ENABLE_GROWTH_PET_SYSTEM")
	_append_action(actions, interface, "system.switchbot", "KEYBIND_ACTION_SYSTEM_SWITCHBOT", CATEGORY_SYSTEMS, 30, "F6", "ToggleSwitchbotWindow", "ENABLE_SWITCHBOT_SYSTEM")
	_append_action(actions, interface, "system.item_shop", "KEYBIND_ACTION_SYSTEM_ITEM_SHOP", CATEGORY_SYSTEMS, 40, "", "OpenItemShopWindow", "ENABLE_ITEMSHOP")
	_append_action(actions, interface, "system.shop_search", "KEYBIND_ACTION_SYSTEM_SHOP_SEARCH", CATEGORY_SYSTEMS, 50, "J", "OpenVirtualMarketWindow", "ENABLE_VIRTUAL_MARKET")
	_append_action(actions, interface, "system.exchange_log", "KEYBIND_ACTION_SYSTEM_EXCHANGE_LOG", CATEGORY_SYSTEMS, 60, "", "OpenExchangeLog", "ENABLE_EXCHANGE_LOG")
	_append_action(actions, interface, "system.destroyed_items", "KEYBIND_ACTION_SYSTEM_DESTROYED_ITEMS", CATEGORY_SYSTEMS, 70, "", "OpenItemSaveWindow", "ENABLE_DESTROY_ITEM_RESTORE")
	_append_action(actions, interface, "system.reward", "KEYBIND_ACTION_SYSTEM_REWARD", CATEGORY_SYSTEMS, 80, "", "OpenRewardWindow", "ENABLE_REWARD_SYSTEM")
	_append_action(actions, interface, "system.support", "KEYBIND_ACTION_SYSTEM_SUPPORT", CATEGORY_SYSTEMS, 90, "", "OpenSupportGui", "ENABLE_BUFF_SYSTEM")
	_append_action(actions, interface, "system.battle_pass", "KEYBIND_ACTION_SYSTEM_BATTLE_PASS", CATEGORY_SYSTEMS, 100, "", "ShowBattlePass", "ENABLE_BATTLE_PASS")
	_append_action(actions, interface, "system.auto_hunt", "KEYBIND_ACTION_SYSTEM_AUTO_HUNT", CATEGORY_SYSTEMS, 110, "", "ToggleAutoHuntingWindow", "ENABLE_AUTOMATIC_HUNTING_SYSTEM")
	_append_action(actions, interface, "system.chat_log", "KEYBIND_ACTION_SYSTEM_CHAT_LOG", CATEGORY_SYSTEMS, 120, "L", "ToggleChatLogWindow")
	_append_action(actions, interface, "system.options", "KEYBIND_ACTION_SYSTEM_OPTIONS", CATEGORY_SYSTEMS, 130, "", "ToggleSystemDialog")
	_append_action(actions, interface, "system.help", "KEYBIND_ACTION_SYSTEM_HELP", CATEGORY_SYSTEMS, 140, "", "ToggleHelpWindow")
	_append_action(actions, interface, "system.craft_book", "KEYBIND_ACTION_SYSTEM_CRAFT_BOOK", CATEGORY_SYSTEMS, 145, "", "ToggleCraftBookWindow")
	# The hit of the mining skill check (uiminingcheck), unbound by default: SPACE stays the attack key
	# (fixed.movement), but while a ring is up Space hits it anyway (game.OnKeyDown -> MinigameSpaceHit).

	_append_action(actions, interface, "system.mining_check", "KEYBIND_ACTION_SYSTEM_MINING_CHECK", CATEGORY_SYSTEMS, 147, "", "MiningCheckHit")

	return actions


# Actions Space already fires while their minigame runs: binding Space to them gets its own message.
SPACE_IN_MINIGAME_ACTIONS = frozenset(("system.mining_check",))


def build_reserved_shortcuts():
	shortcut_owners = {}

	def reserve(owner, serialized_values):
		for serialized in serialized_values:
			shortcut_owners[keybindingcore.Shortcut.parse(serialized)] = owner

	reserve("fixed.movement", ("W", "A", "S", "D", "UP", "DOWN", "LEFT", "RIGHT", "SPACE"))
	reserve("fixed.camera", ("Q", "E", "R", "F", "T", "G", "PGUP", "PGDN", "NUMPAD2", "NUMPAD4", "NUMPAD6", "NUMPAD8", "NUMPAD9"))
	reserve("fixed.pickup", ("Z", "GRAVE"))
	reserve("fixed.quickslot", tuple(str(value) for value in range(1, 10)) + tuple("F%d" % value for value in range(1, 5)) + ("F12",))
	reserve("fixed.quickpage", tuple("CTRL+%d" % value for value in range(1, 10)))
	reserve("fixed.system", ("CTRL+B", "CTRL+E", "CTRL+F", "CTRL+G", "CTRL+H", "CTRL+O", "ADD", "SUBTRACT", "COMMA", "SYSRQ"))
	reserve("fixed.dialog", ("ESC", "ENTER", "ALT+F4"))
	return shortcut_owners


class BindingStore(object):
	def __init__(self, path=CONFIG_RELATIVE_PATH):
		self.path = path

	def load(self, defaults, reserved):
		try:
			with _REAL_OPEN(self.path, "rb") as handle:
				lines = handle.read().decode("utf-8").splitlines()
			if not lines or lines[0] != "VERSION\t%d" % CONFIG_VERSION:
				raise ValueError("unsupported keybinding version")

			parsed = {}
			for line in lines[1:]:
				parts = line.split("\t")
				if len(parts) != 2:
					raise ValueError("malformed keybinding row")
				action_id, serialized = parts
				if not action_id or action_id in parsed:
					raise ValueError("duplicate or empty action")
				parsed[action_id] = keybindingcore.Shortcut.parse(serialized)

			candidate = keybindingcore.BindingState(defaults, reserved)
			merged = dict(defaults)
			explicit = {
				action_id: shortcut
				for action_id, shortcut in parsed.items()
				if action_id in merged
			}
			explicit_shortcuts = {
				shortcut for shortcut in explicit.values() if shortcut is not None
			}
			for action_id, shortcut in merged.items():
				if action_id not in explicit and shortcut in explicit_shortcuts:
					merged[action_id] = None
			merged.update(explicit)
			candidate.replace_all(merged)
			return candidate.as_dict()
		except (OSError, UnicodeError, ValueError, KeyError):
			return dict(defaults)

	def save(self, bindings):
		directory = os.path.dirname(self.path)
		if directory and not os.path.isdir(directory):
			os.makedirs(directory, exist_ok=True)

		temporary_path = self.path + ".tmp"
		body = ["VERSION\t%d" % CONFIG_VERSION]
		for action_id in sorted(bindings):
			shortcut = bindings[action_id]
			body.append(
				"%s\t%s" % (
					action_id,
					"" if shortcut is None else shortcut.serialize(),
				)
			)

		try:
			with _REAL_OPEN(temporary_path, "wb") as handle:
				handle.write(("\n".join(body) + "\n").encode("utf-8"))
				handle.flush()
				os.fsync(handle.fileno())
			os.replace(temporary_path, self.path)
		except Exception:
			try:
				os.unlink(temporary_path)
			except OSError:
				pass
			raise


class Manager(object):
	def __init__(self, interface, store=None):
		self.interface = interface
		self._store = store or BindingStore()
		self._uisystem = _load_uisystem()
		get_channel_count = getattr(
			self._uisystem, "GetChannelCount", None
		)
		request_channel_change = getattr(
			self._uisystem, "RequestChannelChange", None
		)
		channel_count = (
			get_channel_count() if callable(get_channel_count) else 0
		)
		request_adjacent_channel_change = getattr(
			self._uisystem, "RequestAdjacentChannelChange", None
		)
		self.actions = build_actions(
			interface, channel_count, request_channel_change,
			request_adjacent_channel_change
		)
		self._actions_by_id = {
			action.action_id: action for action in self.actions
		}
		defaults = {
			action.action_id: action.default for action in self.actions
		}
		self._reserved = build_reserved_shortcuts()
		self._state = keybindingcore.BindingState(defaults, self._reserved)
		loaded = self._store.load(defaults, self._reserved)
		self._state.replace_all(loaded)
		self._pressed_keys = set()
		self._capture_active = False
		self._dik_to_token = self._build_dik_to_token()
		self._modifier_diks = self._build_modifier_diks()
		self._modifier_dik_values = frozenset(
			value
			for values in self._modifier_diks.values()
			for value in values
		)

	def _build_dik_to_token(self):
		mapping = {}

		def register(dik_name, token=None):
			value = getattr(app, "DIK_" + dik_name, None)
			if value is not None:
				mapping[value] = token or dik_name

		for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
			register(letter)
		for number in range(10):
			register(str(number))
		for number in range(1, 13):
			register("F%d" % number)
		for number in range(10):
			register("NUMPAD%d" % number)
		for dik_name, token in (
			("UP", "UP"),
			("DOWN", "DOWN"),
			("LEFT", "LEFT"),
			("RIGHT", "RIGHT"),
			("HOME", "HOME"),
			("END", "END"),
			("PGUP", "PGUP"),
			("PGDN", "PGDN"),
			("INSERT", "INSERT"),
			("DELETE", "DELETE"),
			("MINUS", "MINUS"),
			("EQUALS", "EQUALS"),
			("LBRACKET", "LBRACKET"),
			("RBRACKET", "RBRACKET"),
			("SEMICOLON", "SEMICOLON"),
			("APOSTROPHE", "APOSTROPHE"),
			("GRAVE", "GRAVE"),
			("BACKSLASH", "BACKSLASH"),
			("COMMA", "COMMA"),
			("PERIOD", "PERIOD"),
			("SLASH", "SLASH"),
			("SPACE", "SPACE"),
			("RETURN", "ENTER"),
			("ESC", "ESC"),
			("ESCAPE", "ESC"),
			("SYSRQ", "SYSRQ"),
			("TAB", "TAB"),
			("ADD", "ADD"),
			("SUBTRACT", "SUBTRACT"),
			("MULTIPLY", "MULTIPLY"),
			("DIVIDE", "DIVIDE"),
			("DECIMAL", "DECIMAL"),
			("NUMPADENTER", "NUMPADENTER"),
		):
			register(dik_name, token)
		for token in ("MOUSE4", "MOUSE5"):
			value = getattr(app, "KEY_" + token, None)
			if value is not None:
				mapping[value] = token
		return mapping

	def _build_modifier_diks(self):
		def available(*names):
			return tuple(
				value
				for value in (
					getattr(app, "DIK_" + name, None) for name in names
				)
				if value is not None
			)

		return {
			"CTRL": available("LCONTROL", "RCONTROL"),
			"SHIFT": available("LSHIFT", "RSHIFT"),
			"ALT": available("LALT", "RALT"),
		}

	def shortcut_from_dik(self, dik):
		if dik in self._modifier_dik_values:
			return None
		token = self._dik_to_token.get(dik)
		if token is None:
			return None

		modifiers = []
		for name in keybindingcore.MODIFIER_ORDER:
			if any(app.IsPressed(value) for value in self._modifier_diks[name]):
				modifiers.append(name)
		return keybindingcore.Shortcut(token, modifiers)

	def clone_state(self):
		return self._state.clone()

	def actions_by_category(self):
		grouped = []
		indexes = {}
		for action in self.actions:
			if action.category_key not in indexes:
				indexes[action.category_key] = len(grouped)
				grouped.append((action.category_key, []))
			grouped[indexes[action.category_key]][1].append(action)
		return grouped

	def get_action(self, action_id):
		return self._actions_by_id[action_id]

	def set_capture_active(self, active):
		self._capture_active = bool(active)
		if self._capture_active:
			self.clear_pressed()

	def is_capture_active(self):
		return self._capture_active

	def save_state(self, staged):
		bindings = staged.as_dict()
		self._store.save(bindings)
		self._state.replace_all(bindings)

	def dispatch_key_down(self, dik):
		if self._capture_active:
			return False
		if ui and ui.IsEditLineFocused():
			return False

		shortcut = self.shortcut_from_dik(dik)
		if shortcut is None:
			return False
		action_id = self._state.owner_of(shortcut)
		if action_id is None:
			return False
		if dik in self._pressed_keys:
			return True

		self._pressed_keys.add(dik)
		self._actions_by_id[action_id].callback()
		return True

	def release_key(self, dik):
		self._pressed_keys.discard(dik)

	def release_unpressed(self):
		# Focus changes can route key-up to the newly active window.
		for dik in tuple(self._pressed_keys):
			if not app.IsPressed(dik):
				self._pressed_keys.discard(dik)

	def clear_pressed(self):
		self._pressed_keys.clear()

	def shortcut_owner(self, serialized):
		try:
			shortcut = keybindingcore.Shortcut.parse(serialized)
		except ValueError:
			return None
		return self._state.owner_of(shortcut)


_manager = None


def SetManager(manager):
	global _manager
	_manager = manager


def GetManager():
	return _manager


def ShortcutOwner(serialized):
	if not _manager:
		return None
	return _manager.shortcut_owner(serialized)
