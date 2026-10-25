STATE_SENDING = 1
STATE_SENT = 2
STATE_QUEUED = 3
STATE_DELIVERED = 4
STATE_FAILED = 5
STATE_RETRYING = 6
STATE_EXPIRED = 7
STATE_REJECTED = 8

# Server `unified_messenger::Error` values (protocol v1) plus local-only codes
# persisted by the native history store. Local codes never cross the wire.
ERROR_NONE = 0
ERROR_INVALID_RECIPIENT = 1
ERROR_REJECTED = 2
ERROR_QUEUE_FULL = 3
ERROR_RATE_LIMITED = 4
ERROR_MALFORMED = 5
ERROR_DATABASE_UNAVAILABLE = 6
ERROR_RECIPIENT_MISMATCH = 64
ERROR_TRANSPORT_FAILURE = 65
ERROR_UNKNOWN_TO_SERVER = 66
# An accepted message the server no longer knows: delivered or expired, but
# the outcome is unknown. Terminal, never resent.
ERROR_OUTCOME_UNKNOWN = 67

RETRYABLE_ERRORS = (ERROR_QUEUE_FULL, ERROR_RATE_LIMITED,
	ERROR_DATABASE_UNAVAILABLE, ERROR_TRANSPORT_FAILURE, ERROR_UNKNOWN_TO_SERVER)
# A Sending/Retrying row older than this may have been dropped while the
# session was restricted; retrying keeps the original message ID.
STALE_SENDING_MS = 60000

MESSAGE_TYPE_CHAT = 0
MESSAGE_TYPE_GAME_MASTER = 1
# Session-only (never stored): a duel challenge row with Přijmout / Odmítnout.
MESSAGE_TYPE_DUEL_CHALLENGE = 2


def stable_key(pid):
	return "pid:%d" % int(pid)


def ascii_lower(value):
	# The executable folds only ASCII letters in `name:` keys. Unicode lower()
	# would produce different keys for names with non-ASCII capitals.
	return "".join(
		chr(ord(character) + 32) if "A" <= character <= "Z" else character
		for character in str(value))


def provisional_key(name):
	return "name:%s" % ascii_lower(str(name).strip())


def guild_key(guild_id):
	return "guild:%d" % int(guild_id)


def pid_from_key(key):
	key = str(key or "")
	if not key.startswith("pid:"):
		return 0
	try:
		return max(0, int(key[4:]))
	except ValueError:
		return 0


def conversation_aliases(conversations, profile_pid=None):
	# Native outgoing messages remain name-keyed until the server confirms the
	# PID. Project only unambiguous aliases; two PID histories stay separate.
	# `profile_pid(name)` returns the PID currently owning the name according to
	# the authoritative profile cache; a different owner vetoes the alias.
	rows = list(conversations)
	stable = {}
	for row in rows:
		key, name = str(row[0]), row[1]
		if key.startswith("pid:"):
			stable.setdefault(provisional_key(name), []).append((key, name))
	aliases = {}
	for row in rows:
		key = str(row[0])
		targets = stable.get(key, ())
		if not key.startswith("name:") or len(targets) != 1:
			continue
		target, name = targets[0]
		owner = 0
		if profile_pid:
			try:
				owner = int(profile_pid(name) or 0)
			except (TypeError, ValueError):
				owner = 0
		if owner and owner != pid_from_key(target):
			continue
		aliases[key] = target
	return aliases


def conversation_summaries(conversations, aliases=None):
	rows = list(conversations)
	if aliases is None:
		aliases = conversation_aliases(rows)
	summaries = {str(row[0]): list(row[:5]) for row in rows if str(row[0]) not in aliases}
	for row in rows:
		key, activity, unread = str(row[0]), row[3], row[4]
		if key in aliases:
			target = summaries[aliases[key]]
			target[3] = max(int(target[3]), int(activity))
			target[4] = int(target[4]) + int(unread)
	return [tuple(summaries[str(row[0])]) for row in rows if str(row[0]) not in aliases]


def storage_keys_for(key, aliases):
	canonical = aliases.get(str(key), str(key))
	return [canonical] + sorted(alias for alias, target in aliases.items() if target == canonical)


