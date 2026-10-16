# -*- coding: utf-8 -*-
"""Shared A crafting window. All limits, selection and debits are server-owned."""
import app
import net
import mouseModule
import stonecrafting
import craftingselection
from craftinglocale import Text as T
from uicrimsonember import SettingsScrollBar
from uimountfeed import IsInventorySource
from weakref import proxy
import item
import player
import nonplayer
import ui
import wndMgr
import uiToolTip
import cube_renewal
import uicrimsoncontrols
import craftingmodel
import dewcatalog
import uicraftingcontrols as controls

INK = 0xffe4d9c9
MUTED = 0xffb3a691
GOLD = 0xffc8aa78
GREEN = 0xffa5c495
RED = 0xffefb197
RULE = 0xff342d24
WindowDestroy = getattr(ui, 'WindowDestroy', lambda function: function)
GROUPS = {'WEAPON': 'Zbraně', 'ARMOR': 'Výzbroj', 'STONE': 'Kameny',
          'BELT': 'Opasky', 'EVENT': 'Události', 'ETC': 'Ostatní'}


class ChangeEdit(ui.EditLine):
    def __init__(self, changed):
        ui.EditLine.__init__(self)
        self.changed = changed

    def OnIMEUpdate(self):
        ui.EditLine.OnIMEUpdate(self)
        self.changed()


class MenuDismiss(ui.Window):
    def __init__(self, close):
        ui.Window.__init__(self, 'TOP_MOST')
        self.close = close

    def OnMouseLeftButtonDown(self):
        self.close()
        return True

    def OnPressEscapeKey(self):
        self.close()
        return True


