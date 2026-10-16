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

	def NotifyIncoming(self, key, snapshot, fallbackName=""):
		key = str(key or "")
		name = self.__NameForKey(key, fallbackName)
		snapshot = dict(snapshot or {})
		decision = model.notification_decision_for_conversation(
			self.__Settings(), snapshot.get("window_exists", False),
			snapshot.get("visible", False), snapshot.get("selected_key", ""),
			snapshot.get("selected_name", ""), key, name)

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
