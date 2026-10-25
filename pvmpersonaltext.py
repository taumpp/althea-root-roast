# -*- coding: utf-8 -*-
"""Player-facing names; bonus names reuse the ordinary locale vocabulary."""
import bonuscolor
import app
import localeInfo
import pvmpersonal

# Native text colors cross a signed C int boundary, even though ARGB is a
# 32-bit bit pattern. Unsigned 0xff... literals are silently rejected there.
TITLE_COLOR = 0xffE9E7D2 - 0x100000000
LEVEL_COLOR = 0xffDEC297 - 0x100000000
VALUE_COLOR = bonuscolor.POSITIVE
TEXT_COLOR = 0xffC5C7C4 - 0x100000000
MUTED_COLOR = 0xffAAA398 - 0x100000000

_CZ = {
    'TITLE': 'Pasivky', 'ON': 'ZAPNI', 'OFF': 'VYP.', 'UNLEARNED': 'Nenaučeno',
    'PASSIVE': 'Pasivní schopnost:', 'SCOPE_SHARED': 'PvP i PvM', 'SCOPE_MONSTERS': 'Jen běžné příšery',
    'PANEL_TOGGLE': 'Zapíná se samostatně v panelu.',
    'DESCRIPTION_ATTACK': 'Hodnota útoku',
    'DESCRIPTION_DEFENSE': 'Obrana',
    'DESCRIPTION_REDUCTION': 'Odolnost proti běžným příšerám',
    'VALUE_ATTACK': 'Hodnota útoku +%d', 'VALUE_DEFENSE': 'Obrana +%d',
    'VALUE_REDUCTION': 'Odolnost proti běžným příšerám +%d%%',
    'TIME': 'Zbývá: %s', 'DURATION': 'Trvání: 2 hodiny',
    'LEFT': 'Levým tlačítkem zapnout', 'RIGHT': 'Pravým tlačítkem vypnout',
    'LEFT_OFF': 'Levým tlačítkem vypnout',
    'CAST': 'Opětovným použitím vypnout',
    'EXPIRED': 'Bonus skončil: %s.',
    'RECAST': 'Bonus skončil: %s. Sešli schopnost znovu.',
}
_EN = {
    'TITLE': 'Passives', 'ON': 'ON', 'OFF': 'OFF', 'UNLEARNED': 'Unlearned',
    'PASSIVE': 'Passive skill:', 'SCOPE_SHARED': 'PvP and PvM', 'SCOPE_MONSTERS': 'Ordinary monsters only',
    'PANEL_TOGGLE': 'Activated separately in the passive panel.',
    'DESCRIPTION_ATTACK': 'Attack Value',
    'DESCRIPTION_DEFENSE': 'Defense',
    'DESCRIPTION_REDUCTION': 'Ordinary Monster Resistance',
    'VALUE_ATTACK': 'Attack Value +%d', 'VALUE_DEFENSE': 'Defense +%d',
    'VALUE_REDUCTION': 'Ordinary Monster Resistance +%d%%',
    'TIME': 'Remaining: %s', 'DURATION': 'Duration: 2 hours',
    'LEFT': 'Left-click to activate', 'RIGHT': 'Right-click to deactivate',
    'LEFT_OFF': 'Left-click to deactivate',
    'CAST': 'Use again to deactivate',
    'EXPIRED': 'Bonus expired: %s.',
    'RECAST': 'Bonus expired: %s. Cast the skill again.',
}


def legacy_affect_suffix(source, index, affect_type=None):
    """None hides a replaced effect; surviving effects retain their real scope."""
    model = pvmpersonal.current()
    if not model or source not in model.rows:
        return ''
    replaced = {
        3: ({0}, {'ATT_SPEED'}),
        4: ({0}, {'ATT_GRADE'}),
        19: ({0, 1}, {'DEF_GRADE', 'MOV_SPEED'}),
        63: ({0}, {'ATT_GRADE'}),
        65: ({0}, {'DEF_GRADE'}),
        79: ({1}, {'DEF_GRADE'}),
    }
    indices, types = replaced.get(source, (set(), set()))
    hidden = index in indices if affect_type is None else affect_type in types
    if hidden:
        return None
    return ' (PvP)' if source in (63, 64, 65, 79) else ''


def text(key):
    is_czech = app.GetLocalePath().replace('\\', '/').rsplit('/', 1)[-1].lower() == 'cz'
    return (_CZ if is_czech else _EN)[key]


def value(row):
    role, amount = row['role'], row['value']
    if role == 0:
        return localeInfo.TOOLTIP_ATT_GRADE(amount)
    if role == 1:
        return localeInfo.TOOLTIP_DEF_GRADE(amount)
    return text('VALUE_REDUCTION') % amount


def timer(seconds, exact=False):
    seconds = max(0, int(seconds))
    hours, rest = divmod(seconds, 3600)
    minutes, seconds = divmod(rest, 60)
    if exact:
        return '%d:%02d:%02d' % (hours, minutes, seconds)
    return '%dh%02d' % (hours, minutes) if hours else '%02d:%02d' % (minutes, seconds)


def title(source, name, now):
    model = pvmpersonal.current()
    row = model.rows.get(source) if model else None
    if not row or not row['learned']:
        return name
    level = row['activated'] if model.remaining(source, now) else row['learned']
    return '%s | %s' % (name, pvmpersonal.grade(level))


def cast_description(row):
    return text(('DESCRIPTION_ATTACK', 'DESCRIPTION_DEFENSE', 'DESCRIPTION_REDUCTION')[row['role']])


def append_bonus(tooltip, skill, now, passive_controls=True, passive_section=False,
                 passive_only=False, show_scope=False, value_color=None):
    model = pvmpersonal.current()
    row = model.rows.get(skill) if model else None
    if row is None:
        return False
    if passive_section:
        tooltip.AppendPersonalSeparator()
    if passive_section or passive_only:
        tooltip.AutoAppendNewTextLineResize(text('PASSIVE'), LEVEL_COLOR if passive_section else MUTED_COLOR)
    if not row['learned']:
        tooltip.AutoAppendNewTextLineResize(cast_description(row), TEXT_COLOR)
        tooltip.AutoAppendNewTextLineResize(text('UNLEARNED'), MUTED_COLOR)
        if row['role'] != 2:
            tooltip.AutoAppendNewTextLineResize(text('SCOPE_SHARED'), MUTED_COLOR)
        return True
    remaining = model.remaining(skill, now)
    tooltip.AppendSpace(5)
    tooltip.AutoAppendNewTextLineResize(value(row),
        bonuscolor.Value(row['value']))
    tooltip.AutoAppendNewTextLineResize(
        text('TIME') % timer(remaining, True) if remaining else text('DURATION'), TEXT_COLOR)
    if passive_section or passive_only or show_scope:
        tooltip.AutoAppendNewTextLineResize(text('SCOPE_MONSTERS' if row['role'] == 2 else 'SCOPE_SHARED'), MUTED_COLOR)
    if passive_section:
        tooltip.AutoAppendNewTextLineResize(text('PANEL_TOGGLE'), MUTED_COLOR)
    elif passive_only:
        pass
    elif row['hud'] and passive_controls:
        tooltip.AutoAppendNewTextLineResize(text('LEFT_OFF' if remaining else 'LEFT'), TEXT_COLOR)
    elif remaining and skill in pvmpersonal.CAST_SKILLS:
        tooltip.AutoAppendNewTextLineResize(text('CAST'), TEXT_COLOR)
    return True
