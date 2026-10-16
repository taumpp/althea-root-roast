import dbg
import app
import localeInfo
import wndMgr
import systemSetting
import mouseModule
import networkModule
import uiCandidate
import constInfo
import musicInfo
import stringCommander
import os
import fontconfig

# bind_me(locals().values())

def RunApp():
	musicInfo.LoadLastPlayFieldMusic()

	app.SetHairColorEnable(constInfo.HAIR_COLOR_ENABLE)
	app.SetArmorSpecularEnable(constInfo.ARMOR_SPECULAR_ENABLE)
	app.SetWeaponSpecularEnable(constInfo.WEAPON_SPECULAR_ENABLE)

	fonttype = 0
	if app.ENABLE_FONT_OPTION and os.path.exists("UserData/font/fontoption.cfg"):
		fd = old_open("UserData/font/fontoption.cfg", "r")
		fonttype = fd.readline()
		fd.close()

	fontconfig.ConfigureLevel(fonttype)
	localeInfo.UI_DEF_FONT = fontconfig.FontForRole(fontconfig.ROLE_BODY)
	localeInfo.UI_DEF_FONT_SMALL = fontconfig.FontForRole(fontconfig.ROLE_DENSE)
	localeInfo.UI_DEF_FONT_BOLD = fontconfig.FontForRole(fontconfig.ROLE_CONTROL)
	localeInfo.UI_DEF_FONT_LARGE_BOLD = fontconfig.FontForRole(fontconfig.ROLE_LARGE_BOLD)
	localeInfo.UI_DEF_FONT_LARGE = fontconfig.FONT_LARGE

	app.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetMouseHandler(mouseModule.mouseController)
	wndMgr.SetScreenSize(systemSetting.GetWidth(), systemSetting.GetHeight())

	try:
		if app.ENABLE_DISCORD_STUFF:
			app.Create(localeInfo.APP_TITLE, localeInfo.APP_MINI_TITLE, systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
		else:
			app.Create(localeInfo.APP_TITLE, systemSetting.GetWidth(), systemSetting.GetHeight(), 1)
	except RuntimeError as msg:
		msg = str(msg)
		if "CREATE_DEVICE" == msg:
			dbg.LogBox("Sorry, Your system does not support 3D graphics,\r\nplease check your hardware and system configeration\r\nthen try again.")
		else:
			dbg.LogBox("Metin2.%s" % msg)
		return

	app.SetCamera(1500.0, 30.0, 0.0, 180.0)

	# Gets and sets the floating-point control word
	# app.SetControlFP()

	if not mouseModule.mouseController.Create():
		return

	mainStream = networkModule.MainStream()
	mainStream.Create()

	# mainStream.SetLoadingPhase()
	mainStream.SetLogoPhase()
	# mainStream.SetSelectCharacterPhase()
	# mainStream.SetCreateCharacterPhase()
	# mainStream.SetSelectEmpirePhase()
	# mainStream.SetGamePhase()
	app.Loop()

	mainStream.Destroy()

RunApp()
