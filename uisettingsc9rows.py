# -*- coding: utf-8 -*-
"""Settings window v5 rows (2026-10-05): the A7 page descriptions as rows of the new look.

settingspages.compose() calls the same view API on this window as on the A7 window (section, check, radios, slider,
action, hint, ...). On a new page those calls are COLLECTED, filtered to the keys of the page (settingsc9pages blocks,
plus its explicit rows) and laid out centrally: label on the left axis (an icon in front only with "Ikony u voleb"),
the control on the right, "Výchozí: …" beside the control only while the option differs from its default, the
description of a row as a kit tooltip on hover (v5 fix 2026-10-05: the description strip under the content is gone).

  check / toggle      -> uikit.Toggle            radios -> uikit.Segment (or a vertical OptionList)
  slider              -> uikit.Slider + value     action -> uikit.Button (row of buttons / "Open")
  check on a chips page / chips item -> uikit.Chip row      section + numbers -> one range row of two EditFields
  frame_limit         -> segment of FPS limits    refresh_rate -> cycling button + status note
  background_fps      -> segment 10 / 30 / 60 FPS of an inactive window (hidden on a client without the native)
  tree_shadow         -> segment of distances (hidden on a client without the native limit)
  sky_picker          -> button opening the kit sky picker     music_inline -> dropdown (uikit.ListPopup)
  ui_scale            -> value list + active / maximum note (hidden on a client without UI scaling)
  damage_controls     -> font and grouping dropdowns, colour buttons with a swatch, outline switch
                         (hidden on a client without the damage look natives)

Values, persistence, preview of sliders and reset stay the A7 code (change(), Apply(), ResetPage()); chat options go
through settingschat. While a legacy page (panels, queue) is shown, every call goes to the A7 implementation.
"""
import app
import grp
import ui
import wndMgr

import settingsc9pages as c9pages
import settingschat
import settingsmodel
import settingspages as pages
import uikit
import uikitsections
import uikittokens as T
import uisettings as a7
from settingslocale import Text as Tr

Base = a7.GameOptionWindow
FORMS = {'volba': ('volbu', 'volby', 'voleb', 'option', 'options'), 'akce': ('akce', 'akce', 'akcí', 'action', 'actions')}


def Plural(count, word):
    one, few, many, en_one, en_many = FORMS[word]
    czech = one if count == 1 else (few if 2 <= count <= 4 else many)
    return Tr('%d %s' % (count, czech), '%d %s' % (count, en_one if count == 1 else en_many))


def _label_of(options, value):
    for v, label in options:
        if v == value:
            return label
    return str(value)


