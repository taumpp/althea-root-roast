"""Session-scoped album presentation. Progress and rewards come from the server."""
import json
import re

def Number(value, maximum=(1 << 64) - 1):
	if isinstance(value, bool) or not re.match(r"^[0-9]+\Z", str(value)):
		raise ValueError("invalid album integer")
	result = int(value)
	if result > maximum:
		raise ValueError("album integer overflow")
	return result


def Object(pairs):
	result = {}
	for key, value in pairs:
		if key in result:
			raise ValueError("duplicate album field")
		result[key] = value
	return result


class AlbumState(object):
	def __init__(self, view, names=None):
		self.view = view
		self.names = names or {}
		self.ids = [pet["id"] for pet in view["pets"]]
		self.lastError = None
		self.presentationOwner = None
		self.context = None
		self.generation = 0
		self.Clear()

	def OwnsPresentation(self, owner):
		return owner is not None and self.presentationOwner is owner

	def ClaimPresentation(self, owner):
		if self.OwnsPresentation(owner):
			return False
		self.presentationOwner = owner
		self.context = None
		self.Clear()
		return True

	def ReleasePresentation(self, owner):
		if not self.OwnsPresentation(owner):
			return False
		self.presentationOwner = None
		self.context = None
		self.Clear()
		return True

	def Clear(self):
		self.available = False
		self.pets = {}
		self.bonuses = []
		self.attack = self.magicAttack = self.bookPower = 0
		self.albumUtc = 0
		self.notifications = []
		self.visualNotifications = []
		# Independent presentation receipts: the book must not consume popup queues.
		self.discoveryReceipts = {}
		self.unreadCaptures = 0
		self.generation += 1

	def Begin(self, digest, epoch, profile, active):
		try:
			epoch = Number(epoch)
			active = Number(active, 1)
			if (digest != self.view["hash"] or not epoch or
				profile not in ("normal", "qa50") or not active):
				raise ValueError("unavailable album capability")
			context = (digest, epoch, profile)
			# EnterGame and delayed quest readiness may repeat the same offer.
			# Preserve the committed baseline so a fresh clue still emits a notice.
			if context != self.context:
				self.Clear()
				self.context = context
			self.lastError = None
			return True
		except (ValueError, TypeError) as error:
			self.lastError = str(error)
			self.Clear()
			self.context = None
			return False

	def Receive(self, opcode, payload):
		"""Validate a complete frame before changing presentation or native effects."""
		try:
			value = json.loads(payload, object_pairs_hook=Object)
			if not isinstance(value, dict) or self.context is None:
				raise ValueError("album frame without capability")
			context = (value["hash"], Number(value["owner_epoch"]), value["profile"])
			if context != self.context:
				raise ValueError("album frame context mismatch")
			if opcode == 1:
				self.Snapshot(value)
				self.lastError = None
				return ("snapshot",)
			if opcode in (2, 3):
				actor = (Number(value["vid"], (1 << 32) - 1),
					Number(value["core"]), Number(value["incarnation"]))
				if not self.available or not all(actor):
					return None
				if opcode == 3:
					return ("actor",) + actor
				entry = Number(value["entry"], len(self.ids) - 1)
				row = self.pets[self.ids[entry]]
				revision = Number(value["revision"])
				high, low = Number(value["hunt_high"]), Number(value["hunt_low"])
				enabled = Number(value["enabled"], 1)
				if (not revision or revision > row["revision"] or not (high or low)):
					return None
				if enabled and (row["phase"] != 1 or revision != row["hunt_revision"] or
					(high, low) != (row["hunt_high"], row["hunt_low"])):
					return None
				return ("marker", entry) + actor + (high, low, revision, enabled)
		except (ValueError, TypeError, KeyError, OverflowError) as error:
			self.lastError = str(error)
			return None
		return None

	def Snapshot(self, value):
		available = Number(value["available"], 1)
		rows = value["pets"]
		if not available:
			if rows not in ([], ""):
				raise ValueError("unavailable album contains progress")
			# A same-owner DB readiness refresh is not a new login. Keep the
			# committed baseline and queued notices while disabling presentation.
			self.available = False
			self.bonuses = []
			self.attack = self.magicAttack = self.bookPower = 0
			self.generation += 1
			return
		if not isinstance(rows, list) or len(rows) != len(self.ids):
			raise ValueError("incomplete album")
		candidate = {}
		for index, item in enumerate(rows):
			if item["id"] != self.ids[index]:
				raise ValueError("unknown or reordered pet")
			row = {"phase": Number(item["phase"], 2),
				"level": Number(item["level"], self.view["max_level"]),
				"growth": Number(item["growth"]),
				"denominator": Number(item["denominator"]),
				"revision": Number(item["revision"])}
			if (row["denominator"] != self.view["pets"][index]["denominator"] or row["growth"] > row["denominator"] or
				(row["phase"] == 2) != bool(row["level"])):
				raise ValueError("invalid progress")
			previous = self.pets.get(item["id"])
			if previous and row["revision"] < previous["revision"]:
				raise ValueError("stale progress")
			if row["phase"] == 1:
				row["hunt_high"], row["hunt_low"] = Number(item["hunt_high"]), Number(item["hunt_low"])
				row["hunt_revision"] = Number(item["hunt_revision"])
				if (not (row["hunt_high"] or row["hunt_low"]) or
					not row["hunt_revision"] or row["hunt_revision"] > row["revision"]):
					raise ValueError("invalid durable hunt identity")
				row["map"] = Number(item["map"], (1 << 32) - 1)
				row["vnum"] = Number(item["vnum"], (1 << 32) - 1)
				row["next_window"] = Number(item["next_window"])
				# Missing routing fields retain read compatibility with the previous
				# server; new paired servers report a pinned physical channel.
				row["channel"] = Number(item.get("channel", 0), 255)
				row["shared_hub"] = Number(item.get("shared_hub", 0), 1)
				for name in ("map_name", "direction"):
					text = item[name]
					if not isinstance(text, str) or not text or len(text) > 128:
						raise ValueError("invalid hunt description")
					row[name] = text
			candidate[item["id"]] = row
		bonuses = [Number(item, cap) for item, cap in zip(value["bonuses"], self.view["caps"])]
		if len(bonuses) != len(self.view["caps"]) or len(value["bonuses"]) != len(bonuses):
			raise ValueError("invalid bonus groups")
		attack, magic, book = Number(value["attack"]), Number(value["magic_attack"]), Number(value["book_power"])
		utc = Number(value["album_utc"])
		changes = []
		visuals = []
		if self.pets:
			for pet in self.view["pets"]:
				previous, current = self.pets[pet["id"]], candidate[pet["id"]]
				if current["revision"] <= previous["revision"]:
					continue
				name = self.names.get(pet["id"])
				if not name:
					continue
				if previous["phase"] == 0 and current["phase"] == 1:
					changes.append(("clue", name, current["map_name"], current["direction"], pet["when"]))
					visuals.append(dict(kind="clue", id=pet["id"], name=name, channel=current["channel"]))
				elif previous["phase"] == 1 and current["phase"] == 2:
					changes.append(("capture", name))
					visuals.append(dict(kind="capture", id=pet["id"], name=name,
						owned=sum(row["phase"] == 2 for row in candidate.values())))
				elif previous["phase"] == 2 and current["phase"] == 2 and current["level"] > previous["level"]:
					visuals.append(dict(kind="level", id=pet["id"], name=name,
						before_level=previous["level"], level=current["level"]))
		if self.pets:
			for identity, current in candidate.items():
				if current["phase"] and current["phase"] != self.pets[identity]["phase"]:
					self.discoveryReceipts[identity] = current["revision"]
		self.notifications.extend(changes)
		self.visualNotifications.extend(visuals)
		self.unreadCaptures = min(len(self.ids), self.unreadCaptures +
			sum(visual["kind"] == "capture" for visual in visuals))
		self.pets, self.bonuses = candidate, bonuses
		self.attack, self.magicAttack, self.bookPower = attack, magic, book
		self.albumUtc, self.available = utc, True
		self.generation += 1

	def ConsumeNotifications(self):
		result, self.notifications = self.notifications, []
		return result

	def ReadCaptures(self):
		if self.available:
			self.unreadCaptures = 0

	def RestoreUnreadCaptures(self, count):
		try:
			count = Number(count, len(self.ids))
		except (ValueError, TypeError):
			return
		self.unreadCaptures = min(len(self.ids), self.unreadCaptures + count)

	def ConsumeVisualNotifications(self):
		result, self.visualNotifications = self.visualNotifications, []
		return result


state = None


def GetState():
	global state
	if state is None:
		with open("petalbumruntime.txt", "r") as stream:
			view = json.load(stream)
		with open("petalbumcatalog.txt", "r") as stream:
			names = {pet["id"]: pet["name"] for pet in json.load(stream)["pets"]}
		state = AlbumState(view, names)
	return state
