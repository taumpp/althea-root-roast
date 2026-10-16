# -*- coding: utf-8 -*-
"""Catalogue ordering and bounded pages for the shared crafting window."""
# Reuse the pure string folding already supported by the embedded client.
# Importing unicodedata here aborts construction of the entire game interface.
from marketfilters import folded as search_key


def pages(recipes, category, query, height=152):
    result, page, used = [], [], 0
    needle = search_key(query)
    for recipe in recipes:
        if category and recipe['group'] != category:
            continue
        if needle and needle not in search_key(recipe['name']):
            continue
        row_height = max(38, recipe['height'] + 6)
        if page and used + row_height > height:
            result.append(page)
            page, used = [], 0
        page.append(recipe)
        used += row_height
    if page:
        result.append(page)
    return result


def quantity(value, maximum):
    try:
        requested = int(value)
    except (TypeError, ValueError):
        requested = 1
    return max(1, min(requested, max(1, maximum)))
