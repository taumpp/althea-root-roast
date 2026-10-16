# -*- coding: utf-8 -*-
from copy import deepcopy
import re
import item
import net
import ui
import wndMgr
import fontconfig
import uicrimsoncontrols
import uitooltip
from uicrimsonember import SettingsScrollBar
import marketfilters as model

ASSETS = 'd:/ymir work/ui/public/crimson/controls/market_filters/'
INPUTS = 'd:/ymir work/ui/public/crimson/controls/inputs/'
TEXT = 0xffeadfc8
MUTED = 0xffb4aa98
ACCENT = 0xffdab16c
ERROR = 0xffff7979


def label(parent, x, y, text, width=568, role=fontconfig.ROLE_BODY, color=TEXT):
    widget = ui.TextLine()
    widget.SetParent(parent)
    widget.SetPosition(x, y)
    widget.AddFlag('not_pick')
    widget.SetFontName(fontconfig.FontForRole(role))
    widget.SetText(text)
    set_color(widget, color)
    widget.SetLimitWidth(width)
    widget.Show()
    return widget


def set_color(widget, color):
    widget.SetFontColor(((color >> 16) & 255) / 255.0,
        ((color >> 8) & 255) / 255.0, (color & 255) / 255.0)


def fit_label(widget, text, width):
    widget.SetText(text)
    if widget.GetTextSize()[0] <= width: return
    while text and widget.GetTextSize()[0] > width:
        text = text[:-1]
        widget.SetText(text + '…')


def input_box(parent, x, y, width=90, placeholder='', value=''):
    image = ui.ImageBox()
    image.SetParent(parent)
    image.SetPosition(x, y)
    image.LoadImage(INPUTS + {61: 'parameter_02.tga', 90: 'parameter_03.tga', 220: 'parameter_06.tga'}[width])
    image.Show()
    edit = ui.EditLine()
    edit.SetParent(image)
    edit.SetPosition(6, 0)
    edit.SetSize(width - 12, 18)
    edit.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_BODY))
    edit.SetMax(64 if width == 220 else 6)
    edit.SetInfoMessage(placeholder)
    edit.SetText(str(value))
    edit.Show()
    return image, edit


def bonus_text(kind):
    if kind not in uitooltip.ItemToolTip.AFFECT_DICT:
        return None
    try:
        text = str(uitooltip.GET_AFFECT_STRING(kind, 12345))
        if not text or text == 'None': return None
        unit = '%' if '%' in text else 'bodů'
        name = re.sub(r'[+−-]?\s*12345(?:[.,]0+)?\s*%?', '', text)
        return ' '.join(name.split()).strip(' :'), unit
    except (KeyError, TypeError, ValueError):
        return None


class FilterChoice(ui.Button):
    def __init__(self, parent, x, y, width, text, event, selected=False, dropdown=False):
        ui.Button.__init__(self)
        self.SetParent(parent)
        self.SetPosition(x, y)
        family = 'dropdown' if dropdown else 'selection_row'
        self.SetUpVisual(ASSETS + '%s_%s_%d.png' % (family, 'normal' if dropdown or not selected else 'selected', width))
        self.SetOverVisual(ASSETS + '%s_hover_%d.png' % (family, width))
        self.SetDownVisual(ASSETS + '%s_%s_%d.png' % (family, 'open' if dropdown else 'selected', width))
        self.SetDisableVisual(ASSETS + '%s_disabled_%d.png' % (family, width))
        self.label = label(self, 9 if dropdown else 6, 11 if dropdown else 12, text,
            width - (36 if dropdown else 12))
        self.label.SetVerticalAlignCenter()
        fit_label(self.label, text, width - (36 if dropdown else 12))
        self.SetEvent(event)
        self.Show()