def conversation_storage_keys(key, conversations, aliases=None):
	if aliases is None:
		aliases = conversation_aliases(conversations)
	return storage_keys_for(key, aliases)


def conversation_previews(rows, aliases):
	# Rows from the native summary API carry (..., last_body, last_row_id).
	# Pick the newest body among a stable conversation and its aliases.
	previews = {}
	for row in rows:
		if len(row) < 7:
			continue
		canonical = aliases.get(str(row[0]), str(row[0]))
		rowID = int(row[6] or 0)
		if rowID and rowID > previews.get(canonical, (0, ""))[0]:
			previews[canonical] = (rowID, str(row[5] or ""))
	return dict((key, value[1]) for key, value in previews.items())


def conversation_last_rows(rows, aliases):
	"""{canonical key: (newest row id, its storage key)} from the summary rows
	(..., last_body, last_row_id)."""
	last = {}
	for row in rows:
		if len(row) < 7:
			continue
		canonical = aliases.get(str(row[0]), str(row[0]))
		rowID = int(row[6] or 0)
		if rowID and rowID > last.get(canonical, (0, ""))[0]:
			last[canonical] = (rowID, str(row[0]))
	return last


def unread_total(conversations):
	# Guild lines are mirrored from the main chat the player already sees, so
	# the global badge counts private conversations only and ignores filters.
	total = 0
	for row in conversations:
		if not str(row.get("key", "")).startswith("guild:"):
			total += int(row.get("unread", 0) or 0)
	return total


def latest_unread_conversation(conversations):
	"""The newest private conversation with unread messages, or None."""
	unread = [row for row in conversations
		if not str(row.get("key", "")).startswith("guild:") and int(row.get("unread", 0) or 0) > 0]
	if not unread:
		return None
	return max(unread, key=lambda row: int(row.get("last_activity", 0) or 0))


def guild_display_name(stored_name, guild_label):
	stored_name = str(stored_name or "").strip()
	if not stored_name or stored_name == "Guild":
		return str(guild_label)
	return "%s: %s" % (guild_label, stored_name)


def sort_conversations(conversations):
	return sorted(
		conversations,
		key=lambda row: (
			0 if str(row.get("key", "")).startswith("guild:") else 1,
			-int(row.get("last_activity", 0)),
			str(row.get("name", "")).lower(),
		),
	)


def filter_conversations(conversations, query):
	query = str(query).strip().lower()
	if not query:
		return list(conversations)
	return [row for row in conversations if query in str(row.get("name", "")).lower()]


def message_error(message):
	# Field 10 is appended by newer executables; older ones return 10 fields.
	if len(message) > 10:
		try:
			return int(message[10])
		except (TypeError, ValueError):
			return 0
	return None


def can_retry(state, error_code=None, age_ms=0):
	state = int(state)
	if state in (STATE_FAILED, STATE_EXPIRED):
		return True
	# Only executables that persist error codes can retry these safely.
	if error_code is None:
		return False
	if state == STATE_REJECTED:
		# Rows without a stored reason (code 0) may be blocks; keep them final.
		return int(error_code) in RETRYABLE_ERRORS
	if state in (STATE_SENDING, STATE_RETRYING):
		return int(age_ms) >= STALE_SENDING_MS
	return False


def error_key(error_code):
	return {
		ERROR_INVALID_RECIPIENT: "UNIFIED_MESSENGER_ERROR_UNDELIVERABLE",
		ERROR_REJECTED: "UNIFIED_MESSENGER_ERROR_UNDELIVERABLE",
		ERROR_QUEUE_FULL: "UNIFIED_MESSENGER_ERROR_QUEUE_FULL",
		ERROR_RATE_LIMITED: "UNIFIED_MESSENGER_ERROR_RATE_LIMITED",
		ERROR_MALFORMED: "UNIFIED_MESSENGER_ERROR_MALFORMED",
		ERROR_DATABASE_UNAVAILABLE: "UNIFIED_MESSENGER_ERROR_SERVER_UNAVAILABLE",
		ERROR_RECIPIENT_MISMATCH: "UNIFIED_MESSENGER_ERROR_RECIPIENT_CHANGED",
		ERROR_TRANSPORT_FAILURE: "UNIFIED_MESSENGER_ERROR_NOT_SENT",
		ERROR_UNKNOWN_TO_SERVER: "UNIFIED_MESSENGER_ERROR_NOT_SENT",
		ERROR_OUTCOME_UNKNOWN: "UNIFIED_MESSENGER_ERROR_OUTCOME_UNKNOWN",
	}.get(int(error_code or 0), "")


