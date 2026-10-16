"""Approved compact public chat; existing server protocol and Messenger routes."""
import time
from _weakref import proxy, ProxyType

import app
import chat
import ime
import net
import osfInfo
import player
import systemSetting
import ui
import uiChat
import uiCommon
import uiToolTip
import wndMgr
import compactchatmodel as model
import uicompactchatcontrols as controls
from uicrimsonember import SettingsScrollBar

try:
    import messengerHistory
except ImportError:
    messengerHistory = None

FILTER_NAMES = ('Okolí', 'Skupina', 'Cech', 'Volání', 'Systém', 'Oznámení',
                'Kostka', None, 'Předměty', 'Yang')
HEADER = (('all', 'Vše', 67), ('shout', 'Volání', 87), ('party', 'Skupina', 93),
          ('guild', 'Cech', 78), ('system', 'Systém', 91))
CHANNELS = (('Okolí', chat.CHAT_TYPE_TALKING, ''), ('Volání', chat.CHAT_TYPE_SHOUT, '!'),
            ('Skupina', chat.CHAT_TYPE_PARTY, '#'), ('Cech', chat.CHAT_TYPE_GUILD, '%'))
NOTIFICATIONS = (('badge', 'Odznak nepřečtených zpráv'), ('sound', 'Zvuk nové PM'),
                 ('toast', 'Upozornění na novou PM'), ('preview', 'Náhled textu zprávy'))


def event(method, *args):
    callback = ui.__mem_func__(method)
    return lambda: callback(*args)


def weak_owner(owner):
    # ui.__mem_func__ invokes button callbacks with an existing proxy as self.
    # Detached history and its MessageView must reuse it, not proxy it again.
    return owner if type(owner) is ProxyType else proxy(owner)


def kinds_for_filters(filters):
    kinds = set()
    for index in filters:
        if index not in model.AVAILABLE_FILTERS:
            continue
        entry = osfInfo.OPTION_CHECKBOX_MODE.get(index)
        if entry:
            kinds.update(entry[0])
    if 6 in filters:
        for name in ('CHAT_TYPE_MONARCH_NOTICE', 'CHAT_TYPE_BIG_CONTROL_NOTICE'):
            if hasattr(chat, name):
                kinds.add(getattr(chat, name))
    return kinds


def channel_name(kind):
    for index, entry in osfInfo.OPTION_CHECKBOX_MODE.items():
        if kind in entry[0]:
            return FILTER_NAMES[index-1]
    return 'Systém'