class FilterPicker(ui.BoardWithTitleBar):
    VISIBLE = 6
    ROW_HEIGHT = 27

    def __init__(self, owner):
        ui.BoardWithTitleBar.__init__(self)
        self.SetParent(owner)
        self.owner = owner
        self.AddFlag('float')
        self.SetSize(350, 292)
        self.SetTitleName('Výběr filtru')
        self.SetCloseEvent(self.Close)
        self.options = []
        self.filtered = []
        self.rows = []
        self.start = 0
        self.selectEvent = None
        self.anchor = None
        self.ownerPosition = None
        self.searchImage, self.search = input_box(self, 24, 44, 220, 'Hledat…')
        self.search.OnIMEUpdate = ui.__mem_func__(self._SearchChanged)
        self.search.SetEscapeEvent(self.OnPressEscapeKey)
        self.search.SetReturnEvent(self._SelectFirst)
        self.caption = label(self, 24, 72, '', 302, color=MUTED)
        self.scrollBar = SettingsScrollBar()
        self.scrollBar.SetParent(self)
        self.scrollBar.SetPosition(314, 97)
        self.scrollBar.SetScrollBarSize(self.VISIBLE * self.ROW_HEIGHT)
        self.scrollBar.SetScrollEvent(self._Scrolled)
        self.SetOnRunMouseWheelEvent(self._Wheel)
        self.Hide()

    def Open(self, anchor, title, options, selected, event):
        self.Close()
        self.anchor = anchor
        self.selectEvent = event
        self.options = list(options)
        self.selected = selected
        self.SetTitleName(title)
        self.search.SetText('')
        self._Filter()
        x, y = anchor.GetGlobalPosition()
        ownerX, ownerY = self.owner.GetGlobalPosition()
        screenW, screenH = wndMgr.GetScreenWidth(), wndMgr.GetScreenHeight()
        top = y + anchor.GetHeight() + 3
        if top + self.GetHeight() > screenH - 8: top = y - self.GetHeight() - 3
        x = max(8, min(x, screenW - self.GetWidth() - 8))
        top = max(8, min(top, screenH - self.GetHeight() - 8))
        self.SetPosition(x - ownerX, top - ownerY)
        self.ownerPosition = (ownerX, ownerY)
        self.Show()
        self.SetTop()
        self.search.SetFocus()

    def _SearchChanged(self):
        ui.EditLine.OnIMEUpdate(self.search)
        self._Filter()

    def _Filter(self):
        query = model.folded(self.search.GetText().strip())
        self.filtered = [row for row in self.options if query in model.folded(row[1])]
        self.start = 0
        count = len(self.filtered)
        self.caption.SetText('%d možností' % count if count else 'Žádná odpovídající možnost')
        if count > self.VISIBLE:
            self.scrollBar.SetMiddleBarSize(max(20.0 / (self.VISIBLE * self.ROW_HEIGHT), float(self.VISIBLE) / count))
            self.scrollBar.SetScrollStep(1.0 / (count - self.VISIBLE))
            self.scrollBar.SetPos(0.0)
            self.scrollBar.Show()
        else:
            self.scrollBar.Hide()
        self._Rows()

    def _Rows(self):
        for row in self.rows:
            row.SetEvent(None)
            row.Hide()
        self.rows = []
        for index, (value, text) in enumerate(self.filtered[self.start:self.start + self.VISIBLE]):
            row = FilterChoice(self, 24, 97 + index * self.ROW_HEIGHT, 278, text,
                lambda key=value: self._Select(key), value == self.selected)
            row.SetOnRunMouseWheelEvent(self._Wheel)
            row.SetToolTipText(text)
            self.rows.append(row)

    def _Scrolled(self):
        maximum = max(0, len(self.filtered) - self.VISIBLE)
        self.start = min(maximum, int(self.scrollBar.GetPos() * maximum + 0.5))
        self._Rows()

    def _Wheel(self, down):
        maximum = max(0, len(self.filtered) - self.VISIBLE)
        if maximum:
            # Keep row movement independent of the shared thumb's integer pixels.
            self.start = min(maximum, max(0, self.start + (1 if down else -1)))
            self.scrollBar.SetPos(float(self.start) / maximum, moveEvent=False)
            self._Rows()
        return True

    def _SelectFirst(self):
        if self.filtered: self._Select(self.filtered[0][0])
        return True

    def _Select(self, value):
        event = self.selectEvent
        self.Close()
        if event: event(value)

    def Close(self):
        self.search.KillFocus()
        self.KillFocus()
        self.Hide()
        self.selectEvent = None
        self.anchor = None

    def OnUpdate(self):
        if self.ownerPosition != self.owner.GetGlobalPosition(): self.Close()

    def OnPressEscapeKey(self):
        self.Close()
        return True

    def Destroy(self):
        self.Close()
        self.scrollBar.Destroy()
        self.search.OnIMEUpdate = None
        self.search.SetReturnEvent(None)
        self.search.SetEscapeEvent(None)
        for row in self.rows: row.SetEvent(None)
        self.rows = []
        self.owner = None


