import app
import os
import ui
import localeInfo
import uiguildv2widgets


GUILD_MARK_WIDTH = 32
GUILD_MARK_HEIGHT = 32
GUILD_MARK_EXTENSIONS = ("png", "tga", "bmp", "jpg", "jpeg")
# Common image types the client cannot read. They are listed with a reason,
# because Windows hides extensions and browsers often save WebP or JFIF.
GUILD_MARK_UNSUPPORTED = ("webp", "jfif", "gif", "avif", "heic", "ico")


def GuildMarkUploadFolder():
	"""The upload folder next to the game executable, as shown to the player."""
	return os.path.join(os.path.dirname(app.GetName()), "upload")


def ListGuildMarkFiles():
	"""Upload candidates sorted by name without duplicates.

	FindFirstFileW also matches 8.3 short names, so one file can be returned by
	more than one filter (photo.jpeg by *.jpg). The real extension decides."""
	known = GUILD_MARK_EXTENSIONS + GUILD_MARK_UNSUPPORTED
	found = {}
	for extension in known:
		for fileName in app.GetFileList("upload/*." + extension):
			if os.path.splitext(fileName)[1][1:].lower() in known:
				found.setdefault(fileName.lower(), fileName)
	return sorted(found.values(), key=lambda fileName: fileName.lower())


def DescribeGuildMarkFile(fileName):
	"""(usable, status) of one candidate, known before anything is uploaded."""
	kind = os.path.splitext(fileName)[1][1:].lower()
	if kind not in GUILD_MARK_EXTENSIONS:
		return False, "Nepodporovaný formát (.%s) — ulož jako PNG" % kind
	canLoad, width, height = app.GetImageInfo("upload/" + fileName)
	if canLoad != 1:
		return False, "Obrázek nelze přečíst — ulož ho znovu jako PNG"
	if (width, height) != (GUILD_MARK_WIDTH, GUILD_MARK_HEIGHT):
		return False, "%d×%d px — musí být %d×%d" % (width, height, GUILD_MARK_WIDTH, GUILD_MARK_HEIGHT)
	return True, "%d×%d px · připraveno k nahrání" % (width, height)


def OpenGuildMarkUploadFolder():
	uploadPath = GuildMarkUploadFolder()
	try:
		if not os.path.isdir(uploadPath):
			os.makedirs(uploadPath)
	except OSError:
		pass
	app.ShellExecute(uploadPath)

class MarkItem(ui.ListBoxEx.Item):
	def __init__(self, fileName):
		ui.ListBoxEx.Item.__init__(self)
		self.fileName = fileName
		self.imgWidth = 0
		self.imgHeight = 0
		self.canLoad = 0
		self.textLine = self.__CreateTextLine(fileName)
		self.imgBox = self.__CreateImageBox("upload/" + fileName)

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)

	def GetText(self):
		# The label may be shortened for display. Upload the original path.
		return self.fileName

	def SetSize(self, width, height):
		ui.ListBoxEx.Item.SetSize(self, 128, 32) ## Blue Zone

	def __CreateTextLine(self, fileName):
		textLine=ui.TextLine()
		textLine.SetParent(self)
		
		textLine.SetPosition(32+4, 0)
		if len(fileName) > 16:
			fileName = fileName[0:16] + ".."
		textLine.SetText(fileName)
		textLine.Show()
		return textLine

	def __CreateImageBox(self, fileName):
		# Only the size is read (stbi_info reads the disk). ImageBox.LoadImage
		# reads packed resources only and raises for an upload-folder file.
		(self.canLoad, self.imgWidth, self.imgHeight)=app.GetImageInfo(fileName)
		return 0

class SymbolItem(ui.ListBoxEx.Item):
	def __init__(self, fileName):
		ui.ListBoxEx.Item.__init__(self)
		self.textLine = self.__CreateTextLine(fileName)
		(self.canLoad, self.imgWidth, self.imgHeight) = app.GetImageInfo("upload/" + fileName)

	def __del__(self):
		ui.ListBoxEx.Item.__del__(self)

	def GetText(self):
		return self.textLine.GetText()

	def SetSize(self, width, height):
		ui.ListBoxEx.Item.SetSize(self, 6 * len(self.textLine.GetText()) + 4, height)

	def __CreateTextLine(self, fileName):
		textLine = ui.TextLine()
		textLine.SetParent(self)
		textLine.SetPosition(1, 2)
		textLine.SetText(fileName)
		textLine.Show()
		return textLine

class PopupDialog(ui.ScriptWindow):
	def __init__(self, parent):
		# print "NEW POPUP WINDOW ------------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)

		self.__Load()
		self.__Bind()

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		# print "---------------------------------------------------------------------------- DELETE POPUP WINDOW"

	def __Load(self):
		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/PopupDialog.py")
		except:
			import exception
			exception.Abort("PopupDialog.__Load")

	def __Bind(self):
		try:
			self.textLine = self.GetChild("message")
			self.okButton = self.GetChild("accept")
		except:
			import exception
			exception.Abort("PopupDialog.__Bind")

		self.okButton.SetEvent(ui.__mem_func__(self.__OnOK))

	def Open(self, msg):
		self.textLine.SetText(msg)
		self.SetCenterPosition()
		self.Show()
		self.SetTop()

	def __OnOK(self):
		self.Hide()