def submit_notice_key(error_code, native_error_codes):
	# Executables without persisted error codes also forward reconnect status
	# answers for forgotten IDs as a live Rejected result; those would print
	# one notice per pending message at every login, so they stay silent.
	error_code = int(error_code or 0)
	if not native_error_codes and error_code == ERROR_REJECTED:
		return ""
	return error_key(error_code)


def recovery_key(status):
	# Native status text is not localized. A preserved-and-reset database is
	# a recovery; session memory keeps messages until logout; any other status
	# (including every status from executables without session memory) means
	# the Messenger is not available in this session.
	status = str(status or "")
	if "preserved and reset" in status:
		return "UNIFIED_MESSENGER_RECOVERY"
	if "in memory" in status:
		return "UNIFIED_MESSENGER_HISTORY_UNAVAILABLE"
	return "UNIFIED_MESSENGER_HISTORY_DISABLED"


def merge_older_page(loaded, older, cap):
	# Prepend an older page; trim the newest rows when the window is full.
	known = set(row[0] for row in loaded)
	combined = [row for row in older if row[0] not in known] + list(loaded)
	if len(combined) <= cap:
		return combined, []
	return combined[:cap], combined[cap:]


def restore_newer_rows(loaded, newer, count, cap):
	# Move up to `count` previously trimmed newer rows back into the window and
	# drop the same number of oldest rows.
	count = max(0, min(int(count), len(newer)))
	combined = list(loaded) + list(newer[:count])
	remaining = list(newer[count:])
	dropped = max(0, len(combined) - cap)
	return combined[dropped:], remaining, dropped


def typing_transition(text, previous_text, typing_sent, last_sent_ms,
		last_change_ms, now_ms):
	"""Returns None, True (send start/refresh) or False (send stop)."""
	text = str(text or "")
	if not text:
		return False if typing_sent else None
	changed = text != str(previous_text or "")
	if changed:
		if not typing_sent or int(now_ms) - int(last_sent_ms) >= 3000:
			return True
		return None
	if typing_sent and int(now_ms) - int(last_change_ms) >= 4000:
		return False
	return None


def typing_active(last_update_ms, now_ms):
	return 0 <= int(now_ms) - int(last_update_ms) < 5000


# messengerHistory.LoadMessages row field 3 (MessengerHistory.h Direction).
DIRECTION_INCOMING, DIRECTION_OUTGOING = 1, 2


def default_notification_settings():
	return {"badge": True, "sound": False, "toast": True, "preview": False}


def notification_decision(settings, window_visible, conversation_selected):
	quiet = bool(window_visible and conversation_selected)
	return {
		"badge": bool(settings.get("badge", True)) and not quiet,
		"sound": bool(settings.get("sound", False)) and not quiet,
		"toast": bool(settings.get("toast", True)) and not window_visible,
		"preview": bool(settings.get("preview", False)) and not quiet,
		"request_focus": False,
	}


def lookup_prefix_ready(query, now_ms, last_edit_ms):
	return len(str(query or "")) >= 2 and int(now_ms) - int(last_edit_ms) >= 250


def lookup_response_is_current(token, pending_token, dialog_open):
	return bool(dialog_open and int(token) != 0 and
		int(token) == int(pending_token))


def same_conversation(selected_key, selected_name, incoming_key, incoming_name):
	selected_key = str(selected_key or "")
	incoming_key = str(incoming_key or "")
	selected_stable = selected_key.startswith("pid:") or selected_key.startswith("guild:")
	incoming_stable = incoming_key.startswith("pid:") or incoming_key.startswith("guild:")
	if selected_stable and incoming_stable:
		return selected_key == incoming_key
	if selected_key and incoming_key and selected_key == incoming_key:
		return True
	selected_name = str(selected_name or "")
	incoming_name = str(incoming_name or "")
	return bool(selected_name and incoming_name and
		selected_name.lower() == incoming_name.lower())


