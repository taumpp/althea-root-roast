"""Damage appearance controls in the existing settings page."""
from functools import partial
import weakref
import grp
import ui
import fontconfig
import systemSetting
import damageappearance as damage
from settingslocale import Text as T


def build(owner, y):
    change = ui.__mem_func__(owner.change)
    proxy = weakref.proxy(owner)
    selectors = (
        ('damage_font', T('Písmo zásahů','Damage font'), y,
         tuple(enumerate(damage.FONTS))),
        ('damage_grouping', T('Oddělování tisíců','Thousands grouping'), y+163,
         ((0,T('Žádné · 1234567','None · 1234567')),
          (1,T('Mezera · 1 234 567','Space · 1 234 567')),
          (2,T('Tečka · 1.234.567','Dot · 1.234.567')))),
    )
    for key, label, row, choices in selectors:
        line = owner.text(label, 0, row)
        button = owner.action(key, '', row-7,
                              partial(open_choices, proxy, key, choices), left=True, x=176, family='170x24')
        owner.controls.append(dict(kind='damage_selector', key=key, label=line,
                                   widget=button, choices=choices, y=row))
    for key, label, row in (
            ('damage_normal_color',T('Barva normálních zásahů','Normal hit color'),y+42),
            ('damage_critical_color',T('Barva kritických zásahů','Critical hit color'),y+84)):
        line = owner.text(label, 0, row)
        button = owner.action(key, '', row-7, partial(open_color, proxy, key),
                              left=True, x=176, family='170x24')
        swatch = owner._bar(185,row-1,12,12,(*damage.rgb(owner.value(key)),1))
        swatch.AddFlag('not_pick')
        owner.controls.append(dict(kind='damage_color',key=key,label=line,widget=button,swatch=swatch,y=row))
    owner.check('damage_outline',T('Černý obrys číslic','Black number outline'),0,y+124,width=348)
    owner.section(T('Náhled zásahů','Damage preview'),y+201)
    owner.text(T('Normální zásah','Normal hit'),0,y+237,small=True)
    owner.text(T('Kritický zásah','Critical hit'),184,y+237,small=True)
    for x, key, value in ((0,'damage_normal_color',1016),(184,'damage_critical_color',8888)):
        images = [owner._keep(ui.ExpandedImageBox(),x,y+262) for unused in range(13)]
        for image in images:
            image.AddFlag('not_pick')
        owner.controls.append(dict(kind='damage_preview',key=key,images=images,x=x,y=y+262,number=value))
    owner.hint(T('Výška přidává procenta výšky cíle nad původní polohu.','Height adds a percentage of target height above the original position.'),y+307)
    if not callable(getattr(systemSetting,'SetDamageHeight',None)):
        for control in owner.controls:
            if control['key'] == 'damage_height':
                control['widget'].Disable()
    if not damage.supported(systemSetting):
        for control in owner.controls:
            if control['key'] in damage.KEYS and 'widget' in control:
                control['widget'].Disable()
        owner.hint(T('Nové volby vyžadují aktualizaci hry.','Update the client to use these options.'),y+330)


def refresh(control, values):
    kind, key = control['kind'], control['key']
    value = values[key]
    if kind == 'damage_selector':
        control['widget'].SetText(dict(control['choices'])[value] + ' ▾')
    elif kind == 'damage_color':
        control['widget'].SetText('#%06X ▾' % value)
        control['swatch'].SetColor(grp.GenerateColor(*damage.rgb(value),1))
    elif kind == 'damage_preview':
        font, outline = values['damage_font'], values['damage_outline']
        digits = damage.format_number(control['number'], values['damage_grouping'])
        font, glyph_scale, positions = damage.preview_layout(
            systemSetting, font, outline, digits, values['damage_size'])
        legacy = key == 'damage_normal_color' and font == 0 and outline and value == damage.DEFAULTS[key]
        for index, image in enumerate(control['images']):
            if index >= len(digits) or digits[index] == ' ':
                image.Hide()
                continue
            glyph = digits[index]
            old = legacy and glyph != '.'
            path = damage.PATH+'target_'+glyph+'.dds' if old else damage.texture(font,outline,glyph)
            image.LoadImage(path)
            image.SetScale(glyph_scale,glyph_scale)
            image.SetPosition(control['x']+round(positions[index][0]),
                              control['y']+round(positions[index][1])-round(values.get('damage_height',0)*8))
            color = damage.rgb(value)
            image.SetDiffuseColor(*(color if not old or key == 'damage_critical_color' else (1.,1.,1.)),1.)
            image.Show()


def open_color(owner, key):
    if not damage.supported(systemSetting):
        return
    owner._ClosePopup()
    if owner.damage_color_dialog is None:
        from uicolorpicker import ColorPickerDialog
        owner.damage_color_dialog = ColorPickerDialog()
    change = ui.__mem_func__(owner.change)
    owner.damage_color_dialog.Open(owner.value(key), partial(change,key),
                                   partial(change,key,damage.DEFAULTS[key]))


def open_choices(owner, key, choices):
    if not damage.supported(systemSetting):
        return
    owner._ClosePopup()
    popup = ui.BoardWithTitleBar()
    owner.popup = popup
    popup.AddFlag('float')
    popup.SetSize(250,42+24*len(choices))
    popup.SetTitleName(T('Písmo zásahů','Damage font') if key=='damage_font' else T('Oddělování tisíců','Thousands grouping'))
    close = ui.__mem_func__(owner._ClosePopup)
    popup.SetCloseEvent(close)
    popup.OnPressEscapeKey = close
    popup.SetCenterPosition()
    change = ui.__mem_func__(owner.change)
    def selected(value):
        change(key,value)
        close()
    import uicrimsoncontrols as crimson
    for index,(value,label) in enumerate(choices):
        button=ui.Button()
        button.SetParent(popup)
        button.SetPosition(15,35+24*index)
        crimson.ApplyVisuals(button,'170x24')
        button.SetFontName(fontconfig.FontForRole(fontconfig.ROLE_DENSE))
        button.SetText(label)
        button.SetEvent(partial(selected,value))
        button.Show()
        owner.popup_widgets.append(button)
    popup.Show()
    popup.SetTop()
    popup.SetFocus()
