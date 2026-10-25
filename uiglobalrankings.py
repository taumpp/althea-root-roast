# Global cumulative rankings. Scores and placement are exclusively server-owned.
import app
import binascii
import dbg
import localeInfo
import net
import player
import ui
import uir1
from _weakref import proxy

# This UI fork uses explicit cleanup without the optional decorator.
WindowDestroy = getattr(ui, "WindowDestroy", lambda function: function)

CATEGORIES = ((0, 'GLOBAL_RANK_LEVEL', 'd:/ymir work/ui/game/player_ranking/global_r1/level.png'), (8, 'GLOBAL_RANK_TIME', 'd:/ymir work/ui/game/player_ranking/global_r1/time.png'), (1, 'GLOBAL_RANK_METIN', 'd:/ymir work/ui/game/player_ranking/global_r1/metin.png'), (4, 'GLOBAL_RANK_BOSS', 'd:/ymir work/ui/game/player_ranking/global_r1/boss.png'), (6, 'GLOBAL_RANK_MONSTER', 'd:/ymir work/ui/game/player_ranking/global_r1/monster.png'), (3, 'GLOBAL_RANK_DUNGEON', 'd:/ymir work/ui/game/player_ranking/global_r1/dungeon.png'), (9, 'GLOBAL_RANK_MISSION', 'icon/item/50307.tga'), (12, 'GLOBAL_RANK_FISH', 'icon/item/27806.tga'), (13, 'GLOBAL_RANK_MINING', 'icon/item/29101.tga'), (11, 'GLOBAL_RANK_REROLL', 'icon/item/71084.tga'), (10, 'GLOBAL_RANK_CHEST', 'icon/item/boss_box.tga'))
BY_MODE = dict((row[0], row) for row in CATEGORIES)
COL_RANK, COL_NAME, COL_LEVEL, COL_VALUE = 266, 312, 550, 750


def tr(key):
    return getattr(localeInfo, key, key)


def number(value):
    return "{:,}".format(int(value)).replace(',', ' ')


def value_text(mode, value):
    if mode == 8:
        hours, minutes = divmod(int(value), 60)
        return "%s h %02d min" % (number(hours), minutes)
    return number(value)