class CubeRenewalWindows(ui.ScriptWindow):
    def __init__(self):
        ui.ScriptWindow.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(660, 556)
        self.SetCenterPosition()
        self.widgets = []
        self.rows = []
        self.detail = []
        self.menuRows = []
        self.recipes = []
        self.selected = None
        self.category = ''
        self.page = 0
        self.amount = 1
        self.maximum = 0
        self.gold = 0
        self.resultUntil = 0
        self.resultText = ''
        self.owned = (0, 0, 0, 0, 0, 0, 0, 0)
        self.nonce = 0
        self.quotePending = None
        self.quoteAt = 0
        self.nextQuote = 0
        self.pending = None
        self.makeEnabled = None
        self.destroyed = False
        self.basket = craftingselection.Basket()
        self.useAny = True
        self.selectionCapable = False
        self.capNonce = 0
        self.acceptedNonce = 0
        self.selectionNonce = 0
        self.checkEnabled = None
        self.controlEnabled = {}
        self.scrollSyncing = False
        self.listHeight = 400
        self.detailHeight = 304
        self.listContentHeight = 400
        self.detailContentHeight = 304
        self.toolTip = uiToolTip.ItemToolTip()
        self.toolTip.Hide()
        self.dismiss = MenuDismiss(ui.__mem_func__(self.CloseMenu))
        self.dismiss.Hide()
        self._Build()
        cube_renewal.SetCubeRenewalHandler(self)

    def _Keep(self, child, parent, x, y, collection=None):
        child.SetParent(parent)
        child.SetPosition(x, y)
        (self.widgets if collection is None else collection).append(child)
        child.Show()
        return child

    def _Bar(self, parent, x, y, w, h, color, collection=None):
        bar = self._Keep(ui.Bar(), parent, x, y, collection)
        bar.SetSize(w, h)
        bar.SetColor(controls.packed_color(color))
        bar.AddFlag('not_pick')
        return bar

    def _Text(self, parent, x, y, text='', color=INK, font='Tahoma:12', collection=None):
        line = self._Keep(ui.TextLine(), parent, x, y, collection)
        line.SetFontName(font)
        line.SetPackedFontColor(controls.packed_color(color))
        line.SetText(str(text))
        line.AddFlag('not_pick')
        return line

    def _Fit(self, label, text, width):
        label.SetText(text)
        shortened = text
        while label.GetTextSize()[0] > width and shortened:
            shortened = shortened[:-1]
            label.SetText(shortened + '…')

    def _Button(self, parent, x, y, family, text, callback, collection=None):
        button = self._Keep(ui.Button(), parent, x, y, collection)
        uicrimsoncontrols.ApplyVisuals(button, family)
        button.SetSize(*[int(value) for value in family.split('x')])
        button.SetFontName('Tahoma:12')
        button.SetText(text)
        button.SetEvent(ui.__mem_func__(callback) if hasattr(callback, '__self__') else callback)
        return button

    def _FlatButton(self, parent, x, y, width, height, text, callback,
                    collection=None, framed=True, left=False):
        return self._Keep(controls.FlatButton(width, height, text, ui.__mem_func__(callback) if hasattr(callback, '__self__') else callback, framed, left),
                          parent, x, y, collection)

    def _Build(self):
        owner = proxy(self)
        self.board = self._Keep(ui.BoardWithTitleBar(), self, 0, 0)
        self.board.AddFlag('attach')
        self.board.SetSize(660, 556)
        self.board.SetTitleName(T('TITLE'))
        self.board.SetCloseEvent(ui.__mem_func__(self.Close))
        self._Bar(self, 207, 35, 1, 501, RULE)
        self.categoryButton = self._FlatButton(self, 20, 36, 174, 25, T('ALL'),
                                               self.ToggleMenu, left=True)
        self.categoryButton.SetArrow(False)
        self._Keep(controls.Field(174, 25), self, 20, 70)
        self.search = self._Keep(ChangeEdit(ui.__mem_func__(self.Filter)), self, 28, 75)
        self.search.SetSize(158, 16)
        self.search.SetMax(40)
        self.search.SetFontName('Tahoma:12')
        self.search.SetInfoMessage(T('SEARCH'))
        self.search.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
        self.listViewport = self._Keep(ui.Window(), self, 20, 109)
        self.listViewport.SetSize(160, self.listHeight)
        self.listViewport.EnableScissorRect()
        self.listViewport.OnMouseWheel = ui.__mem_func__(self.OnListWheel)
        self.listContent = self._Keep(ui.Window(), self.listViewport, 0, 0)
        self.listContent.SetSize(160, self.listHeight)
        self.listContent.OnMouseWheel = ui.__mem_func__(self.OnListWheel)
        self.listScroll = self._Keep(SettingsScrollBar(), self, 182, 109)
        self.listScroll.SetScrollBarSize(self.listHeight)
        self.listScroll.SetScrollEvent(ui.__mem_func__(self.ScrollList))
        self.listScroll.OnMouseWheel = ui.__mem_func__(self.OnListWheel)
        self.listScroll.Hide()
        self._Bar(self, 20, 510, 174, 1, RULE)
        self.recipeCount = self._Text(self, 20, 522, '', MUTED, 'Tahoma:11')
        self.heroBackground = self._Bar(self, 220, 36, 424, 56, 0xff11110f)
        self.name = self._Text(self, 272, 46, '', INK, 'Tahoma:14')
        self.outputCount = self._Text(self, 272, 69, '', MUTED)
        self.materialCaption = self._Text(self, 220, 106, T('MATERIALS'), GOLD)
        self.countCaption = self._Text(self, 628, 108, T('COUNTS'), MUTED, 'Tahoma:11')
        self.countCaption.SetHorizontalAlignRight()
        self.checkArea = self._Keep(ui.Window(), self, 335, 103)
        self.checkArea.SetSize(166, 24)
        self.checkArea.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.ToggleUseAny))
        self.check = self._Keep(ui.Button(), self.checkArea, 0, 3)
        self.check.SetEvent(ui.__mem_func__(self.ToggleUseAny))
        self._Text(self.checkArea, 21, 5, T('USE_ANY'))
        self.checkArea.Hide()
        self.detailViewport = self._Keep(ui.Window(), self, 220, 129)
        self.detailViewport.SetSize(410, self.detailHeight)
        self.detailViewport.EnableScissorRect()
        self.detailViewport.OnMouseWheel = ui.__mem_func__(self.OnDetailWheel)
        self.detailContent = self._Keep(ui.Window(), self.detailViewport, 0, 0)
        self.detailContent.SetSize(410, self.detailHeight)
        self.detailContent.OnMouseWheel = ui.__mem_func__(self.OnDetailWheel)
        self.detailScroll = self._Keep(SettingsScrollBar(), self, 632, 129)
        self.detailScroll.SetScrollBarSize(self.detailHeight)
        self.detailScroll.SetScrollEvent(ui.__mem_func__(self.ScrollDetail))
        self.detailScroll.OnMouseWheel = ui.__mem_func__(self.OnDetailWheel)
        self.detailScroll.Hide()
        self._Bar(self, 220, 448, 424, 1, RULE)
        self.chanceCaption = self._Text(self, 220, 460, T('CHANCE'), MUTED)
        self.chance = self._Text(self, 263, 460, '', GOLD)
        self.cost = self._Text(self, 644, 460, '', GOLD)
        self.cost.SetHorizontalAlignRight()
        self.quantityLabel = self._Text(self, 220, 482, '', MUTED, 'Tahoma:11')
        self._Text(self, 220, 513, T('QUANTITY'), MUTED)
        self.minus = self._Button(self, 261, 507, '26x24', u'\u2212',
                                  lambda r=owner: r.SetAmount(r.amount-1))
        self.inputArea = self._Keep(ui.Window(), self, 290, 507)
        self.inputArea.SetSize(40, 24)
        self._Keep(controls.Field(40, 24), self.inputArea, 0, 0)
        self.input = self._Keep(ChangeEdit(ui.__mem_func__(self.InputChanged)), self.inputArea, 4, 4)
        self.input.SetSize(32, 17)
        self.input.SetFontName('Tahoma:13')
        self.input.SetPackedFontColor(controls.packed_color(INK))
        self.input.SetMax(4)
        self.input.SetNumberMode()
        self.input.SetText('1')
        self.inputArea.SetOnMouseLeftButtonUpEvent(ui.__mem_func__(self.input.SetFocus))
        self.input.SetReturnEvent(ui.__mem_func__(self.CommitInput))
        self.input.SetEscapeEvent(ui.__mem_func__(self.OnPressEscapeKey))
        self.plus = self._Button(self, 333, 507, '26x24', '+',
                                 lambda r=owner: r.SetAmount(r.amount+1))
        self.maxButton = self._Button(self, 365, 507, '80x24', 'Max: ...',
                                      lambda r=owner: r.SetAmount(r.maximum))
        self.make = self._Button(self, 474, 507, '170x24', T('MAKE') % 1, self.Make)
        self.menu = self._Keep(ui.Window(), self.dismiss, 20, 62)
        self.CloseMenu()
        self._Controls()

    def _Clear(self, collection):
        # Native UI parenting requires a real window. Hide before releasing our
        # references; Window.__del__ owns native destruction and detachment.
        for widget in collection:
            widget.Hide()
        del collection[:]

    def BINARY_CUBE_RENEWAL_LOADING(self):
        if self.destroyed:
            return
        # Invalidate the previous NPC before any rebuild can fail. Indices are
        # local to each NPC: index 0 at Soon is not index 0 at the alchemist.
        self._ResetCatalogue()
        recipes = []
        if not hasattr(cube_renewal, 'GetRecipe'):
            return
        for index in range(cube_renewal.CountDates()):
            recipe = cube_renewal.GetRecipe(index)
            if not recipe or recipe['count'] <= 0:
                continue
            item.SelectItem(recipe['vnum'])
            recipe['name'] = item.GetItemName()
            recipe['height'] = item.GetItemSize()[1]*32
            # The native inventory supports up to three vertical cells.
            if recipe['height'] > 96:
                continue
            raw = recipe['category'].upper()
            if item.GetItemType() == getattr(item, 'ITEM_TYPE_BELT', -1):
                raw = 'BELT'
            elif item.GetItemType() == item.ITEM_TYPE_USE and item.GetItemSubType() in (
                    getattr(item, 'USE_POTION', -1), getattr(item, 'USE_POTION_NODELAY', -2),
                    getattr(item, 'USE_POTION_CONTINUE', -3)):
                raw = 'POTION'
            recipe['group'] = dewcatalog.GROUPS.get(raw, {'POTION':'Lektvary'}.get(raw, GROUPS.get(raw, 'Ostatní')))
            if raw in ('ARMOR','ETC') and item.GetItemType()==getattr(item,'ITEM_TYPE_ARMOR',-1):
                for subtype in ('BODY','HEAD','SHIELD','WRIST','FOOTS','NECK','EAR','GLOVE','PENDANT'):
                    if item.GetItemSubType()==getattr(item,'ARMOR_'+subtype,-1):
                        recipe['group']=T('ARMOR_'+subtype)
                        break
            elif raw=='ETC' and item.GetItemType()==getattr(item,'ITEM_TYPE_COSTUME',-1):
                recipe['group']=T('COSTUMES')
            recipes.append(recipe)
        self.recipes = recipes
        if self.IsDewCatalogue():
            # Open on every family the server sent (ALTHEA-627). Preselecting
            # the first family hid all other colours behind the menu.
            self.board.SetTitleName('Výroba ros')
        else:
            self.board.SetTitleName('Výroba • '+nonplayer.GetMonsterName(recipes[0]['npc'])
                                    if recipes else 'Výroba')
        self.Filter()

    def IsDewCatalogue(self):
        return bool(self.recipes and self.recipes[0]['npc'] == dewcatalog.CATALOGUE)

    def _ResetCatalogue(self):
        self.basket.clear()
        self.useAny = True
        self.selectionCapable = False
        self.acceptedNonce = 0
        self.selectionNonce = 0
        self.capNonce = 0
        self.pending = None
        self.quotePending = None
        self.quoteAt = 0
        self.nextQuote = 0
        self.selected = None
        self.recipes = []
        self.category = ''
        self.page = 0
        self.amount = 1
        self.maximum = 0
        self.gold = 0
        self.owned = (0, 0, 0, 0, 0, 0, 0, 0)
        self.resultUntil = 0
        self.resultText = ''
        self.CloseMenu()
        self.HideTooltip()
        self.categoryButton.SetText(T('ALL'))
        self.search.SetText('')
        self.input.SetText('1')
        self.board.SetTitleName('Výroba')
        for collection in (self.rows, self.detail, self.menuRows):
            self._Clear(collection)
        self.name.SetText(T('NO_RECIPES'))
        self.chance.SetText('')
        self.chanceCaption.Hide()
        self.cost.SetText('')
        self.listScroll.Hide()
        self.detailScroll.Hide()
        self._Controls()

    def Show(self):
        if self.destroyed:
            return
        self.amount = 1
        self.input.SetText('1')
        self.pending = None
        self.quotePending = None
        self.quoteAt = 0
        self.CloseMenu()
        ui.ScriptWindow.Show(self)
        self.nonce = self.nonce%2147483646+1
        self.capNonce = self.nonce
        net.SendChatPacket('/cube select_capability %d' % self.capNonce)
        self.SetTop()
        if self.recipes:
            if self.selected is None:
                self.SelectRecipe(self.recipes[0])
            else:
                self.SelectRecipe(self.selected)
        else:
            self._ResetCatalogue()

    def Filter(self):
        if self.pending:
            return
        self.page = 0
        self.RenderList(select_first=True)

    def ChangePage(self, delta):
        if not self.pending:
            self.listScroll.SetPos(self.listScroll.GetPos()+delta*0.25)
            self.RenderList()

    def RenderList(self, select_first=False):
        self._Clear(self.rows)
        needle = craftingmodel.search_key(self.search.GetText())
        shown = [r for r in self.recipes if (not self.category or r['group']==self.category)
                 and (not needle or needle in craftingmodel.search_key(r['name']))]
        if select_first:
            self.SelectRecipe(shown[0] if shown else None, redraw=False)
            self.listScroll.SetPos(0, False)
        owner = proxy(self)
        y = 0
        for recipe in shown:
            height = max(38, recipe['height']+6)
            row = self._Keep(ui.Window(), self.listContent, 0, y, self.rows)
            row.SetSize(160, height)
            row.OnMouseWheel = ui.__mem_func__(self.OnListWheel)
            if self.selected and recipe['index']==self.selected['index']:
                self._Bar(row, 0, 0, 160, height-2, 0xff302123, self.rows)
                self._Bar(row, 0, 0, 2, height-2, 0xffa75059, self.rows)
            callback = lambda value=recipe,r=owner: r.SelectRecipe(value)
            self._Icon(row, recipe['vnum'], 6, 3, self.rows, callback)
            text = self._Text(row, 46, (height-14)//2, '',
                              INK if self.selected is recipe else MUTED, collection=self.rows)
            self._Fit(text, recipe['name'], 110)
            row.SetOnMouseLeftButtonUpEvent(callback)
            row.OnMouseOverIn = lambda v=recipe['vnum'],r=owner: r.Tooltip(v)
            row.OnMouseOverOut = ui.__mem_func__(self.HideTooltip)
            y += height
        self.listContentHeight = max(self.listHeight,y)
        self.listContent.SetSize(160,self.listContentHeight)
        self.recipeCount.SetText(T('RECIPES') % len(shown))
        self.LayoutScroll(self.listScroll,self.listContentHeight,self.listHeight)
        if select_first:
            self.listScroll.SetPos(0)
        self.ScrollList()

    def _Icon(self, parent, vnum, x, y, collection, selected=None, material_index=None):
        item.SelectItem(vnum)
        height = item.GetItemSize()[1]*32
        slot = self._Keep(ui.SlotWindow(), parent, x, y, collection)
        slot.SetSize(32, height)
        slot.AppendSlot(0, 0, 0, 32, height)
        slot.SetSlotBaseImage('d:/ymir work/ui/slot.png', 1.0, 1.0, 1.0, 1.0)
        slot.SetItemSlot(0, vnum, 0)
        owner = proxy(self)
        slot.SetOverInItemEvent(lambda unused,r=owner: r.Tooltip(vnum, material_index))
        slot.SetOverOutItemEvent(ui.__mem_func__(self.HideTooltip))
        if selected:
            slot.SetSelectItemSlotEvent(lambda unused, callback=selected: callback())
        slot.RefreshSlot()
        return slot

    def SelectRecipe(self, recipe, redraw=True):
        if self.pending:
            return
        if recipe is not None and not any(recipe is current for current in self.recipes):
            return
        self.basket.clear()
        self.useAny = True
        self.acceptedNonce = 0
        self.selectionNonce = 0
        self.selected = recipe
        if recipe and self.selectionCapable:
            self.useAny = not any(self.ManualMaterial(i) for i,(v,n) in enumerate(recipe['materials']) if v and n)
        self.resultUntil = 0
        self.amount = 1
        self.maximum = 0
        self.input.SetText('1')
        self.quotePending = None
        self.quoteAt = 0
        self.owned = (0, 0, 0, 0, 0, 0, 0, 0)
        self.HideTooltip()
        self.DrawDetail()
        if redraw:
            self.RenderList()
        if self.IsShow():
            self.RequestQuote()

    def DrawDetail(self):
        self._Clear(self.detail)
        recipe = self.selected
        if not recipe:
            self.name.SetText(T('NO_RECIPES'))
            self.outputCount.SetText('')
            self.chance.SetText('')
            self.cost.SetText('')
            self.chanceCaption.Hide()
            self.checkArea.Hide()
            self._Controls()
            return
        self.chanceCaption.Show()
        self._Fit(self.name,recipe['name'],362)
        hero_height = max(56,recipe['height']+16)
        dew_info = dewcatalog.get(recipe['vnum'])
        if dew_info:
            hero_height = max(hero_height,72)
        self.heroBackground.SetSize(424,hero_height)
        self._Icon(self,recipe['vnum'],230,36+(hero_height-recipe['height'])//2,self.detail)
        self.outputCount.SetText(T('OUTPUT' if recipe['chance']==100 else 'OUTPUT_UPTO') % (recipe['count']*self.amount))
        if dew_info:
            dew,tier = dew_info
            value = dewcatalog.effective_value(dew['values'][tier],dewcatalog.player_rank())
            label = self._Text(self,272,88,'',GOLD,'Tahoma:11',self.detail)
            self._Fit(label,dew['effect']+' +%d%s' % (value,dew['unit']),362)
        top = 36+hero_height+37
        self.materialCaption.SetPosition(220,top-23)
        self.countCaption.SetPosition(628,top-21)
        self.checkArea.SetPosition(335,top-26)
        manual = any(self.ManualMaterial(i) for i,(v,n) in enumerate(recipe['materials']) if v and n)
        self.checkArea.Show() if manual else self.checkArea.Hide()
        self.PaintCheckbox()
        self.countCaption.SetText(T('SELECTED_COUNTS') if manual and not self.useAny else T('COUNTS'))
        self.detailHeight = 437-top
        self.detailViewport.SetPosition(220,top)
        self.detailViewport.SetSize(410,self.detailHeight)
        self.detailScroll.SetPosition(632,top)
        self.detailScroll.SetScrollBarSize(self.detailHeight)
        y = 0
        owner = proxy(self)
        for index,(vnum,need) in enumerate(recipe['materials']):
            if not vnum or need<=0:
                continue
            item.SelectItem(vnum)
            icon_height = item.GetItemSize()[1]*32
            name = self.MaterialName(index,vnum)
            head = max(38,icon_height+6)
            rows = [row for row in self.basket.sources if row['material']==index]
            expanded = self.ManualMaterial(index) and not self.useAny
            grid_rows = max(1,(len(rows)+1+5)//6)
            height = head+(grid_rows*(icon_height+4)+8 if expanded else 0)
            parent = self._Keep(ui.Window(),self.detailContent,0,y,self.detail)
            parent.SetSize(410,height)
            parent.OnMouseWheel = ui.__mem_func__(self.OnDetailWheel)
            have = self.owned[index]
            required = need*self.amount
            self._Bar(parent,0,0,410,height-2,0xff11110f if have>=required else 0xff201510,self.detail)
            drop = lambda i=index,r=owner: r.DropMaterial(i)
            slot = self._Icon(parent,vnum,8,(head-icon_height)//2,self.detail,
                              drop if self.ManualMaterial(index) else None,index)
            if self.ManualMaterial(index):
                slot.SetSelectEmptySlotEvent(lambda unused,i=index,r=owner:r.DropMaterial(i))
            label = self._Text(parent,49,(head-14)//2,'',INK,collection=self.detail)
            self._Fit(label,name,240)
            count = self._Text(parent,400,(head-14)//2,
                              self.ShortCount(have)+' / '+self.ShortCount(required),
                              GREEN if have>=required else RED,collection=self.detail)
            count.SetHorizontalAlignRight()
            if expanded:
                for cell in range(grid_rows*6):
                    source = rows[cell] if cell<len(rows) else None
                    grid = self._Keep(ui.SlotWindow(),parent,10+(cell%6)*36,
                                     head+3+(cell//6)*(icon_height+4),self.detail)
                    grid.SetSize(32,icon_height)
                    grid.AppendSlot(0,0,0,32,icon_height)
                    grid.SetSlotBaseImage('d:/ymir work/ui/slot.png',1.,1.,1.,1.)
                    if source:
                        grid.SetItemSlot(0,source['vnum'],source['count'] if source['count']>1 else 0)
                        grid.SetSelectItemSlotEvent(lambda unused,row=source,i=index,r=owner:r.ClickSource(row,i))
                        grid.SetUnselectItemSlotEvent(lambda unused,row=source,r=owner:r.RemoveSource(row))
                        grid.SetOverInItemEvent(lambda unused,row=source,r=owner:r.SourceTooltip(row))
                        grid.SetOverOutItemEvent(ui.__mem_func__(self.HideTooltip))
                    else:
                        grid.SetSelectEmptySlotEvent(lambda unused,i=index,r=owner:r.DropMaterial(i))
                    grid.RefreshSlot()
            y += height
        self.detailContentHeight = max(self.detailHeight,y)
        self.detailContent.SetSize(410,self.detailContentHeight)
        self.LayoutScroll(self.detailScroll,self.detailContentHeight,self.detailHeight)
        self.ScrollDetail()
        self.chance.SetText('%d %%' % recipe['chance'])
        self.cost.SetText('{:,} Yang'.format(recipe['gold']*self.amount).replace(',', ' '))
        self.cost.SetPackedFontColor(controls.packed_color(GOLD if recipe['gold']*self.amount<=self.gold else RED))
        self._Controls()

    def _DrawExtendedDetail(self, recipe, materials):
        self.DrawDetail()

    @staticmethod
    def ShortCount(count):
        if count >= 1000000:
            return ('%.1fM' % (count/1000000.0)).replace('.', ',')
        if count >= 10000:
            return ('%.1fk' % (count/1000.0)).replace('.', ',')
        return str(count)

    def SetAmount(self, value):
        if self.pending:
            return
        self.amount = craftingmodel.quantity(value, self.maximum)
        self.input.SetText(str(self.amount))
        self.DrawDetail()

    def InputChanged(self):
        if self.pending:
            self.input.SetText(str(self.amount))
            return
        self.amount = craftingmodel.quantity(self.input.GetText(), self.maximum)
        if self.input.GetText() and self.input.GetText() != str(self.amount):
            self.input.SetText(str(self.amount))
            self.input.SetEndPosition()
        self.DrawDetail()

    def CommitInput(self):
        self.SetAmount(self.input.GetText())
        self.input.KillFocus()

    def RequestQuote(self):
        if not self.selected or self.pending or self.quotePending or not self.IsShow():
            return
        if self.basket.prune(self.InventorySource):
            self.selectionNonce = 0
            self.quoteAt = 0
            self.maximum = 0
            self.DrawDetail()
        self.nonce = self.nonce%2147483646+1
        self.quotePending = (self.nonce,app.GetTime())
        if self.selectionCapable and not self.useAny:
            if not self.selectionNonce:
                self.selectionNonce = self.nonce
                net.SendChatPacket('/cube select_begin %d %d' % (self.selected['wire_index'],self.selectionNonce))
                for row in self.basket.sources:
                    net.SendChatPacket('/cube select_add %d %d %d %d %d %d' %
                        (self.selectionNonce,row['window'],row['cell'],row['vnum'],row['count'],row['id']))
            net.SendChatPacket('/cube select_quote %d %d' % (self.selectionNonce,self.nonce))
        elif not cube_renewal.RequestQuote(self.selected['index'],self.nonce):
            self.quotePending = None
        self.nextQuote = app.GetTime()+1.0

    def BINARY_CRAFTING_QUOTE(self, nonce, wire_index, maximum, gold, owned):
        if self.destroyed or not self.IsShow() or not self.selected or self.pending:
            return
        if not self.quotePending or nonce!=self.quotePending[0] or wire_index!=self.selected['wire_index']:
            return
        self.acceptedNonce = nonce
        self.quotePending = None
        self.quoteAt = app.GetTime()
        unchanged = self.owned == owned and self.gold == gold and self.amount == craftingmodel.quantity(self.amount, maximum)
        self.maximum = max(0, min(2000, maximum))
        self.owned = owned
        self.gold = gold
        self.amount = craftingmodel.quantity(self.amount, self.maximum)
        if not self.input.IsFocus():
            self.input.SetText(str(self.amount))
        if unchanged:
            self._Controls()
        else:
            self.DrawDetail()

    def _Controls(self):
        # Keep short quantities centred without changing the field's hitbox.
        width = min(32, self.input.GetTextSize()[0])
        self.input.SetPosition((40-width)//2, max(0,(24-self.input.GetTextSize()[1])//2))
        self.input.SetSize(max(1, width), 17)
        ready = self.selected is not None and self.quoteAt>0 and app.GetTime()-self.quoteAt<3 and not self.pending
        self.maxButton.SetText('Max: %d' % self.maximum if self.quoteAt else 'Max: …')
        self.make.SetText(T('WAIT') if self.pending else T('MAKE') % self.amount)
        for control, enabled in ((self.minus,ready and self.amount>1), (self.plus,ready and self.amount<self.maximum),
                                 (self.maxButton,ready and self.maximum>0)):
            if self.controlEnabled.get(control)!=enabled:
                control.Enable() if enabled else control.Disable()
                self.controlEnabled[control]=enabled
        # Native Button.Enable resets an in-progress mouse press. Refresh its
        # availability only on transitions, not on every frame/quote update.
        make_enabled = ready and self.maximum>=self.amount
        if make_enabled != self.makeEnabled:
            self.make.Enable() if make_enabled else self.make.Disable()
            self.makeEnabled = make_enabled
        if not self.selected:
            self.quantityLabel.SetText('Počet kusů')
            return
        if self.resultUntil > app.GetTime():
            label = self.resultText
        elif self.selected.get('level', 0) and player.GetStatus(player.LEVEL) < self.selected['level']:
            label = u'Vy\u017eaduje \u00farove\u0148 %d.' % self.selected['level']
        elif self.quoteAt and self.maximum == 0:
            label = T('MISSING') if any(self.owned[i]<n*self.amount for i,(v,n) in enumerate(self.selected['materials']) if v and n) else T('NO_SPACE')
        elif not ready and not self.pending:
            label = ''
        else:
            label = ''
        self._Fit(self.quantityLabel, label, 272)

    def Make(self):
        self.CommitInput()
        if self.pending or not self.selected or self.maximum<self.amount or not self.quoteAt or app.GetTime()-self.quoteAt>=3:
            return
        self.CloseMenu()
        if self.selectionCapable and not self.useAny:
            if not self.acceptedNonce or any(not row['id'] for row in self.basket.sources):
                return
            net.SendChatPacket('/cube select_make %d %d' % (self.selectionNonce,self.amount))
            submitted = True
        else:
            submitted = cube_renewal.MakeBatch(self.selected['index'],self.amount)
        if submitted:
            self.pending = (self.selected['wire_index'],app.GetTime())
            self._Controls()

    def BINARY_CRAFTING_RESULT(self, wire_index, attempted, succeeded):
        if self.destroyed or not self.IsShow() or not self.pending or self.pending[0]!=wire_index:
            return
        self.pending = None
        self.quotePending = None
        self.quoteAt = 0
        self.selectionNonce = 0
        self.acceptedNonce = 0
        if attempted:
            self.basket.refresh_after_make(self.InventorySource)
        self.resultUntil = app.GetTime()+4
        self.resultText = 'Vyrobeno %d ks z %d pokusů' % (succeeded*self.selected['count'], attempted)
        self.amount = 1
        self.input.SetText('1')
        self.DrawDetail()
        self.RequestQuote()

    def BINARY_CUBE_RENEWAL_UPDATE(self):
        self.nextQuote = 0

    def ToggleMenu(self):
        if self.pending:
            return
        if self.menu.IsShow():
            self.CloseMenu()
            return
        self._Clear(self.menuRows)
        groups = ['']+([d['name_cz'] for d in dewcatalog.DEWS] if self.IsDewCatalogue()
                       else sorted(set(r['group'] for r in self.recipes)))
        self.menu.SetSize(151, len(groups)*26+7)
        self._Bar(self.menu, 0, 0, 151, len(groups)*26+7, 0xff171410, self.menuRows)
        self.menuRows.extend(controls.border(self.menu, 151, len(groups)*26+7, 0xff806a48))
        for i, group in enumerate(groups):
            count = sum(not group or r['group']==group for r in self.recipes)
            row = self._FlatButton(self.menu, 3, 4+i*26, 145, 25, '',
                                   lambda g=group,r=proxy(self): r.SelectCategory(g), self.menuRows,
                                   framed=False)
            row.SetSelected(group == self.category)
            self._Text(row, 21, 5, group or 'Vše', INK if group==self.category else MUTED,
                       collection=self.menuRows)
            total = self._Text(row, 136, 5, str(count), GOLD if group==self.category else MUTED,
                               'Tahoma:11', self.menuRows)
            total.SetHorizontalAlignRight()
            if group == self.category:
                self._Text(row, 4, 4, '✓', GOLD, collection=self.menuRows)
        self.dismiss.SetSize(wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight())
        self.dismiss.Show()
        self.dismiss.SetTop()
        x, y = self.GetGlobalPosition()
        self.menu.SetPosition(max(0, min(x+20, wndMgr.GetScreenWidth()-151)),
                              max(0, min(y+62, wndMgr.GetScreenHeight()-self.menu.GetHeight())))
        self.menu.Show()
        self.menu.SetTop()
        self.categoryButton.SetArrow(True)

    def CloseMenu(self):
        if hasattr(self, 'menu'):
            self.menu.Hide()
        if hasattr(self, 'categoryButton'):
            self.categoryButton.SetArrow(False)
        self.dismiss.Hide()

    def SelectCategory(self, group):
        self.category = group
        self.categoryButton.SetText(group or 'Vše')
        self.CloseMenu()
        self.Filter()

    def Tooltip(self, vnum, material_index=None):
        if self.selected and material_index is not None and self.selected['vnum'] in (79620,79633) and vnum in (28030,28430):
            self.toolTip.ClearToolTip()
            self.toolTip.AutoAppendTextLine('Staré kameny +4' if vnum==28430 else 'Staré kameny +0 až +3')
            self.toolTip.AutoAppendTextLine('Lze kombinovat různé druhy. Nové kameny se nepočítají.')
            self.toolTip.AlignHorizonalCenter()
            self.toolTip.ShowToolTip()
        else:
            self.toolTip.SetItemToolTip(vnum)
        if self.selected and material_index is not None:
            self.toolTip.AutoAppendTextLine('Mám %d / potřebuji %d' % (self.owned[material_index], self.selected['materials'][material_index][1]*self.amount))
            self.toolTip.AlignTextLineHorizonalCenter()
            self.toolTip.ShowToolTip()
        elif self.selected and vnum == self.selected['vnum'] and self.selected['copy']:
            self.toolTip.AutoAppendTextLine('Bonusy se přenesou z použitého předmětu.')
            self.toolTip.AlignTextLineHorizonalCenter()
            self.toolTip.ShowToolTip()

    def HideTooltip(self):
        if self.toolTip:
            self.toolTip.Hide()

    def OnUpdate(self):
        if not self.IsShow() or self.destroyed:
            return
        now = app.GetTime()
        if self.pending:
            if now-self.pending[1]>10:
                self.quantityLabel.SetText('Čekám na výsledek. Znovu otevři výrobu.')
            return
        if self.quotePending and now-self.quotePending[1]>4:
            self.quotePending = None
        if now>=self.nextQuote:
            self.RequestQuote()
        self._Controls()

    def Close(self):
        if self.destroyed:
            return
        was_open = self.IsShow()
        self.HideTooltip()
        self.CloseMenu()
        self.search.KillFocus()
        self.input.KillFocus()
        self.pending = None
        self.quotePending = None
        self.quoteAt = 0
        self.selected = None
        self.Hide()
        self._ResetCatalogue()
        if was_open:
            cube_renewal.CubeRenewalClose()

    @WindowDestroy
    def Destroy(self):
        if self.destroyed:
            return
        self.Close()
        self.destroyed = True
        self.listScroll.Destroy()
        self.detailScroll.Destroy()
        self.controlEnabled.clear()
        cube_renewal.SetCubeRenewalHandler(None)
        for collection in (self.rows,self.detail,self.menuRows,self.widgets):
            self._Clear(collection)
        self.toolTip = None
        self.dismiss.Hide()
        self.dismiss = None

    def LayoutScroll(self, bar, total, visible):
        self.scrollSyncing = True
        try:
            bar.SetMiddleBarSize(max(20.0/visible,float(visible)/total))
            bar.SetScrollStep(min(1.,38./max(1,total-visible)))
            bar.SetPos(bar.GetPos(),False)
            bar.Show() if total>visible else bar.Hide()
        finally:
            self.scrollSyncing = False

    def ScrollList(self):
        if not self.scrollSyncing:
            offset=int(max(0,self.listContentHeight-self.listHeight)*self.listScroll.GetPos())
            self.listContent.SetPosition(0,-offset)

    def ScrollDetail(self):
        if not self.scrollSyncing:
            offset=int(max(0,self.detailContentHeight-self.detailHeight)*self.detailScroll.GetPos())
            self.detailContent.SetPosition(0,-offset)

    def OnListWheel(self, delta):
        if self.listScroll.IsShow() and delta:
            self.listScroll.OnUp() if delta>0 else self.listScroll.OnDown()
            return True
        return False

    def OnDetailWheel(self, delta):
        if self.detailScroll.IsShow() and delta:
            self.detailScroll.OnUp() if delta>0 else self.detailScroll.OnDown()
            return True
        return False

    def OnMouseWheel(self, delta):
        x,y=wndMgr.GetMousePosition()
        left,top=self.GetGlobalPosition()
        if x<left+207:
            return self.OnListWheel(delta)
        return self.OnDetailWheel(delta)

    def ManualMaterial(self, index):
        if not self.selected:
            return False
        vnum,need=self.selected['materials'][index]
        if not vnum or need<=0:
            return False
        if len(stonecrafting.MaterialVnums(self.selected['vnum'],vnum))>1:
            return True
        item.SelectItem(vnum)
        return vnum==self.selected['copy'] or item.GetItemType() in tuple(
            getattr(item,'ITEM_TYPE_'+name,-1) for name in ('WEAPON','ARMOR','BELT','COSTUME'))

    def MaterialName(self, index, vnum):
        group=stonecrafting.MaterialGroupKey(self.selected['vnum'],vnum)
        if group:
            return T('OLD_FOUR' if group=='STONE_CRAFT_OLD_FOUR' else 'OLD_LOW')
        item.SelectItem(vnum)
        return item.GetItemName()

    def PaintCheckbox(self):
        path='d:/ymir work/ui/game/crimson_ember/gameoption/checkbox_'
        state='selected' if self.useAny else 'unselected'
        self.check.SetUpVisual(path+state+'.tga')
        self.check.SetOverVisual(path+('selected' if self.useAny else 'hover')+'.tga')
        self.check.SetDownVisual(path+'selected.tga')
        enabled=self.selectionCapable and not self.pending
        if self.checkEnabled!=enabled:
            self.check.Enable() if enabled else self.check.Disable()
            self.checkEnabled=enabled

    def ToggleUseAny(self):
        if self.pending or not self.selectionCapable:
            return
        self.useAny=not self.useAny
        self.SelectionChanged()

    def SelectionChanged(self):
        self.quotePending=None
        self.quoteAt=0
        self.acceptedNonce=0
        self.selectionNonce=0
        self.maximum=0
        self.nextQuote=0
        self.HideTooltip()
        self.DrawDetail()
        self.RequestQuote()

    @staticmethod
    def InventorySource(window, cell):
        return player.GetItemIndex(window,cell),player.GetItemCount(window,cell)

    def DropMaterial(self, index):
        if self.pending or not self.selectionCapable or not self.ManualMaterial(index):
            return
        mouse=mouseModule.mouseController
        if not mouse.isAttached():
            return
        cell=mouse.GetAttachedSlotNumber()
        # Reuse the live normal/special source routing; not storage/equipment.
        if not IsInventorySource(mouse.GetAttachedType(),cell):
            return
        vnum,count=self.InventorySource(player.INVENTORY,cell)
        required=self.selected['materials'][index][0]
        if mouse.GetAttachedItemIndex()!=vnum or vnum not in stonecrafting.MaterialVnums(self.selected['vnum'],required):
            return
        if self.basket.add(player.INVENTORY,cell,vnum,count,index):
            self.useAny=False
            mouse.DeattachObject()
            self.SelectionChanged()

    def ClickSource(self, row, index):
        if mouseModule.mouseController.isAttached():
            self.DropMaterial(index)
        else:
            self.RemoveSource(row)

    def RemoveSource(self, row):
        if not self.pending:
            self.basket.remove(row)
            self.SelectionChanged()

    def SourceTooltip(self, row):
        if self.InventorySource(row['window'],row['cell'])==(row['vnum'],row['count']):
            self.toolTip.SetInventoryItem(row['cell'],row['window'])

    def BINARY_CRAFTING_SELECTION_V1(self, nonce, npc, limit):
        if self.destroyed or not self.IsShow() or not self.selected or int(nonce)!=self.capNonce or int(npc)!=self.selected['npc']:
            return
        self.selectionCapable=True
        self.basket.limit=max(0,int(limit))
        if any(self.ManualMaterial(i) for i,(v,n) in enumerate(self.selected['materials']) if v and n):
            self.useAny=False
            self.SelectionChanged()
        else:
            self.PaintCheckbox()

    def BINARY_CRAFTING_SELECTION_SOURCE_V1(self, nonce, window, cell, identity, vnum, count):
        if self.selectionNonce and int(nonce)==self.selectionNonce:
            self.basket.acknowledge(int(window),int(cell),int(identity),int(vnum),int(count))

    def OnPressEscapeKey(self):
        if self.menu.IsShow():
            self.CloseMenu()
        else:
            self.Close()
        return True