class MarkSelectDialog(object):
	"""Guild mark picker in the guild window style, built on first open.

	Every candidate in the upload folder is listed with its preview and the
	reason it cannot be used, so the player never has to guess."""
	def __init__(self):
		self.selectEvent = None
		self.window = None

	def SAFE_SetSelectEvent(self, event):
		self.selectEvent = ui.__mem_func__(event)

	def Open(self):
		if not self.window:
			self.window = MarkSelectWindow(self)
		self.window.Open()

	def Close(self):
		if self.window:
			self.window.Close()

	def Hide(self):
		self.Close()

	def IsShow(self):
		return bool(self.window and self.window.IsShow())

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Select(self, fileName):
		if self.selectEvent:
			self.selectEvent(fileName)

	def Destroy(self):
		if self.window:
			self.window.Destroy()
			self.window = None
		self.selectEvent = None

class MarkSelectWindow(uiguildv2widgets.Canvas):
	WIDTH, HEIGHT = 580, 500

	def __init__(self, owner):
		w = uiguildv2widgets
		w.Canvas.__init__(self, None, 0, 0, self.WIDTH, self.HEIGHT)
		self.AddFlag("float")
		self.AddFlag("movable")
		self.owner = owner
		self.files = []
		self.selected = None
		self.shell(self.WIDTH, self.HEIGHT, "Znak cechu", ui.__mem_func__(self.Close))
		self.body = w.Canvas(self, 0, 0, self.WIDTH, self.HEIGHT)
		# The full-size content layer must not swallow clicks on the title
		# bar's close button; its own children stay clickable.
		self.body.AddFlag("not_pick")
		self.body.Show()
		self.SetCenterPosition()
		self.Hide()

	def Open(self):
		self.Refresh()
		self.Show()
		self.SetTop()

	def Refresh(self):
		self.files = [(fileName,) + DescribeGuildMarkFile(fileName) for fileName in ListGuildMarkFiles()]
		if self.selected not in [fileName for fileName, usable, status in self.files if usable]:
			self.selected = None
		self.Render()

	def Choose(self, fileName):
		self.selected = fileName
		self.Render()

	def Upload(self):
		fileName = self.selected
		if not fileName:
			return False
		self.Close()
		if self.owner:
			self.owner.Select(fileName)
		return True

	def Render(self):
		w = uiguildv2widgets
		body, width, height = self.body, self.WIDTH, self.HEIGHT
		body.clear()
		folder = GuildMarkUploadFolder()
		body.text(24, 44, "Nahrát znak cechu", width - 48, w.INK, w.ROLE_TITLE)
		body.text(24, 82, "Obrázek 32 × 32 px ve formátu PNG, TGA, BMP nebo JPG. Hledáme ve složce:", width - 48, w.DIM, w.ROLE_CAPTION)
		body.text(24, 102, folder, width - 48, w.GOLD, w.ROLE_CAPTION)
		if self.files:
			body.keep(w.ScrollList(body, 24, 130, width - 48, 262, self.files, 52, self.DrawFile))
		else:
			body.panel(24, 130, width - 48, 262)
			body.block(44, 150, "Ve složce zatím není žádný obrázek.", width - 88, w.GOLD, w.fontconfig.ROLE_CONTROL)
			body.block(44, 180, "Vlož do složky upload obrázek 32 × 32 px ve formátu PNG, TGA, BMP nebo JPG "
				"a klikni na Obnovit. Tlačítko Otevřít složku ji otevře.", width - 88, w.DIM)
			body.block(44, 246, folder, width - 88, w.GOLD, w.ROLE_CAPTION)
		usable = sum(1 for fileName, ok, status in self.files if ok)
		if self.files and not usable:
			body.text(24, height - 66, "Žádný soubor zatím nesplňuje podmínky. Oprav ho podle popisu a klikni na Obnovit.", width - 48, w.GOLD, w.ROLE_CAPTION)
		body.action("Otevřít složku", 24, height - 36, OpenGuildMarkUploadFolder, width=140)
		body.action("Obnovit", 172, height - 36, ui.__mem_func__(self.Refresh), width=110)
		body.button("Nahrát znak", width - 194, height - 36, ui.__mem_func__(self.Upload), bool(self.selected),
			tooltip=None if self.selected else "Vyber obrázek 32 × 32 px")

	def DrawFile(self, canvas, record, y, width):
		w = uiguildv2widgets
		fileName, usable, status = record
		canvas.row(0, y, width, 46, lambda name=fileName: self.Choose(name), fileName == self.selected, enabled=usable)
		canvas.pixel_bar(w.px(10), w.px(y + 7), 34, 34, 0xff4c3d2d)
		# No preview: wndMgr.LoadImage reads only packed resources and raises
		# for a file in the upload folder, which aborted the whole dialog. The
		# released client has no API that draws an arbitrary disk image.
		canvas.pixel_bar(w.px(10) + 1, w.px(y + 7) + 1, 32, 32, 0xff1d2a1c if usable else 0xff110d0b)
		canvas.text(66, y + 6, fileName, width - 80, w.INK if usable else w.MUTED, w.fontconfig.ROLE_CONTROL)
		canvas.text(66, y + 26, status, width - 80, w.GREEN if usable else w.GOLD, w.ROLE_CAPTION)

	def Close(self):
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def Destroy(self):
		self.owner = None
		self.body.Destroy()
		uiguildv2widgets.Canvas.Destroy(self)