class Category(uir1.Interactive):
    def __init__(self, owner, row, index):
        uir1.Interactive.__init__(self)
        self.owner = proxy(owner)
        self.mode = row[0]
        self.selected = False
        self.SetParent(owner)
        self.SetPosition(10, 102 + index * 34)
        self.SetSize(202, 32)
        self.band = uir1.Band(self, 0, 0, 202, 32)
        self.marker = uir1.Rect(self, 0, 7, 2, 18, uir1.T.RED)
        self.icon = ui.ExpandedImageBox()
        self.icon.SetParent(self)
        self.icon.AddFlag('not_pick')
        self.icon.LoadImage(row[2])
        w, h = self.icon.GetWidth(), self.icon.GetHeight()
        scale = min(1.0, 32.0 / max(1, w), 32.0 / max(1, h))
        self.icon.SetScale(scale, scale)
        self.icon.SetPosition(4 + (32-int(w*scale))//2, (32-int(h*scale))//2)
        self.icon.Show()
        self.label = uir1.Text(self, tr(row[1]), 40, 16, owner.kit.font('text_s'), uir1.T.INK_DIM)
        self.Show()
        self.paint()

    def click(self):
        self.owner.DoChange(self.mode)

    def paint(self):
        if not hasattr(self, 'band'):
            return
        self.band.SetState('selected' if self.selected else self.state() if self.hovered else 'normal')
        self.label.SetPackedFontColor(uir1.T.IVORY if self.selected else uir1.T.INK_DIM)
        if self.selected:
            self.marker.Show()
        else:
            self.marker.Hide()


class RankInfo(ui.ScriptWindow):
    def __init__(self):
        ui.ScriptWindow.__init__(self)
        self.Initialize()
        self.AddFlag('float')
        self.AddFlag('movable')
        self.SetSize(780, 560)
        self.kit = uir1.Kit()
        self.chrome = uir1.Chrome(self, self.kit, 780, 560, tr('GLOBAL_RANK_TITLE'), ui.__mem_func__(self.Close))
        self._Build()
        self.SetCenterPosition()

    def Initialize(self):
        self.kit = self.chrome = None
        self.widgets = []
        self.buttons = []
        self.rows = []
        self.own = None
        self.bCurPage = 0
        self.request = 0
        self.active_request = None
        self.loading = False
        self.pending = False
        self.ready_at = 0.0
        self.deadline = 0.0
        self.refresh_at = 0.0
        self.response_error = False
        self.row_counts = dict(received=0, accepted=0, stale=0, format=0, name=0)
        self.diagnostic_at = 0.0
        self.title = self.subtitle = self.unit = self.status = None

    def __del__(self):
        ui.ScriptWindow.__del__(self)

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def _Text(self, text, x, y, role='text_s', color=None, align='left'):
        return self._Keep(uir1.Text(self, text, x, y, self.kit.font(role),
                                   uir1.T.INK_DIM if color is None else color, align))

    def _Build(self):
        self._Keep(uir1.Rect(self, 3, 32, 217, 525, uir1.T.SIDE, 0.75))
        self._Keep(uir1.Rect(self, 220, 32, 1, 525, uir1.T.LINE))
        self._Text(tr('GLOBAL_RANK_CATEGORIES'), 16, 53, 'title', uir1.T.IVORY)
        self._Text(tr('GLOBAL_RANK_TOTALS'), 16, 77)
        self._Keep(uir1.Rect(self, 14, 94, 192, 1, uir1.T.LINE))
        self.buttons = [Category(self, row, i) for i, row in enumerate(CATEGORIES)]
        self._Keep(uir1.Rect(self, 14, 490, 192, 1, uir1.T.LINE))
        self._Text(tr('GLOBAL_RANK_CATEGORY_COUNT'), 16, 514)
        self._Text(tr('GLOBAL_RANK_ALL_TIME'), 16, 537, 'text_xs', uir1.T.MUTED)
        self.title = self._Text('', 236, 54, 'text_l', uir1.T.IVORY)
        self.subtitle = self._Text('', 236, 79)
        self._Keep(uir1.Frame(self, 236, 101, 528, 356, 'panel'))
        self._Keep(uir1.Rect(self, 238, 103, 524, 26, uir1.T.SIDE, 0.85))
        for key, x, align in [('POSITION', COL_RANK, 'center'), ('NAME', COL_NAME, 'left'), ('LEVEL', COL_LEVEL, 'center')]:
            self._Text(tr('GLOBAL_RANK_' + key), x, 116, color=uir1.T.MUTED, align=align)
        self.unit = self._Text('', COL_VALUE, 116, color=uir1.T.MUTED, align='right')
        for i in range(10):
            y = int(round(130 + i*32.4))
            if i % 2 == 0:
                self._Keep(uir1.Rect(self, 238, y, 524, 32, uir1.T.SIDE, 0.36))
            self.rows.append(self._Cells(int(round(146 + i*32.4))))
        self._Text(tr('GLOBAL_RANK_OWN'), 236, 479)
        self._Keep(uir1.Band(self, 236, 495, 528, 35, 'selected'))
        self._Keep(uir1.Rect(self, 236, 503, 2, 19, uir1.T.RED))
        self.own = self._Cells(512)
        self._Text('TOP 10', 236, 545, 'text_xs', uir1.T.MUTED)
        self.status = self._Text('', 762, 545, 'text_xs', uir1.T.MUTED, 'right')
        self._Select()
        self._Clear()

    def _Cells(self, y):
        return [self._Text('', x, y, 'text' if i in (1, 3) else 'text_s', align=align)
                for i, (x, align) in enumerate([(COL_RANK, 'center'), (COL_NAME, 'left'),
                                              (COL_LEVEL, 'center'), (COL_VALUE, 'right')])]

    def _Select(self):
        if self.bCurPage not in BY_MODE:
            self.bCurPage = 0
        row = BY_MODE[self.bCurPage]
        self.title.SetText(tr(row[1] + '_TITLE'))
        self.subtitle.SetText(tr(row[1] + '_SUBTITLE'))
        self.unit.SetText(tr(row[1] + '_UNIT'))
        for button in self.buttons:
            button.selected = button.mode == self.bCurPage
            button.paint()

    def _Clear(self):
        for row in self.rows:
            for line in row:
                line.SetText('')
        self.own[0].SetText('-')
        self.own[1].SetText(player.GetMainCharacterName() + ' ' + tr('GLOBAL_RANK_YOU'))
        self.own[2].SetText(str(player.GetStatus(player.LEVEL)))
        self.own[3].SetText(tr('GLOBAL_RANK_EMPTY'))

    def Show(self):
        if self.chrome is None:
            return
        self._Select()
        ui.ScriptWindow.Show(self)
        self.SetTop()
        self.DoChange(self.bCurPage)

    def Open(self):
        self.Show()

    def DoChange(self, mode):
        if mode not in BY_MODE:
            return
        self.bCurPage = mode
        self._Select()
        self._Clear()
        self.active_request = None
        self.loading = False
        self.pending = True
        self.status.SetText(tr('GLOBAL_RANK_LOADING'))
        self._Request()

    def _Request(self):
        now = app.GetTime()
        if not self.IsShow() or not self.pending or now < self.ready_at:
            return
        self.request = (self.request % 999999998) + 1
        self.active_request = (self.request, self.bCurPage)
        self.pending = False
        self.loading = True
        self.response_error = False
        self.row_counts = dict(received=0, accepted=0, stale=0, format=0, name=0)
        self.ready_at = now + 1.15
        self.deadline = now + 10.0
        net.SendChatPacket('/req_info_rank global %d %d' % (self.bCurPage, self.request))

    def OnUpdate(self):
        now = app.GetTime()
        if self.pending and now >= self.ready_at:
            self._Request()
        elif self.loading and now >= self.deadline:
            self.loading = False
            self.active_request = None
            self.status.SetText(tr('GLOBAL_RANK_ERROR'))
        elif not self.loading and not self.pending and self.refresh_at and now >= self.refresh_at:
            self.refresh_at = 0.0
            self.pending = True
            self.status.SetText(tr('GLOBAL_RANK_REFRESHING'))

    def _RejectRow(self, reason):
        self.row_counts[reason] += 1
        if reason != 'stale' and self.active_request is not None:
            self.response_error = True
            self.status.SetText(tr('GLOBAL_RANK_ERROR'))

    def _MatchesResponse(self, request, mode):
        try:
            key = (int(request), int(mode))
        except (TypeError, ValueError, OverflowError):
            self._RejectRow('format')
            return False
        if self.active_request != key:
            self._RejectRow('stale')
            return False
        return True

    def Begin(self, request, mode):
        if not self._MatchesResponse(request, mode):
            return
        self._Clear()

    def Row(self, request, mode, own, rank, level, value, encoded_name):
        self.row_counts['received'] += 1
        if not self._MatchesResponse(request, mode):
            return
        try:
            rank, own, level, value = int(rank), int(own), int(level), int(value)
        except (TypeError, ValueError, OverflowError):
            self._RejectRow('format')
            return
        if (own not in (0, 1) or not 0 <= level <= 255 or
                not 0 <= value <= 9223372036854775807 or rank < 0 or
                (not own and not 1 <= rank <= 10)):
            self._RejectRow('format')
            return
        try:
            name = binascii.unhexlify(encoded_name)
            if not name or len(name) > 24:
                self._RejectRow('name')
                return
            if not isinstance(name, str):
                name = name.decode('utf-8')
        except (TypeError, ValueError, UnicodeError, binascii.Error):
            self._RejectRow('name')
            return
        cells = self.own if own else self.rows[rank-1]
        texts = [str(rank).zfill(2) if rank else '-', name,
                 str(level), value_text(int(mode), value)]
        if own:
            texts[1] += ' ' + tr('GLOBAL_RANK_YOU')
            if not rank:
                texts[3] = tr('GLOBAL_RANK_EMPTY')
        for i, (line, text) in enumerate(zip(cells, texts)):
            if i == 1:
                uir1.Fit(line, text, COL_LEVEL - COL_NAME - 32)
            else:
                line.SetText(text)
            line.SetPackedFontColor(0xFFD3BD93 if i == 0 and (own or rank <= 3)
                                    else uir1.T.IVORY if i in (1, 3) else uir1.T.INK_DIM)
        self.row_counts['accepted'] += 1

    def End(self, request, mode):
        if not self._MatchesResponse(request, mode):
            return
        self.loading = False
        now = app.GetTime()
        self.refresh_at = now + 30.0
        self.status.SetText(tr('GLOBAL_RANK_ERROR' if self.response_error else 'GLOBAL_RANK_UPDATED'))
        if self.response_error and now >= self.diagnostic_at:
            self.diagnostic_at = now + 30.0
            dbg.TraceError('GLOBAL_RANK_RECEIVE v=1 received=%d accepted=%d stale=%d format=%d name=%d' %
                           tuple(self.row_counts[key] for key in ('received', 'accepted', 'stale', 'format', 'name')))

    def Close(self):
        self.active_request = None
        self.pending = self.loading = False
        self.refresh_at = 0.0
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    # Existing interface entry points for the legacy weekly protocol remain
    # callable while server and content roll out independently.
    def SetItemToolTip(self, tooltip):
        pass

    def SetResetTime(self, time, interval):
        pass

    def SetRewardItem(self, *args):
        pass

    def AppendInfo(self, *args):
        pass

    @WindowDestroy
    def Destroy(self):
        self.Close()
        for widget in self.widgets:
            widget.Hide()
        for button in self.buttons:
            button.Hide()
        if self.chrome:
            self.chrome.Destroy()
        self.ClearDictionary()
        self.Initialize()
