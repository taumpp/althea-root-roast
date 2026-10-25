# -*- coding: utf-8 -*-
"""Names and units derived from the same formatter as item attributes."""
import re
import textcase


def Describe(formatter, kind):
    zero, probe = formatter(kind, 0), formatter(kind, 12345)
    if not zero or not probe or zero.startswith('UNKNOWN_TYPE['):
        return None
    if zero == probe:
        return textcase.CapitalFirst(' '.join(zero.split()).strip(' :')), ''
    start = 0
    while start < min(len(zero), len(probe)) and zero[start] == probe[start]:
        start += 1
    end = 0
    while end < min(len(zero), len(probe)) - start and zero[-end - 1] == probe[-end - 1]:
        end += 1
    prefix, suffix = zero[:start], zero[len(zero) - end:] if end else ''
    prefix = prefix.rstrip().rstrip('+-').rstrip()
    # A decimal formatter shares its fractional zeroes across the two probes.
    suffix = re.sub(r'^[.,]0+', '', suffix).lstrip()
    unit = ''
    if suffix.startswith('%'):
        unit, suffix = '%', suffix[1:]
    elif re.match(r'^m(?:\s|$)', suffix):
        unit, suffix = 'm', suffix[1:]
    name = ' '.join((prefix + ' ' + suffix).split()).strip(' :')
    return textcase.CapitalFirst(name), unit
