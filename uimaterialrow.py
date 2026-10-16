import app
import inventoryshortcutpolicy
import localeInfo
import mouseModule
import player
import ui


class MaterialRow(ui.Window):
	"""A recipe material, including materials absent from the inventory."""

	def __init__(self, tooltip, searchEvent):
		self.tooltip = tooltip
		self.searchEvent = searchEvent
		self.itemVnum = 0
		ui.Window.__init__(self)

	def SetItem(self, vnum):
		self.OnMouseOverOut()
		self.itemVnum = int(vnum)

	def OnMouseOverIn(self):
		if not self.IsShow() or self.itemVnum <= 0 or not self.tooltip:
			return
		self.tooltip.ClearToolTip()
		self.tooltip.AddItemData(
			self.itemVnum,
			[0] * player.METIN_SOCKET_MAX_NUM,
			[(0, 0)] * player.ATTRIBUTE_SLOT_MAX_NUM,
		)
		if getattr(app, "ENABLE_VIRTUAL_MARKET", False) and self.searchEvent:
			self.tooltip.AppendSpace(5)
			self.tooltip.AutoAppendNewTextLineResize(
				"|Ikey/ctrl|i + |Ikey/mouse_left|i - %s"
				% localeInfo.INVENTORY_SHORTCUT_MARKET,
				self.tooltip.TITLE_COLOR,
			)
		self.tooltip.ShowToolTip()

	def OnMouseOverOut(self):
		if self.tooltip:
			self.tooltip.HideToolTip()

	def OnMouseLeftButtonDown(self):
		if (not self.IsShow() or self.itemVnum <= 0 or not self.searchEvent
				or not getattr(app, "ENABLE_VIRTUAL_MARKET", False)
				or mouseModule.mouseController.isAttached()):
			return True
		action = inventoryshortcutpolicy.ResolveLeftClick(
			app.IsPressed(app.DIK_LALT) or app.IsPressed(app.DIK_RALT),
			app.IsPressed(app.DIK_LSHIFT) or app.IsPressed(app.DIK_RSHIFT),
			app.IsPressed(app.DIK_LCONTROL) or app.IsPressed(app.DIK_RCONTROL),
		)
		if action == inventoryshortcutpolicy.ACTION_MARKET:
			self.OnMouseOverOut()
			self.searchEvent(self.itemVnum)
		return True
