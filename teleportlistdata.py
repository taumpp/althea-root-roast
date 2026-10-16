# -*- coding: utf-8 -*-
"""Presentation-only list state; the atlas catalog remains the warp authority."""
import json
import os

import teleportmapdata


PREFERENCES_PATH = "UserData/teleport_atlas.json"
CATEGORIES = (
	("all", "Vše", "compass"),
	("cities", "Města", "town"),
	("basic", "Základní", "sword"),
	("advanced", "Pokročilé", "crossed_swords"),
)
CATEGORY_IDS = tuple(row[0] for row in CATEGORIES)
GROUPS = {
	"cities": ("all_in_one", "bokjung", "bakra", "jayang"),
	"basic": ("seungryong_valley", "orktal"),
	"advanced": ("sungmahi_desert", "sands_of_suffering", "underwater", "mirage_island", "battleground"),
}
ORDER = GROUPS["cities"] + GROUPS["basic"] + GROUPS["advanced"]


def LoadPreferences(path=PREFERENCES_PATH):
	try:
		with open(path, "r") as stream:
			data = json.load(stream)
		if (not isinstance(data, dict) or data.get("version") != 1
			or type(data.get("list")) is not bool or data.get("category") not in CATEGORY_IDS):
			return False, "all"
		return data["list"], data["category"]
	except (IOError, OSError, ValueError, TypeError):
		return False, "all"


def SavePreferences(list_enabled, category, path=PREFERENCES_PATH):
	try:
		directory = os.path.dirname(path)
		if directory and not os.path.isdir(directory):
			os.makedirs(directory)
		with open(path, "w") as stream:
			json.dump({"version": 1, "list": bool(list_enabled),
				"category": category if category in CATEGORY_IDS else "all"}, stream)
		return True
	except (IOError, OSError):
		return False


class TeleportListModel(object):
	PAGE_SIZE = 5

	def __init__(self, category="all"):
		self.category = "all"
		self.offset = 0
		self.selectedId = None
		self.SetCategory(category)

	def Destinations(self):
		ids = ORDER if self.category == "all" else GROUPS[self.category]
		return [teleportmapdata.GetDestination(key) for key in ids
			if teleportmapdata.GetDestination(key) is not None]

	def SetCategory(self, category):
		self.category = category if category in CATEGORY_IDS else "all"
		rows = self.Destinations()
		ids = [row["id"] for row in rows]
		if self.selectedId not in ids:
			self.selectedId = ids[0] if ids else None
		self.offset = 0

	def Select(self, destination_id):
		if destination_id not in [row["id"] for row in self.Destinations()]:
			return False
		self.selectedId = destination_id
		return True

	def Selected(self):
		return teleportmapdata.GetDestination(self.selectedId)

	def CanTeleport(self, level):
		row = self.Selected()
		return row is not None and level >= row["level"]

	def MaxOffset(self):
		return max(0, len(self.Destinations()) - self.PAGE_SIZE)

	def Scroll(self, delta):
		self.offset = max(0, min(self.MaxOffset(), self.offset + int(delta)))

	def Visible(self):
		return self.Destinations()[self.offset:self.offset + self.PAGE_SIZE]