def notification_decision_for_conversation(settings, window_exists,
		window_visible, selected_key, selected_name, incoming_key, incoming_name):
	selected = bool(window_exists and window_visible and same_conversation(
		selected_key, selected_name, incoming_key, incoming_name))
	return notification_decision(settings, bool(window_visible), selected)


def resolve_open_conversation(name, requested_key, conversations):
	name = str(name or "")
	requested_key = str(requested_key or "")
	rows = list(conversations)
	if requested_key:
		for row in rows:
			if str(row[0]) == requested_key:
				return requested_key, str(row[1]), int(row[4])
		return requested_key, name, 0

	matches = [row for row in rows
		if name and str(row[1]).lower() == name.lower()]
	if len(matches) == 1:
		return str(matches[0][0]), str(matches[0][1]), int(matches[0][4])
	return provisional_key(name), name, 0


def resolve_selection(selected_key, selected_name, conversations, changed_key=""):
	selected_key = str(selected_key or "")
	selected_name = str(selected_name or "")
	changed_key = str(changed_key or "")
	stable = selected_key and not selected_key.startswith("name:")
	rows = list(conversations)
	for row in rows:
		key = str(row[0])
		name = str(row[1])
		if stable and key == selected_key:
			return key, name
	if stable:
		return selected_key, selected_name
	if changed_key:
		for row in rows:
			key = str(row[0])
			name = str(row[1])
			if key == changed_key and same_conversation(
					selected_key, selected_name, key, name):
				return key, name
	matches = [(str(row[0]), str(row[1])) for row in rows
		if selected_name and str(row[1]).lower() == selected_name.lower()]
	if len(matches) == 1:
		return matches[0]
	return selected_key, selected_name


def message_state_key(state):
	return {
		STATE_SENDING: "UNIFIED_MESSENGER_STATE_SENDING",
		STATE_SENT: "UNIFIED_MESSENGER_STATE_SENT",
		STATE_QUEUED: "UNIFIED_MESSENGER_STATE_QUEUED",
		STATE_DELIVERED: "UNIFIED_MESSENGER_STATE_DELIVERED",
		STATE_FAILED: "UNIFIED_MESSENGER_STATE_FAILED",
		STATE_RETRYING: "UNIFIED_MESSENGER_STATE_RETRYING",
		STATE_EXPIRED: "UNIFIED_MESSENGER_STATE_EXPIRED",
		STATE_REJECTED: "UNIFIED_MESSENGER_STATE_REJECTED",
	}.get(int(state), "")


def message_time_ms(message):
	"""The time a message shows: this client's own clock when it was sent or
	received (client_timestamp_ms), like the conversation list. The server's
	timestamp only when there is none: its clock may differ from the player's
	(on the local VM it is hours off)."""
	try:
		return int(message[6] or message[7] or 0)
	except (IndexError, TypeError, ValueError):
		return 0


def is_session_row(message):
	"""A session-only row (system whisper, duel challenge or result): its row
	id is fractional (next_local_row_id)."""
	try:
		value = float(message[0])
	except (IndexError, TypeError, ValueError):
		return False
	return value != int(value)


def first_unread_row_id(messages, unread_count):
	"""The row id above which the unread divider stands: the oldest of the
	last `unread_count` incoming stored messages. The player's own messages
	and session rows are never unread, so they never move it."""
	remaining = max(0, int(unread_count or 0))
	found = None
	for message in reversed(list(messages)):
		if not remaining:
			break
		if int(message[3]) == 1 and not is_session_row(message):
			found = message[0]
			remaining -= 1
	return found


def with_unread_separator(messages, unread_count):
	rows = list(messages)
	unread_count = max(0, min(int(unread_count), len(rows)))
	if not unread_count:
		return rows
	index = len(rows) - unread_count
	return rows[:index] + [{"separator": "unread"}] + rows[index:]


def with_date_separators(messages, date_key):
	result = []
	previous = None
	for message in messages:
		current = date_key(message)
		if current != previous:
			result.append({"separator": "date", "value": current})
			previous = current
		result.append(message)
	return result


