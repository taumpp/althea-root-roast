"""Damage glyph catalog shared by the settings preview and native effects."""
FONTS = ('Původní herní číslice', 'Tahoma Bold', 'Arial Bold', 'Verdana Bold',
         'Georgia Bold', 'Bangers', 'Anton', 'Bebas Neue', 'Cinzel Bold',
         'Orbitron Bold', 'Black Ops One', 'Bungee')
KEYS = ('damage_font', 'damage_normal_color', 'damage_critical_color', 'damage_outline', 'damage_grouping')
DEFAULTS = dict(damage_font=0, damage_normal_color=0xFFFF00,
                damage_critical_color=0x66BFFF, damage_outline=1, damage_grouping=0)
PATH = 'd:/ymir work/effect/affect/damagevalue/'


def supported(native):
    return all(callable(getattr(native, method + suffix, None))
               for suffix in ('DamageFont','DamageNormalColor','DamageCriticalColor','DamageOutline','DamageGrouping')
               for method in ('Get','Set'))


def format_number(value, grouping):
    digits = str(max(0, min(0xFFFFFFFF, int(value))))
    if grouping not in (1, 2):
        return digits
    separator = ' ' if grouping == 1 else '.'
    head = len(digits) % 3 or 3
    return separator.join([digits[:head]] + [digits[i:i+3] for i in range(head, len(digits), 3)])


def texture(font, outline, glyph):
    return PATH + 'styles/%d/%s/%s.tga' % (font, 'outline' if outline else 'plain', 'dot' if glyph == '.' else glyph)


def offsets(digits):
    result = []
    position = 0.
    previous = 0.
    for glyph in digits:
        width = 8. if glyph in ' .' else 30.
        if result:
            position += (previous + width) / 2.
        result.append(position)
        previous = width
    return result


def font_scale(native, font):
    getter = getattr(native, 'GetDamageFontScale', None)
    return getter(font) if callable(getter) else 1.


def preview_layout(native, font, outline, digits, size):
    scale = .32 * (1 + size)
    getter = getattr(native, 'GetDamageGlyphLayout', None)
    if font > 0 and callable(getter):
        layout = getter(font, int(outline), digits)
        if layout is not None:
            height_scale, baseline, reference_baseline, origins = layout
            glyph_scale = scale * height_scale
            return font, glyph_scale, [(x * glyph_scale,
                reference_baseline * scale - baseline * glyph_scale) for x in origins]
        font = 0
    height_scale = font_scale(native, font)
    return font, scale * height_scale, [(x * scale, 50 * scale * (1 - height_scale))
                                      for x in offsets(digits)]


def rgb(value):
    return tuple(((int(value) >> shift) & 255) / 255. for shift in (16, 8, 0))
