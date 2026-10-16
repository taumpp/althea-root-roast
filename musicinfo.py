METIN2THEMA = "M2BG.mp3"

loginMusic = "login_window.mp3"
createMusic = "characterselect.mp3"
selectMusic = "characterselect.mp3"
fieldMusic = METIN2THEMA

def SaveLastPlayFieldMusic():
	global fieldMusic

	try:
		lastPlayFile = old_open("BGM/lastplay.inf", "w")
	except IOError:
		return

	with lastPlayFile:
		lastPlayFile.write(fieldMusic)

def LoadLastPlayFieldMusic():
	global fieldMusic

	try:
		# This is mutable user data, not a signed pack asset. pack.Get only
		# accepts script/text extensions and cannot read this .inf file.
		lastPlayFile = old_open("BGM/lastplay.inf", "r")

	except IOError:
		return

	with lastPlayFile:
		fieldMusic = lastPlayFile.read()