class MessageView(ui.Window):
    def __init__(self, parent, owner, width, height):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.owner = weak_owner(owner)
        self.SetSize(width, height)
        self.EnableScissorRect()
        self.rows = []
        self.row_keys = []
        self.cached = {}
        self.lines = []
        self.revision = None
        self.layout_key = None
        self.offset = 0
        self.anchor = None
        self.measurer = controls.label(self, 0, 0)
        self.measurer.Hide()
        self.tip = uiToolTip.ToolTip()
        self.tip_link = ''
        self.scroll = SettingsScrollBar()
        self.scroll.SetParent(self)
        self.scroll.SetPosition(width-12, 0)
        self.scroll.SetScrollBarSize(height)
        self.scroll.SetScrollEvent(ui.__mem_func__(self.OnScroll))
        self.scroll.SetScrollStep(.12)
        self.scroll.Hide()
        self.Show()

    def Resize(self, width, height):
        if (width, height) == (self.GetWidth(), self.GetHeight()):
            return
        self.SetSize(width, height)
        self.scroll.SetPosition(width-12, 0)
        self.scroll.SetScrollBarSize(height)
        self.layout_key = None

    def Measure(self, value):
        self.measurer.SetText(value)
        return self.measurer.GetTextSize()[0]

    def RefreshMessages(self, kinds):
        prefs = self.owner.prefs
        revision = chat.GetMessageRevision()
        key = (self.GetWidth(), self.GetHeight(), prefs['font'], prefs['timestamps'], tuple(sorted(kinds)))
        if self.revision == revision and self.layout_key == key:
            return
        if self.layout_key != key:
            self.cached = {}
            self.measurer.SetFontName(model.chat_font(prefs['font']))
            self.measurer.SetText('')
        self.revision, self.layout_key = revision, key
        messages = chat.GetRecentMessages()
        retained = {row[0] for row in messages}
        self.cached = {seq: runs for seq, runs in self.cached.items() if seq in retained}
        self.lines = []
        own = player.GetName()
        for row in messages:
            if row[1] not in kinds:
                continue
            seq = row[0]
            if seq not in self.cached:
                rich = model.message_text(row, own, prefs['timestamps'], channel_name(row[1]))
                self.cached[seq] = model.wrap_rich(rich, self.GetWidth()-22, self.Measure)
            for index, line in enumerate(self.cached[seq]):
                self.lines.append((seq, index, line, row[5]))
        if self.anchor:
            # New messages must not move a reader who scrolled into history.
            found = next((i for i, row in enumerate(self.lines) if row[:2] == self.anchor), None)
            if found is not None:
                self.offset = max(0, len(self.lines)-found-self.PageSize())
        self.DrawRows()

    def PageSize(self):
        return max(1, self.GetHeight() // (self.owner.prefs['font']+8))

    def DrawRows(self):
        count = self.PageSize()
        maximum = max(0, len(self.lines)-count)
        self.offset = min(maximum, max(0, self.offset))
        end = len(self.lines)-self.offset
        start = max(0, end-count)
        selected = self.lines[start:end]
        self.anchor = selected[0][:2] if self.offset and selected else None
        for row in self.rows[len(selected):]:
            if row.IsShow():
                row.Hide()
        while len(self.rows) < len(selected):
            row = controls.label(self, 0, 0)
            row.SetOutline(True)
            row.DisableEnterToken()
            self.rows.append(row)
            self.row_keys.append(None)
        for index, (seq, subline, value, color) in enumerate(selected):
            row = self.rows[index]
            key = (self.owner.prefs['font'], value, color)
            previous = self.row_keys[index]
            if previous != key:
                if previous is None or previous[0] != key[0]:
                    row.SetFontName(model.chat_font(key[0]))
                    row.SetText('')
                row.SetFontColor(((color>>16)&255)/255., ((color>>8)&255)/255., (color&255)/255.)
                row.SetText(value)
                self.row_keys[index] = key
            row.SetPosition(0, index*(self.owner.prefs['font']+8))
            if not row.IsShow():
                row.Show()
        if maximum:
            self.scroll.SetMiddleBarSize(min(1., count/float(len(self.lines))))
            position = 1.-self.offset/float(maximum)
            self.scroll.SetPos(position, False)
            self.scroll.curPos = position
            self.scroll.Show()
        else:
            self.scroll.Hide()

    def OnScroll(self):
        self.offset = int((1.-self.scroll.GetPos())*max(0, len(self.lines)-self.PageSize()))
        self.DrawRows()

    def OnRunMouseWheel(self, delta):
        self.offset += 3 if delta > 0 else -3
        self.DrawRows()
        return True

    def Latest(self):
        self.offset = 0
        self.anchor = None
        self.DrawRows()

    def OnUpdate(self):
        link = ui.GetHyperlink() if self.IsIn() else ''
        kind, target = model.link_target(link)
        if not target:
            self.tip.HideToolTip()
            self.tip_link = ''
            return
        if link != self.tip_link:
            self.tip.ClearToolTip()
            text = target if kind == 'chatweb' else 'Napsat ' + target
            for start in range(0, len(text), 64):
                self.tip.AutoAppendNewTextLineResize(text[start:start+64])
            self.tip_link = link
        self.tip.ShowToolTip()

    def OnMouseLeftButtonDown(self):
        link = ui.GetHyperlink()
        if link:
            if app.IsPressed(app.DIK_LALT) and link.startswith(('item:', 'petitem:')):
                ime.PasteString(chat.GetLinkFromHyperlink(link))
            elif self.owner.interface:
                self.owner.interface.MakeHyperlinkTooltip(link)
            return True
        return False

    def Hide(self):
        if getattr(self, 'tip', None):
            self.tip.HideToolTip()
        ui.Window.Hide(self)

    def Destroy(self):
        self.Hide()
        self.rows = []
        self.row_keys = []
        self.cached = {}
        self.lines = []
        self.scroll.Destroy()
        self.scroll = None
        self.measurer = None
        self.owner = None


class CompactInput(ui.Window):
    def __init__(self, parent):
        ui.Window.__init__(self)
        self.SetParent(parent)
        self.owner = weak_owner(parent)
        self.chatLine = uiChat.ChatLine()
        self.chatLine.SetParent(self)
        self.chatLine.SetFontName('Tahoma:12')
        self.chatLine.SetMax(512)
        self.chatLine.SetUserMax(256)
        self.chatLine.SAFE_SetEscapeEvent(parent.CloseChat)
        self.chatLine.SAFE_SetReturnEvent(parent.CloseChat)
        self.chatLine.Show()
        self.mode = controls.IconControl(self, 6, 3, None,
            'Vybrat kanál odesílání. Horní filtry se nezmění.', event(parent.OpenChannels), 40, 'Okolí', 17)
        self.mode.text.SetPosition(20, 2)
        self.mode.text.SetFontName('Tahoma:11')
        self.mode.text.SetText('')
        self.mode.text.SetText('Okolí')
        self.chatLine.SetInfoMessage('Napiš zprávu…')
        self.chatLine.backText.SetFontName('Tahoma:12')
        self.chatLine.backText.SetText('')
        self.chatLine.backText.SetText('Napiš zprávu…')
        self.chatLine.backText.SetFontColor(*controls.DIM)
        net.EnableChatInsultFilter(uiChat.ENABLE_INSULT_CHECK)
        uiChat.InsertChatInputSetWindow(self)
        self.Show()

    def RefreshPosition(self):
        self.chatLine.SetPosition(55, 5)
        self.chatLine.SetSize(self.GetWidth()-65, 17)
        self.chatLine.x, self.chatLine.y, self.chatLine.width, self.chatLine.height = self.chatLine.GetRect()

    def BindInterface(self, interface):
        self.chatLine.BindInterface(interface)

    def SetChatFocus(self):
        self.chatLine.SetFocus()

    def OnRefreshChatMode(self):
        index = next((i for i, row in enumerate(CHANNELS) if row[1] == self.chatLine.GetChatMode()), 0)
        self.SelectChannel((index+1)%len(CHANNELS))

    def SelectChannel(self, index):
        name, mode, prefix = CHANNELS[index]
        draft = self.chatLine.GetText()
        if draft[:1] in ('!', '#', '%'):
            draft = draft[1:]
        self.chatLine.SetChatMode(mode)
        self.chatLine.SetText(prefix + draft)
        self.chatLine.SetEndPosition()
        self.mode.SetText(name)
        self.owner.OpenChat()

    def OnUpdate(self):
        value = self.chatLine.GetText()
        prefix = value[:1]
        index = next((i for i, row in enumerate(CHANNELS) if row[2] == prefix), 0)
        name = CHANNELS[index][0] if prefix in ('!', '#', '%') else 'Okolí'
        if self.mode.text.GetText() != name:
            self.mode.SetText(name)

    def OnRender(self):
        x, y = self.GetGlobalPosition()
        ui.RenderRoundBox(x, y, self.GetWidth(), 23, controls.grp.GenerateColor(.40, .33, .25, 1))

    def Hide(self):
        if getattr(self, 'mode', None):
            self.mode.OnMouseOverOut()
        ui.Window.Hide(self)

    def Destroy(self):
        self.chatLine.KillFocus()
        self.chatLine.Hide()
        self.mode.Destroy()
        if self in uiChat.chatInputSetList:
            uiChat.chatInputSetList.remove(self)
        self.chatLine = None
        self.mode = None
        self.owner = None
        self.Hide()


class PassiveView(ui.Window):
    """The native stream owns lifetime/alpha; this view supplies font and wrapping."""
    def __init__(self, owner):
        ui.Window.__init__(self)
        self.SetParent(owner)
        self.AddFlag('not_pick')
        self.owner = weak_owner(owner)
        self.rows = []
        self.keys = []
        self.cached = {}
        self.layout = None
        self.alpha = 0.
        self.measurer = controls.label(self, 0, 0)
        self.measurer.Hide()

    def Measure(self, text):
        self.measurer.SetText(text)
        return self.measurer.GetTextSize()[0]

    def RefreshMessages(self, kinds):
        if not chat.GetVisibleLineCount(self.owner.chatID):
            self.Hide()
            return
        prefs = self.owner.prefs
        width = self.owner.GetWidth()-20
        layout = (width, prefs['font'], prefs['timestamps'])
        if layout != self.layout:
            self.layout = layout
            self.cached = {}
            self.measurer.SetFontName(model.chat_font(prefs['font']))
            self.measurer.SetText('')
        messages = chat.GetRecentMessages()
        retained = {row[0] for row in messages}
        self.cached = {seq: value for seq, value in self.cached.items() if seq in retained}
        selected = []
        for row in reversed(messages):
            # GetRecentMessages returns aColor[CHAT_SET_CHAT_WINDOW] after Update.
            # Expired messages retain <= 0.1 alpha even while in the history cache.
            if row[1] not in kinds or (row[5] >> 24) <= 25:
                continue
            if row[0] not in self.cached:
                text = model.message_text(row, player.GetName(), prefs['timestamps'], channel_name(row[1]))
                self.cached[row[0]] = model.wrap_rich(text, width, self.Measure)
            selected[0:0] = [(line, row[5]) for line in self.cached[row[0]]]
            if len(selected) >= 5:
                break
        selected = selected[-5:]
        if not selected:
            self.Hide()
            return
        step = prefs['font']+8
        self.SetSize(width, len(selected)*step)
        self.SetPosition(10, -self.GetHeight())
        self.alpha = max(color >> 24 for text, color in selected)/255.
        while len(self.rows) < len(selected):
            line = controls.label(self, 0, 0)
            line.SetOutline(True)
            line.DisableEnterToken()
            self.rows.append(line)
            self.keys.append(None)
        for line in self.rows[len(selected):]:
            line.Hide()
        for index, (text, color) in enumerate(selected):
            line = self.rows[index]
            key = (prefs['font'], text)
            if self.keys[index] != key:
                if not self.keys[index] or self.keys[index][0] != key[0]:
                    line.SetFontName(model.chat_font(key[0]))
                    line.SetText('')
                line.SetText(text)
                self.keys[index] = key
            line.SetPackedFontColor(color if color < 0x80000000 else color-0x100000000)
            line.SetPosition(0, index*step)
            if not line.IsShow():
                line.Show()
        self.Show()

    def OnRender(self):
        opacity = self.owner.prefs['idle_opacity']/100.*self.alpha
        if opacity:
            x, y = self.GetGlobalPosition()
            controls.bar(x-10, y-3, self.GetWidth()+20, self.GetHeight()+6, (.035, .039, .043), opacity)

    def Destroy(self):
        self.Hide()
        self.rows = []
        self.keys = []
        self.cached = {}
        self.measurer = None
        self.owner = None


class HistoryPanel(controls.Panel):
    def __init__(self, owner, name, kinds):
        controls.Panel.__init__(self, 588, 400, name, 'history')
        self.owner = weak_owner(owner)
        self.kinds = set(kinds)
        self.AddFlag('movable')
        self.view = MessageView(self, owner, 563, 318)
        self.view.SetPosition(12, 39)
        self.latest = controls.text_button(self, 366, 369, 208, 'Nejnovější zprávy',
            'Vrátit výpis na nové zprávy.', event(self.view.Latest))

    def OnUpdate(self):
        self.view.RefreshMessages(self.kinds)

    def Hide(self):
        if getattr(self, 'view', None):
            self.view.tip.HideToolTip()
        controls.Panel.Hide(self)

    def Destroy(self):
        self.latest.Destroy()
        self.view.Destroy()
        controls.Panel.Destroy(self)
        self.view = None
        self.owner = None


class ChatWindow(ui.Window):
    CHAT_WINDOW_WIDTH = 588
    EDIT_LINE_HEIGHT = 25

    def __init__(self):
        ui.Window.__init__(self)
        self.SetWindowName('Compact public chat')
        self.AddFlag('float')
        self.interface = None
        self.edit_mode = False
        self.destroyed = False
        self.sendWhisperEvent = None
        self.openChatLogEvent = None
        self.store = None
        self.loaded_name = ''
        self.prefs = model.normalize_preferences({})
        self.repeat = model.RepeatShout()
        self.selected = 'all'
        self.tab_index = 0
        self.header = []
        self.buttons = []
        self.panels = {}
        self.histories = {}
        self.question = None
        self.screen = None
        self.anchor_x = None
        self.resize_origin = None
        self.move_origin = None
        self.prefs_dirty = False
        self.view_config_dirty = False
        self.prefs_due = 0.
        self.save_error_reported = False
        self.settings_name = None
        self.passive_kinds = None
        uiChat.ChatWindow._ChatWindow__RegisterChatColorDict(self)
        self.chatID = chat.CreateChatSet(chat.CHAT_SET_CHAT_WINDOW)
        # The native stream keeps aging even while the separate editor is open.
        # Switching its board state on Enter would revive old, faded messages.
        chat.SetBoardState(self.chatID, chat.BOARD_STATE_VIEW)
        self.SetSize(588, 230)
        self.view = MessageView(self, self, 568, 153)
        self.view.SetPosition(10, 38)
        self.passive = PassiveView(self)
        self.resize_grip = controls.ResizeGrip(self)
        self.move_grip = controls.MoveGrip(self)
        self.chatInputSet = CompactInput(self)
        self.BuildHeader()
        actions = (('emoji', 'Vložit emotikon do rozepsané zprávy.', self.OpenEmoji),
                   ('send', 'Odeslat zprávu / Enter', self.Send),
                   ('pm', 'Otevřít stávající Messenger.', self.OpenMessenger),
                   ('history', 'Otevřít historii veřejného chatu.', self.OpenHistory))
        for key, tooltip, callback in actions:
            button = controls.IconControl(self, 0, 0, key, tooltip, event(callback))
            self.buttons.append(button)
        self.LoadPreferences()
        self.Refresh()

    def LoadPreferences(self):
        name = player.GetName()
        if not name or name == self.loaded_name:
            return
        self.repeat.pause()
        self.FlushPreferences()
        self.loaded_name = name
        osfInfo.LoadChatData()
        try:
            self.store = model.PreferenceStore(name)
            self.prefs = self.store.load(osfInfo.cacheChat)
        except ValueError:
            self.store = None
            self.prefs = model.normalize_preferences({}, osfInfo.cacheChat)
        self.anchor_x = self.prefs['x']
        self.BuildHeader()
        self.Refresh()

    def SavePreferences(self):
        try:
            if self.store:
                self.store.save(self.prefs)
            if self.view_config_dirty:
                if not systemSetting.SaveConfig():
                    raise OSError('chat visibility config')
                self.view_config_dirty = False
        except OSError:
            if not self.save_error_reported:
                self.Notice('Nastavení chatu se nepodařilo uložit. Zkusím to znovu.')
            self.save_error_reported = True
            self.prefs_dirty = True
            self.prefs_due = app.GetTime()+2.
            return False
        self.prefs_dirty = False
        self.save_error_reported = False
        return True

    def QueuePreferences(self):
        self.prefs_dirty = True
        self.prefs_due = app.GetTime()+.3

    def FlushPreferences(self):
        if self.prefs_dirty:
            return self.SavePreferences()
        return True

    def Notice(self, text):
        chat.AppendChat(chat.CHAT_TYPE_INFO, text)

    def BuildHeader(self):
        for control in self.header:
            control.Destroy()
        self.header = []
        x = 4
        width = self.GetWidth()
        compact = width < self.CHAT_WINDOW_WIDTH
        for key, name, tab_width in HEADER:
            tab_width = 28 if compact else tab_width
            button = controls.IconControl(self, x, 0, key,
                'Zobrazit: %s. Kanál odesílání se nezmění.' % name,
                event(self.SelectHeader, key), tab_width, '' if compact else name, 28)
            button.SetSelected(self.selected == key)
            self.header.append(button)
            x += tab_width
        if len(self.prefs['tabs']) > 1:
            name = self.prefs['tabs'][self.tab_index]['name'] if self.selected == 'custom' else 'Vlastní…'
            button = controls.IconControl(self, x+2, 0, None, 'Vybrat vlastní záložku nebo oddělené okno: ' + name,
                event(self.OpenCustomTabs), max(24, width-x-102), name, 28)
            # Custom names may contain wide glyphs; keep the action buttons clear.
            while button.text.GetTextSize()[0] > button.GetWidth()-6 and len(name) > 1:
                name = name[:-1]
                button.SetText(name + '…')
            button.SetSelected(self.selected == 'custom')
            self.header.append(button)
        self.repeat_button = controls.IconControl(self, width-95, 2, 'repeat',
            'Opakované volání: stav, uložená zpráva, spuštění a pozastavení.', event(self.OpenRepeat))
        self.repeat_button.running = self.repeat.running
        self.header.append(self.repeat_button)
        self.header.append(controls.IconControl(self, width-69, 2, 'add',
            'Vytvořit vlastní záložku s názvem a filtry.', event(self.OpenAddTab)))
        self.header.append(controls.IconControl(self, width-43, 2, 'settings',
            'Nastavení chatu: Obsah, Vzhled, Upozornění.', event(self.OpenSettings)))
        self.RefreshEditorVisibility()

    def RefreshEditorVisibility(self):
        for control in ([self.view, self.chatInputSet, self.resize_grip, self.move_grip]
                        + self.header + self.buttons):
            if self.edit_mode:
                control.Show()
            else:
                control.Hide()
        if self.edit_mode:
            self.passive.Hide()

    def RefreshPassiveFilters(self):
        kinds = tuple(sorted(self.CurrentKinds()))
        if kinds == self.passive_kinds:
            return
        self.passive_kinds = kinds
        chat.DisableChatMode(self.chatID, chat.CHAT_TYPE_EXP_INFO)
        for kind in kinds_for_filters(model.AVAILABLE_FILTERS):
            if kind in kinds:
                chat.EnableChatMode(self.chatID, kind)
            else:
                chat.DisableChatMode(self.chatID, kind)

    def SelectHeader(self, key):
        self.selected = key
        self.tab_index = 0
        self.view.Latest()
        self.BuildHeader()

    def SelectCustom(self, index):
        self.tab_index = index
        self.selected = 'custom' if index else 'all'
        self.view.Latest()
        self.BuildHeader()
        if 'custom' in self.panels:
            self.panels['custom'].Hide()

    def CurrentKinds(self):
        base = kinds_for_filters(self.prefs['tabs'][self.tab_index]['filters'])
        selected = dict(shout={chat.CHAT_TYPE_SHOUT}, party={chat.CHAT_TYPE_PARTY}, guild={chat.CHAT_TYPE_GUILD},
                        system=kinds_for_filters(range(5, 11)))
        return base.intersection(selected[self.selected]) if self.selected in selected else base

    def Refresh(self):
        screen = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        if self.screen != screen:
            self.resize_origin = None
            self.move_origin = None
            self.anchor_x = self.prefs['x']
            for panel in self.panels.values():
                for child in panel.children:
                    if isinstance(child, controls.DropDown):
                        child.CloseMenu()
        x, y, width, height = model.chat_geometry(self.prefs['width'], self.prefs['height'], screen,
                                                 self.anchor_x, self.prefs['bottom'])
        self.anchor_x = x
        old_width = self.GetWidth()
        visible_height = height if self.edit_mode else 0
        baseline = y+height
        self.SetSize(width, visible_height)
        self.SetPosition(x, max(0, baseline-visible_height))
        chat.SetPosition(self.chatID, x+10, baseline)
        chat.SetHeight(self.chatID, 5*chat.GetLineStep(self.chatID))
        self.screen = screen
        self.resize_grip.SetPosition(width-16, 0)
        self.move_grip.SetSize(width-20, 10)
        self.chatInputSet.SetPosition(1, height-32)
        self.chatInputSet.SetSize(width-119, 24)
        self.chatInputSet.RefreshPosition()
        self.view.Resize(width-20, height-77)
        for index, delta in enumerate((111, 79, 53, 27)):
            self.buttons[index].SetPosition(width-delta, height-32)
        if old_width != width:
            self.BuildHeader()
        self.RefreshEditorVisibility()
        for panel in self.panels.values():
            if panel.IsShow():
                self.PositionPanel(panel)

    def BeginResize(self):
        if self.edit_mode:
            self.EndMove()
            self.resize_origin = (wndMgr.GetMousePosition(), self.GetWidth(), self.GetHeight())

    def DragResize(self):
        if not self.resize_origin or not self.edit_mode:
            return
        (mx, my), width, height = self.resize_origin
        px, py = wndMgr.GetMousePosition()
        # Resizing raises the top edge while the chosen bottom stays anchored.
        bottom = self.GetGlobalPosition()[1]+self.GetHeight()
        x, y, width, height = model.chat_geometry(width+px-mx, min(height+my-py, bottom),
                                                 self.screen, self.anchor_x, self.prefs['bottom'])
        if (width, height) != (self.GetWidth(), self.GetHeight()):
            self.prefs.update(width=width, height=height)
            self.QueuePreferences()
            self.Refresh()

    def EndResize(self):
        self.resize_origin = None
        self.FlushPreferences()

    def BeginMove(self):
        if self.edit_mode:
            self.EndResize()
            self.move_origin = (wndMgr.GetMousePosition(), self.GetGlobalPosition())
            self.SetTop()

    def DragMove(self):
        if not self.move_origin or not self.edit_mode:
            return
        (mx, my), (x, y) = self.move_origin
        px, py = wndMgr.GetMousePosition()
        width, height = self.GetWidth(), self.GetHeight()
        sw, sh = self.screen
        x = max(0, min(x+px-mx, sw-width))
        y = max(0, min(y+py-my, sh-height))
        if (x, y) != self.GetGlobalPosition():
            self.anchor_x = x
            self.prefs.update(x=x, bottom=y+height, width=width, height=height)
            self.QueuePreferences()
            self.Refresh()

    def EndMove(self):
        self.move_origin = None
        self.FlushPreferences()

    def SetHeight(self, height):
        self.Refresh()

    def BindInterface(self, interface):
        self.interface = proxy(interface)
        self.chatInputSet.BindInterface(interface)

    def SetSendWhisperEvent(self, callback):
        self.sendWhisperEvent = callback

    def SetOpenChatLogEvent(self, callback):
        self.openChatLogEvent = callback

    def OpenChat(self):
        opening = not self.edit_mode
        self.edit_mode = True
        self.Refresh()
        if opening:
            # The closed preview follows incoming messages. Reopening must not
            # return to an old scroll anchor and hide those same messages.
            self.view.Latest()
            self.view.RefreshMessages(self.CurrentKinds())
        self.Show()
        self.chatInputSet.chatLine.SetFocus()

    def CloseChat(self):
        self.CaptureSettingsName()
        self.EndResize()
        self.EndMove()
        self.edit_mode = False
        self.chatInputSet.chatLine.KillFocus()
        for panel in self.panels.values():
            panel.Hide()
        self.CloseQuestion()
        self.Refresh()

    def IsEditMode(self):
        return self.edit_mode

    def SetChatFocus(self):
        self.OpenChat()

    def hide_btnChatSizing(self):
        self.CloseChat()

    def show_btnChatSizing(self):
        self.Show()

    def UpdateChat(self):
        self.view.layout_key = None

    def LoadChatLoby(self, isFirst=False):
        self.LoadPreferences()
        self.BuildHeader()

    def Send(self):
        self.OpenChat()
        self.chatInputSet.chatLine.OnIMEReturn()

    def OpenMessenger(self):
        if self.sendWhisperEvent:
            self.sendWhisperEvent()

    def OpenHistory(self, index=None):
        key = index if index is not None else 'main'
        kinds = kinds_for_filters(self.prefs['tabs'][index]['filters']) if index is not None else self.CurrentKinds()
        if key not in self.histories:
            name = self.prefs['tabs'][index]['name'] if index is not None else 'Historie veřejného chatu'
            self.histories[key] = HistoryPanel(self, name, kinds)
            self.PositionPanel(self.histories[key])
        panel = self.histories[key]
        panel.kinds = kinds
        panel.Show()
        panel.SetTop()

    def ToggleHistory(self):
        if 'main' in self.histories and self.histories['main'].IsShow():
            self.histories['main'].Hide()
        else:
            self.OpenHistory()

    def PositionPanel(self, panel):
        x, y = self.GetGlobalPosition()
        panel.SetPosition(min(max(0, x+self.GetWidth()-panel.GetWidth()), max(0, wndMgr.GetScreenWidth()-panel.GetWidth())),
                          max(0, y-panel.GetHeight()-6))

    def NewPanel(self, key, width, height, title, icon, close_event=None):
        if key in self.panels:
            self.panels[key].Destroy()
        panel = controls.Panel(width, height, title, icon, close_event)
        self.panels[key] = panel
        self.PositionPanel(panel)
        panel.Show()
        panel.SetTop()
        return panel

    def OpenChannels(self):
        panel = self.NewPanel('channels', 170, 177, 'Odesílat do', 'send')
        for index, (name, mode, prefix) in enumerate(CHANNELS):
            button = controls.text_button(panel, 12, 40+index*31, 146, name,
                'Přepne kanál odesílání; rozepsaná zpráva zůstane.', event(self.SelectChannel, index))
            button.SetSelected(self.chatInputSet.chatLine.GetChatMode() == mode)
            panel.children.append(button)

    def SelectChannel(self, index):
        self.chatInputSet.SelectChannel(index)
        self.panels['channels'].Hide()

    def OpenEmoji(self, category='recent'):
        panel = self.NewPanel('emoji', 272, 180, 'Emotikony', 'emoji')
        for key, title, x, width in (('recent', 'Nedávné', 6, 86), ('emoji', 'Tváře', 92, 78), ('symbols', 'Symboly', 170, 96)):
            button = controls.IconControl(panel, x, 32, key, 'Kategorie emotikonů: ' + title,
                event(self.OpenEmoji, key), width, title, 28)
            button.text.SetFontName('Tahoma:11')
            button.text.SetText('')
            button.text.SetText(title)
            button.SetSelected(category == key)
            panel.children.append(button)
        names = self.prefs['recent'] if category == 'recent' else (['heart'] if category == 'symbols' else model.EMOJI_NAMES[:-1])
        if category == 'recent' and not names:
            panel.children.append(controls.label(panel, 13, 69, 'Vyber emotikon ze záložky Tváře.', 11, controls.DIM))
        else:
            panel.children.append(controls.label(panel, 13, 69, 'Kliknutím vložíš do rozepsané zprávy.', 11, controls.DIM))
        for index, name in enumerate(names):
            title = next(row[2] for row in model.EMOJI if row[0] == name)
            button = controls.IconControl(panel, 12+(index%7)*34, 91+(index//7)*30, None,
                'Vložit: ' + title, event(self.InsertEmoji, name))
            button.icon = ui.ImageBox()
            button.icon.SetParent(button)
            button.icon.AddFlag('not_pick')
            button.icon.LoadImage('icon/emoji/' + name + '.tga')
            button.icon.SetPosition(4, 4)
            button.icon.Show()
            panel.children.append(button)

    def InsertEmoji(self, name):
        if name not in model.EMOJI_NAMES:
            return
        self.OpenChat()
        ime.PasteString('|Iemoji/' + name + '|i')
        self.prefs['recent'] = [name] + [old for old in self.prefs['recent'] if old != name]
        self.SavePreferences()
        self.panels['emoji'].Hide()

    def OpenRepeat(self):
        panel = self.NewPanel('repeat', 302, 313, 'Opakované zprávy', 'repeat')
        panel.children.append(controls.label(panel, 13, 49, 'Kanál', 11, controls.DIM))
        panel.children.append(controls.label(panel, 239, 49, 'Volání'))
        panel.children.append(controls.label(panel, 13, 77, 'Interval', 11, controls.DIM))
        self.repeat_interval = self.prefs['interval']
        self.interval_button = controls.text_button(panel, 179, 69, 110, '%d sekund' % self.repeat_interval,
            'Vybrat interval: 60, 120, 180 nebo 300 sekund.', event(self.CycleInterval))
        panel.children.append(self.interval_button)
        panel.children.append(controls.label(panel, 13, 112, 'ULOŽENÁ ZPRÁVA', 11, controls.GOLD))
        self.repeat_input = controls.Input(panel, 13, 144, 276, self.prefs['repeat_text'], height=61)
        self.repeat_input.edit.SetMultiLine()
        self.repeat_input.edit.SetLimitWidth(260)
        self.repeat_input.edit.SetReturnEvent(ui.__mem_func__(self.SaveRepeat))
        self.repeat_input.edit.SetEscapeEvent(ui.__mem_func__(panel.Hide))
        panel.children.append(self.repeat_input)
        panel.children.append(controls.label(panel, 13, 218, 'Běžné psaní tento text nepřepíše.', 11, controls.DIM))
        self.repeat_status = controls.label(panel, 13, 245, '', 11, controls.GREEN)
        panel.children.append(self.repeat_status)
        self.repeat_start = controls.text_button(panel, 13, 277, 126, 'Spustit',
            'Výslovně spustit nebo pozastavit opakované volání.', event(self.ToggleRepeat))
        panel.children.append(self.repeat_start)
        panel.children.append(controls.text_button(panel, 153, 277, 136, 'Uložit úpravy',
            'Uloží samostatnou zprávu a interval. Vypnuté opakování nespustí.', event(self.SaveRepeat)))

    def CycleInterval(self):
        options = (60, 120, 180, 300)
        self.repeat_interval = options[(options.index(self.repeat_interval)+1)%len(options)]
        self.interval_button.SetText('%d sekund' % self.repeat_interval)

    def SaveRepeat(self):
        text = self.repeat_input.edit.GetText().strip()
        try:
            candidate = model.RepeatShout()
            candidate.start(text, self.repeat_interval, app.GetTime())
        except ValueError as error:
            self.Notice(str(error))
            return False
        self.prefs['repeat_text'] = text
        self.prefs['interval'] = self.repeat_interval
        if not self.SavePreferences():
            return False
        if self.repeat.running:
            self.repeat.text = text
            self.repeat.interval = self.repeat_interval
            self.repeat.next_send = app.GetTime() + self.repeat_interval
        return True

    def ToggleRepeat(self):
        if self.repeat.running:
            self.PauseRepeat()
            return
        if player.GetStatus(player.LEVEL) < 15:
            self.Notice('Volání je dostupné od úrovně 15.')
            return
        if self.SaveRepeat():
            self.repeat.start(self.prefs['repeat_text'], self.prefs['interval'], app.GetTime())

    def PauseRepeat(self):
        self.repeat.pause()

    def OpenCustomTabs(self):
        panel = self.NewPanel('custom', 302, 48+len(self.prefs['tabs'])*29, 'Vlastní záložky', 'all')
        for index, tab in enumerate(self.prefs['tabs']):
            select = controls.text_button(panel, 12, 37+index*29, 225, tab['name'],
                'Zobrazit tuto záložku v hlavním chatu.', event(self.SelectCustom, index))
            select.SetSelected(self.tab_index == index)
            panel.children.append(select)
            panel.children.append(controls.IconControl(panel, 261, 37+index*29, 'history',
                'Otevřít samostatné okno této záložky.', event(self.OpenHistory, index)))

    def OpenAddTab(self):
        if len(self.prefs['tabs']) >= model.MAX_TABS:
            self.Notice('Můžeš mít nejvýše 10 záložek a jejich oddělených oken.')
            return
        panel = self.NewPanel('add', 302, 225, 'Přidat záložku', 'add')
        panel.children.append(controls.label(panel, 13, 49, 'Název', 11, controls.DIM))
        self.new_name = controls.Input(panel, 89, 43, 200, '', max_length=12)
        self.new_name.edit.SetReturnEvent(ui.__mem_func__(self.CreateTab))
        self.new_name.edit.SetEscapeEvent(ui.__mem_func__(panel.Hide))
        panel.children.append(self.new_name)
        self.new_filters = {2, 3, 6}
        panel.children.append(controls.label(panel, 13, 85, 'Zobrazovat', 11, controls.DIM))
        self.new_filter_controls = {}
        for pos, index in enumerate((2, 3, 4, 6)):
            control = controls.checkbox(panel, 13+(pos%2)*143, 107+(pos//2)*29, 140,
                FILTER_NAMES[index-1], index in self.new_filters, event(self.ToggleNewFilter, index))
            self.new_filter_controls[index] = control
            panel.children.append(control)
        panel.children.append(controls.label(panel, 13, 168, 'Další filtry upravíš v nastavení.', 11, controls.DIM))
        panel.children.append(controls.text_button(panel, 150, 193, 139, 'Vytvořit',
            'Přidat záložku se zvoleným názvem a filtry.', event(self.CreateTab)))
        self.new_name.edit.SetFocus()

    def ToggleNewFilter(self, index):
        if index in self.new_filters:
            self.new_filters.remove(index)
        else:
            self.new_filters.add(index)
        self.new_filter_controls[index].check = index in self.new_filters

    def CreateTab(self):
        name = self.new_name.edit.GetText().strip()
        if not name or len(name) > 12 or any(c in name for c in '|\r\n\x00'):
            self.Notice('Zadej název záložky, nejvýše 12 znaků.')
            return
        if len(self.prefs['tabs']) >= model.MAX_TABS:
            self.Notice('Limit 10 záložek je již naplněný.')
            return
        self.prefs['tabs'].append(dict(name=name, filters=sorted(self.new_filters)))
        self.SavePreferences()
        self.panels['add'].Hide()
        self.SelectCustom(len(self.prefs['tabs'])-1)

    def NotificationSnapshot(self):
        import uisettings
        values = {key: bool(messengerHistory.GetNotificationPreference(key)) if messengerHistory else True
                  for key, label in NOTIFICATIONS}
        backend = self.BlockBackend()
        mode = backend.block_requests[-1] if backend and backend.block_requests else uisettings.blockMode
        values['block'] = bool(mode & 8)
        return values

    def OpenSettings(self):
        self.settings_tab = self.tab_index
        self.settings_view_chat = bool(systemSetting.IsViewChat())
        self.settings_notifications = self.NotificationSnapshot()
        self.settings_page = 'Obsah'
        self.settings_name = None
        self.DrawSettings()

    def CaptureSettingsName(self):
        if not self.settings_name or not self.panels.get('settings') or not self.panels['settings'].IsShow():
            return
        if self.settings_tab and self.settings_tab < len(self.prefs['tabs']):
            name = self.settings_name.edit.GetText().strip().replace('|', '')[:12]
            if name and name != self.prefs['tabs'][self.settings_tab]['name']:
                self.prefs['tabs'][self.settings_tab]['name'] = name
                self.QueuePreferences()
                self.RefreshTabs()

    def CloseSettings(self):
        self.CaptureSettingsName()
        self.FlushPreferences()
        if 'settings' in self.panels:
            self.panels['settings'].Hide()

    def DrawSettings(self):
        self.settings_name = None
        self.appearance_controls = {}
        self.appearance_values = {}
        panel = self.NewPanel('settings', 322, 447, 'Nastavení chatu', 'settings', event(self.CloseSettings))
        for index, title in enumerate(('Obsah', 'Vzhled', 'Upozornění')):
            button = controls.IconControl(panel, 6+index*103, 33, None, 'Nastavení: ' + title,
                event(self.SettingsPage, title), 103, title, 28)
            button.SetSelected(title == self.settings_page)
            panel.children.append(button)
        if self.settings_page == 'Obsah':
            panel.children.append(controls.label(panel, 13, 80, 'Upravuješ záložku', 11, controls.DIM))
            tab = self.prefs['tabs'][self.settings_tab]
            panel.children.append(controls.text_button(panel, 178, 72, 130, tab['name'],
                'Vybrat další záložku pro úpravu filtrů.', event(self.CycleSettingsTab)))
            panel.children.append(controls.label(panel, 13, 115, 'ZOBRAZOVAT ZPRÁVY', 11, controls.GOLD))
            for pos, index in enumerate(model.AVAILABLE_FILTERS):
                panel.children.append(controls.checkbox(panel, 13+(pos%2)*149, 136+(pos//2)*26, 140,
                    FILTER_NAMES[index-1], index in tab['filters'], event(self.ToggleSettingsFilter, index)))
            if self.settings_tab:
                panel.children.append(controls.label(panel, 13, 294, 'Název', 11, controls.DIM))
                self.settings_name = controls.Input(panel, 90, 286, 218, tab['name'], 12)
                self.settings_name.edit.SetReturnEvent(ui.__mem_func__(self.CaptureSettingsName))
                self.settings_name.edit.SetEscapeEvent(ui.__mem_func__(self.CloseSettings))
                panel.children.append(self.settings_name)
                panel.children.append(controls.text_button(panel, 164, 335, 144, 'Odstranit záložku',
                    'Po potvrzení odstraní tuto vlastní záložku.', event(self.AskDeleteTab)))
            else:
                panel.children.append(controls.label(panel, 13, 297, 'Záložku Vše nelze odstranit.', 11, controls.DIM))
        elif self.settings_page == 'Vzhled':
            panel.children.append(controls.checkbox(panel, 13, 76, 293, 'Zobrazovat chat při hraní',
                self.settings_view_chat, event(self.ToggleViewChat)))
            panel.children.append(controls.label(panel, 13, 124, 'Velikost písma', 11, controls.DIM))
            dropdown = controls.DropDown(panel, 174, 119, 134,
                [(size, '%d px' % size) for size in model.FONT_SIZES], self.prefs['font'],
                lambda value: self.SetAppearance('font', value))
            self.appearance_controls['font'] = dropdown
            panel.children.append(dropdown)
            for index, (key, name) in enumerate((('opacity', 'Pozadí při psaní'), ('idle_opacity', 'Pozadí při hraní'))):
                y = 174+index*61
                panel.children.append(controls.label(panel, 13, y+2, name, 11, controls.DIM))
                slider = ui.SliderBar()
                slider.SetParent(panel)
                slider_path = 'd:/ymir work/ui/public/crimson/controls/slider/'
                slider.SetButtonVisual(slider_path, 'small_thumb_01.tga', 'small_thumb_02.tga', 'small_thumb_03.tga')
                slider.SetBackgroundVisual(slider_path + 'small_track.tga')
                slider.SetPosition(174, y)
                slider.SetSliderPos(self.prefs[key]/100.)
                slider.SetEvent(event(self.ChangeOpacity, key))
                slider.Show()
                self.appearance_controls[key] = slider
                value = controls.label(panel, 174, y+22, '%d %%' % self.prefs[key], 11, controls.GOLD)
                self.appearance_values[key] = value
                panel.children.extend((slider, value))
            control = controls.checkbox(panel, 13, 294, 290, 'Zobrazovat čas zpráv',
                self.prefs['timestamps'], event(self.ToggleTimestamps))
            self.appearance_controls['timestamps'] = control
            panel.children.append(control)
            preview = controls.PassivePreview(panel, self.prefs['font'], self.prefs['idle_opacity'])
            panel.children.append(preview)
            self.appearance_controls['preview'] = preview
            panel.children.append(controls.label(panel, 13, 384, 'Velikost okna změníš tažením za roh.', 11, controls.DIM))
        else:
            for index, (key, name) in enumerate(NOTIFICATIONS):
                control = controls.checkbox(panel, 13, 89+index*32, 293, name,
                    self.settings_notifications[key], event(self.ToggleNotification, key))
                control.tooltip = 'Společná volba s Messengerem: ' + name
                control.SetEnabled(messengerHistory is not None)
                panel.children.append(control)
            panel.children.append(controls.checkbox(panel, 13, 249, 293, 'Blokovat soukromé zprávy',
                self.settings_notifications['block'], event(self.ToggleNotification, 'block')))
            panel.children.append(controls.label(panel, 13, 300, 'Nastavení společné s Messengerem.', 11, controls.DIM))
            panel.children.append(controls.label(panel, 13, 321, 'Blokování potvrzuje herní server.', 11, controls.DIM))
        panel.children.append(controls.text_button(panel, 13, 410, 94, 'Obnovit',
            'Po potvrzení obnovit výchozí hodnoty této části.', event(self.AskResetSettings)))
        panel.children.append(controls.label(panel, 118, 416, 'Změny se ukládají automaticky.', 11, controls.DIM))

    def SettingsPage(self, page):
        self.CaptureSettingsName()
        self.FlushPreferences()
        self.settings_page = page
        self.DrawSettings()

    def CycleSettingsTab(self):
        self.CaptureSettingsName()
        self.FlushPreferences()
        self.settings_tab = (self.settings_tab+1)%len(self.prefs['tabs'])
        self.DrawSettings()

    def RefreshTabs(self):
        # Detached histories must not keep a renamed/deleted tab identity.
        for panel in self.histories.values():
            panel.Destroy()
        self.histories = {}
        self.tab_index = min(self.tab_index, len(self.prefs['tabs'])-1)
        if not self.tab_index and self.selected == 'custom':
            self.selected = 'all'
        self.BuildHeader()
        self.view.layout_key = None

    def ToggleSettingsFilter(self, index):
        if index not in model.AVAILABLE_FILTERS:
            return
        self.CaptureSettingsName()
        selected = self.prefs['tabs'][self.settings_tab]['filters']
        selected.remove(index) if index in selected else selected.append(index)
        self.QueuePreferences()
        self.RefreshTabs()
        self.DrawSettings()

    def ChangeOpacity(self, key):
        value = int(round(self.appearance_controls[key].GetSliderPos()*100))
        self.SetAppearance(key, value)

    def SetAppearance(self, key, value):
        if key not in ('font', 'opacity', 'idle_opacity', 'timestamps'):
            return
        self.prefs[key] = model.normalize_preferences(dict(self.prefs, **{key: value}))[key]
        self.QueuePreferences()
        # Never rebuild a pressed native slider or steal the input's focus.
        if key in getattr(self, 'appearance_values', {}):
            self.appearance_values[key].SetText('%d %%' % self.prefs[key])
        if 'preview' in getattr(self, 'appearance_controls', {}):
            self.appearance_controls['preview'].SetStyle(self.prefs['font'], self.prefs['idle_opacity'])
        self.Refresh()

    def ToggleTimestamps(self):
        self.SetAppearance('timestamps', not self.prefs['timestamps'])
        self.appearance_controls['timestamps'].check = self.prefs['timestamps']

    def BlockBackend(self):
        system = getattr(self.interface, 'dlgSystem', None) if self.interface else None
        return getattr(getattr(system, 'gameOptionDlg', None), 'backend', None)

    def SetNotification(self, key, value):
        if key == 'block':
            import uisettings
            backend = self.BlockBackend()
            base = backend.block_requests[-1] if backend and backend.block_requests else uisettings.blockMode
            desired = (base | 8) if value else (base & ~8)
            net.SendChatPacket('/setblockmode %d' % desired)
            if backend:
                backend.block_requests.append(desired)
        elif messengerHistory:
            messengerHistory.SetNotificationPreference(key, value)
        self.settings_notifications[key] = value

    def ToggleNotification(self, key):
        self.SetNotification(key, not self.settings_notifications[key])
        self.DrawSettings()

    def ToggleViewChat(self):
        self.settings_view_chat = not self.settings_view_chat
        systemSetting.SetViewChatFlag(self.settings_view_chat)
        self.view_config_dirty = True
        self.QueuePreferences()
        self.DrawSettings()

    def Ask(self, text, callback):
        if self.question:
            self.question.Close()
        self.question = uiCommon.QuestionDialog()
        self.question.SetText(text)
        self.question.SetAcceptEvent(callback)
        self.question.SetCancelEvent(ui.__mem_func__(self.CloseQuestion))
        self.question.Open()

    def CloseQuestion(self):
        if self.question:
            self.question.Close()
        self.question = None

    def AskResetSettings(self):
        self.Ask('Obnovit výchozí hodnoty této části?', event(self.ResetSettings))

    def ResetSettings(self):
        self.CloseQuestion()
        defaults = model.normalize_preferences({})
        if self.settings_page == 'Obsah':
            self.prefs['tabs'][self.settings_tab]['filters'] = list(model.AVAILABLE_FILTERS)
            self.RefreshTabs()
        elif self.settings_page == 'Vzhled':
            self.settings_view_chat = True
            systemSetting.SetViewChatFlag(True)
            self.view_config_dirty = True
            for key in ('width', 'height', 'font', 'opacity', 'idle_opacity', 'timestamps'):
                self.prefs[key] = defaults[key]
            self.anchor_x = None
            self.Refresh()
        else:
            import unifiedmessengermodel
            for key, value in dict(unifiedmessengermodel.default_notification_settings(), block=False).items():
                if self.settings_notifications[key] != value:
                    self.SetNotification(key, value)
        self.QueuePreferences()
        self.DrawSettings()

    def AskDeleteTab(self):
        self.Ask('Odstranit tuto vlastní záložku?', event(self.DeleteSettingsTab))

    def DeleteSettingsTab(self):
        self.CloseQuestion()
        if self.settings_tab:
            del self.prefs['tabs'][self.settings_tab]
            self.settings_tab = 0
            self.tab_index = 0
            self.selected = 'all'
            self.QueuePreferences()
            self.RefreshTabs()
        self.DrawSettings()

    def OnUpdate(self):
        if self.destroyed:
            return
        self.LoadPreferences()
        self.CaptureSettingsName()
        if self.prefs_dirty and self.resize_origin is None and self.move_origin is None and app.GetTime() >= self.prefs_due:
            self.FlushPreferences()
        if self.screen != (wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()):
            self.Refresh()
        self.RefreshPassiveFilters()
        chat.Update(self.chatID)
        if self.edit_mode:
            self.view.RefreshMessages(self.CurrentKinds())
        elif systemSetting.IsViewChat():
            self.passive.RefreshMessages(self.CurrentKinds())
        else:
            self.passive.Hide()
        now = app.GetTime()
        if self.repeat.due(now):
            text = self.repeat.text
            if net.IsChatInsultIn(text):
                self.PauseRepeat()
                self.Notice('Opakování pozastaveno: zpráva obsahuje zakázaný výraz.')
            else:
                if osfInfo.SHOW_EMOJI_IN_CHAT_LINE:
                    text = model.format_outgoing(text, osfInfo.EmojiFilter)
                if len(text.encode('utf-8')) > model.MAX_TEXT_BYTES:
                    self.PauseRepeat()
                    self.Notice('Opakování pozastaveno: zpráva s emotikony je příliš dlouhá.')
                else:
                    net.SendChatPacket(text, chat.CHAT_TYPE_SHOUT)
        self.repeat_button.running = self.repeat.running
        if self.repeat.running:
            remaining = self.repeat.remaining(now)
            status = 'Opakování: Volání · další za %02d:%02d' % (remaining//60, remaining%60)
        else:
            status = 'Opakování vypnuto'
        if 'repeat' in self.panels and self.panels['repeat'].IsShow():
            if self.repeat_status.GetText() != status:
                self.repeat_status.SetText(status)
            action = 'Pozastavit' if self.repeat.running else 'Spustit'
            if self.repeat_start.text.GetText() != action:
                self.repeat_start.SetText(action)

    def OnRender(self):
        if not self.edit_mode:
            return
        x, y = self.GetGlobalPosition()
        w, h = self.GetWidth(), self.GetHeight()
        controls.bar(x, y, w, h, (9/255., 10/255., 11/255.), self.prefs['opacity']/100.)
        controls.bar(x, y, w, 29, (21/255., 19/255., 19/255.))
        controls.bar(x, y+28, w, 1, (.40, .31, .23))
        controls.bar(x+10, y+h-39, w-20, 1, (.30, .24, .19))

    def Hide(self):
        if hasattr(self, 'panels'):
            self.CloseChat()
            self.passive.Hide()
            for panel in self.histories.values():
                panel.Hide()
            if self.question:
                self.question.Close()
            self.view.tip.HideToolTip()
            for button in self.buttons + self.header:
                button.OnMouseOverOut()
        ui.Window.Hide(self)

    def Destroy(self):
        self.destroyed = True
        self.repeat.pause()
        self.Hide()
        self.SavePreferences()
        for panel in list(self.panels.values()) + list(self.histories.values()):
            panel.Destroy()
        for button in self.buttons + self.header:
            button.Destroy()
        self.repeat_button = None
        self.chatInputSet.Destroy()
        self.view.Destroy()
        self.passive.Destroy()
        self.resize_grip.Destroy()
        self.move_grip.Destroy()
        self.panels = {}
        self.histories = {}
        self.buttons = []
        self.header = []
        self.interface = None
        self.sendWhisperEvent = None
        self.openChatLogEvent = None
        self.question = None
