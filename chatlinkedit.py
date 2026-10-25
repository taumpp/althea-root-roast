# -*- coding: utf-8 -*-
"""An item link (or an emoticon) in the chat input is one piece: deleting any part of it deletes all of it.

The native IME (EterLib/IME.cpp) keeps a pasted link as its raw tags ``|cffXXXXXX|Hitem:...|h[Name]|h|r`` and a
Backspace or Delete removes them one character or one tag at a time. The first Backspace after a link leaves
``...esence]|hr``: the input showed the old link with a stray "r", then "hr", the name shrinking letter by letter, and
once the ``|h`` that opens the name was gone the leftover hidden ``|Hitem:...`` swallowed the rest of the message.

Repair(previous, current) sees such a broken edit and returns the text with the whole link removed (or None when the
edit left every link whole); RenderLength gives the cursor position the IME takes (ime.SetCursorPosition counts the
visible characters, the same rule as EterLib/TextTag.cpp GetTextTagOutputLen). Pure Python, no engine module."""
import re

# A pasted item link (chat.GetLinkFromHyperlink), a bare hyperlink and an emoticon image tag; "||" is an
# escaped "|" inside a name.
_PIECE = re.compile(r'\|c[0-9A-Fa-f]{8}\|H[^|]*\|h(?:[^|]|\|\|)*\|h\|r'
                    r'|\|H[^|]*\|h(?:[^|]|\|\|)*\|h'
                    r'|\|I[^|]*\|i')
_TAGS = 'cHhrIi'


def Pieces(text):
    """(start, end) of every whole link / emoticon in ``text``."""
    return [match.span() for match in _PIECE.finditer(text or '')]


def Broken(text):
    """True when ``text`` holds a tag outside a whole link: a remnant of a link the edit cut."""
    text = text or ''
    rest = _PIECE.sub('', text)
    index = 0
    while True:
        index = rest.find('|', index)
        if index < 0 or index + 1 >= len(rest):
            return False
        following = rest[index + 1]
        if following == '|':
            index += 2                      # "||": a typed "|"
            continue
        if following in _TAGS:
            return True
        index += 1


def _Changed(previous, current):
    """The edit as (start, end) in ``previous`` replaced by current[start:end + len(current) - len(previous)]."""
    limit = min(len(previous), len(current))
    start = 0
    while start < limit and previous[start] == current[start]:
        start += 1
    tail = 0
    while tail < limit - start and previous[-1 - tail] == current[-1 - tail]:
        tail += 1
    return start, len(previous) - tail, current[start:len(current) - tail]


def Repair(previous, current):
    """(text, cursor) - ``current`` with every link the edit cut removed whole, the cursor (an index into text) where
    the link was - or None when nothing is broken (typing, a whole link pasted or removed, no link at all)."""
    if previous is None or current is None or current == previous or not Broken(current):
        return None
    start, end, inserted = _Changed(previous, current)
    pieces = Pieces(previous)
    if start == end:
        # an insertion inside a link (it cannot happen through the IME, which steps over the tags): after the link
        hit = [piece for piece in pieces if piece[0] < start < piece[1]]
        if not hit:
            return None
        at = hit[0][1]
        text = previous[:at] + inserted + previous[at:]
        return text, at + len(inserted)
    hit = [piece for piece in pieces if piece[0] < end and start < piece[1]]
    if not hit:
        return None
    start = min([start] + [piece[0] for piece in hit])
    end = max([end] + [piece[1] for piece in hit])
    text = previous[:start] + inserted + previous[end:]
    if Broken(text):
        return None                         # the edit was something else; leave it to the player
    return text, start + len(inserted)


def RenderLength(text):
    """Visible characters of ``text`` (EterLib GetTextTagOutputLen): the names of links, not their tags."""
    length = 0
    step = 0                                # 0 text, 1 the hidden link data, 2 the link name
    image = False
    index = 0
    size = len(text or '')
    while index < size:
        char = text[index]
        following = text[index + 1] if index + 1 < size else ''
        if char != '|' or not following:
            if step != 1 and not image:
                length += 1
            index += 1
            continue
        if following == 'c' and size - index >= 10:
            index += 10
        elif following == '|':
            if step != 1 and not image:
                length += 1
            index += 2
        elif following == 'r':
            index += 2
        elif following == 'H':
            step = 1
            index += 2
        elif following == 'h':
            step = 2 if step == 1 else 0 if step == 2 else step
            index += 2
        elif following == 'I':
            image = True
            index += 2
        elif following == 'i':
            image = False
            index += 2
        else:
            if step != 1 and not image:
                length += 1
            index += 1
    return length
