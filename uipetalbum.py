# -*- coding: utf-8 -*-
"""Owner-approved V7 book. The validated server snapshot owns all gameplay."""
import json
import math
import app
import ui
import uiScriptLocale
import petalbumstate
import petalbumdisplay as display
import petalbumoccurrence as occurrence
import uicrimsoncontrols
import uimountk1 as K1

WindowDestroy = getattr(ui, 'WindowDestroy', lambda function: function)
ASSET_ROOT = 'd:/ymir work/ui/pet/album_c/'
WIDTH, HEIGHT = 768, 492
OPEN_SECONDS, TURN_SECONDS = .24, .25
PAPER_X, PAPER_Y, PAPER_WIDTH = 400, 59, 311
INK, MUTED, RUBY, GREEN = 0xff35241b, 0xff493626, 0xff702526, 0xff346447


def L(key):
    return getattr(uiScriptLocale, 'PET_ALBUM_' + key)


def Image(parent, x, y, filename):
    image = ui.ExpandedImageBox()
    image.SetParent(parent)
    image.AddFlag('not_pick')
    image.SetPosition(x, y)
    image.LoadImage(ASSET_ROOT + filename)
    image.Show()
    parent.owned.append(image)
    return image


def Text(parent, x, baseline, value, size=11, color=INK, center=False, bold=False, right=False):
    # Tiny glyphs lose Czech accents; probes and visible lines share this floor.
    return K1.Text(parent, x, baseline, value, max(12, size), color,
                   'right' if right else 'center' if center else 'left', bold)


class AlbumPage(ui.Window):
    def __init__(self, parent, width=WIDTH, height=HEIGHT):
        ui.Window.__init__(self)
        self.owned, self._mountOwnedChildren = [], []
        self.SetParent(parent)
        self.SetSize(width, height)
        self.SetPosition(0, 0)
        self.AddFlag('not_pick')

    @WindowDestroy
    def Destroy(self):
        self.Hide()
        for widget in self.owned + self._mountOwnedChildren:
            widget.Hide()
            if isinstance(widget, ui.Button):
                widget.SetEvent(None)
                widget.SetOverEvent(None)
                widget.SetOverOutEvent(None)
            if isinstance(widget, AlbumPage):
                widget.Destroy()
        self.owned, self._mountOwnedChildren = [], []