# Whispers kept only in the native whisper buffer (system notices,
# [SYSTEM]/[Dungeon Info], whisper errors and chat lines the executable could
# not import) and duel challenges (see duelchallenge.py) have no history row.
# Messages shows them as session-only incoming rows. A fractional row id places such a row after the
# newest stored row known when it arrived, so pages and anchors keep working.
LOCAL_MESSAGE_LIMIT = 50
LOCAL_ROW_STEP = 0.0001


def local_message_body(name, line):
	name = str(name or "")
	line = str(line or "")
	prefix = "%s : " % name
	if name and line.startswith(prefix):
		return line[len(prefix):]
	return line


def next_local_row_id(latest_stored_row_id, local_row_ids):
	base = max(0, int(latest_stored_row_id or 0))
	same_base = [float(value) for value in local_row_ids
		if base <= float(value) < base + 1]
	return round(max([float(base)] + same_base) + LOCAL_ROW_STEP, 4)


def local_message_row(row_id, name, body, timestamp_ms, game_master=False):
	kind = MESSAGE_TYPE_GAME_MASTER if game_master else MESSAGE_TYPE_CHAT
	return (row_id, 0, provisional_key(name), 1, str(name), str(body),
		int(timestamp_ms), 0, kind, STATE_DELIVERED)


def stored_page_boundary(before):
	# Stored rows have whole ids; a local anchor (e.g. 105.0001) must still
	# include stored row 105 in the older page.
	value = float(before or 0)
	whole = int(value)
	return whole + 1 if value > whole else whole


def merge_local_messages(stored, local_rows, before, limit):
	rows = list(stored) + [row for row in local_rows
		if not before or row[0] < before]
	rows.sort(key=lambda row: row[0])
	return rows[-int(limit):] if int(limit) > 0 else rows


# A duel challenge row carries "duel:<challenge id>" in the message id field
# (never retried, never sent) and the duel message type.
DUEL_MESSAGE_ID = "duel:%d"


def local_duel_row(row_id, name, body, timestamp_ms, identifier, own_name=""):
	"""A duel row of the thread with `name`: incoming (the challenge), or with
	`own_name` the player's own request (sent by the player, no actions)."""
	row = local_message_row(row_id, name, body, timestamp_ms)
	if own_name:
		row = row[:3] + (0, str(own_name)) + row[5:]
	return row[:1] + (DUEL_MESSAGE_ID % int(identifier),) + row[2:8] + \
		(MESSAGE_TYPE_DUEL_CHALLENGE,) + row[9:]


def duel_identifier(message):
	"""The challenge id of a duel row, 0 for any other message."""
	try:
		if int(message[8] or 0) != MESSAGE_TYPE_DUEL_CHALLENGE:
			return 0
		prefix, value = str(message[1]).split(":", 1)
		return int(value) if prefix == "duel" else 0
	except (IndexError, TypeError, ValueError):
		return 0


def merge_local_conversations(rows, local, present):
	"""Adds session rows (duel challenges) to the conversation list: the
	challenger's existing thread gets the newer activity, preview and the
	unread count; a player without a stored thread gets a provisional one.
	`local` holds dicts (name, last_activity, unread, preview); `present`
	turns (preview, last_activity) into the shown (preview, time)."""
	rows = [dict(row) for row in rows]
	for entry in local:
		name = str(entry["name"])
		activity = int(entry.get("last_activity", 0) or 0)
		target = None
		for row in rows:
			key = str(row.get("key", ""))
			if not key.startswith("guild:") and str(row.get("name", "")).lower() == name.lower():
				target = row
				break
		if target is None:
			target = {"key": provisional_key(name), "name": name,
				"last_activity": 0, "unread": 0, "preview": "", "display_time": ""}
			rows.append(target)
		target["unread"] = int(target.get("unread", 0) or 0) + int(entry.get("unread", 0) or 0)
		if activity >= int(target.get("last_activity", 0) or 0):
			target["last_activity"] = activity
			target["preview"], target["display_time"] = present(
				entry.get("preview", ""), activity)
	return rows
