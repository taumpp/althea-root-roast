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


def unread_total(conversations):
	# Guild lines are mirrored from the main chat the player already sees, so
	# the global badge counts private conversations only and ignores filters.
	total = 0
	for row in conversations:
		if not str(row.get("key", "")).startswith("guild:"):
			total += int(row.get("unread", 0) or 0)
	return total


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