class PetAlbumWindow(ui.Window):
    def __init__(self):
        # Window.__init__ dispatches self.Hide(), which reads these defaults.
        self.Initialize()
        ui.Window.__init__(self)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.SetSize(WIDTH, HEIGHT)
        # pack.Get accepts .txt, not .json.
        with open('petalbumcatalog.txt', 'r') as stream:
            self.catalog = json.load(stream)
        with open('petalbumpresentation.txt', 'r') as stream:
            self.presentation = json.load(stream)
        self.state = petalbumstate.GetState()
        self.metadata = {p['id']: p for p in self.presentation['pets']}
        self.xp = {p['id']: p for p in self.presentation['xp']['pets']}
        self.journal = display.GetJournal()
        self.background = Image(self, 0, 0, 'book.png')
        self.closeButton = self.Button(self, 738, 37, 'close', ui.__mem_func__(self.Close))
        self.cover = Image(self, 0, 0, 'cover.png')
        self.closeButton.AddFlag('float')
        self.cover.AddFlag('attach')
        self.cover.AddFlag('float')
        self.cover.Hide()
        self.paper = Image(self, PAPER_X, PAPER_Y, 'paper-right.png')
        self.cover.AddFlag('float')
        self.paper.AddFlag('float')
        self.paper.Hide()
        self.Hide()

    def __del__(self):
        ui.Window.__del__(self)

    def Initialize(self):
        self.owned = []
        self.catalog = self.presentation = self.state = self.page = None
        self.background = self.closeButton = self.cover = self.paper = None
        self.metadata, self.xp = {}, {}
        self.chapter, self.selected = -1, 0
        self.tab, self.summaryTab = 'acquisition', 'overview'
        self.offset, self.detailOffset, self.newOffset = 0, 0, 0
        self.motion, self.motionStart = None, 0.0
        self.seenGeneration = -1
        self.snapshotLayout = None
        self.liveText, self.liveValues, self.liveBars = {}, {}, {}
        self.cards, self.badges, self.revealImages = [], [], []
        self.revealId, self.revealStart = None, 0.0
        self.lastUpdate = 0.0
        self.journal = None
        self.occurrenceWindow = self.occurrenceButton = None
        self.occurrenceHint = self.occurrenceFooter = None
        self.occurrencePetId = None
        self.occurrenceEnabled = None

    def Available(self):
        return bool(self.state and self.state.available and self.state.context and
                    self.presentation['hash'] == self.state.context[0])

    def Row(self, pet):
        return self.state.pets.get(pet['id']) if self.Available() else None

    def Button(self, parent, x, y, prefix, callback):
        button = ui.Button()
        button.SetParent(parent)
        button.SetPosition(x, y)
        button.SetUpVisual(ASSET_ROOT + prefix + '_normal.png')
        button.SetOverVisual(ASSET_ROOT + prefix + '_hover.png')
        button.SetDownVisual(ASSET_ROOT + prefix + '_pressed.png')
        button.SetEvent(callback)
        button.Show()
        parent.owned.append(button)
        return button

    def Hit(self, parent, x, y, width, height, callback, *args):
        button = ui.Button()
        button.SetParent(parent)
        button.SetPosition(x, y)
        button.SetSize(width, height)
        button.SetEvent(callback, *args)
        button.Show()
        parent.owned.append(button)
        return button

    def Wrapped(self, value, width, size=11, bold=False):
        probe = Text(self.page, 0, 0, '', size, INK, False, bold)
        probe.Hide()
        def measure(text):
            probe.SetText(text)
            return probe.GetTextSize()[0]
        return K1.WrappedLines(value, width, measure)

    def Lines(self, x, y, value, width, size=11, color=INK, center=False, bold=False, spacing=14):
        for index, line in enumerate(self.Wrapped(value, width, size, bold)):
            Text(self.page, x, y+index*spacing, line, size, color, center, bold)

    def Divider(self, x, y, width, color=RUBY, height=1):
        line = ui.Bar()
        line.SetParent(self.page)
        line.AddFlag('not_pick')
        line.SetPosition(x, y)
        line.SetSize(width, height)
        line.SetColor(color if color < 0x80000000 else color-0x100000000)
        line.Show()
        self.page.owned.append(line)

    def Bar(self, x, y, ratio):
        Image(self.page, x, y, 'v7/progress-empty.png')
        if ratio > 0:
            width = round(264*min(1.0, ratio))+1
            if width <= 6:
                Image(self.page, x, y, 'v7/progress-small-%d.png' % width)
            else:
                Image(self.page, x, y, 'v7/progress-left.png')
                middle = Image(self.page, x+3, y, 'v7/progress-middle.png')
                middle.SetScale(width-6, 1)
                Image(self.page, x+width-3, y, 'v7/progress-right.png')

    def LiveText(self, key, x, baseline, value, *args):
        line = Text(self.page, x, baseline, value, *args)
        self.liveText[key], self.liveValues[key] = line, value
        return line

    def SetLiveText(self, key, value):
        if key in self.liveText and self.liveValues.get(key) != value:
            self.liveText[key].SetText(value)
            self.liveValues[key] = value

    def LiveBar(self, key, x, y, ratio):
        Image(self.page, x, y, 'v7/progress-empty.png')
        bar = dict(x=x, y=y, width=None,
                   small=Image(self.page, x, y, 'v7/progress-small-1.png'),
                   left=Image(self.page, x, y, 'v7/progress-left.png'),
                   middle=Image(self.page, x+3, y, 'v7/progress-middle.png'),
                   right=Image(self.page, x, y, 'v7/progress-right.png'))
        self.liveBars[key] = bar
        self.SetLiveBar(key, ratio)

    def SetLiveBar(self, key, ratio):
        bar = self.liveBars.get(key)
        if not bar:
            return
        width = round(264*min(1.0, ratio))+1 if ratio > 0 else 0
        if width == bar['width']:
            return
        bar['width'] = width
        for name in ('small', 'left', 'middle', 'right'):
            bar[name].Hide()
        if 0 < width <= 6:
            bar['small'].LoadImage(ASSET_ROOT+'v7/progress-small-%d.png' % width)
            bar['small'].Show()
        elif width > 6:
            bar['middle'].SetScale(width-6, 1)
            bar['right'].SetPosition(bar['x']+width-3, bar['y'])
            for name in ('left', 'middle', 'right'):
                bar[name].Show()

    def Badge(self, parent, x, y, label):
        image = Image(parent, x, y, 'v7/badge-fill.png')
        Image(parent, x, y, 'v7/badge-border.png')
        line = Text(parent, x+22, y+12, label, 10, RUBY, True, True)
        self.badges.append((image, line))

    def Open(self):
        self.chapter, self.selected = -1, 0
        self.summaryTab = 'overview'
        self.SetCenterPosition()
        self.Refresh()
        self.Show()
        self.SetTop()
        self.state.ReadCaptures()
        self.motion, self.motionStart = 'open', app.GetTime()
        self.lastUpdate = self.motionStart
        self.page.Hide()
        self.cover.SetAlpha(1.0)
        self.cover.Show()
        self.cover.SetTop()
        self.closeButton.SetTop()

    def Hide(self):
        self.motion, self.revealId = None, None
        if self.cover:
            self.cover.Hide()
        if self.paper:
            self.paper.Hide()
        # A temporary interface hide must not restore an aborted blank page.
        if self.page:
            self.page.Show()
        ui.Window.Hide(self)

    def Close(self):
        self.Hide()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    @WindowDestroy
    def Destroy(self):
        self.Hide()
        if self.occurrenceWindow:
            self.occurrenceWindow.Destroy()
        if self.page:
            self.page.Destroy()
        for widget in self.owned:
            widget.Hide()
            if isinstance(widget, ui.Button):
                widget.SetEvent(None)
        self.Initialize()

    def SelectChapter(self, index, selected=0):
        if self.motion or not -1 <= index < len(self.catalog['groups']):
            return
        self.chapter, self.selected = index, selected
        self.tab, self.offset, self.detailOffset = 'acquisition', 0, 0
        self.revealId = None
        self.Refresh()
        self.page.Hide()
        self.motion, self.motionStart = 'turn', app.GetTime()
        self.paper.SetScale(1, 1)
        self.paper.SetPosition(PAPER_X, PAPER_Y)
        self.paper.Show()
        self.paper.SetTop()
        self.closeButton.SetTop()

    def SelectPet(self, index):
        if self.motion or not 0 <= index < 5:
            return
        if index != self.selected:
            self.revealId = None
            self.tab, self.offset, self.detailOffset = 'acquisition', 0, 0
        self.selected = index
        self.Refresh()

    def SelectTab(self, tab):
        if self.chapter >= 0:
            pet = self.ChapterPets()[self.selected]
            row = self.Row(pet)
            if tab == 'growth' and (not row or row['phase'] != 2):
                return
            self.tab = tab
        else:
            self.summaryTab = tab
        self.Refresh()

    def PageGrowth(self, step):
        targets = self.xp[self.ChapterPets()[self.selected]['id']]['targets']
        self.offset = max(0, min(len(targets)-1, self.offset+step))
        self.Refresh()

    def OpenNew(self, identity):
        pet = next(p for p in self.catalog['pets'] if p['id'] == identity)
        pets = [p for p in self.catalog['pets'] if p['group'] == pet['group']]
        self.SelectChapter(pet['group'], pets.index(pet))

    def Heading(self, center, overline, title, subtitle=None, subtitleSize=11, liveSubtitle=None):
        Text(self.page, center, 74, overline, 11, RUBY, True, True)
        Text(self.page, center, 97, title, 18, INK, True)
        if subtitle:
            line = Text(self.page, center, 113, subtitle, subtitleSize, MUTED, True)
            if liveSubtitle:
                self.liveText[liveSubtitle], self.liveValues[liveSubtitle] = line, subtitle

    def SyncJournal(self):
        if not self.Available():
            return
        import player
        if self.journal.Bind(player.GetName(), self.state.context):
            self.journal.Sync(self.state.pets, self.state.discoveryReceipts)

    def Refresh(self):
        self.seenGeneration = self.state.generation
        self.SyncJournal()
        if self.page:
            self.page.Destroy()
        self.occurrenceButton = None
        self.occurrenceHint = self.occurrenceFooter = self.occurrencePetId = None
        self.occurrenceEnabled = None
        self.cards, self.badges, self.revealImages = [], [], []
        self.liveText, self.liveValues, self.liveBars = {}, {}, {}
        self.page = AlbumPage(self)
        if self.chapter == -1:
            self.Contents()
        else:
            self.Chapter()
        self.page.Show()
        self.closeButton.SetTop()
        self.snapshotLayout = self.SnapshotLayout()

    def SnapshotLayout(self):
        # Revisions, XP, levels, bonuses and the server clock do not replace
        # widgets. Acquisition changes still rebuild the approved page/reveal.
        if not self.Available():
            return (False, self.state.context)
        return (True, self.state.context, tuple(
            (pet['id'], self.state.pets[pet['id']]['phase'],
             self.journal.Unread(pet['id']), self.state.discoveryReceipts.get(pet['id']))
            for pet in self.catalog['pets']))

    def UpdateSnapshot(self):
        self.SyncJournal()
        if self.snapshotLayout != self.SnapshotLayout():
            self.Refresh()
            return
        self.seenGeneration = self.state.generation
        if not self.Available():
            return
        if self.chapter == -1:
            maxed = sum(row['level'] == self.state.view['max_level'] for row in self.state.pets.values())
            self.SetLiveText('maxed', L('V7_UROVEN_D_S_35') % (self.state.view['max_level'], maxed))
            for index, cap in enumerate(self.state.view['caps']):
                self.SetLiveText(('bonus', index), '%s / %s%%' % (
                    display.Percent(self.state.bonuses[index]), display.Number(cap/1000000.0)))
            self.SetLiveText('attack', L('V7_UTOK_D_MAGICKY_UTOK_D') % (self.state.attack, self.state.magicAttack))
            cap = self.presentation['bonuses']['book_power_album_complete']
            self.SetLiveText('bookPower', L('V7_SILA_KNIH_PETA_S_S') % (
                display.Percent(self.state.bookPower), display.Number(cap/1000000.0)))
            return
        group = self.catalog['groups'][self.chapter]
        cap = display.Number(self.state.view['caps'][self.chapter]/1000000.0)
        self.SetLiveText('chapterBonus', group['bonus'] + u' | +%s%% / %s%%' % (
            display.Percent(self.state.bonuses[self.chapter]), cap))
        for card in self.cards:
            row = self.Row(card['pet'])
            if row and row['phase'] == 2:
                status = L('V7_NOVY_ULOVEK') if self.RevealAmount(card['pet']['id']) < 1 else L('V7_UR_D') % row['level']
                if card['statusValue'] != status:
                    card['status'].SetText(status)
                    card['statusValue'] = status
        pet = self.ChapterPets()[self.selected]
        row = self.Row(pet)
        if not row or row['phase'] != 2:
            return
        current, total, ratio, maximum = self.XP(pet, row)
        value, cap = self.Individual(pet, row)
        self.SetLiveText('xp', L('V7_LEVEL_MAXIMUM') if maximum else '%s / %s BZK' % (
            display.Number(current), display.Number(total)))
        self.SetLiveBar('xp', ratio)
        self.SetLiveText('level', L('V7_UROVEN_D_D') % (row['level'], self.state.view['max_level']))
        self.SetLiveText('percent', ('%.1f' % (100.0*ratio)).replace('.', ',')+' %')
        self.SetLiveText('individual', L('V7_PET_BONUS') % (display.Percent(value), display.Percent(cap))
                         if self.tab == 'growth' else '+%s %%' % display.Percent(value))
        if self.RevealAmount(pet['id']) >= 1:
            self.SetLiveText('detailStatus', L('V7_ULOVENO_UROVEN_D_D') % (row['level'], self.state.view['max_level']))

    def ChapterPets(self):
        return [p for p in self.catalog['pets'] if p['group'] == self.chapter]

    def NewPets(self):
        return [p for p in self.catalog['pets'] if self.Available() and self.journal.Unread(p['id'])]

    def Contents(self):
        self.Heading(216, L('CHRONICLE'), L('CONTENTS'))
        Text(self.page, 216, 116, L("V7_35_PETU_7_KAPITOL"), 12, MUTED, True)
        for index, group in enumerate(self.catalog['groups']):
            y = 126+index*34
            Image(self.page, 86, y+2, 'v7/chapter-%d.png' % index)
            Text(self.page, 123, y+14, group['name'], 13, INK, False, True)
            Text(self.page, 123, y+29, group['bonus'], 11, MUTED)
            if any(p['group'] == index for p in self.NewPets()):
                self.Badge(self.page, 305, y+2, L("V7_NOVE"))
            self.Hit(self.page, 82, y, 268, 33, ui.__mem_func__(self.SelectChapter), index)
        new = self.NewPets()
        if self.summaryTab == 'new':
            self.NewSummary(new)
        else:
            self.Summary(new)

    def SummaryTabs(self, new):
        for x, label, key in ((480, L("V7_PREHLED"), 'overview'), (624, L("V7_NOVE_D") % len(new), 'new')):
            active = self.summaryTab == key
            Text(self.page, x, 140, label, 12, RUBY if active else MUTED, True, active)
            self.Hit(self.page, x-58, 123, 116, 25, ui.__mem_func__(self.SelectTab), key)
        self.Divider(437 if self.summaryTab == 'overview' else 577, 147, 87 if self.summaryTab == 'overview' else 97, RUBY, 2)

    def Summary(self, new):
        available = self.Available()
        self.Heading(552, L('V7_SUMMARY'), L("V7_SILA_TVE_SBIRKY"))
        Text(self.page, 552, 116, L("V7_BONUSY_AKTIVNI_I_SE_ZAVRENYM_ALBEM") if available else L("WAITING_SERVER"), 11, MUTED, True)
        self.SummaryTabs(new)
        rows = list(self.state.pets.values()) if available else []
        owned = sum(r['phase'] == 2 for r in rows)
        maxed = sum(r['level'] == self.state.view['max_level'] for r in rows)
        complete = sum(all(self.state.pets[p['id']]['phase'] == 2 for p in self.catalog['pets'] if p['group'] == g)
                       for g in range(len(self.catalog['groups']))) if available else 0
        Text(self.page, 424, 173, L("V7_ULOVENO"), 11, RUBY, False, True)
        Text(self.page, 689, 173, '%d/35' % (owned if available else 0), 15, INK, False, True, True)
        self.Bar(424, 181, owned/float(len(self.catalog['pets'])))
        self.LiveText('maxed', 424, 207, L("V7_UROVEN_D_S_35") % (self.state.view['max_level'], maxed if available else '-'), 11, MUTED)
        Text(self.page, 689, 207, L('V7_COMPLETE_CHAPTERS') % (complete if available else '-'), 11, MUTED, False, False, True)
        Text(self.page, 424, 230, L("V7_PASIVNI_BONUSY"), 11, RUBY, False, True)
        Text(self.page, 689, 230, L("V7_NYNI_MAXIMUM"), 10, MUTED, False, False, True)
        self.Divider(424, 235, 265, 0xffc3ad86)
        for index, group in enumerate(self.catalog['groups']):
            Text(self.page, 424, 250+index*17, group['bonus'], 12)
            cap = self.state.view['caps'][index]
            value = '%s / %s%%' % (display.Percent(self.state.bonuses[index]), display.Number(cap/1000000.0)) if available else '- / %s%%' % display.Number(cap/1000000.0)
            self.LiveText(('bonus', index), 689, 250+index*17, value, 11, RUBY, False, True, True)
        self.Divider(424, 360, 265, 0xffc3ad86)
        self.LiveText('attack', 556, 376, L("V7_UTOK_D_MAGICKY_UTOK_D") % (self.state.attack, self.state.magicAttack) if available else L("V7_UTOK_MAGICKY_UTOK"), 11, INK, True, True)
        cap = self.presentation['bonuses']['book_power_album_complete']
        self.LiveText('bookPower', 552, 393, L("V7_SILA_KNIH_PETA_S_S") % (display.Percent(self.state.bookPower), display.Number(cap/1000000.0)) if available else L("V7_CEKAME_NA_POTVRZENY_STAV"), 11, MUTED, True)

    def NewSummary(self, new):
        pet = new[min(self.newOffset, len(new)-1)] if new else None
        row = self.Row(pet) if pet else None
        clue = row and row['phase'] == 1
        self.Heading(552, L('V7_SUMMARY'), L("V7_NOVA_STOPA") if clue else L("V7_NOVY_SPOLECNIK") if pet else L("V7_NOVE_ZAZNAMY"))
        Text(self.page, 552, 116, L("V7_NOVY_ZAZNAM_K_PROHLEDNUTI") if pet else L("V7_VSECHNY_OBJEVY_MAS_PROHLEDNUTE"), 11, MUTED, True)
        self.SummaryTabs(new)
        Image(self.page, 506, 170, 'v7/paw-92.png') if pet else Image(self.page, 516, 180, 'v7/chapter-empty.png')
        if not pet:
            Text(self.page, 552, 301, L("V7_ZADNY_NOVY_ZAZNAM"), 16, INK, True, True)
            Text(self.page, 552, 329, L("V7_SOUHRN_BONUSU_NAJDES_V_PREHLEDU"), 12, MUTED, True)
            return
        Text(self.page, 552, 297, pet['name'], 18, INK, True, True)
        Text(self.page, 552, 320, self.catalog['groups'][pet['group']]['name'], 12, MUTED, True)
        self.Button(self.page, 467, 337, 'v7/action', ui.__mem_func__(self.OpenNewEvent))
        Text(self.page, 552, 353, L('V7_CLUE_DETAILS') if clue else L("V7_PROHLEDNOUT_KARTU"), 11, 0xffe9d5b5, True, True)
        Text(self.page, 552, 389, L("V7_STOPA_JESTE_NEPRIDAVA_BONUS") if clue else L("V7_BONUS_JE_AKTIVNI_UZ_PO_ULOVENI"), 11, MUTED, True)

    def OpenNewEvent(self):
        new = self.NewPets()
        if new:
            self.OpenNew(new[min(self.newOffset, len(new)-1)]['id'])

    def Individual(self, pet, row):
        slot = next(index for index, item in enumerate([p for p in self.catalog['pets'] if p['group'] == pet['group']]) if item['id'] == pet['id'])
        curve = self.presentation['bonuses']['groups'][pet['group']]['level_curves'][slot]
        return (curve[row['level']-1] if row and row['phase'] == 2 else 0), curve[-1]

    def XP(self, pet, row):
        projection = self.xp[pet['id']]
        return display.LevelProgress(row, projection, self.presentation['xp']['units_per_xp'])

    def Chapter(self):
        group = self.catalog['groups'][self.chapter]
        pets = self.ChapterPets()
        available = self.Available()
        owned = sum(bool(self.Row(p) and self.Row(p)['phase'] == 2) for p in pets)
        amount = display.Percent(self.state.bonuses[self.chapter]) if available else '-'
        cap = display.Number(self.state.view['caps'][self.chapter]/1000000.0)
        self.Heading(216, L("V7_KAPITOLA_D_ULOVENO_S_5") % (self.chapter+1, owned if available else 0), group['name'],
                     group['bonus'] + (' | +%s%% / %s%%' % (amount, cap) if available else ' | -'), liveSubtitle='chapterBonus')
        self.Button(self.page, 80, 80, 'arrow_left', ui.__mem_func__(self.Previous))
        if self.chapter < len(self.catalog['groups'])-1:
            self.Button(self.page, 304, 80, 'arrow_right', ui.__mem_func__(self.Next))
        self.Button(self.page, 160, 378, 'arrow_left', ui.__mem_func__(self.ContentsEvent))
        Text(self.page, 213, 392, L('CONTENTS'), 11, RUBY, False, True)
        self.Hit(self.page, 210, 378, 95, 24, ui.__mem_func__(self.ContentsEvent))
        selectedPet = pets[self.selected]
        row = self.Row(selectedPet)
        if row and row['phase'] == 1:
            self.journal.Read(selectedPet['id'])
        elif row and row['phase'] == 2 and self.journal.Unread(selectedPet['id']) and self.revealId != selectedPet['id']:
            self.revealId, self.revealStart = selectedPet['id'], app.GetTime()
        if not row or row['phase'] != 2:
            self.tab, self.revealId = 'acquisition', None
        for index, pet in enumerate(pets):
            self.Card(index, pet)
        self.RaiseCard(self.selected)
        self.Heading(552, L("V7_ZAZNAM_D_5") % (self.selected+1), selectedPet['name'], selectedPet['rarity_name'], 12)
        caught = row and row['phase'] == 2
        if caught:
            for x, label, tab in ((480, L("V7_ZISKANI"), 'acquisition'), (624, L("V7_EXPENI"), 'growth')):
                active = self.tab == tab
                Text(self.page, x, 140, label, 12, RUBY if active else MUTED, True, active)
                self.Hit(self.page, x-58, 123, 116, 25, ui.__mem_func__(self.SelectTab), tab)
            self.Divider(438 if self.tab == 'acquisition' else 579, 147, 85 if self.tab == 'acquisition' else 91, RUBY, 2)
        else:
            Text(self.page, 552, 140, L("V7_ZISKANI"), 12, RUBY, True, True)
            self.Divider(510, 147, 85, RUBY, 2)
        if not row:
            Text(self.page, 552, 225, '-', 55, 0xffb49465, True, True)
            Text(self.page, 552, 281, L("V7_CEKAME_NA_STAV_SERVERU"), 16, INK, True, True)
            Text(self.page, 552, 308, L("V7_VLASTNICTVI_UROVEN_ANI_BONUS_ZATIM_NEZNAME"), 11, MUTED, True)
            Text(self.page, 552, 332, L("V7_POTVRZENY_STAV_SE_NACTE_AUTOMATICKY"), 11, MUTED, True)
            Text(self.page, 552, 393, L("V7_BONUS_ZATIM_NEZNAME"), 11, MUTED, True)
        elif self.tab == 'growth':
            self.Growth(selectedPet, row)
        elif row['phase'] == 1:
            self.Clue(selectedPet, row)
        elif row['phase'] == 0:
            self.Unknown(selectedPet)
        else:
            self.Caught(selectedPet, row)

    def Previous(self):
        self.SelectChapter(self.chapter-1)

    def Next(self):
        self.SelectChapter(self.chapter+1)

    def ContentsEvent(self):
        self.SelectChapter(-1)

    def RevealAmount(self, identity):
        if not self.journal.Unread(identity):
            return 1.0
        if self.revealId != identity:
            return 0.0
        elapsed = max(0.0, min(1.0, (app.GetTime()-self.revealStart)/1.6))
        return elapsed*elapsed*(3-2*elapsed)

    def Portrait(self, parent, pet, center, detail=False):
        width, height = (116, 96) if detail else (62, 62)
        reveal = self.RevealAmount(pet['id'])
        paw = None
        if reveal < 1:
            size = 82 if detail else 49
            paw = Image(parent, center[0]-round(size/2), center[1]-round(size/2), 'v7/paw-%d.png' % size)
            paw.SetAlpha(1-reveal)
        # Match the approved raster composition: paw first, portrait above it.
        image = Image(parent, center[0]-width//2, center[1]-height//2, 'v7/'+pet['id']+('-detail.png' if detail else '-card.png'))
        image.SetAlpha(reveal)
        if paw:
            self.revealImages.append((pet['id'], image, paw))
        return image

    def Card(self, index, pet):
        center = (126, 216, 306, 171, 261)[index]
        x, y = center-44, 252 if index >= 3 else 122
        window = AlbumPage(self.page, 112, 148)
        window.AddFlag('float')
        window.SetPosition(x-12, y-12)
        window.Show()
        self.page.owned.append(window)
        # Labels stay at native pixel size while the artwork animates.
        labels = AlbumPage(self.page, 112, 148)
        labels.AddFlag('float')
        labels.SetPosition(x-12, y-12)
        labels.Show()
        self.page.owned.append(labels)
        amount = .7 if index == self.selected else 0
        material = Image(window, 0, 0, 'v7/card-%d-%02d.png' % (pet['rarity'], round(amount*20)))
        row = self.Row(pet)
        phase = row['phase'] if row else -1
        if phase <= 0:
            Image(window, 25, 30, 'v7/unknown-card.png' if phase == 0 else 'v7/waiting-card.png')
        elif phase == 1:
            Image(window, 32, 36, 'v7/paw-49.png')
        else:
            self.Portrait(window, pet, (56, 61))
        reveal = self.RevealAmount(pet['id']) if phase == 2 else 1
        status = L("V7_CEKANI") if phase == -1 else L("V7_NEOBJEVENO") if phase == 0 else L("V7_STOPA") if phase == 1 else L("V7_NOVY_ULOVEK") if reveal < 1 else L("V7_UR_D") % row['level']
        statusLine = Text(labels, 56, 97, status, 8, 0xffddc79f, True, True)
        names = self.Wrapped(pet['name'], 76, 11, True)
        for line, name in enumerate(names):
            Text(labels, 56, (122 if len(names) == 1 else 112)+line*14, name, 11, INK, True, True)
        if row and self.journal.Unread(pet['id']):
            self.Badge(labels, 17, 16, L("V7_STOPA") if phase == 1 else L("V7_NOVE"))
        hit = self.Hit(self.page, x, y, 88, 124, ui.__mem_func__(self.SelectPet), index)
        hit.SetOverEvent(ui.__mem_func__(self.HoverCard), index, True)
        hit.SetOverOutEvent(ui.__mem_func__(self.HoverCard), index, False)
        sheen = Image(window, 0, 0, 'v7/reveal-00.png') if phase == 2 and reveal < 1 else None
        self.cards.append(dict(sheen=sheen, sheenFrame=0, window=window, labels=labels, material=material, amount=amount, hover=False, frame=round(amount*20),
                               x=x-12, y=y-12, pet=pet, status=statusLine, statusValue=status, hit=hit))

    def RaiseCard(self, index):
        self.cards[index]['window'].SetTop()
        self.cards[index]['labels'].SetTop()

    def HoverCard(self, index, entered):
        if index < len(self.cards):
            self.cards[index]['hover'] = entered
            if entered:
                self.RaiseCard(index)
            elif self.cards:
                self.RaiseCard(self.selected)

    def Clue(self, pet, row):
        Image(self.page, 523, 156, 'v7/paw-58.png')
        Text(self.page, 552, 232, L('V7_CLUE_FOUND'), 12, RUBY, True, True)
        self.occurrencePetId = pet['id']
        button = ui.Button()
        button.SetParent(self.page)
        button.SetUpVisual(uicrimsoncontrols.Visual('137x31', 'normal'))
        button.SetOverVisual(uicrimsoncontrols.Visual('137x31', 'hover'))
        button.SetDownVisual(uicrimsoncontrols.Visual('137x31', 'pressed'))
        button.SetDisableVisual(uicrimsoncontrols.Visual('137x31', 'disabled'))
        button.SetPosition(552-button.GetWidth()//2, 244)
        button.SetText(L('OCCURRENCE'))
        button.ButtonText.AddFlag('not_pick')
        button.Show()
        self.page.owned.append(button)
        self.occurrenceButton = button
        self.occurrenceHint = Text(self.page, 552, 286, '', 12, MUTED, True)
        days, windows, overnight = display.Schedule(self.metadata[pet['id']]['hunt_schedule'], {'anytime': L('V7_ANYTIME'), 'everyday': L('V7_EVERYDAY'), 'whole_day': L('V7_WHOLE_DAY'), 'weekdays': L('V7_WEEKDAYS')})
        multiple = len(windows) > 1
        Text(self.page, 552, 306 if multiple else 316, L('V7_WHEN_HUNT'), 12, RUBY, True, True)
        Text(self.page, 552, 326 if multiple else 338, days, 14 if days == L('V7_ANYTIME') else 13, INK, True, True)
        for index, value in enumerate(windows):
            Text(self.page, 552, (346 if multiple else 357)+index*14, value, 12, INK, True)
        if overnight:
            Text(self.page, 552, 393 if multiple else 374, L('OCCURRENCE_OVERNIGHT'), 12, MUTED, True)
        if not multiple or not overnight:
            self.occurrenceFooter = Text(self.page, 552, 398 if multiple else 392 if overnight else 386, '', 12, MUTED, True)
        self.UpdateOccurrence()

    def OccurrenceAvailable(self):
        return bool(self.Available() and self.occurrencePetId and occurrence.Available(
            self.state.pets.get(self.occurrencePetId), self.state.NowUtc()))

    def UpdateOccurrence(self):
        if not self.occurrenceButton:
            return
        enabled = self.OccurrenceAvailable()
        # Native Enable resets a pending mouse press. Only change state at
        # the schedule boundary, never on every OnUpdate between down/up.
        if enabled != self.occurrenceEnabled:
            self.occurrenceEnabled = enabled
            self.occurrenceButton.SetEvent(ui.__mem_func__(self.OpenOccurrence) if enabled else None)
            if enabled:
                self.occurrenceButton.Enable()
            else:
                self.occurrenceButton.Disable()
            self.occurrenceButton.SetTextColor((0xffe3c8a1 if enabled else 0xff8f816c)-0x100000000)
        self.occurrenceHint.SetText(L('OCCURRENCE_OPEN') if enabled else L('OCCURRENCE_TIME_ONLY'))
        if self.occurrenceFooter:
            self.occurrenceFooter.SetText(L('OCCURRENCE_ALBUM_SEARCH') if enabled else L('OCCURRENCE_CLOSED'))

    def OpenOccurrence(self):
        if not self.OccurrenceAvailable():
            return False
        if not self.occurrenceWindow:
            import uipetalbumoccurrence
            self.occurrenceWindow = uipetalbumoccurrence.PetAlbumOccurrenceWindow()
        pet = next(pet for pet in self.catalog['pets'] if pet['id'] == self.occurrencePetId)
        days, windows, overnight = display.Schedule(self.metadata[pet['id']]['hunt_schedule'], {
            'anytime': L('V7_ANYTIME'), 'everyday': L('V7_EVERYDAY'),
            'whole_day': L('V7_WHOLE_DAY'), 'weekdays': L('V7_WEEKDAYS')})
        return self.occurrenceWindow.Open(self.state, pet['id'], pet['name'], days,
                                          ' / '.join(windows) or L('V7_WHOLE_DAY'), overnight)

    def Unknown(self, pet):
        Image(self.page, 494, 153, 'v7/unknown-detail.png')
        Text(self.page, 552, 259, L("V7_VZHLED_ZATIM_NEZNAMY"), 12, RUBY, True, True)
        source = self.metadata[pet['id']]['first_display']
        lines = [(L("V7_PRVNI_STOPA"), 11, RUBY, True)]
        lines += [(line, 12, INK, False) for line in self.Wrapped(source['activity'], 261, 12)]
        lines += [(L("V7_KDY"), 11, RUBY, True)]
        lines += [(line, 11, MUTED, False) for line in self.Wrapped(source['when'], 261, 11)]
        self.detailOffset = max(0, min(self.detailOffset, max(0, len(lines)-6)))
        for index, (value, size, color, bold) in enumerate(lines[self.detailOffset:self.detailOffset+6]):
            Text(self.page, 424, 282+index*15, value, size, color, False, bold)
        self.acquisitionLineCount = len(lines)
        if len(lines) > 6:
            self.Divider(698, 274, 3, 0xffc3ad84, 94)
            height = max(18, round(94*6/len(lines)))
            top = 274+round((94-height)*self.detailOffset/max(1, len(lines)-6))
            self.Divider(697, top, 4, RUBY, height)
            Text(self.page, 552, 375, L("V7_POSUN_TEXT_D_D_Z_D") % (self.detailOffset+1, min(self.detailOffset+6, len(lines)), len(lines)), 10, MUTED, True)
        value, cap = self.Individual(pet, None)
        Text(self.page, 552, 393, L('V7_PET_MAXIMUM') % display.Percent(cap), 11, MUTED, True)

    def Caught(self, pet, row):
        self.Portrait(self.page, pet, (552, 201), True)
        reveal = self.RevealAmount(pet['id'])
        status = L("V7_NOVY_ULOVEK") if reveal < 1 else L("V7_ULOVENO_UROVEN_D_D") % (row['level'], self.state.view['max_level'])
        self.detailStatus = self.LiveText('detailStatus', 552, 259, status, 12, RUBY if reveal < 1 else GREEN, True, True)
        current, total, ratio, maximum = self.XP(pet, row)
        Text(self.page, 424, 282, L("V7_XP_NEXT_LEVEL"), 11, MUTED)
        self.LiveText('xp', 689, 282, L('V7_LEVEL_MAXIMUM') if maximum else '%s / %s BZK' % (display.Number(current), display.Number(total)), 11, RUBY, False, True, True)
        self.LiveBar('xp', 424, 290, ratio)
        value, cap = self.Individual(pet, row)
        Text(self.page, 424, 321, L("V7_PASIVNI_BONUS"), 11, RUBY, False, True)
        self.LiveText('individual', 689, 321, '+%s %%' % display.Percent(value), 15, INK, False, True, True)
        Text(self.page, 424, 338, self.catalog['groups'][pet['group']]['bonus'], 12, MUTED)
        Text(self.page, 552, 393, L('V7_PET_MAXIMUM') % display.Percent(cap), 11, MUTED, True)

    def Growth(self, pet, row):
        current, total, ratio, maximum = self.XP(pet, row)
        self.LiveText('level', 424, 174, L("V7_UROVEN_D_D") % (row['level'], self.state.view['max_level']), 12, INK, False, True)
        self.LiveText('percent', 689, 174, ('%.1f' % (100.0*ratio)).replace('.', ',')+' %', 12, RUBY, False, True, True)
        self.LiveBar('xp', 424, 182, ratio)
        Text(self.page, 552, 197, L('V7_XP_NEXT_LEVEL'), 11, MUTED, True)
        self.LiveText('xp', 552, 210, L('V7_LEVEL_MAXIMUM') if maximum else '%s / %s BZK' % (display.Number(current), display.Number(total)), 14, INK, True, True)
        Text(self.page, 424, 233, L("V7_CIM_SE_EXPI"), 11, RUBY, False, True)
        Text(self.page, 689, 233, L("V7_XP_ZA_JEDNU_AKCI"), 11, MUTED, False, False, True)
        self.Divider(424, 238, 265, 0xffc3ad86)
        targets = self.xp[pet['id']]['targets']
        rows = display.GrowthRows(targets, self.offset, self.Wrapped)
        for target, y, names, meta in rows:
            for n, name in enumerate(names):
                Text(self.page, 424, y+n*14, name, 12, INK, False, True)
            Text(self.page, 689, y, '+'+display.Number(target['reward_xp'])+' XP', 11, RUBY, False, True, True)
            for n, line in enumerate(meta):
                Text(self.page, 424, y+len(names)*14+1+n*13, line, 11, MUTED)
        if len(targets) > len(rows):
            if self.offset > 0:
                self.Button(self.page, 480, 357, 'arrow_left', ui.__mem_func__(self.GrowthPrevious))
            else:
                Image(self.page, 480, 357, 'arrow_left_normal.png').SetAlpha(.35)
            if self.offset+len(rows) < len(targets):
                self.Button(self.page, 576, 357, 'arrow_right', ui.__mem_func__(self.GrowthNext))
            else:
                Image(self.page, 576, 357, 'arrow_right_normal.png').SetAlpha(.35)
            Text(self.page, 552, 373, L("V7_D_D_D") % (self.offset+1, self.offset+len(rows), len(targets)), 10, MUTED, True)
        value, cap = self.Individual(pet, row)
        self.LiveText('individual', 552, 393, L('V7_PET_BONUS') % (display.Percent(value), display.Percent(cap)), 11, MUTED, True)

    def GrowthPrevious(self):
        self.PageGrowth(-1)

    def GrowthNext(self):
        self.PageGrowth(1)

    def OnMouseWheel(self, length):
        if self.motion or self.chapter < 0:
            return False
        pet = self.ChapterPets()[self.selected]
        row = self.Row(pet)
        if row and row['phase'] == 0 and getattr(self, 'acquisitionLineCount', 0) > 6:
            self.detailOffset = max(0, min(self.acquisitionLineCount-6, self.detailOffset + (-1 if length > 0 else 1)))
            self.Refresh()
            return True
        if row and row['phase'] == 2 and self.tab == 'growth':
            self.PageGrowth(-1 if length > 0 else 1)
            return True
        return False

    def OnUpdate(self):
        if not self.state:
            return
        now = app.GetTime()
        self.UpdateOccurrence()
        delta = max(0.0, min(.25, now-self.lastUpdate))
        self.lastUpdate = now
        if self.seenGeneration != self.state.generation and not self.motion:
            self.UpdateSnapshot()
        if self.motion:
            duration = OPEN_SECONDS if self.motion == 'open' else TURN_SECONDS
            progress = max(0.0, min(1.0, (now-self.motionStart)/duration))
            if progress >= 1:
                self.motion = None
                self.cover.Hide()
                self.paper.Hide()
                self.page.Show()
                if self.revealId:
                    self.revealStart = now
            elif self.motion == 'open':
                self.cover.SetAlpha(1-progress)
            else:
                scale = max(.01, abs(1-2*progress))
                self.paper.SetScale(scale, 1)
                self.paper.SetPosition(PAPER_X if progress < .5 else 368-int(PAPER_WIDTH*scale), PAPER_Y)
            return
        # Scale only artwork; sibling text keeps integer positions and native size.
        import wndMgr
        transform = getattr(wndMgr, 'SetWindowPresentationScale', None)
        for card in self.cards:
            target = 1.0 if card['hover'] else .7 if card is self.cards[self.selected] else 0.0
            card['amount'] += (target-card['amount'])*(1-math.exp(-delta/.09))
            amount = card['amount']
            position = (card['x'], card['y']-round(2*amount))
            card['window'].SetPosition(*position)
            card['labels'].SetPosition(*position)
            if transform:
                scale = 1+.06*amount-(.025 if card['hit'].IsDown() else 0)
                transform(card['window'].hWnd, scale, scale)
            frame = round(amount*20)
            if card['sheen']:
                reveal = self.RevealAmount(card['pet']['id'])
                sheenFrame = round(reveal*32)
                if sheenFrame != card['sheenFrame']:
                    card['sheen'].LoadImage(ASSET_ROOT+'v7/reveal-%02d.png' % sheenFrame)
                    card['sheenFrame'] = sheenFrame
            if frame != card['frame']:
                card['material'].LoadImage(ASSET_ROOT+'v7/card-%d-%02d.png' % (card['pet']['rarity'], frame))
                card['frame'] = frame
        pulse = .68+.32*(.5+.5*math.sin(now*2*math.pi/1.2))
        for image, line in self.badges:
            image.SetAlpha(pulse)
        for identity, image, paw in self.revealImages:
            amount = self.RevealAmount(identity)
            image.SetAlpha(amount)
            paw.SetAlpha(1-amount)
        if self.revealId and self.RevealAmount(self.revealId) >= 1:
            self.journal.Read(self.revealId)
            self.revealId = None
            self.Refresh()
