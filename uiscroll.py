import ui, localeInfo
import net
import pack

class ScrollWindow(ui.DragonBoardWithTitleBar):
	def __init__(self):
		ui.DragonBoardWithTitleBar.__init__(self)

		self.itemPos = -1
		self.mapImage = None
		self.pointEffect = None
		self.pointEffect2 = None
		self.warpButton = None
		self.atlasInfo = []
		self.readAtlasInfo()
		self.AddFlag("float")
		self.AddFlag("movable")

	def __del__(self):
		ui.DragonBoardWithTitleBar.__del__(self)

	def readAtlasInfo(self):
		if len(self.atlasInfo) != 0:
			return
		try:
			lines = open("locale/common/atlasinfo.txt", "r").readlines()
		except IOError:
			import dbg
			dbg.LogBox("readAtlasInfo from locale/common/atlasinfo.txt")
			import app
			app.Abort()
		for line in lines:
			try:
				tokens = line.split("\t")
				if len(tokens) != 5:
					continue
				map = []
				map_name = str(tokens[0])
				map.append(map_name)
				global_x = int(tokens[1])
				map.append(global_x)
				global_y = int(tokens[2])
				map.append(global_y)
				map_width = int(tokens[3])
				map.append(map_width)
				map_height = int(tokens[4])
				map.append(map_height)
				global_end_x = global_x + map_width * 25600
				map.append(global_end_x)
				global_end_y = global_y + map_height * 25600
				map.append(global_end_y)
				self.atlasInfo.append(map)
			except:
				import dbg
				dbg.LogBox("readAtlasInfo from uiscroll.py")
				import app
				app.Abort()

	def Destroy(self):
		self.itemPos=0
		self.mapImage=0
		self.itemPos = -1
		self.mapImage = 0
		self.pointEffect = 0
		self.pointEffect2 = 0
		self.warpButton = 0
		self.atlasInfo = 0

	def Close(self):
		self.Hide()

	def CalculatePos(self, x, y):
		for map in self.atlasInfo:
			if x < int(map[1]) or x > int(map[5]) or y < int(map[2]) or y > int(map[6]):
				continue
			return (str(map[0]),x-int(map[1]),y-int(map[2]))
		return None

	def getData(self, mapname):
		for map in self.atlasInfo:
			if map[0] == mapname:
				return map
		return None

	def warpEvent(self):
		self.Close()
		net.SendItemUsePacket(self.itemPos)

	def initMap(self, x, y, pos):
		if self.CalculatePos(x,y) == None:
			self.Close()
			return

		if self.mapImage == None:
			self.mapImage = ui.ExpandedImageBox()
			self.mapImage.SetParent(self)
			self.mapImage.SetPosition(8,30)

		if self.pointEffect==None:
			self.pointEffect = ui.AniImageBox()
			self.pointEffect.SetParent(self.mapImage)
			for j in range(12):
				self.pointEffect.AppendImage("d:/ymir work/ui/minimap/mini_waypoint%d.sub"%int(j+1))
			self.pointEffect.SetDelay(15)

		if self.pointEffect2==None:
			self.pointEffect2 = ui.AniImageBox()
			self.pointEffect2.SetParent(self.mapImage)
			for j in range(15):
				self.pointEffect2.AppendImage("d:/ymir work/ui/minimap/waypoint%d.sub"%int(j+1))
			self.pointEffect2.SetDelay(5)

		if self.warpButton==None:
			self.warpButton = ui.Button()
			self.warpButton.SetParent(self)
			self.warpButton.SetUpVisual("d:/ymir work/ui/game/scroll/btn_teleport_1.png")
			self.warpButton.SetOverVisual("d:/ymir work/ui/game/scroll/btn_teleport_2.png")
			self.warpButton.SetDownVisual("d:/ymir work/ui/game/scroll/btn_teleport_3.png")
			self.warpButton.SetEvent(ui.__mem_func__(self.warpEvent))
			self.warpButton.SetText(localeInfo.WARP_SCROLL_BUTTON)

		(mapname,new_x,new_y) = self.CalculatePos(x,y)
		new_x = (new_x // 100)
		new_y = (new_y // 100)
		self.itemPos = pos

		if pack.Exist("%s/atlas.sub"%mapname):
			self.mapImage.LoadImage("%s/atlas.sub"%mapname)
		elif pack.Exist("d:/ymir work/ui/atlas/%s/atlas.sub"%mapname):
			self.mapImage.LoadImage("d:/ymir work/ui/atlas/%s/atlas.sub"%mapname)
		else:
			self.warpEvent()
			return
		self.mapImage.Show()

		self.SetSize(self.mapImage.GetWidth()+16,self.mapImage.GetHeight()+80-8)

		map = self.getData(mapname)
		if map==None:
			self.Close()
			return

		calculatex = float(self.mapImage.GetWidth())/float(map[3]*256)
		calculatey = float(self.mapImage.GetHeight())/float(map[4]*256)
		new_x = float(new_x)*float(calculatex)-10
		new_y = float(new_y)*float(calculatey)-10

		if mapname in localeInfo.MINIMAP_ZONE_NAME_DICT:
			self.SetTitleName(localeInfo.MINIMAP_ZONE_NAME_DICT[mapname])
		else:
			self.SetTitleName(localeInfo.WARP_SCROLL_UNKNOWN_MAP)


		self.pointEffect.SetPosition(new_x,new_y)
		self.pointEffect.Show()

		self.pointEffect2.SetPosition(new_x-14,new_y-14)
		self.pointEffect2.Show()

		self.warpButton.SetPosition((self.mapImage.GetWidth()//2+2)-(self.warpButton.GetWidth()//2)+5.5,self.mapImage.GetHeight()+40-5.5)
		self.warpButton.Show()

		self.SetCenterPosition()
		self.Show()