class SymbolSelectDialog(ui.ScriptWindow):
	def __init__(self):
		# print "NEW SYMBOL LIST WINDOW ------------------------------------------------------------------------------"
		ui.ScriptWindow.__init__(self)

		self.selectEvent = None
		self.isLoaded = 0

	def __del__(self):
		ui.ScriptWindow.__del__(self)
		# print "---------------------------------------------------------------------------- DELETE SYMBOL LIST WINDOW"

	def Show(self):
		if self.isLoaded == 0:
			self.isLoaded = 1

			self.__Load()

		ui.ScriptWindow.Show(self)

	def Open(self):
		self.Show()

		self.SetCenterPosition()
		self.SetTop()

		if self.symbolListBox.IsEmpty():
			self.__PopupMessage(localeInfo.GUILDMARK_UPLOADER_ERROR_PATH)

	def Close(self):
		self.popupDialog.Hide()
		self.Hide()

	def OnPressEscapeKey(self):
		self.Close()
		return True

	def SAFE_SetSelectEvent(self, event):
		self.selectEvent = ui.__mem_func__(event)

	def __CreateSymbolListBox(self):
		symbolListBox = ui.ListBoxEx()
		symbolListBox.SetParent(self)
		symbolListBox.SetPosition(15, 50)
		symbolListBox.Show()
		return symbolListBox

	def __Load(self):
		self.popupDialog = PopupDialog(self)

		try:
			pyScrLoader = ui.PythonScriptLoader()
			pyScrLoader.LoadScriptFile(self, "UIScript/MarkListWindow.py")
		except:
			import exception
			exception.Abort("SymbolListBox.__Load")

		try:
			self.symbolListBox = self.__CreateSymbolListBox()
			self.symbolListBox.SetScrollBar(self.GetChild("ScrollBar"))

			self.popupText = self.popupDialog.GetChild("message")
			self.popupDialog.GetChild("accept").SetEvent(ui.__mem_func__(self.popupDialog.Hide))

			self.board = self.GetChild("board")
			self.okButton = self.GetChild("ok")
			self.cancelButton = self.GetChild("cancel")
			self.refreshButton = self.GetChild("refresh")
			self.openFolderButton = self.GetChild("open_folder")

		except:
			import exception
			exception.Abort("SymbolListBox.__Bind")

		self.refreshButton.SetEvent(ui.__mem_func__(self.__OnRefresh))
		self.openFolderButton.SetEvent(ui.__mem_func__(self.__OnOpenFolder))
		self.openFolderButton.SetToolTipText(localeInfo.GUILDMARK_UPLOADER_ERROR_PATH)
		self.cancelButton.SetEvent(ui.__mem_func__(self.__OnCancel))
		self.okButton.SetEvent(ui.__mem_func__(self.__OnOK))
		self.board.SetCloseEvent(ui.__mem_func__(self.__OnCancel))
		self.board.SetTitleName(localeInfo.SYMBOLLIST_TITLE)
		self.UpdateRect()

		self.__RefreshFileList()

	def __PopupMessage(self, msg):
		self.popupDialog.Open(msg)

	def __OnOK(self):
		selItem = self.symbolListBox.GetSelectedItem()
		if selItem:
			if selItem.canLoad != 1:
				self.__PopupMessage(localeInfo.GUILDMARK_UPLOADER_ERROR_FILE_FORMAT)
			elif selItem.imgWidth != 64:
				self.__PopupMessage(localeInfo.GUILDMARK_UPLOADER_ERROR_64_WIDTH)
			elif selItem.imgHeight != 128:
				self.__PopupMessage(localeInfo.GUILDMARK_UPLOADER_ERROR_128_HEIGHT)
			else:
				self.selectEvent(selItem.GetText())
				self.Hide()
		else:
			self.__PopupMessage(localeInfo.GUILDMARK_UPLOADER_ERROR_SELECT)

	def __OnCancel(self):
		self.Hide()

	def __OnRefresh(self):
		self.__RefreshFileList()

	def __OnOpenFolder(self):
		OpenGuildMarkUploadFolder()

	def __RefreshFileList(self):
		self.__ClearFileList()
		self.__AppendFileList("jpg")
		self.__AppendFileList("png")

	def __ClearFileList(self):
		self.symbolListBox.RemoveAllItems()

	def __AppendFileList(self, filter):
		fileNameList = app.GetFileList("upload/*." + filter)
		for fileName in fileNameList:
			self.__AppendFile(fileName)

	def __AppendFile(self, fileName):
		self.symbolListBox.AppendItem(SymbolItem(fileName))
