"""Display generated expedition templates with server-authoritative targets."""
import json


class ExpeditionTexts(object):

	def __init__(self):
		with open("mountexpeditiontexts.txt", "r") as stream:
			catalog = json.load(stream)
		if catalog.get("schema") != "althea-mount-expedition-texts-v1":
			raise ValueError("unsupported mount expedition text catalog")
		self.coreEquipmentText = catalog["core_equipment_text"]
		self.labels = {}
		for row in catalog["tasks"]:
			key = (row["element_id"], row["task_id"])
			if key in self.labels:
				raise ValueError("duplicate mount expedition label")
			self.labels[key] = row["text"]

	def Get(self, task):
		label = self.labels.get((task["element_id"], task["task_id"]))
		if label is None:
			return None
		return label.format(target=task["target"])