class C9Rows(object):
    """Mixin of the settings window: collect -> filter -> merge -> layout -> refresh; the row tooltip."""

    # ------------------------------------------------------------------ collected view API
    def section(self, label, y):
        if self.legacy_mode:
            return Base.section(self, label, y)
        self.c9_items.append(dict(type='section', label=label))

    def _c9_control(self, kind, key, label, **extra):
        item = dict(type='control', kind=kind, key=key, label=label or '', hints=[])
        item.update(extra)
        self.c9_items.append(item)
        return item

    def check(self, key, label, x, y, width=170, mask=None, status=None, hint=''):
        if self.legacy_mode:
            return Base.check(self, key, label, x, y, width, mask, status, hint)
        self._c9_control('toggle', key, label, mask=mask, hint=hint)

    def toggle(self, key, label, y, hint='', compact=False):
        if self.legacy_mode:
            return Base.toggle(self, key, label, y, hint, compact)
        self._c9_control('toggle', key, label, mask=None, hint=hint)

    def radios(self, key, label, y, choices, vertical=False, columns=None, gap=None, pitch=None):
        if self.legacy_mode:
            return Base.radios(self, key, label, y, choices, vertical, columns, gap, pitch)
        choices = list(choices)
        current = self.value(key)
        if key == 'track' and not current:
            import musicInfo
            current = musicInfo.METIN2THEMA
        if key in ('fps', 'track') and current not in dict(choices):
            choices.append((current, str(current) + ' FPS' if key == 'fps' else str(current)))
        self._c9_control('choice', key, label, options=choices, hint='')

    def slider(self, key, label, y, hint='', compact=False):
        if self.legacy_mode:
            return Base.slider(self, key, label, y, hint, compact)
        self._c9_control('slider', key, label, hint=hint)

    def number(self, key, label, x, y):
        if self.legacy_mode:
            return Base.number(self, key, label, x, y)
        self._c9_control('number', key, label, hint='')

    def action(self, key, label, y, event, hint='', left=False, x=0, family='176x21'):
        if self.legacy_mode:
            return Base.action(self, key, label, y, event, hint, left, x, family)
        self._c9_control('button' if left else 'open', key, label, event=event, hint=hint)

    def link(self, key, label, y, hint='', event=None):
        if self.legacy_mode:
            return Base.link(self, key, label, y, hint, event)
        self._c9_control('open', key, label, event=event or (lambda: self.open_page(key)), hint=hint)

    def hint(self, label, y):
        if self.legacy_mode:
            return Base.hint(self, label, y)
        self.c9_items.append(dict(type='hint', text=label))

    def text(self, label, x, y, small=False, bold=False, center=False, width=None, color=a7.INK, permanent=False):
        if self.legacy_mode or permanent:
            return Base.text(self, label, x, y, small, bold, center, width, color, permanent)
        return None  # table captions of A7 pages; the new pages name their rows themselves

    def tint(self, x, y, w, h, index):
        if self.legacy_mode:
            return Base.tint(self, x, y, w, h, index)

    def frame_limit(self, y):
        if self.legacy_mode:
            return Base.frame_limit(self, y)
        current = self.value('fps')
        options = [(v, str(v)) for v in sorted(set((60, 120, 144, 165, 180, 240, current)))]
        self._c9_control('choice', 'fps', Tr('Limit snímků (FPS)', 'Frame limit (FPS)'), options=options, hint='')

    def background_fps(self, y):
        if self.legacy_mode:
            return Base.background_fps(self, y)
        import settingsbackend
        if not settingsbackend.background_fps_supported():
            return  # an older client keeps its fixed inactive-window limit: the row stays hidden
        current = self.value('background_fps')
        options = list(pages.BACKGROUND_FPS_OPTIONS)
        if current not in dict(options):
            options = sorted(options + [(current, str(current))])  # a hand-edited metin2.cfg value stays visible
        self._c9_control('choice', 'background_fps', pages.BACKGROUND_FPS_LABEL, options=options,
                         hint=pages.BACKGROUND_FPS_HINT)

    def refresh_rate(self, y):
        if self.legacy_mode:
            return Base.refresh_rate(self, y)
        self._c9_control('refresh', 'refresh_hz', Tr('Obnovovací frekvence (Hz)', 'Refresh rate (Hz)'), hint='')

    def tree_shadow(self, y):
        if self.legacy_mode:
            return Base.tree_shadow(self, y)
        import settingsbackend
        if not settingsbackend.tree_shadow_supported():
            return  # an older client: the row stays hidden (Base disables it in the old look)
        self._c9_control('choice', 'tree_shadow', pages.TREE_SHADOW_LABEL, options=pages.TREE_SHADOW_OPTIONS,
                         hint=Tr('Stromy dál od postavy nevrhají stín. Menší dosah = více FPS v lese.',
                                 'Trees farther from your character cast no shadow. Shorter distance = more FPS in forests.'))

    def custom_colors(self):
        if self.legacy_mode:
            return Base.custom_colors(self)
        self.c9_items.append(dict(type='custom_colors'))

    def sky_picker(self, y):
        if self.legacy_mode:
            return Base.sky_picker(self, y)
        self._c9_control('sky', 'sky', Tr('Obloha', 'Sky'), hint='')

    def menu_music(self, y):
        if self.legacy_mode:
            return Base.menu_music(self, y)
        import uisettings
        self._c9_control('dropdown', 'menu_music', '', options=uisettings.MenuMusicChoices(), hint='')

    def music_inline(self, y):
        if self.legacy_mode:
            return Base.music_inline(self, y)
        import musicInfo
        default = musicInfo.METIN2THEMA
        choices = [(default, Tr('Výchozí podle mapy', 'Map default'))]
        import uisettings
        ours = uisettings.AltheaTrackChoices()          # our four tracks first, by their names
        choices.extend(ours)
        names = set(app.GetFileList('BGM/*.mp3'))
        current = self.value('track')
        if current and current != default and current not in dict(ours):
            names.add(current)
        choices.extend((name, name[:-4] if name.lower().endswith('.mp3') else name)
                       for name in sorted(names, key=lambda name: name.lower()) if name != default)
        self._c9_control('track', 'track', '', options=choices, hint='')

    def ui_scale(self, y):
        """Velikost rozhraní: the A7 page builds an A7 section with its own widgets; the kit window
        collects one row instead. Returns the A7 page offset (0: the kit ignores A7 coordinates)."""
        if self.legacy_mode:
            return Base.ui_scale(self, y)
        import settingsbackend
        if settingsbackend.ui_scale_info() is None:
            return 0  # an older client: no row, as on the A7 page
        self._c9_control('ui_scale', 'ui_scale', Tr('Velikost rozhraní', 'Interface scale'),
                         hint=Tr('Celé rozhraní a HUD: 50–150 % po 5 %. Změna platí ihned. Výchozí velikost je 100 %.',
                                 'Entire interface and HUD: 50–150% in 5% steps. Changes apply immediately. Default: 100%.'))
        return 0

    def damage_controls(self, y):
        """Písmo a barvy zásahů (main): uidamagesettings.build draws A7 widgets and expects A7 controls, which the
        kit window does not create; the kit collects its own rows for the same keys. The preview stays A7 only."""
        if self.legacy_mode:
            return Base.damage_controls(self, y)
        import systemSetting
        import damageappearance as damage
        if not callable(getattr(systemSetting, 'SetDamageHeight', None)):
            self.c9_items = [item for item in self.c9_items if item.get('key') != 'damage_height']
        if not damage.supported(systemSetting):
            return  # an older client: the rows stay hidden (the A7 page disables them)
        self._c9_control('dropdown', 'damage_font', Tr('Písmo zásahů', 'Damage font'),
                         options=tuple(enumerate(damage.FONTS)), hint='')
        self._c9_control('color', 'damage_normal_color', Tr('Barva normálních zásahů', 'Normal hit color'), hint='')
        self._c9_control('color', 'damage_critical_color', Tr('Barva kritických zásahů', 'Critical hit color'), hint='')
        self._c9_control('toggle', 'damage_outline', Tr('Černý obrys číslic', 'Black number outline'), mask=None,
                         hint='')
        self._c9_control('dropdown', 'damage_grouping', Tr('Oddělování tisíců', 'Thousands grouping'),
                         options=((0, Tr('Žádné · 1234567', 'None · 1234567')),
                                  (1, Tr('Mezera · 1 234 567', 'Space · 1 234 567')),
                                  (2, Tr('Tečka · 1.234.567', 'Dot · 1.234.567'))), hint='')

    # ------------------------------------------------------------------ collect and filter
    def _C9Collect(self, page):
        spec = c9pages.PAGES[page]
        result = []
        for block in c9pages.blocks(page):
            if block[0] == 'section':
                result.append(dict(type='section', label=block[1]))
            elif block[0] == 'item':
                if (block[1].get('key') in settingsmodel.NAME_VISIBILITY_KEYS + ('name_actions',) and
                        not getattr(a7.settingsbackend, 'name_visibility_supported', lambda: False)()):
                    continue
                item = dict(block[1], type='control', hints=[])
                if item['kind'] == 'chips':
                    item['items'] = [dict(sub, type='control', kind='toggle', mask=None, hints=[])
                                     for sub in item['items']]
                result.append(item)
            else:
                self.c9_items = []
                pages.compose(self, block[1])
                result.extend(self._C9Filter(self.c9_items, block[2], spec.get('sections', True)))
        self.c9_items = []
        # A page section whose rows all stayed hidden (an older client without the native) is dropped too.
        return [item for index, item in enumerate(result)
                if item['type'] != 'section' or (index + 1 < len(result) and result[index + 1]['type'] != 'section')]

    def _C9Filter(self, items, keys, sections=True):
        result, section, last_kept = [], None, False
        for item in items:
            kind = item['type']
            if kind == 'section':
                section = item
                continue
            if kind == 'hint':
                if last_kept and result:
                    result[-1].setdefault('hints', []).append(item['text'])
                continue
            if kind == 'custom_colors':
                last_kept = keys is None or any(k in keys for k in c9pages.CUSTOM_COLOR_KEYS)
                if last_kept:
                    result.append(item)
                continue
            if item['key'] == 'npc_names' and getattr(a7.settingsbackend, 'name_visibility_supported', lambda: False)():
                continue  # Replaced by the NPC three-state choice on a compatible EXE.
            last_kept = keys is None or item['key'] in keys
            if not last_kept:
                continue
            if item['key'] == 'names' and getattr(a7.settingsbackend, 'name_visibility_supported', lambda: False)():
                item['label'] = Tr('Názvy kořisti stále viditelné', 'Always show loot names')
            if item['key'] in c9pages.RELABEL:
                item['label'] = c9pages.RELABEL[item['key']]
            if not item['label']:
                item['label'] = c9pages.LABELS.get(item['key']) or (section['label'] if section else '')
            if section is not None:
                if sections and item['label'] != section['label']:
                    result.append(dict(section))
                section = None
            result.append(item)
        return result

    def _C9Expand(self, items):
        visible = self.custom_expanded or self.highlight in dict(pages.CUSTOM_COLORS)
        self.custom_expanded = visible
        self.c9_has_custom = any(item['type'] == 'custom_colors' for item in items)
        self.c9_custom_shown = visible
        for item in items:
            if item['type'] != 'custom_colors':
                yield item
            elif visible:
                for key, label in pages.CUSTOM_COLORS:
                    yield dict(type='control', kind='slider', key=key, label=label, hint='', hints=[])

    def _C9Merge(self, items):
        """Consecutive left-aligned A7 actions become one row of buttons; on a chips page consecutive switches
        become one row of chips; a section followed by numbers becomes one range row (Od - Do)."""
        chips = c9pages.PAGES.get(self.c9_page, {}).get('chips')
        merged = []
        for item in items:
            kind = item.get('kind')
            last = merged[-1] if merged else None
            if item['type'] == 'control' and kind == 'button':
                hint = ' '.join(t for t in [item.get('hint') or ''] + item.get('hints', []) if t)
                if last and last.get('kind') == 'buttons':
                    last['buttons'].append(item)
                    last['hints'].append(hint)
                else:
                    merged.append(dict(type='control', kind='buttons', key=item['key'], label=item['label'],
                                       buttons=[item], hint='', hints=[hint]))
            elif item['type'] == 'control' and kind == 'number':
                if last and last.get('kind') == 'range' and len(last['items']) < 2:
                    last['items'].append(item)
                else:
                    label = last['label'] if last and last['type'] == 'section' else item['label']
                    if last and last['type'] == 'section':
                        merged.pop()
                    merged.append(dict(type='control', kind='range', key=item['key'], label=label, items=[item],
                                       hint='', hints=[]))
            elif item['type'] == 'control' and kind == 'toggle' and chips:
                if last and last.get('kind') == 'chips' and not last.get('fixed'):
                    last['items'].append(item)
                else:
                    label = last['label'] if last and last['type'] == 'section' else item['label']
                    merged.append(dict(type='control', kind='chips', key=item['key'], label=label, items=[item],
                                       hint='', hints=[]))
            else:
                if item['type'] == 'control' and kind == 'chips':
                    item['fixed'] = True
                merged.append(item)
        return merged

    # ------------------------------------------------------------------ layout
    def _C9Track(self, widget, wheel=True):
        self.page_widgets.append(widget)
        if wheel:
            if hasattr(widget, 'SetWheelEvent'):
                widget.SetWheelEvent(self.OnMouseWheel)
            else:
                widget.OnMouseWheel = self.OnMouseWheel
        return widget

    def _C9Text(self, text, x, y, size, color, align='left', valign='center', outline=False, limit=None):
        line = uikit.Text(self.content, text, x, y, self.kit.font(size), color, align, valign, outline, limit)
        self.page_widgets.append(line)
        return line

    def _C9Section(self, label, y, width):
        section = self._C9Track(uikit.Section(self.content, self.kit, 0, y, width, label), wheel=False)
        return section.Height()

    def C9SectionStyle(self):
        """The section separation of the settings pages: uikitsections.SECTION_STYLE (one place for the team's vote,
        design v5 section 1); the default 'v5' draws exactly today's look."""
        return uikitsections.Style(self.kit)

    def _C9TrackStatic(self, widget):
        return self._C9Track(widget, wheel=False)

    def _C9Lead(self):
        """Left axis of the row labels: the icon column only with "Ikony u voleb" on (default off, owner v5)."""
        return self.kit.p('icon_row') + 14 if self.c9_icons else 0

    def _C9Layout(self, items, width):
        k = self.kit
        pitch, isz = k.p('pitch'), k.p('icon_row')
        lead = self._C9Lead()
        self.c9_rows = []
        style = self.C9SectionStyle()
        track = self._C9TrackStatic
        y, first, section, index = 0, True, None, 0
        for item in self._C9Merge(list(self._C9Expand(items))):
            if item['type'] == 'section':
                y += style.Close(section, y)
                y += style.Gap(first)
                section = style.Open(self.content, 0, y, width, track)
                y += style.Heading(self.content, 0, y, width, item['label'], track)
                first, index = False, 0
                continue
            first = False
            inset_l, inset_r = style.Inset() if section is not None else (0, 0)
            lx = lead + inset_l
            back = style.RowBack(self.content, 0, y, width, pitch, index, track)
            index += 1
            row = dict(item, y=y, h=pitch)
            row['hint_text'] = ' '.join(t for t in [item.get('hint') or ''] + item.get('hints', []) if t)
            self.c9_rows.append(row)
            band = self._C9Track(uikit.Band(self.content, 0, y, width, pitch, 'hover'), wheel=False)
            band.Hide()
            row['band'] = band
            hit = self._C9Track(uikit.HitArea(self.content, 0, y, width, pitch))
            hit.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
            row['hit'] = hit
            row['label_cy'] = pitch // 2
            row['ctrl_x'] = None
            h = getattr(self, '_C9Row_' + item['kind'])(row, lx, y, width - inset_r)
            icon = c9pages.ICONS.get(item['key'])
            if self.c9_icons and icon and uikit.IconPath(icon, isz):
                self._C9Track(uikit.Icon(self.content, icon, isz, inset_l, y + row['label_cy'] - isz // 2), wheel=False)
            self._C9InlineDefault(row, lx, y)
            if h != pitch:
                row['h'] = h
                hit.SetSize(width, h)
                band.SetScale(float(width) / 128, float(h) / 28)
                if back is not None:
                    back.SetSize(width, h)
            style.RowLine(self.content, 0, y + h - 1, width, track)
            y += h
        y += style.Close(section, y)
        return y

    def _C9InlineDefault(self, row, lx, y):
        """Changed-option marker (coordinator v5): a small gold diamond + "Výchozí: …" left of the control, shown
        only while the value differs from the default (_C9RefreshDefaults) and only where the row has room.
        An unchanged row shows nothing."""
        row['default_fits'] = False
        if row.get('ctrl_x') is None or not row.get('label_line'):
            return
        right = row['ctrl_x'] - (16 if self.kit.prof == '1080' else 12)
        self.C9DefaultMarker(self.content, row, right, y + row['label_cy'], lx + uikit.TextWidth(row['label_line']) + 24,
                             track=lambda widget: self._C9Track(widget, wheel=False))

    def C9DefaultMarker(self, parent, row, right, cy, min_x=0, track=None):
        """The "Výchozí: …" note of a changed option, right-aligned to ``right`` and centred on ``cy`` (the row /
        control centre), with the gold diamond before it; hidden until _C9RefreshDefaults finds the row changed.
        Owner play test 2026-10-05: the note was the small S size and sat low - it is now Ms (one step below the row
        label, same family) and its lower-case body is centred on the control: the engine centres the font cell,
        whose accent room puts the x-height ~2 px (1080) / 1 px (768) below the centre for Spectral. Custom pages
        (Fronta kamenů) use it too. Returns False when the note does not fit between min_x and right."""
        text = self._C9DefaultText(row)
        if not text:
            return False
        k = self.kit
        line = uikit.Text(parent, text, 0, 0, k.font('Ms'), T.MUTED, align='right')
        mark_path = k.rel('bullet/diamond_selected.png')
        mw, mh = uikit.L.size(mark_path)
        tw = uikit.TextWidth(line)
        if min_x + mw + 7 + tw > right:
            line.Hide()
            return False
        line.SetPosition(int(right), int(cy) - self.C9TextNudge())
        mark = uikit.Image(parent, mark_path, right - tw - 7 - mw, int(cy) - mh // 2)
        line.Hide()
        mark.Hide()
        if track:
            track(line)
            track(mark)
        row['default_fits'] = True
        row['default_line'], row['default_mark'] = line, mark
        return True

    def C9TextNudge(self):
        """Pixels a centred Spectral text moves up so its lower-case body (not the font cell with its accent room)
        sits on the centre line; 0 for the Tahoma fallback of an old EXE."""
        if self.kit.font_set != 'B':
            return 0
        return 2 if self.kit.prof == '1080' else 1

    def _C9DefaultRaw(self, key):
        if key == 'quality_preset':
            return 2
        if key == 'color_preset':
            return 1
        if settingschat.owns(key):
            return settingschat.DEFAULTS[key]
        if key in settingsmodel.COLOR_DEFAULTS:
            return settingsmodel.COLOR_DEFAULTS[key]
        if key == 'row_icons':
            return 0
        if key == 'channel_bar_style':
            return 'stepper'
        if key == 'track':
            import musicInfo
            return musicInfo.METIN2THEMA
        return settingsmodel.DEFAULTS.get(key)

    def _C9Changed(self, row):
        """True when the row's current value differs from its default (as the player sees it)."""
        kind = row['kind']
        keys = [item['key'] for item in row['items']] if kind == 'range' else [row['key']]
        for key in keys:
            value, default = self.value(key), self._C9DefaultRaw(key)
            if key == 'track':
                import musicInfo
                value = value or musicInfo.METIN2THEMA
            if kind in ('toggle', 'look_icons'):
                mask = row.get('mask')
                if (bool(value & mask) if mask else bool(value)) != (bool((default or 0) & mask) if mask else bool(default)):
                    return True
            elif kind == 'slider':
                if self._Format(key, value) != self._Format(key, default):
                    return True
            elif value != default:
                return True
        return False

    def _C9RefreshDefaults(self):
        for row in self.c9_rows:
            if not row.get('default_fits'):
                continue
            changed = self._C9Changed(row)
            for widget in (row['default_line'], row['default_mark']):
                widget.Show() if changed else widget.Hide()
            row['default_shown'] = changed

    def _C9Label(self, row, lx, y, h=None, color=None):
        line = self._C9Text(row['label'], lx, y + (h or self.kit.p('pitch')) // 2, 'M', color or T.INK)
        row['label_line'] = line
        return line

    def _C9Control(self, row, kind, widget, **extra):
        record = dict(kind=kind, key=row['key'], widget=widget, label=row.get('label_line'), y=row['y'], row=row)
        record.update(extra)
        self.controls.append(record)
        row['control'] = record
        if hasattr(widget, 'SetHoverEvent'):
            widget.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
        return record

    def _C9Row_toggle(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        tw, th = uikit.Toggle.Size(k)
        key, mask = row['key'], row.get('mask')
        toggle = self._C9Track(uikit.Toggle(self.content, k, width - tw, y + (pitch - th) // 2,
                                            event=lambda: self._C9Flip(key, mask)))
        row['ctrl_x'] = width - tw
        self._C9Control(row, 'c9_toggle', toggle, mask=mask)
        # The whole row is the hit area (as the A7 check boxes had their label); a disabled switch stays off.
        row['hit'].SetEvent(lambda: toggle.IsEnabled() and self._C9Flip(key, mask))
        return pitch

    def _C9Flip(self, key, mask):
        self.change(key, self.value(key) ^ mask if mask else int(not self.value(key)))

    def _C9Choice(self, row, lx, y, width, options, event):
        """Segment beside the label, else under it, else a vertical option list. Returns (widget, height)."""
        k, pitch = self.kit, self.kit.p('pitch')
        line = self._C9Label(row, lx, y)
        sh = k.p('seg_h')
        inline = width - lx - uikit.TextWidth(line) - 16
        seg = uikit.Segment(self.content, k, options, event=event, max_width=inline)
        if seg.Width() <= inline:
            seg.SetPosition(width - seg.Width(), y + (pitch - sh) // 2)
            row['ctrl_x'] = width - seg.Width()
            return self._C9Track(seg), pitch
        seg.Hide()
        top = k.cell('M') + 16
        row['label_cy'] = top // 2 + 2
        row['ctrl_x'] = width
        line.SetPosition(lx, y + row['label_cy'])
        seg = uikit.Segment(self.content, k, options, event=event, max_width=width - lx)
        if seg.Width() <= width - lx:
            seg.SetPosition(lx, y + top)
            return self._C9Track(seg), top + sh + 12
        seg.Hide()
        listing = uikit.OptionList(self.content, k, options, width - lx, event=event)
        listing.SetPosition(lx, y + top - 2)
        return self._C9Track(listing), top + listing.Height() + 8

    def _C9Row_choice(self, row, lx, y, width):
        key = row['key']
        widget, h = self._C9Choice(row, lx, y, width, row['options'], lambda value, key=key: self.change(key, value))
        self._C9Control(row, 'c9_choice', widget)
        return h

    def _C9Row_look_icons(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        tw, th = uikit.Toggle.Size(k)
        toggle = self._C9Track(uikit.Toggle(self.content, k, width - tw, y + (pitch - th) // 2,
                                            event=lambda: self._C9SetIcons(not self.c9_icons)))
        row['ctrl_x'] = width - tw
        self._C9Control(row, 'c9_look_icons', toggle)
        row['hit'].SetEvent(lambda: self._C9SetIcons(not self.c9_icons))
        return pitch

    def _C9Row_look_old(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        tw, th = uikit.Toggle.Size(k)
        toggle = self._C9Track(uikit.Toggle(self.content, k, width - tw, y + (pitch - th) // 2,
                                            event=lambda: self._C9SetOldLook(True)))
        self._C9Control(row, 'c9_look_old', toggle)
        return pitch

    def _C9SetAllNameVisibility(self, mode):
        if not self.Apply():
            return
        for key in settingsmodel.NAME_VISIBILITY_KEYS:
            self.session.set(key, mode)
        self.Apply()
        self._Refresh()

    def _C9Row_name_actions(self, row, lx, y, width):
        callback = ui.__mem_func__(self._C9SetAllNameVisibility)
        row['buttons'] = [dict(label=Tr('Zobrazit vše', 'Show all'),
                               event=lambda cb=callback: cb(2)),
                          dict(label=Tr('Skrýt vše', 'Hide all'),
                               event=lambda cb=callback: cb(0))]
        return self._C9Row_buttons(row, lx, y, width)

    def _C9Row_reset_all(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        # Secondary like every content button: the window's one primary action is Zavřít (2026-10-06).
        button = uikit.Button(self.content, k, 0, 0, 0, Tr('Obnovit vše...', 'Reset all…'), role='secondary',
                              event=self._C9AskResetAll)
        button.FitWidth(130 if k.prof == '1080' else 104)
        button.SetPosition(width - button.w, y + (pitch - button.h) // 2)
        button.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
        self._C9Track(button)  # an action, not a setting: never in self.controls
        return pitch

    def _C9SliderBounds(self, key):
        if key in settingschat.BOUNDS:
            return settingschat.BOUNDS[key]
        bounds = settingsmodel.COLOR_BOUNDS.get(key, settingsmodel.BOUNDS.get(key))
        if key == 'fov':
            bounds = (float(app.MIN_CAMERA_PERSPECTIVE), float(app.MAX_CAMERA_PERSPECTIVE))
        return bounds

    def _Format(self, key, value):
        if key in settingschat.BOUNDS:
            return '%d %%' % round(value)
        return Base._Format(self, key, value)

    def _C9Row_slider(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        key = row['key']
        track_w = 210 if k.prof == '1080' else 150
        value_w = 56
        slider = uikit.Slider(self.content, k, track_w)
        x0 = width - value_w - track_w
        slider.SetPosition(x0 - slider.knob_w // 2, y + (pitch - slider.h) // 2)
        row['ctrl_x'] = x0 - slider.knob_w // 2
        low, high = self._C9SliderBounds(key)

        def moved():
            value = low + max(0., min(1., slider.GetSliderPos())) * (high - low)
            if key == 'grass_radius':
                value = int(round(value / 10.)) * 10
            self.change(key, value, continuous=True)
        slider.SetEvent(moved)
        self._C9Track(slider)
        text = self._C9Text('', x0 + track_w + 14, y + pitch // 2, 'M', T.INK_DIM)
        self._C9Control(row, 'c9_slider', slider, text=text, bounds=(low, high))
        return pitch

    def _C9Row_buttons(self, row, lx, y, width):
        """A row of A7 actions (e.g. Upravit polohu / Obnovit polohu): one ButtonGroup (B1 separate buttons or the
        joined B3 block, uikit.BUTTON_GROUPS) when it fits the row, else separate buttons wrapped to further lines."""
        k, pitch = self.kit, self.kit.p('pitch')
        min_w = 104 if k.prof == '1080' else 84
        group = uikit.ButtonGroup(self.content, k, [(item['label'], item['event']) for item in row['buttons']],
                                  min_w=min_w)
        if lx + group.Width() <= width:
            group.SetPosition(lx, y + (pitch - group.h) // 2)
            group.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
            self._C9Track(group)
            return pitch
        group.Hide()
        x, line = lx, 0
        for item in row['buttons']:
            button = uikit.Button(self.content, k, 0, 0, 0, item['label'], role='secondary', event=item['event'])
            button.FitWidth(min_w)
            if x > lx and x + button.w > width:
                x, line = lx, line + 1
            button.SetPosition(x, y + line * pitch + (pitch - button.h) // 2)
            button.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
            self._C9Track(button)
            x += button.w + (8 if k.prof == '1080' else 6)
        return (line + 1) * pitch

    def _C9Row_open(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        button = uikit.Button(self.content, k, 0, 0, 0, Tr('Otevřít', 'Open'), role='secondary', event=row['event'])
        button.FitWidth(104 if k.prof == '1080' else 84)
        button.SetPosition(width - button.w, y + (pitch - button.h) // 2)
        button.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
        self._C9Track(button)  # an action, not a setting: never in self.controls (ResetPage resets controls)
        return pitch

    def _C9Row_refresh(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        note_h = k.cell('S') + 2
        line = self._C9Label(row, lx, y)
        line.SetPosition(lx, y + pitch // 2 - note_h // 2 - 1)
        note = self._C9Text('', lx, y + pitch // 2 + k.cell('M') // 2 - note_h // 2 + 3, 'S', T.MUTED, valign='top')
        bw = 140 if k.prof == '1080' else 110
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary', event=self._CycleRefreshRate)
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        self._C9Track(button)
        self._C9Control(row, 'c9_refresh', button, status=note)
        return pitch

    def _C9Row_sky(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        bw = 170 if k.prof == '1080' else 130
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary', event=self.OpenSkyPicker)
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        row['ctrl_x'] = width - bw
        self._C9Track(button)
        self._C9Control(row, 'c9_sky', button)
        return pitch

    def OpenSkyPicker(self):
        """The sky picker in the kit look (uisettingsc9dialogs); the A7 picker (traced) when it cannot be built."""
        try:
            import uisettingsc9dialogs
            uisettingsc9dialogs.OpenSkyPicker(self, pages.SKIES)
        except Exception:
            import dbg
            import traceback
            dbg.TraceError('settings kit sky picker: %s' % traceback.format_exc())
            self._ClosePopup()
            Base.OpenSkyPicker(self)

    def _C9Row_track(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        bw = 250 if k.prof == '1080' else 190
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary', align='left')
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        cw, ch = k.size('chevron/down_normal.png')
        uikit.Image(button, k.rel('chevron/down_normal.png'), bw - cw - 12, (button.h - ch) // 2)
        button.label.SetLimitWidth(bw - cw - 34)
        button.SetEvent(lambda: self._C9OpenTrackList(button, row['options']))
        row['ctrl_x'] = width - bw
        self._C9Track(button)
        self._C9Control(row, 'c9_track', button, options=row['options'])
        return pitch

    def _C9OpenTrackList(self, anchor, options):
        if self.c9_list is None:
            self.c9_list = uikit.ListPopup(self.kit)
            self.c9_list.owner = self
        current = self.value('track')
        if not current:
            import musicInfo
            current = musicInfo.METIN2THEMA
        self.c9_list.Open(anchor, options, current, lambda value: self.change('track', value), anchor.GetWidth())

    def _C9Row_dropdown(self, row, lx, y, width):
        """A value list behind a button (the track row for any key): damage font and thousands grouping."""
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        bw = 250 if k.prof == '1080' else 190
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary', align='left')
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        cw, ch = k.size('chevron/down_normal.png')
        uikit.Image(button, k.rel('chevron/down_normal.png'), bw - cw - 12, (button.h - ch) // 2)
        button.label.SetLimitWidth(bw - cw - 34)
        key, options = row['key'], row['options']
        button.SetEvent(lambda: self._C9OpenValueList(button, key, options))
        row['ctrl_x'] = width - bw
        self._C9Track(button)
        self._C9Control(row, 'c9_dropdown', button, options=options)
        return pitch

    def _C9OpenValueList(self, anchor, key, options):
        from _weakref import proxy
        if self.c9_list is None:
            self.c9_list = uikit.ListPopup(self.kit)
            self.c9_list.owner = self
        self.c9_list.Open(anchor, options, self.value(key),
                          lambda value, owner=proxy(self): owner.change(key, value), anchor.GetWidth())

    def _C9Row_color(self, row, lx, y, width):
        """A damage colour: '#RRGGBB' with a swatch; a click opens the colour picker of the A7 page."""
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        bw = 140 if k.prof == '1080' else 110
        key = row['key']
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary',
                              event=lambda: self._C9OpenDamageColor(key))
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        swatch = ui.Bar()
        swatch.SetParent(button)
        swatch.SetPosition(10, (button.h - 12) // 2)
        swatch.SetSize(12, 12)
        swatch.AddFlag('not_pick')
        swatch.Show()
        row['ctrl_x'] = width - bw
        self._C9Track(button)
        self._C9Control(row, 'c9_color', button, swatch=swatch)
        return pitch

    def _C9OpenDamageColor(self, key):
        """The R1 colour dialog (uisettingsc9color, 9. 10. 2026); the old picker (traced) when it cannot be built."""
        from _weakref import proxy
        import damageappearance as damage
        import systemSetting
        import uidamagesettings
        if not damage.supported(systemSetting):
            return
        dialog = self.damage_color_dialog
        if dialog is None and not getattr(self, 'c9_color_failed', False):
            try:
                import uisettingsc9color
                dialog = self.damage_color_dialog = uisettingsc9color.DamageColorDialog(proxy(self))
            except Exception:
                import uir1
                self.c9_color_failed = True
                uir1.TraceFailure('settings damage colour dialog')
                dialog = None
        if dialog is None or not hasattr(dialog, 'IsOpen'):
            uidamagesettings.open_color(self, key)
            return
        import uisettingsc9color
        owner = proxy(self)
        self._ClosePopup()
        if self.c9_list:
            self.c9_list.Close()
        dialog.Open(key, self.value(key), uisettingsc9color.DamageValues(self),
                    lambda value: owner.change(key, value),
                    lambda: owner.change(key, damage.DEFAULTS[key]))

    def _C9Row_ui_scale(self, row, lx, y, width):
        """Live scale choices; show the actual capped size independently of the request."""
        k, pitch = self.kit, self.kit.p('pitch')
        note_h = k.cell('S') + 2
        line = self._C9Label(row, lx, y)
        line.SetPosition(lx, y + pitch // 2 - note_h // 2 - 1)
        note = self._C9Text('', lx, y + pitch // 2 + k.cell('M') // 2 - note_h // 2 + 3, 'S', T.MUTED, valign='top')
        bw = 140 if k.prof == '1080' else 110
        button = uikit.Button(self.content, k, 0, 0, bw, '', role='secondary')
        from _weakref import proxy
        options = [(value, '%d %%' % value) for value in settingsmodel.UI_SCALE_CHOICES]
        button.SetEvent(lambda owner=proxy(self), anchor=proxy(button):
                        owner._C9OpenValueList(anchor, 'ui_scale', options))
        cw, ch = k.size('chevron/down_normal.png')
        uikit.Image(button, k.rel('chevron/down_normal.png'), bw - cw - 10, (button.h - ch) // 2)
        button.SetPosition(width - bw, y + (pitch - button.h) // 2)
        row['ctrl_x'] = width - bw
        self._C9Track(button)
        self._C9Control(row, 'c9_ui_scale', button, status=note, refresh_at=0.)
        return pitch

    def _C9NumberField(self, row, key, x, y, w):
        k = self.kit
        field = self._C9Track(uikit.EditField(self.content, k, x, y, w, k.font('M'), max_len=3, number=True))
        edit = field.edit
        edit.SetText(str(self.value(key)))
        edit.SetUpdateEvent(lambda: self._NumberChanged(key, edit))
        edit.SetEscapeEvent(self.OnPressEscapeKey)
        self.edit_lines.append(edit)
        self._C9Control(row, 'c9_number', edit, field=field, key=key)
        field.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
        return field

    def _C9Row_number(self, row, lx, y, width):
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        w = 90 if k.prof == '1080' else 72
        fh = k.p('field_h')
        self._C9NumberField(row, row['key'], width - w, y + (pitch - fh) // 2, w)
        return pitch

    def _C9Row_range(self, row, lx, y, width):
        """One row for a level range: label, then "od [ n ] do [ m ]" on the right."""
        k, pitch = self.kit, self.kit.p('pitch')
        self._C9Label(row, lx, y)
        fw, fh = (90 if k.prof == '1080' else 72), k.p('field_h')
        fy = y + (pitch - fh) // 2
        x, places = width, []
        for index in range(len(row['items']) - 1, -1, -1):  # placed from the right, created from the left
            item = row['items'][index]
            x -= fw
            word = self._C9Text(item['label'].lower(), x - 10, y + pitch // 2, 'M', T.INK_DIM, align='right')
            places.append((item['key'], x))
            x -= uikit.TextWidth(word) + 10 + (18 if index else 0)
        for key, fx in reversed(places):
            self._C9NumberField(row, key, fx, fy, fw)
        row['ctrl_x'] = x
        return pitch

    def _C9Row_chips(self, row, lx, y, width):
        """Chips in rows (multi-choice): a chip is ON when the A7 switch is on (e.g. "Nesbírat ... pro" Šaman)."""
        k = self.kit
        gap = 10 if k.prof == '1080' else 8
        pad = 10 if k.prof == '1080' else 8
        x, top = lx, y + pad
        ch = uikit.ButtonHeight(k)   # chips are the v6 family height (content buttons)
        for item in row['items']:
            key, mask = item['key'], item.get('mask')
            chip = uikit.Chip(self.content, k, 0, 0, item['label'], event=lambda key=key, mask=mask: self._C9Flip(key, mask))
            if x > lx and x + chip.Width() > width:
                x, top = lx, top + ch + gap
            chip.SetPosition(x, top)
            chip.SetHoverEvent(lambda row=row: self._C9ShowInfo(row))
            self._C9Track(chip)
            record = dict(kind='c9_chip', key=key, widget=chip, label=None, y=row['y'], row=row, mask=mask)
            self.controls.append(record)
            x += chip.Width() + gap
        return top + ch + pad + 2 - y

    # ------------------------------------------------------------------ refresh and default values
    def _C9RefreshControls(self):
        for control in self.controls:
            kind = control['kind']
            if not kind.startswith('c9_') or kind == 'c9_open':
                continue
            widget = control['widget']
            if kind == 'c9_look_icons':
                widget.SetOn(self.c9_icons)
                continue
            if kind == 'c9_look_old':
                widget.SetOn(False)
                continue
            key = control['key']
            value = self.value(key)
            if settingschat.owns(key):
                widget.Enable() if self.c9_chat.available(key) else widget.Disable()
            if kind in ('c9_toggle', 'c9_chip'):
                mask = control.get('mask')
                widget.SetOn(bool(value & mask) if mask else bool(value))
                if key == 'family_names':
                    widget.Enable() if self.family_name_state and self.family_name_state[0] else widget.Disable()
            elif kind == 'c9_choice':
                widget.SetValue(value)
            elif kind == 'c9_slider':
                low, high = control['bounds']
                widget.SetSliderPos((float(value) - low) / (high - low))
                control['text'].SetText(self._Format(key, value))
            elif kind == 'c9_sky':
                widget.SetText(pages.SKIES[value] if 0 <= value < len(pages.SKIES) else str(value))
            elif kind == 'c9_track':
                if not value:
                    import musicInfo
                    value = musicInfo.METIN2THEMA
                widget.SetText(_label_of(control['options'], value))
            elif kind == 'c9_number':
                if not widget.IsFocus():
                    widget.SetText(str(value))
            elif kind == 'c9_refresh':
                self._C9RefreshRate(control)
            elif kind == 'c9_dropdown':
                widget.SetText(_label_of(control['options'], value))
            elif kind == 'c9_color':
                import damageappearance
                widget.SetText('#%06X' % value)
                control['swatch'].SetColor(grp.GenerateColor(*(tuple(damageappearance.rgb(value)) + (1.,))))
            elif kind == 'c9_ui_scale':
                import settingsbackend
                widget.SetText('%d %%' % value)
                self._RefreshUIScaleStatus(control, settingsbackend.ui_scale_info())
        self._C9RefreshDefaults()

    def _C9RefreshRate(self, control):
        import settingsbackend
        info = settingsbackend.refresh_rate_info()
        button = control['widget']
        if info is None:
            button.SetText('-')
            button.Disable()
            control['status'].SetText(Tr('Dostupné po aktualizaci hry.', 'Available after updating the client.'))
        elif info[2]:
            button.SetText('%d Hz' % info[1] if info[1] else '-')
            button.Disable()
            control['status'].SetText(Tr('V okně se používá nastavení Windows.', 'Windowed mode uses Windows display settings.'))
        else:
            value = self.value('refresh_hz')
            button.Enable()
            button.SetText('%d Hz ›' % value if value else Tr('Auto ›', 'Auto ›'))
            control['status'].SetText(Tr('Teď %d Hz | změna po restartu.', 'Now %d Hz · change after restart.') % info[1])

    def _C9DefaultValue(self, key, kind, row):
        if key == 'quality_preset':
            value = 2
        elif key == 'color_preset':
            value = 1
        elif settingschat.owns(key):
            value = settingschat.DEFAULTS[key]
        elif key in settingsmodel.COLOR_DEFAULTS:
            value = settingsmodel.COLOR_DEFAULTS[key]
        elif key == 'row_icons':
            value = 0
        elif key == 'channel_bar_style':
            value = 'stepper'
        else:
            value = settingsmodel.DEFAULTS.get(key)
        if kind in ('toggle', 'look_icons'):
            mask = row.get('mask')
            on = bool((value or 0) & mask) if mask else bool(value)
            return Tr('Zapnuto', 'On') if on else Tr('Vypnuto', 'Off')
        if kind == 'choice':
            return _label_of(row.get('options', ()), value)
        if kind == 'slider':
            return self._Format(key, value)
        if kind == 'sky':
            return pages.SKIES[value or 0]
        if kind == 'track':
            return Tr('Podle mapy', 'Map default')
        if kind == 'refresh':
            return Tr('Auto', 'Auto')
        if kind == 'dropdown':
            return _label_of(row.get('options', ()), value)
        if kind == 'color':
            return '#%06X' % (value or 0)
        if kind == 'ui_scale':
            return '%d %%' % (value or 100)
        if kind == 'number':
            return str(value)
        return ''

    def _C9DefaultText(self, row):
        kind = row['kind']
        if kind == 'range':
            values = [str(settingsmodel.DEFAULTS.get(item['key'])) for item in row['items']]
            return Tr('Výchozí: %s', 'Default: %s') % '-'.join(values)
        if kind in ('buttons', 'open', 'look_old', 'chips', 'reset_all', 'key', 'name_actions'):
            return ''
        text = self._C9DefaultValue(row['key'], kind, row)
        return Tr('Výchozí: %s', 'Default: %s') % text if text else ''

    # ------------------------------------------------------------------ row tooltip (v5 fix 2026-10-05)
    TIP_DELAY = 0.35  # s on a row before its description shows (moving across rows does not flash tooltips)

    def _C9TipContent(self, row):
        """(title, description, note) of a row's tooltip, or None: a row without a description has no tooltip
        (the default value is not repeated here - a changed option shows it inline, owner v5 fix)."""
        body = row.get('hint_text') or ''
        note = row.get('tip_note') or ''
        key = row.get('key')
        if key and settingschat.owns(key) and not self.c9_chat.available(key):
            note = Tr('Dostupné jen s novým chatem.', 'Needs the new chat.')
        if not body and not note:
            return None
        return row.get('tip_title') or row.get('label') or '', body, note

    def _C9HideTip(self):
        self.c9_tip_pending = self.c9_tip_owner = None
        tip = getattr(self, 'c9_tip', None)
        if tip is not None and tip.IsShow():
            tip.Hide()

    def _C9ShowTip(self, anchor, title, body='', note='', side='below'):
        """Tooltip at a global rect (x, y, w, h), or at a widget that then owns it: the tooltip goes away when the
        mouse leaves that widget (_C9TipTick)."""
        if getattr(self, 'c9_tip', None) is None:
            self.c9_tip = uikit.Tooltip(self.kit)
        rect = anchor
        if hasattr(anchor, 'GetGlobalPosition'):
            x, y = anchor.GetGlobalPosition()
            rect = (x, y, anchor.GetWidth(), anchor.GetHeight())
            self.c9_tip_owner = anchor
        self.c9_tip.ShowAt(rect, title, body, note, side=side)

    @staticmethod
    def _C9MouseIn(rect, mouse):
        return mouse is not None and rect[0] <= mouse[0] < rect[0] + rect[2] and rect[1] <= mouse[1] < rect[1] + rect[3]

    def _C9RowRect(self, row):
        """Global rect of a row (its hit area, else its band), clipped to the visible content."""
        widget = row.get('hit') or row.get('band')
        if widget is None:
            return None
        x, y = widget.GetGlobalPosition()
        w, h = widget.GetWidth(), widget.GetHeight()
        viewport = getattr(self, 'viewport', None)
        if viewport is not None and not self.legacy_mode:
            vx, vy = viewport.GetGlobalPosition()
            top, bottom = max(y, vy), min(y + h, vy + viewport.GetHeight())
            if bottom <= top:
                return None
            y, h = top, bottom - top
        return x, y, w, h

    def _C9TipTick(self):
        """Called every frame: the hovered row loses its band and tooltip once the mouse leaves it (anywhere -
        another part of the window, outside the window), and the pending tooltip shows after TIP_DELAY."""
        try:
            mouse = tuple(wndMgr.GetMousePosition())
        except Exception:
            mouse = None
        mx = mouse[0] if mouse else None
        owner = getattr(self, 'c9_tip_owner', None)
        if owner is not None and mouse is not None:
            x, y = owner.GetGlobalPosition()
            if not owner.IsShow() or not self._C9MouseIn((x, y, owner.GetWidth(), owner.GetHeight()), mouse):
                self._C9HideTip()
        row = getattr(self, 'c9_info_row', None)
        if row is None:
            return
        rect = self._C9RowRect(row)
        if rect is None or (mouse is not None and not self._C9MouseIn(rect, mouse)):
            self._C9ShowInfo(None)
            return
        pending = self.c9_tip_pending
        if pending is None or pending[0] is not row or app.GetTime() < pending[2]:
            return
        self.c9_tip_pending = None
        title, body, note = pending[1]
        x, y, w, h = rect
        tip_w = min(self._C9TipWidth(), w)
        anchor_x = x if mx is None else max(x, min(mx - 16, x + w - tip_w))
        self._C9ShowTip((anchor_x, y, tip_w, h), title, body, note)

    def _C9TipWidth(self):
        return 440 if self.kit.prof == '1080' else 340

    def _C9ShowInfo(self, row=None):
        """Hover of a row (any row of any v5 page, custom pages included): the hover band, and after a moment the
        row's description as a kit tooltip under the row. None = nothing hovered (band and tooltip go away).
        Replaces the description strip under the content (owner play test 2026-10-05)."""
        if row is not None and row is getattr(self, 'c9_info_row', None):
            return
        previous = getattr(self, 'c9_info_row', None)
        if previous is not None and previous is not row and previous.get('band') and not previous.get('marked'):
            previous['band'].Hide()
        if row is not None and row.get('band'):
            row['band'].Show()
        self.c9_info_row = row
        self._C9HideTip()
        content = self._C9TipContent(row) if row is not None else None
        if content is not None:
            self.c9_tip_pending = (row, content, app.GetTime() + self.TIP_DELAY)