class AdvancedMarketFilterDialog(ui.BoardWithTitleBar):
    def __init__(self, applyEvent):
        ui.BoardWithTitleBar.__init__(self)
        self.applyEvent = applyEvent
        self.state = model.FilterState()
        self.widgets = []
        self.edits = {}
        self.bonusValues = []
        self.bonusKinds = []
        self.catalogLoaded = False
        self.SetSize(616, 300)
        self.SetTitleName('Filtry předmětů')
        self.SetCloseEvent(self.Close)
        self.AddFlag('movable')
        self.AddFlag('float')
        self.picker = FilterPicker(self)
        self.Hide()

    def LoadCatalog(self):
        # Re-read on every use: the capability is per server session.
        self.state.set_other_available(
            getattr(net, 'IsVirtualMarketCategoryOtherAvailable', lambda: 0)())
        if not self.catalogLoaded and hasattr(item, 'GetMarketFilterCatalog'):
            catalog = item.GetMarketFilterCatalog()
            if catalog:
                self.state.set_catalog(catalog)
                self.catalogLoaded = True

    def _Keep(self, widget):
        self.widgets.append(widget)
        return widget

    def _Label(self, x, y, text, heading=False, width=568, color=TEXT):
        return self._Keep(label(self, x, y, text, width,
            fontconfig.ROLE_SECTION if heading else fontconfig.ROLE_BODY, color))

    def _Select(self, key, value):
        self._ReadEdits()
        self.state.change(**{key: value})
        self._Build()

    def _Dropdown(self, x, y, width, key, options, title):
        value = self.state.draft.get(key, -1)
        text = dict(options).get(value, options[0][1])
        button = self._Keep(FilterChoice(self, x, y, width, text, None, dropdown=True))
        button.SetEvent(lambda: self.picker.Open(button, title, options, value,
            lambda selected: self._Select(key, selected)))
        button.SetToolTipText(text)
        if len(options) <= 1: button.Disable()
        return button

    def _Range(self, x, y, key, title, options=None, percent=False):
        self._Label(x, y, title, True, 272)
        for index, bound in enumerate(('minimum_', 'maximum_')):
            field = bound + key
            at = x + index * 140
            if options is not None:
                self._Dropdown(at, y + 22, 100, field, [(-1, 'Bez meze')] + options, title)
            else:
                value = self.state.draft.get(field, '')
                image, edit = input_box(self, at, y + 24, 90, 'Od' if not index else 'Do', value)
                self._Keep(image)
                self.edits[field] = edit
                edit.SetNumberMode()
                edit.SetEscapeEvent(self.OnPressEscapeKey)
                edit.SetReturnEvent(self._Apply)
                if percent: self._Label(at + 94, y + 24, '%', width=15)
        self._Label(x + 118, y + 23, '–', width=20, color=ACCENT)

    def _Choices(self, y, key, title, options, width):
        self._Label(24, y, title, True)
        selected = self.state.draft.get(key, -1)
        for index, (value, text) in enumerate(options):
            self._Keep(FilterChoice(self, 24 + index * (width + 8), y + 22, width, text,
                lambda choice=value: self._Select(key, choice), value == selected))

    def _Action(self, x, y, text, event, family='100x21'):
        button = self._Keep(ui.Button())
        button.SetParent(self)
        button.SetPosition(x, y)
        uicrimsoncontrols.ApplyVisuals(button, family)
        button.SetText(text)
        button.SetEvent(event)
        button.Show()
        return button

    def _ClearWidgets(self):
        for edit in list(self.edits.values()) + self.bonusValues:
            edit.KillFocus()
            edit.SetEscapeEvent(None)
            edit.SetReturnEvent(None)
        for widget in self.widgets:
            if isinstance(widget, ui.Button): widget.SetEvent(None)
            widget.Hide()
        self.widgets = []
        self.edits = {}
        self.bonusValues = []
        self.bonusKinds = []

    def _Build(self):
        self.picker.Close()
        self._ClearWidgets()
        state = self.state.draft
        info = model.profile(state, self.state.catalog)
        fields = info['fields']
        self._Label(24, 38, 'Kategorie', True, 272)
        self._Label(320, 38, 'Druh kamene' if state['category'] == 6 else 'Podkategorie', True, 272)
        self._Dropdown(24, 60, 272, 'category', self.state.categories(), 'Kategorie')
        self._Dropdown(320, 60, 272, 'subtype', model.subcategories(state['category'], self.state.catalog), 'Podkategorie')
        y = 96
        if 'job' in fields:
            self._Choices(y, 'job', 'Povolání', model.JOBS, 88)
            y += 62
        if 'level' in fields or 'refine' in fields:
            if 'level' in fields: self._Range(24, y, 'level', 'Požadovaný level')
            if 'refine' in fields: self._Range(320, y, 'refine', 'Vylepšení', [(v, '+%d' % v) for v in info['refines']])
            y += 62
        if 'gender' in fields:
            self._Label(24, y + 3, 'Pohlaví', True, 100)
            selected = state.get('gender', -1)
            for index, (value, text) in enumerate(model.GENDERS):
                self._Keep(FilterChoice(self, 130 + index * 108, y, 100, text,
                    lambda choice=value: self._Select('gender', choice), value == selected))
            y += 48
        if 'absorption' in fields:
            self._Range(24, y, 'absorption', 'Absorpce', percent=True)
            y += 68
        if 'grade' in fields:
            self._Label(24, y, 'Třída', True, 272)
            self._Label(320, y, 'Čistota', True, 272)
            for x, key, index, names in ((24, 'grade', 0, model.GRADES), (320, 'step', 1, model.STEPS)):
                options = [(-1, 'Libovolná')] + [(v, names[v]) for v in sorted(set(row[index] for row in info['variants']))]
                self._Dropdown(x, y + 22, 272, key, options, 'Třída' if key == 'grade' else 'Čistota')
            y += 62
            self._Range(24, y, 'strength', 'Zesílení alchymie',
                [(v, '+%d' % v) for v in sorted(set(row[2] for row in info['variants']))])
            y += 66
        if 'applies' in fields:
            title = 'Bonusy šerpy' if state['category'] == 11 else 'Bonusy kamene' if state['category'] == 6 else 'Bonusy'
            self._Label(24, y, title, True, color=ACCENT)
            self._Label(24, y + 26, 'Předmět musí splnit všechny zvolené bonusy.', color=MUTED)
            self._Label(24, y + 54, 'Bonus', width=360, color=MUTED)
            self._Label(418, y + 54, 'Minimální hodnota', width=174, color=MUTED)
            values = list(state.get('applies', ()))
            for index in range(3):
                kind, value = values[index] if index < len(values) else (0, '')
                text, unit = bonus_text(kind) or ('Bez filtru', '')
                rowY = y + 78 + index * 32
                button = self._Keep(FilterChoice(self, 24, rowY, 360, text, None, dropdown=True))
                button.SetEvent(lambda row=index, anchor=button: self._BonusPicker(row, anchor))
                button.SetToolTipText(text)
                image, edit = input_box(self, 418, rowY + 2, 61, '', value)
                self._Keep(image)
                self.bonusValues.append(edit)
                self.bonusKinds.append(kind)
                edit.SetEscapeEvent(self.OnPressEscapeKey)
                edit.SetReturnEvent(self._Apply)
                if not kind: edit.CanEdit(False)
                self._Label(488, rowY + 3, unit, width=65, color=MUTED)
                remove = self._Keep(ui.Button())
                remove.SetParent(self)
                remove.SetPosition(573, rowY + 1)
                remove.SetUpVisual('d:/ymir work/ui/public/crimson_close_01.tga')
                remove.SetOverVisual('d:/ymir work/ui/public/crimson_close_02.tga')
                remove.SetDownVisual('d:/ymir work/ui/public/crimson_close_03.tga')
                remove.SetEvent(lambda row=index: self._SetBonus(row, 0))
                remove.SetToolTipText('Odebrat bonus')
                remove.Show()
            y += 188
        else:
            self._Label(24, y + 4, 'Pro tuto kategorii použij název a podkategorii.' if not fields else '', color=MUTED)
            y += 42
        self.errorLabel = self._Label(24, y, '', color=ERROR)
        self.summaryLabel = self._Label(24, y, 'Podmínky: %d' % (len(state) - 2), color=MUTED)
        y += 36
        self._Action(24, y, 'Vymazat vše', self._ResetDraft)
        self._Action(310, y, 'Zrušit', self.Close)
        self._Action(422, y - 1, 'Použít filtry', self._Apply, '170x24')
        self.SetSize(616, y + 43)
        x, top = self.GetGlobalPosition()
        self.SetPosition(max(0, min(x, wndMgr.GetScreenWidth() - 616)),
            max(0, min(top, wndMgr.GetScreenHeight() - self.GetHeight())))

    def _ReadEdits(self):
        changes = {}
        for key, edit in self.edits.items():
            text = edit.GetText().strip()
            if text and not text.isdigit(): return key, 'Zadej celé nezáporné číslo.'
            changes[key] = int(text) if text else (0 if key.endswith('level') else -1)
        applies = []
        for kind, edit in zip(self.bonusKinds, self.bonusValues):
            if not kind: continue
            text = edit.GetText().strip()
            try: value = int(text) if text else 0
            except ValueError: return 'applies', 'Zadej celé číslo bonusu.'
            applies.append((kind, value))
        changes['applies'] = applies
        self.state.change(**changes)
        return None

    def _BonusPicker(self, index, anchor):
        self._ReadEdits()
        current = self.bonusKinds[index]
        used = set(self.bonusKinds) - {current, 0}
        options = [(0, 'Bez filtru')]
        for kind in model.profile(self.state.draft, self.state.catalog)['bonuses']:
            text = bonus_text(kind)
            if text and kind not in used: options.append((kind, text[0]))
        options[1:] = sorted(options[1:], key=lambda row: model.folded(row[1]))
        self.picker.Open(anchor, 'Výběr bonusu', options, current,
            lambda value: self._SetBonus(index, value))

    def _SetBonus(self, index, kind):
        self._ReadEdits()
        rows = [(key, model.number(edit.GetText())) for key, edit in zip(self.bonusKinds, self.bonusValues)]
        rows[index] = (kind, rows[index][1] if kind == rows[index][0] else 0)
        self.state.change(applies=rows)
        self._Build()

    def _ResetDraft(self):
        self.state.reset_draft()
        self._Build()

    def _Apply(self):
        error = self._ReadEdits() or self.state.apply()
        if error:
            self.summaryLabel.Hide()
            self.errorLabel.SetText(error[1])
            for key, edit in self.edits.items():
                if key.endswith(error[0]): set_color(edit, ERROR)
            return True
        self.Close()
        if self.applyEvent: self.applyEvent()
        return True

    def GetFilters(self):
        return deepcopy(self.state.applied)

    def SetFilters(self, filters):
        self.LoadCatalog()
        self.state.set_filters(filters)

    def SelectCategory(self, category):
        self.LoadCatalog()
        self.state.select_category(category)
        self.Close()

    def Reset(self):
        self.state.set_filters({'category': self.state.applied['category']})
        self.Close()

    def IsActive(self):
        return len(self.state.applied) > 2 or self.state.applied['subtype'] != (-1, -1)

    def GetArguments(self, vnums, seller, exact, name='', nameExact=False):
        self.LoadCatalog()
        return self.state.arguments(vnums, seller, exact, name, nameExact)

    def Open(self):
        self.LoadCatalog()
        self.state.open()
        self._Build()
        self.SetCenterPosition()
        self.Show()
        self.SetTop()
        self.SetFocus()

    def Close(self):
        self.picker.Close()
        for edit in list(self.edits.values()) + self.bonusValues: edit.KillFocus()
        self.state.cancel()
        self.KillFocus()
        self.Hide()

    def OnMouseLeftButtonDown(self):
        self.picker.Close()

    def OnPressEscapeKey(self):
        if self.picker.IsShow(): self.picker.Close()
        else: self.Close()
        return True

    def Destroy(self):
        self.Close()
        self._ClearWidgets()
        self.picker.Destroy()
        self.applyEvent = None
