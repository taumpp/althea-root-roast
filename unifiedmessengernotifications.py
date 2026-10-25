import unifiedmessengermodel as model


class NotificationController(object):
	def __init__(self, history, presenter, soundModule, application, clock):
		self.history = history
		self.presenter = presenter
		self.sound = soundModule
		self.application = application
		self.clock = clock
		self.lastSound = -1000

	def __Settings(self):
		settings = model.default_notification_settings()
		if not self.history:
			return settings
		for key in settings:
			try:
				settings[key] = bool(
					self.history.GetNotificationPreference(key))
			except:
				pass
		return settings

	def __NameForKey(self, key, fallback=""):
		if self.history and key:
			try:
				for row in self.history.ListConversations():
					if str(row[0]) == str(key):
						return str(row[1])
			except:
				pass
		return str(fallback or key)

	def RestoreUnread(self, snapshot):
		# Reconnect reopens the active character's history, but does not replay
		# incoming events for its existing unread messages. Rebuild only letters.
		if not self.history or snapshot.get("visible", False):
			return
		if not self.__Settings()["toast"]:
			return
		try:
			rows = model.conversation_summaries(self.history.ListConversations())
		except Exception:
			return
		for key, name, kind, activity, unread in rows:
			if int(unread) > 0 and name:
				self.presenter(str(key), str(name))

	def Decision(self, key, snapshot, fallbackName=""):
		"""What an incoming message would show (letter, sound, badge), without
		showing it: the player's settings and whether Messages is shown."""
		key = str(key or "")
		name = self.__NameForKey(key, fallbackName)
		snapshot = dict(snapshot or {})
		return model.notification_decision_for_conversation(
			self.__Settings(), snapshot.get("window_exists", False),
			snapshot.get("visible", False), snapshot.get("selected_key", ""),
			snapshot.get("selected_name", ""), key, name)

	def NotifyGuildLine(self, key, snapshot):
		# Guild chat (player report 21. 10., batch 7 add-on): the executable mirrors
		# every guild line into Messages as event 5, the player's own lines
		# too, and nothing raised a letter. The newest stored line tells who
		# wrote it: only another member's line notifies, like a whisper.
		key = str(key or "")
		if not key.startswith("guild:") or not self.history:
			return None
		try:
			rows = self.history.LoadMessages(key, 0, 1)
		except Exception:
			return None
		if not rows or int(rows[-1][3]) != model.DIRECTION_INCOMING:
			return None
		return self.NotifyIncoming(key, snapshot)

	def NotifyIncoming(self, key, snapshot, fallbackName=""):
		key = str(key or "")
		name = self.__NameForKey(key, fallbackName)
		snapshot = dict(snapshot or {})
		decision = self.Decision(key, snapshot, name)

		selectedKey = str(snapshot.get("selected_key", "") or "")
		stableMatch = (snapshot.get("visible", False) and key and
			(key.startswith("pid:") or key.startswith("guild:")) and
			selectedKey == key)
		if stableMatch and self.history:
			try:
				self.history.MarkRead(key)
			except:
				pass

		if decision["sound"]:
			now = int(self.clock())
			if now - self.lastSound >= 1000:
				snd = self.sound
				snd.PlayNotificationSound("sound/ui/messenger_receive.wav")
				self.lastSound = now

		if decision["toast"] and name:
			self.presenter(key, name)
			app = self.application
			app.FlashApplication()
		return decision
