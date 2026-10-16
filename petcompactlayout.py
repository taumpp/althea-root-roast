"""Approved C geometry; preserve legacy revive and attribute child contracts."""
import uiScriptLocale as L
import uicrimsoncontrols

ART = "d:/ymir work/ui/pet/album_c/"
K1 = "d:/ymir work/ui/game/crimson_ember/mount_system/k1/"
SLOT = "d:/ymir work/ui/public/Slot_Base.sub"


def Text(name, x, y, text="", align="left", size=12, color=0xffe4dacb):
	return {"name":name, "type":"text", "x":x, "y":y,
		"text":text, "text_horizontal_align":align, "fontname":"Tahoma:%da" % size,
		"color":color-0x100000000 if color>0x7fffffff else color,
		"style":("not_pick",)}


def Image(name, x, y, path):
	return {"name":name, "type":"expanded_image", "x":x, "y":y,
		"image":path, "style":("not_pick",)}


def Slot(name, x, y):
	return {"name":name, "type":"slot", "x":x, "y":y,
		"width":32, "height":32, "image":SLOT,
		"slot":({"index":0,"x":0,"y":0,"width":32,"height":32},)}


def Button(name, x, y, caption, family="80x24"):
	return {"name":name, "type":"button", "x":x, "y":y, "text":caption,
		"default_image":uicrimsoncontrols.Visual(family,"normal"),
		"over_image":uicrimsoncontrols.Visual(family,"hover"),
		"down_image":uicrimsoncontrols.Visual(family,"pressed"),
		"disable_image":uicrimsoncontrols.Visual(family,"disabled")}


def Apply(window):
	window.update(width=292, height=520)
	board = window["children"][0]
	board.update(type="board",width=292,height=520)
	children = board["children"]
	old = {child["name"]:child for child in children}
	page = old["PetInfo_Page"]
	page.update(width=292,height=520)
	# Determine remains registered but has no reachable control.
	determine = next(child for child in page["children"] if child["name"] == "DetermineButton")
	old["PetAttrChange_Page"]["children"].append(determine)
	children.remove(old["PetInfoUIBG"])
	children.insert(0, {"name":"PetInfoUIBG","type":"bar","x":6,"y":31,
		"width":280,"height":482,"color":-16185337,"style":("not_pick",)})
	old["TitleBar"].update(x=-4,y=0,width=300)
	page["children"] = [
		Image("PetSection",16,41,K1+"header_260x28.png"),
		Text("PetSectionText",146,48,L.PET_ALBUM_PET,"center",12,0xffe5c17b),
		Image("PetPreviewFrame",17,73,ART+"preview-frame.png"),
		Image("PetPreviewFill",18,74,ART+"preview-fill.png"),
		{"name":"PetPreviewViewport","type":"window","x":18,"y":74,"width":255,"height":172,"style":("not_pick",)},
		Text("PetName",146,82,"","center",14,0xffe5c17b),
		Slot("UpBringing_Pet_Slot",28,108),
		Text("PetSealLabel",44,143,L.PET_ALBUM_SEAL,"center",11),
		Text("LevelTitle",28,217,L.PET_INFORMATION_LEVEL,"left",11),
		Text("LevelValue",78,217),
		Text("AgeValue",264,217,"","right",11),
		Text("EvolName",146,250,"","center"),
		Text("ExpTitle",28,270,L.PET_INFORMATION_EXP,"left",11),
		{"name":"UpBringing_Pet_EXP_Gauge_Board","type":"window","x":173,"y":268,"width":91,"height":19},
		Text("LifeTitle",28,299,L.PET_INFORMATION_LIFE,"left",11),
		Text("LifeTextValue",264,299,"","right",11),
		{"name":"LifeGauge","type":"gauge","x":28,"y":323,"width":236,"color":"red"},
		Button("FeedMainButton",18,452,L.PET_ALBUM_FEED),
		Button("EvolutionMainButton",106,452,L.PET_ALBUM_EVOLVE),
		Button("ReviveMainButton",194,452,L.PET_ALBUM_REVIVE),
		Button("AlbumButton",61,488,L.PET_ALBUM_OPEN,"170x24"),
		Image("AlbumGlyph",87,491,ART+"book-icon-18.png"),
	]
	# Old controller references remain valid; the fifth sprite has a hidden parent.
	legacyExp = {"name":"LegacyExpCarrier","type":"window","x":0,"y":0,"width":0,"height":0,"children":[]}
	for index in range(5):
		legacyExp["children"].append(Image("UpBringing_Pet_EXPGauge_%02d" % (index+1),0,0,"d:/ymir work/ui/pet/exp_gauge/exp_on.sub"))
	old["PetAttrChange_Page"]["children"].append(legacyExp)
	for index,(name,label) in enumerate((("Hp",L.PET_ALBUM_HP),("Def",L.PET_ALBUM_DEF),("Sp",L.PET_ALBUM_SP))):
		y = 340 + index * 19
		page["children"].extend((Text(name+"Title",28,y,label,"left",11),
			Text(name+"Value",264,y,"","right",11,0xff8fcb7c),
			Text(name+"Jump",264,y,"","right",11)))
	for index in range(5):
		page["children"].append(Slot("PetSkillSlot%d" % index,34+index*48,402))
		page["children"].append(Text("PetSkillState%d" % index,50+index*48,437,"","center",9))
